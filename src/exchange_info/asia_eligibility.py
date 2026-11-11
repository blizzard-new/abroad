from __future__ import annotations

import re

from .university_registry import resolve_university

ASIA_OIA_HOME_URL = "https://oia.asia.edu.tw/"
ASIA_PARTNER_MAP_URL = "https://oia.asia.edu.tw/zh_tw/Map"
ASIA_OUTBOUND_EXCHANGE_URL = (
    "https://oia.asia.edu.tw/p/412-1008-258.php?Lang=zh-tw"
)
ASIA_OUTBOUND_ELIGIBILITY_URL = (
    "https://oia.asia.edu.tw/p/412-1008-53.php?Lang=zh-tw"
)
ASIA_EXCHANGE_LIST_URL = "https://oia.asia.edu.tw/p/412-1008-54.php?Lang=zh-tw"
ASIA_EXCHANGE_2027_SPRING_ANNOUNCEMENT_URL = (
    "https://oia.asia.edu.tw/p/406-1008-221849,r2174.php?Lang=zh-tw"
)
ASIA_EXCHANGE_2026_FALL_ANNOUNCEMENT_URL = (
    "https://oia.asia.edu.tw/p/406-1008-216721,r2174.php?Lang=zh-tw"
)
ASIA_318_SCHOLARSHIP_URL = (
    "https://oia.asia.edu.tw/p/412-1008-296.php?Lang=zh-tw"
)
ASIA_XUEHAI_URL = "https://oia.asia.edu.tw/p/412-1008-276.php?Lang=zh-tw"
ASIA_DUAL_DEGREE_URL = "https://oia.asia.edu.tw/p/412-1008-59.php?Lang=zh-tw"
ASIA_EXPERIENCE_REPORTS_URL = (
    "https://oia.asia.edu.tw/p/404-1008-94158.php?Lang=zh-tw"
)
ASIA_AC_REGULATIONS_URL = (
    "https://ac.asia.edu.tw/zh_tw/Downloads/Rules_Regulations"
)

ASIA_EXCHANGE_IMPLEMENTATION_PDF_URL = "https://oia.asia.edu.tw/var/file/8/1008/img/676/%E4%BA%9E%E6%B4%B2%E5%A4%A7%E5%AD%B8%E5%AD%B8%E7%94%9F%E5%87%BA%E5%9C%8B%E4%BA%A4%E6%8F%9B%E7%94%9F%E5%AF%A6%E6%96%BD%E8%BE%A6%E6%B3%95.pdf"
ASIA_2027_SPRING_EXCHANGE_LIST_PDF_URL = (
    "https://oia.asia.edu.tw/var/file/8/1008/img/736/297719364.pdf"
)
ASIA_2027_SPRING_BROCHURE_PDF_URL = (
    "https://oia.asia.edu.tw/var/file/8/1008/img/222234389.pdf"
)
ASIA_2027_SPRING_APPLICATION_PACKAGE_ZIP_URL = (
    "https://oia.asia.edu.tw/var/file/8/1008/img/680/351475617.zip"
)
ASIA_318_GUIDELINES_PDF_URL = (
    "https://oia.asia.edu.tw/var/file/8/1008/img/693/195186761.pdf"
)
ASIA_XUEHAI_GUIDELINES_PDF_URL = (
    "https://oia.asia.edu.tw/var/file/8/1008/img/676/391068346.pdf"
)
ASIA_XUEHAI_SCHOLARSHIP_REGULATIONS_PDF_URL = (
    "https://oia.asia.edu.tw/var/file/8/1008/img/676/208046282.pdf"
)
ASIA_DUAL_DEGREE_SCHOLARSHIP_PDF_URL = (
    "https://oia.asia.edu.tw/var/file/8/1008/img/676/434389903.pdf"
)
ASIA_DUAL_DEGREE_IMPLEMENTATION_PDF_URL = (
    "https://ac.asia.edu.tw/uploads/asset/data/658cefd07489ab398bf00c51/4-8.pdf"
)
ASIA_ABROAD_ACADEMIC_REGISTRATION_PDF_URL = "https://ac.asia.edu.tw/uploads/asset/data/658cefe87489ab3983f00c75/4-10.pdf"
ASIA_CREDIT_TRANSFER_PDF_URL = (
    "https://ac.asia.edu.tw/uploads/asset/data/658cefba7489ab398df00c55/4-5.pdf"
)

ASIA_318_APPLICATION_FORM_DOCX_URL = (
    "https://oia.asia.edu.tw/var/file/8/1008/img/693/850602460.docx"
)
ASIA_318_STUDY_PLAN_DOCX_URL = (
    "https://oia.asia.edu.tw/var/file/8/1008/img/693/585720604.docx"
)
ASIA_318_PARENTAL_CONSENT_DOCX_URL = (
    "https://oia.asia.edu.tw/var/file/8/1008/img/693/113347892.docx"
)
ASIA_XUEHAI_APPLICATION_FORM_DOCX_URL = (
    "https://oia.asia.edu.tw/var/file/8/1008/img/676/308575179.docx"
)

ASIA_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 42.0),
    "ielts": ("IELTS", 4.0),
    "toefl_itp": ("TOEFL ITP/PBT", 460.0),
    "toeic": ("TOEIC", 550.0),
    "duolingo": ("Duolingo English Test", 85.0),
}


def is_asia(school_name: str | None) -> bool:
  school = resolve_university(school_name)
  if school is not None and school.id == "asia":
    return True
  normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
  return normalized in {
      "亞洲大學",
      "亞大",
      "臺中健康暨管理學院",
      "台中健康暨管理學院",
      "asia",
      "asia university",
      "asia university taiwan",
      "asia university, taiwan",
  }


def _is_graduate(degree_level: str | None) -> bool:
  text = (degree_level or "").strip()
  return any(token in text for token in ("碩", "博", "研究"))


def asia_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
  degree = (degree_level or "").strip()
  year = (current_year or "").strip()
  if not degree:
    return (
        "needs_confirmation",
        (
            "尚未提供目前學制與年級；依《亞洲大學學生出國交換生實施辦法》第 3 條及《亞洲大學學海計畫-選送優秀學生出國研修助學金審查要點》規定：（1）限本校具中華民國國籍之全職在學學生，且於亞洲大學就讀滿一學期（含）以上；（2）學士班大二、大三及碩士班、博士班學生為主要甄選對象（大一上學期新生尚未修滿一學期不得申請；不含在職專班、延修生及休學生）；（3）選讀跨國雙聯學位者須符合《亞洲大學與國外大學辦理雙聯學制實施辦法》規定之修業期限（學士班累計至少 32 個月、碩士班至少 12 個月、博士班至少 24 個月）。"
        ),
    )
  if any(
      token in degree or token in year
      for token in (
          "在職專班",
          "碩專",
          "emba",
          "EMBA",
          "學分班",
          "選修生",
          "休學",
          "延畢",
          "延畢生",
          "延修",
          "應屆畢業",
          "當學期畢業",
      )
  ):
    return (
        "fail",
        (
            f"已填報 {degree}{f'（{year}）' if year else ''}；依《亞洲大學學生出國交換生實施辦法》、《亞洲大學 318 國際交流亮點計畫補助要點》與《亞洲大學學海計畫-選送優秀學生出國研修助學金審查要點》，在職專班、延修（延畢）生、休學生及當學期應屆畢業生不得申請出國交換與相關獎助學金。"
        ),
    )
  is_grad = _is_graduate(degree)
  if not is_grad and year in {"大一上", "一年級上學期"}:
    return (
        "fail",
        (
            f"已填報 {degree}（{year}）；依《亞洲大學學生出國交換生實施辦法》第 3 條規定，申請人須於亞洲大學就讀滿一學期（含）以上始得提出申請。建議於大一上學期維持總平均 75 分以上（或系排前 50%）並準備語言檢定，於大一下學期起提出申請。"
        ),
    )
  grad_note = (
      "（提醒：碩博士班研究生可申請 1 學期或 1 學年學期交換、教育部學海計畫或美國北伊利諾大學 NIU 等碩士雙聯學位，出國期間須維持亞大在學註冊且至少修讀 1 門專業課程）"
      if is_grad
      else "（提醒：學士班交換生於姊妹校每學期至少須修讀 2 門或 6 學分專業課程；申請跨國雙聯學位者於兩校修業時間合計須達 32 個月以上，且兩校修習學分數各須達畢業總學分 1/3 以上）"
  )
  return (
      "pass",
      (
          f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合亞洲大學國際事務處《亞洲大學學生出國交換生實施辦法》、《與國外大學辦理雙聯學制實施辦法》及亞大 318／教育部學海計畫之在學身分規定{grad_note}。"
      ),
  )


def asia_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
  score_min = 75.0
  gpa_min = 2.5
  rank_max = 50.0
  details: list[str] = []
  passes_general = False
  passes_high_tier = False

  if academic_score is not None:
    details.append(f"學業平均 {academic_score:g} 分")
    if academic_score >= score_min:
      passes_general = True
    if academic_score >= 80.0:
      passes_high_tier = True
  if academic_gpa is not None:
    details.append(f"GPA {academic_gpa:g}")
    if academic_gpa >= gpa_min:
      passes_general = True
    if academic_gpa >= 3.0:
      passes_high_tier = True
  if class_rank_percent is not None:
    details.append(f"系排名百分比前 {class_rank_percent:g}%")
    if class_rank_percent <= rank_max:
      passes_general = True
    if class_rank_percent <= 30.0:
      passes_high_tier = True

  summary = "、".join(details)
  if (
      academic_score is None
      and academic_gpa is None
      and class_rank_percent is None
  ):
    return (
        "needs_confirmation",
        (
            "尚未填寫歷年學業成績、GPA 或系排名百分比；依《亞洲大學學生出國交換生實施辦法》第 3 條及甄選簡章規定：（1）在校學業成績總平均須達 75 分（含）以上，或名列全系（所）前百分之五十（50%），且操行成績平均達 80 分以上；（2）申請教育部《學海惜珠》者歷年成績須達全班前 40%，申請《學海飛颺》或《雙聯學位獎助學金》建議維持 GPA 3.0（約 75–80 分）以上；（3）部分歐美日韓盟校（如加拿大維多利亞大學 UVic 3.33/4.33、美國蒙clair州立大學 GPA 2.75–3.0、韓國成均館大學與外國語大學 GPA 2.5–3.0）另有指定 GPA 門檻。"
        ),
    )

  if passes_general:
    tier_notes: list[str] = [
        "符合《亞洲大學學生出國交換生實施辦法》第 3 條（學業總平均 75 分以上或全系前 50%）及《亞洲大學 318 國際交流亮點計畫補助要點》之基本學業門檻"
    ]
    if passes_high_tier:
      tier_notes.append(
          "且達教育部《學海飛颺／學海惜珠》（全班前 40% 或優異 GPA）與多數歐美日韓姊妹校（GPA 3.0+）及雙聯學位獎助學金之高階學業基準"
      )
    else:
      tier_notes.append(
          "若欲同時申請教育部《學海惜珠》（須全班前 40%）或要求 GPA 3.0+ 之歐美盟校（如加拿大 UVic、美國 Montclair State University），建議確認目標校個別 GPA 門檻"
      )
    return (
        "pass",
        f"已填報 {summary}；{'；'.join(tier_notes)}。",
    )

  return (
      "needs_confirmation",
      (
          f"已填報 {summary}；未達《亞洲大學學生出國交換生實施辦法》第 3 條規定之「學業總平均 75 分以上或名列全系前 50%」門檻，建議同時填報系排名百分比或向國際事務處（行政大樓 L105）確認是否符合特定計畫資格。"
      ),
  )


def asia_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
  test = (language_test or "").strip().lower()
  if not test or language_score is None:
    return (
        "needs_confirmation",
        (
            "尚未填寫外語能力檢定成績。依亞洲大學國際事務處《2027 春季班出國交換學校一覽表（115-2）》與《學海飛颺／雙聯學位獎助學金辦法》：（1）英語組盟校依各校規定要求 TOEFL iBT 60–90、IELTS 5.5–6.5 或 TOEIC 550–800（例如捷克奧斯特拉瓦大學要求 CEFR B2［TOEFL iBT 72 / IELTS 5.5 / TOEIC 785］、法國蒙彼利埃商學院要求 TOEFL iBT 80 / IELTS 6.0 / Duolingo 105、韓國成均館大學要求 TOEFL iBT 80 / IELTS 6.0、加拿大維多利亞大學要求 TOEFL iBT 90 / IELTS 6.5、印尼群島伊斯蘭大學要求 TOEIC 550 / IELTS 5.0）；（2）日語組盟校（近畿大學、關西國際大學、亞細亞大學、長崎外國語大學、帝京大學、東亞大學等）要求 JLPT N2–N4（近畿大學與關西國際大學要求 JLPT N2，亞細亞大學、長崎外國語大學與東亞大學要求 N3，帝京大學要求 N4）；（3）韓語組盟校（慶熙大學、韓國外國語大學、釜山外國語大學、成均館大學等）要求 TOPIK 2–3 級或英語檢定；（4）申請《亞大 318 國際交流亮點計畫》或《教育部學海飛颺／惜珠》須檢附有效外語能力證明（建議達 CEFR B1–B2 以上）。"
        ),
    )
  if test in ASIA_ENGLISH_MINIMUMS:
    label, minimum = ASIA_ENGLISH_MINIMUMS[test]
    passed = language_score >= minimum
    tier_note = "達 CEFR B1 基礎英語門檻（符合印尼群島伊斯蘭大學、馬來西亞拉曼大學 UTAR、日本關西國際大學英語學程及亞大 318 計畫基本外語基準）"
    if (
        (test == "toefl" and language_score >= 80)
        or (test == "ielts" and language_score >= 6.0)
        or (test == "toefl_itp" and language_score >= 550)
        or (test == "toeic" and language_score >= 800)
        or (test == "duolingo" and language_score >= 105)
    ):
      tier_note = "達高階英語門檻（TOEFL iBT 80+ / IELTS 6.0+ / TOEIC 800+ / Duolingo 105+），符合法國蒙彼利埃商學院（MBS）、韓國成均館大學（SKKU）、韓國外國語大學（HUFS）、捷克馬薩里克大學與奧斯特拉瓦大學、波蘭華沙經濟大學（SGH）、美國北伊利諾大學（NIU 雙聯）及教育部學海飛颺高階英語基準（註：加拿大維多利亞大學 UVic 交換要求 TOEFL iBT 90 / IELTS 6.5）"
    elif (
        (test == "toefl" and language_score >= 72)
        or (test == "ielts" and language_score >= 5.5)
        or (test == "toefl_itp" and language_score >= 543)
        or (test == "toeic" and language_score >= 785)
    ):
      tier_note = "達 CEFR B2 門檻（TOEFL iBT 72+ / IELTS 5.5+ / TOEIC 785+），符合捷克奧斯特拉瓦大學、捷克赫拉德茨克拉洛韋大學、義大利天主教聖心大學、韓國世宗大學、韓國中央大學、泰國清邁大學，以及亞洲大學學海飛颺／雙聯學位獎助學金主流英語要求"
    return (
        "pass" if passed else "fail",
        (
            f"{label} {language_score:g} {'符合' if passed else '未達'}亞洲大學出國交換暨獎助學金英語檢定基準（最低採計門檻：{label} {minimum:g}；{tier_note}）。"
        ),
    )
  if test == "jlpt":
    level = int(language_score)
    passed = 1 <= level <= 4
    if level in (1, 2):
      tier_note = f"JLPT N{level} 符合亞洲大學全部日本姊妹校門檻（含近畿大學 N2、關西國際大學 N2、京都先端科學大學 N2、亞細亞大學 N3、長崎外國語大學 N3、東亞大學 N3、穴吹學園 N3、帝京大學 N4）及教育部學海飛颺／亞大 318 計畫日語標準"
    elif level == 3:
      tier_note = "JLPT N3 符合日本亞細亞大學（Asia University, Japan）、長崎外國語大學、東亞大學、穴吹學園（N3）及帝京大學（N4）交換門檻，並達 CEFR B1 學海計畫基準（惟日本近畿大學與關西國際大學日語修課組要求 JLPT N2）"
    elif level == 4:
      tier_note = "JLPT N4 符合日本帝京大學（Teikyo University）交換門檻（若欲申請亞細亞大學、長崎外國語大學或東亞大學須達 JLPT N3，近畿大學與關西國際大學須達 JLPT N2）"
    else:
      tier_note = f"目前為 JLPT N{level}，未達日本帝京大學（N4）、亞細亞大學／長崎外國語大學／東亞大學（N3）或近畿大學／關西國際大學（N2）之日語檢定門檻"
    return (
        "pass" if passed else "fail",
        f"JLPT N{level} {'符合' if passed else '未達'}亞洲大學日本姊妹校交換日語檢定基準（{tier_note}）。",
    )
  if test == "topik":
    level = int(language_score)
    passed = 2 <= level <= 6
    if level >= 3:
      tier_note = f"TOPIK {level} 級符合韓國慶熙大學（TOPIK 3 級）、成均館大學、韓國外國語大學、釜山外國語大學、仁川大學、大邱大學等韓國姊妹校韓語授課組門檻，以及教育部學海飛颺／亞大 318 計畫韓語基準"
    elif level == 2:
      tier_note = "TOPIK 2 級符合韓國釜山外國語大學、大邱大學、極東大學等姊妹校基本韓語門檻（慶熙大學與多數首爾圈盟校韓語組要求 TOPIK 3 級以上，或改以英語檢定申請英語授課組）"
    else:
      tier_note = f"目前為 TOPIK {level} 級，未達韓國姊妹校韓語授課組一般門檻（TOPIK 2–3 級以上，惟部分韓國姊妹校可改以 TOEFL/IELTS/TOEIC 申請英語授課課程）"
    return (
        "pass" if passed else "fail",
        f"TOPIK {level} 級{'符合' if passed else '未達'}亞洲大學韓國姊妹校韓語檢定基準（{tier_note}）。",
    )
  return (
      "needs_confirmation",
      f"已填報語言檢定 {language_test}（{language_score:g}）；請對照亞洲大學國際事務處當期《出國交換學校一覽表（Fact Sheet）》及《學海計畫助學金審查要點》確認目標合作姊妹校之語言門檻。",
  )
