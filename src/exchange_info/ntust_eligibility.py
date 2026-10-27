from __future__ import annotations

import re

from .university_registry import NTUST, resolve_university

NTUST_OUTBOUND_URL = "https://oia.ntust.edu.tw/p/405-1060-62102,c9056.php?Lang=zh-tw"
NTUST_APPLY_PORTAL_URL = "https://oia.ntust.edu.tw/p/405-1060-62102,c9056.php?Lang=zh-tw"
NTUST_QUOTALIST_URL = "https://oia.ntust.edu.tw/p/405-1060-62105,c9035.php?Lang=zh-tw"
NTUST_MAINLAND_URL = "https://oia.ntust.edu.tw/p/405-1060-143054,c9057.php?Lang=zh-tw"
NTUST_REGULATION_URL = "https://oia.ntust.edu.tw/var/file/60/1060/img/2289/948853506.pdf"

NTUST_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 57.0),
    "ielts": ("IELTS Academic", 4.0),
    "toeic": ("TOEIC", 550.0),
}


def is_ntust(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == NTUST.id:
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "國立臺灣科技大學",
        "國立台灣科技大學",
        "臺灣科技大學",
        "台灣科技大學",
        "臺科大",
        "台科大",
        "ntust",
        "taiwan tech",
        "national taiwan university of science and technology",
    }


def _is_graduate(degree_level: str | None) -> bool:
    text = (degree_level or "").strip()
    return any(token in text for token in ("碩", "博", "研究"))


def ntust_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
    degree, year = (degree_level or "").strip(), (current_year or "").strip()
    if any(token in degree for token in ("在職", "EMBA")):
        return "fail", "所讀116-1歐美亞澳及115-2大陸簡章均排除在職班。"
    if not degree or not year:
        return "needs_confirmation", "須確認學制、交換時年級及已有本校成績的學期數；不能只憑學制判定。"
    if any(token in degree for token in ("產學", "進修", "推廣")):
        return "needs_confirmation", "產學專班須於期限內上傳贊助企業及專班主任書面同意；其他特殊學制另核。"
    if any(token in year for token in ("大一", "大學一年級", "學士班一年級")):
        return "needs_confirmation", "條文以交換時大二以上及申請時本校一學年成績為準；目前年級不足以確認兩條件。"
    if _is_graduate(degree) and any(token in year for token in ("碩一", "博一", "一年級")):
        return "needs_confirmation", "研究所交換時須碩一以上；116-1資格表共用欄列本校一學年成績，115-2大陸組列一學期。須按計畫及實際成績確認，並取得指導教授簽名同意。"
    return "pass", "已填學制與年級在一般範圍；仍須核對本校成績期間、持續在學、指導教授同意及接待校條件。最後一學期不開放赴日本交換。"


def ntust_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
    if partner_country in {"中國大陸", "大陸地區"}:
        if not degree_level or academic_score is None:
            return "needs_confirmation", "115-2大陸簡章須按學制核對歷年總平均：大學部75分、研究所80分。GPA或排名不能代替。"
        minimum = 80 if _is_graduate(degree_level) else 75
        return ("pass" if academic_score >= minimum else "fail",
                f"115-2大陸簡章之{degree_level}歷年總平均門檻為{minimum}分；此為已截止梯次規則，新梯次須重新確認。")
    if class_rank_percent is None or not 0 < class_rank_percent <= 100:
        return "needs_confirmation", "116-1歐美亞澳簡章要求114-2學期班排名前70%（經系所審查通過例外）；平均65分或GPA2.3不能替代該排名。"
    if class_rank_percent > 70:
        return "needs_confirmation", "已填排名不在70%內，但官方允許經系所審查通過者例外，須確認系所核可，不能直接判定不符。"
    return "needs_confirmation", "已填排名在70%內，但須確認是簡章指定的114-2學期班排名，而非歷年累計或系排名；接待校條件及特殊系所仍另核。"


def ntust_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
    mainland = partner_country in {"中國大陸", "大陸地區"}
    test = (language_test or "").strip().lower()
    scope = "115-2大陸組（已截止梯次）" if mainland else "116-1歐美亞澳組"
    if not test or language_score is None:
        return "needs_confirmation", f"{scope}有語檢要求，不能視為免語檢；英語基本門檻為TOEIC550、舊制TOEFL iBT57或IELTS4.0，接待校更高條件另核。"
    if test == "toefl" and language_score <= 6:
        return "needs_confirmation", "須確認TOEFL考試版本及計分尺度；116-1報名列新制4分，獎助段落列3.5分，不能把6分制與120分制混用或僅因達獎助分數判定可申請。"
    if test in NTUST_ENGLISH_MINIMUMS:
        label, minimum = NTUST_ENGLISH_MINIMUMS[test]
        return ("pass" if language_score >= minimum else "fail",
                f"{scope}母校{label}門檻為{minimum:g}；語檢效期、系所額外要求及接待校要求另核。達此門檻不等於具備獎學金資格。")
    if not mainland and test == "jlpt":
        return ("pass" if language_score in {1, 2} else "fail", "116-1母校日語基準為JLPT N2以上，接待校及授課語言另核。")
    if not mainland and test == "topik":
        return ("pass" if language_score in {3, 4, 5, 6} else "fail", "116-1母校韓語基準為TOPIK3以上，不能以TOPIK2判通過。")
    return "needs_confirmation", f"須核對{scope}接受的檢定種類及效期，不能把其他組別語言條件直接套用。"
