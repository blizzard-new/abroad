from pathlib import Path
from collections import Counter
import base64,hashlib,json,xml.etree.ElementTree as ET
import argparse
p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[3]);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
ROOT=a.repo.resolve();ORIG=ROOT/'docs/tku-acceptance-evidence/4133667';OUT=a.output.resolve();OUT.mkdir(parents=True,exist_ok=False)
RAW_CHUNK=150000;MAX_FILE=500000;SOURCE_COMMIT='14a7a459d02dc6e8495aed7139a419d4b603a87c'
def sha(data):return hashlib.sha256(data).hexdigest()
def write_json(path,value):
 path.parent.mkdir(parents=True,exist_ok=True);data=(json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n').encode();assert len(data)<MAX_FILE,(path,len(data));path.write_bytes(data);return {'path':str(path.relative_to(OUT)),'bytes':len(data),'sha256':sha(data)}
def split_bytes(data,target):
 target.mkdir(parents=True,exist_ok=True);parts=[];restored=[]
 for seq,start in enumerate(range(0,len(data),RAW_CHUNK)):
  raw=data[start:start+RAW_CHUNK];encoded=base64.b64encode(raw)+b'\n';name=f'part-{seq:04d}.b64';(target/name).write_bytes(encoded);assert len(encoded)<MAX_FILE
  recovered=base64.b64decode(encoded,validate=False);assert recovered==raw;restored.append(recovered)
  parts.append({'sequence':seq,'file':name,'offset':start,'raw_bytes':len(raw),'raw_sha256':sha(raw),'encoded_bytes':len(encoded),'encoded_sha256':sha(encoded)})
 assert b''.join(restored)==data
 return {'encoding':'base64 ASCII with one final LF','raw_chunk_bytes':RAW_CHUNK,'original_bytes':len(data),'original_sha256':sha(data),'reassembly':'sort parts by sequence, base64-decode each, concatenate bytes; verify original_bytes and original_sha256','parts':parts,'local_reassembly_byte_identical':True}
summary={'code_candidate':'4133667cfede9f3be70216795c74051adb6f3a33','original_evidence_commit':SOURCE_COMMIT,'original_files_unchanged':True,'derived_index_only':True,'all_created_files_less_than_bytes':MAX_FILE,'runs':{},'xml_splits':[]}
for kind in ['pr','push']:
 meta=json.loads((ORIG/f'remote/{kind}-artifacts.json').read_text());candidate=[];control=[];failure_count=0
 for artifact in sorted(meta['artifacts'],key=lambda a:int(a['name'].rsplit('-',1)[1])):
  shard=int(artifact['name'].rsplit('-',1)[1]);folder=ORIG/'remote/original-artifacts'/str(artifact['id'])
  for role,sub in [('candidate',folder),('main-control',folder/'main-control')]:
   original=sub/'suite.xml';data=original.read_bytes();nodes=(sub/'collect-nodeids.txt').read_text().splitlines();aliases={(n.rsplit('::',1)[0].replace('.py','').replace('/','.').replace('::','.'),n.rsplit('::',1)[1]):n for n in nodes};rows=[]
   for case in ET.fromstring(data).iter('testcase'):
    node=aliases[(case.attrib['classname'],case.attrib['name'])];failure=case.find('failure');error=case.find('error');skipped=case.find('skipped');status='failed' if failure is not None else 'error' if error is not None else 'skipped' if skipped is not None else 'passed'
    row={'node':node,'status':status,'seconds':case.attrib.get('time','0'),'shard':shard,'original_artifact_id':artifact['id']}
    if role=='candidate' and status in ['failed','error']:
     failure_count+=1;body=failure if failure is not None else error;payload={'node':node,'status':status,'original_evidence_commit':SOURCE_COMMIT,'original_xml_path':str(original.relative_to(ROOT)),'original_xml_sha256':sha(data),'classname':case.attrib['classname'],'name':case.attrib['name'],'failure_attributes':body.attrib,'failure_text':body.text or '', 'representation':'Derived verbatim XML-decoded attributes and text. Original XML bytes are preserved separately; XML entity decoding is explicit.'};body_bytes=(json.dumps(payload,ensure_ascii=False,separators=(',',':'))+'\n').encode();label=f'case-{failure_count:02d}';directory=OUT/kind/'failures';directory.mkdir(parents=True,exist_ok=True)
     info={'node':node,'status':status,'original_xml_path':payload['original_xml_path'],'original_xml_sha256':sha(data),'full_decoded_failure_bytes':len(body_bytes),'full_decoded_failure_sha256':sha(body_bytes),'message_preview':body.attrib.get('message','')[:1500],'preview_is_truncated':len(body.attrib.get('message',''))>1500,'complete_failure_payload_is_preserved':True}
     if len(body_bytes)<200000:
      file=directory/(label+'-original.json');file.write_bytes(body_bytes);info['complete_failure_file']=str(file.relative_to(OUT))
     else:
      target=directory/(label+'-original.parts');parts=split_bytes(body_bytes,target);write_json(target/'reassembly.json',parts);info['complete_failure_parts_manifest']=str((target/'reassembly.json').relative_to(OUT))
     write_json(directory/(label+'.json'),info);row['failure_reference']=str((directory/(label+'.json')).relative_to(OUT))
    rows.append(row)
   assert len(rows)==len(nodes)==len({r['node'] for r in rows}) and {r['node'] for r in rows}==set(nodes)
   write_json(OUT/kind/f'{role}-shard-{shard}-nodes.json',{'original_xml_path':str(original.relative_to(ROOT)),'original_xml_bytes':len(data),'original_xml_sha256':sha(data),'collect_nodeids_sha256':sha((sub/'collect-nodeids.txt').read_bytes()),'node_count':len(rows),'counts':dict(Counter(r['status'] for r in rows)),'nodes':rows})
   (candidate if role=='candidate' else control).extend(rows)
   if len(data)>=MAX_FILE:
    target=OUT/'xml-parts'/f'{kind}-{role}-shard-{shard}';parts=split_bytes(data,target);parts['original_evidence_commit']=SOURCE_COMMIT;parts['original_xml_path']=str(original.relative_to(ROOT));write_json(target/'reassembly.json',parts);summary['xml_splits'].append({'run':kind,'role':role,'shard':shard,'original_xml_path':parts['original_xml_path'],'original_bytes':len(data),'original_sha256':sha(data),'parts_count':len(parts['parts']),'manifest':str((target/'reassembly.json').relative_to(OUT)),'local_reassembly_byte_identical':True})
 assert len(candidate)==len({r['node'] for r in candidate})==1764 and len(control)==len({r['node'] for r in control})==62 and failure_count==31
 # Both a compact whole-run index and small groups of 100 nodes are available.
 for role,rows in [('candidate',candidate),('main-control',control)]:
  rows.sort(key=lambda r:r['node']);write_json(OUT/kind/f'{role}-all-nodes.json',{'node_count':len(rows),'counts':dict(Counter(r['status'] for r in rows)),'nodes':rows});groups=[]
  for group,start in enumerate(range(0,len(rows),100)):
   selected=rows[start:start+100];ref=write_json(OUT/kind/'node-groups'/f'{role}-{group:02d}.json',{'group':group,'start':start,'node_count':len(selected),'counts':dict(Counter(r['status'] for r in selected)),'nodes':selected});ref.update(node_count=len(selected),counts=dict(Counter(r['status'] for r in selected)));groups.append(ref)
  write_json(OUT/kind/f'{role}-groups.json',{'node_count':len(rows),'counts':dict(Counter(r['status'] for r in rows)),'canonical_nodeids_sha256':sha(('\n'.join(r['node'] for r in rows)+'\n').encode()),'groups':groups})
 summary['runs'][kind]={'candidate_nodes':len(candidate),'candidate_counts':dict(Counter(r['status'] for r in candidate)),'main_control_nodes':len(control),'main_control_counts':dict(Counter(r['status'] for r in control)),'candidate_failures':failure_count,'candidate_missing_nodes':0,'candidate_duplicate_nodes':0,'original_candidate_result_files':f'../4133667/remote/original-artifacts (result.json is unmodified)'}
write_json(OUT/'summary.json',summary)
(OUT/'reassemble.py').write_text('''"""Reassemble already-held evidence bytes; no network or third-party modules."""\nimport argparse,base64,hashlib,json\nfrom pathlib import Path\np=argparse.ArgumentParser();p.add_argument('manifest',type=Path);p.add_argument('output',type=Path);a=p.parse_args();m=json.loads(a.manifest.read_text());result=[]\nfor part in sorted(m['parts'],key=lambda r:r['sequence']):\n encoded=(a.manifest.parent/part['file']).read_bytes();assert len(encoded)==part['encoded_bytes'] and hashlib.sha256(encoded).hexdigest()==part['encoded_sha256'];raw=base64.b64decode(encoded,validate=False);assert len(raw)==part['raw_bytes'] and hashlib.sha256(raw).hexdigest()==part['raw_sha256'];result.append(raw)\ndata=b''.join(result);assert len(data)==m['original_bytes'] and hashlib.sha256(data).hexdigest()==m['original_sha256'];a.output.write_bytes(data);print(len(data),hashlib.sha256(data).hexdigest())\n''')
(OUT/'README.md').write_text('''# 4133667 小檔閱讀索引與原 bytes 分塊\n\n只處理已合法持有的原證據，不新增下載或改寫原始结果。[原固定commit 14a7a45](https://github.com/blizzard-new/abroad/tree/14a7a459d02dc6e8495aed7139a419d4b603a87c/docs/tku-acceptance-evidence/4133667/)的XML、collect、result、main-control與96MB ZIP全部不變。此資料夾每個檔案均小於500,000bytes。\n\n先讀summary.json；pr/push各有candidate-all-nodes.json（完整1764逐node，無長failure正文）、main-control-all-nodes.json（62逐node）、各shard索引與每100個node的小組。groups.json列順序、counts與SHA；各node保留原artifact ID、狀態、XML時間及失敗索引，完整列出passed/failed/skipped，不排除或改狀態。兩輪均1717P/31F/16S；PR main控制1P61F、push4P58F，不作豁免。\n\npr/failures與push/failures各31個case-NN.json可讀原message開頭1500字，明示是否截斷並連到完整原文。完整檔保存XML解碼後的原attributes/text，沒有改正文。小於200KB直接存case-NN-original.json；超大正文以原UTF8 JSON bytes分塊並附SHA/重組順序。原始XML自身保持原bytes，可獨立重組核對。\n\nxml-parts有4個超大XML（兩輪第0片candidate與main-control）；raw固定150000bytes，base64文字約200001bytes，最後一片較短。reassembly.json列原XML路徑/原SHA256、每片offset/bytes/SHA及次序。base64可避免UTF8字符切半被文字介面改寫；依sequence解碼拼回，SHA必須等於原始XML。reassemble.py只用stdlib/本地檔，無網路讀取。例如python reassemble.py xml-parts/pr-candidate-shard-0/reassembly.json /tmp/pr-original-suite.xml。\n\n這是閱讀用衍生索引與可逆原bytes表示，沒有重建或冒充原JUnit，沒有新測試或改寫舊驗收；原code candidate4133667、PR synthetic merge a8c48c3保持分開。manifest.json逐檔SHA/大小，沒有任何>500KB檔。\n''')
files=sorted(p for p in OUT.rglob('*') if p.is_file());assert all(p.stat().st_size<MAX_FILE for p in files)
manifest={'source_original_evidence_commit':SOURCE_COMMIT,'code_candidate':summary['code_candidate'],'files':[{'path':str(p.relative_to(OUT)),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in files]};write_json(OUT/'manifest.json',manifest)
print('files',len(files)+1,'bytes',sum(p.stat().st_size for p in files),'max file bytes',max(p.stat().st_size for p in files),'XML splits',len(summary['xml_splits']),'XML parts',sum(s['parts_count'] for s in summary['xml_splits']),'counts',summary['runs'])
