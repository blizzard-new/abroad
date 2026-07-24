import json

from exchange_info.models import PartnerUniversity
from exchange_info.school_image_collector import (
    OFFICIAL_IMAGE_OVERRIDE_NOTES,
    OFFICIAL_IMAGE_OVERRIDES,
    SchoolImageRecord,
    _official_image_override,
    collect_school_images,
    extract_image_candidates,
)


def test_second_ntpu_korean_batch_has_official_photo_overrides() -> None:
    schools = {
        "京畿大學 (Kyonggi University)",
        "東國大學 (Dongguk University)",
        "釜慶大學 (Pukyong National University)",
        "慶北大學 (Kyungpook National University)",
        "誠信女子大學 (Sungshin Women's University)",
        "韓國漢陽大學Erica校區 Hanyang University ERICA",
        "光云大學Kwangwoon University",
    }

    assert schools <= OFFICIAL_IMAGE_OVERRIDES.keys()
    for school in schools:
        image_url, source_url = OFFICIAL_IMAGE_OVERRIDES[school]
        assert image_url.startswith(("http://", "https://"))
        assert source_url.startswith("https://")


def test_ntpu_french_aliases_reuse_verified_official_photo_overrides() -> None:
    rows = {
        "諾歐商學院(Neoma Business School) To study in English :": "neoma-bs.com",
        "特魯瓦工程技術大學(Universite de Technologie de Troyes)": "utt.fr",
        "歐洲知識經濟與管理學院 (Skema Business School)": "skema.edu",
        "諾曼第管理學院 EM Normandie": "em-normandie.com",
        "Kedge商學院 (KEDGE Business School)": "kedge.edu",
        "TBS圖魯斯商學院(Toulouse Business School)": "tbs-education.com",
        "法國計算機及創新技術學院EPITECH": "epitech.eu",
        "法國圖盧茲政治學院 Sciences Po Toulouse": "sciencespo-toulouse.fr",
        "弗羅茨瓦夫大學(University of Wrocław)": "bip.uni.wroc.pl",
        "亞捷隆大學語言文學院 (Jagiellonian University,Faculty of Filology)": "uj.edu.pl",
    }

    for school_name, domain in rows.items():
        override = _official_image_override(school_name)
        assert override is not None
        assert domain in override[1]


def test_ntpu_vietnamese_schools_with_bad_or_missing_auto_photos_have_reviewed_overrides() -> None:
    rows = {
        "鵅鴻大學 (Lac Hong University, LHU)": "lhu.edu.vn",
        "越南河內國家大學 (Vietnam National University,Hanoi)": "vietnam.vn",
        "越南胡志明市國際大學 Vietnam National University, Ho Chi Minh City": "hcmiu.edu.vn",
        "越南文朗大學 (VanLang University)": "vlu.edu.vn",
        "國立胡志明市經濟大學ˇ國際商學院(University of Economics Ho Chi Minh City-International School of Business)": "international.isb.edu.vn",
        "越南德國大學(Vietnamese-German University)": "vgu.edu.vn",
    }

    for school_name, source_domain in rows.items():
        override = _official_image_override(school_name)
        assert override is not None
        image_url, source_url = override
        assert image_url.startswith("https://")
        assert source_domain in source_url

    assert "VNU 官方粉絲頁" in OFFICIAL_IMAGE_OVERRIDE_NOTES[
        "越南河內國家大學 (Vietnam National University,Hanoi)"
    ]


def test_ntpu_thailand_schools_have_reviewed_official_photo_overrides() -> None:
    rows = {
        "先皇技術學院(King Mongkut's institue of Technology ladkrabang)": "oia.kmitl.ac.th",
        "法政大學 (Thammasat University)": "oia.tu.ac.th",
        "蒙庫國王科技大學 (King Mongkut's University of Technology Thonburi (KMUTT))": "kmutt.ac.th",
        "宋卡王子大學 (Prince of Songkla University (PSU))": "psu.ac.th",
    }

    for school_name, source_domain in rows.items():
        override = _official_image_override(school_name)
        assert override is not None
        image_url, source_url = override
        assert image_url.startswith("https://")
        assert source_domain in source_url


def test_official_hero_image_ranks_above_logo() -> None:
    html = """
    <html><head>
      <meta property="og:image" content="/assets/campus-hero.jpg">
    </head><body>
      <img src="/assets/university-logo.png" width="800" height="400" alt="University logo">
      <img src="/assets/students-on-campus.jpg" width="1200" height="700" alt="Students on campus">
    </body></html>
    """

    candidates = extract_image_candidates(html, "https://official.example.edu/")

    assert candidates[0].url == "https://official.example.edu/assets/campus-hero.jpg"
    assert all("logo" not in candidate.url for candidate in candidates)


def test_relative_background_image_is_resolved() -> None:
    html = '<div class="homepage hero" style="background-image: url(../images/campus.jpg)"></div>'

    candidates = extract_image_candidates(html, "https://official.example.edu/en/home/")

    assert candidates[0].url == "https://official.example.edu/en/images/campus.jpg"


def test_nitro_lazy_image_attributes_are_discovered() -> None:
    html = """
    <img width="720" height="405" alt="Students on campus"
      nitro-lazy-src="/campus-720x405.jpg"
      nitro-lazy-srcset="/campus-360x203.jpg 360w, /campus-720x405.jpg 720w">
    """

    candidates = extract_image_candidates(html, "https://official.example.edu/en/")

    assert candidates[0].url == "https://official.example.edu/campus-720x405.jpg"


def test_collecting_ntpu_image_preserves_existing_manifest_rows(tmp_path, monkeypatch) -> None:
    manifest = tmp_path / "school-images.json"
    output = tmp_path / "schools"
    old = SchoolImageRecord(
        school_name="既有大學",
        country="日本",
        official_page_url="https://old.example.edu/",
        image_source_url="https://old.example.edu/campus.jpg",
        local_path="/static/assets/schools/old.jpg",
        width=1600,
        height=900,
        content_hash="old",
        checked_at="2026-07-20T00:00:00+00:00",
        status="verified",
    )
    manifest.write_text(
        json.dumps({"schools": [old.__dict__] if hasattr(old, "__dict__") else [{
            "school_name": old.school_name,
            "country": old.country,
            "official_page_url": old.official_page_url,
            "image_source_url": old.image_source_url,
            "local_path": old.local_path,
            "width": old.width,
            "height": old.height,
            "content_hash": old.content_hash,
            "checked_at": old.checked_at,
            "status": old.status,
            "note": old.note,
        }]}),
        encoding="utf-8",
    )
    new = SchoolImageRecord(
        school_name="明治大學 Meiji University",
        country="日本",
        official_page_url="https://www.meiji.ac.jp/",
        image_source_url="https://www.meiji.ac.jp/campus.jpg",
        local_path="/static/assets/schools/meiji.jpg",
        width=1600,
        height=900,
        content_hash="new",
        checked_at="2026-07-21T00:00:00+00:00",
        status="verified",
    )
    monkeypatch.setattr(
        "exchange_info.school_image_collector._collect_one",
        lambda **kwargs: new,
    )

    collect_school_images(
        output_dir=output,
        manifest_path=manifest,
        partners=[
            PartnerUniversity(
                program_type="交換學生",
                country="日本",
                school_name=new.school_name,
                website=new.official_page_url,
                source_url="https://ntpu.example/partners.pdf",
            )
        ],
    )

    names = {row["school_name"] for row in json.loads(manifest.read_text(encoding="utf-8"))["schools"]}
    assert names == {"既有大學", "明治大學 Meiji University"}
