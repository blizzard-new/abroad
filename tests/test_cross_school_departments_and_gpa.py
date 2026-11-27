"""Regression tests for 71-school department directories, custom department fallback, and 4.0/4.3 GPA scale support."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from cgu_catalogue_fixture import fixed_cgu_catalogue
from fastapi.testclient import TestClient

from exchange_info.advisor import build_advisor_plan
from exchange_info.api import create_app
from exchange_info.models import AdvisorProfile
from exchange_info.university_registry import SUPPORTED_UNIVERSITIES

STATIC_DIR = Path(__file__).parents[1] / "src" / "exchange_info" / "static"


def _load_academic_units() -> dict:
    script = r"""
    const fs = require('node:fs');
    const path = require('node:path');
    const dir = process.argv[1];
    global.window = {};
    for (const file of ['academic-units.js', 'ccu-academic-units.js', 'tku-academic-units.js']) {
      eval(fs.readFileSync(path.join(dir, file), 'utf8'));
    }
    console.log(JSON.stringify(window.UniWayAcademicUnits));
    """
    out = subprocess.check_output(
        ["node", "-e", script, str(STATIC_DIR.resolve())],
        text=True,
        encoding="utf-8",
    )
    return json.loads(out)


def test_all_directory_universities_cover_every_registered_college_and_source_url() -> None:
    units = _load_academic_units()
    assert len(SUPPORTED_UNIVERSITIES) == 71

    for university in SUPPORTED_UNIVERSITIES:
        entry = units.get(university.school_name)
        if entry is None:
            # Schools without a bundled directory fall back to direct text entry (#advisor-department-text).
            assert university.id in {"ntu", "ncu"}
            continue
        source_url = entry.get("sourceUrl") or ""
        assert source_url.startswith("http"), f"{university.id} missing valid sourceUrl"
        colleges_map = entry.get("colleges") or {}
        for college in university.colleges:
            departments = colleges_map.get(college)
            assert departments, f"{university.id} ({university.school_name}) college '{college}' has no departments"

    ccu_colleges = units["國立中正大學"]["colleges"]
    assert "環境工程研究所" in ccu_colleges["工學院"]
    assert "電訊傳播研究所" in ccu_colleges["社會科學院"]
    assert "高階主管法律碩士在職專班" in ccu_colleges["法學院"]
    assert "法學院高階主管法律" not in ccu_colleges["法學院"]
    assert "高齡者教育研究所" in ccu_colleges["教育學院"]
    assert "紫荊不分系學士學位學程" in ccu_colleges["文學院"]


def test_custom_department_option_and_gpa_scale_controls_work_across_schools() -> None:
    script = r"""
    const assert = require('node:assert/strict');
    const fs = require('node:fs');
    const path = require('node:path');
    const staticDir = process.argv[1];
    const window = {};
    for (const file of ['academic-units.js', 'ccu-academic-units.js', 'tku-academic-units.js']) {
      eval(fs.readFileSync(path.join(staticDir, file), 'utf8'));
    }
    const source = fs.readFileSync(path.join(staticDir, 'app.js'), 'utf8');

    global.Option = class Option {
      constructor(label, value) {
        this.label = label;
        this.textContent = label;
        this.value = value;
        this.dataset = {};
      }
    };

    const elements = new Map();
    const makeEl = (id) => ({
      id,
      value: '',
      hidden: false,
      disabled: false,
      max: '4.3',
      placeholder: '',
      textContent: '',
      href: '',
      dataset: {},
      options: [],
      add(opt) { this.options.push(opt); },
      querySelector() { return { disabled: false }; },
      querySelectorAll() { return []; },
    });
    const $ = (sel) => {
      if (!elements.has(sel)) elements.set(sel, makeEl(sel.slice(1)));
      return elements.get(sel);
    };
    const document = { querySelectorAll: () => [] };
    const fillSelect = (selector, values, placeholder, selected = '') => {
      const el = $(selector);
      el.options = [new Option(placeholder, ''), ...values.map((v) => new Option(v, v))];
      el.value = el.options.some((o) => o.value === selected) ? selected : '';
    };

    const state = {
      homeSchool: '國立中正大學',
      supportedUniversities: [{ school_name: '國立中正大學', colleges: ['工學院', '法學院'] }],
      dashboard: {
        school_name: '國立中正大學',
        academic_score_minimum: 70,
        academic_gpa_minimum: 3.0,
        academic_score_rule: '歷年在校GPA至少3.0',
        selection_rules: { academic_policy: 'percentage', accepts_academic_gpa: true, accepts_class_rank: false },
      },
      eligibilityProfile: { gpaScale: '4' },
    };
    const activeHomeSchool = () => state.homeSchool;
    const activeUniversityProfile = () => state.supportedUniversities[0];
    const homeSelectionRules = () => state.dashboard?.selection_rules || {};

    for (const fn of ['departmentField', 'renderDepartmentOptions', 'renderAcademicFields']) {
      const match = source.match(new RegExp('^function ' + fn + '\\([^]*?^}', 'm'));
      assert.ok(match, 'Missing function ' + fn);
      eval(match[0]);
    }

    // 1. Listed department selection works normally; custom input stays hidden.
    $('#advisor-college').value = '工學院';
    renderDepartmentOptions('advisor', '資訊工程學系', { allowCustom: true });
    assert.equal($('#advisor-department').disabled, false);
    assert.equal($('#advisor-department').value, '資訊工程學系');
    assert.equal($('#advisor-department-text').hidden, true);
    assert.equal(departmentField('advisor'), $('#advisor-department'));
    assert.ok($('#advisor-department').options.some((o) => o.value === '__custom__'));

    // 2. Saved unlisted department restores into __custom__ + visible text input.
    renderDepartmentOptions('advisor', '跨院新興半導體博士班', { allowCustom: true });
    assert.equal($('#advisor-department').value, '__custom__');
    assert.equal($('#advisor-department-text').hidden, false);
    assert.equal($('#advisor-department-text').disabled, false);
    assert.equal($('#advisor-department-text').value, '跨院新興半導體博士班');
    assert.equal(departmentField('advisor'), $('#advisor-department-text'));

    // 3. Switching college without custom resets catalog selection cleanly.
    $('#advisor-college').value = '法學院';
    renderDepartmentOptions('advisor', '資訊工程學系', { allowCustom: false });
    assert.equal($('#advisor-department').value, '');
    assert.equal($('#advisor-department-text').hidden, true);

    // 4. GPA 4.0 vs 4.3 scale updates max & placeholder for CCU and FCU, while hiding scale on NTU and hiding GPA on CGU.
    $('#advisor-gpa-scale').value = '';
    renderAcademicFields();
    assert.equal($('#advisor-gpa-field').hidden, false);
    assert.equal($('#advisor-gpa-scale-field').hidden, false);
    assert.equal($('#advisor-gpa-scale').value, '4');
    assert.equal($('#advisor-academic-gpa').max, '4.0');
    assert.match($('#advisor-academic-gpa').placeholder, /4\.0/);

    $('#advisor-gpa-scale').value = '4.3';
    renderAcademicFields();
    assert.equal($('#advisor-academic-gpa').max, '4.3');
    assert.match($('#advisor-academic-gpa').placeholder, /4\.3/);

    // FCU (gpa_or_rank on non-NTU school) hides percentage, shows GPA + scale selector + rank without hardcoding NTU 4.3 label.
    state.homeSchool = '逢甲大學';
    state.dashboard = {
      school_name: '逢甲大學',
      academic_score_minimum: null,
      academic_gpa_minimum: 3.0,
      selection_rules: { academic_policy: 'gpa_or_rank', accepts_academic_gpa: true, accepts_class_rank: true },
    };
    renderAcademicFields();
    assert.equal($('#advisor-percent-field').hidden, true);
    assert.equal($('#advisor-gpa-field').hidden, false);
    assert.equal($('#advisor-gpa-scale-field').hidden, false);
    assert.equal($('#advisor-rank-field').hidden, false);
    assert.doesNotMatch($('#advisor-gpa-label').textContent, /4\.3制/);

    // CGU (accepts_academic_gpa=false) hides GPA & scale selector.
    state.homeSchool = '長庚大學';
    state.dashboard = {
      school_name: '長庚大學',
      academic_score_minimum: 70,
      academic_gpa_minimum: null,
      selection_rules: { academic_policy: 'percentage', accepts_academic_gpa: false, accepts_class_rank: false },
    };
    renderAcademicFields();
    assert.equal($('#advisor-gpa-field').hidden, true);
    assert.equal($('#advisor-gpa-scale-field').hidden, true);
    assert.equal($('#advisor-gpa-converter-row').hidden, true);
    """
    result = subprocess.run(
        ["node", "-e", script, str(STATIC_DIR.resolve())],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0, result.stderr


def test_dashboard_selection_rules_expose_gpa_and_rank_capabilities_across_schools(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("exchange_info.api.create_cgu_catalogue", fixed_cgu_catalogue(lambda: []))
    with TestClient(create_app(tmp_path)) as client:
        cgu = client.get("/student-dashboard", params={"school": "cgu"}).json()
        assert cgu["selection_rules"]["accepts_academic_gpa"] is False
        assert cgu["selection_rules"]["accepts_class_rank"] is False

        ccu = client.get("/student-dashboard", params={"school": "ccu"}).json()
        assert ccu["selection_rules"]["accepts_academic_gpa"] is True
        assert "4.3 或 4.0 制" in ccu["academic_score_rule"]

        fcu = client.get("/student-dashboard", params={"school": "fcu"}).json()
        assert fcu["selection_rules"]["accepts_academic_gpa"] is True

        nthu = client.get("/student-dashboard", params={"school": "nthu"}).json()
        assert nthu["selection_rules"]["accepts_academic_gpa"] is True
        assert nthu["selection_rules"]["accepts_class_rank"] is True

        ncku = client.get("/student-dashboard", params={"school": "ncku"}).json()
        assert ncku["selection_rules"]["accepts_academic_gpa"] is False
        assert ncku["selection_rules"]["accepts_class_rank"] is True

    from exchange_info.fcu_student_view import build_fcu_student_dashboard
    fcu_dash = build_fcu_student_dashboard(partner_universities=[])
    plan = build_advisor_plan(
        AdvisorProfile(school_name="逢甲大學", college="商學院", department="會計學系", degree_level="大學部", academic_gpa=3.6),
        fcu_dash,
        [],
        [],
        [],
    )
    assert any("GPA 3.6" in line for line in plan.qualification)
    assert not any("學業平均尚未填寫" in line for line in plan.qualification)
