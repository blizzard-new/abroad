from pathlib import Path
import json,hashlib,datetime,re,sys,shutil
from research_curator import Curator,ROOT
R=Path('/workspace/abroad-ntu-completion-20261011');S=R/'sources/ntu';D=R/'docs/ntu-completion-20261011/stage7';D.mkdir(exist_ok=True);(D/'validation').mkdir(exist_ok=True);p=json.loads((ROOT/'pending-adoption.json').read_text());old=json.loads((S/'completion-2026-10-11.json').read_text());assert hashlib.sha256((S/'completion-2026-10-11.json').read_bytes()).hexdigest()==p['base_source_sha256'];shutil.copyfile(S/'completion-2026-10-11.json',ROOT/'prior-659.json');shutil.copyfile(S/'reviewed-source-bodies-current-manifest.json',ROOT/'prior-511-manifest.json')
c=Curator();norm=lambda t:re.sub(r'\s+',' ',t).strip()
# Minimal field-specific quotes, in addition to the shared source index.
quotes={
 '9b137fa929f90e42':{'eligibility':'2.0/4.0 or higher','language':'CEFR','deadlines':'March 15, 2027','documents':'Certificate of Health','insurance_visa':'University Insurances','courses':'7 classes per week','housing':'15,000 JPY','cost':'AY 2026','calendar':'Early February 2027'},
 '3aa86a73c01971db':{'eligibility':'undergraduate or graduate','language':'71 or higher','courses':'24 KGU credits','calendar':'January 19'},
 '85f807c0fa8de705':{'eligibility':'undergraduate degree program','language':'4.0','deadlines':'partner universities','documents':'directly to the student','courses':'approval from the lecturers','cost':'JPY 80,000/month'},
 '076b65302e65bdb5':{'eligibility':'partner institutions','language':'from the spring semester 2026','courses':'cannot take classes'},
 '954a52dba55d2dbe':{'language':'placement test','courses':'90 minutes'},
 '7788cb1937f2c926':{'housing':'Accredited auditors and Auditors','cost':'JPY66,000-'},
 'ea3ecbf59cefa45e':{'deadlines':'November 15','documents':'up to 14 documents','housing':'cannot at this time guarantee'},
 'b45d114d1ae38fff':{'cost':'Program Fees','housing':'260,000 - 650,000 JPY'},
 'e1a09126f819f9e4':{'cost':'97,000 JPY - 137,000 JPY'},
 '4bb5df94ad16f3a3':{'housing':'All exchange students are required to live in our dormitories.'},
 '40e01dc4c9056056':{'documents':'2027 Spring Application Checklist'},
}
p['public_source_reviews']['9b137fa929f90e42']['original_quote']='AY2027'
for o in p['new_observations']:
 d=c.read_source(o['source_id']);quote=quotes.get(o['source_id'],{}).get(o['field'],p['public_source_reviews'][o['quote_source_id']]['original_quote']);assert norm(quote) in norm(d['text']),(o['source_id'],quote)
 o.update(original_quote=quote,raw_body_sha256=d['sha256'],publication_role='draft_platform_public_reference_not_formal_selection_rule')
 if o.get('pdf_page'):
  if d.get('pages'):page=next(x['text'] for x in d['pages'] if x['page']==o['pdf_page'])
  else:
   from pypdf import PdfReader
   page=PdfReader(d['_folder']/(o['source_id']+'.pdf')).pages[o['pdf_page']-1].extract_text()
  assert norm(quote) in norm(page),(o['observation_id'],'quote exact page')
 if o['source_id']=='9b137fa929f90e42':
  sections={'eligibility':'p1 Qualifications; p2 Eligibility; p4 GPA conversion','language':'p2 Language Requirements','deadlines':'p1 APPLICATION Fall Entry2027; p2 COE same deadline','documents':'p1 Application Documents and Application Process','insurance_visa':'p2 Visa/COE; p3 Insurance and Health Care Services','courses':'p1 intensive restrictions; p2 Course Information; p3 GLIP','housing':'p3 Accommodation','cost':'p4 Estimated Living Costs; AY2026 insurance line preserved','calendar':'p1 Academic Calendar original winter start year2027 visually confirmed'}
  o['evidence_locator']=sections[o['field']]
  if o['field'] in ['insurance_visa','courses','eligibility','deadlines']:o['scope']+='；各子項頁碼：'+sections[o['field']]
for school in p['school_state_with_candidates']:
 by={o['observation_id']:o for o in school['observations']}
 for o in p['new_observations']:
  if o['portal_id']==school['portal_id']:by[o['observation_id']]={k:v for k,v in o.items() if k not in ['portal_id','school_name']}
 school['observations']=list(by.values())
old['schools']=p['school_state_with_candidates'];old['public_source_reviews']=p['public_source_reviews'];old['reviewed_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();old['scope']='All 288 NTU partners; 700 scoped reviewed public-reference observations materialized in Draft PR9 only; formal host cycle rules not approved and not merged/deployed.';old['integration_stage']={'stage':'stage7_41_references_materialized','previous_source_sha256':p['base_source_sha256'],'new_observations':41,'candidate_reference_only':True,'formal_selection_rules_promoted':False,'merged_or_deployed':False}
assert sum(len(s['observations']) for s in old['schools'])==700 and len(p['new_observations'])==41
(S/'completion-2026-10-11.json').write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n');(D/'第七批41則已匯入增量.json').write_text(json.dumps(p['new_observations'],ensure_ascii=False,indent=2)+'\n')
# Independent manual dispositions join exactly the original and fully read followup versions.
ledger=json.loads((ROOT/'full-body-field-review-ledger.json').read_text());roster=json.loads((ROOT/'priority-source-roster.json').read_text());manual=json.loads((S/'semantic-review-current-2026-10-11.json').read_text());dm={(r['portal_id'],r['field']):r for r in manual};out=[]
notes={
 '816':{'eligibility':('older_reference_and_undated_partner_rule','本科／研與母校提名已核，26/27有2頁要項，未在此找到GPA硬線，不是全校未公告。'),'language':('older_program_track_reference','26/27JLT平片假名與英71expected但不用英文cert；N1只是一般本科選課門檻，不套全體。'),'deadlines':('old_entry_cycle_and_undated_tentative_schedule','2027春確定2026/11/15，general暫定3/15提名／4/15申請不同；未當2027秋新入學確定日。'),'documents':('published_old_cycle_partial_list_and_robots_disallowed_followup','2027春最多14文件與格式公開；Jotform robots200實際不允許此路徑，未繞過；母校專屬nomination/submissionlinks另階段，不稱文件全未公告。'),'cost':('undated_period_specific_cost_and_older_reference','programme一學期40000/全年55000，宿表為整段方案非每月；NHI月估與年折扣不同，不亂加或改成2027確定預算。')},
 '817':{'eligibility':('wrong_scope_candidates_rejected_incoming_rule_read','原SXIP2023活動、LMS不作incoming資格；JOY全日制本科在籍及提名，未找到本頁GPA，不等全站未公告。'),'language':('incoming_rule_read_outgoing_candidates_rejected','原studyabroad為YNU赴外、日JOY索引非詳細門檻；英JOY可英或日，保留兩種TOEFL量尺与母校letter。'),'deadlines':('details_sent_to_home_university_and_after_nomination','官方明說提名details/deadlines給協定校，學生link提名後送；不是公開網站搜尋未找到就說未公告。'),'documents':('application_link_after_nomination','公开JOY頁初申清單未列，個人applicationlink提名後給／JASSOform在packet，不假装取得個人packet。'),'cost':('undated_housing_cost_and_scholarship_scope','學生與researcher房型／月費／一次不退deposit分開；JOY資格和寮auditor排除需核specificstatus，JASSO不保证。')},
 '27':{'eligibility':('target_year_partial_requirement_and_old_scholarship_scope','AY2027新版包括Fall2027；本科研非doctorate、母校一學期與GPA2/4，JASSO2.3/3以前一學年算，不轉交換硬線。'),'language':('target_year_partial_rule_and_proof_alternatives','AY2027EnglishB2或JP N2，母校信替代與母語／degree-in-English仍须信；不是通免证明。'),'deadlines':('target_fall_date_published_old_spring_form_separate','AY2027表明示Fall2027 Jan開March15截止；2027春Checklist2026Nov15不套Fallform；COE同deadline。'),'documents':('target_year_initial_list_public_private_credentials_separate','AY2027七項公开，學生兩表和母校提交分工、password母校轉交；Spring27具體format屬早一批、不保證Fall當期表式。'),'cost':('target_year_partial_estimate_with_explicit_old_insurance_rate','AY2027床具15000比2025/26床具12100不同原年；monthly/quarter/period分開。新版中UniversityInsurance特別標AY2026，不改成2027費率。')},
 '1004':{'eligibility':('undated_program_specific_reference','特別聽講本科研與GJP不同，研生若只選本科應申本科；录取後不能任換programme。'),'language':('effective_from_2026_program_rule_and_false_positive_rejected','特別聽講N2/N1與2026春起不收母校日語信；GJPplacement不是全體初申JLPT，localeventjob誤配拒用。'),'cost':('undated_explicit_period_cost_reference','官方交換免tuition，one-time/semester/monthly拆开；housing page未注明租周期由EstimatedCosts月表核；不替当期全費用确认。')},
 '1198':{'eligibility':('wrong_university_candidates_rejected_correct_host_body_unavailable','五原候選均AIU，NTU1198是AkitaUniversity AUAJ/AUGP。正確官方program入口已定位，但robots302導向soft404 HTML不是可驗robots；未直接忽略或绕過。'),'deadlines':('correct_host_public_announcement_identified_body_unavailable','官方搜尋索引已見AkitaUniversity2027April征集9/8/2026刊，不能稱完全未公告；原AIU housing不是Akita incomingdeadline，正式全文／附件未取。'),'documents':('wrong_university_and_followup_body_unavailable','原AIU住房錄取後portal不是Akita初申文件，reject；正確Akita正式April2027文件入口已辨識但正文讀取限制未解。'),'cost':('wrong_university_housing_prices_rejected','拒用AIU130000semester／sharedliving費率等整组，不能补進秋田大学；NTU正确profile生活70000–80000/月是原参考，保留年份未确认。')}
}
for pid,fields in notes.items():
 for field,(outcome,note) in fields.items():
  ls=[l for l in ledger if l['portal_id']==pid and l['field']==field and l['full_extracted_text_read_for_field']];unique={(l['source_id'],l['body_sha256']):l for l in ls}
  d={'portal_id':pid,'school_name':c.schools[pid]['school_name'],'field':field,'outcome':outcome,'note_zh':note,'reviewed_at':old['reviewed_at'],'sources':[{'source_id':l['source_id'],'url':l['source_url'],'checked_at':l['source_checked_at'],'sha256':l['body_sha256']} for l in unique.values()],'review_method':'逐版本完整本文人工語意判讀；原候選與新公开後续文件分开，不等當期全部子項核實','all_original_cached_body_texts_read':True,'full_current_cycle_requirement_verified':False}
  if (pid,field) in dm:d['prior_review_outcome']=dm[pid,field]['outcome'];d['prior_review_note_zh']=dm[pid,field]['note_zh']
  dm[pid,field]=d;out.append(d)
assert len(out)==22
(S/'semantic-review-current-2026-10-11.json').write_text(json.dumps(list(dm.values()),ensure_ascii=False,indent=2)+'\n');(D/'第七批22項語意待解.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
for src,dst in [('full-body-field-review-ledger.json','full-body-review-current-2026-10-11.json'),('priority-review-progress.json','priority-review-progress-current-2026-10-11.json')]:shutil.copyfile(ROOT/src,S/dst)
print(json.dumps({'imported':41,'total':700,'source_reviews':len(old['public_source_reviews']),'manual_rows':len(dm),'ledger':len(ledger)}))
