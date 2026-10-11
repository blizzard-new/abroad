from pathlib import Path
import subprocess,json,hashlib,concurrent.futures
r=Path(__file__).parent
files=sorted(r.glob('kumamoto-brochure-*.png'))
def run(p):
 base=p.with_suffix('');subprocess.run(['tesseract',str(p),str(base),'-l','eng','--psm','3'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
 text=base.with_suffix('.txt').read_text();return {'pdf_page':int(p.stem.rsplit('-',1)[-1]),'png':p.name,'png_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'ocr_text':text,'ocr_engine':'tesseract eng psm3','manual_visual_verification_pending':True}
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(run,files))
(r/'kumamoto-ocr-pages.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');print('pages',len(rows),'chars',sum(len(x['ocr_text']) for x in rows))
