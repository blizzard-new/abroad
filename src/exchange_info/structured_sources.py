from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable

from .ai_gateway import structured_response
from .extractor import build_exchange_info
from .models import ProcessedPage, StructuredSourceRecord
from .settings import DEFAULT_DATA_DIR
from .storage import (
    load_structured_sources,
    save_structured_sources,
)


def build_structured_source_index(
    pages: Iterable[ProcessedPage],
    data_dir: Path = DEFAULT_DATA_DIR,
    *,
    use_ai: bool = False,
) -> list[StructuredSourceRecord]:
    page_rows = list(pages)
    cached = {
        (row.source_url, row.content_hash, row.extraction_method): row
        for row in load_structured_sources(data_dir)
    }
    expected_method = "ai" if use_ai else "rules"
    records: list[StructuredSourceRecord] = []
    for page in page_rows:
        existing = cached.get((page.source_url, page.content_hash, expected_method))
        records.append(existing or structure_source(page, use_ai=use_ai))
        if use_ai:
            save_structured_sources(records, data_dir)
    save_structured_sources(records, data_dir)
    return records


def structure_source(page: ProcessedPage, *, use_ai: bool = False) -> StructuredSourceRecord:
    fallback = _rule_based_record(page)
    if not use_ai:
        return fallback

    payload = structured_response(
        schema_name="exchange_source_extraction",
        schema={
            "type": "object",
            "properties": {
                "program_type": _string_array_schema(8),
                "academic_year": _string_array_schema(8),
                "semester": _string_array_schema(8),
                "application_start": {"type": ["string", "null"]},
                "application_end": {"type": ["string", "null"]},
                "application_period": _string_array_schema(10),
                "eligibility": _string_array_schema(15),
                "language_requirements": _string_array_schema(15),
                "required_documents": _string_array_schema(20),
                "scholarship_info": _string_array_schema(15),
                "needs_review": {"type": "boolean"},
            },
            "required": [
                "program_type",
                "academic_year",
                "semester",
                "application_start",
                "application_end",
                "application_period",
                "eligibility",
                "language_requirements",
                "required_documents",
                "scholarship_info",
                "needs_review",
            ],
            "additionalProperties": False,
        },
        instructions=(
            "你負責將長庚大學公開交換申請資料抽成結構化欄位。只能使用提供的原文，使用繁體中文；"
            "原文沒有的內容回傳空陣列或 null，不得推測日期、門檻、名額或補助金額。"
            "日期只有在原文明確包含完整年月日時才轉成 YYYY-MM-DD。資訊模糊、互相衝突或像舊年度資料時 needs_review=true。"
        ),
        input_text=(
            f"標題：{page.title}\n發布日期：{page.published_at or '未標示'}\n"
            f"分類：{page.category.value}\n\n原文：\n{page.text[:18_000]}"
        ),
        tier="fast",
    )
    if not isinstance(payload, dict):
        return fallback

    update: dict[str, Any] = {
        "program_type": _clean_list(payload.get("program_type")) or fallback.program_type,
        "academic_year": _clean_list(payload.get("academic_year")) or fallback.academic_year,
        "semester": _clean_list(payload.get("semester")) or fallback.semester,
        "application_start": _iso_date(payload.get("application_start")) or fallback.application_start,
        "application_end": _iso_date(payload.get("application_end")) or fallback.application_end,
        "application_period": _clean_list(payload.get("application_period")) or fallback.application_period,
        "eligibility": _clean_list(payload.get("eligibility")) or fallback.eligibility,
        "language_requirements": _clean_list(payload.get("language_requirements")) or fallback.language_requirements,
        "required_documents": _clean_list(payload.get("required_documents")) or fallback.required_documents,
        "scholarship_info": _clean_list(payload.get("scholarship_info")) or fallback.scholarship_info,
        "extraction_method": "ai",
        "needs_review": bool(payload.get("needs_review", True)),
    }
    if not any(
        update[key]
        for key in (
            "program_type",
            "application_period",
            "eligibility",
            "language_requirements",
            "required_documents",
            "scholarship_info",
        )
    ):
        update["needs_review"] = True
    return fallback.model_copy(update=update)


def _rule_based_record(page: ProcessedPage) -> StructuredSourceRecord:
    info = build_exchange_info([page])
    dates = _explicit_dates("\n".join([page.summary, page.text]))
    return StructuredSourceRecord(
        source_url=page.source_url,
        title=page.title,
        category=page.category,
        published_at=page.published_at,
        last_checked=page.crawled_at,
        content_hash=page.content_hash,
        program_type=info.program_type,
        academic_year=info.academic_year,
        semester=info.semester,
        application_start=dates[0] if dates else None,
        application_end=dates[-1] if len(dates) > 1 else None,
        application_period=info.application_period,
        eligibility=info.eligibility,
        language_requirements=info.language_requirement,
        required_documents=info.required_documents,
        scholarship_info=info.scholarship_info,
        extraction_method="rules",
        needs_review=True,
    )


def _explicit_dates(text: str) -> list[str]:
    rows: list[str] = []
    for year, month, day in re.findall(
        r"(?<!\d)(20\d{2})\s*[年/.-]\s*(1[0-2]|0?[1-9])\s*[月/.-]\s*(3[01]|[12]\d|0?[1-9])\s*日?",
        text,
    ):
        value = f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
        if value not in rows:
            rows.append(value)
    return rows


def _iso_date(value: object) -> str | None:
    text = str(value or "").strip()
    return text if re.fullmatch(r"20\d{2}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])", text) else None


def _clean_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    rows: list[str] = []
    for item in value:
        compact = re.sub(r"\s+", " ", str(item or "")).strip()
        if compact and compact not in rows:
            rows.append(compact[:500])
    return rows


def _string_array_schema(max_items: int) -> dict[str, object]:
    return {
        "type": "array",
        "items": {"type": "string"},
        "maxItems": max_items,
    }
