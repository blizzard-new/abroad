from research_curator import Curator
c=Curator();f=c.fact;d=c.decision;b=c.body_review
web='1bb84f6ea4bd3126';pdf='67f36382771ba8d3'
f('1164',web,'eligibility','恒生官網只接受合作校正式提名；申請時已完成母校至少一學期、累積GPA至少2.5/4或同等。頁連結2026/27春時程，未確認2027–28個別期條件。','HSUHK inbound application一般規則；頁連結Spring2026/27','minimum cumulative Grade Point Average of 2.5',locator='Eligibility/How to Apply')
f('1164',web,'language','恒生非英語母語者需TOEFL550紙筆／213電腦／79網考，或IELTS6；若已完成大量大學程度英語授課亦可能滿足語言能力。保留官網原型態與數字，不換算新TOEFL量表或宣稱個人豁免。','HSUHK inbound application未標新期語言條款','minimum cumulative Grade Point Average of 2.5',locator='Eligibility English qualifications and substantial English coursework')
f('1164',web,'deadlines','恒生官網Application Deadline為秋4/15、春10/1，另連結Spring2026/27時間表；臺大刊載Jan2025factsheet卻寫春Nomination & Application為10月中至下旬，兩版本範圍／日期不一致。不可直接決定2027新期日程。','HSUHK官網常年申請日vs Jan2025factsheet提名及申請合列','minimum cumulative Grade Point Average of 2.5',period='version_conflict',locator='Application Deadline vs factsheet p1 Nomination & Application Deadline')
f('1164',pdf,'documents','恒生Jan2025factsheet要求由合作校提名、填HSUHK Admission Form並經合作校送相关文件；沒有逐一列上傳清單。官網稱被提名者完成online form及相關文件，仍須讀指定表單／提名後指引，不能宣稱清單未公告。','HSUHK Student Exchange factsheet Jan2025 p1；學校刊載文件原版','Updated in Jan 2025',page=1,period='older_year_reference',locator='p1 Application Method; official application page How to Apply')
f('1164',pdf,'cost','恒生Jan2025交換factsheet估住宿HK$1,900–2,300/月、餐費4,000/月、個人支出2,000/月，房型與消費習慣有別；不能當2027正式收費。保險需自行購買且出發前提交涵蓋醫療、住院、事故、緊急撤離／送返的證明。','HSUHK Jan2025factsheet p2；HKD月估生活及保險範圍','Updated in Jan 2025',page=2,period='older_year_reference',theme='cost',locator='p2 Estimated Living Cost/Health Insurance')
for field,sids in {'eligibility':[web,pdf],'language':[web,pdf],'deadlines':[pdf],'documents':[web,pdf,'8983445a87d3fd41'],'cost':[pdf,'8983445a87d3fd41','c4900e49178c53ec']}.items():
 for source in sids:b('1164',source,[field],'完整本欄候選正文已讀：inbound官網、Jan2025兩頁factsheet、incoming首頁索引及outbound心得身分分開。春截止版本不同、完整文件仍需正式流程。')
 d('1164',field,sids+[web] if field=='deadlines' else sids,'reviewed_document_conflict' if field=='deadlines' else 'reviewed_reference_added_partial_scope','本欄既有可讀候選全讀；舊版／常年資訊与incoming/outbound分開，未當作2027完整规则；精確時間表與文件須續查官網連結。')
sid='bbc62867f0c55219';quote='Undergraduate students are required to demonstrate a minimum GPA of 3.0'
f('986',sid,'eligibility','希伯來大學University-level及Erasmus+交換：學士GPA至少3.0、研究生3.2或同等；Faculty-level依該院資格，若跨修RIS亦須符合RIS條件。必須母校提名，校方保留最終錄取判斷，未作2027校內甄選門檻。','HUJI incoming通則；university-level/Erasmus+/faculty-level分別；未標年度',quote,locator='Eligibility and Admissions three exchange tracks')
f('986',sid,'language','HUJI university-level/Erasmus+非英語國家及未完成英語授課學位等需英文能力證明：TOEFL80、IELTS6、Cambridge／CEFR／大學語言中心B2等；DAAD可列B2或TOEFL80／IELTS6同等。院級依院規，希伯來文授課另需相應希伯來語條件，未保證跨院豁免。','HUJI incoming常年英文條件；不同交換協議及授課語言；未標年度',quote,locator='Eligibility language certificate list; Courses Hebrew requirements')
f('986',sid,'documents','HUJI母校提名後線上申請列CV、SOP、正式成績單、medical form、護照個資頁、證件照、兩封保密學術推薦、study abroad approval form、英文成績；文件及線上入口個人資訊提名後再寄。此為公開常年清單，非2027已確認完整個人文件。','HUJI incoming Application and Admissions；partner nominee；未標年度',quote,locator='Application and Admissions online document list')
f('986',sid,'deadlines','HUJI公開申請截止：秋／全年5/15；春學士11/30、研究生12/31。逾期須program director同意才受理，不是保證寬限；本頁未標2027，亦未提供母校提名截止。','HUJI incoming常年application deadlines；UG/GR及nomination分開',quote,locator='Application Deadlines and late application condition')
f('986',sid,'cost','HUJI交換免接待校註冊費及學費，向母校繳費；Ulpan等不在交換包內須另付。Arabic independent study另原文$400/credit，未在此頁核清幣別，不當USD或全部課程費。','HUJI incoming Tuition Fees/Hebrew-Arabic special courses；未標年度',quote,locator='Tuition Fees; Arabic Language Study special fees')
for field in ['eligibility','language','deadlines','documents']:
 b('986',sid,[field],'完整incoming頁全部可用文字已讀，包含三類協議、RIS與院級差異、申請清單、deadline及例外；未標新期，不用普通招生或院級條件代替所有交換。')
 d('986',field,[sid],'reviewed_reference_added_partial_scope','完整本候選正文已讀並補明文；保留未標年度／交換類型範圍，尚須新期及院系具體確認。')
c.save();print('observations',sum(len(s['observations']) for s in c.schools.values()))
