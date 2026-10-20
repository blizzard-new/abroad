from __future__ import annotations

import re

from .university_registry import NTOU, resolve_university

NTOU_OIA_HUB_URL = "https://oia.ntou.edu.tw/"
NTOU_OUTBOUND_OVERVIEW_URL = "https://oia.ntou.edu.tw/p/412-1022-6958.php?Lang=zh-tw"
NTOU_EXCHANGE_PLAN_URL = "https://oia.ntou.edu.tw/p/412-1022-10817.php?Lang=zh-tw"
NTOU_DUAL_DEGREE_URL = "https://oia.ntou.edu.tw/p/412-1022-8671.php?Lang=zh-tw"
NTOU_DUAL_DEGREE_XLSX_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/973/663723575.xlsx"
NTOU_XUEHAI_OVERVIEW_URL = "https://oia.ntou.edu.tw/p/412-1022-10818.php?Lang=zh-tw"
NTOU_XUEHAI_FEIYANG_URL = "https://oia.ntou.edu.tw/p/412-1022-10819.php?Lang=zh-tw"
NTOU_XUEHAI_XIZHU_URL = "https://oia.ntou.edu.tw/p/412-1022-10820.php?Lang=zh-tw"
NTOU_XUEHAI_ZHUMENG_URL = "https://oia.ntou.edu.tw/p/412-1022-10821.php?Lang=zh-tw"
NTOU_BROCHURE_2027_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/1029/779655790.pdf"
NTOU_GUIDELINES_LANG_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/1029/854516693.pdf"
NTOU_ENFORCEMENT_RULES_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/1029/777268759.pdf"
NTOU_XUEHAI_RULES_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/1029/830669231.pdf"
NTOU_MOE_XUEHAI_115_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/1029/380374043.pdf"
NTOU_APP_CHECKLIST_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/1029/892749589.pdf"
NTOU_AUTOBIO_EX_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/1029/764741202.pdf"
NTOU_STUDY_PLAN_EX_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/1029/288285085.pdf"
NTOU_BUDGET_EX_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/1029/814897101.pdf"
NTOU_PRE_DEPARTURE_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/1029/705516691.pdf"
NTOU_REIMBURSEMENT_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/1029/765889941.pdf"
NTOU_SOP_EXCHANGE_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/972/484468333.pdf"
NTOU_SOP_DUAL_URL = "https://oia.ntou.edu.tw/var/file/22/1022/img/972/757675578.pdf"
NTOU_MAINLAND_115_2_URL = "https://oia.ntou.edu.tw/p/406-1022-70577,r11.php?Lang=zh-tw"
NTOU_SISTER_SCHOOLS_URL = "https://oia.ntou.edu.tw/p/412-1022-6904.php?Lang=zh-tw"
NTOU_EXP_SHARING_URL = "https://oia.ntou.edu.tw/p/404-1022-86719.php?Lang=zh-tw"

NTOU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 60.0),
    "ielts": ("IELTS", 5.0),
    "toeic": ("TOEIC", 600.0),
}


def is_ntou(school_name: str | None) -> bool:
  school = resolve_university(school_name)
  if school is not None and school.id == NTOU.id:
    return True
  normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
  return normalized in {
      "國立臺灣海洋大學",
      "國立台灣海洋大學",
      "臺灣海洋大學",
      "台灣海洋大學",
      "海洋大學",
      "海大",
      "ntou",
      "national taiwan ocean university",
  }


def _is_graduate(degree_level: str | None) -> bool:
  text = (degree_level or "").strip()
  return any(token in text for token in ("碩", "博", "研究"))


def ntou_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
  degree = (degree_level or "").strip()
  year = (current_year or "").strip()
  if not degree:
    return (
        "needs_confirmation",
        (
            "尚未提供目前學制與年級；《國立臺灣海洋大學學生赴國外研修要點》第3點規定：申請期間與赴國外研修期間皆應為本校註冊在學生，且非為大一上學期之新生或當學期畢業之學生（大學部須經系所主管與學院同意；碩博士生須經指導教授、系所主管與學院同意）。"
        ),
    )
  if any(token in degree for token in ("學分班", "休學")):
    return (
        "fail",
        f"已填報 {degree}；依《國立臺灣海洋大學學生赴國外研修要點》第3點規定，申請期間與赴國外研修期間皆應為本校註冊在學生（不得休學或畢業）。",
    )
  if "在職" in degree or "延畢" in year:
    return (
        "needs_confirmation",
        (
            f"已填報 {degree}{f'（{year}）' if year else ''}；依《國立臺灣海洋大學學生赴國外研修要點》第3點規定，申請期間與赴國外研修期間皆應為本校註冊在學生且非當學期畢業之學生，在職專班或延修生請向國際事務處及志願姊妹校確認是否受理全職交換生提名。"
        ),
    )
  is_grad = _is_graduate(degree)
  if not is_grad and year in {"大一上"}:
    return (
        "fail",
        (
            f"已填報 {degree}（{year}）；依《國立臺灣海洋大學學生赴國外研修要點》第3點規定，申請人不得為大一上學期之新生。"
        ),
    )
  return (
      "pass",
      f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合國立臺灣海洋大學出國交換學生學制與年級規定（申請期間與赴國外研修期間皆須為海大註冊在學生，且非當學期畢業之學生）。",
  )


def ntou_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
  is_grad = _is_graduate(degree_level)
  min_score = 70.0 if is_grad else 60.0
  min_gpa = 3.0 if is_grad else 2.5
  details: list[str] = []
  score_ok = False
  score_borderline = False

  if academic_score is not None:
    details.append(f"前一學期／歷年學業平均 {academic_score:g} 分")
    if academic_score >= min_score:
      score_ok = True
  if academic_gpa is not None:
    details.append(f"GPA {academic_gpa:g}")
    if academic_gpa >= min_gpa:
      score_ok = True
    elif academic_gpa >= 2.0:
      score_borderline = True
  if class_rank_percent is not None:
    details.append(f"班排前 {class_rank_percent:g}%")

  summary = "、".join(details)
  if academic_score is None and academic_gpa is None:
    return (
        "needs_confirmation",
        (
            f"尚未填寫學業平均成績；《國立臺灣海洋大學學生赴國外研修施行細則》第2點規定：申請之前一學期學業平均須達及格以上（{'研究所 70 分' if is_grad else '大學部 60 分'}），且須符合交換學校訂定之 GPA 標準。國外姊妹校甄選按「在校成績 30%＋外語能力 30%＋書面及面試表現 40%」計分，大陸地區姊妹校按「在校成績 45%＋研修計畫及其他輔助文件 55%」計分。"
        ),
    )

  if score_ok:
    return (
        "pass",
        (
            f"已填報 {summary}；符合國立臺灣海洋大學《學生赴國外研修施行細則》第2點「申請之前一學期學業平均達及格以上（{'研究所 70 分' if is_grad else '大學部 60 分'}）」之門檻（如志願交換學校另設有 GPA 2.5 / 3.0 / 3.5 等標準，請同時確認符合該校規定）。"
        ),
    )

  if score_borderline:
    return (
        "needs_confirmation",
        (
            f"已填報 {summary}；請確認申請之前一學期百分制學業平均是否達 {'70 分（研究所及格標準）' if is_grad else '60 分（大學部及格標準）'} 以上，並符合志願姊妹校 GPA 門檻。"
        ),
    )

  return (
      "fail",
      (
          f"已填報 {summary}；未達國立臺灣海洋大學《學生赴國外研修施行細則》第2點「申請之前一學期學業平均須達及格以上（{'研究所 70 分' if is_grad else '大學部 60 分'}）」之規定。"
      ),
  )


def ntou_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
  test = (language_test or "").strip().lower()
  if partner_country == "中國大陸" and (not test or language_score is None):
    return (
        "pass",
        (
            "申請赴中國大陸地區姊妹校交換免提送外國語言能力證明（依《國立臺灣海洋大學學生赴國外研修要點》附件一備註規定辦理）。"
        ),
    )
  if not test or language_score is None:
    return (
        "needs_confirmation",
        (
            "尚未填寫外語檢定成績。依《國立臺灣海洋大學學生赴國外研修要點》附件一「留學國語文能力證明」標準表規定：英文須達 TOEFL iBT 60 / IELTS 5.0 / TOEIC 600 / GEPT 高級複試以上；日文須達 JLPT N3 以上（部分日本姊妹校要求 N2）；韓文須達 TOPIK 3 級以上；法文須達 DELF B1 以上（里爾、卡昂法語組要求 B2）；德文須達 ZDaF 初級以上（THWS 德語組要求 B2）；西文須達 DELE 初級以上；赴大陸地區得免提送外語證明。"
        ),
    )
  if test in NTOU_ENGLISH_MINIMUMS:
    label, minimum = NTOU_ENGLISH_MINIMUMS[test]
    passed = language_score >= minimum
    adv_note = "符合海大校內英文基本門檻（TOEFL iBT 60 / IELTS 5.0 / TOEIC 600）"
    if (test == "toefl" and language_score >= 80) or (test == "ielts" and language_score >= 6.5) or (test == "toeic" and language_score >= 800):
      adv_note = "符合海大英文門檻及北海道大學 HUSTEP、神戶大學、九州大學、馬來亞大學、克拉克森大學、紐澤西理工學院、紐約州立大學海運學院、辛辛那提大學雙聯等進階英語門檻"
    elif (test == "toefl" and language_score >= 72) or (test == "ielts" and language_score >= 5.5) or (test == "toeic" and language_score >= 730):
      adv_note = "符合海大英文門檻及芝浦工業大學、神戶大學、長崎大學、琉球大學、德國 THWS 等 CEFR B2 英語門檻"
    return (
        "pass" if passed else "fail",
        (
            f"{label} {language_score:g} {'符合' if passed else '未達'}國立臺灣海洋大學「留學國語文能力證明」英文標準（{label} {minimum:g}；{adv_note}）。"
        ),
    )
  if test == "jlpt":
    level = int(language_score)
    passed = level in (1, 2, 3)
    tier_note = (
        "符合北海道大學 SAS、神奈川大學、芝浦工業大學、高知大學、九州大學、長崎大學、琉球大學等 N2 日本姊妹校門檻"
        if level in (1, 2)
        else (
            "符合海大附表一日文基本門檻（JLPT N3）及東京海洋大學、信州大學、靜岡大學、三重大學、長崎大學水產/工學、琉球大學 G Program 等 N3 日本姊妹校門檻（部分日本校要求 N2）"
            if level == 3
            else "未達海大《留學國語文能力證明》JLPT N3(含)以上之日文最低標準"
        )
    )
    return (
        "pass" if passed else "fail",
        f"JLPT N{level} {'符合' if passed else '未達'}國立臺灣海洋大學日本姊妹校日語檢定標準（{tier_note}）。",
    )
  if test == "topik":
    level = int(language_score)
    passed = 3 <= level <= 6
    return (
        "pass" if passed else "fail",
        (
            f"TOPIK {level} 級 {'符合' if passed else '未達'}國立臺灣海洋大學《留學國語文能力證明》韓文 TOPIK 3 級(含)以上標準（適用於中央大學、韓國海洋大學、釜慶大學、全南大學、仁川大學等韓國姊妹校）。"
        ),
    )
  return (
      "needs_confirmation",
      (
          f"已填寫 {language_test} {language_score:g}；請對照《國立臺灣海洋大學學生赴國外研修要點》附件一「留學國語文能力證明」標準表（{NTOU_GUIDELINES_LANG_URL}）及當期交換生甄選簡章確認是否符合志願姊妹校規定。"
      ),
  )
