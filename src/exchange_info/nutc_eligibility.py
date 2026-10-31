from __future__ import annotations

import re

from .university_registry import NUTC, resolve_university

NUTC_OIA_HOME_URL = "https://oia.nutc.edu.tw/"
NUTC_OUTBOUND_EXCHANGE_URL = "https://oia.nutc.edu.tw/p/412-1026-8514.php?Lang=zh-tw"
NUTC_OUTBOUND_NOTICES_URL = "https://oia.nutc.edu.tw/p/403-1026-745-1.php?Lang=zh-tw"
NUTC_XUEHAI_NOTICES_URL = "https://oia.nutc.edu.tw/p/403-1026-746-1.php?Lang=zh-tw"
NUTC_XUEHAI_DATA_ZONE_URL = "https://oia.nutc.edu.tw/p/412-1026-9254.php?Lang=zh-tw"
NUTC_EXPERIENCES_URL = "https://oia.nutc.edu.tw/p/403-1026-955-1.php?Lang=zh-tw"
NUTC_REGULATIONS_URL = "https://oia.nutc.edu.tw/p/412-1026-102.php?Lang=zh-tw"
NUTC_FORMS_URL = "https://oia.nutc.edu.tw/p/412-1026-8451.php?Lang=zh-tw"
NUTC_PARTNERS_JAPAN_URL = "https://oia.nutc.edu.tw/p/404-1026-73311.php"
NUTC_PARTNERS_KOREA_URL = "https://oia.nutc.edu.tw/p/404-1026-73312.php"
NUTC_PARTNERS_SEA_URL = "https://oia.nutc.edu.tw/p/404-1026-73313.php"
NUTC_PARTNERS_EUR_US_URL = "https://oia.nutc.edu.tw/p/404-1026-73314.php"
NUTC_PARTNERS_OCEANIA_URL = "https://oia.nutc.edu.tw/p/404-1026-73315.php"
NUTC_PARTNERS_MAINLAND_URL = "https://oia.nutc.edu.tw/p/404-1026-99581.php"
NUTC_XUEHAI_REVIEW_RULES_PDF_URL = (
    "https://oia.nutc.edu.tw/var/file/26/1026/img/2252/173256894.pdf"
)
NUTC_XUEHAI_ZHUMENG_RULES_PDF_URL = (
    "https://oia.nutc.edu.tw/var/file/26/1026/img/2252/654705623.pdf"
)
NUTC_SPROUT_SUBSIDY_RULES_PDF_URL = (
    "https://oia.nutc.edu.tw/var/file/26/1026/img/2252/661467477.pdf"
)
NUTC_XUEHAI_115_ANNOUNCEMENT_URL = (
    "https://oia.nutc.edu.tw/p/406-1026-130835,r746.php?Lang=zh-tw"
)
NUTC_XUEHAI_115_PDF_URL = (
    "https://oia.nutc.edu.tw/var/file/26/1026/attach/98/pta_92544_1613108_64362.pdf"
)
NUTC_JBNU_2027_SPRING_URL = (
    "https://oia.nutc.edu.tw/p/406-1026-135710,r745.php?Lang=zh-tw"
)
NUTC_JBNU_2027_SPRING_PDF_URL = (
    "https://oia.nutc.edu.tw/var/file/26/1026/attach/11/pta_95851_7474640_60261.pdf"
)
NUTC_SYU_2027_SPRING_URL = (
    "https://oia.nutc.edu.tw/p/406-1026-135258,r745.php?Lang=zh-tw"
)
NUTC_SYU_2027_SPRING_PDF_URL = (
    "https://oia.nutc.edu.tw/var/file/26/1026/attach/99/pta_95590_2612481_14002.pdf"
)
NUTC_SAPPORO_2027_SPRING_URL = (
    "https://oia.nutc.edu.tw/p/406-1026-134919,r745.php?Lang=zh-tw"
)
NUTC_SAPPORO_2027_SPRING_PDF_URL = (
    "https://oia.nutc.edu.tw/var/file/26/1026/attach/2/pta_95308_2263834_20396.pdf"
)
NUTC_MAINLAND_2027_SPRING_URL = (
    "https://oia.nutc.edu.tw/p/406-1026-136798,r745.php?Lang=zh-tw"
)
NUTC_MAINLAND_2027_SPRING_PDF_URL = (
    "https://oia.nutc.edu.tw/var/file/26/1026/attach/98/pta_96597_1136748_50891.pdf"
)

NUTC_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 60.0),
    "ielts": ("IELTS", 5.0),
    "toeic": ("TOEIC", 550.0),
    "toefl_itp": ("TOEFL ITP", 460.0),
}


def is_nutc(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == NUTC.id:
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "國立臺中科技大學",
        "國立台中科技大學",
        "臺中科技大學",
        "台中科技大學",
        "中科大",
        "臺中科大",
        "台中科大",
        "nutc",
        "national taichung university of science and technology",
    }


def _is_graduate(degree_level: str | None) -> bool:
    text = (degree_level or "").strip()
    return any(token in text for token in ("碩", "博", "研究"))


def nutc_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
    degree = (degree_level or "").strip()
    year = (current_year or "").strip()
    if not degree:
        return (
            "needs_confirmation",
            (
                "尚未提供目前學制與年級；依《國立臺中科技大學學生申請教育部學海系列計畫審查要點》及各姊妹校交換留學簡章規定：（1）申請人須為申請時已就讀本校一學期以上之日間部與進修部非應屆畢業在籍學生（學士班、碩士班及五專部四年級(含)以上，不含專科部 1–3 年級生）；（2）境外生、延修生、休學學生、國內及境外在職專班生不得提出申請（赴大陸地區協議學校交換研習限臺灣本地生申請）；（3）交換期間須於本校辦理註冊繳費以保留學籍。"
            ),
        )
    if any(
        token in degree or token in year
        for token in (
            "休學",
            "已畢業",
            "退學",
            "延修",
            "延畢",
            "在職專班",
            "學分班",
            "選修生",
            "大一上",
            "五專一",
            "五專二",
            "五專三",
            "專一",
            "專二",
            "專三",
        )
    ):
        return (
            "fail",
            (
                f"已填報 {degree}{f'（{year}）' if year else ''}；依《國立臺中科技大學學生申請教育部學海系列計畫審查要點》及各姊妹校交換留學簡章規定，專科部 1–3 年級生、延修生、休學學生及在職專班生不得申請出國交換或學海系列計畫（五專部學生須達四年級(含)以上始得申請）。"
            ),
        )
    is_grad = _is_graduate(degree)
    grad_note = (
        "（提醒：碩士班研究生須已就讀本校滿一學期以上且非應屆畢業生，申請表須經指導教授與系所主管簽章，並可評估英國西蘇格蘭大學 UWS 碩士雙聯學位及教育部學海飛颺／惜珠獎學金）"
        if is_grad
        else "（提醒：學士班及五專部四年級(含)以上在籍學生須已於中科大就讀滿一學期以上且為非應屆畢業生；交換期間須於本校完成註冊繳費保留學籍，返國後須完成國際事務處志願服務 20 小時）"
    )
    return (
        "pass",
        (
            f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合《國立臺中科技大學學生申請教育部學海系列計畫審查要點》與交換留學在籍學制規定{grad_note}。"
        ),
    )


def nutc_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
    score_min = 70.0
    gpa_min = 2.7
    rank_max = 50.0
    details: list[str] = []
    passes_nutc = False

    if academic_score is not None:
        details.append(f"學期／歷年平均成績 {academic_score:g} 分")
        if academic_score >= score_min:
            passes_nutc = True
    if academic_gpa is not None:
        details.append(f"GPA {academic_gpa:g}")
        if academic_gpa >= gpa_min:
            passes_nutc = True
    if class_rank_percent is not None:
        details.append(f"班級排名百分比前 {class_rank_percent:g}%")
        if class_rank_percent <= rank_max:
            passes_nutc = True

    summary = "、".join(details)
    if (
        academic_score is None
        and academic_gpa is None
        and class_rank_percent is None
    ):
        return (
            "needs_confirmation",
            (
                "尚未填寫學期平均成績、GPA 或班級排名百分比；依《國立臺中科技大學學生申請教育部學海系列計畫審查要點》及各姊妹校交換留學簡章規定：（1）國外交換留學及教育部學海系列計畫申請人在學期間各科成績皆須達 70 分以上（檢附歷年成績單＋最近一學期含班級排名之中英文版成績單），且操行成績平均達 80 分（含）以上；（2）赴大陸地區協議學校交換研習者，歷年學業成績總平均及操行成績均須達 80 分（含）以上。"
            ),
        )

    if passes_nutc:
        top_rank = (
            (academic_score is not None and academic_score >= 80.0)
            or (academic_gpa is not None and academic_gpa >= 3.38)
            or (class_rank_percent is not None and class_rank_percent <= 25.0)
        )
        tier_note = (
            "同時符合國外姊妹校交換留學（各科 70 分以上）與赴大陸地區協議學校交換研習（歷年學業總平均 80 分［含］以上）標準，並具爭取教育部《學海飛颺》（每人補助 5 萬至 30 萬元）與《學海惜珠》獎學金之競爭優勢"
            if top_rank
            else "符合中科大國外姊妹校交換留學基本學業門檻（各科 70 分以上、操行 80 分以上）；惟若擬申請赴大陸地區協議學校交換研習，歷年學業成績總平均須達 80 分（含）以上"
        )
        return (
            "pass",
            f"已填報 {summary}；符合國立臺中科技大學出國交換留學暨學海系列計畫學業標準（{tier_note}）。",
        )

    return (
        "fail",
        (
            f"已填報 {summary}；未達國立臺中科技大學交換留學簡章規定之「在學各科成績 70 分（含）以上（相當於 GPA {gpa_min:g} 以上；赴大陸協議學校須歷年平均 80 分以上）且操行成績 80 分以上」門檻。"
        ),
    )


def nutc_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
    test = (language_test or "").strip().lower()
    if partner_country in {"中國大陸", "澳門"} and (
        not test or language_score is None
    ):
        return (
            "pass",
            (
                "申請赴大陸及澳門地區協議學校（如北京科技大學、中央財經大學、南開大學、上海戲劇學院、杭州電子科技大學、蘇州大學、東北大學、吉林大學、山東大學、廈門大學、福州大學、澳門科技大學等 55 校）交換研習，免附外語能力檢定證明（惟歷年學業成績平均及操行成績均須達 80 分［含］以上）。"
            ),
        )
    if not test or language_score is None:
        return (
            "needs_confirmation",
            (
                "尚未填寫外語能力檢定成績。依《國立臺中科技大學學生申請教育部學海系列計畫審查要點》第四點第（十）款及各姊妹校交換簡章規定（大陸港澳地區免附）：（1）日本地區姊妹校（札幌大學、札幌市立大學、國立新潟大學、國立信州大學、青森中央學院大學、長崎國際大學等）：須通過 JLPT N2 級及格以上（新潟大學經濟學部另須 TOEIC 550 分以上）；（2）韓國地區姊妹校：國立全北大學須通過 TOPIK 初級（Level 1/2）以上且 TOEIC 550 分以上，三育大學須附韓語能力證明（TOPIK 3 級以上尤佳）；（3）英語及歐美紐澳東南亞地區：依接待校標準（如印尼巴淡國際大學須 TOEIC 605 分以上），未訂標準者須提出全民英檢（GEPT）中級以上或 TOEFL iBT 60 分以上（或 TOEIC 550 / IELTS 5.0 等同級證明）。"
            ),
        )
    if test in NUTC_ENGLISH_MINIMUMS:
        label, minimum = NUTC_ENGLISH_MINIMUMS[test]
        passed = language_score >= minimum
        tier_note = "達《國立臺中科技大學學生申請教育部學海系列計畫審查要點》英語基本門檻（GEPT 中級 / TOEFL iBT 60 / TOEIC 550 / IELTS 5.0），可申請韓國全北大學英語門檻、日本新潟大學經濟學部英語門檻及東南亞英語授課學程"
        if (
            (test == "toefl" and language_score >= 79)
            or (test == "ielts" and language_score >= 6.0)
            or (test == "toeic" and language_score >= 785)
            or (test == "toefl_itp" and language_score >= 550)
        ):
            tier_note = "達 CEFR B2 高階英語標準，符合歐美（美國奧克拉荷馬州立大學、中央奧克拉荷馬大學、天普大學、北伊利諾大學；英國西蘇格蘭大學 UWS 雙聯學位 IELTS 6.0、諾丁漢特倫特大學；德國柏林經濟與法律應用科學大學；澳洲西雪梨大學、坎培拉大學）及印尼巴淡國際大學（TOEIC 605）等全數英語授課姊妹校與教育部《學海飛颺／惜珠》獎學金門檻"
        elif (
            (test == "toefl" and language_score >= 65)
            or (test == "ielts" and language_score >= 5.5)
            or (test == "toeic" and language_score >= 605)
            or (test == "toefl_itp" and language_score >= 500)
        ):
            tier_note = "符合印尼巴淡國際大學（TOEIC 605 免學費免住宿專案）、瑞士 BHMS、捷克赫拉德茨克拉洛韋大學及教育部《學海飛颺／惜珠》申請門檻"
        return (
            "pass" if passed else "fail",
            (
                f"{label} {language_score:g} {'符合' if passed else '未達'}國立臺中科技大學國際事務處出國交換暨學海系列計畫英語能力標準（校內基準門檻：{label} {minimum:g}；{tier_note}）。"
            ),
        )
    if test == "jlpt":
        level = int(language_score)
        passed = 1 <= level <= 2
        if level == 1:
            tier_note = "達 JLPT N1 最高日語標準，符合日本全部 20 所姊妹校（國立新潟大學、國立信州大學、札幌市立大學、札幌大學、青森中央學院大學、長崎國際大學、京都橘大學、名櫻大學、金澤星稜大學、目白大學、大阪觀光大學、環太平洋大學等）交換留學及教育部《學海飛颺／惜珠》、JASSO 獎學金門檻"
        elif level == 2:
            tier_note = "符合《國立臺中科技大學學生申請教育部學海系列計畫審查要點》及日本各姊妹校交換留學簡章規定之 JLPT N2 級及格以上標準（提醒：申請國立新潟大學經濟學部者另須檢附 TOEIC 550 分以上證明）"
        else:
            tier_note = "依《國立臺中科技大學學生申請教育部學海系列計畫審查要點》第四點第（十）款及日本姊妹校交換留學簡章規定，赴日本姊妹校交換須通過 JLPT N2 級（含）以上"
        return (
            "pass" if passed else "fail",
            f"JLPT N{level} {'符合' if passed else '未達'}國立臺中科技大學日本姊妹校交換留學日語能力標準（{tier_note}）。",
        )
    if test == "topik":
        level = int(language_score)
        passed = 1 <= level <= 6
        if level >= 3:
            tier_note = "符合中科大韓國姊妹校（國立全北大學、三育大學、韓世大學等）交換生韓語能力標準及教育部學海系列計畫要求（申請全北大學者另須同時具備 TOEIC 550 分以上或同等英語證明；三育大學提供交換生免費修讀語學堂 1–6 級課程）"
        else:
            tier_note = "符合韓國全北大學（JBNU）交換簡章規定之 TOPIK 初級（Level 1/2）以上韓語門檻（全北大學另須同時檢附 TOEIC 550 分以上證明；三育大學亦接受初級韓語證明並提供免費語學堂課程）"
        return (
            "pass" if passed else "fail",
            f"TOPIK {level} 級{'符合' if passed else '未達'}國立臺中科技大學韓國姊妹校韓語能力標準（{tier_note}）。",
        )
    if test in {"dele", "delf", "goethe", "testdaf", "tcf", "vinatest", "ivpt"}:
        passed = language_score >= 1.0
        return (
            "pass" if passed else "fail",
            f"{language_test.upper()} {language_score:g} {'符合' if passed else '未達'}國立臺中科技大學國際事務處非英日語國家外語能力證明標準。",
        )
    return (
        "needs_confirmation",
        f"已填報語言檢定 {language_test}（{language_score:g}）；請對照《國立臺中科技大學學生申請教育部學海系列計畫審查要點》與各姊妹校最新交換留學簡章確認。",
    )
