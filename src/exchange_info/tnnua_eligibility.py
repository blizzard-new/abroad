from __future__ import annotations

import re

from .university_registry import TNNUA, resolve_university

TNNUA_OIA_HOME_URL = "https://oia.tnnua.edu.tw/"
TNNUA_OUTBOUND_EXCHANGE_URL = (
    "https://oia.tnnua.edu.tw/p/412-1007-1052.php?Lang=zh-tw"
)
TNNUA_MOU_PARTNERS_URL = (
    "https://oia.tnnua.edu.tw/p/412-1007-1071.php?Lang=zh-tw"
)
TNNUA_SCHOLARSHIPS_URL = (
    "https://oia.tnnua.edu.tw/p/412-1007-1091.php?Lang=zh-tw"
)
TNNUA_REGULATIONS_URL = (
    "https://oia.tnnua.edu.tw/p/412-1007-1089.php?Lang=zh-tw"
)
TNNUA_DOWNLOADS_URL = (
    "https://oia.tnnua.edu.tw/p/412-1007-1090.php?Lang=zh-tw"
)
TNNUA_EXPERIENCE_SHARING_URL = (
    "https://oia.tnnua.edu.tw/p/412-1007-1076.php?Lang=zh-tw"
)
TNNUA_FAQ_URL = "https://oia.tnnua.edu.tw/p/412-1007-1080.php?Lang=zh-tw"

TNNUA_EXCHANGE_REGULATION_PDF_URL = (
    "https://oia.tnnua.edu.tw/var/file/7/1007/img/2213/926164552.pdf"
)
TNNUA_DUAL_DEGREE_REGULATION_PDF_URL = (
    "https://oia.tnnua.edu.tw/var/file/7/1007/img/2213/539887990.pdf"
)
TNNUA_XUEHAI_GUIDELINES_PDF_URL = (
    "https://oia.tnnua.edu.tw/var/file/7/1007/img/2213/450750775.pdf"
)
TNNUA_SCHOLARSHIP_REVIEW_PDF_URL = (
    "https://oia.tnnua.edu.tw/var/file/7/1007/img/2213/706905469.pdf"
)
TNNUA_EXCHANGE_CONTRACT_PDF_URL = (
    "https://oia.tnnua.edu.tw/var/file/7/1007/img/1535/816581687.pdf"
)
TNNUA_ELIGIBILITY_TABLE_PDF_URL = (
    "https://oia.tnnua.edu.tw/var/file/7/1007/img/1535/291668657.pdf"
)
TNNUA_LANGUAGE_TABLE_PDF_URL = (
    "https://oia.tnnua.edu.tw/var/file/7/1007/img/1535/894025852.pdf"
)

TNNUA_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 79.0),
    "ielts": ("IELTS", 6.0),
    "toeic": ("TOEIC", 750.0),
    "toefl_itp": ("TOEFL ITP", 550.0),
}


def is_tnnua(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == TNNUA.id:
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "國立臺南藝術大學",
        "國立台南藝術大學",
        "臺南藝術大學",
        "台南藝術大學",
        "南藝大",
        "南藝",
        "tnnua",
        "tainan national university of the arts",
    }


def _is_graduate(degree_level: str | None) -> bool:
    text = (degree_level or "").strip()
    return any(token in text for token in ("碩", "博", "研究"))


def tnnua_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
    degree = (degree_level or "").strip()
    year = (current_year or "").strip()
    if not degree:
        return (
            "needs_confirmation",
            (
                "尚未提供目前學制與年級；依《國立臺南藝術大學選送學生出國研修與交流甄選辦法》第 5 條及《申請資格條件表》規定：（1）申請人須為本校日間學制大學部二年級以上、七年一貫制學士班五年級以上，或碩、博士班就讀一學期以上之在學學生（不含碩士班在職專班、休學生及外籍學位生）；（2）出國研修期間須維持南藝大在學學籍並依規定辦理註冊繳費；（3）擬同時申請教育部《學海飛颺》、《學海惜珠》或《學海築夢》獎助學金者，須具中華民國國籍且在臺灣地區設有戶籍。"
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
            "進修",
            "大一",
            "一年級",
            "貫一",
            "貫二",
            "貫三",
            "貫四",
        )
    ):
        return (
            "fail",
            (
                f"已填報 {degree}{f'（{year}）' if year else ''}；依《國立臺南藝術大學選送學生出國研修與交流甄選辦法》第 5 條規定，申請人須為本校日間學制大學部二年級以上、七年一貫制學士班五年級以上，或碩、博士班就讀一學期以上之在學學生（大學部一年級、七年一貫制一至四年級、碩士班在職專班、休學生、已畢業生及外籍學位生不得申請）。"
            ),
        )
    is_grad = _is_graduate(degree)
    grad_note = (
        "（提醒：碩、博士班研究生須於本校就讀滿一學期以上，第一階段須先送交系所書面初審［占總成績 50%，含歷年成績與研修計畫 30%、專業作品與成就 20%，須經系所會議通過且達 40 分以上］，通過後始進入國際事務處第二階段校內口試複審［占 50%，含面試表現 30%、1–2 分鐘擬赴國家語言自我介紹 20%］）"
        if is_grad
        else (
            "（提醒：日間學制大學部二年級以上及七年一貫制五年級以上學生須先通過系所書面初審［占 50%，初審須達 40 分／50 分以上］及國際事務處校內口試複審［占 50%］，兩階段總成績達 80 分以上始得錄取；交換期間須完成南藝大註冊繳費，且每學期至少修習 1 門專業課程）"
        )
    )
    return (
        "pass",
        (
            f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合《國立臺南藝術大學選送學生出國研修與交流甄選辦法》第 5 條在籍學制規定{grad_note}。"
        ),
    )


def tnnua_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
    score_min = 80.0
    gpa_min = 3.0
    rank_max = 50.0
    details: list[str] = []
    passes_tnnua = False

    if academic_score is not None:
        details.append(f"學業平均成績 {academic_score:g} 分")
        if academic_score >= score_min:
            passes_tnnua = True
    if academic_gpa is not None:
        details.append(f"GPA {academic_gpa:g}")
        if academic_gpa >= gpa_min:
            passes_tnnua = True
    if class_rank_percent is not None:
        details.append(f"班級排名百分比前 {class_rank_percent:g}%")
        if class_rank_percent <= rank_max:
            passes_tnnua = True

    summary = "、".join(details)
    if (
        academic_score is None
        and academic_gpa is None
        and class_rank_percent is None
    ):
        return (
            "needs_confirmation",
            (
                "尚未填寫學業平均成績、GPA 或班級排名百分比；依《國立臺南藝術大學選送學生出國研修與交流甄選辦法》及《辦理教育部學海飛颺、學海惜珠及學海築夢補助作業要點》規定：（1）第一階段系所書面初審（占 50%，其中歷年成績與研修計畫占 30%、專業作品與成就占 20%）須經系所會議通過且達 40 分（滿分 50 分）以上，兩階段總成績須達 80 分以上；（2）申請教育部《學海飛颺》或校內出國研修獎助學金者，在校歷年學業成績總平均須達 80 分（或 GPA 3.0）以上；（3）申請時須檢附歷年中文及英文成績單正本（含班級排名百分比）與藝術創作作品集／演奏（唱）影音檔。"
            ),
        )

    if passes_tnnua:
        top_rank = (
            (academic_score is not None and academic_score >= 85.0)
            or (academic_gpa is not None and academic_gpa >= 3.5)
            or (class_rank_percent is not None and class_rank_percent <= 25.0)
        )
        tier_note = (
            "同時符合教育部《學海飛颺》、《學海惜珠》及南藝大《選送學生赴國外研修獎助學金審查原則》80 分（GPA 3.0）以上學業基準，並於第一階段系所書面初審（歷年成績與研修計畫 30%）及歐美日韓頂尖藝術音樂院校（如奧地利格拉茨音樂與表演藝術大學 KUG、德國特rossingen國立音樂學院、法國國立高等布列塔尼藝術學院 EESAB、日本京都市立藝術大學與東京藝術大學）甄選具高度競爭優勢"
            if top_rank
            else "符合南藝大交換學生甄選與教育部《學海飛颺》歷年學業總平均 80 分（或 GPA 3.0 / 班排前 50%）基準；建議搭配完整中英文研修計畫與專業作品集／演奏影音檔，以確保第一階段系所初審達 40 分（滿分 50 分）以上"
        )
        return (
            "pass",
            (
                f"已填報 {summary}；符合國立臺南藝術大學出國交換學生暨學海獎助學金學業標準（{tier_note}）。"
            ),
        )

    return (
        "fail",
        (
            f"已填報 {summary}；未達《國立臺南藝術大學辦理教育部學海飛颺、學海惜珠及學海築夢補助作業要點》及《選送學生出國研修與交流甄選辦法》建議之學業基準（歷年學業成績總平均 {score_min:g} 分以上、GPA {gpa_min:g} 以上或班級排名前 {rank_max:g}%，且校內兩階段甄選總成績須達 80 分以上）。"
        ),
    )


def tnnua_language_check(
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
                "申請赴大陸地區締約姊妹校（如中央美術學院、中國美術學院、北京電影學院、上海音樂學院、中國音樂學院、南京藝術學院、北京服裝學院等 11 所交換姊妹校）交流研修，以中文授課為主，免附外語檢定證明（惟仍須參加校內口試複審）。"
            ),
        )
    if not test or language_score is None:
        return (
            "needs_confirmation",
            (
                "尚未填寫有效之語言能力測驗成績。依國立臺南藝術大學《選送學生出國研修與交流甄選辦法》附表《外國語文能力對照表》及各姊妹校門檻規定：（1）英語組基準：建議達 TOEFL iBT 79（CBT 213 / ITP 550）或 IELTS 6.0 以上（捷克布拉格藝術建築與設計學院 UMPRUM、奧地利格拉茨音樂與表演藝術大學 KUG、愛沙尼亞藝術學院 EKA 及新加坡拉薩爾藝術學院 LASALLE 等亦接受 CEFR B1–B2 英語證明）；（2）日語組基準：日本廣島市立大學、女子美術大學、京都市立藝術大學、沖繩縣立藝術大學建議達 JLPT N2（含）以上；（3）韓語組基準：韓國國立韓國傳統文化大學（NUCH）建議達 TOPIK 3 級（含）以上或英語組門檻；（4）歐語組基準：法國姊妹校（EESAB、ESADHaR、ESA）須法語 DELF/TCF B1 或 FLPT 150（口試 S-2）以上，德國國立特羅辛根音樂學院須德語 Goethe-Zertifikat B1 / TestDaF TDN3 或 FLPT 150 以上，西班牙瓦倫西亞理工大學（UPV）須西語 DELE B1 或 FLPT 150 以上；（5）第二階段校內口試複審皆須進行 1–2 分鐘「擬赴國家語言自我介紹」。"
            ),
        )
    if test in TNNUA_ENGLISH_MINIMUMS:
        label, minimum = TNNUA_ENGLISH_MINIMUMS[test]
        passed = language_score >= minimum
        if passed:
            tier_note = (
                "全面符合南藝大《外國語文能力對照表》英語基準（TOEFL iBT 79 / IELTS 6.0 / TOEFL ITP 550），可申請美國舊金山藝術學院 SFAI（含雙聯學位）、奧地利格拉茨音樂與表演藝術大學 KUG、捷克布拉格藝術建築與設計學院 UMPRUM、波蘭弗羅茨瓦夫藝術與設計學院、愛沙尼亞藝術學院 EKA、保加利亞國家藝術學院、澳洲國立大學 ANU、新加坡拉薩爾藝術學院 LASALLE、泰國藝術大學 Silpakorn、印尼日惹藝術學院 ISI Yogyakarta 與哈薩克國立藝術學院等英語授課姊妹校"
            )
        elif (
            (test == "toefl" and language_score >= 61)
            or (test == "ielts" and language_score >= 5.0)
            or (test == "toeic" and language_score >= 600)
            or (test == "toefl_itp" and language_score >= 500)
        ):
            passed = True
            tier_note = (
                "達 CEFR B1 中級英語程度，可申請捷克布拉格藝術建築與設計學院 UMPRUM、波蘭弗羅茨瓦夫藝術與設計學院、保加利亞國家藝術學院、印尼日惹藝術學院 ISI Yogyakarta、泰國藝術大學 Silpakorn 及韓國國立韓國傳統文化大學英語組（惟未達南藝大《外國語文能力對照表》TOEFL iBT 79 / IELTS 6.0 參考基準，建議強化第二階段 1–2 分鐘外語口試表現）"
            )
        else:
            tier_note = (
                f"未達南藝大《外國語文能力對照表》英語基準（{label} {minimum:g}）及姊妹校 CEFR B1 門檻"
            )
        return (
            "pass" if passed else "fail",
            (
                f"{label} {language_score:g}"
                f" {'符合' if passed else '未達'}國立臺南藝術大學出國交換暨雙聯學位英語能力標準（{tier_note}）。"
            ),
        )
    if test == "jlpt":
        level = int(language_score)
        passed = 1 <= level <= 3
        if level in (1, 2):
            tier_note = (
                f"達 JLPT N{level} 日語標準，全面符合南藝大《外國語文能力對照表》（JLPT N2）及日本廣島市立大學、女子美術大學、京都市立藝術大學、沖繩縣立藝術大學交換門檻"
            )
        elif level == 3:
            tier_note = (
                "達 JLPT N3 中級日語程度，可參與校內甄選並於第二階段進行日語自我介紹（惟南藝大《外國語文能力對照表》及日本廣島市立大學、女子美術大學、京都市立藝術大學正式提名建議達 JLPT N2 以上）"
            )
        else:
            tier_note = (
                f"JLPT N{level} 未達南藝大《外國語文能力對照表》日語基準（JLPT N2）"
            )
        return (
            "pass" if passed else "fail",
            (
                f"JLPT N{level}"
                f" {'符合' if passed else '未達'}國立臺南藝術大學日本姊妹校交換學生日語能力標準（{tier_note}）。"
            ),
        )
    if test == "topik":
        level = int(language_score)
        passed = 3 <= level <= 6
        tier_note = (
            f"達 TOPIK {level} 級標準，符合南藝大《外國語文能力對照表》（TOPIK 3 級）及韓國國立韓國傳統文化大學（NUCH）交換門檻"
            if passed
            else "南藝大《外國語文能力對照表》韓語基準要求 TOPIK 3 級（含）以上（或改以英語成績申請英語授課課程）"
        )
        return (
            "pass" if passed else "fail",
            (
                f"TOPIK {level}"
                f" 級{'符合' if passed else '未達'}國立臺南藝術大學韓國姊妹校韓語能力標準（{tier_note}）。"
            ),
        )
    if test in {"dele", "delf", "goethe", "testdaf", "tcf", "flpt", "gept"}:
        passed = language_score >= 1.0
        return (
            "pass" if passed else "fail",
            (
                f"{language_test.upper()} {language_score:g}"
                f" {'符合' if passed else '未達'}國立臺南藝術大學《外國語文能力對照表》檢定標準（法國 EESAB / ESADHaR 須法語 DELF/TCF B1 或 FLPT 150、德國國立特羅辛根音樂學院須德語 B1 / TestDaF TDN3 或 FLPT 150、西班牙瓦倫西亞理工大學 UPV 須西語 DELE B1 或 FLPT 150）。"
            ),
        )
    return (
        "needs_confirmation",
        (
            f"已填報語言測驗 {language_test}（{language_score:g}），請對照國立臺南藝術大學《外國語文能力對照表》與目標姊妹校簡章確認是否符合 CEFR B1/B2 或對應語種門檻。"
        ),
    )
