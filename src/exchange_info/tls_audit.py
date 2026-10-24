"""Offline installed-artifact gate for CI, image builds and deployment review."""
from __future__ import annotations

import argparse
import importlib.metadata as metadata
import json
from pathlib import Path
import subprocess
import sys

import certifi
import playwright

from .tls_trust import BLOCKED_ROOT_SHA256, certificate_fingerprints, validate_bundle


def audit(*, system: bool = False) -> dict:
    result = {name: metadata.version(name) for name in ("certifi", "requests", "playwright", "pip", "ddgs")}
    for name, minimum in (("certifi", (2026, 10, 19)), ("pip", (26, 2, 2)), ("playwright", (1, 64, 1))):
        if tuple(map(int, result[name].split('.'))) < minimum:
            raise ValueError(f"Unpatched {name}: {result[name]}")
    validate_bundle(certifi.where())
    import pip._vendor.certifi as pip_certifi
    validate_bundle(pip_certifi.where())
    node = Path(playwright.__file__).parent / "driver" / ("node.exe" if sys.platform == "win32" else "node")
    code = """const tls=require('tls'),{X509Certificate}=require('crypto');
console.log(JSON.stringify({version:process.versions.node,roots:tls.getCACertificates('default').map(p=>new X509Certificate(p).fingerprint256.replaceAll(':','').toLowerCase())}));"""
    node_data = json.loads(subprocess.check_output([str(node), "-e", code], text=True))
    version = tuple(map(int, node_data['version'].split('.')))
    minimum = {22: (22, 23, 4), 24: (24, 22, 1), 26: (26, 12, 1)}.get(version[0])
    if minimum is None or version < minimum or set(node_data['roots']) & BLOCKED_ROOT_SHA256:
        raise ValueError("Playwright Node has unverified version or incident CA roots")
    result['node'] = node_data['version']
    result['certifi_ca_count'] = len(certificate_fingerprints(Path(certifi.where()).read_text(encoding='ascii')))
    result['node_ca_count'] = len(node_data['roots'])
    result['search_transport'] = 'Requests (primp transport bypassed; not claimed patched)'
    if system:
        validate_bundle('/etc/ssl/certs/ca-certificates.crt')
        for path in Path('/etc/ssl/certs').iterdir():
            if path.is_file() and path.suffix != '.crt':
                data = path.read_text(encoding='ascii', errors='ignore')
                if '-----BEGIN CERTIFICATE-----' in data and certificate_fingerprints(data) & BLOCKED_ROOT_SHA256:
                    raise ValueError(f"Incident root in system CApath: {path.name}")
        result['system_ca'] = 'bundle and hashed directory checked'
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--system', action='store_true')
    print(json.dumps(audit(system=parser.parse_args().system), sort_keys=True))
