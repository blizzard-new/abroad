"""Keep the reviewed FCU source generation and its program scopes together.

This is a bundle-building transformation, not a live-source verifier. The
2026-10-21 review read the listed quota, degree and language columns; it did
not establish current host admission, housing or calendar requirements.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

SOURCE_URL = "https://oiasap.fcu.edu.tw/v2/programs?sms=1151"
SOURCE_SHA256 = "9718ca3988d53984648aa4f1c53db0f0e6854746803f0001d7a937c3493e5f89"
SOURCE_FILE = "sources/fcu/oiasap_programs_1151_reviewed_20261021.json"
CHECKED_AT = "2026-10-20T19:15:10+00:00"
ROUND_NOTE = "115-1選送名單參考；校內申請已截止，不能沿用為116學年度或其他梯次的開放名額。"
DEADLINE = (
    "115-1赴2027春季交換的校內申請為2026/07/27至08/10 17:00，已截止。"
    "下一梯次的正式開放日期與個別方案仍待確認；雙聯學制另依其專案規定。"
)
SCHOLARSHIP_NOTE = (
    "逢甲出國研修獎助於線上報名後自動納入審核；實際名額與金額依當年預算、申請人數及審查核定，"
    "不是按排名保證固定金額。經濟弱勢或家庭突遭變故者可提出證明供審查。"
)


def review_common_text(value: str) -> str:
    """Correct only the specific shared assertions reviewed against pp. 6–9."""
    value = re.sub(
        r"（國際地區系排前 10% NT\$13,000[^。]*?清寒弱勢另加發補助）",
        "（名額與金額依預算及審查核定，非固定排名給付；經濟弱勢可附證明供審查）",
        value,
    )
    value = re.sub(
        r"逢甲大學(?:「出國研修獎助學金」|出國研修獎助學金)[^。\n]*NT\$13,000[^。\n]*。",
        SCHOLARSHIP_NOTE,
        value,
    )
    value = value.replace(
        "（初審自動審核，國際地區 NT$8,000–21,000、大陸地區 NT$4,000–11,000）",
        "（報名後自動納入審核；金額與名額依當年預算及審查核定）",
    )
    value = value.replace(
        "教育部「學海飛颺／學海惜珠」（至少 NT$60,000 起）",
        "教育部「學海飛颺」（每人至少 NT$60,000）／「學海惜珠」（依教育部核定，須另案申請）",
    )
    if "大學部一至三年級" in value:
        value = value.replace("大學部一至三年級", "學士班非應屆畢業學生")
        value = value.replace("大學部四年級（應屆畢業年級）", "學士班應屆畢業學生")
        value = value.replace("大學部四年級", "學士班應屆畢業學生").replace("大四", "學士班應屆畢業學生")
        value = value.replace("3 學分", "3 學分（特殊情況經系／學程主任核可並報教務處備查者例外）")
    for old in (
        "115-2 選送（赴 116 學年度 / 2027 秋季班研修）將於 2026/11/16–11/20 舉辦國際研習週說明會，並於 2026 年 12 月中旬公告簡章與開放報名。",
        "115-2 學年度選送（赴 116 學年度 / 2027 秋季班交換，可申請 1 學年或 1 學期）於 2026/11/16–11/20 舉辦國際研習週說明會，預計 2026 年 12 月中旬公告簡章並開放申請。",
    ):
        value = value.replace(old, "下一梯次正式期程、說明會及開放方案尚待核實；介紹頁的一般年度時程不等同當期公告。")
    return value


def load_reviewed_programs(root: Path) -> list[dict]:
    body = (root / SOURCE_FILE).read_bytes()
    if hashlib.sha256(body).hexdigest() != SOURCE_SHA256:
        raise ValueError("FCU reviewed source changed; a new scope review is required")
    return json.loads(body)["data"]


def matching_programs(school_name: str, programs: list[dict]) -> list[dict]:
    """Only documented spelling corrections; never fuzzy-match institutions."""
    matches = []
    for row in programs:
        zh = " ".join(row["name"].split())
        en = " ".join(row["name_en"].split())
        if zh == "關島大學" and en == "University of Guan":
            en = "University of Guam"  # Same URL and second official Guam row.
        if zh == "香港恒生大學(舊稱恒生管理學院)":
            zh = "香港恒生大學"
        if " ".join(f"{zh} {en}".split()) == " ".join(school_name.split()):
            matches.append(row)
    return matches


def _values(row: dict, key: str, name: str) -> str:
    return "、".join(dict.fromkeys(str(x[name]).strip() for x in row.get(key, []) if x.get(name))) or "未列，待確認"


def _language(row: dict) -> str:
    # A semicolon lists source entries without inventing an unconditional OR.
    values = []
    for item in row.get("lang_proficiency", []):
        value = " ".join(str(item.get(k) or "").strip() for k in ("name", "score")).strip()
        if item.get("commit"):
            value += f"（{item['commit'].strip()}）"
        if value:
            values.append(value)
    return "；".join(values) or "來源未列，待確認；不能推定免語檢"


def _quota(row: dict) -> str:
    value = str(row.get("quota") if row.get("quota") is not None else "").strip()
    if not value:
        return "來源未列，待確認"
    return value + " 名" if value.isdigit() else value


def _label(row: dict) -> str:
    tuition = (row.get("tuition_type") or {}).get("name") or "未列"
    return f"{row['program_id']} {row['program_type']}／學費{tuition}"


def _period(row: dict) -> str:
    if row["program_type"] == "學期交換":
        return "115-1甄選赴2027春季一學期；其他梯次待確認"
    return f"來源方案名稱：{row['program_type']}；實際研修年限依雙聯協議，不能套用交換一學期"


def apply_program_review(partner: dict, programs: list[dict]) -> None:
    rows = matching_programs(partner["school_name"], programs)
    fields = ("quota", "colleges", "degree_levels", "language_requirement", "study_period")
    partner["checked_at"] = CHECKED_AT
    evidence = partner.setdefault("field_evidence", {})
    if not rows:
        note = "本次取得的115-1官方名單未對上此既存紀錄；合作是否持續及適用方案仍待補查，不能推論已終止合作。"
        reference = partner.setdefault("reference_data", {})
        for field in fields:
            if partner.get(field):
                reference.setdefault(field, partner[field])
            partner[field] = "待確認（本輪115-1來源未對上；既有值保留於歷史參考）"
            evidence[field] = {
                "source_url": SOURCE_URL, "academic_year": "115",
                "application_round": "115-1", "checked_at": CHECKED_AT,
                "status": "needs_confirmation", "note": note,
            }
        partner["availability_status"] = "needs_confirmation"
        partner["quota_status"] = "reference_only"
        partner["application_window_status"] = "needs_confirmation"
        partner["availability_note"] = note
        partner["language_review_note"] = note
        partner["eligibility"] = note
        partner["course_restrictions"] = note
        partner["program_options"] = []
        partner["student_summary_zh"]["eligibility_points"] = [note]
    else:
        partner["availability_status"] = "reference_only"
        partner["quota_status"] = "reference_only"
        partner["application_window_status"] = "closed"
        partner["availability_note"] = ROUND_NOTE
        partner["academic_year"] = "115"
        partner["application_round"] = "115-1選送名單（歷史參考）"
        partner["language_review_note"] = (
            "此為115-1官方表列語檢參考。須按方案、學制、授課語言、單項分數及考試版本核對；"
            "不能取第一個分數作共同門檻，也不能宣告符合新梯次接待校要求。"
        )
        options = []
        for row in rows:
            pid = row["program_id"]
            language = _language(row)
            colleges = _values(row, "allow_colleges", "college_name")
            degrees = _values(row, "study_levels", "study_level_name")
            nationality = _values(row, "nationality", "nationality_name")
            # Retain comments verbatim, including their stated historical years.
            comment = (row.get("comment") or "").replace("\\n", "\n").strip()
            points = [
                f"115-1來源方案 {pid}；學院：{colleges}；學制：{degrees}",
                f"官方表列語檢（須依備註分別適用）：{language}",
                f"官方表列國籍：{nationality}；適用性仍須依本人身分確認",
            ]
            if comment:
                points.append(f"官方方案備註（原列年度須個別核對）：{comment}")
            options.append({
                "program_type": _label(row), "colleges": colleges,
                "degree_levels": degrees, "study_period": _period(row),
                "quota": _quota(row), "eligibility": "\n".join(points),
                "application_deadline": DEADLINE,
                "tuition_info": f"115-1官方表列學費：{(row.get('tuition_type') or {}).get('name') or '未列'}；其他費用待個別確認。",
                "source_url": SOURCE_URL,
                "student_summary_zh": {"eligibility_points": points, "study_period": _period(row)},
            })
        partner["program_options"] = options
        partner["program_type"] = "；".join(option["program_type"] for option in options)
        for field in ("quota", "colleges", "degree_levels", "study_period"):
            partner[field] = "；".join(f"{row['program_id']}：{option[field]}" for row, option in zip(rows, options))
        partner["language_requirement"] = "；".join(f"{row['program_id']}：{_language(row)}" for row in rows)
        partner["eligibility"] = "\n\n".join(option["eligibility"] for option in options)
        partner["course_restrictions"] = partner["eligibility"]
        partner["student_summary_zh"]["eligibility_points"] = [
            ROUND_NOTE,
            *[option["eligibility"] for option in options],
        ]
        for field in fields:
            evidence[field] = {
                "source_url": SOURCE_URL, "academic_year": "115",
                "application_round": "115-1", "checked_at": CHECKED_AT,
                "status": "reference_only", "reference_excerpt": partner[field],
                "note": f"{ROUND_NOTE} 原文定位：data中program_id=" + ",".join(row["program_id"] for row in rows),
            }
    partner["gpa_requirement"] = (
        "115-1母校簡章要求歷年GPA 3.0；接待校條件須依個別方案完整備註核對，"
        "不能從合併文字取第一個GPA作共同要求。"
    )
    partner["notes"] = partner["availability_note"] + "\n" + partner["eligibility"]
    partner["housing_info"] = "待確認：尚未取得此合作方案的住宿安排證據，不能以一般交換慣例保證校方協助或宿位。"
    partner["semester_dates"] = "待確認：須查接待校、校區及研修年度的正式行事曆，不能套用全國或全校通用月份。"
    partner["application_deadline"] = DEADLINE
    partner["student_summary_zh"]["study_period"] = partner["study_period"]
    partner["student_summary_zh"]["application_deadline"] = DEADLINE
    # These fields also appear in raw bundles, even though older models omit them.
    partner["student_summary_zh"]["quota"] = partner["quota"]
    partner["student_summary_zh"]["colleges"] = partner["colleges"]
    partner["student_summary_zh"]["degree_levels"] = partner["degree_levels"]
