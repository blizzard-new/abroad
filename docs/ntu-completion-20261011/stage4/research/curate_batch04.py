from research_curator import Curator
c=Curator();f=c.fact;d=c.decision;b=c.body_review
sid='6317a3fa41596725';quote='Only applications from students nominated by their home university will be considered.'
f('1283',sid,'language','Uniandes2025–26西語授課需CEFR B1，可由母校、合格語師或認可西語機構證明；英語授課需B2證書。多數課西語、英文課有限且開學前幾週才公布，不保證全英修課；未列特定TOEFL／IELTS數字。','Uniandes Undergraduate–Master2025–26 p1/p3，依授課語言；原年度',quote,page=1,period='older_year_reference',locator='p1 Required Documents3/p3 Languages of Instruction')
f('1283',sid,'documents','Uniandes2025–26交換列護照JPG、正式西／英語成績單PDF（不收非正式或截圖）、語言證明、當期修課證明PDF、西／英語動機信PDF、3×4白底照片JPG；碩士另CV，建築／設計另作品集。母校提名後才寄申請入口，原年度不得直接改新期。','Uniandes Undergraduate–Master2025–26 p1；UG/Master及Architecture/Design個別項',quote,page=1,period='older_year_reference',locator='p1 Required Documents and Additional Master Documents')
f('1283',sid,'cost','Uniandes2025–26 Bogotá五個月估算：房COP6.5–13.5百萬、餐3.5–4.7百萬、安置1.5百萬、交通3.1百萬、其他2.5百萬；合計17.1–25.3百萬COP。不是每月金額，也不是2027正式收費；校方住宅網站僅出現2026-1Tarifas入口，須讀價目附件。','Uniandes2025–26 p4 five-month budget；COP；住房網站2026-1另查',quote,page=4,period='older_year_reference',theme='cost',locator='p4 five-month budget table, separate housing Tarifa2026-1 link')
for field,sources in {'language':[sid],'documents':[sid],'cost':[sid,'ced1da6c2ba9e7fa']}.items():
 for source in sources:b('1283',source,[field],'完整4頁factsheet及所需住房首頁正文已讀；原2025/26、五個月COP與每月不能互換；住宅2026-1只有价目連結待跟進。')
 d('1283',field,sources,'reviewed_previous_cycle_reference','本欄既有可讀候選正文全部讀完；新增舊年明文，費率附件／新期仍待官方後續來源，未宣稱全校未公告。')
sid='49e05d85eb4bcc46'
for field in ['eligibility','cost']:
 b('1200',sid,[field],'完整實用指南已讀；visa、保險／居留註冊為到校手續，不是學科／GPA入學資格；€295semester與約350六個月保險皆未標年度，對照最新2026/27semester頁不一致。')
 d('1200',field,[sid],'wrong_scope_no_exchange_field_detail' if field=='eligibility' else 'reviewed_document_conflict','完整指南已讀，資格候選為到校居留／保險手續，費用舊€295與已查Winter2026/27€369.50差異保留，未改標2027。')
sid='eb5b55b713c2243b'
f('1103',sid,'cost','Thomas More交換blocked account明列26/27為每月€1,062×5月加€250行政費，共€5,560；月款返回本人比利時帳戶，行政費不返。此是簽證財力證明方式，不是額外學費或2027/28固定生活價目；政府月最低額可變。','Thomas More exchange visa blocked account26/27；有接受資格與辦理身分','Blocked account 26/27',period='older_year_reference',locator='Proof of Solvency/Blocked account26/27 formula/refund')
f('1103',sid,'documents','Thomas More交換錄取後，校方在申請截止後寄acceptance letter，可供簽證；blocked account程序須個別向International Office取得。這不是首次交換申請文件清單，也不是臺灣護照簽證已核實。','Thomas More交換visa acceptance letter及blocked account；未標新期身分細節','Blocked account 26/27',locator='How do I get acceptance letter/How to apply blocked account')
for field,sources in {'eligibility':['3a99363d7665d435'],'deadlines':[sid],'cost':['5088358012faf0a8','7474bee1c14913e1','d3b17ee5f6c06e17',sid]}.items():
 for source in sources:b('1103',source,[field],'完整所有候選正文已讀；exchange programme列表或Geel Agriculture介紹無資格／费用，opkot首頁無房租；visa處理3–4月與提前2週抵達為規劃建議非入學截止。26/27blocked account為財力程序。')
 d('1103',field,sources,'reviewed_reference_partial_scope' if field=='cost' else 'wrong_scope_no_exchange_field_detail','全部既有可讀候選已讀；保留26/27財力費用，有效申請期限／入學條件仍需正式exchange application頁；不是可用網址耗盡。')
sid='93a530beda958f5a';quote='FACT SHEET'
f('11',sid,'eligibility','OU2026–27交換須完成母校第一學年、學業良好、母校正式提名；校區Norman，不能把一般OU新生住校兩學期要求套交換生。此為2026–27，不直接採作2027新期。','OU Factsheet2026–27 Norman incoming exchange p1；非學位新生',quote,page=1,period='older_year_reference',locator='p1 Student Nominations academic standing')
f('11',sid,'documents','OU2026–27提名後寄個人線上申請，無需紙本：護照個資頁、英語證明、財力文件、翻成英文成績及當期修課；選課志願稍後另索。不能把推薦或申請入口尚待寄送解讀為公開完全無資訊。','OU2026–27 p1 online Application Requirements；推薦與申請分別',quote,page=1,period='older_year_reference',locator='p1 Application Requirements items1–5')
f('11',sid,'language','OU2026–27：學士iBT79、IELTS6.5、PTE53、DET100；研究生iBT79舊制／4.5新制、IELTS6.5、PTE60、DET115。ITP不收；母校全英文授課可考慮豁免。保留原制及UG/GR差異，不自行換算或套2027。','OU2026–27 p1 UG/GR English requirements，原量表',quote,page=1,period='older_year_reference',locator='p1 English Proficiency UG/GR columns')
f('11',sid,'deadlines','OU2026–27伙伴提名秋／academic year3/15，春／calendar year9/15；提名结束後才寄學生申請連結。這是提名截止，不是完整學生申請截止，不能取Summer2026加退選日期代替。','OU2026–27 p1 Nomination Deadlines；nomination vs personal application',quote,page=1,period='older_year_reference',locator='p1 nomination table/application instructions')
f('11',sid,'cost','OU2026–27交換費用估：餐費$400–600/月、個人$400–800+/月；書$250–800及保險秋$1,132／春$898列在每學期估算，另有卡／迎新／成績單費未定額。每月與每學期分開、不可合算假總額或移標2027。','OU2026–27 p2 Estimated Living Expenses per semester內部month子項',quote,page=2,period='older_year_reference',theme='cost',locator='p2 Estimated Living Expenses and other fees')
for field,sources in {'eligibility':[sid,'da3c8a6e782c82da','e9a1ee782d00396a'],'language':[sid],'deadlines':[sid],'documents':[sid],'cost':[sid,'da3c8a6e782c82da','e9a1ee782d00396a']}.items():
 for source in sources:b('11',source,[field],'完整2026/27兩頁factsheet、一般新生住房首頁及Summer2026兩頁年曆已讀；交換、學位新生與summer加退選分開；夏季late registration$20不是交換學費。')
 d('11',field,sources,'reviewed_previous_cycle_reference','本欄既有候選全文已讀；2026/27明文完整保留範圍，Summer2026及一般新生住房不作交換條件，須追新期及正式學生截止。')
c.save();print('observations',sum(len(s['observations']) for s in c.schools.values()))
