from research_curator import Curator
c=Curator();f=c.fact;d=c.decision;b=c.body_review
b('1305','853a22d949a5aba3',['cost'],'完整讀取Fall2026迎新welcome頁，僅校區與聯絡人／影片，無費率或金額；不是未公告證明。')
d('1305','cost',['853a22d949a5aba3'],'readable_service_index_no_rule_detail','完整迎新welcome正文已讀，Fall2026並非新期，未列费用；須沿官網費用頁追查，不歸外部阻礙。')
b('98','5c4574a1a0169008',['language'],'完整語言中心首頁已讀，是語言課註冊、檢定與課期，不是國際交換入學最低語言門檻；舊2026/27課程日期不套2027/28。')
d('98','language',['5c4574a1a0169008'],'wrong_scope_no_exchange_field_detail','本頁明示課程及語言中心服務；CEFR、IELTS等檢定名稱與課程註冊日期不是incoming交換最低語言規定。')
b('39','15bc2387e6465438',['eligibility'],'完整Domestic Exchange正文已讀；韓國境內46所合作校與SNU出境GPA，不適用臺大國際incoming；數值不採。')
d('39','eligibility',['15bc2387e6465438'],'wrong_scope_no_exchange_field_detail','頁面國內交換與韓國合作校清單；Outbound GPA2.7/3.3不是臺大赴SNU資格，Inbound國內提名規則亦不能套國際交換。')
sid='a2e23a4ebc2d6a8b'
f('798',sid,'eligibility','長崎2026factsheet分一般Student Exchange與JLCP。一般須合作校全時在學並維持到3/31或9/30、符合申請院系條件，僅可申請母校同一學位層級；研究所交換僅研究指導、無學分授課。JLCP另限非日本籍，未作2027新期完整資格。','NU Factsheet2026一般交換／JLCP分列；臺大甄選與實際計畫分配未定','Must be enrolled as a full-time student at one of our partner',page=2,period='older_year_reference',locator='PDFp2 Exchange programs/Qualification and program outline')
f('798',sid,'language','長崎2026factsheet的JLCP明列JLPT N3或同等，不能套到一般Student Exchange；一般交換語言與院系條件須讀Program Outline & Requirements連結。','NU Factsheet2026 JLCP vs Student Exchange；非新期共同語言門檻','Must be enrolled as a full-time student at one of our partner',page=2,period='older_year_reference',locator='PDFp2 two program columns, JLCP Qualification')
f('798',sid,'deadlines','長崎2026一般交換：春提名11/10、申請11/20，秋提名5/10、申請5/20；JLCP：春提名10/10、申請10/20，秋提名3/20、申請4/1。日期屬2026文件的分計畫參考，不作2027提醒。','NU Factsheet2026 p2；partner nomination與student application及計畫分開','Must be enrolled as a full-time student at one of our partner',page=2,period='older_year_reference',locator='PDFp2 Nomination Deadline/Application Deadline two columns')
f('798',sid,'calendar','長崎文件題名2026，但p1表題仍為ACADEMIC CALENDAR FOR 2024，只有Late/around通則及住宿日期稍後公告；不能視為2026或2027確定年曆。','NU Factsheet2026文件／p1 Calendar2024題頭版本不一致','Must be enrolled as a full-time student at one of our partner',page=1,period='version_conflict',locator='PDFp1 FACTSHEET2026 vs ACADEMIC CALENDAR FOR2024')
f('798',sid,'housing','長崎2026factsheet稱交換生有宿舍優先權，未保證配房；具體宿舍資料另有官網連結。','NU Factsheet2026 p3，交換生住宿優先權；非新期個人配房證明','Must be enrolled as a full-time student at one of our partner',page=3,period='older_year_reference',theme='housing',locator='PDFp3 Accommodation')
f('798',sid,'insurance_visa','長崎2026factsheet說明COE寄母校後自行辦學生簽證；日本居留逾三月須加入國保，登記後起算，故建議海外旅行保險涵蓋出發到登記前。此為舊校方說明，未核實2027臺灣個人簽證及保險政策。','NU Factsheet2026 p3；校方既有入境說明','Must be enrolled as a full-time student at one of our partner',page=3,period='older_year_reference',locator='PDFp3 Visa/Health Insurance')
for field in ['eligibility','language','deadlines','documents']:
 b('798',sid,[field],'完整3頁factsheet已讀；一般交換與JLCP分列，2026文件且年曆題頭2024。文件欄只有後續申請指南連結，沒有完整上傳文件清單。')
 d('798',field,[sid],'reviewed_previous_cycle_reference' if field!='documents' else 'readable_index_details_not_yet_read','已讀完整factsheet及雙計畫範圍；2026舊版，應續讀一般交換/JLCP個別申請指南。文件清單本PDF未列，不宣稱未公告。')
c.save();print('observations',sum(len(s['observations']) for s in c.schools.values()))
