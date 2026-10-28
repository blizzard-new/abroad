from __future__ import annotations

import re

from .university_registry import NDHU, resolve_university

NDHU_OIA_HOME_URL = "https://oia.ndhu.edu.tw/"
NDHU_EXCHANGE_OVERVIEW_URL = (
    "https://oia.ndhu.edu.tw/p/412-1027-21499.php?Lang=zh-tw"
)
NDHU_SELECTION_GUIDELINES_URL = (
    "https://oia.ndhu.edu.tw/p/412-1027-21505.php?Lang=zh-tw"
)
NDHU_SUBSIDY_URL = "https://oia.ndhu.edu.tw/p/412-1027-21506.php?Lang=zh-tw"
NDHU_SYSTEM_PARTNERS_URL = (
    "https://oia.ndhu.edu.tw/p/412-1027-21507.php?Lang=zh-tw"
)
NDHU_POST_SELECTION_URL = (
    "https://oia.ndhu.edu.tw/p/412-1027-21508.php?Lang=zh-tw"
)
NDHU_PRE_POST_DEPARTURE_URL = (
    "https://oia.ndhu.edu.tw/p/412-1027-21509.php?Lang=zh-tw"
)
NDHU_EXPERIENCES_URL = (
    "https://oia.ndhu.edu.tw/p/412-1027-21510.php?Lang=zh-tw"
)
NDHU_QA_URL = "https://oia.ndhu.edu.tw/p/412-1027-21511.php?Lang=zh-tw"
NDHU_DUAL_DEGREE_UNIVERSITY_URL = (
    "https://oia.ndhu.edu.tw/p/412-1027-21517.php?Lang=zh-tw"
)
NDHU_DUAL_DEGREE_COLLEGE_URL = (
    "https://oia.ndhu.edu.tw/p/412-1027-21518.php?Lang=zh-tw"
)
NDHU_DUAL_DEGREE_NEW_SOUTHBOUND_URL = (
    "https://oia.ndhu.edu.tw/p/412-1027-22313.php?Lang=zh-tw"
)
NDHU_SISTER_SCHOOLS_URL = (
    "https://oia.ndhu.edu.tw/p/412-1027-21572.php?Lang=zh-tw"
)
NDHU_REGULATIONS_URL = (
    "https://oia.ndhu.edu.tw/p/412-1027-21599.php?Lang=zh-tw"
)
NDHU_SYSTEM_MAINTENANCE_NOTICE_URL = (
    "https://oia.ndhu.edu.tw/p/406-1027-264093,r6457.php?Lang=zh-tw"
)
NDHU_2027_1_GUIDELINES_PDF_URL = (
    "https://oia.ndhu.edu.tw/var/file/27/1027/img/4796/775599658.pdf"
)
NDHU_2027_1_SLIDES_PDF_URL = (
    "https://oia.ndhu.edu.tw/var/file/27/1027/img/4796/637705288.pdf"
)
NDHU_SCHEDULE_QUOTA_PDF_URL = (
    "https://oia.ndhu.edu.tw/var/file/27/1027/img/4796/786875750.pdf"
)
NDHU_OUTBOUND_REGULATIONS_PDF_URL = (
    "https://oia.ndhu.edu.tw/var/file/27/1027/img/304/385745258.pdf"
)
NDHU_DUAL_DEGREE_REGULATIONS_PDF_URL = (
    "https://oia.ndhu.edu.tw/var/file/27/1027/img/509/651349013.pdf"
)
NDHU_CREDIT_TRANSFER_PDF_URL = (
    "https://aa.ndhu.edu.tw/var/file/2/1002/img/1231/180147644.pdf"
)

NDHU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 42.0),
    "ielts": ("IELTS", 5.0),
    "toeic": ("TOEIC", 550.0),
}


def is_ndhu(school_name: str | None) -> bool:
  school = resolve_university(school_name)
  if school is not None and school.id == NDHU.id:
    return True
  normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
  return normalized in {
      "國立東華大學",
      "東華大學",
      "東華",
      "ndhu",
      "national dong hwa university",
  }


def _is_graduate(degree_level: str | None) -> bool:
  text = (degree_level or "").strip()
  return any(token in text for token in ("碩", "博", "研究"))


def ndhu_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
  degree = (degree_level or "").strip()
  year = (current_year or "").strip()
  if not degree:
    return (
        "needs_confirmation",
        (
            "尚未提供目前學制與年級；依《國立東華大學國際交換學生出國計畫作業辦法》第 4 條及《2027年第一次國際交換學生甄選簡章》規定：申請人須為具本校學籍之在學學位生（碩士在職專班、國合會及其他專班生除外），且於出國就讀時為二年級（含）以上（即最快大一升大二時提出申請、大二上或大二下出國；碩士班及博士班在學生亦得申請），並於交換期限中全程具本校學籍。"
        ),
    )
  if any(
      token in degree or token in year
      for token in ("在職", "碩專", "國合會", "學分班", "選修生", "休學")
  ):
    return (
        "fail",
        (
            f"已填報 {degree}{f'（{year}）' if year else ''}；依《國立東華大學國際交換學生出國計畫作業辦法》第 4 條與《2027年第一次國際交換學生甄選簡章》，碩士在職專班、國合會及其他專班生、休學生或無本校正式學位學籍者不得申請校級出國交換學生計畫。"
        ),
    )
  if year in {"大一上", "碩一上", "博一上", "研一上", "一年級上學期"}:
    return (
        "fail",
        (
            f"已填報 {degree}（{year}）；依東華大學《2027年第一次國際交換學生甄選簡章》與 Q&A 規定，申請人「出國就讀時須為二年級（含）以上」，且須附上在東華就讀前一學期或歷年成績單（GPA 達 2.5 以上），故大一上、碩一上或博一上尚無東華完整一學期成績單者，須俟下學期或二年級始得提出申請。"
        ),
    )
  is_grad = _is_graduate(degree)
  grad_note = (
      "（提醒：碩士班及博士班在學生得申請出國交換與雙聯學位；交換期間仍須維持東華在學學籍並註冊繳費，不得於交換期間畢業或休學）"
      if is_grad
      else "（提醒：學士班學生出國就讀時須為二年級［含］以上，大四延畢生亦可於大四時提出申請、延畢學期出國交換；交換期間不得辦理畢業或休學）"
  )
  return (
      "pass",
      (
          f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合國立東華大學國際交換學生出國計畫與雙聯學位制之在學學制及修業年級規定{grad_note}。"
      ),
  )


def ndhu_academic_check(
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

  summary = "、".join(details)
  if (
      academic_score is None
      and academic_gpa is None
      and class_rank_percent is None
  ):
    return (
        "needs_confirmation",
        (
            "尚未填寫學業總平均、GPA 或班級排名百分比；依《國立東華大學國際交換學生出國計畫作業辦法》第 4 條及《2027年第一次國際交換學生甄選簡章》規定：（1）一般交換生校內申請門檻為「前一學期或歷年平均 GPA 達 2.5（滿分 4.5，約百分制 70 分）以上」；（2）若欲同時申請東華校內「出國交換獎助學金」（或教育部學海飛颺、國際移動力先鋒計畫），歷年平均 GPA 須達 3.3（約百分制 78–80 分）以上；（3）校內書面審查總成績配分為：學業表現（歷年成績＋語言能力）20%＋任務企劃書 35%＋讀書計畫 35%＋資料加分 10%。"
        ),
    )

  if passes_score or passes_rank:
    scholarship_eligible = (
        (academic_gpa is not None and academic_gpa >= 3.3)
        or (academic_score is not None and academic_score >= 78.0)
        or (class_rank_percent is not None and class_rank_percent <= 35.0)
    )
    elite_note = (
        "同時達到東華大學「出國交換獎助學金」與「國際移動力先鋒計畫」（歷年 GPA 3.3 以上）及歐美日韓頂尖姊妹校學業門檻"
        if scholarship_eligible
        else "符合東華大學校內一般交換生申請門檻（前一學期或歷年 GPA 2.5／約 70 分以上）；惟若欲申請東華「出國交換獎助學金」或「國際移動力先鋒計畫」，歷年 GPA 須達 3.3（約 78 分）以上"
    )
    return (
        "pass",
        (
            f"已填報 {summary}；符合國立東華大學國際交換學生甄選學業標準（{elite_note}）。"
        ),
    )

  return (
      "fail",
      (
          f"已填報 {summary}；未達國立東華大學《國際交換學生出國計畫作業辦法》第 4 條規定之最低學業門檻（前一學期或歷年平均 GPA 須達 2.5［滿分 4.5］以上，約百分制 70 分以上）。"
      ),
  )


def ndhu_language_check(
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
            "申請赴中國大陸合作姊妹校（含北京大學、復旦大學、南京大學、武漢大學、四川大學、廈門大學、南開大學、天津大學、西安交通大學、蘭州大學、山東、吉林、東北、華東師範、華中師範等 41 所大陸姊妹校）免附外語能力檢定證明（若有外語檢定成績仍可上傳作為書面審查「學業表現 20%」及「資料加分 10%」之佐證）。"
        ),
    )
  if not test or language_score is None:
    return (
        "needs_confirmation",
        (
            "尚未填寫外語檢定成績。依東華大學《2027年第一次國際交換學生甄選簡章》與《國際交換學生出國計畫作業辦法》：（1）申請英語系及歐美新南向姊妹校須具備 TOEFL iBT、IELTS、TOEIC 或全民英檢（GEPT）等有效語言檢定成績（一般姊妹校約需 CEFR B1［TOEIC 550 / IELTS 5.0 / TOEFL iBT 42］以上；歐美主流校、校級雙聯學位及「國際移動力先鋒計畫」多要求 CEFR B2［TOEFL iBT 72–80 / IELTS 6.0 / TOEIC 750–785］以上）；（2）日本姊妹校日語組要求 JLPT N1–N3（英語授課組可憑英語檢定申請）；（3）韓國姊妹校韓語組要求 TOPIK 2–4 級（英語授課組可憑英語檢定申請）；（4）大陸地區姊妹校免附外語檢定證明。"
        ),
    )
  if test in NDHU_ENGLISH_MINIMUMS:
    label, minimum = NDHU_ENGLISH_MINIMUMS[test]
    passed = language_score >= minimum
    adv_note = "符合亞洲及一般海外交換姊妹校基礎英語門檻（CEFR B1）"
    if (
        (test == "toefl" and language_score >= 79)
        or (test == "ielts" and language_score >= 6.5)
        or (test == "toeic" and language_score >= 800)
    ):
      adv_note = "符合東華大學「國際移動力先鋒計畫」（美國懷俄明大學、英國亞伯立斯威大學、法國巴黎第十二大學、德國克勞斯塔爾工業大學、西班牙納瓦拉公立大學、紐西蘭梅西大學等）、校級雙聯學位（澳洲雪梨科技大學 UTS、美國舊金山州立大學 SFSU、德州大學阿靈頓分校 UTA、紐西蘭林肯大學、法國雷恩商學院）及教育部學海飛颺高階英語門檻"
    elif (
        (test == "toefl" and language_score >= 72)
        or (test == "ielts" and language_score >= 6.0)
        or (test == "toeic" and language_score >= 750)
    ):
      adv_note = "達到 CEFR B2 級距，符合歐美主流交換姊妹校、教育部《學海飛颺》與東華校內出國交換獎助學金之英語能力要求"
    return (
        "pass" if passed else "fail",
        (
            f"{label} {language_score:g} {'符合' if passed else '未達'}國立東華大學海外交換語言檢定採認基準（一般建議門檻：{label} {minimum:g}；{adv_note}）。"
        ),
    )
  if test == "jlpt":
    level = int(language_score)
    passed = 1 <= level <= 5
    tier_note = (
        "符合日本北海道大學、東北大學、東京都立大學、青山學院大學（先鋒計畫）、立教大學、芝浦工業大學、廣島大學（交換暨人社院雙聯）、岡山大學、大阪公立大學、長崎大學、佐賀大學、琉球大學等日語授課 N2/N3 門檻"
        if level in (1, 2, 3)
        else "符合日本部分姊妹校基礎日語或搭配英語授課計畫門檻（多數日本國立及私立名校日語組要求 JLPT N2 或 N3 以上）"
    )
    return (
        "pass" if passed else "fail",
        f"JLPT N{level} {'符合' if passed else '未達'}國立東華大學赴日交換日語能力採認基準（{tier_note}）。",
    )
  if test == "topik":
    level = int(language_score)
    passed = 1 <= level <= 6
    bonus_note = (
        "符合韓國中央大學、韓國外國語大學、首爾市立大學、建國大學、仁荷大學（先鋒計畫）、慶北大學、全南大學、釜慶大學、東亞大學、韓國天主教大學、高麗大學世宗校區等韓語／英語交換門檻"
        if level >= 2
        else "部分韓國姊妹校韓語授課組要求 TOPIK 2–3 級以上（亦可搭配英語檢定申請英語授課課程）"
    )
    return (
        "pass" if passed else "fail",
        f"TOPIK {level} 級{'符合' if passed else '未達'}國立東華大學赴韓交換韓語能力採認基準（{bonus_note}）。",
    )
  return (
      "needs_confirmation",
      f"已填報語言檢定 {language_test}（{language_score:g}）；請對照東華大學國際事務處《交換學校一覽表》各姊妹校最新 Fact Sheet（含 GEPT 全民英檢、DELF/DALF、Goethe-Zertifikat、TestDaF、DELE 等）確認是否符合志願校門檻。",
  )
