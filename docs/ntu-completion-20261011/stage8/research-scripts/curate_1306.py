from research_curator import Curator,ROOT
import json
c=Curator();f=c.fact;pid='1306';sid='d5fb82aee97b2949';scope='MSU exchange Factsheet2027–28，由臺大2026/9刊載；Bozeman；非臺大甄選'
f(pid,sid,'eligibility','2027–28 MSU交換要求GPA至少3.0/4.0，另需每學期USD7000／全年14000財力證明。這是接待校條件及資金證明，不是臺大名額或實際支出。',scope,'Minimum 3.0 GPA on a US 4.0 scale',page=2,period='target_year_explicit')
f(pid,sid,'language','2027–28 MSU要項列TOEFL71、IELTS6、Duolingo110或另經核可測試；其他測試須按coordinator規定，不自行換算新TOEFL量尺。',scope,'Duolingo',page=2,period='target_year_explicit')
f(pid,sid,'deadlines','2027–28 MSU秋／學年提名3/10、初申4/1；春／曆年提名9/10、初申10/1。母校先提名，校方再給申請指引與連結；不是臺大11月校內截止。',scope,'Nomination Deadlines',page=2,period='target_year_explicit')
f(pid,sid,'courses','2027–28本科每學期至少12學分、研究生9；建築、平面設計、美術、電影、攝影極有限，多須母校同領域主修及作品集；Nursing不開放交換生。',scope,'Nursing',page=1,period='target_year_explicit')
f(pid,sid,'housing','2027–28交換要項說一般可預留校寮，但協定校交換生不必住校，短租校外難找。「usually able」保留例外，不當保證；一般admissions住房頁的本科保證／30學分規則不逕套交換。',scope,'usually able',page=2,period='target_year_explicit')
f(pid,sid,'calendar','2027秋orientation8/24、開課8/25、期考12/13–16；要項寫semester ends12/17，但Registrar2027秋正文寫12/16，12/17為commencement。保留同年差異，不能任選結束日。',scope+'；同年Registrar結束日差1天','December 17',page=1,period='version_conflict')
f(pid,sid,'calendar','2028春orientation1/10、開課1/11、期考5/1–4；交換要項semester ends5/5，但Registrar写5/4、5/5為commencement。兩官方同年差異須確認。',scope+'；Spring2028同年結束日差1天','May 5',page=1,period='version_conflict')
f(pid,'d3c70bc3af112bd7','calendar','Registrar已列Fall2027及Spring2028，開課8/25／1/11、期考12/13–16／5/1–4；學期末12/16／5/4、畢業式次日。不可把舊2026–27區塊或resident／畢業申請截止當incoming期限。','MSU Registrar Fall2027/Spring2028；與exchange factsheet結束日矛盾','Detailed Spring 2028',period='version_conflict')
f(pid,'fcd91787b6ac97b8','documents','Direct交換先母校提名，再於My Global Connection交財力、英語、申請essay、正式成績、passport、預選課及2推薦信；ISEP此階段僅passport／成績及閱讀指引，兩路徑別混。','MSU IncomingHowtoApply未標學年；Direct／ISEP分流','Two letters of recommendation')
f(pid,'fcd91787b6ac97b8','insurance_visa','非美籍交換通常按校方J-1程序，錄取後提供DS-2019；ISEP文件由ISEP處理。MMR與TB在錄取後註冊前繳；不是全部初申文件或臺灣個人簽證裁定。','MSU未標年incoming錄取後程序；US passport例外保留','MMR immunization records and a TB screening form')
f(pid,'27766577529fcb47','cost','MSU未標年housing頁估校外含utilities每人USD500–1200/月、校寮不退deposit300、early-arrival temporary寮約10/夜且不含餐。各適用身分與時間不同，非2027確定全費用。','MSU一般international admissions住房估計，未標適用年；非exchange專屬保證','non-refundable housing deposit',theme='cost')
roster=json.loads((ROOT/'priority-source-roster.json').read_text())[pid]
note='五份原正文完整讀；27–28exchange要項與general degree住房分開。Registrar同年semester-end比要項少1天；居民／畢業／add-drop非incoming截止。租屋References/CreditHistory不當交換學术資格。Direct3.0與ISEP2.75不同路徑；nom/initial/post-acceptance分階段。'
for source in roster['sources']:
 fields=[k for k,v in roster['fields'].items() if source in v]
 c.body_review(pid,source,fields,note)
for field,sids in roster['fields'].items():
 c.decision(pid,field,sids,'target_year_partial_rules_and_scoped_general_reference',note)
c.snapshot['scope']='All288 NTU partners; stage8 continuing original fixed501 body sets, references materialized in Draft PR9 only; no formal selection-rule promotion.'
c.snapshot['integration_stage']={'stage':'stage8_original_priority_body_completion_in_progress','baseline_observations':700,'candidate_reference_only':True,'formal_selection_rules_promoted':False,'merged_or_deployed':False}
c.save();print('1306 imported; observations',sum(len(s['observations']) for s in c.schools.values()))
