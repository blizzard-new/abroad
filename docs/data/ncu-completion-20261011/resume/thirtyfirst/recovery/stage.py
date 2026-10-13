from pathlib import Path
from datetime import datetime,timezone
import json,gzip,hashlib,base64,shutil,copy,subprocess,zipfile,xml.etree.ElementTree as ET
R=Path('/workspace/abroad');W=Path('/workspace/ncu-resume-work/thirtyfirst');B=R/'sources/ncu/2026-10-08';S=R/'sources/ncu/2026-10-11';D=R/'docs/data/ncu-completion-20261011/resume/thirtyfirst';BASE='d6e2238684faa4ef320e87d4b0165e40f5edb8f5'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()==BASE
D.mkdir(exist_ok=True);(D/'source-pages').mkdir(exist_ok=True);now=datetime.now(timezone.utc).isoformat()
def js(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def gz(p,x):p.write_bytes(gzip.compress(json.dumps(x,ensure_ascii=False).encode(),mtime=0))
pack=json.load(gzip.open(B/'host-web-evidence.json.gz'));byid={s['id']:s for s in pack};receipts={s['source_id']:s for s in json.load(open(W/'fetch-receipts.json'))};notes=json.load(open(W/'reading-notes.json'));ledger=[];rawpack=[]
rows={n['source_id']:'ncu-098'if n['source_id']=='host-sdu-id'else'ncu-124'if'toyama'in n['source_id']else'ncu-126'for n in notes}
for n in notes:
 sid=n['source_id'];s=byid[sid];fmt='xlsx'if sid=='host-sdu-id'else'pdf';raw=(W/(sid+'.'+fmt)).read_bytes();assert hashlib.sha256(raw).hexdigest()==s['sha256']==n['sha256']==receipts[sid]['sha256'];renders=[]
 if fmt=='pdf':
  pages=n['native_pages_read'];assert pages==n['visual_pages_read']==[p['page']for p in s['pages']]
  for page in pages:
   p=W/f'{sid}-p{page:02}.png';q=D/'source-pages'/p.name;shutil.copy2(p,q);renders.append({'pdf_page':page,'path':str(q.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
  s['reading_status']='full_visual_and_native_reviewed';s['reading_review']={'source_sha256':s['sha256'],'pages_reviewed':pages,'full_document_read':True,'reviewed_at':now,'review_note':'第三十一批全物理頁原生與逐頁原圖核讀；Spring2027、一般未年及全校學部清單範圍分開。'}
  s['visual_review']={'source_sha256':s['sha256'],'pdf_pages_reviewed':pages,'full_document_read':True,'reviewed_at':now,'method':'原生全文與逐頁view_image人工核讀，非OCR','rendered_pages':renders,'page_notes_zh':{str(i):t for i,t in n['page_notes']}}
  js(B/f'{sid}-visual-review.json',s['visual_review'])
  s['source_read_scope_note_zh']='第三十一批已全物理頁核讀；'+n['document_year_scope']+'。未核中央116名額或實際接收，不以全讀代替當期核准。'
 else:
  pages=[];s['reading_status']='full_native_sheets_reviewed';s['reading_review']={'source_sha256':s['sha256'],'sheets_reviewed':n['native_sheets_read'],'full_document_read':True,'reviewed_at':now,'review_note':n['note_zh'],'blank_sheets_reviewed':n['blank_sheets']}
  ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
  with zipfile.ZipFile(W/(sid+'.xlsx'))as z:
   assert not any('/media/'in v for v in z.namelist());ss=[''.join(x.itertext())for x in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si',ns)];allcells={}
   for i,name in enumerate(n['native_sheets_read'],1):
    root=ET.fromstring(z.read(f'xl/worksheets/sheet{i}.xml'));cells=[]
    for c in root.findall('.//s:c',ns):
     assert c.find('s:f',ns)is None and c.find('s:is',ns)is None
     v=c.find('s:v',ns)
     if v is not None:cells.append({'cell':c.get('r'),'text':ss[int(v.text)]if c.get('t')=='s'else v.text})
    allcells[name]=cells
   assert len(allcells['Sayfa1'])==14 and not allcells['Sayfa2']and not allcells['Sayfa3']
   js(D/'sdu-blank-workbook-cells.json',{'source_sha256':s['sha256'],'sheets':allcells,'media_count':0,'visual_layout_reviewed':False})
 s['reuse_license_note']='官方公開文字／空白原件供查核，未取得頁內圖像独立開放授權，不轉作校園照片。'
 ledger.append({'source_id':sid,'row_id':rows[sid],'source_url':s['url'],'source_sha256':s['sha256'],'retrieved_at':receipts[sid]['receipt']['checked_at'],'reviewed_at':now,'document_year_scope':n['document_year_scope'],'format':fmt,'pages_reviewed':pages,'sheets_reviewed':n.get('native_sheets_read',[]),'native_full_read':True,'visual_full_read':fmt=='pdf','current_116_approval':False,'page_notes_zh':n.get('page_notes',[]),'sheet_note_zh':n.get('note_zh'),'rendered_pages':renders,'license_scope':s['reuse_license_note']})
 rawpack.append({'source_id':sid,'receipt':receipts[sid]['receipt'],'encoding':'base64','body':base64.b64encode(raw).decode()})
gz(B/'host-web-evidence.json.gz',pack);gz(S/'resume-thirtyfirst-original-responses.json.gz',rawpack);js(D/'reading-ledger.json',{'checked_at':now,'base_sha':BASE,'items':ledger});js(D/'fresh-fetch-receipts.json',list(receipts.values()))
# Preserve year-based index quarantine. Same-page selected original excerpts remain explicitly scoped.
selected={
'host-shizuoka-next-02':[(1,'Exchange Program Information for Spring 2027. Although this is not an official application requirement, it is necessary to understand the course content and complete assignments.'),(2,'Please note that requests to change your academic advisor or assigned faculty cannot be accepted.'),(3,'Academic transcripts will be issued only if requested by the student.'),(4,'Each unit consists of five private rooms, with shared dining, kitchen, shower, and toilet facilities.')],
'host-shizuoka-next-03':[(1,'静岡大学 2027 年度春学期 交換留学プログラム'),(2,'指導教員と相談してください。'),(3,'月額生活費：約100,000 円～ （滞在費を含む）')],
'host-shizuoka-next-04':[(1,'Faculty of Informatics: Hamamatsu. Faculty of Science: Shizuoka.'),(2,'Department of Informatics: Hamamatsu. Department of Science: Shizuoka. Department of Engineering: Hamamatsu. Department of Agriculture: Shizuoka.'),(3,'Graduate School of Science and Technology, Research Division: Hamamatsu/Shizuoka.')]
}
# English campus rows are visual cell-pair transcriptions, not fabricated course availability.
for sid,parts in selected.items():
 s=byid[sid];review=s['visual_review'];review['page_transcriptions']=[{'page':page,'text':text,'note_zh':'同SHA同物理頁人工摘錄；'+next(n['document_year_scope']for n in notes if n['source_id']==sid)+'，不是中央116接收／名額。'}for page,text in parts];review['include_native_with_selected_passages']=True;js(B/f'{sid}-visual-review.json',review)
 # Explicit applicability notes are added without unquarantining the original whole pages.
 p=B/f'{sid}-index-review.json'
 if p.exists():
  policy=json.load(open(p));assert policy['source_sha256']==s['sha256'];policy['page_applicability_notes_zh']={str(page):'僅限'+next(n['document_year_scope']for n in notes if n['source_id']==sid)+'；完整閱讀不代表中央116資格或名額核准。'for page,_ in parts};js(p,policy)
# Review data above is saved in sidecars; rebuild attaches SHA-bound excerpts.
base=json.load(open(B/'reviewed-host-records.json'));records=json.load(open(S/'reviewed-host-records.json'));changes=[];limit='中央116學院、名額及實際交換適用未核，依原件年份參考，不啟用期限提醒。'
for rid in set(rows.values()):
 if rid not in records:records[rid]=copy.deepcopy(base[rid])
 records[rid]['checked_at']=now;records[rid]['applicability']+='；第三十一批既有原件全讀，校級／院級及年份分開。'+limit
 for sid,r in rows.items():
  if r==rid and sid not in records[rid]['source_ids']:records[rid]['source_ids'].append(sid)
def field(rid,key,point,refs):
 r=records[rid];old=copy.deepcopy(r['fields'].get(key,base.get(rid,{}).get('fields',{}).get(key)));assert old
 v={**old,'points':old['points']+[point],'sources':list(old['sources']),'unresolved':(old.get('unresolved')or'')+'；'+limit}
 for sid,pg in refs:
  for page in pg:
   ref={'id':sid,'page':page}
   if ref not in v['sources']:v['sources'].append(ref)
 r['fields'][key]=v;changes.append({'row_id':rid,'field':key,'previous':old,'updated':v})
field('ncu-124','host_documents','一般校級原件明列推薦函由派遣校校長或系主任撰寫，載姓名、所屬及派遣期間；財力表另附收入／餘額及存摺全頁。這些是本原件的格式說明，不能自動當院級協議或116新版必繳；COE初次先交仍不是錄取通知。',[('host-toyama-inbound-en-pdf',[1,2])])
field('ncu-124','housing','一般指引明寫高岡校區沒有International House；只表示没有該類校方國際宿舍，不等於高岡沒有任何可租住所。五福／杉谷申宿在錄取後由母校轉知，沒有保證每人獲房。',[('host-toyama-inbound-en-pdf',[2])])
field('ncu-126','city','20260225學部位置表全讀：本科情報／工學在濱松，人文社科／教育／理／農／全球共創在靜岡；綜合研究科情報及工在濱松、理及農在靜岡。光醫在濱松，自然科學教育與研究部跨兩地。這是全校位置清單，不代表各系皆接收中央交換；實際校區依接收學部核對。',[('host-shizuoka-next-04',[1,2,3])])
field('ncu-126','courses','Spring2027方案的修士接收範圍列人文社科、綜合科學技術及山岳流域三研究科；全校位置清單另有教育、光醫等，不能把名錄當全都開放交換。成績單只在學生提出申請時發行，不假定自動寄送；母校學分承認須出發前確認。',[('host-shizuoka-next-02',[1,3]),('host-shizuoka-next-04',[2])])
field('ncu-126','cost','Spring2027日文版明寫每月約100000日圓起包含滯在費；英文版只概述每月生活費。不能把住宿再次全額加進同一估值當校方合計；仍須依房型和個人列預算，不推成116保證夠用。',[('host-shizuoka-next-03',[3]),('host-shizuoka-next-02',[3])])
field('ncu-126','housing','英日資料表說通常五個獨立單人房組成一個unit，共用餐廳、廚房、淋浴與廁所；不是五人同住一間房。優先安排與多數入住不等於保證床位，錄取後才提供申宿說明。',[('host-shizuoka-next-02',[4]),('host-shizuoka-next-03',[3])])
field('ncu-098','host_documents','學生證工作簿三張表已逐格核對：第一張是空白13欄資料表，其餘兩張空表；父母姓名欄不是額外父母證明件。表本身沒有簽名、照片、費用或截止欄，不據空表新增116件數或當期送件規則。',[('host-sdu-id',[None])])
js(S/'reviewed-host-records.json',records);js(D/'added-host-records.json',{r:records[r]for r in sorted(set(rows.values()))});js(D/'field-reconciliation.json',changes)
js(D/'identity-review.json',[{'row_id':rid,'source_ids':[s for s,r in rows.items()if r==rid],'verification':'逐件官方原域名、原件標頭校名、國別與既有row身份一致；不以學部名稱推中央116適用。','country':'土耳其'if rid=='ncu-098'else'日本','school':{'ncu-098':'Suleyman Demirel University／Isparta','ncu-124':'University of Toyama','ncu-126':'Shizuoka University'}[rid]}for rid in sorted(set(rows.values()))])
print({'fields':len(changes),'hosts':3,'documents':5,'PDFpages':13,'XLSXsheets':3})
