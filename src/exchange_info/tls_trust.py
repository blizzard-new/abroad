"""Explicit CA policy; never fall back to a second, stale system trust store."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import ssl

# https://github.com/certifi/python-certifi/pull/437/files
# https://bugzilla.mozilla.org/show_bug.cgi?id=2083449
# AAA is a cross-sign trust path, not itself a compromised private key.
BLOCKED_ROOT_SHA256 = frozenset({
    "86a1ecba089c4a8d3bbe2734c612ba341d813e043cf9e8a862cd5c57a36bbe6b",
    "d7a7a0fb5d7e2731d771e9484ebcdef71d5f0c3e0a2948782bc83ee0ea699ef4",
})


def certificate_fingerprints(data: str) -> set[str]:
    certs = re.findall(r"-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----", data, re.S)
    if not certs:
        raise ValueError("CA bundle contains no certificates")
    return {hashlib.sha256(ssl.PEM_cert_to_DER_cert(c)).hexdigest() for c in certs}


def validate_bundle(path: str | Path) -> str:
    path = str(path)
    if certificate_fingerprints(Path(path).read_text(encoding="ascii")) & BLOCKED_ROOT_SHA256:
        raise ValueError("CA bundle still trusts an eMudhra incident chain")
    return path


def ca_bundle() -> str:
    # Keep the fingerprint parser stdlib-only for the pre-install image gate.
    import certifi

    return validate_bundle(os.environ.get("REQUESTS_CA_BUNDLE")
                           or os.environ.get("CURL_CA_BUNDLE")
                           or os.environ.get("SSL_CERT_FILE") or certifi.where())


def client_context() -> ssl.SSLContext:
    # Explicit cafile prevents load_default_certs() from adding the OS CApath.
    return ssl.create_default_context(cafile=ca_bundle())
