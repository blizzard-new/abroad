from __future__ import annotations

import re

from .university_registry import NCYU, resolve_university

NCYU_OIA_HOME_URL = "https://www.ncyu.edu.tw/oia/"
NCYU_EXCHANGE_INTRO_URL = "https://www.ncyu.edu.tw/oia/Contents?nodeId=57877"
NCYU_EXCHANGE_HOW_TO_APPLY_URL = "https://www.ncyu.edu.tw/oia/Contents?nodeId=57878"
NCYU_EXCHANGE_NOTES_URL = "https://www.ncyu.edu.tw/oia/Contents?nodeId=57879"
NCYU_ENGLISH_PROFICIENCY_URL = "https://www.ncyu.edu.tw/oia/Contents?nodeId=57880"
NCYU_EXCHANGE_FAQ_URL = "https://www.ncyu.edu.tw/oia/Contents?nodeId=57881"
NCYU_SCHOLARSHIP_URL = "https://www.ncyu.edu.tw/oia/Contents?nodeId=57882"
NCYU_SISTER_SCHOOLS_URL = "https://www.ncyu.edu.tw/oia/Contents?nodeId=58434"
NCYU_DUAL_DEGREE_URL = "https://www.ncyu.edu.tw/oia/Contents?nodeId=61260"
NCYU_DUAL_DEGREE_RULES_URL = "https://www.ncyu.edu.tw/oia/Contents?nodeId=61258"
NCYU_EXPERIENCES_URL = "https://www.ncyu.edu.tw/oia/Subject?nodeId=57887"
NCYU_GROUP_EXPERIENCES_URL = "https://www.ncyu.edu.tw/oia/Subject?nodeId=58623"
NCYU_WEBHD_EXPERIENCES_URL = (
    "https://webhd.ncyu.edu.tw/share.cgi?ssid=6d344228becc46a0a4192a348b3908e1"
)

NCYU_BRIEFING_114_PDF_URL = (
    "https://www.ncyu.edu.tw/Uploads/Item/806541e0-1d48-411f-a316-07d327e93310.pdf"
)
NCYU_REVIEW_RULES_PDF_URL = (
    "https://www.ncyu.edu.tw/Uploads/Item/22750a8b-5f55-4670-8941-29a6f14a81d6.pdf"
)
NCYU_SCHOLARSHIP_RULES_PDF_URL = (
    "https://www.ncyu.edu.tw/Uploads/Item/101b898c-1f2e-45dc-9333-4a94865f40ab.pdf"
)
NCYU_OVERSEAS_MANUAL_PDF_URL = (
    "https://www.ncyu.edu.tw/Uploads/Item/f46b31fb-80d7-4f88-a768-333071d8a346.pdf"
)
NCYU_OUTGOING_HANDBOOK_PDF_URL = (
    "https://www.ncyu.edu.tw/Uploads/Item/32ab2ba6-0301-43c0-a3bd-696fcbfbd723.pdf"
)
NCYU_APPLICATION_FORM_PDF_URL = (
    "https://www.ncyu.edu.tw/Uploads/Item/03db4fa7-b9e0-445d-88bb-0d9918b55249.pdf"
)
NCYU_PARENTAL_CONSENT_PDF_URL = (
    "https://www.ncyu.edu.tw/Uploads/Item/614be129-5fd2-4cc4-a813-dc1496cf3bc6.pdf"
)

NCYU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 46.0),
    "ielts": ("IELTS", 5.0),
    "toeic": ("TOEIC", 550.0),
    "toefl_itp": ("TOEFL ITP", 460.0),
}


def is_ncyu(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == NCYU.id:
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "國立嘉義大學",
        "嘉義大學",
        "嘉大",
        "ncyu",
        "national chiayi university",
    }


def _is_graduate(degree_level: str | None) -> bool:
    text = (degree_level or "").strip()
    return any(token in text for token in ("碩", "博", "研究"))


def ncyu_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
    degree = (degree_level or "").strip()
    year = (current_year or "").strip()
    if not degree:
        return (
            "needs_confirmation",
            (
                "尚未提供目前學制與年級；依《國立嘉義大學薦外交換學生審查要點》第二點及《薦外交換生手冊》規定：（1）申請人須為學士班二年級以上、碩士班一年級以上、博士班一年級以上之在校生（須於嘉大修習至少滿一學期；轉學生尚未有本校成績者不得申請）；（2）外籍生不得申請交換至原屬國家境內之學校；（3）同一修業年限內限申請一次，交換期間為一學期或一學年；（4）申請人最多可選填 2 志願學校，且進修課程規劃需檢附該系、所務會議同意之會議紀錄。"
            ),
        )
    if any(
        token in degree or token in year
        for token in ("休學", "已畢業", "退學", "學分班", "選修生")
    ):
        return (
            "fail",
            (
                f"已填報 {degree}{f'（{year}）' if year else ''}；依《國立嘉義大學薦外交換學生審查要點》，薦外交換計畫僅限具本校正式學籍且在學滿一學期以上之學生申請，休學、已畢業或退學學生不得申請（選取後於出國交換期間亦須回嘉大註冊並保有學籍，不得辦理休學或畢業）。"
            ),
        )
    if year in {"大一", "大一上", "大一下", "一年級", "學士班一年級"}:
        return (
            "fail",
            (
                f"已填報 {degree}（{year}）；依《國立嘉義大學薦外交換學生審查要點》第二點第（一）款規定，學士班學生須為二年級（含）以上之在校生始得申請薦外交換（可於大一期間先行報考語檢並修讀全英語授課課程，於大二上學期提出申請）。"
            ),
        )
    is_grad = _is_graduate(degree)
    grad_note = (
        "（提醒：碩、博士班研究生學期平均成績須達 80 分［含］以上或全班前 20% 以內，申請表須經指導教授與系所主管核章，並可評估堪薩斯州立大學、楊斯鎮州立大學、斯托克頓大學、亞伯丁大學、尾道市立大學、香川大學、湄州大學、布勞爪哇大學等 8 校 13 個雙聯學位專案）"
        if is_grad
        else "（提醒：大學部學士班二年級以上學生學期平均成績須達 75 分［含］以上或全班前 20% 以內；轉學生須於嘉大修滿至少一學期且具本校成績始得申請）"
    )
    return (
        "pass",
        (
            f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合《國立嘉義大學薦外交換學生審查要點》在學學制與年級規定{grad_note}。"
        ),
    )


def ncyu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
    is_grad = _is_graduate(degree_level)
    score_min = 80.0 if is_grad else 75.0
    gpa_min = 3.3 if is_grad else 3.0
    rank_max = 20.0
    details: list[str] = []
    passes_ncyu = False

    if academic_score is not None:
        details.append(f"學期／歷年平均成績 {academic_score:g} 分")
        if academic_score >= score_min:
            passes_ncyu = True
    if academic_gpa is not None:
        details.append(f"GPA {academic_gpa:g}")
        if academic_gpa >= gpa_min:
            passes_ncyu = True
    if class_rank_percent is not None:
        details.append(f"班級排名百分比前 {class_rank_percent:g}%")
        if class_rank_percent <= rank_max:
            passes_ncyu = True

    summary = "、".join(details)
    if (
        academic_score is None
        and academic_gpa is None
        and class_rank_percent is None
    ):
        return (
            "needs_confirmation",
            (
                "尚未填寫學期平均成績、GPA 或班級排名百分比；依《國立嘉義大學薦外交換學生審查要點》第二點第（二）款規定：在校成績須達全班前 20% 以內，或學期平均成績大學部 75 分（含）以上、研究生 80 分（含）以上，且各科（含操行）成績須達及格標準。審查計分方式：非華語地區為「班級排名百分比 40%＋語言能力 40%＋讀書計畫 20%」；華語地區為「班級排名百分比 80%＋讀書計畫 20%」。"
            ),
        )

    if passes_ncyu:
        top_rank = (
            (class_rank_percent is not None and class_rank_percent <= 20.0)
            or (academic_score is not None and academic_score >= 82.0)
            or (academic_gpa is not None and academic_gpa >= 3.5)
        )
        tier_note = (
            "符合嘉大《薦外交換學生審查要點》學業門檻，且班排／成績落在校內審查高分區間（班排前 10% 得 40% 滿分、11–20% 得 37%），具爭取教育部《學海飛颺／惜珠》與《國立嘉義大學薦外姊妹校交換學生獎補助金》之優勢"
            if top_rank
            else f"符合嘉大《薦外交換學生審查要點》{'研究所 80 分' if is_grad else '大學部 75 分'}（或班排前 20%）學業門檻；建議強化外語檢定級別（占 40%）與讀書計畫（占 20%）以提升甄選總分"
        )
        return (
            "pass",
            f"已填報 {summary}；符合國立嘉義大學薦外交換學生暨雙聯學制甄選學業標準（{tier_note}）。",
        )

    return (
        "fail",
        (
            f"已填報 {summary}；未達《國立嘉義大學薦外交換學生審查要點》第二點規定之「全班前 20% 以內，或學期平均成績{'研究生 80 分' if is_grad else '大學部 75 分'}（含）以上（相當於 GPA {gpa_min:g} 以上）」門檻。"
        ),
    )


def ncyu_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
    test = (language_test or "").strip().lower()
    if partner_country in {"中國大陸"} and (
        not test or language_score is None
    ):
        return (
            "pass",
            (
                "申請赴華語地區（中國大陸姊妹校，如西北農林科技大學、東北林業大學、南京林業大學、福建農林大學、華中農業大學、鄭州大學、山東農業大學等）交換，依《國立嘉義大學薦外交換學生審查要點》第五點第（二）款規定免附語言測驗成績（審查配分為：班級排名百分比 80%＋讀書計畫 20%）。"
            ),
        )
    if not test or language_score is None:
        return (
            "needs_confirmation",
            (
                "尚未填寫外語能力檢定成績。依《國立嘉義大學薦外交換學生審查要點》第五點及國際事務處《英語能力檢定測驗門檻對照表》規定（華語地區免附）：（1）校內審查語言能力配分（40%）：A級（40%）為 TOEFL iBT 79–93 / IELTS 6.5 / JLPT N1；B級（36%）為 TOEFL iBT 60–78 / IELTS 6.0 / JLPT N2；C級（32%）為 TOEFL iBT 46–59 / IELTS 5.5 / JLPT N3；D級（24%）為 TOEFL iBT 35–45 / IELTS 5.0 / JLPT N4；（2）歐美英語授課姊妹校常用門檻：CEFR B1（TOEFL iBT 57 / ITP 460 / IELTS 5.0 / TOEIC 550 / GEPT 中級初試）至 CEFR B2（TOEFL iBT 72 / IELTS 6.0 / TOEIC 785）；（3）日本姊妹校：依各校規定須達 JLPT N2 或 N3（如明治大學、東北大學、廣島大學、岡山大學、尾道市立大學、兵庫教育大學、長岡技術科學大學、長崎大學等）。"
            ),
        )
    if test in NCYU_ENGLISH_MINIMUMS:
        label, minimum = NCYU_ENGLISH_MINIMUMS[test]
        passed = language_score >= minimum
        tier_note = "達國立嘉義大學薦外交換學生審查要點英語 C–D 級及 CEFR B1（TOEFL iBT 46–57 / ITP 460 / IELTS 5.0 / TOEIC 550）基本申請門檻"
        if (
            (test == "toefl" and language_score >= 79)
            or (test == "ielts" and language_score >= 6.5)
            or (test == "toeic" and language_score >= 850)
            or (test == "toefl_itp" and language_score >= 550)
        ):
            tier_note = "達《國立嘉義大學薦外交換學生審查要點》語言能力最高 A 級滿分（40%）及 CEFR B2+ 標準，可申請美英德法西全數英語授課姊妹校、雙聯學位（堪薩斯州立大學、亞伯丁大學、斯托克頓大學、楊斯鎮州立大學）並競爭教育部《學海飛颺／惜珠》與嘉大交換獎補助金"
        elif (
            (test == "toefl" and language_score >= 60)
            or (test == "ielts" and language_score >= 6.0)
            or (test == "toeic" and language_score >= 785)
            or (test == "toefl_itp" and language_score >= 500)
        ):
            tier_note = "達《國立嘉義大學薦外交換學生審查要點》語言能力 B 級（36%）與 CEFR B2 標準，符合歐美及亞太絕大多數英語授課姊妹校與教育部《學海飛颺／惜珠》獎學金申請門檻"
        return (
            "pass" if passed else "fail",
            (
                f"{label} {language_score:g} {'符合' if passed else '未達'}國立嘉義大學國際事務處薦外交換英語能力標準（校內建議門檻：{label} {minimum:g}；{tier_note}）。"
            ),
        )
    if test == "jlpt":
        level = int(language_score)
        passed = 1 <= level <= 3
        if level == 1:
            tier_note = "達《國立嘉義大學薦外交換學生審查要點》語言能力最高 A 級滿分（40%），符合日本全部 39 所姊妹校（含明治大學、東北大學、廣島大學、岡山大學、神戶大學、北海道大學、九州大學、尾道市立大學、香川大學、中京大學、酪農學園大學等）最高日語門檻"
        elif level == 2:
            tier_note = "達《國立嘉義大學薦外交換學生審查要點》語言能力 B 級（36%）及教育部學海飛颺／惜珠標準，符合明治大學、東北大學、廣島大學、岡山大學、兵庫教育大學、長岡技術科學大學、尾道市立大學、香川大學、長崎大學等絕大多數日本姊妹校 N2 門檻"
        elif level == 3:
            tier_note = "達《國立嘉義大學薦外交換學生審查要點》語言能力 C 級（32%），符合要求 JLPT N3 之日本姊妹校（如尾道市立大學、長崎大學、北見工業大學、攝南大學、南九州大學等；部分頂尖國立大學或教育部學海獎學金建議提升至 N2）"
        else:
            tier_note = "雖校內審查要點列有 D 級（N4 得 24%），惟日本各姊妹校交換入學實務門檻多要求 JLPT N3 或 N2 以上合格"
        return (
            "pass" if passed else "fail",
            f"JLPT N{level} {'符合' if passed else '未達'}國立嘉義大學日本姊妹校日語能力標準（{tier_note}）。",
        )
    if test == "topik":
        level = int(language_score)
        passed = 3 <= level <= 6
        if level >= 4:
            tier_note = "符合嘉大韓國姊妹校（江原大學、韓京國立大學、大邱大學、東亞大學、慶北大學、忠북大學、首爾市立大學等）韓語授課門檻及教育部學海獎學金標準"
        elif level == 3:
            tier_note = "符合嘉大韓國姊妹校基礎韓語授課申請標準（若欲申請教育部學海獎學金建議達 TOPIK 4 級以上）"
        else:
            tier_note = "申請韓國姊妹校韓語授課課程建議具備 TOPIK 3 級以上或改以英語檢定（CEFR B1–B2）申請全英語授課課程"
        return (
            "pass" if passed else "fail",
            f"TOPIK {level} 級{'符合' if passed else '未達'}國立嘉義大學韓國姊妹校韓語能力標準（{tier_note}）。",
        )
    if test in {"dele", "delf", "goethe", "testdaf", "tcf", "vinatest", "ivpt"}:
        passed = language_score >= 1.0
        return (
            "pass" if passed else "fail",
            f"{language_test.upper()} {language_score:g} {'符合' if passed else '未達'}國立嘉義大學國際事務處歐洲及東南亞姊妹校第二外語（法／德／西語 CEFR B1 以上）語文能力證明標準。",
        )
    return (
        "needs_confirmation",
        f"已填報語言檢定 {language_test}（{language_score:g}）；請對照《國立嘉義大學薦外交換學生審查要點》、《英語能力檢定測驗門檻對照表》與各姊妹校最新簡章確認。",
    )
