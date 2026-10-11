"""Actual data/API/profile withdrawals, preserving source and unaffected bytes."""
import hashlib,json,subprocess
from pathlib import Path
from fastapi.testclient import TestClient
from exchange_info.api import create_app
from exchange_info.tku_data import BUNDLE

BASE='4f142ea36e69338d2956b4ea5d3d37a9f4116e52'
IDS={'tku-sister-65','tku-sister-52'}
ROOT=Path(__file__).resolve().parents[1]
def test_fixed_photo_withdrawal_preserves_evidence_and_all_other_photos():
 prior=json.loads(subprocess.check_output(['git','show',BASE+':src/exchange_info/official_data/tku/campus_asset_manifest.json'],cwd=ROOT))
 current=json.loads((BUNDLE/'campus_asset_manifest.json').read_text());holds=json.loads((BUNDLE/'fixed_photo_blocker_holds.json').read_text())
 assert holds['blocker_document_commit']=='8b7570acca35fc10154e52e8621b9829bc9a815b'
 assert len(current)==262 and {r['id'] for r in prior}-{r['id'] for r in current}==IDS
 assert all(r==next(p for p in prior if p['id']==r['id']) for r in current)
 for hold in holds['schools']:
  assert not hold['display_accepted'] and hold['withdrawal_overrides_old_visual_pass'] and hold['reason'] and hold['evidence']
  blob=(ROOT/'sources/tku/withdrawn-campus-assets'/Path(hold['withdrawn_local_path']).name).read_bytes()
  assert hashlib.sha256(blob).hexdigest()==hold['withdrawn_photo_sha256']==hold['prior_photo']['sha256']
 assert 'West of England' in holds['schools'][0]['reason']
 assert '不判侵權' in holds['schools'][1]['reason']

def test_fixed_photo_gate_cannot_be_undone_by_old_visual_pass():
 from scripts.tku_photo_identity_policy import apply_photo_identity_policy
 holds=json.loads((BUNDLE/'fixed_photo_blocker_holds.json').read_text())['schools']
 assert apply_photo_identity_policy([h['prior_photo'] for h in holds])==[]

def test_fixed_blocked_photos_are_absent_from_api_profiles_and_credit(tmp_path):
 client=TestClient(create_app(tmp_path));dashboard=client.get('/student-dashboard',params={'school':'TKU'}).json()
 holds=json.loads((BUNDLE/'fixed_photo_blocker_holds.json').read_text())['schools']
 for h in holds:
  p=next(p for p in dashboard['partner_universities'] if h['school_name'] in p['school_name'])
  assert p['image_status']=='missing' and p['image_url'] is None and p['image_source_url'] is None and p['image_page_url'] is None
  assert not any(k.startswith('campus_photo_') for k in p['reference_data'])
  row=client.get('/tku/partner-census/'+h['id']).json();field=row['fields']['campus_photo']
  assert field['status']=='not_verified_new' and field['identity_or_attribution_hold']['withdrawn_photo_sha256']==h['withdrawn_photo_sha256']
  profile=client.get('/destination-profile',params={'school':p['school_name'],'home_school':'TKU'}).json()
  assert all(x['image_url']!=h['withdrawn_local_path'] and x['source_url']!=h['prior_photo']['source_url'] for x in profile['guide_photos'])


def test_withdrawn_originals_are_not_public_before_or_after_six_school_cache_warmup(tmp_path):
 client=TestClient(create_app(tmp_path))
 holds=json.loads((BUNDLE/'fixed_photo_blocker_holds.json').read_text())['schools']
 for h in holds:
  assert client.get(h['withdrawn_local_path']).status_code==404
  assert not (ROOT/'src/exchange_info'/h['withdrawn_local_path'].removeprefix('/')).exists()
 for home in ['CGU','NTPU','NTU','TKU','CCU','NCU','TKU']:
  response=client.get('/student-dashboard',params={'school':home})
  assert response.status_code==200
  for h in holds:
   assert h['withdrawn_local_path'] not in response.text
   assert h['prior_photo']['image_source_url'] not in response.text
   assert client.get(h['withdrawn_local_path']).status_code==404
