"""Read public PDFs for byte-hash comparison; do not alter source snapshots."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import gzip, hashlib, json, subprocess
from urllib.parse import urlsplit
import requests

sha = '358a72e7302476ba8dd19c47c35fc398fc205a47'
raw = subprocess.check_output(['git','show',sha+':sources/ncu/2026-10-11/host-web-evidence.json.gz'])
rows = [r for r in json.loads(gzip.decompress(raw)) if r['reading_status'] in ('full_native_text_reviewed','full_visual_and_native_reviewed')]
assert len(rows) == 47 and all(r.get('format') == 'pdf' for r in rows)
def check(row):
    url = row['url']; parsed = urlsplit(url)
    assert parsed.scheme in ('http','https') and not parsed.username and not parsed.password
    result = {'id':row['id'],'url':url,'expected_sha256':row['sha256'],'checked_at':datetime.now(timezone.utc).isoformat(),'reading_status':row['reading_status']}
    try:
        with requests.get(url,stream=True,timeout=(15,45),headers={'User-Agent':'Mozilla/5.0 public-source-integrity-review'}) as response:
            result.update(http_status=response.status_code,final_url=response.url,content_type=response.headers.get('Content-Type'))
            if response.status_code != 200:
                result['result']='unavailable';return result
            digest=hashlib.sha256();length=0;prefix=b''
            for chunk in response.iter_content(65536):
                length+=len(chunk)
                if length>64*1024*1024:raise ValueError('Public PDF exceeds 64MiB integrity-check bound')
                if len(prefix)<1024:prefix=(prefix+chunk)[:1024]
                digest.update(chunk)
            actual=digest.hexdigest()
            result.update(bytes=length,actual_sha256=actual,pdf_header=b'%PDF-' in prefix)
            result['result']='matched' if actual==row['sha256'] and result['pdf_header'] else 'different_or_non_pdf'
    except Exception as error:
        result.update(result='unavailable',error=str(error))
    return result
with ThreadPoolExecutor(max_workers=3) as pool:
    results=list(pool.map(check,rows))
summary={state:sum(r['result']==state for r in results) for state in ('matched','unavailable','different_or_non_pdf')}
report={'source_commit':sha,'kind':'independent live public GET / native response byte-hash comparison','bodies_retained':False,'reason':'Streamed hash only; do not overwrite dated source records with current responses or claim these receipts archive original bodies.','summary':summary,'records':results}
Path('/workspace/recovery-evidence-20261011/ncu-fourth-live-pdf-hashes.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
raise SystemExit(0 if summary['matched']==47 else 1)
