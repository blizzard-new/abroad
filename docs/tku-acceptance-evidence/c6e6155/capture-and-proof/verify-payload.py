from pathlib import Path
import json,hashlib,shutil,subprocess,zipfile,re
base=Path('/workspace/abroad-tku-evidence-c6e6155/docs/tku-acceptance-evidence');raw=base/'c6e6155';read=base/'c6e6155-readable';src=Path('/tmp/tku-ci-contract-c6e6155')
shutil.copy2('/tmp/tku-ci-12b30cd/reassemble.py',read/'reassemble.py')
out=src/'actual-reassembled';out.mkdir(exist_ok=False);reports=[]
for i,path in enumerate(sorted((read/'xml-parts').glob('*/reassembly.json'))):
    dest=out/f'{i:03d}.xml';r=subprocess.run(['python',str(read/'reassemble.py'),str(path),str(dest)],capture_output=True,text=True,check=True)
    m=json.loads(path.read_text());assert dest.read_bytes()==(raw/m['source']).read_bytes()
    reports.append({'original':m['source'],'manifest':str(path.relative_to(read)),'actual_cli_exit':r.returncode,'bytes':m['original_bytes'],'sha256':m['original_sha256'],'byte_identical':True})
assert len(reports)==len(json.loads((read/'summary.json').read_text())['xml_files'])
assert {x['original'] for x in reports}=={str(p.relative_to(raw)) for p in raw.rglob('*.xml')}
members=0
for p in (raw/'remote/original-zips').glob('*.zip'):
    with zipfile.ZipFile(p) as z:members+=sum(not n.endswith('/') for n in z.namelist())
assert members==json.loads((raw/'summary.json').read_text())['original_zip_members_byte_identical']
assert not any(re.fullmatch(r'download-\d+\.json',p.name) for p in raw.rglob('*') if p.is_file())
(read/'actual-cli-reassembly-proof.json').write_text(json.dumps({'original_zip_members':members,'all_actual_cli_reassembled_xml_byte_identical':True,'xml_count':len(reports),'reports':reports},indent=2)+'\n')
manifest=json.loads((raw/'files-manifest.json').read_text())
for x in manifest:
    p=raw/x['path'];assert p.stat().st_size==x['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256']
files=[p for p in read.rglob('*') if p.is_file()];maximum=max(p.stat().st_size for p in files);assert maximum<500000
proof={'raw_files':len(manifest)+1,'readable_files':len(files),'readable_max_bytes':maximum,'xml_count':len(reports),'original_zip_members':members}
(src/'payload-counts.json').write_text(json.dumps(proof,indent=2)+'\n');print(proof)
