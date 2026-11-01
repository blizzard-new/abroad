from __future__ import annotations

import re

from .university_registry import TNUA, resolve_university

TNUA_OIA_HOME_URL = "https://oia.tnua.edu.tw/"
TNUA_OIA_STAFF_URL = "https://oia.tnua.edu.tw/staff/"
TNUA_SISTER_SCHOOLS_URL = "https://oia.tnua.edu.tw/%e5%a7%8a%e5%a6%b9%e6%a0%a1/"
TNUA_OUTBOUND_EXCHANGE_URL = (
    "https://oia.tnua.edu.tw/student-out/%e4%ba%a4%e6%8f%9b%e7%94%9f/"
)
TNUA_XUEHAI_FEIYANG_URL = (
    "https://oia.tnua.edu.tw/student-out/%e5%ad%b8%e6%b5%b7%e9%a3%9b%e9%a2%ba/"
)
TNUA_XUEHAI_XIZHU_URL = (
    "https://oia.tnua.edu.tw/student-out/%e5%ad%b8%e6%b5%b7%e6%83%9c%e7%8f%a0/"
)
TNUA_XUEHAI_ZHUMENG_URL = "https://oia.tnua.edu.tw/student-out/%e5%ad%b8%e6%b5%b7%e7%af%89%e5%a4%a2-%e6%96%b0%e5%8d%97%e5%90%91%e5%ad%b8%e6%b5%b7%e7%af%89%e5%a4%a2/"
TNUA_SHARED_CAMPUS_URL = "https://oia.tnua.edu.tw/sc-intro/"
TNUA_UMAP_URL = "https://oia.tnua.edu.tw/umap%e4%ba%9e%e5%a4%aa%e5%a4%a7%e5%ad%b8%e4%ba%a4%e6%b5%81%e6%9c%83/"
TNUA_REGULATIONS_URL = (
    "https://oia.tnua.edu.tw/student-out/%e7%9b%b8%e9%97%9c%e8%be%a6%e6%b3%95/"
)
TNUA_EXPERIENCE_REPORT_URL = (
    "https://oia.tnua.edu.tw/student-out/%e5%bf%83%e5%be%97%e5%a0%b1%e5%91%8a/"
)
TNUA_EXPERIENCE_GDRIVE_URL = "https://drive.google.com/drive/folders/1XiLr5x48f8-fcPpYW13pUehnGBVqw0Fz?usp=sharing"
TNUA_116_POST_URL = "https://oia.tnua.edu.tw/news/%e3%80%90%e4%ba%a4%e6%8f%9b%e7%94%9f%e8%a8%88%e7%95%ab%e3%80%91116%e5%ad%b8%e5%b9%b4%e5%ba%a6%ef%bc%882027-2028%ef%bc%89%e6%9c%ac%e6%a0%a1%e5%a7%8a%e5%a6%b9%e6%a0%a1%e4%ba%a4%e6%8f%9b%e5%ad%b8/"
TNUA_115_2_POST_URL = "https://oia.tnua.edu.tw/news/%e3%80%90%e4%ba%a4%e6%8f%9b%e7%94%9b%e8%a8%88%e7%95%ab%e3%80%91115-2%e5%ad%b8%e6%9c%9f%ef%bc%882027%e6%98%a5%e5%ad%a3%e7%8f%ad%ef%bc%89%e6%9c%ac%e6%a0%a1%e5%a7%8a%e5%a6%b9%e6%a0%a1%e4%ba%a4/"
TNUA_115_XUEHAI_POST_URL = "https://oia.tnua.edu.tw/news/%e3%80%90%e7%8d%8e%e5%ad%b8%e9%87%91%e3%80%91115%e5%b9%b4%e3%80%8c%e6%95%99%e8%82%b2%e9%83%a8%e9%bc%93%e5%8b%b5%e5%9c%8b%e5%85%a7%e5%a4%a7%e5%b0%88%e6%a0%a1%e9%99%a2%e9%81%b8%e9%80%81%e5%ad%b8/"
TNUA_SELECTION_REGULATIONS_PDF_URL = "https://drive.google.com/uc?export=download&id=1Cs7HYIzxzbGNjmA2i3SvwKKhsKrRXAbV"
TNUA_XUEHAI_GUIDELINES_PDF_URL = "https://drive.google.com/uc?export=download&id=1FdHbYsni5Q17JrhWocUu6AS51rRKZuXT"
TNUA_116_GUIDE_PDF_URL = "https://drive.google.com/uc?export=download&id=1NsldQmV16z_pdpSe0cwDHONcT0ZWqL7P"
TNUA_PARTNERS_EUROPE_PDF_URL = "https://drive.google.com/uc?export=download&id=1GqC-Zfj4GGbAshYmY7XTjs6kUJ-vXEMQ"
TNUA_PARTNERS_ASIA_PDF_URL = "https://drive.google.com/uc?export=download&id=1Prw7b1FbjB2tXTT3xxXTvWYFBS7AdFA3"

TNUA_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 60.0),
    "ielts": ("IELTS", 5.5),
    "toeic": ("TOEIC", 600.0),
    "toefl_itp": ("TOEFL ITP", 500.0),
}


def is_tnua(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == TNUA.id:
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "國立臺北藝術大學",
        "國立台北藝術大學",
        "臺北藝術大學",
        "台北藝術大學",
        "北藝大",
        "北藝",
        "國立藝術學院",
        "tnua",
        "taipei national university of the arts",
    }


def _is_graduate(degree_level: str | None) -> bool:
    text = (degree_level or "").strip()
    return any(token in text for token in ("碩", "博", "研究"))


def tnua_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
    degree = (degree_level or "").strip()
    year = (current_year or "").strip()
    if not degree:
        return (
            "needs_confirmation",
            (
                "尚未提供目前學制與年級；依《國立臺北藝術大學選送學生出國研修辦法》及當期《姊妹校交換學生甄選簡章》規定："
                "（1）申請人須為本校學士班二年級以上學生（不含在職專班）或碩、博士班於本校就讀一學期以上之正式在學學生；"
                "（2）各學制學生於同一學制就讀期間，以參加一次選送赴外交換為限（學士班延修生若於一至四年級期間未曾赴外交換者，得提出申請）；"
                "（3）法國國立巴黎高等藝術學院（Beaux-Arts de Paris）僅限大三學生申請且延修生不能申請；香港浸會大學、泰國瑪希敦大學僅限大學部學生申請。"
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
            "大一",
            "專一",
            "專二",
            "專三",
        )
    ):
        return (
            "fail",
            (
                f"已填報 {degree}{f'（{year}）' if year else ''}；依《國立臺北藝術大學選送學生出國研修辦法》及《姊妹校交換學生甄選簡章》規定，"
                "申請人須為本校學士班二年級以上（不含在職專班）或碩、博士班於本校就讀一學期以上之正式在學學生（大一新生、在職專班生、休學生、已畢業生及非正式學籍生不得申請）。"
            ),
        )
    is_grad = _is_graduate(degree)
    grad_note = (
        "（提醒：碩、博士班研究生須於北藝大就讀滿一學期以上；出國交換期間除繳交全額學雜費基數外，最低應修習 6 學分並繳納最低 6 學分之學分費；法國巴黎高等美院與香港浸會大學僅開放大學部申請）"
        if is_grad
        else (
            "（提醒：學士班學生須為二年級以上［不含在職專班］；法國國立巴黎高等藝術學院 Beaux-Arts de Paris 僅限大三學生申請且延修生不得申請；赴外交換期間即使為延修生仍須繳交北藝大全額學雜費）"
        )
    )
    return (
        "pass",
        (
            f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合《國立臺北藝術大學選送學生出國研修辦法》與姊妹校交換學生甄選簡章在學學制規定{grad_note}。"
        ),
    )


def tnua_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
    score_min = 70.0
    gpa_min = 2.5
    rank_max = 50.0
    details: list[str] = []
    passes_tnua = False

    if academic_score is not None:
        details.append(f"學業平均成績 {academic_score:g} 分")
        if academic_score >= score_min:
            passes_tnua = True
    if academic_gpa is not None:
        details.append(f"GPA {academic_gpa:g}")
        if academic_gpa >= gpa_min:
            passes_tnua = True
    if class_rank_percent is not None:
        details.append(f"班級／系所排名前 {class_rank_percent:g}%")
        if class_rank_percent <= rank_max:
            passes_tnua = True

    summary = "、".join(details)
    if (
        academic_score is None
        and academic_gpa is None
        and class_rank_percent is None
    ):
        return (
            "needs_confirmation",
            (
                "尚未填寫學業平均成績、GPA 或班級排名百分比；依《國立臺北藝術大學選送學生出國研修辦法》及《辦理教育部鼓勵國內大專校院選送學生出國研修或國外專業實習補助要點作業規定》："
                "（1）交換甄選採「各系所／學院初審推薦（依學業成績、專業作品集／展演影音連結、讀書計畫與外語能力排序）→ 國際事務處複審」兩階段審查；"
                "（2）部分姊妹校明訂 GPA 門檻（如香港浸會大學、香港城市大學創意媒體學院要求 GPA 2.5–3.0 以上，韓國藝術綜合學校、中央大學、成均館大學要求平均 80 分或 GPA 3.0 以上）；"
                "（3）若同步申請教育部《學海飛颺》或《學海惜珠》獎學金，校內評選依「歷年學業成績與班級排名、外語能力證明、研修計畫及專業表現」綜合核定補助額度。"
            ),
        )

    if not passes_tnua:
        return (
            "fail",
            (
                f"已填報 {summary}；未達國立臺北藝術大學及海外藝術姊妹校交換建議學業基準"
                f"（學業平均 {score_min:g} 分以上、GPA {gpa_min:g} 以上或班級排名前 {rank_max:g}%，且須無重大懲處紀錄）。"
            ),
        )

    is_top_tier = (
        (class_rank_percent is not None and class_rank_percent <= 25.0)
        or (academic_score is not None and academic_score >= 82.0)
        or (academic_gpa is not None and academic_gpa >= 3.4)
    )
    is_xuehai_tier = (
        (class_rank_percent is not None and class_rank_percent <= 40.0)
        or (academic_score is not None and academic_score >= 75.0)
        or (academic_gpa is not None and academic_gpa >= 3.0)
    )

    if is_top_tier:
        tier_note = (
            "達北藝大七大學院（音樂、美術、戲劇、舞蹈、電影與新媒體、文化資源、人文）初審優先薦送基準及教育部《學海飛颺》高優補助門檻，"
            "於申請歐美日韓頂尖藝術高等學府（如倫敦藝術大學 UAL、蘇黎世藝術大學 ZHdK、巴黎高等美院、東京藝術大學、韓國藝術綜合學校 K-Arts 等）及 Shared Campus 專案具高度競爭優勢"
        )
    elif is_xuehai_tier:
        tier_note = (
            "符合北藝大交換生甄選與教育部《學海飛颺／學海惜珠》申請基準，"
            "並達多數歐美日韓及香港（香港浸會大學、香港城市大學 GPA 2.5–3.0）姊妹校學業門檻"
        )
    else:
        tier_note = (
            "符合北藝大交換生甄選基本學業基準；藝術院校姊妹校極重視專業作品集（Portfolio）或演奏／展演影音紀錄（Audition Link）及外語能力，建議強化作品集與讀書計畫以提升學院推薦排序"
        )

    return (
        "pass",
        f"已填報 {summary}；符合國立臺北藝術大學出國交換學生學業審核基準（{tier_note}）。",
    )


def tnua_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
    test = (language_test or "").strip().lower()
    if partner_country in {"中國大陸"} and (not test or language_score is None):
        return (
            "pass",
            (
                "申請赴中國大陸地區締約姊妹校（中央音樂學院、中國美術學院、北京電影學院、北京舞蹈學院、上海音樂學院、上海戲劇學院、中央戲劇學院、中國音樂學院、中國戲曲學院、廈門大學共 10 校）交換研修，"
                "依《大陸地區姊妹校交換名額一覽表》規定免附外語能力檢定證明，惟須依姊妹校要求備妥專業作品集、演奏／展演影音連結與讀書計畫。"
            ),
        )
    if not test or language_score is None:
        return (
            "needs_confirmation",
            (
                "尚未填寫有效之語言能力檢定成績。依《國立臺北藝術大學選送學生出國研修辦法》、《姊妹校交換學生甄選簡章》及《國際姊妹校交換名額一覽表》規定："
                "（1）英語授課及歐美亞藝術院校：原則須具備 CEFR B1–B2 以上證明（如 TOEFL iBT 60–80、IELTS 5.5–6.5、TOEIC 600–785；例如倫敦藝術大學 UAL、皇家威爾斯音樂戲劇學院 RWCMD、香港浸會大學、香港城市大學要求 IELTS 6.0–6.5 或 TOEFL iBT 79+）；"
                "（2）歐洲各語區藝術院校：德國、奧地利音樂與藝術大學多要求德語 CEFR B1–B2（Goethe / TestDaF），法國高等藝術與音樂院多要求法語 DELF/TCF B1–B2（巴黎高等美院要求法語 B2），西班牙要求西語 DELE B1–B2；"
                "（3）日韓地區：東京藝術大學、京都市立藝術大學、沖繩縣立藝術大學等建議具備 JLPT N2–N3 或英語檢定；韓國藝術綜合學校（K-Arts）、中央大學、成均館大學等要求 TOPIK 2–3 級或英語檢定；"
                "（4）中國大陸 10 所姊妹校免附外語檢定，惟申請教育部《學海飛颺》獎學金者必須檢附符合簡章規定之外語能力證明。"
            ),
        )
    if test in TNUA_ENGLISH_MINIMUMS:
        label, minimum = TNUA_ENGLISH_MINIMUMS[test]
        passed = language_score >= minimum
        tier_note = (
            "達北藝大國際姊妹校交換與教育部《學海飛颺》英語基本基準（CEFR B1 相當：TOEFL iBT 60 / TOEFL ITP 500 / IELTS 5.5 / TOEIC 600）"
        )
        if (
            (test == "toefl" and language_score >= 80)
            or (test == "ielts" and language_score >= 6.0)
            or (test == "toeic" and language_score >= 785)
            or (test == "toefl_itp" and language_score >= 550)
        ):
            tier_note = (
                "達高階英語標準（CEFR B2：TOEFL iBT 80+ / IELTS 6.0–6.5 / TOEIC 785+），"
                "符合英國倫敦藝術大學（UAL）、皇家威爾斯音樂戲劇學院（RWCMD）、瑞士蘇黎世藝術大學（ZHdK）、荷蘭烏特勒支藝術大學（HKU）、"
                "加拿大魁北克大學蒙特婁分校（UQAM）、香港城市大學、香港浸會大學、新加坡拉薩爾藝術學院（LASALLE）等英語授課頂尖藝術院校門檻"
            )
        elif (
            (test == "toefl" and language_score >= 70)
            or (test == "ielts" and language_score >= 5.5)
            or (test == "toeic" and language_score >= 650)
            or (test == "toefl_itp" and language_score >= 520)
        ):
            tier_note = (
                "達多數歐洲（荷蘭、捷克、芬蘭、挪威、波蘭、奧地利、德國英語授課學程）及亞洲（韓國 K-Arts、日本九州大學、泰國瑪希敦大學）姊妹校英語交換門檻"
            )
        return (
            "pass" if passed else "fail",
            (
                f"{label} {language_score:g} {'符合' if passed else '未達'}國立臺北藝術大學國際事務處赴外交換暨教育部學海飛颺英語能力標準"
                f"（建議基本基準：{label} {minimum:g}；{tier_note}）。"
            ),
        )
    if test == "jlpt":
        level = int(language_score)
        passed = 1 <= level <= 4
        if level in (1, 2):
            tier_note = (
                f"達 JLPT N{level} 標準，完全符合東京藝術大學、京都市立藝術大學、沖繩縣立藝術大學、金澤美術工藝大學、名古屋藝術大學、京都藝術大學、九州大學等全數日本姊妹校日語門檻及教育部學海飛颺語言基準"
            )
        elif level in (3, 4):
            tier_note = (
                f"達 JLPT N{level} 標準，符合多數日本藝術姊妹校基礎日語交流門檻（部分學校如京都市立藝術大學、金澤美術工藝大學建議具備 N2–N3 以上日語會話能力）"
            )
        else:
            tier_note = f"JLPT N{level} 未達日本姊妹校交換生建議日語能力基準（須達 JLPT N4–N2 以上）"
        return (
            "pass" if passed else "fail",
            f"JLPT N{level} {'符合' if passed else '未達'}國立臺北藝術大學日本姊妹校交換學生日語能力標準（{tier_note}）。",
        )
    if test == "topik":
        level = int(language_score)
        passed = 2 <= level <= 6
        if level >= 3:
            tier_note = (
                f"TOPIK {level} 級完全符合韓國藝術綜合學校（K-Arts）、中央大學、成均館大學、同德女子大學、秋溪藝術大學等全數韓國姊妹校韓語授課門檻"
            )
        elif level == 2:
            tier_note = "TOPIK 2 級符合韓國藝術綜合學校（K-Arts）多數院系基礎韓語基準（部分理論或戲劇學系要求 TOPIK 3–4 級或英語檢定）"
        else:
            tier_note = "韓國姊妹校要求 TOPIK 2–3 級以上，或改以英語檢定成績申請英語授課課程"
        return (
            "pass" if passed else "fail",
            f"TOPIK {level} 級{'符合' if passed else '未達'}國立臺北藝術大學韓國姊妹校韓語能力標準（{tier_note}）。",
        )
    if test in {"duolingo"}:
        passed = language_score >= 85.0
        return (
            "pass" if passed else "fail",
            f"Duolingo English Test {language_score:g} {'符合' if passed else '未達'}歐美部分藝術姊妹校英語替代檢定基準（建議達 90–105 分以上，並請確認志願校是否採認 Duolingo）。",
        )
    if test in {"dele", "delf", "goethe", "testdaf", "tcf", "cambridge", "linguaskill", "gept"}:
        passed = language_score >= 1.0
        return (
            "pass" if passed else "fail",
            f"{language_test.upper()} {language_score:g} {'符合' if passed else '未達'}國立臺北藝術大學國際事務處外語能力檢定標準（歐洲德語／法語／西語區高等音樂與藝術學院多要求達 CEFR B1–B2 以上，如巴黎高等美院要求法語 B2）。",
        )
    return (
        "needs_confirmation",
        f"已填報 {language_test}（{language_score:g}），請對照國立臺北藝術大學當期《國際姊妹校交換名額一覽表》確認是否符合志願校 CEFR B1/B2 語言門檻。",
    )
