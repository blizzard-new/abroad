"""Requested general healthcare and handbook details retain year and stage limits."""

import json
import subprocess
from pathlib import Path

from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.ccu_overseas import destination_profile
from exchange_info.ccu_student_view import fetch_ccu_partner_universities

B = Path(__file__).resolve().parents[1] / "src/exchange_info/official_data/ccu"
HOME = "國立中正大學"


def read(name):
    return json.loads((B / name).read_text())


def partner(page):
    return next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == page)


def assert_life_render(profile, key, expected):
    """Render the real API profile through the CCU production life renderer."""
    script = r"""
    const assert=require('node:assert/strict'),fs=require('node:fs'),window={};
    eval(fs.readFileSync(process.argv[1],'utf8'));
    const profile=JSON.parse(fs.readFileSync(0,'utf8'));
    const section=profile.student_guide_sections.find(s=>s.key===process.argv[2]);
    section.summary+=' <script>unsafe()</script>';
    const escapeHtml=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
    const html=window.UniWayCcuDetails.renderProfileLife(profile,escapeHtml);
    assert.ok(html.includes('data-ccu-life-field="'+process.argv[2]+'"'));
    assert.ok(html.includes(process.argv[3]));assert.ok(html.includes('待確認'));
    assert.ok(html.includes('&lt;script&gt;unsafe'));assert.ok(!html.includes('<script>unsafe'));
    for(const url of section.source_urls) assert.ok(html.includes(escapeHtml(url)));
    """
    result = subprocess.run([
        "node", "-e", script, str(B.parents[1] / "static/ccu-partner-details.js"), key, expected,
    ], input=profile.model_dump_json(), capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr


def test_general_amu_insurance_is_pending_with_private_options_and_no_phd_substitution(tmp_path):
    amu = partner(95)
    insurance = amu.partner_exchange_details["insurance"]
    assert insurance.status == "needs_confirmation"
    assert "NFZ不是唯一強制方案" in insurance.value and "2020" in insurance.value
    assert all(e.status == "needs_confirmation" and "2027" in insurance.reason for e in insurance.evidence)
    assert {e.source_url for e in insurance.evidence} == {
        "https://amu.edu.pl/en/education/healthcare/general-insurance",
        "https://amu.edu.pl/en/education/healthcare/voluntary-insurance",
    }
    assert "投保手續，非初次交換申請附件" in insurance.value
    for source in read("twentyeighth-source-review.json")["source_reviews"]:
        raw = read("overseas_sources/" + source["source_id"] + ".json")
        assert raw["normal_tls_receipt"]["tls_verify"] and raw["http_status"] == 200
        assert raw["content_applicability"] == "needs_confirmation"
    profile = destination_profile(amu)
    health = next(s for s in profile.student_guide_sections if s.key == "healthcare_reference")
    assert "待確認" in health.caution and "2020" in health.summary
    assert any(url.endswith("/medical-services") for url in health.source_urls)
    assert_life_render(profile, "healthcare_reference", "NFZ")
    client = TestClient(create_app(tmp_path))
    flow = client.get("/application-workflow", params={"home_school": HOME, "school": amu.school_name})
    assert flow.status_code == 200
    life = next(s for s in flow.json()["steps"] if s["phase"] == "合作校行前與生活")
    assert any("一般投保與醫療服務參考" in text and "待確認" in text for text in life["details"])
    assert all("NFZ" not in d["name"] for step in flow.json()["steps"] for d in step["document_requirements"])


def test_mapua_passport_anchor_and_tor_are_pending_and_in_the_correct_stage(tmp_path):
    mapua = partner(83)
    row = next(r for r in read("partner-document-requirements.json") if r["ccu_page"] == 83)
    passport = next(d for d in row["requirements"] if d["requirement"]["name"].startswith("護照資料頁"))
    assert passport["applicability_status"] == "needs_confirmation"
    assert "停留結束後6月" in passport["requirement"]["name"]
    assert {p for e in passport["evidence"] if "international-handbook" in e["source_id"] for p in e["source_pages"]} == {18, 21}
    assert all(e["status"] == "needs_confirmation" for e in passport["evidence"] if "international-handbook" in e["source_id"])
    assert not any("TOR" in d["requirement"]["name"] for d in row["requirements"])
    client = TestClient(create_app(tmp_path))
    response = client.get("/application-workflow", params={"home_school": HOME, "school": mapua.school_name})
    assert response.status_code == 200
    steps = response.json()["steps"]
    before_return = next(s for s in steps if s["phase"] == "行前與返國")
    assert any("TOR" in text and "clearance" in text and "1–2週" in text and "待確認" in text for text in before_return["details"])
    application = steps[4]
    assert all("TOR" not in text for text in application["required_documents"])
    profile = destination_profile(mapua)
    section = next(s for s in profile.student_guide_sections if s.key == "return_preparation")
    assert "待確認" in section.caution and "非初次申請文件" in section.summary
    assert_life_render(profile, "return_preparation", "clearance")
