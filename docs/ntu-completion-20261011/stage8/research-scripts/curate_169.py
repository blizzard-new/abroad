from research_curator import Curator
from finish_school import finish
c=Curator();f=c.fact;p='169';s='4f7a8732b0734225';scope='HKU2026/27 Application頁；舊入學批次，非2027–28';lang='902086b748487bad'
f(p,s,'eligibility','HKU2026/27須母校提名、開始交換前至少完成大学1年與good academic standing；Law須法律主修及CGPA3.33/4.3／B+或2:1，Business需B／CGPA3.0。不同faculty不混成全校GPA門檻。',scope,'Complete at least one year',period='older_year_reference')
f(p,s,'deadlines','2026/27秋初申4/1–4/30/2026、春9/1–9/30/2026；nom後郵件邀請，late不收。Law共通規則9月入學同年4/30、1月入學前一年9/30，但不拿這份舊年表改成2027新日程。',scope,'April 30, 2026',period='older_year_reference')
f(p,s,'documents','HKU2026/27正式英語成績單（可附英譯、不收非正式）、英語證明、passport機讀頁且交換結束後至少6月有效、Law另CV。個人statement無字數上限；studyplan只是審核預選非已選課。',scope,'Curriculum Vitae (CV)',period='older_year_reference')
f(p,lang,'language','目前app連結的July2021英語指引：母語／全英授路徑仍須母校signed/stamped statement或全英degree說明信，非直接免證明。Law明列iBT97／IELTS7各項6.5；一般minimum另連結，本1頁沒有給總分，不憑Law線推全校。','HKU英語Proof PDF明標Updated July2021，2026/27app仍連結；不改標2027','Updated as of July, 2021',page=1,period='older_year_reference')
f(p,lang,'documents','July2021英語Proof表說只收exchange coordinator上傳、不收學生；2026/27app table卻Home institution/Students，2024manual亦允許nom缺件時學生補、resubmission再由母校。保留版本／階段差異，提交權限須確認。','HKU三份公開英文證明上傳規則：2021PDF／2024manual／2026–27app','any submission by students will NOT be accepted.',page=1,period='version_conflict')
f(p,s,'housing','HKU交換初申開始即可用10位refNo申CEDARS，不用等offer；住房不保證，錄取後仍需signedAdmissionNotice給housing，限時接受房間。2026/27申期秋3/20–9/15、春10/1–11/1是舊年時程。',scope,'there is no need to wait',period='older_year_reference',theme='housing')
f(p,'7315c11520a069b3','courses','HKU2026/27建議24–30credits，≥50%在hostfaculty且CommonCore不計此比例；Law非法律課≤12credits、CommonCore最多2門不同AoI。Dentistry/Medicine/ExerciseHealth/finalprojects不開，Architecture/SCDS極有限且需合約涵蓋；確定課目8月才有，預選不保證。','HKU Academic Information列2026/27 courses；非2027開課保證','At least 50%',period='older_year_reference')
f(p,'da046beaf1ebd796','cost','HKU Law頁2026/27非本地Visiting學費224000HKD/年、112000/sem，協定exchange則不收HKUtuition；不能把Visiting價放臺大交換費。住宿按CEDARS別表，utilities依季節，本已讀頁未列2027全費用。','HKU Law交換與Visiting不同身分；2026/27價','HK$224,000',period='older_year_reference')
f(p,s,'insurance_visa','HKU2026/27頁要求收到Notice後申學生visa，校方估至少10週且申請費不退；Law頁則8–10週。臺灣列international/Macao/Taiwan路徑，不能按Mainland permit流程或推個人核准。',scope+'；Law估計時間不同','at least 10 weeks',period='older_year_reference')
c.body_review(p,lang,['language','documents'],'1頁全部讀；明標July2021，native/全英仍需母校信；一般score另連結沒列，Law97/7特例；母校only與app table角色不一致。')
finish(c,p,'六原正文完整讀含15頁2024userManual：2026/27app与Academicdates保留原年；currentStudent／year1選課非初申。GPA／語言Law與Business分別，Visiting tuition不採exchange。新增同app公開linked英語Proof1頁明July2021，不能以2024URL改年份；文內母校上傳only與新版表／2024nom缺件fallback角色差異保留。')
