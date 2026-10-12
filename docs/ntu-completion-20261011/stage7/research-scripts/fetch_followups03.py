from pathlib import Path
import sys,json
ROOT=Path(__file__).parent;sys.path.insert(0,str(ROOT.parent/'stage2'))
import public_fetch
public_fetch.ROOT=ROOT
from public_fetch import Fetcher
f=Fetcher();u='https://www.tufs.ac.jp/common/is/ryugakusei/www/TUFS_2027_Spring_Entry_Information_sheet.pdf';d=f.fetch(u);r={k:d.get(k) for k in ['source_id','url','checked_at','access_status','http_status','sha256','error','pdf_page_count']};r.update(portal_id='27',text_chars=len(d.get('text','')));(ROOT/'followups03-receipts.json').write_text(json.dumps([r],ensure_ascii=False,indent=2)+'\n');print(json.dumps(r,ensure_ascii=False))
