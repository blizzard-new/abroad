"""National Pingtung University (國立屏東大學, NPTU) outbound exchange & dual-degree eligibility checks.

Official rule sources:
- 國立屏東大學 115年出國交換甄選簡章與申請表單:
  https://ccd.nptu.edu.tw/p/406-1091-190211,r2961.php?Lang=zh-tw
- 國立屏東大學 116學年度出國交換／實習說明會公告:
  https://ccd.nptu.edu.tw/p/406-1091-200033,r11.php?Lang=zh-tw
- 國立屏東大學學生出國有關學業及學籍處理要點 (114.03.27修正通過):
  https://reg.nptu.edu.tw/var/file/66/1066/img/1690/law1-14.pdf
- 國立屏東大學與境外大學校院辦理雙聯學制實施辦法 (114.05.22修正通過):
  https://reg.nptu.edu.tw/var/file/66/1066/img/1690/law1-15.pdf
- 國立屏東大學學生抵免學分要點 (115.10.22修正通過):
  https://reg.nptu.edu.tw/var/file/66/1066/img/1690/law1-4.pdf
- 國立屏東大學與外國學制學分轉換準則:
  https://reg.nptu.edu.tw/var/file/66/1066/img/1690/law1-20EN.pdf
"""

from __future__ import annotations

import re

from .university_registry import NPTU, resolve_university

NPTU_OIA_HOME_URL = "https://oia.nptu.edu.tw/index.php"
NPTU_OUTBOUND_EXCHANGE_URL = "https://ccd.nptu.edu.tw/p/412-1091-12234.php?Lang=zh-tw"
NPTU_OUTBOUND_POST_115_URL = "https://ccd.nptu.edu.tw/p/406-1091-190211,r2961.php?Lang=zh-tw"
NPTU_INFO_SESSION_116_URL = "https://ccd.nptu.edu.tw/p/406-1091-200033,r11.php?Lang=zh-tw"
NPTU_DUAL_DEGREE_URL = "https://ccd.nptu.edu.tw/p/412-1091-15344.php?Lang=zh-tw"
NPTU_PARTNER_LIST_URL = "https://ccd.nptu.edu.tw/p/412-1091-6005.php?Lang=zh-tw"
NPTU_MAINLAND_SISTERS_URL = "https://dcma.nptu.edu.tw/p/412-1008-5098.php?Lang=zh-tw"
NPTU_REGULATIONS_URL = "https://ccd.nptu.edu.tw/p/412-1091-6050.php?Lang=zh-tw"

NPTU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 42.0),
    "ielts": ("IELTS", 4.0),
    "toefl_itp": ("TOEFL ITP/PBT", 460.0),
    "toeic": ("TOEIC", 550.0),
    "duolingo": ("Duolingo English Test", 75.0),
}


def is_nptu(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == NPTU.id:
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "nptu",
        "國立屏東大學",
        "屏東大學",
        "屏大",
        "national pingtung university",
    }


def _is_graduate(degree_level: str | None) -> bool:
    text = (degree_level or "").strip()
    return any(token in text for token in ("碩", "博", "研究", "master", "phd", "doctoral"))


def nptu_degree_check(
    degree_level: str | None, current_year: str | int | None = None
) -> tuple[str, str]:
    degree = (degree_level or "").strip()
    year = str(current_year or "").strip()
    if not degree:
        return (
            "needs_confirmation",
            (
                "尚未提供目前學制與年級；依《國立屏東大學出國交換甄選簡章》、《學生出國有關學業及學籍處理要點》及《與境外大學校院辦理雙聯學制實施辦法》：申請對象為於本校就讀滿一學期以上之在學學士班、碩士班及博士班學生（其中「教育部學海飛颺／學海惜珠」與本校「菁英育才」補助不含在職生與進修生；「自費交換」則包含在職生與進修生；修讀雙聯學位者出國前後在屏東大學總修業時間學士班至少 4 學期、碩士班至少 2 學期、博士班至少 3 學期）。"
            ),
        )
    if any(
        token in degree or token in year
        for token in ("學分班", "選修生", "休學", "退學")
    ):
        return (
            "fail",
            (
                f"已填報 {degree}{f'（{year}）' if year else ''}；依國立屏東大學出國交換甄選簡章與《學生出國有關學業及學籍處理要點》規定，休學或不具正式在學學籍者不得申請出國交換與雙聯學位。"
            ),
        )
    if any(
        token in degree or token in year
        for token in ("在職", "進修", "夜", "碩專", "EMBA", "emba")
    ):
        return (
            "pass",
            (
                f"已填報 {degree}{f'（{year}）' if year else ''}；依國立屏東大學出國交換甄選簡章規定，在職專班生與進修部學生可申請「自費出國交換計畫」（惟教育部「學海飛颺」、「學海惜珠」及本校校友捐款「菁英育才」補助對象不含在職生與進修生）。"
            ),
        )
    is_grad = _is_graduate(degree)
    grad_note = (
        "（提醒：碩博士班在學滿一學期以上可申請教育部學海飛颺、學海惜珠、屏大「菁英育才」補助及英國密德薩斯大學 1+1、美國北阿拉巴馬大學 1+1、西來大學 1+1、捷克赫拉德茨克拉洛韋大學 UHK 1+1、捷克托馬斯拔佳大學 TBU 1+1、泰國吞武里蒙庫國王科技大學 KMUTT 1+1 等碩士雙聯學位）"
        if is_grad
        else "（提醒：學士班就讀滿一學期以上可申請學海飛颺、學海惜珠、屏大「菁英育才」補助與自費交換；部分日本與馬來西亞姊妹校如馬來亞大學、弘前大學、山形大學、鹿兒島大學、山陽學園大學限大二以上，兵庫教育大學與香川大學限大三以上；出國期間於屏東大學註冊且大學部每學期至少須修習 1 門課程）"
    )
    return (
        "pass",
        f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合國立屏東大學出國交換與跨國雙聯學位之在學學籍規定{grad_note}。",
    )


def nptu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
    is_grad = _is_graduate(degree_level)
    score_min = 70.0 if is_grad else 60.0
    gpa_min = 3.0 if is_grad else 2.0
    details: list[str] = []
    passes_basic = False
    passes_xuehai_rank = False
    passes_um_gpa = False

    if academic_score is not None:
        details.append(f"學業平均 {academic_score:g} 分")
        if academic_score >= score_min:
            passes_basic = True
        if academic_score >= 70.0:
            passes_um_gpa = True
        if academic_score >= 75.0 and class_rank_percent is None:
            passes_xuehai_rank = True
    if academic_gpa is not None:
        details.append(f"GPA {academic_gpa:g}")
        if academic_gpa >= gpa_min:
            passes_basic = True
        if academic_gpa >= 3.0:
            passes_um_gpa = True
            if class_rank_percent is None:
                passes_xuehai_rank = True
    if class_rank_percent is not None:
        details.append(f"班排名百分比前 {class_rank_percent:g}%")
        if class_rank_percent <= 50.0:
            passes_basic = True
            passes_xuehai_rank = True
        elif academic_score is None and academic_gpa is None:
            passes_basic = True

    summary = "、".join(details)
    if (
        academic_score is None
        and academic_gpa is None
        and class_rank_percent is None
    ):
        return (
            "needs_confirmation",
            (
                "尚未填寫歷年學業平均成績、GPA 或班排名百分比；依《國立屏東大學出國交換甄選簡章》四大推薦計畫規定：（1）【教育部學海飛颺／學海惜珠】歷年學業成績須在班排名前 50% 以內，且操行成績平均 80 分以上、無申誡以上處分；（2）【屏東大學「菁英育才」補助（校友捐款）】無班排前 50% 限制，惟「每學期」操行成績皆須達 80 分以上（非平均）且無申誡以上處分（最高補助生活費 NT$50,000＋機票費 NT$30,000＝NT$80,000）；（3）【自費交換】就讀滿一學期以上且學業及格（學士班 60 分／GPA 2.0、碩博班 70 分／GPA 3.0；惟馬來亞大學要求 GPA 3.0、韓國外國語大學要求 GPA 2.5、西來大學雙聯要求 GPA 2.75–3.0）。"
            ),
        )

    if not passes_basic:
        return (
            "fail",
            (
                f"已填報 {summary}；未達國立屏東大學{'研究所 70 分（GPA 3.0）' if is_grad else '學士班 60 分（GPA 2.0）'}基本及格標準（依《國立屏東大學等第制成績定義與等第績分表及GPA成績對照表》規定）。"
            ),
        )

    tier_notes: list[str] = []
    if class_rank_percent is not None and class_rank_percent > 50.0:
        tier_notes.append(
            f"班排名前 {class_rank_percent:g}% 雖未達教育部《學海飛颺／學海惜珠》（須班排前 50% 以內）門檻，但完全符合屏東大學校友捐款【「菁英育才」補助】（無班排前 50% 限制，每學期操行皆達 80 分以上即可獲每月 NT$10,000 生活費＋最高 NT$30,000 機票補助）及【自費交換】申請資格"
        )
    elif passes_xuehai_rank:
        tier_notes.append(
            "符合教育部《學海飛颺／學海惜珠》（歷年成績班排前 50% 以內，另須操行平均 80 分以上）、屏東大學【「菁英育才」補助】（每學期操行皆 80 分以上）及【自費交換】全部四大推薦計畫學業門檻"
        )
    else:
        tier_notes.append(
            "符合屏東大學【「菁英育才」補助】（無班排前 50% 限制，惟須每學期操行皆 80 分以上）與【自費交換】學業門檻；若欲同時申請教育部《學海飛颺／學海惜珠》請確認歷年成績單班級排名百分比位於前 50% 以內"
        )
    if passes_um_gpa:
        tier_notes.append("亦達馬來亞大學（GPA 3.0）、韓國外國語大學（GPA 2.5）及英美捷泰雙聯學位學業基準")

    return (
        "pass",
        f"已填報 {summary}；符合國立屏東大學出國交換甄選學業標準（{'；'.join(tier_notes)}）。",
    )


def nptu_language_check(
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
                "申請赴大陸地區合作學校（華中科技大學、西安交通大學、蘭州大學、華東師範大學、東北師範大學、南京師範大學、西南大學、雲南大學、福州大學、廣西大學等）交換以中文授課為主，免附英／日／韓外語能力檢定證明。"
            ),
        )
    if not test or language_score is None:
        return (
            "needs_confirmation",
            (
                "尚未填寫外語能力檢定成績。依《國立屏東大學出國交換甄選簡章》規定：（1）赴非日語系國家交換：校內甄選基本門檻須達 CEFR B1（含）以上，即 TOEIC 550 / TOEFL iBT 42 / TOEFL ITP 460 / IELTS 4.0 / GEPT 中級初試 / CSEPT 第一級 170 或第二級 180 以上（部分姊妹校入學門檻較高：馬來亞大學要求 IELTS 6.0 / TOEFL iBT 80 / TOEIC 785、捷克布拉格捷克理工大學與義大利帕維亞大學要求英語 B2、韓國外國語大學要求 TOEFL iBT 71 / IELTS 5.5 或 TOPIK 3 級、美國北阿拉巴馬大學要求 iBT 61 / IELTS 5.5、西來大學要求 iBT 69 / IELTS 5.5、英國密德薩斯大學雙聯要求 IELTS 6.0–6.5）；（2）赴日本 15 所姊妹校交換：原則要求具備日語 JLPT N2（含）以上，惟校內甄選收件時倘尚未取得 N2 證書，得先以「非日語之外語能力 CEFR B1 以上證明」加附本校師長簽署之《日本語力評價表》替代（其中日本國立宮崎大學、弘前大學亦接受 JLPT N3 或英語 B1）。"
            ),
        )
    if test in NPTU_ENGLISH_MINIMUMS:
        label, minimum = NPTU_ENGLISH_MINIMUMS[test]
        passed = language_score >= minimum
        tier_note = "達屏東大學出國交換校內甄選 CEFR B1 英語基準（TOEIC 550 / TOEFL iBT 42 / ITP 460 / IELTS 4.0），且若赴日本交換尚未取得 JLPT N2 亦可搭配師長簽署之《日本語力評價表》報名校內甄選"
        if (
            (test == "toefl" and language_score >= 80)
            or (test == "ielts" and language_score >= 6.0)
            or (test == "toeic" and language_score >= 785)
            or (test == "duolingo" and language_score >= 105)
        ):
            tier_note = "達馬來亞大學 UM（IELTS 6.0 / iBT 80 / TOEIC 785）、英國密德薩斯大學雙聯（IELTS 6.0）、捷克布拉格捷克理工大學 CTU 與義大利帕維亞大學（CEFR B2）、美國西來大學／北阿拉巴馬大學／楊斯鎮州立大學、韓國外國語大學 HUFS 及全部英語授課姊妹校高階門檻"
        elif (
            (test == "toefl" and language_score >= 61)
            or (test == "ielts" and language_score >= 5.5)
            or (test == "toefl_itp" and language_score >= 500)
            or (test == "toeic" and language_score >= 650)
            or (test == "duolingo" and language_score >= 95)
        ):
            tier_note = "符合美國北阿拉巴馬大學 UNA（iBT 61 / IELTS 5.5 / TOEIC 600）、澳洲國際飯店管理學院 ICHM、捷克赫拉德茨克拉洛韋大學 UHK／托馬斯拔佳大學 TBU／利貝雷茨理工大學 TUL、德國柏林 ASH、韓國釜山外大與大邱教大、馬來西亞拉曼大學 UTAR 及泰越全部姊妹校門檻（惟馬來亞大學要求 IELTS 6.0 / iBT 80 / TOEIC 785，布拉格捷克理工與帕維亞大學要求英語 B2）"
        return (
            "pass" if passed else "fail",
            f"{label} {language_score:g} {'符合' if passed else '未達'}國立屏東大學出國交換與雙聯學位英語檢定基準（校內甄選最低門檻：{label} {minimum:g}；{tier_note}）。",
        )
    if test == "jlpt":
        level = int(language_score)
        passed = 1 <= level <= 3
        if level in (1, 2):
            tier_note = f"JLPT N{level} 直接符合國立屏東大學赴日本交換校內甄選門檻（N2 以上）及全部 15 所日本國私立姊妹校（宮崎大學、弘前大學、大阪教育大學、兵庫教育大學、室蘭工業大學、和歌山大學、鹿兒島大學、香川大學、山形大學、信州大學、麗澤大學、姬路獨協大學、廣島修道大學、山陽學園大學、日本經濟大學）日語要求"
        elif level == 3:
            tier_note = "JLPT N3 符合日本國立宮崎大學、國立弘前大學、山陽學園大學、日本經濟大學等校接待門檻；提醒：屏東大學校內甄選規定日語組須具 JLPT N2，倘報名校內甄選時僅持 N3，請一併檢附「非日語之外語能力 CEFR B1 以上證明（如 TOEIC 550）」加附本校師長簽署之《日本語力評價表》即可報名"
        else:
            tier_note = "屏東大學赴日本交換校內甄選要求 JLPT N2 以上（若尚未取得 N2，須以非日語 CEFR B1 證明加附本校師長簽署之《日本語力評價表》替代）"
        return (
            "pass" if passed else "fail",
            f"JLPT N{level} {'符合' if passed else '未達'}國立屏東大學日本姊妹校交換日語基準（{tier_note}）。",
        )
    if test == "topik":
        level = int(language_score)
        passed = level >= 2
        if level >= 3:
            tier_note = f"TOPIK {level} 級符合韓國外國語大學（HUFS，要求 TOPIK 3 級）、釜山外國語大學（BUFS）與國立大邱教育大學（DNUE）韓語門檻（提醒：屏東大學校內甄選簡章規定赴非日語系國家須具 CEFR B1 外語能力證明）"
        elif level == 2:
            tier_note = "TOPIK 2 級符合韓國釜山外國語大學（BUFS）與大邱教育大學（DNUE）韓語門檻（韓國外國語大學 HUFS 要求 TOPIK 3 級或 TOEFL iBT 71 / IELTS 5.5）"
        else:
            tier_note = "申請韓國姊妹校建議達 TOPIK 2–3 級以上或以英語 CEFR B1（TOEIC 550 / TOEFL iBT 42 / IELTS 4.0）申請"
        return (
            "pass" if passed else "fail",
            f"TOPIK {level} 級{'符合' if passed else '未達'}國立屏東大學韓國姊妹校交換韓語基準（{tier_note}）。",
        )
    return (
        "needs_confirmation",
        f"已填報語言檢定 {language_test}（{language_score:g}）；請對照《國立屏東大學出國交換甄選簡章》（非日語組 CEFR B1：TOEIC 550 / TOEFL iBT 42 / ITP 460 / IELTS 4.0 / GEPT 中級；日語組 JLPT N2 或非日語 B1＋《日本語力評價表》）確認目標姊妹校語言門檻。",
    )
