from __future__ import annotations

import re

from .university_registry import NCNU, resolve_university

NCNU_OIA_HOME_URL = "https://oia.ncnu.edu.tw/"
NCNU_EXCHANGE_OVERVIEW_URL = (
    "https://oia.ncnu.edu.tw/p/412-1017-269.php?Lang=zh-tw"
)
NCNU_EXCHANGE_DEADLINES_URL = (
    "https://oia.ncnu.edu.tw/p/406-1017-32102,r44.php?Lang=zh-tw"
)
NCNU_EXCHANGE_PARTNERS_SHEET_URL = "https://docs.google.com/spreadsheets/d/1iLyMA1wtTgx_Ygkbcc3Dps179qrr_-g_-7OzivUsslA/edit?usp=sharing"
NCNU_PARTNERS_MAP_URL = (
    "https://oia.ncnu.edu.tw/p/412-1017-293.php?Lang=zh-tw"
)
NCNU_MAINLAND_PARTNERS_URL = (
    "https://oia.ncnu.edu.tw/p/412-1017-524.php?Lang=zh-tw"
)
NCNU_MAINLAND_APPLY_URL = (
    "https://oia.ncnu.edu.tw/p/412-1017-531.php?Lang=zh-tw"
)
NCNU_MAINLAND_QA_URL = (
    "https://oia.ncnu.edu.tw/p/412-1017-532.php?Lang=zh-tw"
)
NCNU_SCHOLARSHIPS_URL = (
    "https://oia.ncnu.edu.tw/p/412-1017-271.php?Lang=zh-tw"
)
NCNU_XUEHAI_URL = "https://oia.ncnu.edu.tw/p/412-1017-350.php?Lang=zh-tw"
NCNU_SCHOOL_SUBSIDY_URL = (
    "https://oia.ncnu.edu.tw/p/412-1017-351.php?Lang=zh-tw"
)
NCNU_EXPERIENCES_URL = (
    "https://oia.ncnu.edu.tw/p/412-1017-273.php?Lang=zh-tw"
)
NCNU_REGULATIONS_URL = (
    "https://oia.ncnu.edu.tw/p/412-1017-285.php?Lang=zh-tw"
)
NCNU_DOWNLOADS_URL = (
    "https://oia.ncnu.edu.tw/p/412-1017-286.php?Lang=zh-tw"
)
NCNU_DUAL_DEGREE_URL = (
    "https://oia.ncnu.edu.tw/p/412-1017-270.php?Lang=zh-tw"
)
NCNU_SCORE_RULES_PDF_URL = (
    "https://oia.ncnu.edu.tw/var/file/17/1017/img/285/675776290.pdf"
)
NCNU_SUBSIDY_RULES_PDF_URL = (
    "https://oia.ncnu.edu.tw/var/file/17/1017/img/285/554067160.pdf"
)
NCNU_DUAL_DEGREE_RULES_PDF_URL = (
    "https://oia.ncnu.edu.tw/var/file/17/1017/img/285/956940933.pdf"
)
NCNU_SOP_PDF_URL = (
    "https://oia.ncnu.edu.tw/var/file/17/1017/img/285/575480071.pdf"
)
NCNU_CREDIT_CONVERSION_PDF_URL = (
    "https://oia.ncnu.edu.tw/var/file/17/1017/img/286/410787725.pdf"
)
NCNU_APPLICATION_FORM_PDF_URL = (
    "https://oia.ncnu.edu.tw/var/file/17/1017/img/286/795655586.pdf"
)

NCNU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 39.0),
    "ielts": ("IELTS", 4.0),
    "toeic": ("TOEIC", 450.0),
}


def is_ncnu(school_name: str | None) -> bool:
  school = resolve_university(school_name)
  if school is not None and school.id == NCNU.id:
    return True
  normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
  return normalized in {
      "國立暨南國際大學",
      "暨南國際大學",
      "暨南大學",
      "暨南",
      "暨大",
      "ncnu",
      "national chi nan university",
  }


def _is_graduate(degree_level: str | None) -> bool:
  text = (degree_level or "").strip()
  return any(token in text for token in ("碩", "博", "研究"))


def ncnu_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
  degree = (degree_level or "").strip()
  year = (current_year or "").strip()
  if not degree:
    return (
        "needs_confirmation",
        (
            "尚未提供目前學制與年級；依《國立暨南國際大學學生赴海外姊妹校交換標準作業流程》與《選送優秀學生出國補助要點》第 3 點：申請人須為本校正式註冊在學且已於本校就讀至少一學期以上之學士班、碩士班或博士班學生（不包括國內及境外在職專班生、休學生；赴大陸及港澳地區交換生須至少於本校修業滿一年；跨國雙聯學位學士班及博士班須於本校修業滿二學期、碩士班須修業滿一學期）。"
        ),
    )
  if any(
      token in degree or token in year
      for token in ("在職", "學分班", "選修生", "休學", "延畢最後一學期")
  ):
    return (
        "fail",
        (
            f"已填報 {degree}{f'（{year}）' if year else ''}；依《國立暨南國際大學選送優秀學生出國補助要點》第 3 點及國際處交換生規定，國內及境外在職專班生、休學生及無正式學籍選讀生不得申請校級出國交換與補助計畫。"
        ),
    )
  if year in {"大一上", "碩一上", "博一上", "研一上", "一年級上學期"}:
    return (
        "fail",
        (
            f"已填報 {degree}（{year}）；依暨大《學生赴海外姊妹校交換標準作業流程》與《選送優秀學生出國補助要點》，申請人須已於本校註冊就讀至少一學期以上（大一下、碩一下或博一下含以上始得提出校內申請；赴大陸港澳地區交換須於本校修業滿一年）。"
        ),
    )
  is_grad = _is_graduate(degree)
  grad_note = (
      "（提醒：日本熊本大學秋季交換限科技學院研究所學生申請；跨國雙聯學位碩士班須於暨大修業滿一學期、博士班須於暨大修業滿二學期）"
      if is_grad
      else "（提醒：赴大陸及港澳地區交換生須於暨大修業滿一年［大二含以上］始得申請；跨國雙聯學位學士班須於暨大修業滿二學期；日本中央大學限人文學院學生、日本宇都宮大學限人文學院／教育學院學生申請）"
  )
  return (
      "pass",
      (
          f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合國立暨南國際大學海外與大陸港澳交換學生及雙聯學位計畫之在學學制與修業年級規定{grad_note}。"
      ),
  )


def ncnu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
  score_min = 70.0
  gpa_min = 2.5
  rank_max = 75.0
  details: list[str] = []
  passes_score = False
  passes_rank = False
  points_note = ""

  if academic_score is not None:
    details.append(f"學業總平均 {academic_score:g} 分")
    if academic_score >= score_min:
      passes_score = True
  if academic_gpa is not None:
    details.append(f"GPA {academic_gpa:g}")
    if academic_gpa >= gpa_min:
      passes_score = True
  if class_rank_percent is not None:
    details.append(f"歷年班級排名百分比前 {class_rank_percent:g}%")
    if class_rank_percent <= rank_max:
      passes_rank = True
    calc_pts = max(0.0, round(10.0 * (100.0 - class_rank_percent) / 100.0, 2))
    points_note = f"，折合《選送學生出國研修積分計算要點》學業成績積分約 {calc_pts:g} / 10 分"

  summary = "、".join(details)
  if (
      academic_score is None
      and academic_gpa is None
      and class_rank_percent is None
  ):
    return (
        "needs_confirmation",
        (
            "尚未填寫學業總平均、GPA 或班級排名百分比；依《國立暨南國際大學選送學生出國研修積分計算要點》（112年6月14日修正通過）：（1）學士班學業成績積分（滿分 10 分）以「10 分 × (100% − 班級排名百分比)」計算，碩博士班由各院綜合考量給分；（2）院排序前 25% 加 4 分、26%–50% 加 3 分、51%–75% 加 2 分、76%–100% 加 1 分；（3）海外接待姊妹校普遍要求在校 GPA 2.5–3.0（約學業平均 70–75 分以上），部分歐美名校（如美國加州大學河濱分校 3+1+MS、加拿大維多利亞大學、韓國首爾市立大學）要求 GPA 3.0 以上。"
        ),
    )

  if passes_score or passes_rank:
    elite_note = (
        "同時達到歐美日韓主流姊妹校（GPA 3.0 / 75–80 分以上）與教育部《學海飛颺》／《選送優秀學生出國補助要點》優先推薦基準"
        if (academic_score is not None and academic_score >= 75.0)
        or (academic_gpa is not None and academic_gpa >= 3.0)
        or (class_rank_percent is not None and class_rank_percent <= 50.0)
        else "符合暨大校內出國研修積分採計與一般姊妹校（GPA 2.5 / 70 分）申請基準；惟部分歐美姊妹校（如美國加州大學河濱分校、加拿大維多利亞大學、韓國首爾市立大學）要求 GPA 3.0（約 75 分）以上"
    )
    return (
        "pass",
        (
            f"已填報 {summary}{points_note}；符合國立暨南國際大學交換生甄選與海外姊妹校學業標準（{elite_note}）。"
        ),
    )

  return (
      "fail",
      (
          f"已填報 {summary}{points_note}；未達國立暨南國際大學海外交換姊妹校建議學業門檻（建議學業總平均 70 分以上、GPA 2.5 以上或班級排名百分比前 75% 以內）。"
      ),
  )


def ncnu_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
  test = (language_test or "").strip().lower()
  if partner_country in {"中國大陸", "澳門"} and (
      not test or language_score is None
  ):
    return (
        "pass",
        (
            f"申請赴{partner_country}合作姊妹校（含蘭州大學、山東大學、山東大學威海分校、吉林大學、四川大學、華南師範大學、北京第二外國語學院、中央民族大學、中南民族大學、浙江理工大學、澳門城市大學等 20 所大陸及澳門姊妹校）免附外語檢定證明；若有外語檢定成績仍可依《選送學生出國研修積分計算要點》列計主要／次要語言成績積分（提醒：香港教育大學僅於每年 4 月春季開放申請且須具備英語檢定證明）。"
        ),
    )
  if not test or language_score is None:
    return (
        "needs_confirmation",
        (
            "尚未填寫外語檢定成績。依《國立暨南國際大學選送學生出國研修積分計算要點》附表「語言積分標準對照表」及姊妹校一覽表：（1）10 分級距（CEFR B2–C2）：TOEFL iBT 95 / ITP 627、IELTS 7.0、TOEIC 880、GEPT 優級、JLPT N1–N2、TOPIK 4–6 級、DELF/DELE/Goethe B2–C2、VINATEST C 級；（2）8 分級距（CEFR B2，歐美主流姊妹校與學海飛颺門檻）：TOEFL iBT 72 / ITP 543、IELTS 6.0、TOEIC 750、GEPT 高級、JLPT N3、TOPIK 3 級、B1、VINATEST B 級；（3）5 分級距（CEFR B1，一般交換門檻）：TOEFL iBT 42 / ITP 460、IELTS 5.0、TOEIC 550、GEPT 中高級、JLPT N4、TOPIK 2 級、A2；（4）2 分級距（CEFR A2）：TOEFL iBT 39 / ITP 430、IELTS 4.0、TOEIC 450、GEPT 中級、JLPT N5、TOPIK 1 級；（5）大陸及澳門姊妹校免附外語檢定（香港教育大學須附英語檢定）。"
        ),
    )
  if test in NCNU_ENGLISH_MINIMUMS:
    label, minimum = NCNU_ENGLISH_MINIMUMS[test]
    passed = language_score >= minimum
    adv_note = "屬《選送學生出國研修積分計算要點》2 分級距（CEFR A2）"
    if (
        (test == "toefl" and language_score >= 95)
        or (test == "ielts" and language_score >= 7.0)
        or (test == "toeic" and language_score >= 880)
    ):
      adv_note = "獲《選送學生出國研修積分計算要點》主要語言最高滿分 10 分，並符合暨大全部歐美日韓雙聯與交換姊妹校最高英語門檻（含美國加州大學河濱分校 UCR、加拿大維多利亞大學、紐芬蘭紀念大學、英國羅浮堡大學、法國雷恩商學院等）"
    elif (
        (test == "toefl" and language_score >= 72)
        or (test == "ielts" and language_score >= 6.0)
        or (test == "toeic" and language_score >= 750)
    ):
      adv_note = "獲《選送學生出國研修積分計算要點》主要語言 8 分（CEFR B2），符合教育部《學海飛颺》與歐美加澳日韓主流英語授課姊妹校（TOEFL iBT 72–80 / IELTS 6.0 / TOEIC 750）門檻"
    elif (
        (test == "toefl" and language_score >= 42)
        or (test == "ielts" and language_score >= 5.0)
        or (test == "toeic" and language_score >= 550)
    ):
      adv_note = "獲《選送學生出國研修積分計算要點》主要語言 5 分（CEFR B1），符合亞洲、東南亞及部分歐洲應用科技大學英語交換門檻（TOEFL iBT 42–61 / IELTS 5.0–5.5 / TOEIC 550）"
    return (
        "pass" if passed else "fail",
        (
            f"{label} {language_score:g} {'符合' if passed else '未達'}國立暨南國際大學出國研修語言積分採認基準（最低採認門檻：{label} {minimum:g}；{adv_note}）。"
        ),
    )
  if test == "jlpt":
    level = int(language_score)
    passed = 1 <= level <= 5
    pts_map = {1: 10, 2: 10, 3: 8, 4: 5, 5: 2}
    pts = pts_map.get(level, 0)
    tier_note = (
        f"折合《選送學生出國研修積分計算要點》主要語言積分 {pts} 分；符合日本中央大學、信州大學、福井大學、宇都宮大學、熊本大學、龍谷大學、同志社大學、廣島大學等日語授課 N2/N3 門檻"
        if level in (1, 2, 3)
        else f"折合《選送學生出國研修積分計算要點》主要語言積分 {pts} 分；符合日本多摩大學、高崎經濟大學等 N4 或英語授課姊妹校申請基準（多數日本國立及私立名校日語組要求 JLPT N2 或 N3 以上）"
    )
    return (
        "pass" if passed else "fail",
        f"JLPT N{level} {'符合' if passed else '未達'}國立暨南國際大學日語能力採認基準（{tier_note}）。",
    )
  if test == "topik":
    level = int(language_score)
    passed = 1 <= level <= 6
    pts = 10 if level >= 4 else (8 if level == 3 else (5 if level == 2 else 2))
    bonus_note = (
        f"折合《選送學生出國研修積分計算要點》主要語言積分 {pts} 分；符合韓國高麗大學世宗校區、中央大學、韓國外國語大學、慶北大學、梨花女子大學、淑明女子大學、首爾市立大學、明知大學、京畿大學、嘉泉大學等韓語／英語交換門檻"
        if level >= 2
        else f"折合《選送學生出國研修積分計算要點》主要語言積分 {pts} 分；部分韓國姊妹校韓語授課要求 TOPIK 2–3 級以上（亦可搭配英語檢定申請英語授課課程）"
    )
    return (
        "pass" if passed else "fail",
        f"TOPIK {level} 級{'符合' if passed else '未達'}國立暨南國際大學韓語能力採認基準（{bonus_note}）。",
    )
  return (
      "needs_confirmation",
      f"已填報語言檢定 {language_test}（{language_score:g}）；請對照暨大《選送學生出國研修積分計算要點》附表（含 GEPT、DELF/DALF、Goethe-Zertifikat、TestDaF、DELE、VINATEST 越南語檢定）確認對應積分與接待姊妹校門檻。",
  )
