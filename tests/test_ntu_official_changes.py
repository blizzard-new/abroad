"""Dated source updates must not unlock unconfirmed selection or reminders."""
import hashlib
import json
import shutil
from pathlib import Path

from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.ntu_official_changes import apply_official_changes
from exchange_info.ntu_student_view import fetch_ntu_partner_universities
from exchange_info.application_rules import _partner_language_threshold

ROOT = Path(__file__).parents[1]
BUNDLE = ROOT / 'src/exchange_info/official_data/ntu'


def test_twenty_portal_updates_are_scoped_and_scores_preserve_their_scale(tmp_path):
    snapshot=json.loads((ROOT/'sources/ntu/2026-10-10-official-changes.json').read_text())
    assert len(snapshot['schools'])==20
    assert len({s['portal_id'] for s in snapshot['schools']})==20
    assert all(s['selection_quota'] is None and not s['list_marked_updated'] for s in snapshot['schools'])
    assert all(s['source_academic_year'] is None and s['current_cycle_finality']=='not_confirmed' for s in snapshot['schools'])
    assert all(not s['confirmation_banner_observed'] for s in snapshot['schools'])
    assert all({a['scale'] for a in s['language_score_alternatives']}=={'1-6','0-120'} for s in snapshot['schools'])
    assert all(not a['conversion_applied'] for s in snapshot['schools'] for a in s['language_score_alternatives'])
    partners={p.school_name:p for p in fetch_ntu_partner_universities()}
    assert 'GPA 達3.30' in partners['慕尼黑大學'].eligibility
    assert 'TOEFL iBT 4.5' in partners['慕尼黑大學'].eligibility
    assert _partner_language_threshold(partners['明斯特大學'],'toefl')==80
    assert _partner_language_threshold(partners['明斯特大學'],'toefl_new') is None
    assert '不含博士生' in partners['卡爾斯魯爾理工學院'].eligibility
    assert '/博一以上' in partners['波昂大學'].eligibility.replace('\n','')
    assert 'only' in partners['烏普薩拉大學'].application_info.lower()
    assert 'Physiology and Anatomy' in partners['烏普薩拉大學'].application_info
    assert 'March 2028' in partners['明斯特大學'].application_info
    assert all(p.availability_status!='open' for p in partners.values())
    assert all(p.quota is None or p.quota_status=='published' for p in partners.values() if p.source_url in {s['official_url'] for s in snapshot['schools']})
    client=TestClient(create_app(tmp_path))
    dashboard=client.get('/student-dashboard',params={'school':'NTU'}).json()
    assert sum(p['quota'] is None for p in dashboard['partner_universities'])==274
    assert sum(p['quota']=='0 名' for p in dashboard['partner_universities'])==6
    workflow=client.get('/application-workflow',params={'school':'明斯特大學','home_school':'國立臺灣大學','academic_year':'116'}).json()
    assert workflow['review_status']=='pending_review' and workflow['published_at'] is None
    assert all(not step['deadline_reminder_eligible'] for step in workflow['steps'])


def test_reapplying_updates_is_idempotent_and_preserves_unrelated_data(tmp_path):
    shutil.copytree(BUNDLE,tmp_path/'bundle')
    bundle=tmp_path/'bundle'
    before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in bundle.iterdir() if p.is_file()}
    apply_official_changes(bundle)
    # The dated completion overlay follows the historical portal replay.
    from exchange_info.ntu_completion import apply_completion
    apply_completion(bundle)
    after={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in bundle.iterdir() if p.is_file()}
    assert before==after
    ledger={r['portal_id']:r for r in json.loads((bundle/'verification_status.json').read_text())}
    assert ledger['107']['fields']['deadlines']['status']=='conflict'
    assert ledger['62']['fields']['courses']['reviewed_partial_value']['affected_programme']=='Medicine'
    observation=ledger['1200']['fields']['calendar']['official_portal_observations'][0]
    assert observation['evidence_academic_year']=='2027-2028'
    assert not observation['selection_rule_confirmed']
    assert all(not r['full_116_1_information_confirmed'] for r in ledger.values())
