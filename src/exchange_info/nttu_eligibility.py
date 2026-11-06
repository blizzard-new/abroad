from __future__ import annotations

import re

from .university_registry import resolve_university

NTTU_COIA_HOME_URL = "https://rd.nttu.edu.tw/p/412-1007-3262.php?Lang=zh-tw"
NTTU_PARTNER_LIST_URL = "https://rd.nttu.edu.tw/p/412-1007-3264.php?Lang=zh-tw"
NTTU_OUTBOUND_EXCHANGE_URL = "https://rd.nttu.edu.tw/p/412-1007-9902.php?Lang=zh-tw"
NTTU_EXCHANGE_RECRUITMENT_URL = "https://rd.nttu.edu.tw/p/412-1007-9903.php?Lang=zh-tw"
NTTU_2027_SPRING_ANNOUNCEMENT_URL = "https://rd.nttu.edu.tw/p/406-1007-179057,r1848.php?Lang=zh-tw"
NTTU_2026_FALL_ANNOUNCEMENT_URL = "https://rd.nttu.edu.tw/p/406-1007-173156,r1848.php?Lang=zh-tw"
NTTU_2027_SPRING_RESULTS_URL = "https://rd.nttu.edu.tw/p/406-1007-180597,r1848.php?Lang=zh-tw"
NTTU_EXCHANGE_REGULATIONS_URL = "https://rd.nttu.edu.tw/p/412-1007-9904.php?Lang=zh-tw"
NTTU_XUEHAI_HUB_URL = "https://rd.nttu.edu.tw/p/412-1007-9897.php?Lang=zh-tw"
NTTU_XUEHAI_FEIYANG_REGULATIONS_URL = "https://rd.nttu.edu.tw/p/412-1007-9910.php?Lang=zh-tw"
NTTU_XUEHAI_ZHUMENG_REGULATIONS_URL = "https://rd.nttu.edu.tw/p/412-1007-10011.php?Lang=zh-tw"
NTTU_EXPERIENCE_SHARING_URL = "https://rd.nttu.edu.tw/p/412-1007-9911.php?Lang=zh-tw"
NTTU_ZHUMENG_EXPERIENCE_URL = "https://rd.nttu.edu.tw/p/412-1007-10015.php?Lang=zh-tw"
NTTU_AA_REGULATIONS_URL = "https://aa.nttu.edu.tw/p/412-1002-8180.php?Lang=zh-tw"

NTTU_2027_SPRING_QUOTA_PDF_URL = "https://rd.nttu.edu.tw/var/file/7/1007/img/1704/900770058.pdf"
NTTU_2027_SPRING_BROCHURE_PDF_URL = "https://rd.nttu.edu.tw/var/file/7/1007/img/1704/684217375.pdf"
NTTU_2026_FALL_QUOTA_PDF_URL = "https://rd.nttu.edu.tw/var/file/7/1007/img/1704/146113981.pdf"
NTTU_2026_FALL_BROCHURE_PDF_URL = "https://rd.nttu.edu.tw/var/file/7/1007/img/1704/896144241.pdf"
NTTU_OUTBOUND_FLOWCHART_PDF_URL = "https://rd.nttu.edu.tw/var/file/7/1007/img/1704/524705677.pdf"
NTTU_EXCHANGE_GUIDELINES_PDF_URL = "https://rd.nttu.edu.tw/var/file/7/1007/img/1704/615221646.pdf"
NTTU_SCHOLARSHIP_GUIDELINES_PDF_URL = "https://rd.nttu.edu.tw/var/file/7/1007/img/1704/747047936.pdf"
NTTU_DUAL_DEGREE_REGULATIONS_PDF_URL = "https://aa.nttu.edu.tw/var/file/2/1002/img/1164/473961823.pdf"
NTTU_STUDY_ABROAD_ACADEMIC_PDF_URL = "https://aa.nttu.edu.tw/var/file/2/1002/img/1164/738126067.pdf"
NTTU_CREDIT_TRANSFER_PDF_URL = "https://aa.nttu.edu.tw/var/file/2/1002/img/1164/833443330.pdf"
NTTU_GPA_CONVERSION_PDF_URL = "https://aa.nttu.edu.tw/var/file/2/1002/img/1164/257867879.pdf"

NTTU_APPLICATION_FORM_DOCX_URL = "https://rd.nttu.edu.tw/var/file/7/1007/img/1704/339798359.docx"
NTTU_PARENTAL_CONSENT_DOCX_URL = "https://rd.nttu.edu.tw/var/file/7/1007/img/1704/393778079.docx"
NTTU_STUDY_PLAN_DOCX_URL = "https://rd.nttu.edu.tw/var/file/7/1007/img/1704/488363506.docx"
NTTU_SCHOLARSHIP_FORM_DOCX_URL = "https://rd.nttu.edu.tw/var/file/7/1007/img/1704/447717464.docx"
NTTU_XUEHAI_FORM_DOCX_URL = "https://rd.nttu.edu.tw/var/file/7/1007/img/1704/146816299.docx"

NTTU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 42.0),
    "ielts": ("IELTS", 4.0),
    "toefl_itp": ("TOEFL ITP/PBT", 460.0),
    "toeic": ("TOEIC", 550.0),
    "duolingo": ("Duolingo English Test", 85.0),
}


def is_nttu(school_name: str | None) -> bool:
  school = resolve_university(school_name)
  if school is not None and school.id == "nttu":
    return True
  normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
  return normalized in {
      "國立臺東大學",
      "國立台東大學",
      "臺東大學",
      "台東大學",
      "東大",
      "nttu",
      "national taitung university",
  }


def _is_graduate(degree_level: str | None) -> bool:
  text = (degree_level or "").strip()
  return any(token in text for token in ("碩", "博", "研究"))


def nttu_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
  degree = (degree_level or "").strip()
  year = (current_year or "").strip()
  if not degree:
    return (
        "needs_confirmation",
        (
            "尚未提供目前學制與年級；依《國立臺東大學辦理學生申請出國進修或交換作業要點》第 3 點及當期交換生甄選簡章：（1）限本校二年級（含）以上之在學學位生（含學士班大二至大四、碩士班、博士班）申請，不含大一新生、當學期畢業生、延畢生及在職專班學生；（2）大四學生申請交換以一學期為限（上海華東師範大學不接受大四下學期交換，北京中央民族大學不接受大四學生且僅收秋季班，武漢華中師範大學接受大四學生）；（3）日本仙台大學 2.5+2 雙聯與琵琶湖成蹊體育運動大學 1.5+2+1 雙聯僅限學士班學生申請（研究生不適用）。"
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
          "應屆畢業",
          "當學期畢業",
      )
  ):
    return (
        "fail",
        (
            f"已填報 {degree}{f'（{year}）' if year else ''}；依《國立臺東大學辦理學生申請出國進修或交換作業要點》與《國立臺東大學學生出國進修獎助學金要點》，大一新生、當學期畢業生、延畢生、休學生及在職專班學生不得申請出國交換甄選與出國進修獎助學金。"
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
            f"已填報 {degree}（{year}）；依《國立臺東大學辦理學生申請出國進修或交換作業要點》及甄選簡章規定，學士班學生須為「二年級（含）以上之在學學位生」始得提出申請（不含大一新生）。建議於大一期間維持班排名前 50% 並準備外語檢定證照，於大二上學期起提出申請。"
        ),
    )
  grad_note = (
      "（提醒：碩博士班研究生可申請 1 學期或 1 學年出國交換，並可由系所推薦申請《學生出國進修獎助學金》最高新臺幣 30 萬元［外語須達 CEFR B2］或教育部《學海飛颺／學海惜珠》；惟日本仙台大學 2.5+2 及琵琶湖成蹊體育運動大學 1.5+2+1 雙聯學制僅限學士班學生申請）"
      if is_grad
      else "（提醒：大四學生申請交換以 1 學期為限；申請日本琵琶湖成蹊體育運動大學 1.5+2+1 雙聯者出國前須於東大修滿 3 學期［大二下出國］，申請日本仙台大學 2.5+2 雙聯者出國前須於東大修滿至少 5 學期［大三下出國］）"
  )
  return (
      "pass",
      (
          f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合國立臺東大學研究發展處國際事務中心《辦理學生申請出國進修或交換作業要點》、《與境外大學校院辦理雙聯學制實施辦法》及出國進修獎助學金之在學身分規定{grad_note}。"
      ),
  )


def nttu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
  score_min = 70.0
  gpa_min = 2.5
  rank_max = 50.0
  details: list[str] = []
  passes_general = False
  passes_scholarship = False

  if academic_score is not None:
    details.append(f"學業平均 {academic_score:g} 分")
    if academic_score >= score_min:
      passes_general = True
    if academic_score >= 80.0:
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
            "尚未填寫歷年學業成績、GPA 或班排名百分比；依《國立臺東大學辦理學生申請出國進修或交換作業要點》及《國立臺東大學學生出國進修獎助學金要點》第 4 點：（1）報名出國交換或雙聯甄選須檢附中文歷年學業成績單正本（3 份）及歷年學業成績名次證明（班排名證明，3 份），甄選採書面資料審查 50%＋面試（含外語口試）50%；（2）若同時申請校內《學生出國進修獎助學金》（最高 30 萬元）或教育部《學海飛颺／學海惜珠》，學士班學生在校各學期平均成績須達全班前二分之一（50%，含）以上（申請學海計畫亦可採計在校學業總平均達 80 分以上），碩士班及博士班學生須由系所推薦。"
        ),
    )

  if passes_general:
    tier_notes: list[str] = [
        "符合臺東大學出國交換暨雙聯學位甄選書面審查（佔總成績 50%）之基本學業條件"
    ]
    if passes_scholarship:
      tier_notes.append(
          "且達《國立臺東大學學生出國進修獎助學金要點》（學士班各學期班排前 50% 以上）與教育部《學海飛颺／學海惜珠》（班排前 50% 或總平均 80 分以上）之獎助學金學業門檻"
      )
    else:
      tier_notes.append(
          "若欲同時申請校內《學生出國進修獎助學金》或教育部《學海飛颺／學海惜珠》，學士班須確認各學期班排名達前 50%（或學海總平均達 80 分以上），碩博士班須由系所推薦"
      )
    return (
        "pass",
        f"已填報 {summary}；{'；'.join(tier_notes)}。",
    )

  return (
      "needs_confirmation",
      (
          f"已填報 {summary}；臺東大學出國交換甄選採書面審查（50%）與面試（50%）綜合評比，惟若欲申請校內《學生出國進修獎助學金》（最高 30 萬元）或教育部《學海飛颺／學海惜珠》，學士班各學期平均須達全班前 50%（含）以上（或學海總平均 80 分以上），建議向研究發展處國際事務中心確認。"
      ),
  )


def nttu_language_check(
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
            "申請赴中國大陸地區合作姊妹校（華東師範大學、蘭州大學、華中師範大學、西南大學、東北師範大學、中央民族大學、鄭州大學等）為中文授課，免附外語檢定證照；惟仍須備齊歷年成績單、班排名證明與出國進修交換計畫書（各 3 份）參加校內書審（50%）與面試（50%）。"
        ),
    )
  if not test or language_score is None:
    return (
        "needs_confirmation",
        (
            "尚未填寫外語能力檢定成績。依國立臺東大學研究發展處國際事務中心《出國交換名額一覽表》與《學生出國進修獎助學金要點》附件一：（1）捷克茲林托馬斯巴塔大學要求 CEFR B2（TOEFL iBT 72+ / TOEIC 785［聽400/讀385、說160/寫150］/ IELTS 5.5+）；（2）美國西來大學學分班要求 TOEFL iBT 61 或 IELTS 5.5 以上（未達標可參加該校線上英語分級測驗 Remote EPT 就讀非學分 IEP，惟領取獎助學金者須修讀正式學分課程）；（3）日本仙台大學交換生要求 JLPT N4 或日語修課證明、2.5+2 雙聯生要求 JLPT N2 或日語修課證明；琵琶湖成蹊體育運動大學 1.5+2+1 雙聯生要求 JLPT N3 以上；天理大學要求日檢或日語修課證明；（4）韓國釜山教育大學要求 TOPIK 2 級以上，韓國國立順天大學與高神大學免附韓檢證明；（5）申請校內《學生出國進修獎助學金》或教育部《學海飛颺／惜珠》者，學士班須達 CEFR B1（TOEIC 550 / TOEFL iBT 42 / TOEFL ITP 460 / IELTS 4.0 / GEPT 中級 / JLPT N3 / TOPIK II 3級），碩博士班須達 CEFR B2（TOEIC 785 / TOEFL iBT 72 / TOEFL ITP 543 / IELTS 5.5 / GEPT 中高級 / JLPT N2 / TOPIK II 4級）。"
        ),
    )
  if test in NTTU_ENGLISH_MINIMUMS:
    label, minimum = NTTU_ENGLISH_MINIMUMS[test]
    passed = language_score >= minimum
    tier_note = "達 CEFR B1 基準門檻（符合臺東大學學士班申請《學生出國進修獎助學金》及教育部《學海飛颺／學海惜珠》外語門檻）"
    if (
        (test == "toefl" and language_score >= 72)
        or (test == "ielts" and language_score >= 5.5)
        or (test == "toefl_itp" and language_score >= 543)
        or (test == "toeic" and language_score >= 785)
    ):
      tier_note = "達 CEFR B2 門檻（TOEFL iBT 72 / IELTS 5.5 / TOEIC 785+），符合捷克茲林托馬斯巴塔大學（Tomas Bata University in Zlín）、美國加州西來大學（University of the West）正式學分班，以及臺東大學碩博士班與學士班申請《學生出國進修獎助學金》（最高 30 萬元）及教育部《學海飛颺／學海惜珠》全部英語門檻"
    elif (
        (test == "toefl" and language_score >= 61)
        or (test == "toefl_itp" and language_score >= 500)
        or (test == "toeic" and language_score >= 650)
    ):
      tier_note = "符合美國加州西來大學（University of the West）正式學分班（TOEFL iBT 61 / IELTS 5.5）及臺東大學學士班申請《學生出國進修獎助學金》與教育部《學海飛颺／學海惜珠》門檻（捷克茲林托馬斯巴塔大學及碩博士班獎助學金要求 CEFR B2：TOEFL iBT 72 / TOEIC 785 / IELTS 5.5）"
    return (
        "pass" if passed else "fail",
        (
            f"{label} {language_score:g} {'符合' if passed else '未達'}國立臺東大學出國交換暨出國進修獎助學金英語檢定基準（最低採計門檻：{label} {minimum:g}；{tier_note}）。"
        ),
    )
  if test == "jlpt":
    level = int(language_score)
    passed = 1 <= level <= 4
    if level in (1, 2):
      tier_note = f"JLPT N{level} 符合日本仙台大學（2.5+2 雙聯學位 N2＆交換生 N4）、琵琶湖成蹊體育運動大學（1.5+2+1 雙聯學位 N3）、天理大學交換生，以及臺東大學學士班（N3）與碩博士班（N2）申請《學生出國進修獎助學金》（最高 30 萬元）與教育部《學海飛颺／惜珠》全部日語門檻"
    elif level == 3:
      tier_note = "JLPT N3 符合日本琵琶湖成蹊體育運動大學（1.5+2+1 雙聯學位 N3）、仙台大學交換生（N4）、天理大學交換生，以及臺東大學學士班申請《學生出國進修獎助學金》與教育部《學海飛颺／惜珠》（CEFR B1 = N3）門檻（仙台大學 2.5+2 雙聯學位要求 JLPT N2 或日語修課證明；碩博士班獎助學金要求 N2）"
    elif level == 4:
      tier_note = "JLPT N4 符合日本仙台大學交換生（JLPT N4 或日語修課證明）及天理大學交換生門檻（若欲申請琵琶湖成蹊 1.5+2+1 雙聯或學士班出國進修獎助學金須達 JLPT N3；仙台大學 2.5+2 雙聯須達 JLPT N2 或具日語修課證明）"
    else:
      tier_note = f"目前為 JLPT N{level}，未達日本仙台大學交換生（JLPT N4）、琵琶湖成蹊 1.5+2+1 雙聯（N3）或仙台 2.5+2 雙聯（N2）檢定門檻（仙台大學與天理大學另可檢附日語修課證明）"
    return (
        "pass" if passed else "fail",
        f"JLPT N{level} {'符合' if passed else '未達'}國立臺東大學日本姊妹校交換暨雙聯日語檢定基準（{tier_note}）。",
    )
  if test == "topik":
    level = int(language_score)
    passed = 2 <= level <= 6
    if level >= 4:
      tier_note = f"TOPIK {level} 級符合韓國釜山教育大學（TOPIK 2 級）、國立順天大學、高神大學交換門檻，以及臺東大學學士班（3 級）與碩博士班（4 級）申請《學生出國進修獎助學金》與教育部《學海飛颺／惜珠》全部韓語門檻"
    elif level == 3:
      tier_note = "TOPIK 3 級符合韓國釜山教育大學（TOPIK 2 級）、國立順天大學、高神大學交換門檻，以及臺東大學學士班申請《學生出國進修獎助學金》與教育部《學海飛颺／惜珠》（CEFR B1 = TOPIK II 3級）門檻（碩博士班獎助學金要求 TOPIK II 4級）"
    elif level == 2:
      tier_note = "TOPIK 2 級符合韓國釜山教育大學（TOPIK 2 級）、國立順天大學及高神大學交換門檻（若欲同時申請臺東大學出國進修獎助學金，學士班須達 TOPIK II 3級、碩博士班須達 4級）"
    else:
      tier_note = f"目前為 TOPIK {level} 級，未達韓國釜山教育大學（TOPIK 2 級）與出國進修獎助學金（TOPIK 3 級）門檻（惟韓國國立順天大學與高神大學交換生免附韓語檢定證明）"
    return (
        "pass" if passed else "fail",
        f"TOPIK {level} 級{'符合' if passed else '未達'}國立臺東大學韓國姊妹校韓語檢定基準（{tier_note}）。",
    )
  return (
      "needs_confirmation",
      f"已填報語言檢定 {language_test}（{language_score:g}）；請對照國立臺東大學《學生出國進修獎助學金要點》附件一（CEFR B1/B2 語言能力基準表）及當期《出國交換名額一覽表》確認目標合作姊妹校之語言門檻。",
  )
