from pathlib import Path
from datetime import datetime,timezone
import json,gzip,hashlib,base64,shutil
R=Path('/workspace/abroad');W=Path('/workspace/ncu-resume-work/twentieth');S=R/'sources/ncu/2026-10-11';B=R/'sources/ncu/2026-10-08';D=R/'docs/data/ncu-completion-20261011/resume/twentieth';D.mkdir(exist_ok=True);(D/'source-pages').mkdir(exist_ok=True)
now=datetime.now(timezone.utc).isoformat()
def js(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def gz(p,x):p.write_bytes(gzip.compress(json.dumps(x,ensure_ascii=False).encode(),mtime=0))
receipts={r['source_id']:r for r in json.load(open(W/'fetch-receipts.json'))};pack=json.load(gzip.open(B/'drive-evidence.json.gz'));byid={s['id']:s for s in pack};notes=json.load(open(W/'reading-notes.json'));mapping=json.load(open(W/'candidate-identity-mapping.json'));rows={sid:r['row_id']for r in mapping for sid in r['files']};ledger=[];responses=[]
for n in notes:
 sid=n['source_id'];s=byid[sid];pages=list(range(1,len(s['pages'])+1));assert n['native_pages_read']==n['visual_pages_read']==pages
 raw=(W/f'{sid}.pdf').read_bytes();assert hashlib.sha256(raw).hexdigest()==s['sha256']==n['sha256']==receipts[sid]['sha256']
 renders=[]
 for page in pages:
  p=W/f'{sid}-p{page:02}.png';q=D/'source-pages'/p.name;shutil.copy2(p,q);renders.append({'pdf_page':page,'path':str(q.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 s['reading_status']='full_visual_and_native_reviewed';s['reading_review']={'source_sha256':s['sha256'],'pages_reviewed':pages,'full_document_read':True,'reviewed_at':now,'review_note':'14頁第二十批全篇原生與原圖核讀；母校院別、學程與外校一般指引分列，原年、校區、條件與原件錯誤保留。'}
 s['visual_review']={'source_sha256':s['sha256'],'pdf_pages_reviewed':pages,'full_document_read':True,'reviewed_at':now,'method':'原生全文與逐頁view_image人工核對；非OCR','rendered_pages':renders,'page_notes_zh':{str(p):v for p,v in n['page_notes']}}
 s['reuse_license_note']='母校公開官方原件僅供查核；未取得頁內照片獨立開放授權，不轉作校景。'
 ledger.append({'source_id':sid,'row_id':rows[sid],'source_url':s['url'],'source_sha256':s['sha256'],'retrieved_at':receipts[sid]['receipt']['checked_at'],'reviewed_at':now,'document_year_scope':n['document_year_scope'],'pages_reviewed':pages,'native_full_read':True,'visual_full_read':True,'page_notes_zh':n['page_notes'],'current_116_approval':False,'license_scope':s['reuse_license_note'],'rendered_pages':renders})
 responses.append({'source_id':sid,'receipt':receipts[sid]['receipt'],'encoding':'base64','body':base64.b64encode(raw).decode()})
gz(B/'drive-evidence.json.gz',pack);gz(S/'resume-twentieth-original-responses.json.gz',responses);js(D/'fresh-fetch-receipts.json',list(receipts.values()));js(D/'reading-ledger.json',{'checked_at':now,'base_sha':'77fff87df6e0877f36048d5de1cb459edf731354','items':ledger})
identity={
'ncu-025':'母校原件明列UMLP瑪麗路易巴斯德與原UFC風舍孔泰名稱，校徽與法國Besancon SaintJacques地址吻合舊UFC資料；保留舊名舊資料，不把改名視為全方案當期續准。',
'ncu-034':'索邦北巴黎USPN原Paris13，母校與外校校徽、法國Villetaneuse99avenueJeanBaptisteClement一致；不是其他Sorbonne。母校舊方案限大學部國際商管，與外校一般LLSHS/研究所規則分列。',
'ncu-062':'林雪坪/林雪平中文異字，母校與外校均LinkopingUniversity、LiU校徽、瑞典SE58183郵址一致；母校紅字院別限制不可用全校聯絡表取消。',
'ncu-079':'XAMK全名與校徽、芬蘭國別一致；母校Kouvola地址、新外校Mikkeli通訊地址、4校區專業格分別核對，不以單一點代表全部交換教學地。',
'ncu-087':'BrnoUniversityofTechnology母校中英名/校徽/CZBRNO01與捷克Brno行政地址一致；2026–27原件為FIT資訊科技學院與Erasmus，校務、學院、宿舍地址分列，不以院級規定當全部雙邊通用。'}
for r in mapping:r['matching_status']='human_identity_country_and_campus_reviewed';r['identity_review']=identity[r['row_id']];r['reviewed_at']=now;r['current_116_approval']=False
js(D/'identity-review.json',mapping)
records=json.load(open(S/'reviewed-host-records.json'));base=json.load(open(B/'reviewed-host-records.json'));assert not(set(rows.values())&(set(records)|set(base)))
LIMIT='中央116年度校別、名額、方案及實際校區仍待核實；以下保留原件年度參考，不啟用期限提醒。'
def record(rid,scope):
 r={'source_ids':[s for s,v in rows.items()if v==rid],'applicability':scope+'；'+LIMIT,'checked_at':now,'fields':{},'host_documents':[]};records[rid]=r;return r
def f(r,key,points,sid,pages,gap=None,gap_only=False):
 r['fields'][key]={'points':points if isinstance(points,list)else[points],'sources':[{'id':sid,'page':p}for p in pages],'unresolved':gap or LIMIT}
 if gap_only:r['fields'][key]['gap_only']=True
 return r['fields'][key]
def more(r,key,sid,pages):r['fields'][key]['sources'] += [{'id':sid,'page':p}for p in pages]
def doc(name,sid,page=1,stage='student_application',condition=None,signatures=None):
 d={'name':name,'source_urls':[byid[sid]['url']+f'#page={page}'],'needs_confirmation':True,'stage':stage,'applicability_status':'reference_only','applicability_note':LIMIT}
 if condition:d.update(conditional=True,condition=condition)
 if signatures:d['signatures']=signatures
 return d
# UMLP sources explicitly identify former UFC; retain undated document limits.
sid='1QSeMwHSexme8AsYTQKKoMDPBXY_y9l3v';old='1BT0vrPgAHKyTh1MSJj1ZIlXSgO917mcE';r=record('ncu-025','瑪麗路易巴斯德母校介紹及原風舍孔泰UFC資料表，均未註年')
f(r,'city','母校原件明列瑪麗路易巴斯德大學原名風舍孔泰；法國貝桑松聖雅克廣場4號，舊UFC國際處也列聖雅克廣場。舊表另有貝爾福、蒙貝利亞爾等六校區，國際處地址不是所有授課地點。',old,[1]);more(r,'city',sid,[1,2])
f(r,'eligibility','母校未註年資料列大學部與研究所；舊UFC簡介的學士、碩士、博士學位介紹不等於中央交換全部學制都獲准。116可申請學制與系所仍待核實。',old,[1]);more(r,'eligibility',sid,[1])
f(r,'language','舊UFC資料按方案要求法語B2或C1，亦列法語教師等值能力信；其他授課語言的測驗依所選方案。母校簡介只列B2，不能因此消除特定方案C1要求，也不能直接視為中央116接受免考。',sid,[2]);more(r,'language',old,[1])
f(r,'host_deadline','未註年舊UFC表：秋季提名5/15、入學與住宿申請6/1；春季提名10/15、入學與住宿申請11/1。沒有年度與截止時間，不製作116提醒。',sid,[2])
f(r,'host_documents','舊表指出經Mobility Online辦理入學與住宿，未列完整初次申請附件或最新表格；不能僅由流程自行補必繳件。',sid,[2],gap='已讀程序，但完整附件清單及116平台通知仍缺。')
f(r,'study_period','舊UFC表列交換一或兩學期；母校未註年介紹為秋季9月至1月、春季2月至7月，未取得116確切校曆。',sid,[1]);more(r,'study_period',old,[1])
f(r,'courses','未註年UFC表列每學期30學分；另介紹應用語言中心法語外語課，從一週到全年、含文化及實習支援。這些語言課介紹不等於所有交換生必修、免費或可抵免，實際課單與先備仍須確認。',sid,[1])
f(r,'housing','未註年UFC表稱向所有國際交換生提供校內住宿，須在Mobility Online申請；秋6/1、春11/1與入學截止相同。這是舊文件陳述，不能保證116床位；未列租金、押金或房型。',sid,[2])
f(r,'cost','未註年UFC表生活預估700–800歐元／月，明註僅供參考；未細列是否含全部住宿、保險與交通，不補成固定當期預算。',sid,[2])
f(r,'arrival','舊表介紹法語中心文化活動與學生支援，以及文化、體育、休閒與社團；沒有116迎新、接機或必到校日期，服務介紹不視為已預約或全免費。',sid,[1])
# USPN general guidance must not remove the home institution's programme restriction.
sid='1ZkcBoGJ0d135L-fSbdKbVj_EVNsYHR_P';old='1aeRSUI95MKEzTrKG7AWpy6kQMCIt-cOY';r=record('ncu-034','索邦北巴黎資料表檔名2025–26、正文未註年；母校未註年資料另限定國際商管大學部')
f(r,'city','法國維勒塔訥茲校區，讓－巴蒂斯特・克萊芒大道99號、郵遞區號93430；國際處在IUT大樓L101室。另有博比尼、聖但尼等校區，行政窗口不能代表所有課程所在地。',sid,[1]);more(r,'city',old,[1])
f(r,'eligibility',['母校未註年介紹只列大學部，且限國際商務與管理方案；不能用外校一般接受研究所的說明擴大中央可申請範圍。','外校一般資料接受大學部／研究所，但部分M1、M2課不開放；醫學原則排除，除非協議特別許可。文中名額只說依協議，沒有中央116數字。'],old,[1]);more(r,'eligibility',sid,[1])
f(r,'language',['一般法語方案要求B1、強烈建議B2，可用母校／教師信、DELF或TCF；母語者免交語言證明。LLSHS人文語言學院的非Erasmus學生另須大學部DELF B1／研究所DELF B2，並接受教授視訊面試，不能用一般教師信替代。','母校舊國際商管方案原文寫「B1 preferable, or B2 level in English」，前半B1未明列語種；不能自行補成法語，也不能將一般法語門檻直接套英授商管。中央116與實際方案語言仍待核。'],sid,[1]);more(r,'language',old,[1])
f(r,'host_deadline','資料表提名截止為秋季／全年5/15、春季10/31；沒有另列學生申請截止。檔名2025–26且正文未註年，不將提名日當116學生截止。',sid,[1,2])
f(r,'host_documents',['母校電子郵件提名需姓名、國籍、生日、電子郵件、領域與ISCED代碼、學期；學生收到MoveOn申請表後上傳八件：學習協議、正式成績單、目的陳述、課程負責人推薦信、法語能力證明、履歷、護照、母校學生證。','線上學習協議須申請完成並獲接收後才簽署，不能要求初申就已有外校簽好版本。法語證明及LLSHS特殊要求仍按所選方案判定，中央舊英授商管適用性未核。'],sid,[2]);more(r,'host_documents',sid,[1]);more(r,'host_documents',old,[1])
r['host_documents']=[doc(n,sid,2)for n in ['學習協議（外校線上簽署在申請完成接受後）','正式成績單','目的陳述','課程負責人推薦信','所選方案要求的法語能力證明（英授商管適用性待核）','履歷','護照影本','母校學生證']]
r['host_document_stages']=[{'id':'accepted-learning-agreement','position':'after_host_application','field':'host_documents','timing':'外校申請完成並獲接收後','title':'確認線上學習協議簽署','phase':'合作校申請','responsible_party':'學生、母校與接收校','summary':'原件把線上學習協議簽署放在申請完成並獲接受之後，不把外校已簽署版列為初次申請先決條件。','document_requirements':[doc('線上學習協議簽署確認',sid,2,'post_offer','適用本資料表方案，且申請已完成並獲接收')]}]
f(r,'study_period','資料表一般校曆：秋季9/1–1/31、春季2/1–6/30；母校舊商管介紹春季1月至6月，兩者不一致。須依錄取方案通知，不當116確定行程。',sid,[2]);more(r,'study_period',old,[1])
f(r,'courses','一般資料列每學期可取得30 ECTS、全年60 ECTS，交換實際須認可學分由派出母校與學生決定，不把30當全體硬性最低。開學法語密集一週18小時，A2–C1分班是課程安排，不等於入學門檻；部分研究所與醫學課另有限制。',sid,[1,2])
f(r,'housing','需住宿者在申請表勾選CROUS宿舍，依剩餘房源分配，非保證。原件列350–550歐元但未明計費週期，不能自行加上每月或每學期；未列房型、押金或另行截止。',sid,[2])
f(r,'cost','資料表生活預估約800歐元／月；原件檔名2025–26、正文未註年，沒有細項與包含範圍，不視為116固定預算或與宿舍估值重複相加。',sid,[2])
f(r,'insurance','校方資料要求意外、疾病及民事責任保險；另寫28歲以下須加入免費學生社會保險，這項年齡與制度說法未核現行效力，僅保留為舊校方文字，不能當116政府規則或免保依據。',sid,[2])
f(r,'visa','資料表列D類學生簽證及法國留學申請系統程序；國籍、所選方案與当期實際簽證／居留要求仍需主管機關核對，這份未註年正文不是政府核准。',sid,[2])
f(r,'arrival','每學期初迎新後接法語密集班，另有Tandem語言文化互助，可與法國學生交流；未列116確日、接機或住宿保證。',sid,[2])
# LiU: faculty scope and non-guaranteed housing, avoid adding rent twice.
sid='1fSWggjM147-lFXkgmUFXiX_GV7Zj_GyH';old='1lw6Z-dz1j3SIRy_bzcsofMEDEEhXdhFD';r=record('ncu-062','林雪坪理工學院資料及全校2026–2027概況；母校未註年介紹限定派出院別')
f(r,'city','瑞典林雪坪大學通訊郵遞區號SE-581 83；文件只列通訊城市，沒有逐系授課地址，不能把郵址當成所有課程的教室或校區。',sid,[2]);more(r,'city',old,[1])
f(r,'eligibility','母校原件紅字限理、工、生醫理工及資電學院的大學部／研究所學生申請。2026–27全校概況雖列四學院聯絡窗口，不能據此取消母校院別限制或推定各學院都可交換。',old,[1]);more(r,'eligibility',sid,[1,2])
f(r,'language','理工學院外校資料不要求語言證明，但須有足夠英語能力跟上技術課；母校舊介紹另提醒修瑞典語課須有瑞典語能力。這是外校參考，不等於中央116免語言門檻。',sid,[1]);more(r,'language',old,[1])
f(r,'host_deadline','2026–27理工學院提名與申請截止同為秋季／全年4/15、春季10/15；提名學生錄取決定約10週內，並非保證全部錄取或116沿用相同日。',sid,[1,2])
f(r,'host_documents','須先由母校提名，再依外校網站完成申請；原件提供流程連結但未列完整附件、格式或表格，不能自行補必繳件。',sid,[1,2],gap='完整初次附件、所選課程先備與116通知仍待核實。')
f(r,'study_period','2026–27參考：秋季8月至1月、春季1月至6月初；迎新與抵達另查接收通知，未列116確切日期。',sid,[2])
f(r,'courses','理工學院可跨學科及系所選課，但須符合先備。全時每週至少40小時、每學期30 ECTS；資料另稱非歐盟學生須申請且獲錄取至少30 ECTS以符合居留條件，這是校方2026–27說明，當期移民要求仍需官方核對。',sid,[1,2])
f(r,'housing','2026–27可在入學申請時同時申請住宿；非歐盟學生分配優先、歐洲學生視餘位，仍明列不保證住宿。若獲校方房間，估380歐元／月，含暖氣、電及網路，不適用所有私人房源。',sid,[1,2])
f(r,'cost','2026–27全部生活預估約950歐元／月，包含住宿、餐飲、教材、娛樂等；不能再把校方房租380歐元重複加進總額。估算不是116報價。',sid,[2])
f(r,'insurance','2026–27建議出發前備健康及遺失／損害保險；歐盟公民另準備EHIC。原件未列保費、保障額度或臺灣學生替代保單，按當期接收要求核對。',sid,[2])
f(r,'visa','2026–27校方說明須簽證或居留者取得錄取信後向移民局線上申請，概估審理約四個月；這是校方概估，不是主管機關時效保證或已獲准居留。',sid,[2])
f(r,'arrival','資料提供新生抵達、迎新、瑞典語密集及兼讀課程、身心障礙支持等連結；未列必到日、接送或每項服務費用，不以連結存在當作已完成安排。',sid,[2])
# XAMK: visually matched four campus columns and preserved two grading overlaps.
sid='1Kkl1LEnElibIowhWBt_V2ibjJT947aul';old='1Nne_gYrk1GZVxT769QXOWR6xs21H-V_x';r=record('ncu-079','東南芬蘭XAMK外校2025–2026資料表及未註年母校介紹')
f(r,'city','外校2025–26列米凱利通訊地址Patteristonkatu 3 D、郵遞區號50100；母校舊介紹列科沃拉Paraatikenttä 7、45100。四校區按專業分配，不能把通訊地址或科沃拉位置當全部交換教學地。',sid,[1]);more(r,'city',old,[1])
f(r,'eligibility','母校未註年介紹列大學部及研究所；外校2025–26方案按四校區與學習／實習區分，不能由學校開設學士碩士就認定中央116全部可申請。',old,[1]);more(r,'eligibility',sid,[1])
f(r,'language','外校2025–26標為建議：學生學業與實習英語B2，職員C1，芬蘭語無要求；不能把職員C1套學生。母校舊介紹直接列英語B2，中央116強制與可用證明仍待核。',sid,[2]);more(r,'language',old,[1])
f(r,'host_deadline','2025–26提名秋5/1、春10/15；學生申請秋季／全年5/15、春季11/1，使用SoleMOVE。這是舊週期，不是116截止。',sid,[2])
f(r,'host_documents','提名與學生申請皆在SoleMOVE，原件僅提供指引連結，未列完整初次附件或表格；不能自行加入護照、成績、學習協議等為必繳。',sid,[2],gap='完整附件與116平台、表格、通知仍待讀原件或新公告核實。')
f(r,'study_period','2025秋9/1–12/21、2026春1/12–4/30，學期開始有迎新日；母校舊介紹春季寫1月至5月，不能覆蓋外校明列舊期程，也不能直接延用至116。',sid,[1]);more(r,'study_period',old,[1])
f(r,'courses',['2025–26原表按校區：科特卡為遊戲程式、遊戲技術、資安、物流、社會照護，健康照護僅實習；科沃拉為數位國際商務與文化設計，包括遊戲、平面、修復、服務、室內家具、服裝與舞台服裝。','米凱利為環境工程、資訊科技，青年工作與社工僅實習；薩翁林納為生物產品技術、護理，物理治療主要實習。不能按文字抽取順序把各專業配到錯校區。','採ECTS；成績表原圖確有重疊：B為77–88、C為65–77，77同時出現；E及格40–52與F不及格小於51也重疊。保留原件錯誤，不自行修正或據此換算抵免。'],sid,[1,2])
f(r,'housing','2025–26外校說明協助安排交換生住宿；沒有承諾保證床位，也未列房型、租金、押金、申請期限或付款方式。',sid,[2])
f(r,'insurance','2025–26要求涵蓋整段在芬蘭停留期間的有效健康保險；保費、最低保障額及具體投保程序未列，不自行填值。',sid,[2])
f(r,'arrival','2025–26每學期開始有迎新日；各校區的學業與實習聯絡窗口分列，抵達通知須對應錄取校區與方案。沒有機場接送或116確切報到日期。',sid,[1,2])
# Brno FIT specific document, preserve autumn orientation/calendar contradiction.
sid='1vR0gVYttXYrTQxNhb900Gbr4BzwJFoJU';old='19_r844eDJUSvpbBQ5_VliZCKh3YAdaWK';r=record('ncu-087','布爾諾資訊科技學院FIT 2026–2027資料表，含Erasmus特定申請說明；母校未註年簡介')
f(r,'city','捷克布爾諾：大學行政地址Antonínská 1，資訊科技學院地址Božetěchova 2，宿舍辦公室Kolejní 2；三種地址分開，不能把行政樓當成學院上課或宿舍地點。',sid,[1])
f(r,'eligibility','母校舊介紹列大學部與研究所；2026–27新原件限資訊科技學院，且部分申請文字明指Erasmus。中央116雙邊交換是否適用同一方案仍未核實，不擴成全校通用。',old,[1]);more(r,'eligibility',sid,[1])
f(r,'language','母校未註年簡介列英語B2，可用證書或證明；資訊科技學院2026–27表未另列語言門檻。不能把舊簡介當116最新考試或免考核准。',old,[1])
f(r,'host_deadline','資訊科技學院2026–27：冬季電子申請3/31–5/31，需要簽證者提前至4/30；夏季申請及延長交換至11/15，需要簽證者提前至10/15。沒有提名截止與時區；Erasmus文字的中央雙邊適用性待核，不啟用116提醒。',sid,[1])
f(r,'host_documents','資訊科技學院表將電子申請列為Erasmus唯一申請方式，但未列初次附件；中央雙邊方案是否走同一入口也未核實，不自行補必繳文件。',sid,[1],gap='缺當期雙邊申請入口確認、完整附件及116表格。')
f(r,'study_period','2026–27資訊科技學院冬季9/7開始、夏季2027/2/8開始，每學期13週授課加5週考試。母校舊介紹夏季3月至7月，不能替代學院明列日期；116新校曆仍缺。',sid,[1]);more(r,'study_period',old,[1])
f(r,'courses','2026–27資訊科技學院表有課程連結，但網址仍帶year=2025；尚未核對其實際年度課單、課程先備與最低學分，不把新表標題當全部連結內容也已更新。',sid,[1])
f(r,'housing','2026–27資料表提供宿舍辦公室及線上申請入口，未列交換生保證名額、房型、租金、押金或住宿截止；不能從聯絡方式推定免費或保證入住。',sid,[1])
f(r,'insurance','母校舊簡介要求涵蓋整段停留期間保險並建議出發前辦理；未取得當期最低保額、可用保險或保費，校方舊文字不作政府核准。',old,[1])
f(r,'visa','母校未註年簡介請需簽證者向捷克使領館確認，並列至少出發前60日送件；這是舊校方建議，不是當期法定時效或審核完成保證。',old,[1])
f(r,'arrival','資訊科技學院2026–27強烈建議迎新，並規定最晚學期第一週完成註冊。文字稱迎新在開課前一週，但冬季迎新9/7–11與學期9/7開始在同週，原件有矛盾；夏季迎新2/1–5則在2/8開學前。須由接收校確認，不能自行平移日期或把建議改必到。',sid,[1])
js(S/'reviewed-host-records.json',records);js(D/'added-host-records.json',{k:records[k]for k in identity});print({'new_hosts':5,'fields':sum(len(records[k]['fields'])for k in identity),'source_documents':len(ledger),'pages':sum(len(i['pages_reviewed'])for i in ledger)})
