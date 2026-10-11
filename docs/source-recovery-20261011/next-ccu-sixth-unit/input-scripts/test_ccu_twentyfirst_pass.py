"""CCU current multilingual policies, private later forms and scoped mirrors."""

import hashlib
import json

from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.ccu_documents import reviewed_documents
from exchange_info.ccu_overseas import reviewed_rows
from exchange_info.ccu_sources import BUNDLE, HOME
from exchange_info.ccu_student_view import fetch_ccu_partner_universities


def read(name):
    return json.loads((BUNDLE / name).read_text())


def partner(page):
    return next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == page)


def test_ryukoku_actual_2027_translations_keep_the_arrival_date_conflict():
    field = reviewed_rows()[32]["fields"]["arrival"]
    assert field["status"] == "conflict"
    assert "9/10" in field["value"] and "3/25" in field["value"]
    cn = read("overseas_sources/p32-r21-a4220ed681.json")
    jp = read("overseas_sources/p32-r21-c29dc98b6f.json")
    assert "2027 年 9 月 10 日" in cn["text_pages"][2]
    assert "2027 年 3 月 25 日" in cn["text_pages"][2]
    assert "2027 年 3 月 25 日" in jp["text_pages"][2]
    assert all(e["status"] == "conflict" for e in field["evidence"])
    assert any(e["source_pages"] == [3] and "9 月 10 日" in e["excerpt"] for e in field["evidence"])


def test_ryukoku_all_applicants_have_self_assessment_and_spot_without_signature_invention():
    items = reviewed_documents()[32]["requirements"]
    for index in [4, 5]:
        item = items[index]
        assert not item["conditional"] and item["stage"] == "student_application"
        assert "全體交換生" in item["requirement"]["name"]
        assert any(e["source_id"] == "p32-r21-c29dc98b6f" and e["source_pages"] == [3] for e in item["evidence"])
    assert items[4]["requirement"]["signatures"] == []
    assert "不額外要求" in items[4]["applicability_note"]
    language = reviewed_rows()[32]["fields"]["language"]["value"]
    assert "建議300小時" in language and "硬門檻" in language


def test_ryukoku_nasic_forms_remain_conditional_later_and_private(tmp_path):
    client = TestClient(create_app(tmp_path))
    data = client.get("/application-center/catalog", params={"school": HOME, "target_school": partner(32).school_name}).json()
    items = [x for x in data["items"] if "NASIC" in x["name"]]
    assert len(items) == 2
    assert all(x["conditional"] and x["stage"] == "after_dorm_assignment" for x in items)
    assert all(not x["download_available"] for x in items)
    pledge = next(x for x in items if "誓約書" in x["name"])
    assert pledge["signatures"] == ["學生"]
    assert "後發" in pledge["applicability_note"]


def test_dit_certificate_and_language_ability_are_separate_conflicting_rules():
    fields = reviewed_rows()[101]["fields"]
    assert fields["language"]["status"] == fields["documents"]["status"] == "conflict"
    assert "不要求" in fields["language"]["value"]
    assert "能力B1–C1與證書要求分開" in fields["language"]["value"]
    assert any("Language certificates are not required" in e["excerpt"] for e in fields["language"]["evidence"])
    grade = next(x for x in reviewed_documents()[101]["requirements"] if "exam grade sheet" in x["requirement"]["name"])
    assert grade["conditional"] and grade["applicability_status"] == "needs_confirmation"


def test_hufs_archived_general_essay_and_bank_rules_are_not_current_requirements():
    source = read("overseas_sources/p47-r21-68e89a4601.json")
    assert "/10-deleted-page/" in source["source_url"]
    assert source["content_applicability"] == "reference_only"
    items = reviewed_documents()[47]["requirements"]
    assert "未載最少頁數" in items[1]["requirement"]["name"]
    assert "封存" in items[1]["applicability_note"]
    assert items[9]["stage"] == "after_application"
    assert not items[9]["requirement"]["stamps"]
    assert any(e["status"] == "reference_only" for e in items[9]["evidence"])
    assert reviewed_rows()[47]["fields"]["documents"]["status"] == "verified_current"


def test_fhnw_business_required_and_conditional_later_documents_are_distinct():
    items = reviewed_documents()[104]["requirements"]
    assert len(items) == 3
    grant = next(x for x in items if "獎助" in x["requirement"]["name"])
    assert grant["conditional"] and grant["stage"] == "post_offer"
    assert grant["requirement"]["official_form_url"] is None
    assert "非人人保證" in grant["condition"]
    initial = [x for x in items if x["stage"] == "student_application"]
    assert len(initial) == 2 and all(not x["conditional"] for x in initial)
    assert any("Learning Agreement" in x["requirement"]["name"] for x in initial)
    assert all(x["applicability_status"] == "needs_confirmation" for x in items)


def test_sdu_housing_city_reply_windows_do_not_become_one_universal_deadline():
    fields = reviewed_rows()[89]["fields"]
    value = fields["housing_deadline"]["value"]
    assert "Esbjerg住房offer回覆7日" in value
    assert "Kolding住房offer回覆7日" in value
    assert "Odense住房offer回覆6日" in value
    item = next(x for x in reviewed_documents()[89]["requirements"] if "WelcomeLetter" in x["requirement"]["name"])
    assert item["stage"] == "after_dorm_assignment" and item["conditional"]
    assert item["requirement"]["official_form_url"] is None
    assert "MedicineBA/MA授課全Danish" in fields["course_restrictions"]["value"]


def test_proven_same_body_rechecks_preserve_all_prior_snapshots():
    report = read("twentyfirst-source-review.json")
    assert report["acquisition_count"] == len(report["source_reviews"]) == 84
    assert report["new_source_count"] == 43
    assert len(report["same_body_rechecks"]) == 11
    assert len(report["prior_snapshot_hashes"]) == 876
    for sid, expected in report["prior_snapshot_hashes"].items():
        assert hashlib.sha256((BUNDLE / "overseas_sources" / (sid + ".json")).read_bytes()).hexdigest() == expected
    for item in report["same_body_rechecks"]:
        assert item["same_extracted_text"] and item["text_sha256"] and item["final_url"]
    sdu = next(x for x in report["same_body_rechecks"] if x["candidate_source_id"] == "p89-r21-04ca22ff09")
    assert sdu["same_original_bytes"] and sdu["existing_source_id"] == "p89-mirror"


def test_old_housing_guide_and_outgoing_tables_do_not_become_current_incoming_data():
    guide = read("overseas_sources/p87-r21-f68abae9a3.json")
    assert guide["content_applicability"] == "reference_only"
    assert "DMG 2025" in guide["text_pages"][1]
    assert hashlib.sha256((BUNDLE / guide["bundled_file"]).read_bytes()).hexdigest() == guide["sha256"]
    report = read("twentyfirst-source-review.json")
    table = next(x for x in report["source_reviews"] if "6aabc2e77372f1789641447.pdf" in x["url"])
    assert table["disposition"] == "excluded_other_recipient"
    assert "CCU為目的校" in table["review_note"]
    assert not (BUNDLE / "overseas_sources/p80-r21-98769c508f.json").exists()
