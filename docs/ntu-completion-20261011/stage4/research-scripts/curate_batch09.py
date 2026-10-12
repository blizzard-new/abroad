from research_curator import Curator,ROOT
import json
c=Curator();f=c.fact;b=c.body_review;d=c.decision;q=json.loads((ROOT/'priority-source-roster.json').read_text())
notes={
'26':'原7正文全讀，2026授課與生活支援不是申請日語門檻，住宿學年資格非交换甄選。已跟到官網2027英／日要項4頁並核對，2025版保留舊版，2027Fall與2028Spring分開。',
'378':'原4正文全讀；incoming共通頁、Spring2026 Seoul PDF、Fall2026宿舍、IIE独立语校分開。申请10/30与旧PDF10/31、宿舍11/30不可任择；费用旧年，保險／語言核對新頁。',
'37':'原6正文全讀，KUINEP本科／GEAuditor／GESResearch分開；现行英语72或4与2025/26 PDF79版本不同。母校6/12月得指南不等于2027未公告；奖学金非生活预算／一般资格。',
'40':'原6正文全讀，交换页母校提名／母校缴费，语言D4签证、NHIS2021费用与签证到校/延长手续不是exchange入学条件／申请截止。宿费每期依入住期，不推断未写的外租金额期间。',
'207':'原6正文全讀，院首页与住宿入口无交换GPA；GettingStarted有本科年级、MoneyMatters明确26/27预算与NU-SHIP。无入学文件全清单不视未公告；offcampus免费是平台服务非租金。',
'369':'原11正文全讀，9次StarRez公开登入壳没有房费，不进入帐号或用系统错误猜费；宿舍申请期2026/27不是2027/28。UH25–28calendar已采用不重复，暑期仅Manoa。此前公开oncampus费率已核实为旧年。'}
for pid,note in notes.items():
 for field,sids in q[pid]['fields'].items():
  for sid in sids:b(pid,sid,[field],note)
  d(pid,field,sids,'reviewed_original_body_scope_and_current_followups',note)
# Ochanomizu FY2027: contemporary text is explicitly scoped only to Fall2027 for NTU116-1.
sid='c97c35e59c980a2f';quote='Application Guidelines for Exchange Students';scope='御茶水FY2027要項4頁，適用2027秋10月至2028/3；不涵蓋2028春入學'
f('26',sid,'eligibility','御茶水FY2027限女性或自認女性；最新GPA推薦2.5/4，低於2.5可個案審核並先相談，不是絕對最低分。本科／研可選(a)聽課取學分；(b)研究交換只限研，期後返母校畢業。',scope,quote,page=2,period='target_year_explicit',locator='p1 statuses; p2 Application Requirement / recommended GPA and exceptions')
f('26',sid,'language','御茶水FY2027聽課交換須足以參與講授／研討／指導的日語，未列JLPT N級最低值；(b)研交換獲指導老師同意且研究英語足夠，可不具熟練日語。placement是分班，不用2026日語課level表當入學門檻。',scope,quote,page=2,period='target_year_explicit',locator='p2 Language Proficiency vs p3 placement test')
f('26',sid,'deadlines','御茶水2027秋入學申請2027/4/16截止；只限(b)研究交換事前登録2027/3/18。2027春事前9/18/2026、申請10/16/2026不屬臺大116-1秋2027／春2028的春學期，不能套至2028春。',scope,quote,page=1,period='target_year_explicit',locator='p1 pre-registration only(b) vs application, visual table confirmed')
f('26',sid,'documents','御茶水FY2027母校先登學生資料，學生線上資料並上傳護照ID頁、成績、COE純色底照片、適用JLPT結果與分數、指定推薦FormB；可母校coordinator／指導老師上傳。(b)研究另在事前截止交ResearchPlan FormA，可能與預定指導老師線上面談。不進登入／上傳或使用頁面密碼。',scope,quote,page=2,period='target_year_explicit',locator='p2 Pre-registration / Application documents and institutional submission phases')
f('26',sid,'calendar','御茶水FY2027秋學期在籍2027/10–2028/3，春2027/4–9；未細列秋2027第一授課／考試日，不以2026/10/1課程簡報改標2027精確開課。',scope,quote,page=1,period='target_year_explicit',locator='p1 Period of Study/Research, not exact class/exam days')
f('26',sid,'courses','御茶水FY2027(a)聽課取學分本科／研每週至少8課含日語；(b)研研究型只能經任課老師同意旁聽、不取學分。Japanese/Culture各2credit；SpecialJapanese非正規學分且抵認問母校，申請後placement分班。',scope,quote,page=1,period='target_year_explicit',theme='academics',locator='p1 status course load and p3 regular vs special Japanese classes')
f('26',sid,'housing','御茶水FY2027校內單人套房有床、淋浴、廁所、桌、冰箱、空調，洗衣共同且不供餐；公開要項說available，不等個人保證配房。',scope,quote,page=4,period='target_year_explicit',theme='housing',locator='p4 Accommodations and meals')
f('26',sid,'cost','御茶水FY2027寮入居一次JPY31680、月65300含租／共益／網路／保險／utility，另連帶保證4000；2025版月61900且gas除外不可改標當期。2027日本文明确gas公共费用included，校方不提供獎學金；未把寮保險當國民健康保險全部。',scope,quote,page=4,period='target_year_explicit',theme='cost',locator='p4 costs vs FY2025 p3; JP2027 p4 gas included; p3 scholarship none')
for sx in ['c97c35e59c980a2f','c74edca7feea258d']:
 b('26',sx,['eligibility','language','deadlines','documents','calendar','courses','housing','cost'],'完整4頁英日FY2027逐項比對；GPArecommended與研究型獨立流程、2027秋截止與宿費不同舊版。',visual_pages=[1] if sx==sid else None,visual_files=['ocha2027-deadline-page1.png'] if sx==sid else None)
# Kyoto program-scoped current rule vs older fact sheet.
sid='5e3603d6c575c91a';quote='Kyoto U General Exchange Program guidelines';scope='京都GE現行共通官網未標學年；GEA／GESR與KUINEP分開'
f('37',sid,'eligibility','京都GE須GPA3/4、海外協議母校在籍全期、良好學術紀律且結束返校；本科GEA聽課、研GEA或GESR研究由是否取credit分開，各院審核，不能把研研究型套本科。',scope,quote,locator='Eligibility and General Exchange student statuses')
f('37',sid,'language','京都GEA多數日語課需JLPT N1；研有限英語課門檻現頁iBT舊72／新band4或IELTS6.5並须足夠開課量。GESR視老師，通常N1或英語72/4 desirable，不是全員硬門檻；2025/26 PDF英語79與現頁72為版本差異，116-1待當期母校指南。',scope,quote,period='version_conflict',locator='Language requirements GEA vs GESR; FY2025/26 PDF English79')
f('37',sid,'cost','京都GE與KUINEP協議交換免考試、入學與接待校學費；JASSO80k/月競爭且他處月支持>80k或無Student在留不適用，不把獎學金當全員收入。共通頁NHI约2000/月、Gakubai2000/年、COOP會員4000可退，未標2027費率。',scope,quote,theme='cost',locator='Tuition and fees; Financial aid; Mandatory health insurance')
f('37',sid,'insurance_visa','京都GE/ KUINEP非日本國籍或永久居民须Student visa，京都代申COE，錄取後另細節；校頁要NHI與Gakubai及COOP，建議另旅保。政策與費率未當作2027政府法規法律意見；預備visa須回當期主管機關核對。',scope,quote,locator='Entering Japan / insurance sequence and nationality exception')
sid='91f5b31723d79864';quote='KUINEP guidelines'
f('37',sid,'eligibility','京都KUINEP限海外協議母校本科在籍全期，GPA3/4、良好學術紀律並期後返校，ILAS SpecialAuditor；不是研究所GEA/GESR。', '京都KUINEP現行未標年本科英語授課計畫',quote,locator='Eligibility / Student status')
f('37',sid,'language','京都KUINEP全英語無日語要求；現頁iBT72／band4、IELTS6.5或相當，與2025/26 PDF79分開版本，不以舊79覆蓋現行也不推算2027特定版。','京都KUINEP現行共通語言與2025/26舊factsheet',quote,period='version_conflict',locator='Language of instruction and scale footnotes')
sid='a9af522ac6ae0a16';quote='Exchange students'
f('37',sid,'deadlines','京都申請指南6月／12月寄母校，申請只經母校、不收學生直申；秋10月入學2月截止、春4月入學前一年9月截止僅共通月份。舊PDF2025秋提名1/17申請2/14、2026春提名8/22/2025申請9/19/2025不可改2027／2028。','京都現行母校指南流程未載2027精確截止；舊2025/26PDF另保留',quote,locator='Overview / partner guide delivery / month-only deadlines')
f('37',sid,'documents','京都現行頁只说明母校國際處提交、6/12月寄指南，沒有完整申請附件清單；可記當期指南須經母校取得，不能把COE、课程選單或奖学金附件當完整交換申請文件或「確實未公告」。','京都現行exchange Overview；institutional application guide availability',quote,locator='Application guide sent to partner institutions, no complete document list here')
sid='a21f0ff9a2176452';quote='Kyoto University Exchange Program for 2025/26 Fact Sheet'
f('37',sid,'housing','京都2025/26舊表6個InternationalHouses等宿舍，月JPY12400–44400不保证；2021全國生活平均93000不是京都2027支出。該頁2025/26價格按舊年保留。','京都2025/26 factsheet；2021生活全國平均非京都當期',quote,period='older_year_reference',theme='housing',locator='p1/2 Other housing and cost-of-living scope')
# Suncheon: exchange entry versus language training and resident paperwork.
sid='3944f14a59553bdf';quote='Exchange Student';scope='順天SCNU Exchange Student共通未標年度'
f('40',sid,'eligibility','順天交換限協議母校在籍提名、一或兩學期、母校繳學費並轉回credit；頁無GPA或語言最低值，不取NHIS資格／宿舍成績豁免作學術門檻。',scope,quote,locator='Introduction / nominated exchange students')
f('40',sid,'deadlines','順天交換頁春12月、秋6月申請，審核1/7月中、錄取1/7月底；共通月表未標2027精確日，語校visa3週–2月與延長4個月前不是交换deadline。',scope,quote,locator='Exchange Calendar vs visa processing windows')
f('40',sid,'documents','順天交換頁仍說email申請、online將來接受、ALL required docs齊才處理，但此頁未列全部附件；只記未取得完整清單。外國居留申請／延簽護照、住址、成績等不是初輪交換必繳清單。',scope,quote,locator='How to apply / application docs missing on this page')
sid='df8efe233edee32b';quote='Housing'
f('40',sid,'housing','順天官網稱所有國際學生可住寮且不依分數，校內約步行5分雙人公寓型；仍須按當期入住流程確認，不以1896全校床位當臺大交換名額。語校trainee原則須住寮是另一身分。','順天Housing未標年份；國際學生與語校身分分開',quote,theme='housing',locator='On-Campus introduction / residence scope / language trainee rule')
f('40',sid,'cost','順天校內約KRW1900000含餐或800000不含餐，按每學期入住期變動；校外250000–400000隨房型未明載期間，不自行改成每月。租約自簽，公開外國／穆斯林自炊kitchen免費非全部住宿免費。','順天Housing費用未標年與入住期；外租表未標period',quote,theme='cost',locator='On-campus costs per check-in period vs Off-campus unspecified-period prices')
sid='1069b0399d573355';quote='National Health Insurance'
f('40',sid,'insurance_visa','順天NHIS頁明列2021保費43490等及D2居留登記、D4六個月後不同生效；不升格2027費率／普遍D2等半年。民間團保年140000/半年80000也未標当期，不替代NHIS核對；表中保費減免202170%是歷史。','順天Insurance頁2021主段與未標年團保；D2/D4分開',quote,period='older_year_reference',locator='National Health Insurance 2021 and Illness/accident group policy')
# Northwestern publicly published costs and level requirements.
sid='c3db6f018c500d7d';quote='Getting Started'
f('207',sid,'eligibility','西北本科交換至少完成一年大學、協議母校提名及英語能力；每term通常4課，可修Weinberg／McCormick本科且須先修與有空位；住宿與院首頁沒有GPA數字。','西北本科incoming共通未標年度',quote,locator='Verify eligibility / Identify academic goals')
f('207',sid,'housing','西北交換on-campus不保證，依餘額盡力安排，可Evanston/Chicago校外；校外網站可公開browse，聯繫刊登須NetID，平台免費不是租房免費／校方房東背書。','西北incoming与Off-campus housing共通；不登入',quote,theme='housing',locator='Research housing options; official offcampus disclaimer read')
sid='93f93b78a44f3e4f';quote='Costs & Money Management'
f('207',sid,'cost','西北明列2026–27每quarter預算USD12500：prearrival2000、hosttuition0、房4200餐2950保險2000書300交通200個人850；保險全期一次預收不能按quarter付，房餐各quarter。prearrival是護照/visa/往返機票，不能把該一次支出機械乘每季或改成2027–28費率。','西北2026–27 quarterly student budget含pre-arrival一次項目',quote,period='older_year_reference',theme='cost',locator='Student Budget per quarter; Billing NU-SHIP upfront versus quarterly housing/meals')
f('207',sid,'insurance_visa','西北要求整段exchange用NU-SHIP且一次預收全部，2026–27budget保險估2000；不是任意海外保單可代替。當期金額須2027–28正式版本，billing付款介面標Tuition仍可支付房餐保險、非重新收免除學費。','西北2026–27 budget與未標年billing程序',quote,period='older_year_reference',locator='Health Insurance mandatory policy / upfront full-period billing')
c.save();print('observations',sum(len(s['observations']) for s in c.schools.values()))
