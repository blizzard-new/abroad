from __future__ import annotations

import re
from pathlib import Path

from fastapi.testclient import TestClient

import exchange_info
from exchange_info.api import create_app
from exchange_info.application_documents import all_application_templates
from exchange_info.university_registry import SUPPORTED_UNIVERSITIES
from exchange_info.verified_window_deadlines import (
    build_school_window_ics,
    build_verified_window_deadline_catalog,
)


DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
STATIC_DIR = Path(exchange_info.__file__).parent / "static"


def test_verified_window_catalog_covers_all_supported_universities_and_10_week_window() -> None:
    catalog = build_verified_window_deadline_catalog()
    assert catalog.window_start_date == "2026-10-19"
    assert catalog.window_end_date == "2026-12-31"
    assert len(catalog.items) == len(SUPPORTED_UNIVERSITIES)

    supported_ids = {u.id for u in SUPPORTED_UNIVERSITIES}
    catalog_ids = {card.school_id for card in catalog.items}
    assert catalog_ids == supported_ids

    active_window_cards = [card for card in catalog.items if card.in_ten_week_window]
    assert catalog.ten_week_school_count == len(active_window_cards)
    added_school_ids = {"ncue", "nknu", "tmu", "csmu", "cmu", "kmu", "mcu", "ntub", "ncnu"}
    audited_cards = [card for card in active_window_cards if card.school_id not in added_school_ids]
    assert len(audited_cards) == 18
    assert {card.school_id for card in catalog.items if card.school_id in added_school_ids} == added_school_ids
    assert catalog.ten_week_school_count == 27


def test_every_verified_rule_and_subtask_has_https_source_and_last_checked_date() -> None:
    catalog = build_verified_window_deadline_catalog()
    for card in catalog.items:
        for rule_name, fact in (
            ("online_deadline", card.online_deadline),
            ("paper_deadline", card.paper_deadline),
            ("study_plan_limit", card.study_plan_limit),
        ):
            where = f"{card.school_id}.{rule_name}"
            assert str(fact.source_url).startswith("https://"), where
            assert DATE_PATTERN.match(fact.last_checked_at), where
            assert fact.label.strip(), where
            assert fact.value_text.strip(), where
            assert fact.source_title.strip(), where
            assert "全台第一" not in fact.value_text, where

        if card.primary_deadline_date:
            assert len(card.subtasks) >= 4, card.school_id
        else:
            # Missing evidence must stay visible, without fabricated tasks.
            assert not card.subtasks, card.school_id
            assert card.ics_download_url is None
            assert card.google_calendar_url is None
        for subtask in card.subtasks:
            where = f"{card.school_id}.subtask.{subtask.id}"
            assert str(subtask.source_url).startswith("https://"), where
            assert DATE_PATTERN.match(subtask.last_checked_at), where
            if subtask.due_date is not None:
                assert DATE_PATTERN.match(subtask.due_date), where


def test_no_fabricated_2359_deadlines_for_schools_without_official_2359_time() -> None:
    catalog = build_verified_window_deadline_catalog()
    by_id = {card.school_id: card for card in catalog.items}

    for pending_id in ("cgu", "fcu", "nsysu", "ntut"):
        card = by_id[pending_id]
        assert card.primary_deadline_at is None, f"{pending_id} must not fabricate exact timestamp"
        assert card.online_deadline.exact_deadline_at is None, f"{pending_id} must not fabricate 23:59"

    for daytime_id, expected_hour in (
        ("ntu", 16),
        ("fju", 16),
        ("nccu", 16),
        ("nthu", 16),
        ("nycu", 16),
        ("ncku", 16),
        ("ntpu", 17),
        ("ncu", 12),
        ("scu", 12),
        ("nchu", 12),
    ):
        card = by_id[daytime_id]
        assert card.online_deadline.exact_deadline_at is not None
        assert card.online_deadline.exact_deadline_at.hour == expected_hour


def test_retention_hooks_and_ics_feed_include_subtasks_and_alarms() -> None:
    client = TestClient(create_app())
    response = client.get("/verified-window-deadlines", params={"school": "國立臺灣大學"})
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 1
    ntu = payload["items"][0]
    assert ntu["school_id"] == "ntu"
    assert ntu["ics_download_url"] == "/calendar/school-window.ics?school=ntu"
    assert ntu["google_calendar_url"].startswith("https://calendar.google.com/calendar/render?")
    assert ntu["line_oa_url"].startswith("https://line.me/R/oaMessage/")
    assert "https://studyabroad.ntu.edu.tw/" in ntu["line_copy_summary"]

    ics_response = client.get("/calendar/school-window.ics", params={"school": "ntu"})
    assert ics_response.status_code == 200
    assert "text/calendar" in ics_response.headers["content-type"]
    assert 'filename="uniway-ntu-exchange-deadlines.ics"' in ics_response.headers["content-disposition"]
    ics_text = ics_response.text
    assert "BEGIN:VCALENDAR" in ics_text
    assert "END:VCALENDAR" in ics_text
    assert ics_text.count("BEGIN:VEVENT") >= 4
    assert "TRIGGER:-P14D" in ics_text
    assert "TRIGGER:-P7D" in ics_text
    assert "TRIGGER:-P3D" in ics_text
    assert "TRIGGER:-P1D" in ics_text
    assert "https://studyabroad.ntu.edu.tw/" in ics_text
    assert "最後查核日期：2026-10-07" in ics_text


def test_every_writing_rule_template_includes_https_source_and_last_checked_at() -> None:
    checked = 0
    for university in SUPPORTED_UNIVERSITIES:
        for template in all_application_templates(university.school_name):
            rules = template.writing_rules
            if rules is None:
                continue
            checked += 1
            where = f"{university.id}/{template.id}"
            assert rules.source_url is not None, where
            assert str(rules.source_url).startswith("https://"), where
            assert rules.last_checked_at is not None, where
            assert DATE_PATTERN.match(rules.last_checked_at), where
    assert checked >= 30


def test_frontend_mounts_verified_window_and_provenance_hooks() -> None:
    index_html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    app_js = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    redesign_css = (STATIC_DIR / "platform-redesign.css").read_text(encoding="utf-8")

    assert "home-verified-window" not in index_html
    assert "renderHomeVerifiedWindowSection" not in app_js
    assert 'id="calendar-verified-window-hook"' in index_html
    assert 'id="deadlines-verified-window-card"' in index_html

    assert "loadVerifiedWindowDeadlines" in app_js
    assert "renderVerifiedWindowRetentionHook" in app_js
    assert "importVerifiedSchoolSubtasksToCalendar" in app_js
    assert "官方 HTTPS 來源" in app_js
    assert "最後查核日期" in app_js
    assert "全台第一" not in app_js

    assert ".verified-window-retention-hook" in redesign_css
    assert ".verified-rule-provenance" in redesign_css
