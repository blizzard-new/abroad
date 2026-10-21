from __future__ import annotations

import re

from .university_registry import KMU, resolve_university

KMU_OIA_ZH_HOME_URL = "https://ciae2.kmu.edu.tw/index.php/zh-tw"
KMU_OIA_EN_HOME_URL = "https://ciae2.kmu.edu.tw/index.php/en-gb"
KMU_PARTNERS_ZH_URL = "https://ciae2.kmu.edu.tw/index.php/zh-tw/%E5%9C%8B%E9%9A%9B%E5%90%88%E4%BD%9C/%E5%A7%8A%E5%A6%B9%E6%A0%A1%E7%B7%A0%E7%B4%84%E6%83%85%E5%BD%A2"
KMU_PARTNERS_EN_URL = "https://ciae2.kmu.edu.tw/index.php/en-gb/global-network/partner-institutions"
KMU_DUAL_PARTNERS_URL = "https://ciae2.kmu.edu.tw/index.php/zh-tw/%E5%AD%B8%E7%94%9F%E4%BA%A4%E6%B5%81/%E5%87%BA%E5%9C%8B%E7%A0%94%E7%BF%92%E8%88%87%E7%8D%8E%E5%AD%B8%E9%87%91/%E9%9B%99%E8%81%AF%E5%AD%B8%E5%88%B6"
KMU_JUNTENDO_EXCHANGE_URL = "https://ciae2.kmu.edu.tw/index.php/zh-tw/%E6%9C%80%E6%96%B0%E6%B6%88%E6%81%AF/%E5%85%AC%E5%91%8A%E8%A8%8A%E6%81%AF/2997"
KMU_SUBSIDY_STD_URL = "https://ciae2.kmu.edu.tw/index.php/zh-tw/%E5%AD%B8%E7%94%9F%E4%BA%A4%E6%B5%81/%E5%87%BA%E5%9C%8B%E7%A0%94%E7%BF%92%E8%88%87%E7%8D%8E%E5%AD%B8%E9%87%91/2541"
KMU_XUEHAI_URL = "https://ciae2.kmu.edu.tw/index.php/zh-tw/%E5%AD%B8%E7%94%9F%E4%BA%A4%E6%B5%81/%E5%87%BA%E5%9C%8B%E7%A0%94%E7%BF%92%E8%88%87%E7%8D%8E%E5%AD%B8%E9%87%91/%E5%AD%B8%E6%B5%B7%E7%B3%BB%E5%88%97%E8%A3%9C%E5%8A%A9"
KMU_QIANLIMA_115_URL = "https://ciae2.kmu.edu.tw/index.php/zh-tw/%E6%9C%80%E6%96%B0%E6%B6%88%E6%81%AF/%E5%85%AC%E5%91%8A%E8%A8%8A%E6%81%AF/3221"
KMU_NA_ALUMNI_2026_URL = "https://ciae2.kmu.edu.tw/index.php/zh-tw/%E6%9C%80%E6%96%B0%E6%B6%88%E6%81%AF/%E5%85%AC%E5%91%8A%E8%A8%8A%E6%81%AF/3153"
KMU_REG_INTL_REWARD_PDF_URL = "https://ciae2.kmu.edu.tw/images/files/StudentMobility/%E9%AB%98%E9%9B%84%E9%86%AB%E5%AD%B8%E5%A4%A7%E5%AD%B8%E5%AD%B8%E7%94%9F%E5%9C%8B%E9%9A%9B%E7%A0%94%E7%BF%92%E6%9C%8D%E5%8B%99%E7%8D%8E%E5%8B%B5%E8%A6%81%E9%BB%9E.pdf"
KMU_CMED_2027_NOTICE_URL = "https://cmed.kmu.edu.tw/p/406-1010-29601,r11.php?Lang=zh-tw"
KMU_CMED_2027_SHEET_URL = "https://docs.google.com/spreadsheets/d/1q7mAzXMyCslEwZCuoieUl1ldiXAb6zJtU2YBcgco2KY/edit?usp=sharing"
KMU_DENT_363_URL = "https://dent.kmu.edu.tw/p/412-1084-363.php?Lang=zh-tw"

KMU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 57.0),
    "ielts": ("IELTS", 5.0),
    "toeic": ("TOEIC", 550.0),
}


def is_kmu(school_name: str | None) -> bool:
  school = resolve_university(school_name)
  if school is not None and school.id == KMU.id:
    return True
  normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
  return normalized in {
      "高雄醫學大學",
      "高醫大",
      "高醫",
      "高雄醫大",
      "kmu",
      "kaohsiung medical university",
  }


def _is_graduate(degree_level: str | None) -> bool:
  text = (degree_level or "").strip()
  return any(token in text for token in ("碩", "博", "研究"))


def kmu_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
  degree = (degree_level or "").strip()
  year = (current_year or "").strip()
  if not degree:
    return (
        "needs_confirmation",
        (
            "尚未提供目前學制與年級；依《高雄醫學大學學海系列方案甄選及補助辦法》及《學生國際研習服務獎勵要點》規定：申請人須為本校 7 大學院具正式學籍之在學學生（休學生、在職專班生不得申請校內與學海補助；醫學院與各學院海外臨床見實習依各系所規定年級開放）。"
        ),
    )
  if any(
      token in degree or token in year
      for token in ("學分班", "選修生", "休學", "延畢", "延修", "在職")
  ):
    return (
        "fail",
        (
            f"已填報 {degree}{f'（{year}）' if year else ''}；依《高雄醫學大學學海系列方案甄選及補助辦法》及《學生國際研習服務獎勵要點》規定，休學生、延修生及在職專班生不得申請出國交換與校內出國研習實習補助。"
        ),
    )
  is_grad = _is_graduate(degree)
  if not is_grad and year in {"大一上"}:
    return (
        "fail",
        (
            f"已填報 {degree}（{year}）；申請高醫大出國交換、學海系列計畫與海外臨床見實習須檢附至少前一學期在學成績單，大一上新生尚無完整學期成績可供審查。"
        ),
    )
  return (
      "pass",
      (
          f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合高雄醫學大學校級出國交換（日本順天堂大學）、10 校跨國雙聯學位（烏普薩拉、賽蓋德、UCI、City of Hope、艾克斯-馬賽、格里菲斯、熊本、朱拉隆功、瑪希朵、清邁）、醫學院 2027（21 校 64+ 名）海外臨床見實習及各學院海外見實習之在學學籍規定。"
      ),
  )


def kmu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
  is_grad = _is_graduate(degree_level)
  min_pass_score = 70.0 if is_grad else 60.0
  dental_score = 75.0
  emi_score = 80.0
  dual_gpa = 3.0
  details: list[str] = []
  passes_emi_or_dual = False
  passes_dental = False
  passes_basic = False

  if academic_score is not None:
    details.append(f"學業平均 {academic_score:g} 分")
    if academic_score >= emi_score:
      passes_emi_or_dual = True
      passes_dental = True
      passes_basic = True
    elif academic_score >= dental_score:
      passes_dental = True
      passes_basic = True
    elif academic_score >= min_pass_score:
      passes_basic = True
  if academic_gpa is not None:
    details.append(f"GPA {academic_gpa:g}")
    if academic_gpa >= dual_gpa:
      passes_emi_or_dual = True
      passes_dental = True
      passes_basic = True
    elif academic_gpa >= 2.0:
      passes_basic = True
  if class_rank_percent is not None:
    details.append(f"系所／班級排名前 {class_rank_percent:g}%")
    if class_rank_percent <= 30.0:
      passes_emi_or_dual = True
      passes_dental = True
      passes_basic = True
    elif class_rank_percent <= 75.0:
      passes_dental = True
      passes_basic = True

  summary = "、".join(details)
  if academic_score is None and academic_gpa is None and class_rank_percent is None:
    return (
        "needs_confirmation",
        (
            "尚未填寫學業平均、GPA 或系所排名；依高醫大規定：（1）一般出國研習與教育部學海計畫須前一學期學業成績總平均及格（60 分以上）且無不及格科目；（2）口腔醫學院牙醫學系海外見實習須歷年平均 75 分以上且班排前 75%；（3）跨國雙聯博士與 115 千里馬計畫須 GPA 3.0（75–80 分）以上；（4）醫學院雙語計畫（EMI）海外實習高額補助須歷年平均 80 分以上。"
        ),
    )

  if passes_emi_or_dual:
    return (
        "pass",
        (
            f"已填報 {summary}；符合高雄醫學大學最高階出國甄選標準（含醫學院 2027［21 校 64+ 名］海外臨床見實習、醫學院雙語計畫 EMI 高額補助 80 分門檻、10 校跨國雙聯學位與 115 千里馬博士生計畫 GPA 3.0 門檻、牙醫學系海外見實習 75 分與班排前 75% 門檻，以及國際事務處出國研習補助與教育部學海計畫）。"
        ),
    )

  if passes_dental:
    return (
        "pass",
        (
            f"已填報 {summary}；符合高雄醫學大學《國際事務處補助學生出國研習標準》、《學海系列方案甄選及補助辦法》、校級日本順天堂大學交換、醫學院 2027 海外臨床見實習及口腔醫學院牙醫學系海外見實習（75 分以上且班排前 75%）之學業門檻（若欲申請醫學院雙語計畫 EMI 全額補助須達 80 分以上）。"
        ),
    )

  if passes_basic:
    return (
        "pass",
        (
            f"已填報 {summary}；符合《高雄醫學大學學海系列方案甄選及補助辦法》與《學生國際研習服務獎勵要點》基本及格門檻（60 分 / GPA 2.0 以上；提醒：若申請牙醫學系海外見實習須達 75 分且班排前 75%，申請跨國雙聯博士須達 GPA 3.0，申請醫學院雙語計畫 EMI 補助須達 80 分）。"
        ),
    )

  return (
      "fail",
      (
          f"已填報 {summary}；未達高雄醫學大學出國交換、跨國雙聯學位與海外臨床見實習之學業及格基準（大學部 60 分 / 研究所 70 分 / GPA 2.0）。"
      ),
  )


def kmu_language_check(
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
            f"申請赴{partner_country}合作姊妹校交流以中文授課為主（提醒：若欲申請校內出國研習補助或歐美亞英語系計畫，仍須具備有效外語檢定證明）。"
        ),
    )
  if not test or language_score is None:
    return (
        "needs_confirmation",
        (
            "尚未填寫外語檢定成績。依高雄醫學大學規定：（1）一般交換、學海計畫與國際處出國研習補助須具 CEFR B1–B2 以上證明（TOEFL iBT 57 / IELTS 5.0 / TOEIC 550 / GEPT 中級）；（2）美國哈佛醫學院（HMS 6 名）須達 TOEFL iBT 100；（3）德國科隆大學（4 名）須達英語 C1（iBT 95 / IELTS 7.0 / TOEIC 945）或德語 B2；（4）澳洲邦德大學（4 名）與瑞典烏普薩拉大學雙聯（6 名）須達 TOEFL iBT 79 / IELTS 6.0–6.5；（5）日本順天堂大學 LAP 交換須達 JLPT N2 或 TOEFL iBT 72 / IELTS 5.5。"
        ),
    )
  if test in KMU_ENGLISH_MINIMUMS:
    label, minimum = KMU_ENGLISH_MINIMUMS[test]
    passed = language_score >= minimum
    adv_note = "符合高醫大一般出國交換、教育部學海計畫與國際處出國研習補助基本英語門檻（TOEFL iBT 57 / IELTS 5.0 / TOEIC 550）"
    if test == "toefl" and language_score >= 100:
      adv_note = "符合高雄醫學大學全部 188 所合作校院與最高階臨床見實習英語標準（含美國哈佛醫學院 HMS 臨床見習 TOEFL iBT 100、德國科隆大學英語 C1、澳洲邦德大學、瑞典烏普薩拉大學與匈牙利賽蓋德大學雙聯及全部歐美亞教學醫院見實習）"
    elif (
        (test == "toefl" and language_score >= 95)
        or (test == "ielts" and language_score >= 7.0)
        or (test == "toeic" and language_score >= 945)
    ):
      adv_note = "符合德國科隆大學醫學院臨床見習（英語 CEFR C1）、澳洲邦德大學、瑞典烏普薩拉大學雙聯、美國 City of Hope / 羅格斯 / 梅哈里 / 夏威夷大學 / 約翰霍普金斯 / 南加大 USC 等絕大多數歐美亞臨床見實習門檻（僅哈佛醫學院要求 TOEFL iBT 100）"
    elif (
        (test == "toefl" and language_score >= 79)
        or (test == "ielts" and language_score >= 6.0)
        or (test == "toeic" and language_score >= 785)
    ):
      adv_note = "符合瑞典烏普薩拉大學雙聯交換（iBT 79 / IELTS 6.0）、澳洲邦德大學臨床見習（CEFR B2）、日本順天堂大學 LAP 交換（iBT 72 / IELTS 5.5）、泰國朱拉隆功大學雙聯博士（iBT 65 / IELTS 5.5）及多數臨床見實習門檻"
    elif (
        (test == "toefl" and language_score >= 65)
        or (test == "ielts" and language_score >= 5.5)
        or (test == "toeic" and language_score >= 650)
    ):
      adv_note = "符合泰國朱拉隆功大學藥學雙聯博士（iBT 65 / IELTS 5.5）、日本順天堂大學交換（IELTS 5.5）及校內出國研習補助門檻"
    return (
        "pass" if passed else "fail",
        (
            f"{label} {language_score:g} {'符合' if passed else '未達'}高雄醫學大學出國交換、跨國雙聯學位與海外臨床見實習英語標準（基準：{label} {minimum:g}；{adv_note}）。"
        ),
    )
  if test == "jlpt":
    level = int(language_score)
    passed = level in (1, 2, 3, 4)
    tier_note = (
        "符合日本順天堂大學 LAP 國際教養課程交換（JLPT N2）、京都大學、慶應義塾大學、東京醫科大學、東京科學大學（TMDU）、東北大學、廣島大學、神戶大學、熊本大學、日本藥科大學、聖路加國際大學等全部日本合作姊妹校日語標準"
        if level in (1, 2)
        else (
            "符合日本順天堂大學 JLCSP 日語文化學程交換及日本各大學附設醫院短期臨床見實習日語基準（若申請順天堂大學 LAP 專業學部課程須達 JLPT N2 或 TOEFL iBT 72 / IELTS 5.5）"
            if level in (3, 4)
            else "未達高醫大日本合作姊妹校 JLPT 日語檢定門檻"
        )
    )
    return (
        "pass" if passed else "fail",
        f"JLPT N{level} {'符合' if passed else '未達'}高雄醫學大學日本合作姊妹校日語檢定要求（{tier_note}）。",
    )
  if test == "topik":
    level = int(language_score)
    passed = 2 <= level <= 6
    return (
        "pass" if passed else "fail",
        f"TOPIK {level} 級{'符合' if passed else '未達'}高雄醫學大學韓國合作姊妹校（首爾大學、高麗大學、亞洲大學、釜山大學、全北大學、嘉泉大學）韓語檢定基準。",
    )
  if test in {"gept", "bestep", "delf", "dalf", "tcf", "cefr"}:
    passed = language_score >= 1
    return (
        "pass" if passed else "fail",
        "已填報全民英檢 GEPT／培力英檢 BESTEP／歐洲語言檢定成績；依高醫大規定，GEPT 中級至中高級或 BESTEP B1–B2 符合出國研習補助與學海計畫門檻（德國科隆大學臨床見習採認德語 B2 或英語 C1）。",
    )
  return (
      "needs_confirmation",
      f"已填報語言檢定 {language_test}（{language_score:g}）；請對照高雄醫學大學國際事務處與各學院海外見實習簡章確認是否符合指定外語標準。",
  )
