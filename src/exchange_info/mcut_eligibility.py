from __future__ import annotations

import re

from .university_registry import resolve_university

MCUT_OIA_HOME_URL = "https://oia.mcut.edu.tw/?Lang=zh-tw"
MCUT_PARTNER_LIST_URL = "https://oia.mcut.edu.tw/p/412-1012-7472.php?Lang=zh-tw"
MCUT_REGULATIONS_URL = "https://oia.mcut.edu.tw/p/412-1012-6963.php?Lang=zh-tw"
MCUT_EXPERIENCE_HUB_URL = "https://oia.mcut.edu.tw/p/412-1012-10463.php?Lang=zh-tw"
MCUT_DUAL_EXP_URL = "https://oia.mcut.edu.tw/p/405-1012-64124,c10463.php?Lang=zh-tw"
MCUT_EXCH_EXP_URL = "https://oia.mcut.edu.tw/p/405-1012-64113,c10463.php?Lang=zh-tw"
MCUT_QA_HUB_URL = "https://oia.mcut.edu.tw/p/412-1012-10009.php?Lang=zh-tw"
MCUT_2026_2027_EXCHANGE_ANNOUNCEMENT_URL = "https://oia.mcut.edu.tw/p/406-1012-76292,r840.php?Lang=zh-tw"
MCUT_NIU_DUAL_SPRING_URL = "https://oia.mcut.edu.tw/p/406-1012-80170,r840.php?Lang=zh-tw"
MCUT_UC_DUAL_SPRING_URL = "https://oia.mcut.edu.tw/p/406-1012-80168,r840.php?Lang=zh-tw"
MCUT_NIU_DUAL_FALL_URL = "https://oia.mcut.edu.tw/p/406-1012-76297,r840.php?Lang=zh-tw"
MCUT_ELISAVA_SFSU_DUAL_URL = "https://oia.mcut.edu.tw/p/406-1012-76298,r840.php?Lang=zh-tw"
MCUT_UC_DUAL_FALL_URL = "https://oia.mcut.edu.tw/p/406-1012-76293,r840.php?Lang=zh-tw"
MCUT_ESIEE_ALBA_DUAL_URL = "https://oia.mcut.edu.tw/p/406-1012-70826,r840.php?Lang=zh-tw"
MCUT_SHORT_TERM_URL = "https://oia.mcut.edu.tw/p/406-1012-75791,r840.php?Lang=zh-tw"
MCUT_GSITES_HOME_URL = "https://sites.google.com/view/mcutaroundtheworld/home"
MCUT_GOOGLE_FORM_URL = "https://forms.gle/SWrEct6zFhJiaLSV8"

MCUT_EXCHANGE_SUBSIDY_REG_PDF_URL = "https://oia.mcut.edu.tw/var/file/12/1012/img/816/736779544.pdf"
MCUT_UNDERGRAD_EXCHANGE_COURSE_DOCX_URL = "https://oia.mcut.edu.tw/var/file/12/1012/img/816/A2Q1060001.docx"
MCUT_XUEHAI_SELECTION_REG_PDF_URL = "https://oia.mcut.edu.tw/var/file/12/1012/img/816/848114138.pdf"
MCUT_SHORT_TERM_REG_DOCX_URL = "https://oia.mcut.edu.tw/var/file/12/1012/img/816/A2Q1030010.docx"
MCUT_LANG_CEFR_TABLE_PDF_URL = "https://oia.mcut.edu.tw/var/file/12/1012/img/816/197207162.pdf"

MCUT_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 42.0),
    "ielts": ("IELTS", 4.0),
    "toefl_itp": ("TOEFL ITP/PBT", 460.0),
    "toeic": ("TOEIC", 550.0),
    "duolingo": ("Duolingo English Test", 60.0),
}


def is_mcut(school_name: str | None) -> bool:
  school = resolve_university(school_name)
  if school is not None and school.id == "mcut":
    return True
  normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
  return normalized in {
      "明志科技大學",
      "明志科大",
      "明志工專",
      "明志",
      "mcut",
      "ming chi university of technology",
  }


def _is_graduate(degree_level: str | None) -> bool:
  text = (degree_level or "").strip()
  return any(token in text for token in ("碩", "博", "研究"))


def mcut_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
  degree = (degree_level or "").strip()
  year = (current_year or "").strip()
  if not degree:
    return (
        "needs_confirmation",
        (
            "尚未提供目前學制與年級；依《明志科技大學學生出國雙聯學位學習及交換學習實施及補助辦法（A2Q1040008）》第 4 條及當期甄選簡章：（1）限本校就讀滿一學期以上之日間部大二、大三在學學生及日間部碩士班、博士班在學學生申請（不含大一新生及在職專班學生）；（2）大學部僅大二升大三擬以海外交換抵免大三「工讀實務實習」課程（上學期 16 學分、下學期 18 學分）者可申請一學年交換，其餘年級皆以申請一學期交換為原則；（3）申請跨國碩士雙聯學位者，出國前須先通過母系所之「論文計畫書審查（或專業實務報告初稿）」。"
        ),
    )
  if any(
      token in degree or token in year
      for token in (
          "在職專班",
          "碩專",
          "emba",
          "EMBA",
          "學分班",
          "選修生",
          "休學",
          "延畢",
          "延畢生",
      )
  ):
    return (
        "fail",
        (
            f"已填報 {degree}{f'（{year}）' if year else ''}；依《明志科技大學學生出國雙聯學位學習及交換學習實施及補助辦法（A2Q1040008）》，限日間部大二、大三及日間部碩博士班在學學生申請，大一新生、延畢生、休學生及在職專班學生不得申請出國交換或雙聯學位甄選。"
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
            f"已填報 {degree}（{year}）；依《明志科技大學學生出國雙聯學位學習及交換學習實施及補助辦法（A2Q1040008）》及甄選簡章規定，大學部學生須為「日間部二年級、三年級在學學生」始得提出申請（不含大一新生）。建議於大一期間維持 GPA 3.0 及操行 80 分以上並考取 CEFR B1 外語證照，於大二起提出申請（大二升大三可申請一學年交換抵免大三工讀實務實習）。"
        ),
    )
  grad_note = (
      "（提醒：碩博士班研究生可申請 1 學期交換或跨國碩士雙聯學位［美國辛辛那提大學 UC、北伊利諾大學 NIU、舊金山州立大學 SFSU、西班牙 ELISAVA、法國 ESIEE Paris、希臘 ALBA 等］，申請雙聯者出國前須通過母系所「論文計畫書審查／專業實務報告初稿」，錄取後可申請非亞洲區雙聯最高 24 萬元、交換最高 8萬／16 萬元補助）"
      if is_grad
      else "（提醒：大學部僅大二升大三擬以海外交換抵免大三「工讀實務實習」課程者可依《大學部海外交換學習課程實施辦法 A2Q1060001》申請一學年交換［每學期至少修讀 6 學分，歐洲 2 ECTS = 1 學分，並每三個月繳交四階段學習報告］；其餘皆以申請一學期為原則）"
  )
  return (
      "pass",
      (
          f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合明志科技大學國際事務處全球交流組《學生出國雙聯學位學習及交換學習實施及補助辦法（A2Q1040008）》之在學身分規定{grad_note}。"
      ),
  )


def mcut_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
  score_min = 75.0
  gpa_min = 3.0
  dual_gpa_min = 2.75
  details: list[str] = []
  passes_exchange = False
  passes_dual_275 = False

  if academic_score is not None:
    details.append(f"學業平均 {academic_score:g} 分")
    if academic_score >= score_min:
      passes_exchange = True
      passes_dual_275 = True
    elif academic_score >= 70.0:
      passes_dual_275 = True
  if academic_gpa is not None:
    details.append(f"GPA {academic_gpa:g}")
    if academic_gpa >= gpa_min:
      passes_exchange = True
      passes_dual_275 = True
    elif academic_gpa >= dual_gpa_min:
      passes_dual_275 = True
  if class_rank_percent is not None:
    details.append(f"班排名百分比前 {class_rank_percent:g}%")
    if class_rank_percent <= 50.0 and academic_score is None and academic_gpa is None:
      passes_exchange = True
      passes_dual_275 = True

  summary = "、".join(details)
  if (
      academic_score is None
      and academic_gpa is None
      and class_rank_percent is None
  ):
    return (
        "needs_confirmation",
        (
            "尚未填寫歷年學業成績、GPA 或班排名百分比；依《明志科技大學學生出國雙聯學位學習及交換學習實施及補助辦法（A2Q1040008）》第 4 條及當期甄選簡章：（1）申請海外交換學習及美國辛辛那提大學（UC）、舊金山州立大學（SFSU）碩士雙聯者，在校歷年學業成績平均 GPA 須達 3.0（含）以上（折合百分制約 75 分以上）；（2）申請美國北伊利諾大學（NIU）、西班牙巴塞隆納高等設計學院（ELISAVA）、法國 ESIEE Paris、希臘 ALBA 商學院碩士雙聯者，大學及碩士歷年 GPA 須達 2.75（含）以上；（3）所有申請人在校歷年操行成績平均須達 80 分（含）以上且無記過處分紀錄。"
        ),
    )

  if passes_exchange:
    return (
        "pass",
        (
            f"已填報 {summary}；符合明志科技大學海外交換學習計畫（GPA ≥ 3.0／百分制約 75 分以上）、跨國碩士雙聯學位（UC & SFSU GPA ≥ 3.0；NIU、ELISAVA、ESIEE、ALBA GPA ≥ 2.75）及校內《雙聯學位（最高 24 萬）及交換學習（最高 16 萬）補助》與教育部《學海飛颺／惜珠》之學業門檻（另須檢附生輔組用印之歷年獎懲證明確認操行平均 ≥ 80 分且無記過）。"
        ),
    )

  if passes_dual_275:
    return (
        "needs_confirmation",
        (
            f"已填報 {summary}；已達美國北伊利諾大學（NIU）、西班牙巴塞隆納高等設計學院（ELISAVA）、法國 ESIEE Paris 及希臘 ALBA 商學院碩士雙聯學位門檻（GPA ≥ 2.75），惟一般海外交換學習計畫及美國辛辛那提大學（UC）、舊金山州立大學（SFSU）碩士雙聯要求在校歷年 GPA 達 3.0（約 75 分）以上，建議向國際事務處全球交流組確認。"
        ),
    )

  return (
      "fail",
      (
          f"已填報 {summary}；未達明志科技大學海外交換學習計畫（GPA ≥ 3.0／約 75 分以上）及跨國碩士雙聯學位（GPA ≥ 2.75–3.0）之最低學業門檻。"
      ),
  )


def mcut_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
  test = (language_test or "").strip().lower()
  if partner_country in {"中國大陸", "中國"} and (not test or language_score is None):
    return (
        "pass",
        (
            "申請赴中國大陸地區合作姊妹校（北京科技大學、南京理工大學、北京理工大學、中國礦業大學、蘇州大學、福州大學、廣州美術學院等）為中文授課，姊妹校端免附外語檢定證照；惟依明志科技大學校內甄選簡章與《雙聯及交換學習實施及補助辦法》規定，申請校內甄選及交換補助（亞洲區一學期最高 5 萬元／一學年最高 10 萬元）原則上仍建議備妥 CEFR B1 外語能力證明。"
        ),
    )
  if not test or language_score is None:
    return (
        "needs_confirmation",
        (
            "尚未填寫外語能力檢定成績。依明志科技大學《各類語言檢定證照等級對照表（197207162.pdf）》及甄選簡章：（1）校內海外交換基本門檻為 CEFR B1 以上（TOEIC 550［聽275/讀275］/ TOEFL iBT 42 / TOEFL ITP 460 / IELTS 4.0 / GEPT 中級 / FLPT 筆試 150 且口試 S-2 / Duolingo 60 / JLPT N3 / TOPIK 3級）；（2）美國加州大學河濱分校（UCR）、蒙大拿大學、西維吉尼亞大學、加拿大勞倫森大學、奧地利 MCI、捷克孟德爾大學要求英語達 CEFR B2（TOEFL iBT 72–80 / IELTS 5.5–6.0 / TOEIC 785），日本芝浦工業大學要求 JLPT N2 或英語 CEFR B2；（3）跨國碩士雙聯門檻：美國辛辛那提大學 UC 為 TOEFL iBT 80–85 / IELTS 6.5 / Duolingo 110，北伊利諾大學 NIU 為 iBT 80 / IELTS 6.5 / Duolingo 115，舊金山州立大學 SFSU 為 iBT 80 / IELTS 6.0–7.0，西班牙 ELISAVA 為 IELTS 6.0 / iBT 78 / TOEIC 785，法國 ESIEE Paris 為 iBT 72 / IELTS 5.5 / TOEIC 785，希臘 ALBA 為 IELTS 6.5 / iBT 100。"
        ),
    )
  if test in MCUT_ENGLISH_MINIMUMS:
    label, minimum = MCUT_ENGLISH_MINIMUMS[test]
    passed = language_score >= minimum
    tier_note = "達明志科技大學 CEFR B1 基本交換暨獎助學金門檻（TOEIC 550 / TOEFL iBT 42 / IELTS 4.0 / Duolingo 60+）"
    if (
        (test == "toefl" and language_score >= 85)
        or (test == "ielts" and language_score >= 6.5)
        or (test == "duolingo" and language_score >= 115)
    ):
      tier_note = "達高階雙聯與交換英語門檻（TOEFL iBT 85+ / IELTS 6.5+ / Duolingo 115+），符合美國辛辛那提大學（UC）、北伊利諾大學（NIU）、舊金山州立大學（SFSU）、西班牙 ELISAVA、法國 ESIEE Paris 跨國碩士雙聯學位及全數歐美交換姊妹校門檻"
    elif (
        (test == "toefl" and language_score >= 72)
        or (test == "ielts" and language_score >= 5.5)
        or (test == "toefl_itp" and language_score >= 543)
        or (test == "toeic" and language_score >= 785)
        or (test == "duolingo" and language_score >= 100)
    ):
      tier_note = "達 CEFR B2 門檻（TOEFL iBT 72+ / IELTS 5.5+ / TOEIC 785+），符合法國 ESIEE Paris（iBT 72 / IELTS 5.5 / TOEIC 785）與西班牙 ELISAVA（TOEIC 785 / IELTS 6.0）碩士雙聯，以及歐美 CEFR B2 交換姊妹校與明志校內雙聯／交換補助門檻（美國 UC、NIU、SFSU 碩士雙聯要求 TOEFL iBT 80–85 / IELTS 6.0–6.5）"
    return (
        "pass" if passed else "fail",
        (
            f"{label} {language_score:g} {'符合' if passed else '未達'}明志科技大學出國交換暨雙聯學位英語檢定基準（最低採計門檻：{label} {minimum:g}；{tier_note}）。"
        ),
    )
  if test == "jlpt":
    level = int(language_score)
    passed = 1 <= level <= 3
    if level in (1, 2):
      tier_note = f"JLPT N{level}（CEFR B2–C1）符合日本芝浦工業大學（N2）、福岡工業大學、日本工業大學、東京都市大學等全部日本交換與雙聯姊妹校及明志校內獎助學金門檻"
    elif level == 3:
      tier_note = "JLPT N3（CEFR B1）符合明志科技大學校內日本交換基本門檻及福岡工業大學、日本工業大學等姊妹校要求（日本芝浦工業大學要求 JLPT N2 或英語 CEFR B2）"
    else:
      tier_note = f"目前為 JLPT N{level}（CEFR A1–A2），未達明志科技大學《各類語言檢定證照等級對照表》規定之 CEFR B1（JLPT N3）出國交換門檻"
    return (
        "pass" if passed else "fail",
        f"JLPT N{level} {'符合' if passed else '未達'}明志科技大學日本姊妹校交換日語檢定基準（{tier_note}）。",
    )
  if test == "topik":
    level = int(language_score)
    passed = 3 <= level <= 6
    if level >= 4:
      tier_note = f"TOPIK {level} 級（CEFR B2–C2）符合韓國國民大學、同德女子大學及全部韓國姊妹校與明志校內獎助學金門檻"
    elif level == 3:
      tier_note = "TOPIK 3 級（CEFR B1）符合明志科技大學《各類語言檢定證照等級對照表》規定之 CEFR B1 交換暨獎助學金門檻"
    else:
      tier_note = f"目前為 TOPIK {level} 級（CEFR A1–A2），未達明志科技大學校內規定之 CEFR B1（TOPIK 3 級）門檻（惟韓國國民大學與同德女子大學接待端免韓檢，建議搭配英語 CEFR B1 證照提出申請）"
    return (
        "pass" if passed else "fail",
        f"TOPIK {level} 級{'符合' if passed else '未達'}明志科技大學韓國姊妹校韓語檢定基準（{tier_note}）。",
    )
  return (
      "needs_confirmation",
      f"已填報語言檢定 {language_test}（{language_score:g}）；請對照明志科技大學《各類語言檢定證照等級對照表（197207162.pdf）》（CEFR B1/B2 基準）及當期交換與雙聯簡章確認目標合作姊妹校之語言門檻。",
  )
