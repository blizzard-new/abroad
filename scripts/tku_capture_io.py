"""Read TKU raw captures from loose refresh files or immutable evidence packs."""
import hashlib
import json
import tempfile
from functools import lru_cache
from pathlib import Path
from zipfile import ZipFile

BUNDLE=Path(__file__).resolve().parents[1]/'src/exchange_info/official_data/tku'


@lru_cache(maxsize=1)
def pack_manifest():
    path=BUNDLE/'capture_pack_manifest.json'
    return json.loads(path.read_text()) if path.exists() else {'files':{},'archives':[]}


def manifest():return pack_manifest()['files']


def relative(path):return Path(path).relative_to(BUNDLE).as_posix()


def exists(path):return Path(path).exists() or relative(path) in manifest()


@lru_cache(maxsize=16)
def archive(name):
    path=BUNDLE/'capture_packs'/name
    if path.exists():return ZipFile(path)
    record=next(r for r in pack_manifest()['archives'] if r['file']==name)
    assembled=tempfile.TemporaryFile(prefix='tku-evidence-')
    digest=hashlib.sha256()
    for part in record['parts']:
        blob=(BUNDLE/'capture_packs'/part['file']).read_bytes()
        assert hashlib.sha256(blob).hexdigest()==part['sha256'],part['file']
        assembled.write(blob);digest.update(blob)
    assert digest.hexdigest()==record['sha256'],name
    assembled.seek(0)
    return ZipFile(assembled)


def read_bytes(path):
    if Path(path).exists():return Path(path).read_bytes()
    entry=manifest()[relative(path)]
    blob=archive(entry['archive']).read(relative(path))
    assert hashlib.sha256(blob).hexdigest()==entry['sha256'],str(path)
    return blob


def captures(directory):
    prefix=relative(directory)+'/'
    loose=set(Path(directory).glob('*.json.gz'))
    packed={BUNDLE/key for key in manifest() if key.startswith(prefix) and key.endswith('.json.gz')}
    return sorted(loose|packed)
