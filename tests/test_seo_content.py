from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.testclient import TestClient

from exchange_info.models import PartnerProgramOption, PartnerUniversity
from exchange_info.seo import EDITORIAL_PATHS, SeoSettings, create_seo_router, partner_details, partner_id


def partner(**updates):
    values = dict(school_name="測試大學", country="日本", program_type="交換", source_url="https://www.cgu.edu.tw/test",
                  eligibility="GPA 3.0；語言 IELTS 6.5。", study_period="一學期", tuition_info="免繳合作校學費")
    return PartnerUniversity(**{**values, **updates})


def test_identical_program_option_is_removed_but_distinct_conditions_survive():
    p = partner()
    duplicate = PartnerProgramOption(**{k: v for k, v in p.model_dump().items() if k in PartnerProgramOption.model_fields})
    changed = duplicate.model_copy(update={"program_type": "另一方案", "eligibility": "GPA 3.5"})
    p = p.model_copy(update={"program_options": [duplicate, changed, changed]})
    html = partner_details(p)
    assert html.count("GPA 3.0") == 1
    assert html.count("GPA 3.5") == 1
    assert html.count("免繳合作校學費") == 1
    assert "另一方案：方案差異" in html


def test_mixed_quota_is_not_promoted_to_confirmed_current_seats():
    soup = BeautifulSoup(partner_details(partner(quota="2 2027 春梯次暫估 1 名（以一學期交換為原則）")), "html.parser")
    values = {dt.get_text(): dt.find_next_sibling("dd").get_text() for dt in soup.select("dt")}
    assert values["來源列載數字（年度與口徑待確認）"] == "2"
    assert values["來源中的目標梯次暫估（非核定）"].startswith("2027 春梯次暫估 1 名")
    assert values["當期名額確認狀態"] == "待確認"
    assert "不可相加" in values["名額閱讀提醒"]
    assert values["來源適用學年度"] == "來源未明確標示，待確認"


def test_source_provenance_survives_same_facts_in_different_program():
    p = partner()
    alternative = PartnerProgramOption(program_type=p.program_type, eligibility=p.eligibility, source_url="https://other.edu/program")
    html = partner_details(p.model_copy(update={"program_options": [alternative]}))
    assert "https://other.edu/program" in html and html.count("GPA 3.0") == 1


def test_topic_pages_are_crawlable_linked_and_specific_to_each_home():
    app = FastAPI()
    p = partner()
    app.include_router(create_seo_router(SeoSettings("https://example.com", True), lambda _: ([p], None)))
    with TestClient(app) as client:
        assert "全台大學交換學生" in client.get("/schools").text
        sitemap = client.get("/sitemaps/pages.xml").text
        for path in EDITORIAL_PATHS:
            assert "https://example.com" + path in sitemap
            response = client.get(path)
            soup = BeautifulSoup(response.text, "html.parser")
            assert response.status_code == 200 and len(soup.select("h1")) == 1
            assert soup.select_one('link[rel="canonical"]')["href"] == "https://example.com" + path
        country = client.get("/destinations/japan").text
        assert f"/schools/cgu/partners/{partner_id(p)}" in country
        assert f"/schools/ntu/partners/{partner_id(p)}" in country
        assert "生活費" in country and "不是當期名額" in country
        detail = client.get(f"/schools/cgu/partners/{partner_id(p)}").text
        assert "/destinations/japan" in detail and "/guides/exchange-budget" in detail
        assert "申請資格與語言" in detail and "研修期間與申請期限" in detail
        assert client.get("/destinations/unknown").status_code == 404
        assert client.get("/guides/unknown").status_code == 404


def test_long_text_is_split_without_changing_or_executing_source_content():
    html = partner_details(partner(eligibility="第一項。第二項；<script>alert(1)</script>"))
    soup = BeautifulSoup(html, "html.parser")
    assert not soup.select("script")
    assert soup.find("p", string="第一項。") and soup.find("p", string="第二項；")
    assert "<script>alert(1)</script>" in soup.get_text()
