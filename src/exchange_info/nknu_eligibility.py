from __future__ import annotations

import re

from .university_registry import NKNU, resolve_university

NKNU_OIA_HUB_URL = "https://oia.nknu.edu.tw/"
NKNU_OUTBOUND_EXCHANGE_URL = "https://oia.nknu.edu.tw/exchange-programs.php"
NKNU_MAINLAND_EXCHANGE_URL = "https://oia.nknu.edu.tw/exchange-programs-mainland.php"
NKNU_SISTER_SCHOOLS_URL = "https://oia.nknu.edu.tw/sister-schools.php"
NKNU_DUAL_DEGREE_URL = "https://oia.nknu.edu.tw/dual-degree.php"
NKNU_REGULATIONS_URL = "https://oia.nknu.edu.tw/regulations.php"
NKNU_ACA_REGULATIONS_URL = "https://c.nknu.edu.tw/aca/Laws.aspx?PN=48"
NKNU_SSO_APPLY_URL = "https://sso.nknu.edu.tw/InternationalAdmissions/StudentAboard/Apply.aspx"
NKNU_116_XUEHAI_INFO_URL = "https://oia.nknu.edu.tw/news-detail.php?id=496"
NKNU_2027_SPRING_MAINLAND_URL = "https://oia.nknu.edu.tw/news-detail.php?id=460"
NKNU_2026_FALL_MAINLAND_URL = "https://oia.nknu.edu.tw/news-detail.php?id=377"
NKNU_115_XUEHAI_BRIEFING_PDF_URL = "https://oia.nknu.edu.tw/uploads/files/%E5%AD%B8%E6%B5%B7%E8%AA%AA%E6%98%8E%E6%9C%83115%E5%B9%B4%E7%B0%A1%E5%A0%B1_final%20version_20251029.pdf"
NKNU_115_OUTBOUND_HANDBOOK_PDF_URL = "https://oia.nknu.edu.tw/uploads/files/115%E5%B9%B4%E9%81%B8%E9%80%81%E5%AD%B8%E7%94%9F%E5%87%BA%E5%9C%8B%E8%AA%AA%E6%98%8E%E6%9C%83%E6%89%8B%E5%86%8A%EF%BC%BF%E5%9C%8B%E9%9A%9B%E8%99%95final%20version_20251027.pdf"
NKNU_SELECTION_GUIDELINES_PDF_URL = "https://oia.nknu.edu.tw/uploads/files/20251007113315_68e489fb6d963.pdf"
NKNU_SELECTION_FLOWCHART_PDF_URL = "https://oia.nknu.edu.tw/uploads/files/20251007113402_68e48a2ac6dd3.pdf"
NKNU_OUTBOUND_APP_FORMS_DOC_URL = "https://oia.nknu.edu.tw/uploads/files/20251007113419_68e48a3b07252.doc"
NKNU_PREDEPARTURE_NOTES_PDF_URL = "https://oia.nknu.edu.tw/uploads/files/20251007113835_68e48b3b21461.pdf"
NKNU_OVERSEAS_SAFETY_PDF_URL = "https://oia.nknu.edu.tw/uploads/files/20251007113907_68e48b5ba5a30.pdf"
NKNU_EXPERIENCE_GUIDE_PDF_URL = "https://oia.nknu.edu.tw/uploads/files/20251007114733_68e48d55f30f9.pdf"
NKNU_REIMBURSEMENT_CHECKLIST_DOCX_URL = "https://oia.nknu.edu.tw/uploads/files/20251007115119_68e48e37521e8.docx"
NKNU_DUAL_DEGREE_APP_FORM_DOCX_URL = "https://oia.nknu.edu.tw/uploads/files/20251007132226_68e4a392d4c4a.docx"
NKNU_DUAL_DEGREE_REGULATIONS_PDF_URL = "https://c.nknu.edu.tw/aca/Download.ashx?FileNo=1972&GID=20"
NKNU_COURSE_SELECTION_PDF_URL = "https://c.nknu.edu.tw/aca/Download.ashx?FileNo=1052&GID=20"
NKNU_ACADEMIC_STATUS_PDF_URL = "https://c.nknu.edu.tw/aca/Download.ashx?FileNo=919&GID=20"
NKNU_CREDIT_TRANSFER_PDF_URL = "https://c.nknu.edu.tw/aca/Download.ashx?FileNo=1075&GID=20"

NKNU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 47.0),
    "ielts": ("IELTS", 4.0),
    "toeic": ("TOEIC", 550.0),
}


def is_nknu(school_name: str | None) -> bool:
  school = resolve_university(school_name)
  if school is not None and school.id == NKNU.id:
    return True
  normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
  return normalized in {
      "國立高雄師範大學",
      "高雄師範大學",
      "高雄師大",
      "高師大",
      "高師",
      "nknu",
      "national kaohsiung normal university",
  }


def _is_graduate(degree_level: str | None) -> bool:
  text = (degree_level or "").strip()
  return any(token in text for token in ("碩", "博", "研究"))


def nknu_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
  degree = (degree_level or "").strip()
  year = (current_year or "").strip()
  if not degree:
    return (
        "needs_confirmation",
        (
            "尚未提供目前學制與年級；依《國立高雄師範大學選送學生出國研修審查要點》第3點及《學生出國選修課程實施要點》第3點規定：申請人須為本校在學且已就讀至少一學期以上之學士班、碩士班或博士班學生（休學生、學士班延期畢業生、選修生及領受臺灣獎學金之外國生不得提出申請）。"
        ),
    )
  if any(token in degree for token in ("學分班", "選修生", "休學")):
    return (
        "fail",
        f"已填報 {degree}；依《國立高雄師範大學選送學生出國研修審查要點》第3點規定，休學生及選修生不得申請出國交換研修。",
    )
  is_grad = _is_graduate(degree)
  if ("延畢" in year or "延修" in year) and not is_grad:
    return (
        "fail",
        (
            f"已填報 {degree}（{year}）；依《國立高雄師範大學選送學生出國研修審查要點》第3點規定，學士班延期畢業生不得申請選送出國研修。"
        ),
    )
  if "在職" in degree:
    return (
        "needs_confirmation",
        (
            f"已填報 {degree}{f'（{year}）' if year else ''}；依《國立高雄師範大學選送學生出國研修審查要點》第3點規定，進修學院在職專班學生得檢附《服務機關之出國同意書》申請自費出國交換，惟不得申請教育部學海系列或校內任何獎助學金。"
        ),
    )
  if not is_grad and year in {"大一上"}:
    return (
        "fail",
        (
            f"已填報 {degree}（{year}）；依《國立高雄師範大學學生出國選修課程實施要點》第3點及《選送學生出國研修審查要點》規定，申請人須於本校就讀一學期以上並檢附前一學期全班排名成績單，大一上學期新生尚不得提出申請。"
        ),
    )
  return (
      "pass",
      (
          f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合國立高雄師範大學選送學生出國研修學制與年級規定（在學且已就讀一學期以上之學士、碩士、博士班學生；出國期間須維持高師大在學註冊，至多出國交換二次、合計不超過一學年）。"
      ),
  )


def nknu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
  is_grad = _is_graduate(degree_level)
  min_pass_score = 70.0 if is_grad else 60.0
  target_gpa = 2.5
  target_rank = 50.0
  details: list[str] = []
  passes_rank_or_gpa = False
  passes_basic = False

  if academic_score is not None:
    details.append(f"學業平均 {academic_score:g} 分")
    if academic_score >= 70.0:
      passes_rank_or_gpa = True
      passes_basic = True
    elif academic_score >= min_pass_score:
      passes_basic = True
  if academic_gpa is not None:
    details.append(f"GPA {academic_gpa:g}")
    if academic_gpa >= target_gpa:
      passes_rank_or_gpa = True
      passes_basic = True
    elif academic_gpa >= 2.0:
      passes_basic = True
  if class_rank_percent is not None:
    details.append(f"全班排名前 {class_rank_percent:g}%")
    if class_rank_percent <= target_rank:
      passes_rank_or_gpa = True
      passes_basic = True

  summary = "、".join(details)
  if academic_score is None and academic_gpa is None and class_rank_percent is None:
    return (
        "needs_confirmation",
        (
            "尚未填寫學業平均、GPA 或班排名；依《國立高雄師範大學選送學生出國研修審查要點》第4點及《大陸及港澳地區姊妹校交換申請資訊》規定：申請人前一學期學業成績須為全班前 50% 且操行成績達 80 分以上，並須符合志願姊妹校 GPA 門檻（如美國北卡夏洛特、明尼蘇達州立曼卡托、西密西根、德國帕德博恩、日本櫻美林、日本中央大學要求 GPA 2.50/4.00 以上，韓國東國大學要求 GPA 2.5/4.5 以上）。"
        ),
    )

  if class_rank_percent is not None and class_rank_percent > target_rank:
    return (
        "fail",
        (
            f"已填報 {summary}；未達《國立高雄師範大學選送學生出國研修審查要點》第4點規定之前一學期學業成績全班前 50% 門檻。"
        ),
    )

  if passes_rank_or_gpa:
    return (
        "pass",
        (
            f"已填報 {summary}；符合國立高雄師範大學選送學生出國研修學業門檻（前一學期學業成績全班前 50%、操行成績 80 分以上及多數歐美日韓姊妹校 GPA 2.5 標準）。"
        ),
    )

  if passes_basic:
    return (
        "needs_confirmation",
        (
            f"已填報 {summary}；請確認前一學期學業成績是否位居全班前 50% 且操行成績達 80 分以上（《選送學生出國研修審查要點》第4點必要門檻），並留意部分歐美日韓姊妹校另要求歷年 GPA 2.50 以上。"
        ),
    )

  return (
      "fail",
      (
          f"已填報 {summary}；未達國立高雄師範大學學業及格基準（{'研究所 70 分' if is_grad else '大學部 60 分'} / GPA 2.5 / 全班前 50%）。"
      ),
  )


def nknu_language_check(
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
            f"申請赴{partner_country}姊妹校交換免檢附外語能力檢定證明（依《國立高雄師範大學選送學生出國研修審查要點》第4點及《大陸及港澳地區姊妹校交換申請資訊》規定，書面審查語言能力 40% 配分併入研修計畫書評分）。"
        ),
    )
  if not test or language_score is None:
    return (
        "needs_confirmation",
        (
            "尚未填寫外語檢定成績。依《國立高雄師範大學選送學生出國研修審查要點》第4點及《外國語言標準暨成績對照表》規定：申請人須符合志願姊妹校外語門檻且達本校 CEFR B1 進階級基準（TOEFL iBT 47 / TOEFL ITP 457 / IELTS 4.0 / TOEIC 550 / GEPT 中級，2 年內有效；注意：外國學校明訂要求國際 TOEFL 或 IELTS 者，不得以 TOEIC 或全民英檢替代）；非英語組須達日本 JLPT N2–N3、韓國 TOPIK 3–4 級或法國 DELF B2。"
        ),
    )
  if test in NKNU_ENGLISH_MINIMUMS:
    label, minimum = NKNU_ENGLISH_MINIMUMS[test]
    passed = language_score >= minimum
    adv_note = "符合高師大出國交換英文基本門檻（CEFR B1：TOEFL iBT 47 / IELTS 4.0 / TOEIC 550）"
    if (
        (test == "toefl" and language_score >= 79)
        or (test == "ielts" and language_score >= 6.5)
        or (test == "toeic" and language_score >= 785)
    ):
      adv_note = "符合高師大英文基準及美國西佛羅里達（iBT 79–80 / IELTS 6.0）、北卡夏洛特（iBT 70 / IELTS 6.0）、明尼蘇達州立曼卡托（iBT 61 / IELTS 5.5）、西密西根（iBT 71–80 / IELTS 6.0–6.5）、德國帕德博恩（iBT 79 / IELTS 6.5）、瑞典達拉納（iBT 79 / IELTS 6.0）等歐美姊妹校進階英語門檻（注意：美歐姊妹校多要求正式 TOEFL iBT 或 IELTS，不接受以 TOEIC 替代）"
    elif (
        (test == "toefl" and language_score >= 61)
        or (test == "ielts" and language_score >= 5.5)
        or (test == "toeic" and language_score >= 670)
    ):
      adv_note = "符合高師大英文基準及美國明尼蘇達州立曼卡托、捷克普爾基涅大學（B2）、韓國江原大學、東國大學、韓國中央大學、日本新潟大學等英語授課交換門檻"
    return (
        "pass" if passed else "fail",
        (
            f"{label} {language_score:g} {'符合' if passed else '未達'}國立高雄師範大學選送學生出國研修英文標準（校內 CEFR B1 基準：{label} {minimum:g}；{adv_note}）。"
        ),
    )
  if test == "jlpt":
    level = int(language_score)
    passed = level in (1, 2, 3)
    tier_note = (
        "符合日本三重大學、岩手大學、櫻美林大學、兵庫教育大學、千葉大學、滋賀大學、金澤星稜大學（JLPT N2）、大阪教育大學（JLPT N3）及新潟大學等全部日本交換姊妹校日檢門檻"
        if level in (1, 2)
        else (
            "符合日本大阪教育大學（JLPT N3）及新潟大學日語門檻（若申請三重、岩手、櫻美林、兵庫教育、千葉、滋賀、金澤星稜大學則須達 JLPT N2 以上）"
            if level == 3
            else "未達高師大日本交換姊妹校 JLPT N3–N2 日語檢定門檻"
        )
    )
    return (
        "pass" if passed else "fail",
        f"JLPT N{level} {'符合' if passed else '未達'}國立高雄師範大學日本姊妹校日語檢定要求（{tier_note}）。",
    )
  if test == "topik":
    level = int(language_score)
    passed = 3 <= level <= 6
    tier_note = (
        "符合韓國中央大學（TOPIK 4 級）、群山大學（TOPIK 3 級）、釜山外語大學（TOPIK 3 級）、江原大學、東國大學、梨花女子大學、瑞逸大學等全部韓國交換姊妹校韓檢門檻"
        if level >= 4
        else (
            "符合韓國群山大學（TOPIK 3 級）、釜山外語大學（TOPIK 3 級）及江原大學、東國大學、梨花女子大學韓語門檻（韓國中央大學韓語授課另要求 TOPIK 4 級）"
            if level == 3
            else "部分韓國姊妹校（如東國、江原、梨花女大、瑞逸）可搭配英語成績或修讀語學堂申請，惟群山大學、釜山外大要求 TOPIK 3 級、韓國中央大學要求 TOPIK 4 級"
        )
    )
    return (
        "pass" if passed else "needs_confirmation",
        f"TOPIK {level} 級：{'符合' if passed else '請確認志願韓國姊妹校韓語或英語門檻'}（{tier_note}）。",
    )
  return (
      "needs_confirmation",
      (
          f"已填寫 {language_test} {language_score:g}；請對照《國立高雄師範大學選送學生出國研修審查要點》（{NKNU_SELECTION_GUIDELINES_PDF_URL}）與《115年選送學生出國說明會手冊》（{NKNU_115_OUTBOUND_HANDBOOK_PDF_URL}）確認是否符合志願姊妹校規定（如法國巴黎西岱大學要求法語 DELF B2）。"
      ),
  )
