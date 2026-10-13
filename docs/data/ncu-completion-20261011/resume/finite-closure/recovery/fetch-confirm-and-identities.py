from pathlib import Path
import sys,json,gzip,hashlib
from bs4 import BeautifulSoup
sys.path.insert(0,'/workspace/ncu-resume-work');from collect_visual_candidates import fetch
R=Path('/workspace/abroad');W=Path('/workspace/ncu-resume-work/finite-closure')
form=BeautifulSoup((W/'host-tuaf-newhandbook.pdf').read_bytes(),'html.parser').find('form',id='download-form');assert form['action']=='https://drive.usercontent.google.com/download';params={i['name']:i['value']for i in form.select('input[name]')};raw=fetch(form['action'],W/'host-tuaf-newhandbook-confirmed.pdf',params=params);print({'source_id':'host-tuaf-newhandbook','pdf':bool(raw and raw.startswith(b'%PDF')),'sha256':hashlib.sha256(raw).hexdigest()if raw else None},flush=True)
ss={s['id']:s for s in json.load(gzip.open(R/'src/exchange_info/official_data/ncu/source-evidence.json.gz'))}
for sid in ['1wBS543cWlwXllG7O_07PAcEUBODZkfna','1cWQi5Dl3m374SttYuL6C0IZ0_sALdB50']:
 s=ss[sid];raw=fetch(s.get('download_url',s['url']),W/(sid+'.pdf'));print({'source_id':sid,'pdf':bool(raw and raw.startswith(b'%PDF')),'sha256':hashlib.sha256(raw).hexdigest()if raw else None,'unchanged':bool(raw and hashlib.sha256(raw).hexdigest()==s['sha256'])},flush=True)
