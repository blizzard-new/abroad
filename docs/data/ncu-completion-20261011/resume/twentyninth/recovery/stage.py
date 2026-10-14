from pathlib import Path
from datetime import datetime,timezone
import json,gzip,hashlib,base64,shutil,copy,subprocess
R=Path('/workspace/abroad');W=Path('/workspace/ncu-resume-work/twentyninth');S=R/'sources/ncu/2026-10-11';B=R/'sources/ncu/2026-10-08';D=R/'docs/data/ncu-completion-20261011/resume/twentyninth';D.mkdir(exist_ok=True);(D/'source-pages').mkdir(exist_ok=True)
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()=='c9cc78890403998adc7848c59564751217ca79bd'
now=datetime.now(timezone.utc).isoformat()
def js(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def gz(p,x):p.write_bytes(gzip.compress(json.dumps(x,ensure_ascii=False).encode(),mtime=0))
receipts={r['source_id']:r for r in json.load(open(W/'fetch-receipts.json'))};pack=json.load(gzip.open(B/'drive-evidence.json.gz'));webpack=json.load(gzip.open(B/'host-web-evidence.json.gz'));byid={s['id']:s for s in pack+webpack};notes=json.load(open(W/'reading-notes.json'));mapping=json.load(open(W/'candidate-identity-mapping.json'));rows={sid:r['row_id']for r in mapping for sid in r['files']};ledger=[];responses=[]
for n in notes:
 sid=n['source_id'];s=byid[sid];pages=list(range(1,len(s['pages'])+1));assert n['native_pages_read']==n['visual_pages_read']==pages
 raw=(W/f'{sid}.pdf').read_bytes();assert hashlib.sha256(raw).hexdigest()==s['sha256']==n['sha256']==receipts[sid]['sha256']
 renders=[]
 for page in pages:
  p=W/f'{sid}-p{page:02}.png';q=D/'source-pages'/p.name;shutil.copy2(p,q);renders.append({'pdf_page':page,'path':str(q.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 s['reading_status']='full_visual_and_native_reviewed';s['reading_review']={'source_sha256':s['sha256'],'pages_reviewed':pages,'full_document_read':True,'reviewed_at':now,'review_note':'5份11頁第二十九批全篇原生與原圖核讀；方案、年度、學科限制與原件衝突保留。'}
 s['visual_review']={'source_sha256':s['sha256'],'pdf_pages_reviewed':pages,'full_document_read':True,'reviewed_at':now,'method':'原生全文與逐頁view_image人工核對；非OCR','rendered_pages':renders,'page_notes_zh':{str(p):v for p,v in n['page_notes']}}
 s['reuse_license_note']='母校公開官方原件僅供查核；未取得頁內照片獨立開放授權，不轉作校景。'
 if n.get('selected_passages'):
  s['visual_review']['page_transcriptions']=n['selected_passages'];s['visual_review']['include_native_with_selected_passages']=sid!='host-tuaf-2026'
  s['page_transcriptions']=n['selected_passages']
 js(B/f'{sid}-visual-review.json',s['visual_review'])
 ledger.append({'source_id':sid,'row_id':rows[sid],'source_url':s['url'],'source_sha256':s['sha256'],'retrieved_at':receipts[sid]['receipt']['checked_at'],'reviewed_at':now,'document_year_scope':n['document_year_scope'],'pages_reviewed':pages,'native_full_read':True,'native_text_limitations':n.get('native_text_limitations'),'blank_visual_pages':n.get('blank_visual_pages',[]),'selected_passages':n.get('selected_passages',[]),'visual_full_read':True,'page_notes_zh':n['page_notes'],'current_116_approval':False,'license_scope':s['reuse_license_note'],'rendered_pages':renders})
 responses.append({'source_id':sid,'receipt':receipts[sid]['receipt'],'encoding':'base64','body':base64.b64encode(raw).decode()})
gz(B/'drive-evidence.json.gz',pack);gz(B/'host-web-evidence.json.gz',webpack);gz(S/'resume-twentyninth-original-responses.json.gz',responses);js(D/'fresh-fetch-receipts.json',list(receipts.values()));js(D/'reading-ledger.json',{'checked_at':now,'base_sha':'c9cc78890403998adc7848c59564751217ca79bd','items':ledger})
js(D/'identity-review.json',mapping)
records=json.load(open(S/'reviewed-host-records.json'));base=json.load(open(B/'reviewed-host-records.json'));before=copy.deepcopy(records);changes=[]
LIMIT='中央116校別、名額、方案與實際校區仍未核實；以下依原件學年作參考，不啟用期限提醒。'
for sid,rid in rows.items():
 if rid not in records:records[rid]=copy.deepcopy(base[rid])
 if sid not in records[rid]['source_ids']:records[rid]['source_ids'].append(sid)
 records[rid]['checked_at']=now
 records[rid]['applicability']+='；第二十九批核讀'+next(n['document_year_scope']for n in notes if n['source_id']==sid)+'。'+LIMIT

def field(rid,key,points,sid,pages,unresolved=LIMIT,append=True,gap_only=False):
 r=records[rid];old=copy.deepcopy(r['fields'].get(key,base.get(rid,{}).get('fields',{}).get(key)));p=points if isinstance(points,list)else[points];refs=[{'id':sid,'page':page}for page in pages]
 if append and old:p=old['points']+p;refs=old['sources']+refs
 v={'points':p,'sources':refs,'unresolved':unresolved}
 if gap_only:v['gap_only']=True
 r['fields'][key]=v;changes.append({'row_id':rid,'field':key,'previous':old,'updated':v})
def doc(name,sid,page=1,condition=None,signatures=None,stage='student_application'):
 d={'name':name,'source_urls':[byid[sid]['url']+f'#page={page}'],'needs_confirmation':True,'stage':stage,'applicability_status':'reference_only','applicability_note':LIMIT}
 if condition:d.update(conditional=True,condition=condition)
 if signatures:d['signatures']=signatures
 return d
# Quarantine only the known misordered native fee rows; retain original extraction.
sid='host-tuaf-2026';js(B/f'{sid}-index-review.json',{'source_sha256':byid[sid]['sha256'],'quarantined_pdf_pages':[2],'page_applicability_notes_zh':{'2':'原頁只寫$，未獨立證明幣別。年例／2026入口参考，非中央116核准；行政及簽證費以同頁視讀對應欄為準。'},'isolation_note_zh':'此頁文字排序把行政與簽證費金額對調，原生留稽核，不供問答直接沿用。'})
rid='ncu-213';sid='host-tuaf-2026'
field(rid,'tuition','本批重讀兩版原圖，行政費均為$70、到校後提交；簽證費$95／6個月與$135／12個月。年例版的原生文字順序錯置不代表費種變更；原頁未明寫幣別，維持未知。僅合作校學費免收，不把行政、簽證或食宿當全部免費。',sid,[2])
field(rid,'host_deadline','年例版PDF本身未印適用學年，原來源2026標籤不升為116。2024–25表的Acceptance段另列秋7/5、春10/20，和年例版7/25、11/25不同；兩者段落名均為Acceptance，不擅當成已確認學生申請截止。','host-tuaf-factsheet',[1])
field(rid,'study_period','兩份原頁全讀：2024–25表春季1/5至6/10，年例版春1/15至6/10，起日差10天；秋均8/15至12/30。保留版本差異，未擅選其一當116校曆。',sid,[1])
field(rid,'cost','兩版資料表住宿均只列$10而未標週期；餐食$90–110每月、單餐$1–1.3、水電清潔等$7–15每月。其他手冊另明列月房費，不能把那份週期補成這份原頁已寫，或把各版本合成官方單一總額。','host-tuaf-factsheet',[2])
field(rid,'host_documents','兩版資料表均列申請表加七件：成績、語言證明、學生證、動機與短期計畫、推薦信、護照、當地醫院健檢英文翻譯；年例版明寫英語證明，2024–25版泛稱語言證明。已讀填寫範例的optional標示仍有差異，未取消本人需核對的語言證明條件。',sid,[1])
field(rid,'insurance','兩版資料表建議在母國購買旅行保險，未列本頁保费、最低保額或全期保障條文；不能把手冊其他年度健康保險額度直接當這份表的強制費。','host-tuaf-factsheet',[2])
rid='ncu-098';sid='host-sdu-info'
field(rid,'city','2017檔名資訊表身份為土耳其Süleyman Demirel大學，TR ISPARTA01，國際處郵址Isparta西校區32260；不是其他國家的同名校。',sid,[1])
field(rid,'host_deadline','2017入口舊表提名截止寫None，僅表示這份表未設提名期限，不等於不用母校提名或當期可隨時申請。學生秋6/30、春12/30與未年網頁相同，但仍非2027–28精確已核期限。',sid,[2])
field(rid,'study_period','舊表秋9月中至1月底，考試在1月；春2月中至6月中，考試5月底至6月中。這是歷史一般約期，不當116確切行程。',sid,[2])
field(rid,'courses','舊資訊表列英語課程及ECTS課程入口，沒有逐課英語開課表或名額；不能因單行English便宣稱全校每門課皆可英語修讀。',sid,[2])
field(rid,'housing','舊表交換住宿由ESN成員協助安排校外房源，一般資訊另列校方Guest House；兩種選項均未列價格、申請期限或床位保證。',sid,[2])
field(rid,'arrival','舊表建議秋9/15、春2/15抵達，迎新概略9月／2月；建議日期不是強制當期報到日，ESN協助不保證接送或住宿。',sid,[2])
field(rid,'cost','2017入口資訊表沒有完整生活費、房租或押金金額；Guest House名稱與ESN住宿協助不能用來推算預算。',sid,[2],gap_only=True,unresolved='原件未列生活分項、幣別價格及週期，仍需續讀當期來源。')
rid='ncu-125';sid='host-fukui-admin-instructions2027spring'
field(rid,'eligibility','2026年8月承辦通知要求交換結束返母校續讀學位，交換在福井期間不能從母校畢業或取得學位。每合作校一至二人的一般接收限制不是中央116名額，不填入當期配額。',sid,[1])
field(rid,'host_documents','Spring2027承辦通知明確不收學生直接送件，除提名表以電子郵件外，其餘文件由母校審查後經線上系統提交，並用外校最新版本；提名後才寄系統指引。其他原件提名指定入口的差異仍保留，未由本任務代送或猜測私人入口。',sid,[1])
field(rid,'arrival','Spring2027通知預定2026年12月中錄取、2027年2月中寄COE、3月初至中線上日語分級，3/25或26入住、3/29至31迎新，並註可變動。這是別期參考，不能套中央116或保證COE與入境日期。',sid,[1])
field(rid,'courses','承辦通知說特別聽講生成績單春季通常10月底、秋季4月底發；提早申請須母校正式請求信，校方考慮後最早春9月底、秋4月初。不是最後上課日即取得，也不保證一要求便提前。',sid,[1,2])
field(rid,'cost','Spring2027承辦通知JASSO每月8萬日圓須獲選，結果預計2027年2月；前一學年原則JASSO換算GPA至少2.30／3.0屬獎學金条件，不當一般交換錄取GPA。原文叫參考第3頁，但下載PDF僅兩頁，換算附頁未取得，不自行補公式或當保證收入。',sid,[2])
rid='ncu-008';sid='1d5poIFBPY9TgENmwraKpEx-3Th0uGwAQ'
field(rid,'host_documents','2026–27資料表提名用母校收到的Excel名單寄國際處；若需新空白範本須向校方索取，公開表沒有附該Excel，不聲稱已取得。既有申請表附件規則另保留，不把提名名單當學生完整申請。',sid,[2])
field(rid,'study_period','2026–27資料表秋9月至1月中、補考3月中可能線上，並非保證遠距補考；春1月至4月中，若方案要求實習則可到8月，不能推定每人4月結束或每人都實習到8月。',sid,[2])
field(rid,'housing','全文核讀仍是每月300–800歐元、附近學生宿舍有限且先到先分、首次赴法優先；第3頁另列私人找房入口，不升為全體保證。校表對非歐洲住房補助的概述較籠統，既有政府例外條件繼續並列，不擅改成全面禁止。',sid,[2,3])
field(rid,'arrival','2026–27表要求需特別支援的學生提前告知，以便安排；不是要求公開健康資訊或保證所有調整方案已確認。',sid,[3])
js(S/'reviewed-host-records.json',records);js(D/'field-reconciliation.json',changes);js(D/'added-host-records.json',{rid:records[rid]for rid in set(rows.values())})
print({'documents':len(notes),'pdf_pages':sum(len(n['visual_pages_read'])for n in notes),'hosts':len(set(rows.values())),'new_hosts':0,'updated_fields':len(changes),'drive_completed':1,'base_host_completed':4})
