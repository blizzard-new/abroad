from pathlib import Path
import sys,json,datetime,hashlib
sys.path.insert(0,'/workspace/ntu-research-2026-10-07/scripts')
import collect_ntu as c
h=Path(__file__).parent/'collection';h.mkdir(exist_ok=True);c.ROOT=h;c.SOURCE=h/'sources';c.SOURCE.mkdir(exist_ok=True);c.LAST.clear()
ids=['998','1302','1103','1194','71','69','72','74','1307','206','313','1109','210','97','95','96','94','93','92','1']
a=c.inventory();assert len(a)==288
chosen={s['ntu_sn']:s for s in a};profiles=[]
for sn in ids:
 profiles.append(c.profile(chosen[sn]));print(sn,profiles[-1]['source'].get('http_status'),flush=True)
c.save(h/'profiles.json',profiles)
pdf=c.fetch('https://studyabroad.ntu.edu.tw/wp-content/uploads/2026/10/UBC-Factsheet-2027-2028-updated-September-2026.pdf','ntu_hosted_UBC_2027_28_factsheet');assert pdf.get('http_status')==200 and pdf['sha256']=='720e42df05035fb9c355dc698b07ee21781a0863ee484f0ffc2728a62138a8b5'
assert all(p['source'].get('http_status')==200 and p.get('parse_status')=='parsed' for p in profiles)
quota={p['ntu_sn']:(p['selection_quota_text'],p['selection_headcount_text']) for p in a if p['selection_quota_text'] not in (None,'0 名')}
assert quota=={'998':('1 名','2 名'),'1302':('2 名','4 名'),'1103':('1 名','2 名'),'1194':('1 名','2 名'),'71':('2 名','4 名'),'69':('1 名','2 名'),'72':('3 名','6 名'),'74':('2 名','4 名')},quota
assert sum(p['selection_quota_text'] is None for p in a)==274 and sum(p['selection_quota_text']=='0 名' for p in a)==6
print(json.dumps({'details':len(profiles),'quota_published':quota,'pending':274,'zero':6,'UBC_PDF_sha256':pdf['sha256']},ensure_ascii=False))
