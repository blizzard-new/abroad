from __future__ import annotations

import re

from .university_registry import UTAIPEI, resolve_university

UTAIPEI_OIA_HOME_URL = "https://international.utaipei.edu.tw/index.php"
UTAIPEI_SISTER_SCHOOLS_URL = "https://international.utaipei.edu.tw/p/412-1006-6691.php?Lang=zh-tw"
UTAIPEI_EXCHANGE_OVERVIEW_URL = "https://international.utaipei.edu.tw/p/412-1006-6692.php?Lang=zh-tw"
UTAIPEI_EXCHANGE_ASIA_URL = "https://international.utaipei.edu.tw/p/412-1006-5392.php?Lang=zh-tw"
UTAIPEI_EXCHANGE_NON_ASIA_URL = "https://international.utaipei.edu.tw/p/412-1006-5393.php?Lang=zh-tw"
UTAIPEI_DUAL_DEGREE_URL = "https://international.utaipei.edu.tw/p/412-1006-7685.php?Lang=zh-tw"
UTAIPEI_PROCESS_URL = "https://international.utaipei.edu.tw/p/412-1006-6857.php?Lang=zh-tw"
UTAIPEI_DOCUMENTS_URL = "https://international.utaipei.edu.tw/p/412-1006-7065.php?Lang=zh-tw"
UTAIPEI_FAQ_URL = "https://international.utaipei.edu.tw/p/412-1006-6861.php?Lang=zh-tw"
UTAIPEI_SCHOLARSHIPS_URL = "https://international.utaipei.edu.tw/p/412-1006-6925.php?Lang=zh-tw"
UTAIPEI_MOE_XUEHAI_URL = "https://international.utaipei.edu.tw/p/412-1006-6949.php?Lang=zh-tw"
UTAIPEI_LIVING_SUBSIDY_URL = "https://international.utaipei.edu.tw/p/412-1006-6957.php?Lang=zh-tw"
UTAIPEI_REGULATIONS_URL = "https://international.utaipei.edu.tw/p/412-1006-6682.php?Lang=zh-tw"
UTAIPEI_FORMS_URL = "https://international.utaipei.edu.tw/p/412-1006-7123.php?Lang=zh-tw"
UTAIPEI_EXPERIENCE_URL = "https://international.utaipei.edu.tw/p/412-1006-7510.php?Lang=zh-tw"
UTAIPEI_116_1_POST_URL = "https://international.utaipei.edu.tw/p/406-1006-135111,r567.php?Lang=zh-tw"
UTAIPEI_115_2_POST_URL = "https://international.utaipei.edu.tw/p/406-1006-131053,r567.php?Lang=zh-tw"
UTAIPEI_SELECTION_SUBSIDY_PDF_URL = "https://international.utaipei.edu.tw/var/file/6/1006/img/866152961.pdf"
UTAIPEI_COURSE_GUIDELINES_PDF_URL = "https://international.utaipei.edu.tw/var/file/6/1006/img/1244/157821227.pdf"
UTAIPEI_XUEHAI_GUIDELINES_PDF_URL = "https://international.utaipei.edu.tw/var/file/6/1006/img/656133403.pdf"

UTAIPEI_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 42.0),
    "ielts": ("IELTS", 4.0),
    "toeic": ("TOEIC", 550.0),
    "toefl_itp": ("TOEFL ITP", 433.0),
}


def is_utaipei(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == UTAIPEI.id:
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "臺北市立大學",
        "台北市立大學",
        "北市大",
        "utaipei",
        "ut",
        "university of taipei",
    }


def _is_graduate(degree_level: str | None) -> bool:
    text = (degree_level or "").strip()
    return any(token in text for token in ("碩", "博", "研究"))


def utaipei_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
    degree = (degree_level or "").strip()
    year = (current_year or "").strip()
    if not degree:
        return (
            "needs_confirmation",
            (
                "尚未提供目前學制與年級；依《臺北市立大學學生赴外研修甄選暨獎補助要點》第 3 點及當期《赴外姊妹校交換學生甄選簡章》規定："
                "（1）申請人須為於本校就讀一學期以上之在學學士班（實際出國交換時須為二年級以上）及碩、博士班（非當學期畢業）學生；"
                "（2）不含在職專班及休學生；（3）同一學制內以參加二次赴外交換為限（不同學制分開計算）。"
            ),
        )
    if any(
        token in degree or token in year
        for token in (
            "休學",
            "已畢業",
            "退學",
            "學分班",
            "選修生",
            "在職",
            "大一上",
            "專一",
            "專二",
            "專三",
        )
    ):
        return (
            "fail",
            (
                f"已填報 {degree}{f'（{year}）' if year else ''}；依《臺北市立大學學生赴外研修甄選暨獎補助要點》及當期《赴外姊妹校交換學生甄選簡章》規定，"
                "申請人須為於本校就讀一學期以上之正式在學學士班（出國時大二以上）或碩博士班（非當學期畢業）學生（大一上新生、在職專班生、休學生、已畢業生及非正式學籍生不得申請）。"
            ),
        )
    is_grad = _is_graduate(degree)
    grad_note = (
        "（提醒：碩博士班研究生須於本校就讀一學期以上且非當學期畢業；教育學系、音樂學系、英語教學系、經營管理碩士學位學程、體育學院及資訊科學系研究生另可評估美國 IUP、英國 University of Essex、紐西蘭奧克蘭大學、泰國朱拉隆功大學、馬來西亞馬來亞大學、哈薩克 Satbayev University 碩博士雙聯學位學程）"
        if is_grad
        else (
            "（提醒：大學部學生申請時須於本校就讀一學期以上、實際出國交換時須為學士班二年級以上；海外交換每學期至少應修習相當於本校 6 學分課程［歐洲 2 ECTS 折算 1 學分］，並可評估美國 SWOSU/Troy、英國 Essex/Trinity Laban/Nottingham、加拿大 Western 2+2 或 3+1 雙聯學位學程）"
        )
    )
    return (
        "pass",
        (
            f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合《臺北市立大學學生赴外研修甄選暨獎補助要點》與交換學生甄選簡章在學學制規定{grad_note}。"
        ),
    )


def utaipei_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
    score_min = 70.0
    gpa_min = 2.5
    rank_max = 50.0
    details: list[str] = []
    passes_utaipei = False

    if academic_score is not None:
        details.append(f"學業平均成績 {academic_score:g} 分")
        if academic_score >= score_min:
            passes_utaipei = True
    if academic_gpa is not None:
        details.append(f"GPA {academic_gpa:g}")
        if academic_gpa >= gpa_min:
            passes_utaipei = True
    if class_rank_percent is not None:
        details.append(f"班級排名百分比前 {class_rank_percent:g}%")
        if class_rank_percent <= rank_max:
            passes_utaipei = True

    summary = "、".join(details)
    if (
        academic_score is None
        and academic_gpa is None
        and class_rank_percent is None
    ):
        return (
            "needs_confirmation",
            (
                "尚未填寫學業平均成績、GPA 或班級排名百分比；依《臺北市立大學學生赴外研修甄選暨獎補助要點》及當期《赴外姊妹校交換學生甄選簡章》規定："
                "（1）前一學期操行成績須達 80 分以上，且在學期間未受申誡以上處分、無違反性平法或重大違法行為（須簽署《行為確認聲明書》）；"
                "（2）甄選優先順序分為四類：A 類（第一優先：前一學期學業成績班級排名前 40%）、B 類（第二優先：在學期間具專業著作／重要展演／全國或國際競賽獲獎）、"
                "C 類（第三優先：其他符合外語門檻者）、D 類（第四優先：同一學制第二次申請者）；"
                "（3）部分姊妹校另訂有個別 GPA 門檻（如 GPA 2.5–3.7 或 75 分以上），須同時符合姊妹校規定。"
            ),
        )

    if not passes_utaipei:
        return (
            "fail",
            (
                f"已填報 {summary}；未達臺北市立大學及海外姊妹校交換／雙聯學位建議學業基準"
                f"（學業平均 {score_min:g} 分以上、GPA {gpa_min:g} 以上或班級排名前 {rank_max:g}%，且前一學期操行成績須達 80 分以上）。"
            ),
        )

    is_cat_a = (
        (class_rank_percent is not None and class_rank_percent <= 40.0)
        or (academic_score is not None and academic_score >= 80.0)
        or (academic_gpa is not None and academic_gpa >= 3.2)
    )
    high_gpa = (
        (academic_gpa is not None and academic_gpa >= 3.0)
        or (academic_score is not None and academic_score >= 78.0)
    )

    if is_cat_a:
        tier_note = (
            "符合北市大「A 類（第一優先：前一學期班級排名前 40%）」甄選資格，於校內志願分發及返國生活獎補助（第 1、3 級優先順位）具最優先優勢；"
            "若歷年 GPA 達 3.0 以上，亦同時滿足英國 University of Essex / Nottingham、紐西蘭奧克蘭大學、泰國朱拉隆功大學、馬來西亞馬來亞大學雙聯學位與多數歐美日韓姊妹校門檻"
        )
    elif high_gpa:
        tier_note = (
            "符合北市大交換生與雙聯學位學業基準（若前一學期班排前 40% 列為 A 類第一優先，若有專業著作／展演／競賽獲獎列為 B 類第二優先，其餘列為 C 類第三優先），"
            "並達 GPA 3.0 門檻姊妹校（如英國 Essex / Nottingham、韓國仁荷大學 75 分、美國 SWOSU GPA 2.5 等）要求"
        )
    else:
        tier_note = (
            "符合北市大交換甄選 C 類（一般申請者）或 B 類（若有專業著作／展演／全國或國際競賽獲獎）資格及美國 Troy University（GPA 2.0）、SWOSU（GPA 2.5）等校門檻；"
            "惟請確認前一學期操行成績達 80 分以上，且若志願校要求更高 GPA（如 2.75 或 3.0 以上）須留意其個別限制"
        )

    return (
        "pass",
        f"已填報 {summary}；符合臺北市立大學出國交換學生暨雙聯學位學業審核基準（{tier_note}）。",
    )


def utaipei_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
    test = (language_test or "").strip().lower()
    if partner_country in {"中國大陸", "香港", "澳門"} and (not test or language_score is None):
        return (
            "pass",
            (
                "申請赴中國大陸及港澳地區締約姊妹校（如北京師範大學、華東師範大學、上海體育大學、北京體育大學、中央音樂學院、北京舞蹈學院、香港教育大學、澳門大學等）交換研修，依簡章規定華語地區免附外語能力檢定證明。"
            ),
        )
    if not test or language_score is None:
        return (
            "needs_confirmation",
            (
                "尚未填寫有效之語言能力檢定成績。依《臺北市立大學學生赴外研修甄選暨獎補助要點》及《各項英檢與 CEFR 架構對照表》規定："
                "（1）申請非華語國家須具備英語能力相當於 CEFR B1 級以上（全民英檢 GEPT 中級、TOEIC 550、TOEFL iBT 42［新制 3 分］、TOEFL ITP 433、IELTS 4.0、劍橋英檢 140、Linguaskill 140 或 Duolingo 60），"
                "或申請國語言 CEFR B1 以上檢定；（2）日本姊妹校依簡章要求 JLPT N1（大東文化大學）、JLPT N2（名古屋外國語大學、京都橘大學、東北大學等）或 JLPT N3（北海道教育大學、上越教育大學、中央大學等）；"
                "（3）韓國姊妹校依簡章要求 TOPIK 2–4 級或英語 CEFR B1/B2；（4）申請華語國家（中國大陸）免附外語檢定。"
            ),
        )
    if test in UTAIPEI_ENGLISH_MINIMUMS:
        label, minimum = UTAIPEI_ENGLISH_MINIMUMS[test]
        passed = language_score >= minimum
        tier_note = (
            "達北市大《各項英檢與 CEFR 架構對照表》CEFR B1 進階級基準（TOEIC 550 / TOEFL iBT 42 / TOEFL ITP 433 / IELTS 4.0），"
            "符合 CEFR B1 門檻之歐美亞姊妹校及返國生活獎補助 B1 等級資格"
        )
        if (
            (test == "toefl" and language_score >= 79)
            or (test == "ielts" and language_score >= 6.0)
            or (test == "toeic" and language_score >= 800)
            or (test == "toefl_itp" and language_score >= 550)
        ):
            tier_note = (
                "達高階英語標準（CEFR B2+），全面符合英國 University of Essex / Trinity Laban / Nottingham（IELTS 6.0–6.5）、"
                "紐西蘭奧克蘭大學（IELTS 6.5）、泰國朱拉隆功大學（iBT 79 / IELTS 6.5）、馬來西亞馬來亞大學（iBT 80 / IELTS 6.0）雙聯學位，"
                "以及法國雷恩商學院、德國科隆體育大學、美國舊金山州立大學等全數歐美亞 B2 姊妹校門檻，並於返國生活獎補助享 B2 優先級別"
            )
        elif (
            (test == "toefl" and language_score >= 72)
            or (test == "ielts" and language_score >= 5.5)
            or (test == "toeic" and language_score >= 785)
            or (test == "toefl_itp" and language_score >= 543)
        ):
            tier_note = (
                "達北市大《各項英檢與 CEFR 架構對照表》CEFR B2 高階級標準（TOEIC 785 / TOEFL iBT 72 / TOEFL ITP 543 / IELTS 5.5），"
                "符合美國舊金山州立大學、中央奧克拉荷馬大學、SWOSU / Troy 雙聯學位、法國雷恩商學院、德國科隆體育大學、波蘭體育大學等 B2 門檻姊妹校，並於返國生活獎補助列為 B2 優先級別"
            )
        return (
            "pass" if passed else "fail",
            (
                f"{label} {language_score:g} {'符合' if passed else '未達'}臺北市立大學國際事務處赴外交換暨雙聯學位英語能力標準"
                f"（校內非華語國家 CEFR B1 最低門檻：{label} {minimum:g}；{tier_note}）。"
            ),
        )
    if test == "jlpt":
        level = int(language_score)
        passed = 1 <= level <= 4
        if level == 1:
            tier_note = "達 JLPT N1 最高日語標準，符合大東文化大學（須 N1）、名古屋外國語大學／京都橘大學／東北大學（N2）及北海道教育大學／上越教育大學／中央大學（N3）等全數日本姊妹校門檻"
        elif level == 2:
            tier_note = "達 JLPT N2（CEFR B2 相當）標準，符合名古屋外國語大學、京都橘大學、東北大學、北海道教育大學、鳴門教育大學、上越教育大學、中央大學等絕大多數日本姊妹校門檻（惟大東文化大學須 N1）"
        elif level == 3:
            tier_note = "達 JLPT N3（CEFR B1 相當）標準，符合北海道教育大學、上越教育大學、中央大學、鳴門教育大學、環太平洋大學等日本姊妹校 N3 門檻（若申請名古屋外國語大學或京都橘大學則須 N2 以上）"
        elif level == 4:
            tier_note = "達 JLPT N4 基礎日語標準，可申請採認 N4 或英語授課學程之日本姊妹校（多數日本姊妹校日語組要求 N3 或 N2 以上）"
        else:
            tier_note = f"JLPT N{level} 未達臺北市立大學赴外交換 CEFR B1（原則上相當於 JLPT N3–N4 以上）及日本姊妹校門檻"
        return (
            "pass" if passed else "fail",
            f"JLPT N{level} {'符合' if passed else '未達'}臺北市立大學日本姊妹校交換學生日語能力標準（{tier_note}）。",
        )
    if test == "topik":
        level = int(language_score)
        passed = 2 <= level <= 6
        tier_note = (
            f"TOPIK {level} 級符合韓國首爾市立大學、梨花女子大學、檀國大學、世宗大學、誠信女子大學、釜山外國語大學等韓語組交換門檻"
            if passed
            else "韓國姊妹校韓語組原則上要求 TOPIK 2–4 級以上（或改以英語 CEFR B1/B2 成績申請英語授課學程）"
        )
        return (
            "pass" if passed else "fail",
            f"TOPIK {level} 級{'符合' if passed else '未達'}臺北市立大學韓國姊妹校韓語能力標準（{tier_note}）。",
        )
    if test in {"duolingo"}:
        passed = language_score >= 60.0
        return (
            "pass" if passed else "fail",
            f"Duolingo English Test {language_score:g} {'符合' if passed else '未達'}臺北市立大學《各項英檢與 CEFR 架構對照表》CEFR B1 門檻（最低 60 分；CEFR B2 為 100 分、美國 SWOSU 雙聯要求 85 分）。",
        )
    if test in {"dele", "delf", "goethe", "testdaf", "tcf", "gept", "cambridge", "linguaskill"}:
        passed = language_score >= 1.0
        return (
            "pass" if passed else "fail",
            f"{language_test.upper()} {language_score:g} {'符合' if passed else '未達'}臺北市立大學國際事務處外語能力檢定標準（須達 CEFR B1 以上並符合志願姊妹校規定）。",
        )
    return (
        "needs_confirmation",
        f"已填報語言檢定 {language_test}（{language_score:g}）；請對照臺北市立大學《各項英檢與 CEFR 架構對照表》與《116-1 赴外姊妹校交換學生甄選簡章》確認。",
    )
