from __future__ import annotations

import re

from .university_registry import PU, resolve_university

PU_OIA_HOME_URL = "https://oia.pu.edu.tw/"
PU_411_HOME_URL = "https://411.pu.edu.tw/"
PU_EXCHANGE_OVERVIEW_URL = "https://411.pu.edu.tw/p/426-1073-5.php?Lang=zh-tw"
PU_SCHOOLS_OVERVIEW_URL = "https://411.pu.edu.tw/p/426-1073-34.php?Lang=zh-tw"
PU_ISEP_URL = "https://411.pu.edu.tw/p/426-1073-9.php?Lang=zh-tw"
PU_DUAL_DEGREE_URL = "https://411.pu.edu.tw/p/426-1073-6.php?Lang=zh-tw"
PU_SCHOLARSHIPS_URL = "https://411.pu.edu.tw/p/426-1073-16.php?Lang=zh-tw"
PU_REGULATIONS_URL = "https://411.pu.edu.tw/p/426-1073-11.php?Lang=zh-tw"
PU_FORMS_URL = "https://411.pu.edu.tw/p/426-1073-15.php?Lang=zh-tw"
PU_FAQ_URL = "https://411.pu.edu.tw/p/426-1073-23.php?Lang=zh-tw"
PU_NEWS_URL = "https://411.pu.edu.tw/p/403-1073-13-1.php?Lang=zh-tw"
PU_OIA_SISTERS_URL = "https://oia.pu.edu.tw/p/426-1048-10.php"
PU_EAGLE_FUND_URL = "https://411.pu.edu.tw/p/406-1073-64488,r13.php?Lang=zh-tw"
PU_STUDY_ABROAD_RULES_PDF_URL = (
    "https://411.pu.edu.tw/var/file/73/1073/img/221/522370780.pdf"
)
PU_SELECTION_RULES_PDF_URL = (
    "https://411.pu.edu.tw/var/file/73/1073/img/221/270849722.pdf"
)
PU_TUITION_RULES_PDF_URL = (
    "https://411.pu.edu.tw/var/file/73/1073/img/221/210113684.pdf"
)
PU_SCHOLARSHIP_RULES_PDF_URL = (
    "https://411.pu.edu.tw/var/file/73/1073/img/221/168944169.pdf"
)
PU_DUAL_DEGREE_RULES_PDF_URL = (
    "https://411.pu.edu.tw/var/file/73/1073/img/221/557250910.pdf"
)
PU_CREDIT_TRANSFER_RULES_PDF_URL = (
    "https://411.pu.edu.tw/var/file/73/1073/img/221/252980871.pdf"
)
PU_XUEHAI_RULES_PDF_URL = (
    "https://411.pu.edu.tw/var/file/73/1073/img/221/876667481.pdf"
)
PU_SPAIN_PARTNERS_PDF_URL = (
    "https://411.pu.edu.tw/var/file/73/1073/img/222/808817649.pdf"
)

PU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 42.0),
    "ielts": ("IELTS", 4.5),
    "toeic": ("TOEIC", 550.0),
    "toefl_itp": ("TOEFL ITP", 460.0),
}


def is_pu(school_name: str | None) -> bool:
  school = resolve_university(school_name)
  if school is not None and school.id == PU.id:
    return True
  normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
  return normalized in {
      "靜宜大學",
      "靜宜",
      "pu",
      "providence university",
      "providence",
  }


def _is_graduate(degree_level: str | None) -> bool:
  text = (degree_level or "").strip()
  return any(token in text for token in ("碩", "博", "研究"))


def pu_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
  degree = (degree_level or "").strip()
  year = (current_year or "").strip()
  if not degree:
    return (
        "needs_confirmation",
        (
            "尚未提供目前學制與年級；依《靜宜大學在校學生出國(境)研修實施辦法》、《靜宜大學學生出國(境)研修甄選施行細則》及 411 遊留學中心申請資格規定：（1）出國研修期間須維持靜宜大學正式學籍（不得為已畢業、退學、休學等身分）；（2）申請交換學生須於本校完成至少一年學業（雙聯學制大學部須修業滿二學期、碩士班滿一學期；教育部學海飛颺／惜珠獎學金須就讀一學期以上且不含國內及境外在職專班生）；（3）大二至大四生優先（三年級優先於二年級），延畢生亦得申請或備取交換名額，出國期間須繳交靜宜全額學費（免繳雜費）。"
        ),
    )
  if any(
      token in degree or token in year
      for token in ("在職專班", "碩專", "emba", "EMBA", "進修學士班", "進修部", "學分班", "選修生", "休學")
  ):
    return (
        "fail",
        (
            f"已填報 {degree}{f'（{year}）' if year else ''}；依《靜宜大學在校學生出國(境)研修實施辦法》、《靜宜大學學生出國研修獎助學金實施辦法》第二條及《選送學生出國研修作業要點（學海計畫）》第二點，出國研修期間不得為休學或無正式學籍身分，且國內及境外在職專班生不得申請學海計畫與出國研修獎助學金。"
        ),
    )
  if year in {"大一上", "一年級上學期"}:
    return (
        "fail",
        (
            f"已填報 {degree}（{year}）；依靜宜大學 411 遊留學中心《出國研修學校資訊—申請資格及徵選規則》及《與境外大學校院辦理雙聯學制實施辦法》第三條，大學部學生須在本校完成至少一年（二學期）學業始得赴姊妹校交換或修讀雙聯學制。"
        ),
    )
  is_grad = _is_graduate(degree)
  grad_note = (
      "（提醒：碩博士生可申請出國交換，惟部分姊妹校僅開放學士班課程，建議先向 411 遊留學中心確認目標校是否開放研究所選課；碩士生亦可申請美國達拉斯浸信會大學 1+1 雙碩士、法國里昂天主教大學 ESDES 商學院 1+1 雙碩士或澳洲西雪梨大學 1+1 雙碩士計畫）"
      if is_grad
      else "（提醒：每名學生初審至多可填 3 所姊妹校志願［ISEP Exchange 可填 10 個志願］，同校競爭時依「語言能力證明 → 在校成績 → 未曾出國研修同學 → 屆臨畢業同學（大三優先於大二，延畢生得備取）」排序；延畢生出國期間須繳交靜宜全額學費、免繳雜費）"
  )
  return (
      "pass",
      (
          f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合《靜宜大學在校學生出國(境)研修實施辦法》與 411 遊留學中心在學學籍及修業年限規定{grad_note}。"
      ),
  )


def pu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
  score_min = 70.0
  gpa_min = 2.75
  gpa_rule_min = 2.70
  rank_max = 50.0
  details: list[str] = []
  passes_pu = False

  if academic_score is not None:
    details.append(f"歷年學業總平均 {academic_score:g} 分")
    if academic_score >= score_min:
      passes_pu = True
  if academic_gpa is not None:
    details.append(f"GPA {academic_gpa:g}")
    if academic_gpa >= gpa_rule_min:
      passes_pu = True
  if class_rank_percent is not None:
    details.append(f"系／班排名百分比前 {class_rank_percent:g}%")
    if class_rank_percent <= rank_max:
      passes_pu = True

  summary = "、".join(details)
  if (
      academic_score is None
      and academic_gpa is None
      and class_rank_percent is None
  ):
    return (
        "needs_confirmation",
        (
            "尚未填寫歷年學業平均成績、GPA 或系排名百分比；依靜宜大學 411 遊留學中心《交換學生／雙聯學制申請門檻》與《學生出國(境)研修甄選施行細則》第二條：（1）校內初審（8 月底／9 月底、2 月底／3 月底）與雙聯學制要求歷年學業成績達 GPA 2.75 以上（約 75 分；甄選施行細則彈性底線為前一學期 GPA 2.7 以上，未達門檻者須另提研修計畫佐證，或自動延至 4 月份／10 月份配合「姊妹校專業語言課程」審核）；（2）申請教育部《學海飛颺》獎學金須前一學年度下學期單學期正式成績單之系排名前 50%；（3）個別姊妹校另有更高 GPA 要求（如日本立命館亞洲太平洋大學與香港嶺南大學要求 GPA 3.0、瑞士蘇黎世應用科技大學要求 GPA 3.0）。"
        ),
    )

  if passes_pu:
    strict_275 = (
        (academic_gpa is not None and academic_gpa >= gpa_min)
        or (academic_score is not None and academic_score >= score_min)
    )
    xuehai_ok = (
        (class_rank_percent is not None and class_rank_percent <= rank_max)
        or (academic_gpa is not None and academic_gpa >= 3.0)
        or (academic_score is not None and academic_score >= 78.0)
    )
    tier_note = (
        "同時符合 411 遊留學中心校內初審與雙聯學制標準（GPA 2.75 / 約 75 分以上）及教育部《學海飛颺》獎學金（系排名前 50%）申請門檻"
        if (strict_275 and xuehai_ok)
        else (
            "符合 411 遊留學中心交換生初審與雙聯學制 GPA 2.75（約 75 分）門檻；若欲申請教育部《學海飛颺》獎學金，請確認上一學年度下學期單學期成績單之系排名達前 50%"
            if strict_275
            else "符合《靜宜大學學生出國(境)研修甄選施行細則》第二條（GPA 2.7 以上）與學海飛颺（系排名前 50%）基準；若 GPA 介於 2.70–2.74 之間，建議附上研修計畫書佐證"
        )
    )
    return (
        "pass",
        f"已填報 {summary}；符合靜宜大學出國研修甄選學業標準（{tier_note}）。",
    )

  return (
      "fail",
      (
          f"已填報 {summary}；未達靜宜大學 411 遊留學中心交換學生與雙聯學制校內初審門檻（歷年 GPA 2.75 / 約 75 分以上，或甄選施行細則第二條 GPA 2.7 以上）。未達校內初審門檻者，秋季班申請件將自動延至 4 月份、春季班延至 10 月份，可改申請免 GPA 與語檢門檻之「姊妹校專業語言課程」或檢附研修計畫書佐證。"
      ),
  )


def pu_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
  test = (language_test or "").strip().lower()
  if partner_country in {"中國大陸"} and (
      not test or language_score is None
  ):
    return (
        "pass",
        (
            "申請赴中國大陸姊妹校交換（含南京大學、南開大學、華中科技大學、中南大學、大連理工大學、中國傳媒大學、北京郵電大學、北京科技大學、鄭州大學、上海財經大學、東華大學、上海大學、蘇州大學、蘭州大學、西南財經大學、電子科技大學等 33 校），依靜宜大學 411 遊留學中心規定免繳外語能力證明（注意：初審通過後一週內須繳交赴陸申請文件）。"
        ),
    )
  if not test or language_score is None:
    return (
        "needs_confirmation",
        (
            "尚未填寫外語能力檢定成績。依靜宜大學 411 遊留學中心《出國研修學校資訊》與《學生出國(境)研修甄選施行細則》第三條：（1）英語授課校內初審門檻為 TOEFL ITP 500 或 TOEFL iBT 61 以上（ISEP 初審門檻為 TOEFL ITP 500；美國姊妹校要求 iBT 65–80 以上；英國與歐洲區姊妹校要求 IELTS 6.0 以上［每科不低於 5.5，英國學位生須考 UKVI IELTS 6.0］；雙聯學制要求 TOEFL iBT 80 或 IELTS 6.0 以上；部分歐亞姊妹校採認 CEFR B1/B2 或 TOEIC 550–785）；（2）日語授課（日本姊妹校）要求 JLPT N2 以上（部分日本姊妹校開放 N3 或英語授課軌道）；（3）韓語授課（韓國姊妹校）要求 TOPIK 3 級以上（部分學校開放 TOPIK 2 級或英語授課）；（4）西語／德語／法語授課要求 CEFR B1–B2 以上（西語授課需具二年以上西語能力或 DELE B1/B2）；（5）赴中國大陸交換及申請「姊妹校專業語言課程」（4 月底／10 月底截止）免附外語檢定證明。"
        ),
    )
  if test in PU_ENGLISH_MINIMUMS:
    label, minimum = PU_ENGLISH_MINIMUMS[test]
    passed = language_score >= minimum
    tier_note = "達部分歐亞姊妹校 CEFR B1 英語授課基準（提醒：411 遊留學中心一般初審不採計多益，僅特定註明採認 TOEIC / CEFR B1 之姊妹校適用，強烈建議報考 TOEFL ITP 500 / iBT 61 或 IELTS 6.0）"
    if (
        (test == "toefl" and language_score >= 80)
        or (test == "ielts" and language_score >= 6.5)
        or (test == "toeic" and language_score >= 785)
        or (test == "toefl_itp" and language_score >= 550)
    ):
      tier_note = "符合靜宜大學全部歐美、英澳、亞洲英語授課姊妹校、ISEP Exchange / Direct、西班牙卡洛斯第三大學（iBT 80 / IELTS 6.5）及全部 16 項歐美日澳跨國雙聯學制（TOEFL iBT 80 / IELTS 6.0–6.5）最高英語門檻"
    elif (
        (test == "toefl" and language_score >= 65)
        or (test == "ielts" and language_score >= 6.0)
        or (test == "toefl_itp" and language_score >= 520)
    ):
      tier_note = "符合 411 遊留學中心美國姊妹校（TOEFL iBT 65+）、英國與歐洲區姊妹校（IELTS 6.0，單科不低於 5.5）、澳洲姊妹校、ISEP 會員校及多數雙聯學制（IELTS 6.0）英語門檻"
    elif (
        (test == "toefl" and language_score >= 61)
        or (test == "toefl_itp" and language_score >= 500)
    ):
      tier_note = "符合靜宜大學 411 遊留學中心英語授課校內初審門檻（TOEFL iTP 500 / iBT 61）及 ISEP 初審門檻（ITP 500）；惟美國姊妹校多要求 iBT 65–79 以上、英國與歐洲姊妹校多要求 IELTS 6.0（CEFR B2）以上"
    return (
        "pass" if passed else "fail",
        (
            f"{label} {language_score:g} {'符合' if passed else '未達'}靜宜大學 411 遊留學中心出國研修英語檢定基準（最低採計門檻：{label} {minimum:g}；{tier_note}）。"
        ),
    )
  if test == "jlpt":
    level = int(language_score)
    passed = 1 <= level <= 4
    if level == 1:
      tier_note = "符合日本九州大學、同志社大學、立命館亞洲太平洋大學（部分學系 N1）及全部 51 所日本交換與雙聯姊妹校最高日語門檻"
    elif level == 2:
      tier_note = "符合靜宜大學 411 遊留學中心與《學生出國(境)研修甄選施行細則》日語授課通則（JLPT N2 以上），可申請青山學院大學、學習院大學、日本女子大學、神田外語大學、麗澤大學、東京經濟大學、亞細亞大學、白百合女子大學、聖心女子大學、愛知縣立大學（含台文系 2+2 雙學士）、京都女子大學、京都精華大學、福岡大學、西南學院大學等絕大多數日本姊妹校"
    elif level == 3:
      tier_note = "可申請明確採認 JLPT N3 之日本姊妹校（如北海道文教大學、仙台白百合女子大學、清泉女子大學、金澤星稜大學、名古屋學院大學、大阪學院大學、追手門學院大學、神戶女學院大學、長崎純心大學、宮崎國際大學、鹿兒島純心大學、沖繩大學等；一般日本姊妹校初審通則為 N2 以上）"
    elif level == 4:
      tier_note = "可申請日本長崎外國語大學、山陽學園大學、東亞大學等採認基礎日語或搭配英語授課之日本姊妹校（一般日本姊妹校初審通則為 JLPT N2 以上）"
    else:
      tier_note = "靜宜大學日本姊妹校校內初審通則要求 JLPT N2 以上（部分學校開放 N3–N4 或英語授課軌道）"
    return (
        "pass" if passed else "fail",
        f"JLPT N{level} {'符合' if passed else '未達'}靜宜大學日本姊妹校日語檢定基準（{tier_note}）。",
    )
  if test == "topik":
    level = int(language_score)
    passed = 1 <= level <= 6
    if level >= 3:
      tier_note = "符合靜宜大學 411 遊留學中心韓語授課校內初審通則（TOPIK 3 級以上），可申請西江大學、梨花女子大學、崇實大學、東國大學、天主教關東大學、順天鄉大學、韓南大學、釜山外國語大學、東亞大學、大邱天主教大學、濟州國立大學等全部韓國姊妹校"
    elif level >= 1:
      tier_note = "可申請接受基礎韓語或搭配英語檢定（CEFR B1–B2）之韓國姊妹校（如培材大學、花賢都社會福祉大學、韓東國際大學、釜山天主教大學等；411 韓語授課初審通則為 TOPIK 3 級以上）"
    else:
      tier_note = "靜宜大學韓國姊妹校韓語授課要求 TOPIK 3 級以上，或改以英語檢定（TOEFL iBT 61+ / IELTS 5.5–6.0 / ITP 500+）申請英語授課軌道"
    return (
        "pass" if passed else "fail",
        f"TOPIK {level} 級{'符合' if passed else '未達'}靜宜大學韓國姊妹校韓語檢定基準（{tier_note}）。",
    )
  if test in {"dele", "delf", "goethe", "testdaf"}:
    passed = language_score >= 1.0
    return (
        "pass" if passed else "fail",
        f"{language_test.upper()} {language_score:g} {'符合' if passed else '未達'}靜宜大學 411 遊留學中心歐語區（西語／法語／德語）姊妹校語言檢定基準。",
    )
  return (
      "needs_confirmation",
      f"已填報語言檢定 {language_test}（{language_score:g}）；請對照靜宜大學 411 遊留學中心《出國研修學校資訊》各區姊妹校門檻（英語 TOEFL iBT / ITP / IELTS、日語 JLPT N2、韓語 TOPIK 3 級、西語／德語／法語 CEFR B1–B2）確認。",
  )
