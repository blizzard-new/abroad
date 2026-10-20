from __future__ import annotations

import re

from .university_registry import NKUST, resolve_university

NKUST_OIA_HUB_URL = "https://oia.nkust.edu.tw/"
NKUST_EXCHANGE_PAGE_URL = "https://oia.nkust.edu.tw/unit-4-374-21.html"
NKUST_SCHOLARSHIP_PAGE_URL = "https://oia.nkust.edu.tw/unit-4-377-45.html"
NKUST_SHORT_TERM_PAGE_URL = "https://oia.nkust.edu.tw/unit-4-352-39.html"
NKUST_GS_PORTAL_URL = "https://sites.google.com/nkust.edu.tw/exchange-student/"
NKUST_115_GUIDELINES_URL = "https://oia.nkust.edu.tw/images/upload/files/115%E5%AD%B8%E5%B9%B4%E5%BA%A6%E6%A0%A1%E7%B4%9A%E4%BA%A4%E6%8F%9B%E7%94%9F%E7%94%84%E9%81%B8%E7%B0%A1%E7%AB%A02025_12_02(1).pdf"
NKUST_115_PREF_FORM_URL = "https://oia.nkust.edu.tw/images/upload/files/115%E5%AD%B8%E5%B9%B4%E5%BA%A6%E6%A0%A1%E7%B4%9A%E4%BA%A4%E6%8F%9B%E7%A0%94%E4%BF%AE%E5%BF%97%E9%A1%98%E8%A1%A8(2).docx"
NKUST_115_UNI_SHEET_URL = "https://docs.google.com/spreadsheets/d/1ZdfUgev-p_N35eh2mD-vF7rH7iH8zJ3O/edit?gid=142150725#gid=142150725"
NKUST_COLLEGE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1ZdfUgev-p_N35eh2mD-vF7rH7iH8zJ3O/edit?gid=1014746314#gid=1014746314"
NKUST_REGULATIONS_URL = "https://oia.nkust.edu.tw/images/upload/files/%E5%9C%8B%EF%A7%97%E9%AB%98%E9%9B%84%E7%A7%91%E6%8A%80%E5%A4%A7%E5%AD%B8%E5%AD%B8%E7%94%9F%E8%B5%B4%E5%A2%83%E5%A4%96%E5%A4%A7%E5%AD%B8%E6%A0%A1%E9%99%A2%E4%BA%A4%E6%8F%9B%E7%A0%94%E4%BF%AE%E4%BD%9C%E6%A5%AD%E8%A6%81%E9%BB%9E.pdf"
NKUST_SCHOLARSHIP_REG_URL = "https://oia.nkust.edu.tw/images/upload/files/%E5%9C%8B%E7%AB%8B%E9%AB%98%E9%9B%84%E7%A7%91%E6%8A%80%E5%A4%A7%E5%AD%B8%E7%8D%8E%E5%8A%A9%E5%AD%B8%E7%94%9F%E8%B5%B4%E5%A2%83%E5%A4%96%E5%A4%A7%E5%AD%B8%E6%A0%A1%E9%99%A2%E7%A0%94%E4%BF%AE%E8%A6%81%E9%BB%9E(4).pdf"
NKUST_FLEC_CEF_URL = "https://flec.nkust.edu.tw/var/file/46/1046/img/581/277450219.pdf"
NKUST_116_INFO_SESSION_URL = "https://oia.nkust.edu.tw/news_det-980.html"

NKUST_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 42.0),
    "ielts": ("IELTS", 4.0),
    "toeic": ("TOEIC", 550.0),
}


def is_nkust(school_name: str | None) -> bool:
  school = resolve_university(school_name)
  if school is not None and school.id == NKUST.id:
    return True
  normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
  return normalized in {
      "國立高雄科技大學",
      "高雄科技大學",
      "高科大",
      "nkust",
      "national kaohsiung university of science and technology",
  }


def _is_graduate(degree_level: str | None) -> bool:
  text = (degree_level or "").strip()
  return any(token in text for token in ("碩", "博", "研究"))


def nkust_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
  degree = (degree_level or "").strip()
  year = (current_year or "").strip()
  if not degree:
    return (
        "needs_confirmation",
        (
            "尚未提供目前學制與年級；《國立高雄科技大學學生赴境外大學校院交換研修作業要點》及《校級交換生甄選簡章》規定：申請人須為本校大學部二年級（含）以上、研究所（含碩士班、博士班及在職專班）及五年制專科部四年級（含）以上之本國籍、僑生或外籍在學學生。"
        ),
    )
  if any(token in degree for token in ("學分班", "休學")):
    return (
        "fail",
        f"已填報 {degree}；依《國立高雄科技大學學生赴境外大學校院交換研修作業要點》規定，申請時及赴外交換期間均須保有高科大正式在學學籍（不得辦理休學或畢業離校）。",
    )
  is_grad = _is_graduate(degree)
  if not is_grad and year in {"一年級", "大一", "1", "專一", "專二", "專三", "五專一", "五專二", "五專三"}:
    return (
        "fail",
        (
            f"已填報 {degree}（{year}）；依《國立高雄科技大學學生赴境外大學校院交換研修作業要點》及校級交換甄選簡章規定，大學部須達二年級（含）以上、五專部須達四年級（含）以上始得申請赴外交換，目前年級尚未符合門檻。"
        ),
    )
  in_service_note = (
      "（注意：在職專班學生可申請校級／院系級交換，惟教育部學海飛颺／惜珠及本校高教深耕境外研修獎助金限非在職專班之本國籍學生申請）"
      if "在職" in degree
      else "（出國交換期間須全程維持高科大在學學籍並完成註冊繳費，不得辦理休學或畢業離校）"
  )
  return (
      "pass",
      f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合國立高雄科技大學赴外交換學生學制與年級規定{in_service_note}。",
  )


def nkust_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
  details: list[str] = []
  score_ok = False
  score_borderline = False

  if academic_score is not None:
    details.append(f"歷年學業總平均 {academic_score:g} 分")
    if academic_score >= 75.0:
      score_ok = True
    elif academic_score >= 60.0:
      score_borderline = True
  if academic_gpa is not None:
    details.append(f"GPA {academic_gpa:g}")
    if academic_gpa >= 2.5:
      score_ok = True
    elif academic_gpa >= 2.0:
      score_borderline = True
  if class_rank_percent is not None:
    details.append(f"班/系排名前 {class_rank_percent:g}%")
    if class_rank_percent <= 30.0:
      score_ok = True
    elif class_rank_percent <= 50.0:
      score_borderline = True

  summary = "、".join(details)
  if (
      academic_score is None
      and academic_gpa is None
      and class_rank_percent is None
  ):
    return (
        "needs_confirmation",
        (
            "尚未填寫歷年學業平均成績；高科大校級交換甄選簡章規定：申請人在當前就讀學制中須有一學期以上之學期成績且成績良好，歷年操行成績至少須達 75 分（含）以上；甄選總成績採計「在校歷年成績 20%」（無外語要求之大陸姊妹校採計 40%），且多數歐美日韓姊妹校要求 GPA 2.5–3.2（或歷年學業總平均 75–80 分）以上。"
        ),
    )

  if score_ok:
    return (
        "pass",
        (
            f"已填報 {summary}；符合國立高雄科技大學赴外交換在校成績良好標準及多數歐美日韓姊妹校 GPA 門檻（請確認中文歷年成績單上之操行成績至少達 75 分以上；校內甄選總分依「第一志願專業領域契合度 50%＋外語檢定 CEFR 等級 30%＋在校歷年成績 20%」加權比序）。"
        ),
    )

  if score_borderline:
    return (
        "needs_confirmation",
        (
            f"已填報 {summary}；符合高科大校內基本及格標準（惟請務必確認操行成績至少達 75 分以上），可申請無特定 GPA 門檻之姊妹校；部分要求 GPA 2.5–3.0（或歷年平均 75–80 分）以上之歐美日韓姊妹校請先核對各校 Fact Sheet 規定。"
        ),
    )

  return (
      "fail",
      (
          f"已填報 {summary}；未達國立高雄科技大學赴外交換學業成績良好與操行 75 分之基本要求。"
      ),
  )


def nkust_language_check(
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
            "申請赴中國大陸無外語要求之姊妹校（同濟、重慶、華南理工、華中科大、大連理工、中國海洋、上海海事等）免附外語檢定證明（甄選權重調整為：第一志願專業領域契合度 60%＋在校歷年成績 40%；惟深圳大學仍要求檢附英語檢定證明）。"
        ),
    )
  if not test or language_score is None:
    return (
        "needs_confirmation",
        (
            "尚未填寫外語檢定成績。高科大校級交換甄選將「外語檢定成績（30%）」依《外語教育中心各類外語檢定證照等級對照表》換算分數（C1 以上 100 分、B2 90 分、B1 80 分、A2 以下 70 分）：（1）英語檢定：CEFR B1 為 TOEIC 550 / TOEFL iBT 42 / ITP 460 / IELTS 4.0，CEFR B2 為 TOEIC 785 / TOEFL iBT 72 / ITP 543 / IELTS 5.5；（2）日語檢定：日本 27 校要求 JLPT N1–N5；（3）歐語／韓語：德語或法語 B1–B2、韓語 TOPIK 2–3 級或修課時數證明。"
        ),
    )
  if test in NKUST_ENGLISH_MINIMUMS:
    label, minimum = NKUST_ENGLISH_MINIMUMS[test]
    passed = language_score >= minimum
    cefr_tier = "CEFR B1（語檢項評定 80 分）"
    if (test == "toeic" and language_score >= 945) or (test == "toefl" and language_score >= 95) or (test == "ielts" and language_score >= 7.0):
      cefr_tier = "CEFR C1（語檢項滿分 100 分）"
    elif (test == "toeic" and language_score >= 785) or (test == "toefl" and language_score >= 72) or (test == "ielts" and language_score >= 5.5):
      cefr_tier = "CEFR B2（語檢項評定 90 分，符合德奧法英美多數 B2 姊妹校門檻）"
    return (
        "pass" if passed else "fail",
        (
            f"{label} {language_score:g} 對照高科大外語教育中心標準達 {cefr_tier}，符合高科大英語授課姊妹校基本申請門檻（請同時對照第一志願學校特定要求）。"
            if passed
            else f"{label} {language_score:g} 未達高科大 CEFR B1 基本外語檢定門檻（{label} {minimum:g}，屬 CEFR A2 以下）；請留意第一志願姊妹校是否要求 CEFR B1 或 B2 以上成績。"
        ),
    )
  if test == "jlpt":
    passed = 1.0 <= language_score <= 5.0
    level = int(language_score)
    tier_note = (
        "符合高科大所有 27 所日本姊妹校（含明治、關西、京都外大本科、同志社女子、千葉、神戶、龍谷、信州、熊本、東京海洋等 N1–N2 學校）日語門檻"
        if level in (1, 2)
        else (
            "符合愛媛、長崎、鹿兒島、福岡工大、高知、福井縣立、獨協、大東文化、京都外大日本語學習課程、流通科學、神戶等 N3 日本姊妹校門檻"
            if level == 3
            else "符合鹿兒島國際大學（N4）、靜岡理工科大學（N5）及接受英語成績或初級日語之日本姊妹校門檻"
        )
    )
    return (
        "pass" if passed else "fail",
        f"JLPT N{level} {'符合' if passed else '未達'}國立高雄科技大學日本姊妹校日語檢定採計標準（{tier_note}）。",
    )
  if test == "topik":
    passed = 1.0 <= language_score <= 6.0
    return (
        "pass" if passed else "fail",
        f"TOPIK {int(language_score)} 級 {'符合' if passed else '未達'}國立高雄科技大學韓國 8 所姊妹校（韓國海洋、仁荷、漢陽 ERICA、慶尚國立、朝鮮、聖潔、韓世等）韓語檢定採計標準。",
    )
  return (
      "needs_confirmation",
      (
          f"已填寫 {language_test} {language_score:g}；請對照《國立高雄科技大學外語教育中心各類外語檢定證照等級對照表》（{NKUST_FLEC_CEF_URL}）及《115學年度校級交換學校一覽表》確認是否符合志願姊妹校規定。"
      ),
  )
