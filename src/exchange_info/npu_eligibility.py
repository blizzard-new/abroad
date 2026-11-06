"""National Penghu University of Science and Technology (國立澎湖科技大學, NPU) outbound exchange, dual-degree & Xuehai eligibility checks.

Official rule sources:
- 國立澎湖科技大學交換學生赴國外（含大陸地區）姊妹校就讀選薦辦法（108年9月19日行政會議修正通過）:
  https://www.npu.edu.tw/df_ufiles/083/國立澎湖科技大學交換學生赴國外（含大陸地區）姊妹校就讀選薦辦法1080919.pdf
- 國立澎湖科技大學辦理教育部鼓勵大專校院選送學生出國研修（學海飛颺、學海惜珠）審查要點（115年3月19日行政會議通過、115年3月25日校務基金管理委員會議通過）:
  https://www.npu.edu.tw/df_ufiles/083/1150325國立澎湖科技大學辦理教育部鼓勵大專校院選送學生出國研修(學海飛颺、學海惜珠)審查要點(過校務基金委員會).pdf
- 國立澎湖科技大學辦理教育部鼓勵大專校院選送學生國外專業實習（學海築夢、新南向學海築夢）審查要點（115年3月19日行政會議通過、115年3月25日校務基金管理委員會議通過）:
  https://www.npu.edu.tw/df_ufiles/083/1150325國立澎湖科技大學辦理教育部鼓勵大專校院選送學生國外專業實習(學海築夢、新南向學海築夢)審查要點(過校務基金管理委員會).pdf
- 國立澎湖科技大學獎助學生境外研修及參訪辦法（108年12月19日行政會議修正通過）:
  https://www.npu.edu.tw/df_ufiles/083/國立澎湖科技大學獎助學生境外研修及參訪辦法(含表格).pdf
- 國立澎湖科技大學辦理雙聯學制實施辦法（104年4月15日校務會議修正通過、教育部臺教技(四)字第1040166534號函備查）:
  https://www.npu.edu.tw/df_ufiles/262/國立澎湖科技大學辦理雙聯學制實施辦法(1041103教務會議修正通過).pdf
"""

from __future__ import annotations

import re

from .university_registry import NPU, resolve_university

NPU_RD_INTL_URL = "https://www.npu.edu.tw/submenu.aspx?id=271"
NPU_OUTBOUND_EXCHANGE_URL = "https://www.npu.edu.tw/content.aspx?id=273"
NPU_SISTER_SCHOOLS_URL = "https://www.npu.edu.tw/content.aspx?id=271"
NPU_OUTBOUND_REGULATION_URL = "https://www.npu.edu.tw/df_ufiles/083/國立澎湖科技大學交換學生赴國外（含大陸地區）姊妹校就讀選薦辦法1080919.pdf"
NPU_XUEHAI_FEIYANG_URL = "https://www.npu.edu.tw/df_ufiles/083/1150325國立澎湖科技大學辦理教育部鼓勵大專校院選送學生出國研修(學海飛颺、學海惜珠)審查要點(過校務基金委員會).pdf"
NPU_XUEHAI_ZHUMENG_URL = "https://www.npu.edu.tw/df_ufiles/083/1150325國立澎湖科技大學辦理教育部鼓勵大專校院選送學生國外專業實習(學海築夢、新南向學海築夢)審查要點(過校務基金管理委員會).pdf"
NPU_OVERSEAS_GRANT_URL = "https://www.npu.edu.tw/df_ufiles/083/國立澎湖科技大學獎助學生境外研修及參訪辦法(含表格).pdf"
NPU_DUAL_DEGREE_REGULATION_URL = "https://www.npu.edu.tw/df_ufiles/262/國立澎湖科技大學辦理雙聯學制實施辦法(1041103教務會議修正通過).pdf"

NPU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 42.0),
    "ielts": ("IELTS", 4.0),
    "toefl_itp": ("TOEFL ITP/PBT", 457.0),
    "toeic": ("TOEIC", 550.0),
    "duolingo": ("Duolingo English Test", 75.0),
}


def is_npu(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == NPU.id:
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "npu",
        "國立澎湖科技大學",
        "澎湖科技大學",
        "澎科大",
        "澎湖科大",
        "national penghu university of science and technology",
    }


def _is_graduate(degree_level: str | None) -> bool:
    text = (degree_level or "").strip()
    return any(token in text for token in ("碩", "博", "研究", "master", "phd", "doctoral"))


def npu_degree_check(
    degree_level: str | None, current_year: str | int | None = None
) -> tuple[str, str]:
    degree = (degree_level or "").strip()
    year = str(current_year or "").strip()
    if not degree:
        return (
            "needs_confirmation",
            (
                "尚未提供目前學制與年級；依《國立澎湖科技大學交換學生赴國外（含大陸地區）姊妹校就讀選薦辦法》及《辦理教育部鼓勵大專校院選送學生出國研修（學海飛颺、學海惜珠）審查要點》第 4 點：申請對象為國立澎湖科技大學已就讀一學期以上且非當學期畢業之在學學生（不含國內及境外在職專班生；五專部須為四年級或五年級在學學生）。"
            ),
        )
    if any(
        token in degree or token in year
        for token in ("在職專班", "碩專", "emba", "EMBA", "學分班", "選修生", "休學", "專一", "專二", "專三")
    ):
        return (
            "fail",
            (
                f"已填報 {degree}{f'（{year}）' if year else ''}；依《國立澎湖科技大學辦理教育部鼓勵大專校院選送學生出國研修（學海飛颺、學海惜珠）審查要點》第 4 點及交換生選薦規定，在職專班生、休學生、五專一至三年級或不具正式一般生學籍者不在校級出國交換與學海系列獎助申請範圍內（五專部限專四或專五學生申請）。"
            ),
        )
    is_grad = _is_graduate(degree)
    if not is_grad and year in {"4", "大四", "大四下", "四年級下學期", "應屆畢業", "延修"}:
        return (
            "needs_confirmation",
            (
                f"已填報 {degree}（{year}）；依國立澎湖科技大學交換生選薦辦法與學海計畫審查要點規定，申請人須為「非當學期畢業之在學學生」，且交換期間仍應辦理本校註冊手續並繳交全額學雜費（《獎助學生境外研修及參訪辦法》另規定延長修業生除外），大四學生如擬申請須確認非當學期畢業並經系所及研發處核可。"
            ),
        )
    grad_note = (
        "（提醒：碩士班學生申請出國交換或雙聯學位須於本校修業滿一學期以上，並經指導教授及系所課程委員會／系務會議同意；修讀碩士雙聯學制者在兩校累計修業時間至少須滿 12 個月）"
        if is_grad
        else "（提醒：大學部四技、二技及五專專四／專五學生申請時須已就讀滿一學期以上，修業年限內限申請交換一次；修讀美國匹茲堡州立大學 2+2、越南孫德勝大學或泰國湄州大學學士雙聯學位者，於兩校累計修業時間至少須滿 32 個月）"
    )
    return (
        "pass",
        f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合國立澎湖科技大學出國交換學生選薦、雙聯學制與教育部學海計畫之在學學籍規定{grad_note}。",
    )


def npu_academic_check(
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
                "尚未填寫歷年學業平均成績、GPA 或班排名百分比；依《國立澎湖科技大學交換學生赴國外（含大陸地區）姊妹校就讀選薦辦法》第 4 條：（1）校內選薦審查標準為「在校成績 40%、語文能力 40%、讀書計畫 20%」，總評分在 70 分（含）以上者始得推薦（建議歷年學業平均達 70 分 / GPA 2.5 以上）；（2）申請教育部《學海築夢／新南向學海築夢》海外專業實習者歷年操行成績總平均須達 80 分以上；（3）申請泰國朱拉隆功大學、大陸中國海洋大學及爭取教育部《學海飛颺／學海惜珠》高額獎學金（NT$ 50,000–300,000）建議歷年平均達 75～80 分（GPA 2.75～3.0）以上。"
            ),
        )

    if passes_general:
        tier_notes: list[str] = []
        if passes_high_tier:
            tier_notes.append(
                "同時達到美國匹茲堡州立大學 2+2 雙聯、馬來西亞拉曼大學（UTAR）、泰國朱拉隆功大學、大陸中國海洋大學／上海海洋大學，以及教育部《學海飛颺／學海惜珠》與《獎助學生境外研修及參訪辦法》之優良學業水準（申請學海築夢實習另須歷年操行平均 80 分以上）"
            )
        else:
            tier_notes.append(
                "符合國立澎湖科技大學交換生選薦基礎學業門檻（總評分 70 分 / GPA 2.5 以上）；惟申請泰國朱拉隆功大學、大陸中國海洋大學或爭取教育部學海飛颺高額獎助金建議達 GPA 2.75～3.0（約 75～80 分）以上"
            )
        return (
            "pass",
            f"已填報 {summary}；符合國立澎湖科技大學出國交換選薦與雙聯學位學業標準（{'；'.join(tier_notes)}）。",
        )

    return (
        "fail" if (academic_score is not None and academic_score < 70.0) else "needs_confirmation",
        (
            f"已填報 {summary}；依《國立澎湖科技大學交換學生赴國外（含大陸地區）姊妹校就讀選薦辦法》第 4 條，研究發展處學術合作審查小組依「在校成績 40%、語文能力 40%、讀書計畫 20%」評分，總分須達 70 分（含）以上始得推薦（馬來西亞拉曼大學與美國匹茲堡州立大學另要求 CGPA 2.5 以上）。"
        ),
    )


def npu_language_check(
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
                "申請赴大陸地區姊妹校（中國海洋大學、上海海洋大學、集美大學、浙江海洋大學、汕頭大學、龍岩學院、浙江越秀外國語學院、黎明職業大學、廣州航海學院、深圳職業技術大學等）交換以中文授課為主，依《國立澎湖科技大學交換學生赴國外（含大陸地區）姊妹校就讀選薦辦法》第 3 條第 6 款規定免附語言能力證明。"
            ),
        )
    if not test or language_score is None:
        return (
            "needs_confirmation",
            (
                "尚未填寫外語能力檢定成績。依《國立澎湖科技大學辦理教育部鼓勵大專校院選送學生出國研修（學海飛颺、學海惜珠）審查要點（115.03.25通過）》第 4 點第 3 款及各姊妹校簡章：（1）校內自訂英文基準（擇一）：TOEIC 550 分以上、IELTS 4.0 分以上（且單項均至少 4.0 分）、TOEFL ITP 457 分以上（約 TOEFL iBT 42），適用於馬來西亞拉曼大學（UTAR）、越南峴港大學、越南孫德勝大學（雙聯／交換）、泰國湄州大學（雙聯／交換）、菲律賓甲米地州立大學及日本琉球大學國際交換學程；（2）歐美與頂尖學府英語門檻：美國匹茲堡州立大學（2+2 雙聯／交換）要求 TOEFL iBT 68（ITP 520）/ IELTS 6.0 / TOEIC 650（未達可先修 IEP 密集英語），瑞士教育集團（SEG）要求 IELTS 5.0–5.5 / TOEIC 550，泰國朱拉隆功大學要求 TOEFL iBT 79 / IELTS 6.0（或依學院協定採計 TOEIC 550）；（3）校內自訂日文基準（擇一）：日本語能力試驗 JLPT N4 及格、J.TEST E 級（日本琉球大學與長崎大學日語授課本科系要求 JLPT N2）；（4）大陸地區姊妹校免附語檢證明；（5）教育部學海築夢／新南向學海築夢海外專業實習要求新制 TOEIC 400 分以上、GEPT 中級或 JLPT N4 以上。"
            ),
        )
    if test in NPU_ENGLISH_MINIMUMS:
        label, minimum = NPU_ENGLISH_MINIMUMS[test]
        passed = language_score >= minimum
        tier_note = "達國立澎湖科技大學校內交換暨教育部學海飛颺／惜珠英語基準（TOEIC 550 / IELTS 4.0 / TOEFL ITP 457 / iBT 42），可申請馬來西亞拉曼大學、越南峴港大學、孫德勝大學、泰國湄州大學、菲律賓甲米地州立大學及日本琉球大學英語交換學程"
        if (
            (test == "toefl" and language_score >= 68)
            or (test == "ielts" and language_score >= 6.0)
            or (test == "toefl_itp" and language_score >= 520)
            or (test == "toeic" and language_score >= 650)
            or (test == "duolingo" and language_score >= 95)
        ):
            tier_note = "達美國匹茲堡州立大學（Pittsburg State University 2+2 雙聯與交換直入門檻）、泰國朱拉隆功大學、瑞士教育集團（SEG）、馬來西亞拉曼大學（UTAR）及教育部學海飛颺最高英語門檻"
        return (
            "pass" if passed else "fail",
            f"{label} {language_score:g} {'符合' if passed else '未達'}國立澎湖科技大學出國交換、雙聯學位與教育部學海飛颺英語檢定基準（最低採計門檻：{label} {minimum:g}；{tier_note}）。",
        )
    if test == "jlpt":
        level = int(language_score)
        passed = 1 <= level <= 4
        if level in {1, 2}:
            tier_note = f"JLPT N{level} 符合日本國立琉球大學、長崎大學全部日語授課本科學系及教育部學海飛颺最高日語門檻"
        elif level in {3, 4}:
            tier_note = f"JLPT N{level} 符合《國立澎湖科技大學辦理教育部學海飛颺、學海惜珠審查要點》第 4 點校內日語基準（JLPT N4 及格）與日本琉球大學國際交換／日語研修課程門檻（惟修讀日本姊妹校一般日語授課專業學系多要求 JLPT N2 以上）"
        else:
            tier_note = "國立澎湖科技大學校內出國交換與學海飛颺日語基準要求 JLPT N4（含）以上（本科專業課程要求 N2 以上）"
        return (
            "pass" if passed else "fail",
            f"JLPT N{level} {'符合' if passed else '未達'}國立澎湖科技大學日本姊妹校交換與學海飛颺日語檢定基準（{tier_note}）。",
        )
    return (
        "needs_confirmation",
        f"已填報語言檢定 {language_test}（{language_score:g}）；請對照國立澎湖科技大學《交換學生赴國外（含大陸地區）姊妹校就讀選薦辦法》與《學海飛颺、學海惜珠審查要點》（英文 TOEIC 550 / IELTS 4.0 / TOEFL ITP 457 / iBT 42、日文 JLPT N4 / J.TEST E 級、學海築夢 TOEIC 400）確認目標姊妹校語言門檻。",
    )
