from pathlib import Path
import gzip,hashlib,json,subprocess,time
from exchange_info import ncu_student_view as ncu
root=Path.cwd();result={'sha':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'files':[]}
def digest(rows):
 h=hashlib.sha256();count=0
 for row in rows:
  blob=json.dumps(row,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode();h.update(str(len(blob)).encode()+b':'+blob);count+=1
 return count,h.hexdigest()
for name in ('field-audit.json','source-evidence.json.gz'):
 p=ncu.NCU_OFFICIAL_DATA_DIR/name;raw=p.read_bytes();legacy=json.loads(gzip.decompress(raw) if name.endswith('.gz') else raw)
 a=digest(legacy);start=time.monotonic();b=digest(ncu._iter_audit_rows(p));assert a==b
 result['files'].append({'file':name,'file_sha256':hashlib.sha256(raw).hexdigest(),'all_records':a[0],'canonical_full_payload_sha256':a[1],'identical_to_original_full_decode':True,'stream_seconds':time.monotonic()-start})
 if name=='field-audit.json':audits=legacy
 else:sources=legacy
selected=[audits[0],audits[-1],max(audits,key=lambda r:len(json.dumps(r))),next(r for r in audits if '誠信' in r['school_name'])]
for row in selected:
 expected={**row,'source_evidence':[s for s in sources if s['id'] in {i['id'] for i in row['read_sources']}]}
 assert ncu.ncu_source_audit(row['school_name'])==expected,row['school_name']
result['exact_api_helper_payload_comparisons']=[r['school_name'] for r in selected]
result['cache_bytes']=ncu._audit_cache_bytes
assert ncu._audit_cache_bytes<=ncu._AUDIT_CACHE_BYTES
out=Path('/workspace/recovery-evidence-20261011/ntu3-ncu-streamed-payload-parity.json');out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
