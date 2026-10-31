from __future__ import annotations

import re

from .university_registry import NCUT, resolve_university

NCUT_OIA_HOME_URL = "https://oia.ncut.edu.tw/"
NCUT_OUTBOUND_EXCHANGE_URL = "https://oia.ncut.edu.tw/p/412-1030-6648.php?Lang=zh-tw"
NCUT_DUAL_DEGREE_URL = "https://oia.ncut.edu.tw/p/412-1030-6651.php?Lang=zh-tw"
NCUT_SHORT_TERM_URL = "https://oia.ncut.edu.tw/p/412-1030-6649.php?Lang=zh-tw"
NCUT_SCHOLARSHIPS_URL = "https://oia.ncut.edu.tw/p/412-1030-3189.php?Lang=zh-tw"
NCUT_MOU_PARTNERS_URL = "https://oia.ncut.edu.tw/p/412-1030-2698.php?Lang=zh-tw"
NCUT_EXPERIENCE_SHARING_URL = "https://oia.ncut.edu.tw/p/412-1030-6652.php?Lang=zh-tw"
NCUT_FAQ_URL = "https://oia.ncut.edu.tw/p/412-1030-6654.php?Lang=zh-tw"
NCUT_REGULATIONS_URL = "https://oia.ncut.edu.tw/p/412-1030-6774.php?Lang=zh-tw"
NCUT_DOWNLOADS_URL = "https://oia.ncut.edu.tw/p/412-1030-6653.php?Lang=zh-tw"

NCUT_EXCHANGE_REGULATION_PDF_URL = (
    "https://oia.ncut.edu.tw/var/file/30/1030/img/816/441856971.pdf"
)
NCUT_CREDIT_TRANSFER_PDF_URL = (
    "https://oia.ncut.edu.tw/var/file/30/1030/img/816/771299156.pdf"
)
NCUT_SUBSIDY_REGULATION_PDF_URL = (
    "https://oia.ncut.edu.tw/var/file/30/1030/img/816/135383977.pdf"
)
NCUT_DUAL_DEGREE_REGULATION_PDF_URL = (
    "https://oia.ncut.edu.tw/var/file/30/1030/img/816/394575938.pdf"
)
NCUT_SCHOLARSHIP_QA_PDF_URL = (
    "https://oia.ncut.edu.tw/var/file/30/1030/img/926/687373270.pdf"
)
NCUT_EXCHANGE_APP_FORM_ODT_URL = (
    "https://oia.ncut.edu.tw/var/file/30/1030/img/1535/822026397.odt"
)

NCUT_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 42.0),
    "ielts": ("IELTS", 4.0),
    "toeic": ("TOEIC", 550.0),
    "toefl_itp": ("TOEFL ITP", 457.0),
}


def is_ncut(school_name: str | None) -> bool:
  school = resolve_university(school_name)
  if school is not None and school.id == NCUT.id:
    return True
  normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
  return normalized in {
      "國立勤益科技大學",
      "勤益科技大學",
      "勤益科大",
      "國立勤益科大",
      "勤益",
      "ncut",
      "national chin-yi university of technology",
      "chin-yi university of technology",
  }


def _is_graduate(degree_level: str | None) -> bool:
  text = (degree_level or "").strip()
  return any(token in text for token in ("碩", "博", "研究"))


def ncut_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
  degree = (degree_level or "").strip()
  year = (current_year or "").strip()
  if not degree:
    return (
        "needs_confirmation",
        (
            "尚未提供目前學制與年級；依《國立勤益科技大學選送學生出國研修辦法》及《選送學生出國交換研修申請簡章》規定：（1）申請人須為本校具正式學籍之在學學生（不含國內及境外在職專班生），且於本校就讀滿一學期（含）以上；（2）應屆畢業生須於出國交換期間保有勤益科大在學學籍（必要時應辦理延畢）；（3）欲同時申請教育部學海飛颺／學海惜珠及本校國際化多元學習補助者，須具中華民國國籍且在臺灣地區設有戶籍。"
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
            f"已填報 {degree}{f'（{year}）' if year else ''}；依《國立勤益科技大學選送學生出國研修辦法》及交換學生甄選簡章規定，申請人須為本校具正式學籍之日間部／進修部在學學生且就讀滿一學期（含）以上（大一上新生、在職專班、休學生、已畢業生及非正式學籍之選修生不得申請）。"
        ),
    )
  is_grad = _is_graduate(degree)
  grad_note = (
      "（提醒：碩博士班研究生須修滿一學期以上，報名表須經指導教授、系所主任及院長核章；工程與電資學院研究生另可評估日本國立東北大學材料科學研究所雙聯博士學位、國立岩手大學理工學府雙聯碩士學位及越南大南大學雙聯碩士學位）"
      if is_grad
      else (
          "（提醒：四技／二技大學部學生須修滿一學期（含）以上且歷年學業總平均達 70 分以上、操行成績平均達 80 分以上；大學部學生另可評估加拿大皇家大學 RRU 2+2 雙聯學士學位，海外研修期間每學期至少應修習 2 門或 6 學分專業課程）"
      )
  )
  return (
      "pass",
      (
          f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合《國立勤益科技大學選送學生出國研修辦法》與交換學生甄選簡章在籍學制規定{grad_note}。"
      ),
  )


def ncut_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
  score_min = 70.0
  gpa_min = 2.5
  rank_max = 50.0
  details: list[str] = []
  passes_ncut = False

  if academic_score is not None:
    details.append(f"學業平均成績 {academic_score:g} 分")
    if academic_score >= score_min:
      passes_ncut = True
  if academic_gpa is not None:
    details.append(f"GPA {academic_gpa:g}")
    if academic_gpa >= gpa_min:
      passes_ncut = True
  if class_rank_percent is not None:
    details.append(f"班級排名百分比前 {class_rank_percent:g}%")
    if class_rank_percent <= rank_max:
      passes_ncut = True

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
            " 或班級排名百分比；依《國立勤益科技大學選送學生出國研修辦法》及《選送學生出國交換研修申請簡章》規定：（1）在校歷年學業成績總平均須達"
            " 70 分（含）以上，且歷年操行成績平均達 80"
            " 分（含）以上，無記小過以上處分紀錄；（2）申請時須檢附歷年中英文成績單正本（含班級排名百分比）；（3）若擬申請教育部《學海飛颺》獎助學金，建議班級排名前"
            " 30% 至前 50% 以提升甄選競爭力。"
        ),
    )

  if passes_ncut:
    top_rank = (
        (academic_score is not None and academic_score >= 80.0)
        or (academic_gpa is not None and academic_gpa >= 3.0)
        or (class_rank_percent is not None and class_rank_percent <= 30.0)
    )
    tier_note = (
        "同時符合日本國立信州大學、韓國首爾科學技術大學、法國巴黎高等電子學院 ISEP、德國德根多夫應用科技大學 DIT、加拿大皇家大學 RRU（GPA 2.7+）及日本國立東北大學／岩手大學雙聯學位高階學業標準，並具爭取教育部《學海飛颺》、《學海惜珠》與勤益《國際化多元學習補助》之高度競爭優勢"
        if top_rank
        else "符合勤益科大出國交換學生歷年學業總平均 70 分（或 GPA 2.5）以上之法定門檻；惟若擬申請教育部《學海飛颺》獎學金或加拿大皇家大學 RRU 雙聯學位，建議維持班排名前 30% 及歷年平均 75–80 分以上"
    )
    return (
        "pass",
        (
            f"已填報 {summary}；符合國立勤益科技大學出國交換學生暨雙聯學位學業標準（{tier_note}）。"
        ),
    )

  return (
      "fail",
      (
          f"已填報 {summary}；未達《國立勤益科技大學選送學生出國研修辦法》規定之學業基準（歷年學業成績總平均"
          f" {score_min:g} 分以上、GPA {gpa_min:g} 以上或班級排名前"
          f" {rank_max:g}%，且歷年操行成績平均須達 80 分以上）。"
      ),
  )


def ncut_language_check(
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
            "申請赴大陸地區締約合作高校（如北京理工大學、中國礦業大學、西南交通大學、南京理工大學、蘇州大學等）交流研修，以中文授課為主，免附外語檢定證明。"
        ),
    )
  if not test or language_score is None:
    return (
        "needs_confirmation",
        (
            "尚未填寫有效之語言能力測驗成績。依國立勤益科技大學《選送學生出國交換研修申請簡章》及各姊妹校申請門檻規定：（1）英語授課組基礎門檻（CEFR"
            " B1）：須達 TOEIC 550、TOEFL iBT 42、TOEFL ITP 457、IELTS 4.0 或全民英檢"
            " GEPT 中級（捷克赫拉德茨克拉洛韋大學 UHK、波蘭盧布林理工大學、拉脫維亞里加技術大學"
            " RTU、越南胡志明市經濟財經大學 UEF、印尼泗水理工學院 ITS）；（2）歐美韓高階英語門檻（CEFR"
            " B2）：德國德根多夫應用科技大學 DIT、法國巴黎高等電子學院 ISEP、美國聖地牙哥州立大學"
            " SDSU、加拿大皇家大學 RRU（2+2 雙聯）、韓國首爾科學技術大學及漢陽大學 ERICA 建議達"
            " TOEIC 750–785、TOEFL iBT 72–80 或 IELTS 5.5–6.0；（3）日本姊妹校：國立信州大學、北見工業大學、近畿大學、人間綜合科學大學須"
            " JLPT N2–N3 以上，千歲科學技術大學、城西國際大學、日本文理大學、第一工科大學、別府大學須"
            " JLPT N3–N5 或基礎日語能力；（4）韓國姊妹校韓語組：須達 TOPIK 2–3 級以上。"
        ),
    )
  if test in NCUT_ENGLISH_MINIMUMS:
    label, minimum = NCUT_ENGLISH_MINIMUMS[test]
    passed = language_score >= minimum
    tier_note = (
        "達勤益科大英語組 CEFR B1 基礎門檻（TOEIC 550 / TOEFL iBT 42 / TOEFL ITP"
        " 457 / IELTS 4.0），可申請捷克赫拉德茨克拉洛韋大學 UHK、波蘭盧布林理工大學、拉脫維亞里加技術大學"
        " RTU、越南胡志明市經濟財經大學 UEF、印尼泗水理工學院 ITS 及日本北見工業大學／千歲科學技術大學英文專題組"
    )
    if (
        (test == "toefl" and language_score >= 80)
        or (test == "ielts" and language_score >= 6.0)
        or (test == "toeic" and language_score >= 785)
        or (test == "toefl_itp" and language_score >= 543)
    ):
      tier_note = (
          "達高階英語標準（CEFR B2），全面符合美國聖地牙哥州立大學 SDSU、加拿大皇家大學"
          " RRU（2+2 雙聯學士）、日本國立東北大學／岩手大學雙聯學位、法國巴黎高等電子學院"
          " ISEP、德國德根多夫應用科技大學 DIT、韓國首爾科學技術大學與漢陽大學 ERICA"
          " 及全數歐美亞英語授課姊妹校門檻"
      )
    elif (
        (test == "toefl" and language_score >= 61)
        or (test == "ielts" and language_score >= 5.0)
        or (test == "toeic" and language_score >= 650)
        or (test == "toefl_itp" and language_score >= 500)
    ):
      tier_note = (
          "符合韓國東國大學 WISE、東亞大學、建陽大學、清州大學英語組、馬來西亞拉曼大學"
          " UTAR、泰國先皇技術學院 KMITL、菲律賓亞當森大學及歐洲捷克／波蘭／拉脫維亞姊妹校英語門檻"
      )
    return (
        "pass" if passed else "fail",
        (
            f"{label} {language_score:g}"
            f" {'符合' if passed else '未達'}國立勤益科技大學國際事務處出國交換暨雙聯學位英語能力標準（校內"
            f" CEFR B1 基準門檻：{label} {minimum:g}；{tier_note}）。"
        ),
    )
  if test == "jlpt":
    level = int(language_score)
    passed = 1 <= level <= 5
    if level in (1, 2):
      tier_note = (
          f"達 JLPT N{level} 高階日語標準，全面符合日本國立信州大學（N2）、近畿大學（N2）、國立北見工業大學、人間綜合科學大學、城西國際大學、日本文理大學、第一工科大學、別府大學及國立岩手大學雙聯碩士全數日本姊妹校交換門檻"
      )
    elif level == 3:
      tier_note = (
          "達 JLPT N3 中級日語標準，符合日本國立北見工業大學、人間綜合科學大學、城西國際大學、日本文理大學、第一工科大學、別府大學及南九州大學交換門檻（惟若欲申請國立信州大學或近畿大學一般學部須達 JLPT N2）"
      )
    else:
      tier_note = (
          f"達 JLPT N{level} 基礎日語標準，可申請日本千歲科學技術大學、第一工科大學、日本文理大學及別府大學（部分學系建議搭配英語能力或修畢校內基礎日語課程）"
      )
    return (
        "pass" if passed else "fail",
        (
            f"JLPT N{level}"
            f" {'符合' if passed else '未達'}國立勤益科技大學日本姊妹校交換學生日語能力標準（{tier_note}）。"
        ),
    )
  if test == "topik":
    level = int(language_score)
    passed = 2 <= level <= 6
    tier_note = (
        "符合韓國首爾科學技術大學、漢陽大學 ERICA、東國大學 WISE、東亞大學、建陽大學、清州大學及南部大學韓語交換門檻"
        if passed
        else "韓國姊妹校韓語授課組一般要求 TOPIK 2 級至 3 級（含）以上（或改以英語 TOEIC 550+ / TOEFL iBT 61+ / IELTS 5.5+ 申請英語授課組）"
    )
    return (
        "pass" if passed else "fail",
        (
            f"TOPIK {level}"
            f" 級{'符合' if passed else '未達'}國立勤益科技大學韓國姊妹校韓語能力標準（{tier_note}）。"
        ),
    )
  if test in {"dele", "delf", "goethe", "testdaf", "tcf", "vinatest", "ivpt", "gept"}:
    passed = language_score >= 1.0
    return (
        "pass" if passed else "fail",
        (
            f"{language_test.upper()} {language_score:g}"
            f" {'符合' if passed else '未達'}國立勤益科技大學國際事務處外語能力檢定標準（如德國德根多夫應用科技大學德語 B1/B2、法國巴黎高等電子學院法語 B1/B2 或全民英檢 GEPT 中級以上）。"
        ),
    )
  return (
      "needs_confirmation",
      (
          f"已填報語言檢定 {language_test}（{language_score:g}）；請對照國立勤益科技大學《選送學生出國交換研修申請簡章》與各姊妹校申請條件確認。"
      ),
  )
