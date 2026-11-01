from __future__ import annotations

import re

from .university_registry import NPUST, resolve_university

NPUST_OIA_HOME_URL = "https://oia2.npust.edu.tw/zh/"
NPUST_OUTBOUND_EXCHANGE_URL = (
    "https://oia2.npust.edu.tw/zh/cooperation/%e4%ba%a4%e6%8f%9b%e5%ad%b8%e7%94%9f-2/"
)
NPUST_OUTBOUND_EXCHANGE_EN_URL = (
    "https://oia2.npust.edu.tw/en/outbound-student-exchange-program/"
)
NPUST_SISTER_SCHOOLS_URL = "https://oia2.npust.edu.tw/zh/sister-schools/"
NPUST_SISTER_SCHOOLS_EN_URL = "https://oia2.npust.edu.tw/en/sister-schools/"
NPUST_DOUBLE_DEGREE_URL = "https://oia2.npust.edu.tw/en/double-degree-programs/"
NPUST_EXCHANGE_SHARING_2026_URL = "https://oia2.npust.edu.tw/zh/2026/03/02/20260326/"
NPUST_EXCHANGE_SHARING_2023_URL = (
    "https://oia2.npust.edu.tw/zh/2023/02/15/%e3%80%90%e6%b4%bb%e5%8b%95%e8%a8%8a%e6%81%af%e3%80%9120230302%e3%80%8a%e5%ad%b8%e7%94%9f%e8%b5%b4%e5%a4%96%e4%ba%a4%e6%8f%9b%e7%a0%94%e7%bf%92%e7%b6%93%e9%a9%97%e5%88%86%e4%ba%ab%e6%9c%83%e3%80%8b/"
)
NPUST_RMUTI_3PLUS3_URL = (
    "https://oia2.npust.edu.tw/zh/2026/03/24/rmuti%e7%b7%9a%e4%b8%8a%e8%aa%aa%e6%98%8e%e6%9c%83/"
)
NPUST_SCHOLARSHIPS_URL = (
    "https://oia2.npust.edu.tw/zh/about-npust-2/%e7%8d%8e%e5%ad%b8%e9%87%91/"
)
NPUST_XUEHAI_URL = "https://aa.npust.edu.tw/%e5%ad%b8%e6%b5%b7%e5%90%84%e9%a0%85%e8%a8%88%e7%95%ab/"
NPUST_OUTBOUND_GUIDELINES_PDF_URL = (
    "https://oia2.npust.edu.tw/wp-content/uploads/2025/05/04.%E5%9C%8B%E7%AB%8B%E5%B1%8F%E6%9D%B1%E7%A7%91%E6%8A%80%E5%A4%A7%E5%AD%B8%E4%BA%A4%E6%8F%9B%E5%AD%B8%E7%94%9F%E5%87%BA%E5%9C%8B%E8%A8%88%E7%95%AB%E5%AF%A6%E6%96%BD%E8%A6%81%E9%BB%9E_1140410.pdf"
)
NPUST_OVERSEAS_GRANT_PDF_URL = (
    "https://oia2.npust.edu.tw/wp-content/uploads/2024/11/02.%E5%9C%8B%E7%AB%8B%E5%B1%8F%E6%9D%B1%E7%A7%91%E6%8A%80%E5%A4%A7%E5%AD%B8%E5%AD%B8%E7%94%9F%E8%B5%B4%E6%B5%B7%E5%A4%96%E7%A0%94%E7%BF%92%E7%8D%8E%E8%A3%9C%E5%8A%A9%E8%A6%81%E9%BB%9E1130409.pdf"
)
NPUST_LANGUAGE_REWARD_PDF_URL = (
    "https://oia2.npust.edu.tw/wp-content/uploads/2024/11/01.%E5%9C%8B%E7%AB%8B%E5%B1%8F%E6%9D%B1%E7%A7%91%E6%8A%80%E5%A4%A7%E5%AD%B8%E5%AD%B8%E7%94%9F%E5%8F%83%E8%88%87%E5%A4%96%E8%AA%9E%E8%83%BD%E5%8A%9B%E6%AA%A2%E5%AE%9A%E7%8D%8E%E5%8B%B5%E8%BE%A6%E6%B3%951120802.pdf"
)
NPUST_STUDENT_ABROAD_RULES_PDF_URL = (
    "https://oia2.npust.edu.tw/wp-content/uploads/2021/10/08.%E5%9C%8B%E7%AB%8B%E5%B1%8F%E6%9D%B1%E7%A7%91%E6%8A%80%E5%A4%A7%E5%AD%B8%E5%AD%B8%E7%94%9F%E5%87%BA%E5%9C%8B%E6%9C%9F%E9%96%93%E6%9C%89%E9%97%9C%E5%AD%B8%E6%A5%AD%E5%8F%8A%E5%AD%B8%E7%B1%8D%E8%99%95%E7%90%86%E8%BE%A6%E6%B3%95.pdf"
)
NPUST_DUAL_DEGREE_GUIDELINES_PDF_URL = (
    "https://oia2.npust.edu.tw/wp-content/uploads/2021/10/07.%E5%9C%8B%E7%AB%8B%E5%B1%8F%E6%9D%B1%E7%A7%91%E6%8A%80%E5%A4%A7%E5%AD%B8%E8%88%87%E5%9C%8B%E5%A4%96%E5%A4%A7%E5%AD%B8%E8%BE%A6%E7%90%86%E9%9B%99%E8%81%AF%E5%AD%B8%E5%88%B6%E5%AF%A6%E6%96%BD%E8%A6%81%E9%BB%9E.pdf"
)
NPUST_DUAL_DEGREE_FLOWCHART_PDF_URL = (
    "https://oia2.npust.edu.tw/wp-content/uploads/2021/10/%E5%9C%8B%E7%AB%8B%E5%B1%8F%E6%9D%B1%E7%A7%91%E6%8A%80%E5%A4%A7%E5%AD%B8%E8%BE%A6%E7%90%86%E6%B5%B7%E5%A4%96%E9%9B%99%E8%81%AF%E5%AD%B8%E5%88%B6%E6%B5%81%E7%A8%8B%E5%9C%96.pdf"
)
NPUST_XUEHAI_FEIYANG_RULES_PDF_URL = (
    "https://aa.npust.edu.tw/wp-content/uploads/2025/12/%E5%9C%8B%E7%AB%8B%E5%B1%8F%E6%9D%B1%E7%A7%91%E6%8A%80%E5%A4%A7%E5%AD%B8%E3%80%8C%E6%95%99%E8%82%B2%E9%83%A8%E5%AD%B8%E6%B5%B7%E9%A3%9B%E9%A2%BA%E8%A8%88%E7%95%AB%E3%80%8D%E7%94%84%E9%81%B8%E8%BE%A6%E6%B3%95.pdf"
)
NPUST_XUEHAI_FEIYANG_PRINCIPLES_PDF_URL = (
    "https://aa.npust.edu.tw/wp-content/uploads/2025/04/%E6%95%99%E8%82%B2%E9%83%A8%E5%AD%B8%E6%B5%B7%E9%A3%9B%E9%A2%BA%E8%A8%88%E7%95%AB%E6%A0%A1%E5%85%A7%E5%AF%A9%E6%9F%A5%E5%8E%9F%E5%89%87.pdf"
)
NPUST_XUEHAI_XIZHU_RULES_PDF_URL = (
    "https://aa.npust.edu.tw/wp-content/uploads/2025/12/%E5%9C%8B%E7%AB%8B%E5%B1%8F%E6%9D%B1%E7%A7%91%E6%8A%80%E5%A4%A7%E5%AD%B8%E3%80%8C%E6%95%99%E8%82%B2%E9%83%A8%E5%AD%B8%E6%B5%B7%E6%83%9C%E7%8F%A0%E8%A8%88%E7%95%AB%E3%80%8D%E7%94%84%E9%81%B8%E8%BE%A6%E6%B3%95.pdf"
)
NPUST_XUEHAI_ZHUMENG_RULES_PDF_URL = (
    "https://aa.npust.edu.tw/wp-content/uploads/2025/12/%E5%9C%8B%E7%AB%8B%E5%B1%8F%E6%9D%B1%E7%A7%91%E6%8A%80%E5%A4%A7%E5%AD%B8%E3%80%8C%E6%95%99%E8%82%B2%E9%83%A8%E5%AD%B8%E6%B5%B7%E7%AF%89%E5%A4%A2%E8%A8%88%E7%95%AB%E3%80%8D%E7%94%84%E9%81%B8%E8%BE%A6%E6%B3%95.pdf"
)
NPUST_EXCHANGE_SCHOOLS_SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/1tB-W-s1f7f0s-6xK7e-V4pU-A-m_qW4S/edit?usp=sharing"
)

NPUST_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 42.0),
    "ielts": ("IELTS", 4.5),
    "toefl_itp": ("TOEFL ITP/PBT", 450.0),
    "toeic": ("TOEIC", 350.0),
}


def is_npust(school_name: str | None) -> bool:
  school = resolve_university(school_name)
  if school is not None and school.id == NPUST.id:
    return True
  normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
  return normalized in {
      "國立屏東科技大學",
      "屏東科技大學",
      "屏科大",
      "npust",
      "national pingtung university of science and technology",
  }


def _is_graduate(degree_level: str | None) -> bool:
  text = (degree_level or "").strip()
  return any(token in text for token in ("碩", "博", "研究"))


def npust_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
  degree = (degree_level or "").strip()
  year = (current_year or "").strip()
  if not degree:
    return (
        "needs_confirmation",
        (
            "尚未提供目前學制與年級；依《國立屏東科技大學交換學生出國計畫實施要點》第 4 點及《教育部學海飛颺計畫甄選辦法》第 4 條：申請人須為本校大學部二年級以上、碩士班一年級以上或博士班一年級以上之在學學生（轉學生若尚未有本校成績者不得報名；學海系列計畫不含國內及境外在職專班生）。非中華民國國籍之本校學生可參加交換學生甄選，但不得交換至其原屬國家境內之學校。"
        ),
    )
  if any(
      token in degree or token in year
      for token in ("在職專班", "碩專", "emba", "EMBA", "學分班", "選修生", "休學")
  ):
    return (
        "fail",
        (
            f"已填報 {degree}{f'（{year}）' if year else ''}；依《國立屏東科技大學交換學生出國計畫實施要點》及《教育部學海飛颺計畫甄選辦法》第 4 條，在職專班生、休學生或無正式一般生學籍者不得申請出國交換與教育部學海飛颺／惜珠獎助。"
        ),
    )
  is_grad = _is_graduate(degree)
  if not is_grad and year in {"大一", "大一上", "大一下", "一年級", "一年級上學期", "一年級下學期"}:
    return (
        "fail",
        (
            f"已填報 {degree}（{year}）；依《國立屏東科技大學交換學生出國計畫實施要點》第 4 點規定，大學部申請人須為「大學部二年級以上」之在學學生（轉學生若尚未有本校成績者不得報名）。建議於大一期間準備外語檢定並參與《學生參與外語能力檢定獎勵辦法》，於大二起提出交換申請。"
        ),
    )
  grad_note = (
      "（提醒：日本大阪府立大學僅限研究生申請；東北農業大學限大三及碩士二年級以上；上海大學社會學院僅限社工系學生；跨國雙聯學制碩士班於兩校累計修業時間至少須滿 12 個月、博士班至少滿 24 個月）"
      if is_grad
      else "（提醒：日本宮崎大學、帶廣畜產大學、筑波大學、靜岡理工科大學限大二以上且大四除外；東北農業大學限大三及碩二以上；上海大學社會學院僅限社工系；泰國皇家科技大學 RMUTI 3+3 雙邊交換限財務金融國際學士學位學程；跨國雙聯學制學士班於兩校累計修業時間至少須滿 32 個月）"
  )
  return (
      "pass",
      (
          f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合國立屏東科技大學《交換學生出國計畫實施要點》第 4 點（大學部二年級以上／碩博士班一年級以上）及雙聯學制之在學身分規定{grad_note}。"
      ),
  )


def npust_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
  score_min = 70.0
  gpa_min = 2.5
  rank_max = 50.0
  details: list[str] = []
  passes_general = False
  passes_xuehai = False

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
    if class_rank_percent <= 30.0:
      passes_general = True
      passes_xuehai = True
    elif class_rank_percent <= rank_max:
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
            "尚未填寫歷年學業平均、GPA 或班上排名百分比；依國立屏東科技大學國際事務處《交換學生出國計畫實施要點》及教務處《教育部學海飛颺計畫甄選辦法》：（1）報名須檢附本校中／英文歷年成績單正本並註記班上排名（大陸地區甄選採計在校成績 50%、其他地區採計在校成績 30%）；（2）多數海外交換校要求 CGPA 2.5/4.0（約學業平均 70 分）以上（如韓國慶尚國立大學、越南國家農業大學、印尼泗水大學），印尼建國大學 Binus 要求 GPA 2.75 以上，馬來西亞馬來亞大學 UM 要求 CGPA 3.0（學業平均 75 分）以上；（3）申請教育部「學海飛颺」獎學金須前兩學期學業成績達全班前 30% 且操行成績達 80 分以上（校內審查學業成績占 40%）；申請《學生赴海外研習獎補助要點》第一類語言文化研習個人補助須達全班或全所前 20%。"
        ),
    )

  if passes_general:
    tier_notes: list[str] = []
    if (academic_gpa is not None and academic_gpa >= 3.0) or (
        academic_score is not None and academic_score >= 75.0
    ):
      tier_notes.append(
          "已達馬來亞大學（CGPA 3.0／平均 75 分）、印尼建國大學（GPA 2.75）及全部姊妹校最高學業門檻"
      )
    else:
      tier_notes.append(
          "符合多數姊妹校（CGPA 2.5／平均 70 分，如慶尚國立大學、越南國家農業大學、泗水大學）門檻，惟馬來亞大學要求 CGPA 3.0（平均 75 分）以上、建國大學要求 GPA 2.75 以上"
      )
    if passes_xuehai:
      tier_notes.append(
          "且班排名達前 30% 以內，符合教育部《學海飛颺計畫甄選辦法》第 4 條申請資格"
      )
    return (
        "pass",
        f"已填報 {summary}；符合國立屏東科技大學出國交換甄選學業標準（{'；'.join(tier_notes)}）。",
    )

  return (
      "needs_confirmation",
      (
          f"已填報 {summary}；雖《交換學生出國計畫實施要點》校內初審採總分制（大陸地區在校成績 50%、其他地區在校成績 30%），惟多數海外交換學校（如馬來亞大學 CGPA 3.0、建國大學 GPA 2.75、慶尚國立大學／越南國家農業大學／泗水大學 CGPA 2.5 即 70 分）及教育部《學海飛颺計畫》（全班前 30%）設有學業門檻，建議確認目標姊妹校之個別 GPA 要求。"
      ),
  )


def npust_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
  test = (language_test or "").strip().lower()
  if partner_country in {"中國大陸", "中國"} and (not test or language_score is None):
    return (
        "pass",
        (
            "申請赴中國大陸地區交換學校（北京科技大學、東北林業大學、東北農業大學、福建農林大學、上海大學社會學院）為中文授課，免附外語能力檢定證明；依《交換學生出國計畫實施要點》第 7 點，大陸地區甄選標準採計：在校成績 50%、研究／讀書計畫 25%、自傳及其餘表現 25%。"
        ),
    )
  if not test or language_score is None:
    return (
        "needs_confirmation",
        (
            "尚未填寫外語能力檢定成績。依國立屏東科技大學《交換學生出國計畫實施要點》第 7 點（非大陸地區語言成績占 30%）及《教育部學海飛颺計畫甄選辦法》（外語成績占 40%）：（1）英語檢定：教育部學海飛颺最低門檻為新版 TOEIC 350 分或 GEPT 中級初試；泰國孔敬大學与藝術大學要求 TOEIC 500 分；跨國雙聯學制要求 TOEIC 530 / TOEFL ITP 500 / IELTS 5.0；泰國皇家科技大學 RMUTI 要求 CEFR B1（約 TOEIC 550）；印尼泗水大學要求 IELTS 5.0 / TOEFL iBT 61 / PBT 450；越南國家農業大學要求 TOEFL PBT 500；韓國慶尚國立大學要求 TOEIC 700 / TOEFL iBT 71 / IELTS 5.5；馬來亞大學要求 TOEIC 750 或 CEFR B2；泰國朱拉隆功大學、KMUTT、印尼建國大學要求 TOEFL iBT 79 / IELTS 6.0；奧地利茵斯布魯克管理學院 MCI、波蘭華沙生命科學大學、西里西亞科技大學、捷克布拉格生命科學大學要求 CEFR B2（TOEIC 785 / TOEFL iBT 72–80 / IELTS 5.5–6.0）；（2）日語檢定：日本靜岡理工科大學要求 JLPT N3 以上，宮崎大學、帶廣畜產大學、大阪府立大學、明治大學、筑波大學要求 JLPT N2 以上（明治大學法學部要求 N1）；（3）韓語檢定：韓國嘉泉大學要求 TOPIK 2 級以上，慶尚國立大學要求 TOPIK 3 級以上；（4）大陸地區姊妹校免附外語檢定。"
        ),
    )
  if test in NPUST_ENGLISH_MINIMUMS:
    label, minimum = NPUST_ENGLISH_MINIMUMS[test]
    passed = language_score >= minimum
    tier_note = "達教育部《學海飛颺計畫甄選辦法》第 4 條外語基準門檻（新版 TOEIC 350 / CEFR A2）"
    if (
        (test == "toefl" and language_score >= 80)
        or (test == "ielts" and language_score >= 6.0)
        or (test == "toefl_itp" and language_score >= 550)
        or (test == "toeic" and language_score >= 785)
    ):
      tier_note = "達 CEFR B2 高階門檻（學海飛颺外語審查 30–40 分），符合奧地利茵斯布魯克管理學院 MCI、波蘭華沙生命科學大學、西里西亞科技大學、捷克布拉格生命科學大學、泰國朱拉隆功大學、吞武里蒙庫國王科技大學 KMUTT、馬來亞大學、印尼建國大學 Binus 等全部歐亞英語授課交換校與雙聯學位最高門檻"
    elif (
        (test == "toefl" and language_score >= 71)
        or (test == "ielts" and language_score >= 5.5)
        or (test == "toefl_itp" and language_score >= 520)
        or (test == "toeic" and language_score >= 700)
    ):
      tier_note = "符合韓國慶尚國立大學（TOEIC 700 / iBT 71 / IELTS 5.5）、印尼泗水大學、越南國家農業大學、泰國孔敬大學、藝術大學、皇家科技大學 RMUTI 及跨國雙聯學制門檻（馬來亞大學需 TOEIC 750、朱拉隆功／KMUTT／Binus 需 iBT 79 / IELTS 6.0、歐洲姊妹校需 CEFR B2）"
    elif (
        (test == "toefl" and language_score >= 61)
        or (test == "ielts" and language_score >= 5.0)
        or (test == "toefl_itp" and language_score >= 500)
        or (test == "toeic" and language_score >= 530)
    ):
      tier_note = "達 CEFR B1 門檻（學海飛颺外語審查 20 分），符合跨國雙聯學制（TOEIC 530 / ITP 500 / IELTS 5.0）、印尼泗水大學（IELTS 5.0 / iBT 61）、越南國家農業大學（PBT 500）、泰國孔敬大學與藝術大學（TOEIC 500）及泰國皇家科技大學 RMUTI（CEFR B1）門檻"
    elif test == "toeic" and language_score >= 500:
      tier_note = "符合泰國孔敬大學（Khon Kaen University）與泰國藝術大學（Silpakorn University）之 TOEIC 500 分交換門檻，以及教育部學海飛颺計畫申請基準"
    return (
        "pass" if passed else "fail",
        (
            f"{label} {language_score:g} {'符合' if passed else '未達'}國立屏東科技大學出國交換與學海飛颺外語檢定採計基準（最低採計門檻：{label} {minimum:g}；{tier_note}）。"
        ),
    )
  if test == "jlpt":
    level = int(language_score)
    passed = 1 <= level <= 5
    if level == 1:
      tier_note = "達學海飛颺日語審查滿分（40 分），符合日本明治大學（含法學部 N1）、筑波大學、大阪府立大學、宮崎大學、帶廣畜產大學、靜岡理工科大學等全部日本交換校最高門檻，並可申請屏科大外語檢定獎勵金 3,000 元"
    elif level == 2:
      tier_note = "達學海飛颺日語審查 35 分，符合日本宮崎大學、帶廣畜產大學、大阪府立大學、筑波大學、明治大學（法學部除外）及靜岡理工科大學之 JLPT N2 交換門檻，並可申請屏科大外語檢定獎勵金 1,500 元"
    elif level == 3:
      tier_note = "達學海飛颺日語審查 30 分，符合日本靜岡理工科大學（JLPT N3）交換門檻（宮崎大學、帶廣畜產大學、大阪府立大學、明治大學、筑波大學要求 JLPT N2 以上）"
    else:
      tier_note = f"達教育部學海飛颺計畫日語檢定審查計分基準（N{level} 採計 {20 if level == 4 else 10} 分），惟日本交換姊妹校最低要求靜岡理工科大學 JLPT N3、其餘日本姊妹校要求 JLPT N2 以上"
    return (
        "pass" if passed else "fail",
        f"JLPT N{level} {'符合' if passed else '未達'}國立屏東科技大學日本姊妹校交換與學海飛颺日語檢定基準（{tier_note}）。",
    )
  if test == "topik":
    level = int(language_score)
    passed = 1 <= level <= 6
    if level >= 3:
      tier_note = "符合韓國慶尚國立大學（TOPIK 3 級）與嘉泉大學（TOPIK 2 級）全部韓國交換姊妹校韓語門檻"
    elif level == 2:
      tier_note = "符合韓國嘉泉大學（Gachon University，TOPIK 2 級）交換門檻（慶尚國立大學要求 TOPIK 3 級或 TOEIC 700 / TOEFL iBT 71 / IELTS 5.5）"
    else:
      tier_note = "已具基礎韓語檢定成績（可申請屏科大外語能力檢定獎勵），惟韓國嘉泉大學要求 TOPIK 2 級以上、慶尚國立大學要求 TOPIK 3 級以上（或改以英語檢定申請慶尚國立大學）"
    return (
        "pass" if passed else "fail",
        f"TOPIK {level} 級{'符合' if passed else '未達'}國立屏東科技大學韓國姊妹校交換外語基準（{tier_note}）。",
    )
  return (
      "needs_confirmation",
      f"已填報語言檢定 {language_test}（{language_score:g}）；請對照國立屏東科技大學國際事務處《姊妹校申請資格一覽表》與《教育部學海飛颺計畫校內審查原則》（CEFR A2–C2、TOEIC、TOEFL、IELTS、JLPT、TOPIK）確認目標姊妹校語言門檻。",
  )
