from __future__ import annotations

import re

from .university_registry import YUNTECH, resolve_university

YUNTECH_OIA_HUB_URL = "https://tdx.yuntech.edu.tw/"
YUNTECH_OE_PORTAL_URL = "https://admissions-oia.yuntech.edu.tw/oe/index/index/puid/115-2/lang/zh_TW"
YUNTECH_OE_INTRO_115_2_URL = "https://admissions-oia.yuntech.edu.tw/oe/index/intro/puid/115-2/lang/zh_TW"
YUNTECH_OUTBOUND_NON_MAINLAND_URL = "https://tdx.yuntech.edu.tw/index.php/zh-tw/%E5%87%BA%E5%9C%8B%E4%BA%A4%E6%B5%81/%E5%87%BA%E5%9C%8B%E4%BA%A4%E6%8F%9B%E7%94%9F/%E9%9D%9E%E5%A4%A7%E9%99%B8%E5%9C%B0%E5%8D%80%E4%BA%A4%E6%8F%9B%E7%94%9F"
YUNTECH_MAINLAND_2027S_URL = "https://tdx.yuntech.edu.tw/index.php/zh-tw/%E5%87%BA%E5%9C%8B%E4%BA%A4%E6%B5%81/%E5%87%BA%E5%9C%8B%E4%BA%A4%E6%8F%9B%E7%94%9F/%E5%A4%A7%E9%99%B8%E5%9C%B0%E5%8D%80%E4%BA%A4%E6%8F%9B%E7%94%9F/2027%E6%98%A5%E5%AD%A3%E7%8F%AD"
YUNTECH_APPLY_2027S_URL = "https://tdx.yuntech.edu.tw/index.php/zh-tw/component/k2/item/1413-2027"
YUNTECH_ROSTER_2027S_URL = "https://tdx.yuntech.edu.tw/index.php/zh-tw/component/k2/item/1472-2027"
YUNTECH_EXCHANGE_GUIDELINES_URL = "https://tdx.yuntech.edu.tw/images/International_Exchange_Students/Outgoing/Non_mainland_China_area/%E5%9C%8B%E7%AB%8B%E9%9B%B2%E6%9E%97%E7%A7%91%E6%8A%80%E5%A4%A7%E5%AD%B8%E5%9C%8B%E9%9A%9B%E4%BA%A4%E6%8F%9B%E5%AD%B8%E7%94%9F%E5%AF%A6%E6%96%BD%E8%A6%81%E9%BB%9E20250422.pdf"
YUNTECH_SCORING_RUBRIC_URL = "https://tdx.yuntech.edu.tw/images/International_Exchange_Students/Outgoing/Non_mainland_China_area/%E9%9D%9E%E5%A4%A7%E9%99%B8%E5%9C%B0%E5%8D%80%E4%BA%A4%E6%8F%9B%E5%AD%B8%E7%94%9F%E8%A9%95%E5%88%86%E6%A8%99%E6%BA%96%E8%A1%A8.pdf"
YUNTECH_SLIDES_2027S_URL = "https://tdx.yuntech.edu.tw/images/International_Exchange_Students/Outgoing/Non_mainland_China_area/2027%E6%98%A5%E5%AD%A3(115-2)%E8%B5%B4%E9%9D%9E%E5%A4%A7%E9%99%B8%E5%9C%B0%E5%8D%80%E7%B0%A1%E5%A0%B1.pdf"
YUNTECH_GRANT_PAGE_URL = "https://tdx.yuntech.edu.tw/index.php/zh-tw/%E5%87%BA%E5%9C%8B%E4%BA%A4%E6%B5%81/%E7%8D%8E%E5%8A%A9%E5%AD%B8%E9%87%91/%E5%87%BA%E5%9C%8B%E4%BA%A4%E6%B5%81%E6%88%96%E9%80%B2%E4%BF%AE%E8%A3%9C%E5%8A%A9/115%E5%B9%B4%E5%BA%A6"
YUNTECH_SUBSIDY_RULES_URL = "https://tdx.yuntech.edu.tw/images/Scholarship/%E5%9C%8B%E7%AB%8B%E9%9B%B2%E6%9E%97%E7%A7%91%E6%8A%80%E5%A4%A7%E5%AD%B8%E5%AD%B8%E7%94%9F%E5%87%BA%E5%9C%8B%E4%BA%A4%E6%B5%81%E6%88%96%E9%80%B2%E4%BF%AE%E8%A3%9C%E5%8A%A9%E8%A6%81%E9%BB%9E_11406.pdf"
YUNTECH_WANG_PAGE_URL = "https://tdx.yuntech.edu.tw/index.php/zh-tw/%E5%87%BA%E5%9C%8B%E4%BA%A4%E6%B5%81/%E7%8D%8E%E5%8A%A9%E5%AD%B8%E9%87%91/%E7%8E%8B%E7%A7%8B%E9%9B%84%E6%A6%AE%E8%AD%BD%E5%8D%9A%E5%A3%AB%E7%8D%8E%E5%8A%A9%E9%87%91/115%E5%AD%B8%E5%B9%B4%E5%BA%A6"
YUNTECH_WANG_RULES_URL = "https://tdx.yuntech.edu.tw/images/Scholarship/%E7%8E%8B%E7%A7%8B%E9%9B%84%E6%A6%AE%E8%AD%BD%E5%8D%9A%E5%A3%AB%E8%A3%9C%E5%8A%A9%E5%BE%B7%E6%97%A5%E7%BE%8E%E4%BA%A4%E6%B5%81%E6%88%96%E9%80%B2%E4%BF%AE%E7%8D%8E%E5%8A%A9%E9%87%91%E5%AF%A6%E6%96%BD%E8%A6%81%E9%BB%9E%E5%8F%8A%E7%99%BC%E6%94%BE%E4%BD%9C%E6%A5%AD%E8%A6%8F%E5%AE%9A20240710.pdf"
YUNTECH_XUEHAI_PAGE_URL = "https://tdx.yuntech.edu.tw/index.php/zh-tw/component/k2/item/1400-115"
YUNTECH_XUEHAI_RULES_URL = "https://tdx.yuntech.edu.tw/images/Scholarship/%E5%AD%B8%E6%B5%B7%E7%B3%BB%E5%88%97/%E5%9C%8B%E7%AB%8B%E9%9B%B2%E6%9E%97%E7%A7%91%E6%8A%80%E5%A4%A7%E5%AD%B8%E3%80%8C%E5%AD%B8%E6%B5%B7%E9%A3%9B%E9%A2%BA%E3%80%8D%E8%88%87%E3%80%8C%E5%AD%B8%E6%B5%B7%E6%83%9C%E7%8F%A0%E3%80%8D%E5%B0%88%E6%A1%88%E6%8E%A8%E8%96%A6%E4%BD%9C%E6%A5%AD%E8%A6%81%E9%BB%9E1130422%E4%BF%AE%E8%A8%82%E9%80%9A%E9%81%8E.pdf"
YUNTECH_DUAL_DEGREE_URL = "https://tdx.yuntech.edu.tw/index.php/zh-tw/%E5%87%BA%E5%9C%8B%E4%BA%A4%E6%B5%81/%E9%9B%99%E8%81%AF%E5%AD%B8%E4%BD%8D"
YUNTECH_PATHWAY_URL = "https://tdx.yuntech.edu.tw/index.php/zh-tw/%E5%87%BA%E5%9C%8B%E4%BA%A4%E6%B5%81/%E9%8A%9C%E6%8E%A5%E5%AD%B8%E4%BD%8D"
YUNTECH_EXP_115_URL = "https://tdx.yuntech.edu.tw/index.php/expsharing/item/1401-115"

YUNTECH_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 61.0),
    "ielts": ("IELTS", 5.0),
    "toeic": ("TOEIC", 650.0),
}


def is_yuntech(school_name: str | None) -> bool:
  school = resolve_university(school_name)
  if school is not None and school.id == YUNTECH.id:
    return True
  normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
  return normalized in {
      "國立雲林科技大學",
      "雲林科技大學",
      "雲科大",
      "yuntech",
      "nyust",
      "national yunlin university of science and technology",
  }


def _is_graduate(degree_level: str | None) -> bool:
  text = (degree_level or "").strip()
  return any(token in text for token in ("碩", "博", "研究"))


def yuntech_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
  degree = (degree_level or "").strip()
  year = (current_year or "").strip()
  if not degree:
    return (
        "needs_confirmation",
        (
            "尚未提供目前學制與年級；《國立雲林科技大學國際交換學生實施要點》第2點規定：申請人須為本校研究所在學學生，或入學一學期以上之大學部在學學生（應屆畢業生經核准獲交換學校同意交換者，得申請延長修業年限最長一年）。"
        ),
    )
  if any(token in degree for token in ("學分班", "休學")):
    return (
        "fail",
        f"已填報 {degree}；依《國立雲林科技大學國際交換學生實施要點》規定，申請時及赴外交換期間均須保有雲科大在學學籍並履行註冊繳費義務。",
    )
  is_grad = _is_graduate(degree)
  if not is_grad and year in {"大一上"}:
    return (
        "fail",
        (
            f"已填報 {degree}（{year}）；依《國立雲林科技大學國際交換學生實施要點》第2點規定，大學部學生須入學一學期以上始得申請出國交換。"
        ),
    )
  in_service_note = (
      "（注意：依《國際交換學生實施要點》第5點規定，在職專班學生得參加甄選交換學生，但不得申請本校獎學金之補助）"
      if "在職" in degree
      else "（出國交換期間並未免除在本校之註冊及繳費義務，仍須辦理本校註冊並繳交學雜費）"
  )
  return (
      "pass",
      f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合國立雲林科技大學國際交換學生學制與年級規定{in_service_note}。",
  )


def yuntech_academic_check(
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
    elif academic_score >= 70.0:
      score_borderline = True
  if class_rank_percent is not None:
    details.append(f"班級排名前 {class_rank_percent:g}%")
    if class_rank_percent <= 50.0:
      score_ok = True
  if academic_gpa is not None:
    details.append(f"GPA {academic_gpa:g}")
    if academic_gpa >= 2.75:
      score_ok = True
    elif academic_gpa >= 2.5:
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
            "尚未填寫歷年學業平均成績或班級排名比率；《國立雲林科技大學國際交換學生實施要點》第2點規定：申請人歷年學業成績須達 75 分（含）以上或班級排名前 50%，且操行成績達 80 分（含）以上。非大陸地區校內甄選『學業成績及班級排名比率』佔總分 40%（大學部平均成績 20%＋班排比率 20%；研究所無班排者平均成績 40%）。"
        ),
    )

  if score_ok:
    return (
        "pass",
        (
            f"已填報 {summary}；符合國立雲林科技大學《國際交換學生實施要點》第2點「學業成績達 75 分（含）以上或班級排名前 50%」之門檻（請同時確認歷年操行成績達 80 分以上；校內甄選依「學業及班排 40%＋語言能力證明 40%＋其他優秀表現 20%」計分）。"
        ),
    )

  if score_borderline:
    return (
        "needs_confirmation",
        (
            f"已填報 {summary}；若歷年學業平均未達 75 分，請確認「歷年班級排名是否居前 50%」且操行成績達 80 分以上（符合其一即達雲科大校內學業門檻）。"
        ),
    )

  return (
      "fail",
      (
          f"已填報 {summary}；未達國立雲林科技大學《國際交換學生實施要點》第2點「學業成績達 75 分（含）以上或班級排名前 50%，且操行成績達 80 分以上」之規定。"
      ),
  )


def yuntech_language_check(
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
            "申請赴中國大陸地區交換學校免附外語能力檢定證明（依《國立雲林科技大學國際交換學生實施要點》第2點第7款規定，赴大陸地區不在此限）。"
        ),
    )
  if partner_country in {"印尼", "越南", "馬來西亞", "菲律賓"} and (
      not test or language_score is None
  ):
    return (
        "needs_confirmation",
        (
            f"申請赴東南亞地區（{partner_country}）交換學校，依《國際交換學生實施要點》第2點第7款不受校內 TOEIC 650 底線限制，惟仍須符合該接待校規定之語言門檻，且檢附有效語檢證明可獲校內甄選「語言能力證明（最高 40 分）」加分。"
        ),
    )
  if not test or language_score is None:
    return (
        "needs_confirmation",
        (
            "尚未填寫外語檢定成績。依《國立雲林科技大學國際交換學生實施要點》第2點第7款及《非大陸地區交換學生評分標準表》規定：申請以英文授課之交換學校，語言能力應達 TOEIC 650 分或同等能力標準（赴大陸地區、東南亞地區不在此限）；且「語言能力證明」佔甄選總分 40%（C1 如 TOEIC 945 / iBT 95 / IELTS 7.0 / JLPT N1 得 40 分；B2 如 TOEIC 785 / iBT 72 / IELTS 5.5 / JLPT N2 得 30 分；B1 如 TOEIC 550 / iBT 42 / IELTS 4.0 / JLPT N3 得 20 分；A2 得 10 分；A1 得 5 分）。"
        ),
    )
  if test in YUNTECH_ENGLISH_MINIMUMS:
    label, minimum = YUNTECH_ENGLISH_MINIMUMS[test]
    is_sea = partner_country in {"印尼", "越南", "馬來西亞", "菲律賓"}
    passed = language_score >= (550.0 if test == "toeic" and is_sea else minimum)
    score_pts = "10 分（CEFR A2）"
    if (test == "toeic" and language_score >= 945) or (test == "toefl" and language_score >= 95) or (test == "ielts" and language_score >= 7.0):
      score_pts = "40 分滿分（CEFR C1）"
    elif (test == "toeic" and language_score >= 785) or (test == "toefl" and language_score >= 72) or (test == "ielts" and language_score >= 5.5):
      score_pts = "30 分（CEFR B2，符合歐美多數名校及王秋雄榮譽博士獎助金美國線 B2 門檻）"
    elif (test == "toeic" and language_score >= 550) or (test == "toefl" and language_score >= 42) or (test == "ielts" and language_score >= 4.0):
      score_pts = "20 分（CEFR B1，符合王秋雄榮譽博士獎助金德國／日本線 B1 門檻）"
    return (
        "pass" if passed else ("needs_confirmation" if language_score >= 550 or is_sea else "fail"),
        (
            f"{label} {language_score:g} 符合雲科大英語授課交換學校基準（{label} {minimum:g}），對照《非大陸地區交換學生評分標準表》可獲語檢項目 {score_pts}。"
            if passed
            else f"{label} {language_score:g} 對照評分標準表為 {score_pts}；若申請歐美英語授課姊妹校，校內基準為 TOEIC 650（或同等標準 TOEFL iBT 61 / IELTS 5.0），赴東南亞地區或非英語授課學程則依接待校規定辦理。"
        ),
    )
  if test == "jlpt":
    passed = 1.0 <= language_score <= 5.0
    level = int(language_score)
    pts_map = {1: 40, 2: 30, 3: 20, 4: 10, 5: 5}
    pts = pts_map.get(level, 0)
    tier_note = (
        f"對照《非大陸地區交換學生評分標準表》獲語檢項目 {pts} 分，且符合《王秋雄榮譽博士獎助金》日本線 N2 以上門檻及千葉、福井、琉球、岡山縣立、大阪工大、神戶藝術工科、福岡大學等日本姊妹校規定"
        if level in (1, 2)
        else (
            f"對照《非大陸地區交換學生評分標準表》獲語檢項目 {pts} 分，符合神戶藝術工科大學、岡山縣立大學、福岡大學等 N3 日本姊妹校門檻"
            if level == 3
            else f"對照《非大陸地區交換學生評分標準表》獲語檢項目 {pts} 分，請確認目標日本姊妹校是否要求 N2–N3 或英語 TOEIC 650 以上"
        )
    )
    return (
        "pass" if level in (1, 2, 3) else ("needs_confirmation" if passed else "fail"),
        f"JLPT N{level} {'符合' if passed else '未達'}國立雲林科技大學日本姊妹校日語檢定採計標準（{tier_note}）。",
    )
  if test == "topik":
    passed = 1.0 <= language_score <= 6.0
    return (
        "pass" if passed else "fail",
        f"TOPIK {int(language_score)} 級 {'符合' if passed else '未達'}國立雲林科技大學韓國 8 所姊妹校（首爾科技大學、建國大學、高麗大學世宗校區、弘益大學、檀國大學、同德女子大學、韓巴大學、清州大學）韓語檢定採計標準。",
    )
  return (
      "needs_confirmation",
      (
          f"已填寫 {language_test} {language_score:g}；請對照《國立雲林科技大學非大陸地區交換學生評分標準表》（{YUNTECH_SCORING_RUBRIC_URL}）及出國交換生系統各校簡章確認是否符合志願姊妹校規定。"
      ),
  )
