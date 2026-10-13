from pathlib import Path
from datetime import datetime,timezone
import json,gzip,hashlib,base64,shutil,copy,subprocess
R=Path('/workspace/abroad');W=Path('/workspace/ncu-resume-work/twentysixth');S=R/'sources/ncu/2026-10-11';B=R/'sources/ncu/2026-10-08';D=R/'docs/data/ncu-completion-20261011/resume/twentysixth';D.mkdir(exist_ok=True);(D/'source-pages').mkdir(exist_ok=True)
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()=='46c70072273f4b472b6ed8a5b2fe2ece66e8bd93'
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
 s['reading_status']='full_visual_and_native_reviewed';s['reading_review']={'source_sha256':s['sha256'],'pages_reviewed':pages,'full_document_read':True,'reviewed_at':now,'review_note':'5份10頁第二十六批全篇原生與原圖核讀；方案、年度、學科限制與原件衝突保留。'}
 s['visual_review']={'source_sha256':s['sha256'],'pdf_pages_reviewed':pages,'full_document_read':True,'reviewed_at':now,'method':'原生全文與逐頁view_image人工核對；非OCR','rendered_pages':renders,'page_notes_zh':{str(p):v for p,v in n['page_notes']}}
 s['reuse_license_note']='母校公開官方原件僅供查核；未取得頁內照片獨立開放授權，不轉作校景。'
 ledger.append({'source_id':sid,'row_id':rows[sid],'source_url':s['url'],'source_sha256':s['sha256'],'retrieved_at':receipts[sid]['receipt']['checked_at'],'reviewed_at':now,'document_year_scope':n['document_year_scope'],'pages_reviewed':pages,'native_full_read':True,'visual_full_read':True,'page_notes_zh':n['page_notes'],'current_116_approval':False,'license_scope':s['reuse_license_note'],'rendered_pages':renders})
 responses.append({'source_id':sid,'receipt':receipts[sid]['receipt'],'encoding':'base64','body':base64.b64encode(raw).decode()})
gz(B/'drive-evidence.json.gz',pack);gz(S/'resume-twentysixth-original-responses.json.gz',responses);js(D/'fresh-fetch-receipts.json',list(receipts.values()));js(D/'reading-ledger.json',{'checked_at':now,'base_sha':'46c70072273f4b472b6ed8a5b2fe2ece66e8bd93','items':ledger})
js(D/'identity-review.json',mapping)
records=json.load(open(S/'reviewed-host-records.json'));base=json.load(open(B/'reviewed-host-records.json'));before=copy.deepcopy(records);changes=[]
LIMIT='中央116校別、名額、方案與實際校區仍未核實；以下依原件學年作參考，不啟用期限提醒。'
for sid,rid in rows.items():
 if sid not in records[rid]['source_ids']:records[rid]['source_ids'].append(sid)
 records[rid]['checked_at']=now
 records[rid]['applicability']+='；第二十六批核讀'+next(n['document_year_scope']for n in notes if n['source_id']==sid)+'。'+LIMIT

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
rid='ncu-060';sid='13fvTs2j9VwsZKxmTjGxqI2bvhBzUSr07'
field(rid,'language','2026–27新版要求最低B2：全課程英語授課的派出校可出具母校證明信，其他學生可用TOEFL79（原表未標制式）、IELTS6.0或原列Cambridge CFE、CAE、CPE。CFE是原件拼法，測驗名稱及效期須確認；英授母校可用信件，不等於不用任何B2證明。',[sid][0],[1])
field(rid,'host_deadline','2026–27新版仍列提名秋4/15、春10/15，學生申請秋4/30、春10/30；提名後寄網申連結。這不是中央116的2027–28期限。',sid,[1])
field(rid,'host_documents','2026–27仍列八類：護照或身分證、護照照片、履歷、動機信、成績單、健康與責任保險確認聲明、B2語言證明、學習協議。新版語言欄明列全英授派出校可用正式母校信，其餘用所列測驗；不能沿用舊版條件而把英授學生當作完全免證明。保險確認聲明仍不是已投保保單。',sid,[1])
records[rid]['host_documents']=[doc(name,sid)for name in ['護照或身分證掃描','護照尺寸照片','履歷','動機信','成績單','健康與責任保險確認聲明（不是已投保保單）','B2語言能力證明（全英授母校可用正式證明信，其餘依測驗規則）','學習協議']]
field(rid,'study_period','2026–27學士秋從2026/9/7那一週起至12/18，不能把「那一週」改成確定9/7報到；春2027/1/28至6/25。碩士秋2026/9/3至12/18、春2027/1/6至6/25。新版考試及補考全部待確認，不能沿用2025–26考日或保證學期末即可離校。',sid,[1])
field(rid,'courses','2026–27新版明列不能跨學程混選；與母校協調人選定一個學程，再在其中選課。仍採美制學分、每學分約15面授小時，但新版未再寫最低15美制學分=30 ECTS，舊版最低負荷不能自行當作新期硬性要求。',sid,[1])
field(rid,'housing','2026–27同樣沒有校內住宿，學生自行找房付款，學服提供協助。單房參考改為650–800歐元、公寓800–1200歐元，仍未標計價週期；不補成月租，也不混用2025–26單房600歐元下限。',sid,[2])
field(rid,'cost','2026–27只有住宿價格範圍且未標週期，沒有完整每月預算；新版單房650–800歐元不能当每月生活總額。',sid,[2])
field(rid,'tuition','2026–27學生社團費每學期87.50歐元仍明列待確認；不是交換學費或已核116收費。',sid,[2])
rid='ncu-065';sid='18gqKN0ML2pIZLf1aVd8BM7fBKsjyoxba'
field(rid,'eligibility','2026–27外校一般表要求按雙邊協議指定的學院申請，不能因聯絡窗口表列藝術、音樂或健康學院，就取消中央母校派出院別限制。',sid,[1,2])
field(rid,'language','2026–27漢斯外校不要求交換生另交英語能力證明，但要求派出校選出至少B2程度者。這是外校收件規則，不能取消中央校內甄選的語言門檻或附件。',sid,[2])
field(rid,'host_deadline','2026–27：秋提名3/15至5/15、學生申請4/15至6/1；春提名9/15至10/15、學生申請10/1至11/1。母校與學生兩個窗口分開，不能互相代用或改標116。',sid,[2],append=False)
field(rid,'host_documents','2026–27提名由母校填線上表，學生另網申上傳文件；本資料表沒有完整附件清單，只明列學習協議由接收學院核准簽署。外校不收英語證明不等於中央免繳，未把護照、成績等常見附件自行補為必繳。',sid,[2],append=False,gap_only=True,unresolved='已確認提名／申請入口與學習協議簽署方，完整附件及116當期通知仍待核。')
records[rid]['host_documents']=[doc('出發前學習協議（由漢斯接收學院核准；非完整初申清單）',sid,2,signatures=['漢斯接收學院'],stage='post_offer')]
field(rid,'study_period','2026–27一般秋學期9/1至2/1、春學期2/1至7/1，實際學院校曆另查；工程課程的秋／春開設限制仍分別適用，不以一般學期替代逐課季節。',sid,[2])
field(rid,'courses','2026–27採固定課組，因課表限制不能跨學程自由拼課；依協議所列接收學院選方案，學習協議及課程問題由該學院確認。語言中心課名額有限、費用各異，不是保證免費。',sid,[2])
field(rid,'housing','2026–27明列學生自行找房，應及早開始；校方住宿窗口提供建議與協助，不是配房或床位保證。資料表未列房型、價格、押金及申請期限。',sid,[1,2],append=False)
field(rid,'insurance','2026–27資料表建議全期足額保險，並說明非EU學生由移民團隊向AON辦理；未列保費或保單完整保障，不能當全部免費或任何風險均涵蓋。',sid,[1,2])
field(rid,'visa','2026–27校方說明非歐洲學生的簽證／許可程序在錄取後由移民團隊聯絡，程序涉及財力保證款；本表未給金額，不能當学費或生活總額。這是校方流程參考，本人國籍與116法律適用仍須主管機關確認。',sid,[2])
field(rid,'arrival','2026–27每學期開始有迎新日，但本表未列確切日期；接機服務提供申請入口，不代表免費或已安排接送。語言課名額有限且另有費用。',sid,[2])
rid='ncu-022';sid='1vODypBeHScxOw41FSLYABSWq-ggmGDVp'
field(rid,'eligibility','2026–27一般交換按商科背景分級：Level 2至少60 ECTS／一年，Level 3與4至少120 ECTS／兩年，Level 5須學士程度或180 ECTS／三年。雙學位須專門協議，不能當一般交換；其PGE資格行在原件頁底被截斷，未自行補出缺文。',sid,[1])
field(rid,'language','2026–27一般學分交換為英語B2，可用TOEFL、TOEIC、IELTS或母校證明；Level 2國際事務方向另需法語B2。雙學位另列原文TOEFL iBT >80、IELTS >6.5、TOEIC >785或>800按學程，不能套成一般交換最低分。母語英語免測驗，但原表一般交換證明寫所有人，是否免母校信仍待確認。',sid,[2])
field(rid,'host_deadline','2026–27秋提名5/10、學生5/20；春提名10/10、學生10/20。提名連結於3月及9月寄母校，學生提名後另收到網申連結；不是中央116截止。',sid,[1])
field(rid,'host_documents','2026–27資料表列九類附件但分方案：五項共通為已簽母校協調表、一張護照照、護照（EU公民才可用身分證）、蓋校章正式成績單、英文履歷；一般學分交換另英語證明，Level 2國際事務方向另法語證明。正式TOEFL／TOEIC／IELTS成績單及動機信兩項是雙學位專用，不能要求所有一般交換都交；網申表本身另在系統填。',sid,[1,2])
records[rid]['host_documents']=[doc('線上申請表（提名後系統通知）',sid),doc('已填妥及簽署的母校協調人表',sid,signatures=['母校協調人']),doc('一張護照規格照片',sid),doc('護照影本（EU公民才可用身分證）',sid),doc('蓋母校正式印章的成績單',sid,signatures=['母校正式印章']),doc('英文履歷',sid),doc('一般學分交換英語B2證明（測驗或母校信；母語免測驗條件另核）',sid),doc('法語B2證明',sid,condition='限Level 2國際事務方向；不要求其他一般交換方向。')]
field(rid,'study_period','2026–27表列秋各級9月中至12月底；春Level 3一月中開始，Level 2、4、5一月初開始，均至四月底。這與未註年官網Level 2僅秋季的說明不同，保留衝突，不能據此宣稱中央Level 2春季已開放。',sid,[1])
field(rid,'courses','2026–27到校前線上選課，秋／全年6月、春11月聯絡註冊。最低管理課數：Level 2八門，Level 3四門（完整一個方向加至少一門核心），Level 4四門，Level 5三至五門且同一專長，原表註可能微調。原表只接受因撞堂而更課；30 ECTS通常對應15美制或60英制學分，不保證中央抵免。',sid,[2])
field(rid,'housing','2026–27住宿平台須入學註冊後由住宿團隊開通，收到錄取信應及早找房訂房，不保證校內住宿或床位。房租參考每月450–700歐元，押金與實際房源仍待確認。',sid,[2])
field(rid,'cost','2026–27分項預算：房租450–700、餐食150–200、公車月票25.20、電話15–20歐元，以上每月；簽證保險等雜支150–200歐元則是每年，不是每月。未把年度雜支混入月支或自行產生官方總額。',sid,[2])
field(rid,'insurance','2026–27校方要求非歐洲學生私人保險涵蓋全期運返，醫療可納入私人保單或依適用條件登記法國公保；醫療保險選擇不能當成免運返保障。歐盟／EEA／瑞士另列全期有效EHIC，實際當期適用須官方確認。',sid,[2])
rid='ncu-086';sid='1GrxLPz2lPZQlllQoMj7gIVZ-0n49q0Zp'
field(rid,'host_deadline','另份母校保存的未年VSB表列冬季／全年提名3/31、申請4/30，夏季提名9/30、申請10/31；與已讀另一未年官方表的簽證分组期限不同。兩份都未註適用學年，分享日期不能判定規則新舊，116方案與期限仍待校方確認。',sid,[1])
field(rid,'language','另份未年VSB表列IELTS5.5、TOEFL72（未註制式）、TOEIC785或B2等效，最低B2；與另一未年表IELTS5.0、iBT62及B1–B2範圍不同。原件並列保留，未擅選較低門檻、測驗版本或當期適用。',sid,[2])
field(rid,'courses','另份未年VSB表只寫建議23–30 ECTS，不是最低23；與另一表最低20、建議30的表述分開保留。個別課程、接收學院與中央116方案待確認。',sid,[2])
field(rid,'host_documents','未年VSB表說明母校使用提名通知所附表，含學生姓名、電子郵件、接收學院、GPA及語言程度；學生在校方平台網申。未列完整初申附件、簽章或全部表格，不能自行把常見文件列為必繳。',sid,[1],gap_only=True,unresolved='僅確認提名資料及網申入口，完整文件與116通知待核。')
field(rid,'tuition','母校保存的未年VSB表把每學期12000捷克克朗（原表約500歐元）放在自由申請訪問學生方案，不能當成中央雙邊交換必繳學費。交換獎學金只有方案入口，未核額度或資格，不能保證補助。',sid,[1])
field(rid,'housing','未年VSB資料表列雙人或三人住宿及住宿入口，沒有租價、押金、申請日或床位保證，當期住宿規則仍待核。',sid,[2])
field(rid,'arrival','未年VSB表說學生組織為入境學生提供Buddy並舉辦活動，未提供當期報到日；簽證及到後支援僅列入口，不當作文件全文已核。',sid,[2])
rid='ncu-081';sid='13HE9I87Z-H0yMUBeKXGxGkPpFPHiUApF'
field(rid,'eligibility','2026–27資料表至少已讀四學期；碩士課可由碩士生或學士三、四年級申請，與官網學士最後一年的表述不同，不能對所有學制直接畫等號。',sid,[2])
field(rid,'study_period','2026–27資料表把行政學期與教學分開：秋行政8/1至12/31、教學8月底或9月初至12月底；春行政1/1至7/31、教學1月初至5月中末。7/31不是必然最後到課日；確切課程、考試與離校安排須另核。',sid,[2])
field(rid,'courses','2026–27表允许論文或研究但須自行找導師，非博士學生至少一半學習負荷仍須課程。醫學、經濟領域限相关主修；法律及教育外系學生須有餘額。這是負荷及選課規則，不能把論文研究當成全期免修課。',sid,[2])
field(rid,'tuition','2026–27表免交換學生學費、課程及註冊費；學生會約55歐元是每學年自願加入、校方推薦，不能改為每學期必繳費或全部生活免費。',sid,[2])
field(rid,'housing','2026–27表可向TYS申請學生住宿，租金約每月330–500歐元，不等於校方保證床位；校區有Turku、Pori、Rauma，Pori距Turku約140公里、Rauma約90公里，不能當同一通勤點。',sid,[2])
field(rid,'cost','2026–27表每月生活費600–1000歐元，隨租金而異且不含休閒活動；另列租金330–500歐元為組成參考，不把房租重複加到生活總額，也不當全部支出全包。',sid,[2])
field(rid,'arrival','2026–27表為每名交換生安排芬蘭朋輩志願Tutor，成績單在考核期結束後五週內發出，非最後上課日即取得；表中的一般迎新月份不取代先前已核2026秋／2027春確日。',sid,[2])
js(S/'reviewed-host-records.json',records);js(D/'field-reconciliation.json',changes);js(D/'added-host-records.json',{rid:records[rid]for rid in rows.values()})
js(D/'inventory-counting-correction.json',{'previous_method':'後一期records整筆覆蓋早期records，僅檢source_ids，未包含欄位sources。','new_method':'依build合併來源及fields，計算source_ids及所有field來源引用聯集。','known_omission':'Turku2026–27資料表p1已有field引用，舊清單列未引用；本批才全文完成，不計為首次讀取。','completion_sources_unchanged':801,'completion_reading_records_unchanged':691})
print({'reviewed_docs':5,'physical_pdf_pages':10,'updated_hosts':5,'new_hosts':0,'updated_fields':len(changes),'previous_gap_only_with_reference':sum(bool((x['previous']or{}).get('gap_only'))and not x['updated'].get('gap_only')for x in changes)})
