from pathlib import Path
from datetime import datetime,timezone
import json,gzip,hashlib,base64,shutil,copy,subprocess
R=Path('/workspace/abroad');W=Path('/workspace/ncu-resume-work/twentyfourth');S=R/'sources/ncu/2026-10-11';D=R/'docs/data/ncu-completion-20261011/resume/twentyfourth';BASE='f235f46bd87c6f512e79d36bf4fedef5503ef900'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()==BASE
D.mkdir(exist_ok=True);(D/'source-pages').mkdir(exist_ok=True);now=datetime.now(timezone.utc).isoformat()
def js(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def gz(p,x):p.write_bytes(gzip.compress(json.dumps(x,ensure_ascii=False).encode(),mtime=0))
sources=json.load(gzip.open(S/'host-web-evidence.json.gz'));assert len(sources)==785
records=json.load(open(S/'reviewed-host-records.json'));before=copy.deepcopy(records);notes=json.load(open(W/'reading-notes.json'));ledger=[];rawpack=[];byid={s['id']:s for s in sources};ids={}
for n in notes:
 slug=n['slug'];rid=n['row_id'];p=W/n['filename'];ext=p.suffix[1:];meta=json.load(open(p.with_suffix(p.suffix+'.source.json')));sha=hashlib.sha256(p.read_bytes()).hexdigest();assert sha==n['source_sha256']==meta['sha256'] and meta['status']==200
 sid=f'{rid}-resume24-{slug}';assert sid not in byid;ids[slug]=sid
 template=next(s for s in sources if rid in s.get('row_ids',[]))
 if ext=='pdf':pages=[{'page':i,'text':(W/f'{slug}-p{i:02}.txt').read_text()}for i in n['native_pages_read']]
 elif ext=='docx':pages=[{'page':None,'text':'\n'.join((W/f'{slug}-p{i:02}.txt').read_text()for i in n['native_pages_read'])}]
 else:pages=[{'page':None,'text':(W/f'{slug}.txt').read_text()}]
 s={'id':sid,'school_name':template['school_name'],'country':template['country'],'row_ids':[rid],'url':meta['url'],'final_url':meta.get('final_url',meta['url']),'kind':'host_official_candidate','purpose':'兩校官方交換程序、條件文件、課程與住宿逐件核讀','label':slug+'（'+n['document_year_scope']+'）','authority_kind':'partner_university','checked_at':meta['checked_at'],'status':200,'sha256':sha,'content_type':meta['content_type'],'format':ext,'pages':pages,'links':json.load(open(W/(slug+'-links.json')))if ext=='html'else[],'applicability':n['document_year_scope']+'；中央116校別、名額與方案仍未核实。','reading_status':'selected_passages_reviewed'if ext=='html'else'full_visual_and_native_reviewed','reading_review':{'source_sha256':sha,'pages_reviewed':[p['page']for p in pages],'full_document_read':n['full_document_read'],'reviewed_at':now,'review_note':' '.join(t for _,t in n['page_notes']),'year_scope':n['document_year_scope']},'reuse_license_note':n['license_scope']}
 renders=[]
 for i in n['visual_pages_read']:
  png=W/f'{slug}-p{i:02}.png';dest=D/'source-pages'/png.name;shutil.copy2(png,dest);renders.append({'page':i,'page_kind':'local_docx_conversion'if ext=='docx'else'original_pdf','path':str(dest.relative_to(R)),'sha256':hashlib.sha256(png.read_bytes()).hexdigest()})
 if ext!='html':
  s['visual_review']={'source_sha256':sha,'pdf_pages_reviewed':n['visual_pages_read']if ext=='pdf'else[],'converted_pages_reviewed':n['visual_pages_read']if ext=='docx'else[],'full_document_read':True,'reviewed_at':now,'method':'原生文字全文與逐頁view_image核對；Word另核OOXML及LibreOffice本地轉換頁，無原生固定PDF頁碼；非OCR。','rendered_pages':renders,'page_notes_zh':{str(i):t for i,t in n['page_notes']}}
 if ext=='docx':
  converted=W/'docx-rendered'/f'{slug}.pdf';dest=D/'source-pages'/converted.name;shutil.copy2(converted,dest);s['document_format']='docx_no_fixed_pdf_pages';s['visual_review']['converted_pdf_sha256']=hashlib.sha256(converted.read_bytes()).hexdigest();s['visual_review']['converted_pdf_path']=str(dest.relative_to(R))
 sources.append(s);byid[sid]=s;records[rid]['source_ids'].append(sid);records[rid]['checked_at']=now
 rawpack.append({'source_id':sid,'receipt':meta,'encoding':'base64','body':base64.b64encode(p.read_bytes()).decode()})
 ledger.append({**n,'source_id':sid,'retrieved_at':meta['checked_at'],'reviewed_at':now,'current_116_approval':False,'rendered_pages':renders})
LIMIT='中央116校別、名額、方案及實際校區仍未核實；僅保留原年參考，不啟用期限提醒。'
changes=[]
def field(rid,key,points,refs,unresolved=LIMIT,append=False,gap_only=False):
 r=records[rid];old=copy.deepcopy(r['fields'].get(key));p=points if isinstance(points,list)else[points];rr=[{'id':ids[slug],'page':page}for slug,page in refs]
 if append and old:p=old['points']+p;rr=old['sources']+rr
 v={'points':p,'sources':rr,'unresolved':unresolved}
 if gap_only:v['gap_only']=True
 r['fields'][key]=v;changes.append({'row_id':rid,'field':key,'previous':old,'updated':v})
def doc(name,slug,page=None,condition=None,signatures=None):
 d={'name':name,'source_urls':[byid[ids[slug]]['url']+(f'#page={page}'if page is not None else'')],'needs_confirmation':True,'stage':'student_application','applicability_status':'reference_only','applicability_note':LIMIT}
 if condition:d.update(conditional=True,condition=condition)
 if signatures:d['signatures']=signatures
 return d
# IUM authored 2025-26 factsheet hosted by a university partner.
rid='ncu-060';slug='monaco-factsheet-2025-26'
records[rid]['applicability']='母校未註年介紹加IUM編製2025–26資料表（Carleton官方交換網站保存）；'+LIMIT
field(rid,'eligibility','2025–26外校方案提供工商管理學士與理學碩士，必須由派出母校正式提名；不能由校級學科簡介推為每個學院自由申請。',[ (slug,1)],append=True)
field(rid,'language','2025–26外校課程英授，來自非英語授課機構者須語言程度證明；資料表未指定測驗或分數。此條件不取消母校B2要求，也不能自行推定中央所有學生均免語證。',[(slug,1)],append=True)
field(rid,'host_deadline','2025–26表：母校提名秋4/15、春10/15；學生申請秋4/30、春10/30。提名後才寄網申連結，日期保留原週期，不轉為中央116提醒。',[(slug,1)])
field(rid,'host_documents','2025–26初申八類：護照或身分證掃描、護照尺寸照片、履歷、動機信、成績單、健康及責任保險確認聲明、有條件的語言程度證明、學習協議。保險確認聲明不是已投保保單，語證適用於派出機構非英語授課者；当期表格與通知仍待核。',[(slug,1)])
records[rid]['host_documents']=[doc(name,slug,1)for name in ['護照或身分證掃描','護照尺寸照片','履歷','動機信','成績單','健康與責任保險確認聲明（不是已投保保單）']]+[doc('語言程度證明',slug,1,condition='2025–26表要求派出機構非英語授課者提供；不取消中央母校B2條件，當期豁免須確認。'),doc('學習協議',slug,1)]
field(rid,'study_period',['2025–26學士：秋2025/9/11至12/19，春2026/1/22至6/26；秋考12/11至19、春考5/4至12。學士補考5/26至29在跨欄合併列，原表未清楚分秋春，不自行歸為單一學期。','碩士：秋2025/9/4至12/19，春2026/1/7至6/26；秋考12/15至19，春考3/23至28及6/10至16。補考另列2026/2/23至27及6/30至7/4，部分晚於一般學期末，不能保證學期末即可離校。'],[(slug,1)])
field(rid,'courses','2025–26採預設課程模組，由學生與母校國際協調人選方案及專長模組，不是全校自由單科組合。採美制學分，每學分約15面授小時；每一選項至少15美制學分、相當30 ECTS，不能誤寫成15 ECTS或直接保證中央抵免。',[(slug,1)])
field(rid,'housing','2025–26明列沒有校內住宿，學生自行找房及付款，學服提供協助。單人房參考600–800歐元、公寓800–1200歐元，但原表未寫計價週期，不能自行補成月租；房源、押金、租期與116價格待核。',[(slug,2)])
field(rid,'cost','2025–26只提供住宿參考價且未寫計價週期，沒有完整生活預算；不能把單房600–800歐元當每月總生活費。餐食、交通、保險及其他生活費尚待核讀。',[(slug,2)],unresolved='僅有未標計價週期的原年住宿價，完整生活費與116費額待核。')
field(rid,'tuition','2025–26學生社團費每學期87.50歐元，原表特別註明待確認；不是學費、當期已定收費或全部活動免費。兩校正式學費與其他雜費仍待中央116方案及接收通知確認。',[(slug,2)])
field(rid,'insurance','2025–26外校要求在摩納哥就學及住摩納哥或法國期間有健康、意外與責任險。學服可推薦保險公司，學生仍須核對個別保障；初申的保險確認聲明與實際有效保障不同，不自行加入已付保費金額。',[(slug,1),(slug,2)])
field(rid,'visa','2025–26校方依住法國或摩納哥分別說明簽證路徑，並在申請過程提供邀請信；這是舊期校方指引，非已核當期政府規則。本人國籍、實際居住國與116文件需向適用官方窗口確認，不把兩國路徑混用。',[(slug,2)])
field(rid,'transport','2025–26表以尼斯機場為最近機場，列到摩納哥約30–45分鐘、尼斯至摩納哥火車約20分鐘等概覽；不是當期班表、票價或校方接機承諾。校址可步行到車站及公車站，實際住宿通勤仍按地址確認。',[(slug,2)])
field(rid,'arrival','學生社團提供運動、辯論、休閒及金融創業等活動與部分商家折扣；2025–26社團費另列每學期87.50歐元待確認，折扣不等於全部免費，未列中央116迎新或必到日。',[(slug,2)])
# BUEM: host evidence does not silently erase the mixed home description.
rid='ncu-061';web='buem-incoming';guide='buem-studyguide';app='buem-application';la='buem-learning';dorm='buem-dormitory';courses='buem-courses'
records[rid]['applicability']='母校未年混校原文保留，另有身份明確BUEM官方incoming程序、2026–27校曆、2023檔名指南、表內2022/23申請表及未年LA；'+LIMIT
field(rid,'eligibility','BUEM官方交換頁要求先有雙邊協議並獲派出母校提名，程序標示Erasmus；官方課單另列學士、碩士。這能確認BUEM自身資訊，但中央116實際雙邊方案及母校混寫仍須釐清。',[(web,None),(courses,None)],append=True,gap_only=True)
field(rid,'language','BUEM外語課單多為英授、部分另列俄語；學習協議只提供A1至母語程度勾選欄，沒有一律最低級別。不能把空白自評欄或英授課單當成降低母校語檢門檻的依據。',[(courses,None),(la,None)],append=True,gap_only=True)
field(rid,'host_deadline','BUEM交換頁列秋季／全年申請6月底、春季11月底；2023檔名指南具體寫6/30、11/30。官網校曆是2026–27，但期限段未另註年，中央116是否沿用仍待核，不啟用提醒。',[(web,None),(guide,1)])
field(rid,'host_documents',['BUEM官方網頁明列四類：申請表、學習協議、履歷、護照或身分證；參與電子協議系統者用線上學習協議，未參與者用紙本版本，兩條路徑不是各交一套。電腦填後列印由學生及母校協調人簽，外校接受後約四週寄回簽署協議及接受信，不能申請前就要求已錄取。','官網現行連結的申請表內仍印2022/23，另列動機信及英文成績單，與網頁四類清單不同。兩項舊表追加列為待核條件，不能靜默刪除或改成116已核必繳。申請表接收方預勾暫准、個人欄預勾男或曾實習均是模板預設，不表示個人資格或已獲錄取。'],[(web,None),(app,None)])
records[rid]['host_documents']=[doc('申請表（連結表內2022/23；電腦填後列印、貼照片）',app,signatures=['學生','派出母校系所協調人','派出母校校級協調人']),doc('學習協議（依母校系統採線上或紙本一種）',la,signatures=['學生','派出母校負責人']),doc('履歷（舊表另標歐式履歷）',web),doc('護照或身分證影本',web),doc('動機信（舊表追加，當期是否必繳待核）',app,condition='官網連結的2022/23申請表列此件，但目前網頁清單未列，須接收校確認當期要求。'),doc('英文成績單（舊表追加，當期是否必繳待核）',app,condition='官網連結的2022/23申請表列此件，但目前網頁清單未列，須接收校確認當期要求。')]
field(rid,'study_period','BUEM官網2026–27秋學期2026/9/28至2027/1/30，授課至12/18、考試1/4至30；春學期2027/2/8至6/30，授課至4/30、考試5/3至6/30。這份身份明確的官方校曆與母校混校未年概述分開，不外推中央116年度。',[(web,None)])
field(rid,'courses','BUEM未註年外語課單分學士／碩士、秋／春，多英語、部分課兼俄語；例如學士秋會計4學分、企業管理導論5學分，碩士春國際管理與國際商務6學分。課名、代碼及學分逐課核對，沒有把頁末空白研究後課程標題當博士開放，也不保證116每課開設。學習協議的課程變更與回校抵免表屬交換中／結束後，不能列成初申已完成文件。',[(courses,None),(la,None)])
field(rid,'housing',['BUEM學生住宿位於赫利尼茨卡街1號的職業學校宿舍三樓，與富爾代科瓦街16號教學校址分開。舒適房三床、豪華房兩床；舒適房若只住兩人，須共同負担第三床的較高費率。洗衣包含在住宿費中，廚衛共用，沒有保證每人獲房。','官網三個月Erasmus及雙邊交換方案：每人每月三人舒適房200歐元、雙人豪華房300歐元。2026/9/1起十一個月以上長租及九個月／兩學期另有較低價，不能把十一個月三人房150歐元套到三個月交換。短住25歐元／晚需特別批准；押金、期限與116房源仍待核。'],[(dorm,None),('buem-accommodation',1),(guide,2)])
field(rid,'cost','官方住宿頁只提供按租期區分的房價，沒有完整每月生活預算。三個月交換房價每人每月200或300歐元依房型，餐費、交通、保險及其他生活支出另待核；附加住宿費按住宿規則，不能假設所有服務全包。',[(dorm,None)],unresolved='房价有特定租期／方案，完整生活費、附加費、116費額仍待核。')
field(rid,'insurance','2023檔名指南要求涵蓋全期在斯洛伐克的健康、意外及責任險，歐盟與非歐盟身分分開說明；列舉的保障上限不是保費或每人法定最低。原文強調保障依個別契約，中央116適用保單與當期規則仍待核。',[(guide,3)])
field(rid,'visa','2023檔名指南把簽證、居留及行政健康文件分為抵達前、抵達後及離境階段，並註明規定可能變更；不能把到後居留健康證明當BUEM初申附件。這些舊校方說明未當成當期政府規則，116本人適用仍須官方確認。',[(guide,2),(guide,3)])
field(rid,'transport','官網宿舍頁以電車3號、佩克納街站步行約8分鐘及到校約26分鐘作交通概覽；2023住宿列表以約30分鐘概述BUEM宿舍路程，非相同起訖測量或保證班次。停車只有兩個付費名額且須事先安排，不是免費保證車位。',[(dorm,None),('buem-accommodation',1)])
field(rid,'arrival','官網2026–27迎新週：秋2026/9/28至10/2、春2027/2/8至12；沒有宣告中央116必到日。學習協議中途更課須按表向學生與兩校負責人確認，交換後成績與母校抵免欄在結束後填，不能要求初申時已完成。',[(web,None),(la,None)])
js(S/'reviewed-host-records.json',records);gz(S/'host-web-evidence.json.gz',sources);gz(S/'resume-twentyfourth-original-responses.json.gz',rawpack);js(D/'reading-ledger.json',{'checked_at':now,'base_sha':BASE,'items':ledger});js(D/'field-reconciliation.json',changes);js(D/'added-host-records.json',{k:records[k]for k in ['ncu-060','ncu-061']});js(D/'identity-review.json',{'ncu-060':'IUM校徽、官方編製2025–26表、國別摩納哥及LeStella14同址；Carleton官方partner mirror，非另校內容。','ncu-061':'BUEM/VSEM、SKBRATISL13及Furdekova16官方互證，既有照片座標保留；Hlinicka1只住宿地址，不替代教學位置。','current_116_approval':False})
print({'sources':len(sources),'reading_records':sum(bool(s.get('reading_review'))for s in sources),'new_hosts':0,'updated_hosts':2,'updated_fields':len(changes),'previous_gap_only_resolved_to_reference':sum(bool((x['previous']or{}).get('gap_only'))and not x['updated'].get('gap_only')for x in changes),'documents':5,'original_pdf_pages':12,'local_docx_rendered_pages':7,'html_main_passages':3})
