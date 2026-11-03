from __future__ import annotations

import re

from .university_registry import NUU, resolve_university

NUU_OIA_HOME_URL = "https://oia.nuu.edu.tw/"
NUU_OUTBOUND_OVERVIEW_URL = "https://oia.nuu.edu.tw/p/412-1068-1242.php"
NUU_REGULATIONS_URL = "https://oia.nuu.edu.tw/p/412-1068-4274.php"
NUU_PARTNER_LIST_URL = "https://oia.nuu.edu.tw/p/412-1068-5201.php"
NUU_EXCHANGE_ANNOUNCEMENTS_URL = "https://oia.nuu.edu.tw/p/412-1068-5616.php"
NUU_EXCHANGE_FORMS_URL = "https://oia.nuu.edu.tw/p/412-1068-5617.php"
NUU_EXCHANGE_REPORTS_URL = "https://oia.nuu.edu.tw/p/412-1068-6601.php"
NUU_XUEHAI_OVERVIEW_URL = "https://oia.nuu.edu.tw/p/412-1068-5605.php"
NUU_XUEHAI_FEIYANG_URL = "https://oia.nuu.edu.tw/p/412-1068-5608.php"
NUU_XUEHAI_XIZHU_URL = "https://oia.nuu.edu.tw/p/412-1068-5609.php"
NUU_XUEHAI_ZHUMENG_URL = "https://oia.nuu.edu.tw/p/412-1068-5610.php"
NUU_DUAL_DEGREE_URL = "https://oia.nuu.edu.tw/p/405-1068-53495,c10935.php?Lang=zh-tw"
NUU_NIT_SUMMER_2026_URL = "https://oia.nuu.edu.tw/p/405-1068-54408,c10935.php?Lang=zh-tw"
NUU_EXCHANGE_RULES_PDF_URL = (
    "https://oia.nuu.edu.tw/var/file/68/1068/img/2871/409353423.pdf"
)
NUU_INTL_EXCHANGE_RULES_PDF_URL = (
    "https://oia.nuu.edu.tw/var/file/68/1068/img/2871/480880843.pdf"
)
NUU_DUAL_DEGREE_RULES_PDF_URL = (
    "https://oia.nuu.edu.tw/var/file/68/1068/img/2871/905555154.pdf"
)
NUU_LANGUAGE_STANDARDS_PDF_URL = (
    "https://oia.nuu.edu.tw/var/file/68/1068/img/3121/266944988.pdf"
)
NUU_OVERSEAS_GRANT_PDF_URL = (
    "https://oia.nuu.edu.tw/var/file/68/1068/img/2871/686071848.pdf"
)
NUU_XUEHAI_SELECTION_RULES_PDF_URL = (
    "https://oia.nuu.edu.tw/p/405-1068-42099,c4274.php?Lang=zh-tw"
)
NUU_CREDIT_CONVERSION_PDF_URL = (
    "https://oia.nuu.edu.tw/p/405-1068-24627,c5617.php?Lang=zh-tw"
)
NUU_EXCHANGE_SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/18Hj-lWko1BrEwy4dWYn-qCHJdalff0t_/edit?gid=110584674#gid=110584674"
)
NUU_PARTNER_SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/1t40XgNHPIAEXJcZGb7o-xKFL78cbvUtyYm4OfOZHVLc/edit?usp=sharing"
)

NUU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 57.0),
    "ielts": ("IELTS", 4.0),
    "toefl_itp": ("TOEFL ITP", 457.0),
    "toeic": ("TOEIC", 550.0),
}


def is_nuu(school_name: str | None) -> bool:
  school = resolve_university(school_name)
  if school is not None and school.id == NUU.id:
    return True
  normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
  return normalized in {
      "國立聯合大學",
      "聯合大學",
      "聯大",
      "nuu",
      "national united university",
  }


def _is_graduate(degree_level: str | None) -> bool:
  text = (degree_level or "").strip()
  return any(token in text for token in ("碩", "博", "研究"))


def nuu_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
  degree = (degree_level or "").strip()
  year = (current_year or "").strip()
  if not degree:
    return (
        "needs_confirmation",
        (
            "尚未提供目前學制與年級；依《國立聯合大學國際交換學生作業要點》第 2 點規定：具本校大學部及研究所學籍之在學學生（不含以在職生身分入學者）皆可提出申請，惟各姊妹校之年級及院系/所限制以「出國交換當時」之學籍身分與年級為準（非提出申請時）。境外生（外籍生、僑生、陸生）可申請，但不得交換回其所屬國家；同一學制內已獲推薦出國交換或無故放棄者不得再申請。"
        ),
    )
  if any(
      token in degree or token in year
      for token in ("在職專班", "碩專", "emba", "EMBA", "學分班", "選修生", "休學")
  ):
    return (
        "fail",
        (
            f"已填報 {degree}{f'（{year}）' if year else ''}；依《國立聯合大學國際交換學生作業要點》第 2 點及《學海系列計畫甄選作業要點》，以在職生身分入學者、休學生或無正式一般生學籍者不得申請出國交換與教育部學海系列計畫。"
        ),
    )
  is_grad = _is_graduate(degree)
  grad_note = (
      "（提醒：各姊妹校之年級與系所限制以「出國交換當時」之學籍為準；日本甲南大學限碩一至碩二上，部分日本國立高專限大學部大二至大三或專科生轉入碩一；交換期間研究所學生每學期至少須修讀 1 門課程及格）"
      if is_grad
      else "（提醒：各姊妹校之年級與系所限制以「出國交換當時」之身分與年級為準，故大一學生可提前申請大二出國交換；日本國立高專限理工與電資學院大二至大三、德國馬德堡大學限大三以上、加拿大安大略理工大學限大三下及大四、美國 FSU/FIT/Boise State 2+2 雙聯學位限修畢大一至大二課程後赴美修讀大三至大四；交換期間大學部學生每學期至少須修讀 3 門課程及格）"
  )
  return (
      "pass",
      (
          f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合國立聯合大學《國際交換學生作業要點》第 2 點之在學身分規定{grad_note}。"
      ),
  )


def nuu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
  score_min = 60.0
  gpa_min = 2.5
  rank_max = 50.0
  details: list[str] = []
  passes_general = False

  if academic_score is not None:
    details.append(f"學業平均 {academic_score:g} 分")
    if academic_score >= score_min:
      passes_general = True
  if academic_gpa is not None:
    details.append(f"GPA {academic_gpa:g}")
    if academic_gpa >= gpa_min:
      passes_general = True
  if class_rank_percent is not None:
    details.append(f"班排名百分比前 {class_rank_percent:g}%")
    if class_rank_percent <= rank_max:
      passes_general = True

  summary = "、".join(details)
  if (
      academic_score is None
      and academic_gpa is None
      and class_rank_percent is None
  ):
    return (
        "needs_confirmation",
        (
            "尚未填寫歷年學業平均、GPA 或班級排名百分比；依國立聯合大學《國際交換學生作業要點》第 3 點及第 4 點：（1）報名須檢附含排名之中英文歷年學業成績單（赴大陸以外地區大學部在校成績占書審 50%、研究所占 30%；赴大陸地區大學部占 60%、研究所占 40%），校內甄選總成績未達 60 分者不予推薦；（2）個別歐美交換與雙聯姊妹校設有 GPA 門檻：美國明尼蘇達州立大學曼卡托分校要求 GPA 2.5 以上、美國南猶他大學（SUU）要求 GPA 2.75 以上、加拿大安大略理工大學與美國佛羅里達理工學院（FIT 獎學金門檻）要求 GPA 3.0 以上、加拿大卡加利大學要求 GPA 3.2 以上。"
        ),
    )

  if passes_general:
    tier_notes: list[str] = []
    if (academic_gpa is not None and academic_gpa >= 3.2) or (
        academic_score is not None and academic_score >= 80.0
    ):
      tier_notes.append(
          "已達加拿大卡加利大學（GPA 3.2）、安大略理工大學（GPA 3.0）、美國佛羅里達理工學院 FIT 獎學金門檻（GPA 3.0）及全部姊妹校最高學業標準"
      )
    elif (academic_gpa is not None and academic_gpa >= 3.0) or (
        academic_score is not None and academic_score >= 75.0
    ):
      tier_notes.append(
          "符合加拿大安大略理工大學（GPA 3.0）、美國佛羅里達理工學院 FIT 每學期 USD 5,000 獎學金門檻（GPA 3.0）、南猶他大學 SUU（GPA 2.75）及明尼蘇達州立大學曼卡托分校（GPA 2.5）門檻（卡加利大學要求 GPA 3.2 以上）"
      )
    else:
      tier_notes.append(
          "符合聯大校內甄選及多數亞太、歐洲姊妹校與美國明尼蘇達州立大學曼卡托分校（GPA 2.5）門檻，惟美國南猶他大學要求 GPA 2.75、安大略理工大學與 FIT 獎學金要求 GPA 3.0、卡加利大學要求 GPA 3.2 以上"
      )
    return (
        "pass",
        f"已填報 {summary}；符合國立聯合大學出國交換甄選學業標準（{'；'.join(tier_notes)}）。",
    )

  return (
      "needs_confirmation",
      (
          f"已填報 {summary}；依《國立聯合大學國際交換學生作業要點》第 4 點，校內甄選總成績未達 60 分者不予推薦，且歐美交換與雙聯姊妹校（如明尼蘇達州立大學 GPA 2.5、南猶他大學 GPA 2.75、安大略理工大學 GPA 3.0、卡加利大學 GPA 3.2）設有學業門檻，建議確認目標姊妹校之個別 GPA 要求。"
      ),
  )


def nuu_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
  test = (language_test or "").strip().lower()
  if partner_country in {"中國大陸", "中國"} and (
      not test or language_score is None
  ):
    return (
        "pass",
        (
            "申請赴中國大陸地區姊妹校交換為中文授課，依《國立聯合大學國際交換學生作業要點》第 3 點及第 4 點免附外國語言能力檢定證明（大陸地區書審採計：大學部在校成績 60%＋自傳 15%＋讀書計畫/動機信 20%＋其他 5%；研究所在校成績 40%＋自傳 25%＋讀書計畫/動機信 30%＋其他 5%）。"
        ),
    )
  if not test or language_score is None:
    return (
        "needs_confirmation",
        (
            "尚未填寫外語能力檢定成績。依《國立聯合大學學生赴國外研修留學國語言能力參考標準》及《交換學校一覽表》（非大陸地區外語能力占書審 20%）：（1）英語參考標準：TOEFL iBT 57 / TOEFL ITP 457 / IELTS 4.0 / TOEIC 550 / GEPT 中級複試通過（美國明尼蘇達州立大學、南猶他大學 SUU、霜堡州立大學 FSU 要求 iBT 61–71 / IELTS 5.5–6.0；美國佛羅里達理工學院 FIT、樹城州立大學 Boise State、加拿大安大略理工大學、卡加利大學要求 iBT 79–86 / IELTS 6.0–6.5）；（2）日語參考標準：日本國立高專（宇部、高知、新居濱、阿南、木更津、明石、小山、釧路）要求 JLPT N3 以上或英語 TOEIC 550 以上；日本甲南大學、國立愛知教育大學要求 JLPT N2 以上；（3）韓語參考標準：韓國仁荷大學、國立昌原大學要求 TOPIK 3 級或英語 TOEIC 550 / iBT 71 / IELTS 5.5 以上；（4）法語與德語：法國南特理工大學、薩瓦勃朗峰大學要求英語或法語 DELF B1（文學院 B2），德國馬德堡大學要求英語或德語 B1–B2；（5）大陸地區姊妹校免附外語檢定。"
        ),
    )
  if test in NUU_ENGLISH_MINIMUMS:
    label, minimum = NUU_ENGLISH_MINIMUMS[test]
    passed = language_score >= minimum
    tier_note = "達《國立聯合大學學生赴國外研修留學國語言能力參考標準》英語基準門檻（TOEFL iBT 57 / ITP 457 / IELTS 4.0 / TOEIC 550）"
    if (
        (test == "toefl" and language_score >= 86)
        or (test == "ielts" and language_score >= 6.5)
        or (test == "toefl_itp" and language_score >= 570)
        or (test == "toeic" and language_score >= 850)
    ):
      tier_note = "符合加拿大安大略理工大學（iBT 83–86 / IELTS 6.5）、卡加利大學、美國佛羅里達理工學院 FIT（並達每學期加發 USD 2,000 語言獎學金門檻 iBT 88 / IELTS 6.5）、樹城州立大學 Boise State、霜堡州立大學 FSU 等全部歐美亞英語授課交換與雙聯學位最高門檻"
    elif (
        (test == "toefl" and language_score >= 79)
        or (test == "ielts" and language_score >= 6.0)
        or (test == "toefl_itp" and language_score >= 550)
        or (test == "toeic" and language_score >= 785)
    ):
      tier_note = "達 CEFR B2 門檻，符合美國佛羅里達理工學院 FIT 2+2（iBT 79 / IELTS 6.0）、樹城州立大學 Boise State 2+2、霜堡州立大學 FSU 2+2、南猶他大學 SUU、明尼蘇達州立大學曼卡托分校、德國馬德堡大學、法國南特理工大學及泰國 KMUTT 等歐美亞英語授課學程門檻"
    elif (
        (test == "toefl" and language_score >= 61)
        or (test == "ielts" and language_score >= 5.5)
        or (test == "toefl_itp" and language_score >= 500)
        or (test == "toeic" and language_score >= 600)
    ):
      tier_note = "符合美國明尼蘇達州立大學曼卡托分校（iBT 61 / IELTS 5.5）、南猶他大學 SUU、霜堡州立大學 FSU、韓國仁荷大學、昌原國立大學、馬來西亞拉曼大學 UTAR、越南胡志明市經濟大學 UEH、印尼總統大學、迪波內戈羅大學及日本高專英語授課研習門檻"
    return (
        "pass" if passed else "fail",
        (
            f"{label} {language_score:g} {'符合' if passed else '未達'}國立聯合大學《學生赴國外研修留學國語言能力參考標準》英語基準（最低採計門檻：{label} {minimum:g}；{tier_note}）。"
        ),
    )
  if test == "jlpt":
    level = int(language_score)
    passed = 1 <= level <= 3
    if level in (1, 2):
      tier_note = "符合日本甲南大學（JLPT N2）、國立愛知教育大學（JLPT N2）及全部日本國立高等專門學校（宇部、高知、新居濱、阿南、木更津、明石、小山、釧路高專，要求 N3 以上）最高日語門檻"
    elif level == 3:
      tier_note = "達《國立聯合大學學生赴國外研修留學國語言能力參考標準》日語基準（JLPT N3），符合日本國立高等專門學校（宇部、高知、新居濱、阿南、木更津、明石、小山、釧路高專）交換與暑期研習門檻（甲南大學、愛知教育大學要求 JLPT N2 以上）"
    else:
      tier_note = f"目前為 JLPT N{level}；依《國立聯合大學學生赴國外研修留學國語言能力參考標準》，日語基準為 JLPT N3 以上（甲南大學、愛知教育大學要求 N2 以上；若申請日本高專暑期實驗室研習亦可改以英語 TOEIC 550 / iBT 57 以上申請）"
    return (
        "pass" if passed else "fail",
        f"JLPT N{level} {'符合' if passed else '未達'}國立聯合大學日本姊妹校交換日語檢定基準（{tier_note}）。",
    )
  if test == "topik":
    level = int(language_score)
    passed = 3 <= level <= 6
    if passed:
      tier_note = "符合韓國仁荷大學（Inha University，TOPIK 3 級）與國立昌原大學（Changwon National University，TOPIK 3 級）全部韓國姊妹校韓語交換門檻"
    else:
      tier_note = f"目前為 TOPIK {level} 級；韓國仁荷大學與國立昌原大學韓語授課交換要求 TOPIK 3 級以上（若修讀英語授課課程可改以 TOEIC 550 / TOEFL iBT 71 / IELTS 5.5 申請）"
    return (
        "pass" if passed else "fail",
        f"TOPIK {level} 級{'符合' if passed else '未達'}國立聯合大學韓國姊妹校交換韓語基準（{tier_note}）。",
    )
  return (
      "needs_confirmation",
      f"已填報語言檢定 {language_test}（{language_score:g}）；請對照《國立聯合大學學生赴國外研修留學國語言能力參考標準》與《交換學校一覽表》（TOEFL iBT 57 / ITP 457 / IELTS 4.0 / TOEIC 550 / GEPT 中級複試 / JLPT N2–N3 / TOPIK 3 級 / DELF B1）確認目標姊妹校語言門檻。",
  )
