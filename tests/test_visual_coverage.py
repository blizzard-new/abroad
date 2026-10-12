import hashlib
import json
from pathlib import Path
import subprocess

from exchange_info import api
from exchange_info.models import PartnerUniversity, StudentDashboard
from exchange_info.school_identity import VisualRecordIndex, _loose_key, school_identity_key, visual_identity_aliases
from exchange_info.university_locations import load_university_locations, public_location
from exchange_info.university_registry import SUPPORTED_UNIVERSITIES
from scripts.audit_visual_coverage import marker_available, photo_evidence


def test_visual_aliases_require_unique_identity_country_and_keep_review_decisions():
    record = {"status": "verified"}
    index = VisualRecordIndex({("university of life sciences", "波蘭"): record})
    assert index.get(("university of lifesciences", "波蘭")) is record
    assert index.get(("university of lifesciences", "英國")) is None
    assert index.get(("university of life sciences west campus", "波蘭")) is None
    review = {"status": "needs_review"}
    index = VisualRecordIndex({("university of life sciences", "波蘭"): record,
                               ("university of lifesciences", "波蘭"): review})
    assert index.get(("university of lifesciences", "波蘭")) is review
    assert index.get(("universityoflifesciences", "波蘭")) is None


def test_bilingual_order_and_known_country_aliases_do_not_merge_campuses_or_hong_kong():
    photos = [
        {"school_name": "南京大學 Nanjing University", "country": "大陸地區", "status": "verified"},
        {"school_name": "立命館大學", "country": "日本", "status": "verified"},
        {"school_name": "東國大學 (Dongguk University)", "country": "韓國", "status": "verified"},
    ]
    index = VisualRecordIndex({(school_identity_key(r["school_name"]),r["country"]):r for r in photos})
    assert index.get(("Nanjing University 南京大學", "中國大陸")) is photos[0]
    assert index.get(("立命館大學 Ritsumeikan University", "日本")) is photos[1]
    assert index.get(("東國大學 Dongguk University", "南韓")) is photos[2]
    assert index.get(("南京大學 Nanjing University", "香港")) is None
    assert index.get(("南京大學 Nanjing University", "澳門")) is None
    assert index.get(("立命館大學 Ritsumeikan University Osaka Campus", "日本")) is None
    assert index.get(("Nanjing University 南京大學蘇州校區", "中國大陸")) is None
    assert index.get(("Nanjing University 南京大學醫學院", "中國大陸")) is None
    assert index.get(("---", "中國大陸")) is None
    # Two different schools with the same Chinese translation remain ambiguous.
    collision = [{"school_name":"測試大學 First University"},{"school_name":"測試大學 Second University"}]
    ambiguous = VisualRecordIndex({(school_identity_key(r["school_name"]),"日本"):r for r in collision})
    assert ambiguous.get(("測試大學", "日本")) is None


def test_photo_api_reuses_extraction_alias_without_changing_zero_or_missing_quota(tmp_path, monkeypatch):
    path = tmp_path / "images.json"
    path.write_text(json.dumps({"schools": [{"school_name": "University of Life Sciences", "country": "波蘭",
        "status": "verified", "local_path": "/static/campus.jpg"}]}))
    monkeypatch.setattr(api, "SCHOOL_IMAGE_MANIFEST", path)
    rows = [PartnerUniversity(school_name="University of LifeSciences", country="波蘭", quota=quota,
                              program_type="交換學生", source_url="https://example.edu/source") for quota in ("0", "")]
    result = api._attach_school_images(StudentDashboard(partner_universities=rows), base_url="https://example.org")
    assert [r.image_url for r in result.partner_universities] == ["https://example.org/static/campus.jpg"] * 2
    assert [r.quota for r in result.partner_universities] == ["0", ""]


def test_all_six_home_locations_have_sourced_representative_points(tmp_path):
    locations = load_university_locations(tmp_path)
    for university in SUPPORTED_UNIVERSITIES:
        location = public_location(locations, university.school_name, "臺灣")
        assert marker_available(location.model_dump())
        assert location.source_url and location.identity_source_url and location.geocoded_at
    tku = public_location(locations, "淡江大學", "臺灣")
    assert "淡水" in tku.city and "不能代表其他校區" in tku.note
    assert 25.16 < tku.latitude < 25.19 and 121.43 < tku.longitude < 121.46


def test_photo_file_identity_license_and_hash_are_separate(tmp_path):
    file = tmp_path / "campus.jpg"
    file.write_bytes(b"isolated image hash fixture")
    row = {"status": "verified", "local_path": "/static/campus.jpg",
           "content_hash": hashlib.sha256(file.read_bytes()).hexdigest()}
    evidence = photo_evidence(row, tmp_path)
    assert evidence["file_ok"] and evidence["hash_ok"]
    assert evidence["license_metadata"] == "pending"
    row.update(license_name="CC BY-SA 4.0", license_url="https://creativecommons.org/licenses/by-sa/4.0/",
               artist="Unknown", official_page_url="https://commons.wikimedia.org/wiki/File:Campus.jpg",
               identity_source_url="https://example.edu/campus", checked_at="2026-10-11")
    assert photo_evidence(row, tmp_path)["license_metadata"] == "pending"
    row["artist"] = "Example photographer"
    assert photo_evidence(row, tmp_path)["license_metadata"] == "documented"
    file.write_bytes(b"changed asset")
    assert not photo_evidence(row, tmp_path)["hash_ok"]
    assert not photo_evidence(row | {"local_path": "/static/../outside.jpg"}, tmp_path)["file_ok"]


def test_frontend_and_backend_visual_identity_agree_for_entire_shipped_manifest():
    static = Path("src/exchange_info/static")
    source = (static / "app.js").read_text()
    functions = source[source.index("function visualSchoolIdentity("):source.index("function renderSchoolPhoto(")]
    rows = json.loads((static / "assets/school-images.json").read_text())["schools"]
    names = [r["school_name"] for r in rows] + ["University of LifeSciences", "Straße University", "臺大（E交換學生計畫、V訪問學生計畫）", "Nanjing University 南京大學", "立命館大學 Ritsumeikan University", "Nanjing University 南京大學醫學院"]
    command = 'const state={schoolImages:[]};' + functions + '\nconst input=JSON.parse(require("fs").readFileSync(0,"utf8"));process.stdout.write(JSON.stringify(input.map(n=>[visualSchoolIdentity(n),visualSchoolIdentity(n,true),visualSchoolAliases(n)])));'
    result = subprocess.run(["node", "-e", command], input=json.dumps(names), text=True, capture_output=True, check=True)
    assert json.loads(result.stdout) == [[school_identity_key(n), _loose_key(n), list(visual_identity_aliases(n))] for n in names]
