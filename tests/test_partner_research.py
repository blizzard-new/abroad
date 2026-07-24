from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.application_workflow_collector import (
    collect_application_workflow,
    is_official_partner_url,
)
from exchange_info.models import (
    ApplicationStep,
    CollectionAudit,
    DestinationProfile,
    PageCategory,
    PartnerResearchRecord,
    PartnerUniversity,
    UniversityApplicationWorkflow,
)
from exchange_info.partner_research import (
    _candidate_score,
    apply_partner_research,
    collect_destination_profile,
    discover_partner_official_site,
    research_school_name,
)
from exchange_info.storage import (
    ensure_data_dirs,
    load_application_workflows,
    replace_application_workflow,
    upsert_collection_audit,
    upsert_destination_profile,
)


def _partner(*, website: str | None = None) -> PartnerUniversity:
    return PartnerUniversity(
        program_type="交換學生（英語組）",
        country="日本",
        school_name="明治大學 Meiji University",
        website=website,
        source_url="https://cms-carrier.ntpu.edu.tw/uploads/partners.pdf",
    )


def _workflow(home: str) -> UniversityApplicationWorkflow:
    return UniversityApplicationWorkflow(
        home_university=home,
        school_name=_partner().school_name,
        coverage_status="official_verified",
        steps=[
            ApplicationStep(
                order=1,
                phase="校內申請",
                title=f"{home}流程",
                responsible_party=home,
                summary="測試",
            )
        ],
    )


def test_official_site_scoring_rejects_aggregators() -> None:
    partner = _partner()

    assert (
        _candidate_score(
            partner,
            title="Meiji University",
            url="https://en.wikipedia.org/wiki/Meiji_University",
            body="Meiji University profile",
        )
        < 0
    )
    assert (
        _candidate_score(
            partner,
            title="Meiji University official website",
            url="https://www.meiji.ac.jp/cip/english/",
            body="Incoming exchange and international students",
        )
        >= 12
    )


def test_korean_academic_domains_do_not_collapse_to_ac_kr() -> None:
    assert is_official_partner_url(
        "https://admu-intl.unist.ac.kr/",
        "https://www.unist.ac.kr/unist/index.do",
    )
    assert not is_official_partner_url(
        "https://international.ulsan.ac.kr/international",
        "https://www.unist.ac.kr/unist/index.do",
    )


def test_ntpu_blank_marker_is_not_part_of_japanese_school_identity() -> None:
    assert (
        research_school_name("一橋大學 (Hitotsubashi University) 無")
        == "Hitotsubashi University"
    )


def test_ntpu_location_note_is_not_part_of_chinese_school_identity() -> None:
    assert research_school_name("東北林業大學 黑龍江省哈爾 濱市") == "東北林業大學"


def test_remaining_ntpu_japanese_sites_are_verified_without_search(monkeypatch) -> None:
    monkeypatch.setattr(
        "exchange_info.partner_research._search_candidates",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("search should not run")),
    )
    rows = [
        ("一橋大學 (Hitotsubashi University) 無", "international.hit-u.ac.jp"),
        ("明治大學 (Meiji University) 無", "meiji.ac.jp"),
        ("中央大學 (Chuo University)", "chuo-u.ac.jp"),
        ("宇都宮大學國際學部 (Utsunomiya University)", "utsunomiya-u.ac.jp"),
        ("神戶大學(法學部) (Kobe University)", "kobe-u.ac.jp"),
        ("甲南大學 (Konan University) 無", "konan-u.ac.jp"),
        ("大阪經濟大學 (Osaka University of Economics) 無", "osaka-ue.ac.jp"),
        ("筑波大學 (The University of Tsukuba) 無", "tsukuba.ac.jp"),
        ("福島大學 (Fukushima University) 無", "english.adb.fukushima-u.ac.jp"),
        ("近畿大學 (Kindai University) 無", "kindai.ac.jp"),
        ("千葉大學 (Chiba University)", "chiba-u.jp"),
        ("大東文化大學 (Daito Bunka University) 無", "daito.ac.jp"),
        ("西九州大學 (Nishikyusyu University) 無", "nisikyu-u.ac.jp"),
        ("靜岡縣立大學 無", "eng.u-shizuoka-ken.ac.jp"),
    ]
    for school_name, domain in rows:
        record = discover_partner_official_site(
            PartnerUniversity(
                program_type="交換學生",
                country="日本",
                school_name=school_name,
                source_url="https://ntpu.example/partners.pdf",
            ),
            home_university="國立臺北大學",
        )
        assert record.verification_status == "official_verified"
        assert record.official_domain == domain


def test_ntpu_mainland_china_sites_are_verified_without_search(monkeypatch) -> None:
    monkeypatch.setattr(
        "exchange_info.partner_research._search_candidates",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("search should not run")),
    )
    rows = [
        ("上海立信會計 金融學院", "en.lixin.edu.cn"),
        ("上海財經大學", "iecoenglish.sufe.edu.cn"),
        ("天津大學", "en.tju.edu.cn"),
        ("華東師範大學", "lxs.ecnu.edu.cn"),
        ("南開大學", "ensie.nankai.edu.cn"),
        ("中國人民大學", "sis.ruc.edu.cn"),
        ("中國政法大學", "sis.cupl.edu.cn"),
        ("北京體育大學", "en.bsu.edu.cn"),
        ("西南大學", "admissions.swu.edu.cn"),
        ("山東師範大學", "en.cie.sdnu.edu.cn"),
        ("東北林業大學 黑龍江省哈爾 濱市", "siee.nefu.edu.cn"),
        ("武漢大學", "en.whu.edu.cn"),
        ("華中農業大學", "en.hzau.edu.cn"),
        ("吉林大學", "cie.jlu.edu.cn"),
        ("四川大學", "global.scu.edu.cn"),
        ("南京大學", "stuex.nju.edu.cn"),
        ("西北政法大學", "en.nwupl.edu.cn"),
        ("西安交通大學", "sie.xjtu.edu.cn"),
        ("廈門大學", "admissions.xmu.edu.cn"),
    ]
    for school_name, domain in rows:
        record = discover_partner_official_site(
            PartnerUniversity(
                program_type="交換學生",
                country="大陸地區",
                school_name=school_name,
                source_url="https://ntpu.example/partners.pdf",
            ),
            home_university="國立臺北大學",
        )
        assert record.verification_status == "official_verified"
        assert record.official_domain == domain


def test_ntpu_french_sites_are_verified_without_search(monkeypatch) -> None:
    monkeypatch.setattr(
        "exchange_info.partner_research._search_candidates",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("search should not run")),
    )
    rows = [
        ("諾歐商學院(Neoma Business School) To study in English :", "neoma-bs.com"),
        ("特魯瓦工程技術大學(Universite de Technologie de Troyes)", "utt.fr"),
        ("巴黎計算機電子工程師學院(EFREI)", "eng.efrei.fr"),
        ("拉羅歇爾高等商學院 (Excelia Business School)", "excelia-group.com"),
        ("雷恩商學院 (Rennes School of Business)", "rennes-sb.com"),
        ("法國巴黎高等對外貿易學院 (ESCE International Business School)", "esce.fr"),
        ("昂傑高等商學院(ESSCA)", "essca.eu"),
        ("歐洲知識經濟與管理學院 (Skema Business School)", "skema.edu"),
        ("達芬奇大學 (Leonard De Vinci)", "devinci.fr"),
        ("諾曼第管理學院 EM Normandie", "em-normandie.com"),
        ("北方高等商學院 EDHEC Business school", "edhec.edu"),
        ("TBS圖魯斯商學院(Toulouse Business School)", "tbs-education.com"),
        ("巴黎經濟商業管理高等商學院 (EDC Paris Business School)", "edcparis.edu"),
        ("圖魯斯第一大學 (Toulouse Capitole University)", "ut-capitole.fr"),
        ("法國計算機及創新技術學院EPITECH", "epitech.eu"),
        ("法國普羅旺斯艾克斯政治大學 Sciences Po Aix", "sciencespo-aix.fr"),
        ("法國圖盧茲政治學院 Sciences Po Toulouse", "sciencespo-toulouse.fr"),
        ("Kedge商學院 (KEDGE Business School)", "student.kedge.edu"),
        ("里爾大學 (UNIVERSITÉ DE LILLE)", "international.univ-lille.fr"),
    ]
    for school_name, domain in rows:
        record = discover_partner_official_site(
            PartnerUniversity(
                program_type="交換學生",
                country="法國",
                school_name=school_name,
                source_url="https://ntpu.example/partners.pdf",
            ),
            home_university="國立臺北大學",
        )
        assert record.verification_status == "official_verified"
        assert record.official_domain == domain


def test_ntpu_polish_sites_are_verified_without_search(monkeypatch) -> None:
    monkeypatch.setattr(
        "exchange_info.partner_research._search_candidates",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("search should not run")),
    )
    rows = [
        ("亞當密茲坎維奇大學 (Adam Mickiewicz University)", "erasmus.amu.edu.pl"),
        ("科茲明斯基大學 (Kozminski University)", "kozminski.edu.pl"),
        ("波茲南經濟與商業大學 (Poznan University of Economics and Business )", "ue.poznan.pl"),
        ("波茲南科技大學 (Poznan University of Technology)", "put.poznan.pl"),
        ("華沙生命科學大學(Warsaw University of Life Sciences)", "rekrutacja.sggw.edu.pl"),
        ("弗羅茨瓦夫大學(University of Wrocław)", "international.uni.wroc.pl"),
        ("克拉科夫經濟大學(Krakow University of Economics)", "bpz.uek.krakow.pl"),
        ("亞捷隆大學語言文學院 (Jagiellonian University,Faculty of Filology)", "mymobility.uj.edu.pl"),
    ]
    for school_name, domain in rows:
        record = discover_partner_official_site(
            PartnerUniversity(
                program_type="交換學生",
                country="波蘭",
                school_name=school_name,
                source_url="https://ntpu.example/partners.pdf",
            ),
            home_university="國立臺北大學",
        )
        assert record.verification_status == "official_verified"
        assert record.official_domain == domain


def test_ntpu_vietnamese_sites_are_verified_without_search(monkeypatch) -> None:
    monkeypatch.setattr(
        "exchange_info.partner_research._search_candidates",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("search should not run")),
    )
    rows = [
        ("國民經濟大學 (National Economics University, Vietnam)", "neu.edu.vn"),
        ("鵅鴻大學 (Lac Hong University, LHU)", "en.lhu.edu.vn"),
        ("越南河內國家大學 (Vietnam National University,Hanoi)", "vnu.edu.vn"),
        ("越南胡志明市國際大學 Vietnam National University, Ho Chi Minh City", "hcmiu.edu.vn"),
        ("越南文朗大學 (VanLang University)", "vlu.edu.vn"),
        ("越南胡志明市經濟與法律大學(University of Economics and Law)", "uel.edu.vn"),
        (
            "國立胡志明市經濟大學ˇ國際商學院(University of Economics Ho Chi Minh City-International School of Business)",
            "international.isb.edu.vn",
        ),
        ("越南德國大學(Vietnamese-German University)", "vgu.edu.vn"),
    ]
    for school_name, domain in rows:
        record = discover_partner_official_site(
            PartnerUniversity(
                program_type="交換學生",
                country="越南",
                school_name=school_name,
                source_url="https://ntpu.example/partners.pdf",
            ),
            home_university="國立臺北大學",
        )
        assert record.verification_status == "official_verified"
        assert record.official_domain == domain


def test_ntpu_thailand_sites_are_verified_without_search(monkeypatch) -> None:
    monkeypatch.setattr(
        "exchange_info.partner_research._search_candidates",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("search should not run")),
    )
    rows = [
        (
            "先皇技術學院(King Mongkut's institue of Technology ladkrabang)",
            "oia.kmitl.ac.th",
        ),
        ("法政大學 (Thammasat University)", "oia.tu.ac.th"),
        (
            "蒙庫國王科技大學 (King Mongkut's University of Technology Thonburi (KMUTT))",
            "kmutt.ac.th",
        ),
        ("宋卡王子大學 (Prince of Songkla University (PSU))", "gao.psu.ac.th"),
    ]
    for school_name, domain in rows:
        record = discover_partner_official_site(
            PartnerUniversity(
                program_type="交換學生",
                country="泰國",
                school_name=school_name,
                source_url="https://ntpu.example/partners.pdf",
            ),
            home_university="國立臺北大學",
        )
        assert record.verification_status == "official_verified", (
            school_name,
            research_school_name(school_name),
            record.note,
        )
        assert record.official_domain == domain


def test_verified_korean_sites_bypass_ambiguous_search(monkeypatch) -> None:
    monkeypatch.setattr(
        "exchange_info.partner_research._search_candidates",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("search should not run")),
    )
    rows = [
        ("京畿大學 (Kyonggi University)", "kyonggi.ac.kr"),
        ("東國大學 (Dongguk University)", "dongguk.edu"),
        ("釜慶大學 (Pukyong National University)", "pknu.ac.kr"),
        ("慶北大學 (Kyungpook National University)", "en.knu.ac.kr"),
        ("誠信女子大學 (Sungshin Women's University)", "sungshin.ac.kr"),
        ("韓國漢陽大學Erica校區 Hanyang University ERICA", "hanyang.ac.kr"),
        ("光云大學Kwangwoon University", "kw.ac.kr"),
        ("蔚山科技大學(Ulsan National Institute of Science and Technology)", "unist.ac.kr"),
        ("明知大學(Myongi university)", "english.mju.ac.kr"),
        ("世宗大學 (Sejong University)", "sejong.edu"),
    ]
    for school_name, domain in rows:
        record = discover_partner_official_site(
            PartnerUniversity(
                program_type="交換學生",
                country="韓國",
                school_name=school_name,
                source_url="https://ntpu.example/partners.pdf",
            ),
            home_university="國立臺北大學",
        )
        assert record.verification_status == "official_verified"
        assert record.official_domain == domain


def test_discovery_and_enrichment_keep_home_school_scope(monkeypatch) -> None:
    partner = _partner()
    monkeypatch.setattr(
        "exchange_info.partner_research._search_candidates",
        lambda *args, **kwargs: [
            (
                18,
                "Meiji University official website",
                "https://www.meiji.ac.jp/cip/english/",
                "Incoming exchange",
            )
        ],
    )

    record = discover_partner_official_site(
        partner,
        home_university="國立臺北大學",
    )
    enriched = apply_partner_research(
        [partner],
        [
            record,
            PartnerResearchRecord(
                home_university="長庚大學",
                school_name=partner.school_name,
                official_website="https://wrong.example.edu",
                verification_status="official_verified",
            ),
        ],
        home_university="國立臺北大學",
    )

    assert record.verification_status == "official_verified"
    assert record.official_domain == "meiji.ac.jp"
    assert (
        enriched[0].website
        == "https://www.meiji.ac.jp/cip/english/admissions/exchange.html"
    )


def test_destination_profile_only_uses_official_domain(monkeypatch) -> None:
    partner = _partner(website="https://www.meiji.ac.jp/")
    monkeypatch.setattr(
        "exchange_info.partner_research._official_information_pages",
        lambda *args, **kwargs: [
            ("Housing", "https://www.meiji.ac.jp/cip/housing.html"),
            ("Campus life", "https://www.meiji.ac.jp/cip/campus-life.html"),
            ("Unofficial guide", "https://example.com/meiji-guide"),
        ],
    )
    monkeypatch.setattr(
        "exchange_info.application_workflow_collector.fetch_official_page_text",
        lambda url, *args, **kwargs: (
            "International student accommodation and residence hall details. "
            "Campus life orientation, student clubs, and public transport information."
        ),
    )

    profile = collect_destination_profile(partner)

    assert profile.coverage_status == "official_verified"
    partner_sources = [
        row for row in profile.sources if row.category == PageCategory.PARTNER_SCHOOL
    ]
    assert len(partner_sources) == 4
    assert all("meiji.ac.jp" in row.source_url for row in partner_sources)
    assert all("example.com" not in row.source_url for row in profile.sources)
    assert profile.housing_summary
    assert profile.campus_life_summary


def test_destination_link_body_is_summarized_for_students(monkeypatch) -> None:
    partner = _partner(website="https://www.meiji.ac.jp/")
    monkeypatch.setattr(
        "exchange_info.partner_research._official_information_pages",
        lambda *args, **kwargs: [
            ("Official housing", "https://www.meiji.ac.jp/cip/housing.html")
        ],
    )
    monkeypatch.setattr(
        "exchange_info.application_workflow_collector.fetch_official_page_text",
        lambda *args, **kwargs: "Meiji University offers two residence halls. " * 20,
    )
    monkeypatch.setattr(
        "exchange_info.partner_research.summarize_official_life_link",
        lambda **kwargs: {
            "summary_zh": "這個官方頁面說明交換生可申請的兩處學生宿舍與分配方式。",
            "housing_points": ["交換生可申請兩處學生宿舍，實際房型依校方分配。"],
            "cost_points": [],
            "transport_points": [],
            "campus_life_points": [],
        },
    )

    profile = collect_destination_profile(partner)

    assert profile.sources[0].summary.startswith("這個官方頁面")
    assert "明治大學安排的宿舍" in profile.housing_summary


def test_first_batch_destination_summary_uses_curated_official_details(
    monkeypatch,
) -> None:
    partner = PartnerUniversity(
        program_type="交換學生（英語組）",
        country="日本",
        school_name="佐賀大學 (Saga University For SPACE-SAGA /SE-B/SE-G Program)",
        website="https://www.saga-u.ac.jp/en/",
        source_url="https://cms-carrier.ntpu.edu.tw/uploads/partners.pdf",
    )
    monkeypatch.setattr(
        "exchange_info.partner_research._official_information_pages",
        lambda *args, **kwargs: [],
    )

    profile = collect_destination_profile(partner)

    assert profile.coverage_status == "official_verified"
    assert "11,000" in profile.housing_summary
    assert "水電" in profile.cost_summary
    assert any("irdc.saga-u.ac.jp" in row.source_url for row in profile.sources)


def test_second_korean_batch_has_student_facing_curated_summaries(monkeypatch) -> None:
    monkeypatch.setattr(
        "exchange_info.partner_research._official_information_pages",
        lambda *args, **kwargs: [],
    )
    rows = [
        ("京畿大學 (Kyonggi University)", "住宿", "kyonggi.ac.kr"),
        ("慶北大學 (Kyungpook National University)", "雙人房", "knu.ac.kr"),
        ("誠信女子大學 (Sungshin Women's University)", "地鐵 4 號線", "sungshin.ac.kr"),
        ("光云大學Kwangwoon University", "步行約 6 分鐘", "kw.ac.kr"),
    ]
    for school_name, expected, domain in rows:
        profile = collect_destination_profile(
            PartnerUniversity(
                program_type="交換學生",
                country="韓國",
                school_name=school_name,
                website=f"https://www.{domain}/",
                source_url="https://ntpu.example/partners.pdf",
            )
        )
        serialized = profile.model_dump_json()
        assert profile.coverage_status in {"official_verified", "official_partial"}
        assert expected in serialized
        assert any(domain in source.source_url for source in profile.sources)


def test_remaining_japanese_batch_has_student_facing_curated_summaries(monkeypatch) -> None:
    monkeypatch.setattr(
        "exchange_info.partner_research._official_information_pages",
        lambda *args, **kwargs: [],
    )
    rows = [
        ("一橋大學 (Hitotsubashi University) 無", "一橋寮"),
        ("明治大學 (Meiji University) 無", "144 萬日圓"),
        ("神戶大學(法學部) (Kobe University)", "單人房"),
        ("筑波大學 (The University of Tsukuba) 無", "Short Stay House"),
        ("福島大學 (Fukushima University) 無", "8,900 日圓"),
        ("千葉大學 (Chiba University)", "停止新申請"),
        ("靜岡縣立大學 無", "conversation partner"),
    ]
    for school_name, expected in rows:
        profile = collect_destination_profile(
            PartnerUniversity(
                program_type="交換學生",
                country="日本",
                school_name=school_name,
                website="https://official.example.edu/",
                source_url="https://ntpu.example/partners.pdf",
            )
        )
        assert profile.coverage_status in {"official_verified", "official_partial"}
        assert expected in profile.model_dump_json()
        assert profile.sources


def test_mainland_china_batch_has_student_facing_curated_summaries(monkeypatch) -> None:
    monkeypatch.setattr(
        "exchange_info.partner_research._official_information_pages",
        lambda *args, **kwargs: [],
    )
    rows = [
        ("上海財經大學", "正式提名"),
        ("天津大學", "每晚 60 元"),
        ("中國人民大學", "先到先得"),
        ("東北林業大學 黑龍江省哈爾 濱市", "雙人房"),
        ("南京大學", "床位不保證"),
        ("西安交通大學", "線上系統"),
        ("廈門大學", "思明校區"),
    ]
    for school_name, expected in rows:
        profile = collect_destination_profile(
            PartnerUniversity(
                program_type="交換學生",
                country="大陸地區",
                school_name=school_name,
                website="https://official.example.edu/",
                source_url="https://ntpu.example/partners.pdf",
            )
        )
        assert profile.coverage_status in {"official_verified", "official_partial"}
        assert expected in profile.model_dump_json()
        assert profile.sources


def test_nanjing_profile_contains_source_backed_student_survival_guide(monkeypatch) -> None:
    monkeypatch.setattr(
        "exchange_info.partner_research._official_information_pages",
        lambda *args, **kwargs: [],
    )
    profile = collect_destination_profile(
        PartnerUniversity(
            program_type="交換學生",
            country="大陸地區",
            school_name="南京大學",
            website="https://stuex.nju.edu.cn/",
            source_url="https://ntpu.example/partners.pdf",
        )
    )

    assert profile.city == "南京（仙林校區／鼓樓校區）"
    assert len(profile.guide_photos) == 4
    assert all(photo.image_url.startswith("/static/assets/guides/") for photo in profile.guide_photos)
    assert {section.key for section in profile.student_guide_sections} >= {
        "courses_and_workload",
        "faculty_and_teaching",
        "housing_reality",
        "neighborhood_and_daily_life",
        "mobile_money_and_cards",
        "transport_and_arrival",
    }
    assert len(profile.first_72_hours) >= 5
    assert profile.packing_from_taiwan
    assert profile.buy_after_arrival

    visible_sources = {source.source_url for source in profile.sources}
    cited_sources = {
        source_url
        for section in profile.student_guide_sections
        for source_url in section.source_urls
    }
    for collection in (
        profile.first_72_hours,
        profile.packing_from_taiwan,
        profile.buy_after_arrival,
    ):
        cited_sources.update(
            source_url for item in collection for source_url in item.source_urls
        )
    assert cited_sources <= visible_sources


def test_other_china_profiles_receive_transparent_student_survival_baseline(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "exchange_info.partner_research._official_information_pages",
        lambda *args, **kwargs: [],
    )
    profile = collect_destination_profile(
        PartnerUniversity(
            program_type="交換學生",
            country="大陸地區",
            school_name="上海財經大學",
            website="https://iecoenglish.sufe.edu.cn/",
            source_url="https://ntpu.example/partners.pdf",
        )
    )

    assert {section.key for section in profile.student_guide_sections} == {
        "courses_and_workload",
        "faculty_and_teaching",
        "housing_reality",
        "neighborhood_and_daily_life",
        "mobile_money_and_cards",
        "transport_and_arrival",
    }
    assert len(profile.first_72_hours) == 5
    assert len(profile.packing_from_taiwan) == 4
    assert len(profile.buy_after_arrival) == 4
    assert "不足" in next(
        section.summary
        for section in profile.student_guide_sections
        if section.key == "courses_and_workload"
    )

    visible_sources = {source.source_url for source in profile.sources}
    cited_sources = {
        source_url
        for section in profile.student_guide_sections
        for source_url in section.source_urls
    }
    for collection in (
        profile.first_72_hours,
        profile.packing_from_taiwan,
        profile.buy_after_arrival,
    ):
        cited_sources.update(
            source_url for item in collection for source_url in item.source_urls
        )
    assert cited_sources <= visible_sources
    assert all(source.summary for source in profile.sources)


def test_navigation_only_official_page_gets_transparent_source_summary(monkeypatch) -> None:
    monkeypatch.setattr(
        "exchange_info.partner_research._official_information_pages",
        lambda *args, **kwargs: [
            ("International", "https://official.example.edu/international")
        ],
    )
    monkeypatch.setattr(
        "exchange_info.application_workflow_collector.fetch_official_page_text",
        lambda *args, **kwargs: "International Contact",
    )
    monkeypatch.setattr(
        "exchange_info.partner_research.summarize_official_life_link",
        lambda *args, **kwargs: None,
    )

    profile = collect_destination_profile(
        PartnerUniversity(
            program_type="交換學生",
            country="法國",
            school_name="Example University",
            website="https://official.example.edu/",
            source_url="https://ntpu.example/partners.pdf",
        )
    )

    source = next(
        row for row in profile.sources if row.source_url.endswith("/international")
    )
    assert "頁面導覽" in source.summary


def test_regional_profiles_receive_country_specific_survival_guides(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "exchange_info.partner_research._official_information_pages",
        lambda *args, **kwargs: [],
    )
    rows = (
        (
            "日本",
            "明治大學 Meiji University",
            "https://www.meiji.ac.jp/",
            "確認在留卡與住址登記",
        ),
        (
            "韓國",
            "東國大學 (Dongguk University)",
            "https://www.dongguk.edu/eng/main",
            "預約外國人登錄並備齊文件",
        ),
        (
            "法國",
            "雷恩商學院 (Rennes School of Business)",
            "https://www.rennes-sb.com/exchange-programmes/incoming-exchange-students/",
            "完成 VLS-TS 線上驗證與學校註冊",
        ),
        (
            "波蘭",
            "科茲明斯基大學 (Kozminski University)",
            "https://www.kozminski.edu.pl/en/community/incoming-students",
            "核對簽證效期與暫時居留需求",
        ),
        (
            "越南",
            "越南文朗大學 (VanLang University)",
            "https://www.vlu.edu.vn/en/admissions/student-exchange-opportunities",
            "確認就學簽證、入境口岸與住宿登記",
        ),
        (
            "泰國",
            "蒙庫國王科技大學 (King Mongkut's University of Technology Thonburi (KMUTT))",
            "https://www.kmutt.ac.th/internationalization/mobility-program/exchange-programs/",
            "確認 ED 簽證、停留期限與再次入境安排",
        ),
    )

    for country, school_name, website, residence_step in rows:
        profile = collect_destination_profile(
            PartnerUniversity(
                program_type="交換學生",
                country=country,
                school_name=school_name,
                website=website,
                source_url="https://ntpu.example/partners.pdf",
            )
        )

        assert len(profile.student_guide_sections) == 6
        assert len(profile.first_72_hours) == 5
        assert len(profile.packing_from_taiwan) == 4
        assert len(profile.buy_after_arrival) == 4
        assert any(
            item.title == residence_step for item in profile.first_72_hours
        )

        visible_sources = {source.source_url for source in profile.sources}
        cited_sources = {
            source_url
            for section in profile.student_guide_sections
            for source_url in section.source_urls
        }
        for collection in (
            profile.first_72_hours,
            profile.packing_from_taiwan,
            profile.buy_after_arrival,
        ):
            cited_sources.update(
                source_url for item in collection for source_url in item.source_urls
            )
        assert cited_sources <= visible_sources
        assert all(source.summary for source in profile.sources)
        if "Dongguk University" in school_name:
            assert len(profile.guide_photos) == 4
            assert all(photo.category == "housing" for photo in profile.guide_photos)
            assert all(
                photo.image_url.startswith("/static/assets/guides/dongguk-chungmu-")
                for photo in profile.guide_photos
            )
            assert "東大入口站 6 號出口" in profile.transport_summary
            assert "\ufffc" not in profile.model_dump_json()


def test_blocked_mainland_homepages_still_have_reviewed_link_summaries(monkeypatch) -> None:
    monkeypatch.setattr(
        "exchange_info.partner_research._official_information_pages",
        lambda *args, **kwargs: [],
    )
    for school_name in ("中國政法大學", "山東師範大學"):
        profile = collect_destination_profile(
            PartnerUniversity(
                program_type="交換學生",
                country="大陸地區",
                school_name=school_name,
                website="https://official.example.edu/",
                source_url="https://ntpu.example/partners.pdf",
            )
        )
        assert profile.sources
        assert all(source.summary for source in profile.sources)


def test_curated_official_links_always_have_student_summary(monkeypatch) -> None:
    monkeypatch.setattr(
        "exchange_info.partner_research._official_information_pages",
        lambda *args, **kwargs: [],
    )
    for country, school_name in (
        ("日本", "近畿大學 (Kindai University) 無"),
        ("韓國", "東國大學 (Dongguk University)"),
        ("大陸地區", "西安交通大學"),
    ):
        profile = collect_destination_profile(
            PartnerUniversity(
                program_type="交換學生",
                country=country,
                school_name=school_name,
                website="https://official.example.edu/",
                source_url="https://ntpu.example/partners.pdf",
            )
        )
        assert profile.sources
        assert all(source.summary for source in profile.sources)


def test_ntpu_workflow_does_not_leak_cgu_copy(monkeypatch) -> None:
    monkeypatch.setattr(
        "exchange_info.application_workflow_collector.discover_official_partner_pages",
        lambda *args, **kwargs: [],
    )
    workflow = collect_application_workflow(
        _partner(),
        home_university="國立臺北大學",
        rate_limit_seconds=0,
    )
    serialized = workflow.model_dump_json()

    assert workflow.home_university == "國立臺北大學"
    assert len(workflow.steps) == 6
    assert "長庚" not in serialized
    assert "臺北大學" in serialized


def test_workflow_storage_preserves_same_partner_for_two_home_schools(tmp_path) -> None:
    ensure_data_dirs(tmp_path)
    replace_application_workflow(_workflow("長庚大學"), tmp_path)
    replace_application_workflow(_workflow("國立臺北大學"), tmp_path)

    rows = load_application_workflows(tmp_path)

    assert len(rows) == 2
    assert {row.home_university for row in rows} == {"長庚大學", "國立臺北大學"}


def test_ntpu_coverage_does_not_claim_shared_cgu_data_as_researched(
    tmp_path,
    monkeypatch,
) -> None:
    partner = _partner()
    ensure_data_dirs(tmp_path)
    replace_application_workflow(_workflow("長庚大學"), tmp_path)
    upsert_destination_profile(
        DestinationProfile(
            school_name=partner.school_name,
            coverage_status="official_verified",
        ),
        tmp_path,
    )
    monkeypatch.setattr(
        "exchange_info.api.fetch_ntpu_partner_universities",
        lambda: [partner],
    )
    client = TestClient(create_app(tmp_path))

    initial = client.get("/coverage", params={"school": "NTPU"}).json()

    assert initial["total_partner_schools"] == 1
    assert initial["workflow_school_count"] == 0
    assert initial["destination_profile_count"] == 0

    replace_application_workflow(_workflow("國立臺北大學"), tmp_path)
    upsert_collection_audit(
        CollectionAudit(
            home_university="國立臺北大學",
            school_name=partner.school_name,
            collector="destinations",
            status="official_verified",
            result_count=1,
        ),
        tmp_path,
    )

    researched = client.get("/coverage", params={"school": "NTPU"}).json()

    assert researched["workflow_school_count"] == 1
    assert researched["destination_profile_count"] == 1
