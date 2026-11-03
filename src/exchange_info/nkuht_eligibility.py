from __future__ import annotations

import re

from .university_registry import resolve_university

NKUHT_IAO_HOME_URL = "https://iao.nkuht.edu.tw/"
NKUHT_STUDY_ABROAD_URL = "https://iao.nkuht.edu.tw/p/412-1007-7229.php?Lang=zh-tw"
NKUHT_2027_28_PLATFORM_URL = "https://iao.nkuht.edu.tw/p/412-1007-7236.php?Lang=zh-tw"
NKUHT_TUITION_FREE_URL = "https://iao.nkuht.edu.tw/p/403-1007-1052.php?Lang=zh-tw"
NKUHT_FEE_BASED_URL = "https://iao.nkuht.edu.tw/p/403-1007-1051.php?Lang=zh-tw"
NKUHT_APPLICATION_QUALIFICATIONS_URL = "https://iao.nkuht.edu.tw/p/412-1007-5693.php?Lang=zh-tw"
NKUHT_APPLICATION_DOWNLOADS_URL = "https://iao.nkuht.edu.tw/p/412-1007-5714.php?Lang=zh-tw"
NKUHT_XUEHAI_SCHOLARSHIP_URL = "https://iao.nkuht.edu.tw/p/412-1007-6527.php?Lang=zh-tw"
NKUHT_VOYAGE_OF_DISCOVERY_URL = "https://iao.nkuht.edu.tw/p/412-1007-6272.php?Lang=zh-tw"
NKUHT_EXPERIENCE_SHARING_URL = "https://iao.nkuht.edu.tw/p/404-1007-28830.php?Lang=zh-tw"
NKUHT_KEY_PARTNERS_URL = "https://iao.nkuht.edu.tw/p/412-1007-6251.php?Lang=zh-tw"
NKUHT_DUAL_DEGREE_URL = "https://iao.nkuht.edu.tw/p/412-1007-1495.php?Lang=zh-tw"
NKUHT_REGULATIONS_URL = "https://iao.nkuht.edu.tw/p/412-1007-1554.php?Lang=zh-tw"
NKUHT_OVERSEAS_INTERNSHIP_STUDY_SUPPLEMENT_PDF_URL = (
    "https://iao.nkuht.edu.tw/var/file/7/1007/img/1554/525995679.pdf"
)
NKUHT_IAO_SOP_PDF_URL = (
    "https://iao.nkuht.edu.tw/var/file/7/1007/img/1554/180823920.pdf"
)
NKUHT_XUEHAI_115_BROCHURE_PDF_URL = (
    "https://iao.nkuht.edu.tw/var/file/7/1007/img/6527/550985664.pdf"
)
NKUHT_VOYAGE_RULES_PDF_URL = (
    "https://iao.nkuht.edu.tw/var/file/7/1007/img/6272/983135147.pdf"
)
NKUHT_BRIEFING_2027_28_PDF_URL = (
    "https://iao.nkuht.edu.tw/var/file/7/1007/img/7236/869148640.pdf"
)
NKUHT_CEFR_EQUIVALENCY_PDF_URL = (
    "https://iao.nkuht.edu.tw/var/file/7/1007/img/7236/529517726.pdf"
)

NKUHT_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 42.0),
    "ielts": ("IELTS", 4.0),
    "toefl_itp": ("TOEFL ITP/PBT", 460.0),
    "toeic": ("TOEIC", 550.0),
}


def is_nkuht(school_name: str | None) -> bool:
  school = resolve_university(school_name)
  if school is not None and school.id == "nkuht":
    return True
  normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
  return normalized in {
      "國立高雄餐旅大學",
      "高雄餐旅大學",
      "高餐大",
      "高餐",
      "nkuht",
      "national kaohsiung university of hospitality and tourism",
  }


def _is_graduate(degree_level: str | None) -> bool:
  text = (degree_level or "").strip()
  return any(token in text for token in ("碩", "博", "研究"))


def nkuht_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
  degree = (degree_level or "").strip()
  year = (current_year or "").strip()
  if not degree:
    return (
        "needs_confirmation",
        (
            "尚未提供目前學制與年級；依《國立高雄餐旅大學學生海外實習及研習輔導補充規定》及國際事務處《海外研修暨實習甄選申請資格》：（1）日間部四技二年級（含）以上、二技一年級下學期及五專四年級在學學生得申請大三／專四海外研修暨實習方案（研修加實習以 12 個月為原則，各對應 1 學期必修 10 學分）；（2）研究所碩士生得申請澳洲昆士蘭大學（The University of Queensland）1+1 雙聯碩士學位方案；（3）申請教育部「學海飛颺」或「學海惜珠」獎學金須具中華民國國籍且為四技二年級以上或五專四年級以上在學學生（不含在職專班生）。"
        ),
    )
  if any(
      token in degree or token in year
      for token in ("在職專班", "碩專", "emba", "EMBA", "學分班", "選修生", "休學", "五專一", "五專二", "五專三")
  ):
    return (
        "fail",
        (
            f"已填報 {degree}{f'（{year}）' if year else ''}；依《國立高雄餐旅大學學生海外實習及研習輔導補充規定》及《學海飛颺與學海惜珠獎學金申請作業簡章》，在職專班生、休學生或未達五專四年級／四技二年級之學生不得申請海外研修暨實習甄選及教育部學海系列獎助。"
        ),
    )
  is_grad = _is_graduate(degree)
  if not is_grad and year in {"大一", "大一上", "大一下", "一年級", "一年級上學期", "一年級下學期"}:
    return (
        "fail",
        (
            f"已填報 {degree}（{year}）；依國立高雄餐旅大學《海外研修暨實習方案申請資格》與《學海飛颺與學海惜珠獎學金申請作業簡章》，四技學生須於「二年級（含）以上」提出申請（五專部須於四年級提出申請），並於大三全學年（或專四）執行海外研修暨實習。建議於大一、大二期間修畢學院規定之 EMI／ESP 全英語專業課程並取得外語檢定證照。"
        ),
    )
  grad_note = (
      "（提醒：碩士生可申請澳洲昆士蘭大學 The University of Queensland 1+1 旅遊酒店與會展管理雙碩士學位方案，名額不限，須具 IELTS 6.5［單科不低於 6.0］或 TOEFL iBT 87；亦可申請《探索之航：發現新天地》出國研修／雙聯學位獎學金最高 NT$60,000）"
      if is_grad
      else "（提醒：大學部海外研修加實習以 12 個月為原則，各抵免 1 學期必修 10 學分；餐旅學院與觀光學院等重點培育學院學生出國前須修習 EMI 或 ESP 課程至少 2 門，廚藝學院及應日系學生至少 1 門；韓國漢陽女子大學僅限女生申請）"
  )
  return (
      "pass",
      (
          f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合國立高雄餐旅大學國際事務處《海外研修暨實習方案》、《與國外大學校院辦理跨國雙聯學制實施辦法》及獎助學金之在學身分規定{grad_note}。"
      ),
  )


def nkuht_academic_check(
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
  passes_top_tier = False

  if academic_score is not None:
    details.append(f"學業／操行參考平均 {academic_score:g} 分")
    if academic_score >= score_min:
      passes_general = True
    if academic_score >= 75.0:
      passes_top_tier = True
  if academic_gpa is not None:
    details.append(f"GPA {academic_gpa:g}")
    if academic_gpa >= gpa_min:
      passes_general = True
    if academic_gpa >= 3.0:
      passes_top_tier = True
  if class_rank_percent is not None:
    details.append(f"班排名百分比前 {class_rank_percent:g}%")
    if class_rank_percent <= 30.0:
      passes_general = True
      passes_top_tier = True
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
            "尚未填寫歷年學業成績、GPA 或班排名百分比；依《國立高雄餐旅大學學生海外實習及研習輔導補充規定》第 2 點及《115 年度學海飛颺與學海惜珠獎學金申請作業簡章》：（1）申請學海系列獎助金及海外研修暨實習甄選者，前各學年上、下學期（前三學期）操行成績平均須達 70 分以上，且在校期間不得有小過（含）以上處分或違法紀錄；（2）重點培育學院（餐旅學院、觀光學院、國際學院）學生須修習 EMI 或 ESP 課程至少 2 門且及格，廚藝學院及應日系學生至少 1 門；（3）報名時須繳交中文歷年成績單（須含班級排名），部分歐美及港澳名校（如香港理工大學、澳門旅遊大學、澳洲昆士蘭大學、荷蘭海牙旅館管理學院、美國蒙特克萊爾州立大學迪士尼交換計畫）另審查歷年 GPA（建議達 GPA 2.75–3.0／平均 75 分以上）。"
        ),
    )

  if passes_general:
    tier_notes: list[str] = [
        "符合高餐大《學生海外實習及研習輔導補充規定》與《學海飛颺／惜珠獎學金》操行及學業基準（70 分以上）"
    ]
    if passes_top_tier:
      tier_notes.append(
          "且達香港理工大學、澳門旅遊大學、澳洲昆士蘭大學 1+1 雙碩士、荷蘭海牙旅館管理學院及美國蒙特克萊爾州立大學迪士尼交換計畫之建議 GPA 門檻"
      )
    else:
      tier_notes.append(
          "請同步確認已修畢學院規定之 EMI／ESP 全英語專業課程門數（重點培育學院 2 門、其他學院及應日系 1 門）且在校無小過以上紀錄"
      )
    return (
        "pass",
        f"已填報 {summary}；{'；'.join(tier_notes)}。",
    )

  return (
      "needs_confirmation",
      (
          f"已填報 {summary}；依《國立高雄餐旅大學學生海外實習及研習輔導補充規定》及《學海飛颺與學海惜珠獎學金申請作業簡章》，申請人前三學期操行成績平均須達 70 分以上且無小過以上處分，部分姊妹校（如香港理工大學、昆士蘭大學、蒙特克萊爾州立大學）另設有 GPA 門檻，建議向國際事務處確認。"
      ),
  )


def nkuht_language_check(
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
            "申請赴中國大陸地區合作院校（北京第二外國語學院、浙江旅遊職業學院、南京旅遊職業學院）為中文授課，免附外語檢定證照；惟仍須符合高餐大校內甄選之歷年成績、操行（70 分以上）及書面審查規定。"
        ),
    )
  if not test or language_score is None:
    return (
        "needs_confirmation",
        (
            "尚未填寫外語能力檢定成績。依國立高雄餐旅大學國際事務處《2027–28 海外研修暨實習方案》與《各類語言檢定證照等級對照表》（CEFR B1/B2）：（1）英語授課組：泰國瓦萊嵐大學、菲律賓三一大學、加拿大漢堡學院要求 CEFR B1（新版 TOEIC 550［聽275/讀275］/ IELTS 4.0 / TOEFL iBT 42 / GEPT 中級）；韓國又松大學、泰國藝術大學、曼谷大學、菲律賓萊西姆大學、杜拜阿聯酋酒店管理學院、美國南佛羅里達大學要求 TOEIC 600 / IELTS 5.0–5.5 / TOEFL iBT 61 / Duolingo 80–85；芬蘭赫爾辛基哈戈赫利亞應用科大、法國薩維尼雅克國際旅館學校、荷蘭海牙旅館管理學院、瑞士格里昂 Glion、瑞士廚藝管理大學 CAAS、瑞士旅館管理學校 SHMS 要求 CEFR B2（新版 TOEIC 785［聽400/讀385］/ IELTS 5.5 / TOEFL iBT 72）；香港理工大學、澳門旅遊大學、澳洲國際旅館管理學院 ICHM、英國艾賽克斯大學、英國伯明罕大學學院 UCB、瑞士雷赫士 Les Roches、美國蒙特克萊爾州立大學迪士尼計畫要求 IELTS 6.0 / TOEFL iBT 70–80 / TOEIC 750–785；法國法蘭迪大學 FERRANDI、法國里昂廚藝與餐旅管理學院 Institut Lyfe、澳洲昆士蘭大學 1+1 雙碩士要求 IELTS 6.5 / TOEIC 780+；（2）日語組：日本京都先端科學大學要求 JLPT N3 以上；文京學院大學、阪南大學、山口大學、九州國際大學要求 JLPT N2 以上；武藏野大學要求 JLPT N1；（3）韓語組：韓國仁德大學、漢陽女子大學要求 TOPIK 3 級以上；（4）115-1 梯次申請者最遲須於 2027/02/26–03/03 前補繳達標語言證照。"
        ),
    )
  if test in NKUHT_ENGLISH_MINIMUMS:
    label, minimum = NKUHT_ENGLISH_MINIMUMS[test]
    passed = language_score >= minimum
    tier_note = "達 CEFR B1 基準門檻（符合泰國瓦萊嵐大學、菲律賓三一大學、加拿大漢堡學院及學海系列基本外語門檻）"
    if (
        (test == "toefl" and language_score >= 87)
        or (test == "ielts" and language_score >= 6.5)
        or (test == "toefl_itp" and language_score >= 560)
        or (test == "toeic" and language_score >= 800)
    ):
      tier_note = "達高階門檻（IELTS 6.5 / TOEFL iBT 87 / TOEIC 800+），符合法國法蘭迪大學（FERRANDI Paris）、法國里昂廚藝與餐旅管理學院（Institut Lyfe）、澳洲昆士蘭大學（UQ 1+1 雙碩士）、香港理工大學、澳門旅遊大學、瑞士雷赫士（Les Roches）及美國蒙特克萊爾州立大學迪士尼計畫等全部英語系姊妹校最高門檻"
    elif (
        (test == "toefl" and language_score >= 72)
        or (test == "ielts" and language_score >= 6.0)
        or (test == "toefl_itp" and language_score >= 543)
        or (test == "toeic" and language_score >= 785)
    ):
      tier_note = "達 CEFR B2 門檻（新版 TOEIC 785 / IELTS 6.0 / TOEFL iBT 72+），符合香港理工大學、澳門旅遊大學、芬蘭 Haaga-Helia、法國 Savignac、荷蘭海牙旅館管理學院、澳洲 ICHM、英國 Essex 與 UCB、瑞士 Les Roches / Glion / CAAS / SHMS 及美國蒙特克萊爾州立大學迪士尼交換計畫門檻（法國 FERRANDI、Institut Lyfe 及澳洲昆士蘭大學需 IELTS 6.5）"
    elif (
        (test == "toefl" and language_score >= 61)
        or (test == "ielts" and language_score >= 5.5)
        or (test == "toefl_itp" and language_score >= 500)
        or (test == "toeic" and language_score >= 600)
    ):
      tier_note = "符合韓國又松大學（Woosong）、泰國藝術大學（Silpakorn）、曼谷大學（Bangkok University）、瓦萊嵐大學、菲律賓三一大學、萊西姆大學、加拿大漢堡學院、杜拜阿聯酋酒店管理學院及美國南佛羅里達大學門檻（若為 IELTS 5.5 亦符合瑞士 Glion / CAAS / SHMS、芬蘭 Haaga-Helia、法國 Savignac 及荷蘭海牙旅館管理學院）"
    return (
        "pass" if passed else "fail",
        (
            f"{label} {language_score:g} {'符合' if passed else '未達'}國立高雄餐旅大學海外研修暨實習英語檢定基準（最低採計門檻：{label} {minimum:g}；{tier_note}）。"
        ),
    )
  if test == "jlpt":
    level = int(language_score)
    passed = 1 <= level <= 3
    if level == 1:
      tier_note = "符合日本武藏野大學（JLPT N1）、文京學院大學、阪南大學、山口大學、九州國際大學（JLPT N2）及京都先端科學大學（JLPT N3）全部日本姊妹校研修暨飯店／溫泉旅館實習門檻"
    elif level == 2:
      tier_note = "符合日本文京學院大學（含阪急阪神第一飯店集團實習）、阪南大學（含 JASSO／校內獎學金申請資格）、山口大學（含常盤溫泉旅館實習）、九州國際大學（JLPT N2）及京都先端科學大學（JLPT N3）門檻（武藏野大學要求 JLPT N1）"
    elif level == 3:
      tier_note = "符合日本京都先端科學大學（KUAS，JLPT N3）研修暨實習門檻（文京學院大學、阪南大學、山口大學、九州國際大學要求 JLPT N2 以上；武藏野大學要求 JLPT N1）"
    else:
      tier_note = f"目前為 JLPT N{level}，未達高餐大日本研修暨實習合作校最低門檻（京都先端科學大學需 JLPT N3 以上，文京學院大學／阪南大學／山口大學需 N2 以上，武藏野大學需 N1；最遲須於 2027/02/26 前補繳達標證照）"
    return (
        "pass" if passed else "fail",
        f"JLPT N{level} {'符合' if passed else '未達'}國立高雄餐旅大學日本姊妹校海外研修暨實習日語檢定基準（{tier_note}）。",
    )
  if test == "topik":
    level = int(language_score)
    passed = 3 <= level <= 6
    if passed:
      tier_note = "符合韓國仁德大學（Induk University）與漢陽女子大學（Hanyang Women's University，限女生）之 TOPIK 3 級交換門檻"
    else:
      tier_note = f"目前為 TOPIK {level} 級，韓國仁德大學與漢陽女子大學要求 TOPIK 3 級以上（韓國又松大學 Woosong University 則採計英語檢定 TOEIC 600 / IELTS 5.5 / TOEFL iBT 61）"
    return (
        "pass" if passed else "fail",
        f"TOPIK {level} 級{'符合' if passed else '未達'}國立高雄餐旅大學韓國姊妹校韓語檢定基準（{tier_note}）。",
    )
  return (
      "needs_confirmation",
      f"已填報語言檢定 {language_test}（{language_score:g}）；請對照國立高雄餐旅大學國際事務處《各類語言檢定證照等級對照表》（CEFR B1/B2、TOEIC、TOEFL、IELTS、JLPT、TOPIK、DELF）確認目標合作學校之語言門檻。",
  )
