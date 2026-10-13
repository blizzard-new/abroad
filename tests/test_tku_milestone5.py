"""Readable-source outcomes, source periods and safe document parser regressions."""
import gzip
import hashlib
import io
import json
import subprocess
from collections import Counter
from pathlib import Path
from zipfile import ZipFile
import pytest
from fastapi.testclient import TestClient
from exchange_info.api import create_app
from exchange_info.tku_data import BUNDLE
from scripts.tku_capture_io import read_bytes


def data(name):return json.loads((BUNDLE/name).read_text())
def captured(sid):return json.loads(gzip.decompress(read_bytes(BUNDLE/'host_census_sources'/(sid+'.json.gz'))))


def test_all47_readable_schools_have_distinct_reviewable_outcomes():
 baseline=data('milestone5_readable_inputs.json')['schools'];r=data('milestone5_readable_outcomes.json')
 assert len(r['schools'])==len({s['id'] for s in r['schools']})==47
 assert {s['id'] for s in r['schools']}=={s['id'] for s in baseline}
 assert Counter(s['state'] for s in r['schools'])=={'connected_reference':12,'external_limit':5,'needs_source':30}
 assert r['connected_semester_rule_institutions']==10 and r['connected_narrow_scope_service_institutions']==2
 for s in r['schools']:
  assert s['assessment'] and s['source_evidence']
  assert not s['current_TKU_application_verified'] and not s['global_public_source_exhaustion_proven']
  for e in s['source_evidence']:
   c=captured(e['source_id']);assert e['checked_at'] and e['source_url']==c['source_url']
   assert e['content_sha256']==c.get('sha256') and e['quote'] in c.get('text','')


def test_new89_fields_are_scoped_exact_quotes_not_home_rules():
 rows=data('milestone5_reviewed_host_facts.json')
 assert len(rows)==12 and sum(len(r['fields']) for r in rows)==89
 for r in rows:
  assert not {'quota','home_eligibility','home_language','home_deadline','documents'}.intersection(r['fields'])
  for f in r['fields'].values():
   assert f['status']=='reference_only' and isinstance(f['source_period_verified'],bool)
   assert f['review_scope'] and f['reason']
   for e in f['evidence']:
    s=captured(e['source_id']);assert e['quote'] in s['text'] and e['content_sha256']==s['sha256']
    assert e['source_url'] and e['checked_at'] and e['locator'] and e['applicable_year']


def test_current_host_years_and_real_conflicts_stay_visible():
 rows={r['id']:r['fields'] for r in data('milestone5_reviewed_host_facts.json')}
 assert rows['tku-sister-264']['host_deadline']['source_period_verified']
 assert '2026/10/15' in rows['tku-sister-264']['host_deadline']['value']
 assert not rows['tku-sister-264']['host_nomination_deadline']['source_period_verified']
 assert rows['tku-sister-245']['department_scope']['source_period_verified']
 assert '本科不得選研究所' in rows['tku-sister-245']['department_scope']['value']
 assert rows['tku-sister-41']['study_period']['source_period_verified']
 assert not rows['tku-sister-41']['host_deadline']['source_period_verified']
 assert 'November15,2025' in rows['tku-sister-41']['host_deadline']['value']
 assert 'AY2025/26' in rows['tku-sister-232']['latest_forms']['value']
 assert '未列淡江' in rows['tku-sister-118']['host_eligibility']['value']
 assert '不是交換簡章官方尚未公告' in rows['tku-sister-169']['student_support']['value']
 conflicts=data('milestone5_source_conflicts.json');assert len(conflicts)==5
 assert all(c['status']=='pending_official_confirmation' and c['evidence'] for c in conflicts)


def test_binary_attachments_open_but_captcha_responses_do_not():
 reviews=data('milestone5_attachment_reviews.json')
 assert Counter(r['status'] for r in reviews)=={'binary_opened_content_reviewed':10,'CAPTCHA_gate_not_document':2,'historical_template_directory_not_attachment':1}
 for r in reviews:
  if r['attachment_obtained']:
   blob=read_bytes(BUNDLE/'host_census_sources'/r['local_file'])
   assert blob.startswith((b'%PDF',b'PK')) and hashlib.sha256(blob).hexdigest()==r['content_sha256']
  elif r['status']=='CAPTCHA_gate_not_document':
   assert r['http_status']==200 and not r['local_file'] and '验证码' in r['quote']
 assert all(c['exclude_from_semester_reference_index'] for c in data('milestone5_source_scope_reviews.json'))


def test_named_map_points_and_clinical_address_do_not_force_display_assets():
 assets=data('milestone5_asset_outcomes.json');assert len(assets['schools'])==39
 assert assets['photos']==assets['coordinates']==264 and assets['additional_display_assets']==0
 assert assets['photo_gaps']==assets['coordinate_gaps']==23
 ad=next(r for r in assets['schools'] if r['id']=='tku-sister-319')
 assert 'West' in ad['new_safe_path_review'] and '視窗中心' in ad['new_safe_path_review'] and '不任選' in ad['new_safe_path_review']
 acad=next(r for r in assets['schools'] if r['id']=='tku-sister-328')
 assert 'academiccampus' in acad['new_safe_path_review']
 readers=data('milestone5_public_reader_checks.json')
 assert len(readers)==8 and all('ERR_CERT_AUTHORITY_INVALID' in r['error'] for r in readers)
 assert all('TLS validation enabled' in r['reader'] for r in readers)


def test_prior_milestones_are_immutable_and_other_schools_unchanged():
 root=Path(__file__).resolve().parents[1];base='1619ba890e3dc282bb26f92ebeeeece375e9ffe8'
 paths=subprocess.check_output(['git','ls-tree','-r','--name-only',base,'--','src/exchange_info/official_data/tku'],cwd=root,text=True).splitlines()
 snapshots=[p for p in paths if '/milestone3_' in p or '/milestone4_' in p]
 assert len(snapshots)>=20
 for p in snapshots:assert (root/p).read_bytes()==subprocess.check_output(['git','show',base+':'+p],cwd=root)
 prior=json.loads(subprocess.check_output(['git','show',base+':src/exchange_info/official_data/tku/curated_partner_facts.json'],cwd=root))
 current={r['id']:r for r in data('curated_partner_facts.json')}
 assert all(current[r['id']]==r for r in prior)


def test_new_fields_reach_live_api_without_opening_home_applications(tmp_path):
 client=TestClient(create_app(tmp_path))
 dashboard=client.get('/student-dashboard',params={'school':'TKU'}).json()
 assert len(dashboard['partner_universities'])==287
 for identifier in ['tku-sister-264','tku-sister-245','tku-sister-41','tku-sister-130']:
  row=client.get('/tku/partner-census/'+identifier).json()
  assert row['fields']['quota']['status']!='verified_current'
  assert row['fields']['host_deadline']['status']=='reference_only'
 audit=client.get('/tku/partner-census').json()
 assert audit['currently_open_home_applications']==0 and audit['latest_round_quota']==7
 assert len(audit['field_counts'])==22


@pytest.mark.parametrize('kind',['xlsx','docx'])
def test_official_download_endpoint_without_extension_uses_office_zip_members(monkeypatch,tmp_path,kind):
 from scripts import capture_tku_census_hosts as m
 memory=io.BytesIO()
 with ZipFile(memory,'w') as z:
  if kind=='xlsx':
   z.writestr('xl/workbook.xml','<workbook/>')
   z.writestr('xl/worksheets/sheet1.xml','<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>2027 test year inside workbook</t></is></c></row></sheetData></worksheet>')
  else:z.writestr('word/document.xml','<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Actual undated template body</w:t></w:r></w:p></w:body></w:document>')
 url='https://official.example.invalid/download.jsp?attachment='+kind
 class Response:
  status_code=200;headers={};content=memory.getvalue()
  def __init__(self):self.url=url
  def raise_for_status(self):pass
 monkeypatch.setattr(m,'STORE',tmp_path);monkeypatch.setattr(m,'exists',lambda _:False)
 monkeypatch.setattr(m.requests,'get',lambda *_,**__:Response())
 r=m.capture(url)
 assert not r.get('error') and r['local_file'].endswith('.'+kind)
 assert '2027 test year inside workbook' in r['text'] if kind=='xlsx' else 'Actual undated template body' in r['text']
 assert (tmp_path/r['local_file']).read_bytes()==memory.getvalue()
