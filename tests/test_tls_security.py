"""Offline regressions: no external services or production data involved."""
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import socket
import ssl

import certifi
import pytest
import requests
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID
from urllib3.connection import HTTPSConnection

from exchange_info import tls_trust
from exchange_info.http_client import SafeHTTPSConnection, get_safe_session
from exchange_info.search_transport import RequestsDDGS, RequestsTransport


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def denied(*args, **kwargs):
        pytest.fail("Offline TLS tests must not create network connections")
    monkeypatch.setattr(socket, "getaddrinfo", denied)
    monkeypatch.setattr(socket.socket, "connect", denied)
    for key in ('REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE', 'SSL_CERT_FILE', 'SSL_CERT_DIR'):
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def internal_ca(tmp_path):
    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'isolated-gateway-test')])
    now = datetime.now(timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
            .serial_number(x509.random_serial_number()).not_valid_before(now-timedelta(days=1))
            .not_valid_after(now+timedelta(days=1)).add_extension(x509.BasicConstraints(ca=True, path_length=None), True)
            .sign(key, hashes.SHA256()))
    pem = cert.public_bytes(serialization.Encoding.PEM).decode('ascii')
    bundle = tmp_path/'bundle.pem'
    bundle.write_text(Path(certifi.where()).read_text(encoding='ascii') + pem, encoding='ascii')
    return bundle, cert, key, pem


def test_internal_gateway_ca_survives_without_loading_system_store(internal_ca, monkeypatch):
    bundle, cert, _, _ = internal_ca
    monkeypatch.setenv('REQUESTS_CA_BUNDLE', str(bundle))
    monkeypatch.setenv('SSL_CERT_DIR', '/must-not-be-loaded')
    def denied(*args, **kwargs):
        pytest.fail('must not load default/system certificates')
    monkeypatch.setattr(ssl.SSLContext, 'load_default_certs', denied)
    context = tls_trust.client_context()
    assert cert.fingerprint(hashes.SHA256()).hex() in {hashlib.sha256(c).hexdigest() for c in context.get_ca_certs(binary_form=True)}
    assert context.verify_mode == ssl.CERT_REQUIRED and context.check_hostname
    session = get_safe_session()
    session.trust_env = False
    assert session.verify == str(bundle)
    assert SafeHTTPSConnection.connect is HTTPSConnection.connect


def test_exact_fingerprint_block_preserves_other_roots(internal_ca, monkeypatch, tmp_path):
    bundle, cert, _, pem = internal_ca
    blocked = cert.fingerprint(hashes.SHA256()).hex()
    monkeypatch.setattr(tls_trust, 'BLOCKED_ROOT_SHA256', frozenset({blocked}))
    with pytest.raises(ValueError, match='incident chain'):
        tls_trust.validate_bundle(bundle)
    tls_trust.validate_bundle(certifi.where())
    spec = importlib.util.spec_from_file_location('harden_ca', Path(__file__).parents[1]/'scripts/harden_image_ca.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    root = tmp_path/'roots'; root.mkdir()
    (root/'incident.crt').write_text(pem, encoding='ascii')
    untouched = root/'good.crt'
    untouched.write_bytes(Path(certifi.where()).read_bytes())
    assert module.remove_incident_roots(root) == 1
    assert untouched.read_bytes() == Path(certifi.where()).read_bytes()


def test_adapter_rejects_verify_false_before_network():
    with pytest.raises(ValueError, match='cannot be disabled'):
        get_safe_session().get('https://example.invalid', verify=False)


def test_internal_gateway_tls_handshake_in_memory(internal_ca, tmp_path, monkeypatch):
    bundle, ca, ca_key, _ = internal_ca
    key = ec.generate_private_key(ec.SECP256R1())
    now = datetime.now(timezone.utc)
    leaf = (x509.CertificateBuilder()
            .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'gateway.test')]))
            .issuer_name(ca.subject).public_key(key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now-timedelta(days=1)).not_valid_after(now+timedelta(days=1))
            .add_extension(x509.SubjectAlternativeName([x509.DNSName('gateway.test')]), False)
            .sign(ca_key, hashes.SHA256()))
    chain = tmp_path/'test-chain.pem'; keyfile = tmp_path/'test-key.pem'
    chain.write_bytes(leaf.public_bytes(serialization.Encoding.PEM))
    keyfile.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    server_context.load_cert_chain(chain, keyfile)
    monkeypatch.setenv('REQUESTS_CA_BUNDLE', str(bundle))
    def handshake(host):
        incoming, outgoing, peer_in, peer_out = (ssl.MemoryBIO() for _ in range(4))
        client = tls_trust.client_context().wrap_bio(incoming, outgoing, server_hostname=host)
        server = server_context.wrap_bio(peer_in, peer_out, server_side=True)
        for _ in range(10):
            try:
                client.do_handshake()
                return
            except ssl.SSLWantReadError:
                pass
            peer_in.write(outgoing.read())
            try:
                server.do_handshake()
            except ssl.SSLWantReadError:
                pass
            incoming.write(peer_out.read())
        pytest.fail('TLS handshake did not complete')
    handshake('gateway.test')
    with pytest.raises(ssl.SSLCertVerificationError):
        handshake('wrong.test')
    monkeypatch.delenv('REQUESTS_CA_BUNDLE')
    with pytest.raises(ssl.SSLCertVerificationError):
        handshake('gateway.test')


@pytest.mark.parametrize(('category', 'backend'), [('text','brave'), ('text','yahoo'), ('videos','duckduckgo')])
def test_every_search_backend_avoids_primp_and_preserves_payload(monkeypatch, category, backend):
    import primp
    monkeypatch.setattr(primp, 'Client', lambda *a, **k: pytest.fail('primp must never be constructed'))
    with RequestsDDGS(timeout=3) as client:
        engine = client._get_engines(category, backend)[0]
        assert isinstance(engine.http_client, RequestsTransport)
        assert engine.http_client.session.verify == certifi.where()
        if backend == 'duckduckgo':
            monkeypatch.setattr(engine, '_get_vqd', lambda query: 'test-vqd')
        payload = engine.build_payload('test', 'wt-wt', 'moderate', None, 1)
        assert payload.get('q', payload.get('p')) == 'test'
        assert client._get_engines(category, backend)[0] is engine
        with pytest.raises(KeyError):
            client._get_engines('text', 'auto')


def test_search_results_and_video_parsing_use_only_requests(monkeypatch):
    from exchange_info.web_search import search_text, search_videos
    def response(self, method, url, **kwargs):
        r = requests.Response(); r.status_code=200
        if 'brave' in url:
            r._content=b'<div data-type="web"><a href="https://school.example"><div class="title">Test school</div></a><div class="snippet"><div class="content">Test exchange</div></div></div>'
        elif '/v.js' in url:
            r._content=json.dumps({'results':[{'title':'Test video','description':'Test exchange video','content':'https://video.example'}]}).encode()
        elif 'duckduckgo' in url:
            r._content=b'vqd="12345-67890";'
        else:
            r._content=b'<html></html>'
        return r
    monkeypatch.setattr(RequestsTransport, 'request', response)
    assert search_text('test school', max_results=3, timeout_seconds=3)[0]['href']=='https://school.example'
    with RequestsDDGS(timeout=3) as client:
        assert client.videos('test', max_results=3, backend='duckduckgo')[0]['content']=='https://video.example'
    assert search_videos('test', max_results=3, timeout_seconds=3)[0]['content']=='https://video.example'


def test_installed_artifacts_pass_gate():
    from exchange_info.tls_audit import audit
    report = audit()
    assert report['node_ca_count'] > 0


def test_android_google_auth_transport_keeps_internal_ca(internal_ca, monkeypatch):
    import google.auth
    from google.auth.credentials import AnonymousCredentials
    from exchange_info.mobile_push import FcmSender
    bundle, _, _, _ = internal_ca
    monkeypatch.setenv('REQUESTS_CA_BUNDLE', str(bundle))
    monkeypatch.setattr(google.auth, 'default', lambda **kwargs: (AnonymousCredentials(), 'isolated-project'))
    observed = []
    def send(adapter, request, **kwargs):
        observed.append(kwargs['verify'])
        response = requests.Response()
        response.status_code = 200
        response._content = b'{}'
        return response
    monkeypatch.setattr(requests.adapters.HTTPAdapter, 'send', send)
    sender = FcmSender('isolated-project')
    try:
        assert sender.send('test-installation', 'test-account', 'test-notification') == 'sent'
    finally:
        sender.session.close()
    assert observed == [str(bundle)]


@pytest.mark.parametrize('status', [403, 429, 500])
def test_search_rejection_returns_empty_without_retry_or_primp(monkeypatch, status):
    import primp
    from exchange_info.web_search import search_text, search_videos
    monkeypatch.setattr(primp, 'Client', lambda *a, **k: pytest.fail('no vulnerable fallback'))
    calls = []
    def response(self, method, url, **kwargs):
        calls.append(url)
        result = requests.Response()
        result.status_code = status
        result._content = b'Unavailable'
        return result
    monkeypatch.setattr(RequestsTransport, 'request', response)
    assert search_text('isolated query', max_results=3, timeout_seconds=1) == []
    assert search_videos('isolated query', max_results=3, timeout_seconds=1) == []
    assert len(calls) == 3  # Brave, Yahoo, and the initial DuckDuckGo request only.


def test_search_uses_available_backend_after_another_rejects(monkeypatch):
    from exchange_info.web_search import search_text
    def response(self, method, url, **kwargs):
        result = requests.Response()
        result.status_code = 429 if 'brave' in url else 200
        result._content = b'<div class="relsrch"><div class="Title"><h3>Exchange school</h3><a href="https://school.example"></a></div><div class="Text">Exchange information</div></div>'
        return result
    monkeypatch.setattr(RequestsTransport, 'request', response)
    assert search_text('exchange school', max_results=3, timeout_seconds=1)[0]['href'] == 'https://school.example'


@pytest.mark.parametrize(('version', 'roots'), [
    ('24.21.0', []),
    ('24.22.1', list(tls_trust.BLOCKED_ROOT_SHA256)),
])
def test_effective_playwright_node_override_is_checked(monkeypatch, version, roots):
    from exchange_info import tls_audit
    monkeypatch.setenv('PLAYWRIGHT_NODEJS_PATH', '/isolated/custom-node')
    def report(command, **kwargs):
        assert command[0] == '/isolated/custom-node'
        return json.dumps({'version': version, 'roots': roots})
    monkeypatch.setattr(tls_audit.subprocess, 'check_output', report)
    with pytest.raises(ValueError, match='Playwright Node'):
        tls_audit.audit()
