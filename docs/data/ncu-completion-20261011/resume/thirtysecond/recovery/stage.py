from pathlib import Path
from datetime import datetime,timezone
import json,gzip,hashlib,base64,shutil,copy,subprocess
R=Path('/workspace/abroad');W=Path('/workspace/ncu-resume-work/thirtysecond');B=R/'sources/ncu/2026-10-08';S=R/'sources/ncu/2026-10-11';D=R/'docs/data/ncu-completion-20261011/resume/thirtysecond';BASE='6240363d8e8c585eca13b8acec2b59344c0f3bc6'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()==BASE
D.mkdir(exist_ok=True);(D/'source-pages').mkdir(exist_ok=True);now=datetime.now(timezone.utc).isoformat()
def js(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def gz(p,x):p.write_bytes(gzip.compress(json.dumps(x,ensure_ascii=False).encode(),mtime=0))
packs={p:json.load(gzip.open(B/p))for p in ['drive-evidence.json.gz','host-web-evidence.json.gz']};byid={s['id']:s for pack in packs.values()for s in pack};receipts={r['source_id']:r for r in json.load(open(W/'fetch-receipts.json'))};notes=json.load(open(W/'reading-notes.json'))
rows={'host-ensea-appform':'ncu-008','host-chuo-next-02':'ncu-128','1AML0E9CXUoPyoVyhc05Wpj653l1mrkfT':'ncu-101','1AdVkwhgEY3gs_o9SnS1uXCWXKGMIFQuP':'ncu-083','18V9vNjSgs4HCh9YSLlzmQYs_qXvLn9yK':'ncu-132'}
ledger=[];responses=[]
for n in notes:
 sid=n['source_id'];s=byid[sid];pages=[p['page']for p in s['pages']];assert pages==n['native_pages_read']==n['visual_pages_read'];raw=(W/(sid+'.pdf')).read_bytes();assert hashlib.sha256(raw).hexdigest()==s['sha256']==n['sha256']==receipts[sid]['sha256'];renders=[]
 for page in pages:
  p=W/f'{sid}-p{page:02}.png';q=D/'source-pages'/p.name;shutil.copy2(p,q);renders.append({'pdf_page':page,'path':str(q.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 s['reading_status']='full_visual_and_native_reviewed';s['reading_review']={'source_sha256':s['sha256'],'pages_reviewed':pages,'full_document_read':True,'reviewed_at':now,'review_note':'第三十二批原生全文及原圖逐頁核讀；歷史版本、學院與國別獨立辨識。'}
 s['visual_review']={'source_sha256':s['sha256'],'pdf_pages_reviewed':pages,'full_document_read':True,'reviewed_at':now,'method':'原生全文加逐頁view_image人工核讀，非OCR','rendered_pages':renders,'page_notes_zh':{str(i):v for i,v in n['page_notes']}}
 s['reuse_license_note']='官方公開原件作來源查核；未取得頁內照片獨立授權，不轉作校景。'
 s['source_read_scope_note_zh']='第三十二批已全物理頁核讀；'+n['document_year_scope']+'；不代表中央116核准、名額或全部外鏈已讀。'
 js(B/f'{sid}-visual-review.json',s['visual_review'])
 ledger.append({'source_id':sid,'row_id':rows[sid],'source_url':s['url'],'source_sha256':s['sha256'],'retrieved_at':receipts[sid]['receipt']['checked_at'],'reviewed_at':now,'document_year_scope':n['document_year_scope'],'pages_reviewed':pages,'native_full_read':True,'visual_full_read':True,'current_116_approval':False,'page_notes_zh':n['page_notes'],'native_text_limitations':n.get('native_text_limitations'),'license_scope':s['reuse_license_note'],'rendered_pages':renders})
 responses.append({'source_id':sid,'receipt':receipts[sid]['receipt'],'encoding':'base64','body':base64.b64encode(raw).decode()})
# Keep original year quarantines; add only verified visual passages. ENSEA native extraction misorders study plan into KA171.
selections={
'host-ensea-appform':[(4,'To be included in your application: For all students: A copy of your passport or identity card (for European citizens). A curriculum vitae. Study Plan Form (to download from the website). For Erasmus students: a copy of the learning agreement. Transcript of records with the university International Relations stamp (latest year of study).')],
'host-chuo-next-02':[(1,'List of Partner Institutions of Chuo University -Student Exchange Agreement- (As of July 2026)'),(3,'Taiwan: National Central University （国立中央大学）')],
'18V9vNjSgs4HCh9YSLlzmQYs_qXvLn9yK':[(4,'OMU exchange program for the Fall 2025 Semester Check Sheet. Certificate of English Proficiency: Please submit if you have one. Please have the person in charge of the university submit the application documents by email or cloud storage. Applications from individual students cannot be accepted. Please do NOT convert Word or Excel to PDF when submitting. Submission of the original documents is not required.')]
}
for sid,ps in selections.items():
 s=byid[sid];v=s['visual_review'];v['page_transcriptions']=[{'page':p,'text':t,'note_zh':next(n['document_year_scope']for n in notes if n['source_id']==sid)+'；同SHA原圖選定原文，不是中央116核准。'}for p,t in ps];v['include_native_with_selected_passages']=sid!='host-ensea-appform';js(B/f'{sid}-visual-review.json',v)
 p=B/f'{sid}-index-review.json'
 if sid=='host-ensea-appform':policy={'source_sha256':s['sha256'],'quarantined_pdf_pages':[4],'isolation_note_zh':'原生p4把Study Plan排序到KA171清單後，原圖其實屬For all students；原生抽取保留稽核，問答只用人工選定原文。空白表未標學年，不替代2026–27或中央116。'}
 else:
  policy=json.load(open(p));assert policy['source_sha256']==s['sha256'];policy['review_update_zh']='第三十二批已逐頁視讀全件，原年度隔離仍保留。'
  if sid.startswith('18V'):policy['isolation_note_zh']='2025秋N2、期限、校區及格式只供歷史參考，不替代2027春或中央116。第4頁日文字型抽取錯乱，本批已原圖全讀，錯乱原生不直接供問答。'
 js(p,policy)
for p,pack in packs.items():gz(B/p,pack)
gz(S/'resume-thirtysecond-original-responses.json.gz',responses);js(D/'fresh-fetch-receipts.json',list(receipts.values()));js(D/'reading-ledger.json',{'checked_at':now,'base_sha':BASE,'items':ledger})
base=json.load(open(B/'reviewed-host-records.json'));rs=json.load(open(S/'reviewed-host-records.json'));changes=[]
limit='中央116名額、方案與實際接收未核；不同年度及學院條件分開，未啟用期限提醒。'
def field(rid,key,point,refs):
 if rid not in rs:rs[rid]=copy.deepcopy(base[rid])
 r=rs[rid];old=copy.deepcopy(r['fields'].get(key,base.get(rid,{}).get('fields',{}).get(key)));assert old
 value={**old,'points':old['points']+[point],'sources':list(old['sources']),'unresolved':old.get('unresolved','')+'；'+limit}
 for sid,pg in refs:
  for page in pg:
   ref={'id':sid,'page':page}
   if ref not in value['sources']:value['sources'].append(ref)
 r['fields'][key]=value;r['checked_at']=now;r['applicability']+='；第三十二批原件全讀。'+limit;changes.append({'row_id':rid,'field':key,'previous':old,'updated':value})
field('ncu-128','eligibility','2026年7月交換協議名單第3頁在University Wide Agreement的Taiwan欄列National Central University／國立中央大學；第1頁臺大及台北大法學院是別的院級條目。這只確認協議列名，不提供中央116名額或本人錄取保證。',[('host-chuo-next-02',[1,3])])
field('ncu-083','language','2026–27資料表泛稱Natural／Technical Sciences可能要語言文件，較新學院網頁則明列必上傳或報名收據及補交規則；依工程學院具體規定核對，不能用舊表may取消既有要求。舊表83／6.5不包含新TOEFL量表。',[('1AdVkwhgEY3gs_o9SnS1uXCWXKGMIFQuP',[3])])
field('ncu-083','courses','2026–27資料表列全時每學期30 ECTS；一般一學院、多數一系選课，工程學院前述20＋10 ECTS例外另依其規則。丹麥02為及格、有pass/fail課；學生自行線上下載官方PDF成績，不假定校方自動寄送。',[('1AdVkwhgEY3gs_o9SnS1uXCWXKGMIFQuP',[3])])
js(S/'reviewed-host-records.json',rs);js(D/'field-reconciliation.json',changes);js(D/'added-host-records.json',{rid:rs.get(rid,base.get(rid))for rid in sorted(set(rows.values()))})
names={'ncu-008':('France','ENSEA／Cergy'),'ncu-128':('Japan','Chuo University'),'ncu-101':('Canada','University of Manitoba／Winnipeg'),'ncu-083':('Denmark','Aarhus University'),'ncu-132':('Japan','Osaka Metropolitan University')}
js(D/'identity-review.json',[{'row_id':rid,'source_ids':[s for s,r in rows.items()if r==rid],'country':names[rid][0],'school':names[rid][1],'verification':'原件校名、國別、官方域名或母校公開原件來源逐一對應，非相似校名自動匹配。Manitoba原件清楚寫Winnipeg Canada，未套Neubrandenburg。'}for rid in sorted(set(rows.values()))])
print({'documents':5,'pages':21,'updated_fields':len(changes),'sources_with_full_reading':5,'new_manual_hosts':0})
