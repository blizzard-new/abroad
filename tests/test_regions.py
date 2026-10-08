"""Regions for the school search, and the Czech school names that used to start with a stray "Republic"."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from exchange_info.ntpu_student_view import _country_and_body, fetch_ntpu_partner_universities
from exchange_info.school_identity import same_school

STATIC = Path("src/exchange_info/static")
DATA = Path("src/exchange_info/official_data")


def node(script: str):
    code = f"const R = require('./{STATIC.as_posix()}/regions.js'); console.log(JSON.stringify({script}));"
    result = subprocess.run(["node", "-e", code], capture_output=True, text=True, encoding="utf-8", timeout=30, check=True)
    return json.loads(result.stdout)


def bundled_countries() -> set[str]:
    countries: set[str] = set()
    for path in DATA.rglob("*.jsonl"):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                if isinstance(row, dict) and isinstance(row.get("country"), str):
                    countries.add(row["country"])
    return countries


def test_every_country_in_the_bundled_data_belongs_to_a_region() -> None:
    countries = sorted(bundled_countries())
    assert len(countries) > 40
    unplaced = node(f"{json.dumps(countries, ensure_ascii=False)}.filter(c => R.regionOf(c) === 'other')")
    assert unplaced == [], "give these a region in regions.js, or they land under 其他地區"


def test_eastern_europe_is_the_nine_countries_ntpu_has_schools_in() -> None:
    ntpu = {json.loads(line)["country"] for line in (DATA / "ntpu" / "destination_profiles.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()}
    inside = node(f"{json.dumps(sorted(ntpu), ensure_ascii=False)}.filter(c => R.inRegion(c, 'eastern-europe'))")
    assert set(inside) == {"波蘭", "捷克", "斯洛伐克", "匈牙利", "羅馬尼亞", "立陶宛", "拉脫維亞", "俄羅斯", "阿爾巴尼亞"}
    assert "哈薩克" not in inside and "德國" not in inside


def test_a_region_group_contains_its_parts_and_turkey_counts_as_europe_like_ntpus_own_list() -> None:
    assert node("['波蘭', '法國', '瑞典', '西班牙', '土耳其', '日本', '美國'].filter(c => R.inRegion(c, 'europe'))") == ["波蘭", "法國", "瑞典", "西班牙", "土耳其"]
    assert node("['日本', '越南', '印度', '土耳其', '法國'].filter(c => R.inRegion(c, 'asia'))") == ["日本", "越南", "印度", "土耳其"]
    assert node("R.inRegion('日本', '')") is True, "no region chosen means everything"


def test_search_words_cover_the_ways_a_student_asks() -> None:
    words = node("Object.fromEntries(['波蘭', '捷克', '德國', '日本', '立陶宛'].map(c => [c, R.searchText(c)]))")
    assert "東歐" in words["波蘭"] and "poland" in words["波蘭"] and "歐洲" in words["波蘭"] and "eastern europe" in words["波蘭"]
    assert "czech republic" in words["捷克"] and "czechia" in words["捷克"]
    assert "中歐" in words["德國"] and "東歐" not in words["德國"]
    assert "東歐" not in words["日本"] and "japan" in words["日本"] and "亞洲" in words["日本"]
    assert "波羅的海" in words["立陶宛"]


def test_the_drop_downs_only_offer_regions_that_have_a_school() -> None:
    groups = node("R.regionGroups(['波蘭', '日本', '紐西蘭'])")
    labels = {group["label"]: [option["label"] for option in group["options"]] for group in groups}
    assert labels == {"歐洲": ["東歐／中歐"], "亞洲": ["東亞"], "大洋洲": ["大洋洲"]}, "one part only: no 'all of it' line"
    both = node("R.regionGroups(['波蘭', '法國']).map(g => g.options.map(o => o.label))")
    assert both == [["歐洲（全部）", "東歐／中歐", "西歐"]]
    placed = node("R.countryGroups(['波蘭', '日本', '火星', '捷克']).map(g => [g.label, g.countries])")
    assert [label for label, _ in placed] == ["東歐／中歐", "東亞", "其他地區"]
    assert set(placed[0][1]) == {"捷克", "波蘭"} and placed[1][1] == ["日本"]
    assert placed[-1] == ["其他地區", ["火星"]], "an unknown country is still listed"


def test_the_czech_country_prefix_takes_the_word_republic_with_it() -> None:
    country, body = _country_and_body("捷克 Czech Republic 布拉格生命科學大學 (Czech University of Life Sciences Prague)", "英語組")
    assert country == "捷克" and body.startswith("布拉格生命科學大學")
    country, body = _country_and_body("捷克 Czech 西波西米亞大學 (University of West Bohemia)", "英語組")
    assert country == "捷克" and body.startswith("西波西米亞大學")


def test_no_school_name_in_the_bundled_data_starts_with_a_stray_republic() -> None:
    stale = re.compile(r"(?<![A-Za-z])Republic (?=[一-鿿])")
    files = [*DATA.rglob("*.jsonl"), *DATA.glob("*.json"), *(DATA / "ntpu").glob("*.json"), STATIC / "assets" / "school-images.json"]
    assert len(files) > 10
    for path in files:
        assert not stale.search(path.read_text(encoding="utf-8")), path.name


def test_every_ntpu_school_still_finds_its_profile_after_the_rename() -> None:
    profiles = [json.loads(line)["school_name"] for line in (DATA / "ntpu" / "destination_profiles.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    partners = fetch_ntpu_partner_universities()
    assert len(partners) == 206
    assert [row.school_name for row in partners if not any(same_school(row.school_name, name) for name in profiles)] == []
    assert not any(row.school_name.startswith("Republic") for row in partners)
