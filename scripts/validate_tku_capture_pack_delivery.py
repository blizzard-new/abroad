"""Verify every TKU capture using committed transport parts, without loose caches."""
import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from datetime import datetime,timezone
from pathlib import Path
import tku_capture_io as capture_io


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--baseline',default='88bd00531d9a77fb98ba54dbfd8786cbde18db96')
    ap.add_argument('--output',default='/tmp/tku-milestone3-pack-only.json')
    args=ap.parse_args()
    original=capture_io.BUNDLE;root=original.parents[3]
    manifest=json.loads((original/'capture_pack_manifest.json').read_text())
    previous=json.loads(subprocess.check_output(['git','show',args.baseline+':src/exchange_info/official_data/tku/capture_pack_manifest.json'],cwd=root))
    assert all(manifest['files'][key]==entry for key,entry in previous['files'].items())
    assert manifest['archives'][:len(previous['archives'])]==previous['archives']
    restored=0;archives=[];parts=0
    with tempfile.TemporaryDirectory(prefix='tku-pack-only-') as directory:
        target=Path(directory);(target/'capture_packs').mkdir()
        shutil.copy2(original/'capture_pack_manifest.json',target/'capture_pack_manifest.json')
        for archive in manifest['archives']:
            for part in archive['parts']:
                blob=(original/'capture_packs'/part['file']).read_bytes()
                assert len(blob)==part['bytes'] and hashlib.sha256(blob).hexdigest()==part['sha256']
                (target/'capture_packs'/part['file']).write_bytes(blob);parts+=1
        capture_io.BUNDLE=target;capture_io.pack_manifest.cache_clear();capture_io.archive.cache_clear()
        try:
            for key,entry in manifest['files'].items():
                assert not (target/key).exists(), 'Loose cache present in pack-only validation'
                blob=capture_io.read_bytes(target/key)
                assert len(blob)==entry['bytes'] and hashlib.sha256(blob).hexdigest()==entry['sha256'],key
                restored+=len(blob)
            for archive in manifest['archives']:
                package=capture_io.archive(archive['file'])
                assert len(package.namelist())==archive['members'];archives.append(package)
        finally:
            for package in archives:package.close()
            capture_io.archive.cache_clear();capture_io.pack_manifest.cache_clear();capture_io.BUNDLE=original
    result=dict(status='passed',checked_at=datetime.now(timezone.utc).isoformat(),mode='Only copied manifest and transport parts; no logical ZIP or loose capture files available',files=len(manifest['files']),archives=len(manifest['archives']),parts=parts,restored_bytes=restored,baseline=args.baseline,prior_files=len(previous['files']),prior_archives=len(previous['archives']),prior_files_and_archives_immutable=True,new_files=len(manifest['files'])-len(previous['files']))
    Path(args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
