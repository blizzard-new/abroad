from __future__ import annotations

import ipaddress
import socket
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.connection import HTTPConnection, HTTPSConnection
from urllib3.connectionpool import HTTPConnectionPool, HTTPSConnectionPool
from urllib3.poolmanager import PoolManager

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
                if parsed_ip.is_global and not parsed_ip.is_private and not parsed_ip.is_loopback and not parsed_ip.is_link_local and not parsed_ip.is_multicast:
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
    def connect(self) -> None:
        self.sock = self._new_conn()
        # For HTTPS, SNI requires the hostname.
        # We set `server_hostname` to self.host because self.host is the original hostname,
        # but the socket is connected to valid_ip.
        if hasattr(self, "proxy_is_forwarding") and self.proxy_is_forwarding:
            # urllib3 v2 logic
            self._connect_tls_proxy(self.host, self.sock)
        elif not hasattr(self, "_connect_tls_proxy"):
            self._proxy_requires_url_absolute_form = False
        
        server_hostname = self.host
        if self.assert_hostname is not False:
            server_hostname = self.assert_hostname or self.host

        tls_in_tls = False
        if hasattr(self, "_is_using_tunnel") and self._is_using_tunnel():
            if hasattr(self, "tls_in_tls_required"):
                tls_in_tls = self.tls_in_tls_required
        
        if hasattr(self.ssl_context, "wrap_socket"):
            self.sock = self.ssl_context.wrap_socket(
                self.sock,
                server_hostname=server_hostname,
            )
        else:
            import ssl
            context = ssl.create_default_context()
            self.sock = context.wrap_socket(self.sock, server_hostname=server_hostname)

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
    adapter = SafeHTTPAdapter()
    
    if require_https:
        session.mount("https://", adapter)
        session.mount("http://", _BlockHttpAdapter())
    else:
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
    return session
