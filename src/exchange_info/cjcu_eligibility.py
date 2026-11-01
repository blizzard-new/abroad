from __future__ import annotations

import re

from .university_registry import CJCU, resolve_university

CJCU_OIA_HOME_URL = "https://dweb.cjcu.edu.tw/intl"
CJCU_OIA_HOME_EN_URL = "https://dweb.cjcu.edu.tw/intl?lang=en"
CJCU_SISTER_SCHOOLS_URL = "https://dweb.cjcu.edu.tw/intl/article/2577"
CJCU_SISTER_SCHOOLS_EN_URL = "https://dweb.cjcu.edu.tw/intl/article/2577?lang=en"
CJCU_EXCHANGE_RULES_URL = "https://dweb.cjcu.edu.tw/intl/article/1552"
CJCU_EXCHANGE_BROCHURE_URL = "https://dweb.cjcu.edu.tw/intl/article/1583"
CJCU_EXCHANGE_SCHOOLS_URL = "https://dweb.cjcu.edu.tw/intl/files/1370"
CJCU_EXCHANGE_RESULTS_URL = "https://dweb.cjcu.edu.tw/intl/article/4549"
CJCU_SCHOLARSHIPS_URL = "https://dweb.cjcu.edu.tw/intl/article/1587"
CJCU_PREDEPARTURE_URL = "https://dweb.cjcu.edu.tw/intl/article/1584"
CJCU_ARRIVAL_URL = "https://dweb.cjcu.edu.tw/intl/article/1585"
CJCU_RETURN_URL = "https://dweb.cjcu.edu.tw/intl/article/1586"
CJCU_EXPERIENCES_URL = "https://dweb.cjcu.edu.tw/intl/article/1613"
CJCU_DUAL_DEGREE_URL = "https://dweb.cjcu.edu.tw/intl/article/8240"
CJCU_DUAL_DEGREE_EN_URL = "https://dweb.cjcu.edu.tw/intl/article/8240?lang=en"
CJCU_SHORT_TERM_URL = "https://dweb.cjcu.edu.tw/intl/article/4379"
CJCU_REGULATIONS_URL = "https://dweb.cjcu.edu.tw/intl/files/350"
CJCU_DOWNLOADS_URL = "https://dweb.cjcu.edu.tw/intl/files/370"
CJCU_HANDBOOK_URL = "https://dweb.cjcu.edu.tw/intl/files/1742"
CJCU_BROCHURE_115_PDF_URL = (
    "https://dweb.cjcu.edu.tw/ShepherdFiles/B2600/File/20260923181924667.pdf"
)
CJCU_OUTBOUND_RULES_PDF_URL = (
    "https://dweb.cjcu.edu.tw/ShepherdFiles/B2600/File/20240402101918107.pdf"
)
CJCU_SCHOLARSHIP_RULES_PDF_URL = (
    "https://dweb.cjcu.edu.tw/ShepherdFiles/B2600/File/20230818094122129.pdf"
)
CJCU_SCHOLARSHIP_BROCHURE_PDF_URL = (
    "https://dweb.cjcu.edu.tw/ShepherdFiles/B2600/File/2026011316184515.pdf"
)
CJCU_MOE_XUEHAI_RULES_PDF_URL = (
    "https://dweb.cjcu.edu.tw/ShepherdFiles/B2600/File/20240112171307159.pdf"
)
CJCU_SHORT_TERM_RULES_PDF_URL = (
    "https://dweb.cjcu.edu.tw/ShepherdFiles/B2600/File/20240321154041506.pdf"
)
CJCU_SHORT_TERM_CALL_PDF_URL = (
    "https://dweb.cjcu.edu.tw/ShepherdFiles/B2600/File/20260116091118684.pdf"
)
CJCU_ADMIN_CONTRACT_PDF_URL = (
    "https://dweb.cjcu.edu.tw/ShepherdFiles/B2600/File/20260305143710725.pdf"
)
CJCU_PREDEPARTURE_CHECKLIST_PDF_URL = (
    "https://dweb.cjcu.edu.tw/ShepherdFiles/B2600/File/20260629094936848.pdf"
)
CJCU_STATISTICS_PDF_URL = (
    "https://dweb.cjcu.edu.tw/ShepherdFiles/B2600/File/20250103095903136.pdf"
)

CJCU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 57.0),
    "ielts": ("IELTS", 5.0),
    "toefl_itp": ("TOEFL ITP/PBT", 500.0),
    "toeic": ("TOEIC", 550.0),
    "duolingo": ("Duolingo English Test", 90.0),
}


def is_cjcu(school_name: str | None) -> bool:
  school = resolve_university(school_name)
  if school is not None and school.id == CJCU.id:
    return True
  normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
  return normalized in {
      "長榮大學",
      "長大",
      "cjcu",
      "chang jung christian university",
  }


def _is_graduate(degree_level: str | None) -> bool:
  text = (degree_level or "").strip()
  return any(token in text for token in ("碩", "博", "研究"))


def cjcu_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
  degree = (degree_level or "").strip()
  year = (current_year or "").strip()
  if not degree:
    return (
        "needs_confirmation",
        (
            "尚未提供目前學制與年級；依《長榮大學赴外研修生作業要點》（113年3月7日行政會議修正通過）第 3 點及《115學年度校級國際交換生甄選簡章》第 2 點：申請人須於長榮大學修業滿一學年（含）以上、具正式學籍且於甄選與出國期間皆具備本校在學學生身分（雙聯學制學生另依各院系雙聯協議辦理）。申請人如為境外生，不得申請交換回原國籍國家研修。"
        ),
    )
  if any(
      token in degree or token in year
      for token in ("在職專班", "碩專", "emba", "EMBA", "學分班", "選修生", "休學")
  ):
    return (
        "fail",
        (
            f"已填報 {degree}{f'（{year}）' if year else ''}；依《長榮大學赴外研修生作業要點》第 4 點及《學生赴海外交換研修獎助金申請簡章》第 3 點，休學、不具正式一般生學籍者不得參加出國交換，且國內及境外在職專班生不符合教育部《學海飛颺／學海惜珠》獎助學金申請資格。"
        ),
    )
  is_grad = _is_graduate(degree)
  if not is_grad and year in {"大一", "大一上", "大一下", "一年級", "一年級上學期", "一年級下學期"}:
    return (
        "fail",
        (
            f"已填報 {degree}（{year}）；依《長榮大學赴外研修生作業要點》第 3 點及《115學年度校級國際交換生甄選簡章》第 2 點規定，校級交換生申請時須於長榮大學「修業滿一學年（含）以上」（即大學部二年級以上，惟跨國雙聯學制及《短期交流補助作業要點》不在此列）。建議大一同學先參與海外短期交流計畫（每人最高補助 40,000 元）並修讀外語課程，於大二起提出校級交換申請。"
        ),
    )
  grad_note = (
      "（提醒：美國聖道大學 UIW、德國北方商學院 NBS 一學期組及韓國韓東國際大學僅限大學部學生申請；人文社會學院翻譯學系碩士班可申請澳洲墨爾本皇家理工大學 RMIT 雙聯學制）"
      if is_grad
      else "（提醒：美國聖道大學 UIW、德國北方商學院 NBS、韓國韓東國際大學及全校 75 個校級交換志願均開放大學部申請；大四生須確保出國交換期間全程保有長榮大學在學學生身分；管理學院、人文社會學院、資訊暨設計學院另有瑞士 BHMS／英國 RGU、法國雷恩商學院 RSB、日本函館大學、聖學院大學、澳洲 RMIT、西雪梨大學 WSU、美國中田納西州立大學 MTSU 雙聯學制）"
  )
  return (
      "pass",
      (
          f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合長榮大學《赴外研修生作業要點》第 3 點（於長榮大學修業滿一學年以上且具正式學籍）之在學身分規定{grad_note}。"
      ),
  )


def cjcu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
  score_min = 70.0
  gpa_min = 2.2
  details: list[str] = []
  passes_general = False
  passes_xuehai = False
  passes_cjcu_grant = False

  if academic_score is not None:
    details.append(f"學業平均 {academic_score:g} 分")
    if academic_score >= score_min:
      passes_general = True
      passes_cjcu_grant = True
    elif academic_score >= 60.0:
      passes_cjcu_grant = True
    if academic_score >= 75.0:
      passes_xuehai = True
  if academic_gpa is not None:
    details.append(f"GPA {academic_gpa:g}")
    if academic_gpa >= 2.5:
      passes_general = True
      passes_cjcu_grant = True
    elif academic_gpa >= gpa_min:
      passes_cjcu_grant = True
    if academic_gpa >= 3.0:
      passes_xuehai = True
  if class_rank_percent is not None:
    details.append(f"班排名百分比前 {class_rank_percent:g}%")
    if class_rank_percent <= 25.0:
      passes_general = True
      passes_xuehai = True
      passes_cjcu_grant = True
    elif class_rank_percent <= 50.0:
      passes_general = True
      passes_cjcu_grant = True

  summary = "、".join(details)
  if (
      academic_score is None
      and academic_gpa is None
      and class_rank_percent is None
  ):
    return (
        "needs_confirmation",
        (
            "尚未填寫前一學年度學業平均成績、GPA 或班排名百分比；依長榮大學《115學年度校級國際交換生甄選簡章》第 2 點及《學生赴海外交換研修獎助金申請簡章》第 3 點：（1）校級交換生申請門檻為「前一學年度學業平均成績達 70 分（含）以上」（甄選書面審查 60% 中：前一學年度學業成績占 10%、前一學年度操行成績占 10%）；（2）個別姊妹校另設 GPA 門檻：印度 Marwadi University 要求 GPA 2.2，日本大阪女學院大學、近畿大學、創價大學及越南太原科學大學要求 GPA 2.5，印度 Chandigarh University 要求 GPA 2.6，韓國漢陽女子大學要求 GPA 2.7，印尼貝特拉基督教大學要求 GPA 2.75，菲律賓馬尼拉雅典耀大學要求 GPA 2.8，波蘭 VIZJA 大學、韓國韓東國際大學、印尼萬隆天主教帕拉揚安大學及越南阮必成大學要求 GPA 3.0；（3）申請教育部《學海飛颺／學海惜珠》獎學金須前一學年學業平均 75 分（含）以上或全班前 25%；申請《長榮大學推展學生國際學術交流獎補助金》須前一學年度學業平均及格或全班前 50%。"
        ),
    )

  if passes_general:
    tier_notes: list[str] = []
    if (academic_gpa is not None and academic_gpa >= 3.0) or (
        academic_score is not None and academic_score >= 75.0
    ):
      tier_notes.append(
          "已達波蘭 VIZJA 大學、韓國韓東國際大學、印尼萬隆天主教帕拉揚安大學、越南阮必成大學（GPA 3.0）及菲律賓馬尼拉雅典耀大學（GPA 2.8）等全部姊妹校最高 GPA 門檻"
      )
    else:
      tier_notes.append(
          "符合長榮大學校級交換（前一學年度平均 70 分以上）與多數姊妹校（GPA 2.5–2.75，如日本大阪女學院大學、近畿大學、創價大學、韓國漢陽女子大學、印尼貝特拉基督教大學）門檻，惟波蘭 VIZJA 大學、韓國韓東國際大學、印尼萬隆天主教帕拉揚安大學與越南阮必成大學要求 GPA 3.0 以上"
      )
    if passes_xuehai:
      tier_notes.append(
          "同時符合教育部《學海飛颺／學海惜珠》獎學金（前一學年平均 75 分以上或班排前 25%）與《長榮大學推展學生國際學術交流獎補助金》申請資格"
      )
    elif passes_cjcu_grant:
      tier_notes.append(
          "符合《長榮大學推展學生國際學術交流獎補助金》（前一學年度平均及格或班排前 50%）申請資格（教育部學海飛颺／惜珠需平均 75 分以上或班排前 25%）"
      )
    return (
        "pass",
        f"已填報 {summary}；符合長榮大學校級國際交換生甄選學業標準（{'；'.join(tier_notes)}）。",
    )

  return (
      "fail" if (academic_score is not None and academic_score < 70.0) else "needs_confirmation",
      (
          f"已填報 {summary}；依《115學年度校級國際交換生甄選簡章》第 2 點規定，校級交換生申請人「前一學年度學業平均成績須達 70 分（含）以上」，且教育部《學海飛颺／學海惜珠》要求前一學年平均 75 分以上或班排前 25%，建議提升學業成績或洽詢各院系雙聯學制與短期交流方案。"
      ),
  )


def cjcu_language_check(
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
            "申請赴中國大陸地區交換學校（東華大學、西南財經大學、南通大學、上海體育大學等）屬校內甄選「中文組」（中文簡報與面試審查 40%＋書面審查 60%），免附外語能力檢定證明，且依《115學年度校級國際交換生甄選簡章》第 8 點規定，「僅填寫中國或日語組志願」之申請人免選修語文教育中心開設之「交換生英語加強課程」。"
        ),
    )
  if not test or language_score is None:
    return (
        "needs_confirmation",
        (
            "尚未填寫外語能力檢定成績。依長榮大學《115學年度校級國際交換生甄選簡章》第 7 點（面試 40%＋書面審查 60%，其中語文證明占 10%）及附錄一各校門檻：（1）英語組／英韓組：加拿大聖保羅大學要求 TOEFL iBT 86 / IELTS 6.5 / Duolingo 120；美國聖道大學 UIW 要求 TOEFL iBT 79 / IELTS 6.0 / TOEIC 650；奧地利約翰克卜勒林茲大學 JKU、西班牙武康大學 UCAM、義大利沙列諾大學、德國北方商學院 NBS、波蘭 VIZJA 大學要求 TOEFL iBT 79 / IELTS 5.5 / TOEIC 785（CEFR B2）；韓國翰林大學、越南蓮花大學要求 TOEFL iBT 71 / PBT 510 / IELTS 5.5 / TOEIC 785；韓國崇實大學建議 TOEFL iBT 70 / IELTS 5.0 / TOEIC 750；日本大阪女學院大學要求 TOEIC 675；日本秋田大學 AUGP/AUSF 要求 TOEFL iBT 57 / IELTS 5.0 / TOEIC 670；日本近畿大學要求 TOEFL iBT 61 / IELTS 6.0；印尼貝特拉基督教大學要求 TOEFL iBT 61 / PBT 500 / IELTS 6.0 / TOEIC 575；印尼薩蒂亞瓦卡納基督教大學要求 TOEFL PBT 500 / IELTS 5.5 / Duolingo 90；捷克 UHK、泰國、印度、菲律賓、馬來西亞、越南等多數姊妹校建議達 CEFR B1（含）以上；（2）日語組：日本大阪國際大學與神戶學院大學要求 JLPT N4 以上；武藏野大學、櫻美林大學、神戶國際大學、鎮西學院大學（免住宿費）、高崎經濟大學要求 JLPT N3 以上；長野大學、拓殖大學、鈴鹿大學、福岡女學院大學、熊本大學、沖繩基督教學院大學、秋田大學、札幌大學、近畿大學、創價大學（免住宿費）、東北學院大學、共愛學園前橋國際大學、中村學園大學、多摩大學、岐阜市立女子短期大學、山梨學院大學要求 JLPT N2 以上；（3）韓語檢定與二外修課證明：韓世大學、韓信大學（免住宿費）要求 TOPIK 2 級以上，東新、啟明、白石、聖公會、漢陽女子大學修讀韓語授課需 TOPIK 3 級以上；且志願含「奧地利、西班牙、法國、德國、韓國」者，報名時必須繳交二年內曾修讀相關語言課程之證明，錄取後（日語組與中國地區除外）須修讀通過語文教育中心「交換生英語加強課程」。"
        ),
    )
  if test in CJCU_ENGLISH_MINIMUMS:
    label, minimum = CJCU_ENGLISH_MINIMUMS[test]
    passed = language_score >= minimum
    tier_note = "達長榮大學英語授課交換校基礎門檻（CEFR B1 / 秋田大學 AUGP・印尼貝特拉・薩蒂亞瓦卡納門檻）"
    if (
        (test == "toefl" and language_score >= 86)
        or (test == "ielts" and language_score >= 6.5)
        or (test == "duolingo" and language_score >= 120)
    ):
      tier_note = "達加拿大聖保羅大學（TOEFL iBT 86 / IELTS 6.5 / Duolingo 120）、澳洲墨爾本皇家理工大學 RMIT 與西雪梨大學 WSU 雙聯學制（IELTS 6.5）及全部歐美亞英語交換校最高語言門檻"
    elif (
        (test == "toefl" and language_score >= 79)
        or (test == "ielts" and language_score >= 6.0)
        or (test == "toefl_itp" and language_score >= 550)
        or (test == "toeic" and language_score >= 785)
    ):
      tier_note = "達 CEFR B2 高階門檻，符合美國聖道大學 UIW（iBT 79 / IELTS 6.0 / TOEIC 650）、奧地利約翰克卜勒林茲大學 JKU、西班牙武康大學 UCAM、義大利沙列諾大學、法國旺代天主教大學 ICES、德國北方商學院 NBS、波蘭 VIZJA 大學、韓國翰林大學、越南蓮花大學、日本創價大學英語授課及瑞士 BHMS／英國 RGU、法國雷恩商學院 RSB 雙聯學制門檻（加拿大聖保羅大學需 iBT 86 / IELTS 6.5 / Duolingo 120）"
    elif (
        (test == "toefl" and language_score >= 70)
        or (test == "ielts" and language_score >= 5.5)
        or (test == "toefl_itp" and language_score >= 510)
        or (test == "toeic" and language_score >= 675)
        or (test == "duolingo" and language_score >= 100)
    ):
      tier_note = "符合韓國崇實大學（iBT 70 / IELTS 5.0 / TOEIC 750）、美國聖道大學（TOEIC 650）、日本大阪女學院大學（TOEIC 675）、日本秋田大學 AUGP/AUSF（TOEIC 670）、印尼薩蒂亞瓦卡納基督教大學（PBT 500 / IELTS 5.5 / Duolingo 90）及捷克 UHK、泰國、印度、菲律賓、印尼、馬來西亞、越南等 CEFR B1 交換校門檻（奧地利 JKU、西班牙 UCAM、義大利沙列諾、德國 NBS、韓國翰林、越南蓮花需 TOEIC 785 / iBT 71–79 / IELTS 5.5）"
    return (
        "pass" if passed else "fail",
        (
            f"{label} {language_score:g} {'符合' if passed else '未達'}長榮大學出國交換與雙聯學制英語檢定採計基準（最低採計門檻：{label} {minimum:g}；{tier_note}；提醒：申請奧地利、西班牙、法國、德國、韓國志願須另附二年內曾修讀相關語言課程之證明，且錄取後須修讀通過語文教育中心「交換生英語加強課程」）。"
        ),
    )
  if test == "jlpt":
    level = int(language_score)
    passed = 1 <= level <= 4
    if level in {1, 2}:
      tier_note = f"JLPT N{level} 符合日本熊本大學、長野大學、拓殖大學、鈴鹿大學、福岡女學院大學、沖繩基督教學院大學、秋田大學（AUAJ）、札幌大學、近畿大學、創價大學（免住宿費）、東北學院大學、共愛學園前橋國際大學、中村學園大學、多摩大學、岐阜市立女子短期大學、山梨學院大學及應日系雙聯學制（函館大學、聖學院大學）全部日本姊妹校最高門檻"
    elif level == 3:
      tier_note = "JLPT N3 符合日本武藏野大學、櫻美林大學、神戶國際大學、鎮西學院大學（免住宿費）、高崎經濟大學、秋田大學（AUGP/AUSF）、大阪國際大學及神戶學院大學交換門檻（熊本大學、拓殖大學、創價大學、近畿大學、東北學院大學等要求 JLPT N2 以上）"
    elif level == 4:
      tier_note = "JLPT N4 符合日本大阪國際大學與神戶學院大學之日檢門檻（武藏野、櫻美林、鎮西學院、高崎經濟大學要求 N3 以上，熊本、拓殖、創價、近畿等校要求 N2 以上）"
    else:
      tier_note = "長榮大學日本交換姊妹校最低要求為 JLPT N4（大阪國際大學、神戶學院大學）、N3 或 N2 以上"
    return (
        "pass" if passed else "fail",
        f"JLPT N{level} {'符合' if passed else '未達'}長榮大學日本姊妹校交換與雙聯學制日語檢定基準（{tier_note}；僅填寫日語組志願者免修交換生英語加強課程，惟錄取後須每週參與應日系日文口語練習活動）。",
    )
  if test == "topik":
    level = int(language_score)
    passed = 1 <= level <= 6
    if level >= 4:
      tier_note = "符合韓國崇實大學（TOPIK 4 級修讀韓語授課）、東新大學、啟明大學、白石大學、聖公會大學、漢陽女子大學（TOPIK 3 級）及韓世大學、韓信大學（TOPIK 2 級，韓信大學免住宿費）全部韓國交換姊妹校最高韓語門檻"
    elif level == 3:
      tier_note = "符合韓國東新大學、啟明大學、白石大學、聖公會大學、漢陽女子大學（TOPIK 3 級可修韓語授課且漢陽女大免自費語學堂）及韓世大學、韓信大學（TOPIK 2 級）交換門檻"
    elif level == 2:
      tier_note = "符合韓國韓世大學與韓信大學（免住宿費）之 TOPIK 2 級必備門檻，並可申請東新、啟明、白石、聖公會、又松、韓東國際、韓一長神大學（惟修讀韓語授課需 TOPIK 3 級以上）"
    else:
      tier_note = "韓國東新大學、啟明大學、白石大學、聖公會大學雖無韓語基礎可申請，但韓世大學與韓信大學要求 TOPIK 2 級以上，且所有韓國志願報名時均須繳交二年內曾修讀韓文課程之證明"
    return (
        "pass" if passed else "fail",
        f"TOPIK {level} 級{'符合' if passed else '未達'}長榮大學韓國姊妹校交換韓語基準（{tier_note}）。",
    )
  return (
      "needs_confirmation",
      f"已填報語言檢定 {language_test}（{language_score:g}）；請對照長榮大學《115學年度校級國際交換生甄選簡章》附錄一（CEFR A2–B2、TOEFL iBT、IELTS、TOEIC、Duolingo、JLPT N2–N4、TOPIK 2–4 級及德／法／西／韓語二年內修課證明）確認目標姊妹校語言門檻。",
  )
