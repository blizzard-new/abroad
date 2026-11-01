from __future__ import annotations

import re

from .university_registry import NTCU, resolve_university

NTCU_OIA_HOME_URL = "https://oia.ntcu.edu.tw/"
NTCU_OIA_ABOUT_URL = "https://oia.ntcu.edu.tw/target/gdZnM02QyXfg"
NTCU_SISTER_OVERVIEW_URL = "https://oia.ntcu.edu.tw/data/1?cate=1"
NTCU_SISTER_SCHOOLS_URL = "https://oia.ntcu.edu.tw/data/1?cate=8"
NTCU_EXCHANGE_SCHOOLS_URL = "https://oia.ntcu.edu.tw/data/1?cate=2"
NTCU_ERASMUS_SCHOOLS_URL = "https://oia.ntcu.edu.tw/data/1?cate=85"
NTCU_DUAL_DEGREE_SCHOOLS_URL = "https://oia.ntcu.edu.tw/data/1?cate=86"
NTCU_OUTBOUND_EXCHANGE_URL = "https://oia.ntcu.edu.tw/data/3"
NTCU_EXPERIENCE_OVERVIEW_URL = "https://oia.ntcu.edu.tw/data/4"
NTCU_EXCHANGE_EXPERIENCE_URL = "https://oia.ntcu.edu.tw/data/15"
NTCU_XUEHAI_OVERVIEW_URL = "https://oia.ntcu.edu.tw/data/14"
NTCU_REGULATIONS_URL = "https://oia.ntcu.edu.tw/data/16"
NTCU_MAINLAND_ZONE_URL = "https://oia.ntcu.edu.tw/data/23"
NTCU_116_POST_URL = "https://oia.ntcu.edu.tw/news/dgb3GtmdKwVY"
NTCU_115_3_POST_URL = "https://oia.ntcu.edu.tw/news/MCYs01HS6XTq"
NTCU_SELECTION_GUIDELINES_PDF_URL = "https://oia.ntcu.edu.tw/storage/media/XbozX1KfqmtPyvx1Q0pX9lMVv0XVKKSyGG1ZwGPH.pdf"
NTCU_SUBSIDY_GUIDELINES_PDF_URL = "https://secretary.ntcu.edu.tw/storage/media/xaVxZfSPSETIlJzUV2Y00F37feImu0ZeLaGtZvt3.pdf"
NTCU_DUAL_DEGREE_PDF_URL = "https://secretary.ntcu.edu.tw/storage/media/RZZFpDH6CXp3fR0ar2icQwzHpiScDWFeSLINapu2.pdf"

NTCU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 57.0),
    "ielts": ("IELTS", 5.0),
    "toeic": ("TOEIC", 550.0),
    "toefl_itp": ("TOEFL ITP", 500.0),
}


def is_ntcu(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == NTCU.id:
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "國立臺中教育大學",
        "國立台中教育大學",
        "臺中教育大學",
        "台中教育大學",
        "中教大",
        "臺中教大",
        "台中教大",
        "中師",
        "臺中師院",
        "ntcu",
        "national taichung university of education",
    }


def _is_graduate(degree_level: str | None) -> bool:
    text = (degree_level or "").strip()
    return any(token in text for token in ("碩", "博", "研究"))


def ntcu_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
    degree = (degree_level or "").strip()
    year = (current_year or "").strip()
    if not degree:
        return (
            "needs_confirmation",
            (
                "尚未提供目前學制與年級；依《國立臺中教育大學交換學生甄選作業要點》及當期《赴國外姐妹校交換學習甄選簡章》規定："
                "（1）申請人須為本校大學部修業滿一年以上（大二以上）或碩、博士班在學學生；"
                "（2）不含在職專班及休學生；（3）應屆畢業生須經系所主管同意並符合本校延畢相關規定；"
                "（4）陸生、僑生、外籍生不得申請交換至原居住國，領取臺灣獎學金者不具申請資格。"
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
                f"已填報 {degree}{f'（{year}）' if year else ''}；依《國立臺中教育大學交換學生甄選作業要點》及當期《赴國外姐妹校交換學習甄選簡章》規定，"
                "申請人須為本校大學部修業滿一年以上（大二以上）或碩、博士班正式在學學生（大一新生、在職專班生、休學生、已畢業生及非正式學籍生不得申請）。"
            ),
        )
    is_grad = _is_graduate(degree)
    grad_note = (
        "（提醒：碩博士班研究生外語門檻依《交換學生甄選作業要點》原則上為 TOEFL iBT 87［ITP 550］或 IELTS 6.0 以上；教育學系碩士班研究生另可評估加拿大湯普森河大學 Thompson Rivers University 教育雙聯碩士學位學制）"
        if is_grad
        else (
            "（提醒：大學部學生須修業滿一年以上［大二以上］，英語門檻原則上為 TOEFL iBT 61［ITP 500］／IELTS 5.5／TOEIC 550–785 以上；國際企業學系、英語學系及音樂學系學生另可評估美國印第安納波利斯大學 University of Indianapolis、日本相愛大學 Soai University 雙聯學位學制）"
        )
    )
    return (
        "pass",
        (
            f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合《國立臺中教育大學交換學生甄選作業要點》與交換學生甄選簡章在學學制規定{grad_note}。"
        ),
    )


def ntcu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
    score_min = 70.0
    gpa_min = 2.5
    rank_max = 50.0
    details: list[str] = []
    passes_ntcu = False

    if academic_score is not None:
        details.append(f"學業平均成績 {academic_score:g} 分")
        if academic_score >= score_min:
            passes_ntcu = True
    if academic_gpa is not None:
        details.append(f"GPA {academic_gpa:g}")
        if academic_gpa >= gpa_min:
            passes_ntcu = True
    if class_rank_percent is not None:
        details.append(f"班級排名百分比前 {class_rank_percent:g}%")
        if class_rank_percent <= rank_max:
            passes_ntcu = True

    summary = "、".join(details)
    if (
        academic_score is None
        and academic_gpa is None
        and class_rank_percent is None
    ):
        return (
            "needs_confirmation",
            (
                "尚未填寫學業平均成績、GPA 或班級排名百分比；依《國立臺中教育大學交換學生甄選作業要點》及《國立臺中教育大學獎勵學生赴國外修習課程實施要點》規定："
                "（1）交換甄選書面審核配分為：外語檢定成績 50%、學業成績 35%、參與活動／競賽優秀表現或其他特殊事蹟 10%、師長推薦信 5%；"
                "（2）若同時申請校內優秀學生赴國外修習課程獎助，大學部前一學期學業總成績須達全班前 20%（前五分之一）且操行成績 80 分以上無懲戒紀錄，碩博士班學業平均成績須達 80 分以上；"
                "（3）若同步申請教育部學海飛颺獎學金，建議歷年班級或系所排名前 30%–40%。"
            ),
        )

    if not passes_ntcu:
        return (
            "fail",
            (
                f"已填報 {summary}；未達國立臺中教育大學及海外姊妹校交換／雙聯學位建議學業基準"
                f"（學業平均 {score_min:g} 分以上、GPA {gpa_min:g} 以上或班級排名前 {rank_max:g}%，且操行成績須達 80 分以上無懲戒紀錄）。"
            ),
        )

    is_top_tier = (
        (class_rank_percent is not None and class_rank_percent <= 20.0)
        or (academic_score is not None and academic_score >= 80.0)
        or (academic_gpa is not None and academic_gpa >= 3.4)
    )
    is_xuehai_tier = (
        (class_rank_percent is not None and class_rank_percent <= 40.0)
        or (academic_score is not None and academic_score >= 75.0)
        or (academic_gpa is not None and academic_gpa >= 3.0)
    )

    if is_top_tier:
        tier_note = (
            "同時符合《國立臺中教育大學獎勵學生赴國外修習課程實施要點》優秀學生獎助門檻（大學部全班前 20% 且操行 80 分以上／研究所學業平均 80 分以上）及教育部《學海飛颺》優先推薦基準，"
            "於校內書審（學業成績占 35%）及歐美日韓雙聯與 Erasmus+ 獎助名額分發具高度競爭優勢"
        )
    elif is_xuehai_tier:
        tier_note = (
            "符合中教大交換生甄選（學業成績占總分 35%）與教育部《學海飛颺／學海惜珠》推薦基準，"
            "並達多數美國、加拿大、歐洲、日本及韓國姊妹校 GPA 3.0（或 75 分）門檻"
        )
    else:
        tier_note = (
            "符合中教大交換生甄選基本學業基準（學業成績占書審總分 35%）；建議強化外語檢定成績（占書審 50%）與活動／競賽優秀事蹟（占 10%）以提升分發排序"
        )

    return (
        "pass",
        f"已填報 {summary}；符合國立臺中教育大學出國交換學生暨雙聯學制學業審核基準（{tier_note}）。",
    )


def ntcu_language_check(
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
                "申請赴中國大陸及港澳地區締約姊妹校（如東北師範大學、華中師範大學、首都師範大學、吉林大學、華中科技大學、鄭州大學、廣州大學、集美大學、香港教育大學等）交換研修，"
                "依簡章規定大陸地區免附外語能力檢定證明（若申請香港教育大學全英語授課課程，建議另備 TOEFL iBT 61／IELTS 5.5／TOEIC 550 以上證明）。"
            ),
        )
    if not test or language_score is None:
        return (
            "needs_confirmation",
            (
                "尚未填寫有效之語言能力檢定成績。依《國立臺中教育大學交換學生甄選作業要點》（外語檢定成績占書審總分 50%）及當期《赴國外姐妹校交換學習甄選簡章》規定："
                "（1）英語系及歐美地區：大學部基本門檻為 TOEFL iBT 61（ITP 500）或 IELTS 5.5（《獎勵學生赴國外修習課程實施要點》為 TOEFL iBT 57 或 IELTS 5.0；簡章亦採認相當 CEFR B1/B2 之 TOEIC 550–785 以上檢定，不含全民英檢 GEPT）；碩博士班為 TOEFL iBT 87（ITP 550）或 IELTS 6.0；"
                "（2）日本地區：日本語能力試驗 JLPT N2（二級）以上（部分日本姊妹校得採認 N3 或英語檢定）；"
                "（3）韓國地區：韓語檢定 TOPIK 3 級（三級）以上或英語檢定；（4）大陸地區免附外語檢定。"
            ),
        )
    if test in NTCU_ENGLISH_MINIMUMS:
        label, minimum = NTCU_ENGLISH_MINIMUMS[test]
        passed = language_score >= minimum
        tier_note = (
            "達《國立臺中教育大學獎勵學生赴國外修習課程實施要點》及交換簡章英語基本基準（TOEFL iBT 57–61 / TOEFL ITP 500 / IELTS 5.0–5.5 / TOEIC 550）"
        )
        if (
            (test == "toefl" and language_score >= 87)
            or (test == "ielts" and language_score >= 6.0)
            or (test == "toeic" and language_score >= 785)
            or (test == "toefl_itp" and language_score >= 550)
        ):
            tier_note = (
                "達《國立臺中教育大學交換學生甄選作業要點》碩博士班高階英語標準（TOEFL iBT 87 / ITP 550 / IELTS 6.0 / TOEIC 785+），"
                "全面符合美國印第安納波利斯大學（UIndy 雙聯／交換）、斯托克頓大學、加州州立理工大學波莫納分校（Cal Poly Pomona）、舊金山州立大學、北科羅拉多大學、"
                "加拿大湯普森河大學（TRU 雙聯／交換）、里賈納大學，以及西班牙巴利亞多利德大學、奧地利福拉爾貝格教育大學／林茲教區私立教育大學等歐美亞全數姊妹校門檻"
            )
        elif (
            (test == "toefl" and language_score >= 61)
            or (test == "ielts" and language_score >= 5.5)
            or (test == "toeic" and language_score >= 650)
            or (test == "toefl_itp" and language_score >= 500)
        ):
            tier_note = (
                "達《國立臺中教育大學交換學生甄選作業要點》大學部正式英語門檻（TOEFL iBT 61 / ITP 500 / IELTS 5.5），"
                "符合美國、加拿大、歐洲（奧地利、德國、捷克、西班牙、法國、比利時、羅馬尼亞、土耳其）及亞洲英語授課姊妹校申請基準"
            )
        return (
            "pass" if passed else "fail",
            (
                f"{label} {language_score:g} {'符合' if passed else '未達'}國立臺中教育大學國際事務處赴外交換暨雙聯學制英語能力標準"
                f"（校內最低基準：{label} {minimum:g}，且外語檢定成績占甄選書審總分 50%；{tier_note}）。"
            ),
        )
    if test == "jlpt":
        level = int(language_score)
        passed = 1 <= level <= 3
        if level in (1, 2):
            tier_note = (
                f"達 JLPT N{level} 標準，完全符合《國立臺中教育大學交換學生甄選作業要點》日本地區姊妹校「日本語能力測驗 N2（二級）以上」正式門檻"
                "（適用東京學藝大學、大阪教育大學、兵庫教育大學、京都產業大學、關西國際大學、德島文理大學、相愛大學雙聯／交換、武藏野大學、茨城大學、工學院大學、山梨英和大學等全數日本姊妹校）"
            )
        elif level == 3:
            tier_note = (
                "達 JLPT N3（CEFR B1 相當）標準，可申請部分採認 N3 或搭配英語檢定之日本姊妹校（惟《交換學生甄選作業要點》原則規定日本地區為 N2 以上，東京學藝大學與大阪教育大學日語教育學程建議具備 N2）"
            )
        else:
            tier_note = f"JLPT N{level} 未達國立臺中教育大學日本地區姊妹校日語能力門檻（須達 JLPT N2 或部分學校 N3 以上）"
        return (
            "pass" if passed else "fail",
            f"JLPT N{level} {'符合' if passed else '未達'}國立臺中教育大學日本姊妹校交換學生日語能力標準（{tier_note}）。",
        )
    if test == "topik":
        level = int(language_score)
        passed = 2 <= level <= 6
        if level >= 3:
            tier_note = (
                f"TOPIK {level} 級完全符合《國立臺中教育大學交換學生甄選作業要點》韓國地區姊妹校「TOPIK 3 級（三級）以上」正式門檻"
                "（適用國立首爾教育大學、國立大邱教育大學、國立京仁教育大學、國立忠南大學、國立釜慶大學、明知大學、建國大學、釜山外國語大學等全數韓國姊妹校）"
            )
        elif level == 2:
            tier_note = "TOPIK 2 級符合韓國姊妹校基礎韓語研修或英語授課組別基準（惟《交換學生甄選作業要點》原則規定韓語組須達 TOPIK 3 級以上，或同時檢附英語檢定證明）"
        else:
            tier_note = "韓國姊妹校要求 TOPIK 3 級（部分學校 2 級）以上，或改以英語檢定成績申請英語授課課程"
        return (
            "pass" if passed else "fail",
            f"TOPIK {level} 級{'符合' if passed else '未達'}國立臺中教育大學韓國姊妹校韓語能力標準（{tier_note}）。",
        )
    if test in {"duolingo"}:
        passed = language_score >= 80.0
        return (
            "pass" if passed else "fail",
            f"Duolingo English Test {language_score:g} {'符合' if passed else '未達'}美國與歐洲部分姊妹校英語替代檢定基準（建議達 85–100 分以上，並請確認志願校是否採認 Duolingo）。",
        )
    if test in {"dele", "delf", "goethe", "testdaf", "tcf", "cambridge", "linguaskill"}:
        passed = language_score >= 1.0
        return (
            "pass" if passed else "fail",
            f"{language_test.upper()} {language_score:g} {'符合' if passed else '未達'}國立臺中教育大學國際事務處外語能力檢定標準（須達 CEFR B1/B2 以上並符合志願姊妹校規定；注意校內簡章不採認全民英檢 GEPT）。",
        )
    return (
        "needs_confirmation",
        f"已填報語言檢定 {language_test}（{language_score:g}）；請對照《國立臺中教育大學交換學生甄選作業要點》與《116學年度赴國外姐妹校交換學習甄選簡章》確認（注意：校內甄選簡章明訂不採認全民英檢 GEPT）。",
    )
