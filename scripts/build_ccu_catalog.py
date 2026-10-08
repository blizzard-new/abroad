"""Rebuild CCU's school-isolated catalogue from the bundled colour PDF.

Offline by default. --refresh downloads ONLY CCU's current linked sources, checks
file signatures/content, then replaces them. Grey text is historical; a grey name
means explicitly not open (PDF p7). A blank quota never means zero or open.
No CGU/NTPU bundle is read or changed. No workflow is marked published.
"""

from __future__ import annotations
import argparse
import hashlib
import io
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit
from zipfile import ZipFile
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from pypdf import PdfReader
from exchange_info.ccu_sources import *
from exchange_info.models import (
    ExchangeFieldEvidence,
    PartnerStudentSummary,
    PartnerUniversity,
)

# Reviewed table starts: continuations, blank p90/p110, and p121 are excluded.
# p95 draws Adam Mickiewicz's notes before its heading in PDF reading order.
STARTS = [
    7,
    9,
    10,
    11,
    12,
    13,
    14,
    15,
    16,
    17,
    18,
    19,
    20,
    21,
    22,
    23,
    24,
    25,
    26,
    27,
    29,
    30,
    31,
    32,
    33,
    34,
    35,
    37,
    39,
    40,
    41,
    42,
    43,
    44,
    45,
    46,
    47,
    48,
    49,
    50,
    51,
    52,
    53,
    54,
    55,
    56,
    57,
    58,
    59,
    60,
    61,
    62,
    63,
    64,
    65,
    66,
    67,
    68,
    69,
    70,
    71,
    72,
    73,
    74,
    75,
    76,
    77,
    79,
    80,
    81,
    83,
    84,
    85,
    86,
    87,
    88,
    89,
    91,
    92,
    93,
    95,
    96,
    97,
    98,
    99,
    100,
    101,
    102,
    103,
    104,
    105,
    106,
    107,
    108,
    109,
    111,
    112,
    113,
    114,
    115,
    116,
    117,
    119,
    120,
]
LABELS = {
    "study_period": "交換期程",
    "quota": "甄選名額",
    "eligibility": "申請資格",
    "language_requirement": "語言能力",
    "fact_sheet": "姊妹校簡章",
    "partner_documents": "第二階繳交",
    "additional_info": "相關資料",
    "notes": "備註",
}


def compact(t):
    return re.sub(r"\s+", "", t)


def clean(t):
    return re.sub(r"\s+", " ", t).strip(" \n⚫▪•\uf09f")


def meaningful(t):
    return bool(re.search(r"[\w\u4e00-\u9fff]", t))


def is_grey(color):
    return min(color) >= 0.60 and max(color) - min(color) < 0.06


def spans_for_page(page):
    color = [(0.0, 0.0, 0.0)]
    stack = []
    spans = []
    last_y = 0.0
    last_x = 0.0

    def before(op, args, cm, tm):
        if op == b"q":
            stack.append(color[0])
        elif op == b"Q" and stack:
            color[0] = stack.pop()
        elif op == b"rg":
            color[0] = tuple(float(a) for a in args)
        elif op == b"g":
            color[0] = (float(args[0]),) * 3
        elif op == b"k":
            c, m, y, k = map(float, args)
            color[0] = tuple(1 - min(1, v + k) for v in (c, m, y))

    def visit(t, cm, tm, font, size):
        nonlocal last_y, last_x
        if not t:
            return
        x, y = float(tm[4]), float(tm[5])
        # Inline numeric chunks may be emitted at a reset text matrix.
        if x == 0 and y == 0:
            x, y = last_x, last_y
        else:
            last_x, last_y = x, y
        if 70 < y < 785:
            spans.append(dict(text=t, x=x, y=y, grey=is_grey(color[0]), color=color[0]))

    page.extract_text(visitor_operand_before=before, visitor_text=visit)
    return spans


def country_for(page):
    for stop, country in [
        (31, "中國大陸"),
        (39, "日本"),
        (55, "韓國"),
        (56, "香港"),
        (57, "澳門"),
        (61, "泰國"),
        (63, "馬來西亞"),
        (65, "印尼"),
        (71, "越南"),
        (80, "印度"),
        (83, "菲律賓"),
        (84, "賽普勒斯"),
        (88, "法國"),
        (90, "丹麥"),
        (94, "西班牙"),
        (95, "波蘭"),
        (97, "俄羅斯"),
        (102, "德國"),
        (104, "瑞士"),
        (106, "土耳其"),
        (113, "捷克"),
        (114, "挪威"),
        (118, "美國"),
        (119, "墨西哥"),
        (120, "澳洲"),
    ]:
        if page <= stop:
            return country
    raise ValueError(page)


def table_geometry(pdf_page):
    rects = [
        tuple(map(float, a))
        for a, op in pdf_page.get_contents().operations
        if op == b"re"
        and 75 < float(a[0]) < 150
        and float(a[2]) > 300
        and float(a[3]) > 10
    ]
    if not rects:
        return 100.0, []
    boundary = Counter(r[0] for r in rects).most_common(1)[0][0]
    width = Counter(round(r[2], 1) for r in rects).most_common(1)[0][0]
    return boundary, list(
        set(
            (r[1], r[1] + r[3])
            for r in rects
            if abs(r[0] - boundary) < 0.5 and abs(r[2] - width) < 1
        )
    )


def field_spans(page, geometry, carry="notes"):
    boundary, boxes = geometry
    markers = []
    left = [s for s in page if s["x"] < boundary and s["text"].strip()]
    for i, s in enumerate(left):
        candidate = compact(
            "".join(p["text"] for p in left[i : i + 5] if 0 <= s["y"] - p["y"] < 42)
        )
        for key, label in LABELS.items():
            if candidate.startswith(label) or (
                key == "eligibility" and candidate.startswith("申請條件及")
            ):
                if not any(k == key and abs(y - s["y"]) < 35 for k, y in markers):
                    markers.append((key, s["y"]))
    markers.sort(key=lambda t: -t[1])
    result = {}
    bounds = {}
    for key, y in markers:
        candidates = [(low, high) for low, high in boxes if low <= y <= high]
        if candidates:
            bounds[key] = max(candidates, key=lambda b: b[1] - b[0])
    # A merged left label can span several right-side programme subcells.
    for index, (key, y) in enumerate(markers[:-1]):
        next_key = markers[index + 1][0]
        if key in bounds and next_key in bounds:
            bounds[key] = (bounds[next_key][1], bounds[key][1])
    for s in page:
        if s["x"] < boundary:
            continue
        matches = [
            k for k, (low, high) in bounds.items() if low - 0.5 <= s["y"] <= high + 0.5
        ]
        if matches:
            key = matches[0]
        elif not markers:
            key = carry
        else:
            continue
        result.setdefault(key, []).append(s)
    return result, markers[-1][0] if markers else carry


def evidence(current, reference, pages, status=None, note=None):
    return ExchangeFieldEvidence(
        source_url=PARTNERS_URL,
        source_pages=sorted(set(pages)),
        academic_year=YEAR if current else None,
        application_round=ROUND if current else None,
        checked_at=CHECKED_AT,
        status=status
        or (
            "verified_current"
            if current
            else "reference_only"
            if reference
            else "missing"
        ),
        excerpt=current or None,
        reference_excerpt=reference or None,
        note=note,
    )


def row_for(reader, start, end):
    pages = list(range(start, end + 1))
    full = reader.pages[start - 1].extract_text()
    header = full.split("交換期程")[0].replace("2026.09.17", "").strip().splitlines()
    header = [s.strip() for s in header if s.strip() and not s.strip().isdigit()]
    if start == 7:
        header = header[-2:]
    elif start == 95:
        header = header[-2:]
    else:
        header = [
            s
            for s in header
            if not re.fullmatch(r"[\u4e00-\u9fff\s]+\([A-Za-z ]+\)", s)
        ]
    name = clean(" ".join(header))
    zh = header[-1]
    heading = [
        s
        for s in spans_for_page(reader.pages[start - 1])
        if compact(s["text"]) and compact(s["text"]) in compact(zh)
    ]
    if not heading:
        raise ValueError(f"No colour evidence for heading p{start}")
    closed = all(s["grey"] for s in heading)
    values = {}
    refs = {}
    ev = {}
    pieces = {}
    carry = "notes"
    links = []
    for n in pages:
        spans = spans_for_page(reader.pages[n - 1])
        fields, carry = field_spans(spans, table_geometry(reader.pages[n - 1]), carry)
        for key, ss in fields.items():
            pieces.setdefault(key, []).extend((n, s) for s in ss)
        for a in reader.pages[n - 1].get("/Annots", []):
            a = a.get_object()
            u = a.get("/A", {}).get("/URI")
            if isinstance(u, bytes):
                u = u.decode("utf-8", errors="replace")
            if u and u.startswith(("https://", "http://")):
                links.append(
                    dict(url=u, page=n, rect=list(map(float, a.get("/Rect", []))))
                )
    for key in LABELS:
        ss = pieces.get(key, [])
        current = clean(
            "".join(s["text"] for _, s in ss if not s["grey"] and not closed)
        )
        reference = clean("".join(s["text"] for _, s in ss if s["grey"] or closed))
        # Dark text can still explicitly label an attachment as an old version.
        if key == "fact_sheet" and re.search(r"舊簡章|供參考|做參考", current):
            reference = clean(" ".join([reference, current]))
            current = ""
        if not meaningful(current):
            current = ""
        if not meaningful(reference):
            reference = ""
        values[key] = current or None
        if reference:
            refs[key] = reference
        ev[key] = evidence(current, reference, [n for n, _ in ss] or [start])
        if key == "fact_sheet" and current:
            ev[key].status = "needs_confirmation"
            ev[key].note = "中正当期PDF所列連結；連結附件內容及適用年度尚未逐份核實。"
    quota = values["quota"]
    qs = (
        "reference_only"
        if closed
        else "not_published"
        if not quota
        else "zero"
        if re.fullmatch(r"0\s*名", quota)
        else "published"
    )
    availability = (
        "not_open"
        if closed
        else "needs_confirmation"
        if not quota
        else "zero_quota"
        if qs == "zero"
        else "open"
    )
    notes = values["notes"] or ""
    extra = values["additional_info"] or ""
    # Any explicit old-year dates remain reference, even when printed in dark text.
    lines = []
    for key in ("notes", "additional_info", "partner_documents"):
        for n, s in pieces.get(key, []):
            if s["grey"] or closed:
                continue
            # Collect actual rendered lines, not individual font/colour fragments.
            line_key = (n, round(s["y"]))
            if lines and lines[-1][0] == line_key:
                lines[-1] = (line_key, lines[-1][1] + s["text"])
            else:
                lines.append((line_key, s["text"]))
    combined = clean(" ".join(text for _, text in lines))
    deadline = re.findall(
        r"(?:Application\s*Deadline|申請截止日?期?)[^:：]{0,18}[:：]\s*([0-9]{4}[/.-][0-9]{1,2}[/.-][0-9]{1,2})",
        combined,
        re.I,
    )
    deadline = list(dict.fromkeys(deadline))
    current_dates = [
        d
        for d in deadline
        if d.startswith(("2026/", "2026-", "2026.", "2027/", "2027-", "2027."))
    ]
    past_dates = [d for d in deadline if d not in current_dates]
    partner_deadline = "、".join(current_dates) or None
    scoped_deadlines = clean(
        " ".join(
            text
            for _, text in lines
            if re.search(
                r"application\s*deadline|申請截止|HUSTEP:.*2026|SA/.*2026", text, re.I
            )
        )
    )
    if scoped_deadlines and re.search(r"202[67]", scoped_deadlines):
        partner_deadline = scoped_deadlines
    if not partner_deadline and re.search(r"申請截止日.*2026", notes):
        partner_deadline = notes
    if past_dates:
        refs["partner_application_deadline"] = "、".join(past_dates)
    ev["partner_application_deadline"] = evidence(
        partner_deadline,
        refs.get("partner_application_deadline"),
        pages,
        status="conflict" if len(current_dates) > 1 else None,
        note="日期未載時刻；不可建立精確提醒。"
        if partner_deadline
        else "灰字及舊年份日期不能當成2027春季期限。",
    )
    ev["nomination_deadline"] = evidence(
        None,
        None,
        pages,
        note="未核實當期逐校提名截止；由中正國際處依合作校通知辦理，不能用學生申請截止代替。",
    )
    # Retain all current course/housing notes; the original fields remain available.
    housing = (
        clean(
            " ".join(
                text
                for _, text in lines
                if re.search(r"住宿|housing|accommodation|dorm|rent", text, re.I)
            )
        )
        or None
    )
    fees = (
        clean(
            " ".join(
                text
                for _, text in lines
                if re.search(
                    r"學費|費用|生活費|tuition|fees?|cost|per.month|€|\$", text, re.I
                )
            )
        )
        or None
    )
    course = (
        clean(
            " ".join(
                text
                for _, text in lines
                if re.search(
                    r"選課|跨系|學分|課程|courses|credits|ECTS|facult", text, re.I
                )
            )
        )
        or None
    )
    semester = (
        clean(
            " ".join(
                text
                for _, text in lines
                if re.search(r"學期時間|學期期間", text) and "2027" in text
            )
        )
        or None
    )
    if start == 37:
        semester = "HUSTEP: 2027/04/01–2027/08/31；SA/SRS: 2027/04/01–2027/09/30（一學期）或2028/03/31（一學年）"
    if semester and re.search(r"2027.*[-–~].*2026", semester):
        refs["semester_dates"] = semester
        semester = None
        ev["semester_dates"] = evidence(
            None,
            refs["semester_dates"],
            pages,
            status="conflict",
            note="官方學期起迄年份矛盾，待承辦確認，未自行更正。",
        )
    for key, value in [
        ("housing_info", housing),
        ("tuition_info", fees),
        ("course_restrictions", course),
        ("semester_dates", semester),
    ]:
        if key not in ev:
            ev[key] = evidence(value, None, pages)
    ev["availability_status"] = evidence(
        "本季未開放交換" if closed else "校名非灰字；名額" + (quota or "空白"),
        None,
        [7, start],
    )
    ev["school_name"] = evidence(name, None, [start])
    ev["country"] = evidence(
        country_for(start), None, [start], note="依官方資料國別分段定位。"
    )
    r = home_round(name)
    online, paper = ROUND_DEADLINES[r]
    ev["application_deadline"] = ExchangeFieldEvidence(
        source_url=ANNOUNCEMENT_URL,
        source_pages=[],
        academic_year=YEAR,
        application_round=ROUND,
        checked_at=CHECKED_AT,
        status="verified_current",
        excerpt=f"第{r}梯次：線上 {online}；紙本 {paper}",
    )
    note = (
        "官方PDF p7：連同校名全數灰色字體，本季未開放交換。"
        if closed
        else "2027春季名額欄空白，名額尚未核實；不視為零名額或可申請。"
        if not quota
        else "2027春季名額已列；校內收件已截止，限既有申請人依提名通知辦理。"
    )
    row = PartnerUniversity(
        program_type="校級薦外交換",
        country=country_for(start),
        school_name=name,
        academic_year=YEAR,
        application_round=ROUND,
        checked_at=CHECKED_AT,
        source_pages=pages,
        source_url=PARTNERS_URL,
        availability_status=availability,
        availability_note=note,
        quota_status=qs,
        application_window_status="closed",
        agreement_level="校級",
        quota=quota,
        study_period=values["study_period"],
        eligibility=values["eligibility"],
        language_requirement=values["language_requirement"],
        application_deadline=f"{ROUND}第{r}梯次：線上 {online}；紙本 {paper}（已截止）",
        partner_application_deadline=partner_deadline,
        semester_dates=semester,
        housing_info=housing,
        tuition_info=fees,
        course_restrictions=course,
        application_info=values["partner_documents"],
        field_evidence=ev,
        reference_data=refs,
        colleges="工學院" if start == 103 else "管理學院" if start == 104 else None,
        student_summary_zh=PartnerStudentSummary(
            study_period=values["study_period"],
            application_deadline=partner_deadline,
            eligibility_points=[
                x for x in [values["eligibility"], values["language_requirement"]] if x
            ],
            application_steps=[x for x in [values["partner_documents"]] if x],
        ),
    )
    if start == 119:
        row.field_evidence["language_requirement"].status = "conflict"
        row.field_evidence[
            "language_requirement"
        ].note = "語言欄英文B2，第二階文件欄寫英文或西文B1；合作校承辦需確認。"
    if start == 10:
        row.field_evidence["additional_info"].status = "needs_confirmation"
        row.field_evidence[
            "additional_info"
        ].note = "當期中正PDF仍連向2022/2023系所頁；不得視為已核實2027課程或科系名單。"
    if start == 107:
        row.reference_data["partner_documents"] = row.application_info
        row.student_summary_zh.application_steps = [
            "中正PDF誤列一般入學流程的可能性待確認，不能當成交換必備文件。"
        ]
        row.application_info = "當期交換文件尚未核實；中正PDF第107頁列一般入學流程（含入學考試、繳學費），須確認是否誤用。原文保留於reference_data。"
        row.field_evidence["partner_documents"].status = "needs_confirmation"
        row.field_evidence["partner_documents"].note = row.application_info
        row.field_evidence["tuition_info"].status = "conflict"
        row.field_evidence[
            "tuition_info"
        ].note = "一般入學流程寫Pay tuition，中正交換簡章原則免合作校學費；是否適用交換待承辦確認。"
    if start == 85:
        row.tuition_info = "DEFLE法語課程：" + (row.tuition_info or "")
        row.field_evidence[
            "tuition_info"
        ].note = "不額外收費與不授學分僅屬DEFLE，不能套用所有普通學士或研究所課程。"
    if row.colleges:
        row.field_evidence["colleges"] = evidence(
            row.colleges, None, [start], note="合作校接收範圍，與中正母校資格分開。"
        )
    from exchange_info.models import PartnerProgramOption

    specs = []
    if start == 37:
        specs = [
            (
                "HUSTEP",
                "大學部",
                "限大三、大四；TOEFL iBT 79 / IELTS 6.5 / CEFR C1；須合作校推薦函格式。",
            ),
            (
                "SA",
                "大學部、研究所",
                "JLPT N2以上；不得跨系，不接受大四下應屆畢業生；研究生人文科學類請申請SRS。",
            ),
            ("SRS", "研究所", "主要研究；英文或日文流利。"),
        ]
    elif start == 35:
        specs = [
            (
                "IPLA",
                "大學部",
                "大二至大四，人文科學類；英檢必附，TOEFL iBT 79 / IELTS 6 / TOEIC 730 / CEFR B2。",
            ),
            (
                "JYPE",
                "大學部",
                "限大三、大四理工農；表中只列F+S或F，春季適用待承辦確認；TOEFL iBT 79 / IELTS 6 / TOEIC 730 / CEFR B2。",
            ),
            (
                "COLABS",
                "研究所",
                "自然科學、工程、醫學、藥學研究；TOEFL iBT 79 / IELTS 6 / TOEIC 730 / CEFR B2。",
            ),
            ("DEEP", "大學部", "JLPT N1；依官方計畫介紹核對。"),
        ]
    elif start == 103:
        specs = [
            (
                "SoE Bachelor",
                "大學部",
                "英文課程B2（IELTS 5.5 / TOEFL iBT 72）；德文課程德文B2；不得跨學制修碩士課。",
            ),
            (
                "SoE Master",
                "碩士班",
                "英文C1（IELTS 7.0 / TOEFL iBT 95）；檢定須2024/11/01之後。",
            ),
        ]
    elif start == 85:
        specs = [
            ("普通大學部課程", "大學部", "法文DELF B2；英文課程有限。"),
            ("普通研究所課程", "研究所", "法文DELF C1；英文課程有限。"),
            (
                "DEFLE法語課程",
                "學制尚未核實",
                "無須法文檢定／基礎，課前分級測驗；不授學分、不得修其他正規課，每週16小時法語課；交換生不額外收費。",
            ),
        ]
    for program, degree, rule in specs:
        deadline = partner_deadline
        period = row.study_period
        if start == 37:
            deadline = (
                "2026/10/23（未載時刻）"
                if program == "HUSTEP"
                else "2026/11/13（未載時刻）"
            )
            period = (
                "2027/04/01–2027/08/31"
                if program == "HUSTEP"
                else "2027/04/01–2027/09/30（一學期）或2028/03/31（一學年）"
            )
        elif start == 35 and program == "JYPE":
            period = "F+S或F（秋季起始；春季適用待承辦確認）"
        row.program_options.append(
            PartnerProgramOption(
                program_type=program,
                degree_levels=degree,
                eligibility=rule,
                source_url=PARTNERS_URL,
                application_deadline=deadline,
                study_period=period,
                application_info="名額屬全校共用，不按本方案另加名額；詳見官方PDF第"
                + "、".join(map(str, pages))
                + "頁。",
                student_summary_zh=PartnerStudentSummary(eligibility_points=[rule]),
            )
        )
    if specs:
        row.degree_levels = "大學部、碩士班" if start == 103 else "大學部、研究所"
        row.field_evidence["degree_levels"] = evidence(
            row.degree_levels,
            None,
            pages,
            note="逐計畫學制分開；不可跨計畫套用語言或課程限制。",
        )
    return row, dict(
        school_name=name,
        source_pages=pages,
        fields={k: v.model_dump(mode="json") for k, v in row.field_evidence.items()},
        related_links=links,
        links_status="extracted_from_official_pdf_not_individually_opened",
        reference_data=row.reference_data,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    BUNDLE.mkdir(parents=True, exist_ok=True)
    if args.refresh:
        import requests

        if datetime.now(timezone.utc).date() != CHECKED_AT.date():
            raise ValueError(
                "Update CCU source check date and verify the current round before a later-day refresh"
            )
        downloaded = {}
        for name, url in [
            ("2027-spring-partners.pdf", PARTNERS_URL),
            ("2027-spring-guidelines.pdf", GUIDELINES_URL),
            ("2027-spring-application.doc", FORM_DOC_URL),
            ("2027-spring-application.odt", FORM_ODT_URL),
            ("guardian-consent.pdf", GUARDIAN_URL),
        ]:
            response = requests.get(url, timeout=(15, 90))
            response.raise_for_status()
            content = response.content
            expected = (
                b"%PDF-"
                if name.endswith(".pdf")
                else b"PK"
                if name.endswith(".odt")
                else b"\xd0\xcf\x11\xe0"
            )
            if not content.startswith(expected):
                raise ValueError(f"{url}: wrong file signature, no overwrite")
            if name.endswith(".pdf"):
                pdf = PdfReader(io.BytesIO(content))
                expected_pages = (
                    121 if "partners" in name else 8 if "guidelines" in name else 1
                )
                title = "2027春季" if "2027" in name else "家長同意書"
                if len(pdf.pages) != expected_pages or title not in compact(
                    pdf.pages[0].extract_text()
                ):
                    raise ValueError(
                        f"{url}: applicable contents or layout changed, no overwrite"
                    )
            elif name.endswith(".odt"):
                with ZipFile(io.BytesIO(content)) as archive:
                    title_text = "".join(
                        ET.fromstring(archive.read("content.xml")).itertext()
                    )
                if "2027春季" not in compact(title_text):
                    raise ValueError(f"{url}: application title changed, no overwrite")
            elif "2027春季" not in content.decode("utf-16-le", errors="ignore"):
                raise ValueError(f"{url}: DOC application title changed, no overwrite")
            downloaded[name] = content
        for name, content in downloaded.items():
            (BUNDLE / name).write_bytes(content)
    reader = PdfReader(BUNDLE / "2027-spring-partners.pdf")
    guidelines = PdfReader(BUNDLE / "2027-spring-guidelines.pdf")
    if (
        len(reader.pages) != 121
        or "2027" not in reader.pages[0].extract_text()
        or "2027" not in guidelines.pages[0].extract_text()
    ):
        raise ValueError(
            "Unexpected cycle or layout: review source contents and STARTS before rebuilding"
        )
    rows = []
    details = []
    for i, start in enumerate(STARTS):
        row, detail = row_for(
            reader, start, (STARTS[i + 1] - 1) if i + 1 < len(STARTS) else 120
        )
        rows.append(row)
        details.append(detail)
    if len({r.school_name for r in rows}) != len(rows):
        raise ValueError("Duplicate partner identity")
    (BUNDLE / "partners.jsonl").write_text(
        "".join(r.model_dump_json() + "\n" for r in rows), encoding="utf-8"
    )
    from exchange_info.ccu_student_view import build_ccu_workflow
    from exchange_info.workflow_structuring import (
        structure_application_workflow,
        workflow_structure_issues,
    )

    workflows = [
        structure_application_workflow(build_ccu_workflow(row))
        for row in rows
        if row.availability_status != "not_open"
    ]
    issues = [issue for row in workflows for issue in workflow_structure_issues(row)]
    if issues:
        raise ValueError(f"CCU workflow structure failed: {issues}")
    (BUNDLE / "application_workflows.jsonl").write_text(
        "".join(r.model_dump_json() + "\n" for r in workflows), encoding="utf-8"
    )
    (BUNDLE / "field-audit.json").write_text(
        json.dumps(details, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    stats = dict(
        total=len(rows),
        workflow_count=len(workflows),
        availability=dict(Counter(r.availability_status for r in rows)),
        quota_status=dict(Counter(r.quota_status for r in rows)),
        current_field_counts={
            k: sum(
                k in r.field_evidence
                and r.field_evidence[k].status == "verified_current"
                for r in rows
            )
            for k in sorted({k for r in rows for k in r.field_evidence})
        },
        checked_at=CHECKED_AT.isoformat(),
        academic_year=YEAR,
        application_round=ROUND,
    )
    (BUNDLE / "completeness.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(stats, ensure_ascii=False))


if __name__ == "__main__":
    main()
