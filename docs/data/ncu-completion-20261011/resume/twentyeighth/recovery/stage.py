from pathlib import Path
from datetime import datetime,timezone
import json,gzip,hashlib,base64,shutil,copy,subprocess
R=Path('/workspace/abroad');W=Path('/workspace/ncu-resume-work/twentyeighth');S=R/'sources/ncu/2026-10-11';B=R/'sources/ncu/2026-10-08';D=R/'docs/data/ncu-completion-20261011/resume/twentyeighth';D.mkdir(exist_ok=True);(D/'source-pages').mkdir(exist_ok=True)
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()=='1232d4b3f74d2bf25a07795d451252f9b17f002c'
now=datetime.now(timezone.utc).isoformat()
def js(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def gz(p,x):p.write_bytes(gzip.compress(json.dumps(x,ensure_ascii=False).encode(),mtime=0))
receipts={r['source_id']:r for r in json.load(open(W/'all-fetch-receipts.json'))};pack=json.load(gzip.open(B/'drive-evidence.json.gz'));byid={s['id']:s for s in pack};notes=json.load(open(W/'reading-notes.json'));mapping=json.load(open(W/'candidate-identity-mapping.json'));rows={sid:r['row_id']for r in mapping for sid in r['files']};ledger=[];responses=[]
for n in notes:
 sid=n['source_id'];s=byid[sid];pages=list(range(1,len(s['pages'])+1));assert n['native_pages_read']==n['visual_pages_read']==pages
 raw=(W/f'{sid}.pdf').read_bytes();assert hashlib.sha256(raw).hexdigest()==s['sha256']==n['sha256']==receipts[sid]['sha256']
 renders=[]
 for page in pages:
  p=W/f'{sid}-p{page:02}.png';q=D/'source-pages'/p.name;shutil.copy2(p,q);renders.append({'pdf_page':page,'path':str(q.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 s['reading_status']='full_visual_and_native_reviewed';s['reading_review']={'source_sha256':s['sha256'],'pages_reviewed':pages,'full_document_read':True,'reviewed_at':now,'review_note':'8份17頁第二十八批全篇原生與原圖核讀；方案、年度、學科限制與原件衝突保留。'}
 s['visual_review']={'source_sha256':s['sha256'],'pdf_pages_reviewed':pages,'full_document_read':True,'reviewed_at':now,'method':'原生全文與逐頁view_image人工核對；非OCR','rendered_pages':renders,'page_notes_zh':{str(p):v for p,v in n['page_notes']}}
 s['reuse_license_note']='母校公開官方原件僅供查核；未取得頁內照片獨立開放授權，不轉作校景。'
 if n.get('selected_passages'):
  s['visual_review']['page_transcriptions']=n['selected_passages'];s['visual_review']['include_native_with_selected_passages']=True
  s['page_transcriptions']=n['selected_passages']
  js(B/f'{sid}-visual-review.json',s['visual_review'])
 ledger.append({'source_id':sid,'row_id':rows[sid],'source_url':s['url'],'source_sha256':s['sha256'],'retrieved_at':receipts[sid]['receipt']['checked_at'],'reviewed_at':now,'document_year_scope':n['document_year_scope'],'pages_reviewed':pages,'native_full_read':True,'native_text_limitations':n.get('native_text_limitations'),'blank_visual_pages':n.get('blank_visual_pages',[]),'selected_passages':n.get('selected_passages',[]),'visual_full_read':True,'page_notes_zh':n['page_notes'],'current_116_approval':False,'license_scope':s['reuse_license_note'],'rendered_pages':renders})
 responses.append({'source_id':sid,'receipt':receipts[sid]['receipt'],'encoding':'base64','body':base64.b64encode(raw).decode()})
gz(B/'drive-evidence.json.gz',pack);gz(S/'resume-twentyeighth-original-responses.json.gz',responses);js(D/'fresh-fetch-receipts.json',list(receipts.values()));js(D/'reading-ledger.json',{'checked_at':now,'base_sha':'1232d4b3f74d2bf25a07795d451252f9b17f002c','items':ledger})
js(D/'identity-review.json',mapping)
records=json.load(open(S/'reviewed-host-records.json'));base=json.load(open(B/'reviewed-host-records.json'));before=copy.deepcopy(records);changes=[]
LIMIT='中央116校別、名額、方案與實際校區仍未核實；以下依原件學年作參考，不啟用期限提醒。'
for sid,rid in rows.items():
 if rid not in records:records[rid]={'source_ids':[],'fields':{},'applicability':'中央公開未年學校介紹，僅歷史參考。','host_documents':[]}
 if sid not in records[rid]['source_ids']:records[rid]['source_ids'].append(sid)
 records[rid]['checked_at']=now
 records[rid]['applicability']+='；第二十八批核讀'+next(n['document_year_scope']for n in notes if n['source_id']==sid)+'。'+LIMIT

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
rid='ncu-075';sid='1b-WhgD6NfDCo3KDw1YFZn2wKcL8B296S'
field(rid,'city','2027–28資料表為義大利錫耶納外國人大學，Piazza Carlo Rosselli 27/28；不是另一所錫耶納大學。',sid,[1])
field(rid,'eligibility','2027–28表提供人文學系三年制學士及兩年制碩士課程，交換須依雙邊協議。資料表年份雖對應116，中央校別、名額與本人可提名方案尚未確認；表未給中央名額，不從協議推導數量。',sid,[1])
field(rid,'language','2027–28學位課須義大利語B2，授課語言只列義大利語、沒有其他語言；較低程度可參加按月義大利語課程，不代表可直接修B2學位課。',sid,[1])
field(rid,'host_deadline','2027–28表：秋／全年提名5月31日、學生申請7月15日；春提名10月31日、學生申請12月15日。提名與申請分開，中央116方案仍未核，不啟用期限提醒。',sid,[1])
field(rid,'host_documents','2027–28表初申列申請表與護照影本兩項；接獲母校提名後才寄申請表給學生。後續簽證及居留材料不併入初申必繳清單，最新版空白表尚未取得。',sid,[1])
records[rid]['host_documents']=[doc('交換申請表（母校提名後外校寄給本人，空白原表未取得）',sid),doc('護照影本',sid)]
field(rid,'study_period','2027–28秋授課2027年9月底至2028年1月底，考試1月底至2月底；春授課2028年3月初至6月中，考試6月中至7月底。不能把授課結束當完成考試或保證離校日。',sid,[1])
field(rid,'courses','2027–28可跨不同學位課程選課，但排除「國際視野下的義大利語、文學與藝術」線上學位課程；交換可免學費參加義語課三個月，不是整年免費。考試0–30分、18及格、30可附優等註記，原表等級對照不保證中央抵免。',sid,[2])
field(rid,'tuition','2027–28資料表在交換生必繳校方費用欄回答沒有；另列義語課免費三個月。這不代表食宿、保險或居留規費免費，也不自動核准中央116方案。',sid,[1,2])
field(rid,'housing','2027–28表提供找房協助，雙人宿舍床位有限、建議提前預訂，不保證住宿。私人住房參考：市中心單人400歐元、郊區單人350、市中心雙人每人300；第四項又寫郊區單人250。兩個郊區單人價格照原保留，未擅改房型；房價均未標計價週期，不自行當月租。',sid,[2])
field(rid,'cost','2027–28表列單次食堂全餐8.50歐元、披薩店餐20、早餐3；70分鐘公車票2、三個月票107.30歐元。三個月票不是月票，住宿價格另未標週期，沒有完整每月生活總額。',sid,[2])
field(rid,'transport','2027–28表公車單票2歐元有效70分鐘，三個月通行票107.30歐元；未列接機或指定通勤路線，不當即時交通保證。',sid,[2])
field(rid,'insurance','2027–28校方表將健康保險列為居留重要要求，建議保單涵蓋醫療及住院；自願加入公共醫保列每年700歐元，非每月或全體必須購買該方案。母國保單章戳及本人適用須按當期主管機關要求另核。',sid,[2,3])
field(rid,'visa','2027–28校方流程提到Universitaly預註冊、適用者申請簽證，D類逾90日者抵達後8工作天內辦居留。居留材料為護照個資頁、簽證頁、醫保、交換錄取信及住址證明副本；另印花16、郵局30、電子許可70.46歐元。這是錄取後有條件流程及校方規費參考，不是全部學生初申文件或本次已核當期法律。',sid,[2,3])
field(rid,'arrival','2027–28表預計收到填妥申請表約5工作天寄錄取信給學生與母校，不保證五天必錄取；成績單須另寄信申請，秋考後約2月底、春考後約8月初寄給兩方。適用居留者另依郵局收據完成警局指紋預約。',sid,[3])
rid='ncu-073';sid='1cxiSNWUhl6aaO2rqEgKJwBc4ku7QPJAF'
field(rid,'city','另份Comillas資料表明載2022–23：國際處郵址Alberto Aguilera32、ICAI工學院25、商法學院23；同路不同單位，不把三個門牌改成同一棟。其他學院分布Cantoblanco等校區，不能取消中央工學院／資電學院限制。',sid,[1,2])
field(rid,'host_deadline','2022–23舊表只列提名：非EU秋2022/5/1、春2022/10/1；Erasmus另6/1及11/1。這不是學生申請截止，也不能改標2027或116；當期學生截止仍未核。',sid,[1],append=False)
field(rid,'study_period','2022–23舊表授課秋2022/9/1至12/7、春2023/1/16至4/28，另學期末考試及6月補考；須等確定考試安排再訂離校旅行。與未年介紹約期不同，保留年度差異，未生成當期行程。',sid,[1])
field(rid,'courses','2022–23舊表中「國際學生西班牙語」課須先線上分級測驗，通知另寄本人；不是全體交換入學都須西語測驗。各學院課程問對應協調人，校區名單不等於中央協議全開。',sid,[1,2])
field(rid,'housing','2022–23表列Lodgerin、Aluni、MadridEasy、Erasmusplay及Innfamily等外部住宿協作商；不表示自有宿舍或保證床位，未列房價及申請截止。',sid,[1],append=False)
field(rid,'insurance','2022–23表非EU且未被西班牙公共醫療涵蓋者須全期疾病、住院、意外、民責及運返保障；相比未年介紹多列運返，不自行刪除。EU／EEA／瑞士另列歐洲醫療卡，個人當期適用仍需確認。',sid,[2])
field(rid,'arrival','2022–23一般迎新與各學院迎新由通知或電子郵件告知；國際生24小時緊急服務卡須取得帳密後下载，本表未列電話，不虛構號碼或日期。',sid,[1,2])
rid='ncu-109';sid='1AnG1Xklcp86rE396xF6E0C1Uz_Lomeby'
field(rid,'eligibility','2025–26一般Exchange表要求有效協議母校提名、GPA至少2.5（系所可更高）、在母校持續攻讀學位且學業與紀律狀態良好。抵達前已取得學位者不能作大學部交換；中央未年介紹另排除管理學院，保留母校限制與付費方案待核。',sid,[2])
field(rid,'language','2025–26表正式iBT70、工程79；IELTS6、工程6.5；PTE Academic53，部分系所可更高，不收Institutional TOEFL。英語非官方語言國家學生不因母校全英授或不同主修自動免正式測驗。表格另列Duolingo105，但同頁說明只列TOEFL／IELTS／PTE，保留內文差異待校方確認。',sid,[2,3])
field(rid,'host_deadline','2025–26一般Exchange秋／全年提名3/1、申請3/15；春提名9/15、申請10/1，提名被接受後才寄申請指示，處理預留約8週。中央付費方案及116適用仍未核。',sid,[1],append=False)
field(rid,'host_documents','2025–26表明列正式語言成績並排除Institutional TOEFL；部分藝術、音樂、舞蹈、建築等進階課可能需作品集或試演，不當全體初申必交。表只說提名後寄申請指示，完整初申清單仍未知。',sid,[2,3],append=False,gap_only=True,unresolved='已核部分語言及學科条件；同一付費方案的完整初申清單尚未取得。')
records[rid]['host_documents']=[doc('正式英語測驗成績（2025–26一般Exchange規則，付費方案適用另核）',sid,3,condition='英語非官方語言國家學生；母校英授不自動豁免。')]
field(rid,'courses','2025–26商科原則不開，例外BNAD449秋、450春、201秋；301／302／303幾乎額滿且畢業班優先，不能抵銷中央管理學院派出限制。資工最多三門、本校主輔修優先，至少另選一門外系以滿12學分。影視300／400專業課、零售消費科學、平面設計／插畫／字體及護理不開；影視通識看餘額，藝音舞建築進階課可能須作品集或試演。',sid,[2])
field(rid,'study_period','2025–26表秋2025/8/25至12/18、春2026/1/14至5/14，兩季迎新均在抵達前線上進行；不是116學年。校曆連結路徑有2023–24但錨點2025–26，不依URL較舊文字改掉文件標年。',sid,[1,3])
field(rid,'insurance','2025–26一般Exchange全體自動加入亞利桑那大學醫保，首日上課前繳費。豁免須符合校方保障規格、由母校或承辦機構提供並由母校代買團體保單，個案審核且很少批准；個人自行買的保單不能豁免。這與UCI自備保單說明是不同學校，不能互套。',sid,[3])
field(rid,'arrival','2025–26秋春迎新都在抵達前線上辦理；本表未列具體場次，錄取處理約8週亦非保證錄取日。',sid,[1,3])
rid='ncu-068';sid='1VjEap3Ca0WyulBsNZ24yNQ8hlIoPH-9C'
field(rid,'city','中央未年介紹對應德烏斯托大學西班牙畢爾包校區，地址Unibertsitate Etorbidea24；不將其他分校區視為同一通勤點。',sid,[1])
field(rid,'eligibility','中央未年介紹列大學部及研究所；研究所課程須學程主任批准，可能另要求成績單，不能把條件式審查當全體統一文件。',sid,[1])
field(rid,'language','原頁影像表：大學部一般英語或西語至少B1、強烈建議B2；工程學位B2為必要，現代語言部分課需B2或C1。外校說大學部不需正式證書，不取消中央校內語檢。碩博士通常須授課語C1、依學程確認；不能把B1套到所有層級。',sid,[1])
field(rid,'courses','未年原件建議不會西語者先參加學前密集西語，常規學期零程度班不保證；兩類語言課免課費但教材另計。只修英語者須來前確認有足夠英授課，沒有完整課程名單或名額保證。',sid,[1])
field(rid,'study_period','未年介紹秋9月至1月、春2月至6月，沒有確切學年或考試日，不改標116。',sid,[2])
field(rid,'host_documents','原頁只說研究所接收由學程主任批准，可能另要成績單；沒有全體完整初申附件或空白申請表，未自行補成統一必繳。',sid,[1],gap_only=True,unresolved='完整初申清單、條件式文件與116學程待核。')
field(rid,'host_deadline','原件只列交換學期及舊入口，沒有提名或學生截止。',sid,[2],gap_only=True,unresolved='當期兩階段期限未取得。')
field(rid,'housing','原件住宿欄只有短網址，未提供房型、價格、期限或保證條款；連結存在不等已讀其內容。',sid,[2],gap_only=True,unresolved='需續讀官方住房來源及116適用。')
field(rid,'cost','原件未列完整生活費；語言課免課費但教材另付，不能擴成一般交換所有學雜費或生活免費。',sid,[1,2],gap_only=True,unresolved='完整預算、房租及計價週期待查。')
rid='ncu-015';sid='1V2l_TJuu9UEVPq7Mr-TLvaZKwIFAakqq'
field(rid,'city','中央未年介紹為巴黎天主教大學ICP，21 Rue d’Assas、Paris75006法國；不是里爾、里昂等其他天主教院校。',sid,[1])
field(rid,'eligibility','未年介紹列大學部及研究所；校史簡介標示摘自維基百科，不拿校史或聯盟名單當交換資格或開放學院依據。',sid,[1])
field(rid,'language','未年介紹僅修全英語課者需英文B2證明；學士法語課最低B1、強烈建議B2，碩博士法語課需C1。建議B2不能改成學士硬性最低，也不能把法語C1套到只修英語課者。',sid,[2])
field(rid,'courses','未年介紹最多30 ECTS每學期、每ECTS約25–30工作小時，不是最低30。多數課法語；原文說自2023年9月起，英語課只在文學院與社會科學／經濟／法律學院，神學、教會法、哲學、教育沒有英語課；2023起始描述不是文件學年或當期完整課單。',sid,[1])
field(rid,'study_period','未年介紹稱冬學期9月至12月、春2月至6月，沒有116確切校曆或考試安排。',sid,[2])
for key,label in [('host_documents','完整初申文件及表格'),('host_deadline','提名與學生申請期限'),('housing','住宿申請及房價'),('cost','每月生活預算')]:field(rid,key,'這份兩頁未年介紹沒有列出'+label+'；既有課程或學期文字不能填補該缺口。',sid,[1,2],gap_only=True,unresolved=label+'仍需從當期官方來源續查。')
rid='ncu-105';sid='1BXTeoOlQECl9TMR4sISlJQPyUjt6bwU7'
field(rid,'eligibility','2026–27 NAU表允許碩士生以大學部身分参加交換，並寫可修大學及研究所課；已讀官網則說500–799課通常不提供，保留身分允許與實際課程可得性的差異，不能保證研究所課有位。',sid,[1])
field(rid,'language','2026–27表明寫新TOEFL自2026/1/21起最低3.5，與已讀官網誤寫2016不同；新表提供年份佐證，不抹去原頁錯字。舊iBT70接受MyBest且ETS直寄、IELTS6、Duolingo95直寄；B2替代明限歐洲交換生，英授高中／大學證明依條件，不取消中央語檢。',sid,[1])
field(rid,'language','另一份中央未年NAU介紹分大學iBT70／IELTS6、研究所iBT80／IELTS6.5；與2026–27表碩士按大學部身分交換的說明分開保留，不把舊研究所門檻自動套所有碩士交換。','1Bqbinel4T1rSs7y1mw0d6MAsfk1fdfUQ',[1])
field(rid,'host_deadline','2026–27表秋提名2026/3/15、學生4/1；春提名2026/9/15、學生10/1，母校提名後收到邀请才申請。遲交可能個案接受，不代表普遍延長。同母校所有被提名者完成申請後寄錄取及DS-2019套件，非個人提交即寄。',sid,[1])
field(rid,'study_period','2026–27表秋2026/8/24至12/11、春2027/1/11至5/7，前一週新生迎新；與未年介紹秋8–12、春1–5月份分開，不移作116校曆。',sid,[1])
field(rid,'courses','2026–27表英文授課、每學期至少12面授學分、最多19學分（通常4–6課）；牙科衛生及護理不開，音樂另較高要求，實際選課看資格及餘額。',sid,[2])
field(rid,'housing','2026–27表多數交換生住International House，但校內房有限，錄取後應立即申請；「多數入住」不是全體住宿保證。',sid,[2])
field(rid,'cost','2026–27表總額秋10903、春11605、全年20808美元，不含個人支出，另建議每學期至少1500美元，特殊課另收費。全年住宿8499不同於兩個單學期5099相加；學生費全年1625、單期813兩次則差1美元，按原表保留，不自行校正或把學年總額換成月費。',sid,[2])
field(rid,'insurance','2026–27表所有交換生購NAU醫保直接記學生帳，另麻疹接種證明為註冊課程要求；官網特定身分保險豁免另存，不能把本表概述變成所有人無例外。麻疹證明不是這份表已列的完整初申附件。',sid,[2])
field(rid,'arrival','未年NAU折頁要求開課前一週迎新，提供社團、無障礙支援及校內工作／實習探索入口；工作資訊不是聘用或本人工作資格保證。','1Pv7Sy8im0xCmvBGkZQk4JfITr0t3iLMC',[2])
# Explicit data correction after country, city, branding and all three originals were reviewed.
p=B/'source-map-candidates.json';maps=json.load(open(p));ua=next(x for x in maps if x['row_id']=='ncu-109');nau=next(x for x in maps if x['row_id']=='ncu-105');prior=copy.deepcopy(ua);remove=['1Pv7Sy8im0xCmvBGkZQk4JfITr0t3iLMC','1BXTeoOlQECl9TMR4sISlJQPyUjt6bwU7','1Bqbinel4T1rSs7y1mw0d6MAsfk1fdfUQ'];assert set(remove)<=set(ua['files'])and set(remove)<=set(nau['files'])
ua['files']=[f for f in ua['files']if f not in remove];ua['matched_entries']=[x for x in ua['matched_entries']if x['id']not in ['1JwYOWk2TuXimG-Ym9bF_fWtqu_93fZ1n','1Bqbinel4T1rSs7y1mw0d6MAsfk1fdfUQ']];ua['matching_status']='human_identity_reviewed_nau_excluded_ua_programme_scope_pending';ua['identity_review_note']='三份NAU原件逐頁核讀：美國Flagstaff、NorthernArizonaUniversity及nau.edu，屬ncu-105；不是ncu-109TucsonUniversityofArizona，不共用來源。UA剩餘付費與Exchange方案適用另核。'
js(p,maps);js(D/'source-map-correction.json',{'checked_at':now,'before':prior,'after':ua,'retained_correct_row':nau,'removed_wrong_school_files':remove,'evidence':next(n for n in notes if n['source_id']==remove[1]),'shared_matcher_changed':False})
js(S/'reviewed-host-records.json',records);js(D/'field-reconciliation.json',changes);js(D/'added-host-records.json',{rid:records[rid]for rid in set(rows.values())})
print({'documents':len(notes),'pdf_pages':sum(len(n['visual_pages_read'])for n in notes),'hosts':len(set(rows.values())),'new_hosts':3,'updated_fields':len(changes)})
