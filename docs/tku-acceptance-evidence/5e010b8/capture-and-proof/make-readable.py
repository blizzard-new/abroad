"""Derive small read files while keeping original XML bytes recoverable."""
import argparse, base64, hashlib, json, collections, xml.etree.ElementTree as ET
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
root=a.root.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
def digest(b): return hashlib.sha256(b).hexdigest()
def write(path,obj):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def split_bytes(data,folder,source):
 folder.mkdir(parents=True,exist_ok=True);parts=[];rejoined=b''
 for i,start in enumerate(range(0,len(data),150000)):
  chunk=data[start:start+150000];name=f'{i:04d}.b64';encoded=base64.b64encode(chunk)
  (folder/name).write_bytes(encoded+b'\n');assert base64.b64decode(encoded)==chunk;rejoined+=base64.b64decode(encoded)
  parts.append({'path':name,'offset':start,'bytes':len(chunk),'sha256':digest(chunk)})
 assert rejoined==data
 write(folder/'reassembly.json',{'source':source,'original_bytes':len(data),'original_sha256':digest(data),'parts':parts,'actual_reassembly_byte_identical':True})
 return str((folder/'reassembly.json').relative_to(out))
index=[]
for raw in sorted(root.rglob('*.xml')):
 data=raw.read_bytes()
 try: tree=ET.fromstring(data)
 except ET.ParseError: continue
 cases=list(tree.iter('testcase'))
 if not cases: continue
 relative=str(raw.relative_to(root));label=relative.replace('/','__').replace('.xml','')
 xml_manifest=split_bytes(data,out/'xml-parts'/label,relative)
 rows=[]
 for i,case in enumerate(cases):
  status='passed';failure=None
  for tag in ['error','failure','skipped']:
   child=case.find(tag)
   if child is not None:status=tag;failure=child;break
  row={'id':case.get('classname','')+'::'+case.get('name',''),'status':status,'seconds':case.get('time')}
  if status in ['error','failure']:
   payload={'original_xml_path':relative,'original_xml_sha256':digest(data),'case_attributes':case.attrib,'failure_tag':failure.tag,'failure_attributes':failure.attrib,'full_text':failure.text or ''}
   content=(json.dumps(payload,ensure_ascii=False,indent=2)+'\n').encode()
   dest=out/'failures'/label/f'{i:04d}.json'
   if len(content)<=200000:
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(content);row['failure_file']=str(dest.relative_to(out))
   else:row['failure_reassembly']=split_bytes(content,out/'failure-parts'/label/f'{i:04d}',f'derived full failure JSON from {relative} testcase {i}')
  rows.append(row)
 group_files=[]
 for i,start in enumerate(range(0,len(rows),100)):
  dest=out/'nodes'/label/f'{i:03d}.json';write(dest,rows[start:start+100]);group_files.append(str(dest.relative_to(out)))
 counts=dict(collections.Counter(r['status'] for r in rows));write(out/'nodes'/label/'index.json',{'raw_xml':relative,'raw_xml_sha256':digest(data),'counts':counts,'node_count':len(rows),'groups':group_files,'original_xml_reassembly':xml_manifest})
 index.append({'raw_xml':relative,'counts':counts,'node_count':len(rows),'index':str((out/'nodes'/label/'index.json').relative_to(out))})
write(out/'summary.json',{'originals_preserved':True,'original_xml_reconstruction':False,'xml_files':index,'chunk_bytes':150000,'limitation':'Indexes and extracted failure JSON are derived; original XML remains untouched and its byte-exact base64 reassembly is verified. Each result is bound to its own raw run metadata; no relabeling.'})
files=[q for q in out.rglob('*') if q.is_file()];maximum=max(q.stat().st_size for q in files);assert maximum<500000
print(json.dumps({'readable_files':len(files),'maximum_bytes':maximum,'all_files_under_500KB':True,'xmls':len(index)}))
