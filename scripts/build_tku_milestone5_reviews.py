"""Manually quoted TKU host references after readable-route continuation.

Every field is reference_only. No home quota, eligibility or document promotion.
Academic years come from actual body; contradictions and generic rules persist.
"""
import json
from build_tku_milestone3_host_reviews import source,fact
from tku_capture_io import BUNDLE


def main():
 rows=[]
 def add(n,fields):rows.append(dict(id='tku-sister-'+str(n),fields=fields))
 def F(sid,v,needle,year='Undated actual host rule; TKU nomination/track/current cycle unverified',page=None,verified=False,role='host_incoming'):
  return fact(source(sid),v,needle,year,page,verified,role)
 # Warsaw's filename2025 does not establish an academic year in its body.
 w='a82a9b7f2456809887e90a2c';wy='Intrinsically undated Mobility Information Sheet; filename2025 not academic-year evidence'
 def W(v,n):return F(w,v,n,wy,2)
 add(58,dict(host_deadline=W('一般接待申請秋／全年5/15、春11/15；未明載獨立年度，不作淡江母校期限。','Deadlines for applications:'),host_nomination_deadline=W('一般接待母校提名秋／全年4/30、春10/31；未明載獨立年度。','Nomination deadlines:'),host_language=W('incoming要求波蘭語或英語B2或同等；實際授課語言依院系，未確認淡江協議學科／年度。','B2 or equivalent Polish or English'),study_period=W('一般秋10/1–2月中、春2月中–6月底，考試包含其中；正文註明日期逐年可能不同，不能改寫2027精確行事曆。','Academic Year: October'),department_scope=W('資料表列Bachelor、Master與Doctoral學制；博士欄不等於淡江可申請博士名額或全部系所。','Academic Level(s)'),course_restrictions=W('每學期最多30ECTS；額內另可有一門波蘭語、一門外語及體育免費，實際課與協議院系須另核對。','Maximum 30 ECTS'),housing=W('宿舍名額有限，多為雙人房共用浴廚；IRK同一申請表填住宿，先到先配，無床位者協助找私人租屋，沒有人人保證。','A limited number of places available')))
 # Dankook exact2027 calendar exists, but nomination/application year conflicts.
 d='f9e8dc0ae975d3ce75428225';dy='Actual Fact Sheet calendar Fall2026/Spring2027; deadlines table Spring2027 with literal2025 dates inconsistent; other prices/rules undated'
 def D(v,n,known=False):return F(d,v,n,dy,verified=known)
 df=dict(host_eligibility=D('全時母校在籍、完成至少一學期、GPA≥2.0/4.5或同等；交換須母校提名，visiting另有非partner程序。淡江母校資格未知。','Maintaining a minimum GPA'),host_language=D('須足夠英語或韓語，韓語課推薦TOPIK4以上；這是修課建議，頁面未列交換統一英語分數。','Courses Offered in Korean'),host_deadline=D('Fact Sheet表頭Spring2027卻寫申請November15,2025，Fall2027寫May15而無年；舊exchange頁實載2024。保留來源矛盾，不自行改成2026或2027截止。','Application Deadline'),host_nomination_deadline=D('Spring2027表卻寫September21–October30,2025；另一官方一般頁春9/1–10/30、秋3/1–4/30，Fact Sheet秋3/15–4/30。年與起日均待確認，不補猜。','September 21'),study_period=D('實載Spring2027：2/23–24入住、2/25–26必到迎新、3/3開課、6/8課終、6/8–22期末、6/30退宿；Fall2026另列，不能當Fall2027。','Fall 2026',True),campus=D('英語課只在Jukjeon，Cheonan不開英文課；只能單一校區修課，不能任選混修兩校區。','Courses offered in English are available'),department_scope=D('Jukjeon Theater/Film/Musical，以及Cheonan醫／牙／藥／護理不開放；其他選課仍受院系限制及餘額。','School of Theater and Film'),course_restrictions=D('最多19學分含韓語，不允許超修或旁聽；建議至少6而非強制最低6。先到先選不保證餘額，母校學分認定另核對。','Students can take up to 19'),course_schedule=D('每新學期約開課前一個月發布；目前連結Spring2026／Fall2026是歷史課表，不代表2027同課再開。','approximately one month'),housing=D('線上申請選校內住宿者保證安排；JukjeonWoongbi／CheonanDanwoo雙人房，無單人房，室友偏好不保證。自找校外房不由校方安排。','Guaranteed placement'),housing_costs=D('未載獨立報價年：校內約KRW1,600,000／學期4月；不是已核實2027/28費率。','approx. 1,600,000'),costs=D('交換免學費；訪問生按degree/college另付學費，不套用交換。註冊與ARC參考65,000KRW，未載独立費率年。','Waived for Exchange Students'),living_costs=D('未載獨立年：餐／個人支出估KRW700,000/月、書約100,000；依生活與課程改變，不作固定總預算。','700,000 KRW'),insurance=D('來韓前自備涵蓋疾病、意外、死亡醫保；另須韓國國民健保，私人險符合要求可豁免。70,000KRW/月為未載年份估計。','Additionally, students must subscribe'),latest_forms=D('提名後才收線上申請連結；護照、成績單、StudyPlan、Pledge、IDPhoto，以及non-OECD所需在籍／銀行證明。國籍個別文件須接待確認，未下載當期模板，未加入母校文件catalog。','Required Documents'))
 df['host_nomination_deadline']['evidence']+=F('69b201cfec2eaa59eaf50ea3','','September 1','Undated main OIA page; nomination start differs from incoming Fact Sheet')['evidence']
 df['host_deadline']['evidence']+=F('7da61b609029425fd305e60d','','November 15, 2023','Actual historical Spring2024 deadline; not2027')['evidence']
 add(41,df)
 # Actual incoming UI rules, separate from its outgoing Exchange Program page.
 ui='0ed9f4f477176ced328c3c48'
 def U(v,n):return F(ui,v,n)
 uf=dict(host_eligibility=U('需UI有效partner協議、母校批准及提名；無協議、過期或超協議quota改走自費StudyAbroad，不能把全部姊妹校協議或自費視為TKU交換名額。','the agreement has expired'),study_period=U('入境exchange本科／研究所可一或兩學期；自費一學期至一年另案，未載獨立年度及精確日。','one/two semesters'),costs=U('有效exchange免UI academic fees，仍可能付母校學費；fee-paying另付學費，不能因同一頁而給所有學生免費。','not charged for academic fees'),department_scope=U('入境方案含本科與graduate課程，但沒有核實TKU協議院系或全部課可選。AUN/ASEAN、AIMS與Erasmus另列，不據此認定台灣學生適用。','undergraduate or graduate program courses'),latest_forms=U('提名後UI寄application package並審查；正文只顯示2026/27FactSheet標籤，未取得該附件正文。實際模板目錄明載AY2025/26，七類exchange與fee-paying分開，未核實新版，不能當淡江本期表格。','application package'))
 uf['latest_forms']['evidence']+=F('595edc1bf6752254a4fb0450','','Document Template for Student Exchange AY 2025/2026','Actual template directory AY2025/26; newer template bodies not verified')['evidence']
 add(232,uf)
 # ENU Kazakh body explicitly distinguishes inbound foreign/domestic/freemover.
 e='a21cdba66e6f6f72ee7751ad'
 def E(v,n):return F(e,v,n)
 add(197,dict(host_eligibility=E('外國大學incoming與哈薩克國內incoming分開；可協議partner或無協議freemover，TKU實際track／雙邊資格未核實。','Free mover'),study_period=E('外國incoming可一學期或一學年；未列精確年度、上課／考試日，不能補為2027。','бір семестр немесе оқу жылы'),host_deadline=E('一般文件窗口秋3/15–4/30、春10/1–11/15；無獨立年份，不是淡江母校期限。','15 наурыз'),course_schedule=E('提名後才由ENU向partner發該學期可修課清單；不能把一般目錄或全部系所當可選課。','пәндер тізімін'),latest_forms=E('母校提名信列姓名、學制、programme代碼／名稱；提名後交問卷、護照、成績單及含選課的LearningAgreement。此頁未有可開啟當期表，未加入淡江catalog。','толтырылған сауалнама')))
 # UM-Flint admissions article itself references degree admission; no guessed GPA.
 fl='0d4a68111512ec167df210aa'
 def M(v,n):return F(fl,v,n)
 add(96,dict(host_eligibility=M('incoming exchange與hosted均須母校提名；交換J-1、hosted可能J-1或F-1另分。英語／GPA連到First-Year degree admissions，尚未逐條核實交换適用分數，不套用degree門檻。','nominated by their home universities'),host_nomination_deadline=M('一般提名Fall／全年5/1、Winter10/31；Spring/Summer須詢問，無独立年份。','May 1'),host_deadline=M('一般接待申請Fall／全年7/1、Winter11/10；Spring/Summer須詢問，未核實淡江年度／母校期限。','November 10'),course_restrictions=M('國際exchange／hosted多數課須含實體課（face-to-face、mixed、hyperflex）；不能以全線上課取代，實際課須錄取後依SIS與advisor確認。','a majority of classes'),course_schedule=M('一般catalog不保證該term實開；錄取後以UMID看SIS課表。LearningAgreement於錄取後完成並與advisor登課。','may or may not represent actual courses'),housing=M('exchange／hosted住RiverfrontResidenceHall，餐計畫可選；本頁未核實當期房租、保證餘額或TKU分配。','Riverfront Residence Hall'),transport=M('CGE提供FlintBishopFNT接機；到DTW／ORD後若無轉FNT，學生須自行安排到Flint，不作所有機場免費接送保證。','Students without a connecting flight'),latest_forms=M('提名後CGE寄私人申請portal操作，再處理DS-2019與visa；公開頁不是已取得申請權或淡江文件模板。','instructions on how to submit')))
 # UTSA: exact new TOEFL scale from actual host page, no cross-school transfer.
 a='5b6b697364d0449cb3e8ae03'
 def A(v,n):return F(a,v,n)
 add(194,dict(host_eligibility=A('全時母校本科、雙邊exchange協議及母校提名，GPA≥2.5/4.0；未核實淡江本期track，不能把研究生或所有姊妹校資格套入。','full-time undergraduate'),host_language=A('TOEFLiBT2026/1/21前≥79、當日起≥4.0；PBT550、IELTS6.5、PTE58、iTEP3.8、CambridgeC1 180/C、DET95；各明示美國修課／高中／SAT/ACT豁免另核對。不把此新制轉換套到別校。','For exams taken on or after January 21, 2026'),insurance=A('在學須全面醫保，SHIP自動加入並計費；符合可比較計畫可依規定申請豁免，不能推定旅行險即可。$1,428/學期只是本頁未載報價年的估計。','Enrollment in the UTSA Student Health'),housing=A('校內Hall／apartment及校外房分開，校外供應商非校方affiliate；本頁沒有人人宿舍保證或當期價格。','UTSA is not affiliated'),living_costs=A('接待要求每月至少USD1,500或每學期6,000財力；另列估計校內食宿7,456、校外5,962、個人1,080、書每課100–150。估計表未載獨立年份且不等於財力門檻足付全部費用。','at least $1500'),costs=A('本頁exchange涵蓋tuition、differential及mandatoryfees；另收課程/departmentfees，估500–600USD，不將免學費當全部費用免除或已核實2027費率。','UTSA covers tuition'),transport=A('VIA公車對UTSA學生免費；校外通勤另依shuttle、市區公車或汽車，未核實TKU實際校區或接機。','VIA bus services are free'),latest_forms=A('錄取後接受函、WelcomeLetter及DS-2019寄母校coordinator；免疫接種規則亦錄取後另通知。本頁沒有當期公開申請表或期限，不把錄取後文件当淡江校內表。','Once Accepted')))
 # CPP lists two Taiwan partners, neither TKU: keep programme applicability gap.
 cp='7f3e52a70c97da014cf1e799';cy='Undated CPP J-1 incoming exchange; actual partner list Taiwan NTUST/YunTech, TKU absent; not proof of no institutional agreement'
 def C(v,n):return F(cp,v,n,cy)
 cf=dict(host_eligibility=C('僅列交換partner可申請；臺灣現列臺科大、雲科大，未列淡江。這是J-1 programme-list觀察，不能据此宣布全校無協議，也不能認定TKU可提名。','Taiwan: National Taiwan University'),host_nomination_deadline=C('一般母校coordinator提名秋3/15、春9/15；沒有独立年／後續申請截止，TKU權限未核實。','Fall: March 15'),host_language=C('此未載年份頁仍列舊制TOEFLiBT71／CBT197／PBT527–530及特定國家豁免；未核實2026新制適用或TKU route，不擅自換算。','at least 71'),latest_forms=C('母校提名後私密申請連結；英語護照、成績單、每學期USD10,000財力、2吋照片、TOEFL。只是公開頁清單，未取得TKU當期申請權／模板；不加入母校catalog。','Proof of Financial Support'),housing=C('錄取及取得studentID後才申請VillageApartments，保留部分exchange床位但不保證每人；可另找校外房。','some spaces specifically'),insurance=C('須全期医保，抵達時經國際處購批准計畫；約USD650/學期且明示可變動，無獨立年份。','approximately $650'),costs=C('直接雙邊exchange僅StudentSuccessFee，其它exchange需所有campusfees；一般免tuition不等於全免，TKU協議對應未知。','only responsible for the Student Success Fee'),living_costs=C('未載独立年：4月學期總估USD10,000（fees850、書450、食宿6000、個人2000、交通700）；不作2027實際帳單。','Estimated Cost for a Semester'))
 add(118,cf)
 # NPU actual2026 body; Taiwan student's international-student route unverified.
 np='210aaa9a8d528712b20b9e28';ny='Actual2026 NPU exchange guide, published2025-10-27; historical2025/2026 deadlines; Taiwan-student route and2027 edition unverified'
 def N(v,n):return F(np,v,n,ny,verified=True,role='host_international_student_historical')
 nf=dict(host_deadline=N('歷史2026交換：春2025/12/31、秋2026/6/15申請；2027新版尚未核實，不稱官方尚未公告。','Application Deadline'),host_nomination_deadline=N('歷史2026：春2025/12/15、秋2026/5/31提名；不是淡江116新申請期限。','Nomination Deadline'),host_language=N('2026国际交流文件列IELTS6.0／TOEFL80／DET115，母語者免；台灣學生是否適用該国际生route未核實，不能转成淡江最低語言。','Language proficiency certificate'),study_period=N('2026可學分交換或漢語課，1學期或1學年；兩方案分開，不能當2027已定行事曆。','Credits Programs'),costs=N('partner提名依協議免tuition與申請費，非所有individual免；訪問獎學金含宿舍及生活補助屬另申且不保證，不能當TKU固定收入。','Tuition fee: Nominees'),housing_costs=N('2026參考校內宿舍450–900CNY/月，未核實2027房價、保證床位或TKU校區。','450-900CNY/month'),latest_forms=N('2026正文列護照（有效>6月）、公證學歷／在籍、成績單、語言、個人申請者教授接受函、6月內無犯罪／外國人體檢表等。連出JPGfactsheet與Autumn2026XLSX，兩者實際HTTP200都是「请输入验证码下载附件」，未取得二進位、不解驗證碼，不宣稱附件可開啟。','Admission Documents'))
 for sid in ['83aa7b3d294826bb88205338','e59813d6af2bfce29dcca738']:nf['latest_forms']['evidence']+=F(sid,'','请输入验证码','Attachment CAPTCHA gate, not actual document content; no year verified',role='host_attachment_access_limit')['evidence']
 add(130,nf)
 # ITS2027 webpage and intrinsically dated2026 factsheet separately.
 it='601acc388b5d5965fa10b209';iy='Actual Spring2027 incoming webpage; TKU nomination/track/current home application unverified'
 def I(v,n):return F(it,v,n,iy,verified=True)
 fs='05a4aa438d8ebf31679b8690';fy='Actual2026 University Factsheet linked fromSpring2027 page;2027 applicability not independently established'
 def IP(v,n,page):return F(fs,v,n,fy,page)
 its=dict(host_deadline=I('接待正文Spring2027申請2026/10/15截止，僅simad線上處理；母校TKU新申請是否仍開放未核實，不能以此延長淡江deadline。','Application Deadline : 15 October 2026'),study_period=I('Spring2027為2027/2–6月；partnerexchange本科／碩士可一或兩學期。不能以2026參考文件或舊XLSX秋9–1月取代2027正文。','Semester 2027'),host_eligibility=IP('2026接待FactSheet GPA≥3.0/4.0；2027網頁說本科／碩士partner資格依協議。未確認2026GPA沿用2027或TKU國際生適用，博士不能因模板選項就視為開放。','Minimum of 3.00',2),host_language=IP('2026接待表TOEFLiBT64／IELTS5.5／PBT510、2年內，英語學校可母校聲明替代；2027語言新版未獨立核實，不換算新TOEFL量尺。','TOEFL IBT: 64',2),host_nomination_deadline=IP('2026接待表提名春9/15、秋4/15；不是2027已核實提名日期，也不是淡江母校申請截止。','Nomination Deadline',1),course_restrictions=IP('2026表最多3個departments、本科21SKS、碩／博士15SKS，1SKS=1.7ECTS；博士欄與2027網頁只列本科／碩士範圍分開，TKU適用未核實。接待至多20人可議，不是淡江quota。','Restriction',2),housing=I('partner可能按互惠免宿舍費、優先安排GuestHouse／Dormitory；depends on agreement及may不等於每人免费或保证床位。','eligible students may receive free dormitory'),costs=I('regularexchange無校方財務支持；partner學費免除仍依特定協議。2026表只明示免一學期，兩學期費用適用仍待核對。','While ITS does not offer financial support'),latest_forms=I('2027頁仍連2019/2022模板。已開2DOCX、XLSX、3頁2026FactSheet、19頁prospectiveguide及32頁2026generalguide。模板正文無學年度；courseform含[E.g.]範例及舊秋9–1月；HealthForm需英語與手簽，guide卻指醫師1–2頁與醫院章，模板沒有同樣醫師欄，待確認。指南非degree成績單與本科degree/博士資料分開，不把全部目錄套到exchange；未加入母校catalog。','ITS Health Information Form'),insurance=F('c66078617ff857ad4bf79066','無年份HealthForm強烈建議有可在印尼使用的医保、未買須自負醫療；不能當硬性統一保額或2027明定費率。','strongly recommended that you make your own health insurance','Intrinsically undated health template linked fromSpring2027; no verified2027 insurance amount',role='host_template_reference'),transport=F('b2210c9b8835a99c03af759e','2026generalguide接機是if receive pickup再通知，抵達Juanda指定terminal；不是所有交換生均保證免費接送。','if you receive airport pick-up service','Actual2026 general international-student guide; not2027 guarantee',5))
 its['latest_forms']['evidence']+=F('5493584d7040fb257bca569b','','[E.g.]','Intrinsically undated XLSX example; actual cells, not approved2027 course list')['evidence']+F('7be3b95d2b85f0f6c98b252a','','I will cover the tuition fee','Intrinsically undated behaviour/self-funding template linkedSpring2027')['evidence']+F('a828b8852053af90e48cb816','','The doctor must','Intrinsically undated prospective guide; body/year not established by filename2026',11)['evidence']
 its['latest_forms']['evidence'][1]['locator']='XLSX xl/worksheets/sheet1.xml cells B12/D12/V12/AH12; example only'
 its['course_restrictions']['evidence']+=IP('','Up to 20 students',1)['evidence']
 its['costs']['evidence']+=IP('','fully waived for one semester',2)['evidence']
 add(264,its)
 # SIT current bodyAY2027/28 fully read, retains contradictory older webpage.
 si='a906097f7984aab36743d119';sy='ActualAY2027–2028 SDW guidelines, updatedSeptember2026; TKU nominated programme unverified'
 def S(v,n,page):return F(si,v,n,sy,page,True)
 sf=dict(host_eligibility=S('本科／研究所母校在籍、交換後畢業前回母校；partner需正式提名。2027–28SDW與REP研究1月–1年另案，不能混用。','The applicant must:',5),host_language=S('2027–28英語CEFRB2；表列TOEIC785–940、IELTS5.5–6.5、iBT72–94等同範圍可變動，非自動新TOEFL換算。英語degree可官方授課語言信；未考列出測驗可母校出至少B2證明。日語可選課N2是修課條件，非全員入學門檻。','Notes on English Proficiency:',5),host_deadline=S('AY2027–28簡章列春entry10/1–31、秋entry4/1–30，月份沒有獨立年份，不自行補日期年。提名在TAO申請内完成、不能逾期。僅接待期限，母校本期資格／名額待核對。','Spring semester entry:',6),study_period=S('SDW1或2學期最多一年；春4月初–7月底、秋9月底–1月底；一年以4/1起算。單學期不能在交換中延長。精確抵達與orientation另通知。','No Extension of Study Period Allowed',7),campus=S('2027–28Toyosu（Tokyo）工程／建築／設計，Omiya（Saitama）系統工程科學；依實際課程與通勤選，不視為任意校區互換。','Toyosu campus (Tokyo)',9),department_scope=S('2027春起一般本科不得選研究所課；研究生可兩學制。5年一貫制高年级须母校證明碩士等同。建築主修可跨領域、非建築主修排除Architecture。網頁仍說符合先修本科可修graduate及全系皆可，來源矛盾待確認，保留PDF具體限制。','Starting from Spring Semester 2027',3),course_restrictions=S('全學期每週至少600分鐘，限SITMobility課表；依先修／餘額、建築實作限額不保證，母校學分認定另核對。','600 minutes',3),course_schedule=S('次學年度final課表約3月中公布；目前課表只能參考，不保證2027重開，暑期／fieldwork特別時段須另查。','around mid-March',4),costs=S('2027–28partner申請費JPY30,000不可因partner免掉；support/facilities每學期47,000，總一學期77,000／兩學期124,000，admission/tuitionwaived。non-partner表TBD明示待公布，與TKU協議本期未核實分開。','Application (Registration) fee',8),living_costs=S('申請財力證明每月JPY130,000，一學期5月650,000、兩學期10月1,300,000；这是證明門檻不是保证全支出。','The required amount is JPY 130,000',10),housing=S('Toyosu附近TIEC優先degree學生、短交換房極有限；OmiyaGlobalDorm超額須審，不保證床位。錄取後給房源／仲介資訊，須備其他選項。','accommodation cannot be guaranteed',13),latest_forms=S('TAO申請與母校提名、財力文件；新版Pledge正文Sep2026更新、學生手寫簽名不收typed/e-sign，母校coordinator亦签。3份PDF實開逐頁讀（14pguide/3pstart/1ppledge）。guide要求申請時體檢，網頁仍寫錄取後，保留矛盾；healthstage待確認。不加入淡江母校catalog。','Health checkup/certificate is required upon application.',5),transport=S('2027–28簡章明示不提供機場接送；依羽田／成田公共交通自行到住宿，不把國際支援當免費接機。','we do not provide the airport pick up',14))
 for key,needle in [('department_scope','both the Undergraduate and Postgraduate'),('latest_forms','after you accepted by SIT officially')]:sf[key]['evidence']+=F('189fe0a064d92bfeedfb411b','',needle,'Undated SDW webpage, conflicts with currentAY2027/28 guideline')['evidence']
 sf['host_language']['evidence']+=S('','at least CEFR B2 level',6)['evidence']+S('','JLPT N2 or Higher',4)['evidence']
 sf['department_scope']['evidence']+=S('','Five-Year Integrated Degree Programs',6)['evidence']
 sf['latest_forms']['evidence']+=F('ab48d2fdc4e619f64540f987','','Typed or electronic signatures','ActualPledge updatedSep2026, linked currentAY2027/28 programme',1,True)['evidence']+F('51e4f34fe8532d56c4f1199a','','required number of recommenders','Intrinsically undated current-linked TAO start guide;1nominator not2',3)['evidence']
 add(245,sf)
 # Two narrowly scoped references, not verified semester application rules.
 add(285,dict(department_scope=F('405107f3a5502a2178da302a','官方國際化正文分歐洲Erasmus+入境一學期、IntensiveWeek一週及freemover；沒有核實TKU雙邊學期track，不能以EuropeanErasmus或短期課推定TKU可選。','across Europe','Undated institutional programme strategy; TKU bilateral semester route unverified',role='host_programme_scope_reference')))
 om=F('4c3e22fa7e2d8e387fa2fd9d','OMU官方ac.jp頁連到臨時omu.moe國際事務公告／英語詢問；臨時頁寫目前無公告只限該公告feed，不是交換簡章官方尚未公告，也無當期入境表／校區。','There are no announcements at the moment.','Undated temporary international-affairs service; academic cycle not established',role='host_service_reference')
 om['evidence']+=F('ba04130f6cf4ca2e7b0cf361','','International Affairs','OfficialOMU ac.jp bridge to temporary service; no current exchange rules')['evidence']
 add(169,dict(student_support=om))
 # Accepted attachments alone: CAPTCHA responses excluded despiteHTTP200.
 for n in [264,245]:
  r=next(r for r in rows if r['id']=='tku-sister-'+str(n));cs=json.loads((BUNDLE/'milestone5_document_capture_checks.json').read_text());checks=[]
  for c in cs:
   if c['institution_id']!=r['id']:continue
   s=source(c['source_id']);assert s.get('local_file')
   checks.append(dict(source_id=s['id'],source_url=s['source_url'],checked_at=s['checked_at'],http_status=s['http_status'],local_file=s['local_file'],sha256=s['sha256'],content_reviewed=True,review_scope='opened and relevant instructions, semantic template content and applicable-year reviewed; no filename-only inference',applicable_year=sy if n==245 and c['ordinal']==6 else 'See individually quoted field: dated2026 factsheet or intrinsically undated current-linked template; not assumed revised2027',pages=len(s.get('pages',[]))))
  r['fields']['latest_forms']['attachment_checks']=checks
 assert len(rows)==12 and len({r['id'] for r in rows})==12
 assert all(f['status']=='reference_only' for r in rows for f in r['fields'].values())
 (BUNDLE/'milestone5_reviewed_host_facts.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(dict(additional_institutions=len(rows),additional_fields=sum(len(r['fields']) for r in rows))))
if __name__=='__main__':main()
