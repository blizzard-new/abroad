"""Finite42-school closure, literal period evidence and opaque-form boundaries."""
import gzip,hashlib,json,subprocess
from collections import Counter
from pathlib import Path
from fastapi.testclient import TestClient
from exchange_info.api import create_app
from exchange_info.tku_data import BUNDLE as B
from scripts.tku_capture_io import read_bytes

BASE='4f142ea36e69338d2956b4ea5d3d37a9f4116e52'
ROOT=Path(__file__).resolve().parents[1]
def data(n):return json.loads((B/(n+'.json')).read_text())
def capture(sid):return json.loads(gzip.decompress(read_bytes(B/'host_census_sources'/(sid+'.json.gz'))))

def test_frozen42_classification_is_not_a_claim_of_never_read_official_roots():
 r=data('milestone6_remaining_source_outcomes');prior=data('milestone5_full_gap_outcomes')
 assert len(r['schools'])==len({s['id'] for s in r['schools']})==42
 assert {s['id'] for s in r['schools']}=={s['id'] for s in prior['schools'] if s['state']=='needs_source'}
 assert r['never_attempted_official_roots']==0 and all(s['official_root_attempted'] for s in r['schools'])
 assert r['initial_classifications']=={'relevant_official_leaf_not_attempted':9,'targeted_entry_attempt_failed':12,'read_but_no_applicable_content':21}
 assert {a['institution_id'] for a in r['same_body_alias_attempts']}=={'tku-sister-252','tku-sister-191','tku-sister-79'}
 assert all(capture(a['source_id'])['sha256']==a['content_sha256'] for a in r['same_body_alias_attempts'])
 assert r['final_classifications']=={'connected_reference':7,'targeted_entry_attempt_failed':12,'read_but_no_applicable_content':23}
 for s in r['schools']:
  assert s['source_evidence'] and s['minimum_school_provided_content'] and s['stop_reason']
  assert s['school_contact_action']=='Request list only; no messages sent'
  assert not s['current_TKU_application_verified'] and not s['global_public_source_exhaustion_proven']
  for e in s['source_evidence']:
   c=capture(e['source_id']);assert e['source_url']==c['source_url'] and e['checked_at']==c['checked_at'] and e['quote'] in c.get('text','') and e['content_sha256']==c.get('sha256')
 full=data('milestone6_full_gap_outcomes');assert len(full['schools'])==98
 assert full['statuses']==dict(Counter(s['state'] for s in full['schools']))=={'connected_reference':27,'external_limit':36,'needs_source':35}
 assert [s for s in full['schools'] if s['state']=='external_limit']==[s for s in prior['schools'] if s['state']=='external_limit']

def test_new61_host_fields_have_exact_quotes_pages_periods_and_no_home_promotion():
 rows=data('milestone6_reviewed_host_facts');assert len(rows)==7 and sum(len(r['fields']) for r in rows)==61
 assert sum(f['source_period_verified'] for r in rows for f in r['fields'].values())==23
 for r in rows:
  assert not {'quota','home_eligibility','home_language','home_deadline','documents'}.intersection(r['fields'])
  for f in r['fields'].values():
   assert f['status']=='reference_only' and f['reason'] and f['review_scope']
   for e in f['evidence']:
    c=capture(e['source_id']);assert e['quote'] in c['text'] and e['source_url']==c['source_url'] and e['content_sha256']==c['sha256']
    assert e['checked_at'] and e['locator'] and e['applicable_year']
    if c.get('local_file','').endswith('.pdf'):assert e['locator'].startswith('PDF p.')

def test_actual2027_body_wins_over2007_filename_but_historical2025_stays_history():
 rows={r['id']:r['fields'] for r in data('milestone6_reviewed_host_facts')}
 agu=capture('a6ad8d0b582e21f47764e912');assert '2007Spring' in agu['source_url'] and 'First (Spring) Semester of 2027' in agu['pages'][0]['text']
 assert rows['tku-sister-33']['host_deadline']['source_period_verified'] and '2026/11/10' in rows['tku-sister-33']['host_deadline']['value']
 assert not rows['tku-sister-33']['course_schedule']['source_period_verified'] and '2026' in rows['tku-sister-33']['course_schedule']['value']
 assert not rows['tku-sister-33']['latest_forms']['source_period_verified']
 assert all(f['status']=='reference_only' and any('2025' in e['applicable_year'] and 'historical' in e['applicable_year'] for e in f['evidence']) for f in rows['tku-sister-174'].values())
 assert '國內交換' in rows['tku-sister-186']['costs']['value']
 assert 'In preparation' in rows['tku-sister-39']['host_deadline']['value'] and '已過' in rows['tku-sister-39']['host_deadline']['value']
 conflicts=data('milestone6_source_conflicts');assert len(conflicts)==5 and len(data('milestone5_source_conflicts'))==5
 assert all(c['status']=='pending_official_confirmation' and c['evidence'] for c in conflicts)

def test_real_attachments_and_encrypted_ole_are_separate_from_readable_templates():
 rows=data('milestone6_attachment_reviews');assert Counter(r['status'] for r in rows)=={'binary_opened_text_content_reviewed':8,'binary_opened_visual_reviewed':2,'binary_opened_sheet_content_reviewed':2,'encrypted_office_container_not_decrypted':2,'single_read_timeout_no_attachment':1}
 for r in rows:
  assert not r.get('academic_year_from_filename') and not r.get('template_is_current_home_document')
  if r['attachment_obtained']:
   blob=read_bytes(B/'host_census_sources'/r['local_file']);assert hashlib.sha256(blob).hexdigest()==r['content_sha256']
   if r['status']=='binary_opened_sheet_content_reviewed':
    assert blob.startswith(b'PK') and r['content_opened'] and len(r['body_review']['sheets'])==8
    assert r['body_review']['body_cells']['Application_1']['H55']=='2027'
    assert not r['body_review']['macros_executed'] and not r['body_review']['external_links_updated']
   elif r['status'].startswith('binary_opened'):assert blob.startswith(b'%PDF') and r['content_opened'] and r['pages_reviewed']
   else:
    assert blob.startswith(bytes.fromhex('d0cf11e0a1b11ae1')) and r['encrypted_office_package'] and not r['content_opened']
    assert {'EncryptionInfo','EncryptedPackage'} <= set(r['directory_names'])
    c=capture(r['source_id']);assert c['text']=='' and c['error'].startswith('EncryptedOfficeContainer')
 timeout=next(r for r in rows if r['status']=='single_read_timeout_no_attachment');assert 'ReadTimeout' in timeout['error']
 # HTTP200 alone cannot establish content readability. Original unparsed
 # captures and the later, linked offline parser results remain distinct.
 legacy=[r for r in data('full_census_acceptance')['downloaded_attachments'] if r['file'].endswith('.doc')]
 assert len(legacy)==12 and len({r['file'] for r in legacy})==6 and len({r['source_id'] for r in legacy})==12
 originals=[r for r in legacy if not r['original_capture_id']]
 parsed=[r for r in legacy if r['original_capture_id']]
 assert len(originals)==len(parsed)==6 and len({r['file'] for r in parsed})==5
 assert all(not r['content_opened'] and r['content_limitation']=='legacy_DOC_parser_not_available' for r in originals)
 original_by_id={r['source_id']:r for r in originals}
 for row in parsed:
  source=capture(row['source_id']);original=original_by_id[row['original_capture_id']]
  assert row['content_opened'] and row['content_extraction_status']=='parsed_legacy_DOC_text_offline' and row['content_limitation'] is None
  assert source['text'].strip() and source['parser']['conversion_exit_code']==0
  assert source['parser']['macro_security_level']==3 and source['parser']['external_link_update']==0
  assert row['sha256']==original['sha256'] and row['file']==original['file']

def test_new_directories_degree_pages_maps_and_formats_cannot_auto_generate_rules():
 scopes=data('milestone6_source_scope_reviews');assert len(scopes)==56 and all(s['exclude_from_semester_reference_index'] for s in scopes)
 rows=[json.loads(l) for l in (B/'partner_enrichment.jsonl').read_text().splitlines()]
 assert sum(len(r['reference_excerpts']) for r in rows)==2350
 prohibited={r['source_id'] for r in scopes}
 assert not prohibited & {e['source_id'] for r in rows for excerpt in r['reference_excerpts'] for e in excerpt['evidence']}
 assert sum(bool(r['fields']) for r in rows)==216
 assets=data('milestone6_asset_outcomes');assert len(assets['schools'])==39 and assets['original_union_gap_institutions']==39
 assert assets['union_gap_institutions']==41 and assets['photos']==262 and assets['coordinates']==264
 paris=next(r for r in assets['schools'] if r['id']=='tku-sister-203');assert paris['named_marker_candidate']['latitude']==48.8292405 and not paris['named_marker_candidate']['display_accepted']
 assert sum(bool(r['milestone6_safe_path_review']) for r in assets['schools'])==8

def test_prior_m5_snapshots_curated_fields_and_coordinates_remain_exact():
 paths=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'--','src/exchange_info/official_data/tku'],cwd=ROOT,text=True).splitlines()
 snapshots=[p for p in paths if any('/milestone'+str(n)+'_' in p for n in [3,4,5])]
 assert len(snapshots)>=30
 for p in snapshots:assert (ROOT/p).read_bytes()==subprocess.check_output(['git','show',BASE+':'+p],cwd=ROOT)
 prior=json.loads(subprocess.check_output(['git','show',BASE+':src/exchange_info/official_data/tku/curated_partner_facts.json'],cwd=ROOT));current={r['id']:r for r in data('curated_partner_facts')}
 assert len(prior)==40 and len(current)==47 and all(current[r['id']]==r for r in prior)
 assert (B/'campus_location_manifest.json').read_bytes()==subprocess.check_output(['git','show',BASE+':src/exchange_info/official_data/tku/campus_location_manifest.json'],cwd=ROOT)

def test_seven_host_reviews_reach_offline_live_api_without_new_home_rules(tmp_path,monkeypatch):
 monkeypatch.setattr('requests.get',lambda *a,**k:(_ for _ in ()).throw(AssertionError('Bundled API must not make network requests')))
 client=TestClient(create_app(tmp_path));dashboard=client.get('/student-dashboard',params={'school':'TKU'}).json();assert len(dashboard['partner_universities'])==287
 for row in data('milestone6_reviewed_host_facts'):
  r=client.get('/tku/partner-census/'+row['id']).json()
  assert r['fields']['quota']['status']!='verified_current'
  for key,value in row['fields'].items():
   if key in r['fields']:
    assert r['fields'][key]['public_reference']['status']=='reference_only'
    assert r['fields'][key]['public_reference']['value']==value['value']
 audit=client.get('/tku/partner-census').json();assert audit['currently_open_home_applications']==0 and audit['latest_round_quota']==7 and audit['latest_round_schools']==4
