from __future__ import annotations

import re

from .university_registry import NCKU, resolve_university

NCKU_OUTBOUND_URL = "https://oia.ncku.edu.tw/p/404-1032-227700.php?Lang=zh-tw"
NCKU_116_1_ANNOUNCEMENT_URL = "https://oia.ncku.edu.tw/p/406-1032-301175,r3414.php?Lang=zh-tw"
NCKU_GUIDELINES_PDF_URL = "https://oia.ncku.edu.tw/var/file/32/1032/img/107138261.pdf"
NCKU_PARTNERS_PDF_URL = "https://oia.ncku.edu.tw/var/file/32/1032/img/535260712.pdf"
NCKU_PORTAL_URL = "https://exchange.oia.ncku.edu.tw/index.php?outgoing_auth"
NCKU_REGULATION_URL = "https://oia.ncku.edu.tw/p/404-1032-227702.php?Lang=zh-tw"
NCKU_SCHOLARSHIP_URL = "https://oia.ncku.edu.tw/p/404-1032-228571.php?Lang=zh-tw"
NCKU_EXPERIENCE_URL = "https://oia.ncku.edu.tw/p/405-1032-252564,c29777.php?Lang=zh-tw"

NCKU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 72.0),
    "toefl_new": ("TOEFL iBT 新制", 4.0),
    "ielts": ("IELTS Academic", 5.5),
    "toeic": ("TOEIC Listening & Reading", 785.0),
}


def is_ncku(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == NCKU.id:
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "國立成功大學",
        "成功大學",
        "成大",
        "ncku",
        "cheng kung university",
        "national cheng kung university",
    }


def _is_graduate(degree_level: str | None) -> bool:
    text = (degree_level or "").strip()
    return any(token in text for token in ("碩", "博", "研究"))


def ncku_degree_check(degree_level: str | None, current_year: str | None = None) -> tuple[str, str]:
    degree, year = (degree_level or "").strip(), (current_year or "").strip()
    is_grad = _is_graduate(degree)
    is_undergrad = any(token in degree for token in ("大學", "學士"))
    if not is_grad and not is_undergrad:
        return "needs_confirmation", "須確認實際學制與年級。116-1簡章允許在職專班申請，獎學金及接待校資格另依各自規定。"
    if is_undergrad and year in {"一年級", "大一", "1"}:
        return "fail", "116-1母校資格要求大學部二年級以上；大一未達此門檻。"
    if is_undergrad and year not in {"大二", "大三", "大四", "大五", "大六", "二年級", "三年級", "四年級", "五年級", "六年級", "2", "3", "4", "5", "6", "延畢"}:
        return "needs_confirmation", "尚須確認大學部二年級以上及持續在學資格；轉學生另須在成大就讀至少一學期。"
    return "pass", (
        f"已填報{degree}（{year or '研究所在學'}）；符合116-1母校表列年級門檻。"
        "從報名開始至交換結束須維持成大在學身分及同一學位別；同一學制曾參加校級交換者仍可申請，"
        "但不得再申請相同交換校。轉學生、國籍與先前放棄資格等限制仍須核對。"
    )


def ncku_academic_check(degree_level: str | None, academic_score: float | None,
                        academic_gpa: float | None = None, class_rank_percent: float | None = None) -> tuple[str, str]:
    if _is_graduate(degree_level):
        return "pass", "116-1研究所無校內成績最低門檻，仍須取得指導教授同意；甄選在校成績占50%，接待校GPA門檻另行核對。"
    if not any(token in (degree_level or "") for token in ("學士", "大學")):
        return "needs_confirmation", "尚須確認學制，才能套用大學部或研究所成績規定。"
    if (academic_score is not None and academic_score >= 77) or (class_rank_percent is not None and 0 < class_rank_percent <= 50):
        return "pass", "符合116-1大學部前一學期平均77分（含）以上或全班／全系排名前50%的擇一門檻；成績期間及證明仍須核對。"
    if academic_score is None or class_rank_percent is None:
        return "needs_confirmation", "尚未完整提供前一學期平均或班／系排名；已知項目未能證實擇一門檻。簡章沒有提供GPA換算替代門檻，不能只憑GPA判定合格。"
    return "fail", "已提供的平均成績與排名均未達116-1大學部77分（含）以上或前50%的擇一門檻；GPA不能自行換算替代。"


def ncku_language_check(language_test: str | None, language_score: float | None,
                        *, partner_country: str | None = None) -> tuple[str, str]:
    test = (language_test or "").strip().lower()
    note = "證明須為2024年11月20日以後的有效成績；接待校可另訂總分、小分、效期及測驗採認要求。申請中國學校也須提出母校要求的外語證明。"
    if not test or language_score is None:
        return "needs_confirmation", "116-1母校門檻為TOEFL iBT72或新制4、IELTS Academic5.5、TOEIC785，或符合接待校要求的其他外語證明。" + note
    if test in NCKU_ENGLISH_MINIMUMS:
        label, minimum = NCKU_ENGLISH_MINIMUMS[test]
        maximum = {"toefl":120,"toefl_new":6,"ielts":9,"toeic":990}[test]
        if not 0 <= language_score <= maximum:
            return "fail", f"{label}分數超出此測驗量尺，請確認測驗種類與成績。"
        passed = language_score >= minimum
        return ("pass" if passed else "fail", f"{label} {language_score:g}{'符合' if passed else '未達'}116-1母校分數門檻{minimum:g}。此項僅比較分數。" + note)
    if test in {"jlpt", "topik"}:
        levels = {1,2,3,4,5} if test == "jlpt" else {1,2,3,4,5,6}
        if language_score not in levels:
            return "fail", f"{test.upper()}等級格式不正確，請核對正式成績。"
        return "needs_confirmation", f"已填報{test.upper()} {language_score:g}級；母校沒有此語種的統一級數門檻，須先確認接待校採認與要求等級，不能僅憑有效級數判定合格。" + note
    return "needs_confirmation", f"已填報{language_test} {language_score:g}；須確認接待校是否接受此測驗以及所需門檻。" + note
