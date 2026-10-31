from __future__ import annotations

import re

from .university_registry import NFU, resolve_university

NFU_OIA_HOME_URL = "https://oia.nfu.edu.tw/"
NFU_ABOUT_URL = "https://oia.nfu.edu.tw/zh_tw/aboutoia/intro/introducation"
NFU_MEMBERS_URL = "https://oia.nfu.edu.tw/zh_tw/aboutoia/intro/members"
NFU_SISTER_INDEX_URL = "https://oia.nfu.edu.tw/zh_tw/aboutoia/sister"
NFU_SISTER_ASIA_URL = "https://oia.nfu.edu.tw/zh_tw/aboutoia/sister/asia"
NFU_SISTER_EUROPE_URL = "https://oia.nfu.edu.tw/zh_tw/aboutoia/sister/europe"
NFU_SISTER_AMERICA_URL = "https://oia.nfu.edu.tw/zh_tw/aboutoia/sister/america"
NFU_SISTER_OCEANIA_URL = "https://oia.nfu.edu.tw/zh_tw/aboutoia/sister/ocaenia"
NFU_REGULATIONS_URL = "https://oia.nfu.edu.tw/zh_tw/aboutoia/regulations"
NFU_OUTBOUND_ABROAD_URL = "https://oia.nfu.edu.tw/zh_tw/out/abroad"
NFU_OUTBOUND_311_URL = "https://oia.nfu.edu.tw/zh_tw/out/abroad/311"
NFU_EXCHANGE_SCHOOLS_URL = "https://oia.nfu.edu.tw/zh_tw/out/exlink/abroad"
NFU_EXCHANGE_STUDENT_URL = "https://oia.nfu.edu.tw/zh_tw/out/exlink/abroadlink2"
NFU_SCHOLARSHIPS_URL = "https://oia.nfu.edu.tw/zh_tw/out/exlink/flying"
NFU_DREAM_URL = "https://oia.nfu.edu.tw/zh_tw/out/short/dream"
NFU_SHARING_URL = "https://oia.nfu.edu.tw/zh_tw/out/sharing"
NFU_NEWS_OUTBOUND_URL = "https://oia.nfu.edu.tw/zh_tw/news/Outbound"
NFU_SELECTION_GUIDELINES_PDF_URL = (
    "https://oia.nfu.edu.tw/xhr/archive/download?file=69e990bc4eae358574b1be0f"
)
NFU_SUBSIDY_GUIDELINES_PDF_URL = (
    "https://oia.nfu.edu.tw/xhr/archive/download?file=69e9911a4eae358574b1be18"
)
NFU_APP_FORM_ODT_URL = "https://oia.nfu.edu.tw/uploads/asset/data/6a30b8844eae35ab549ba560/3.%E4%BA%A4%E6%8F%9B%E5%AD%B8%E7%94%9F%E7%94%84%E9%81%B8%E5%A0%B1%E5%90%8D%E8%A1%A8-1.odt"
NFU_115_2_EXCHANGE_POST_URL = "https://oia.nfu.edu.tw/zh_tw/news/Outbound/-115%E5%AD%B8%E5%B9%B4%E5%BA%A6%E7%AC%AC%E4%BA%8C%E5%AD%B8%E6%9C%9F-%E4%BA%A4%E6%8F%9B%E5%AD%B8%E7%94%9F%E7%94%B3%E8%AB%8B-%E8%87%AA%E5%8D%B3%E6%97%A5%E8%B5%B7%E8%87%B3115%E5%B9%B49%E6%9C%8810%E6%97%A5%E6%AD%A2-42884964"
NFU_115_2_XIZHU_POST_URL = "https://oia.nfu.edu.tw/zh_tw/news/Outbound/-115%E5%AD%B8%E5%B9%B4%E5%BA%A6%E7%AC%AC%E4%BA%8C%E5%AD%B8%E6%9C%9F-%E4%BA%A4%E6%8F%9B%E5%AD%B8%E7%94%9F%E7%94%B3%E8%AB%8B-%E5%AD%B8%E6%B5%B7%E6%83%9C%E7%8F%A0%E7%AC%AC2%E6%AC%A1%E5%BE%B5%E4%BB%B6-%E8%87%AA%E5%8D%B3%E6%97%A5%E8%B5%B7%E8%87%B3115%E5%B9%B49%E6%9C%8810%E6%97%A5%E6%AD%A2-64583857"
NFU_115_2_BROCHURE_PDF_URL = "https://oia.nfu.edu.tw/uploads/bulletin_file/file/6a1ce9144eae351ff5f951a5/4.%E4%BA%A4%E6%8F%9B%E5%AD%B8%E7%94%9F%E7%94%84%E9%81%B8%E7%B0%A1%E7%AB%A0.pdf"
NFU_115_2_XIZHU_BROCHURE_PDF_URL = "https://oia.nfu.edu.tw/uploads/bulletin_file/file/6a5895ea4eae352077a3a6f6/4.%E4%BA%A4%E6%8F%9B%E5%AD%B8%E7%94%9F_%E5%AD%B8%E6%B5%B7%E6%83%9C%E7%8F%A0%E7%94%84%E9%81%B8%E7%B0%A1%E7%AB%A011507.pdf"
NFU_CEFR_TABLE_PDF_URL = "https://oia.nfu.edu.tw/uploads/bulletin_file/file/6a1ce9144eae351ff5f951a6/5.CEF%E8%88%87%E5%90%84%E9%A0%85%E8%8B%B1%E6%AA%A2%E5%B0%8D%E7%85%A7%E8%A1%A8.pdf"
NFU_PARTNER_LIST_11506_PDF_URL = "https://oia.nfu.edu.tw/uploads/bulletin_file/file/6a1ce9144eae351ff5f951a7/6.%E5%9C%8B%E7%AB%8B%E8%99%8E%E5%B0%BE%E7%A7%91%E6%8A%80%E5%A4%A7%E5%AD%B8%E6%B5%B7%E5%A4%96%E5%A7%8A%E5%A6%B9%E6%A0%A1%E4%BA%A4%E6%8F%9B%E5%AD%B8%E7%94%9F%E4%B8%80%E8%A6%BD%E8%A1%A8__115.06_.pdf"
NFU_UNLV_SUMMER_PDF_URL = "https://oia.nfu.edu.tw/uploads/bulletin_file/file/69cb1942085777c11be50dd8/2026%E7%BE%8E%E5%9C%8B%E6%8B%89%E6%96%AF%E7%B6%AD%E5%8A%A0%E6%96%AFUNLV%E6%9A%91%E6%9C%9F%E7%A0%94%E7%BF%92%E8%A8%88%E7%95%AB%E5%85%AC%E5%91%8A0325.pdf"

NFU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 42.0),
    "ielts": ("IELTS", 4.0),
    "toeic": ("TOEIC", 550.0),
    "toefl_itp": ("TOEFL ITP", 457.0),
}


def is_nfu(school_name: str | None) -> bool:
  school = resolve_university(school_name)
  if school is not None and school.id == NFU.id:
    return True
  normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
  return normalized in {
      "國立虎尾科技大學",
      "虎尾科技大學",
      "虎科大",
      "虎尾科大",
      "nfu",
      "national formosa university",
  }


def _is_graduate(degree_level: str | None) -> bool:
  text = (degree_level or "").strip()
  return any(token in text for token in ("碩", "博", "研究"))


def nfu_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
  degree = (degree_level or "").strip()
  year = (current_year or "").strip()
  if not degree:
    return (
        "needs_confirmation",
        (
            "尚未提供目前學制與年級；依《國立虎尾科技大學甄選學生赴國外研修作業要點》及《辦理交換學生甄選簡章》規定：（1）報名參加甄選之學生必須為本校在學學生且修滿一學期（含）以上（春季班以「非應屆畢業生」優先薦送）；（2）四年制學生與研究所學生出國研修以不超過一年為原則，二年制學生以不超過半年為原則；（3）欲同時申請教育部學海飛颺／惜珠補助者，須具中華民國國籍且在臺灣地區設有戶籍（不包括國內及境外在職專班生）。"
        ),
    )
  if any(
      token in degree or token in year
      for token in (
          "休學",
          "已畢業",
          "退學",
          "學分班",
          "選修生",
          "在職",
          "大一上",
          "專一",
          "專二",
          "專三",
      )
  ):
    return (
        "fail",
        (
            f"已填報 {degree}{f'（{year}）' if year else ''}；依《國立虎尾科技大學甄選學生赴國外研修作業要點》及《辦理交換學生甄選簡章》規定，申請人必須為本校在學學生且修滿一學期（含）以上（大一上新生、休學生、已畢業生及非正式學籍之學分班／選修生不得申請）。"
        ),
    )
  is_grad = _is_graduate(degree)
  grad_note = (
      "（提醒：碩博士班研究生須修滿一學期以上，報名表免填班級排行百分比，須經指導老師、系所主任及學院院長簽名；電機資訊學院及管理學院學生另可評估美國喬治梅森大學"
      " GMU 與波莫納加州州立理工大學 Cal Poly Pomona 3+1+1 雙聯學制）"
      if is_grad
      else (
          "（提醒：大學部學生須修滿一學期（含）以上，春季班以非應屆畢業生優先薦送，日本近畿大學不接受應屆畢業生申請［直升本校研究所者例外］；海外一學期至少應修"
          " 9 學分或 18 ECTS，返國後有義務擔任國際事務處志工）"
      )
  )
  return (
      "pass",
      (
          f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合《國立虎尾科技大學甄選學生赴國外研修作業要點》與交換學生甄選簡章在籍學制規定{grad_note}。"
      ),
  )


def nfu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
  score_min = 75.0
  gpa_min = 2.5
  rank_max = 50.0
  details: list[str] = []
  passes_nfu = False

  if academic_score is not None:
    details.append(f"學業平均成績 {academic_score:g} 分")
    if academic_score >= score_min:
      passes_nfu = True
  if academic_gpa is not None:
    details.append(f"GPA {academic_gpa:g}")
    if academic_gpa >= gpa_min:
      passes_nfu = True
  if class_rank_percent is not None:
    details.append(f"班級排行百分比前 {class_rank_percent:g}%")
    if class_rank_percent <= rank_max:
      passes_nfu = True

  summary = "、".join(details)
  if (
      academic_score is None
      and academic_gpa is None
      and class_rank_percent is None
  ):
    return (
        "needs_confirmation",
        (
            "尚未填寫學業平均成績、GPA"
            " 或班級排行百分比；依《國立虎尾科技大學甄選學生赴國外研修作業要點》及《辦理交換學生甄選簡章》規定：（1）學業及操行成績優良，操行成績達"
            " 80 分（含）以上，申請時須檢附歷年中英文成績單正本及跨學期班排名證明書正本；（2）符合欲申請姊妹校之"
            " GPA 要求（如美國匹茲堡州立大學要求 GPA 2.5"
            " 以上、內華達大學拉斯維加斯分校 UNLV 要求 GPA 3.0"
            " 以上）；（3）校內甄試（書審＋面試）平均成績未達 70 分者不予錄取。"
        ),
    )

  if passes_nfu:
    top_rank = (
        (academic_score is not None and academic_score >= 80.0)
        or (academic_gpa is not None and academic_gpa >= 3.0)
        or (class_rank_percent is not None and class_rank_percent <= 25.0)
    )
    tier_note = (
        "同時符合美國內華達大學拉斯維加斯分校 UNLV（GPA 3.0 以上）、匹茲堡州立大學（GPA 2.5 以上）、美國 3+1+1 雙聯學制（GMU / Cal Poly Pomona）及全數歐美亞姊妹校標準，並具爭取教育部《學海飛颺》與《學海惜珠》補助之競爭優勢"
        if top_rank
        else "符合虎科大交換學生基本學業標準及美國匹茲堡州立大學（GPA 2.5 以上）門檻；惟若擬申請美國內華達大學拉斯維加斯分校（UNLV），歷年 GPA 須達 3.0 以上"
    )
    return (
        "pass",
        (
            f"已填報 {summary}；符合國立虎尾科技大學出國交換學生暨學海系列計畫學業標準（{tier_note}）。"
        ),
    )

  return (
      "fail",
      (
          f"已填報 {summary}；未達國立虎尾科技大學交換學生甄選建議學業基準（學業平均"
          f" {score_min:g} 分以上、GPA {gpa_min:g} 以上或班級排名前"
          f" {rank_max:g}%，且操行成績須達 80 分以上）。"
      ),
  )


def nfu_language_check(
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
            "申請赴大陸地區締約合作高校（如大連理工大學、天津大學、中國石油大學、武漢科技大學、江蘇大學等）交流研修，以中文授課為主，免附外語檢定證明。"
        ),
    )
  if not test or language_score is None:
    return (
        "needs_confirmation",
        (
            "尚未填寫一年內有效之語言能力測驗成績。依國立虎尾科技大學《CEF"
            " 語言能力參考指標對照表》及《海外姊妹校交換學生申請資訊一覽表》規定：（1）CEFR"
            " B1 門檻（法國特魯瓦工程技術大學"
            " UTT、德國埃斯林根應用科技大學、越南胡志明市外語信息大學"
            " HUFLIT）：須達新制 TOEIC 550（聽力 275／閱讀 275）、TOEFL iBT"
            " 42、TOEFL ITP 457 或 IELTS 4.0；（2）CEFR B2"
            " 門檻（荷蘭阿姆斯特丹應用科技大學、奧地利薩爾茨堡應用科學大學、捷克三校、匈牙利布達佩斯商業大學、德國卡爾斯魯厄／達姆施塔特／德烈斯登／柏林"
            " HTW／亞琛應用科技大學、土耳其庫克羅瓦大學、韓國東西大學）：須達新制"
            " TOEIC 785、TOEFL iBT 72、TOEFL ITP 527 或 IELTS"
            " 5.5；（3）日本姊妹校：明治大學須 JLPT N4 以上、群馬大學與近畿大學須"
            " JLPT N2 以上（群馬理工學部須 N1）；（4）韓國明知大學須 TOPIK"
            " Level 3 或 TOEFL iBT 70 / IELTS 5.5。"
        ),
    )
  if test in NFU_ENGLISH_MINIMUMS:
    label, minimum = NFU_ENGLISH_MINIMUMS[test]
    passed = language_score >= minimum
    tier_note = (
        "達虎科大《CEF 語言能力參考指標對照表》CEFR B1 進階級標準（TOEIC 550 /"
        " TOEFL iBT 42 / TOEFL ITP 457 / IELTS 4.0），可申請法國特魯瓦工程技術大學"
        " UTT、德國埃斯林根應用科技大學及越南胡志明市外語信息大學 HUFLIT"
    )
    if (
        (test == "toefl" and language_score >= 80)
        or (test == "ielts" and language_score >= 6.5)
        or (test == "toeic" and language_score >= 800)
        or (test == "toefl_itp" and language_score >= 550)
    ):
      tier_note = (
          "達高階英語標準，全面符合美國喬治梅森大學 GMU（3+1+1雙聯 iBT 80 /"
          " IELTS 6.5）、印尼大學 UI（iBT 80 / IELTS 6.0）、泰國先皇技術學院"
          " KMITL（iBT 79 / IELTS 6.0）、美國 Cal Poly Pomona（3+1+1雙聯）、美國"
          " SIUC / PSU / UM-Flint / UNLV / UTSA 及全數歐洲 CEFR B2 姊妹校門檻"
      )
    elif (
        (test == "toefl" and language_score >= 72)
        or (test == "ielts" and language_score >= 5.5)
        or (test == "toeic" and language_score >= 785)
        or (test == "toefl_itp" and language_score >= 527)
    ):
      tier_note = (
          "達虎科大《CEF 語言能力參考指標對照表》CEFR B2 高階級標準（TOEIC 785"
          " / TOEFL iBT 72 / TOEFL ITP 527 / IELTS"
          " 5.5），符合荷蘭阿姆斯特丹應用科技大學、奧地利薩爾茨堡應用科學大學、捷克三校、匈牙利布達佩斯商業大學、德國"
          " HAWtech 六校聯盟、土耳其庫克羅瓦大學、韓國東西大學與明知大學，以及美國"
          " SIUC / PSU / UM-Flint / UNLV / UTSA 英語門檻"
      )
    elif (
        (test == "toefl" and language_score >= 61)
        or (test == "ielts" and language_score >= 5.0)
        or (test == "toeic" and language_score >= 600)
        or (test == "toefl_itp" and language_score >= 500)
    ):
      tier_note = (
          "符合美國德州大學聖安東尼校區 UTSA（TOEIC 600 / IELTS"
          " 5.0）、南伊利諾大學卡本岱爾校區 SIUC、密西根大學弗林特分校、內華達大學拉斯維加斯分校"
          " UNLV、日本近畿大學英語組（TOEFL iBT 61）及 CEFR B1 姊妹校門檻"
      )
    return (
        "pass" if passed else "fail",
        (
            f"{label} {language_score:g}"
            f" {'符合' if passed else '未達'}國立虎尾科技大學國際事務處出國交換暨"
            f" 3+1+1 雙聯學制英語能力標準（校內 CEFR B1 基準門檻：{label}"
            f" {minimum:g}；{tier_note}）。"
        ),
    )
  if test == "jlpt":
    level = int(language_score)
    passed = 1 <= level <= 4
    if level == 1:
      tier_note = (
          "達 JLPT N1 最高日語標準，符合日本群馬大學理工學部（須 N1）、群馬大學一般學部與近畿大學（N2）、明治大學（N4）及近畿大學產業理工學部全數日本姊妹校交換門檻"
      )
    elif level == 2:
      tier_note = (
          "達 JLPT N2 標準，符合日本群馬大學、近畿大學、明治大學及近畿大學產業理工學部交換門檻（惟申請群馬大學理工學部者須具備"
          " JLPT N1）"
      )
    else:
      tier_note = (
          f"達 JLPT N{level} 標準，符合日本明治大學（JLPT N4"
          " 含以上，證照須於兩年內考取）及近畿大學產業理工學部申請門檻；若欲申請群馬大學或近畿大學日語組則須達"
          " JLPT N2（含）以上"
      )
    return (
        "pass" if passed else "fail",
        (
            f"JLPT N{level}"
            f" {'符合' if passed else '未達'}國立虎尾科技大學日本姊妹校交換學生日語能力標準（{tier_note}）。"
        ),
    )
  if test == "topik":
    level = int(language_score)
    passed = 3 <= level <= 6
    tier_note = (
        "符合韓國明知大學（TOPIK Level 3 含以上）與釜山東西大學韓語交換門檻"
        if passed
        else "韓國明知大學要求 TOPIK Level 3（含）以上（或改以英語 TOEFL iBT 70 / IELTS 5.5 申請）"
    )
    return (
        "pass" if passed else "fail",
        (
            f"TOPIK {level}"
            f" 級{'符合' if passed else '未達'}國立虎尾科技大學韓國姊妹校韓語能力標準（{tier_note}）。"
        ),
    )
  if test in {"dele", "delf", "goethe", "testdaf", "tcf", "vinatest", "ivpt"}:
    passed = language_score >= 1.0
    return (
        "pass" if passed else "fail",
        (
            f"{language_test.upper()} {language_score:g}"
            f" {'符合' if passed else '未達'}國立虎尾科技大學國際事務處德／法／第二外語能力證明標準（如德國"
            " HAWtech 聯盟德文 B1/B2、法國 UTT 法文 B1）。"
        ),
    )
  return (
      "needs_confirmation",
      (
          f"已填報語言檢定 {language_test}（{language_score:g}）；請對照國立虎尾科技大學《CEF"
          " 語言能力參考指標對照表》與《海外姊妹校交換學生一覽表》確認。"
      ),
  )
