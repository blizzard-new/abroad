from __future__ import annotations

import re

from .university_registry import resolve_university

CYUT_OIA_HOME_URL = "https://icsc.cyut.edu.tw/"
CYUT_PARTNER_LIST_URL = "https://icsc.cyut.edu.tw/p/412-1008-5342.php?Lang=zh-tw"
CYUT_REGULATIONS_URL = "https://icsc.cyut.edu.tw/p/412-1008-5552.php?Lang=zh-tw"
CYUT_DOWNLOADS_URL = "https://icsc.cyut.edu.tw/p/412-1008-4642.php?Lang=zh-tw"
CYUT_FALL_ASIA_URL = "https://icsc.cyut.edu.tw/p/404-1008-53429.php?Lang=zh-tw"
CYUT_FALL_EU_URL = "https://icsc.cyut.edu.tw/p/404-1008-53430.php?Lang=zh-tw"
CYUT_SPRING_ASIA_URL = "https://icsc.cyut.edu.tw/p/404-1008-55551.php?Lang=zh-tw"
CYUT_SPRING_EU_URL = "https://icsc.cyut.edu.tw/p/404-1008-55552.php?Lang=zh-tw"
CYUT_DUAL_DEGREE_URL = "https://icsc.cyut.edu.tw/p/404-1008-42094.php?Lang=zh-tw"
CYUT_DUAL_DEGREE_NOTICE_URL = "https://icsc.cyut.edu.tw/p/404-1008-53431.php?Lang=zh-tw"
CYUT_ENG_CAMP_URL = "https://icsc.cyut.edu.tw/p/406-1008-55550,r456.php?Lang=zh-tw"
CYUT_XUEHAI_URL = "https://icsc.cyut.edu.tw/p/406-1008-53997,r456.php?Lang=zh-tw"
CYUT_ETEN_URL = "https://icsc.cyut.edu.tw/p/406-1008-41345,r869.php?Lang=zh-tw"
CYUT_THOUSAND_URL = "https://icsc.cyut.edu.tw/p/405-1008-41580,c3353.php?Lang=zh-tw"

CYUT_EXCHANGE_REG_PDF_URL = "https://icsc.cyut.edu.tw/var/file/8/1008/img/957/827358022.pdf"
CYUT_EXCHANGE_SUBSIDY_PDF_URL = "https://icsc.cyut.edu.tw/var/file/8/1008/img/957/141748962.pdf"
CYUT_DUAL_DEGREE_REG_PDF_URL = "https://icsc.cyut.edu.tw/var/file/8/1008/img/957/141559661.pdf"
CYUT_DUAL_DEGREE_SCHOLARSHIP_PDF_URL = "https://icsc.cyut.edu.tw/var/file/8/1008/img/957/520105383.pdf"
CYUT_ENG_CAMP_REG_PDF_URL = "https://icsc.cyut.edu.tw/var/file/8/1008/img/957/578852414.pdf"
CYUT_THOUSAND_REG_PDF_URL = "https://icsc.cyut.edu.tw/var/file/8/1008/img/957/175137758.pdf"
CYUT_XUEHAI_GUIDELINE_PDF_URL = "https://icsc.cyut.edu.tw/var/file/8/1008/img/957/796678916.pdf"
CYUT_CREDIT_REG_PDF_URL = "https://icsc.cyut.edu.tw/var/file/8/1008/img/957/706154572.pdf"

CYUT_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 61.0),
    "ielts": ("IELTS", 5.0),
    "toefl_itp": ("TOEFL ITP/PBT", 500.0),
    "toeic": ("TOEIC", 550.0),
    "duolingo": ("Duolingo English Test", 85.0),
}


def is_cyut(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == "cyut":
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "朝陽科技大學",
        "朝陽科大",
        "朝陽",
        "cyut",
        "chaoyang university of technology",
    }


def _is_graduate(degree_level: str | None) -> bool:
    text = (degree_level or "").strip()
    return any(token in text for token in ("碩", "博", "研究"))


def cyut_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
    degree = (degree_level or "").strip()
    year = (current_year or "").strip()
    if not degree:
        return (
            "needs_confirmation",
            (
                "尚未提供目前學制與年級；依《朝陽科技大學與境外大學辦理交換學生實施要點》與當期甄選簡章：（1）限本校日間部四技、二技及碩博士班修業滿 1 年以上之在學學生申請（不含延修生、休學生及進修部／在職專班學生）；（2）日本芝浦工業大學、日本岩手縣立大學、日本長野大學及丹麥維亞大學要求四技修業滿 2 年（大三以上）；（3）跨國雙聯學位（3+1、2+2 雙學士及 1+1、1.5+1 雙碩士）須符合二校累計修業月數規定（雙學士合計至少 32 個月、雙碩士合計至少 12 個月）。"
            ),
        )
    if any(
        token in degree or token in year
        for token in (
            "在職專班",
            "進修部",
            "碩專",
            "emba",
            "EMBA",
            "學分班",
            "選修生",
            "休學",
            "延畢",
            "延畢生",
            "延修",
            "延修生",
        )
    ):
        return (
            "fail",
            (
                f"已填報 {degree}{f'（{year}）' if year else ''}；依《朝陽科技大學與境外大學辦理交換學生實施要點》與《學生赴國外姐妹校交換學習補助要點》，交換生及雙聯學位甄選限日間部正式學籍在學學生（不含延修生、休學生及在職專班）申請。"
            ),
        )
    is_grad = _is_graduate(degree)
    if not is_grad and year in {
        "大一",
        "大一上",
        "大一下",
        "一年級",
        "一年級上學期",
        "一年級下學期",
    }:
        return (
            "fail",
            (
                f"已填報 {degree}（{year}）；依《朝陽科技大學與境外大學辦理交換學生實施要點》及甄選簡章規定，大學部學生須修業滿 1 年以上（大二以上；芝浦工大、岩手縣大、長野大學及丹麥維亞大學要求四技修業滿 2 年以上）始得申請出國交換（惟大一下學期可先行報名寒暑假菲律賓拉普拉普宿霧國際大學 LCIC 英語密集研習營）。"
            ),
        )
    grad_note = (
        "（提醒：碩博士班研究生須修業滿 1 年以上，可申請日本芝浦工大研究交流與交換、岩手縣大／會津大學／函館未來大學／德國 OTH Regensburg 資訊碩士 1+1 雙聯、澳洲西雪梨大學社工碩士 1.5+1 雙聯、美國明州西南州立大學企管碩士 1+1 雙聯及英國德蒙福特大學／西蘇格蘭大學 1+1 雙碩士）"
        if is_grad
        else "（提醒：日本芝浦工業大學、岩手縣立大學、長野大學及丹麥維亞大學要求四技修業滿 2 年［大三以上］；攻讀英國 3+1／2+2 或澳洲南十字星大學 2+2 雙學士須於朝陽修滿 2–3 學年）"
    )
    return (
        "pass",
        (
            f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合朝陽科技大學國際事務處《與境外大學辦理交換學生實施要點》、《與國外大學辦理雙聯學制實施辦法》及出國交換機票補助之在學身分規定{grad_note}。"
        ),
    )


def cyut_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
    score_min = 70.0
    gpa_min = 2.7
    rank_max = 50.0
    details: list[str] = []
    passes_general = False
    passes_scholarship = False

    if academic_score is not None:
        details.append(f"學業平均 {academic_score:g} 分")
        if academic_score >= score_min:
            passes_general = True
        if academic_score >= 75.0:
            passes_scholarship = True
    if academic_gpa is not None:
        details.append(f"GPA {academic_gpa:g}")
        if academic_gpa >= gpa_min:
            passes_general = True
        if academic_gpa >= 3.0:
            passes_scholarship = True
    if class_rank_percent is not None:
        details.append(f"班排名百分比前 {class_rank_percent:g}%")
        if class_rank_percent <= rank_max:
            passes_general = True
            passes_scholarship = True

    summary = "、".join(details)
    if (
        academic_score is None
        and academic_gpa is None
        and class_rank_percent is None
    ):
        return (
            "needs_confirmation",
            (
                "尚未填寫歷年學業成績、GPA 或班排名百分比；依《朝陽科技大學與境外大學辦理交換學生實施要點》與《選送優秀學生寒暑假赴海外姐妹校英語研習營甄選辦法》：（1）申請出國交換或雙聯學位須歷年學業總平均達 70 分（GPA 2.7）以上或班級排名前 50%，且歷年操行成績達 80 分以上、無記過處分紀錄；（2）申請教育部《學海飛颺／學海惜珠》或寒暑假菲律賓拉普拉普宿霧國際大學（LCIC）英語研習營者，學業成績須達班級排名前 50%。"
            ),
        )

    if passes_general:
        tier_notes: list[str] = [
            "符合朝陽科技大學出國交換暨雙聯學位甄選（學業總平均 70 分／GPA 2.7 或班排前 50%）及《學生赴國外姐妹校交換學習補助要點》來回機票補助（亞洲上限 NT$18,000–20,000、歐美上限 NT$45,000）學業門檻"
        ]
        if passes_scholarship:
            tier_notes.append(
                "且達教育部《學海飛颺／學海惜珠》（6萬–24萬元）及寒暑假赴菲律賓 LCIC 英語密集研習營（班排前 50%，補助 50% 研習費上限 NT$30,000＋機票上限 NT$10,000）之學業標準"
            )
        else:
            tier_notes.append(
                "若欲同時申請教育部《學海飛颺／學海惜珠》或寒暑假菲律賓英語研習營，須確認班級排名位於前 50% 且操行成績達 80 分以上"
            )
        return (
            "pass",
            f"已填報 {summary}；{'；'.join(tier_notes)}。",
        )

    return (
        "fail",
        (
            f"已填報 {summary}；未達朝陽科技大學出國交換甄選最低學業標準（歷年學業總平均 70 分／GPA 2.7 以上或班級排名前 50%，且操行成績達 80 分以上）。"
        ),
    )


def cyut_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
    test = (language_test or "").strip().lower()
    if partner_country in {"中國大陸", "中國", "澳門"} and (
        not test or language_score is None
    ):
        return (
            "pass",
            (
                "申請赴大陸及澳門地區合作姊妹校（北京科技大學、北京服裝學院、廈門理工學院、福州大學、深圳大學、澳門科技大學等）為中文授課，免附外語檢定證照；惟仍須備齊核章申請表、家長同意書、歷年成績單與讀書計畫參加校內審查。"
            ),
        )
    if not test or language_score is None:
        return (
            "needs_confirmation",
            (
                "尚未填寫外語能力檢定成績。依朝陽科技大學國際事務處《赴亞洲及歐美姊妹校交換生甄選簡章》與《跨國雙聯學位甄選簡章》：（1）歐美墨交換生組要求 IELTS 5.0–5.5（捷克馬薩里克大學、德國東巴伐利亞雷根斯堡應科大 OTH Regensburg、德國帕紹大學要求 IELTS 5.5 以上；丹麥維亞大學 VIA、哥本哈根應科大 UCC、荷蘭漢斯 Hanze／海牙 THUAS／漢恩 HAN、比利時 UCLL、西班牙蒙德拉貢／維克大學、德國烏茲堡應科大 THWS、俄羅斯秋明大學、墨西哥蒙特雷科大要求 IELTS 5.0–5.5 或 TOEFL iBT 61–72 以上）並須通過英語口試；（2）日本芝浦工業大學與岩手縣立大學要求英文 CEFR B2（IELTS 5.5 / TOEFL iBT 80 / TOEIC 785）或日文 JLPT N2，會津大學、長野大學、函館未來大學建議 JLPT N3 或 IELTS 5.0；（3）韓國東義、三育、水原、龍仁、順天、忠清大學建議 TOPIK 3 級或 IELTS 5.0–5.5 / TOEIC 550–785；（4）英美澳雙聯學位要求 IELTS UKVI 6.0–6.5 或 TOEFL iBT 80。"
            ),
        )
    if test in CYUT_ENGLISH_MINIMUMS:
        label, minimum = CYUT_ENGLISH_MINIMUMS[test]
        passed = language_score >= minimum
        if (
            (test == "toefl" and language_score >= 80)
            or (test == "ielts" and language_score >= 6.0)
            or (test == "toefl_itp" and language_score >= 550)
            or (test == "toeic" and language_score >= 785)
        ):
            tier_note = "達 CEFR B2 高階門檻（IELTS 6.0+ / TOEFL iBT 80+ / TOEIC 785+），符合歐美墨全部交換姊妹校、日本芝浦工大與岩手縣大英語學程、韓國龍仁大學英語學程，以及英國（密德薩斯、德蒙福特、桑德蘭、西蘇格蘭）、美國（明州西南州立大學、漢弗萊斯大學）、德國（OTH Regensburg）與日本（會津大學）跨國雙聯學位英語門檻"
        elif (
            (test == "toefl" and language_score >= 72)
            or (test == "ielts" and language_score >= 5.5)
            or (test == "toefl_itp" and language_score >= 543)
        ):
            tier_note = "達 CEFR B2 門檻（IELTS 5.5 / TOEFL iBT 72+），符合捷克馬薩里克大學、德國 OTH Regensburg、德國帕紹大學、丹麥、荷蘭、比利時、西班牙、墨西哥等全部歐美墨交換姊妹校及日本芝浦工大、岩手縣大英語交換門檻（英國雙聯學位要求 IELTS UKVI 6.0）"
        else:
            tier_note = "達 CEFR B1 基本門檻（IELTS 5.0 / TOEFL iBT 61 / TOEIC 550），符合丹麥、荷蘭、比利時、西班牙、德國烏茲堡應科大、俄羅斯秋明大學、墨西哥蒙特雷科大、日韓部分姊妹校及菲律賓 LCIC 英語研習營門檻（捷克馬薩里克、德國 OTH Regensburg、帕紹大學及芝浦工大要求 IELTS 5.5 / CEFR B2）"
        return (
            "pass" if passed else "fail",
            (
                f"{label} {language_score:g} {'符合' if passed else '未達'}朝陽科技大學出國交換暨雙聯學位英語檢定基準（一般交換最低採計門檻：{label} {minimum:g}；{tier_note}）。"
            ),
        )
    if test == "jlpt":
        level = int(language_score)
        passed = 1 <= level <= 3
        if level in (1, 2):
            tier_note = f"JLPT N{level} 符合日本芝浦工業大學（日語學程 N2）、岩手縣立大學（日語學程 N2）、會津大學（N3）、長野大學（N3）、公立函館未來大學（N3）全部日本姊妹校交換與雙聯日語門檻"
        elif level == 3:
            tier_note = "JLPT N3 符合日本會津大學、長野大學、公立函館未來大學交換門檻及教育部學海飛颺／惜珠日語基準（日本芝浦工業大學與岩手縣立大學日語授課學程要求 JLPT N2，或改以 CEFR B2 英語成績申請英語學程）"
        else:
            tier_note = f"目前為 JLPT N{level}，未達日本會津大學／長野大學（建議 JLPT N3）及芝浦工業大學／岩手縣立大學（JLPT N2）日語檢定門檻"
        return (
            "pass" if passed else "fail",
            f"JLPT N{level} {'符合' if passed else '未達'}朝陽科技大學日本姊妹校交換暨雙聯日語檢定基準（{tier_note}）。",
        )
    if test == "topik":
        level = int(language_score)
        passed = 2 <= level <= 6
        if level >= 3:
            tier_note = f"TOPIK {level} 級符合韓國東義大學（免學費且免收校內宿舍費）、三育大學、水原大學、龍仁大學、國立順天大學及忠清大學全部韓國姊妹校交換門檻及教育部學海飛颺／惜珠韓語基準"
        elif level == 2:
            tier_note = "TOPIK 2 級符合韓國國立順天大學、忠清大學及東義大學基礎韓語門檻（三育大學、水原大學及龍仁大學建議達 TOPIK 3 級或改以 IELTS 5.0–5.5 / TOEIC 550–785 英語成績申請）"
        else:
            tier_note = f"目前為 TOPIK {level} 級，建議提升至 TOPIK 2–3 級或搭配英語檢定證明申請韓國姊妹校交換"
        return (
            "pass" if passed else "fail",
            f"TOPIK {level} 級{'符合' if passed else '未達'}朝陽科技大學韓國姊妹校韓語檢定基準（{tier_note}）。",
        )
    return (
        "needs_confirmation",
        f"已填報語言檢定 {language_test}（{language_score:g}）；請對照朝陽科技大學國際事務處當期《赴亞洲及歐美姊妹校交換學生甄選簡章》確認目標姊妹校之語言門檻。",
    )
