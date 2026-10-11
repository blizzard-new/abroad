"""NCU-only reviewed supplements. Never shares a candidate with another home."""
from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path

from .models import DestinationProfile, StudentGuidePhoto, StudentDashboard
from .school_identity import school_identity_key
from .university_locations import UniversityLocation

ASSETS = Path(__file__).parent / "official_data/ncu/campus-assets.json"
LOCATIONS = ASSETS.with_name("campus-locations.json")


@lru_cache(maxsize=1)
def _locations_snapshot(signature):
    data = json.loads(LOCATIONS.read_text())
    rows = {}
    for row in data["locations"]:
        location = UniversityLocation.model_validate(row)
        if location.geocode_status != "verified":
            location = location.model_copy(update={"latitude": None, "longitude": None})
        rows[(school_identity_key(row["school_name"]), row["country"])] = location
    return rows


def campus_location(partner, fallback, data_dir=None):
    if data_dir is not None:
        from .university_locations import local_location_override
        operator = local_location_override(data_dir, partner.school_name, partner.country)
        if operator is not None:
            return operator
    if not LOCATIONS.exists():
        return fallback
    stat = LOCATIONS.stat()
    candidate = _locations_snapshot((stat.st_mtime_ns, stat.st_size)).get(
        (school_identity_key(partner.school_name), partner.country))
    if candidate is None or (
        candidate.geocode_status != "verified"
        and fallback is not None and fallback.geocode_status == "verified"
    ):
        return fallback
    return candidate


@lru_cache(maxsize=1)
def _assets_snapshot(signature):
    data = json.loads(ASSETS.read_text())
    return {(school_identity_key(row["school_name"]), row["country"]): row for row in data["photos"]}


def campus_photo(school_name, country):
    if not ASSETS.exists():
        return None
    stat = ASSETS.stat()
    return _assets_snapshot((stat.st_mtime_ns, stat.st_size)).get((school_identity_key(school_name), country))


def attach_campus_photos(dashboard: StudentDashboard, *, base_url=""):
    if dashboard.school_name != "國立中央大學":
        return dashboard
    partners = []
    for partner in dashboard.partner_universities:
        photo = campus_photo(partner.school_name, partner.country)
        updates = {"image_url": None, "image_source_url": None, "image_page_url": None, "image_status": "license_unverified"}
        if photo:
            updates = {key: photo[key] for key in ("image_url", "image_source_url", "image_page_url")}
            updates.update(image_url=base_url.rstrip("/") + photo["image_url"], image_status="verified")
        partners.append(partner.model_copy(update=updates))
    return dashboard.model_copy(update={"partner_universities": partners})


def attach_profile_campus_photo(profile: DestinationProfile):
    if profile.home_university != "國立中央大學":
        return profile
    photo = campus_photo(profile.school_name, profile.country)
    if not photo:
        return profile
    addition = StudentGuidePhoto(image_url=photo["image_url"], source_url=photo["image_page_url"],
        alt=profile.school_name + "校園參考照片", caption=photo["caption_zh"], category="campus")
    existing = [row for row in profile.guide_photos if not row.image_url.startswith("/static/assets/ncu-schools/")]
    return profile.model_copy(update={"guide_photos": [addition, *existing]})
