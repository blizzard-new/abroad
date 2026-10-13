"""Losslessly package only new TKU captures; original bundles stay untouched."""
import hashlib
import argparse
import json
from pathlib import Path
from zipfile import ZipFile,ZipInfo,ZIP_DEFLATED

ROOT=Path(__file__).resolve().parents[1]
B=ROOT/'src/exchange_info/official_data/tku'
FOLDERS=['census_sources','host_census_sources','campus_source_candidates','commons_campus_candidates','asset_batch_sources','asset_source_retries']


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--folders',nargs='+',choices=FOLDERS,default=FOLDERS)
    folders=parser.parse_args().folders
    target=B/'capture_packs';target.mkdir(exist_ok=True)
    manifest=B/'capture_pack_manifest.json'
    previous=json.loads(manifest.read_text()) if manifest.exists() else {'files':{},'archives':[]}
    entries=dict(previous['files']);packs=list(previous['archives'])
    groups=[];group=[];size=0
    for path in sorted(p for folder in folders if (B/folder).exists() for p in (B/folder).iterdir() if p.is_file() and p.name!='.gitignore'):
        key=path.relative_to(B).as_posix()
        if key in entries:
            assert hashlib.sha256(path.read_bytes()).hexdigest()==entries[key]['sha256'],f'Historic capture changed: {key}'
            continue
        if group and size+path.stat().st_size>24*1024*1024:
            groups.append(group);group=[];size=0
        group.append(path);size+=path.stat().st_size
    if group:groups.append(group)
    first=len(packs)
    for number,group in enumerate(groups,start=first):
        name=f'tku-public-captures-{number:03}.zip';path=target/name
        with ZipFile(path,'w',compression=ZIP_DEFLATED,compresslevel=6) as package:
            for file in group:
                key=file.relative_to(B).as_posix();blob=file.read_bytes()
                info=ZipInfo(key,date_time=(2026,10,11,0,0,0));info.compress_type=ZIP_DEFLATED;info.external_attr=0o100644<<16
                package.writestr(info,blob)
                entries[key]=dict(archive=name,bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest())
        parts=[]
        with path.open('rb') as stream:
            for piece in range(100):
                blob=stream.read(9*1024*1024)
                if not blob:break
                part_name=name+f'.{piece:03}';(target/part_name).write_bytes(blob)
                parts.append(dict(file=part_name,bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest()))
        packs.append(dict(file=name,bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),members=len(group),parts=parts))
    result=dict(checked_date='2026-10-11',format='ZIP; exact original capture bytes, deterministic member timestamps',
        original_loose_files_preserved_locally=True,files=entries,archives=packs)
    manifest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    (target/'.gitignore').write_text('# Logical ZIP files are delivered as ordered transport-safe parts.\n*.zip\n')
    for folder in FOLDERS:
        if not (B/folder).exists():continue
        if folder=='asset_source_retries':
            (B/folder/'.gitignore').write_text('# Binary public attachments are retained losslessly in capture_packs.\n*.pdf\n*.docx\n*.doc\n*.xlsx\n')
        else:
            (B/folder/'.gitignore').write_text('# Raw refresh cache; exact bytes are retained in capture_packs with SHA256.\n*\n!.gitignore\n')
    print(json.dumps(dict(files=len(entries),archives=len(packs),new_archives=len(packs)-first,archive_bytes=sum(p['bytes'] for p in packs))))


if __name__=='__main__':main()
