"""National University of Tainan (國立臺南大學, NUTN) outbound exchange & dual-degree eligibility checks.

Official rule sources:
- 國立臺南大學選送學生出國研修辦法（109年3月18日108學年度第2學期第1次教務會議修正通過）:
  https://www.nutn.edu.tw/var/file/0/1000/img/2200/372060088.pdf
- 國立臺南大學與國外大學校院辦理跨國雙學位制實施辦法（107年11月28日教務會議通過、教育部臺教高(二)字第1070221647號函備查）:
  https://www.nutn.edu.tw/var/file/0/1000/img/2200/748482610.pdf
- 國立臺南大學鼓勵學生赴外國或大陸地區姊妹校交換研習獎助要點:
  https://oia.nutn.edu.tw/upload/file/202109221126252a33a1.pdf
- 國立臺南大學 2026 秋季班赴境外姊妹校交換學生甄選簡章（亞洲及大洋洲／歐美地區／大陸地區）:
  https://oia.nutn.edu.tw/upload/file/2026012014402909d5bf.pdf
  https://oia.nutn.edu.tw/upload/file/20260120165522dc0c84.pdf
  https://oia.nutn.edu.tw/upload/file/20260120165750317972.pdf
"""

from __future__ import annotations

import re

from .university_registry import NUTN, resolve_university

NUTN_OIA_HOME_URL = "https://oia.nutn.edu.tw/"
NUTN_OVERSEAS_REGULATION_URL = "https://www.nutn.edu.tw/var/file/0/1000/img/2200/372060088.pdf"
NUTN_DUAL_DEGREE_REGULATION_URL = "https://www.nutn.edu.tw/var/file/0/1000/img/2200/748482610.pdf"
NUTN_SCHOLARSHIP_GUIDELINE_URL = "https://oia.nutn.edu.tw/upload/file/202109221126252a33a1.pdf"
NUTN_ASIA_OCEANIA_BROCHURE_URL = "https://oia.nutn.edu.tw/upload/file/2026012014402909d5bf.pdf"
NUTN_EUROPE_AMERICA_BROCHURE_URL = "https://oia.nutn.edu.tw/upload/file/20260120165522dc0c84.pdf"
NUTN_MAINLAND_BROCHURE_URL = "https://oia.nutn.edu.tw/upload/file/20260120165750317972.pdf"
NUTN_PARTNER_LIST_URL = "https://oia.nutn.edu.tw/index.php?option=module&lang=cht&task=pageinfo&id=576&index=2"

NUTN_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 45.0),
    "ielts": ("IELTS", 5.5),
    "toefl_itp": ("TOEFL ITP/PBT", 500.0),
    "toeic": ("TOEIC", 550.0),
    "duolingo": ("Duolingo English Test", 90.0),
}


def is_nutn(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == NUTN.id:
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "nutn",
        "國立臺南大學",
        "國立台南大學",
        "臺南大學",
        "台南大學",
        "南大",
        "national university of tainan",
    }


def _is_graduate(degree_level: str | None) -> bool:
    text = (degree_level or "").strip()
    return any(token in text for token in ("碩", "博", "研究", "master", "phd", "doctoral"))


def nutn_degree_check(
    degree_level: str | None, current_year: str | int | None = None
) -> tuple[str, str]:
    degree = (degree_level or "").strip()
    year = str(current_year or "").strip()
    if not degree:
        return (
            "needs_confirmation",
            (
                "尚未提供目前學制與年級；依《國立臺南大學選送學生出國研修辦法》第 4 條及 2026 秋季班赴境外姊妹校交換學生甄選簡章：申請對象為國立臺南大學具正式學籍之在學學生，且出國交換前須於本校就讀滿一學年以上（申請時為大一或碩博一在學者，須待修滿一學年即大二或碩博二以上始得出國交換；休學學生、在職專班生或出國期間已畢業／喪失本校在學學籍者不得出國交換）。"
            ),
        )
    if any(
        token in degree or token in year
        for token in ("在職專班", "碩專", "emba", "EMBA", "學分班", "選修生", "休學")
    ):
        return (
            "fail",
            (
                f"已填報 {degree}{f'（{year}）' if year else ''}；依《國立臺南大學選送學生出國研修辦法》與出國交換學生甄選簡章規定，在職專班、休學或不具正式一般生學籍者不在校級交換與教育部學海系列獎助學金申請範圍內。"
            ),
        )
    is_grad = _is_graduate(degree)
    if not is_grad and year in {"4", "大四", "大四下", "四年級下學期", "應屆畢業"}:
        return (
            "needs_confirmation",
            (
                f"已填報 {degree}（{year}）；依國立臺南大學出國交換簡章規定，出國交換期間須全程保有本校正式在學學籍（不得於出國期間畢業或休學），大四學生如擬申請出國交換須確認辦理延長修業年限並經系所及國際事務處核可。"
            ),
        )
    grad_note = (
        "（提醒：碩博士班學生出國交換前須於南大修業滿一學年以上，並經指導教授及系所主管同意；亦可評估申請捷克赫拉德茨克拉洛韋大學理學院博士雙聯學位等計畫）"
        if is_grad
        else "（提醒：學士班學生出國交換時須為大二以上在學學生，大一學生於大一下學期申請者須於大二上學期始得出國；修讀美國北德州大學 3+2 學碩雙聯或韓國蔚山大學 2+2 雙學士雙聯學位者，於兩校修業時間合計須滿 32 個月以上）"
    )
    return (
        "pass",
        f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合國立臺南大學出國交換學生甄選與跨國雙學位制之在學學籍規定{grad_note}。",
    )


def nutn_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
    score_min = 70.0
    gpa_min = 2.5
    details: list[str] = []
    passes_general = False
    passes_high_tier = False

    if academic_score is not None:
        details.append(f"學業平均 {academic_score:g} 分")
        if academic_score >= score_min:
            passes_general = True
        if academic_score >= 75.0:
            passes_high_tier = True
    if academic_gpa is not None:
        details.append(f"GPA {academic_gpa:g}")
        if academic_gpa >= gpa_min:
            passes_general = True
        if academic_gpa >= 3.0:
            passes_high_tier = True
    if class_rank_percent is not None:
        details.append(f"班排名百分比前 {class_rank_percent:g}%")
        if class_rank_percent <= 30.0:
            passes_general = True
            passes_high_tier = True
        elif class_rank_percent <= 50.0 and academic_score is None and academic_gpa is None:
            passes_general = True

    summary = "、".join(details)
    if (
        academic_score is None
        and academic_gpa is None
        and class_rank_percent is None
    ):
        return (
            "needs_confirmation",
            (
                "尚未填寫歷年學業平均成績、GPA 或班排名百分比；依《國立臺南大學選送學生出國研修辦法》及 2026 秋季班赴境外姊妹校交換學生甄選簡章：（1）校內甄選基本資格：在學期間學業成績總平均達 70 分（GPA 2.5）以上或班排名前 50%，且操行成績平均達 80 分以上（在校期間無記過以上處分）；（2）歐美姊妹校（如美國德州農工大學康莫斯分校、中密西根大學、加州州立大學蒙特利灣分校、西維吉尼亞大學）、日本長崎大學（GPA 3.0）及教育部《學海飛颺／學海惜珠》或《國立臺南大學鼓勵學生赴外國或大陸地區姊妹校交換研習獎助要點》建議歷年平均達 75～80 分（GPA 2.75～3.0 或班排名前 30%）以上；甄選評分依在校成績 30%、外語能力及各類表現 30%、面試表現 40% 擇優錄取。"
            ),
        )

    if passes_general:
        tier_notes: list[str] = []
        if passes_high_tier:
            tier_notes.append(
                "同時達到歐美姊妹校（GPA 2.75～3.0）、日本長崎大學（GPA 3.0）、美國北德州大學 3+2 雙聯學位，以及教育部《學海飛颺／學海惜珠》與《國立臺南大學鼓勵學生赴外國或大陸地區姊妹校交換研習獎助要點》之優良學業門檻（另須操行平均 80 分以上）"
            )
        else:
            tier_notes.append(
                "符合國立臺南大學出國交換甄選基礎學業門檻（歷年平均 70 分 / GPA 2.5 或班排前 50% 以上，另須操行 80 分以上）；惟申請日本長崎大學、部分歐美姊妹校或爭取教育部學海飛颺及校內高額交換獎助金建議達 GPA 2.75～3.0（約 75～80 分）以上"
            )
        return (
            "pass",
            f"已填報 {summary}；符合國立臺南大學出國交換甄選學業標準（{'；'.join(tier_notes)}）。",
        )

    return (
        "fail" if (academic_score is not None and academic_score < 70.0) else "needs_confirmation",
        (
            f"已填報 {summary}；依國立臺南大學出國交換學生甄選簡章及《選送學生出國研修辦法》，申請人歷年學業總平均原則上須達 70 分（GPA 2.5）或班排名前 50% 以上且操行平均達 80 分以上，部分歐美日姊妹校及教育部學海飛颺獎學金要求 GPA 2.75～3.0（75～80 分）以上。"
        ),
    )


def nutn_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
    test = (language_test or "").strip().lower()
    if partner_country in {"中國大陸", "中國", "大陸地區"} and (not test or language_score is None):
        return (
            "pass",
            (
                "申請赴大陸地區姊妹校（廈門大學、南開大學、北京師範大學、華東師範大學、山東大學、蘭州大學、蘇州大學、東北師範大學、陝西師範大學、華中師範大學、西南大學、中央民族大學等）交換以中文授課為主，免附英／日／韓外語能力檢定證明。"
            ),
        )
    if not test or language_score is None:
        return (
            "needs_confirmation",
            (
                "尚未填寫外語能力檢定成績。依國立臺南大學國際事務處 2026 秋季班赴境外姊妹校交換學生甄選簡章與雙聯學位規定：（1）英語授課組：歐美及亞洲英語授課姊妹校要求 CEFR B1～B2 以上，其中波蘭羅茲大學、立陶宛維ytautas Magnus 大學、拉脫維亞大學、羅馬尼亞巴比什博雅依大學要求 CEFR B1～B2（約 TOEIC 550～785 / IELTS 5.5 / TOEFL iBT 61～72）；美國中密西根大學要求 TOEFL iBT 61 / IELTS 5.5（全額學費優惠門檻 iBT 79 / IELTS 6.5）；美國加州州立大學蒙特利灣分校（CSUMB）與西維吉尼亞大學（WVU）要求 TOEFL iBT 61 / IELTS 6.0；美國德州農工大學康莫斯分校（TAMUC）與北德州大學（UNT 3+2 雙聯）要求 TOEFL iBT 79 / IELTS 6.0～6.5；捷克赫拉德茨克拉洛韋大學與帕爾杜比采大學要求 CEFR B2；（2）日語組：日本長崎大學、千葉大學、廣島大學、宮崎大學、滋賀大學、兵庫教育大學、上越教育大學、鳴門教育大學、大阪教育大學、大東文化大學、高崎經濟大學、四國大學、聖泉大學、人間環境大學、梅花女子大學等要求 JLPT N2～N3 以上（專門科目多要求 N2 以上）；（3）韓語／英語組：韓國中央大學、光운大學、德成女子大學、全北大學、國立木浦大學、京仁教育大學、首爾市立大學、順天鄉大學、慶南大學、東亞大學、翰林大學、漢城大學、東國大學 WISE、國立江原大學、白石大學等要求 TOPIK 2～3 級或英語 CEFR B1～B2（TOEIC 550～750 / TOEFL iBT 45～71 / IELTS 5.5）。"
            ),
        )
    if test in NUTN_ENGLISH_MINIMUMS:
        label, minimum = NUTN_ENGLISH_MINIMUMS[test]
        passed = language_score >= minimum
        tier_note = "達韓國國立木浦大學英語組（TOEFL iBT 45）或亞洲／歐洲基礎英語組門檻（TOEIC 550 / IELTS 5.5 / TOEFL ITP 500）"
        if (
            (test == "toefl" and language_score >= 79)
            or (test == "ielts" and language_score >= 6.5)
            or (test == "toeic" and language_score >= 785)
            or (test == "duolingo" and language_score >= 105)
        ):
            tier_note = "達美國德州農工大學康莫斯分校（TAMUC）、中密西根大學（CMU 學費減免門檻）、加州州立大學蒙特利灣分校（CSUMB）、西維吉尼亞大學（WVU）、北德州大學 3+2 雙聯、捷克赫拉德茨克拉洛韋大學／帕爾杜比采大學（CEFR B2）及教育部學海飛颺最高英語門檻"
        elif (
            (test == "toefl" and language_score >= 61)
            or (test == "ielts" and language_score >= 5.5)
            or (test == "toefl_itp" and language_score >= 500)
            or (test == "toeic" and language_score >= 600)
            or (test == "duolingo" and language_score >= 95)
        ):
            tier_note = "符合美國中密西根大學一般自費交換（iBT 61 / IELTS 5.5）、歐洲波蘭羅茲大學／立陶宛 VMU／拉脫維亞大學／羅馬尼亞巴比什博雅依大學（CEFR B1～B2）及韓國中央大學／全北大學／光云大學等英語授課交換門檻（惟美國 TAMUC、北德州大學雙聯及 CMU 學費優惠門檻需 TOEFL iBT 79 / IELTS 6.0～6.5）"
        return (
            "pass" if passed else "fail",
            f"{label} {language_score:g} {'符合' if passed else '未達'}國立臺南大學出國交換與雙聯學位英語檢定基準（最低採計門檻：{label} {minimum:g}；{tier_note}）。",
        )
    if test == "jlpt":
        level = int(language_score)
        passed = 1 <= level <= 4
        if level in {1, 2}:
            tier_note = f"JLPT N{level} 符合日本國立長崎大學、千葉大學、廣島大學、宮崎大學、滋賀大學、兵庫教育大學、上越教育大學、鳴門教育大學、大阪教育大學、大東文化大學、高崎經濟大學等全部日本姊妹校專門課程與交換門檻"
        elif level == 3:
            tier_note = "JLPT N3 符合日本多數姊妹校日語研修與基礎交換門檻（惟長崎大學、千葉大學、廣島大學、大阪教育大學、大東文化大學等本科專業課程多要求 JLPT N2 以上）"
        elif level == 4:
            tier_note = "JLPT N4 僅符合少數日本姊妹校初級日語別科／基礎交換門檻（多數日本國立與私立姊妹校要求 JLPT N3～N2 以上）"
        else:
            tier_note = "國立臺南大學日本交換姊妹校要求 JLPT N3～N2 以上（部分學校初級日語課程接受 N4）"
        return (
            "pass" if passed else "fail",
            f"JLPT N{level} {'符合' if passed else '未達'}國立臺南大學日本姊妹校交換日語檢定基準（{tier_note}）。",
        )
    if test == "topik":
        level = int(language_score)
        passed = level >= 2
        if level >= 3:
            tier_note = f"TOPIK {level} 級符合韓國中央大學、光云大學、德成女子大學、全北大學、國立木浦大學、京仁教育大學、首爾市立大學、順天鄉大學、慶南大學等全部韓語授課交換門檻"
        elif level == 2:
            tier_note = "TOPIK 2 級符合韓國國立木浦大學（TOPIK 2 級以上）及部分韓國姊妹校基礎韓語門檻（部分學校韓語授課本科系要求 TOPIK 3 級以上，或改以英語成績申請英語授課課程）"
        else:
            tier_note = "國立臺南大學韓國姊妹校韓語授課組要求 TOPIK 2～3 級以上（若修讀英語授課課程可改以英語檢定成績申請）"
        return (
            "pass" if passed else "fail",
            f"TOPIK {level} 級{'符合' if passed else '未達'}國立臺南大學韓國姊妹校交換韓語基準（{tier_note}）。",
        )
    return (
        "needs_confirmation",
        f"已填報語言檢定 {language_test}（{language_score:g}）；請對照國立臺南大學國際事務處 2026 秋季班赴境外姊妹校交換學生甄選簡章（英語組 CEFR B1～B2 / TOEFL iBT 45～79 / IELTS 5.5～6.5 / TOEIC 550～785、日語組 JLPT N3～N2、韓語組 TOPIK 2～3 級）確認目標姊妹校語言門檻。",
    )
