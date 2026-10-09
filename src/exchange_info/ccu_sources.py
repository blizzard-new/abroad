"""CCU outbound Spring 2027 sources; the school uses calendar-year rounds."""

import json
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path

HOME = "國立中正大學"
ROUND = "2027春季"
YEAR = "115"  # Spring 2027 = 115學年度第二學期, normalized by calendar.
CHECKED_AT = datetime(2026, 10, 8, tzinfo=UTC)
BUNDLE = Path(__file__).resolve().parent / "official_data" / "ccu"


@lru_cache(maxsize=1)
def source_security_reviews():
    path = BUNDLE / "tls-source-impact.json"
    return json.loads(path.read_text())["historical_sources"] if path.exists() else {}


def source_security_record(source):
    """Apply current-use restrictions without rewriting historical snapshots."""
    review = source_security_reviews().get(source["source_id"])
    if not review:
        return source
    result = {**source, "current_use_allowed": review["current_use_allowed"],
              "security_revalidation": review}
    if not review["current_use_allowed"]:
        result["historical_content_applicability"] = source.get("content_applicability")
        result["content_applicability"] = "needs_confirmation"
        result["content_review_note"] = "歷史略過憑證或其衍生取得；不作現行欄位依據，正常TLS新來源另列。"
    return result


def require_usable_source(source):
    if ("ignore_https_errors=True" in source.get("acquisition_method", "")
            or not source_security_record(source).get("current_use_allowed", True)):
        raise ValueError("Historical insecure CCU acquisition cannot support current mappings")
NEWS_URL = "https://oia.ccu.edu.tw/p/412-1008-3408.php?Lang=zh-tw"
ANNOUNCEMENT_URL = "https://oia.ccu.edu.tw/p/406-1008-93586,r1714.php?Lang=zh-tw"
PARTNERS_URL = "https://oia.ccu.edu.tw/var/file/8/1008/img/1130/717520038.pdf"
GUIDELINES_URL = (
    "https://oia.ccu.edu.tw/var/file/8/1008/attach/78/pta_54384_797227_45763.pdf"
)
FORM_DOC_URL = (
    "https://oia.ccu.edu.tw/var/file/8/1008/attach/78/pta_54382_5424695_45762.doc"
)
FORM_ODT_URL = (
    "https://oia.ccu.edu.tw/var/file/8/1008/attach/78/pta_54383_6330341_45763.odt"
)
GUARDIAN_URL = "https://oia.ccu.edu.tw/var/file/8/1008/img/1130/733224149.pdf"
TUTORIAL_URL = (
    "https://oia.ccu.edu.tw/var/file/8/1008/attach/78/pta_54385_8046857_45763.pdf"
)
PORTAL_URL = "https://www026147.ccu.edu.tw/cc_int/"
# Paper/online are separate required submissions. The opening is stated as 即日起.
ROUND_DEADLINES = {
    1: ("2026-08-26T23:59:00+08:00", "2026-08-27T17:00:00+08:00"),
    2: ("2026-09-06T23:59:00+08:00", "2026-09-07T17:00:00+08:00"),
    3: ("2026-09-20T23:59:00+08:00", "2026-09-21T17:00:00+08:00"),
}


def home_round(name: str) -> int:
    if "國立法政" in name:
        return 1
    if any(
        token in name
        for token in ("南丹麥", "北海道", "總統大學", "HCMUT胡志明", "維爾特克")
    ):
        return 2
    return 3
