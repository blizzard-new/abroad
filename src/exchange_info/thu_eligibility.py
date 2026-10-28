from __future__ import annotations

import re

from .university_registry import THU, resolve_university

THU_OIR_HOME_URL = "https://oir.thu.edu.tw/"
THU_EXCHANGE_OVERVIEW_URL = (
    "https://oir.thu.edu.tw/front/301_ex_overview/302_Out_EX_Prog/302_1_Qualifica?lang=tw"
)
THU_EXCHANGE_SELECTION_URL = (
    "https://oir.thu.edu.tw/front/301_ex_overview/302_Out_EX_Prog/302_2_Interview?lang=tw"
)
THU_SCHOLARSHIPS_URL = (
    "https://oir.thu.edu.tw/front/301_ex_overview/302_Out_EX_Prog/302_3_Tuition_S?lang=tw"
)
THU_PRE_DEPARTURE_URL = (
    "https://oir.thu.edu.tw/front/301_ex_overview/302_Out_EX_Prog/302_4_Departure?lang=tw"
)
THU_POST_RETURN_URL = (
    "https://oir.thu.edu.tw/front/301_ex_overview/302_Out_EX_Prog/302_5_Important?lang=tw"
)
THU_OBLIGATIONS_URL = (
    "https://oir.thu.edu.tw/front/301_ex_overview/302_Out_EX_Prog/302_6_Regulatio?lang=tw"
)
THU_FAQ_URL = (
    "https://oir.thu.edu.tw/front/301_ex_overview/302_Out_EX_Prog/302_7_Exchange_?lang=tw"
)
THU_EXPERIENCES_URL = (
    "https://oir.thu.edu.tw/front/301_ex_overview/302_Out_EX_Prog/302_8_Exchange_?lang=tw"
)
THU_CN_EXCHANGE_URL = (
    "https://oir.thu.edu.tw/front/301_ex_overview/308_Exchange_Pr/308_CN_out_ex_1?lang=tw"
)
THU_DUAL_DEGREE_URL = (
    "https://oir.thu.edu.tw/front/303_Dual_Degree/303_1_OutDual?lang=tw"
)
THU_PARTNERSHIP_URL = (
    "https://oir.thu.edu.tw/front/200_exchange/201_Partnership/201_1_Asia?lang=tw"
)
THU_CROSS_STRAIT_PARTNERS_URL = (
    "https://oir.thu.edu.tw/front/200_exchange/202_Cross_Strai?lang=tw"
)
THU_COOPERATION_DB_URL = "https://oir.thu.edu.tw/cooperation/index.php"
THU_2027_SPRING_NEWS_URL = (
    "https://oir.thu.edu.tw/front/NEWS/news.php?ID=dGh1X29pciZORVdT&Sn=1323&lang=tw"
)
THU_2027_SPRING_BROCHURE_PDF_URL = (
    "https://oir.thu.edu.tw/upload/ck/files/2027%E5%B9%B4%E6%98%A5%E5%AD%B8%E6%9C%9F%E6%9D%B1%E6%B5%B7%E5%A4%A7%E5%AD%B8%E8%B5%B4%E5%85%A8%E7%90%83%E5%A7%8A%E5%A6%B9%E6%A0%A1%E4%BA%A4%E6%8F%9B%E7%94%84%E8%A9%A6%E7%B0%A1%E7%AB%A01012%E6%9B%B4.pdf"
)
THU_2026_FALL_BROCHURE_PDF_URL = (
    "https://oir.thu.edu.tw/upload/ck/files/2026%E5%B9%B4%E7%A7%8B%E5%AD%B8%E6%9C%9F%E6%9D%B1%E6%B5%B7%E5%A4%A7%E5%AD%B8%E8%B5%B4%E5%85%A8%E7%90%83%E5%A7%8A%E5%A6%B9%E6%A0%A1%E4%BA%A4%E6%8F%9B%E7%94%84%E8%A9%A6%E7%B0%A1%E7%AB%A00317%E6%9B%B4.pdf"
)
THU_RULE_UPDATE_PDF_URL = (
    "https://oir.thu.edu.tw/upload/ck/files/%E4%BA%A4%E6%8F%9B%E7%94%84%E9%81%B8%E8%BE%A6%E6%B3%95%E9%87%8D%E5%A4%A7%E6%9B%B4%E6%96%B0%E9%80%9A%E7%9F%A520251118.pdf"
)
THU_SPROUT_GRANT_PDF_URL = (
    "https://oir.thu.edu.tw/upload/ck/files/%E9%AB%98%E7%AD%89%E6%95%99%E8%82%B2%E6%B7%B1%E8%80%95%E8%A8%88%E7%95%AB%E5%9C%8B%E9%9A%9B%E7%A7%BB%E5%8B%95%E5%8A%9B%E6%B4%BB%E5%8B%95%E7%8D%8E%E8%A3%9C%E5%8A%A9%E5%AF%A6%E6%96%BD%E8%A6%81%E9%BB%9E%282%29.pdf"
)

THU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 42.0),
    "ielts": ("IELTS", 5.0),
    "toefl_itp": ("TOEFL ITP", 430.0),
}


def is_thu(school_name: str | None) -> bool:
  school = resolve_university(school_name)
  if school is not None and school.id == THU.id:
    return True
  normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
  return normalized in {
      "東海大學",
      "東海",
      "thu",
      "tunghai university",
      "tunghai",
  }


def _is_graduate(degree_level: str | None) -> bool:
  text = (degree_level or "").strip()
  return any(token in text for token in ("碩", "博", "研究"))


def thu_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
  degree = (degree_level or "").strip()
  year = (current_year or "").strip()
  if not degree:
    return (
        "needs_confirmation",
        (
            "尚未提供目前學制與年級；依《東海大學赴全球姊妹校交換甄試簡章》及國際暨兩岸合作處《申請資格》：申請人須為本校修業滿一學期的在學學生（含學士班、碩士班、博士班及轉學生，不含碩士在職專班），且赴外交換學習期間須具備東海大學在學身分。同一教育階段赴境外研修期限（除修讀雙聯學位者外）合計以一學年（二學期）為限；自 2026 年秋季甄試起，當學期已在外校研修或交換之同學亦開放報名參加長期交換甄試。"
        ),
    )
  if any(
      token in degree or token in year
      for token in ("在職專班", "碩專", "emba", "EMBA", "學分班", "選修生", "休學")
  ):
    return (
        "fail",
        (
            f"已填報 {degree}{f'（{year}）' if year else ''}；依東海大學《赴全球姊妹校交換甄試簡章》，碩士在職專班、休學生及無正式學籍選讀生不得申請赴全球姊妹校交換計畫。"
        ),
    )
  if year in {"大一上", "碩一上", "博一上", "研一上", "一年級上學期"}:
    return (
        "fail",
        (
            f"已填報 {degree}（{year}）；依東海大學《赴全球姊妹校交換甄試簡章》，申請人須為本校修業滿一學期的在學學生（須具備至少一學期東海歷年成績單與名次證明書），一年級上學期新生尚無前一學期成績，須於一年級下學期起申請。"
        ),
    )
  is_grad = _is_graduate(degree)
  grad_note = (
      "（提醒：部分姊妹校如日本佛教大學、韓國全北大學、東北林業大學僅限大學部申請；日本立命館亞洲太平洋大學研究生僅限修讀大學部課程；北京大學與復旦大學碩士班申請人須達 GPA 4.0 以上）"
      if is_grad
      else "（提醒：申請雙聯學位計畫原則上須為大三或大四在學學生且累計 GPA 達 3.0 以上；同一學制階段赴境外交換研修期限除雙聯學位外以一年為限）"
  )
  return (
      "pass",
      (
          f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合東海大學赴全球暨兩岸姊妹校交換甄試與雙聯學位計畫之在學學制及修業學期規定{grad_note}。"
      ),
  )


def thu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
  score_min = 70.0
  gpa_min = 2.5
  rank_max = 50.0
  details: list[str] = []
  passes_global = False
  passes_mainland = False

  if academic_score is not None:
    details.append(f"學業平均 {academic_score:g} 分")
    if academic_score >= score_min:
      passes_global = True
      passes_mainland = True
    elif academic_score >= 65.0:
      passes_mainland = True
  if academic_gpa is not None:
    details.append(f"GPA {academic_gpa:g}")
    if academic_gpa >= gpa_min:
      passes_global = True
      passes_mainland = True
    elif academic_gpa >= 2.0:
      passes_mainland = True
  if class_rank_percent is not None:
    details.append(f"歷年學期班排名百分比平均前 {class_rank_percent:g}%")
    if class_rank_percent <= rank_max:
      passes_global = True
      passes_mainland = True

  summary = "、".join(details)
  if (
      academic_score is None
      and academic_gpa is None
      and class_rank_percent is None
  ):
    return (
        "needs_confirmation",
        (
            "尚未填寫歷年學期 GPA、學業平均或班排名百分比；依東海大學《2027 年春學期／2026 年秋學期赴全球姊妹校交換甄試簡章》：（1）「全球暨港澳組」歷年學期 GPA 須達 2.5（含，約百分制 70 分）以上（早稻田大學、關西學院大學、龍谷大學、馬來亞大學、印尼總統大學、美國天普／北帕克／愛達荷／SUNY ESF／雙聯學位、哥倫比亞羅薩里奧大學、德國柏林管理學院、匈牙利卡洛里大學要求 GPA 3.0 以上；法國圖爾-昂熱-勒芒高等美術學院要求 GPA 3.5 以上）；（2）「大陸組」歷年學期 GPA 須達 2.0（含）以上（北京大學、復旦大學要求大學部歷年班排名平均前 25%［2027 春］／前 10%［2026 秋］或碩士班 GPA 4.0 以上；西安交通大學要求 GPA 高於 2.8/4.3 且無不及格科目）；（3）甄試總成績採計：歷年學期班排名百分比平均 20%、外語能力 30%、歷年學期 GPA 平均 15%、學行優良表現 35%，完成基本勞作教育另加總分 5 分。"
        ),
    )

  if passes_global:
    high_gpa_note = (
        "同時達到早稻田大學、天普大學、愛達荷大學、SUNY ESF、關西學院大學、馬來亞大學及美方雙聯學位之 GPA 3.0 高門檻標準"
        if (academic_gpa is not None and academic_gpa >= 3.0)
        or (academic_score is not None and academic_score >= 78.0)
        else "符合東海大學「全球暨港澳組」姊妹校交換門檻（GPA 2.5／約 70 分以上）與「大陸組」門檻（GPA 2.0 以上）；惟申請早稻田、天普、愛達荷、SUNY ESF、關西學院、馬來亞、羅薩里奧或美方雙聯學位須達 GPA 3.0 以上"
    )
    return (
        "pass",
        (
            f"已填報 {summary}；符合東海大學赴全球姊妹校交換甄試學業標準（{high_gpa_note}）。"
        ),
    )

  if passes_mainland:
    return (
        "needs_confirmation",
        (
            f"已填報 {summary}；符合東海大學「大陸組」交換生甄試最低門檻（GPA 2.0 以上），惟未達「全球暨港澳組」最低門檻（GPA 2.5／約百分制 70 分以上）。若欲選填全球暨港澳組姊妹校，須提升歷年 GPA 至 2.5 以上。"
        ),
    )

  return (
      "fail",
      (
          f"已填報 {summary}；未達東海大學《赴全球姊妹校交換甄試簡章》之最低學業門檻（全球暨港澳組須達 GPA 2.5／約 70 分以上，大陸組須達 GPA 2.0／約 65 分以上）。"
      ),
  )


def thu_language_check(
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
            "申請赴中國大陸地區姊妹校（含北京大學、復旦大學、南京大學、同濟大學、西安交通大學、北京師範大學、中國人民大學、廈門大學、中山大學、四川大學、天津大學、南開大學等）屬「大陸組」，免附外語能力檢定證明，且外語能力項目（30%）於大陸組一律不計分。"
        ),
    )
  if not test or language_score is None:
    return (
        "needs_confirmation",
        (
            "尚未填寫外語能力檢定成績。依東海大學《赴全球姊妹校交換甄試簡章》外語能力計分表（占甄試總分 30%，擇最優單一成績採計）：（1）英語檢定採認 TOEFL ITP（430–677）、TOEFL iBT（42–120）或 IELTS（5.0–9.0），多數歐美及亞洲英語授課姊妹校要求 TOEFL iBT 72–80 或 IELTS 5.5–6.5（馬來西亞拉曼大學接受 iBT 45 / IELTS 5.0、韓國全北大學 iBT 60 / IELTS 5.5、日本武藏野大學 iBT 61 / IELTS 5.5、美國北方中心學院 iBT 68 / IELTS 5.5）；（2）日語檢定採認 JLPT N5–N1（日本東海大學與愛知縣立大學接受 N5，龍谷大學 N4，昭和女子／山口／島根／信州／東洋／西南學院大學接受 N3，多數日本姊妹校要求 N2，早稻田／國際基督教大學／武藏野日語組要求 N1）；（3）韓語檢定採認 TOPIK 1–6 級（全北大學 2 級、啟明大學與漢陽 ERICA 3 級、建國／梨花女大／延世大學 4 級，或以 TOEFL iBT / IELTS 替代）；（4）歐語檢定採認 CEFR B1–C2（西班牙羅薩里奧大學要求西語 B1，法國圖爾-昂熱-勒芒高等美術學院要求法語 B2）；（5）大陸組免附外語檢定。"
        ),
    )
  if test in THU_ENGLISH_MINIMUMS:
    label, minimum = THU_ENGLISH_MINIMUMS[test]
    passed = language_score >= minimum
    tier_note = "達東海交換甄試外語能力計分表 Level F（8%）基準，可申請馬來西亞拉曼大學（iBT 45 / IELTS 5.0）等基礎門檻校"
    if (
        (test == "toefl" and language_score >= 95)
        or (test == "ielts" and language_score >= 7.0)
        or (test == "toefl_itp" and language_score >= 627)
    ):
      tier_note = "達東海交換甄試外語能力計分表 Level C–A（20%–30%）高分標準，並符合全部歐美、日韓、東協與港澳英語授課姊妹校及美方雙聯學位最高門檻（含盧昂高等電機電子學院、企業創造領導學院、諾歐商學院 iBT 85 / IELTS 6.5、雪菲爾大學與哥本哈根大學 iBT 80 / IELTS 6.5）"
    elif (
        (test == "toefl" and language_score >= 80)
        or (test == "ielts" and language_score >= 6.5)
        or (test == "toefl_itp" and language_score >= 585)
    ):
      tier_note = "達東海交換甄試外語能力計分表 Level D–E（15%–18%），符合英國雪菲爾大學、丹麥哥本哈根大學、日本早稻田大學、關西外大、立命館 APU、韓國延世／建國／梨花女大、美國天普／愛達荷／羅德島／南佛羅里達／SUNY ESF 等主流姊妹校門檻"
    elif (
        (test == "toefl" and language_score >= 72)
        or (test == "ielts" and language_score >= 6.0)
        or (test == "toefl_itp" and language_score >= 543)
    ):
      tier_note = "達東海交換甄試外語能力計分表 Level E（15%），符合大多數歐洲（德、法、西、義、捷、波、立、匈、瑞、奧）、東南亞（馬希竇、SIIT、日惹、萬隆天主教、慈育、胡志明經濟大學）及香港浸會／嶺南大學（IELTS 6.0）門檻"
    return (
        "pass" if passed else "fail",
        (
            f"{label} {language_score:g} {'符合' if passed else '未達'}東海大學全球暨港澳組交換甄試外語能力採計基準（最低採計門檻：{label} {minimum:g}；{tier_note}）。"
        ),
    )
  if test == "toeic":
    if partner_country in {"中國大陸"}:
      return (
          "pass",
          f"TOEIC {language_score:g}：申請赴中國大陸地區姊妹校屬「大陸組」，免附外語檢定證明。",
      )
    return (
        "needs_confirmation",
        (
            f"已填報 TOEIC {language_score:g}；提醒您：東海大學《赴全球姊妹校交換甄試簡章》外語能力計分表（30%）僅採計 TOEFL ITP、TOEFL iBT、IELTS、CEFR 歐語檢定、JLPT 及 TOPIK（另培力英檢 BESTEP 可於「學行優良表現」加 5 分），一般姊妹校交換不採計多益 TOEIC（僅西班牙馬拉加大學 Erasmus+ 交換專案採認 TOEIC 聽讀 785／說寫 310，或可用於申請《東海大學學生參加英語檢定考試補助辦法》報名費補助）。建議報考 TOEFL ITP、TOEFL iBT 或 IELTS 以取得全球暨港澳組外語積分與選校資格。"
        ),
    )
  if test == "jlpt":
    level = int(language_score)
    passed = 1 <= level <= 5
    if level == 1:
      tier_note = "達東海交換甄試外語能力計分表 Level B（25%，滿分則為 Level A 30%），符合日本早稻田大學、國際基督教大學、武藏野大學（N1）及全部 29 所日本姊妹校最高門檻"
    elif level == 2:
      tier_note = "達東海交換甄試外語能力計分表 Level C（20%），符合立命館大學、立命館 APU、橫濱市立大學、奈良女子大學、御茶水女子大學、甲南大學、櫻美林大學、東洋大學、關西學院大學、大分大學、高知大學、北星學園大學、沖繩國際大學、佛教大學、桃山學院大學等絕大多數日本姊妹校 N2 門檻（早稻田、ICU、武藏野日語組需 N1）"
    elif level == 3:
      tier_note = "達東海交換甄試外語能力計分表 Level E（15%），可申請日本昭和女子大學（日語課程 N3）、琉球大學、島根大學、山口大學、信州大學、東洋大學、西南學院大學等 N3 門檻姊妹校"
    elif level == 4:
      tier_note = "達東海交換甄試外語能力計分表 Level F（8%），可申請日本龍谷大學（N4）、東海大學（N5）、愛知縣立大學（N5）"
    else:
      tier_note = "達東海交換甄試外語能力計分表 Level G（4%），可申請日本東海大學（N5）與愛知縣立大學（N5，限一學年交換）"
    return (
        "pass" if passed else "fail",
        f"JLPT N{level} {'符合' if passed else '未達'}東海大學日本姊妹校交換外語檢定基準（{tier_note}）。",
    )
  if test == "topik":
    level = int(language_score)
    passed = 1 <= level <= 6
    if level >= 4:
      tier_note = "達東海交換甄試外語能力計分表 Level D–B（18%–25%），符合韓國延世大學、建國大學、梨花女子大學（TOPIK 4 級）、啟明大學、漢陽大學 ERICA（3 級）與全北大學（2 級）全部韓國姊妹校韓語門檻"
    elif level == 3:
      tier_note = "達東海交換甄試外語能力計分表 Level E（15%），符合韓國啟明大學、漢陽大學安山校區（ERICA）TOPIK 3 級與全北大學 TOPIK 2 級門檻"
    elif level == 2:
      tier_note = "達東海交換甄試外語能力計分表 Level F（8%），符合韓國全北大學 TOPIK 2 級門檻（延世、建國、梨花女大需 TOPIK 4 級或改以 TOEFL iBT / IELTS 申請）"
    else:
      tier_note = "達東海交換甄試外語能力計分表 Level G（4%），惟韓國姊妹校最低要求全北大學 TOPIK 2 級、啟明／漢陽 ERICA 3 級、延世／建國／梨花女大 4 級（或改以英語檢定 TOEFL iBT / IELTS 申請）"
    return (
        "pass" if passed else "fail",
        f"TOPIK {level} 級{'符合' if passed else '未達'}東海大學韓國姊妹校交換與外語計分基準（{tier_note}）。",
    )
  return (
      "needs_confirmation",
      f"已填報語言檢定 {language_test}（{language_score:g}）；請對照東海大學《赴全球姊妹校交換甄試簡章》外語能力計分表（TOEFL ITP / TOEFL iBT / IELTS / CEFR / JLPT / TOPIK）與目標姊妹校語言門檻確認。",
  )
