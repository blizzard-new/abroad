"""Losslessly package only new TKU captures; original bundles stay untouched."""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile,ZipInfo,ZIP_DEFLATED

ROOT=Path(__file__).resolve().parents[1]
B=ROOT/'src/exchange_info/official_data/tku'
FOLDERS=['census_sources','host_census_sources','campus_source_candidates','commons_campus_candidates']


def main():
    target=B/'capture_packs';target.mkdir(exist_ok=True)
    groups=[];group=[];size=0
    for path in sorted(p for folder in FOLDERS for p in (B/folder).iterdir() if p.is_file() and p.name!='.gitignore'):
        if group and size+path.stat().st_size>24*1024*1024:
            groups.append(group);group=[];size=0
        group.append(path);size+=path.stat().st_size
    if group:groups.append(group)
    entries={};packs=[]
    for number,group in enumerate(groups):
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
    (B/'capture_pack_manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    (target/'.gitignore').write_text('# Logical ZIP files are delivered as ordered transport-safe parts.\n*.zip\n')
    for folder in FOLDERS:
        (B/folder/'.gitignore').write_text('# Raw refresh cache; exact bytes are retained in capture_packs with SHA256.\n*\n!.gitignore\n')
    print(json.dumps(dict(files=len(entries),archives=len(packs),archive_bytes=sum(p['bytes'] for p in packs))))


if __name__=='__main__':main()
