from __future__ import annotations

import re

from .university_registry import TMU, resolve_university

TMU_OGE_ZH_HOME_URL = "https://oge.tmu.edu.tw/zh-hant/"
TMU_OGE_EN_HOME_URL = "https://oge.tmu.edu.tw/"
TMU_OUTBOUND_EXCHANGE_URL = "https://oge.tmu.edu.tw/zh-hant/%e5%ad%b8%e7%94%9f%e4%ba%a4%e6%b5%81/tmu-student-outbound-exchange/"
TMU_OUTBOUND_STUDENTS_EN_URL = "https://oge.tmu.edu.tw/international-mobility-2/outbound-students/"
TMU_DUAL_DEGREE_URL = "https://oge.tmu.edu.tw/zh-hant/%e5%ad%b8%e7%94%9f%e4%ba%a4%e6%b5%81/%e9%9b%99%e8%81%af%e5%ad%b8%e4%bd%8d-2/"
TMU_OVERSEAS_COURSES_URL = "https://oge.tmu.edu.tw/zh-hant/%e5%ad%b8%e7%94%9f%e4%ba%a4%e6%b5%81/%e6%b5%b7%e5%a4%96%e4%ba%a4%e6%b5%81/"
TMU_SCHOLARSHIPS_URL = "https://oge.tmu.edu.tw/zh-hant/%e5%ad%b8%e7%94%9f%e4%ba%a4%e6%b5%81/%e6%a0%a1%e5%85%a7%e5%a4%96%e7%8d%8e%e5%ad%b8%e9%87%91%e6%b5%81%e7%a8%8b/"
TMU_STUDENT_EXPERIENCES_URL = "https://oge.tmu.edu.tw/zh-hant/%e5%ad%b8%e7%94%9f%e4%ba%a4%e6%b5%81/%e5%ad%b8%e7%94%9f%e6%b5%b7%e5%a4%96%e4%ba%a4%e6%b5%81%e5%bf%83%e5%be%97%e5%88%86%e4%ba%ab/"
TMU_PARTNERS_LIST_ZH_URL = "https://oge.tmu.edu.tw/zh-hant/%e5%9c%8b%e9%9a%9b%e4%ba%a4%e6%b5%81/%e7%9b%9f%e6%a0%a1%e4%b8%80%e8%a6%bd/"
TMU_PARTNERS_LIST_EN_URL = "https://oge.tmu.edu.tw/international-mobility/partners-list/"
TMU_REGULATIONS_COOP_URL = "https://oge.tmu.edu.tw/zh-hant/%e6%b3%95%e8%a6%8f/%e5%9c%8b%e9%9a%9b%e4%ba%a4%e6%b5%81%e5%90%88%e4%bd%9c/"
TMU_115_XUEHAI_INFO_URL = "https://oge.tmu.edu.tw/zh-hant/115%e5%b9%b4%e6%95%99%e8%82%b2%e9%83%a8%e5%ad%b8%e6%b5%b7%e8%a8%88%e7%95%ab%e8%aa%aa%e6%98%8e%e6%9c%83/"
TMU_115_XUEHAI_BRIEFING_PDF_URL = "https://oge.tmu.edu.tw/wp-content/uploads/2025/11/2026%E6%B0%91%E5%9C%8B115%E5%B9%B4%E6%95%99%E8%82%B2%E9%83%A8%E5%AD%B8%E6%B5%B7%E8%A8%88%E7%95%AB%E7%8D%8E%E5%AD%B8%E9%87%91%E6%A0%A1%E5%85%A7%E8%AA%AA%E6%98%8E%E6%9C%83%E7%B0%A1%E5%A0%B1.pdf"
TMU_115_2_XUEHAI_XIZHU_PDF_URL = "https://oge.tmu.edu.tw/wp-content/uploads/2026/07/%E8%87%BA%E5%8C%97%E9%86%AB%E5%AD%B8%E5%A4%A7%E5%AD%B8%E3%80%8C115%E5%B9%B4%E5%BA%A6%E6%95%99%E8%82%B2%E9%83%A8%E5%AD%B8%E6%B5%B7%E6%83%9C%E7%8F%A0%E8%A8%88%E7%95%AB%E3%80%8D%E7%AC%AC%E4%BA%8C%E6%AC%A1%E7%94%B3%E8%AB%8B%E5%85%AC%E5%91%8A.pdf"
TMU_115_2_XUEHAI_ZHUMENG_PDF_URL = "https://oge.tmu.edu.tw/wp-content/uploads/2026/07/%E8%87%BA%E5%8C%97%E9%86%AB%E5%AD%B8%E5%A4%A7%E5%AD%B8%E3%80%8C115%E5%B9%B4%E5%BA%A6%E6%95%99%E8%82%B2%E9%83%A8%E5%AD%B8%E6%B5%B7%E7%AF%89%E5%A4%A2%E6%96%B0%E5%8D%97%E5%90%91%E7%AF%89%E5%A4%A2%E8%A8%88%E7%95%AB%E3%80%8D%E7%AC%AC%E4%BA%8C%E6%AC%A1%E7%94%B3%E8%AB%8B%E5%85%AC%E5%91%8A.pdf"
TMU_OVERSEAS_INCENTIVE_REGULATIONS_PDF_URL = "https://oge.tmu.edu.tw/wp-content/uploads/2022/05/%E8%87%BA%E5%8C%97%E9%86%AB%E5%AD%B8%E5%A4%A7%E5%AD%B8%E5%A2%83%E5%A4%96%E7%A0%94%E4%BF%AE%E6%9A%A8%E8%A6%8B%E5%AF%A6%E7%BF%92%E7%8D%8E%E5%8B%B5%E8%BE%A6%E6%B3%95.pdf"
TMU_OVERSEAS_INCENTIVE_APP_DOCX_URL = "https://oge.tmu.edu.tw/wp-content/uploads/2025/09/%E8%87%BA%E5%8C%97%E9%86%AB%E5%AD%B8%E5%A4%A7%E5%AD%B8%E5%A2%83%E5%A4%96%E7%A0%94%E4%BF%AE%E6%9A%A8%E8%A6%8B%E5%AF%A6%E7%BF%92%E7%8D%8E%E5%8B%B5%E8%BE%A6%E6%B3%95_%E9%99%84%E4%BB%B6%E5%8F%8A%E7%94%B3%E8%AB%8B%E8%A8%88%E5%8A%83%E6%9B%B8%E7%AF%84%E4%BE%8B_V6.docx"
TMU_PREDEPARTURE_FORM_PDF_URL = "https://oge.tmu.edu.tw/wp-content/uploads/2025/03/%E5%AD%B8%E7%94%9F%E6%B5%B7%E5%A4%96%E8%A1%8C%E5%89%8D%E5%A0%B1%E5%88%B0%E5%96%AE.pdf"
TMU_DUAL_DEGREE_FLOWCHART_PDF_URL = "https://oge.tmu.edu.tw/wp-content/uploads/2020/12/%E8%B7%A8%E5%9C%8B%E9%9B%99%E8%81%AF%E5%AD%B8%E5%88%B6%E6%B5%81%E7%A8%8B%E5%9C%96.pdf"
TMU_ACA_OVERSEAS_STUDY_GUIDELINES_PDF_URL = "https://aca.tmu.edu.tw/download.php?dir=archive&filename=358399ca0e0e15f4b063fb115b5a2d1e.pdf&title=%E8%87%BA%E5%8C%97%E9%86%AB%E5%AD%B8%E5%A4%A7%E5%AD%B8%E5%AD%B8%E7%94%9F%E5%A2%83%E5%A4%96%E7%A0%94%E4%BF%AE%E4%BD%9C%E6%A5%AD%E8%A6%81%E9%BB%9E.pdf"
TMU_ACA_DUAL_DEGREE_REGULATIONS_PDF_URL = "https://aca.tmu.edu.tw/download.php?dir=archive&filename=a9a9d49c530b3768ac9a45d6e3b91ca0.pdf&title=%E8%87%BA%E5%8C%97%E9%86%AB%E5%AD%B8%E5%A4%A7%E5%AD%B8%E8%BE%A6%E7%90%86%E5%A2%83%E5%A4%96%E9%9B%99%E8%81%AF%E5%AD%B8%E5%88%B6%E5%AF%A6%E6%96%BD%E8%BE%A6%E6%B3%95.pdf"
TMU_ACA_CREDIT_TRANSFER_REGULATIONS_PDF_URL = "https://aca.tmu.edu.tw/download.php?dir=archive&filename=e8cd47d9cdee0bdb4115e85674126af8.pdf&title=%E8%87%BA%E5%8C%97%E9%86%AB%E5%AD%B8%E5%A4%A7%E5%AD%B8%E5%AD%B8%E7%94%9F%E6%8A%B5%E5%85%8D%E5%AD%B8%E5%88%86%E8%BE%A6%E6%B3%95.pdf"

TMU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 72.0),
    "ielts": ("IELTS", 5.0),
    "toeic": ("TOEIC", 750.0),
}


def is_tmu(school_name: str | None) -> bool:
  school = resolve_university(school_name)
  if school is not None and school.id == TMU.id:
    return True
  normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
  return normalized in {
      "臺北醫學大學",
      "台北醫學大學",
      "北醫大",
      "北醫",
      "臺北醫大",
      "台北醫大",
      "tmu",
      "taipei medical university",
  }


def _is_graduate(degree_level: str | None) -> bool:
  text = (degree_level or "").strip()
  return any(token in text for token in ("碩", "博", "研究"))


def tmu_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
  degree = (degree_level or "").strip()
  year = (current_year or "").strip()
  if not degree:
    return (
        "needs_confirmation",
        (
            "尚未提供目前學制與年級；依《臺北醫學大學學生境外研修作業要點》、《辦理境外雙聯學制實施辦法》及《境外研修暨見實習獎勵辦法》規定：申請人須為本校當學期已註冊在學之學士班、碩士班或博士班學生（申請教育部學海飛颺／惜珠者須於北醫大就讀一學期以上且不含在職專班生；境外研修期間若辦理休學者，其修習科目、學分及成績均不予採計）。"
        ),
    )
  if any(token in degree or token in year for token in ("學分班", "選修生", "休學")):
    return (
        "fail",
        f"已填報 {degree}{f'（{year}）' if year else ''}；依《臺北醫學大學學生境外研修作業要點》第5點及《境外研修暨見實習獎勵辦法》第3條規定，境外研修期間須維持本校在學註冊，辦理休學或非正式學籍選修生不得申請境外研修學分採認及獎學金。",
    )
  is_grad = _is_graduate(degree)
  if "在職" in degree:
    return (
        "needs_confirmation",
        (
            f"已填報 {degree}{f'（{year}）' if year else ''}；依北醫大跨國雙聯學制規定（如呼吸治療學系與美國喬治亞州立大學、護理學系及高齡健康暨長期照護學系與澳洲伍倫貢大學／西雪梨大學／印尼加札馬達大學），碩士在職專班生得檢附《單位主管同意書》申請自費雙聯學位或境外研修，惟不得申請教育部學海系列及校內境外研修暨見實習獎學金。"
        ),
    )
  if not is_grad and year in {"大一上"}:
    return (
        "fail",
        (
            f"已填報 {degree}（{year}）；依北醫大《教育部學海飛颺／學海惜珠計畫申請公告》規定，申請人須於臺北醫學大學就讀一學期以上並檢附歷年成績單（含系所排名前 40% 或班排名前 30% 證明），大一上學期新生尚不得提出申請。"
        ),
    )
  return (
      "pass",
      (
          f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合臺北醫學大學境外研修、臨床見實習與跨國雙聯學制之在學學制規定（依《學生境外研修作業要點》第4、5點，境外研修期間須維持北醫大在學註冊，一般境外研修至多一年，雙聯學制依兩校協議辦理）。"
      ),
  )


def tmu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
  is_grad = _is_graduate(degree_level)
  min_pass_score = 70.0 if is_grad else 60.0
  target_score = 75.0
  target_gpa = 3.0
  target_rank = 40.0
  details: list[str] = []
  passes_scholarship_or_dual = False
  passes_basic = False

  if academic_score is not None:
    details.append(f"學業平均 {academic_score:g} 分")
    if academic_score >= target_score:
      passes_scholarship_or_dual = True
      passes_basic = True
    elif academic_score >= min_pass_score:
      passes_basic = True
  if academic_gpa is not None:
    details.append(f"GPA {academic_gpa:g}")
    if academic_gpa >= target_gpa:
      passes_scholarship_or_dual = True
      passes_basic = True
    elif academic_gpa >= 2.5:
      passes_basic = True
  if class_rank_percent is not None:
    details.append(f"系所／班級排名前 {class_rank_percent:g}%")
    if class_rank_percent <= target_rank:
      passes_scholarship_or_dual = True
      passes_basic = True

  summary = "、".join(details)
  if academic_score is None and academic_gpa is None and class_rank_percent is None:
    return (
        "needs_confirmation",
        (
            "尚未填寫學業平均、GPA 或系所／班排名；依北醫大《教育部學海飛颺／學海惜珠申請公告》及各院跨國雙聯學制規定：申請學海飛颺／惜珠者，歷年在校學業成績須達每系所排名前 40% 或每班排名前 30%（研究所免附排名，檢附學年總成績）且操行成績達 80 分以上；申請跨國雙聯學位（如美國凱斯西儲大學、南加州大學、賓州州立大學）多要求歷年 GPA 3.0（約 75 分）以上。"
        ),
    )

  if class_rank_percent is not None and class_rank_percent > target_rank and not is_grad:
    return (
        "needs_confirmation" if passes_basic else "fail",
        (
            f"已填報 {summary}；未達北醫大《教育部學海飛颺／學海惜珠》大學部歷年成績每系所排名前 40%（或每班排名前 30%）之獎學金門檻，僅能申請自費境外研修、海外交流課程或部分院系見實習計畫。"
        ),
    )

  if passes_scholarship_or_dual:
    return (
        "pass",
        (
            f"已填報 {summary}；符合臺北醫學大學境外研修暨教育部學海飛颺／惜珠獎學金（系所排名前 40% 或班排名前 30%、操行 80 分以上）與跨國雙聯學位（GPA 3.0 / 學業平均 75 分以上）學業標準。"
        ),
    )

  if passes_basic:
    return (
        "needs_confirmation",
        (
            f"已填報 {summary}；符合北醫大基本及格標準，惟申請教育部《學海飛颺／學海惜珠》須達每系所排名前 40% 或每班排名前 30%（操行 80 分以上），且美國凱斯西儲大學、南加州大學、賓州州立大學等雙聯學位要求歷年 GPA 3.0 以上，請確認是否符合目標計畫門檻。"
        ),
    )

  return (
      "fail",
      (
          f"已填報 {summary}；未達臺北醫學大學境外研修學業基準（{'研究所 70 分' if is_grad else '大學部 60 分'} / GPA 3.0 / 系所排名前 40%）。"
      ),
  )


def tmu_language_check(
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
            f"申請赴{partner_country}合作盟校短期交流或非醫事專業研修免檢附外語檢定證明（特別注意：依《臺北醫學大學學生境外研修作業要點》第2點規定，大陸地區有關醫療法所稱醫事人員高等學校學分不予採認，且兩岸學術交流不得涉及醫學人才培養）。"
        ),
    )
  if not test or language_score is None:
    return (
        "needs_confirmation",
        (
            "尚未填寫外語檢定成績。依北醫大《教育部學海計畫說明會簡報》及《境外研修暨見實習獎勵辦法》第4條規定：（1）申請教育部學海飛颺／惜珠：英語系國家須達 TOEFL iBT 79 分或 IELTS 5.5；非英語系國家須達 TOEFL iBT 75 分或 IELTS 5.0；日語組須達 JLPT N2；（2）申請校內《境外研修暨見實習獎學金》：英語能力須達 CEFR B2（TOEFL iBT 72 / IELTS 5.5 / TOEIC 785）；（3）跨國雙聯學位：如美國凱斯西儲大學要求 TOEFL iBT 90 / IELTS 7.0、喬治亞州立大學要求 TOEFL iBT 79 / IELTS 6.5、義大利卡利亞里大學中草藥博士雙聯要求 TOEIC > 750。"
        ),
    )
  if test in TMU_ENGLISH_MINIMUMS:
    label, minimum = TMU_ENGLISH_MINIMUMS[test]
    passed = language_score >= minimum
    adv_note = "符合北醫大校內《境外研修暨見實習獎勵辦法》CEFR B2 基準或雙聯基本英語門檻"
    if (test == "toefl" and language_score >= 90) or (
        test == "ielts" and language_score >= 7.0
    ):
      adv_note = "符合北醫大教育部學海飛颺／惜珠英語系國家門檻（iBT 79 / IELTS 5.5）、校內境外研修獎學金 CEFR B2 門檻，以及美國凱斯西儲大學（iBT 90 / IELTS 7.0）、南加州大學、賓州州立大學、喬治亞州立大學（iBT 79 / IELTS 6.5）、澳洲伍倫貢大學等全部跨國雙聯學位最高英語標準"
    elif (
        (test == "toefl" and language_score >= 79)
        or (test == "ielts" and language_score >= 5.5)
        or (test == "toeic" and language_score >= 785)
    ):
      adv_note = "符合北醫大教育部學海飛颺／惜珠英語系國家門檻（TOEFL iBT 79 / IELTS 5.5）、非英語系國家門檻（iBT 75 / IELTS 5.0）及校內《境外研修暨見實習獎勵辦法》CEFR B2 標準（若申請美國凱斯西儲大學雙聯學位則須達 TOEFL iBT 90 / IELTS 7.0）"
    elif (test == "toefl" and language_score >= 75) or (
        test == "ielts" and language_score >= 5.0
    ):
      adv_note = "符合北醫大教育部學海飛颺／惜珠非英語系國家門檻（TOEFL iBT 75 / IELTS 5.0；若申請英語系國家學海飛颺／惜珠須達 iBT 79 / IELTS 5.5，申請校內境外研修獎學金須達 CEFR B2［iBT 72 / IELTS 5.5 / TOEIC 785］）"
    return (
        "pass" if passed else "fail",
        (
            f"{label} {language_score:g} {'符合' if passed else '未達'}臺北醫學大學境外研修與雙聯學制英語標準（基準：{label} {minimum:g}；{adv_note}）。"
        ),
    )
  if test == "jlpt":
    level = int(language_score)
    passed = level in (1, 2, 3)
    tier_note = (
        "符合北醫大教育部學海飛颺／惜珠日文檢定 N2（2級）門檻，以及日本大阪大學、東京理科大學、北海道醫療大學、東北大學、北海道大學、九州大學、長崎大學、御茶水女子大學等全部日本合作盟校日語標準"
        if level in (1, 2)
        else (
            "符合日本部分短期見實習與海外交流課程日語門檻（若申請教育部學海飛颺／惜珠日語組或學期交換則須達 JLPT N2 以上，或改以英語檢定 TOEFL iBT 75 / IELTS 5.0 申請英語授課計畫如東北大學 JYPE、北海道大學 HUSTEP、九州大學 JTW）"
            if level == 3
            else "未達北醫大日本合作盟校 JLPT N2 日語檢定門檻"
        )
    )
    return (
        "pass" if passed else "fail",
        f"JLPT N{level} {'符合' if passed else '未達'}臺北醫學大學日本合作盟校日語檢定要求（{tier_note}）。",
    )
  if test == "topik":
    level = int(language_score)
    passed = 2 <= level <= 6
    return (
        "pass" if passed else "fail",
        f"TOPIK {level} 級{'符合' if passed else '未達'}臺北醫學大學韓國合作盟校（首爾大學、高麗大學、成均館大學、漢陽大學、梨花女子大學、韓國中央大學、全南大學）韓語檢定基準。",
    )
  if test in {"delf", "dalf", "tcf", "cefr"}:
    passed = language_score >= 2
    return (
        "pass" if passed else "fail",
        "已填報歐洲語言檢定成績；申請法國里爾大學雙聯學位、聖艾蒂安讓莫內大學、德國海德堡大學、丹麥奧胡斯大學等歐洲盟校請確認符合 B2 或英語授課標準。",
    )
  return (
      "needs_confirmation",
      f"已填報語言檢定 {language_test}（{language_score:g}）；請對照北醫大《教育部學海計畫說明會簡報》、《境外研修暨見實習獎勵辦法》與各盟校雙聯／交換簡章確認是否符合 CEFR B2 或指定檢定標準。",
  )
