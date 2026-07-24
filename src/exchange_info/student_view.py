from __future__ import annotations

import json
import re
import zipfile
from datetime import datetime, timezone
from functools import lru_cache
from html import unescape
from io import BytesIO
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

import requests
from bs4 import BeautifulSoup

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - dependency is declared, fallback keeps API usable.
    PdfReader = None  # type: ignore[assignment]

from .models import (
    ExchangeInfo,
    PageCategory,
    PartnerProgramOption,
    PartnerStudentSummary,
    PartnerUniversity,
    ProcessedPage,
    RuleExplanation,
    SourceReference,
    StudentDashboard,
    StudentInfoItem,
)
from .partner_localization import build_partner_student_summary, merge_student_summaries
from .school_identity import school_identity_key


EXCHANGE_SHEET_ID = "1EAOsiZkw5oWWUpAyXz-04aQWdSMR9f_c3Jup69LeiuA"
DOUBLE_DEGREE_SHEET_ID = "1aQiwbtrQu1QOIOkFrOYl9WkzT0mqnZqIwI9KJCXGb4E"
EXCHANGE_SOURCE_URL = "https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17554"
DOUBLE_DEGREE_SOURCE_URL = "https://www.cgu.edu.tw/oia-ch/Contents?nodeId=17533"
CGU_BASE_URL = "https://www.cgu.edu.tw"
OFFICIAL_DOCUMENT_SPECS = [
    {
        "slug": "navigator",
        "title": "長庚大學領航者補助作業要點",
        "document_type": "補助要點",
        "summary": "這是長庚大學學生出國修讀學分的校內補助規則，學生看到申請資格中的「領航者補助作業要點」時，主要要確認成績、語言、補助限制與返國義務。",
        "source_url": "https://www.cgu.edu.tw/regulation/RegulationManagement/RegulationDetail/b85add3b-7d9e-43ff-b22f-f0657e11765c",
        "document_url": "https://www.cgu.edu.tw/regulation/ServerFile/Get/e3b68a9a-e820-4614-a799-e88023a40161",
        "applies_to": ["交換學生", "自費研修", "學海飛颺", "出國修讀學分"],
    },
    {
        "slug": "xuehai_sizhu",
        "title": "長庚大學辦理教育部學海惜珠補助要點",
        "document_type": "補助要點",
        "summary": "這是勵學學生申請教育部學海惜珠出國修讀學分時使用的補助規則，重點在身分資格、經濟條件、不得重複領取政府補助與申請文件。",
        "source_url": "https://www.cgu.edu.tw/regulation/RegulationManagement/RegulationDetail/d5fa7ac2-d65e-4dcd-8f18-0717d32d5639",
        "document_url": "https://www.cgu.edu.tw/regulation/ServerFile/Get/fe589216-9fe9-42b3-816c-31cde93b5d1a",
        "applies_to": ["學海惜珠", "勵學學生", "出國修讀學分"],
    },
    {
        "slug": "outbound_exchange",
        "title": "長庚大學學生赴境外學校進修交流作業要點",
        "document_type": "作業要點",
        "summary": "這是學生赴境外學校進修交流的基礎規範，重點在誰可以參加、交流類型、費用自理項目，以及出國前的選課與學分採認。",
        "source_url": "https://www.cgu.edu.tw/regulation/RegulationManagement/RegulationDetail/aeb2f385-2687-43fb-93c5-b4e09cd78137",
        "document_url": "https://www.cgu.edu.tw/regulation/ServerFile/Get/dd1e19ee-f5bd-4977-9135-9aedaba47f09",
        "applies_to": ["交換生", "雙聯學位", "修課", "研究", "交流"],
    },
    {
        "slug": "short_credit_subsidy",
        "title": "長庚大學補助學生參加境外短期學分課程作業要點",
        "document_type": "補助要點",
        "summary": "這是寒暑假或短期境外學分課程的補助規則，重點在短期課程資格、申請文件、補助限制與完成課程後要繳交的資料。",
        "source_url": "https://www.cgu.edu.tw/regulation/RegulationManagement/RegulationDetail/188edb21-5c53-4cbe-9e55-81089f90528b",
        "document_url": "https://www.cgu.edu.tw/regulation/ServerFile/Get/f036738d-a1c8-46b2-b208-bebf6901f0e5",
        "applies_to": ["短期學分課程", "寒暑假課程", "出國補助"],
        "include_related_documents": True,
    },
    {
        "slug": "xuehai_internship",
        "title": "長庚大學辦理教育部學海築夢及新南向學海築夢補助要點",
        "document_type": "補助要點",
        "summary": "這是學生出國專業實習相關的教育部補助規則，重點在實習計畫、申請資格、補助限制與相關同意或聲明文件。",
        "source_url": "https://www.cgu.edu.tw/regulation/RegulationManagement/RegulationDetail/17a33812-80d0-45f1-b4ef-6c2cf40a0c50",
        "document_url": "https://www.cgu.edu.tw/regulation/ServerFile/Get/20198fac-b649-4e2e-816d-29e6c657c370",
        "applies_to": ["出國實習", "學海築夢", "新南向學海築夢"],
        "include_related_documents": True,
    },
]


def build_student_dashboard(
    pages: list[ProcessedPage],
    exchange_info: ExchangeInfo | None = None,
    *,
    fetch_partner_sheets: bool = True,
    fetch_regulation_rules: bool = True,
    raw_files_dir: Path | None = None,
) -> StudentDashboard:
    page_map = {page.source_url: page for page in pages}
    selection = _page_containing(page_map, "15656")
    preparation = _page_containing(page_map, "18380")
    workflow = _page_containing(page_map, "15680")
    exchange_schools = _page_containing(page_map, "17554")
    double_degree_schools = _page_containing(page_map, "17533")
    short_courses = _page_containing(page_map, "15717")
    teep = _page_containing(page_map, "19081")
    subsidy_credit = _page_containing(page_map, "15724")
    subsidy_low_income = _page_containing(page_map, "15725")

    partner_universities: list[PartnerUniversity] = []
    if fetch_partner_sheets:
        partner_universities = fetch_partner_universities()

    document_explanations: list[RuleExplanation] = []
    if fetch_regulation_rules:
        document_explanations = fetch_document_explanations(
            context_text={
                "navigator": "\n".join(
                    _page_text(page)
                    for page in [selection, subsidy_credit]
                    if page
                ),
                "xuehai_sizhu": _page_text(subsidy_low_income),
            },
            raw_files_dir=raw_files_dir,
        )

    sources = [
        _source_ref(page)
        for page in pages
        if page.title != "國際事務處" and page.category != PageCategory.OTHER
    ]
    sources = _dedupe_sources([*sources, *(item.source for item in document_explanations)])

    return StudentDashboard(
        school_name="長庚大學",
        last_checked=_last_checked(pages, exchange_info),
        academic_score_minimum=70,
        academic_score_rule="學業平均 70 分以上，並依各合作校及計畫規定個別核對。",
        language_score_minimums={
            "toeic": 700,
            "ielts": 5.5,
            "toefl": 72,
            "duolingo": 105,
        },
        application_periods=_application_periods(exchange_schools, double_degree_schools, short_courses),
        program_overview=_program_overview(preparation, short_courses, teep),
        eligibility=_eligibility(selection),
        language_requirements=_language_requirements(selection),
        required_documents=_required_documents(workflow),
        scholarship_info=_scholarship_info(preparation, teep),
        document_explanations=document_explanations,
        rule_explanations=document_explanations,
        partner_universities=partner_universities,
        sources=sources,
    )


def fetch_partner_universities(timeout_seconds: float = 8.0) -> list[PartnerUniversity]:
    rows: list[PartnerUniversity] = []
    rows.extend(
        _fetch_sheet_rows(
            spreadsheet_id=EXCHANGE_SHEET_ID,
            program_type="交換學生 / 自費研修",
            source_url=EXCHANGE_SOURCE_URL,
            timeout_seconds=timeout_seconds,
        )
    )
    rows.extend(
        _fetch_sheet_rows(
            spreadsheet_id=DOUBLE_DEGREE_SHEET_ID,
            program_type="雙學位",
            source_url=DOUBLE_DEGREE_SOURCE_URL,
            timeout_seconds=timeout_seconds,
        )
    )
    return _merge_partner_universities(rows)


def _merge_partner_universities(
    rows: list[PartnerUniversity],
) -> list[PartnerUniversity]:
    grouped: dict[str, list[PartnerUniversity]] = {}
    for row in rows:
        key = school_identity_key(row.school_name)
        grouped.setdefault(key, []).append(row)

    merged: list[PartnerUniversity] = []
    for group in grouped.values():
        primary = group[0]
        options = [
            PartnerProgramOption(
                program_type=row.program_type,
                colleges=row.colleges,
                degree_levels=row.degree_levels,
                study_period=row.study_period,
                quota=row.quota,
                eligibility=row.eligibility,
                application_deadline=row.application_deadline,
                application_info=row.application_info,
                tuition_info=row.tuition_info,
                source_url=row.source_url,
                student_summary_zh=row.student_summary_zh,
            )
            for row in group
        ]
        merged.append(
            PartnerUniversity(
                program_type=_join_partner_values(group, "program_type") or primary.program_type,
                country=_join_partner_values(group, "country"),
                school_name=primary.school_name,
                website=next((row.website for row in group if row.website), None),
                colleges=_join_partner_values(group, "colleges"),
                degree_levels=_join_partner_values(group, "degree_levels"),
                study_period=_join_partner_values(group, "study_period"),
                quota=_join_partner_values(group, "quota"),
                eligibility=_join_partner_values(group, "eligibility"),
                application_deadline=_join_partner_values(group, "application_deadline"),
                application_info=_join_partner_values(group, "application_info"),
                tuition_info=_join_partner_values(group, "tuition_info"),
                ranking_info=_join_partner_values(group, "ranking_info"),
                source_url=primary.source_url,
                program_options=options,
                student_summary_zh=PartnerStudentSummary(
                    **merge_student_summaries(
                        row.student_summary_zh.model_dump() for row in group
                    )
                ),
            )
        )
    return merged


def _join_partner_values(rows: list[PartnerUniversity], field: str) -> str | None:
    values = list(
        dict.fromkeys(
            value.strip()
            for row in rows
            if (value := getattr(row, field, None)) and value.strip()
        )
    )
    return "；".join(values) or None


def fetch_document_explanations(
    *,
    context_text: dict[str, str] | None = None,
    raw_files_dir: Path | None = None,
    timeout_seconds: float = 8.0,
) -> list[RuleExplanation]:
    context_text = context_text or {}
    explanations: list[RuleExplanation] = []
    for spec in OFFICIAL_DOCUMENT_SPECS:
        document_url = str(spec.get("document_url") or _resolve_primary_document_url(str(spec["source_url"]), timeout_seconds))
        text = _fetch_pdf_text(
            document_url,
            title=str(spec["title"]),
            raw_files_dir=raw_files_dir,
            timeout_seconds=timeout_seconds,
        )
        combined_text = "\n".join([text, context_text.get(str(spec["slug"]), "")])
        key_points = _document_key_points(str(spec["slug"]), str(spec["title"]), combined_text)
        if not key_points:
            key_points = ["已保留官方規章來源，PDF 文字暫時無法抽取；請以官方檔案為準。"]
        explanations.append(
            RuleExplanation(
                title=str(spec["title"]),
                summary=str(spec.get("summary") or _document_summary(str(spec["title"]))),
                key_points=key_points,
                applies_to=list(spec.get("applies_to") or _infer_applies_to(str(spec["title"]), combined_text)),
                source=SourceReference(
                    title=str(spec["title"]),
                    source_url=str(spec["source_url"]),
                    category=PageCategory.SCHOLARSHIP,
                ),
                document_url=document_url,
                document_type=str(spec.get("document_type") or _infer_document_type(str(spec["title"]))),
                full_text_extracted=bool(text.strip()),
            )
        )
        if spec.get("include_related_documents"):
            explanations.extend(
                _related_document_explanations(
                    spec,
                    primary_url=document_url,
                    raw_files_dir=raw_files_dir,
                    timeout_seconds=timeout_seconds,
                )
            )
    return explanations


def fetch_rule_explanations(**kwargs: Any) -> list[RuleExplanation]:
    return fetch_document_explanations(**kwargs)


def _fetch_sheet_rows(
    *, spreadsheet_id: str, program_type: str, source_url: str, timeout_seconds: float
) -> list[PartnerUniversity]:
    url = (
        f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq"
        "?tqx=out:json&sheet=%E7%B8%BD%E8%A1%A8"
    )
    try:
        response = requests.get(url, timeout=timeout_seconds)
        response.raise_for_status()
        payload = _parse_gviz_payload(response.text)
    except (requests.RequestException, ValueError, json.JSONDecodeError):
        return []

    labels = [col.get("label") or "" for col in payload["table"]["cols"]]
    universities: list[PartnerUniversity] = []
    for row in payload["table"]["rows"]:
        values = [_cell_value(cell) for cell in row.get("c", [])]
        item = {label: values[index] if index < len(values) else "" for index, label in enumerate(labels)}
        school_name = _plain(item.get("校名") or "")
        if not school_name:
            continue

        study_period = _plain(item.get("研修期間") or item.get("預計研修期間"))
        eligibility_raw = _plain(item.get("申請資格"))
        eligibility = _compact_long_text(eligibility_raw)
        application_deadline = _plain(item.get("該校申請期限"))
        application_info_raw = _plain(item.get("該校申請資訊") or item.get("申請程序"))
        application_info = _compact_long_text(application_info_raw)
        tuition_info_raw = _plain(item.get("學費資訊"))
        tuition_info = _compact_long_text(tuition_info_raw)
        student_summary = PartnerStudentSummary(
            **build_partner_student_summary(
                study_period=study_period,
                application_deadline=application_deadline,
                eligibility=eligibility_raw,
                application_info=application_info_raw,
                tuition_info=tuition_info_raw,
            )
        )

        universities.append(
            PartnerUniversity(
                program_type=program_type,
                country=_plain(item.get("國家")),
                school_name=school_name,
                website=_plain(item.get("學校網站")),
                colleges=_plain(item.get("可申請學院") or item.get("本校可申請學院")),
                degree_levels=_plain(item.get("可申請學制") or item.get("本校可申請學制")),
                study_period=study_period,
                quota=_plain(item.get("名額")),
                eligibility=eligibility,
                application_deadline=application_deadline,
                application_info=application_info,
                tuition_info=tuition_info,
                ranking_info=_plain(item.get("排名資訊")),
                source_url=source_url,
                student_summary_zh=student_summary,
            )
        )
    return universities


def _parse_gviz_payload(text: str) -> dict[str, Any]:
    start = text.index("(") + 1
    end = text.rindex(")")
    return json.loads(text[start:end])


def _cell_value(cell: dict[str, Any] | None) -> str:
    if not cell:
        return ""
    value = cell.get("f", cell.get("v", ""))
    return str(value) if value is not None else ""


@lru_cache(maxsize=12)
def _fetch_binary(url: str, timeout_seconds: float) -> bytes:
    response = requests.get(url, timeout=timeout_seconds)
    response.raise_for_status()
    return response.content


@lru_cache(maxsize=12)
def _fetch_text(url: str, timeout_seconds: float) -> str:
    response = requests.get(url, timeout=timeout_seconds)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or response.encoding
    return response.text


def _resolve_primary_document_url(source_url: str, timeout_seconds: float) -> str:
    for title, url in _document_links_from_page(source_url, timeout_seconds):
        if _is_downloadable_document(title, url) and "操作說明" not in title:
            return url
    return source_url


def _document_links_from_page(source_url: str, timeout_seconds: float) -> list[tuple[str, str]]:
    try:
        html = _fetch_text(source_url, timeout_seconds)
    except requests.RequestException:
        return []
    soup = BeautifulSoup(html, "html.parser")
    links: list[tuple[str, str]] = []
    for anchor in soup.select("a[href]"):
        title = _plain(anchor.get_text(" ", strip=True))
        href = anchor.get("href") or ""
        url = _absolute_cgu_url(href)
        if not title or not _is_downloadable_document(title, url):
            continue
        links.append((title, url))
    return links


def _related_document_explanations(
    spec: dict[str, Any],
    *,
    primary_url: str,
    raw_files_dir: Path | None,
    timeout_seconds: float,
) -> list[RuleExplanation]:
    related: list[RuleExplanation] = []
    for title, document_url in _select_related_documents(
        _document_links_from_page(str(spec["source_url"]), timeout_seconds),
        primary_url=primary_url,
    ):
        text = _fetch_pdf_text(
            document_url,
            title=title,
            raw_files_dir=raw_files_dir,
            timeout_seconds=timeout_seconds,
        )
        related.append(
            RuleExplanation(
                title=title,
                summary=_document_summary(title),
                key_points=_document_key_points("related_document", title, text),
                applies_to=list(spec.get("applies_to") or _infer_applies_to(title, text)),
                source=SourceReference(
                    title=str(spec["title"]),
                    source_url=str(spec["source_url"]),
                    category=PageCategory.SCHOLARSHIP,
                ),
                document_url=document_url,
                document_type=_infer_document_type(title),
                full_text_extracted=bool(text.strip()),
            )
        )
    return related


def _select_related_documents(links: list[tuple[str, str]], *, primary_url: str) -> list[tuple[str, str]]:
    selected: dict[str, tuple[int, str, str]] = {}
    for title, url in links:
        if url == primary_url or "操作說明" in title:
            continue
        if not any(keyword in title for keyword in ["申請表", "同意書", "計畫書", "報告", "聲明書", "契約書"]):
            continue
        key = _document_group_key(title)
        priority = _document_format_priority(title, url)
        if key not in selected or priority < selected[key][0]:
            selected[key] = (priority, title, url)
    return [(title, url) for _, title, url in selected.values()]


def _document_group_key(title: str) -> str:
    title = re.sub(r"\.(pdf|docx?|odt|pptx?)$", "", title, flags=re.I)
    title = re.sub(r"^[A-Z0-9]+\s*", "", title)
    return _plain(title)


def _document_format_priority(title: str, url: str) -> int:
    lowered = f"{title} {url}".lower()
    if ".pdf" in lowered:
        return 0
    if ".docx" in lowered:
        return 1
    if ".doc" in lowered:
        return 2
    if ".odt" in lowered:
        return 3
    return 4


def _is_downloadable_document(title: str, url: str) -> bool:
    lowered = f"{title} {url}".lower()
    return "/serverfile/get/" in lowered or any(
        lowered.endswith(extension) or extension in lowered
        for extension in [".pdf", ".doc", ".docx", ".ppt", ".pptx", ".odt"]
    )


def _absolute_cgu_url(href: str) -> str:
    if href.startswith("http://") or href.startswith("https://"):
        return href
    return f"{CGU_BASE_URL}{href if href.startswith('/') else '/' + href}"


def _fetch_pdf_text(
    url: str,
    *,
    title: str,
    raw_files_dir: Path | None,
    timeout_seconds: float,
) -> str:
    try:
        content = _fetch_binary(url, timeout_seconds)
    except requests.RequestException:
        return ""

    if raw_files_dir:
        _write_raw_document(raw_files_dir, title, content)

    if content.startswith(b"PK"):
        return _extract_docx_text(content)

    if PdfReader is None or not content.startswith(b"%PDF"):
        return ""

    try:
        reader = PdfReader(BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        return ""


def _extract_docx_text(content: bytes) -> str:
    try:
        with zipfile.ZipFile(BytesIO(content)) as archive:
            document_xml = archive.read("word/document.xml")
    except (KeyError, zipfile.BadZipFile):
        return ""
    try:
        root = ElementTree.fromstring(document_xml)
    except ElementTree.ParseError:
        return ""
    text_nodes = [
        node.text
        for node in root.iter()
        if node.tag.endswith("}t") and node.text
    ]
    return "\n".join(_plain(text) for text in text_nodes if _plain(text))


def _write_raw_document(raw_files_dir: Path, title: str, content: bytes) -> None:
    raw_files_dir.mkdir(parents=True, exist_ok=True)
    filename = re.sub(r'[<>:"/\\|?*\s]+', "_", title).strip("_")
    extension = _document_extension(filename, content)
    filename = re.sub(r"\.(pdf|docx?|odt|pptx?)$", "", filename, flags=re.I)
    path = raw_files_dir / f"{filename}{extension}"
    if not path.exists() or path.stat().st_size != len(content):
        path.write_bytes(content)


def _document_extension(filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".odt"}:
        return suffix
    if content.startswith(b"%PDF"):
        return ".pdf"
    if content.startswith(b"PK"):
        return ".docx"
    return ".bin"


def _document_key_points(slug: str, title: str, text: str) -> list[str]:
    exact = _rule_key_points(slug, text)
    if slug in {"navigator", "xuehai_sizhu"} and exact:
        return _dedupe_text(exact)[:10]
    generic = _generic_document_key_points(title, text)
    return _dedupe_text([*exact, *generic])[:10]


def _rule_key_points(slug: str, text: str) -> list[str]:
    compact = re.sub(r"\s+", "", text)
    if slug == "navigator":
        candidates = [
            (
                ["出國修讀學分", "學海飛颺"],
                "適用範圍：補助學生到國外大專校院修讀學分，包含學海飛颺等出國研修補助。",
            ),
            (
                ["就讀一學期以上", "在職專班"],
                "基本資格：須為長庚大學就讀一學期以上在學學生；國內及境外在職專班生不適用。",
            ),
            (
                ["中華民國國籍", "臺灣地區設有戶籍"],
                "身分資格：須具中華民國國籍，且在臺灣地區設有戶籍。",
            ),
            (
                ["學業成績平均達70", "70分以上"],
                "成績門檻：歷年學業成績平均以 70 分以上為原則。",
            ),
            (
                ["多益700", "TOEFLiBT"],
                "語言門檻：英文至少等同多益 TOEIC 700；也可用 IELTS 5.5、TOEFL iBT 72、Duolingo 105 等同級證明，若國外學校標準更高則依該校規定。",
            ),
            (
                ["不得同時領取", "其他出國研修補助"],
                "補助限制：不得同時領取我國政府提供的其他出國研修補助；同一學制期間已領過本校出國修讀學分補助者不可重複申請。",
            ),
            (
                ["75000", "150000", "75,000", "150,000"],
                "補助額度：依研修地區與期間不同，一學期上限可能為 75,000 或 60,000 元，一學年上限可能為 150,000 或 120,000 元。",
            ),
            (
                ["前30%", "壹萬元"],
                "加碼條件：申請時歷年學業成績班排名前 30%，補助金額得每學期增加 10,000 元。",
            ),
            (
                ["返國後兩週內", "心得"],
                "返國義務：研修期滿返國後兩週內須完成返校手續，並提交問卷、心得報告、經驗分享短片及心得電子檔。",
            ),
        ]
    elif slug == "xuehai_sizhu":
        candidates = [
            (
                ["學海惜珠", "勵學優秀學生"],
                "適用範圍：學海惜珠是給勵學優秀學生赴國外大專校院修讀學分的補助。",
            ),
            (
                ["中華民國國籍", "臺灣地區設有戶籍"],
                "身分資格：須具中華民國國籍，且在臺灣地區設有戶籍。",
            ),
            (
                ["低收入戶", "中低收入"],
                "經濟條件：須具低收入戶、中低收入戶或中低收入相關補助資格。",
            ),
            (
                ["就讀一學期以上", "在職專班"],
                "在學資格：須為長庚大學就讀一學期以上在學學生；國內及境外在職專班生不適用。",
            ),
            (
                ["學業及語文成績標準", "領航者補助作業要點"],
                "成績與語言：學業及語文標準原則上依「領航者補助作業要點」辦理，也就是仍要看 70 分與語言門檻。",
            ),
            (
                ["不得同時或重複領取", "政府其他出國研修獎學金"],
                "補助限制：不得同時或重複領取政府其他出國研修獎學金。",
            ),
            (
                ["一學期", "一學年", "經費預算調整"],
                "補助期限與額度：補助以一學期或一學年為限，實際額度依教育部當年度經費預算調整。",
            ),
            (
                ["家長或監護人同意書", "師長推薦函"],
                "申請文件：除教育部當年度規定文件外，通常還需要家長或監護人同意書、師長推薦函及其他佐證資料。",
            ),
        ]
    else:
        return []

    return [point for keywords, point in candidates if any(keyword in compact for keyword in keywords)]


def _generic_document_key_points(title: str, text: str) -> list[str]:
    compact = re.sub(r"\s+", "", f"{title}\n{text}")
    candidates = [
        (
            ["正式學籍之在學學生", "皆可參與進修交流"],
            "適用對象：具長庚大學正式學籍的在學學生可參與境外進修交流。",
        ),
        (
            ["雙聯學位", "一學季", "研究", "交流"],
            "交流類型：包含雙聯學位、一學季/期/年修課、研究與交流活動等。",
        ),
        (
            ["機票費", "簽證費", "生活費", "保險費"],
            "費用提醒：機票、簽證、生活費與保險費等通常由學生自理，若有補助則依補助規定辦理。",
        ),
        (
            ["學分採認", "學生赴境外修課申請表", "雙重學籍申請表"],
            "學分採認：出國修課前要先和系所或通識中心確認課程與學分採認，並辦理境外修課或雙重學籍申請。",
        ),
        (
            ["境外短期學分課程", "短期學分課程"],
            "適用範圍：這份文件主要用於境外短期學分課程或寒暑假短期課程。",
        ),
        (
            ["家長或監護人同意書"],
            "申請文件：通常需要家長或監護人同意書，未成年或需家長同意的情境要特別留意。",
        ),
        (
            ["計畫書"],
            "申請文件：若文件名稱包含計畫書，學生需要先整理出國目的、課程內容、學習規劃與預期成果。",
        ),
        (
            ["申請表"],
            "申請文件：這是申請流程需要填寫的正式表單，送件前要確認欄位、簽章與附件是否齊全。",
        ),
        (
            ["報告"],
            "返國或結案資料：這類報告通常是課程或補助結束後要繳交的成果文件。",
        ),
        (
            ["聲明書"],
            "承諾與聲明：這類文件通常用來確認學生了解補助規範、責任或不得重複領補助等限制。",
        ),
        (
            ["國外專業實習", "學海築夢", "新南向學海築夢"],
            "適用範圍：這份文件主要用於出國專業實習、學海築夢或新南向學海築夢補助。",
        ),
        (
            ["不得同時", "不得重複"],
            "補助限制：若文件提到不得同時或重複領取補助，學生需先確認自己是否已申請其他政府或校內補助。",
        ),
        (
            ["補助期限", "一學期", "一學年"],
            "期間限制：補助或研修期間可能限定為一學期、一學年或特定短期課程期間。",
        ),
        (
            ["截止日期", "截止日前", "校內作業時程"],
            "申請時程：文件若要求截止日前送件，仍要回到當年度公告確認實際日期。",
        ),
        (
            ["師長推薦函"],
            "申請文件：若要求師長推薦函，學生應提早請老師協助，避免壓線送件。",
        ),
    ]
    return [point for keywords, point in candidates if any(keyword in compact for keyword in keywords)]


def _document_summary(title: str) -> str:
    if "申請表" in title:
        return "這是申請時要填寫的正式表單，學生可以先看摘要確認用途，再開啟完整文件填寫。"
    if "同意書" in title:
        return "這是出國、補助或課程申請常見的同意文件，通常需要學生與家長/監護人確認後簽署。"
    if "計畫書" in title:
        return "這是說明出國學習或實習規劃的文件，重點通常包含目的、課程/實習內容與預期成果。"
    if "報告" in title:
        return "這是課程、研修或補助結束後的成果文件，學生可先確認返國或結案時要交什麼。"
    if "聲明書" in title:
        return "這是確認學生理解規定、責任或補助限制的聲明文件，簽署前應看清楚限制。"
    if "契約書" in title:
        return "這是接受補助或出國研修時的契約文件，重點在權利義務、違規或未完成時的處理方式。"
    if "補助" in title:
        return "這是補助相關規則，系統先整理資格、文件、額度、限制與義務，完整條文仍可開啟官方文件確認。"
    if "要點" in title:
        return "這是官方作業要點，系統先整理學生需要先知道的規定，完整條文仍可開啟官方文件確認。"
    return "這是官方公開文件，系統先整理用途與學生需要注意的重點；完整版本可從來源連結開啟。"


def _infer_document_type(title: str) -> str:
    for keyword, label in [
        ("申請表", "申請表"),
        ("同意書", "同意書"),
        ("計畫書", "計畫書"),
        ("報告", "報告"),
        ("聲明書", "聲明書"),
        ("契約書", "契約書"),
        ("補助", "補助要點"),
        ("要點", "作業要點"),
    ]:
        if keyword in title:
            return label
    return "官方文件"


def _infer_applies_to(title: str, text: str) -> list[str]:
    compact = f"{title}\n{text}"
    tags = []
    for keyword, tag in [
        ("交換", "交換學生"),
        ("雙聯", "雙聯學位"),
        ("短期", "短期課程"),
        ("學海惜珠", "學海惜珠"),
        ("學海築夢", "學海築夢"),
        ("新南向", "新南向學海築夢"),
        ("實習", "出國實習"),
        ("補助", "出國補助"),
    ]:
        if keyword in compact and tag not in tags:
            tags.append(tag)
    return tags or ["長庚學生出國"]


def _dedupe_text(items: list[str]) -> list[str]:
    seen: set[str] = set()
    results: list[str] = []
    for item in items:
        item = _plain(item)
        if item and item not in seen:
            seen.add(item)
            results.append(item)
    return results


def _application_periods(
    exchange_schools: ProcessedPage | None,
    double_degree_schools: ProcessedPage | None,
    short_courses: ProcessedPage | None,
) -> list[StudentInfoItem]:
    items: list[StudentInfoItem] = []
    for page, title in [
        (exchange_schools, "交換學生 / 自費研修"),
        (double_degree_schools, "雙學位"),
    ]:
        lines = _lines(page)
        autumn = _join_after(lines, "秋季班出國研修一學期或一學年", 1)
        spring = _join_after(lines, "春季班出國研修一學期", 1)
        details = [
            _clean_detail(autumn) or "秋季班出國研修一學期或一學年：11/01-12/20",
            _clean_detail(spring) or "春季班出國研修一學期：4/21-6/06",
            "申請表可選擇最適合的交換學校 2 所；若合作狀態異動，由國際處與學生協商替代學校。",
        ]
        items.append(StudentInfoItem(title=title, details=details, source=_source_ref(page)))

    if short_courses:
        details = _extract_matching_lines(
            short_courses,
            ["2026年暑假短期課程", "3月31日", "2026年寒假短期課程", "每位同學只能申請一間"],
            limit=4,
        )
        if details:
            items.append(StudentInfoItem(title="國外寒暑假短期課程", details=details, source=_source_ref(short_courses)))
    return items


def _program_overview(
    preparation: ProcessedPage | None,
    short_courses: ProcessedPage | None,
    teep: ProcessedPage | None,
) -> list[StudentInfoItem]:
    return [
        StudentInfoItem(
            title="雙學位",
            details=_slice_details(preparation, 1, 6),
            source=_source_ref(preparation),
        ),
        StudentInfoItem(
            title="學年/學期交換",
            details=_slice_details(preparation, 10, 13),
            source=_source_ref(preparation),
        ),
        StudentInfoItem(
            title="海外實習",
            details=_slice_details(preparation, 13, 20),
            source=_source_ref(preparation),
        ),
        StudentInfoItem(
            title="短期學分課程",
            details=_slice_details(short_courses, 4, 13),
            source=_source_ref(short_courses),
        ),
        StudentInfoItem(
            title="TEEP 研究實習",
            details=_slice_details(teep, 0, 6),
            source=_source_ref(teep),
        ),
    ]


def _eligibility(selection: ProcessedPage | None) -> list[StudentInfoItem]:
    details = _extract_matching_lines(
        selection,
        ["歷年學業成績平均以70以上", "語文能力證明", "請勿提出申請", "外國學生得申請非原國籍"],
        limit=8,
    )
    return [StudentInfoItem(title="校內申請資格", details=details, source=_source_ref(selection))]


def _language_requirements(selection: ProcessedPage | None) -> list[StudentInfoItem]:
    details = _extract_matching_lines(
        selection,
        [
            "等同多益 700",
            "全民英檢GEPT",
            "雅思IELTS",
            "網路托福TOEFL iBT",
            "多鄰國Duolingo",
            "日文",
            "法文",
            "德文",
            "西班牙文",
        ],
        limit=12,
    )
    return [StudentInfoItem(title="語言門檻", details=details, source=_source_ref(selection))]


def _required_documents(workflow: ProcessedPage | None) -> list[StudentInfoItem]:
    details = _extract_matching_lines(
        workflow,
        [
            "學生赴境外修課申請表",
            "雙重學籍申請表",
            "出國研修切結書",
            "在學役男出國相關文件",
            "出國通報單",
            "宿舍",
            "深耕學園藝文時數",
            "學生平安保險",
            "抵達國外報到表",
            "學期(季)報告表",
            "心得",
        ],
        limit=14,
    )
    return [StudentInfoItem(title="出國前後需處理文件", details=details, source=_source_ref(workflow))]


def _scholarship_info(preparation: ProcessedPage | None, teep: ProcessedPage | None) -> list[StudentInfoItem]:
    items = [
        StudentInfoItem(
            title="出國補助",
            details=_extract_matching_lines(
                preparation,
                ["國際處同步為學生申請教育部補助", "實際補助名額與額度", "符合本校補助規定者"],
                limit=4,
            ),
            source=_source_ref(preparation),
        )
    ]
    if teep:
        items.append(
            StudentInfoItem(
                title="TEEP 注意事項",
                details=_slice_details(teep, 0, 6),
                source=_source_ref(teep),
            )
        )
    return items


def _page_containing(page_map: dict[str, ProcessedPage], node_id: str) -> ProcessedPage | None:
    for url, page in page_map.items():
        if f"nodeId={node_id}" in url:
            return page
    return None


def _last_checked(pages: list[ProcessedPage], exchange_info: ExchangeInfo | None) -> datetime:
    if exchange_info and exchange_info.last_checked:
        return exchange_info.last_checked
    return max((page.crawled_at for page in pages), default=datetime.now(timezone.utc))


def _source_ref(page: ProcessedPage | None) -> SourceReference | None:
    if not page:
        return None
    return SourceReference(title=page.title, source_url=page.source_url, category=page.category)


def _dedupe_sources(sources: list[SourceReference | None]) -> list[SourceReference]:
    seen: set[str] = set()
    results: list[SourceReference] = []
    for source in sources:
        if not source or source.source_url in seen:
            continue
        seen.add(source.source_url)
        results.append(source)
    return results


def _page_text(page: ProcessedPage | None) -> str:
    return page.text if page else ""


def _lines(page: ProcessedPage | None) -> list[str]:
    if not page:
        return []
    return [_plain(line) for line in page.text.splitlines() if _plain(line)]


def _slice_details(page: ProcessedPage | None, start: int, end: int) -> list[str]:
    return [_clean_detail(line) for line in _lines(page)[start:end] if _clean_detail(line)]


def _extract_matching_lines(page: ProcessedPage | None, keywords: list[str], limit: int) -> list[str]:
    results: list[str] = []
    for line in _lines(page):
        if any(keyword in line for keyword in keywords):
            cleaned = _clean_detail(line)
            if cleaned and cleaned not in results:
                results.append(cleaned)
        if len(results) >= limit:
            break
    return results


def _join_after(lines: list[str], marker: str, following: int) -> str:
    for index, line in enumerate(lines):
        if marker in line:
            parts = [line, *lines[index + 1 : index + 1 + following]]
            return " ".join(parts)
    return ""


def _clean_detail(text: str) -> str:
    text = _plain(text)
    text = re.sub(r"^(:::|Previous|Next|進階搜尋|筆資料，目前在|/1頁)$", "", text)
    return text.strip(" -：:")


def _compact_long_text(text: str, limit: int = 360) -> str | None:
    text = _plain(text)
    if not text:
        return None
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "..."


def _plain(value: Any) -> str:
    text = unescape(str(value or ""))
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("\u3000", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()
