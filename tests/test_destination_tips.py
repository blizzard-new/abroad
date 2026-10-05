"""Country-level "before you go" guides: the bundled data, its validator and the API."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from exchange_info import destination_tips
from exchange_info.api import create_app
from exchange_info.destination_tips import TOPICS, load_guides, validate_guides

ROOT = Path(__file__).resolve().parents[1]
LOCATIONS = ROOT / "src" / "exchange_info" / "official_data" / "university_locations.jsonl"


def destination_countries() -> set[str]:
    rows = [json.loads(line) for line in LOCATIONS.read_text(encoding="utf-8").splitlines() if line.strip()]
    return {row["country"] for row in rows} - {"臺灣"}


def good_payload() -> dict:
    tip = {"title": "查簽證", "detail": "出發前查官方頁面。", "importance": "must",
           "sources": [{"name": "外交部", "url": "https://www.boca.gov.tw/"}], "checked_at": "2026-10-04"}
    guide = {"country": "日本", "display_name": "日本", "topics": [{"topic": "documents", "title": TOPICS["documents"], "tips": [tip]}],
             "review_status": "draft", "reviewers": [], "last_checked": "2026-10-04"}
    return {"version": 1, "guides": {"日本": guide}}


@pytest.fixture
def client(tmp_path):
    return TestClient(create_app(tmp_path))


# ----------------------------------------------------------------------------- the bundled data


def test_the_bundled_guides_pass_the_validator():
    payload = json.loads(destination_tips.GUIDES_FILE.read_text(encoding="utf-8"))
    assert validate_guides(payload) == []


def test_every_destination_country_has_a_guide_and_nothing_else_does():
    assert set(load_guides()) == destination_countries()


def test_nothing_is_marked_reviewed_without_two_reviewers():
    for guide in load_guides().values():
        assert guide.review_status == "draft" and guide.reviewers == [], guide.country
        assert "尚未經過兩位審核者" in guide.disclaimer


def test_every_tip_names_an_https_source_and_the_date_it_was_checked():
    for guide in load_guides().values():
        for topic in guide.topics:
            for tip in topic.tips:
                assert tip.sources and all(source.url.startswith("https://") and source.name for source in tip.sources), (guide.country, tip.title)
                assert tip.checked_at == "2026-10-04"


def test_china_carries_the_hidden_details_a_student_would_otherwise_look_up():
    china = load_guides()["大陸地區"]
    assert china.display_name == "中國大陸"
    topics = {topic.topic: topic for topic in china.topics}
    assert {"documents", "phone_internet", "payment", "housing", "health_insurance", "safety_law", "emergency"} <= set(topics)
    text = "\n".join(tip.title + tip.detail for topic in china.topics for tip in topic.tips)
    for needle in ("台胞證", "國際漫遊", "VPN", "實名", "微信支付", "支付寶", "24 小時", "備份", "(02)2533-9995", "陸委會"):
        assert needle in text, needle
    assert len(topics["phone_internet"].tips) >= 5 and len(topics["payment"].tips) >= 5


def test_other_countries_share_the_basics_and_say_the_details_are_still_coming():
    japan = load_guides()["日本"]
    titles = [tip.title for topic in japan.topics for tip in topic.tips]
    assert any("簽證與入境" in title for title in titles) and any("緊急聯絡中心" in title for title in titles)
    assert any("110" in tip.detail and "119" in tip.detail for topic in japan.topics for tip in topic.tips)
    germany = load_guides()["德國"]
    assert "還在整理" in germany.intro and "110" in "".join(tip.detail for topic in germany.topics for tip in topic.tips)
    hong_kong = load_guides()["香港"]
    assert any("陸委會" in tip.title for topic in hong_kong.topics for tip in topic.tips), "港澳 register with 陸委會, not 外交部"


def test_the_emergency_center_number_is_given_exactly_as_the_foreign_ministry_publishes_it():
    tip = next(tip for topic in load_guides()["法國"].topics for tip in topic.tips if "緊急聯絡中心" in tip.title)
    assert "0800-085-095" in tip.detail and "+886-800-085-095" in tip.detail


# ----------------------------------------------------------------------------- the validator


def test_a_valid_payload_has_no_problems():
    assert validate_guides(good_payload()) == []


def mutate(change) -> list[str]:
    payload = copy.deepcopy(good_payload())
    change(payload["guides"]["日本"])
    return validate_guides(payload)


def test_a_tip_without_a_source_is_rejected():
    assert any("沒有任何來源" in problem for problem in mutate(lambda g: g["topics"][0]["tips"][0].update(sources=[])))


def test_a_plain_http_source_is_rejected():
    problems = mutate(lambda g: g["topics"][0]["tips"][0]["sources"][0].update(url="http://example.com/x"))
    assert any("https" in problem for problem in problems)


def test_a_bad_date_or_topic_or_title_is_rejected():
    assert any("checked_at" in p for p in mutate(lambda g: g["topics"][0]["tips"][0].update(checked_at="2026/10/04")))
    assert any("未知主題" in p for p in mutate(lambda g: g["topics"][0].update(topic="weather")))
    assert any("標題應為" in p for p in mutate(lambda g: g["topics"][0].update(title="別的標題")))
    assert any("importance" in p or "格式錯誤" in p for p in mutate(lambda g: g["topics"][0]["tips"][0].update(importance="urgent")))


def test_reviewed_needs_two_different_reviewers_and_draft_lists_none():
    assert any("兩位" in p for p in mutate(lambda g: g.update(review_status="reviewed", reviewers=["甲"])))
    assert any("兩位" in p for p in mutate(lambda g: g.update(review_status="reviewed", reviewers=["甲", "甲"])))
    assert mutate(lambda g: g.update(review_status="reviewed", reviewers=["甲", "乙"])) == []
    assert any("draft 不應列出審核者" in p for p in mutate(lambda g: g.update(reviewers=["甲"])))


def test_duplicate_titles_and_empty_guides_are_rejected():
    def duplicate(g):
        g["topics"][0]["tips"].append(copy.deepcopy(g["topics"][0]["tips"][0]))

    assert any("重複" in p for p in mutate(duplicate))
    assert any("沒有任何提醒" in p for p in mutate(lambda g: g.update(topics=[])))
    assert validate_guides({"version": 2, "guides": {}})


# ----------------------------------------------------------------------------- the API


def test_the_api_returns_a_guide_and_lists_every_country(client):
    guide = client.get("/destination-tips", params={"country": "大陸地區"})
    assert guide.status_code == 200 and guide.json()["display_name"] == "中國大陸"
    listing = client.get("/destination-tips/countries").json()
    assert len(listing) == 43 and all(row["review_status"] == "draft" and row["tip_count"] >= 5 for row in listing)
    assert next(row for row in listing if row["country"] == "大陸地區")["tip_count"] > 25


def test_an_unknown_country_is_a_polite_404(client):
    response = client.get("/destination-tips", params={"country": "火星"})
    assert response.status_code == 404 and "還在整理中" in response.json()["detail"]
    assert client.get("/destination-tips").status_code == 422


def test_the_routes_are_in_the_openapi_contract(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert {"/destination-tips", "/destination-tips/countries", "/experience-digest"} <= set(paths)


def test_the_same_country_under_different_names_finds_the_same_guide():
    from exchange_info.destination_tips import COUNTRY_ALIASES, canonical_country, guide_for_country

    for name in ("大陸地區", "中國", "中國大陸", "中華人民共和國", "China", " china "):
        assert guide_for_country(name).country == "大陸地區", name
    assert guide_for_country("Hong Kong").country == "香港" and guide_for_country("South Korea").country == "韓國"
    assert guide_for_country("火星") is None and guide_for_country("") is None
    assert canonical_country("火星") == "火星"
    assert set(COUNTRY_ALIASES) <= set(load_guides()), "every alias points at a guide that exists"
    seen = [alias.casefold() for aliases in COUNTRY_ALIASES.values() for alias in aliases]
    assert len(seen) == len(set(seen)), "an alias belongs to one country only"


def test_the_api_accepts_alternative_country_names(client):
    response = client.get("/destination-tips", params={"country": "中國"})
    assert response.status_code == 200 and response.json()["country"] == "大陸地區"


# ----------------------------------------------------------------------------- 日本、韓國、法國、美國


def guide_text(country: str) -> str:
    return "\n".join(tip.title + tip.detail for topic in load_guides()[country].topics for tip in topic.tips)


def test_japan_carries_the_arrival_paperwork_money_and_bank_account_warnings():
    text = guide_text("日本")
    for needle in ("在留卡", "14 天內", "My Number", "國民健康保險", "30%", "資格外活動許可", "敷金", "禮金", "0570-016811",
                   "絕對不要賣或借出你的銀行帳戶", "080-1009-7179", "090-8794-4568", "Gakkensai"):
        assert needle in text, needle
    assert "手機門號" in load_guides()["日本"].intro, "the intro says what was not researched"


def test_korea_carries_registration_insurance_phone_and_bank_rules():
    text = guide_text("韓國")
    for needle in ("90 天內", "HiKorea", "15 天內", "100 萬韓元", "2021 年 3 月 1 日", "2024 年 4 月 3 日", "6 個月", "預付",
                   "2025 年 3 月 21 日", "傳貰", "82-10-9080-2761"):
        assert needle in text, needle
    insurance = next(tip for topic in load_guides()["韓國"].topics for tip in topic.tips if "NHIS" in tip.title)
    assert "沒有查到明確說明" in insurance.detail, "the open question about one-semester students is stated, not guessed"


def test_france_carries_visa_validation_cvec_social_security_and_the_2026_housing_aid_change():
    text = guide_text("法國")
    for needle in ("VLS-TS", "3 個月內", "ANEF", "VLS-T", "CVEC", "etudiant-etranger.ameli.fr", "60%", "mutuelle",
                   "2026 年 7 月 1 日", "APL", "Visale", "(33) 680074994"):
        assert needle in text, needle
    vlst = next(tip for topic in load_guides()["法國"].topics for tip in topic.tips if "暫時長期簽證" in tip.title)
    assert "無法自動讀取" in vlst.detail, "a page we could not open says so"


def test_usa_carries_i20_sevis_insurance_ssn_and_work_rules():
    text = guide_text("美國")
    for needle in ("30 天", "I-20", "I-901", "F-1", "J-1", "100,000", "25,000", "50,000", "500 美元", "SSN", "10 天", "DMV",
                   "(1-202) 669-0180"):
        assert needle in text, needle


def test_deep_notes_come_first_and_the_shared_ones_follow_without_duplicates():
    for country in ("日本", "韓國", "法國", "美國"):
        guide = load_guides()[country]
        order = [topic.topic for topic in guide.topics]
        assert order == [key for key in TOPICS if key in order], f"{country}: topics keep the usual order"
        for topic in guide.topics:
            titles = [tip.title for tip in topic.tips]
            assert len(titles) == len(set(titles)), (country, topic.topic)
        documents = next(topic for topic in guide.topics if topic.topic == "documents")
        assert any("簽證與入境" in tip.title for tip in documents.tips), f"{country}: the shared visa lookup is still there"
        assert sum(len(topic.tips) for topic in guide.topics) >= 14, country


def test_every_overseas_country_explains_what_a_representative_office_can_and_cannot_do():
    for country, guide in load_guides().items():
        titles = [tip.title for topic in guide.topics for tip in topic.tips]
        has_note = any("駐外館處能幫什麼" in title for title in titles)
        assert has_note == (country not in {"大陸地區", "香港"}), country
    tip = next(tip for topic in load_guides()["法國"].topics for tip in topic.tips if "駐外館處能幫什麼" in tip.title)
    assert "不代墊" in tip.detail and "領事探視" in tip.detail
