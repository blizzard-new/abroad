from datetime import datetime, timezone

from fastapi.testclient import TestClient

from exchange_info.api import create_app
from exchange_info.experience_collector import (
    _candidate_to_source,
    _summarize_link_content,
    build_experience_digest,
    build_experience_queries,
    merge_refreshed_student_experiences,
    normalize_source_url,
    school_search_name,
)
from exchange_info.content_summary import FetchedPageContent
from exchange_info.models import (
    CollectionAudit,
    DestinationProfile,
    ExperienceSourceType,
    PartnerUniversity,
    StudentExperienceSource,
)
from exchange_info.storage import (
    ensure_data_dirs,
    load_collection_audits,
    load_destination_profiles,
    load_student_experiences,
    replace_school_experiences,
    save_destination_profiles,
    upsert_collection_audit,
    upsert_destination_profile,
)


def _partner() -> PartnerUniversity:
    return PartnerUniversity(
        program_type="交換學生 / 自費研修",
        country="紐西蘭",
        school_name="林肯大學 Lincoln University",
        website="https://www.lincoln.ac.nz/",
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
    )


def test_experience_link_uses_full_page_summary_and_theme_points(monkeypatch) -> None:
    source = StudentExperienceSource(
        school_name="林肯大學 Lincoln University",
        country="紐西蘭",
        title="My exchange at Lincoln University",
        source_url="https://student.example.com/lincoln-exchange",
        source_type=ExperienceSourceType.ARTICLE,
        platform="student.example.com",
        summary="這個來源主要談到住宿。",
        themes=["housing"],
        content_hash="old",
    )
    monkeypatch.setattr(
        "exchange_info.experience_collector.fetch_page_content",
        lambda *args, **kwargs: FetchedPageContent(
            title="My exchange at Lincoln University",
            text=(
                "I studied abroad at Lincoln University in New Zealand. "
                "The student hall was next to campus and included shared kitchens. "
            )
            * 8,
            final_url=source.source_url,
            status="full_text",
        ),
    )
    monkeypatch.setattr(
        "exchange_info.experience_collector.summarize_student_link",
        lambda **kwargs: {
            "summary_zh": "作者在林肯大學交換期間住學生宿舍，宿舍鄰近校園並使用共用廚房。",
            "theme_points": [
                {"theme": "housing", "point_zh": "學生宿舍鄰近校園，廚房採共用形式。"}
            ],
        },
    )

    enriched = _summarize_link_content(source, _partner(), timeout_seconds=5)

    assert enriched is not None
    assert enriched.content_status == "full_text"
    assert "共用廚房" in enriched.summary
    assert "鄰近校園" in enriched.theme_summaries["housing"]


def _cityu_partner() -> PartnerUniversity:
    return PartnerUniversity(
        program_type="交換學生",
        country="香港",
        school_name="香港城市大學 City University of Hong Kong",
        website="https://www.cityu.edu.hk/",
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
    )


def _sorbonne_partner() -> PartnerUniversity:
    return PartnerUniversity(
        program_type="交換學生",
        country="法國",
        school_name="法國索邦大學 Sorbonne Université",
        website="https://www.sorbonne-universite.fr/en",
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
    )


def _tsinghua_partner() -> PartnerUniversity:
    return PartnerUniversity(
        program_type="交換學生",
        country="大陸地區",
        school_name="北京清華大學 Tsinghua University",
        website="https://www.tsinghua.edu.cn/en/",
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
    )


def _source(
    *,
    school_name: str = "林肯大學 Lincoln University",
    source_url: str = "https://example.com/lincoln-review",
    source_type: ExperienceSourceType = ExperienceSourceType.ARTICLE,
    published_at: str | None = None,
) -> StudentExperienceSource:
    return StudentExperienceSource(
        school_name=school_name,
        country="紐西蘭",
        title="My exchange experience at Lincoln University",
        source_url=source_url,
        source_type=source_type,
        platform="Example",
        language="en",
        summary="校園規模較小，人際互動可能比大型綜合大學更密切。",
        themes=["campus_culture", "social"],
        theme_summaries={
            "campus_culture": "校園規模較小，人際互動可能比大型綜合大學更密切。",
            "social": "學生常透過社團與學生組織認識同學並融入校園。",
        },
        content_status="full_text",
        perspective="student_created",
        published_at=published_at,
        discovered_at=datetime(2026, 7, 11, tzinfo=timezone.utc),
        content_hash=source_url,
    )


def test_experience_queries_use_university_and_country() -> None:
    partner = _partner()
    assert school_search_name(partner.school_name) == "Lincoln University"

    queries = build_experience_queries(partner)

    assert any("Lincoln University" in query for query, _ in queries)
    assert any("New Zealand" in query for query, _ in queries)
    assert any(source_type == "video" for _, source_type in queries)


def test_chinese_partner_queries_use_verified_english_school_name() -> None:
    partner = PartnerUniversity(
        program_type="交換學生",
        country="大陸地區",
        school_name="南京大學",
        source_url="https://cms-carrier.ntpu.edu.tw/uploads/partners.pdf",
    )

    assert school_search_name(partner.school_name) == "Nanjing University"
    assert any(
        "Nanjing University China" in query
        for query, _ in build_experience_queries(partner)
    )


def test_school_search_name_preserves_accented_characters() -> None:
    assert school_search_name("法國索邦大學 Sorbonne Université") == "Sorbonne Université"


def test_sorbonne_queries_use_unambiguous_english_alias() -> None:
    queries = build_experience_queries(_sorbonne_partner())

    assert all("Sorbonne University" in query for query, _ in queries)


def test_normalize_source_url_removes_tracking_but_keeps_video_id() -> None:
    assert normalize_source_url(
        "https://www.youtube.com/watch?v=abc123&utm_source=test&feature=share"
    ) == "https://youtube.com/watch?v=abc123"


def test_normalize_source_url_collapses_review_pagination() -> None:
    assert normalize_source_url(
        "https://studyabroad101.com/programs/lincoln-exchange?page=3&utm_source=test"
    ) == "https://studyabroad101.com/programs/lincoln-exchange"


def test_candidate_rejects_generic_recruitment_page() -> None:
    source = _candidate_to_source(
        {
            "search_type": "text",
            "href": "https://academicjobs.com/employers/lincoln-university/123",
            "title": "Lincoln University jobs and student careers",
            "body": "Review open jobs and campus opportunities at Lincoln University.",
        },
        _partner(),
    )

    assert source is None


def test_candidate_rejects_institutional_partnership_news() -> None:
    source = _candidate_to_source(
        {
            "search_type": "text",
            "href": "https://partner.example.edu/news/lincoln-partnership",
            "title": "Partner university joins hands with Lincoln University",
            "body": (
                "The universities established a partnership to enhance student "
                "exchange and campus opportunities."
            ),
        },
        _partner(),
    )

    assert source is None


def test_candidate_rejects_study_agency_marketing_page() -> None:
    source = _candidate_to_source(
        {
            "search_type": "text",
            "href": "https://studies-overseas.com/universities/lincoln-university",
            "title": "Lincoln University rankings, programs and reviews",
            "body": "Explore student life, campus housing and study abroad options.",
        },
        _partner(),
    )

    assert source is None


def test_candidate_rejects_generic_course_fee_ranking_catalog() -> None:
    source = _candidate_to_source(
        {
            "search_type": "text",
            "href": "https://catalog.example.com/lincoln-university",
            "title": "Lincoln University: Courses, Fees, Rankings, Scholarships",
            "body": "Read campus reviews and explore study abroad admissions.",
        },
        _partner(),
    )

    assert source is None


def test_candidate_rejects_exchange_program_announcement() -> None:
    source = _candidate_to_source(
        {
            "search_type": "text",
            "href": "https://partner.example.edu/news/lincoln-spring-2027",
            "title": "Lincoln University Student Exchange Program Spring 2027",
            "body": "Application announcement for exchange students in New Zealand.",
        },
        _partner(),
    )

    assert source is None


def test_candidate_rejects_cooperation_partner_directory() -> None:
    source = _candidate_to_source(
        {
            "search_type": "text",
            "href": "https://partner.example.edu/cooperation/lincoln-university",
            "title": "Lincoln University Cooperation Partner Details",
            "body": "Institutional cooperation and student exchange campus information.",
        },
        _partner(),
    )

    assert source is None


def test_candidate_rejects_cooperation_directory_by_url_path() -> None:
    source = _candidate_to_source(
        {
            "search_type": "text",
            "href": (
                "https://partner.example.edu/research/"
                "cooperation-partner-details/lincoln-university"
            ),
            "title": "Lincoln University - Partner University",
            "body": "Campus cooperation, exchange and student review information.",
        },
        _partner(),
    )

    assert source is None


def test_eduopinions_school_page_gets_clean_review_title() -> None:
    source = _candidate_to_source(
        {
            "search_type": "text",
            "href": "https://eduopinions.com/universities/universities-in-new-zealand/lincoln-university",
            "title": "Lincoln University Reviews & Rankings Other Search Results",
            "body": (
                "Students review campus life, courses and housing at Lincoln "
                "University in New Zealand."
            ),
        },
        _partner(),
    )

    assert source is not None
    assert source.title == "Lincoln University｜學生評價彙整"


def test_refresh_preserves_previously_accepted_source_when_search_is_empty() -> None:
    previous = _source(
        source_url="https://studyabroad101.com/programs/lincoln-exchange/reviews/1"
    )

    refreshed = merge_refreshed_student_experiences(
        _partner(),
        [previous],
        [],
    )

    assert [source.source_url for source in refreshed] == [previous.source_url]


def test_refresh_cleans_title_of_previously_accepted_iagora_source() -> None:
    previous = _source(
        school_name="北京清華大學 Tsinghua University",
        source_url="https://iagora.com/studies/uni/Tsinghua_University::show=reviews:type=life",
    ).model_copy(
        update={
            "country": "大陸地區",
            "title": "Student life - Reviews of Tsinghua University and other results",
        }
    )

    refreshed = merge_refreshed_student_experiences(
        _tsinghua_partner(), [previous], [], max_sources=12
    )

    assert len(refreshed) == 1
    assert refreshed[0].title == "Tsinghua University｜學生生活評價"


def test_refresh_keeps_clean_study_abroad_review_title_idempotent() -> None:
    previous = _source(
        school_name="北京清華大學 Tsinghua University",
        source_url="https://studyabroad101.com/programs/tsinghua-university/reviews/1",
    ).model_copy(
        update={
            "country": "大陸地區",
            "title": "Worth it｜Tsinghua University 交換心得｜Tsinghua University 交換心得",
        }
    )

    refreshed = merge_refreshed_student_experiences(
        _tsinghua_partner(), [previous], [], max_sources=12
    )

    assert refreshed[0].title == "Worth it｜Tsinghua University 交換心得"


def test_refresh_removes_previously_stored_marketing_catalog() -> None:
    previous = _source(
        source_url="https://catalog.example.com/lincoln-university"
    ).model_copy(
        update={"title": "Lincoln University: Courses, Fees, Rankings, Scholarships"}
    )

    refreshed = merge_refreshed_student_experiences(
        _partner(),
        [previous],
        [],
    )

    assert refreshed == []


def test_candidate_rejects_academgo_university_catalog() -> None:
    source = _candidate_to_source(
        {
            "search_type": "text",
            "href": "https://academgo.com/universities-in-new-zealand/lincoln-university",
            "title": "Study at Lincoln University | Academgo",
            "body": "Student clubs, campus life and admissions information.",
        },
        _partner(),
    )

    assert source is None


def test_candidate_rejects_acceptance_rate_discussion() -> None:
    source = _candidate_to_source(
        {
            "search_type": "text",
            "href": "https://reddit.com/r/studyabroad/comments/abc/lincoln_acceptance_rate",
            "title": "What is Lincoln University's acceptance rate?",
            "body": "International students discuss admissions chances and campus study.",
        },
        _partner(),
    )

    assert source is None


def test_warsaw_technology_rejects_university_of_warsaw_review() -> None:
    partner = PartnerUniversity(
        program_type="交換學生",
        country="波蘭",
        school_name="波蘭華沙理工大學Warsaw University of Technology",
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
    )
    source = _candidate_to_source(
        {
            "search_type": "text",
            "href": "https://iagora.com/studies/uni/Uniwersytet_Warszawski::show=reviews",
            "title": (
                "Student life - Reviews of Uniwersytet Warszawski "
                "Warsaw University of Technology search results"
            ),
            "body": "Student reviews about studying and housing in Warsaw, Poland.",
        },
        partner,
    )

    assert source is None


def test_wuhan_rejects_science_and_technology_university_video() -> None:
    partner = PartnerUniversity(
        program_type="交換學生",
        country="大陸地區",
        school_name="武漢大學 Wuhan University",
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
    )
    source = _candidate_to_source(
        {
            "search_type": "video",
            "content": "https://youtube.com/watch?v=wrong-school",
            "title": "Dorm vlog at Wuhan University of Science and Technology",
            "description": "Student life and housing in Wuhan University search results.",
        },
        partner,
    )

    assert source is None


def test_candidate_rejects_studyabroad_city_landing_page() -> None:
    source = _candidate_to_source(
        {
            "search_type": "text",
            "href": "https://studyabroad101.com/cities/new-zealand/lincoln",
            "title": "Study Abroad in Lincoln, New Zealand",
            "body": "Find exchange programs, student reviews and campus information.",
        },
        _partner(),
    )

    assert source is None


def test_studyabroad_program_index_ignores_unrelated_snippet_claims() -> None:
    source = _candidate_to_source(
        {
            "search_type": "text",
            "href": "https://studyabroad101.com/programs/lincoln-university-direct-enrollment-exchange",
            "title": "Lincoln University direct enrollment exchange student reviews",
            "body": (
                "Student reviews in New Zealand. Another rural agriculture program "
                "has farms and countryside housing."
            ),
        },
        _partner(),
    )

    assert source is not None
    assert "challenges" not in source.themes
    assert "農業" not in source.summary


def test_candidate_rejects_broken_replacement_character_url() -> None:
    source = _candidate_to_source(
        {
            "search_type": "text",
            "href": "https://example.com/lincoln-student-\ufffd-review",
            "title": "My Lincoln University student review",
            "body": "My exchange student experience in New Zealand.",
        },
        _partner(),
    )

    assert source is None


def test_cityu_candidate_rejects_chinese_university_false_positive() -> None:
    source = _candidate_to_source(
        {
            "search_type": "text",
            "href": "https://studyabroad101.com/programs/chinese-university-of-hong-kong/reviews/21121",
            "title": "My journey in Asia's world city - Chinese University of Hong Kong review",
            "body": "A student review about study abroad life in Hong Kong.",
        },
        _cityu_partner(),
    )

    assert source is None


def test_cityu_candidate_accepts_exact_school_identity() -> None:
    source = _candidate_to_source(
        {
            "search_type": "text",
            "href": "https://studyabroad101.com/universities/city-university-of-hong-kong",
            "title": "City University of Hong Kong student reviews",
            "body": "Exchange students review campus life and housing in Hong Kong.",
        },
        _cityu_partner(),
    )

    assert source is not None
    assert source.title == "City University of Hong Kong｜學生評價彙整"
    assert source.language == "en"


def test_sorbonne_candidate_rejects_pantheon_sorbonne() -> None:
    source = _candidate_to_source(
        {
            "search_type": "text",
            "href": "https://iagora.com/studies/uni/universite-pantheon-sorbonne-paris-1/reviews",
            "title": "Reviews of Université Panthéon-Sorbonne Paris I",
            "body": "International student reviews about campus life in Paris.",
        },
        _sorbonne_partner(),
    )

    assert source is None


def test_sorbonne_candidate_rejects_new_sorbonne_paris_three() -> None:
    source = _candidate_to_source(
        {
            "search_type": "text",
            "href": "https://studyabroad101.com/programs/micefa-new-sorbonne-university-paris-3/reviews/2974",
            "title": "Paris: challenging yet rewarding - New Sorbonne University Paris 3",
            "body": "A student review about studying in Paris.",
        },
        _sorbonne_partner(),
    )

    assert source is None


def test_sorbonne_candidate_accepts_paris_sorbonne_review() -> None:
    source = _candidate_to_source(
        {
            "search_type": "text",
            "href": "https://studyabroad101.com/programs/sorbonne-university-paris/reviews/18839",
            "title": "Trip of a Lifetime - Paris-Sorbonne University Past Review",
            "body": "A student review about exchange classes and life in Paris.",
        },
        _sorbonne_partner(),
    )

    assert source is not None
    assert "Sorbonne Université" in source.title


def test_tsinghua_candidate_rejects_generic_wentchina_guide() -> None:
    source = _candidate_to_source(
        {
            "search_type": "text",
            "href": "https://wentchina.com/tsinghua-university-student-life-guide/",
            "title": "Tsinghua University student life guide",
            "body": "A guide to campus life and housing for international students.",
        },
        _tsinghua_partner(),
    )

    assert source is None


def test_tsinghua_iagora_candidate_gets_concise_title() -> None:
    source = _candidate_to_source(
        {
            "search_type": "text",
            "href": "https://iagora.com/studies/uni/Tsinghua_University::show=reviews::type=life",
            "title": "Student life - Reviews of Tsinghua University - Campus and more",
            "body": "International students review campus life and housing at Tsinghua University.",
        },
        _tsinghua_partner(),
    )

    assert source is not None
    assert source.title == "Tsinghua University｜學生生活評價"


def test_fuzhou_candidate_rejects_different_international_studies_university() -> None:
    partner = PartnerUniversity(
        program_type="交換學生",
        country="大陸地區",
        school_name="福州大學 Fuzhou University",
        website="https://www.fzu.edu.cn/",
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
    )
    source = _candidate_to_source(
        {
            "search_type": "text",
            "href": "https://isacteach.com/campus/campus-life-at-fuzhou-university-of-international-studies",
            "title": "Campus Life at Fuzhou University of International Studies",
            "body": "Students describe campus life and dorms in Fuzhou, China.",
        },
        partner,
    )

    assert source is None


def test_fuzhou_candidate_rejects_generic_university_catalog() -> None:
    partner = PartnerUniversity(
        program_type="交換學生",
        country="大陸地區",
        school_name="福州大學 Fuzhou University",
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
    )
    source = _candidate_to_source(
        {
            "search_type": "text",
            "href": "https://alluniversity.info/china/fuzhou-university",
            "title": "Fuzhou University, China - Find Detailed Information",
            "body": "University programs, jobs and campus information.",
        },
        partner,
    )

    assert source is None


def test_ostrava_candidate_rejects_technical_university() -> None:
    partner = PartnerUniversity(
        program_type="交換學生",
        country="捷克",
        school_name="捷克奧斯特拉瓦大學University of Ostrava",
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
    )
    source = _candidate_to_source(
        {
            "search_type": "text",
            "href": "https://reddit.com/r/czech/comments/example/technical_university_of_ostrava",
            "title": "Technical University of Ostrava for computer science?",
            "body": "Students discuss classes and campus life in Ostrava.",
        },
        partner,
    )

    assert source is None


def test_go_minnesota_candidate_rejects_unrelated_outbound_program() -> None:
    partner = PartnerUniversity(
        program_type="交換學生",
        country="美國",
        school_name="美國明尼蘇達大學 University of Minnesota (GO Minnesota方案)",
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
    )
    source = _candidate_to_source(
        {
            "search_type": "text",
            "href": "https://studyabroad101.com/programs/university-of-minnesota-virtual-internships-in-montpellier/reviews/52119",
            "title": "Montpellier virtual internship student review",
            "body": "A University of Minnesota outbound program in France.",
        },
        partner,
    )

    assert source is None


def test_go_minnesota_candidate_accepts_exact_inbound_program_story() -> None:
    partner = PartnerUniversity(
        program_type="交換學生",
        country="美國",
        school_name="美國明尼蘇達大學 University of Minnesota (GO Minnesota方案)",
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
    )
    source = _candidate_to_source(
        {
            "search_type": "video",
            "content": "https://youtube.com/watch?v=go-minnesota",
            "title": "My GO Minnesota exchange student experience",
            "description": "Life at the University of Minnesota Twin Cities campus and dorms.",
        },
        partner,
    )

    assert source is not None


def test_go_minnesota_refresh_removes_stored_outbound_review_with_generated_title() -> None:
    partner = PartnerUniversity(
        program_type="交換學生",
        country="美國",
        school_name="美國明尼蘇達大學 University of Minnesota (GO Minnesota方案)",
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
    )
    previous = _source(
        school_name=partner.school_name,
        source_url="https://studyabroad101.com/programs/university-of-minnesota-senegal/reviews/1",
    ).model_copy(
        update={
            "country": "美國",
            "title": "Senegal development program｜University of Minnesota (GO Minnesota方案) 交換心得",
        }
    )

    refreshed = merge_refreshed_student_experiences(partner, [previous], [])

    assert refreshed == []


def test_minnesota_candidate_rejects_unrelated_outbound_program() -> None:
    partner = PartnerUniversity(
        program_type="雙學位",
        country="美國",
        school_name="明尼蘇達大學 University of Minnesota",
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17533",
    )
    source = _candidate_to_source(
        {
            "search_type": "text",
            "href": "https://studyabroad101.com/programs/university-of-minnesota-msid-ecuador/reviews/1",
            "title": "University of Minnesota MSID Ecuador student review",
            "body": "A University of Minnesota outbound study abroad program in Ecuador.",
        },
        partner,
    )

    assert source is None


def test_minnesota_candidate_accepts_exact_twin_cities_review_page() -> None:
    partner = PartnerUniversity(
        program_type="雙學位",
        country="美國",
        school_name="明尼蘇達大學 University of Minnesota",
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17533",
    )
    source = _candidate_to_source(
        {
            "search_type": "text",
            "href": "https://studyabroad101.com/universities/university-of-minnesota-twin-cities",
            "title": "University of Minnesota Twin Cities student reviews",
            "body": "International students discuss campus life and housing in Minneapolis.",
        },
        partner,
    )

    assert source is not None


def test_job_review_hosts_are_not_student_experiences() -> None:
    partner = PartnerUniversity(
        program_type="雙學位",
        country="美國",
        school_name="內布拉斯加大學醫學中心分校 University of Nebraska Medical Center",
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17533",
    )

    for href in (
        "https://glassdoor.com/Reviews/University-of-Nebraska-Medical-Center-Reviews-E123.htm",
        "https://simplyhired.com/company/University-of-Nebraska-Medical-Center/reviews",
    ):
        source = _candidate_to_source(
            {
                "search_type": "text",
                "href": href,
                "title": "University of Nebraska Medical Center employee reviews",
                "body": "Employees review jobs, pay and management.",
            },
            partner,
        )
        assert source is None


def test_uc_irvine_candidate_rejects_outbound_provider_and_internship_pages() -> None:
    partner = PartnerUniversity(
        program_type="雙學位",
        country="美國",
        school_name="加州大學爾灣分校 University of California, Irvine",
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17533",
    )

    for href in (
        "https://studyabroad101.com/providers/university-of-california-irvine",
        "https://studyabroad101.com/programs/university-of-california-irvine-summer-global-internships",
    ):
        source = _candidate_to_source(
            {
                "search_type": "text",
                "href": href,
                "title": "Study abroad with University of California Irvine",
                "body": "An outbound global internship provider page.",
            },
            partner,
        )
        assert source is None


def test_fordham_candidate_rejects_outbound_london_program() -> None:
    partner = PartnerUniversity(
        program_type="雙學位",
        country="美國",
        school_name="福坦莫大學 Fordham University",
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17533",
    )
    source = _candidate_to_source(
        {
            "search_type": "text",
            "href": "https://studyabroad101.com/programs/fordham-university-london-liberal-arts/reviews/11116",
            "title": "London was the time of my life | Fordham University review",
            "body": "A review of Fordham's outbound London liberal arts program.",
        },
        partner,
    )

    assert source is None


def test_generic_directory_and_impostor_hosts_are_not_student_experiences() -> None:
    partner = PartnerUniversity(
        program_type="雙學位",
        country="澳洲",
        school_name="澳洲昆士蘭大學 The University of Queensland",
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17533",
    )

    for href in (
        "https://amberstudent.com/places/search/university-of-queensland",
        "https://inigoleigh.blogspot.com/2021/10/student-hall-directory.html",
        "https://niche.com/colleges/the-university-of-queensland",
        "https://usnews.com/best-colleges/the-university-of-queensland",
        "https://unigo.com/colleges/the-university-of-queensland",
        "https://queenslanduniversity.au/",
        "https://wikipedia.org/wiki/The_University_of_Queensland",
        "https://princetonreview.com/college/the-university-of-queensland",
        "https://collegedunia.com/australia/university/queensland/reviews",
    ):
        source = _candidate_to_source(
            {
                "search_type": "text",
                "href": href,
                "title": "The University of Queensland student reviews",
                "body": "Campus life, housing and student experience information.",
            },
            partner,
        )
        assert source is None


def test_rennes_candidate_rejects_unrelated_ciee_liberal_arts_program() -> None:
    partner = PartnerUniversity(
        program_type="交換學生",
        country="法國",
        school_name="雷恩商學院 Rennes School of Business",
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
    )
    source = _candidate_to_source(
        {
            "search_type": "text",
            "href": "https://studyabroad101.com/programs/ciee-rennes-liberal-arts/reviews/1648",
            "title": "Study Abroad in Rennes, France | Rennes School of Business results",
            "body": "A CIEE Rennes liberal arts student review.",
        },
        partner,
    )

    assert source is None


def test_youtube_candidate_removes_concatenated_search_results() -> None:
    partner = PartnerUniversity(
        program_type="交換學生",
        country="波蘭",
        school_name="波蘭華沙生命科學大學 Warsaw University of Life Sciences",
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
    )
    source = _candidate_to_source(
        {
            "search_type": "video",
            "content": "https://youtube.com/watch?v=sggw-dorm",
            "title": "SGGW Dorm Tour Warsaw | Student Room + Life in Poland ...Other search result",
            "description": "A student dorm tour at Warsaw University of Life Sciences.",
        },
        partner,
    )

    assert source is not None
    assert source.title == "SGGW Dorm Tour Warsaw | Student Room + Life in Poland ..."


def test_sorbonne_candidate_rejects_third_party_language_program() -> None:
    source = _candidate_to_source(
        {
            "search_type": "text",
            "href": "https://studyabroad101.com/programs/nrcsa-paris-sorbonne-university/reviews/6516",
            "title": "Learning French at the Sorbonne and Living in Paris",
            "body": "A review of a third-party language programme in Paris.",
        },
        _sorbonne_partner(),
    )

    assert source is None


def test_study_abroad_review_title_removes_concatenated_results() -> None:
    source = _candidate_to_source(
        {
            "search_type": "text",
            "href": "https://studyabroad101.com/programs/city-university-of-hong-kong/reviews/28712",
            "title": (
                "Holy Crap that went by fast!!! | A review for City University "
                "of Hong Kong Chinese University of Hong Kong review"
            ),
            "body": "A student review about exchange classes and housing in Hong Kong.",
        },
        _cityu_partner(),
    )

    assert source is not None
    assert source.title == "Holy Crap that went by fast!!!｜City University of Hong Kong 交換心得"
    assert "Chinese University" not in source.title


def test_official_about_page_is_not_a_student_experience() -> None:
    source = _candidate_to_source(
        {
            "search_type": "text",
            "href": "https://www.cityu.edu.hk/about",
            "title": "About CityUHK | City University of Hong Kong",
            "body": "Discover campus life at City University of Hong Kong.",
        },
        _cityu_partner(),
    )

    assert source is None


def test_official_student_story_is_kept() -> None:
    source = _candidate_to_source(
        {
            "search_type": "text",
            "href": "https://www.cityu.edu.hk/international/student-stories/exchange-life",
            "title": "Student story: my exchange life at City University of Hong Kong",
            "body": "An exchange student shares a personal campus and housing experience.",
        },
        _cityu_partner(),
    )

    assert source is not None


def test_official_sibling_subdomain_is_not_a_student_experience() -> None:
    partner = PartnerUniversity(
        program_type="交換學生",
        country="日本",
        school_name="日本東北大學 Tohoku University",
        website="https://www.eng.tohoku.ac.jp/english/",
        source_url="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554",
    )
    source = _candidate_to_source(
        {
            "search_type": "text",
            "href": "https://lifesci.tohoku.ac.jp/en/curriculums/studentlife",
            "title": "Student Life | Tohoku University",
            "body": "Campus and student life information at Tohoku University.",
        },
        partner,
    )

    assert source is None


def test_video_candidate_keeps_public_author_name() -> None:
    source = _candidate_to_source(
        {
            "search_type": "video",
            "content": "https://www.youtube.com/watch?v=abc123",
            "title": "Lincoln University exchange student vlog",
            "description": "My student exchange experience in New Zealand",
            "uploader": "Public Student Channel",
            "published": "2025-08-10",
        },
        _partner(),
    )

    assert source is not None
    assert source.author_name == "Public Student Channel"


def test_digest_counts_sources_and_builds_theme_highlights() -> None:
    sources = [
        _source(published_at="2025-08-10"),
        _source(
            source_url="https://reddit.com/r/example/lincoln",
            source_type=ExperienceSourceType.COMMUNITY,
            published_at="2024-03-02",
        ),
    ]

    digest = build_experience_digest("林肯大學 Lincoln University", "紐西蘭", sources)

    assert digest.total_sources == 2
    assert digest.article_count == 1
    assert digest.community_count == 1
    assert digest.highlights[0].source_count == 2
    assert "校園規模較小" in digest.highlights[0].summary
    assert digest.highlights[0].key_points
    assert all("來源談到" not in point and "來源提到" not in point for point in digest.highlights[0].key_points)
    assert digest.common_strengths[0].source_count == 2
    assert digest.source_years == [2025, 2024]
    assert {highlight.theme for highlight in digest.highlights} == {
        "campus_culture",
        "social",
    }


def test_digest_does_not_present_generic_source_description_as_a_key_point() -> None:
    source = _source().model_copy(
        update={
            "themes": ["academics"],
            "summary": "這個來源主要談到課業與教學，可搭配其他年份與不同身分的心得交叉查看。",
        }
    )

    digest = build_experience_digest(source.school_name, source.country, [source])

    assert digest.highlights == []


def test_digest_does_not_treat_discovery_date_as_publication_year() -> None:
    digest = build_experience_digest(
        "林肯大學 Lincoln University", "紐西蘭", [_source()]
    )

    assert digest.source_years == []


def test_digest_filters_challenge_pages_navigation_and_wrong_chinese_school() -> None:
    blocked = StudentExperienceSource(
        school_name="南京大學",
        country="大陸地區",
        title="Just a moment...",
        source_url="https://dcard.tw/f/studyabroad/p/example",
        source_type=ExperienceSourceType.ARTICLE,
        platform="Dcard",
        summary="Verification successful. Waiting for www.dcard.tw to respond。",
        themes=["safety", "challenges"],
        theme_summaries={"challenges": "您操作的頻率過快，或使用 VPN 或 Proxy 服務。"},
        content_status="full_text",
        content_hash="blocked",
    )
    navigation = StudentExperienceSource(
        school_name="南京大學",
        country="大陸地區",
        title="Nanjing University Reviews | CUCAS",
        source_url="https://nju.cucas.cn/reviews",
        source_type=ExperienceSourceType.ARTICLE,
        platform="CUCAS",
        summary=(
            "Find a Program Chinese Programs MBBS Course Program Lists "
            "About Us About CUCAS University Application Accommodation Booking "
            "Airport Pick-Up Money Transfer Contact Us"
        ),
        themes=["academics", "housing"],
        theme_summaries={"housing": "About Us About CUCAS Contact Us"},
        content_status="full_text",
        content_hash="navigation",
    )
    navigation_chrome = StudentExperienceSource(
        school_name="南京大學",
        country="大陸地區",
        title="Exchange at Nanjing University",
        source_url="https://example.com/nju-repost",
        source_type=ExperienceSourceType.ARTICLE,
        platform="Repost",
        summary="Life Housing Student Activities Dining",
        themes=["housing", "food", "transport"],
        theme_summaries={"housing": "Life Housing Student Activities Dining"},
        content_status="full_text",
        content_hash="navigation-chrome",
    )
    wrong_school = StudentExperienceSource(
        school_name="天津大學",
        country="大陸地區",
        title="My Time at Tsinghua University",
        source_url="https://medium.com/example/tsinghua",
        source_type=ExperienceSourceType.ARTICLE,
        platform="Medium",
        summary="作者在清華大學交換一學期，描述北京校園生活。",
        themes=["campus_culture"],
        theme_summaries={"campus_culture": "清華大學校園很大。"},
        content_status="full_text",
        content_hash="wrong-school",
    )

    assert build_experience_digest(
        "南京大學", "大陸地區", [blocked, navigation, navigation_chrome]
    ).total_sources == 0
    assert build_experience_digest(
        "天津大學", "大陸地區", [wrong_school]
    ).total_sources == 0


def test_digest_integrates_visible_source_summaries_into_three_decision_groups() -> None:
    rows = [
        StudentExperienceSource(
            school_name="南京大學",
            country="大陸地區",
            title="Reflections of an Exchange Student at Nanjing University",
            source_url="https://stuex.nju.edu.cn/en_/student-reflection",
            source_type=ExperienceSourceType.ARTICLE,
            platform="Nanjing University",
            summary="學生認為合作課堂值得推薦，也因小組合作建立友誼。",
            themes=["academics"],
            theme_summaries={
                "academics": "與本地學生合作的課堂值得推薦，也因小組合作建立友誼。"
            },
            content_status="full_text",
            perspective="official_student_story",
            published_at="2018-07-23",
            content_hash="nju-one",
        ),
        StudentExperienceSource(
            school_name="南京大學",
            country="大陸地區",
            title="Exchange at Nanjing University",
            source_url="https://stuex.nju.edu.cn/en_/exchange-at-nju",
            source_type=ExperienceSourceType.ARTICLE,
            platform="Nanjing University",
            summary="課程多元、教授友善且願意提供協助。",
            themes=["academics"],
            theme_summaries={
                "academics": "課程選擇多元、教授友善且願意提供協助。"
            },
            content_status="full_text",
            perspective="official_student_story",
            published_at="2018-09-19",
            content_hash="nju-two",
        ),
        StudentExperienceSource(
            school_name="南京大學",
            country="大陸地區",
            title="Nanjing University course presentation review",
            source_url="https://example.com/nju-course-pressure",
            source_type=ExperienceSourceType.ARTICLE,
            platform="Student Blog",
            summary="分組簡報帶來壓力，準備時間比預期長。",
            themes=["academics"],
            theme_summaries={"academics": "分組簡報帶來壓力，準備時間比預期長。"},
            content_status="full_text",
            published_at="2022-04-12",
            content_hash="nju-three",
        ),
        StudentExperienceSource(
            school_name="南京大學",
            country="大陸地區",
            title="English courses at Nanjing University",
            source_url="https://example.com/nju-limited-courses",
            source_type=ExperienceSourceType.ARTICLE,
            platform="Student Blog",
            summary="英文授課課程數量有限，排課選擇需要提早確認。",
            themes=["academics"],
            theme_summaries={"academics": "英文授課課程數量有限，排課選擇需要提早確認。"},
            content_status="full_text",
            published_at="2023-09-01",
            content_hash="nju-four",
        ),
    ]

    digest = build_experience_digest("南京大學", "大陸地區", rows)

    assert digest.total_sources == 4
    assert digest.common_strengths
    assert digest.common_challenges
    assert digest.mixed_opinions
    visible_urls = {source.source_url for source in digest.sources}
    assert all(
        set(insight.source_urls).issubset(visible_urls)
        for group in (
            digest.common_strengths,
            digest.common_challenges,
            digest.mixed_opinions,
        )
        for insight in group
    )


def test_replace_school_experiences_preserves_other_schools(tmp_path) -> None:
    ensure_data_dirs(tmp_path)
    other = _source(
        school_name="其他大學 Other University",
        source_url="https://example.com/other",
    )
    replace_school_experiences(other.school_name, [other], tmp_path)

    replacement = _source(source_url="https://example.com/new-lincoln-review")
    rows = replace_school_experiences(replacement.school_name, [replacement], tmp_path)

    assert {row.source_url for row in rows} == {
        "https://example.com/other",
        "https://example.com/new-lincoln-review",
    }


def test_replace_school_experiences_consolidates_alias_and_duplicate_url(tmp_path) -> None:
    ensure_data_dirs(tmp_path)
    alias = _source(
        school_name="諾歐商學院 NEOMA Business School",
        source_url="https://example.com/neoma-review",
    )
    replace_school_experiences(alias.school_name, [alias], tmp_path)
    duplicate_at_other_school = _source(
        school_name="其他大學 Other University",
        source_url=alias.source_url,
    )
    replace_school_experiences(
        duplicate_at_other_school.school_name,
        [duplicate_at_other_school],
        tmp_path,
    )
    canonical = _source(
        school_name="法國諾歐商學院 NEOMA Business School",
        source_url=alias.source_url,
    )

    rows = replace_school_experiences(canonical.school_name, [canonical], tmp_path)

    assert len(rows) == 1
    assert rows[0].school_name == canonical.school_name


def test_collection_audit_upserts_by_school_and_collector(tmp_path) -> None:
    ensure_data_dirs(tmp_path)
    upsert_collection_audit(
        CollectionAudit(
            school_name="林肯大學 Lincoln University",
            collector="experiences",
            status="no_results",
        ),
        tmp_path,
    )
    upsert_collection_audit(
        CollectionAudit(
            school_name="林肯大學 Lincoln University",
            collector="experiences",
            status="completed",
            result_count=2,
        ),
        tmp_path,
    )

    audits = load_collection_audits(tmp_path)
    assert len(audits) == 1
    assert audits[0].status == "completed"
    assert audits[0].result_count == 2


def test_collection_audit_upserts_across_chinese_name_aliases(tmp_path) -> None:
    ensure_data_dirs(tmp_path)
    upsert_collection_audit(
        CollectionAudit(
            school_name="諾歐商學院 NEOMA Business School",
            collector="experiences",
            status="no_results",
        ),
        tmp_path,
    )
    upsert_collection_audit(
        CollectionAudit(
            school_name="法國諾歐商學院 NEOMA Business School",
            collector="experiences",
            status="completed",
        ),
        tmp_path,
    )

    audits = load_collection_audits(tmp_path)
    assert len(audits) == 1
    assert audits[0].status == "completed"


def test_destination_profile_upserts_across_chinese_name_aliases(tmp_path) -> None:
    ensure_data_dirs(tmp_path)
    upsert_destination_profile(
        DestinationProfile(
            school_name="諾歐商學院 NEOMA Business School",
            country="法國",
            city="Rouen",
        ),
        tmp_path,
    )
    upsert_destination_profile(
        DestinationProfile(
            school_name="法國諾歐商學院 NEOMA Business School",
            country="法國",
            city="Rouen / Reims",
        ),
        tmp_path,
    )

    profiles = load_destination_profiles(tmp_path)
    assert len(profiles) == 1
    assert profiles[0].city == "Rouen / Reims"


def test_experience_api_reads_cache_and_refreshes_selected_school(tmp_path, monkeypatch) -> None:
    ensure_data_dirs(tmp_path)
    partner = _partner()
    cached = _source()
    replace_school_experiences(partner.school_name, [cached], tmp_path)
    monkeypatch.setattr("exchange_info.api.fetch_partner_universities", lambda: [partner])
    refreshed = _source(source_url="https://example.com/refreshed")
    monkeypatch.setattr(
        "exchange_info.api.collect_student_experiences",
        lambda partner, max_sources=12: [refreshed],
    )
    client = TestClient(create_app(tmp_path))

    cached_response = client.get(
        "/student-experiences", params={"school": partner.school_name}
    )
    assert cached_response.status_code == 200
    assert cached_response.json()["total_sources"] == 1
    coverage = client.get("/coverage").json()
    assert coverage["total_partner_schools"] == 1
    assert coverage["experience_school_count"] == 1
    assert coverage["experience_checked_count"] == 1
    assert coverage["experience_source_count"] == 1
    assert coverage["partners"][0]["experience_status"] == "completed"

    refreshed_response = client.post(
        "/student-experiences/refresh", params={"school": partner.school_name}
    )
    assert refreshed_response.status_code == 200
    refreshed_urls = {
        source["source_url"] for source in refreshed_response.json()["sources"]
    }
    assert refreshed.source_url in refreshed_urls
    assert cached.source_url in refreshed_urls
    stored_urls = {source.source_url for source in load_student_experiences(tmp_path)}
    assert stored_urls == {cached.source_url, refreshed.source_url}
    assert load_collection_audits(tmp_path)[0].status == "completed"


def test_experience_refresh_records_verified_no_results(tmp_path, monkeypatch) -> None:
    ensure_data_dirs(tmp_path)
    partner = _partner()
    monkeypatch.setattr("exchange_info.api.fetch_partner_universities", lambda: [partner])
    monkeypatch.setattr(
        "exchange_info.api.collect_student_experiences",
        lambda partner, max_sources=12: [],
    )
    client = TestClient(create_app(tmp_path))

    response = client.post(
        "/student-experiences/refresh", params={"school": partner.school_name}
    )
    coverage = client.get("/coverage").json()

    assert response.status_code == 200
    assert coverage["experience_checked_count"] == 1
    assert coverage["experience_school_count"] == 0
    assert coverage["partners"][0]["experience_status"] == "no_results"


def test_destination_profile_api_returns_verified_official_summary(tmp_path, monkeypatch) -> None:
    ensure_data_dirs(tmp_path)
    partner = _partner()
    save_destination_profiles(
        [
            DestinationProfile(
                school_name=partner.school_name,
                country=partner.country,
                city="Lincoln, Canterbury",
                cost_summary="自炊宿舍 NZ$245-320／週",
                coverage_status="official_verified",
            )
        ],
        tmp_path,
    )
    monkeypatch.setattr("exchange_info.api.fetch_partner_universities", lambda: [partner])
    client = TestClient(create_app(tmp_path))

    response = client.get(
        "/destination-profile", params={"school": partner.school_name}
    )
    list_response = client.get("/destination-profiles")
    coverage = client.get("/coverage").json()

    assert response.status_code == 200
    assert response.json()["city"] == "Lincoln, Canterbury"
    assert list_response.status_code == 200
    assert list_response.json()[0]["city"] == "Lincoln, Canterbury"
    assert coverage["destination_profile_count"] == 1
    assert coverage["partners"][0]["destination_status"] == "official_verified"
