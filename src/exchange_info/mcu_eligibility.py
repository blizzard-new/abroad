from __future__ import annotations

import re

from .university_registry import MCU, resolve_university

MCU_IEE_HOME_URL = "https://iee.mcu.edu.tw/"
MCU_IEE_EN_HOME_URL = "https://iee.mcu.edu.tw/en/"
MCU_GUIDELINES_ZH_URL = "https://iee.mcu.edu.tw/%E5%87%BA%E5%9C%8B%E7%95%99%E5%AD%B8%E8%A8%88%E7%95%AB%E8%AA%AA%E6%98%8E/"
MCU_PROCEDURE_ZH_URL = "https://iee.mcu.edu.tw/%E5%87%BA%E5%9C%8B%E7%95%99%E5%AD%B8%E7%94%B3%E8%AB%8B%E7%A8%8B%E5%BA%8F/"
MCU_PARTNER_LIST_ZH_URL = "https://iee.mcu.edu.tw/%E5%87%BA%E5%9C%8B%E7%95%99%E5%AD%B8%E5%AD%B8%E6%A0%A1%E4%B8%80%E8%A6%BD%E8%A1%A8/"
MCU_DOWNLOADS_ZH_URL = "https://iee.mcu.edu.tw/%E5%87%BA%E5%9C%8B%E7%95%99%E5%AD%B8%E8%A8%88%E7%95%AB%E8%AA%AA%E6%98%8E-%E8%B3%87%E6%96%99%E4%B8%8B%E8%BC%89/"
MCU_FAQ_ZH_URL = "https://iee.mcu.edu.tw/%E5%87%BA%E5%9C%8B%E7%95%99%E5%AD%B8%E8%A8%88%E7%95%AB%E8%AA%AA%E6%98%8E-%E5%B8%B8%E8%A6%8B%E5%95%8F%E7%AD%94%E9%9B%86/"
MCU_EXPERIENCE_ZH_URL = "https://iee.mcu.edu.tw/experience/"
MCU_GLOBAL_PARTNERS_ZH_URL = "https://iee.mcu.edu.tw/%e5%9c%8b%e9%9a%9b%e4%ba%a4%e6%b5%81%e5%ad%b8%e6%a0%a1/"
MCU_GLOBAL_PARTNERS_EN_URL = "https://iee.mcu.edu.tw/en/global-partnership/"
MCU_DUAL_DEGREE_ZH_URL = "https://iee.mcu.edu.tw/mcu%e9%9b%99%e5%ad%b8%e4%bd%8d%e9%a0%85%e7%9b%ae/"
MCU_DUAL_DEGREE_PDF_URL = "https://iee.mcu.edu.tw/wp-content/uploads/sites/101/2026/10/MCU%E9%9B%99%E5%AD%B8%E4%BD%8D%E9%A0%85%E7%9B%AECE20261021.pdf"
MCU_EXCHANGE_DB_2027_PDF_URL = "https://iee.mcu.edu.tw/wp-content/uploads/sites/101/2026/10/MCU_Exchange_University_Database_Template_2027-2028.pdf"
MCU_116_PRIORITY_ODT_URL = "https://iee.mcu.edu.tw/wp-content/uploads/sites/101/2026/10/116%E5%BF%97%E9%A1%98%E9%81%B8%E5%A1%AB%E8%A1%A8Priority_List1021.odt"
MCU_116_XUEHAI_PDF_URL = "https://iee.mcu.edu.tw/wp-content/uploads/sites/101/2026/10/%E9%8A%98%E5%82%B3%E5%A4%A7%E5%AD%B8116%E5%AD%B8%E6%B5%B7%E9%A3%9B%E9%A2%BAr%E5%AD%B8%E6%B5%B7%E6%83%9C%E7%8F%A0%E7%94%84%E9%81%B8%E8%BE%A6%E6%B3%95.pdf"
MCU_REGULATIONS_PDF_URL = "https://iee.mcu.edu.tw/wp-content/uploads/sites/101/2026/06/%E9%8A%98%E5%82%B3%E5%A4%A7%E5%AD%B8%E5%87%BA%E5%9C%8B%E9%80%B2%E4%BF%AE%E4%BA%A4%E6%8F%9B%E5%AD%B8%E7%94%9F%E8%A8%88%E7%95%AB%E4%BD%9C%E6%A5%AD%E8%BE%A6%E6%B3%95-115.6.8.pdf"
MCU_BUDGET_SCHOLARSHIP_URL = "https://drive.google.com/file/d/1CW0VzmIphyjUd6UWlebgoAk2VXvhnXNj/view?usp=sharing"
MCU_MAINLAND_EXCHANGE_URL = "https://iee.mcu.edu.tw/%E8%B5%B4%E5%A4%A7%E9%99%B8%E4%BA%A4%E6%8F%9B%E7%A0%94%E7%BF%92/"
MCU_MAINLAND_SCHOOLS_URL = "https://iee.mcu.edu.tw/%E8%B5%B4%E5%A4%A7%E9%99%B8%E4%BA%A4%E6%8F%9B%E7%A0%94%E7%BF%92-%E4%BA%A4%E6%8F%9B%E5%AD%B8%E6%A0%A1%E5%90%8D%E5%96%AE/"
MCU_MAINLAND_ELIGIBILITY_URL = "https://iee.mcu.edu.tw/%E8%B5%B4%E5%A4%A7%E9%99%B8%E4%BA%A4%E6%8F%9B%E7%A0%94%E7%BF%92-2027%E6%98%A5%E5%AD%A3%E4%BA%A4%E6%8F%9B%E7%94%84%E9%81%B8%E8%B3%87%E6%A0%BC%E5%8F%8A%E6%A8%99%E6%BA%96/"
MCU_MAINLAND_SCHEDULE_URL = "https://iee.mcu.edu.tw/%E8%B5%B4%E5%A4%A7%E9%99%B8%E4%BA%A4%E6%8F%9B%E7%A0%94%E7%BF%92-2027%E6%98%A5%E5%AD%A3%E8%B5%B4%E5%A4%A7%E9%99%B8%E9%A0%82%E5%B0%96%E5%A4%A7%E5%AD%B8%E4%BA%A4%E6%8F%9B%E8%A8%88%E7%95%AB%E7%94%84/"
MCU_MAINLAND_SISTERS_ZH_URL = "https://iee.mcu.edu.tw/%E5%A4%A7%E9%99%B8%E4%BA%8B%E5%8B%99%E7%B5%84-%E5%A7%90%E5%A6%B9%E6%A0%A1/"

MCU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 60.0),
    "ielts": ("IELTS", 5.0),
    "toeic": ("TOEIC", 550.0),
}


def is_mcu(school_name: str | None) -> bool:
  school = resolve_university(school_name)
  if school is not None and school.id == MCU.id:
    return True
  normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
  return normalized in {
      "銘傳大學",
      "銘傳",
      "北銘",
      "桃銘",
      "mcu",
      "ming chuan university",
  }


def _is_graduate(degree_level: str | None) -> bool:
  text = (degree_level or "").strip()
  return any(token in text for token in ("碩", "博", "研究"))


def mcu_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
  degree = (degree_level or "").strip()
  year = (current_year or "").strip()
  if not degree:
    return (
        "needs_confirmation",
        (
            "尚未提供目前學制與年級；依《銘傳大學出國進修交換學生計畫作業辦法》第 4 條及《116 學海飛颺、學海惜珠甄選辦法》規定：申請人於申請期間及赴海外就學期間應為本校全職在學學生（不含休學生、國內及境外在職專班生），且未曾參加交換計畫者為限。"
        ),
    )
  if any(
      token in degree or token in year
      for token in ("學分班", "選修生", "休學", "延畢", "延修", "在職")
  ):
    return (
        "fail",
        (
            f"已填報 {degree}{f'（{year}）' if year else ''}；依《銘傳大學出國進修交換學生計畫作業辦法》與《116 學海飛颺、學海惜珠甄選辦法》規定，休學生、延修生及國內外在職專班生不得申請出國交換與學海獎助計畫。"
        ),
    )
  is_grad = _is_graduate(degree)
  if not is_grad and year in {"大一上"}:
    return (
        "fail",
        (
            f"已填報 {degree}（{year}）；申請銘傳大學海外交換、赴大陸頂尖大學交換與教育部學海計畫須就讀滿一學期以上並檢附歷年成績單，大一上新生尚無完整學期成績可供審查。"
        ),
    )
  return (
      "pass",
      (
          f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合銘傳大學 116 學年度（2027秋–2028春）菁英海外留學交換計畫（65 校）、跨國雙學位計畫（10 校 14 項 2+2 / 3+1 / 3.5+1.5 / 4+1 / 1+1 計畫）及 2027 春季赴大陸頂尖大學交換計畫（42 所 985 / 211 / 省部共建高校）之全職在學學籍規定。"
      ),
  )


def mcu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
  is_grad = _is_graduate(degree_level)
  mainland_min = 75.0 if is_grad else 68.0
  scholarship_min = 80.0 if is_grad else 70.0
  overseas_std = 75.0
  xuehai_std = 80.0
  details: list[str] = []
  passes_xuehai = False
  passes_overseas = False
  passes_mainland_or_sprout = False

  if academic_score is not None:
    details.append(f"學業平均 {academic_score:g} 分")
    if academic_score >= xuehai_std:
      passes_xuehai = True
      passes_overseas = True
      passes_mainland_or_sprout = True
    elif academic_score >= overseas_std:
      passes_overseas = True
      passes_mainland_or_sprout = True
    elif academic_score >= min(mainland_min, scholarship_min):
      passes_mainland_or_sprout = True
  if academic_gpa is not None:
    details.append(f"GPA {academic_gpa:g}")
    if academic_gpa >= 3.3:
      passes_xuehai = True
      passes_overseas = True
      passes_mainland_or_sprout = True
    elif academic_gpa >= 3.0:
      passes_overseas = True
      passes_mainland_or_sprout = True
    elif academic_gpa >= 2.5:
      passes_mainland_or_sprout = True
  if class_rank_percent is not None:
    details.append(f"班級／系所排名前 {class_rank_percent:g}%")
    if class_rank_percent <= 30.0:
      passes_xuehai = True
      passes_overseas = True
      passes_mainland_or_sprout = True
    elif class_rank_percent <= 50.0:
      passes_mainland_or_sprout = True

  summary = "、".join(details)
  if academic_score is None and academic_gpa is None and class_rank_percent is None:
    return (
        "needs_confirmation",
        (
            "尚未填寫學業平均、GPA 或班級排名；依銘傳大學規定：（1）《出國進修交換學生計畫作業辦法》第 4 條規定海外留學交換原則須歷年學業總成績平均 75 分以上（未達 75 分仍可備妥社團幹部與國際交流經歷提請委員會專案審議）；（2）《赴大陸頂尖大學交換計畫》規定操行須達 80 分以上，且大學部歷年平均達 70 分、或全班前 50%、或歷年 68 分且前一學期 75 分（碩士班須 75 分）；（3）《高教深耕菁英海外留學計畫獎勵金》要求出國前一學期平均大學部 70 分／研究所 80 分且操行 80 分；（4）教育部《116 學海飛颺》要求歷年平均 80 分以上、《學海惜珠》要求系前 40% 或班前 30%。"
        ),
    )

  if passes_xuehai:
    return (
        "pass",
        (
            f"已填報 {summary}；符合銘傳大學最高階出國甄選與獎學金標準（含《116 學海飛颺》80 分門檻、《學海惜珠》班前 30%／系前 40% 門檻、《出國進修交換學生計畫作業辦法》75 分門檻、美英法雙學位 GPA 3.0 門檻、2027 春季赴大陸頂尖大學交換計畫，以及高教深耕菁英海外留學獎勵金大學部 70 分／研究所 80 分標準）。"
        ),
    )

  if passes_overseas:
    return (
        "pass",
        (
            f"已填報 {summary}；符合《銘傳大學出國進修交換學生計畫作業辦法》第 4 條歷年學業總平均 75 分以上標準、美英法跨國雙學位 GPA 3.0 標準、2027 春季赴大陸頂尖大學交換計畫及高教深耕大學部出國獎勵金（70 分）門檻（若欲申請教育部《116 學海飛颺》須歷年平均達 80 分以上）。"
        ),
    )

  if passes_mainland_or_sprout:
    return (
        "pass",
        (
            f"已填報 {summary}；符合銘傳大學《2027 春季赴大陸頂尖大學交換計畫》（大學部歷年平均 70 分／全班前 50%／歷年 68 分且前一學期 75 分，且操行 80 分以上）與《高教深耕菁英海外留學計畫獎勵金》大學部 70 分門檻；若申請歐美日韓海外留學交換（原則 75 分），依國教處 Q&A 第 3 點仍可檢附社團幹部、文化參訪、接待外賓等個人經歷證明提請審核委員會審議。"
        ),
    )

  return (
      "fail",
      (
          f"已填報 {summary}；未達銘傳大學赴大陸頂尖大學交換計畫（68–70 分或班排前 50%）、高教深耕出國獎勵金（70 分）及海外留學交換計畫（原則 75 分）之學業基準。"
      ),
  )


def mcu_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
  test = (language_test or "").strip().lower()
  if partner_country in {"中國大陸", "香港", "澳門"} and (
      not test or language_score is None
  ):
    return (
        "pass",
        (
            f"申請赴{partner_country}合作姊妹校（如 42 所大陸 985 / 211 / 省部共建高校或澳門城市大學）免附外語檢定證明（澳門城市大學建議具備 TOEFL iBT 80 / IELTS 6.0 / TOEIC 690）。"
        ),
    )
  if not test or language_score is None:
    return (
        "needs_confirmation",
        (
            "尚未填寫外語檢定成績。依銘傳大學 116 學年度（2027–2028）《留學學校一覽表》與《116 學海飛颺、學海惜珠甄選辦法》規定：（1）歐美及學海飛颺標準門檻為 TOEFL iBT 79（新制 4 分）或 IELTS 6.0；（2）亞洲英語授課與部分美日韓姊妹校（如塞基諾州立大學 SVSU、關東學院大學、蘭實大學、東方大學、韓世大學、仁川國立大學、光云大學、拉夫里科技大學等）開放 TOEFL iBT 60–72 / IELTS 5.0–5.5 / TOEIC 550–785；（3）日本姊妹校要求 JLPT N1 或 N2（學海飛颺赴日須達 N2）；（4）韓國姊妹校要求或建議 TOPIK 2–4 級（學海飛颺赴韓須達 TOPIK 3 級）；（5）國際學院學生申請越南外貿大學、印尼彼得拉基督教大學、美國西維吉尼亞大學、法國雷恩商學院雙學位享免英檢入學待遇。"
        ),
    )
  if test in MCU_ENGLISH_MINIMUMS:
    label, minimum = MCU_ENGLISH_MINIMUMS[test]
    passed = language_score >= minimum
    adv_note = "符合銘傳大學部分美亞歐英語授課姊妹校最低門檻（TOEFL iBT 60 / IELTS 5.0 / TOEIC 550，如新加坡南洋理工學院、韓國韓世大學、仁川國立大學、光云大學、日本福井大學、關東學院大學、泰國蘭實大學、東方大學、美國塞基諾州立大學 SVSU 交換與 2+2 雙學位）"
    if (test == "toefl" and language_score >= 100) or (
        test == "ielts" and language_score >= 7.5
    ):
      adv_note = "符合銘傳大學全部海外交換與雙學位姊妹校最高標準（含英國西英格蘭大學 UWE 3+1/4+1 TOEFL iBT 90、英國艾塞克斯大學 3+1 碩士雙學位 iBT 88 / IELTS 6.5、法國諾歐商學院 NEOMA iBT 85），並可獲高教深耕外語能力最高加碼獎勵 +NT$ 5,000（TOEFL iBT 100+ / IELTS 7.5+）"
    elif (test == "toefl" and language_score >= 85) or (
        test == "ielts" and language_score >= 6.5
    ):
      adv_note = "符合法國諾歐商學院 NEOMA（iBT 85）、法國雷恩商學院與巴黎高等商業學校（iBT 80 / IELTS 6.5）、美國聖道大學與西維吉尼亞大學（IELTS 6.5）、德州大學聖安東尼奧分校 UTSA 雙學位（iBT 79 / IELTS 6.5）及《116 學海飛颺》，並可獲高教深耕外語能力加碼獎勵 +NT$ 3,000（TOEFL iBT 85–99 / IELTS 6.5–7.0）"
    elif (
        (test == "toefl" and language_score >= 79)
        or (test == "ielts" and language_score >= 6.0)
        or (test == "toeic" and language_score >= 750)
    ):
      adv_note = "符合銘傳大學歐美主流交換姊妹校（美加波法德比荷奧 TOEFL iBT 79 / IELTS 6.0 標準）及教育部《116 學海飛颺、學海惜珠》英語門檻（提醒：申請教育部學海飛颺僅採認托福或雅思，不採計多益）"
    elif (
        (test == "toefl" and language_score >= 70)
        or (test == "ielts" and language_score >= 5.5)
        or (test == "toeic" and language_score >= 650)
    ):
      adv_note = "符合韓國東亞大學、明知大學、嘉泉大學、漢陽大學、日本武藏野大學、金澤星稜大學、中京大學、櫻美林大學、越南蓮花大學及美國塞基諾州立大學 SVSU 等姊妹校門檻"
    return (
        "pass" if passed else "fail",
        (
            f"{label} {language_score:g} {'符合' if passed else '未達'}銘傳大學出國留學交換與雙學位計畫英語標準（基準：{label} {minimum:g}；{adv_note}）。"
        ),
    )
  if test == "jlpt":
    level = int(language_score)
    passed = level in (1, 2)
    tier_note = (
        "符合日本全部 13 所交換與雙學位姊妹校（含武藏野大學 N1、實踐女子大學 N1、名古屋外國語大學碩士班 N1、產業能率大學 SANNO 2+2 雙學位 N1，以及富山大學、四國大學、金澤星稜大學、福井大學、中京大學、新潟國際情報大學、二松學舍大學、櫻美林大學 N2）與教育部《116 學海飛颺》赴日門檻，且 JLPT N1 可獲高教深耕外語能力加碼獎勵 +NT$ 3,000"
        if level == 1
        else (
            "符合日本富山大學、四國大學、名古屋外國語大學（大學部）、金澤星稜大學、福井大學、中京大學、新潟國際情報大學、二松學舍大學、櫻美林大學及教育部《116 學海飛颺》赴日 JLPT N2 標準（武藏野大學、實踐女子大學與產業能率大學 2+2 雙學位要求 N1）"
            if level == 2
            else "銘傳大學日本交換與雙學位姊妹校及《116 學海飛颺》均要求 JLPT N2 或 N1 以上"
        )
    )
    return (
        "pass" if passed else "fail",
        f"JLPT N{level} {'符合' if passed else '未達'}銘傳大學日本合作姊妹校日語檢定要求（{tier_note}）。",
    )
  if test == "topik":
    level = int(language_score)
    passed = 2 <= level <= 6
    bonus_note = (
        "符合韓國全部 16 所交換姊妹校（含中央大學與鮮文大學 TOPIK 4 級、仁德大學與祥明大學與漢陽大學 TOPIK 3 級）及《116 學海飛颺》赴韓門檻，並可獲高教深耕外語加碼獎勵（TOPIK 4 級 +NT$ 3,000、TOPIK 5 級以上 +NT$ 5,000）"
        if level >= 4
        else (
            "符合韓國東亞大學、培才大學、安養大學、仁德大學、明知大學、祥明大學、嘉泉大學、慶南大學、江原大學、仁川國立大學、漢陽大學及《116 學海飛颺》赴韓 TOPIK 3 級標準"
            if level == 3
            else "符合韓國水原大學與韓世大學 TOPIK 2 級標準（多數韓國姊妹校與學海飛颺建議或要求 TOPIK 3–4 級）"
        )
    )
    return (
        "pass" if passed else "fail",
        f"TOPIK {level} 級{'符合' if passed else '未達'}銘傳大學韓國合作姊妹校韓語檢定基準（{bonus_note}）。",
    )
  if test in {"duolingo", "det"}:
    passed = language_score >= 85
    return (
        "pass" if passed else "fail",
        (
            f"Duolingo English Test {language_score:g} {'符合' if passed else '未達'}銘傳大學美加與法國部分姊妹校採認標準（塞基諾州立大學 SVSU 85、溫索普大學 95、北俄亥俄大學與巴黎高等商業學校 100、西維吉尼亞大學與加州州立大學長堤分校及加拿大麥迪森海特學院 105、聖道大學 UIW 110）。"
        ),
    )
  return (
      "needs_confirmation",
      f"已填報語言檢定 {language_test}（{language_score:g}）；請對照銘傳大學 116 學年度《留學學校一覽表》確認是否符合目標姊妹校指定外語標準。",
  )
