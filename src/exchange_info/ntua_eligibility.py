from __future__ import annotations

import re

from .university_registry import NTUA, resolve_university

NTUA_OIA_HOME_URL = "https://international.ntua.edu.tw/"
NTUA_OIA_ABOUT_URL = "https://international.ntua.edu.tw/#/Post/22/13"
NTUA_OIA_STAFF_URL = "https://international.ntua.edu.tw/#/Post/23/14"
NTUA_OIA_CONTACT_URL = "https://international.ntua.edu.tw/#/Post/56/16"
NTUA_REGULATIONS_URL = "https://international.ntua.edu.tw/#/Post/59/15"
NTUA_SISTER_SCHOOLS_URL = "https://international.ntua.edu.tw/#/SisterSchools"
NTUA_EXCHANGE_SCHOOLS_URL = "https://international.ntua.edu.tw/#/ExchangeSchool"
NTUA_EXCHANGE_INTRO_URL = "https://international.ntua.edu.tw/#/Post/298/45"
NTUA_PREDEPARTURE_URL = "https://international.ntua.edu.tw/#/Post/432/48"
NTUA_VISITING_STUDENT_URL = "https://international.ntua.edu.tw/#/Post/189/39"
NTUA_OVERSEAS_INTERNSHIP_URL = "https://international.ntua.edu.tw/#/Post/191/42"
NTUA_116_1_POST_URL = "https://international.ntua.edu.tw/#/Post/1079/46"
NTUA_115_2_RESULTS_URL = "https://international.ntua.edu.tw/#/Post/1077/46"
NTUA_115_XUEHAI_POST_URL = "https://international.ntua.edu.tw/#/Post/1034/107"
NTUA_EXPERIENCE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1XVenaXbrPn6TkeK3IiL06elCLt9tf3z_9tQ481CKjW8"
NTUA_116_1_BROCHURE_PDF_URL = "https://international.ntua.edu.tw/Upload/FileManager/da72286d-2290-443b-a81e-c8680504ce26.pdf"
NTUA_116_1_BRIEFING_PDF_URL = "https://international.ntua.edu.tw/Upload/FileManager/a943aff6-c104-4f24-8c37-1b22f8217d17.pdf"
NTUA_SELECTION_GUIDELINES_PDF_URL = "https://international.ntua.edu.tw/Upload/FileManager/c91fce80-dcc4-4f3a-aa84-a71295110ce5.pdf"
NTUA_XUEHAI_GUIDELINES_PDF_URL = "https://international.ntua.edu.tw/Upload/FileManager/ddeb84c3-6055-4218-9d73-18e71e98c821.pdf"

NTUA_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 60.0),
    "ielts": ("IELTS", 5.5),
    "toeic": ("TOEIC", 550.0),
    "toefl_itp": ("TOEFL ITP", 500.0),
}


def is_ntua(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == NTUA.id:
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "國立臺灣藝術大學",
        "國立台灣藝術大學",
        "臺灣藝術大學",
        "台灣藝術大學",
        "臺藝大",
        "台藝大",
        "臺藝",
        "台藝",
        "國立藝專",
        "臺灣藝術專科學校",
        "ntua",
        "national taiwan university of arts",
    }


def _is_graduate(degree_level: str | None) -> bool:
    text = (degree_level or "").strip()
    return any(token in text for token in ("碩", "博", "研究"))


def ntua_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
    degree = (degree_level or "").strip()
    year = (current_year or "").strip()
    if not degree:
        return (
            "needs_confirmation",
            (
                "尚未提供目前學制與年級；依《國立臺灣藝術大學交換學生甄選要點》及《116 學年度第 1 學期交換學生計畫甄選簡章》規定："
                "（1）申請時已在本校就讀滿 1 學期（含）以上之本校在學學生（畢業於本校之在學碩、博士生亦須就讀滿 1 學期以上，不含在職專班）；"
                "（2）申請與出國研修期間須為本校在學生（不得辦理休、退學或畢業），同一學制僅得出國交換一次（學士班、碩士班及博士班期間皆可分別參加一次）；"
                "（3）大四、碩二、博三（含）以上應屆畢業生須填寫《應屆畢業生切結書》。"
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
            "碩一上",
            "博一上",
            "專一",
            "專二",
            "專三",
        )
    ):
        return (
            "fail",
            (
                f"已填報 {degree}{f'（{year}）' if year else ''}；依《國立臺灣藝術大學交換學生甄選要點》及當期甄選簡章規定，"
                "申請人須為已於本校就讀滿 1 學期（含）以上之正式在學學生（不含在職專班；大一上學期新生、在職專班生、休學生、已畢業生及非正式學籍生不得申請）。"
            ),
        )
    is_grad = _is_graduate(degree)
    grad_note = (
        "（提醒：碩、博士班研究生須於臺藝大就讀滿 1 學期以上，中文成績單免顯示排名，履歷可附論文發表清單並撰寫研究計畫；碩二、博三以上須檢附《應屆畢業生切結書》）"
        if is_grad
        else (
            "（提醒：學士班學生須於臺藝大就讀滿 1 學期以上，歷年中文成績單必須顯示班／系排名［未顯示排名者視同資料不齊不予受理］；大四或延修生須檢附《應屆畢業生切結書》）"
        )
    )
    return (
        "pass",
        (
            f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合《國立臺灣藝術大學交換學生甄選要點》與交換學生計畫甄選簡章在學學制規定{grad_note}。"
        ),
    )


def ntua_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
    score_min = 80.0
    gpa_min = 3.0
    rank_max = 70.0
    details: list[str] = []
    passes_ntua = False

    if academic_score is not None:
        details.append(f"歷年學業平均成績 {academic_score:g} 分")
        if academic_score >= score_min:
            passes_ntua = True
    if academic_gpa is not None:
        details.append(f"GPA {academic_gpa:g}")
        if academic_gpa >= gpa_min:
            passes_ntua = True
    if class_rank_percent is not None:
        details.append(f"班（系）排名前 {class_rank_percent:g}%")
        if class_rank_percent <= rank_max:
            passes_ntua = True

    summary = "、".join(details)
    if (
        academic_score is None
        and academic_gpa is None
        and class_rank_percent is None
    ):
        return (
            "needs_confirmation",
            (
                "尚未填寫歷年學業平均成績、GPA 或班（系）排名百分比；依《國立臺灣藝術大學交換學生甄選要點》及《116 學年度第 1 學期交換學生計畫甄選簡章》規定："
                "（1）歷年學業成績（各學期加總）平均須達 80 分以上或班（系）排名前 70%，操行成績 85 分以上且無懲處紀錄；"
                "（2）校內審查標準：需語言檢定之學校為「在校成績 45%＋語言能力 25%＋研修計畫 20%＋其他（得獎、論文、實習等）10%」；不需語言檢定之學校為「在校成績 55%＋研修計畫 25%＋其他 20%」；"
                "（3）若同步申請教育部《學海飛颺》或《學海惜珠》獎學金，歷年學業總平均須達 80 分以上，且大學部申請學海飛颺以系排名前 30%（或班排前 20%）為原則、學海惜珠以系排名前 40%（或班排前 30%）為原則。"
            ),
        )

    if not passes_ntua:
        return (
            "fail",
            (
                f"已填報 {summary}；未達國立臺灣藝術大學交換學生計畫甄選簡章規定門檻"
                f"（歷年學業平均成績 {score_min:g} 分以上或班／系排名前 {rank_max:g}%，或 GPA {gpa_min:g} 以上，且操行成績須達 85 分以上無懲處紀錄）。"
            ),
        )

    is_feiyang_tier = (
        (academic_score is not None and academic_score >= 80.0)
        and (class_rank_percent is None or class_rank_percent <= 30.0)
    ) or (class_rank_percent is not None and class_rank_percent <= 20.0)
    is_xizhu_tier = (
        (academic_score is not None and academic_score >= 80.0)
        and (class_rank_percent is None or class_rank_percent <= 40.0)
    ) or (class_rank_percent is not None and class_rank_percent <= 30.0)

    if is_feiyang_tier:
        tier_note = (
            "符合臺藝大交換學生甄選門檻及教育部《學海飛颺》（歷年平均 80 分以上且系排前 30%／班排前 20%）與《學海惜珠》獎學金申請標準，"
            "於校內審查（在校成績占 45%–55%）及歐美日韓頂尖藝術姊妹校分發具高度競爭優勢"
        )
    elif is_xizhu_tier:
        tier_note = (
            "符合臺藝大交換學生甄選門檻及教育部《學海惜珠》（歷年平均 80 分以上且系排前 40%／班排前 30%）申請標準"
        )
    else:
        tier_note = (
            "符合臺藝大交換學生甄選簡章門檻（歷年平均 80 分以上或班／系排名前 70%）；建議強化個人作品集、讀書／研究計畫（占 20%–25%）與外語能力證明（占 20%–25%）以提升總分排序"
        )

    return (
        "pass",
        f"已填報 {summary}；符合國立臺灣藝術大學出國交換學生學業審核標準（{tier_note}）。",
    )


def ntua_language_check(
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
                "申請赴中國大陸地區締約姊妹校（清華大學、同濟大學、中央美術學院、中國美術學院、中國傳媒大學、上海戲劇學院、中央民族大學、南京藝術學院、四川美術學院等）交換研修，"
                "依《交換學生計畫甄選簡章》規定免附外語能力檢定證明與英文成績單，惟須備妥符合規範之個人作品集與讀書／研究計畫。"
            ),
        )
    if not test or language_score is None:
        return (
            "needs_confirmation",
            (
                "尚未填寫有效之語言能力檢定成績。依《國立臺灣藝術大學 116 學年度第 1 學期交換學生計畫甄選簡章》及《辦理教育部學海系列計畫補助作業要點》規定："
                "（1）姊妹校設有語檢門檻者（如 TOEFL iBT、IELTS、TOEIC、JLPT N1–N3、TOPIK 2–4 級、DELF B1–B2、DELE B1–B2、TestDaF），申請人必須於遞件時檢附有效語檢證明影本（校內審查占 25%）；"
                "（2）姊妹校無語檢要求者得免附（校內審查不需語檢學校以『在校成績 55%＋研修計畫 25%＋其他含語檢加分 20%』評比）；"
                "（3）若申請教育部《學海飛颺／學海惜珠》且研修學校無設定語言標準者，須達本校學海語言標準（英語依臺藝大英文畢業門檻實施要點、日語 JLPT N3、法語 DELF A2、韓語 TOPIK 3、西語 DELE A2、德語 TestDaF TDN3 以上）。"
            ),
        )
    if test in NTUA_ENGLISH_MINIMUMS:
        label, minimum = NTUA_ENGLISH_MINIMUMS[test]
        passed = language_score >= minimum
        tier_note = (
            "達臺藝大交換甄選與教育部《學海飛颺／學海惜珠》英語基本基準（CEFR B1 相當：TOEFL iBT 60 / TOEFL ITP 500 / IELTS 5.5 / TOEIC 550）"
        )
        if (
            (test == "toefl" and language_score >= 80)
            or (test == "ielts" and language_score >= 6.0)
            or (test == "toeic" and language_score >= 785)
            or (test == "toefl_itp" and language_score >= 550)
        ):
            tier_note = (
                "達高階英語標準（CEFR B2：TOEFL iBT 80+ / IELTS 6.0–6.5 / TOEIC 785+），"
                "符合英國倫敦金士頓大學（Kingston）、瑞丁大學（Reading）、巴斯斯巴大學（Bath Spa）、聖三一拉邦音樂舞蹈學院（Trinity Laban）、"
                "加拿大安大略藝術設計大學（OCAD）、澳洲國立大學（ANU）、美國南猶他大學、捷克布拉格電影電視學院（FAMU）等英語授課院校門檻"
            )
        elif (
            (test == "toefl" and language_score >= 70)
            or (test == "ielts" and language_score >= 5.5)
            or (test == "toeic" and language_score >= 650)
            or (test == "toefl_itp" and language_score >= 520)
        ):
            tier_note = (
                "達多數歐洲（捷克布拉格藝術建築暨設計學院 UMPRUM、荷蘭、波蘭波滋南藝術大學、德國斯圖加特媒體大學、匈牙利美術大學）及亞洲（新加坡南洋藝術學院 NAFA、泰國朱拉隆功大學、韓國藝術綜合大學 K-Arts）姊妹校英語交換門檻"
            )
        return (
            "pass" if passed else "fail",
            (
                f"{label} {language_score:g} {'符合' if passed else '未達'}國立臺灣藝術大學國際事務處出國交換暨教育部學海計畫英語能力標準"
                f"（建議基本基準：{label} {minimum:g}；{tier_note}）。"
            ),
        )
    if test == "jlpt":
        level = int(language_score)
        passed = 1 <= level <= 3
        if level in (1, 2):
            tier_note = (
                f"達 JLPT N{level} 標準，完全符合多摩美術大學、女子美術大學、沖繩縣立藝術大學、神戶藝術工科大學、名古屋造形大學、筑波大學、大東文化大學等全數日本姊妹校日語門檻及教育部學海飛颺日語基準（JLPT N3 以上）"
            )
        elif level == 3:
            tier_note = (
                "達 JLPT N3 標準，符合教育部學海飛颺日語門檻（JLPT N3 以上）及多數日本藝術姊妹校交換基準（部分學校如多摩美術大學建議具備 N2 以上日語能力）"
            )
        else:
            tier_note = f"JLPT N{level} 未達臺藝大教育部學海計畫及日本姊妹校日語能力標準（須達 JLPT N3–N2 以上）"
        return (
            "pass" if passed else "fail",
            f"JLPT N{level} {'符合' if passed else '未達'}國立臺灣藝術大學日本姊妹校交換暨學海計畫日語能力標準（{tier_note}）。",
        )
    if test == "topik":
        level = int(language_score)
        passed = 2 <= level <= 6
        if level >= 3:
            tier_note = (
                f"TOPIK {level} 級完全符合韓國藝術綜合大學（K-Arts）、中央大學、漢陽大學、建國大學、檀國大學、首爾國立科技大學、慶北大學、啟明大學、明知大學等韓國姊妹校及教育部學海計畫韓語門檻（TOPIK 3 級以上）"
            )
        elif level == 2:
            tier_note = "TOPIK 2 級符合部分韓國姊妹校基礎韓語門檻（惟申請教育部學海飛颺／學海惜珠韓語組須達 TOPIK 3 級以上，或改檢附英語檢定成績）"
        else:
            tier_note = "韓國姊妹校及教育部學海計畫要求 TOPIK 2–3 級以上，或改以英語檢定成績申請英語授課課程"
        return (
            "pass" if passed else "fail",
            f"TOPIK {level} 級{'符合' if passed else '未達'}國立臺灣藝術大學韓國姊妹校韓語能力標準（{tier_note}）。",
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
            f"{language_test.upper()} {language_score:g} {'符合' if passed else '未達'}國立臺灣藝術大學國際事務處外語能力檢定標準（學海計畫基準：法語 DELF A2、西語 DELE A2、德語 TestDaF TDN3 以上；歐洲藝術院校多要求 CEFR B1–B2）。",
        )
    return (
        "needs_confirmation",
        f"已填報 {language_test}（{language_score:g}），請對照國立臺灣藝術大學當期《交換學生計畫學校一覽表》及《CEF 與各項英檢對照表》確認是否符合志願校語言門檻。",
    )
