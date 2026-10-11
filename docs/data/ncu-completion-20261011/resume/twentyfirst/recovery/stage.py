from pathlib import Path
from datetime import datetime,timezone
import json,gzip,hashlib,base64,shutil
R=Path('/workspace/abroad');W=Path('/workspace/ncu-resume-work/twentyfirst');S=R/'sources/ncu/2026-10-11';B=R/'sources/ncu/2026-10-08';D=R/'docs/data/ncu-completion-20261011/resume/twentyfirst';D.mkdir(exist_ok=True);(D/'source-pages').mkdir(exist_ok=True)
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
 s['reading_status']='full_visual_and_native_reviewed';s['reading_review']={'source_sha256':s['sha256'],'pages_reviewed':pages,'full_document_read':True,'reviewed_at':now,'review_note':'20頁第二十一批全篇原生與原圖核讀；母校院別、學程與外校一般指引分列，原年、校區、條件與原件錯誤保留。'}
 s['visual_review']={'source_sha256':s['sha256'],'pdf_pages_reviewed':pages,'full_document_read':True,'reviewed_at':now,'method':'原生全文與逐頁view_image人工核對；非OCR','rendered_pages':renders,'page_notes_zh':{str(p):v for p,v in n['page_notes']}}
 s['reuse_license_note']='母校公開官方原件僅供查核；未取得頁內照片獨立開放授權，不轉作校景。'
 ledger.append({'source_id':sid,'row_id':rows[sid],'source_url':s['url'],'source_sha256':s['sha256'],'retrieved_at':receipts[sid]['receipt']['checked_at'],'reviewed_at':now,'document_year_scope':n['document_year_scope'],'pages_reviewed':pages,'native_full_read':True,'visual_full_read':True,'page_notes_zh':n['page_notes'],'current_116_approval':False,'license_scope':s['reuse_license_note'],'rendered_pages':renders})
 responses.append({'source_id':sid,'receipt':receipts[sid]['receipt'],'encoding':'base64','body':base64.b64encode(raw).decode()})
gz(B/'drive-evidence.json.gz',pack);gz(S/'resume-twentyfirst-original-responses.json.gz',responses);js(D/'fresh-fetch-receipts.json',list(receipts.values()));js(D/'reading-ledger.json',{'checked_at':now,'base_sha':'4bc5612b7fd3d4015014945ff75ab4a62761e81e','items':ledger})
identity={
'ncu-003':'母校舊ESC與新Clermont School of Business校徽、法國Clermont-Ferrand、4 boulevard Trudaine同址；學位與非學位交換分列。',
'ncu-057':'University of Geneva中英名、校徽、瑞士Geneva一致；Uni Dufour國際處24 rue du General Dufour為行政地址，不代表所有教學樓。',
'ncu-110':'Temple校名校徽、美國Philadelphia PA19122吻合；母校1801 N Broad St與Global Programs 1938 Liacouras Walk為校務與辦公用途，非東京或羅馬校區；中央自費方案不等於互惠Exchange。',
'ncu-145':'Dongguk校徽、韓國首爾Jung-gu/Pildong新舊址一致，不是慶州校區；生命科學與生技明列一山校區，不能全部套首爾上課。',
'ncu-204':'Universitas/University of Brawijaya同UB校徽、印尼Malang65145；母校JalanVeteran全校與FEB JalanMT.Haryono165院址分開，FEB特定方案不擴全校。'}
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
# Clermont: conditional B1, not an unconditional downgrade from B2.
sid='1ECGpDBzluK_H5EsPeU-yK4mkaV8X7dMR';old='1_21NXsggFlaHJ3UDg32CzPV6MDuM3Ee9';r=record('ncu-003','克萊蒙資料表檔名2026、正文未註年；母校語言格註2024更新')
f(r,'city','法國克萊蒙費朗，特呂代訥大道4號、郵遞區號63037；母校舊ESC名稱與新商學院名稱的校徽及地址對應，未推定新增校區。',sid,[1]);more(r,'city',old,[1])
f(r,'eligibility','母校列大學部與研究所；外校表把一般修課交換與雙聯／學位方案分開，資格不能混用，中央116實際開放方案待核。',old,[1]);more(r,'eligibility',sid,[2])
f(r,'language',['一般文件欄列授課語言最低B2；表格特別註明非學位交換可接受B1證明，母校2024更新嵌圖也保留此例外。不能把B1擴成所有學位、雙聯或中央116方案的通用門檻。','學位方案英語：母語者或TOEFL ITP550／iBT80、IELTS6、TOEIC750、Duolingo115、PTE通用3／學術58、ITEP學術3.9、ISE II、劍橋B2 First或C1 Advanced；法語學位為母語或B2。須先核實所選方案，不能選較低條件直接套用。'],sid,[2]);more(r,'language',old,[1])
f(r,'host_deadline','資料表學生申請秋季5/31、春季10/31，未列提名截止、時區或正文年度，不啟用116期限提醒。',sid,[1,2])
f(r,'host_documents','母校先提名姓名、現就讀學制、一般修課或雙聯類型、學生與母校窗口郵件；學生線上選合作校身分，再交四類附件：照片、護照或身分證明、前年度成績／學位證書、授課語言證明。語言文件按學位／非學位條件判定。',sid,[2])
r['host_documents']=[doc(n,sid,2)for n in ['照片','護照或身分證明','前年度成績／學位證書','授課語言證明（按學位／非學位方案門檻）']]
f(r,'study_period','正文未註年：秋季9月初至12月中，春季1月初至5月底；母校舊表秋9至12月、春1至5月。不能當116確切到離校日。',sid,[1]);more(r,'study_period',old,[1])
f(r,'courses','英授大學部1至3年級、研究所4至5年級秋春皆有；每學期至少8、最多30 ECTS。初中級法語全年免費，其他語言進階課學期中免費；課單試算表尚未逐課核對。成績A至E有學分、FX與F無；秋季成績單2月、春季6月中發布。',sid,[1])
f(r,'housing','合作房屋服務Moversia收費，含找私人住宿、接送與租務等行政協助，另列私人宿舍、租屋及擔保選項；不是免費或保證校內宿舍。母校旧表明說無法預訂學生宿舍，應由當期校方再確認；服務費、租金與押金未列。',sid,[2]);more(r,'housing',old,[1])
f(r,'cost','外校未註年正文估每月700–800歐元，含房租、餐食與帳單；首月押金、開通水電電話等另計。母校舊表為610–1050歐元／月，年度不同不選低值當116預算。',sid,[2]);more(r,'cost',old,[1])
f(r,'visa','資料表標題雖寫簽證與保險，正文只提非歐盟、停留逾三個月辦學生簽證並連主管機關；未列保險規則，不自行補值。這是未註年校方說明，實際簽證另按國籍與當期官方要求核對。',sid,[2])
f(r,'arrival','開學前提供線上與到校迎新、國際處協助及社團活動；原件未寫必到日期或全部強制。Moversia接送屬收費服務內容，非全體免費接機。',sid,[2])
# Geneva: faculty restrictions, language exceptions and document stages.
sid='1pqSP_a3saamO8OoJo21AI22MTr0TYuJi';old='1nkS_ocMRsINB0luAkc4m-1VxfUpZz6Fn';r=record('ncu-057','日內瓦2026–2027外校資料及未註年母校介紹')
f(r,'city','瑞士日內瓦，國際交換辦公室位於Uni Dufour、杜富爾將軍街24號，郵遞區號1211日內瓦4；這是行政聯絡處，不代表各學院授課地點。',sid,[1])
f(r,'eligibility','母校舊表列大學部與研究所；2026–27課程最多跨兩學院／機構，大學部不能選碩士課。經濟管理、法律、英語文學及英語語言學須在母校就讀相應主修，不能當成全校自由選課。',sid,[2]);more(r,'eligibility',old,[1])
f(r,'language',['2026–27標題寫建議程度，但正文要求授課語言B2，法語為主、部分英授；法語或英語文學領域原文明寫法語C1，不能自行改成英文C1。法語學校預備年B1、浸入年A2屬特定例外。','可用正式測驗或教授官方能力證明；兩語授課都選時須證明兩種能力。登錄頁另載目前授課語言適用的證明豁免，須條件確認。母校舊B2及心理教育法B2不取消新表特例；10瑞郎線上法語測驗不是全體必繳。'],sid,[1,2]);more(r,'language',old,[1])
f(r,'host_deadline','2026–27母校提名秋3/31、春8/31；學生登錄秋4/10、春9/10。文件完整才預期於5/30或10/30發錄取信，不是保證录取，亦非中央116截止。',sid,[1])
f(r,'host_documents','提名由母校提供姓名、郵件、學期、領域及特殊需求；初申六類為動機信、正式成績單、照片、護照、語言證明、學習計畫。語言證明有目前授課語言豁免條件，兩語選課須各自證明；簽證居留財力證明不加成初申第七件。',sid,[1,2,3])
r['host_documents']=[doc(n,sid)for n in ['動機信','正式成績單','照片','護照']]+[doc('授課語言能力證明',sid,1,condition='按所選語言／領域；目前授課語言適用豁免須確認，兩語選課需兩種證明')]+[doc('學習計畫',sid)]
f(r,'study_period','2026–27秋季2026/9/14至2027/2/12，春季2027/2/22至6/25，理學院延至6/30。秋考1至2月、春考5至6月，考試須實體出席，不能假設遠距考完即可早退。',sid,[1])
f(r,'courses',['每年夏季公布課單，申請先參考前一年、公布後調整；學習計畫須學期前核准，到校後僅小幅修改，不能整份或主學院全部更换，最多跨兩院且大學部不能修碩士課。','學前法語密集課為優惠價；學期中每週兩門免費法語支持課、各3 ECTS，報名後須出席。要求好成績的最低4是日內瓦0–6尺度，不是GPA4/4；各課先備與當期課單仍待核。'],sid,[2])
f(r,'housing','2026–27大學城一棟整修、房源減少，早提名先到先得，非保證住宿；超過34歲不能申請大學城住宿，並非不能租日內瓦其他房源。當期租金、押金與房型未列。',sid,[3])
f(r,'cost','2026–27生活估約每月2000瑞郎。母校舊表也列2000，但房租500、餐食基本600、保險100只合計1200，不是完整分解，不能自行補出差額；未核中央116預算。',sid,[3]);more(r,'cost',old,[1])
f(r,'insurance','2026–27校方要求健康及意外保險，可申請承認私人保單，或購瑞士學生方案每月65瑞郎起；私人保單不是自動接受，起價不是所有人的固定保費。母校舊約100瑞郎為不同資料，不混用。',sid,[3]);more(r,'insurance',old,[1])
f(r,'visa','校方2026–27建議非歐盟學生提前三個月詢瑞士使館，30歲以上簽證須特別批准，抵達後向OCPM辦居留；財力文件在簽證／居留階段。這些為校方說明，尚未核對當期政府要求，不代表個案獲准。',sid,[3])
f(r,'arrival','2026–27迎新為2026/9/11及2027/2/19；評量後約六週產生成績單，離校前須提供母校國際處郵寄地址以收正式成績。地址提供是後续程序，不是初申必繳件。',sid,[1,3])
# Temple: self-paying programme, initial five documents and I-20 children after acceptance.
sid='1fjbURDv94SGZ42PI-Sz04ECxnZ0R6vYV';old='1twa72-6AdXRzdVzGy8qTlcnlJaiRvO0J';r=record('ncu-110','天普外校正文2025–2026、學費2024–2025，母校未註年自費方案；檔名AY2026不升格')
f(r,'city','美國賓夕法尼亞州費城，母校原件校址為北布羅德街1801號；全球方案辦公室在Liacouras Walk 1938號203室，郵遞區號19122。兩者用途不同，不能套用東京或羅馬校區。',sid,[1]);more(r,'city',old,[1])
f(r,'eligibility',['母校自費方案列大二以上及研究所、GPA2.75/4；低於2.75可附至少一封教師推薦信供考慮，並非自動錄取。外校2025–26大學部須先完成兩個全時學期，互惠交換GPA3/4、自費訪學2.5/4，不能逕選較低門檻當中央116資格。','碩士依學程；博士不適用外校Exchange，不能推論所有自費博士已准或已禁。外校常見訪學每校同時10人、Exchange每年4個學期數，均非中央116人數；4學期不可填成4名。'],sid,[1,2]);more(r,'eligibility',old,[1])
f(r,'language','外校2025–26英語TOEFL iBT79／ITP550、IELTS6、Duolingo110、CEFR B2、TOEIC聽力與閱讀各390，不是總分390。未達者可能需語言中心課程，不保證條件錄取；母校舊表相同聽讀條件不能當116核准。',sid,[2]);more(r,'language',old,[1])
f(r,'host_deadline','正文2025–26秋季優先4/1、最終4/15，春季10/15；由母校先提名再獲線上申請連結，不把舊截止改成116提醒。',sid,[1])
f(r,'host_documents','原图縮排區分初申五類：當學期課表、正式語言成績、選課程序表、正式成績單、住宿協議（如適用）。I-20申請在錄取後，其下財力證明與護照個資頁屬該階段子項，不加成初申必繳。母校先提名、學生建帳上傳、校方審查後發接受資料。',sid,[1])
r['host_documents']=[doc(n,sid)for n in ['當學期課表','正式語言成績','選課程序表','正式成績單']]+[doc('住宿協議',sid,condition='申請住宿且外校要求時')]
r['host_document_stages']=[{'id':'accepted-i20','position':'after_host_application','field':'host_documents','timing':'外校錄取後，按個案身分確認I-20程序','title':'確認錄取後I-20文件','phase':'合作校申請','responsible_party':'學生與天普國際處','summary':'原件I-20明列錄取後，財力與護照為其縮排子項；母校舊J1與新文件路徑差異須再核，不自行判定簽證種類。','document_requirements':[doc(n,sid,1,'post_offer','外校錄取後且個案適用I-20程序')for n in ['I-20申請','財力證明（I-20附件）','護照個資頁（I-20附件）']]}]
f(r,'study_period','正文暫定2025秋8/25至12/16、2026春1/12至5/5，可一學期或全年。母校舊春季1至4月與外校正文不同，兩者均不當116確定校曆。',sid,[1,3]);more(r,'study_period',old,[1])
f(r,'courses','須符合課程先備與餘額，研究所課另經教授／系主任批准，在校須維持GPA2/4。建築、表演、資訊、專業學院、商學（須商科主修）、視覺藝術、教育與運動旅遊旅館課可能限額或需許可，不等於全部禁止。當期課單與學分上限未核。',sid,[2])
f(r,'housing','外校2025–26校內住宿先到先得，不保證房間；可另找校外住宿。食宿估7500美元／學期不是單純房租，住宿協議僅適用者需交。',sid,[1,3])
f(r,'cost',['母校明列自費學生須繳中央與天普兩校學雜費；美國籍可參加但以州外費率計，不能因外校表同時介紹互惠Exchange就誤標免學費。','外校每學期學費16956美元明註2024–25，雖正文2025–26仍不是同年新報價。508美元服務費僅訪學方案、175美元國際生費全體，課程另可能收費；食宿7500、旅行書籍個人2750美元／學期為概估，中央學雜費另計，不能當116總價。'],old,[1]);more(r,'cost',sid,[3])
f(r,'insurance','外校資料表示可購校方或獨立健康保險，費用依方案不同，沒有列最低保障額；不能由可自購推定任意保單皆獲接受。',sid,[3])
f(r,'visa','母校未註年自費表列J1，外校2025–26列錄取後I-20流程；兩者路徑不同，須由接收校及主管機關核實個案，不能自行改成F1或認定舊J1仍適用。',old,[1]);more(r,'visa',sid,[1])
f(r,'arrival','外校2025–26迎新在開學前一週，抵達日期於錄取後通知；暫定校曆不等於已確認航班或116報到日，未列免費接機。',sid,[3])
# Dongguk: master's cap, deferred insurance and one-semester housing.
sid='10uCIcGHCpV6nqVloAagGMONP8QL4Zazc';old='1nHSbJlL0JoiIS46Jp9YxBo-24tGP8aQA';r=record('ncu-145','東國標題2026–2027，內文校曆2026、課單2025；母校介紹未註年')
f(r,'city','韓國首爾中區筆洞路1街30號為國際處；生命科學與生物技術學院所有課程另在京畿道一山校區，不可全部顯示成首爾授課。母校舊筆洞地址與首爾身份相符，不是慶州分校。',sid,[1]);more(r,'city',old,[1])
f(r,'eligibility','外校2026–27要求GPA3/4.5，學制為大學部或碩士；母校舊表列大二以上／研究所，不能擴成博士也可。研究所只接受一般研究所，特殊或專業研究所不適用；名額僅寫依兩校協議，未公布中央116人數。',sid,[1]);more(r,'eligibility',old,[1])
f(r,'language','外校不要求語言能力證書，母校舊表也不要求英文測驗，但仍须有能力修讀相應語言課。多數研究所課為韓語，可選英授大學部課；舊英授25%與商英系50%不能當當期課程比例保證。',sid,[1]);more(r,'language',old,[1])
f(r,'host_deadline','2026–27表提名秋5/15、春11/15；申請秋5/30、春11/30。母校國際處統一寄件，不能自行送件或將這些日期當116已核期限。',sid,[1])
f(r,'host_documents','原件七類：申請表、中或英文正式成績單、在學證明、推薦信、護照、全停留海外保險、JPG頭照；成績／在學／推薦實際接受韓文或英文，中文原件須轉成該語種。母校國際處以郵件送件，不接受個人申請，不需紙本；保險證明可簽證核發後補，不能強制初申已備。',sid,[1])
# Keep exact accepted languages Korean/English (Chinese UI wording is not a source-language permission).
r['fields']['host_documents']['points']=['原件七類：申請表、韓文或英文正式成績單、韓文或英文在學證明、韓文或英文推薦信、護照、全停留海外保險、JPG頭照。母校國際處以郵件統一送件，不接受個人申請，不需紙本；保險證明可簽證核發後補，不能強制初申已備。']
r['host_documents']=[doc(n,sid)for n in ['申請表','正式成績單（韓文或英文）','在學證明（韓文或英文）','推薦信（韓文或英文）','護照影本','JPG頭照']]
r['host_document_stages']=[{'id':'visa-issued-insurance','position':'after_host_application','field':'host_documents','timing':'可於學生簽證核發後補交，並涵蓋全部停留期','title':'補交海外保險證明','phase':'合作校申請','responsible_party':'學生與母校國際處','summary':'原件七類中保險允許後補，故初申六件與本後續一件分列，不誤成可免保險。','document_requirements':[doc('涵蓋全部停留期的海外保險證明',sid,1,'post_offer')]}]
f(r,'study_period','標題2026–27但校曆明列2026春3月初至6月中、秋9月初至12月中，選課分別2月初與8月初，仍可能異動。母校舊秋8至1月、春2至6月不一致；課單欄還寫2025秋，不能由標題推定全部已更新。',sid,[1]);more(r,'study_period',old,[1])
f(r,'courses',['大學部至少一門、最多18學分；碩士至少兩門、最多9學分。底列一般至少一門、18學分不能覆蓋碩士較嚴格限制。研究所多韓語，可選英授大學部課，須避免與韓語課撞期。','大學部排除藥學、未來融合、韓國音樂、戲劇及體育文化；生命科學／生技在一山。另付費韓語班每季10週、折後1225000韓元，非學分課、不發國際處正式成績單，費用與時間可變。成績表D0為1分，但文字寫高於D0才給學分，原件差異保留待核。'],sid,[1,2])
f(r,'housing','校內宿舍不保證，最多一學期含假期；一年交換後段須自找住宿，原文部分句尾受版面截切，未自行補確日。忠武校外3至6人房有共用廚房、南山校內雙人房無廚房；每學期160萬至170萬韓元含水電，整筆繳。約1月／7月中通知分配，入宿另按通知繳結核檢查、MMR疫苗、保險等，非全部列入初申。',sid,[2])
f(r,'cost','外校估餐飲交通等每月35萬至50萬韓元；自租住房每月40萬至60萬另計，不能把住房說成已含生活估算。韓語班另付費、健保亦另有費用，這些皆為原週期參考，非中央116報價。',sid,[2,3])
f(r,'insurance','校方明寫兩種都需要：本國保險涵蓋全停留的意外傷害與住院醫療，加上韓國國民健康保險。不能二選一；居留卡核發後寄繳費單，約每月8萬韓元、依實單。此為校方2026–27說明，當期政府適用及保費須另核。',sid,[1,3])
f(r,'visa','校方資料列交換D-2-6，文件通過後錄取證明寄母校、學生列印向使館申請；所需簽證文件須查領館。母校舊D-2與紙本保險說明不直接變成116現行要求。',sid,[2]);more(r,'visa',old,[1])
f(r,'arrival','無機場接送服務；可安排學伴但不保證一對一，依招募情況。學期結束後一個月內電子成績單寄學生；入住宿與報到資料依分配通知，不自行增加初申附件。',sid,[2])
# Brawijaya: FEB-only, strict inequality, currency unspecified, LoA then course form.
sid='1QzL2RhXhbqKkiNsy_zl1H7IOn8qu22WG';old='1BmTecGKmVudvDqU_dlMpcFfu0LWFFiEi';poster='1Q7NgoqWBefphbjBdkdhrkoKNx4rLgSiF';r=record('ncu-204','布勞爪哇未註年FEB經濟商學院交換資料、海報及母校全校介紹')
f(r,'city','印尼東爪哇瑪琅市，母校介紹全校地址Jalan Veteran；經濟商學院地址Jalan M.T. Haryono 165，郵遞區號65145。院址與全校地址分列，不能把學院交換要求套全校。',sid,[1]);more(r,'city',old,[1])
f(r,'eligibility','母校未註年全校介紹列大學部／研究所；外校文件是經濟商學院國際學士方案相關窗口與院級交換，不能推定全校研究所或所有科系均適用，也未列中央116名額。',sid,[1]);more(r,'eligibility',old,[1])
f(r,'language','經濟商學院非英語母語者原圖列TOEFL ITP大於525、IELTS大於5.5或Duolingo大於95；符號是嚴格大於，不自行改成大於等於。母校舊表ITP500、IELTS5.5或TOEIC等值且無具體分數，與院級資料不同，不能擇低或自行換算。',sid,[1]);more(r,'language',old,[1])
f(r,'host_deadline','未註年經管院第一學期7/1、第二學期12/1截止；預計接受通知7/10、12/10，未列母校提名日。海報相同但無年度，不能當116期限。',sid,[1]);more(r,'host_deadline',poster,[1])
f(r,'host_documents','經管院初申十類：正式成績單、履歷、學校／學院聲明、學生證、推薦信、意向信、英語能力證明、有效護照、3×4白底照、申請表；全部英文或官方英文翻譯，統一上傳指定入口。收到錄取信後才發課單與填選課表，不把選課表加入初申第十一件。',sid,[1,2]);more(r,'host_documents',poster,[1])
r['host_documents']=[doc(n,sid)for n in ['正式成績單（英文或官方英文翻譯）','履歷（英文）','學校／學院聲明（英文或官方英文翻譯）','學生證（英文或官方英文翻譯）','推薦信（英文或官方英文翻譯）','意向信（英文）','英語能力證明','有效護照','3×4白底證件照','申請表（英文）']]
r['host_document_stages']=[{'id':'accepted-course-form','position':'after_host_application','field':'courses','timing':'收到外校錄取信後','title':'依錄取信課單填選課表','phase':'合作校申請','responsible_party':'學生與經濟商學院','summary':'資料表明列課單隨錄取信提供，選課表在收到錄取信後填寫，不要求初申已有最終課單。','document_requirements':[doc('選課表',sid,2,'post_offer')]}]
f(r,'study_period','未註年經管院奇數學期8至12月、偶數學期2至6月；母校舊全校介紹為9至2月、3至8月，兩者不同，應依接收方案確認，不能覆蓋或當116行程。',sid,[1]);more(r,'study_period',old,[1])
f(r,'courses','經管院全英授課，課單隨錄取信提供、之後才填選課表；採SKS，原件170分鐘與45.3小時描述未說清週／學期跨度，不自行換算ECTS。母校舊介紹另要求交換生修3學分印尼語文化並列入成績，院級新資料未確認，不能逕取消或擴為全部方案現行必修。第一學期成績單1月、第二學期7月寄出。',sid,[1,2]);more(r,'courses',old,[1])
f(r,'housing','經管院未註年資料列校內宿舍$350／六個月、依房型，校外$150–250／月；原件只用$未明幣別，不能直接填美元。沒有保證床位、押金或申請截止，母校僅說可宿舍或校外租屋。',sid,[2]);more(r,'housing',old,[1])
f(r,'cost','經管院估生活$120–200／月，原件未註$幣別或完整包含範圍；母校舊表300美元／月另列，不能混為同年或同方案。海報免學費只指經管院交換，不代表免中央學雜費、住宿或生活成本。',sid,[2]);more(r,'cost',old,[1]);more(r,'cost',poster,[1])
f(r,'visa','經管院只提供簽證與許可手冊連結及全校窗口，手冊尚待全文讀取；不能從連結存在推定簽證種類、財力門檻、費用或時程。',sid,[1,2],gap='簽證手冊、國籍適用與當期政府要求仍待核讀。')
f(r,'arrival','有需要朱安達機場接送者須先向校方確認；機場至校概估97公里、兩小時，沒有保證免費或已安排。成績單於第一學期後1月、第二學期後7月寄送，未提供116迎新確日。',sid,[2])
js(S/'reviewed-host-records.json',records);js(D/'added-host-records.json',{k:records[k]for k in identity});shutil.copy2(W/'latest-donor-photo-review.json',D/'latest-donor-photo-review.json')
print({'new_hosts':5,'fields':sum(len(records[k]['fields'])for k in identity),'source_documents':len(ledger),'pages':sum(len(i['pages_reviewed'])for i in ledger)})
