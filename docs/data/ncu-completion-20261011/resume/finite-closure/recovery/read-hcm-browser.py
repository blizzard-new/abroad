from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
from playwright.sync_api import sync_playwright
W=Path('/workspace/ncu-resume-work/finite-closure');url='https://hcmiu.edu.vn/wp-content/uploads/2018/03/F-IEX1.pdf';result={'url':url,'checked_at':datetime.now(timezone.utc).isoformat(),'method':'normal Chromium page navigation; TLS verification enabled'}
with sync_playwright()as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True);c=b.new_context(accept_downloads=True);page=c.new_page()
 try:
  with page.expect_download(timeout=30000)as d:
   try:page.goto(url,wait_until='domcontentloaded',timeout=25000)
   except Exception as e:result['navigation_error_type']=type(e).__name__
  path=W/'host-hcm-iex-2018-browser-current.pdf';d.value.save_as(path);raw=path.read_bytes();result.update(pdf=raw.startswith(b'%PDF'),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
 except Exception as e:
  result.update(error_type=type(e).__name__,final_url=page.url,title=page.title())
 b.close()
(W/'hcm-browser-receipt.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(result)
