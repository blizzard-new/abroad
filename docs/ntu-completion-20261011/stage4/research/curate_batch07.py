from research_curator import Curator
from pathlib import Path
import json
c=Curator();f=c.fact;d=c.decision;b=c.body_review;q=json.loads((Path(__file__).parent/'priority-source-roster.json').read_text())
def complete(pid,note,outcome='reviewed_reference_added_partial_scope'):
 for field,sids in q[pid]['fields'].items():
  for sid in sids:b(pid,sid,[field],note,visual_pages=[1] if sid=='6a1c2744e58a0950' else None,visual_files=['hyogo-language-annex.png'] if sid=='6a1c2744e58a0950' else None)
  d(pid,field,sids,outcome,note)
sid='36798daf85b42f97';quote='Mobility application procedure';scope='UNAM2025 factsheet；本科、學院／校區細則另依call'
f('903',sid,'eligibility','UNAM2025本科交换须母校國際處先经SGMEE提名；通用资格与各学院Specific requirements另以當次call規定，factsheet未列完整GPA／年級門檻，不能推斷無限制。',scope,quote,page=3,period='older_year_reference',locator='p3 Mobility Application Procedure / corresponding call')
f('903',sid,'language','UNAM2025非西語母語或授課語的學生须CEFR B2，僅DELE/SIELE；SIELE接受GLOBAL四測或S5的書寫／口說組合。英語或其他語課依各academic entity要求，不能用B2西語一概套所有英語課。',scope,quote,page=3,period='older_year_reference',locator='p3 Official Language / SIELE modalities')
f('903',sid,'documents','UNAM2025申請至少母校institutional application letter與適用者DELE/SIELE B2證明，其餘完整上傳清單须當次call與SGMEE，不能把兩項說成全部必繳。',scope,quote,page=3,period='older_year_reference',locator='p3 uploaded documentation including...')
f('903',sid,'cost','UNAM2025月估USD住宿200–500、食350–450、交通40–60、娛樂100–200，材料依學位；arrival field-practice accident insurance另約MXN220。USD250註冊／275每科每學期屬無協議Visiting Student，不套臺大協議交換。',scope,quote,page=4,period='older_year_reference',theme='cost',locator='p4 monthlyUSD vs p3 nonagreement visiting fees')
complete('903','完整4頁2025factsheet已讀；資格細項明指call，不把導覽／visit收费作全部交換門檻。')
sid='2279ca4e09ab46b1';quote='Housing & Meals'
f('14',sid,'housing','UH Manoa交換／訪問生須先錄取及取得UH ID才能申請宿舍；秋5/1、春12/1是宿舍priority date，非交換申請截止。宿舍無保證，提早抵達需自行短住，入住須health clearance。','UH Manoa MIX incoming Housing & Meals；undated流程',quote,theme='housing',locator='On-Campus Housing / application process / priority deadlines')
f('14',sid,'cost','UH Manoa Housing & Meals所列Honolulu平均租金USD1,662/月明標截至2024/6；不是2027宿舍價格或總生活費。住校餐計畫必買、校外可選；未給現行房型費率，需續讀官方rates連結。','UH Manoa MIX；2024/6城市外租估計與unmarked meal-plan rule',quote,period='older_year_reference',theme='cost',locator='Off-Campus Housing June2024 rent; Residential dining')
complete('14','完整6個候選正文已讀：housing applicant類别不是交換資格，5/1與12/1是住宿priority；2026Summer年曆deadline含畢業或Post-Baccalaureate unclassified而非交換入學。租金是2024/6舊估，另需MIX入學與rates。','reviewed_source_scope_split')
sid='cef9e451f552d278';quote='Fall, 2025';scope='University of Hyogo Fall2025 inter-university exchange；不同学院/校區'
f('978',sid,'documents','兵庫2025秋提名後才寄學生與母校online link及COE／財力／申請理由指定表；十項为online、英文成績、日／英推薦、護照、COE、財力表、本人或支援人英文存款、照片、申請理由、研究生研究計畫。COE用xlsx、照jpg/png、指定其他表PDF；各院可加文件。',scope,quote,page=3,period='older_year_reference',locator='p3 Application materials / file formats / conditional research plan')
f('978',sid,'deadlines','兵庫2025秋版明列春季提名9/1申請9/30、秋季提名3/1申請3/31；現行官網只說前春7–8月、秋1–2月向協議校送當次deadline，不接受學生或第三方直接索取。把舊精確日與新取得方式分開，未確認2027日期。',scope,quote,page=2,period='older_year_reference',locator='p2 Nomination vs p3 Application dates; current landing restriction')
f('978',sid,'cost','兵庫2025協議免接待校學費，住宿至少JPY30,000/月、食及其他至少50,000/月，另機票；是minimum estimates可能更高，不把80000總數當保證上限或2027費率。',scope,quote,page=4,period='older_year_reference',theme='cost',locator='p4 necessary funds minimum estimated expenditures')
sid='6a1c2744e58a0950';quote='Language Proficiency Level';scope='臺大刊載Hyogo学院表；版面原日期25-May-21、2025資料組，不改2027'
f('978',sid,'language','兵庫学院表须逐院看：本科經濟／工商、社會資訊JLPTN2；本科GBC英语iBT42/IELTS4/Cambridge140/TOEICL&R+S&W1150且願学日語文化；人類環境、護理、区域資源／灾害研究所等N1；理研日語優先可英文替代。GlobalHouse另B1是宿舍條件，不是所有学院唯一学业門檻。',scope,quote,page=1,period='older_year_reference',locator='p1 complete rendered table, row2 English GBC vs dorm column')
f('978',sid,'eligibility','兵庫学院表護理本科与研须GPA3.0/4及800字以上日語申請理由／讀書計畫，本科大一–三无practical training；工本科偏好大三以上；社科研究所經濟／工商／会计仅研究生第一年优良成绩，Business另至少2年工作经历；不可用护理GPA套全部学院。',scope,quote,page=1,period='older_year_reference',locator='p1 visual rows4/7/11 criteria column alignment')
f('978',sid,'courses','兵庫社會資訊本科seminar不開給交換生；人類環境本科／研不收目標日語／文化者且無國際生日語课；本科護理無practical training。提名最多兩院且须關聯母校专业，學生不能因GlobalHouse英語要求推斷各系英语授课。',scope,quote,page=1,period='older_year_reference',theme='academics',locator='p1 rows3/6/7 vs Fall2025factsheet p2 nomination')
complete('978','完整6个原cached正文及学院表整頁圖已讀，護理GPA/essay欄跨本研、globalhouseB1房務條件與GBC语言分开；現官網當次InformationSheet須母校渠道取得，2025舊PDF仍可引用但不改年。')
sid='977bd1a03eac6e4e';quote='Kindai University';scope='Kindai官方連結公開Google11頁slides；統計2026/5，exchange規則未標學年、cost表2025/5'
f('1187',sid,'eligibility','近畿slides交換須外国籍、交換結束前維持母校學位；期間畢業但已獲母校研究所錄取者可提供錄取信例外。UG/GR均可但只選本科課；成績轉換表100分>78，不符須Letter of Academic Achievement；不是100分≥78且不是無例外硬拒。',scope,quote,locator='HTML slide4 eligibility / slide5 academic grades')
f('1187',sid,'language','近畿slides ProgramA新增DET100，並列iBT3.5(61/120)、IELTS6/B2；無英語測驗可Letter of Language Competence。ProgramB JLPTN2/N1；保持ProgramA/B及免測文件範圍，不套2027確定。',scope,quote,locator='HTML slide5 language proficiency')
f('1187',sid,'deadlines','近畿slides明列第一學期提名9月底、學生10月底；第二學期提名2月底、學生3月底。資訊另春約8月／秋約1月送母校、錄取結果春約12月／秋約5月；年未標，不自動補2027日期。',scope,quote,locator='HTML slide4 nomination/application vs slide8 FAQ')
f('1187',sid,'housing','近畿slidesFAQ保證100%校外指定住宿安排且学生须住校方指定住房；住房細節只提供獲录取者。不是校内宿舍也不是自由选择所有外租；指定住房估500,000JPY/semester，信用卡付款。',scope,quote,theme='housing',locator='HTML slide6 housing vs slide8 placement FAQ')
f('1187',sid,'cost','近畿同slides房價正文约JPY500,000/semester，生活表住房460,000、書20,000、食140,000、保險30,000合650,000/semester並附2025/5汇率；同页住房兩數不一致，列版本矛盾不暗自選一重算2027總额。交換无校方奖學金且不支持奖學金申请；Summer2026短期330,000屬另一program，不能當semester交換學費。',scope,quote,period='version_conflict',theme='cost',locator='HTML slide6 conflicting housing460000/500000; slide8 scholarships; slide9 distinct2026shortterm')
f('1187',sid,'courses','近畿slides每学期至少7課，A用ListA英语/B用ListB日语，可跨科系；研究生僅本科課。1近畿credit約2ECTS但实际转認仍由母校決定。','Kindai exchange undated slide5/8；not summer program',quote,theme='academics',locator='HTML slides5/8 course restrictions/credit conversion')
b('1187',sid,['eligibility','language','deadlines','documents','cost','housing','courses'],'已完整讀公开HTML11頁slides，取得追加費率与住宿安排，無登入／繞封鎖；documents仍需原flow与提名后packet，混年與房價矛盾保留。')
d('1187','cost',['977bd1a03eac6e4e','2a56237663aa6548'],'reviewed_version_conflict','公開HTML已讀，房價500000與生活表460000同來源不一致；未確認2027。')
sid='ec3f3a8503846fd3';quote='NATIONAL HEALTH INSURANCE SERVICE (NHIS)'
f('1305',sid,'insurance_visa','HUFS保險專頁稱RC申請後自動登記NHIS，處理1–2月空窗须自備travel/health；不能依factsheet的Otherwise推論買私人保险即自動免NHIS。頁內France/Japan例外有少於6月與少於4月兩版本、廣泛foreigninsurance又窄France/Japan等敘述不一致，須以NHIS官方當期判定，不宣稱臺灣生免缴。','HUFS travel/NHIS專頁未標學年；規則內部矛盾，待NHIS当期',quote,period='version_conflict',locator='NHIS processing vs exemption overview / 1–4months / exemption guide')
f('1305',sid,'cost','HUFS保險專頁估NHIS每月KRW70,000–80,000但未標費率年；每月約10日收下月預繳單、25日前付。只保留校方未标年估计与缴款流程，不能當2027政府官方費率或判斷是否豁免。','HUFS NHIS專頁undated estimates；not statutory2027rate',quote,theme='cost',locator='Insurance Fee sections')
b('1305',sid,['insurance_visa','cost'],'完整8031字專頁已讀，先保留autoRC/空窗要求及保费估计，豁免條款互相矛盾需NHIS官方续查。')
c.save();print('observations',sum(len(s['observations']) for s in c.schools.values()))
