from __future__ import annotations

import re

from .university_registry import CSMU, resolve_university

CSMU_OIA_ZH_HOME_URL = "https://oia.csmu.edu.tw/?Lang=zh-tw"
CSMU_OIA_EN_HOME_URL = "https://oia.csmu.edu.tw/?Lang=en"
CSMU_SISTER_SCHOOLS_OVERVIEW_URL = "https://oia.csmu.edu.tw/p/412-1004-75.php?Lang=zh-tw"
CSMU_PARTNERS_AMERICAS_ZH_URL = "https://oia.csmu.edu.tw/p/412-1004-2933.php?Lang=zh-tw"
CSMU_PARTNERS_ASIA_PACIFIC_ZH_URL = "https://oia.csmu.edu.tw/p/412-1004-3963.php?Lang=zh-tw"
CSMU_PARTNERS_EUROPE_AFRICA_ZH_URL = "https://oia.csmu.edu.tw/p/412-1004-3964.php?Lang=zh-tw"
CSMU_PARTNERS_EN_URL = "https://oia.csmu.edu.tw/p/412-1004-3902.php?Lang=en"
CSMU_EXCHANGE_REGS_FORMS_URL = "https://oia.csmu.edu.tw/p/412-1004-3228.php?Lang=zh-tw"
CSMU_EXCHANGE_FAQ_URL = "https://oia.csmu.edu.tw/p/412-1004-3227.php?Lang=zh-tw"
CSMU_XUEHAI_HOW_TO_APPLY_URL = "https://oia.csmu.edu.tw/p/412-1004-3092.php?Lang=zh-tw"
CSMU_XUEHAI_REGS_FORMS_URL = "https://oia.csmu.edu.tw/p/412-1004-3094.php?Lang=zh-tw"
CSMU_XUEHAI_COUNTS_URL = "https://oia.csmu.edu.tw/p/412-1004-3091.php?Lang=zh-tw"
CSMU_STUDENT_EXPERIENCES_URL = "https://oia.csmu.edu.tw/p/403-1004-725-1.php?Lang=zh-tw"

CSMU_2027_ST_MARTINS_NOTICE_URL = "https://oia.csmu.edu.tw/p/406-1004-77969,r830.php?Lang=zh-tw"
CSMU_2027_TOKUSHIMA_NOTICE_URL = "https://oia.csmu.edu.tw/p/406-1004-77970,r830.php?Lang=zh-tw"
CSMU_2027_OAKLAND_NOTICE_URL = "https://oia.csmu.edu.tw/p/406-1004-77972,r830.php?Lang=zh-tw"
CSMU_2027_LSU_NOTICE_URL = "https://oia.csmu.edu.tw/p/406-1004-77958,r830.php?Lang=zh-tw"
CSMU_116_XUEHAI_FEIYANG_NOTICE_URL = "https://oia.csmu.edu.tw/p/405-1004-78068,c4359.php?Lang=zh-tw"
CSMU_115_2_XUEHAI_ZHUMENG_NOTICE_URL = "https://oia.csmu.edu.tw/p/406-1004-77774,r830.php?Lang=zh-tw"
CSMU_2026_KAWAMURA_NOTICE_URL = "https://oia.csmu.edu.tw/p/406-1004-71185,r830.php?Lang=zh-tw"

CSMU_EXCHANGE_SELECTION_REGS_PDF_URL = "https://oia.csmu.edu.tw/var/file/4/1004/img/1597/131990159.pdf"
CSMU_OVERSEAS_COURSE_REGS_PDF_URL = "https://oia.csmu.edu.tw/var/file/4/1004/img/1597/191294726.pdf"
CSMU_XUEHAI_SUBSIDY_REGS_PDF_URL = "https://oia.csmu.edu.tw/var/file/4/1004/img/1595/570112202.pdf"

CSMU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 71.0),
    "ielts": ("IELTS", 5.5),
    "toeic": ("TOEIC", 700.0),
}


def is_csmu(school_name: str | None) -> bool:
  school = resolve_university(school_name)
  if school is not None and school.id == CSMU.id:
    return True
  normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
  return normalized in {
      "中山醫學大學",
      "中山醫大",
      "中山醫",
      "csmu",
      "chung shan medical university",
  }


def _is_graduate(degree_level: str | None) -> bool:
  text = (degree_level or "").strip()
  return any(token in text for token in ("碩", "博", "研究"))


def csmu_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
  degree = (degree_level or "").strip()
  year = (current_year or "").strip()
  if not degree:
    return (
        "needs_confirmation",
        (
            "尚未提供目前學制與年級；依《中山醫學大學選送學生出國研修甄選辦法》、《學生出國選修課程辦法》及《教育部116年度學海飛颺、學海惜珠甄選公告》規定：申請人須為本校在學滿一學期以上之學士班、碩士班或博士班學生（應屆畢業最後一學期及延畢生不得申請交換；出國期間須維持中山醫在學學籍並繳交全額學雜費，出國交換次數以 2 次、總修業時間不超過 2 年為限）。"
        ),
    )
  if any(token in degree or token in year for token in ("學分班", "選修生", "休學", "延畢")):
    return (
        "fail",
        (
            f"已填報 {degree}{f'（{year}）' if year else ''}；依《中山醫學大學選送學生出國研修甄選辦法》及《學生出國選修課程辦法》第4條規定，應屆畢業最後一學期、延畢生、休學生或非正式學籍生不得申請出國交換研修與教育部學海計畫獎助。"
        ),
    )
  is_grad = _is_graduate(degree)
  if "在職" in degree:
    return (
        "needs_confirmation",
        (
            f"已填報 {degree}{f'（{year}）' if year else ''}；依教育部《鼓勵國內大專校院選送學生出國研修或國外專業實習補助要點》規定，國內及境外在職專班生不得申請教育部學海飛颺、學海惜珠、學海築夢及新南向學海築夢補助，惟得依各學院規定洽詢自費海外專業研習。"
        ),
    )
  if not is_grad and year in {"大一上"}:
    return (
        "fail",
        (
            f"已填報 {degree}（{year}）；依中山醫大《教育部116年度學海飛颺、學海惜珠甄選公告》及《2027年赴美國聖馬丁大學／密西根州奧克蘭大學／日本德島文理大學交換甄選公告》規定，申請人須於本校在學至少滿一學期並具歷年成績單（出國時至少完成大一課程），大一上學期新生尚不得提出申請。"
        ),
    )
  return (
      "pass",
      (
          f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合中山醫學大學出國交換研修、跨國雙聯學位（奧克蘭大學、安德魯大學、杜肯大學、德島文理大學 PP 計畫）、海外研究獎學金（美國路易斯安那州立大學醫學中心 LSUHSC 限碩博士生）及臨床專業實習之在學學籍規定。"
      ),
  )


def csmu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
  is_grad = _is_graduate(degree_level)
  min_pass_score = 70.0 if is_grad else 60.0
  target_score = 75.0
  xuehai_score = 80.0
  target_gpa = 3.0
  target_rank = 40.0
  details: list[str] = []
  passes_xuehai = False
  passes_exchange_gpa = False
  passes_basic = False

  if academic_score is not None:
    details.append(f"學業平均 {academic_score:g} 分")
    if academic_score >= xuehai_score:
      passes_xuehai = True
      passes_exchange_gpa = True
      passes_basic = True
    elif academic_score >= target_score:
      passes_exchange_gpa = True
      passes_basic = True
    elif academic_score >= min_pass_score:
      passes_basic = True
  if academic_gpa is not None:
    details.append(f"GPA {academic_gpa:g}")
    if academic_gpa >= target_gpa:
      passes_exchange_gpa = True
      passes_basic = True
    elif academic_gpa >= 2.5:
      passes_basic = True
  if class_rank_percent is not None:
    details.append(f"系所／班級排名前 {class_rank_percent:g}%")
    if class_rank_percent <= target_rank:
      passes_xuehai = True
      passes_exchange_gpa = True
      passes_basic = True

  summary = "、".join(details)
  if academic_score is None and academic_gpa is None and class_rank_percent is None:
    return (
        "needs_confirmation",
        (
            "尚未填寫學業平均、GPA 或系所排名；依中山醫大《2027年赴美國聖馬丁大學／日本德島文理大學／美國奧克蘭大學交換生及學位連讀甄選公告》及《教育部116年度學海飛颺、學海惜珠甄選公告》規定：（1）申請聖馬丁大學、德島文理大學、杜肯大學及奧克蘭大學生物學 4+1/4+2 學碩連讀須達歷年 GPA 3.0（約 75 分）以上（奧克蘭大學 ASAP 交換為 GPA 2.5 以上）；（2）申請教育部學海飛颺／惜珠獎學金須達在校學業總平均 80 分以上或系所排名前 40%。"
        ),
    )

  if passes_xuehai:
    return (
        "pass",
        (
            f"已填報 {summary}；同時符合中山醫學大學《教育部116年度學海飛颺／學海惜珠》獎學金門檻（在校學業總平均 80 分以上或系所排名前 40%）及美國聖馬丁大學、奧克蘭大學、日本德島文理大學等重點姊妹校交換與雙聯學位（GPA 3.0 以上）標準。"
        ),
    )

  if passes_exchange_gpa:
    return (
        "pass",
        (
            f"已填報 {summary}；符合中山醫學大學赴美國聖馬丁大學、日本德島文理大學、美國奧克蘭大學、安德魯大學、杜肯大學之出國交換與雙聯學位門檻（GPA 3.0 / 學業平均 75 分以上；惟若欲同時申請教育部 116 年度學海飛颺／惜珠獎學金，須達在校學業總平均 80 分以上或系所排名前 40%）。"
        ),
    )

  if passes_basic:
    return (
        "needs_confirmation",
        (
            f"已填報 {summary}；符合美國密西根州奧克蘭大學（Oakland University）International ASAP 交換計畫（GPA 2.5 以上）或部分學海築夢海外實習基本標準，惟未達聖馬丁大學、德島文理大學免學費交換生（GPA 3.0 以上）及教育部學海飛颺／惜珠（總平均 80 分以上或系排名前 40%）門檻。"
        ),
    )

  return (
      "fail",
      (
          f"已填報 {summary}；未達中山醫學大學出國交換研修與教育部學海計畫學業基準（GPA 3.0 / 學業總平均 75–80 分 / 系所排名前 40%）。"
      ),
  )


def csmu_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
  test = (language_test or "").strip().lower()
  if partner_country in {"中國大陸", "澳門"} and (not test or language_score is None):
    return (
        "pass",
        (
            f"申請赴{partner_country}合作姊妹校或教學醫院短期交流免檢附外語檢定證明（提醒：辦理赴陸教育交流活動應依教育部規定落實填報登錄平臺，且出國選課須先完成《中山醫學大學學生出國選修課程申請表》審核）。"
        ),
    )
  if not test or language_score is None:
    return (
        "needs_confirmation",
        (
            "尚未填寫外語檢定成績。依中山醫大 116 學年度（2027）出國交換、學位連讀與學海計畫公告：（1）美國聖馬丁大學要求 TOEFL iBT 71 / ITP 525 / TOEIC 700 / IELTS 6.0 以上；（2）美國奧克蘭大學要求 TOEFL iBT 79 / IELTS 6.5 / Duolingo 105（ESL 銜接為 iBT 68 / IELTS 6.0 / Duolingo 95）；（3）美國安德魯大學與杜肯大學雙聯要求 TOEFL iBT 80 / IELTS 6.5；（4）日本德島文理大學交換及 PP 研究所銜接計畫要求 JLPT N2（或 EJU 200 分）以上。"
        ),
    )
  if test in CSMU_ENGLISH_MINIMUMS:
    label, minimum = CSMU_ENGLISH_MINIMUMS[test]
    passed = language_score >= minimum
    adv_note = "符合美國聖馬丁大學（TOEFL iBT 71 / TOEIC 700）及學海築夢海外專業實習基本英語門檻"
    if (test == "toefl" and language_score >= 80) or (
        test == "ielts" and language_score >= 6.5
    ) or (test == "toeic" and language_score >= 800):
      adv_note = "符合中山醫大全部歐美澳與新加坡合作校院最高英語標準（含美國奧克蘭大學 iBT 79 / IELTS 6.5、安德魯大學與杜肯大學雙聯 iBT 80 / IELTS 6.5、聖馬丁大學 iBT 71 / IELTS 6.0、新加坡中央醫院與國大醫院臨床實習及教育部學海飛颺獎學金）"
    elif (test == "toefl" and language_score >= 79) or (
        test == "ielts" and language_score >= 6.0
    ) or (test == "toeic" and language_score >= 750):
      adv_note = "符合美國聖馬丁大學（iBT 71 / IELTS 6.0 / TOEIC 700）、奧克蘭大學（iBT 79）、薩盧斯大學與太平洋大學視光臨床實習及教育部學海飛颺英語門檻"
    return (
        "pass" if passed else "fail",
        (
            f"{label} {language_score:g} {'符合' if passed else '未達'}中山醫學大學出國交換、雙聯學位與海外臨床實習英語標準（基準：{label} {minimum:g}；{adv_note}）。"
        ),
    )
  if test == "jlpt":
    level = int(language_score)
    passed = level in (1, 2, 3)
    tier_note = (
        "符合日本德島文理大學免學費交換生與 PP 赴日升學研究所課程銜接計畫（JLPT N2 以上）、東邦大學、東京醫科大學、順天堂大學、日本齒科大學、目白大學、新潟醫療福祉大學等全部日本姊妹校日語標準"
        if level in (1, 2)
        else (
            "符合日本德島文理大學夏季日語文化研修團或部分短期見習門檻（若申請德島文理大學學期免學費交換生、PP 研究所銜接計畫或教育部學海飛颺日語組則須達 JLPT N2 以上）"
            if level == 3
            else "未達中山醫大日本合作姊妹校 JLPT N2 日語檢定門檻"
        )
    )
    return (
        "pass" if passed else "fail",
        f"JLPT N{level} {'符合' if passed else '未達'}中山醫學大學日本合作姊妹校日語檢定要求（{tier_note}）。",
    )
  if test == "topik":
    level = int(language_score)
    passed = 2 <= level <= 6
    return (
        "pass" if passed else "fail",
        f"TOPIK {level} 級{'符合' if passed else '未達'}中山醫學大學韓國合作姊妹校（嶺南大學 Yeungnam University）韓語檢定基準。",
    )
  if test in {"delf", "dalf", "tcf", "cefr"}:
    passed = language_score >= 2
    return (
        "pass" if passed else "fail",
        "已填報歐洲語言檢定成績；申請法國視光高等學院（ISO）、奧地利維也納醫學大學、瑞士伯恩大學、波蘭華沙醫學大學、匈牙利德布勒森大學等歐洲合作校請確認符合 B1/B2 或英語授課標準。",
    )
  if test == "duolingo":
    passed = language_score >= 95
    tier_note = (
        "符合美國密西根州奧克蘭大學（Oakland University）生物學 4+1/4+2 學碩連讀與一般交換生英語門檻（Duolingo 105 以上）"
        if language_score >= 105
        else (
            "符合美國密西根州奧克蘭大學（Oakland University）International ASAP 銜接交換英語門檻（Duolingo 95 以上；生物學 4+1/4+2 雙聯為 105 以上）"
            if language_score >= 95
            else "未達美國密西根州奧克蘭大學（Oakland University）Duolingo 95–105 英語門檻"
        )
    )
    return (
        "pass" if passed else "fail",
        f"Duolingo {language_score:g} {'符合' if passed else '未達'}中山醫學大學合作校英語檢定要求（{tier_note}）。",
    )
  return (
      "needs_confirmation",
      f"已填報語言檢定 {language_test}（{language_score:g}）；請對照中山醫大國際事務處各校交換／雙聯甄選簡章與教育部 116 年度學海飛颺／惜珠公告確認是否符合指定外語標準。",
  )
