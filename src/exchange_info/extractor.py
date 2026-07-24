from __future__ import annotations

import re
from datetime import datetime, timezone

from .models import ExchangeInfo, PageCategory, ProcessedPage


PROGRAM_KEYWORDS = [
    "交換學生",
    "出國研修",
    "自費研修",
    "雙聯學位",
    "雙學位",
    "短期課程",
    "出國補助",
]

FIELD_TRIGGERS = {
    "application_period": ["申請期間", "報名期間", "申請期限", "截止", "收件至", "開放申請"],
    "eligibility": ["申請資格", "資格", "符合", "限", "對象"],
    "language_requirement": ["語言", "英文", "托福", "TOEFL", "雅思", "IELTS", "檢定"],
    "required_documents": ["申請文件", "應繳", "繳交", "文件", "備審", "資料"],
    "scholarship_info": ["補助", "獎學金", "經費", "Scholarship", "scholarship"],
}

ACADEMIC_YEAR_RE = re.compile(r"(?:\b\d{3}\s*學年度|\b20\d{2}\s*年)")
SEMESTER_RE = re.compile(r"(\d{3}\s*-\s*[12]\s*學期|上學期|下學期|春季|秋季|Spring|Fall)", re.I)
PARTNER_LINE_RE = re.compile(r"(University|College|Institute|大學|學院|研究所|Universit)", re.I)


def build_exchange_info(pages: list[ProcessedPage], school_name: str = "長庚大學") -> ExchangeInfo:
    relevant_pages = [page for page in pages if page.category != PageCategory.OTHER]
    source_pages = relevant_pages or pages

    program_type: list[str] = []
    academic_year: list[str] = []
    semester: list[str] = []
    application_period: list[str] = []
    eligibility: list[str] = []
    language_requirement: list[str] = []
    required_documents: list[str] = []
    scholarship_info: list[str] = []
    partner_universities: list[str] = []
    source_urls: list[str] = []
    last_checked: datetime | None = None

    for page in source_pages:
        text = f"{page.title}\n{page.text}"
        source_urls.append(page.source_url)
        if last_checked is None or page.crawled_at > last_checked:
            last_checked = page.crawled_at

        for keyword in PROGRAM_KEYWORDS:
            if keyword in text:
                program_type.append(keyword)

        academic_year.extend(match.group(0).replace(" ", "") for match in ACADEMIC_YEAR_RE.finditer(text))
        semester.extend(match.group(1).replace(" ", "") for match in SEMESTER_RE.finditer(text))

        application_period.extend(_extract_trigger_lines(page.text, FIELD_TRIGGERS["application_period"]))
        eligibility.extend(_extract_trigger_lines(page.text, FIELD_TRIGGERS["eligibility"]))
        language_requirement.extend(_extract_trigger_lines(page.text, FIELD_TRIGGERS["language_requirement"]))
        required_documents.extend(_extract_trigger_lines(page.text, FIELD_TRIGGERS["required_documents"]))
        scholarship_info.extend(_extract_trigger_lines(page.text, FIELD_TRIGGERS["scholarship_info"]))

        if page.category == PageCategory.PARTNER_SCHOOL:
            partner_universities.extend(_extract_partner_lines(page.text))

    return ExchangeInfo(
        school_name=school_name,
        program_type=_dedupe(program_type, limit=20),
        academic_year=_dedupe(academic_year, limit=20),
        semester=_dedupe(semester, limit=20),
        application_period=_dedupe(application_period, limit=30),
        eligibility=_dedupe(eligibility, limit=30),
        language_requirement=_dedupe(language_requirement, limit=30),
        required_documents=_dedupe(required_documents, limit=30),
        scholarship_info=_dedupe(scholarship_info, limit=30),
        partner_universities=_dedupe(partner_universities, limit=100),
        source_urls=_dedupe(source_urls),
        last_checked=last_checked or datetime.now(timezone.utc),
    )


def _extract_trigger_lines(text: str, triggers: list[str], max_line_chars: int = 240) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    matches: list[str] = []
    for index, line in enumerate(lines):
        if not any(trigger.lower() in line.lower() for trigger in triggers):
            continue
        snippet = line
        if len(snippet) < 18 and index + 1 < len(lines):
            snippet = f"{snippet} {lines[index + 1]}"
        if len(snippet) <= max_line_chars:
            matches.append(snippet)
    return matches


def _extract_partner_lines(text: str) -> list[str]:
    lines = [line.strip(" -•\t") for line in text.splitlines() if line.strip()]
    matches: list[str] = []
    for line in lines:
        if 4 <= len(line) <= 160 and PARTNER_LINE_RE.search(line):
            matches.append(line)
    return matches


def _dedupe(values: list[str], limit: int | None = None) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = re.sub(r"\s+", " ", value).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
        if limit is not None and len(result) >= limit:
            break
    return result
