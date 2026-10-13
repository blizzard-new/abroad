from pathlib import Path
from datetime import datetime,timezone
import json,gzip,hashlib,base64,shutil,copy,subprocess
R=Path('/workspace/abroad');W=Path('/workspace/ncu-resume-work/thirtieth');B=R/'sources/ncu/2026-10-08';S=R/'sources/ncu/2026-10-11';D=R/'docs/data/ncu-completion-20261011/resume/thirtieth';BASE='f58ad0cefc6363fa662b66567a12cdbb19d66491'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()==BASE
D.mkdir(exist_ok=True);(D/'source-pages').mkdir(exist_ok=True);now=datetime.now(timezone.utc).isoformat()
def js(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def gz(p,x):p.write_bytes(gzip.compress(json.dumps(x,ensure_ascii=False).encode(),mtime=0))
basepack=json.load(gzip.open(B/'host-web-evidence.json.gz'));completion=json.load(gzip.open(S/'host-web-evidence.json.gz'));byid={s['id']:s for s in basepack+completion};receipts={s['source_id']:s for s in json.load(open(W/'fetch-receipts.json'))};notes=json.load(open(W/'reading-notes.json'));ledger=[];rawpack=[]
for n in notes:
 sid=n['source_id'];s=byid[sid];raw=(W/(sid+'.pdf')).read_bytes();assert hashlib.sha256(raw).hexdigest()==s['sha256']==n['sha256'];pages=n['visual_pages_read'];assert n['native_pages_read']==pages
 renders=[];local=[]
 for page in pages:
  p=W/f'{sid}-p{page:02}.png';hash=hashlib.sha256(p.read_bytes()).hexdigest()
  if 'kansai' in sid:local.append({'pdf_page':page,'sha256':hash,'archive_status':'local_only; preserve existing public excerpt scope; no additional identifiable testimonials or people photos'})
  else:
   q=D/'source-pages'/p.name;shutil.copy2(p,q);renders.append({'pdf_page':page,'path':str(q.relative_to(R)),'sha256':hash})
 s['reading_status']='full_visual_and_native_reviewed';s['reading_review']={'source_sha256':s['sha256'],'pages_reviewed':pages,'full_document_read':True,'reviewed_at':now,'review_note':'第三十批核讀完整物理頁；公開摘錄範圍、歷史版本與個人適用限制保留。'}
 s['visual_review']={'source_sha256':s['sha256'],'pdf_pages_reviewed':pages,'full_document_read':True,'reviewed_at':now,'method':'原生全文及逐頁view_image核讀，非OCR','rendered_pages':renders,'local_render_sha256':local,'page_notes_zh':{str(p):v for p,v in n['page_notes']}}
 s['reuse_license_note']='空白政府CGAF表明可複製、不得販售；非校景授權。'if'ph-'in sid else'原公開摘錄供來源查核，照片與具名心得不新增轉存；無校景獨立開放授權。'
 js(B/f'{sid}-visual-review.json',s['visual_review'])
 if 'kansai' in sid:
  p=B/f'{sid}-public-excerpt.json';ex=json.load(open(p));ex['note_zh']='原件5頁已於第三十批全文及逐頁視讀；公開仍只保留第1／5頁一般homestay／FAQ，省略照片及具名經驗頁。原件SHA改變須重核才沿用摘錄。';js(p,ex)
 else:rawpack.append({'source_id':sid,'receipt':receipts[sid]['receipt'],'encoding':'base64','body':base64.b64encode(raw).decode()})
 ledger.append({'source_id':sid,'row_id':'ncu-129'if'kansai'in sid else'ncu-199','source_url':s['url'],'source_sha256':s['sha256'],'retrieved_at':receipts[sid]['receipt']['checked_at'],'reviewed_at':now,'document_year_scope':n['document_year_scope'],'pages_reviewed':pages,'native_full_read':True,'visual_full_read':True,'current_116_approval':False,'page_notes_zh':n['page_notes'],'license_scope':s['reuse_license_note'],'rendered_pages':renders,'local_render_sha256':local})
# Record the identity-checked same-URL/same-SHA duplicate; do not double-count reading as a new original.
a=byid['host-kansai-next-08'];b=byid['ncu-129-follow-3e0c81928e'];assert a['url']==b['url']and a['sha256']==b['sha256'];assert b['reading_review']['full_document_read']
duplicate={'existing_full_text_source_id':b['id'],'reviewed_alias':a['id'],'source_sha256':a['sha256'],'same_url':a['url'],'school_identity':'Kansai University／日本／校方KokusaiのHomestay leaflet。両記録がncu-129を参照。','note_zh':'首次全文閱讀份數不加一；舊別名補全文與視讀。公開摘錄仍1/5頁；其餘頁不轉存。'}
partial=json.load(open(W/'cuk-partial-review.json'));sid=partial['source_id'];s=byid[sid];assert s['sha256']==partial['source_sha256'];s['selected_visual_review']=partial;s['reading_review']['full_document_read']=False;s['reading_review']['sheet_reading_scope']+='；第三十批補Trinity Screen三嵌图及List前5列，未完整核對List。';s['reading_review']['selected_visual_reviewed_at']=now
# Neither workbook is marked as fully read. No workbook or screenshot with a person's account/course history is copied into the repo.
gz(B/'host-web-evidence.json.gz',basepack);gz(S/'host-web-evidence.json.gz',completion);gz(S/'resume-thirtieth-original-responses.json.gz',rawpack)
js(D/'reading-ledger.json',{'checked_at':now,'base_sha':BASE,'items':ledger});js(D/'duplicate-source-review.json',duplicate);js(D/'partial-workbook-review.json',partial);js(D/'fresh-fetch-receipts.json',list(receipts.values()))
js(D/'identity-review.json',[{'row_id':'ncu-129','school':'關西大學 Kansai University','country':'日本','files':['host-kansai-next-08'],'method':'官方kansai-u.ac.jp Kokusai連結及同SHA現有ncu129原件逐筆一致；一般住家示例非授課校區。'},{'row_id':'ncu-199','school':'打拉省立大學 Tarlac State University','country':'菲律賓','files':['host-ph-ssp-cgaf','host-ph-9f-cgaf'],'method':'政府immigration.gov.ph空白共用表，僅作既有TSU菲律賓簽證條件參考，不是校方錄取文件或校別資格。'},{'row_id':'ncu-155','school':'韓國天主教大學 The Catholic University of Korea','country':'南韓','files':['ncu-155-resume14-cuk-courses'],'method':'校方oia.catholic.ac.kr附件、CUK2026Fall表頭及가톨릭대학교標誌相符；Trinity畫面2026第二學期성심；非2027清單。'},{'row_id':'ncu-192','school':'廈門大學 Xiamen University','country':'中國大陸','files':['host-xmu-course-reference-2025-26'],'method':'既有visiting.xmu.edu.cn課表URL與SHA相同，兩表內容未新全讀，沒有提升可選資格。'}])
base=json.load(open(B/'reviewed-host-records.json'));records=json.load(open(S/'reviewed-host-records.json'));changes=[];limit='中央116校別、名額與個人適用仍未核；歷史／一般原件僅參考，不啟用期限提醒。'
for rid in ['ncu-129','ncu-199','ncu-155']:
 if rid not in records:records[rid]=copy.deepcopy(base[rid])
 records[rid]['checked_at']=now
 records[rid]['applicability']+='；第三十批補原件核讀及明列未完成範圍。'+limit

def field(rid,key,point,refs):
 r=records[rid];old=copy.deepcopy(r['fields'].get(key,base.get(rid,{}).get('fields',{}).get(key)));assert old
 v={**old,'points':old['points']+[point],'sources':list(old['sources'])}
 for sid,pages in refs:
  if sid not in r['source_ids']:r['source_ids'].append(sid)
  for page in pages:
   ref={'id':sid,'page':page}
   if ref not in v['sources']:v['sources'].append(ref)
 v['unresolved']=(old.get('unresolved')or'')+'；'+limit;r['fields'][key]=v;changes.append({'row_id':rid,'field':key,'previous':old,'updated':v})
field('ncu-199','visa','兩版CGAF均為學生簽證與SSP共用空白表，不能依下載分類就替個人選定簽證。兩頁皆有，首頁雖印Page1of1，不能漏附實際第2頁。第2頁DO NOT FILL OUT THIS PORTION及核准／蓋章區屬機關處理，不當學生自行核准或一般申請人簽名欄；兩版長官署名不同，僅保留版本，不推現任或適用已核。',[('host-ph-ssp-cgaf',[1,2]),('host-ph-9f-cgaf',[1,2])])
field('ncu-199','arrival','CGAF另列學校代表身分號、學校accreditation、ACR號與效期、CRN，以及雙地住址與監護欄；空白欄本身不表示每位交換生已有或必須補辦所有號碼。月份／一年勾選是申請欄，不保證相同合法停留期限；表內未給當期處理日數或費用。',[('host-ph-ssp-cgaf',[1,2]),('host-ph-9f-cgaf',[1,2])])
field('ncu-129','housing','寄宿leaflet原件5頁已全視讀，公開仍只留第1與5頁一般說明。頁1估離校約30–60分鐘，未明校區與交通方式，不保證每位中央交換生相同路程；房間示例與四則個人心得不是床位、設備或活動保證。',[('host-kansai-next-08',[1,5])])
field('ncu-129','cost','寄宿方案頁1說交通費由學生負擔，含早餐晚餐及依需求Wi-Fi；沒有通勤票價、寄宿單價、押金或稅金細目，不能用宣傳例合成116全包總額。',[('host-kansai-next-08',[1])])
field('ncu-129','arrival','寄宿FAQ建議出發前熟悉日語與習俗；飲食需求先通知，外出不回家用餐先告知家庭。orientation會介紹文化差異與常見誤解，但未公布當期日期、到達接送或指定家庭。',[('host-kansai-next-08',[5])])
field('ncu-155','courses','已補看工作簿Trinity Screen三張操作圖：科目代碼查詢後選班次、Confirm再Apply，屬2026第二學期操作示例，不能保證班次有位或送出即錄取。外語授課狀態須另核欄位，英文介面不是全英授證據；具名帳號／已選課記錄不轉存。List其餘課程仍未逐列核完，未聲稱整份工作簿已讀。',[('ncu-155-resume14-cuk-courses',[None])])
js(S/'reviewed-host-records.json',records);js(D/'added-host-records.json',{rid:records[rid]for rid in ['ncu-129','ncu-199','ncu-155']});js(D/'field-reconciliation.json',changes)
js(D/'remaining-workbooks.json',[{'source_id':'host-xmu-course-reference-2025-26','scope':'25–26兩表4124／4174列；原件SHA相同，既有前9列選讀，其餘未讀。','external_blocker':False},{'source_id':'ncu-155-resume14-cuk-courses','scope':'List1351非空列僅原前12與本輪前5列；Trinity Screen文字及3圖本輪全視讀。List未全文，不算完成。','external_blocker':False}])
print({'fields':len(changes),'hosts':3,'full_source_aliases':3,'new_full_originals':2,'pdf_physical_pages_viewed':9,'public_page_images':4,'partial_workbook_images_viewed':3})
