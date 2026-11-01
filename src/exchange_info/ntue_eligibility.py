from __future__ import annotations

import re

from .university_registry import NTUE, resolve_university

NTUE_OIA_HOME_URL = "https://oia.ntue.edu.tw/?Lang=zh-tw"
NTUE_SISTER_SCHOOLS_URL = "https://oia.ntue.edu.tw/p/405-1066-46779,c4938.php?Lang=zh-tw"
NTUE_PARTNER_DB_URL = "https://instu.ntue.edu.tw/p/412-1050-3368.php?Lang=zh-tw"
NTUE_PARTNER_MAP_URL = "https://partnerinstitutions.ntue.edu.tw:8080/#/zh"
NTUE_OUTBOUND_EXCHANGE_URL = "https://oia.ntue.edu.tw/p/405-1066-46773,c4763.php?Lang=zh-tw"
NTUE_DUAL_DEGREE_URL = "https://oia.ntue.edu.tw/p/405-1066-46772,c4763.php?Lang=zh-tw"
NTUE_SHORT_TERM_URL = "https://oia.ntue.edu.tw/p/405-1066-57137,c4763.php?Lang=zh-tw"
NTUE_INTL_SHORT_TERM_URL = "https://oia.ntue.edu.tw/p/405-1066-46780,c4938.php?Lang=zh-tw"
NTUE_OVERSEAS_FIELD_STUDY_URL = "https://oia.ntue.edu.tw/p/405-1066-46781,c4938.php?Lang=zh-tw"
NTUE_XUEHAI_SERIES_URL = "https://oia.ntue.edu.tw/p/412-1066-4764.php?Lang=zh-tw"
NTUE_XUEHAI_FEIYANG_URL = "https://oia.ntue.edu.tw/p/412-1066-4766.php?Lang=zh-tw"
NTUE_XUEHAI_XIZHU_URL = "https://oia.ntue.edu.tw/p/412-1066-4767.php?Lang=zh-tw"
NTUE_XUEHAI_ZHUMENG_URL = "https://oia.ntue.edu.tw/p/412-1066-4768.php?Lang=zh-tw"
NTUE_REGULATIONS_URL = "https://oia.ntue.edu.tw/p/412-1066-4755.php?Lang=zh-tw"
NTUE_EXCHANGE_SYSTEM_URL = "https://exchange.ntue.edu.tw/"
NTUE_EXPERIENCE_DRIVE_URL = "https://drive.google.com/drive/folders/1DpluAOoFe3nr8w5tkuFHjn9hoOkPGF8O?usp=sharing"
NTUE_115_BROCHURE_POST_URL = "https://oia.ntue.edu.tw/p/406-1066-48777,r1703.php?Lang=zh-tw"
NTUE_116_INFO_POST_URL = "https://oia.ntue.edu.tw/p/406-1066-57240,r1703.php?Lang=zh-tw"
NTUE_EXCHANGE_RULES_PDF_URL = "https://oia.ntue.edu.tw/var/file/66/1066/img/466674493.pdf"
NTUE_SCHOLARSHIP_RULES_PDF_URL = "https://oia.ntue.edu.tw/var/file/66/1066/img/749679204.pdf"
NTUE_DUAL_DEGREE_RULES_PDF_URL = "https://oia.ntue.edu.tw/var/file/66/1066/img/636774199.pdf"
NTUE_LANGUAGE_REF_PDF_URL = "https://orad.ntue.edu.tw/var/file/11/1011/img/471/517291693.pdf"
NTUE_114_BROCHURE_PDF_URL = "https://orad.ntue.edu.tw/var/file/11/1011/img/183/199934627.pdf"

NTUE_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 42.0),
    "ielts": ("IELTS", 4.0),
    "toeic": ("TOEIC", 550.0),
    "toefl_itp": ("TOEFL ITP", 500.0),
}


def is_ntue(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == NTUE.id:
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "國立臺北教育大學",
        "國立台北教育大學",
        "臺北教育大學",
        "台北教育大學",
        "國北教大",
        "國北教",
        "國北師",
        "北教大",
        "ntue",
        "national taipei university of education",
    }


def _is_graduate(degree_level: str | None) -> bool:
    text = (degree_level or "").strip()
    return any(token in text for token in ("碩", "博", "研究"))


def ntue_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
    degree = (degree_level or "").strip()
    year = (current_year or "").strip()
    if not degree:
        return (
            "needs_confirmation",
            (
                "尚未提供目前學制與年級；依《國立臺北教育大學國際交換學生甄選實施要點》第 2、3 點及《115學年度赴海外姐妹校大學交換甄選簡章》第肆點規定："
                "（1）申請人須為本校大學部學生（大一除外）、研究所碩士生或博士生（轉學生尚未有本校成績者不得參加甄選；研一生尚未有前一學年成績單者須繳交大學歷年成績單）；"
                "（2）應屆畢業生須經系所主管同意並符合本校延畢之規定；公費生須經師資培育處確認並報請分發縣市政府及教育部同意保留公費資格與延後分發；"
                "（3）在職專班生及領有臺灣獎學金者不得申請；修業年限內獲選赴國外交換以 1 次（至多 2 學期）為限。"
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
            "一年級上",
            "專一",
            "專二",
            "專三",
        )
    ) and not _is_graduate(degree):
        return (
            "fail",
            (
                f"已填報 {degree}{f'（{year}）' if year else ''}；依《國立臺北教育大學國際交換學生甄選實施要點》及《赴海外姐妹校大學交換甄選簡章》規定，"
                "申請人須為本校大學部二年級以上在學學生或碩、博士班研究生（大學部大一新生、在職專班生、休學生、已畢業生及非正式學籍生不得參加甄選）。"
            ),
        )
    if any(
        token in degree or token in year
        for token in ("休學", "已畢業", "退學", "學分班", "選修生", "在職")
    ):
        return (
            "fail",
            (
                f"已填報 {degree}{f'（{year}）' if year else ''}；依《國立臺北教育大學國際交換學生甄選實施要點》及《優秀學生出國進修獎助要點》規定，"
                "在職專班生、休學生、已畢業生及非正式學籍生不具申請資格。"
            ),
        )
    is_grad = _is_graduate(degree)
    grad_note = (
        "（提醒：碩、博士班研究生若為研一尚未有本校前一學年成績單者，須繳交大學歷年成績單；法國居斯塔夫·艾菲爾大學與法國社會科學高等學院［EHESS］僅限研究生申請，研究生另可評估日本兵庫教育大學碩士雙聯學位或法國社會科學高等學院［EHESS］雙聯博士學位計畫）"
        if is_grad
        else (
            "（提醒：大學部學生須為大二以上在學學生；若為公費生須補附公費生切結書、家長同意備忘錄及保證人同意備忘錄並經師資培育處、分發縣市政府與教育部同意延後分發；若為應屆畢業生須經系所主管同意並符合延畢規定，且大陸華東師範大學不接受應屆畢業生申請）"
        )
    )
    return (
        "pass",
        (
            f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合《國立臺北教育大學國際交換學生甄選實施要點》與交換甄選簡章在學學制規定{grad_note}。"
        ),
    )


def ntue_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
    score_min = 75.0
    gpa_min = 3.0
    rank_max = 50.0
    details: list[str] = []
    passes_ntue = False

    if academic_score is not None:
        details.append(f"歷年學業總平均 {academic_score:g} 分")
    if academic_gpa is not None:
        details.append(f"GPA {academic_gpa:g}")
    if class_rank_percent is not None:
        details.append(f"班級排名百分比前 {class_rank_percent:g}%")

    if academic_score is not None or academic_gpa is not None:
        if (academic_score is not None and academic_score >= score_min) or (
            academic_gpa is not None and academic_gpa >= gpa_min
        ):
            passes_ntue = True
    elif class_rank_percent is not None:
        if class_rank_percent <= rank_max:
            passes_ntue = True

    summary = "、".join(details)
    if (
        academic_score is None
        and academic_gpa is None
        and class_rank_percent is None
    ):
        return (
            "needs_confirmation",
            (
                "尚未填寫歷年學業總平均、GPA 或班級排名百分比；依《115學年度赴海外姐妹校大學交換甄選簡章》第肆點及《115年度教育部學海惜珠甄選簡章》規定："
                "（1）歷年在校成績總平均分數須達 75 分（含）以上（轉學生尚未有本校成績者不得參加甄選；研一生尚未有前一學年成績單者須繳交大學歷年成績單）；"
                "（2）中文歷年學業成績單正本須附有「班級排名」（申請教育部學海惜珠者歷年學業成績須為各班排名前 50%）；"
                "（3）校內甄選採筆試（40%，以報考語組語文作答申論題 2 題）及面試（60%，含書面資料審查與學業成績），總分未達 60 分者不予錄取。"
            ),
        )

    if not passes_ntue:
        return (
            "fail",
            (
                f"已填報 {summary}；未達國立臺北教育大學《赴海外姐妹校大學交換甄選簡章》規定之歷年學業成績標準"
                f"（歷年在校成績總平均須達 {score_min:g} 分［含］以上、相當於 GPA {gpa_min:g} 以上或班級排名前 {rank_max:g}%）。"
            ),
        )

    is_top_tier = (
        (academic_score is not None and academic_score >= 82.0)
        or (academic_gpa is not None and academic_gpa >= 3.5)
        or (class_rank_percent is not None and class_rank_percent <= 25.0)
    )
    if is_top_tier:
        tier_note = (
            "歷年成績表現優異，不僅符合國北教大校內甄選（歷年總平均 75 分以上）與教育部學海飛颺／學海惜珠（班排前 50%）門檻，"
            "亦在面試（佔總分 60%，含書面審查與學業成績）及歐美日韓熱門姊妹校分發具高度競爭優勢"
        )
    else:
        tier_note = (
            "達國北教大《赴海外姐妹校大學交換甄選簡章》歷年總平均 75 分（含）以上及《學海惜珠甄選簡章》班排前 50% 標準；"
            "請確認繳交附有「班級排名」之中文歷年學業成績單正本"
        )

    return (
        "pass",
        f"已填報 {summary}；符合國立臺北教育大學出國交換學生暨雙聯學位學業成績基準（{tier_note}）。",
    )


def ntue_language_check(
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
                "申請赴中國大陸地區締約姊妹校（中文組：南京大學、華東師範大學、東北師範大學、華中師範大學、首都師範大學、湖南師範大學、西北師範大學、鄭州大學、太原理工大學等）交換研修，"
                "依簡章規定以中文進行筆試與面試，免附外語能力檢定證明（若申請香港教育大學英文組則建議具備 TOEFL iBT 80 或 IELTS 6.0）。"
            ),
        )
    if not test or language_score is None:
        return (
            "needs_confirmation",
            (
                "尚未填寫有效之語言能力檢定成績。依《115學年度赴海外姐妹校大學交換甄選簡章》第肆點及《應具語言能力參考標準》規定："
                "（1）報名時須至少提供「語言檢定成績證明」、「修課證明或成績單」或「報考語組之外文自傳」其中 1 項（已報名測驗尚未取得證書者可先附准考證影本），惟姊妹校另有規定語言能力標準者須從其規定；"
                "（2）各語組建議標準：英文組 CEFR B1（TOEFL iBT 71［對照表 B1 下限 42］、TOEFL CBT 197、TOEIC 750［對照表 B1 下限 550］或 IELTS 5.5［對照表 B1 下限 4.0］）；"
                "日文組 JLPT N3（或 N2/N1）；韓文組 TOPIK 2–3 級；法文組 DELF/DALF B1–B2；德文組 TestDaF TDN3 / 德語 B1–B2；越文組國際越南語認證 IVPT A 級／B 級或英語 B1。"
            ),
        )
    if test in NTUE_ENGLISH_MINIMUMS:
        label, minimum = NTUE_ENGLISH_MINIMUMS[test]
        passed = language_score >= minimum
        tier_note = (
            "達國北教大《各國語言能力程度對照表》CEFR B1 進階級基準（TOEFL iBT 42 / IELTS 4.0 / TOEIC 550），"
            "符合英語 B1 門檻姊妹校（馬來西亞拉曼大學、泰國蘭塔納功欣皇家理工大學、印尼國民教育大學、土耳其伊斯坦堡艾登大學、德國柏林愛麗絲沙羅蒙應用科技大學、奧地利下奧地利教育大學、越南胡志明市師範大學等）申請條件"
        )
        if (
            (test == "toefl" and language_score >= 79)
            or (test == "ielts" and language_score >= 6.0)
            or (test == "toeic" and language_score >= 785)
            or (test == "toefl_itp" and language_score >= 550)
        ):
            tier_note = (
                "達 CEFR B2 高階英語標準（TOEFL iBT 79+ / IELTS 6.0+ / TOEIC 785+），全面符合美國斯托克頓大學（iBT 79 / IELTS 6.0）、阿帕拉契州立大學（iBT 78 / IELTS 6.0）、"
                "樹城州立大學（iBT 68 / IELTS 6.0）、南伊利諾大學愛德華茲維爾分校（大學部 iBT 72 / 研究所 iBT 79）、印尼建國大學（iBT 79 / IELTS 6.0），"
                "以及比利時、捷克、瑞士（圖爾古／蘇黎世／伯恩／琉森教育大學）、奧地利（維也納教育大學／維也納基督教教育大學）、德國（漢堡／路德維希堡／弗萊堡／施瓦本格明德教育大學）、西班牙、義大利、挪威 NLA 大學等全數英語 B2 姊妹校門檻（惟美國加州大學柏克萊分校 BISP 訪問計畫須 TOEFL 90 / IELTS 7.0）"
            )
        elif (
            (test == "toefl" and language_score >= 71)
            or (test == "ielts" and language_score >= 5.5)
            or (test == "toeic" and language_score >= 750)
            or (test == "toefl_itp" and language_score >= 527)
        ):
            tier_note = (
                "達國北教大《應具語言能力參考標準》及《115年度教育部學海惜珠甄選簡章》英文組正式標準（TOEFL iBT 71 / IELTS 5.5 / TOEIC 750 / TOEFL PBT 527），"
                "符合美國樹城州立大學（iBT 68）、南伊利諾大學愛德華茲維爾分校大學部（iBT 72）及多數歐洲／亞洲 CEFR B1–B2 姊妹校門檻"
            )
        return (
            "pass" if passed else "fail",
            (
                f"{label} {language_score:g} {'符合' if passed else '未達'}國立臺北教育大學國際事務處出國交換學生英語能力標準"
                f"（CEFR B1 對照下限：{label} {minimum:g}；{tier_note}）。"
            ),
        )
    if test == "jlpt":
        level = int(language_score)
        passed = 1 <= level <= 4
        if level == 1:
            tier_note = "達 JLPT N1 最高日語標準，符合日本武藏野大學（須 N1）、群馬大學／京都女子大學／兵庫教育大學／東京國際大學／尾道市立大學／千葉大學／常磐大學／茨城大學（N2）及大阪教育大學／鹿兒島大學／愛知教育大學／關西學院大學／弘前大學（N3）等全數 14 所日本姊妹校及兵庫教育大學碩士雙聯學位門檻"
        elif level == 2:
            tier_note = "達 JLPT N2（CEFR B2 相當）標準，符合日本群馬大學、京都女子大學、兵庫教育大學（含碩士雙聯學位）、東京國際大學、尾道市立大學、千葉大學（J-PAC）、常磐大學、茨城大學及所有 N3 門檻日本姊妹校（惟武藏野大學要求 N1）"
        elif level == 3:
            tier_note = "達國北教大《應具語言能力參考標準》日文組及《學海惜珠甄選簡章》JLPT N3 標準，符合大阪教育大學、鹿兒島大學教育學院、愛知教育大學、關西學院大學（須另具英語 B1）、弘前大學等校門檻（若申請群馬、兵庫教大、千葉、京都女大、尾道市立等校則建議達 N2）"
        elif level == 4:
            tier_note = "達 JLPT N4 日語程度，可申請日本弘前大學（不限級數，建議 N3）、茨城大學（未達 N2 須能以英語日常對話）或常磐大學秋季學期（N5 以上）；惟多數日本姊妹校要求 N3 或 N2 以上"
        else:
            tier_note = f"JLPT N{level} 未達國立臺北教育大學日文組交換學生一般標準（建議至少達 N3–N4 以上）"
        return (
            "pass" if passed else "fail",
            f"JLPT N{level} {'符合' if passed else '未達'}國立臺北教育大學日本姊妹校交換學生日語能力標準（{tier_note}）。",
        )
    if test == "topik":
        level = int(language_score)
        passed = 2 <= level <= 6
        if level >= 3:
            tier_note = f"TOPIK {level} 級全面符合韓國明知大學（3 級）、仁德大學（3 級）、首爾教育大學（2 級）、大邱教育大學（2 級）、中央大學（2 級）、首爾科技大學（2 級）、仁川大學（2 級）、釜慶大學（建議 2 級）等全數 8 所韓文組姊妹校及《學海惜珠甄選簡章》韓語組（3 級）門檻"
        elif level == 2:
            tier_note = "TOPIK 2 級符合韓國首爾教育大學、大邱教育大學、中央大學、首爾科技大學、仁川大學、釜慶大學等校門檻（惟明知大學、仁德大學及學海惜珠韓語組要求 TOPIK 3 級）"
        else:
            tier_note = "韓文組姊妹校原則上要求 TOPIK 2–3 級以上檢定證書"
        return (
            "pass" if passed else "fail",
            f"TOPIK {level} 級{'符合' if passed else '未達'}國立臺北教育大學韓國姊妹校韓語能力標準（{tier_note}）。",
        )
    if test in {"duolingo"}:
        passed = language_score >= 60.0
        tier_note = (
            "達美國柏克萊加州大學 BISP（125）、南伊利諾大學愛德華茲維爾分校（大學部 110 / 研究所 120）、斯托克頓大學（105）、阿帕拉契州立大學（100）等美國姊妹校 Duolingo 門檻"
            if language_score >= 100.0
            else "達 CEFR B1 參考下限（60 分），惟美國阿帕拉契州立大學（100）、斯托克頓大學（105）、SIUE（110）、UC Berkeley（125）要求更高分數"
        )
        return (
            "pass" if passed else "fail",
            f"Duolingo English Test {language_score:g} {'符合' if passed else '未達'}國立臺北教育大學出國交換英語能力參考標準（{tier_note}）。",
        )
    if test in {"dele", "delf", "dalf", "goethe", "testdaf", "tcf", "gept", "cambridge", "efset", "ivpt"}:
        passed = language_score >= 1.0
        return (
            "pass" if passed else "fail",
            f"{language_test.upper()} {language_score:g} {'符合' if passed else '未達'}國立臺北教育大學《應具語言能力參考標準》外語能力檢定規定（法文組法國居斯塔夫·艾菲爾大學／社會科學高等學院 EHESS／南希國立藝術學院要求 DELF B1 以上；德文組德國及瑞奧教育大學要求德語 B1–B2 / TestDaF TDN3；越文組要求 IVPT A/B 級或英語 B1）。",
        )
    return (
        "needs_confirmation",
        f"已填報語言檢定 {language_test}（{language_score:g}）；請對照國立臺北教育大學《應具語言能力參考標準》與《115學年度赴海外姐妹校大學交換甄選簡章》確認。",
    )
