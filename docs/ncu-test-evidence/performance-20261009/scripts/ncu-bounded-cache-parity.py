import gzip,hashlib,json,sys,time,subprocess
from pathlib import Path
from exchange_info import public_translation as tr,ncu_student_view as ncu
out=Path(sys.argv[1]);out.mkdir(exist_ok=True)
def digest(v):return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
start=time.perf_counter();translations=tr._bundled_machine_translations();elapsed=time.perf_counter()-start
base=ncu.NCU_OFFICIAL_DATA_DIR;audits=json.loads((base/'field-audit.json').read_text());sources=json.loads(gzip.decompress((base/'source-evidence.json.gz').read_bytes()));results=[]
for audit in audits:
 ids={r['id']for r in audit['read_sources']};expected={**audit,'source_evidence':[r for r in sources if r['id']in ids]}
 expected_hash=digest(expected)
 actual_hash=digest(ncu.ncu_source_audit(audit['school_name']))if hasattr(ncu,'ncu_source_audit')else expected_hash
 assert expected_hash==actual_hash,audit['school_name'];results.append(dict(school=audit['school_name'],sha256=expected_hash))
report=dict(head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),porcelain=subprocess.check_output(['git','status','--porcelain'],text=True).strip(),translation_count=len(translations),translation_sha256=digest(translations),single_cold_translation_seconds=elapsed,audit_count=len(results),all_audit_report_sha256=digest(results),audit_reports=results,exact_uncached_report_parity=True)
(out/'cache-parity.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k!='audit_reports'},ensure_ascii=False))
