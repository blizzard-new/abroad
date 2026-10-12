from research_curator import Curator
c=Curator();f=c.fact;d=c.decision;b=c.body_review
b('11','e9a1ee782d00396a',['deadlines','documents'],'完整Summer2026兩頁年曆已讀；nomination/application keyword屬畢業／博士exam／學位／修課，不是incoming exchange申請文件與期限。')
pdf='9b640fa60410ce29';quote='USP FACT SHEET 2026'
f('1115','db37b36ac06c996a','eligibility','USP本科交換須合作校學生且從大二起、母校提名。舊頁還列Free Movers及非協議校可由教授／國際處提名交各院審；與中央總頁Free Movers不可經中央辦申請的說明是流程／院級範圍差別，不套臺大甄選名額。','USP本科交換舊官網一般規則；合作校與非伙伴／院級不同','Exchange Programme for Undergraduate Students',locator='Before you apply and second-year rule')
f('1115',pdf,'language','USP2026文件明列多數課葡語，應具CEFR B1程度但不強制正式語言證書；純研究活動依學生與指導教授共同約定語言，不能把本科授課B1套所有研究。','USP Factsheet2026 p3；course-based vs research mobility',quote,page=3,period='older_year_reference',locator='p3 Language Requirements')
f('1115',pdf,'cost','USP2026稱交換免費，除部分短期summer／extension；一般課亦無註冊或材料費，Short/Summer另例外。沒有住宿與生活數字，不能以「免費」推斷總生活成本為0。','USP2026factsheet p4；exchange vs Short/Summer course fees',quote,page=4,period='older_year_reference',locator='p4 Tuition Fees, registration/material exception')
f('1115',pdf,'documents','USP2026到校註冊須提交醫療／旅行醫療保險及簽證影本，保險涵蓋全期間且出發前買妥；這是arrival enrollment文件，不是完整交換申請上傳清單。新官網本科／研究生申請指南另列連結。','USP2026factsheet p3 application links vs p4/p5 prearrival/enrollment',quote,page=5,period='older_year_reference',locator='p5 Enrollment; p3 Admission links')
f('1115','0040bc3e548bbc81','deadlines','USP研究生申請明示Research-based與Taught Courses的提名／申請程序與截止不同，須各讀對應類別。現有入口未給精確日期，不能以大學部或一般學期日程替代。','USP graduate exchange landing page；未標年度','Research-based Exchange Program',locator='Procedures/deadlines vary by exchange purpose')
for field,sources in {'eligibility':['0040bc3e548bbc81',pdf,'b122da529fb48e5f','db37b36ac06c996a'],'language':[pdf,'db37b36ac06c996a'],'deadlines':['0040bc3e548bbc81',pdf,'b122da529fb48e5f','db37b36ac06c996a'],'documents':[pdf,'b122da529fb48e5f'],'cost':[pdf,'b122da529fb48e5f']}.items():
 for source in sources:b('1115',source,[field],'完整本欄既有可讀候選已讀，5頁2026factsheet、本科／研究生入口与總交換頁分開；部分舊頁折疊條款只有目錄，新官網申請指南與Mundus需續讀，未當來源阻礙。')
 d('1115',field,sources,'reviewed_reference_added_partial_scope','已讀全部原cached候選，保留2026及UG/GR與research/taught範圍；新官網實際申請文件／精確截止仍須後續公網站。')
sid='8fae4cbc2e01df94';quote='Inbound Exchange Programme Factsheet (2025-26)'
f('22',sid,'deadlines','CityUHK2025–26秋提名2025/3/31–5/1、申請4/8–5/15；春提名9/1–10/1、申請9/1–10/15。簽證另建議秋6/1、春11/1前，不能把簽證截止或re-admission延期日期當首次交換申請日。','CityUHK2025–26臺灣factsheet p1 nomination/application；p4–5 visa；原年',quote,page=1,period='older_year_reference',locator='p1 Nomination/Application periods; p4/5 visa deadlines')
f('22',sid,'cost','CityUHK2025–26 Ma On Shan每人每學期双人HK$11,900、單人23,800；外租估25,000–30,000/學期且不含utility/internet，其他生活估25,000/學期。簽證行政費600不退；宿舍抽籤且不保證，價格年度覆核，不套2027。','CityUHK2025–26 p4/6；HKD每人每學期、MOS住區与住房條件',quote,page=6,period='older_year_reference',theme='cost',locator='p6 Estimated Expenses/MOS rates; p4 nonrefundable visa fee')
f('22',sid,'documents','CityUHK2025–26申請上傳正式成績，非英語授課者另TOEFL/IELTS/CET；須先選至少6門預選課才能送出。先修課宜提供當期修課與syllabus；不是保證6門皆能選上或完整2027文件清單。','CityUHK2025–26 p2 Application Checklist/Notes for Exchange Applicants',quote,page=2,period='older_year_reference',locator='p2 supporting documents/preselected courses')
for field in ['deadlines','cost']:
 b('22',sid,[field],'完整6頁臺灣版factsheet已讀；2025–26、nomination/application/visa及re-admission四種日期分开；月／學期／每人房型與抽籤不保證分開。')
 d('22',field,[sid],'reviewed_previous_cycle_reference','本欄原cached全文已讀，均為2025/26舊版；須續讀現行接待校官網，不能任改2027。')
c.save();print('observations',sum(len(s['observations']) for s in c.schools.values()))
