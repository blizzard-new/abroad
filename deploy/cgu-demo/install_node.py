"""Install the effective Playwright Node runtime inside the demo image only."""
from __future__ import annotations

import hashlib
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile
from urllib.request import urlopen

VERSION = '24.22.1'
# Official nodejs.org/dist/v24.22.1/SHASUMS256.txt, retrieved 2026-11-11.
ARCHIVES = {
    'amd64': ('x64', '6c172a9ab6718f7b801fb5a7bd486af2ee5e32758086a04b84fcce2aa77095e6'),
    'arm64': ('arm64', 'dbabf7a1cbf947e6059ffad2c27b80041db97dea1e553b62afdee7f13fca336e'),
}


def main(architecture: str) -> None:
    arch, expected = ARCHIVES[architecture]
    name = f'node-v{VERSION}-linux-{arch}'
    with tempfile.TemporaryDirectory() as directory:
        archive = Path(directory) / 'node.tar.xz'
        digest = hashlib.sha256()
        with urlopen(f'https://nodejs.org/dist/v{VERSION}/{name}.tar.xz', timeout=60) as response, archive.open('wb') as output:
            while chunk := response.read(1024 * 1024):
                digest.update(chunk)
                output.write(chunk)
        if digest.hexdigest() != expected:
            raise ValueError('Node archive checksum mismatch')
        target = Path('/opt/uniway-node/bin/node')
        target.parent.mkdir(parents=True, exist_ok=True)
        with tarfile.open(archive, 'r:xz') as bundle:
            source = bundle.extractfile(name + '/bin/node')
            if source is None:
                raise ValueError('Node binary missing')
            with source, target.open('wb') as output:
                shutil.copyfileobj(source, output)
        target.chmod(0o755)
    print(f'Installed checksum-verified Node {VERSION} ({arch})')


if __name__ == '__main__':
    main(sys.argv[1])
