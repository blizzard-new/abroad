"""School-isolated, reviewed CCU photographs and geographic representative points."""
from __future__ import annotations

from functools import lru_cache
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

from .ccu_sources import BUNDLE
from .ccu_completion_sources import validate_completion_source
from .models import PartnerUniversity
from .university_locations import UniversityLocation


@lru_cache(maxsize=1)
def reviewed_assets():
    path = BUNDLE / "campus-assets.json"
    if not path.exists():
        return {}
    rows = json.loads(path.read_text(encoding="utf-8"))["schools"]
    if len(rows) != 104 or len({row["ccu_page"] for row in rows}) != 104:
        raise ValueError("CCU asset inventory must cover all 104 exchange-list identities")
    result = {}
    checked = {}
    for row in rows:
        for key in ["photo", "coordinates"]:
            field = row[key]
            if field["status"] != "verified_current":
                continue
            if not field.get("value") or not field.get("evidence"):
                raise ValueError("CCU campus assets require source evidence")
            for ev in field["evidence"]:
                validate_completion_source(BUNDLE, ev, checked)
            if key == "coordinates":
                location = UniversityLocation.model_validate(field["value"])
                if (location.school_name != row["school_name"] or location.country != row["country"]
                        or location.geocode_status != "verified"):
                    raise ValueError("CCU coordinate campus identity mismatch")
            else:
                photo = field["value"]
                for name in ["artist", "license_name", "license_url", "campus_caption", "source_page_url", "checked_at"]:
                    if not photo.get(name):
                        raise ValueError("CCU photograph attribution is incomplete")
                if any(urlsplit(photo[name]).scheme not in {"http", "https"} for name in ["license_url", "source_page_url", "image_source_url"]):
                    raise ValueError("Invalid campus asset source URL")
                if not photo["local_path"].startswith("/static/assets/ccu/campuses/"):
                    raise ValueError("CCU photographs must use the isolated asset directory")
                file = (Path(__file__).parent / photo["local_path"].removeprefix("/")).resolve()
                if not file.is_relative_to((Path(__file__).parent / "static/assets/ccu/campuses").resolve()):
                    raise ValueError("CCU photograph path escapes its campus directory")
                if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != photo["sha256"]:
                    raise ValueError("CCU photograph changed after review")
        result[row["ccu_page"]] = row
    return result


def apply_campus_assets(partner: PartnerUniversity) -> PartnerUniversity:
    row = reviewed_assets().get(partner.source_pages[0])
    if row is None:
        return partner
    if row["school_name"] != partner.school_name or row["country"] != partner.country:
        raise ValueError("CCU asset partner identity mismatch")
    public = {}
    point = row["coordinates"]
    if point["status"] == "verified_current":
        partner.location = UniversityLocation.model_validate(point["value"])
        public["coordinates"] = {"note": partner.location.note, "source_url": partner.location.source_url,
                                 "precision": partner.location.precision, "checked_at": partner.location.geocoded_at.isoformat()}
    photo = row["photo"]
    if photo["status"] == "verified_current":
        value = photo["value"]
        partner.image_url = value["local_path"]
        partner.image_source_url = value["image_source_url"]
        partner.image_page_url = value["source_page_url"]
        partner.image_status = "verified"
        public["photo"] = {key: value[key] for key in ["artist", "license_name", "license_url", "source_page_url", "campus_caption", "checked_at", "modifications", "applicability"]}
    if public:
        partner.reference_data = {**partner.reference_data, "ccu_campus_assets": json.dumps(public, ensure_ascii=False)}
    return partner


def attach_reviewed_image(partner: PartnerUniversity, base_url: str) -> PartnerUniversity:
    """Keep the image and its licence together when shared aliases also match."""
    row = reviewed_assets().get(partner.source_pages[0]) if partner.source_pages else None
    if row is None:
        return partner
    field = row["photo"]
    if field["status"] != "verified_current":
        return partner.model_copy(update={"image_url": None, "image_source_url": None,
                                          "image_page_url": None, "image_status": "missing"})
    value = field["value"]
    return partner.model_copy(update={"image_url": base_url.rstrip("/") + value["local_path"],
                                      "image_source_url": value["image_source_url"],
                                      "image_page_url": value["source_page_url"], "image_status": "verified"})


def reviewed_image_coverage(partner: PartnerUniversity) -> dict:
    """Report the same approved photograph that the CCU dashboard serves."""
    row = reviewed_assets().get(partner.source_pages[0]) if partner.source_pages else None
    field = row["photo"] if row else None
    if not field or field["status"] != "verified_current":
        return {"status": "missing", "checked_at": None}
    return {"status": "verified", "checked_at": field["value"]["checked_at"]}
