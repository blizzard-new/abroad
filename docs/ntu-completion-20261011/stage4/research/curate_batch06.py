from research_curator import Curator
c=Curator();f=c.fact;d=c.decision;b=c.body_review
sid='b72528f679f2995f';q='Spring 2027 - fall 2027';scope='HUFS官網Spring2027–Fall2027；2027秋、Seoul與Global；不涵蓋2028春'
f('1305',sid,'eligibility','HUFS2027交換參與時須在現行學位的母校至少完成一學期，GPA至少2.5/4.0。是接待校資格，未替代臺大116-1甄選資格。',scope,q,period='target_year_explicit',locator='Program Eligibility')
f('1305',sid,'language','HUFS2027英語授課可IELTS6、TOEFL/ITP550、CBT213、iBT80、TOEIC750或母校英語能力證明擇一；韓語授課可TOPIK3+、KLAT150+(B2)、大學韓語15小時(4–5門)、HUFS intensive level4或母校韓語證明擇一。原頁仍用舊iBT尺度，沒有列2026新尺度對照，不自行換算。',scope,q,period='target_year_explicit',locator='Language Proficiency / English / Korean')
f('1305',sid,'deadlines','HUFS2027秋季提名與申請期間明列2027/2/1–4/30，官網把兩程序合列，不能自創不同截止。Spring2027另列2026/8/1–10/30；web搜尋快取仍顯2027/8/1，與本輪原始HTML不同，Spring不在116-1適用範圍且不拿快取覆蓋即時原文。',scope,q,period='target_year_explicit',locator='Nomination & Application Period; live HTML SHA24a351... vs stale web cache')
f('1305',sid,'calendar','HUFS2027秋季為9/1–12/21；兩校區迎新均開學前一週工作日但TBC，宿舍入住／退宿實際日亦TBC。可確認學期日期，但迎新與入住日期屬原文明確未定，不能說全部時程未公告。',scope,q,period='target_year_explicit',locator='Semester Dates / New Student Orientation / Dormitory Check-in-out Dates')
f('1305',sid,'documents','HUFS2027先線上申請，審查後約一週才出Google Form連結。英語文件：申請PDF、至少1頁經歷與讀書計畫、成績、在學、非英語母校的英語證明或推薦、護照、3×4白底彩色JPEG照；住宿另宿舍表、Intensive Korean另至少1頁計畫。非OECD護照在學證明須apostille或韓國使領館認證；財力須等校方在申請後另要求，不預先當首輪未繳。',scope,q,period='target_year_explicit',locator='Required Application Documents; two-stage process / conditional documents')
f('1305',sid,'cost','HUFS2027財力欄的4/6個月KRW8,000,000、10/12個月16,000,000是母校學費加生活費的移民財力基準，生活費須至少其中一半，不能當接待校收費或實際月預算；非OECD另母校學費繳交證據。一般非韓語／東亞主副修者Intensive Korean自付800,000，對應主副修常規學期全免；寒暑假不享同全免、原頁折後約1,141,000；Survival Korean交換生免。',scope,q,period='target_year_explicit',theme='cost',locator='Financial Statement vs optional Intensive/Survival Korean fees')
f('1305',sid,'housing','HUFS2027宿舍先到先審但不保證名額，每學期須重新申請；Google Form選住宿不等於獲分配。入住TB證明：Globee與Global僅X-ray，International House可X-ray或skin；原頁明稱所有宿舍不用Hepatitis test。',scope,q,period='target_year_explicit',theme='housing',locator='Housing; Required Documents dormitory TB conditions')
f('1305',sid,'courses','HUFS2027禁選清單包括碩士法學院、Language & Diplomacy／Trade、BA Communicative Languages electives、教育學院、Graduate Interpretation & Translation等；BA商學僅第二輪中段可登記且競爭、不保證第一志願。Intensive Korean非學分，另至少一門本科／研究所課。',scope,q,period='target_year_explicit',theme='academics',locator='Restricted/Semi-restricted Courses; Korean Language program')
f('1305',sid,'insurance_visa','HUFS2027頁要求入境前取得D-2-6／D-2-8，錄取後提供acceptance、admission與分校business registration。保險文字的Otherwise/NHIS條件仍须讀專頁，未據此判斷私人保險即可豁免國民保險。',scope,q,period='target_year_explicit',locator='Admission Package / Visa Process / Health Insurance ambiguity')
b('1305',sid,['eligibility','language','deadlines','documents','cost','calendar','housing','courses','insurance_visa'],'完整15,647字factsheet已讀；2027秋明示，2028未載，所有校區／条件文件與金額用途分開，保險专頁尚須跟進。')
# Newly readable application/cost sources supplement previously negative page-scope checks.
sid='6c857a110f5d918d';q='Requirements for exchange students';t=c.read_source(sid)['text'];q='J-1 Exchange Student Application' if 'J-1 Exchange Student Application' in t else 'Application'
f('1299',sid,'eligibility','NJIT J-1交換須母校與NJIT有協議且獲母校提名，母校當期成績GPA至少3.0/4.0。建筑／設計另portfolio與系所核准；未標學年，不套2027。','NJIT Global J-1 Exchange application；未標年度',q,locator='Application requirements / architecture-design portfolio')
f('1299',sid,'language','NJIT J-1頁列TOEFL iBT79、IELTS6.5或Duolingo120的英語證明；iBT未列2026新尺度，保留原尺度與未標年度，不能當NTU116-1已核實門檻。','NJIT J-1 exchange application；undated',q,locator='English language proficiency requirement')
f('1299',sid,'documents','NJIT J-1申請須Exchange application、DS-2019 eligibility request、財力、當期母校成績、護照及英語證明；Architecture/Design另portfolio及系所許可。DS-2019與財力用途不當臺大甄選文件。','NJIT J-1 exchange application；undated',q,locator='Supporting documents list')
f('1299',sid,'deadlines','NJIT J-1申請秋季5/1、春季10/15；這是交換申請日，與先前保險waiver申請日不同。官網未標年份，仍待2027年度確認。','NJIT J-1 application；undated',q,locator='Deadlines for Submission')
sid2='bec23f16952ac276';q2='J-1 Exchange Student Costs' if 'J-1 Exchange Student Costs' in c.read_source(sid2)['text'] else 'Costs'
f('1299',sid2,'cost','NJIT J-1估每月至少USD2,000、semester通常4個月；學費依交換協議，不能一律宣稱全免。保險估USD1,100/學期含提前一週抵達，personal/misc另列600/學期但勿在2000月估之外自動重加。住宿雙人房標準不含Maple，頁面缺各房型數字；meal plan可選。','NJIT J-1 exchange costs；undated estimate, not 2027 price',q2,theme='cost',locator='Cost breakdown / funding / health insurance')
for field in ['eligibility','language','documents','deadlines']:
 b('1299',sid,[field],'完整J1申請正文已讀；身分、申请vs保险waiver日期分開。')
 d('1299',field,[sid],'reviewed_undated_reference_added','先前保险页不是学业资格，本轮新增J1官方申请具体规则；仍无2027年度。')
b('1299',sid2,['cost'],'完整J1费用正文已读，月／学期、估計／實收、學費協議分開。');d('1299','cost',[sid2],'reviewed_undated_reference_added','具體金额已取得但未標年度；保留旧保险页範圍判讀，不改為2027價格。')
sid='523faeda4ebe3971';q='The program-wide minimum language proficiency requirements apply'
f('798',sid,'language','長崎一般交換全計畫最低日語CEFR B2：JLPTN2總分至少112或N1，須成績證明與score report兩份；英語须官方CEFR B2測驗，種類／分數／免試依院。院低於或未設門檻仍適用全計畫最低，高於則从高，雙語課須兩語均合格。GHSS另iBT2026/1/21起4.5、此前79／IELTS6／B2；教育院表iBT45旁註全計畫最低仍適用，不把45採為普遍最低。','長崎一般交換未標學年PDF p2目視、p3–6学院；2026尺度切换明示',q,page=3,locator='Visual scanned p2 + faculty table red minimum notes p3–6')
f('798',sid,'eligibility','長崎一般交換须在交換全期間維持母校正規在學；醫學僅醫學背景的基礎研究，健康科學限护理／PT／OT，藥學大三以上；研究所多院须指導教師內諾及證明，經濟研究所另細分碩／博。不是所有學生均可用通用條件。','長崎一般交換undated p1、p4–6；各学院',q,page=3,locator='Visual p1 / undergraduate restrictions p4 / graduate p5–6')
f('798',sid,'deadlines','長崎一般交換秋季母校提名5/10、學生申請5/20，春季提名11/10、申請11/20；文件未標學年，不能轉成2027確定日。錄取／COE通常秋8月中後、春2月中後。','長崎一般交換undated p1目視；兩階段日期',q,page=3,locator='Visual scanned p1 nomination/application and acceptance/COE chart')
f('798',sid,'courses','長崎一般交換各院學分不同：GHSS至少每週10小時約7課且至少一半GHSS，另註14–24credits，两條原文皆保留；教育14–25專門且不可申請後改選，牙醫專門7但含GE總14；JLCP另有不同學分與禁專業課規則，不能混用。','長崎一般交换undated p3/4学院表；不是JLCP',q,page=3,theme='academics',locator='GHSS hours and credits / Education / Dentistry table')
b('798',sid,['eligibility','language','deadlines','courses'],'全部6頁已讀；p1/2抽文字为空但已render逐页目視，p3–6文字及版面均核对，6張PNG留存。',visual_pages=[1,2,3,4,5,6])
sid='31c7adffc34d29c8';q='Japanese Language and Culture Program';scope='長崎JLCP文件明載2026–27 JASSO未入選；舊年度，不同一般交換'
f('798',sid,'eligibility','JLCP須合作校正規在學並維持、母校推薦、主／副修日語或以日語與日本文化學習為主要目的、學業優良及原則非日本籍；母校一般交換資格不足以保證JLCP。',scope,q,page=1,period='older_year_reference',locator='p1 Eligibility')
f('798',sid,'language','JLCP須JLPTN3或同等，語測在申請開始前2年內，須score及certificate；這是JLCP，不能套一般交換B2/N2規則。',scope,q,page=1,period='older_year_reference',locator='p1 language / p5 required test results')
f('798',sid,'documents','JLCP9項：近期3個月內4×3照片(JPEG/PNG/GIF)、熟悉日語能力的一封教師／指導推薦(日／英)、在學、成績、約1000日文字指定essay、護照、指定健康表、COE Excel、2年內日語測驗成績及certificate。不能把照片直接用護照照片或把推薦寫2封。',scope,q,page=5,period='older_year_reference',locator='p5 Documents Required for Application')
f('798',sid,'deadlines','JLCP秋季申請4/1、春季10/20，通知經母校；這與一般交換5/20、11/20不同且為原版規則，非2027確定截止。',scope,q,page=5,period='older_year_reference',locator='p5 Application Deadlines')
f('798',sid,'cost','JLCP超過MoU免學費名額可能改Fee-Paying，其費用JPY14,800/credit且可變；接待校約50人/學期、約30免20付費只是host計畫容量，完全不代填臺大名額。2026–27 JLCP未獲JASSO選定，不宣稱該年必有獎學金。',scope,q,page=7,period='older_year_reference',theme='cost',locator='p2 host capacity / p7 Fee Paying / p8 JASSO2026-27')
f('798',sid,'courses','JLCP完成至少7credits/學期、14/year，GE不算JLCP完成學分；僅本科AdvancedJapanese I/II能日語GE、本科任level英語GE，研究生不能GE；JLCP不能專門faculty課。',scope,q,page=7,period='older_year_reference',theme='academics',locator='p4 GE access / p7 completion credits')
b('798',sid,['eligibility','language','documents','deadlines','cost','courses'],'完整8頁JLCP已讀，容量／母校名額及JLCP／一般交換分開，2026–27舊版。')
for field in ['eligibility','language','deadlines']:
 d('798',field,['523faeda4ebe3971','31c7adffc34d29c8'],'reviewed_program_and_cycle_scope_split','一般交換未標年與JLCP2026–27已區分；語言／截止兩計畫不同，非自行選高或挑早。')
sid='f975649735f1756b';q='TARIFAS ACTUALIZADAS SEMESTRE 2026-1'
f('1283',sid,'housing','Uniandes官方2026-1住區月價是每人且至少5月合約，原頁$：2AI3,249,000；4A1,599,000；4B3,049,000；3CC1,399,000；3A1,799,000；3B2,099,000；2A1,899,000。頁未寫幣別代碼，不改成美元；水電WiFi及每月6次清潔含，寢具裝飾厨具洗衣不含。以availability為準，5/10月全繳2%折扣屬条件；不是保證on-campus分配。','Uniandes住房2026-1；每人月價、5月最低合約；原頁$未明示代碼',q,period='older_year_reference',theme='housing',locator='Tarifas2026-1 rate table / inclusions / conditions')
b('1283',sid,['housing','cost'],'完整官方房價表已讀，月／semester、每人、合約長度及币别未明示分開。')
for pid,sid,fields,note in [('1187','2a56237663aa6548',['cost'],'完整Google Slides入口只有工具UI；官方HTML view公開可讀連結待跟進，非須權限結論。'),('1305','793069d05bb46405',['cost'],'完整GeneralFAQ已讀，wifi/calendar/airport不是費用額；最新Factsheet另已讀。')]:b(pid,sid,fields,note)
c.save();print('observations',sum(len(s['observations']) for s in c.schools.values()))
