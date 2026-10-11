from pathlib import Path
import json,hashlib,datetime
from research_curator import Curator

R=Path('/workspace/abroad-ntu-completion-20261011');H=Path(__file__).parent
baseline=json.loads((R/'sources/ntu/completion-2026-10-11.json').read_text())
baseids={o['observation_id'] for s in baseline['schools'] for o in s['observations']}
basehash=hashlib.sha256((R/'sources/ntu/completion-2026-10-11.json').read_bytes()).hexdigest()
c=Curator()
def f(pid,sid,field,text,scope,quote,page=None,period='undated_public_reference',locator=None):
 c.fact(pid,sid,field,text,scope,quote,page=page,period=period,locator=locator)
 o=c.schools[pid]['observations'][-1];d=c.read_source(sid)
 o['original_quote']=quote;o['raw_body_sha256']=d['sha256'];o['publication_role']='research_candidate_not_formal_selection_rule'
 if page:
  normalize=lambda x:' '.join(x.split())
  assert normalize(quote) in normalize(d['pages'][page-1]['text']),(sid,page,quote)

sid='2611f0bb6f869229';scope='聖加倫Partner university exchange Bachelor/Master共通未標2027–28學年'
f('89',sid,'eligibility','Bachelor/Master協定校学生須經母校國際處檢核及電子提名，才取得Mobility-Online密碼；不同Freemover、ISP-MBA、CEMS與SwissMobility流程不混用。',scope,'Nomination by partner university')
f('89',sid,'deadlines','一般協定校秋提名4/15、學生申請5/15；春提名9/15、學生申請9/30。頁未標學年，不寫成2027–28具年期限。',scope,'Nomination deadline for home university',locator='Nomination deadline and separate student application deadline tables')
f('89',sid,'documents','Mobility-Online初申上傳已簽application confirmation、實際入境所用有效護照或國民ID、學生證照片；核完才寄AcceptanceLetter與Compass登入。不要從其他programme增列語言考試證明。',scope,'Application Procedure')
sid='eb20cda67854c83e';scope='HSG Student Exchange FactSheet2026/27 p5；非2027–28規定'
f('89',sid,'language','一般交換英／德授課期望CEFR B2，明說不需正式證書；iBT89/IELTS6.5及全英MBA豁免屬ISP，不是臺大一般Bachelor/Master交換門檻。',scope,'LANGUAGE REQUIREMENTS',5,'older_year_reference')
f('89',sid,'cost','2026/27每月房租含utilities CHF700–1050、餐600、通訊70、交通180、保險100–280、休閒150、其他100–150；housing申請費250不退、簽證／permit66–240依國籍。住房額可更高，未把保險一律寫成20。',scope,'MONTHLY LIVING EXPENSES',5,'older_year_reference')
f('89',sid,'housing','同為2026/27，Partner頁連結PDF p5春住宿2/1–6/30；incoming總頁V05 PDF p5寫2/1–5/31。兩版秋同8/1–12/31、先到先得。結束日版本矛盾尚未定奪，不自行挑一版或標成未公告。',scope+'；另V05 p5對照','Contract durations:',5,'version_conflict',locator='Compare with 20e267fa05ee1b7d page5 Spring contract end May31')
f('89',sid,'courses','2026/27一般交換至少16、最多40ECTS（THEMIS33）；本科一般讀本科，符合先修才能例外修研且不得研核心課；研可按必要修本科。確定課表約開學前1月，容量限制與bidding不保證全部志願。','HSG2026/27 factsheet p4；不是2027–28完整課程清單','REQUIRED WORKLOAD',4,'older_year_reference')
f('89',sid,'eligibility','2026/27提名學生在母校的學科須與HSGManagement/Business/Economics/PoliticalSciences/Law相近；此是一般提名條件，ISP35名容量不作臺大名額。','HSG2026/27 general online nomination p6','STEP 1: ONLINE NOMINATION BY',6,'older_year_reference')
f('89',sid,'calendar','已公告2026秋9/14–12/19、2027春2/22–5/29（含單學期客生考試），春必到迎新2/18，CEMS/ISP各別。2027春不是NTU116-1的2028春；二學期學生第一學期考試仍按正常規則。','HSG2026/27 p7；非2027秋／2028春','Term Calender 2026/2027',7,'older_year_reference')
sid='883a586993b89da3'
f('89',sid,'housing','HSG HousingOffice共通申請秋5/18 09:00CET、春10/1 09:00CET，由MobilityOnline；頁寫春滿額可waitinglist但未標哪年。租含WiFi、水電暖、radio/TV、洗衣與床具、不收租押金，不能推成無250申請費。','HSGhousing現行頁未標年度，官方原文時區CET照錄不擅改CEST','The application starts on 18 May at 9:00 CET',locator='Housing application opening, inclusions and unqualified Spring fully-booked notice')

sid='a26ce0e694771f4d'
f('1268',sid,'housing','Bennett頁2026–27新生公告：7/25/2026以後錄取者無on-campus宿舍，需自行校外；未明涵蓋交換、不套2027–28。一般triple-sharing/first-come與10000床位不等臺大保障名額。','Bennett AY2026–27 admission hostel notice；exchange身份尚未確認','Campus Hostel Accommodation Notice',period='older_year_reference')

sid='806dd7e12db3b3a2';scope='立命館SKP2027春入學要項；不當2027秋初申完整規則'
f('809',sid,'eligibility','需在有效協定校本科／研在籍且正式母校提名，入學前至少完整本科1學年；標準GPA3.0/4.0或B等值，協議另訂則依協議。這與JASSO獎學金2.3/3.0不同。',scope,'The standard required GPA is 3.0 on a 4.0 scale',8,'older_year_reference')
f('809',sid,'language','RCJ日檢N1或EJU聽讀合280＋寫35；IJL無日語先修要求，零初學需基本英語；RCE及想選英文課的IJL需iBT76（新4.0）、IELTSAcademic6、Cambridge170或DET100，協定／全英program／指定國條件可豁免且母校提名時註明。',scope,'Language',8,'older_year_reference',locator='Track comparison p8 and score-waiver conditions pp8–9')
f('809',sid,'language','SKP要項不收TOEFLHome/Essentials/MyBest、IELTSOnline/OneSkillRetake/TOEICIP及其他institutionaltests；IJL英文課語證申請時交、事後不收。不能套LMU接受Home/MyBest的條件。',scope,'The following tests/scores are NOT',8,'older_year_reference')
f('809',sid,'documents','2027春初申主要PDF：在學／適用畢業證、最新官方成績含制度與不及格／學分／學期（研一另本科成績）、適用語證、日500–700字或英500–700wordsPS、護照ID及既往入日章、適用ResidenceCard正面。非英日文件附可自行翻的英日譯；COE與錄取後Health另程序。',scope,'Required Application Documents',19,'older_year_reference',locator='Checklist pp17–19, PS p16, formats p13')
f('809',sid,'documents','SKP母校先提名才於約1週取得login；全online、提交後track/campus/period不能改，第三方／AI代寫内容被列無效。這是申請者內容規則，研究候選本身不代寫申請。',scope,'Applications containing plagiarized, third-party, or AI-generated content will be invalid.',13,'older_year_reference')
f('809',sid,'deadlines','2027春學生申請2026/10/2 10:00–11/2 09:00 JST；不是舊2025/26的earlyNov，也不是2027秋申請。錄取最遲lateDec、SupportFee earlyJan、Health midJan暫定、Housing結果endFeb均不同階段。',scope,'Application Submission Deadline',2,'older_year_reference')
f('809',sid,'cost','從Spring2027起所有SKP含exchange須一次付JPY50000 SupportFee，錄取後2週Convera，含指定Gakkensai/Gakkenbai、醫療支援與COE行政等；NHI、自選保險／COOP另繳。不要與舊生活估算所有保險列再直接相加。',scope+'；規定生效起點Spring2027','SKP Student Support Fee (JPY 50,000)',4,'older_year_reference')
f('809',sid,'housing','初申填housing preference不是正式寮申請；錄取後依校區I-House資料另申請，結果endFeb。當頁資料不足不能叫未公告，也不保證席位。',scope,'The official housing application must be submitted after the announcement of admission results.',18,'older_year_reference')
f('809',sid,'insurance_visa','無日籍且無有效ResidenceCard者另COEwebform由校指定行政書士處理，詳情之後提供；日籍含雙重國籍應日護照入境、不申COE但錄取後戸籍抄本／學生證照。ResidenceCard有否另COE須校逐案判斷。',scope,'Student Visa Applicants',20,'older_year_reference')
f('809',sid,'documents','錄取後所有學生另HealthInformationForm（midJan暫定）；正在治療／用藥／嚴重過敏等適用診斷書處方，申請accommodation另母校支援證明等。不是所有學生初申都要醫證，也不是未公布Health程序。',scope,'After the admission results are announced',21,'older_year_reference')
f('809',sid,'courses','SKP僅可讀自己track/campus提供的清單，不含一般全校課表或研究指導；本科限本科SKP、研可兩級，每週>=7堂95分、最多20學分，選課lottery、跨校1.5hr與IJL英文最多2門限制；Design/Art暫不开放。',scope,'Research guidance is not provided to SKP students.',7,'older_year_reference')
f('809',sid,'cost','RUSSES於2026Fall結束，Spring2027起不再提供；JASSO80000/月僅當年program获funding及個人獲選、不可當保證收入或COE財力，原官網PDF2025止與現官網2026止保留版本，不以舊GPA獎學金值代學術資格。',scope,'JASSO Scholarship cannot be used as financial proof for your Certificate of Eligibility.',12,'older_year_reference',locator='RUSSES revision p4 and JASSO pp11–12')
f('809',sid,'calendar','2027春要項p2一學年參與者另列2027Fall開學9/26、授課9/27、program至2028/1/31；此是Spring2027入學的全年參與表，不等Fall2027 incoming申請已公告。半學期不能入學後延全年、也不接受連續兩次半學期重申。',scope+'；Spring2027開始全年者之Fall2027時間表','September 26, 2027',2,'target_year_explicit',locator='Fall column within Spring2027 entry schedule and non-extension rule p3')
sid='9e9e4cc13a4b3f3f'
f('809',sid,'cost','SKP現行網頁exchange免學費、SupportFee一／兩學期均50000；self-sponsored425900/851800不套交換。生活表一學期798000／兩學期1582000含房390000/780000、食210000/420000等，未標本期費率；其保險與新SupportFee是否重疊尚須核對，不自算總預算。','SKP現行費用頁未標2027–28當期與估算期間長度','Estimated Living Expenses')

sid='62e61b56a7576c3b';scope='九大校級incoming通用頁、未標2027–28；各program須另外核對'
f('30',sid,'eligibility','協定校經母校申請，拒學生個人直申；分JTW、JLCC及各學部／研，不把一般同頁N1等值套JTW。',scope,'Please note that we do not accept applications directly from individual students')
f('30',sid,'language','一般各學部／研日語N1或等值；只有目標單位足够英授時可iBT79/IELTS6.0，不意味全校自由英授。頁未說2026新TOEFLband換算，舊79照錄不自行換算。',scope,'TOEFL score of at least iBT 79 or IELTS 6.0.')
sid='9b402cd7a01b532a';scope='九大JLCC申請頁共通、未標年度，Ito11個月日本研究programme'
f('30',sid,'eligibility','JLCC原則本科、參加時不得大一、日本研究主修且至修畢仍母校在籍；頁敘課程概要也提研，但申請資格原則本科，不能憑概要一律放研。',scope,'原則として学部学生（本コース参加時に1年次生である者を除く）')
f('30',sid,'language','JLCC须完成中級日文、可用日文讀日本社文課，N1程度為望ましい而非明文硬證書門檻；材料後指定期間onlineplacement，必要面試。',scope,'日本語能力試験N1程度が望ましい')
f('30',sid,'documents','JLCC按成績、日文能力、研修計画書、母校推薦書等综合審；日文填申請並經母校期限online。公開有文件類別但精確表單／日月由母校提供，不能說完全未公布。',scope,'研修計画書',locator='Application routes and selection documents')
f('30',sid,'deadlines','JLCC交換明說經母校於案內期日前online，公開頁無具年日月；大使館MEXT、母校推薦MEXT與普通交換是三途徑。須母校案內不等未找到或確認未公告。',scope,'案内された期日までにオンライン申請')
f('30',sid,'cost','JLCC一般列月29700＋入學84600＋檢定9800JPY，但依有效校級協定交換及獲許可MEXT明示全免；這不是所有臺大JTW／學部的應付費。JASSO80000需校內選，不保證。',scope,'上記の授業料等はすべて免除されます。')
sid='ca47547ad37442c7';scope='九大JTW Apply共通未標2027–28；部分學費明標asof2019'
f('30',sid,'eligibility','JTW本科至少完整大學1年、strongrecord；成功者通常GPA3.2以上是描述不是最低硬3.2。研可申但課程主要本科日本社文，不把中心概覽本科一句當研全面排除。',scope,'successful applicants usually have a GPA of 3.2 or higher')
f('30',sid,'language','JTW非英母語須iBT79／IELTS6或PBT550/CBT213；無日文先修數值在此頁。這些iBT舊量尺未自行改新制，完整當期例外待招生材料。',scope,'You have the necessary English proficiency')
f('30',sid,'deadlines','JTW秋申請2/10、結果midApril；春10/10、earlyJan結果，頁未標年度且實際母校流程另更早，不把10/10當臺大校內截止。',scope,'Application Materials & Deadlines')
f('30',sid,'documents','JTW初申需母校指導、essay與projectproposal，公開基本表單／ApplicationGuide連結仍待跟讀，不聲稱完整清單已核實；錄取後SupportCenter另online簽證／宿舍／接機。',scope,'your essay and project proposal')
f('30',sid,'cost','JTW每學分14800、12學分177600/semester明標asof2019；協定互免且母校正式提名可免，须母校確認互免條款，不採此一般auditor費為臺大應缴。JASSO80000/月競爭不保證。',scope,'14,800 yen (as of 2019)',period='older_year_reference')
sid='27873445b94384a0'
f('30',sid,'housing','九大普通寮原則6月，<=1年短期學生可到就讀完但researchstudent例外。校方尽力可轉較貴指定寮，亦可全無房；伊都／馬出／大橋／筑紫不同住房按vacancy，不能寫保證任選。','九大housing共通未標年度／实际就讀校區各別','The period of residence in a dormitory is up to 6 months as a rule.')
f('30',sid,'deadlines','九大Housing頁2/5/8/11月為福岡市營宅、3/6/10為縣營宅申請，公共设施使用表提前1週也不是incoming交換初申deadline。','九大housing中的公共住宅／facility程序，非exchange','Application Period: February, May, August and November')
sid='507fd56f8eb942ce'
f('30',sid,'cost','九大generalcost列生活合計80000–115000JPY，房utilities15000–50000、食30000等；本體未明2027–28或全表費用期間，ESP明确1000/year。學費表不能凌駕JTW/JLCC互免條款；MEXT UG117000列year疑似單位誤植也不採當月收入。','九大generalCost未標學年／生活表期間；不據語境補成2027月費','Approximate Living Expenses')

sid='20a649c8555d2ff8';scope='LMUexchange Application共通未標2027–28年度'
f('391',sid,'eligibility','須協定校母校提名，LMU國際處才寄申請說明；LMUexchange最多每degreecycle2學期，非degree admission規則。',scope,'your university must be an LMU partner university.')
f('391',sid,'deadlines','學生online冬5/15、夏11/15，宿舍在同初申勾選且逾期不受理；頁未標年度不稱116-1正式期限。提名日仍需另一正式Nomination頁，不以申請日代提名。',scope,'15 May',locator='Online application May15 / Nov15 and housing application deadline')
f('391',sid,'documents','初申含onlineform、官方成績、母校與本人簽LA、語言證明、台灣用passportID頁、consent；LMUexchange可母校／LMULA，host簽在送件查核後，不須先三方全簽。Erasmus專用OLA不強加一般交換。',scope,'An application is considered complete if it includes the following documents:')
f('391',sid,'language','共通初申至少B1、入學B2；只修英授不用證明德語。NorthAmericaStudies/EnglishPhilology及研PoliticalScience入學英C1（初申B2）；人醫牙醫vet按clinical/taught分德C1/B2。','LMUexchange共通含department exceptions未標年度','at least B1 for your application')
f('391',sid,'language','語證須<=2年，可母校coordinator簽languageconfirmation；英B2新iBT4(72+)、C1新5(95+)，IELTS5.5/7、TOEIC785/945，接受Home/MyBest/IELTSOneSkillRetake。不同於立命館拒用這些tests。',scope,'The following language certificates (not older than 2 years) are accepted:')
f('391',sid,'courses','LA正常30ECTS不是交换硬最低，依母校；LMUexchange至少60%本科／研major/minor，剩40%最多2領域，最多3領域。LA只是意向、需另department註冊且不保證。',scope,'30 ECTS but this is not compulsory for exchange students.')
sid='7c8f1696df233c8c'
f('391',sid,'courses','本科一般不得研課；正式夏課表2月底/3初、冬7月底/8初，因此初申時確定當期清單未出，2026/27英授overview只是示例不保證下期。可以往期編LA到校再修，不等host沒有課。','LMUChoosingCourses未標2027–28，明确將來正式清單時間','will not be available by the application deadline.')
sid='1d824f253ce7c370'
f('391',sid,'housing','Bachelor/Master交換可在online初申勾宿舍，不可直接找StudentUnion申請；約半數可供房但不保證個人、PhD需自找。冬9月至2月底、夏3月至7月底、一般一學期，EUR400–600/月。獲offer需簽Annahmeerklärung並繳3月租＋letter列押金。','LMUexchange housing現行共通未標2027費率','The average rent is between 400 € and 600 € per month')
sid='11d38a18e16e6a43'
f('391',sid,'insurance_visa','LMU註冊須足够醫保且由德國法定醫保provider發Versicherungsbescheinigung；意外／責任保險是建議。visa依國籍／停留，頁只連Guide，不憑此推臺灣免簽或旅遊visa可全學期。','LMUarrival共通；國籍法規與2027保費尚未核','A certificate of insurance (Versicherungsbescheinigung) has to be issued by a German statutory health insurance provider.')
f('391',sid,'documents','入學註冊冬9/10月、夏3/4月由IntlOffice處理需email可連絡；到Munich地址2週內親到登記，帶form/房東確認/passport，為錄取後生活程序而非初申文件。','LMUArrival registration and city-address phase未標年','Registering your address in Munich')
sid='7ae124511c7888f6'
f('391',sid,'cost','Registrar正式頁只列2026夏basicfee EUR97，2024/25舊85與過去semester交通費保留；Winter2023/24起額外semester-ticketfee暫停、LMUcard不再MVV車票。incoming說須semesterfee，但2027–28費率未在此頁列，不將85/97改標本期。','LMURegistrar2026summerfee；非2027–28費率','Summer Semester 2026: basic fee 97,00 €',period='older_year_reference')

# Every original candidate text for these five schools has actually been read.
q=json.loads((H/'priority-source-roster.json').read_text())
for pid in ['1268','89','809','30','391']:
 for sid in q[pid]['sources']:
  c.body_review(pid,sid,[field for field,sids in q[pid]['fields'].items() if sid in sids],
   '完整原候選抽取文字已讀；outgoing、開放日、公共住宅、設施使用、full-degree與獎學金資格不混成incoming初申規則。本文完整讀過不代表當期細節皆核實。')
for pid,sid,fields in [('89','eb20cda67854c83e',['eligibility','language','documents','deadlines','cost','calendar','courses','housing']),('89','20e267fa05ee1b7d',['housing','language','eligibility','cost','deadlines','calendar']),('89','883a586993b89da3',['housing','cost','deadlines']),('809','f494e276173b3e9d',['eligibility','documents','deadlines','cost']),('809','806dd7e12db3b3a2',['eligibility','language','documents','deadlines','courses','cost','calendar','housing','insurance_visa']),('30','3c568d2bf0a113f7',['eligibility','language']),('30','9b402cd7a01b532a',['eligibility','language','documents','deadlines','cost']),('30','ca47547ad37442c7',['eligibility','language','documents','deadlines','cost','insurance_visa']),('30','686b086aaabdbabb',['documents','courses','calendar']),('391','7ae124511c7888f6',['cost'])]:
 c.body_review(pid,sid,fields,'完整新公開抽取正文／全部PDF文字頁已讀；文件實際年份／program／initial-vs-after-admission／fee-period保留，未讀新連結另待跟讀。')
new=[]
for s in c.schools.values():
 for o in s['observations']:
  if o['observation_id'] not in baseids:new.append({'portal_id':s['portal_id'],'school_name':s['school_name'],**o})
sources={sid:c.sources[sid] for sid in {o['source_id'] for o in new}}
payload={'kind':'scoped_research_delta','base_stage4_source_sha256':basehash,'base_stage4_remote_commit':'e89935bdeae1c6ab2bca2a602c53179dc6597ac8','checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runtime_materialization_performed':False,'formal_platform_update_performed':False,'source_checked_at_retained_per_observation':True,'school_count':5,'new_observation_count':len(new),'observations':new,'public_source_reviews':sources}
(H/'候選增量.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
c.snapshot['candidate_only']=True
c.snapshot['research_stage']='stage5_candidate_only'
c.snapshot['research_meta']={'base_validated_source_sha256':basehash,'base_validated_remote_commit':payload['base_stage4_remote_commit'],'incremental_observations':51,'runtime_materialization_performed':False,'formal_platform_update_performed':False,'note_zh':'659則合併研究候選；目前測試／runtime仍是608則。須先按來源scope審核、重建與驗證才可使用於平台。'}
(H/'結構化候選資料.json').write_text(json.dumps(c.snapshot,ensure_ascii=False,indent=2)+'\n')
assert hashlib.sha256((R/'sources/ntu/completion-2026-10-11.json').read_bytes()).hexdigest()==basehash
print(json.dumps({'new_observations':len(new),'schools':5,'quote_sources':len(sources),'base_source_unchanged':True},ensure_ascii=False))
