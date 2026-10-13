"""Close the original finite source scope, with per-school evidence and requests.

No network calls. Frozen intakes/checks are inputs, never reconstructed post-hoc.
Incoming references cannot promote home quota, eligibility, documents or dates.
"""
import json
from collections import Counter
from build_tku_milestone3_host_reviews import source, fact
from tku_capture_io import BUNDLE as B

BASE='4f142ea36e69338d2956b4ea5d3d37a9f4116e52'
STAGES=['official','followup','rule','final_document','template','remaining_document']
UNTRIED={290,251,193,186,174,144,139,33,39}
# Specific targeted incoming route failed/soft404/empty/TLS; root may be readable.
# Readable non-incoming alternatives remain separately recorded in every row.
FAILED={341,334,328,310,281,270,267,253,252,9,63,22}
REQUESTS={
341:'可用的官方學期incoming入口、適用學年、提名程序、可接收學制與科系；目前交換標題無可追正文，正常瀏覽器TLS失敗。',
334:'真正incoming目錄／partner factsheet、適用年度与期限；另需Campo Tiro接收校區命名點，不能採La Garza行政點。',
328:'學期交換受入規則與academic campus身分／點；Main Clinic及外院聯絡地址不能作教學校区。',
320:'實體學期交換與MBA/PhD eLearning的適用分界、當期提名與文件；另需有重用授權、拍攝年月及校區身分的校景。',
312:'對境外partner學生的學期incoming factsheet／期限／文件；World Bank或研究介紹不適用。',
311:'對母校提名學生的incoming programme與當期規則；Global Partner Exchange出國清單不能代替。',
310:'目前真正International Office／incoming公開入口及當期partner factsheet；兩個假設入口404不證明全校未公告。',
290:'TKU協議學制／院系／campus与當期名額、具年度期限；公開一般指南未載獨立年，2026 factsheet只能參考，Learning Agreement模板需母校取得。',
306:'適用臺灣學生的非學位學期交换正文與年度、提名／申請資料；漢語及獎學金頁不代替。',
281:'有效incoming exchange入口／当期partner factsheet；outbound Education Abroad及degree admissions不代替。',
270:'可用OIE incoming／partner factsheet URL及學年、提名與學生期限；已查兩個舊route404。',
267:'精確接收機構／院系雙邊計畫與臺灣學生適用年度、提名文件；不能補一般Erasmus規則。',
253:'可用incoming正文與當期適用資訊；新international路徑正文soft404。若需校景，提供有重用授權與拍攝年月候選。',
252:'可讀的臺港澳incoming方案正文／年度／期限；SIE HTTPS與直接官方HTTP入口只回12字。',
251:'臺灣學期incoming當期規則、接收學制／科系與模板；已讀港澳台合作目錄，未見適用正文。',
249:'非學位臺灣學期交换的接收與提名規則；degree、language scholarship及summer公告不可代替。',
246:'獨立incoming exchange programme與年度／協議範圍；外國degree／課程註冊有效期不適用。',
224:'臺灣學生學期incoming規則、期限與指定校區；出國、暑期營及degree訊息不適用。',
214:'雙邊非Erasmus臺灣incoming factsheet与接收校區；歐盟capacity-building及credit-transfer計畫不能直接套用。',
203:'Paris Diderot原協議由Paris Cité承繼的證據、當期incoming學制／院系／campus；Grands Moulins命名map point雖讀得但承繼未核實。',
193:'當期雙邊交換日程實際日期、TKU協議／院系费用與可用承諾模板；公開英語DOCX一次ReadTimeout，未登入協議表或申請系統。',
191:'適用臺灣incoming semester规则／年與期限；留學degree與世新／澳門／Oswego本校出國公告不適用。',
186:'淡江臺灣學生是否走國內交换而非國際方案、當期學制／院系／費率／期限，並確認照片需兩張或三張；两公開申請表正文未載年。',
183:'學期incoming交換與當期partner條件；2027/28 full-time degree Batch2不能當交換年度。',
184:'真正non-degree incoming exchange而非國際degree／研究所介紹、當期期限及文件。',
174:'更新2026／2027港澳台来校交流指南與模板、TKU协议和接收科系／校區；2025明文僅歷史參考。',
126:'境外partner incoming流程／年與期限；國際關係學院是學術單位而非必然交換承辦。',
55:'incoming接待規則与年度、提名及文件；Movilidad Estudiantil本校出國選拔已明確排除。',
39:'確認2027春In preparation與已過2026/9/17截止矛盾、TKU partner適用；由母校取得Packet／Checklist及公開但實際加密SAS表格之可讀官方版本。',
37:'incoming当期指南、資格／期限／文件；library／art museum／research／degree頁不適用。校景另需實際拍攝年月，不使用上傳年。',
144:'公開臺灣學期incoming實際申請／教務規則、學年與模板；已讀教務處交換目錄與國際學生院lhlx，只見degree／獎學金／漢語／summer或空目錄。',
33:'TKU協議UG/Master及接收校區／科系、當期名額与2027課表；兩校區CoE XLSX已讀2027正文預填值但非保證旅行日期。請確認英語替代證明、成績單時間及health模板與2027指南差異。',
139:'TKU校級或院系級協議、適用學制／科系、當期提名／截止／初次申請模板；common links含淡江不等於交換表／名額。',
9:'真正exchange及實體／線上學期適用，官方可用入口；distance degree不可默認實體交換。',
86:'incoming exchange當期partner factsheet／deadline／模板；OISS一般支援及Study Away出國不可代替。',
61:'真正incoming公开规则／年／期限；國際候選返回同一root正文，不是交換頁。',
63:'真正incoming／院系bilateral agreement資料与當期期限；假設exchange網址正文為404。',
44:'incoming當期指南與適用臺灣學生規則；English sitemap僅degree／general course。校景另需自由重用授權、校區與拍攝年月。',
79:'incoming exchange J-1／partner規則与當期提名期限，不能用degree International Office要求。',
56:'incoming programme／partner factsheet；各院contacts不等於交換條件。',
23:'exchange受入規則／年／期限；AUCP出國及International Students degree不適用，最後目錄空體。',
22:'官方實際國際交流受入資料／學年／deadline；兩條route404且browser TLS失敗；cgu.ac.jp不同臺灣CGU。',
}
ASSET_NOTES={
322:'官方contact／Our campuses實讀：Vlissingen Edisonweg與Middelburg Het Groene Woud按學科分布；exchange programme指定校區與數值點仍未驗，不採任意一住所。',
242:'IACT官方聯絡正文有VSQ@PJ City Block2 Unit13A-01地址，沒有校園數值點；地址或generic SST degree費用公告不當交換費率或定位完成。',
175:'UM2頁官方map已實際視讀，封面Produced August2026。現有Hengqin主校區與未完工Cooperation Zone新campus不同；map/go跳轉僅JS shell，未提供可採的單一數值point。',
207:'UMA2頁官方map實際視讀，正文未核實獨立年，不能由2025檔名定年；Teatinos／El Ejido／city centre各faculty不同，沒有TKU指定校區，圖上位置不代數值point。',
203:'官方Campus directory多校区；官方連Google map命名Grands Moulins marker48.8292405,2.3817211；@48.8294977,2.3795055只是viewport。舊Diderot協議／校區承繼未驗，marker只存候選。',
307:'長安大學官方校园地图directory實讀，未得單一數值點／交換校區對應，多校區不代選。',
15:'官方連OSM way32469535實際是Maison des sciences humaines et environnementales Claude Nicolas Ledoux研究建物9nodes；ODbL不解決programme campus，未採任意建物centroid。',
195:'ESIEA新官方campus-laval alias正文實讀；未獲消除舊JSON-LD與named map經度矛盾的證據，保留既有差異，不改展示坐標。',
}

def read(name):return json.loads((B/(name+'.json')).read_text())
def write(name,value):(B/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def evidence(sid):
 s=source(sid)
 return dict(source_id=sid,source_url=s['source_url'],final_url=s.get('final_url'),checked_at=s['checked_at'],http_status=s.get('http_status'),error=s.get('error'),content_sha256=s.get('sha256'),quote=(s.get('text') or '')[:600],locator='Retained actual HTML text/PDF body or explicit failure; manual facts carry exact page/quotation',applicable_year='Not established unless individually quoted/visually documented; URL/upload/copyright date not academic year')

def main():
 old=read('milestone5_full_gap_outcomes');baseline=[s for s in old['schools'] if s['state']=='needs_source'];assert len(baseline)==42
 facts=read('milestone6_reviewed_host_facts');byid={r['id']:r for r in facts};intake={r['id']:r for r in read('milestone6_official_inputs')['schools']}
 checks=[dict(c,stage=stage) for stage in STAGES for c in read('milestone6_'+stage+'_capture_checks')]
 checks += [dict(institution_id='tku-sister-39',source_id=r['id'],stage='office_container',**{k:r.get(k) for k in ['source_url','http_status','error','checked_at']}) for r in read('milestone6_office_container_reviews')]
 assert len(checks)==56 and len({c['source_id'] for c in checks})==56
 used={e['source_id'] for r in facts for f in r['fields'].values() for e in f['evidence']}
 aliases=[]
 for c in checks:
  if c['stage']!='official' or c['institution_id'] not in intake:continue
  s=source(c['source_id'])
  prior=[p for p in intake[c['institution_id']]['prior_source_checks'] if p.get('content_sha256')==s.get('sha256') and p['source_url']!=s['source_url']]
  if prior:aliases.append(dict(institution_id=c['institution_id'],source_id=c['source_id'],source_url=s['source_url'],prior_same_body_urls=[p['source_url'] for p in prior],content_sha256=s['sha256'],decision='Retained actual alias request, not an unattempted distinct official body or new applicable incoming rule'))
 assert {a['institution_id'] for a in aliases}=={'tku-sister-252','tku-sister-191','tku-sister-79'}
 scopes=[dict(**evidence(c['source_id']),exclude_from_semester_reference_index=True,status='quoted_manual_reference_fields_only' if c['source_id'] in used else 'route_or_asset_discovery_no_rule_promotion',review_scope='Scope/route/template format only unless exact individually reviewed host facts; no claim every sidebar or future year applicable',assessment='Outgoing, degree, empty directory, map assets and encrypted forms never automatically produce incoming semester rules') for c in checks]
 write('milestone6_source_scope_reviews',scopes)
 rows=[]
 for s in baseline:
  n=int(s['id'].removeprefix('tku-sister-'));cs=[c for c in checks if c['institution_id']==s['id']];fields=byid.get(s['id'],{}).get('fields',{});b=intake[s['id']]
  initial='relevant_official_leaf_not_attempted' if n in UNTRIED else 'targeted_entry_attempt_failed' if n in FAILED else 'read_but_no_applicable_content'
  final='connected_reference' if fields else 'targeted_entry_attempt_failed' if n in FAILED|{252} else 'read_but_no_applicable_content'
  assert n in REQUESTS and b['official_entry_attempted']
  ev={e['source_id']:e for e in s['source_evidence']}
  for c in b['prior_source_checks']+cs:ev[c['source_id']]=evidence(c['source_id'])
  rows.append(dict(id=s['id'],school_name=s['school_name'],country=s['country'],official_root_attempted=True,initial_classification=initial,final_classification=final,state='connected_reference' if fields else 'needs_source',
   initial_classification_definition='Priority: actual unattempted relevant incoming leaf; else failed targeted exchange/contact/TLS route; else readable available body without applicable incoming rules. Readable root and failed alternative may coexist.',
   baseline_assessment=s['assessment'],new_attempt_records=len(cs),source_evidence=list(ev.values()),reference_fields=list(fields),reviewed_host_period_fields=[k for k,f in fields.items() if f['source_period_verified']],facts_file='milestone6_reviewed_host_facts.json' if fields else None,
   minimum_school_provided_content=REQUESTS[n],school_contact_action='Request list only; no messages sent',current_TKU_application_verified=False,global_public_source_exhaustion_proven=False,
   stop_reason='Finite actual official links reviewed; remaining named gaps require current applicable source or school clarification. No unlimited new candidates or same failed route retry.'))
 init=dict(Counter(r['initial_classification'] for r in rows));final=dict(Counter(r['final_classification'] for r in rows))
 assert init=={'targeted_entry_attempt_failed':12,'read_but_no_applicable_content':21,'relevant_official_leaf_not_attempted':9}
 assert final=={'targeted_entry_attempt_failed':12,'read_but_no_applicable_content':23,'connected_reference':7}
 write('milestone6_remaining_source_outcomes',dict(base_commit=BASE,checked_date='2026-10-11',frozen_institutions=42,never_attempted_official_roots=0,initial_classifications=init,final_classifications=final,classification_refinement='Three requested HTTP/index aliases returned SHA-identical prior bodies; retain attempts, classify prior source state instead of calling them new unattempted bodies',same_body_alias_attempts=aliases,additional_reference_institutions=7,additional_reference_fields=61,attempt_records=len(checks),unique_request_urls=len({source(c['source_id'])['source_url'] for c in checks}),unchanged_external_institutions=36,current_TKU_new_home_applications=0,schools=rows))
 now={r['id']:r for r in rows};full=[now.get(s['id'],s) for s in old['schools']];states=dict(Counter(s['state'] for s in full));assert states=={'needs_source':35,'external_limit':36,'connected_reference':27}
 write('milestone6_full_gap_outcomes',dict(base_commit=BASE,checked_date='2026-10-11',frozen_baseline=98,statuses=states,remaining_without_reference=71,scope='Original98 only. Reference connected does not mean current TKU nomination/quota/campus/host requirements complete.',schools=full))
 assets=read('milestone5_asset_outcomes');ar=[]
 for s in assets['schools']:
  n=int(s['id'].removeprefix('tku-sister-')) if s['id'].startswith('tku-sister-') else None;cs=[c for c in checks if c['institution_id']==s['id'] and c['stage']=='official' and c['source_id'] not in used]
  r=dict(s,prior_evidence_file='milestone5_asset_outcomes.json',milestone6_safe_path_review=ASSET_NOTES.get(n),milestone6_source_checks=[evidence(c['source_id']) for c in cs],minimum_school_provided_asset='Confirm receiving campus/merger identity and a named point; for missing photos provide freely reusable actual campus photo with capture date, author and licence.',no_new_display_asset=True)
  if n==203:r['named_marker_candidate']=dict(latitude=48.8292405,longitude=2.3817211,source_id='2b2257732f72671233b49503',campus='Campus Grands Moulins',display_accepted=False,reason='Diderot agreement inheritance/current receiving campus not verified')
  if n in [175,207]:r['visual_pdf_review']=dict(source_id='3edb2020fa5415b5bb0ddf3c' if n==175 else '86fbe7554929762b4f0d3400',pages=[1,2],actual_body_period='Produced August2026' if n==175 else 'Body year not verified;2025 filename excluded',rendered_evidence=['milestone6-map-'+('um' if n==175 else 'uma')+'-'+str(p)+'.png' for p in [1,2]])
  ar.append(r)
 photos=read('campus_asset_manifest');coords=read('campus_location_manifest')
 original_ids={r['id'] for r in ar};withdrawal=read('fixed_photo_blocker_holds')
 extra={r['id'] for r in withdrawal['schools']}-original_ids
 write('milestone6_asset_outcomes',dict(checked_date='2026-10-11',photos=len(photos),coordinates=len(coords),photo_gaps=287-len(photos),coordinate_gaps=287-len(coords),original_union_gap_institutions=39,union_gap_institutions=39+len(extra),new_named_lead_institutions=8,additional_display_assets=0,additional_photo_withdrawal_institutions=len(extra),photo_withdrawal_file='fixed_photo_blocker_holds.json',schools=ar))
 # Keep both literal sources and the unresolved condition; never fix source dates.
 def E(sid,needle,page=None,year='See actual body; no automatic current-home applicability'):
  return fact(source(sid),'',needle,year,page)['evidence']
 conflict_specs=[
 ('nqu_photo_count','tku-sister-186',['latest_forms'],'International page two photos vs both undated application PDFs three photos',E('cfd1a14ad1323c16de5e95d3','Two recent 2-inch')+E('d7d943061ef6dfb050e67163','Attach three recent',1)+E('5d00191c1318c7f554ddbb3c','Attach three recent',1)),
 ('agu_english_alternative','tku-sister-33',['host_language'],'2027 guideline cannot provide score vs2027 factsheet tests not held in country',E('a6ad8d0b582e21f47764e912','If an applicant cannot',3)+E('fe6ba0603f976dbf7c01cb6d','In case TOEFL',4)),
 ('agu_transcript_timing','tku-sister-33',['student_support'],'2027 guideline late March vs factsheet English transcript April for second semester',E('a6ad8d0b582e21f47764e912','transcripts',1)+E('fe6ba0603f976dbf7c01cb6d','Transcripts',3)),
 ('agu_health_template','tku-sister-33',['latest_forms'],'2027 guideline health3months / mandatory2vaccinations vs undated template chestXray1year / immunity history or antibody alternatives; requirements need office confirmation',E('a6ad8d0b582e21f47764e912','three (3) months',6)+E('1f7a5b7ad67a0ee10ed03658','within one year',3)),
 ('aizu_2027_spring_status','tku-sister-39',['host_deadline'],'2027Spring In preparation alongside already-past ThursdaySeptember17,2026 deadline; no guessed year correction',E('5113f11c4c728da620ea778d','Status: In preparation')),
 ]
 write('milestone6_source_conflicts',[dict(id=k,institution_id=i,fields=f,status='pending_official_confirmation',reason=r,evidence=e,resolution='Retain both official statements; no guessed correction or home-policy promotion',prior_conflicts_file='milestone5_source_conflicts.json') for k,i,f,r,e in conflict_specs])
 attachments=[]
 for c in checks:
  s=source(c['source_id']);local=s.get('local_file')
  if local and local.endswith('.pdf'):
   visual=c['source_id'] in {'3edb2020fa5415b5bb0ddf3c','86fbe7554929762b4f0d3400'}
   attachments.append(dict(**evidence(c['source_id']),institution_id=c['institution_id'],local_file=local,status='binary_opened_visual_reviewed' if visual else 'binary_opened_text_content_reviewed',attachment_obtained=True,content_opened=True,pages_reviewed=[p['page'] for p in s['pages']],academic_year_from_filename=False,template_is_current_home_document=False,visual_evidence=next((a.get('visual_pdf_review') for a in ar if a.get('visual_pdf_review',{}).get('source_id')==c['source_id']),None)))
  elif c['stage']=='office_container':
   attachments.append(dict(**evidence(c['source_id']),institution_id=c['institution_id'],local_file=local,status='encrypted_office_container_not_decrypted',attachment_obtained=True,content_opened=False,encrypted_office_package=s['encrypted_office_package'],directory_names=s['directory_names'],academic_year_from_filename=False,template_is_current_home_document=False))
  elif c['source_id']=='02082a94eabf4bcfdcbf7041':attachments.append(dict(**evidence(c['source_id']),institution_id=c['institution_id'],status='single_read_timeout_no_attachment',attachment_obtained=False,content_opened=False,local_file=None))
  elif local and local.endswith('.xlsx'):
   review=next(r for r in read('milestone6_remaining_document_reviews') if r['source_id']==s['id'])
   attachments.append(dict(**evidence(c['source_id']),institution_id=c['institution_id'],local_file=local,status='binary_opened_sheet_content_reviewed',attachment_obtained=True,content_opened=True,academic_year_from_filename=False,template_is_current_home_document=False,body_review=review))
 assert Counter(a['status'] for a in attachments)=={'binary_opened_text_content_reviewed':8,'binary_opened_visual_reviewed':2,'binary_opened_sheet_content_reviewed':2,'encrypted_office_container_not_decrypted':2,'single_read_timeout_no_attachment':1}
 write('milestone6_attachment_reviews',attachments)
 print(json.dumps(dict(initial=init,final=final,original98=states,attempt_records=len(checks),unique_urls=len({source(c['source_id'])['source_url'] for c in checks}),asset_leads8=True,attachments=dict(Counter(a['status'] for a in attachments))),ensure_ascii=False))

if __name__=='__main__':main()
