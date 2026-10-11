"""Annual dates, unversioned exchange rules and private forms stay distinct."""
import json

from exchange_info.ccu_sources import BUNDLE
from exchange_info.ccu_student_view import fetch_ccu_partner_universities


def load(name):
    return json.loads((BUNDLE / name).read_text())


def school(page):
    return next(r for r in load("completion-reviewed-fields.json")["schools"] if r["ccu_page"] == page)


def test_bfsu_explicit_2022_dates_and_originals_stay_historical():
    fields = school(17)["host_fields"]
    for key in ["nomination_deadline", "application_deadline", "documents", "application_forms", "arrival"]:
        assert fields[key]["status"] == "reference_only"
        assert all("2022" in e["academic_year"] for e in fields[key]["evidence"])
    assert "2022-04-10至05-20" in fields["nomination_deadline"]["value"]
    assert "2022-04-10至05-31" in fields["application_deadline"]["value"]
    assert "1–4" in fields["documents"]["value"] and "5–6" in fields["documents"]["value"]
    assert "未取得" in fields["application_forms"]["value"]


def test_oneonta_recurring_deadline_is_not_a_verified_2027_reminder():
    fields = school(117)["host_fields"]
    assert fields["application_deadline"]["status"] == "needs_confirmation"
    assert "未標" in fields["application_deadline"]["evidence"][0]["academic_year"]
    assert fields["nomination_deadline"]["status"] == "missing"
    assert fields["host_tuition"]["status"] == "missing"  # No application fee is not tuition exemption.
    assert "iBT61" in fields["language"]["value"]
    assert "F-1最低12credits" in fields["course_restrictions"]["value"]


def test_oneonta_annual_calendar_preserves_conflicting_orientation():
    fields = school(117)["host_fields"]
    assert fields["academic_calendar"]["status"] == "verified_current"
    assert "01-25至05-14" in fields["academic_calendar"]["value"]
    assert "05-17至21" in fields["academic_calendar"]["value"]
    assert fields["arrival"]["status"] == "conflict"
    assert "01-21至23" in fields["arrival"]["value"] and "22–23" in fields["arrival"]["value"]
    assert "Spring2026" in fields["academic_calendar"]["value"]


def test_oneonta_seven_month_insurance_is_not_a_spring_housing_or_tuition_quote():
    fields = school(117)["host_fields"]
    assert fields["insurance"]["status"] == "verified_current"
    assert "1396.28" in fields["insurance"]["value"] and "共7月" in fields["insurance"]["value"]
    assert fields["costs"]["status"] == "needs_confirmation"
    assert fields["housing"]["status"] == "needs_confirmation"
    assert "不强制套交換" in fields["housing"]["value"]


def test_oneonta_personal_forms_require_explicit_access_evidence():
    forms = school(117)["host_fields"]["application_forms"]
    assert forms["research_classification"] == "personal_access_required"
    assert "After signing in" in forms["access_requirement_evidence"][0]["excerpt"]
    assert "未註冊/登入/填送" in forms["value"]


def test_new_receiving_rules_do_not_open_home_reference_choices():
    partners = {p.source_pages[0]: p for p in fetch_ccu_partner_universities()}
    for page in [17, 117]:
        p = partners[page]
        assert p.availability_status == "not_open" and p.application_window_status == "closed"
        assert p.quota is None and p.eligibility is None and p.language_requirement is None
        assert not p.partner_exchange_details
        ref = json.loads(p.reference_data["ccu_completion"])["reference_host_fields"]
        assert ref["application_deadline"]["status"] != "verified_current"


def test_refugee_and_degree_screening_does_not_promote_ordinary_exchange():
    readings = {r["source_id"]: r for r in load("completion-eighth-reading-input.json")}
    assert readings["p39-host_entry-2"]["disposition"] == "distinct_population_refugees"
    assert readings["p109-life-1"]["disposition"] == "distinct_population_refugees"
    assert readings["p73-host_entry-2"]["disposition"] == "degree_programme_exclusion"
    assert "rest unclaimed" in readings["p73-host_entry-2"]["review_extent"]
    assert not readings["p73-host_entry-2"]["full_visible_read"]
