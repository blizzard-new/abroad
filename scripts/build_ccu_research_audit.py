"""Classify CCU research gaps from actual acquisitions, without inventing blockers.

Offline: reread keyword candidates are a work queue, never factual evidence.
Only the reviewed field file can supply facts. No school contact or login occurs.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from exchange_info.ccu_overseas import LABELS
from exchange_info.ccu_sources import BUNDLE

PATTERNS = {
    "program_scope": r"exchange|bilateral|campus|交換|校區",
    "eligibility": r"eligib|GPA|enrol|資格|年級",
    "language": r"language|TOEFL|IELTS|JLPT|HSK|CEFR|語言",
    "nomination_deadline": r"nominat|提名",
    "application_deadline": r"deadline|apply by|截止",
    "documents": r"document|passport|transcript|成績單|成绩单",
    "application_forms": r"form|申請表|申请表",
    "academic_calendar": r"calendar|exam|lecture|校曆|考試",
    "course_restrictions": r"course|credit|ECTS|課程|學分",
    "housing": r"accommod|housing|dorm|宿舍|住宿",
    "housing_deadline": r"accommod|housing|dorm|宿舍|住宿",
    "costs": r"cost|rent|currency|EUR|USD|KRW|JPY|費用|费用",
    "insurance": r"insurance|保險|保险",
    "visa": r"visa|簽證|签证|permit",
    "arrival": r"orient|arriv|迎新|報到|报到",
    "host_tuition": r"tuition|學費|学费|fee waiver",
    "exchange_duration": r"duration|semester|one year|學期|学期",
}


def write(name, value):
    (BUNDLE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def source_check(source, field, used, semantically_reviewed=()):
    sid = source["source_id"]
    timestamp = source["checked_at"]
    if source["status"] == "fetch_failed":
        result = f"讀取失敗；HTTP {source.get('http_status', '未取得')}；{source.get('error') or source.get('browser_check_error') or '詳見取得紀錄'}"
    elif source.get("access_result") in {
        "challenge_page",
        "captcha_required",
        "empty_response",
    }:
        result = (
            f"未取得政策正文；{source['access_result']}；"
            f"HTTP {source.get('http_status', 'web提取，無原始HTTP碼')}；"
            "限制頁或空白回應不能當政策讀取成功，沒有解驗證碼或存取挑戰。"
        )
    elif sid in used:
        result = "已取得並逐欄核對原文；本欄適用性見evidence，不由下載成功推定當期。"
    elif sid in semantically_reviewed:
        result = "已全文讀取並核對本欄；此來源未提供可直接映射的本欄當期依據，舊年及計畫範圍另見來源紀錄。"
    else:
        result = f"已取得{source['status']}；尚非本欄已核實依據，語意／年度／身分仍在補查佇列。"
    return {
        "source_id": sid,
        "source_url": source["source_url"],
        "checked_at": timestamp,
        "timestamp_precision": "date" if "T00:00:00" in timestamp else "datetime",
        "result": result,
    }


def classify(field, sources, candidates, page, key):
    if field["status"] == "verified_current":
        return (
            "verified_supported",
            "以本欄原文、年度及計畫為準；不代表全校17欄已完整。",
        )
    if field["status"] == "explicit_not_announced":
        return "official_not_announced", "僅限本欄原文明示TBC；其他缺值不推定尚未公告。"
    if field["status"] == "conflict":
        return (
            "unresolved_source_conflict",
            "已讀來源仍有年度、日期或計畫矛盾；繼續核對公開適用依據，未認定必須登入或聯絡校方。",
        )
    if key == "application_forms" and page == 53:
        return (
            "login_or_school_confirmation",
            "當期PDF所連學生GoogleForms兩份重試均HTTP401；未登入，無法讀實際表單內容。這不表示其他公開資料不存在。",
        )
    value = field["value"] or ""
    if field["evidence"] and re.search(r"帳號.*產生.*PDF", value):
        return (
            "login_or_school_confirmation",
            "公開指引說明須建立帳號並提交後才產生個人PDF，該個人表未取得；已讀公開LA和住宿PDF另列，其他公開資料仍可續查。",
        )
    if field["evidence"] and re.search(
        r"提名後.*通知|由.*寄送|Link sent by email|登入後|個別通知", value
    ):
        return (
            "login_or_school_confirmation",
            "公開原文指向個別通知或提名後表單；尚未登入或聯絡。其他公開替代來源仍可續查。",
        )
    if (
        field["status"] == "missing"
        and sources
        and all(s["status"] == "fetch_failed" for s in sources)
    ):
        return (
            "source_technical_failure",
            "已查入口實際失敗；這只描述本次來源結果，未認定所有官方替代入口不可取得。",
        )
    pending = (
        "已取得內容含候選段落，但尚未逐欄完成語意／年度／計畫核對。"
        if candidates
        else "尚未取得支持此欄當期適用性的原文；官方替代入口及深層附件仍須續查。"
    )
    return (
        "alternative_official_sources_not_fully_checked",
        pending + "不是官方明示尚未公告，也不是必須聯絡學校的結論。",
    )


def main():
    rows = json.loads((BUNDLE / "overseas-reviewed-fields.json").read_text())
    sources = {
        p.stem: json.loads(p.read_text())
        for p in (BUNDLE / "overseas_sources").glob("*.json")
    }
    ledger_path = BUNDLE / "semantic-review-ledger.json"
    ledger = (
        {row["ccu_page"]: row for row in json.loads(ledger_path.read_text())}
        if ledger_path.exists()
        else {}
    )
    passes = [
        json.loads(p.read_text()) for p in sorted(BUNDLE.glob("*-pass-changes.json"))
    ]
    changes = max(passes, key=lambda item: item["reviewed_at"])
    changed = {(x["ccu_page"], x["field"]): x for x in changes["changes"]}
    inventory, matrix = [], []
    counts = Counter(
        {
            k: 0
            for k in [
                "verified_supported",
                "official_not_announced",
                "unresolved_source_conflict",
                "login_or_school_confirmation",
                "source_technical_failure",
                "alternative_official_sources_not_fully_checked",
            ]
        }
    )
    for row in rows:
        acquired = [sources[sid] for sid in row["sources"]]
        candidates = []
        for key, field in row["fields"].items():
            if field["status"] != "missing":
                continue
            for source in acquired:
                for page, text in enumerate(source.get("text_pages", []), 1):
                    hits = list(re.finditer(PATTERNS[key], text, re.IGNORECASE))
                    if hits:
                        candidates.append(
                            {
                                "source_id": source["source_id"],
                                "field": key,
                                "source_page": page,
                                "source_status": source.get("content_applicability"),
                                "excerpts": [
                                    re.sub(
                                        r"\s+",
                                        " ",
                                        text[max(0, h.start() - 90) : h.end() + 320],
                                    )
                                    for h in hits[:2]
                                ],
                            }
                        )
        row_fields = {}
        for key, field in row["fields"].items():
            relevant = [c for c in candidates if c["field"] == key]
            category, note = classify(field, acquired, relevant, row["ccu_page"], key)
            review = ledger.get(row["ccu_page"], {}).get("fields", {}).get(key, {})
            read_sources = review.get("readable_source_ids", [])
            if review and category == "alternative_official_sources_not_fully_checked":
                note = (
                    "本輪所列可讀官方PDF/子頁已全文及逐欄核對，未找到本欄當期適用依據；"
                    "舊年、其他計畫與實際存取限制已記錄。其他官方入口仍可續查，"
                    "不是未讀候選段落，也不是官方明示尚未公告。"
                )
            used = {e["source_id"] for e in field["evidence"]}
            field.update(
                research_category=category,
                research_note=note,
                source_checks=[
                    source_check(s, key, used, read_sources) for s in acquired
                ],
            )
            counts[category] += 1
            row_fields[key] = {
                "status": field["status"],
                "category": category,
                "note": note,
                "acquired_unmapped_candidates": len(relevant),
                "source_checks": field["source_checks"],
            }
        inventory.append(
            {
                "ccu_page": row["ccu_page"],
                "school_name": row["school_name"],
                "candidates": candidates,
                "fields_reread_this_pass": [
                    changed[(row["ccu_page"], k)]
                    for k in LABELS
                    if (row["ccu_page"], k) in changed
                ],
                "remaining_review_status": (
                    "listed_sources_semantically_reviewed_more_sources_pending"
                    if row["ccu_page"] in ledger
                    else "pending_semantic_reread"
                    if candidates
                    else "alternative_sources_pending"
                ),
                "warning": "關鍵字只是候選索引；沒有逐欄確認的段落不能當證據。此佇列持續補查，不視為不可完成。",
            }
        )
        matrix.append(
            {
                "ccu_page": row["ccu_page"],
                "school_name": row["school_name"],
                "fields": row_fields,
            }
        )
    failures = []
    for sid, source in sorted(sources.items()):
        if source["status"] != "fetch_failed" or re.search(r"-r\d", sid):
            continue
        page = source.get("ccu_page", source.get("page"))
        retry = sources.get(sid + "-r2retry")
        alternatives = [
            s
            for s in sources.values()
            if s.get("ccu_page") == page and re.search(r"-r\d-", s["source_id"])
        ]
        failures.append(
            {
                "original": source_check(source, None, set()),
                "retry": source_check(retry, None, set()) if retry else None,
                "safe_alternatives": [
                    source_check(s, None, set()) for s in alternatives
                ],
                "conclusion": "原入口重試可讀；內容適用性仍另核對。"
                if retry and retry["status"] != "fetch_failed"
                else "原入口重試仍失敗；可讀替代資料已另逐欄核對，未查完的替代入口繼續補查。",
            }
        )
    write("overseas-reviewed-fields.json", rows)
    write("acquired-content-review.json", inventory)
    write(
        "research-gap-audit.json",
        {
            "reviewed_at": changes["reviewed_at"],
            "school_count": len(rows),
            "field_count": sum(counts.values()),
            "category_counts": dict(counts),
            "complete_research_claimed": False,
            "definition": "每欄區分事實狀態與查核工作進度；查核失敗或缺值不等於官方未公告或研究不可能。",
            "schools": matrix,
        },
    )
    write(
        "source-failure-followup.json",
        {"original_failed_source_count": len(failures), "sources": failures},
    )
    print(
        json.dumps(
            {"category_counts": dict(counts), "retry_count": len(failures)},
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
