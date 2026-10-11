"""Official contact redirect, named destination, map viewport and mother boundary."""
import gzip
import hashlib
import json

from bs4 import BeautifulSoup

from exchange_info.ccu_sources import BUNDLE
from exchange_info.ccu_student_view import fetch_ccu_partner_universities


def read(name):
    return json.loads((BUNDLE / name).read_text())


def test_saintgits_contact_redirect_does_not_silently_become_an_engineering_page():
    record = read("completion_sources/p74-engineering-contact-followup.receipt.json")
    assert record["resolved_url"] == "https://saintgits.org/saintgits-design-school/contact-us/"
    stored = (BUNDLE / record["bundled_file"]).read_bytes()
    body = gzip.decompress(stored)
    assert hashlib.sha256(body).hexdigest() == record["sha256"]
    assert BeautifulSoup(body, "html.parser").find("a", href="https://goo.gl/maps/zxt3rGJ8S46DX3ws7")


def test_saintgits_destination_names_engineering_and_uses_marker_not_viewport_or_camera():
    point = read("campus-coordinate-review.json")["schools"]["74"]["field"]
    record = read("completion_sources/p74-engineering-official-map-marker.receipt.json")
    assert "Saintgits+College+of+Engineering+(Autonomous)" in record["resolved_url"]
    assert "!3d9.5100096!4d76.5513594" in record["resolved_url"]
    assert "@9.5100096,76.5491707" in record["resolved_url"]
    assert point["value"]["latitude"] == 9.5100096
    assert point["value"]["longitude"] == 76.5513594
    assert "camera GPS" in point["value"]["note"]
    assert point["value"]["precision"] == "representative"


def test_saintgits_runtime_keeps_mother_quota_and_closed_window():
    partner = next(p for p in fetch_ccu_partner_universities() if p.source_pages[0] == 74)
    assert partner.location.geocode_status == "verified"
    assert partner.location.longitude == 76.5513594
    assert partner.country == "印度"
    assert partner.availability_status == "open" and partner.quota_status == "published"
    assert partner.application_window_status == "closed"
    assert partner.quota == "2名"


def test_saintgits_general_point_does_not_clear_its_missing_host_fields():
    row = next(r for r in read("completion-reviewed-fields.json")["schools"] if r["ccu_page"] == 74)
    assert sum(f["status"] == "missing" for f in row["host_fields"].values()) == 16
    queue = next(r for r in read("completion-followup-gap-research.json")["schools"] if r["ccu_page"] == 74)
    assert "coordinates" not in queue["requested_assets"]
