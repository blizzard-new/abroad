import json
import subprocess
from pathlib import Path

import pytest
from pydantic import ValidationError

from exchange_info.discovery import DiscoveryWorkspace, localize_experience_digest
from exchange_info.models import StudentExperienceDigest, StudentExperienceSource
from test_account_workspace_api import _client, _workspace


def test_personal_selection_roundtrip_and_legacy_client_preservation(tmp_path):
    client, headers = _client(tmp_path)
    payload = _workspace()
    payload["discovery"] = {
        "school_preferences": {"林肯大學 Lincoln University": {"interest": 5, "note": "住宿是主要考量"}},
        "preference_order": ["林肯大學 Lincoln University"],
        "saved_experiences": {"article": {"school_name": "林肯大學 Lincoln University", "source_url": "https://www.lincoln.ac.nz/student-story", "summary_zh": "可以騎車上學。"}},
        "recent_views": [{"kind": "school", "school_name": "林肯大學 Lincoln University", "viewed_at": "2026-09-24T12:00:00Z"}],
    }
    saved = client.put("/account/workspace", headers=headers, json=payload)
    assert saved.status_code == 200, saved.text
    retrieved = client.get("/account/workspace", headers=headers).json()["workspace"]
    assert retrieved["discovery"]["school_preferences"]["林肯大學 Lincoln University"]["note"] == "住宿是主要考量"
    assert retrieved["discovery"]["saved_experiences"]["article"]["summary_zh"] == "可以騎車上學。"
    assert client.get("/account/workspace?home_school=國立臺北大學", headers=headers).json()["workspace"]["discovery"]["preference_order"] == []
    old_client = _workspace()
    old_client["revision"] = retrieved["revision"]
    response = client.put("/account/workspace", headers=headers, json=old_client)
    assert response.status_code == 200
    assert response.json()["workspace"]["discovery"] == retrieved["discovery"]
    # An explicit empty discovery object still intentionally clears this user's data.
    old_client.update(revision=response.json()["workspace"]["revision"], discovery={})
    assert client.put("/account/workspace", headers=headers, json=old_client).json()["workspace"]["discovery"]["school_preferences"] == {}


@pytest.mark.parametrize("payload", [
    {"school_preferences": {"school": {"interest": 9}}},
    {"school_preferences": {"school": {"note": "x" * 1001}}},
    {"saved_experiences": {"a": {"school_name": "school", "source_url": "javascript:alert(1)"}}},
    {"saved_experiences": {"a": {"school_name": "school"}}},
    {"preference_order": ["a"] * 31},
])
def test_discovery_bounds_and_link_validation(payload):
    with pytest.raises(ValidationError):
        DiscoveryWorkspace.model_validate(payload)


def test_translation_keeps_original_and_does_not_invent_exchange_term(tmp_path, monkeypatch):
    source = StudentExperienceSource(school_name="測試學校", title="Student story", source_url="https://example.edu/story", source_type="article", platform="official", summary="I cooked in the residence kitchen.", themes=["food"], theme_summaries={"food": "I cooked in the residence kitchen."}, content_hash="fixture", published_at="2025-10-01")
    monkeypatch.setattr("exchange_info.discovery.cached_translation", lambda *args: ("我在宿舍廚房煮飯。", "machine"))
    digest = localize_experience_digest(StudentExperienceDigest(school_name="測試學校", sources=[source]), tmp_path)
    translated = digest.sources[0]
    assert translated.summary_zh == "我在宿舍廚房煮飯。"
    assert translated.original_summary == source.summary
    assert translated.exchange_term is None
    assert translated.translation_status == "machine"
    monkeypatch.setattr("exchange_info.discovery.cached_translation", lambda *args: None)
    pending = localize_experience_digest(StudentExperienceDigest(school_name="測試學校", sources=[source]), tmp_path).sources[0]
    assert pending.summary_zh == ""
    assert pending.original_summary == source.summary


def test_filter_handles_unknown_scales_alternatives_and_separate_programs():
    module = Path("src/exchange_info/static/discovery-core.js").resolve()
    script = r'''
    const assert = require('node:assert/strict');
    const D = require(process.argv[1]);
    const p = {eligibility:'IELTS 6.5; GPA 3.0 / 4.0', degree_levels:'大學部', study_period:'春季或秋季'};
    const c = {test:'ielts',score:'7',grade:'3.5',scale:'4',degree:'undergraduate',term:'fall'};
    assert.equal(D.assess(p,c).status,'match');
    assert.equal(D.assess(p,{...c,score:'5'}).status,'mismatch');
    assert.equal(D.assess(p,{...c,scale:'4.3'}).status,'unknown');
    assert.equal(D.assess({...p,study_period:'一學期'},c).status,'unknown');
    assert.equal(D.assess({...p,eligibility:'JLPT N2'}, {test:'jlpt',score:'1'}).status,'match');
    assert.equal(D.assess({...p,eligibility:'JLPT N2'}, {test:'jlpt',score:'3'}).status,'mismatch');
    assert.equal(D.assess({...p,eligibility:'IELTS 6.5 or TOEFL iBT 79'}, {test:'ielts',score:'6'}).status,'unknown');
    assert.equal(D.assess({...p,eligibility:'IELTS 6.5，各科 6.0'}, {test:'ielts',score:'7'}).status,'unknown');
    assert.equal(D.assess({...p,eligibility:'IELTS 6.5 and JLPT N2'}, {test:'ielts',score:'7'}).status,'unknown');
    assert.equal(D.assess({...p,availability_status:'agreement_only'},c).status,'unknown');
    const multiple = {program_options:[{eligibility:'IELTS 7.0',degree_levels:'大學部'},{eligibility:'IELTS 5.5',degree_levels:'研究所'}]};
    assert.equal(D.assess(multiple,{test:'ielts',score:'6',degree:'undergraduate'}).status,'mismatch');
    assert.equal(D.assess({...p,student_summary_zh:{eligibility_points:['IELTS 9.0']},program_options:[{eligibility:'IELTS 6.0'}]}, {test:'ielts',score:'7'}).status,'match');
    assert.equal(D.safeUrl('javascript:alert(1)'), '');
    assert.equal(D.sanitize({recent_views:[{kind:'experience',school_name:'A',source_url:'javascript:x'}]}).recent_views.length,0);
    console.log('candidate edge cases passed');
    '''
    result = subprocess.run(["node", "-e", script, str(module)], capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0, result.stderr


def test_picking_only_a_language_test_or_a_term_still_tells_schools_apart():
    """The explore page's two dropdowns send a test (no score) or a term; the data names the intakes in the schedule."""
    module = Path("src/exchange_info/static/discovery-core.js").resolve()
    script = r'''
    const assert = require('node:assert/strict');
    const D = require(process.argv[1]);
    const school = {eligibility:'一般組 IELTS 6.0 或 TOEFL iBT 79', application_deadline:'秋季班：4月30日 春季班：10月30日', study_period:'1學期', degree_levels:'大學部'};
    // A test with no score: listed, not listed, or left open by "equivalent" and by silence.
    assert.equal(D.assess(school,{test:'ielts'}).status,'match');
    assert.equal(D.assess(school,{test:'toefl'}).status,'match');
    assert.equal(D.assess(school,{test:'jlpt'}).status,'mismatch');
    assert.match(D.assess(school,{test:'jlpt'}).reasons[0], /只列 IELTS、TOEFL iBT，未列 日檢 JLPT/);
    assert.equal(D.assess({...school,eligibility:'IELTS 6.0 或同等英語成績'},{test:'toeic'}).status,'unknown');
    assert.equal(D.assess({...school,eligibility:'須先通過校內甄選'},{test:'jlpt'}).status,'unknown');
    assert.equal(D.assess({...school,eligibility:'日本語能力試驗 N2'},{test:'jlpt'}).status,'match');
    // A school whose open status is unconfirmed cannot be called a match, but it is still ranked as one.
    const pending = D.assess({...school,availability_status:'pending'},{test:'ielts'});
    assert.equal(pending.status,'unknown');
    assert.equal(pending.matched,true);
    assert.equal(D.assess({...school,availability_status:'pending'},{test:'jlpt'}).matched,false);
    // A score still goes through the threshold check.
    assert.equal(D.assess({...school,eligibility:'IELTS 6.5'},{test:'ielts',score:'7'}).status,'match');
    assert.equal(D.assess({...school,eligibility:'IELTS 6.5'},{test:'ielts',score:'5'}).status,'mismatch');
    // A term: study_period only says how long, so the intakes come from the schedule, by season words only.
    assert.equal(D.assess(school,{term:'fall'}).status,'match');
    assert.equal(D.assess(school,{term:'spring'}).status,'match');
    assert.equal(D.assess({...school,application_deadline:'春季班：10月30日'},{term:'fall'}).status,'mismatch');
    assert.equal(D.assess({...school,application_deadline:'春季班：10月30日'},{term:'spring'}).status,'match');
    assert.equal(D.assess({...school,application_deadline:'冬季學期／全學年：5 月 31 日；夏季學期：11 月 15 日'},{term:'spring'}).status,'match');
    assert.equal(D.assess({...school,application_deadline:'Winter Semester (本校第一學期)：4/30'},{term:'spring'}).status,'mismatch');
    assert.equal(D.assess({...school,application_deadline:'2027春季第3梯次：2026-09-20'},{term:'fall'}).status,'mismatch');
    // "Semester 1" starts in February in the southern hemisphere, so it says nothing about the season.
    assert.equal(D.assess({...school,application_deadline:'Semester 1 (February – June): 30 September'},{term:'fall'}).status,'unknown');
    assert.equal(D.assess({...school,application_deadline:'依當期公告'},{term:'fall'}).status,'unknown');
    assert.equal(D.assess({...school,student_summary_zh:{application_deadline:'春季班：10月30日'},application_deadline:''},{term:'fall'}).status,'mismatch');
    console.log('dropdown cases passed');
    '''
    result = subprocess.run(["node", "-e", script, str(module)], capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0, result.stderr
