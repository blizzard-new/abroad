"""Docker build only: remove exact incident anchors, preserving other roots.

Never run against the production host. The mandatory directory argument also
allows testing the transformation against a temporary tree.
"""
from pathlib import Path
import sys

from exchange_info.tls_trust import BLOCKED_ROOT_SHA256, certificate_fingerprints


def remove_incident_roots(directory: Path) -> int:
    removed = 0
    for path in directory.rglob("*.crt"):
        fingerprints = certificate_fingerprints(path.read_text(encoding="ascii"))
        if fingerprints & BLOCKED_ROOT_SHA256:
            if len(fingerprints) != 1:
                raise ValueError("Refusing to remove a multi-certificate bundle")
            path.unlink()
            removed += 1
    return removed


if __name__ == "__main__":
    print("Removed incident anchors:", remove_incident_roots(Path(sys.argv[1])))
