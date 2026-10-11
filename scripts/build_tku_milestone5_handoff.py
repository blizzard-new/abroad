"""Freeze continuation outcomes: connected references, external limits, source needs."""
import json
from collections import Counter
from build_tku_milestone3_host_reviews import source
from tku_capture_io import BUNDLE

EXTERNAL={262:'官方study.cqu.edu.cn回412；未繞過precondition/challenge。需新的公開適用入境資料。',167:'官方國際學生sie入口503；未重複服務重試或繞過。東陸／呈貢校區仍不能代配。',60:'官方international入口403；未繞過。需公開適用入境資料。',72:'官方EducationAbroad incoming路徑403；未繞過；degree admissions不能替代。',11:'官方OAICE根及/es/均ReadTimeout(22秒)；UCR其他新聞可讀，不能把教學國際活動當學生入境申請。'}
NEEDS={306:'官方海外學生服務與非學歷目錄可讀；可追內容是漢語課及獎學金、非學期交換受入。2027東吳公告是本校出國。需台灣incoming交換適用正文。',341:'可讀正文有StudentExchange標題但沒有可追的公開anchor；指定publicreader因TLS驗證失敗未得DOM。需官方學期incoming規則／適用track。',334:'根頁新聞可讀、假設國際route404；publicreaderTLS失敗。需實際官方incoming目錄與CampoTiro校區點，不用LaGarza行政點。',328:'degree根可讀；ContactUs是HTTP202空體；官方連出的healthcare頁只證明MainClinic9100ParkWestDr與院外醫院，不證明academic校區點。需incoming規則與academiccampus證據。',320:'官方international頁是IMBA/PhD eLearning分支，SMK為本校出國、Sias為summer；不作入境學期。新住所與網站圖片未帶自由重用授權，需incomingtrack／有授權且有拍攝年的校景。',311:'TKU舊.com頁正文確連uml.edu；已讀uml.edu GlobalPartnerExchange，列學生出國partner、未得incoming申請正文。需母校提名可用入境programme。',310:'官方根可讀，兩個international候選404；需實際公開InternationalOffice/incoming入口，不將失敗假設路径當全校服務不存在。',281:'EducationAbroad正文是K-State本校學生出國與programmeprovider；需incomingexchange規則，不套本科degree admission。',270:'總統辦公室可讀，OIE假設root/leaf404；需有效官方incoming入口／partnerfactsheet。',267:'根僅211字，incoming候選404；normalreaderTLS失敗。需官方實際入境雙邊方案，不補一般Erasmus規則。',253:'新international假設routeHTTP200但正文明示Trangkhôngtồntại404；需有效官方incoming正文。有校景圖片不等於取得重用授權。',252:'SIE入口HTTP200仅12字，沒有招生／交換正文；需當期台港澳incoming適用規則，不取outgoing或校區介紹補值。',251:'國際／境內合作頁是機構策略及導覽，尚未定位台灣學生可用交換track／規則。',246:'已讀網站指南，主要是degree/nonlocalUWL/Wrexham課程註冊；教育局課程有效期不是交換年度。需獨立incoming方案。',224:'GJC官方根可讀，包含出國學生、研討／暑期營與國際degree訊息；需學期incoming與台灣學生適用資料，地址兩校區不代配。',191:'官方留學福建師大目錄僅導覽，2027世新／澳門／Oswego是本校出國公告；需台灣incoming學期正文。',186:'國際交換計畫頁是金門母校對外甄選：實載105/106等歷史；外國degree招生與TKU兩岸國內交換分開，需淡江可用接待流程。',183:'internationaladmissions正文2027/28 full-time degree Batch2實載期限；不能當exchange。需UMY學期incoming方案。',174:'合作交流頁主要全校合作機構入口與策略；未定位接待台灣交換實際程序。',39:'會津根／en可讀為研究與學生競賽；兩個假設international/sgu404。需實際官方exchange受入入口，不將事件或本科全英學位當交換。',55:'官方MovilidadEstudiantil頁是本校向外選拔／獎學金申請，M3已讀並排除；沒有新incoming正文，不重標為入境。',9:'官方根可讀、international與international-students候選404；需可用交換方案，distance-degree課不推定學期實體交換。',86:'OISS是一般國際學生支援，GlobalEngagement/StudyAway主體是出國；normalreaderTLS失敗，需incomingapplication/partnerfactsheet。',61:'假設國際routeHTTP200回同一root新聞／招生，不是學期incoming；需可核實適用的公開incoming表／期限。',63:'假設exchangeURLHTTP200但正文404Página no encontrada；需真正的incoming/院系agreement資料。',44:'English/sitemap可讀，但只有一般course／degree／scholarship欄；normalreaderTLS失敗，沒有可核實的exchange受入簡章或自由授權校景。',79:'InternationalOffice正文為degree國際招生及服務；尚未定位學期incoming規則，不借用一般degree門檻。',56:'Contacts正文是各院contact directory，不是studentexchange；normalreaderTLS失敗，需正式incomingprogramme。',23:'AUCP是本校出國中國careerprogramme；InternationalStudents為degree介紹，後續rootHTTP200空體；需交換受入規則。',22:'官方根可讀，兩個international假設route404；normalreaderTLS失敗，需實際國際交流受入資料；cgu.ac.jp不可與臺灣CGU混同。'}

def main():
 baseline=json.loads((BUNDLE/'milestone5_readable_inputs.json').read_text())['schools'];facts=json.loads((BUNDLE/'milestone5_reviewed_host_facts.json').read_text());byid={r['id']:r for r in facts}
 files=['route','followup','body','programme','document','geography'];checks=[]
 for stage in files:
  for c in json.loads((BUNDLE/f'milestone5_{stage}_capture_checks.json').read_text()):checks.append(dict(**c,stage=stage))
 readers=json.loads((BUNDLE/'milestone5_public_reader_checks.json').read_text())
 used={e['source_id'] for r in facts for f in r['fields'].values() for e in f['evidence']}
 ids={c['source_id'] for c in checks+readers}|{sid for r in baseline for sid in r['baseline_source_ids']};scopes=[]
 for sid in sorted(ids):
  s=source(sid);scopes.append(dict(source_id=sid,source_url=s['source_url'],checked_at=s['checked_at'],http_status=s.get('http_status'),error=s.get('error'),content_sha256=s.get('sha256'),
   status='quoted_manual_reference_fields_only' if sid in used else 'route_or_asset_discovery_no_rule_promotion',exclude_from_semester_reference_index=True,
   review_scope='Institutional route/scope/location review; only individually quoted fields semantically verified; not a claim to full review of every news/sidebar body',
   quote=(s.get('text') or '')[:600],applicable_year='See individually reviewed fields; neither URL year nor copyright establishes academic cycle',
   assessment='CAPTCHA/TLS/access/empty/soft404, full-degree, outgoing, strategy and directories do not generate automatic semester rules. Accepted incoming facts remain reference_only.'))
 (BUNDLE/'milestone5_source_scope_reviews.json').write_text(json.dumps(scopes,ensure_ascii=False,indent=2)+'\n')
 schools=[]
 for r in baseline:
  n=int(r['id'].removeprefix('tku-sister-'));cs=[c for c in checks+readers if c['institution_id']==r['id']];fields=byid.get(r['id'],{}).get('fields',{})
  if fields:state='connected_reference';assessment='可展示欄位已接平台；'+('僅計畫／臨時服務範圍，不是完整學期申請規則。' if n in [285,169] else '實際學期incoming正文已定位；不表示TKU本期名額／資格／全部欄位核實。')
  elif n in EXTERNAL:state='external_limit';assessment=EXTERNAL[n]
  else:state='needs_source';assessment=NEEDS[n]
  evidence=[]
  for sid in dict.fromkeys(r['baseline_source_ids']+[c['source_id'] for c in cs]):
   s=source(sid);evidence.append(dict(source_id=sid,source_url=s['source_url'],final_url=s.get('final_url'),checked_at=s['checked_at'],http_status=s.get('http_status'),error=s.get('error'),content_sha256=s.get('sha256'),quote=(s.get('text') or '')[:450],locator='Retained actual extracted HTML/PDF body or public-reader error; detailed fields have page/exact quotation',applicable_year='Not established unless individually quoted in reviewed facts'))
  schools.append(dict(id=r['id'],school_name=r['school_name'],country=r['country'],state=state,assessment=assessment,reference_fields=list(fields),reviewed_host_period_fields=[k for k,f in fields.items() if f.get('source_period_verified')],facts_file='milestone5_reviewed_host_facts.json' if fields else None,source_evidence=evidence,current_TKU_application_verified=False,global_public_source_exhaustion_proven=False))
 assert len(schools)==len({r['id'] for r in schools})==47
 states=dict(Counter(r['state'] for r in schools));assert states=={'needs_source':30,'connected_reference':12,'external_limit':5}
 # Actual source conflicts remain machine-readable, with both originals linked.
 conflict_specs=[('dankook_deadline_year','tku-sister-41',['host_deadline','host_nomination_deadline'],'Spring2027 header vs2025 numeric deadlines, historical2024 page and main OIA differing nomination start; no year correction'),('sit_course_scope','tku-sister-245',['department_scope'],'AY2027/28 PDF restricts undergraduate graduate/architecture courses; undated webpage permits more'),('sit_health_stage','tku-sister-245',['latest_forms'],'AY2027/28 guideline upon application vs webpage after acceptance'),('its_health_template','tku-sister-264',['latest_forms'],'Prospectiveguide doctor/stamp pages1–2 instructions do not match retained undated health template sections/signature fields'),('its_period_scope','tku-sister-264',['host_deadline','host_nomination_deadline','costs','latest_forms'],'2027 webpage vs2026 generic nomination/single-semester waiver and intrinsically undated2019/2022-linked templates; no automatic year propagation')]
 conflicts=[]
 for key,identifier,keys,reason in conflict_specs:
  evidence=[e for k in keys for e in byid[identifier]['fields'][k]['evidence']]
  conflicts.append(dict(id=key,institution_id=identifier,fields=keys,status='pending_official_confirmation',reason=reason,evidence=evidence,resolution='No guessed values, date-year correction, home-policy promotion or automatic preference'))
 (BUNDLE/'milestone5_source_conflicts.json').write_text(json.dumps(conflicts,ensure_ascii=False,indent=2)+'\n')
 result=dict(base_commit='1619ba890e3dc282bb26f92ebeeeece375e9ffe8',checked_date='2026-10-11',fixed_readable_institutions=47,statuses=states,connected_semester_rule_institutions=10,connected_narrow_scope_service_institutions=2,additional_fields=sum(len(r['fields']) for r in facts),previous31external_and12_nonsemester='unchanged; no repeated probes without new official alternatives',attempt_records=len(checks)+len(readers),unique_source_ids=len({c['source_id'] for c in checks+readers}),attempt_http_statuses=dict(Counter(str(c.get('http_status') or 'connection_error') for c in checks+readers)),public_reader_results=dict(Counter('TLS_certificate_failure' if 'ERR_CERT_AUTHORITY_INVALID' in (c.get('error') or '') else 'other' for c in readers)),source_scope_reviews=len(scopes),source_conflicts=len(conflicts),current_TKU_new_home_applications=0,schools=schools)
 (BUNDLE/'milestone5_readable_outcomes.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 # Reconcile all original98 gaps while retaining the earlier31/12 decisions.
 old_gaps=json.loads((BUNDLE/'milestone4_remaining_source_limits.json').read_text())['schools'];current={r['id']:r for r in schools};complete=[]
 for old in old_gaps:
  if old['id'] in current:
   entry=dict(current[old['id']],reviewed_in_milestone5=True,prior_status=old['status'])
  else:
   state='connected_reference' if old['status'].startswith('reference_added') else 'external_limit' if old['status'].startswith('external_') else 'needs_source'
   entry=dict(id=old['id'],school_name=old['school_name'],country=old['country'],state=state,assessment=old['next_action'],reference_fields=old['added_reference_fields'],reviewed_in_milestone5=False,prior_status=old['status'],prior_evidence_file='milestone4_remaining_source_limits.json',source_evidence=old['source_checks'],current_TKU_application_verified=False)
  complete.append(entry)
 all_states=dict(Counter(r['state'] for r in complete));assert len(complete)==98 and all_states=={'needs_source':42,'external_limit':36,'connected_reference':20}
 (BUNDLE/'milestone5_full_gap_outcomes.json').write_text(json.dumps(dict(checked_date='2026-10-11',frozen_baseline=98,statuses=all_states,remaining_without_reference=78,scope='Connected reference does not mean all current TKU rules, fields or nomination campus verified',schools=complete),ensure_ascii=False,indent=2)+'\n')
 # All39 asset gaps retained, with new safe-path outcomes, not forced coordinates.
 old=json.loads((BUNDLE/'milestone4_asset_source_limits.json').read_text());assets=[]
 notes={319:'已讀官方連uMap及公開CityCampus圖層9features；East[138.60511,-34.919845]、West[138.591258,-34.923052]是兩個命名point，其餘7polygon；top-levelgeometry只是視窗中心。舊UniversityofAdelaide與新AdelaideUniversity協議承繼、East/West對應未知，兩點均保留候選，不任選代配。',328:'已讀官方連出healthcareContact：MainClinic及各HoustonMethodist醫院服務點，不證明academiccampus或數值point；academiccontactHTTP202空體。',169:'ac.jp已證明連到臨時omu.moeInternationalAffairs，可用於服務身份；未提供具體校區point，不能用醫院／高中／母體坐標。',334:'intro新聞仍可讀，假設國際route404、正常browserTLS失敗；CampoTiro與LaGarza校區差異未消除。',167:'本輪SIE入口503停止；東陸／呈貢對應未核實，不為分母完整而代選。',320:'已讀IICinternationalContact，為IMBA/PhD分支；沒有新授權且具拍攝年校景。舊Commons公函／人物／活動拒收保留。',253:'新international候選soft404；正文頁圖片沒有已取得自由重用授權，舊活動／人物／隔間照片拒收保留。',44:'Englishsitemap一般課程可讀、普通readerTLS失敗；沒有新的具身份／校景／自由授權／拍攝年候選。'}
 for r in old['schools']:
  related=[c for c in checks+readers if c['institution_id']==r['id']];a=dict(id=r['id'],school_name=r['school_name'],checked_date='2026-10-11',photo_state='needs_licensed_dated_campus_source' if r.get('photo_reason') else 'already_verified',coordinate_state='needs_named_campus_identity_or_point' if r.get('coordinate_reason') else 'already_verified',photo_reason=r.get('photo_reason'),coordinate_reason=r.get('coordinate_reason'),prior_evidence_file='milestone4_asset_source_limits.json',new_safe_path_review=notes.get(int(r['id'].removeprefix('tku-sister-'))) if r['id'].startswith('tku-sister-') else None,new_source_checks=[{k:c.get(k) for k in ['source_id','source_url','url','checked_at','http_status','error','content_sha256']} for c in related],global_safe_source_exhaustion_proven=False)
  assets.append(a)
 asset_result=dict(checked_date='2026-10-11',photos=264,coordinates=264,photo_gaps=23,coordinate_gaps=23,union_gap_institutions=39,additional_display_assets=0,schools=assets)
 (BUNDLE/'milestone5_asset_outcomes.json').write_text(json.dumps(asset_result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k!='schools'},ensure_ascii=False))
if __name__=='__main__':main()
