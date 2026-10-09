"""Reproduce the TKU-only embedded font from its pinned, licensed upstream.

Development-only command: requires fontTools 4.61.1 (not a runtime dependency).
Reads the pinned provenance record, verifies the upstream SHA256, instantiates
weight 400 with the complete repertoire, and writes only the school font asset.
"""
import hashlib
import json
import tempfile
import urllib.request
from pathlib import Path


def build():
    from fontTools.ttLib import TTFont
    from fontTools.varLib.instancer import instantiateVariableFont
    folder=Path(__file__).resolve().parents[1]/'src/exchange_info/official_data/tku/fonts'
    provenance=json.loads((folder/'provenance.json').read_text())
    with urllib.request.urlopen(provenance['source_url'],timeout=50) as response:
        source=response.read()
    assert hashlib.sha256(source).hexdigest()==provenance['source_sha256']
    with tempfile.TemporaryDirectory(prefix='tku-font-') as temporary:
        upstream=Path(temporary)/'upstream.ttf'
        upstream.write_bytes(source)
        font=TTFont(upstream,recalcTimestamp=False)
        instantiateVariableFont(font,{'wght':400},inplace=True)
        destination=Path(temporary)/provenance['derived_filename']
        font.save(destination)
        output=destination.read_bytes()
        if hashlib.sha256(output).hexdigest()!=provenance['derived_sha256']:
            raise RuntimeError('Derived font differs; verify fontTools version before replacing the asset')
        (folder/provenance['derived_filename']).write_bytes(output)


if __name__=='__main__':
    build()
