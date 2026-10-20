from __future__ import annotations

import re

from .university_registry import NCUE, resolve_university

NCUE_OICA_HUB_URL = "https://oicaweb.ncue.edu.tw/"
NCUE_OUTBOUND_HUB_URL = "https://oicaweb.ncue.edu.tw/p/412-1019-1171.php?Lang=zh-tw"
NCUE_OVERSEAS_HUB_URL = "https://oicaweb.ncue.edu.tw/p/412-1019-1220.php?Lang=zh-tw"
NCUE_MAINLAND_HUB_URL = "https://oicaweb.ncue.edu.tw/p/412-1019-1219.php?Lang=zh-tw"
NCUE_GLOBAL_SISTERS_URL = "https://oicaweb.ncue.edu.tw/p/412-1019-1164.php?Lang=zh-tw"
NCUE_DUAL_DEGREE_URL = "https://oicaweb.ncue.edu.tw/p/412-1019-1167.php?Lang=zh-tw"
NCUE_REGULATIONS_URL = "https://oicaweb.ncue.edu.tw/p/412-1019-1117.php?Lang=zh-tw"
NCUE_FORMS_URL = "https://oicaweb.ncue.edu.tw/p/412-1019-1118.php?Lang=zh-tw"
NCUE_OVERSEAS_116_ANNOUNCEMENT_URL = "https://oicaweb.ncue.edu.tw/p/406-1019-34307,r140.php?Lang=zh-tw"
NCUE_OVERSEAS_116_BROCHURE_PDF_URL = "https://oicaweb.ncue.edu.tw/var/file/19/1019/img/542278849.pdf"
NCUE_OVERSEAS_116_SHEET_URL = "https://docs.google.com/spreadsheets/d/1JZEHkhetJoABfPogFlrqiyvG8URvmEw9/edit?gid=323620502#gid=323620502"
NCUE_OVERSEAS_116_APP_FORM_URL = "https://oicaweb.ncue.edu.tw/var/file/19/1019/img/974155076.docx"
NCUE_PARENTAL_GUARANTEE_URL = "https://oicaweb.ncue.edu.tw/var/file/19/1019/img/348780386.docx"
NCUE_HEALTH_DECLARATION_URL = "https://oicaweb.ncue.edu.tw/var/file/19/1019/img/522622028.docx"
NCUE_MAINLAND_115_2_ANNOUNCEMENT_URL = "https://oicaweb.ncue.edu.tw/p/405-1019-34980,c1219.php?Lang=zh-tw"
NCUE_MAINLAND_115_2_PARTNERS_URL = "https://oicaweb.ncue.edu.tw/p/404-1019-34979.php?Lang=zh-tw"
NCUE_MAINLAND_115_1_ANNOUNCEMENT_URL = "https://oicaweb.ncue.edu.tw/p/405-1019-33054,c1219.php?Lang=zh-tw"
NCUE_XUEHAI_116_ANNOUNCEMENT_URL = "https://oicaweb.ncue.edu.tw/p/404-1019-31228.php?Lang=zh-tw"
NCUE_SELECTION_GUIDELINES_PDF_URL = "https://oicaweb.ncue.edu.tw/var/file/19/1019/img/154/547428539.pdf"
NCUE_XUEHAI_GUIDELINES_PDF_URL = "https://oicaweb.ncue.edu.tw/var/file/19/1019/img/191957275.pdf"
NCUE_COURSE_SELECTION_PDF_URL = "https://oicaweb.ncue.edu.tw/var/file/19/1019/img/433095064.pdf"
NCUE_CREDIT_TRANSFER_PDF_URL = "https://oicaweb.ncue.edu.tw/var/file/19/1019/img/154/504843202.pdf"
NCUE_CREDIT_CONVERSION_PDF_URL = "https://oicaweb.ncue.edu.tw/var/file/19/1019/img/123052535.pdf"
NCUE_DUAL_DEGREE_RULES_PDF_URL = "https://oicaweb.ncue.edu.tw/var/file/19/1019/img/156/603615731.pdf"
NCUE_OVERSEAS_EXP_LIST_URL = "https://oicaweb.ncue.edu.tw/p/403-1019-163-1.php?Lang=zh-tw"
NCUE_MAINLAND_EXP_LIST_URL = "https://oicaweb.ncue.edu.tw/p/403-1019-159-1.php?Lang=zh-tw"

NCUE_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 61.0),
    "ielts": ("IELTS", 5.5),
    "toeic": ("TOEIC", 670.0),
}


def is_ncue(school_name: str | None) -> bool:
  school = resolve_university(school_name)
  if school is not None and school.id == NCUE.id:
    return True
  normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
  return normalized in {
      "國立彰化師範大學",
      "彰化師範大學",
      "彰化師大",
      "彰師大",
      "彰師",
      "ncue",
      "national changhua university of education",
  }


def _is_graduate(degree_level: str | None) -> bool:
  text = (degree_level or "").strip()
  return any(token in text for token in ("碩", "博", "研究"))


def ncue_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
  degree = (degree_level or "").strip()
  year = (current_year or "").strip()
  if not degree:
    return (
        "needs_confirmation",
        (
            "尚未提供目前學制與年級；依《國立彰化師範大學交換學生甄選作業要點》第2點及《116學年赴國外非大陸姊妹校交換研修甄選簡章》規定：申請人須具本校正式學籍（未休學），且於本校就讀一學期以上之大學部、碩士班或博士班在學學生（大學部最早可於大一下學期申請、大二上學期出國；出國期間須為在學註冊學生）。"
        ),
    )
  if any(token in degree for token in ("學分班", "休學")):
    return (
        "fail",
        f"已填報 {degree}；依《國立彰化師範大學交換學生甄選作業要點》第2點規定，休學生及非正式學籍生不得申請出國交換。",
    )
  if "延畢" in year or "延修" in year:
    return (
        "needs_confirmation",
        (
            f"已填報 {degree}（{year}）；依《國立彰化師範大學交換學生甄選作業要點》第2點與《學生出國選修課程實施注意事項》第3點規定，延期畢業生不得提出申請（惟若已完成畢業條件經核准赴國外非大陸交換者，得申請延長修業期限至多一年；部分日本姊妹校如新潟、福岡教育、愛知教育、秋田大學明確不接受大五或延畢生）。"
        ),
    )
  if "在職" in degree:
    return (
        "needs_confirmation",
        (
            f"已填報 {degree}{f'（{year}）' if year else ''}；依《116學年赴國外非大陸姊妹校交換研修甄選簡章》第1點規定，進修學院在職進修專班學生得申請赴國外交換，惟教育部《學海飛颺／學海惜珠》補助要點及部分姊妹校（如西南財經大學）不含國內及境外在職專班生，請先向國際處確認。"
        ),
    )
  is_grad = _is_graduate(degree)
  if not is_grad and year in {"大一上"}:
    return (
        "fail",
        (
            f"已填報 {degree}（{year}）；依《國立彰化師範大學交換學生甄選作業要點》第2點及《116學年甄選簡章》規定，申請人須於本校就讀一學期以上（大學部最早一下申請、二上出國），大一上學期新生尚不得提出申請。"
        ),
    )
  return (
      "pass",
      (
          f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合國立彰化師範大學出國交換學生學制與年級規定（就讀一學期以上之在學學士、碩士、博士生，出國期間維持在學註冊並繳交本校全額學雜費；師培公費生另須先取得師培中心及分發縣市政府同意）。"
      ),
  )


def ncue_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
  is_grad = _is_graduate(degree_level)
  min_pass_score = 70.0 if is_grad else 60.0
  xuehai_gpa = 2.5
  xuehai_rank = 50.0
  details: list[str] = []
  passes_xuehai = False
  passes_basic = False

  if academic_score is not None:
    details.append(f"歷年學業總平均 {academic_score:g} 分")
    if academic_score >= 70.0:
      passes_xuehai = True
      passes_basic = True
    elif academic_score >= min_pass_score:
      passes_basic = True
  if academic_gpa is not None:
    details.append(f"GPA {academic_gpa:g}")
    if academic_gpa >= xuehai_gpa:
      passes_xuehai = True
      passes_basic = True
    elif academic_gpa >= 2.0:
      passes_basic = True
  if class_rank_percent is not None:
    details.append(f"全班排名前 {class_rank_percent:g}%")
    if class_rank_percent <= xuehai_rank:
      passes_xuehai = True
      passes_basic = True

  summary = "、".join(details)
  if academic_score is None and academic_gpa is None and class_rank_percent is None:
    return (
        "needs_confirmation",
        (
            "尚未填寫歷年學業總平均、GPA 或班排名；依《116學年赴國外非大陸姊妹校交換研修甄選簡章》與《國立彰化師範大學辦理教育部學海系列補助作業準則》規定：申請人須檢附含全班排名百分比之中英文歷年成績單並符合志願姊妹校 GPA 門檻（多數歐美日韓印姊妹校要求 GPA 2.5–3.0 以上），申請教育部《學海飛颺／學海惜珠》獎助金者須達 GPA 2.5(含)以上或歷年全班排名前 50%。"
        ),
    )

  if passes_xuehai:
    return (
        "pass",
        (
            f"已填報 {summary}；符合國立彰化師範大學出國交換及教育部《學海飛颺／學海惜珠》獎助金學業門檻（GPA 2.5 以上或歷年全班排名前 50%；如申請 UC Berkeley、UC Irvine、天普雙聯、史崔克萊雙聯、新南威爾斯、印尼大學、艾爾朗加等要求 GPA 3.0 以上之姊妹校，請一併確認符合該校標準）。"
        ),
    )

  if passes_basic:
    return (
        "needs_confirmation",
        (
            f"已填報 {summary}；符合部分姊妹校（如捷克奧斯特拉瓦大學 GPA 2.0、加州州立大學弗雷斯諾分校雙聯 GPA 2.4）或一般交換申請資格，惟若欲申請教育部《學海飛颺／學海惜珠》獎助金須達 GPA 2.5(含)以上或歷年全班排名前 50%，請一併提供班排名或確認志願姊妹校 GPA 要求。"
        ),
    )

  return (
      "fail",
      (
          f"已填報 {summary}；未達國立彰化師範大學學業及格基準（{'研究所 70 分' if is_grad else '大學部 60 分'} / GPA 2.0）及教育部《學海飛颺／學海惜珠》獎助金門檻（GPA 2.5 或全班排名前 50%）。"
      ),
  )


def ncue_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
  test = (language_test or "").strip().lower()
  if partner_country == "中國大陸" and (not test or language_score is None):
    return (
        "pass",
        (
            "申請赴中國大陸地區姊妹校交換免檢附外語能力檢定證明（依《國立彰化師範大學交換學生甄選作業要點》第3點及《赴大陸地區姊妹校交換計畫甄選簡章》辦理）。"
        ),
    )
  if not test or language_score is None:
    return (
        "needs_confirmation",
        (
            "尚未填寫外語檢定成績。依《116學年赴國外非大陸姊妹校交換研修甄選簡章》及《辦理教育部學海系列補助作業準則》規定：申請人須檢附 2 年內有效且符合姊妹校規定之語言能力證明（不採計 TOEIC 多益校園考成績，IELTS 雅思須為學術組）；若交換學校無明訂標準或申請《學海飛颺／學海惜珠》獎助金，英語基準為 TOEFL iBT 61 / IELTS 5.5 / TOEIC 670 / GEPT 中高級以上，其他語系為該國語言檢定（如日檢 JLPT N2–N4、韓檢 TOPIK 3–4 級、德檢/法檢/西檢 B1–B2）或英語基準。"
        ),
    )
  if test in NCUE_ENGLISH_MINIMUMS:
    label, minimum = NCUE_ENGLISH_MINIMUMS[test]
    passed = language_score >= minimum
    adv_note = "符合彰師大出國交換暨學海飛颺／惜珠英文基準（TOEFL iBT 61 / IELTS 5.5 / TOEIC 670）"
    if (
        (test == "toefl" and language_score >= 87)
        or (test == "ielts" and language_score >= 6.5)
        or (test == "toeic" and language_score >= 785)
    ):
      adv_note = "符合彰師大英文基準及 UC Irvine、天普雙聯、西英格蘭雙聯、史崔克萊雙聯、新南威爾斯、索邦大學、德國/捷克/西班牙多數姊妹校 B2–C1 進階英語門檻（UC Berkeley 另要求 TOEFL iBT 90 / IELTS 7.0）"
    elif (
        (test == "toefl" and language_score >= 71)
        or (test == "ielts" and language_score >= 6.0)
        or (test == "toeic" and language_score >= 750)
    ):
      adv_note = "符合彰師大英文基準及加州州立大學弗雷斯諾分校、莫瑞州立大學、聖彼得堡電工大學、布萊梅應科大、開姆尼茨工大、羅特林根大學、香港教育大學等姊妹校中階英語門檻"
    return (
        "pass" if passed else "needs_confirmation" if language_score >= 42 else "fail",
        (
            f"{label} {language_score:g} {'符合' if passed else '部分符合特定姊妹校但未達學海補助基準' if language_score >= 42 else '未達'}國立彰化師範大學國外交換與學海補助英文標準（基準：{label} {minimum:g}；{adv_note}；提醒：不採多益校園考，雅思須為學術組）。"
        ),
    )
  if test == "jlpt":
    level = int(language_score)
    passed = level in (1, 2, 3, 4)
    tier_note = (
        "符合日本新潟大學管理學院、筑波大學教育學院、秋田大學日語組（AUGP）及福岡教育大學、愛知教育大學等全部日本姊妹校日檢門檻"
        if level in (1, 2)
        else (
            "符合日本福岡教育大學（N4 以上）、愛知教育大學（N4 以上）、新潟大學理學院及秋田大學英語組（AUEP）門檻（若申請筑波大學教院、新潟管院或秋田 AUGP 則須達 JLPT N2）"
            if level in (3, 4)
            else "未達日本姊妹校 JLPT N4–N2 日語檢定門檻"
        )
    )
    return (
        "pass" if passed else "fail",
        f"JLPT N{level} {'符合' if passed else '未達'}國立彰化師範大學日本姊妹校日語檢定要求（{tier_note}）。",
    )
  if test == "topik":
    level = int(language_score)
    passed = 3 <= level <= 6
    tier_note = (
        "符合韓國慶尚國立大學（TOPIK 4 級）、明知大學（TOPIK 3 級）、又松大學（TOPIK 3 級）、首爾市立大學、首爾女子大學、釜慶大學、大邱大學等全部韓國姊妹校韓檢門檻"
        if level >= 4
        else (
            "符合韓國明知大學、又松大學（TOPIK 3 級）及首爾市立大學、首爾女子大學、釜慶大學、大邱大學韓語門檻（慶尚國立大學另要求 TOPIK 4 級）"
            if level == 3
            else "建議備妥 TOPIK 3–4 級以上（首爾市立、首爾女子、釜慶、大邱接受基礎韓語能力，惟申請學海補助須另具韓檢或英檢多益 670 以上證明）"
        )
    )
    return (
        "pass" if passed else "needs_confirmation",
        f"TOPIK {level} 級：{'符合' if passed else '部分韓國姊妹校可受理但須確認學海門檻'}（{tier_note}）。",
    )
  return (
      "needs_confirmation",
      (
          f"已填寫 {language_test} {language_score:g}；請對照國立彰化師範大學《116學年赴國外非大陸姊妹校交換研修甄選簡章》（{NCUE_OVERSEAS_116_BROCHURE_PDF_URL}）與姊妹校名額門檻一覽表（{NCUE_OVERSEAS_116_SHEET_URL}）確認是否符合志願學校規定。"
      ),
  )
