from research_curator import Curator,ROOT
from pathlib import Path
import json,hashlib,datetime
c=Curator();base_ids={o['observation_id'] for s in c.schools.values() for o in s['observations']};f=c.fact;b=c.body_review
# Existing undated web pages and the newly read 2026-27 two-page fact sheet are kept separate.
f('816','0076863b56833d96','eligibility','CJP交換須在KGU協定校保持學籍並經母校選派；KGU保留最終錄取決定。美國非協定校USAC路徑不是臺大一般交換。','KGU Contemporary Japan Program共通公開說明，年度未列','Participating students will be selected by the home institution.')
f('816','05bc306de80477d4','deadlines','CJP共通暫定日月：秋提名3/15、初申3/1–4/15；春提名10/15、初申10/1–11/15。學生準備後由母校上傳全部文件，不套2027秋確定日期。','KGU CJP Application Period (Tentative)，未標年度','Application Period')
f('816','ea3ecbf59cefa45e','deadlines','2027春CJP專頁明列11/15截止，入口頁寫2026/11/15；這是2027春入學批次，不是116-1的2027秋／2028春。','KGU 2027 Spring Intake；2026/11/15申請截止','CJP Application Procedure (2027 Spring Intake)',period='older_year_reference')
f('816','ea3ecbf59cefa45e','documents','2027春CJP最多14份依情境文件，英／日文或附英日翻譯，除了Health不得手寫；通常PDF，ID照可JPG，文件05依教授專屬流程已上傳者不重交。母校持提交連結；14份具體清單所在公開Jotform因robots讀取不可用未取得，不能稱文件未公告。','KGU 2027 Spring Intake文件及母校提交流程，舊入學批次','CJP Application Procedure (2027 Spring Intake)',period='older_year_reference')
f('816','ea3ecbf59cefa45e','housing','2027春CJP所有被提名學生可申請安排住宿，但不保證分配；Residence Center預計11月初另送申請方式，未抽到需自行校外。','KGU 2027 Spring Intake住宿，舊入學批次','CJP Application Procedure (2027 Spring Intake)',period='older_year_reference')
sid='3aa86a73c01971db';quote='Last updated on January 2026'
f('816',sid,'eligibility','2026–27 CJP要項准本科或研究生經協定校提名，交換一學期或全年；沒有在這份2頁要項列GPA最低值，未找到不等整校未公告。','KGU CJP 2026–27；January2026更新',quote,page=1,period='older_year_reference')
f('816',sid,'language','2026–27 CJP Japanese Language Track到日前須流暢讀寫理解發音平假名／片假名；Modern Japan Track不要求日語。非英語母語者預期英語相當iBT71以上，但明說不用交英文檢定證明。','KGU CJP 2026–27 JLT/MJT各別；不將expected與certification混為硬證照',quote,page=1,period='older_year_reference')
f('816',sid,'courses','2026–27 CJP日語Track每週5堂必修；Modern Japan Track每週1堂Modern Japan Seminar。一般日語本科課須N1或placement高分，每週超過10小時且至少7節，上限每學期24KGU學分；不是所有Track初申都要N1。','KGU CJP 2026–27課程負荷與一般本科選課',quote,page=2,period='older_year_reference')
f('816',sid,'calendar','2026–27 CJP要項秋非IBA課期／考試至1月中、退寮1/19；IBA至2/7且可延住宿。春非IBA至7月中下、退寮7/21；IBA至7月底。這與舊2025秋網頁1/31退寮不同年度，不任選改成2027–28。','KGU CJP 2026–27 tentative calendar，非2027–28；Spring將在November定案',quote,page=1,period='older_year_reference')
f('816','b45d114d1ae38fff','cost','KGU共通費頁交換免學費；Program Fees含mandatory Insurance/Support Pack，一學期JPY40000、全年55000，開課前繳。未標適用學年且可變，不認定2027–28費率。','KGU交換費頁未標年度；一學期／全年分別','Program Fees')
f('816','b45d114d1ae38fff','housing','KGU費頁整段宿費：秋一學期JPY260000–650000，春240000–600000；秋起全年530000–1300000、春起500000–1250000。雖逐月帳單，表中是方案期間總額，不能直接當月租。homestay秋500000、春400000，依一學期／全年繳費流程；住房仍不保證。','KGU undated accommodation cost；表格方案期間／monthly billing分開','Program Fees')
f('816','b45d114d1ae38fff','cost','KGU未標年月估計不含住宿／往返機票：寮生JPY70000、homestay55000；health3000、food40000／15000、books7000、misc20000。通勤可能另付，獎學金不保證，USAC/ACUCA/UMAP路徑不能申該校推薦獎學金。','KGU每月Living Expenses (Estimate)；年度未列','Program Fees')
f('816','e5db46b46b52136a','insurance_visa','KGU學生指南列日本NHI加入程序與到市區役所所需passport/residencecard/studentID，折扣保費通常約JPY10000/年但依自治體／前一年收入而異；70%給付僅保障項目。這是校方指引參考，與Program Fees Insurance Pack分开，不推固定2027保费或個人簽證結論。','KGU undated National Health Insurance institution guidance','National Health Insurance')
f('816','ac94c584ea09245c','insurance_visa','KGU指引要求收到COE後向所在地日本使領館申請Student Visa，其他所需文件按使領館；COE隨附coverletter有表格說明。這是錄取後入境程序，不是初申全部文件或臺灣個人签证裁定。','KGU incoming Visa and Entry共通；COE後階段','Applying for a Student Visa')
# YNU: programme-specific incoming JOY instead of outgoing or housing keyword matches.
sid='85f807c0fa8de705';quote='JOY Program (Exchange Program)'
f('817',sid,'eligibility','YNU JOY要求協定校全日制本科在籍且母校正式提名；錄取按文件品質及兩校交換平衡。研／博不從此本科JOY頁推可申，亦沒有在本頁找到GPA硬線。','YNU JOY incoming本科共通，未標適用學年',quote)
f('817',sid,'language','YNU JOY可英語或日語：iBT80（2026/1前量尺）／4.0（2026/1後）或IELTS6；日語JLPTN2以上。其他英文證書可加母校信，證明相當iBT4/IELTS6/CEFRB2；不是兩種語言都必備。','YNU JOY公開語言要求；2026量尺分開，年度未列',quote)
f('817',sid,'deadlines','YNU JOY正式頁明說提名細節與截止送合作校，接到母校提名後直接寄學生申請連結；未在此公開正文列日月，屬指定母校／提名後取得細節，不能推整校未公告。','YNU JOY Nomination/Application階段，年度未列',quote)
f('817',sid,'documents','YNU JOY公開正文未逐份列初申文件，申請連結在提名後直接送學生；JASSO申請表在JOY application packet。這是具體階段限制，未取得登入後個人packet、不稱沒有文件。','YNU JOY公開流程；個人申請連結／packet提名後取得',quote)
f('817',sid,'courses','JOY有特別英文授課的人文社會工程科目；要選其他學部課，須具足語言能力並获授課教師同意，非所有日文專業課均开放。已列2026/25課表不是2027–28開課保證。','YNU JOY incoming courses共通，年度未列；historical timetables各自年份',quote)
f('817',sid,'cost','JOY可競爭JASSO每月JPY80000，名額有限且不能同時領其他海外獎學金合計超80000/月（旅費援助除外）；不當保证收入、交換硬GPA門檻或臺大名額。','YNU JOY JASSO公開說明，未標年度',quote)
f('817','f27f5fb98e5c4c46','housing','YNU住宿總覽Minesawa4/10月以lottery入住，4月入住通常1月申、10月入住通常7月申；其他寮按空房。這些是住房流程，非JOY初申截止或保證住房。YISH是城市對full-time本科／研篩選，不能當所有交換生可得。','YNU general international student housing；未標年度','Accommodations for International Students')
f('817','7788cb1937f2c926','cost','Tokiwadai學生Shared房月租JPY38000＋管理7000＋水電網15510；Private房51000＋7000＋15510。另入住66000不退（含行政／退房清潔），續約16500；不要套研究員82000以上房型或只列38000全包。','YNU Tokiwadai International Residence學生房型與月單位；未標適用學年','Tokiwadai International Residence')
f('817','7788cb1937f2c926','housing','Tokiwadai官網學生房住進條件排除Accredited auditors/Auditors；是否涵蓋JOY個人接收身分須確認，303總房量是整棟統計，非臺大分配／保證名額。','YNU Tokiwadai學生housing eligibility；JOY具体身分未核定','Tokiwadai International Residence')
# NUFS study abroad programme vs Global Japan Program, and valid recurring cost units.
sid='076b65302e65bdb5';quote='Must be enrolled in and recommended by one of our partner institutions.'
f('1004',sid,'eligibility','NUFS特別聽講須協定校在籍推薦；研究所課限母校研究生。若母校研生只想選本科課，应申本科特別聽講；不可以研究所名義只選本科，也不能錄取後任改programme。','NUFS Study Abroad Program at Undergraduate/Graduate Schools；共通未標年度',quote)
f('1004',sid,'language','NUFS特別聽講本科須JLPTN2，研課N1或認可的其他官方日語測試；校方明說母校日語能力信自2026春不再接受（先前到2025秋可）。這個限制不套Global Japan Program。','NUFS特別聽講；母校證明信2026春起不接受；各programme分開',quote)
f('1004',sid,'courses','NUFS特別聽講不能選Global Japan Program課。研生以研課為主可加1–3本科課；至少7堂/學期（週10.5小時、每堂90分鐘），10–12是推薦非最低。容量與課程可變。','NUFS Study Abroad Program課程規則；未標年度',quote)
f('1004','954a52dba55d2dbe','language','NUFS GJP日語core按onlineplacement，不按修過教材；初學者自行先精熟平／片假名並受測。JLPTN3/N2準備課是開課層級，不是所有GJP初申JLPT門檻。','NUFS GJP JLC語言／placement共通；未標入學年度','GLOBAL JAPAN PROGRAM')
f('1004','954a52dba55d2dbe','courses','NUFS GJP JLC/GJSC合計至少每週7個90分鐘classroomhour，非7個60分鐘時數；不推薦超11。想選日語須core；少於4人可停開，GJSC容量抽籤不保证選上。2026課目表不當2027–28。','NUFS GJP共通負荷；2026課目表另保留原年','GLOBAL JAPAN PROGRAM')
f('1004','4bb5df94ad16f3a3','housing','NUFS所有exchange必須住校寮，申請時選偏好但國際處決定且不接受後續變更；容量可能分到第三志願。3個寮房型有不同廚房設計，不能把房間數當臺大名額。','NUFS incoming exchange housing共通；年度未列','Housing Information -Dormitories-')
f('1004','e1a09126f819f9e4','cost','NUFS官方估計交換免學費；入住10000不退、選租床具6600一次、課本15000–30000/學期。月租含水電35000、NHI2000、食物30000–50000、其他30000–50000；月合计97000–137000。一次費、學期費与每月費分開，未標適用學年。','NUFS Estimated Costs未標年度；one-time/semester/monthly原單位','Estimated Costs')
# Every original body for these four schools was fully read, even when rejected for identity/field.
roster=json.loads((ROOT/'priority-source-roster.json').read_text())
notes={'816':'完整讀原11正文，2025–26PDF與26–27新PDF各原年；general tentative dates与2027Spring專頁分開；住宅/insurance/visa不充學術門檻。','817':'完整讀原8正文；2023SXIP活動不是incoming资格、outgoing語學與LMS非JOY门槛；JOY母校／提名後資料與住房門檻分開。','27':'完整讀原9正文及2027新4頁／checklist；ShortStay suspended与ISEPTUFS不同，JASSO和初申GPA、年份及費用單位分開。','1004':'完整讀原7正文；特別聽講與GJP、localjobs與語言要求分開；2026catalogue不改標2027。','1198':'完整讀原5正文；全部web.aiu.ac.jp屬Akita International University，與NTU指定Akita University AUAJ/AUGP不同學校，拒用全部此校候選。'}
for pid in notes:
 for sid in roster[pid]['sources']:
  fields=[field for field,sids in roster[pid]['fields'].items() if sid in sids];b(pid,sid,fields,notes[pid])
for sid,fields in [('3aa86a73c01971db',['eligibility','language','deadlines','documents','calendar','courses','housing','cost']),('06f5728f2d0786b7',['deadlines','documents']),('c726dfdb6622f4a3',['deadlines','documents']),('ea3ecbf59cefa45e',['eligibility','language','deadlines','documents','housing']),('40e01dc4c9056056',['eligibility','language','documents','deadlines']),('9b137fa929f90e42',['eligibility','language','documents','deadlines','calendar','courses','housing','cost','insurance_visa'])]:b('27' if sid in ['40e01dc4c9056056','9b137fa929f90e42'] else '816',sid,fields,'完整抽取文字與全部PDF頁已讀；原標年月／申請身分／文件階段保留，課程／費率可變與文內不一致不自行修補。')
delta=[{'portal_id':s['portal_id'],'school_name':s['school_name'],**o} for s in c.schools.values() for o in s['observations'] if o['observation_id'] not in base_ids]
# Deliberately leave runtime snapshot frozen at the currently running 659 suite.
payload={'base_source_sha256':hashlib.sha256((Path('/workspace/abroad-ntu-completion-20261011')/'sources/ntu/completion-2026-10-11.json').read_bytes()).hexdigest(),'new_observations':delta,'public_source_reviews':c.sources,'school_state_with_candidates':list(c.schools.values()),'runtime_saved':False}
(ROOT/'batch01-pending-adoption.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n');print('staged facts',len(delta))
