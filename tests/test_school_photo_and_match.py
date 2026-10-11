"""Regressions for real school photo identities and incomplete match profiles."""

import json
import subprocess
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image

from exchange_info.school_image_collector import _read_existing_manifest


def test_school_photo_manifest_files_and_aliases():
    static = Path("src/exchange_info/static")
    records = _read_existing_manifest(static / "assets/school-images.json")
    assert len(records) >= 284
    for record in records.values():
        if record.status != "verified":
            continue
        path = static / urlparse(record.local_path).path.removeprefix("/static/")
        with Image.open(path) as image:
            image.verify()
        assert record.official_page_url.startswith("https://") or record.official_page_url.startswith("http://")
    for fragment in ["CHA University", "EIGSI Engineering School", "National Polytechnic Institute of Toulouse", "Wroc ław", "Tur ība"]:
        assert any(fragment in name for name in records)
    vsb = records["捷克俄斯特拉發科技大學 VSB – Technical University of Ostrava"]
    assert "4a217bb251ff05.jpg" in vsb.local_path


def test_match_missing_profile_fields_and_real_mismatches():
    source = Path("src/exchange_info/static/app.js").resolve()
    script = r'''
    const assert = require('node:assert/strict');
    const fs = require('node:fs');
    const source = fs.readFileSync(process.argv[1], 'utf8');
    const state = {eligibilityProfile: null, schoolImages: []};
    let schoolVisualSource = null, schoolVisualExact = new Map(), schoolVisualAliases = new Map();
    const coverageForSchool = () => null;
    const destinationProfileForSchool = () => null;
    const homeCollegeValue = value => ['工學院', '管理學院', '醫學院'].includes(value) ? value : '';
    const homeSelectionRules = () => ({partner_requirements_need_confirmation:false,pending_quota_planning:true});
    const partnerSummaryPoints = item => item.eligibility_points || [];
    for (const name of ['normalize', 'escapeHtml', 'academicScopeNeedsConfirmation', 'collegeMatches', 'degreeMatches', 'coupledAcademicScopeOptions', 'coupledAcademicScopeMatches', 'resolvedDegreeLevel', 'partnerDegreeScopeMatches',
      'languageThresholdFromPartner', 'partnerAvailabilityMeta', 'partnerMatch',
      'renderPartnerMatchExplanation', 'visualSchoolIdentity', 'visualCountryIdentity', 'visualSchoolAliases', 'schoolVisualRecordFor', 'schoolImageFor', 'renderSchoolPhoto']) {
      const match = source.match(new RegExp('^function ' + name + '\\([^]*?^}', 'm'));
      assert.ok(match, name); eval(match[0]);
    }
    const school = {school_name: '測試大學', country: '韓國', colleges: '四院皆可',
      degree_levels: '大學部', eligibility_points: ['TOEIC 700']};
    const empty = partnerMatch(school, {});
    assert.notEqual(empty.tone, 'blocked');
    assert.equal(empty.label, '條件待補齊');
    assert.ok(empty.risks.includes('尚未填寫學院'));
    const full = {college: '工學院', degree: '大學部', languageTest: 'toeic', languageScore: 800};
    assert.notEqual(partnerMatch(school, full).tone, 'blocked');
    for (const score of ['', 0, null, 'invalid']) {
      assert.notEqual(partnerMatch(school, {...full, languageScore: score}).tone, 'blocked');
    }
    assert.notEqual(partnerMatch(school, {...full, college: '春季班)'}).tone, 'blocked');
    const degree = partnerMatch(school, {...full, degree: '研究所'});
    assert.equal(degree.label, '學制範圍待確認');
    assert.ok(degree.risks.some(x => x.includes('研究所') && x.includes('大學部')));
    const language = partnerMatch(school, {...full, languageScore: 600});
    assert.equal(language.label, '語言分數未達門檻');
    assert.ok(language.risks.some(x => x.includes('600') && x.includes('700')));
    assert.equal(partnerMatch({...school, availability_status: 'agreement_only'}, full).label, '本期名額待確認');
    state.eligibilityProfile = full;
    assert.match(renderPartnerMatchExplanation(degree), /你的學制：研究所/);
    assert.match(renderPartnerMatchExplanation({...degree, risks: ['<script>']}), /&lt;script&gt;/);
    // Backend identity matches remain usable even when the manifest's label differs.
    assert.match(renderSchoolPhoto({...school, image_url: '/static/assets/schools/verified.jpg', image_status: 'verified'}), /src="\/static\/assets\/schools\/verified.jpg"/);
    assert.doesNotMatch(renderSchoolPhoto({...school, image_url: '/unverified.jpg', image_status: 'missing'}), /<img/);
    '''
    result = subprocess.run(["node", "-e", script, str(source)], capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0, result.stderr
