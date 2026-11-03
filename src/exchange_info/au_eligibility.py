from __future__ import annotations

import re

from .university_registry import AU, resolve_university

AU_HOME_URL = "https://www.au.edu.tw/"
AU_CIA_HOME_URL = "https://cia.au.edu.tw/"
AU_OUTBOUND_OVERVIEW_URL = (
    "https://cia.au.edu.tw/p/403-1022-109353.php?Lang=zh-tw"
)
AU_EXCHANGE_PROGRAMS_URL = (
    "https://cia.au.edu.tw/p/403-1022-111632.php?Lang=zh-tw"
)
AU_DUAL_DEGREE_URL = (
    "https://cia.au.edu.tw/p/403-1022-111695.php?Lang=zh-tw"
)
AU_SHORT_TERM_URL = (
    "https://cia.au.edu.tw/p/403-1022-111633.php?Lang=zh-tw"
)
AU_STUDY_ABROAD_GALLERY_URL = (
    "https://cia.au.edu.tw/p/403-1022-111634.php?Lang=zh-tw"
)
AU_STUDENT_EXPERIENCES_URL = (
    "https://cia.au.edu.tw/p/403-1022-111635.php?Lang=zh-tw"
)
AU_SISTER_SCHOOLS_URL = (
    "https://cia.au.edu.tw/p/403-1022-109350.php?Lang=zh-tw"
)
AU_REGULATIONS_URL = (
    "https://cia.au.edu.tw/p/403-1022-109356.php?Lang=zh-tw"
)
AU_OUTBOUND_REGULATIONS_URL = (
    "https://cia.au.edu.tw/p/403-1022-111641.php?Lang=zh-tw"
)
AU_SCHOLARSHIP_REGULATIONS_URL = (
    "https://cia.au.edu.tw/p/403-1022-111640.php?Lang=zh-tw"
)
AU_XUEHAI_OVERVIEW_URL = (
    "https://cia.au.edu.tw/p/403-1022-112299.php?Lang=zh-tw"
)
AU_XUEHAI_FEIYANG_URL = (
    "https://cia.au.edu.tw/p/403-1022-112300.php?Lang=zh-tw"
)
AU_XUEHAI_XIZHU_URL = (
    "https://cia.au.edu.tw/p/403-1022-112301.php?Lang=zh-tw"
)
AU_XUEHAI_ZHUMENG_URL = (
    "https://cia.au.edu.tw/p/403-1022-112302.php?Lang=zh-tw"
)
AU_SELECTION_REGULATION_PAGE_URL = (
    "https://cia.au.edu.tw/p/406-1022-84480,r111641.php?Lang=zh-tw"
)
AU_CREDIT_TRANSFER_REGULATION_PAGE_URL = (
    "https://cia.au.edu.tw/p/406-1022-70817,r111641.php?Lang=zh-tw"
)
AU_DUAL_DEGREE_REGULATION_PAGE_URL = (
    "https://cia.au.edu.tw/p/406-1022-93784,r111641.php?Lang=zh-tw"
)
AU_2027_SPRING_EXCHANGE_URL = (
    "https://cia.au.edu.tw/p/406-1022-118696,r111632.php?Lang=zh-tw"
)
AU_2026_FALL_EXCHANGE_URL = (
    "https://cia.au.edu.tw/p/406-1022-116680,r111632.php?Lang=zh-tw"
)
AU_2026_2027_JAPAN_EXCHANGE_URL = (
    "https://cia.au.edu.tw/p/406-1022-115847,r111632.php?Lang=zh-tw"
)
AU_MACQUARIE_PROGRAM_URL = (
    "https://cia.au.edu.tw/p/406-1022-113277,r111632.php?Lang=zh-tw"
)
AU_MIDDLESEX_DUAL_URL = (
    "https://cia.au.edu.tw/p/406-1022-86012,r111695.php?Lang=zh-tw"
)
AU_UWE_DUAL_URL = (
    "https://cia.au.edu.tw/p/406-1022-86013,r111695.php?Lang=zh-tw"
)
AU_STPOL_DUAL_URL = (
    "https://cia.au.edu.tw/p/406-1022-86011,r111695.php?Lang=zh-tw"
)
AU_EXCHANGE_SCHOLARSHIP_PDF_URL = (
    "https://cia.au.edu.tw/var/file/22/1022/img/2737/P-01-510.pdf"
)
AU_STUDY_TOUR_SCHOLARSHIP_PDF_URL = (
    "https://cia.au.edu.tw/var/file/22/1022/img/2737/P-01-509.pdf"
)
AU_VOLUNTEER_SCHOLARSHIP_PDF_URL = (
    "https://cia.au.edu.tw/var/file/22/1022/img/2737/P-01-513.pdf"
)
AU_SPECIAL_CONTRIBUTION_SCHOLARSHIP_PDF_URL = (
    "https://cia.au.edu.tw/var/file/22/1022/img/2737/P-01-526.pdf"
)
AU_SCHOLARSHIP_REIMBURSEMENT_URL = (
    "https://cia.au.edu.tw/p/406-1022-80923,r109353.php?Lang=zh-tw"
)
AU_XUEHAI_GUIDELINE_PAGE_URL = (
    "https://cia.au.edu.tw/p/406-1022-89178,r112299.php?Lang=zh-tw"
)

AU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 57.0),
    "ielts": ("IELTS", 5.0),
    "toefl_itp": ("TOEFL ITP/PBT", 460.0),
    "toeic": ("TOEIC", 600.0),
}


def is_au(school_name: str | None) -> bool:
  school = resolve_university(school_name)
  if school is not None and school.id == AU.id:
    return True
  normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
  return normalized in {
      "真理大學",
      "真理",
      "真大",
      "au",
      "aletheia university",
      "oxford college tamsui",
  }


def _is_graduate(degree_level: str | None) -> bool:
  text = (degree_level or "").strip()
  return any(token in text for token in ("碩", "博", "研究"))


def au_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
  degree = (degree_level or "").strip()
  year = (current_year or "").strip()
  if not degree:
    return (
        "needs_confirmation",
        (
            "尚未提供目前學制與年級；依《真理大學交換學生出國甄選辦法》（教-P-806）第 4 條第 1 款：具有本校學籍之大學部與研究所在學學生，須曾在本校就讀滿一學年以上（即大學部大二以上、研究所碩二以上），始得參加甄選。"
        ),
    )
  if any(
      token in degree or token in year
      for token in ("休學", "退學", "學分班", "選修生")
  ):
    return (
        "fail",
        (
            f"已填報 {degree}{f'（{year}）' if year else ''}；依《真理大學交換學生出國甄選辦法》第 4 條規定，申請人須為具本校正式學籍之在學學生。"
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
            f"已填報 {degree}（{year}）；依《真理大學交換學生出國甄選辦法》第 4 條第 1 款規定，申請人須曾在本校就讀滿一學年以上（即大學部二年級以上）始得參加交換甄選。建議於大一期間準備外語檢定並參與國際事務中心志工服務，於升大二後提出申請（註：教育部《學海飛颺／惜珠計畫》要求於本校就讀一學期以上）。"
        ),
    )
  if is_grad and year in {
      "碩一",
      "碩一上",
      "碩一下",
      "碩士班一年級",
      "博一",
  }:
    return (
        "fail",
        (
            f"已填報 {degree}（{year}）；依《真理大學交換學生出國甄選辦法》第 4 條第 1 款規定，申請校級交換學生須曾在本校就讀滿一學年以上（註：若為觀光事業學系碩士班申請英國密德薩斯大學或西班牙赫羅納大學觀光學院 EUHT StPOL「1+1 碩士雙聯學制」，則依雙聯學制簡章於碩一期間申請、碩二出國修讀）。"
        ),
    )
  grad_note = (
      "（提醒：交換期間仍需繳交真理大學全額學雜費且每學期至少修習 9 學分；觀光事業學系碩士班另可申請英國密德薩斯大學或西班牙赫羅納大學附設桑特波爾廚藝觀光學院 EUHT StPOL 之 1+1 碩士雙聯學位）"
      if is_grad
      else "（提醒：報名時需繳交 NT$ 3,000 行政處理費，交換期間需繳交真理大學全額學雜費且每學期修習課程不得低於 9 學分；日本昭和女子大學與韓國梨花女子大學限女性申請；英國密德薩斯大學與西英格蘭大學 UWE Bristol 開放 3+1、4+1、3+15 個月雙聯學位）"
  )
  return (
      "pass",
      (
          f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合《真理大學交換學生出國甄選辦法》第 4 條（就讀滿一學年以上之大學部與研究所在學學生）及雙聯學制之在學身分規定{grad_note}。"
      ),
  )


def au_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
  score_min = 60.0
  gpa_min = 2.5
  rank_max = 50.0
  details: list[str] = []
  passes_general = False
  passes_xuehai = False

  if academic_score is not None:
    details.append(f"學業平均 {academic_score:g} 分")
    if academic_score >= 75.0:
      passes_general = True
      passes_xuehai = True
    elif academic_score >= score_min:
      passes_general = True
  if academic_gpa is not None:
    details.append(f"GPA {academic_gpa:g}")
    if academic_gpa >= gpa_min:
      passes_general = True
  if class_rank_percent is not None:
    details.append(f"全班排名百分比前 {class_rank_percent:g}%")
    if class_rank_percent <= 30.0:
      passes_general = True
      passes_xuehai = True
    elif class_rank_percent <= rank_max:
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
            "尚未填寫歷年學業平均、GPA 或班排名百分比；依《真理大學交換學生出國甄選辦法》（教-P-806）第 4 條第 2 款及相關簡章：（1）申請校級交換學生須「前一學期學業成績全班前 50% 為原則，且操行分數達 80 分以上」；（2）申請教育部《學海飛颺／學海惜珠計畫》須「歷年成績平均達 75 分，或班排名前 30%」；（3）申請澳洲麥覺理大學交換須在校總平均 WAM 達 60 分以上；（4）申請英國密德薩斯大學雙聯學制須 CGPA 達 2.5 以上。"
        ),
    )

  if class_rank_percent is not None and class_rank_percent > rank_max and not passes_xuehai:
    return (
        "needs_confirmation",
        (
            f"已填報 {summary}；未達《真理大學交換學生出國甄選辦法》第 4 條第 2 款「前一學期學業成績全班前 50% 為原則」之門檻，建議向所屬學系及國際事務中心確認當學期名額與審查彈性。"
        ),
    )

  if passes_general:
    tier_notes: list[str] = []
    if (academic_gpa is not None and academic_gpa >= 2.5) or (
        academic_score is not None and academic_score >= 70.0
    ) or (class_rank_percent is not None and class_rank_percent <= 50.0):
      tier_notes.append(
          "符合《真理大學交換學生出國甄選辦法》全班前 50%、澳洲麥覺理大學（WAM 60）與英國密德薩斯大學雙聯學制（CGPA 2.5）學業門檻"
      )
    else:
      tier_notes.append(
          "已達基本及格與澳洲麥覺理大學（WAM 60）標準，惟須同時確認前一學期成績達全班前 50% 及操行 80 分以上（英國密德薩斯大學雙聯要求 CGPA 2.5）"
      )
    if passes_xuehai:
      tier_notes.append(
          "且達歷年平均 75 分以上或班排前 30%，符合《真理大學「學海飛颺」及「學海惜珠」計畫校內甄選簡章》學業成績門檻"
      )
    return (
        "pass",
        f"已填報 {summary}；符合真理大學出國交換與雙聯學制甄選學業標準（{'；'.join(tier_notes)}）。",
    )

  return (
      "needs_confirmation",
      (
          f"已填報 {summary}；未達全班前 50% 或 CGPA 2.5／平均 60 分門檻，依《真理大學交換學生出國甄選辦法》第 4 條規定，建議先提升學期成績並向國際事務中心確認。"
      ),
  )


def au_language_check(
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
            "申請赴中國大陸（北京體育大學、北京交通大學、南京航空航天大學、上海體育大學）或澳門（澳門城市大學中文班）交換姊妹校為中文授課，依《國外姐妹校交換學生實施計畫》免附外語能力檢定證明。"
        ),
    )
  if not test or language_score is None:
    return (
        "needs_confirmation",
        (
            "尚未填寫外語能力檢定成績。依《真理大學交換學生出國甄選辦法》第 5 條及各計畫簡章：（1）日本交換組（10 校，交換一學年）：城西國際大學、北亞大學、國立香川大學、新潟經營大學、名城大學、星城大學、長崎外國語大學、三重大學、昭和女子大學要求三年內通過 JLPT N2 以上；【日本多摩大學】可憑 JLPT N2 以上或 TOEIC 600 分以上申請；（2）澳洲麥覺理大學：要求 IELTS 6.5（單科不低於 6.0）；（3）英國雙聯學制：密德薩斯大學與西英格蘭大學（UWE Bristol）3+1 學士雙聯要求 IELTS 6.0（單科 5.5），1+1／4+1／3+15 個月碩士雙聯要求 IELTS 6.5；（4）教育部學海飛颺／惜珠計畫：要求兩年內通過英語組（GEPT 中高級初試 / TOEFL iBT 57 / IELTS 5.0 / New TOEIC 750）、日語組（JLPT N2）或韓語組（TOPIK 2 級）。"
        ),
    )
  if test in AU_ENGLISH_MINIMUMS:
    label, minimum = AU_ENGLISH_MINIMUMS[test]
    passed = language_score >= minimum
    tier_note = "達教育部《學海飛颺／惜珠計畫》基礎英檢或日本多摩大學（TOEIC 600）申請基準"
    if (
        (test == "toefl" and language_score >= 79)
        or (test == "ielts" and language_score >= 6.5)
        or (test == "toefl_itp" and language_score >= 550)
        or (test == "toeic" and language_score >= 785)
    ):
      tier_note = "達高階英語門檻，符合澳洲麥覺理大學（IELTS 6.5）、英國密德薩斯大學與西英格蘭大學碩士雙聯（IELTS 6.5）、教育部學海飛颺／惜珠（New TOEIC 750 / iBT 57 / IELTS 5.0）及日本多摩大學（TOEIC 600）等全部英語組門檻"
    elif (
        (test == "toefl" and language_score >= 61)
        or (test == "ielts" and language_score >= 6.0)
        or (test == "toefl_itp" and language_score >= 500)
        or (test == "toeic" and language_score >= 750)
    ):
      tier_note = "符合英國密德薩斯大學與西英格蘭大學 3+1 學士雙聯（IELTS 6.0）、美國明州西南州立大學（iBT 61）、教育部學海飛颺／惜珠計畫（New TOEIC 750 / iBT 57 / IELTS 5.0）及日本多摩大學（TOEIC 600）門檻（澳洲麥覺理大學與英國碩士雙聯需 IELTS 6.5）"
    return (
        "pass" if passed else "fail",
        (
            f"{label} {language_score:g} {'符合' if passed else '未達'}真理大學《國外姐妹校交換學生實施計畫》與《學海飛颺／雙聯學制》英語採計標準（最低基準：{label} {minimum:g}；{tier_note}）。"
        ),
    )
  if test == "jlpt":
    level = int(language_score)
    passed = 1 <= level <= 2
    if passed:
      tier_note = f"JLPT N{level} 符合《日本姐妹校交換學生實施計畫》全部 10 所日本交換姊妹校（城西國際大學、北亞大學、國立香川大學、新潟經營大學、名城大學、星城大學、長崎外國語大學、三重大學、多摩大學、昭和女子大學）及教育部《學海飛颺／惜珠計畫》日語組（JLPT N2 以上）門檻"
    else:
      tier_note = f"目前為 JLPT N{level}，未達《真理大學日本姐妹校交換學生實施計畫》與教育部《學海飛颺／惜珠計畫》規定之「日語檢定 N2 以上」門檻（註：若具備多益 TOEIC 600 分以上，可改以英語成績申請日本多摩大學交換）"
    return (
        "pass" if passed else "fail",
        f"JLPT N{level} {'符合' if passed else '未達'}真理大學日本姊妹校交換日語檢定基準（{tier_note}）。",
    )
  if test == "topik":
    level = int(language_score)
    passed = 2 <= level <= 6
    if level >= 3:
      tier_note = "符合韓國漢陽大學 ERICA 校區、國民大學 Seoul 校區、祥明大學、崇實大學、明知大學、啟明大學、又松大學、東明大學、韓世大學、濟州觀光大學、梨花女子大學等全部 11 所韓國交換姊妹校及教育部《學海飛颺／惜珠計畫》（TOPIK 2 級以上）門檻"
    elif level == 2:
      tier_note = "符合教育部《學海飛颺／惜珠計畫》韓語組（TOPIK 2 級以上）及多數韓國交換姊妹校門檻（提醒：韓國祥明大學等部分韓文寫作或專業課程建議具備 TOPIK 3–6 級或選修英語／留學生專班課程）"
    else:
      tier_note = "目前為 TOPIK 1 級，未達教育部《學海飛颺／惜珠計畫》韓語組 TOPIK 2 級門檻，建議提升至 TOPIK 2 級以上或搭配英語成績選修韓國姊妹校英語授課課程"
    return (
        "pass" if passed else "fail",
        f"TOPIK {level} 級{'符合' if passed else '未達'}真理大學韓國姊妹校交換與學海計畫韓語基準（{tier_note}）。",
    )
  return (
      "needs_confirmation",
      f"已填報語言檢定 {language_test}（{language_score:g}）；請對照真理大學國際事務中心《國外／日本姐妹校交換學生實施計畫》與《雙聯學制簡章》確認目標姊妹校語言門檻。",
  )
