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
