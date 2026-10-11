from cgu_catalogue_fixture import fixed_cgu_catalogue
import json
import subprocess
from pathlib import Path

from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.university_registry import CGU, NTPU


def test_universities_expose_colleges_without_partner_data(tmp_path, monkeypatch):
    monkeypatch.setattr('exchange_info.api.create_cgu_catalogue', fixed_cgu_catalogue(lambda: []))
    with TestClient(create_app(tmp_path)) as client:
        response = client.get("/universities")
    assert response.status_code == 200
    by_id = {row["id"]: row for row in response.json()}
    assert by_id["cgu"]["colleges"] == ["醫學院", "工學院", "管理學院", "智慧運算學院"]
    assert by_id["ntpu"]["colleges"] == list(NTPU.colleges)
    assert len(by_id["ntpu"]["colleges"]) == 7


def test_college_selects_ignore_partner_notes_and_follow_home_university():
    profiles = [
        {"school_name": university.school_name, "colleges": list(university.colleges)}
        for university in (CGU, NTPU)
    ]
    script = r'''
    const assert = require('node:assert/strict');
    const fs = require('node:fs');
    const source = fs.readFileSync(process.argv[1], 'utf8');
    const profiles = JSON.parse(process.argv[2]);
    const DEFAULT_HOME_SCHOOL = profiles[0].school_name;
    const window = {UniWayAcademicUnits: {}};
    const dirtyScope = '制、春季班)、大三以上或研究生、社會科學學院及公共事務學院、最後錄取結果仍須視接待學校審查結果而定';
    const state = {
      homeSchool: profiles[0].school_name, supportedUniversities: profiles,
      dashboard: {partner_universities: [{colleges: dirtyScope, country: '日本', degree_levels: '大學部', school_name: '合作校'}]},
      college: '春季班)', country: '', degree: '', availability: '', applications: [],
      eligibilityProfile: {college: '制'},
    };
    const calls = new Map(), elements = new Map();
    const $ = selector => {
      if (!elements.has(selector)) elements.set(selector, {value: '', id: selector.slice(1), dataset: {}, options: []});
      return elements.get(selector);
    };
    const fillSelect = (selector, values, placeholder, selected = '') => calls.set(selector, {values, selected});
    const fillRegionSelect = () => {};
    const fillCountrySelect = () => {};
    const renderAcademicFields = () => {};
    const renderApplicationPeriodOptions = () => {};
    const renderAdvisorAccessState = () => {};
    for (const name of ['normalize', 'activeHomeSchool', 'activeUniversityProfile',
      'homeCollegeOptions', 'homeCollegeValue', 'renderDepartmentOptions', 'unique', 'splitOptions', 'partnerAvailabilityMeta',
      'renderPartnerFilters', 'renderEligibilityOptions', 'restoreEligibilityForm', 'renderAdvisorForm']) {
      const match = source.match(new RegExp('^function ' + name + '\\([^]*?^}', 'm'));
      assert.ok(match, 'Missing production function: ' + name);
      eval(match[0]);
    }
    const renderAll = () => {
      renderPartnerFilters(); renderEligibilityOptions(); restoreEligibilityForm(); renderAdvisorForm();
    };
    for (const profile of profiles) {
      state.homeSchool = profile.school_name;
      state.college = '春季班)';
      renderAll();
      for (const selector of ['#advisor-college', '#college-filter']) {
        assert.deepEqual(calls.get(selector).values, profile.colleges);
      }
      assert.equal(state.college, '');
      assert.equal(calls.get('#advisor-college').selected, '');
      state.eligibilityProfile = {college: profile.colleges[0]};
      renderAll();
      assert.equal(calls.get('#advisor-college').selected, profile.colleges[0]);
      state.eligibilityProfile = {college: '制'};
    }
    // School changes cannot retain the previous school's college.
    state.homeSchool = profiles[0].school_name;
    state.eligibilityProfile = {college: '法律學院'};
    renderAll();
    assert.equal(calls.get('#advisor-college').selected, '');
    // Missing directory metadata must never fall back to noisy partner text.
    state.supportedUniversities = [];
    renderAll();
    assert.deepEqual(calls.get('#advisor-college').values, []);
    assert.deepEqual(calls.get('#college-filter').values, []);
    console.log('college option regressions passed');
    '''
    result = subprocess.run(
        ["node", "-e", script, str(Path("src/exchange_info/static/app.js").resolve()),
         json.dumps(profiles, ensure_ascii=False)],
        capture_output=True, text=True, encoding="utf-8",
    )
    assert result.returncode == 0, result.stderr
