from pathlib import Path
import json,hashlib,shutil,datetime
from pypdf import PdfReader
H=Path(__file__).parent;C=H/'collection';R=Path('/workspace/abroad-ntu-official-20261014');D=R/'sources/ntu/2026-10-14-official';D.mkdir(parents=True,exist_ok=True)
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
a=read(C/'official-inventory.json');profiles={p['ntu_sn']:p for p in read(C/'profiles.json')};metas=[read(p) for p in (C/'sources').glob('*.json') if not p.name.startswith('robots-')]
manifest={}
for m in metas:
 if m.get('access_status')=='content_available':
  p=C/m['local_file'];assert sha(p)==m['sha256'];q=D/p.name;shutil.copyfile(p,q);manifest[m['source_id']]={**m,'local_file':str(q.relative_to(R))}
for p in (C/'sources').glob('robots-*.json'):shutil.copyfile(p,D/p.name)
listmeta=next(m for m in manifest.values() if m['role']=='ntu_selection_inventory');assert listmeta['sha256']=='68e38975b6ef4890ff0010360c7d517b08a5685950e0f3790223f9b6af56b64f'
receipt={'url':listmeta['url'],'http_status':200,'sha256':listmeta['sha256'],'checked_at':listmeta['checked_at'],'source_id':listmeta['source_id'],'academic_year':'116','outgoing_semester':1,'source_academic_year':'2027/2028','rows':[{'portal_id':p['ntu_sn'],'name':p['school_name'],'country':p['country'],'quota':p['selection_quota_text'] or '', 'headcount':p['selection_headcount_text'] or '', 'marked_updated':p['updated_marker']} for p in a['schools']]}
quotas=[]
for p in a['schools']:
 if p['selection_quota_text'] not in (None,'0 名'):
  q=int(p['selection_quota_text'].split()[0]);n=int(p['selection_headcount_text'].split()[0]);d=profiles[p['ntu_sn']];sec=next(s for s in d['sections'] if s['heading']=='名額');assert '可選擇交換一學期或一學年，限於本校第一學期出國交換' in sec['text']
  quotas.append({'portal_id':p['ntu_sn'],'school_name':p['school_name'],'country':p['country'],'academic_year':'116','source_academic_year':'2027/2028','application_round':'116-1','quota_academic_years':q,'maximum_persons':n,'quota_original':p['selection_quota_text'],'maximum_persons_original':p['selection_headcount_text'],'quota_display':f'{q} 學年名額（最多 {n} 人次）','list_source_id':listmeta['source_id'],'detail_source_id':d['source']['source_id'],'detail_url':d['ntu_profile_url'],'exchange_duration_original':sec['text'],'checked_at':listmeta['checked_at'],'detail_checked_at':d['source']['checked_at'],'application_open_confirmed':False})
assert len(quotas)==8 and sum(q['quota_academic_years'] for q in quotas)==13 and sum(q['maximum_persons'] for q in quotas)==26
visa=[];visaids=['1307','206','313','1109','210','97','95','96','94','93','92']
for sn in visaids:
 p=profiles[sn];s=next(s for s in p['sections'] if s['heading']=='簽證資訊');assert 'Student Visa (Subclass 500)' in s['text'] and 'Since May 2026' in s['text']
 visa.append({'portal_id':sn,'school_name':p['school_name'],'country':p['country'],'source_id':p['source']['source_id'],'source_url':p['ntu_profile_url'],'checked_at':p['source']['checked_at'],'original_quote':'we strongly recommend that students intending to study with us apply for the Student Visa (Subclass 500)','text_zh':'臺大新增簽證提醒：建議交換生申請 Student Visa (Subclass 500)，避免以 Working Holiday Visa 安排交換；該頁提及自2026年5月以來拒簽及處理延誤造成取消交換的風險。這是臺大新增提醒，未獨立核實為新法律或一律禁止；個人適用資格與最新規定請核對澳洲內政部。','official_external_url':'https://immi.homeaffairs.gov.au/','legal_rule_independently_verified':False,'selection_rule_confirmed':False})
notes={'998':'維也納移除僅具英語者的額外說明連結，最低語言門檻未變；更新課程、語言課、保險、簽證及住宿參考連結。','1302':'蒙斯理學院與師培院系連結更新；未核實為資格或課程准修條件變更。','1103':'Thomas More商管交換課程連結更新，basis Dutch拼字改為basic Dutch；未改最低語言門檻。','71':'波昂新增360-degree tour參考；不當作交換校區分配或新座標證據。','69':'柏林自由課程名稱改為European Perspectives on Berlin and Germany，原連結未變；不推論准修資格改變。'}
heads={'998':['注意事項','實用資訊','住宿資訊'],'1302':['Faculties and Schools'],'1103':['注意事項'],'71':['Other Highlight'],'69':['Special Courses for Exchange Students']}
refs=[]
for sn,note in notes.items():
 p=profiles[sn];sections=[s for s in p['sections'] if s['heading'] in heads[sn]]
 refs.append({'portal_id':sn,'school_name':p['school_name'],'source_id':p['source']['source_id'],'source_url':p['ntu_profile_url'],'checked_at':p['source']['checked_at'],'note_zh':note,'sections':sections,'qualification_change_confirmed':False,'receiving_page_contents_independently_rechecked':False})
pdf=next(m for m in manifest.values() if m['role']=='ntu_hosted_UBC_2027_28_factsheet');pages=[p.extract_text() for p in PdfReader(R/pdf['local_file']).pages];assert len(pages)==6
ubc={'portal_id':'1','school_name':profiles['1']['school_name'],'source_id':pdf['source_id'],'source_url':pdf['url'],'source_sha256':pdf['sha256'],'checked_at':pdf['checked_at'],'source_academic_year':'2027/2028','document_updated_at':'2026-09-10','pages':6,'replaces_source_url':'https://studyabroad.ntu.edu.tw/wp-content/uploads/2025/12/UBC-Factsheet-2026-2027-updated-Dec-2025.pdf','supersedes_fee_observation_ids':['496d17708504e9730ed0','21f16c7d99bb12e5c9ac'],'new_fee_amount_first_discovery':False,'scope':'UBC incoming exchange 2027/2028，Vancouver／Okanagan按各項分列；非臺大甄選期限、配額或錄取保證','selection_rule_confirmed':False,'facts':[
 {'field':'deadlines','pdf_page':2,'text_zh':'UBC接收端第一輪提名2027/1/15–3/15（Term1、Term2、全年或split-year）；第二輪2027/7/1–8/25（Term2／split-year，Law與Computer Science不適用）。文件截止分別2027/4/1、9/15，由母校透過partner portal上傳；非臺大校內報名期限。'},
 {'field':'calendar','pdf_page':2,'text_zh':'要項標為暫定：Term1授課2027/9/7–12/7、考試12/11–22；Term2授課2028/1/5–4/7、考試4/11–26。舊2026/27 PDF的年份矛盾保留歷史，不改寫舊原件。'},
 {'field':'courses','pdf_page':3,'text_zh':'第一輪選課窗口由舊版July–September改為June–September，涵Term1與Term2；第二輪November–January。實際選課及院系限制仍依錄取校區通知。'},
 {'field':'housing','pdf_page':5,'text_zh':'Vancouver住宿優先項目已移除Full year students；仍不保證住宿，約50–60%交換生可獲安排。取得UBC ID後申請，CAD50不退申請費；Okanagan亦不保證住宿，依各輪與入學期個別截止，split-year的2028/9–12不保證。'},
 {'field':'cost','pdf_page':6,'text_zh':'2027/28要項確認既有未標年網頁費率：单學期iMED CAD295.10＋11.15；全年／split-year前三月CAD204.30＋11.15，MSP CAD75／月；U-Pass CAD191.40／學期（Metro Vancouver適用）。費用可調整。本次是年度／舊PDF衝突釐清，不重複計為首次發現金額。'},
 {'field':'cost','pdf_page':6,'text_zh':'新增取消／退出費用提醒：若未在該學期可退課且不記W的截止日前通知取消／退出，學生仍須支付其帳戶已核算費用；要項未給此截止的個人固定日期。'},
 {'field':'insurance_visa','pdf_page':6,'text_zh':'上述iMED保費是UBC2027/28接收參考，單學期與全年／split-year保障期間分開；不得把原2026/27 PDF338＋10.95、237及U-Pass187.60當新年度價格。個人保障日期、國籍及入境文件仍需確認。'}]}
source={'format_version':1,'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'base_main_sha':json.loads((H/'main-ref.json').read_text())['object']['sha'],'academic_year':'116','source_academic_year':'2027/2028','outgoing_semester':1,'list_receipt':receipt,'source_manifest':manifest,'quota_updates':quotas,'visa_reminders':visa,'reference_updates':refs,'ubc_update':ubc,'counts':{'partners':288,'published_positive':8,'pending':274,'zero':6,'academic_year_slots':13,'maximum_persons':26},'application_open_confirmed':False,'all_current_cycle_fields_verified':False,'baseline_comparison':{'parent_2026_10_13_raw_baseline_received':False,'parent_reported_all288_check':'18 changed detail pages; eligibility/quota/calendar paragraphs unchanged relative to10/13. Formal slots published in list cells.','local_historical_snapshot':'completion-2026-10-11.json','do_not_claim_local_10_13_byte_comparison':True}}
(R/'sources/ntu/2026-10-14-official-update.json').write_text(json.dumps(source,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'sources':len(manifest),'positive_quota_schools':len(quotas),'visa_schools':len(visa),'reference_schools':len(refs),'ubc_facts':len(ubc['facts']),'source_sha256':sha(R/'sources/ntu/2026-10-14-official-update.json')},ensure_ascii=False))
