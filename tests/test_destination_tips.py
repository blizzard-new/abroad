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
    return {destination_tips.canonical_country(row["country"]) for row in rows} - {"臺灣"}


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


def test_destination_guide_coverage_accounts_for_every_known_gap(client):
    # The expanded six-school coordinate catalog includes countries with no
    # researched guide. Keep those missing instead of fabricating tips or dates.
    gaps = {"丹麥", "以色列", "冰島", "南非", "哥倫比亞", "墨西哥", "希臘",
            "斯洛維尼亞", "智利", "澳門", "盧森堡", "科索沃", "芬蘭", "葡萄牙"}
    assert set(load_guides()) | gaps == destination_countries()
    assert not set(load_guides()) & gaps
    for country in sorted(gaps):
        assert destination_tips.guide_for_country(country) is None
        response = client.get("/destination-tips", params={"country": country})
        assert response.status_code == 404
        assert response.json()["detail"] == "這個國家的出發前提醒還在整理中。"


def test_nothing_is_marked_reviewed_without_two_reviewers():
    for guide in load_guides().values():
        assert guide.review_status == "draft" and guide.reviewers == [], guide.country
        assert "尚未經過兩位審核者" in guide.disclaimer


def test_every_tip_names_an_https_source_and_the_date_it_was_checked():
    for guide in load_guides().values():
        for topic in guide.topics:
            for tip in topic.tips:
                assert tip.sources and all(source.url.startswith("https://") and source.name for source in tip.sources), (guide.country, tip.title)
                assert tip.checked_at in {"2026-10-04", "2026-10-05"}, "the two research days"


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
    indonesia = load_guides()["印尼"]  # still only the shared notes
    assert "還在整理" in indonesia.intro and "110" in "".join(tip.detail for topic in indonesia.topics for tip in topic.tips)
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


# ----------------------------------------------------------------------------- 德國、波蘭、越南、捷克、泰國、香港、印度、西班牙、瑞典、加拿大

BATCH2 = ("德國", "波蘭", "越南", "捷克", "泰國", "香港", "印度", "西班牙", "瑞典", "加拿大")
OFFICE_HOSTS = {"www.mofa.gov.tw", "www.roc-taiwan.org", "www.teco-hk.org"}


def find_tip(country: str, needle: str):
    return next(tip for topic in load_guides()[country].topics for tip in topic.tips if needle in tip.title)


def test_the_bundled_file_is_exactly_what_the_builder_script_writes():
    import importlib.util
    import sys

    scripts = str(ROOT / "scripts")
    sys.path.insert(0, scripts)
    try:
        spec = importlib.util.spec_from_file_location("build_destination_tips", ROOT / "scripts" / "build_destination_tips.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        built = module.build()
    finally:
        sys.path.remove(scripts)
    assert built == json.loads(destination_tips.GUIDES_FILE.read_text(encoding="utf-8")), "re-run scripts/build_destination_tips.py"


def test_the_ten_batch2_countries_go_well_beyond_the_shared_notes():
    for country in BATCH2:
        guide = load_guides()[country]
        count = sum(len(topic.tips) for topic in guide.topics)
        assert count >= 12, (country, count)
        assert guide.last_checked == "2026-10-05" and guide.review_status == "draft", country
        assert "還在整理" not in guide.intro, f"{country}: the shared 'still being written' intro was replaced"


def test_germany_carries_visa_blocked_account_registration_insurance_and_broadcast_fee():
    text = guide_text("德國")
    for needle in ("2026 年 5 月 1 日", "Auslandsportal", "992 歐元", "11,904", "2 週內", "Wohnungsgeberbestätigung", "§ 551", "18.36",
                   "120 個全天", "240 個半天", "+49-171 3898257", "§ 172"):
        assert needle in text, needle
    assert "151 1105 6641" not in text and "1713147552" not in text, "Frankfurt's number differed between sources, so it is left out"
    assert "沒有查到說明" in find_tip("德國", "健康保險").detail, "whether Taiwan's NHI is accepted is stated as unknown"


def test_poland_carries_the_taipei_visa_route_the_residence_card_and_prepaid_registration():
    text = guide_text("波蘭")
    for needle in ("本人到辦事處", "e-konsulat", "6 個月", "15 個曆日", "45 日", "7,492", "30,000 歐元", "karta pobytu", "390",
                   "15 個月", "NFZ", "668-027-574", "2017 年 2 月 1 日"):
        assert needle in text, needle
    assert "沒有日期" in find_tip("波蘭", "價格量級").detail, "undated price pages are called undated"


def test_vietnam_carries_evisa_registration_sim_vaccine_and_licence_warnings_without_guessing():
    text = guide_text("越南")
    for needle in ("evisa.gov.vn", "拒絕入境", "DH", "prearrival.immigration.gov.vn", "5,000 美元", "公安", "2026 年 4 月 15 日",
                   "臉部生物特徵", "瘧疾", "+84-913219986", "+84-903927019"):
        assert needle in text, needle
    assert "請不要假設可以" in find_tip("越南", "駕照").detail
    assert "不寫小時數" in find_tip("越南", "住宿一定要").detail, "the residence-declaration deadline we could not confirm is not given"
    assert "沒有寫外國護照持有人怎麼辦" in find_tip("越南", "手機卡").detail


def test_czech_republic_carries_visa_documents_police_report_and_the_expired_insurer_monopoly():
    text = guide_text("捷克")
    for needle in ("2024 年 1 月 8 日", "Taipei.Visa@mzv.gov.cz", "180,000", "3 個工作日", "60 天", "90 天", "603-166-707",
                   "2026 年 8 月 2 日", "Pojišťovna VZP", "ISIC", "233-320-606"):
        assert needle in text, needle
    insurance = find_tip("捷克", "保險要涵蓋全程")
    assert "之後的規定我沒查到" in insurance.detail, "what replaced the VZP-only period is not guessed"
    assert "舊文件" in find_tip("捷克", "就學簽證").detail


def test_thailand_carries_the_2026_visa_free_rule_tdac_exchange_visa_and_overstay_penalties():
    text = guide_text("泰國")
    for needle in ("2026 年 9 月 15 日", "30 天", "TDAC", "72 小時", "2 萬泰銖", "eVisa", "學校對學校", "2,300", "200,000", "500 銖",
                   "20,000 銖", "5 年內禁止再入境", "10 年內禁止再入境", "081-6664006"):
        assert needle in text, needle
    unread = find_tip("泰國", "住宿通報")
    assert unread.importance == "good_to_know" and "沒能讀到" in unread.title and "拒絕自動讀取" in unread.detail


def test_hong_kong_says_visitors_cannot_study_and_keeps_the_shared_mainland_registration_note():
    text = guide_text("香港")
    for needle in ("不得在香港就讀", "ID 995A", "ID 995B", "六星期", "戶籍謄本", "多次入境許可證", "180 天", "30 天內", "2,100", "7,400",
                   "八號", "70 毫米", "852-61439012"):
        assert needle in text, needle
    documents = next(topic for topic in load_guides()["香港"].topics if topic.topic == "documents")
    assert any("陸委會" in tip.title for tip in documents.tips), "the 陸委會 registration reminder is still there"


def test_india_states_the_conflicting_visa_sources_instead_of_choosing_one():
    text = guide_text("印度")
    for needle in ("14 天內", "180 天", "FRRO", "e-FRRO", "bonafide", "HIV", "9810-642-658", "11-46077777"):
        assert needle in text, needle
    visa = find_tip("印度", "台灣護照怎麼申請學生簽證")
    assert "矛盾" in visa.detail and "印度台北協會" in visa.detail
    assert "核對" in find_tip("印度", "緊急電話").detail, "the emergency number must be checked against the page"


def test_spain_carries_visa_tie_padron_and_the_missing_social_security_agreement():
    text = guide_text("西班牙")
    for needle in ("90 天", "兩個月", "sutramiteconsular.maec.es", "IPREM", "180 天", "一個月內", "TIE", "Padrón", "沒有簽署社會保障協議",
                   "639384883", "esp@mofa.gov.tw"):
        assert needle in text, needle


def test_sweden_carries_permit_funds_insurance_and_coordination_number():
    text = guide_text("瑞典")
    for needle in ("90 天", "10,656", "4,736", "2,960", "75%", "全面健康保險", "samordningsnummer", "個人號碼", "+46-70-675 5089"):
        assert needle in text, needle


def test_canada_carries_permit_length_eta_work_limit_and_provincial_insurance():
    text = guide_text("加拿大")
    for needle in ("6 個月", "eTA", "身分證字號", "PAL", "24 小時", "SIN", "UHIP", "75 加幣", "MSP", "(613) 762-6090", "(416) 587-8111",
                   "(604) 377-8730"):
        assert needle in text, needle
    assert "原文指南" in find_tip("加拿大", "eTA").detail, "a summary that contradicted the primary text is called out"


def test_batch2_emergency_numbers_come_from_the_representative_offices_own_pages():
    for country in BATCH2:
        guide = load_guides()[country]
        emergency = next(topic for topic in guide.topics if topic.topic == "emergency")
        first = emergency.tips[0]
        assert first.importance == "must" and any(ch.isdigit() for ch in first.detail), country
        hosts = {source.url.split("/")[2] for source in first.sources}
        assert hosts <= OFFICE_HOSTS, (country, hosts)


def test_batch2_tips_name_a_page_for_everything_and_never_claim_review():
    for country in BATCH2:
        for topic in load_guides()[country].topics:
            for tip in topic.tips:
                assert tip.sources and all(source.name.strip() and source.url.startswith("https://") for source in tip.sources), (country, tip.title)
        assert load_guides()[country].reviewers == []
