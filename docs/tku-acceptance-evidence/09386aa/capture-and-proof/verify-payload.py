from pathlib import Path
import json,hashlib,shutil,subprocess,zipfile
base=Path('/workspace/abroad-tku-evidence-09386aa/docs/tku-acceptance-evidence')
raw=base/'09386aa';read=base/'09386aa-readable';src=Path('/tmp/tku-ci-09386aa')
for name in ['capture-runtime.py','verify-payload.py']:
    shutil.copy2(src/name,raw/'capture-and-proof'/name)
shutil.copy2('/tmp/tku-ci-5e010b8/download-original.py',raw/'capture-and-proof/download-original.py')
shutil.copy2('/tmp/tku-ci-12b30cd/reassemble.py',read/'reassemble.py')
proof=[]
out=src/'actual-reassembled';out.mkdir(exist_ok=True)
for i,manifest in enumerate(sorted((read/'xml-parts').glob('*/reassembly.json'))):
    dest=out/f'{i:03d}.xml'
    result=subprocess.run(['python',str(read/'reassemble.py'),str(manifest),str(dest)],capture_output=True,text=True,check=True)
    meta=json.loads(manifest.read_text());assert dest.read_bytes()==(raw/meta['source']).read_bytes()
    proof.append({'original':meta['source'],'manifest':str(manifest.relative_to(read)),'actual_cli_exit':result.returncode,'bytes':len(dest.read_bytes()),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'original_byte_identical':True})
member_count=0
for p in (raw/'remote/original-zips').glob('*.zip'):
    with zipfile.ZipFile(p) as z: member_count+=sum(not n.endswith('/') for n in z.namelist())
expected_xmls=len(json.loads((read/'summary.json').read_text())['xml_files'])
assert len(proof)==expected_xmls==29 and member_count==152
(read/'actual-cli-reassembly-proof.json').write_text(json.dumps({'all_original_xmls_byte_identical':True,'xml_count':len(proof),'original_zip_member_count':member_count,'reports':proof},indent=2)+'\n')
manifest=[]
for p in sorted(raw.rglob('*')):
    if p.is_file() and p.name!='files-manifest.json':manifest.append({'path':str(p.relative_to(raw)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(raw/'files-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
files=[p for p in read.rglob('*') if p.is_file()];maximum=max(p.stat().st_size for p in files);assert maximum<500000
print({'original_zip_member_count':member_count,'xmls_actual_cli_reassembled':len(proof),'raw_files':len(manifest)+1,'readable_files':len(files),'max_readable_bytes':maximum})
