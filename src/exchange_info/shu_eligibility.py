from __future__ import annotations

import re

from .university_registry import SHU, resolve_university

SHU_GLOBAL_HOME_URL = "https://global.web.shu.edu.tw/"
SHU_OCSE_HOME_URL = "https://ocse.web.shu.edu.tw/"
SHU_EXCHANGE_OVERVIEW_URL = "https://global.web.shu.edu.tw/exchange-c1/"
SHU_EXCHANGE_INTRO_URL = "https://global.web.shu.edu.tw/exchange-c1/exchange-c2/"
SHU_2027_SPRING_EXCHANGE_URL = (
    "https://global.web.shu.edu.tw/exchange-c1/2027%E6%98%A5%E5%AD%A3%E7%8F%AD%E8%B5%B4%E5%A4%96%E4%BA%A4%E6%8F%9B%E8%A8%88%E7%95%AB%E7%94%B3%E8%AB%8B-2-2-2/"
)
SHU_2026_FALL_EXCHANGE_URL = (
    "https://global.web.shu.edu.tw/exchange-c1/2026%E7%A7%8B%E5%AD%A3%E7%8F%AD%E8%B5%B4%E5%A4%96%E4%BA%A4%E6%8F%9B%E8%A8%88%E7%95%AB%E7%94%B3%E8%AB%8B-2-2/"
)
SHU_OCSE_2027_SPRING_URL = (
    "https://ocse.web.shu.edu.tw/2027%E5%B9%B4%E3%80%90%E6%98%A5%E5%AD%A3%E3%80%91%E8%B5%B4%E5%A4%96%E4%BA%A4%E6%8F%9B%E7%94%9F%E7%94%84%E9%81%B8%E7%B0%A1%E7%AB%A0%E8%8F%AF%E8%AA%9E%E7%B5%84%EF%BC%8C%E6%AD%A1%E8%BF%8E%E4%B8%8B/"
)
SHU_OCSE_2026_FALL_URL = (
    "https://ocse.web.shu.edu.tw/2026%E5%B9%B4%E3%80%90%E7%A7%8B%E5%AD%A3%E3%80%91%E8%B5%B4%E5%A4%96%E4%BA%A4%E6%8F%9B%E7%94%9F%E7%94%84%E9%81%B8%E7%B0%A1%E7%AB%A0%E8%8F%AF%E8%AA%9E%E7%B5%84%EF%BC%8C%E6%AD%A1%E8%BF%8E%E4%B8%8B/"
)
SHU_OCSE_2027_SPRING_PDF_URL = (
    "https://ocse.web.shu.edu.tw/wp-content/uploads/sites/56/2026/09/2027SpringGeneralReg.pdf"
)
SHU_OCSE_2026_FALL_PDF_URL = (
    "https://ocse.web.shu.edu.tw/wp-content/uploads/sites/56/2026/03/2026AutumnGeneralReg0.pdf"
)
SHU_2027_SPRING_BROCHURE_PDF_URL = (
    "https://drive.google.com/file/d/1R1pH5PnffVsCjqVpkUXfNd4JMN0kgP4d/view"
)
SHU_2027_SPRING_HANDBOOK_PDF_URL = (
    "https://drive.google.com/file/d/1qcJ_W8R9-3HiYChDEYX9QBOuwE-fobTm/view"
)
SHU_2026_FALL_BROCHURE_PDF_URL = (
    "https://drive.google.com/file/d/1U9JDwBLpLCfsgze50gFvsF6ZQNNgAX5W/view"
)
SHU_2026_FALL_HANDBOOK_PDF_URL = (
    "https://drive.google.com/file/d/13rLpfpc2ZTw0EAhf5V4f6SjW2-52EIt8/view"
)
SHU_DUAL_DEGREE_PDF_URL = (
    "https://drive.google.com/file/d/1aJhQ0tXFXc5JcLWus7D7OoUbtofjycVm/view"
)
SHU_SCHOLARSHIPS_URL = "https://global.web.shu.edu.tw/scholarship-c/"
SHU_SCHOLARSHIP_PDF_URL = (
    "https://drive.google.com/file/d/1Gh8TUDjQq7aY_oQB10bhreL6PWeD3oJH/view"
)
SHU_SUBSIDY_URL = "https://global.web.shu.edu.tw/%E5%9C%8B%E9%9A%9B%E5%90%88%E4%BD%9C%E4%BA%A4%E6%B5%81%E8%A3%9C%E5%8A%A9/"
SHU_PARTNERSHIP_URL = "https://global.web.shu.edu.tw/ac-2/"
SHU_CROSS_STRAIT_PARTNERS_URL = (
    "https://ocse.web.shu.edu.tw/services/%E5%A2%83%E5%A4%96%E7%94%9F%E4%BA%8B%E5%8B%99/%E5%A7%8A%E5%A6%B9%E6%A0%A1/"
)
SHU_EXPERIENCES_URL = "https://global.web.shu.edu.tw/category/reports/"
SHU_OCSE_EXPERIENCES_URL = (
    "https://ocse.web.shu.edu.tw/category/news/mcssc/%E4%BA%A4%E6%8F%9B%E7%94%9F%E5%BF%83%E5%BE%97/"
)
SHU_SELECTION_RULES_PDF_URL = (
    "https://drive.google.com/file/d/1TsRN-kwCAsxtG-u-4PRBWV3RBlQ7KFgT/view"
)
SHU_XUEHAI_RULES_PDF_URL = (
    "https://drive.google.com/file/d/1Zd75wmOdI77JmYdfacobTaB5EZeb8V1F/view"
)
SHU_CREDIT_TRANSFER_PDF_URL = (
    "https://drive.google.com/file/d/1m2wloXzc5IM1AjqTfJ_xoOH_XQp0ogio/view"
)

SHU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 42.0),
    "ielts": ("IELTS", 5.0),
    "toeic": ("TOEIC", 700.0),
    "toefl_itp": ("TOEFL ITP", 500.0),
}


def is_shu(school_name: str | None) -> bool:
  school = resolve_university(school_name)
  if school is not None and school.id == SHU.id:
    return True
  normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
  return normalized in {
      "世新大學",
      "世新",
      "shu",
      "shih hsin university",
      "shih hsin",
  }


def _is_graduate(degree_level: str | None) -> bool:
  text = (degree_level or "").strip()
  return any(token in text for token in ("碩", "博", "研究"))


def shu_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
  degree = (degree_level or "").strip()
  year = (current_year or "").strip()
  if not degree:
    return (
        "needs_confirmation",
        (
            "尚未提供目前學制與年級；依《世新大學交換學生甄選作業要點》及《2027 春季班／2026 秋季班赴外交換計畫徵選簡章》：申請人須為於本校修業滿一學期以上之在學且具正式學籍學生（含日間及進修學制，但不含碩士在職專班；外籍生領取中華民國政府獎學金者不具申請資格）。出國進修期間須具正式學籍並繳交世新大學全額學雜費（進修學制學生須繳交研修 20 學分以上之學分費），且於同一學制內僅可錄取一次交換生。"
        ),
    )
  if any(
      token in degree or token in year
      for token in ("在職專班", "碩專", "emba", "EMBA", "學分班", "選修生", "休學")
  ):
    return (
        "fail",
        (
            f"已填報 {degree}{f'（{year}）' if year else ''}；依《世新大學交換學生甄選作業要點》第三點及赴外交換計畫徵選簡章，碩士在職專班、休學生及無正式學籍選讀生不得申請赴外交換學生計畫。"
        ),
    )
  if year in {"大一上", "碩一上", "博一上", "研一上", "一年級上學期"}:
    return (
        "fail",
        (
            f"已填報 {degree}（{year}）；依《世新大學交換學生甄選作業要點》第三點及赴外交換計畫徵選簡章，申請人須於該學制修業滿一學期以上（即使碩士班一年級上學期同學大學就讀世新，因碩士學制尚未修滿一學期亦無法申請），最早可於一年級下學期提出申請（於二年級上學期出國）。"
        ),
    )
  is_grad = _is_graduate(degree)
  grad_note = (
      "（提醒：部分姊妹校如美國朱尼亞塔學院、薩基諾谷州立大學、捷克斯柯達汽車大學、日本國學院大學、立正大學、名城大學、目白大學、縣立廣島大學、關西國際大學、韓國中央大學、東西大學、聖公會大學及多所大陸交換校僅開放學士班申請；研究生可選填法國里爾大學、德國阿沙芬堡應用科大、義大利羅馬第一大學、波蘭托倫哥白尼大學、日本東北學院大學、埼玉大學、島根縣立大學、山口大學、韓國釜山外大、明知大學、啟明大學，或申請美國威斯康辛大學雷河分校 1+1 MBA/電腦碩士雙學位）"
      if is_grad
      else "（提醒：提出申請時若為大四下學期或延畢生，須確認出發前符合校內延畢資格並繳交《世新大學赴外交換生延畢聲明書》；同一學制內僅可錄取一次交換生，亦可申請美國朱尼亞塔學院 3+1 或威斯康辛大學雷河分校 3+1 雙學士計畫）"
  )
  return (
      "pass",
      (
          f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合《世新大學交換學生甄選作業要點》修業滿一學期以上之正式學籍規定{grad_note}。"
      ),
  )


def shu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
  score_min = 75.0
  gpa_min = 2.75
  rank_max = 50.0
  details: list[str] = []
  passes_shu = False

  if academic_score is not None:
    details.append(f"歷年學業總平均 {academic_score:g} 分")
    if academic_score >= score_min:
      passes_shu = True
  if academic_gpa is not None:
    details.append(f"GPA {academic_gpa:g}")
    if academic_gpa >= gpa_min:
      passes_shu = True
  if class_rank_percent is not None:
    details.append(f"累計班排名百分比前 {class_rank_percent:g}%")
    if class_rank_percent <= rank_max:
      passes_shu = True

  summary = "、".join(details)
  if (
      academic_score is None
      and academic_gpa is None
      and class_rank_percent is None
  ):
    return (
        "needs_confirmation",
        (
            "尚未填寫歷年學業總平均、GPA 或累計班排名百分比；依《世新大學交換學生甄選作業要點》第三點及《2027 春季班／2026 秋季班赴外交換計畫徵選簡章》（歐美組／韓國組／日本組／華語組）：（1）申請時在校歷年總平均成績須達 75 分以上，或累計班排名／全班總人數為前 50%；（2）申請教育部「學海飛颺暨學海惜珠」獎學金須在校歷年成績平均達 75 分或歷年全班前 30%；（3）個別姊妹校另有 GPA 門檻（匈牙利卡羅裡加斯帕爾歸正教會大學要求 GPA 3.5、哈薩克塔拉茲斯坦國立大學與韓國聖公會大學要求 GPA 3.0、馬來西亞拉曼大學 GPA 2.5、日本埼玉大學 GPA 2.4、美國薩基諾谷州立大學／斯洛伐克普勒索夫大學／韓國中央大學 GPA 2.0）。"
        ),
    )

  if passes_shu:
    xuehai_ok = (
        (academic_score is not None and academic_score >= 75.0)
        or (class_rank_percent is not None and class_rank_percent <= 30.0)
        or (academic_gpa is not None and academic_gpa >= 3.0)
    )
    high_gpa_note = (
        "同時符合《世新大學學海飛颺暨學海惜珠甄選要點》（歷年平均 75 分或班排前 30%）與韓國聖公會大學、哈薩克塔拉茲斯坦國立大學（GPA 3.0）高門檻標準"
        if xuehai_ok
        else "符合世新大學赴外交換生甄選校內門檻（歷年總平均 75 分或累計班排名前 50%）；惟匈牙利卡羅裡加斯帕爾歸正教會大學要求 GPA 3.5、韓國聖公會大學與哈薩克塔拉茲斯坦國立大學要求 GPA 3.0"
    )
    return (
        "pass",
        (
            f"已填報 {summary}；符合世新大學赴外交換學生甄選學業標準（{high_gpa_note}）。"
        ),
    )

  return (
      "fail",
      (
          f"已填報 {summary}；未達《世新大學交換學生甄選作業要點》及赴外交換計畫徵選簡章規定之最低學業門檻（歷年總平均成績須達 75 分以上，或累計班排名為全班前 50%）。"
      ),
  )


def shu_language_check(
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
            "申請赴中國大陸及澳門地區姊妹校（含清華大學、中國人民大學、中國傳媒大學、同濟大學、南京大學、廈門大學、上海大學、重慶大學、大連理工大學、吉林大學、東北師範大學、澳門城市大學等）屬兩岸事務中心「華語組」，免附外語能力檢定證明（提醒：澳門城市大學須具流暢英語應對能力；若申請香港城市大學則須檢附 TOEFL iBT 79 或 IELTS 6.5 以上證明）。"
        ),
    )
  if not test or language_score is None:
    return (
        "needs_confirmation",
        (
            "尚未填寫外語能力檢定成績。依世新大學《2027 春季班／2026 秋季班赴外交換計畫徵選簡章》及《姊妹校手冊》：（1）歐美組與韓國組（英語授課）採認 TOEFL iBT、IELTS、TOEIC、TOEFL ITP 或 Duolingo（土耳其安卡拉大學與拉脫維亞利耶帕亞大學 iBT 42 / IELTS 5.0 / TOEIC 700、德國阿沙芬堡應用科大與斯洛伐克泛歐洲大學 iBT 57 / IELTS 5.0 / TOEIC 750、美國薩基諾谷州立大學 iBT 61 / IELTS 5.5、法國 GEDH 教育集團 iBT 65 / IELTS 5.5 / TOEIC 750、韓國明知大學 iBT 70 / IELTS 5.5 / TOEIC 750、捷克茲林托馬斯巴塔大學與法國里爾大學／義大利羅馬第一大學／波蘭托倫哥白尼大學 iBT 72 / IELTS 5.0–5.5 / TOEIC 750、美國威斯康辛大學雷河分校／安德森大學／弗森德大學 iBT 78 / IELTS 6.0 / TOEIC 750、香港城市大學 iBT 79 / IELTS 6.5、美國朱尼亞塔學院 iBT 80 / IELTS 6.5）；（2）日本組採認 JLPT N4–N1（北海道教育大學、目白大學、名城大學接受 N4；關西國際大學國際交流學院與山口大學教育學院 N3；群馬大學、立正大學、東北學院大學、埼玉大學、大阪工業大學、島根縣立大學、縣立廣島大學 N2；明星大學 N1；國學院大學需修習日文一年以上且達 iBT 55 水準）；（3）韓國組韓語授課採認 TOPIK 1–3 級（聖公會大學、仁德大學、啟明大學 TOPIK 1 級；中央大學、釜山外國語大學、明知大學、東西大學 TOPIK 3 級）；（4）華語組（中國大陸及澳門）免附外語檢定。"
        ),
    )
  if test in SHU_ENGLISH_MINIMUMS:
    label, minimum = SHU_ENGLISH_MINIMUMS[test]
    passed = language_score >= minimum
    tier_note = "達土耳其安卡拉大學、拉脫維亞利耶帕亞大學、韓國仁德／啟明大學及捷克斯柯達汽車大學（iBT 42–71 / IELTS 5.0 / TOEIC 700）基礎門檻"
    if (
        (test == "toefl" and language_score >= 80)
        or (test == "ielts" and language_score >= 6.5)
        or (test == "toeic" and language_score >= 800)
        or (test == "toefl_itp" and language_score >= 550)
    ):
      tier_note = "符合世新大學全部歐美、日韓英語授課姊妹校、香港城市大學（iBT 79 / IELTS 6.5）、日本山口大學創新與科技管理學院（TOEIC 800）以及美國朱尼亞塔學院 3+1 與威斯康辛大學雷河分校 3+1 / 1+1 雙學位計畫最高英語門檻"
    elif (
        (test == "toefl" and language_score >= 72)
        or (test == "ielts" and language_score >= 5.5)
        or (test == "toeic" and language_score >= 750)
    ):
      tier_note = "符合《世新大學學海飛颺暨學海惜珠甄選要點》（iBT 57 / IELTS 5.0 / TOEIC 750）及絕大多數歐美、日韓、馬來西亞拉曼大學姊妹校英語門檻（如法國里爾大學、ISTC、GEDH、德國阿沙芬堡應用科大、義大利羅馬第一大學、IULM、波蘭托倫哥白尼大學、捷克茲林托馬斯巴塔大學、斯洛維尼亞盧比安納大學、美國薩基諾谷州立大學、韓國東西／明知／啟明／仁德大學；美國威斯康辛大學雷河分校、安德森大學、弗森德大學亦接受 TOEIC 750）"
    elif (
        (test == "toefl" and language_score >= 57)
        or (test == "ielts" and language_score >= 5.0)
    ):
      tier_note = "符合《世新大學學海飛颺暨學海惜珠甄選要點》英語基準（TOEFL iBT 57 / IELTS 5.0）及德國阿沙芬堡應用科技大學、斯洛伐克泛歐洲大學、美國薩基諾谷州立大學（iBT 61）等姊妹校門檻"
    return (
        "pass" if passed else "fail",
        (
            f"{label} {language_score:g} {'符合' if passed else '未達'}世新大學赴外交換計畫歐美組／韓國組／雙學位英語檢定基準（最低採計門檻：{label} {minimum:g}；{tier_note}）。"
        ),
    )
  if test == "jlpt":
    level = int(language_score)
    passed = 1 <= level <= 4
    if level == 1:
      tier_note = "符合日本明星大學（JLPT N1）及全部 22 所日本姊妹校最高日語門檻，並符合日本台灣交流協會短期交換留學生獎學金申請資格"
    elif level == 2:
      tier_note = "符合《世新大學學海飛颺暨學海惜珠甄選要點》日語基準（JLPT N2）及日本群馬大學、立正大學（限女生）、東北學院大學、埼玉大學、大阪工業大學、島根縣立大學、縣立廣島大學、關西國際大學、山口大學、名城大學、目白大學、北海道教育大學等絕大多數日本姊妹校門檻（僅明星大學要求 N1）"
    elif level == 3:
      tier_note = "可申請日本關西國際大學國際交流學院（N3）、山口大學教育學院（N3），以及名城大學（N4–N2）、北海道教育大學（N4）、目白大學（N4）、東北學院大學 Other Program（N4）"
    elif level == 4:
      tier_note = "可申請日本北海道教育大學（JLPT N4）、目白大學（N4）、名城大學（N4–N2）、東北學院大學 Other Program（N4）及山口大學其他學院（N4）"
    else:
      tier_note = "世新大學日本組姊妹校最低要求 JLPT N4（北海道教育大學、目白大學、名城大學、東北學院大學 Other Program、山口大學其他學院）或修習日文一年以上（國學院大學）"
    return (
        "pass" if passed else "fail",
        f"JLPT N{level} {'符合' if passed else '未達'}世新大學赴外交換計畫日本組日語檢定基準（{tier_note}）。",
    )
  if test == "topik":
    level = int(language_score)
    passed = 1 <= level <= 6
    if level >= 3:
      tier_note = "符合韓國中央大學、釜山外國語大學、明知大學、東西大學（TOPIK 3 級）及聖公會大學、啟明大學、仁德大學（TOPIK 1 級）全部韓國姊妹校韓語門檻，並達到學海飛颺韓語基準（TOPIK 2 級以上）"
    elif level == 2:
      tier_note = "符合《世新大學學海飛颺暨學海惜珠甄選要點》韓語基準（TOPIK 2 級）及韓國聖公會大學、啟明大學、仁德大學（TOPIK 1 級）門檻（中央、釜山外大、明知、東西大學需 TOPIK 3 級或改以英檢申請）"
    elif level == 1:
      tier_note = "符合韓國聖公會大學、啟明大學、仁德大學韓語門檻（TOPIK 1 級以上；中央、釜山外大、明知、東西大學需 TOPIK 3 級或改以 TOEFL iBT / IELTS / TOEIC 申請）"
    else:
      tier_note = "韓國組姊妹校最低要求 TOPIK 1 級（聖公會、啟明、仁德）或 TOPIK 3 級（中央、釜山外大、明知、東西），或以英語檢定申請"
    return (
        "pass" if passed else "fail",
        f"TOPIK {level} 級{'符合' if passed else '未達'}世新大學赴外交換計畫韓國組韓語檢定基準（{tier_note}）。",
    )
  return (
      "needs_confirmation",
      f"已填報語言檢定 {language_test}（{language_score:g}）；請對照世新大學《2027 春季班／2026 秋季班姊妹校手冊》（TOEFL iBT / IELTS / TOEIC / Duolingo / CEFR 法語德語西語 / JLPT / TOPIK）與目標姊妹校語言門檻確認。",
  )
