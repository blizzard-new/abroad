import pytest
import requests
from exchange_info.http_client import get_safe_session, SSRFError
import socket
import json


@pytest.fixture(autouse=True)
def isolate_dns_guard_from_machine_proxy_settings(monkeypatch):
    # These socket/DNS unit tests exercise direct connections. A machine proxy
    # resolves a different host and would bypass the mocked destination lookup.
    # This changes only each test's environment, never runtime proxy settings.
    for key in ['HTTPS_PROXY', 'HTTP_PROXY', 'ALL_PROXY', 'https_proxy', 'http_proxy', 'all_proxy']:
        monkeypatch.delenv(key, raising=False)

def test_safe_session_blocks_http():
    session = get_safe_session(require_https=True)
    with pytest.raises(SSRFError, match="HTTP is disabled"):
        session.get("http://example.com")

def test_safe_session_allows_https(monkeypatch):
    session = get_safe_session(require_https=True)
    
    # We will mock create_connection to avoid making real network requests
    # but still test the DNS resolution and filtering logic.
    def mock_getaddrinfo(host, port, *args, **kwargs):
        if host == "example.com":
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]
        elif host == "localhost" or host == "127.0.0.1":
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", port))]
        elif host == "internal.local":
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.1", port))]
        elif host == "dns.rebind":
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("169.254.169.254", port))]
        raise socket.gaierror("Name or service not known")
        
    monkeypatch.setattr(socket, "getaddrinfo", mock_getaddrinfo)
    
    # For a valid public IP, it should proceed (we mock wrap_socket and create_connection to just return a dummy)
    import urllib3.util.connection
    def mock_create_connection(address, *args, **kwargs):
        class DummySock:
            def settimeout(self, *args): pass
            def close(self): pass
        return DummySock()
    monkeypatch.setattr(urllib3.util.connection, "create_connection", mock_create_connection)

    # We also mock ssl wrap_socket because it expects a real socket
    import ssl
    def mock_wrap_socket(sock, *args, **kwargs):
        return sock
    monkeypatch.setattr(ssl.SSLContext, "wrap_socket", mock_wrap_socket)
    
    # Mock connectionpool's response logic so it doesn't fail trying to read from DummySock
    from urllib3.connectionpool import HTTPSConnectionPool
    def mock_urlopen(*args, **kwargs):
        from urllib3.response import HTTPResponse
        import io
        return HTTPResponse(
            body=io.BytesIO(b"OK"),
            headers={"Content-Type": "text/plain"},
            status=200,
            preload_content=False
        )
    monkeypatch.setattr(HTTPSConnectionPool, "urlopen", mock_urlopen)

    resp = session.get("https://example.com")
    assert resp.status_code == 200

def test_safe_session_blocks_private_ips(monkeypatch):
    session = get_safe_session(require_https=True)
    
    def mock_getaddrinfo(host, port, *args, **kwargs):
        if host == "localhost":
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", port))]
        if host == "internal":
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.1", port))]
        if host == "aws-metadata":
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("169.254.169.254", port))]
        raise socket.gaierror("Name or service not known")
        
    monkeypatch.setattr(socket, "getaddrinfo", mock_getaddrinfo)
    
    with pytest.raises(requests.exceptions.ConnectionError, match="SSRF blocked: Host localhost resolved to non-public IP"):
        session.get("https://localhost")
        
    with pytest.raises(requests.exceptions.ConnectionError, match="SSRF blocked: Host internal resolved to non-public IP"):
        session.get("https://internal")
        
    with pytest.raises(requests.exceptions.ConnectionError, match="SSRF blocked: Host aws-metadata resolved to non-public IP"):
        session.get("https://aws-metadata")
