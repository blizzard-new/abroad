from __future__ import annotations

import ipaddress
import socket
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.connection import HTTPConnection, HTTPSConnection
from urllib3.connectionpool import HTTPConnectionPool, HTTPSConnectionPool
from urllib3.poolmanager import PoolManager
from .tls_trust import ca_bundle, validate_bundle

class SSRFError(requests.RequestException):
    """Raised when a request attempts to access a non-public IP address."""
    pass

class SSRFSafeguardConnectionMixin:
    def _new_conn(self) -> Any:
        # Resolve and verify before connecting to prevent basic SSRF.
        # To prevent DNS rebinding, we must connect using the verified IP.
        try:
            addr_info = socket.getaddrinfo(self.host, self.port, 0, socket.SOCK_STREAM)
        except socket.gaierror as exc:
            raise SSRFError(f"DNS resolution failed for {self.host}") from exc

        valid_ip = None
        for res in addr_info:
            ip = res[4][0]
            try:
                parsed_ip = ipaddress.ip_address(ip)
                check_ips = [parsed_ip]
                if isinstance(parsed_ip, ipaddress.IPv6Address):
                    if parsed_ip.ipv4_mapped is not None:
                        check_ips.append(parsed_ip.ipv4_mapped)
                    if parsed_ip.sixtofour is not None:
                        check_ips.append(parsed_ip.sixtofour)
                    if parsed_ip.teredo is not None:
                        check_ips.extend(parsed_ip.teredo)
                if all(
                    candidate.is_global
                    and not candidate.is_private
                    and not candidate.is_loopback
                    and not candidate.is_link_local
                    and not candidate.is_multicast
                    and not candidate.is_reserved
                    and not candidate.is_unspecified
                    for candidate in check_ips
                ):
                    valid_ip = ip
                    break
            except ValueError:
                continue
                
        if not valid_ip:
            raise SSRFError(f"SSRF blocked: Host {self.host} resolved to non-public IP")

        # Connect to the verified IP directly
        import urllib3.util.connection
        conn = urllib3.util.connection.create_connection(
            (valid_ip, self.port),
            self.timeout,
            self.source_address,
            self.socket_options
        )
        return conn

class SafeHTTPConnection(SSRFSafeguardConnectionMixin, HTTPConnection):
    pass

class SafeHTTPSConnection(SSRFSafeguardConnectionMixin, HTTPSConnection):
    # Keep urllib3's TLS handshake: it honors Requests' ca_certs, hostname
    # verification, proxy handling and verification result bookkeeping. Only
    # socket creation is overridden by the SSRF mixin above.
    pass

class SafeHTTPConnectionPool(HTTPConnectionPool):
    ConnectionCls = SafeHTTPConnection

class SafeHTTPSConnectionPool(HTTPSConnectionPool):
    ConnectionCls = SafeHTTPSConnection

class SafePoolManager(PoolManager):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.pool_classes_by_scheme = {
            "http": SafeHTTPConnectionPool,
            "https": SafeHTTPSConnectionPool,
        }

class SafeHTTPAdapter(HTTPAdapter):
    def send(self, request, **kwargs):
        if kwargs.get("verify") is False:
            raise ValueError("TLS verification cannot be disabled")
        verify = kwargs.get("verify")
        kwargs["verify"] = validate_bundle(verify) if isinstance(verify, str) else ca_bundle()
        return super().send(request, **kwargs)

    def init_poolmanager(self, connections: int, maxsize: int, block: bool = False, **pool_kwargs: Any) -> None:
        self.poolmanager = SafePoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            **pool_kwargs
        )

class _BlockHttpAdapter(HTTPAdapter):
    def send(self, request: requests.PreparedRequest, *args: Any, **kwargs: Any) -> requests.Response:
        raise SSRFError("HTTP is disabled. Only HTTPS is allowed for public endpoints.")

def get_safe_session(require_https: bool = True) -> requests.Session:
    """Return a requests.Session that protects against SSRF and enforces HTTPS."""
    session = requests.Session()
    session.verify = ca_bundle()
    adapter = SafeHTTPAdapter()
    
    if require_https:
        session.mount("https://", adapter)
        session.mount("http://", _BlockHttpAdapter())
    else:
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
    return session
