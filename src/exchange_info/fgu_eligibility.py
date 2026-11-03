from __future__ import annotations

import re

from .university_registry import FGU, resolve_university

FGU_OICA_HOME_URL = "https://oica.fgu.edu.tw/"
FGU_EXCHANGE_OVERVIEW_URL = "https://oica.fgu.edu.tw/zh_tw/exchange/20"
FGU_EXCHANGE_STATS_URL = "https://oica.fgu.edu.tw/zh_tw/exchange/exchangeStats"
FGU_SCHOLARSHIPS_URL = "https://oica.fgu.edu.tw/zh_tw/21"
FGU_REGULATIONS_URL = (
    "https://oica.fgu.edu.tw/zh_tw/archive/Download_page_relative_laws"
)
FGU_FORMS_URL = "https://oica.fgu.edu.tw/zh_tw/archive/otherform"
FGU_SYSTEM_UNIV_URL = "https://website.fgu.edu.tw/zh_tw/about/eduinstitutions"
FGU_ACADEMICS_URL = "https://website.fgu.edu.tw/zh_tw/academics"
FGU_2PLUS2_PROGRAM_URL = (
    "https://oica.fgu.edu.tw/announcement/%E8%AA%8D%E8%AD%98-2-2-Program-11047722"
)
FGU_115_1_INFO_SESSION_URL = (
    "https://oica.fgu.edu.tw/zh_tw/announcement/115%E5%AD%B8%E5%B9%B4%E5%BA%A6%E7%AC%AC%E4%B8%80%E5%AD%B8%E6%9C%9F-%E4%BA%A4%E6%8F%9B%E7%94%9F-%E9%9B%99%E5%AD%B8%E4%BD%8D%E7%94%84%E9%81%B8%E8%AA%AA%E6%98%8E%E6%9C%83-80520322"
)
FGU_115_1_ADMITTED_URL = (
    "https://oica.fgu.edu.tw/zh_tw/announcement/-%E5%85%AC%E5%91%8A-115%E5%AD%B8%E5%B9%B4%E5%BA%A6%E7%AC%AC1%E5%AD%B8%E6%9C%9F-%E6%B5%B7%E5%A4%96%E4%BA%A4%E6%8F%9B%E6%A0%A1%E5%85%A7%E7%94%84%E9%81%B8%E9%8C%84%E5%8F%96%E5%85%AC%E5%91%8A-18063077"
)
FGU_MIDDLESEX_POST_URL = (
    "https://oica.fgu.edu.tw/zh_tw/announcement/%E8%8B%B1%E5%9C%8B%E5%9C%8B%E7%AB%8B%E5%AF%86%E5%BE%B7%E8%96%A9%E6%96%AF%E5%A4%A7%E5%AD%B8%E9%9B%99%E8%81%AF%E5%AD%B8%E4%BD%8D%E8%AA%AA%E6%98%8E%E6%9C%83-9471519"
)

FGU_LAW_NON_CN_PDF_URL = (
    "https://oica.fgu.edu.tw/xhr/archive/download?file=65001679726c2f4f513075494e317a4d6442416f5a773d3d"
)
FGU_LAW_CN_PDF_URL = (
    "https://oica.fgu.edu.tw/xhr/archive/download?file=5a7866664e734c4966497a54646164663532576341413d3d"
)
FGU_LAW_UWEST_2PLUS2_PDF_URL = (
    "https://oica.fgu.edu.tw/xhr/archive/download?file=4334326f394e6f5761356f494745516d7964733851513d3d"
)
FGU_LAW_LIN_LU_FUND_PDF_URL = (
    "https://oica.fgu.edu.tw/xhr/archive/download?file=66576c4f6a485432524c587a7a697761314b346141413d3d"
)
FGU_LAW_XUEHAI_WUYA_PDF_URL = (
    "https://oica.fgu.edu.tw/xhr/archive/download?file=4a5a5a5233384b68443466396348706e7762683564513d3d"
)
FGU_LAW_OUTBOUND_GUIDELINES_PDF_URL = (
    "https://oica.fgu.edu.tw/xhr/archive/download?file=4b6859786552645a4c6233647044696a7970623359773d3d"
)

FGU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 61.0),
    "ielts": ("IELTS", 5.5),
    "toeic": ("TOEIC", 550.0),
    "toefl_itp": ("TOEFL ITP", 500.0),
}


def is_fgu(school_name: str | None) -> bool:
  school = resolve_university(school_name)
  if school is not None and school.id == FGU.id:
    return True
  normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
  return normalized in {
      "佛光大學",
      "佛大",
      "fgu",
      "fo guang university",
  }


def _is_graduate(degree_level: str | None) -> bool:
  text = (degree_level or "").strip()
  return any(token in text for token in ("碩", "博", "研究"))


def fgu_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
  degree = (degree_level or "").strip()
  year = (current_year or "").strip()
  if not degree:
    return (
        "needs_confirmation",
        (
            "尚未提供目前學制與年級；依《佛光大學赴中國大陸以外國家及地區交換學生甄選辦法》（A06-004）第 2 條、《佛光大學赴大陸交換學生甄選辦法》（A06-005）第 2 條及《佛光大學學生參與西來大學 2+2 計畫實施辦法》規定：（1）申請人須為本校具正式學籍之在學學生（大學部二年級以上或碩、博士班一年級下學期以上；大一下學期可報名參加大二出國交換甄選，大一／大二可報名美國西來大學 2+2 台美雙學位計畫）；（2）出國交換期間須維持佛光大學在學學籍並依規定辦理註冊繳費（應屆畢業生須辦理延畢）；（3）申請教育部《學海飛颺》或《學海惜珠》獎學金者須具中華民國國籍且在臺灣地區設有戶籍。"
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
  ) or year in {"大一", "一年級", "學士班一年級"}:
    return (
        "fail",
        (
            f"已填報 {degree}{f'（{year}）' if year else ''}；依《佛光大學赴中國大陸以外國家及地區交換學生甄選辦法》及《赴大陸交換學生甄選辦法》第 2 條規定，申請人須為本校具正式學籍之在學學生且修業滿一學期以上（大一上新生、休學學生、已畢業生、在職專班及非正式學籍選修生不得申請出國交換）。"
        ),
    )
  is_grad = _is_graduate(degree)
  grad_note = (
      "（提醒：碩博士班研究生須修滿一學期以上，申請表須經指導教授及系所主管推薦簽章；研究所學生另可評估英國國立密德薩斯大學 Middlesex University 1+1 碩士雙聯學位及美國西來大學研究所交換）"
      if is_grad
      else (
          "（提醒：大學部學生須修滿一學期以上且前一學期學業平均達 75 分以上、操行成績達 80 分以上；大學部學生另可評估佛光山系統大學美國西來大學 UWest 2+2 台美雙學位計畫及英國國立密德薩斯大學 Middlesex University 3+1 學士／學碩雙聯學位）"
      )
  )
  return (
      "pass",
      (
          f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合《佛光大學赴中國大陸以外國家及地區交換學生甄選辦法》與《赴大陸交換學生甄選辦法》在籍學制規定{grad_note}。"
      ),
  )


def fgu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
  score_min = 75.0
  gpa_min = 3.0
  rank_max = 50.0
  details: list[str] = []
  passes_fgu = False

  if academic_score is not None:
    details.append(f"學業平均成績 {academic_score:g} 分")
    if academic_score >= score_min:
      passes_fgu = True
  if academic_gpa is not None:
    details.append(f"GPA {academic_gpa:g}")
    if academic_gpa >= gpa_min:
      passes_fgu = True
  if class_rank_percent is not None:
    details.append(f"班級排名百分比前 {class_rank_percent:g}%")
    if class_rank_percent <= rank_max:
      passes_fgu = True

  summary = "、".join(details)
  if (
      academic_score is None
      and academic_gpa is None
      and class_rank_percent is None
  ):
    return (
        "needs_confirmation",
        (
            "尚未填寫學業平均成績、GPA 或班級排名百分比；依《佛光大學赴中國大陸以外國家及地區交換學生甄選辦法》、《佛光大學赴大陸交換學生甄選辦法》及《學生參與西來大學 2+2 計畫實施辦法》規定：（1）一般交換生與雙學位生前一學期學業平均成績須達 75 分（約 GPA 3.0）以上或班級排名前 50% 以內，且操行成績達 80 分以上、無記小過以上處分；（2）申請大陸 985/211 重點名校（如中國人民大學、南京大學、東南大學、四川大學、北京交通大學）者，歷年學業成績須達全班前 20% 以內；（3）申請《林陸素琦女士海外留學獎勵基金》或《西來大學 2+2 計畫獎學金》者，學業總平均須達 75 分以上（或全班前 25%–30%）。"
        ),
    )

  if passes_fgu:
    top_rank = (
        (academic_score is not None and academic_score >= 82.0)
        or (academic_gpa is not None and academic_gpa >= 3.4)
        or (class_rank_percent is not None and class_rank_percent <= 20.0)
    )
    tier_note = (
        "同時達到大陸 985/211 雙一流重點名校（中國人民大學、南京大學、東南大學、四川大學、北京交通大學）全班前 20% 高階門檻，並具申請《教育部學海飛颺／學海惜珠》、《佛光大學林陸素琦女士海外留學獎勵基金》、《學海無涯國際交流獎助學金》及《西來大學 2+2 計畫獎學金》之高度競爭優勢"
        if top_rank
        else "符合佛光大學海外及大陸交換生學業平均 75 分（GPA 3.0）或班排前 50% 之基準門檻（惟若擬申請中國人民大學、南京大學、東南大學、四川大學、北京交通大學等大陸 985/211 名校，建議班級排名達前 20% 以內）"
    )
    return (
        "pass",
        (
            f"已填報 {summary}；符合佛光大學國際暨兩岸事務處出國交換暨雙聯學位學業標準（{tier_note}）。"
        ),
    )

  return (
      "fail",
      (
          f"已填報 {summary}；未達《佛光大學赴中國大陸以外國家及地區交換學生甄選辦法》及《赴大陸交換學生甄選辦法》規定之學業基準（學業平均成績 {score_min:g} 分以上、GPA {gpa_min:g} 以上或班級排名前 {rank_max:g}%，且操行成績須達 80 分以上）。"
      ),
  )


def fgu_language_check(
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
            "申請赴大陸地區締約姊妹校（如中國人民大學、南京大學、東南大學、四川大學、北京交通大學、遼寧大學、西北師範大學、揚州大學、廣州大學、大連海事大學、大連大學、金陵科技學院、浙大寧波理工學院、泉州師範學院等）交換研修，以中文授課為主，免附外語能力檢定證明。"
        ),
    )
  if not test or language_score is None:
    return (
        "needs_confirmation",
        (
            "尚未填寫有效之語言能力測驗成績。依佛光大學國際暨兩岸事務處《交換生／雙學位甄選說明會簡報》及各姊妹校申請門檻規定：（1）校內甄選必備測驗：報名海外交換或雙學位者，須先於圖書館線上英文學習系統完成「EASY TEST iBT 托福題型」模擬測驗並繳交成績單；（2）美英歐菲澳英語授課門檻：美國西來大學 UWest（交換與 2+2 雙學位）要求 TOEFL iBT 69 或 IELTS 5.5（研究生 iBT 79 / IELTS 6.0；未達標者可先修讀 UWest ESL 課程），美國關島大學 UOG 要求 TOEFL iBT 61 或 IELTS 5.5，美國春山學院 Spring Hill College 要求 TOEFL iBT 65 或 IELTS 6.0，英國國立密德薩斯大學 Middlesex 雙聯要求 IELTS 6.0（碩士 6.5），愛沙尼亞塔爾圖大學與菲律賓光明大學、澳洲南天大學要求具備全英語授課能力（CEFR B1–B2 / IELTS 5.5 / TOEIC 550）；（3）日本姊妹校：花園大學要求 JLPT N4 以上，長崎大學與桃山學院大學要求 JLPT N2–N3（或英語學程 TOEFL iBT 61+ / IELTS 5.5+）；（4）韓國姊妹校：東國大學、釜山外國語大學、東亞大學、國立釜慶大學、建國大學、明知大學、成均館大學、天主教大學、金剛大學、京東大學要求 TOPIK 2–3 級以上，或以英語成績申請英語授課／語學堂研修組。"
        ),
    )
  if test in FGU_ENGLISH_MINIMUMS:
    label, minimum = FGU_ENGLISH_MINIMUMS[test]
    passed = language_score >= minimum
    tier_note = (
        "達佛光大學英語組基礎門檻（TOEFL iBT 61 / IELTS 5.5 / TOEIC 550 / TOEFL ITP 500），可申請美國關島大學 UOG、愛沙尼亞塔爾圖大學、菲律賓光明大學、澳洲南天大學及日韓姊妹校英語授課組"
    )
    if (
        (test == "toefl" and language_score >= 69)
        or (test == "ielts" and language_score >= 6.0)
        or (test == "toeic" and language_score >= 750)
        or (test == "toefl_itp" and language_score >= 530)
    ):
      tier_note = (
          "達高階英語標準，全面符合美國西來大學 UWest（交換與 2+2 台美雙學位，TOEFL iBT 69 / IELTS 5.5）、英國國立密德薩斯大學 Middlesex（3+1／1+1 雙聯，IELTS 6.0）、美國春山學院（TOEFL iBT 65 / IELTS 6.0）、休士頓大學清湖分校 UHCL、中央華盛頓大學 CWU、舊金山州立大學 SFSU、關島大學 UOG 及全數歐美亞英語授課姊妹校門檻"
      )
    elif (
        (test == "toefl" and language_score >= 65)
        or (test == "ielts" and language_score >= 5.5)
    ):
      tier_note = (
          "符合美國春山學院（TOEFL iBT 65）、美國關島大學（TOEFL iBT 61 / IELTS 5.5）、美國西來大學 UWest（IELTS 5.5）、愛沙尼亞塔爾圖大學及日韓菲英語授課姊妹校門檻"
      )
    return (
        "pass" if passed else "fail",
        (
            f"{label} {language_score:g} {'符合' if passed else '未達'}佛光大學國際暨兩岸事務處出國交換暨雙聯學位英語能力標準（校內英語基準門檻：{label} {minimum:g}；{tier_note}）。"
        ),
    )
  if test == "jlpt":
    level = int(language_score)
    passed = 1 <= level <= 4
    if level in (1, 2):
      tier_note = (
          f"達 JLPT N{level} 高階日語標準，全面符合日本花園大學（N4）、長崎大學（N2）及桃山學院大學（N2–N3）全數日本姊妹校交換門檻"
      )
    elif level == 3:
      tier_note = (
          "達 JLPT N3 中級日語標準，符合日本花園大學（N4）與桃山學院大學、長崎大學交換門檻"
      )
    elif level == 4:
      tier_note = (
          "達 JLPT N4 檢定標準，符合日本京都花園大學（Hanazono University，每學期 2 名免學費及住宿費、3 名免學費）官方公告日語門檻"
      )
    else:
      tier_note = (
          "日本花園大學要求至少達 JLPT N4（含）以上，長崎大學與桃山學院大學建議達 JLPT N2–N3 以上"
      )
    return (
        "pass" if passed else "fail",
        (
            f"JLPT N{level} {'符合' if passed else '未達'}佛光大學日本姊妹校交換學生日語能力標準（{tier_note}）。"
        ),
    )
  if test == "topik":
    level = int(language_score)
    passed = 2 <= level <= 6
    tier_note = (
        "符合韓國東國大學、釜山外國語大學、東亞大學、國立釜慶大學、建國大學、明知大學、成均館大學、韓國天主教大學、金剛大學及京東大學韓語交換門檻"
        if passed
        else "韓國姊妹校一般學部課程要求 TOPIK 2 級至 3 級以上（若申請釜山外國語大學、金剛大學、東亞大學等語學堂韓語研修或英語授課組，可依簡章免附 TOPIK 或改附英語檢定）"
    )
    return (
        "pass" if passed else "fail",
        (
            f"TOPIK {level} 級{'符合' if passed else '未達'}佛光大學韓國姊妹校韓語能力標準（{tier_note}）。"
        ),
    )
  if test in {"dele", "delf", "goethe", "testdaf", "tcf", "gept"}:
    passed = language_score >= 1.0
    return (
        "pass" if passed else "fail",
        (
            f"{language_test.upper()} {language_score:g} {'符合' if passed else '未達'}佛光大學國際暨兩岸事務處外語能力檢定參考標準（提醒：校內甄選仍須完成圖書館線上 EASY TEST iBT 模擬測驗）。"
        ),
    )
  return (
      "needs_confirmation",
      (
          f"已填報 {language_test}（{language_score:g}），請向佛光大學國際暨兩岸事務處（雲起樓 112 室）確認是否符合目標姊妹校之最新語檢採認標準。"
      ),
  )
