import json
from datetime import datetime
from pathlib import Path

from exchange_info.ccu_host_life import SERVICES
from exchange_info.models import DestinationProfile
from exchange_info.school_content import complete_destination_profile


def test_host_services_preserve_term_specific_evidence_and_partner_scope(tmp_path: Path):
    reviews = json.loads(SERVICES.read_text())["profiles"]
    profiles = {profile.school_name: profile for line in SERVICES.with_name("destination_profiles.jsonl").read_text().splitlines()
                if (profile := DestinationProfile.model_validate_json(line))}
    assert len(reviews) == len({row["school_name"] for row in reviews}) == 16
    for row in reviews:
        baseline = profiles[row["school_name"]]
        assert baseline.coverage_status == "needs_confirmation"
        updated = complete_destination_profile(baseline, tmp_path, locations={})
        section = updated.student_guide_sections[0]
        assert updated.coverage_status == "official_partial"
        assert section.key == "host_life_service" and section.summary == row["summary"]
        assert section.points == [row["next_step"]] and section.source_urls
        assert all(url.startswith("https://") and "ccu.edu.tw" not in url for url in section.source_urls)
        assert set(section.source_urls) <= {s.source_url for s in updated.sources}
        assert (updated.housing_summary, updated.student_guide_sections[1:]) == (baseline.housing_summary, baseline.student_guide_sections)
        assert complete_destination_profile(updated, tmp_path, locations={}) == updated
    newer = baseline.model_copy(update={"last_checked": datetime(2026, 12, 1)})
    assert complete_destination_profile(newer, tmp_path, locations={}).student_guide_sections == baseline.student_guide_sections
    other_home = baseline.model_copy(update={"home_university": "國立臺北大學"})
    assert all(s.key != "host_life_service" for s in complete_destination_profile(other_home, tmp_path, locations={}).student_guide_sections)
