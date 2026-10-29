from __future__ import annotations

import re

from .university_registry import CMU, resolve_university

CMU_OIA_ZH_HOME_URL = "https://cmucia.cmu.edu.tw/"
CMU_OIA_EN_HOME_URL = "https://cmucia.cmu.edu.tw/english/"
CMU_PARTNERS_ZH_URL = "https://cmucia.cmu.edu.tw/a_partner.php"
CMU_PARTNERS_EN_URL = "https://cmucia.cmu.edu.tw/english/a_partner.php"
CMU_OUTBOUND_EXCHANGE_URL = "https://cmucia.cmu.edu.tw/s_exchange.html"
CMU_OUTBOUND_FORMS_URL = "https://cmucia.cmu.edu.tw/download.php"
CMU_NEWS_JAPAN_EXCHANGE_URL = "https://cmucia.cmu.edu.tw/doc/202212281100421.pdf"
CMU_JAPAN_2024_BRIEFING_PDF_URL = "https://cmucia.cmu.edu.tw/doc/202212281100421.pdf"
CMU_EDUHK_AGREEMENT_PDF_URL = "https://cmucia.cmu.edu.tw/upfiles/partner/1480909692_1.pdf"

CMU_STATUTE_EXCHANGE_622_URL = "https://www.cmu.edu.tw/statute/statute_detail.php?sn=622"
CMU_STATUTE_SUBSIDY_342_URL = "https://www.cmu.edu.tw/statute/statute_detail.php?sn=342"
CMU_STATUTE_CREDIT_337_URL = "https://www.cmu.edu.tw/statute/statute_detail.php?sn=66"
CMU_STATUTE_DUAL_647_URL = "https://www.cmu.edu.tw/statute/statute_detail.php?sn=616"
CMU_STATUTE_USC_PHARM_1566_URL = "https://www.cmu.edu.tw/statute/statute_detail.php?sn=1566"
CMU_STATUTE_USC_KECK_917_URL = "https://www.cmu.edu.tw/statute/statute_detail.php?sn=917"
CMU_STATUTE_SC_3PLUS2_1268_URL = "https://www.cmu.edu.tw/statute/statute_detail.php?sn=1268"
CMU_STATUTE_SC_DUAL_1267_URL = "https://www.cmu.edu.tw/statute/statute_detail.php?sn=1267"
CMU_STATUTE_GSU_846_URL = "https://www.cmu.edu.tw/statute/statute_detail.php?sn=846"
CMU_STATUTE_TULANE_848_URL = "https://www.cmu.edu.tw/statute/statute_detail.php?sn=848"
CMU_STATUTE_SDSU_1085_URL = "https://www.cmu.edu.tw/statute/statute_detail.php?sn=1085"
CMU_STATUTE_GRIFFITH_1459_URL = "https://www.cmu.edu.tw/statute/statute_detail.php?sn=1459"
CMU_STATUTE_NEWCASTLE_1222_URL = "https://www.cmu.edu.tw/statute/statute_detail.php?sn=1222"

CMU_PT_115_1_INTERNSHIP_URL = "https://cmupt.cmu.edu.tw/news/753"
CMU_MED_CLERKSHIP_URL = "https://med.cmu.edu.tw/page/international"
CMU_NURSING_INTL_URL = "https://cmunur.cmu.edu.tw/page/41"
CMU_CHMED_INTL_URL = "https://chmed.cmu.edu.tw/news/category/6"

CMU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 57.0),
    "ielts": ("IELTS", 4.0),
    "toeic": ("TOEIC", 550.0),
}


def is_cmu(school_name: str | None) -> bool:
  school = resolve_university(school_name)
  if school is not None and school.id == CMU.id:
    return True
  normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
  return normalized in {
      "中國醫藥大學",
      "中醫大",
      "中國醫大",
      "中國醫",
      "cmu",
      "china medical university",
  }


def _is_graduate(degree_level: str | None) -> bool:
  text = (degree_level or "").strip()
  return any(token in text for token in ("碩", "博", "研究"))


def cmu_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
  degree = (degree_level or "").strip()
  year = (current_year or "").strip()
  if not degree:
    return (
        "needs_confirmation",
        (
            "尚未提供目前學制與年級；依《中國醫藥大學學生出國交換實施要點》（法規編號 622）及《中國醫藥大學補助學生出國研習與實習辦法》（法規編號 342）規定：申請人須為本校 9 大學院具正式學籍之在學學生（一般出國交換須於本校修業滿一學年以上，申請日本北海道大學、北見工業大學交換及美國南達科塔州立大學 2+2 營養雙學士須修業滿兩學年以上；延修生、休學生、在職專班及在職生不得申請）。"
        ),
    )
  if any(
      token in degree or token in year
      for token in ("學分班", "選修生", "休學", "延畢", "延修", "在職")
  ):
    return (
        "fail",
        (
            f"已填報 {degree}{f'（{year}）' if year else ''}；依《中國醫藥大學學生出國交換實施要點》（法規編號 622）第3點規定，延修生、休學生、國內外在職專班及在職生不得申請出國交換與校內出國研習實習補助。"
        ),
    )
  is_grad = _is_graduate(degree)
  if not is_grad and year in {"大一上", "大一下"}:
    return (
        "fail",
        (
            f"已填報 {degree}（{year}）；依《中國醫藥大學學生出國交換實施要點》（法規編號 622）第3點規定，大學部學生須於本校修業滿一學年以上始得申請出國交換（日本北海道大學、北見工業大學及美國南達科塔州立大學 2+2 須修滿兩學年以上），大一學生尚不得提出申請。"
        ),
    )
  return (
      "pass",
      (
          f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合中國醫藥大學出國交換學生（日本北海道大學、北見工業大學、香港教育大學）、7 校 11 個跨國雙聯學位（南加州大學 USC、杜蘭大學、喬治亞州立大學、南卡羅萊納大學、南達科塔州立大學、格里菲斯大學、紐卡索大學）及海外臨床見實習之在學學籍規定。"
      ),
  )


def cmu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
  is_grad = _is_graduate(degree_level)
  min_pass_score = 70.0 if is_grad else 60.0
  target_score = 80.0
  target_gpa = 3.0
  pt_rank = 30.0
  details: list[str] = []
  passes_cmu_standard = False
  passes_pt_rank = False
  passes_basic = False

  if academic_score is not None:
    details.append(f"學業平均 {academic_score:g} 分")
    if academic_score >= target_score:
      passes_cmu_standard = True
      passes_basic = True
    elif academic_score >= min_pass_score:
      passes_basic = True
  if academic_gpa is not None:
    details.append(f"GPA {academic_gpa:g}")
    if academic_gpa >= target_gpa:
      passes_cmu_standard = True
      passes_basic = True
    elif academic_gpa >= 2.5:
      passes_basic = True
  if class_rank_percent is not None:
    details.append(f"系所／班級排名前 {class_rank_percent:g}%")
    if class_rank_percent <= pt_rank:
      passes_pt_rank = True
      passes_cmu_standard = True
      passes_basic = True
    elif class_rank_percent <= 40.0:
      passes_basic = True

  summary = "、".join(details)
  if academic_score is None and academic_gpa is None and class_rank_percent is None:
    return (
        "needs_confirmation",
        (
            "尚未填寫學業平均、GPA 或系所排名；依《中國醫藥大學學生出國交換實施要點》（法規編號 622）第3點、《補助學生出國研習與實習辦法》（法規編號 342）第3條及各校雙聯學位補助施行細則規定：申請人歷年學業成績平均須達等第制 A-（GPA 3.0 或百分制 80 分）以上，且前一學期操行成績須達 80 分以上（物理治療學系 115-1 海外臨床實習要求大學部前兩學年全班前 30% 或碩士班平均 80 分以上）。"
        ),
    )

  if passes_cmu_standard:
    pt_note = (
        "（且班排名前 30% 亦符合健康照護學院物理治療學系 115-1 赴新加坡中央醫院、日本神戶中央市民醫院、關西電力醫院、順天堂醫院海外臨床實習標準）"
        if passes_pt_rank
        else ""
    )
    return (
        "pass",
        (
            f"已填報 {summary}；符合中國醫藥大學《學生出國交換實施要點》、《補助學生出國研習與實習辦法》、日本北海道大學與北見工業大學交換（GPA 3.0+）及 7 校跨國雙聯學位獎助學金之學業門檻（等第制 A- / GPA 3.0 / 學業平均 80 分以上，請併同確認前一學期操行成績達 80 分以上）{pt_note}。"
        ),
    )

  if passes_basic:
    return (
        "needs_confirmation",
        (
            f"已填報 {summary}；未達中國醫藥大學校級出國交換、跨國雙聯學位與《補助學生出國研習與實習辦法》之法定學業門檻（等第制 A- / GPA 3.0 / 學業平均 80 分以上，或物治系海外實習班排前 30%），惟得洽詢所屬學院自費短期研習或教育部學海築夢計畫。"
        ),
    )

  return (
      "fail",
      (
          f"已填報 {summary}；未達中國醫藥大學出國交換、跨國雙聯學位與海外研習實習學業基準（等第制 A- / GPA 3.0 / 學業平均 80 分 / 班排前 30%）。"
      ),
  )


def cmu_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
  test = (language_test or "").strip().lower()
  if partner_country in {"中國大陸", "澳門"} and (not test or language_score is None):
    return (
        "pass",
        (
            f"申請赴{partner_country}合作姊妹校或中醫藥教學醫院交流以中文授課為主（提醒：若欲申請《中國醫藥大學補助學生出國研習與實習辦法》經費補助，仍須具備 TOEFL iBT 59 / IELTS 5.0 / TOEIC 640 / GEPT 中高級初試 / BESTEP B1 或修畢 4 門全英語課程）。"
        ),
    )
  if not test or language_score is None:
    return (
        "needs_confirmation",
        (
            "尚未填寫外語檢定成績。依中國醫藥大學規定：（1）一般出國交換（法規編號 622）須達 TOEFL iBT 57 / IELTS 4.0 / TOEIC 550 / GEPT 中級 / BESTEP B1；（2）申請校內出國研習實習補助（法規編號 342）及日本北見工業大學交換須達 TOEFL iBT 59 / IELTS 5.0 / TOEIC 640 / GEPT 中高級初試 / BESTEP B1；（3）日本北海道大學 HUSTEP 交換須達 TOEFL iBT 79 / IELTS 6.5；（4）物理治療學系 115-1 海外臨床實習須達 TOEFL ITP 550 / iBT 61 / TOEIC 590 / IELTS 4.5；（5）跨國雙聯學位須達 TOEFL iBT 60–100 / IELTS 5.5–7.0。"
        ),
    )
  if test in CMU_ENGLISH_MINIMUMS:
    label, minimum = CMU_ENGLISH_MINIMUMS[test]
    passed = language_score >= minimum
    adv_note = "符合《中國醫藥大學學生出國交換實施要點》（法規編號 622）一般出國交換基本英語門檻（TOEFL iBT 57 / IELTS 4.0 / TOEIC 550）"
    if (test == "toefl" and language_score >= 100) or (
        test == "ielts" and language_score >= 7.0
    ):
      adv_note = "符合中國醫藥大學全部 174 所合作校院與最高階跨國雙聯學位英語標準（含美國南加州大學 USC 藥學系 MS in Regulatory Science 雙聯 iBT 100 / IELTS 7.0、USC 凱克醫學院 MD/MPH 雙聯 iBT 90 / IELTS 6.5、杜蘭大學與格里菲斯大學雙聯 iBT 80 / IELTS 6.5、日本北海道大學 HUSTEP iBT 79 / IELTS 6.5 及全部海外臨床實習）"
    elif (test == "toefl" and language_score >= 90) or (
        test == "ielts" and language_score >= 6.5
    ) or (test == "toeic" and language_score >= 800):
      adv_note = "符合美國南加州大學凱克醫學院 MD/MPH 雙聯（iBT 90 / IELTS 6.5）、杜蘭大學 MD/MPH 雙聯、澳洲格里菲斯大學雙聯、南卡羅萊納大學與喬治亞州立大學雙聯優先補助、澳洲紐卡索大學護理博士雙聯、日本北海道大學 HUSTEP 交換（iBT 79 / IELTS 6.5）及美國 MD Anderson / Emory 臨床見習門檻"
    elif (test == "toefl" and language_score >= 79) or (
        test == "ielts" and language_score >= 6.0
    ) or (test == "toeic" and language_score >= 750):
      adv_note = "符合日本北海道大學 HUSTEP 交換（iBT 79）、美國南卡羅萊納大學／喬治亞州立大學／南達科塔州立大學雙聯及校內出國研習實習補助門檻"
    elif (test == "toefl" and language_score >= 59) or (
        test == "ielts" and language_score >= 5.0
    ) or (test == "toeic" and language_score >= 640):
      adv_note = "符合《中國醫藥大學補助學生出國研習與實習辦法》（iBT 59 / IELTS 5.0 / TOEIC 640）、日本北見工業大學交換、物理治療學系 115-1 海外臨床實習及新南向學海築夢門檻"
    return (
        "pass" if passed else "fail",
        (
            f"{label} {language_score:g} {'符合' if passed else '未達'}中國醫藥大學出國交換、跨國雙聯學位與海外臨床實習英語標準（基準：{label} {minimum:g}；{adv_note}）。"
        ),
    )
  if test == "jlpt":
    level = int(language_score)
    passed = level in (1, 2, 3)
    tier_note = (
        "符合日本北海道大學日語授課交換、北見工業大學、順天堂大學、東京科學大學（TMDU）、日本藥科大學、鈴鹿醫療科學大學等全部日本合作姊妹校日語標準"
        if level in (1, 2)
        else (
            "符合日本北見工業大學交換及日本藥科大學、鈴鹿醫療科學大學、神戶中央市民醫院、關西電力醫院短期臨床見實習日語基準（若申請北海道大學日語授課專業課程建議達 JLPT N2 以上）"
            if level == 3
            else "未達中醫大日本合作姊妹校 JLPT N3–N2 日語檢定門檻"
        )
    )
    return (
        "pass" if passed else "fail",
        f"JLPT N{level} {'符合' if passed else '未達'}中國醫藥大學日本合作姊妹校日語檢定要求（{tier_note}）。",
    )
  if test == "topik":
    level = int(language_score)
    passed = 2 <= level <= 6
    return (
        "pass" if passed else "fail",
        f"TOPIK {level} 級{'符合' if passed else '未達'}中國醫藥大學韓國合作姊妹校（慶熙大學、東國大學、釜山大學、大邱韓醫大學、首爾大學、延世大學、漢陽大學）韓語檢定基準。",
    )
  if test in {"gept", "bestep", "delf", "dalf", "tcf", "cefr"}:
    passed = language_score >= 1
    return (
        "pass" if passed else "fail",
        "已填報全民英檢 GEPT／培力英檢 BESTEP／歐洲語言檢定成績；依中醫大法規，GEPT 中級或 BESTEP B1 符合一般交換與物治系海外實習門檻，GEPT 中高級初試或 BESTEP B1 符合《補助學生出國研習與實習辦法》門檻。",
    )
  return (
      "needs_confirmation",
      f"已填報語言檢定 {language_test}（{language_score:g}）；請對照中國醫藥大學《學生出國交換實施要點》、《補助學生出國研習與實習辦法》與各雙聯學位施行細則確認是否符合指定外語標準。",
  )
