from __future__ import annotations

import re

from .university_registry import ISU, resolve_university

ISU_HOME_URL = "https://www.isu.edu.tw/"
ISU_OICA_HOME_URL = "https://oica.isu.edu.tw/"
ISU_EXCHANGE_DUAL_HUB_URL = (
    "https://oica.isu.edu.tw/page/%E5%87%BA%E5%9C%8B%E4%BA%A4%E6%8F%9B%E6%9A%A8%E9%9B%99%E8%81%AF%E5%AD%B8%E4%BD%8D-6b19J0mB5d1R"
)
ISU_OUTBOUND_EXCHANGE_URL = (
    "https://oica.isu.edu.tw/page/%E5%87%BA%E5%9C%8B%E4%BA%A4%E6%8F%9B-NlHq3RuLdDcK"
)
ISU_EXCHANGE_SISTER_SCHOOLS_URL = (
    "https://oica.isu.edu.tw/page/%E4%BA%A4%E6%8F%9B%E5%A7%90%E5%A6%B9%E6%A0%A1-X2088kX30A7R"
)
ISU_DUAL_DEGREE_URL = (
    "https://oica.isu.edu.tw/page/%E9%9B%99%E8%81%AF%E5%AD%B8%E4%BD%8D-a1O64jH79N8m"
)
ISU_DUAL_DEGREE_SCHOOLS_URL = (
    "https://oica.isu.edu.tw/page/%E9%9B%99%E8%81%AF%E5%AD%B8%E4%BD%8D%E5%AD%B8%E6%A0%A1-O76v3d9W18qB"
)
ISU_PARTNER_SCHOOLS_URL = (
    "https://oica.isu.edu.tw/page/%E5%90%88%E4%BD%9C%E5%A7%90%E5%A6%B9%E6%A0%A1-2136fX4h11fT"
)
ISU_REGULATIONS_URL = (
    "https://oica.isu.edu.tw/page/%E5%85%AC%E5%91%8A%E8%BE%A6%E6%B3%95-x86E5vW50l1r"
)
ISU_SCHOLARSHIPS_URL = (
    "https://oica.isu.edu.tw/page/%E7%8D%8E%E5%AD%B8%E9%87%91-R65031O5136E"
)
ISU_MOBILITY_SCHOLARSHIP_URL = (
    "https://oica.isu.edu.tw/page/%E7%8D%8E%E5%8A%A9%E5%AD%B8%E9%87%91-6187b9V0610U"
)
ISU_STUDENT_EXPERIENCES_URL = (
    "https://oica.isu.edu.tw/page/%E5%AD%B8%E9%95%B7%E5%A7%90%E7%B6%93%E9%A9%97%E5%82%B3%E6%89%BF-4T47lR6a96U4"
)
ISU_FAQ_URL = (
    "https://oica.isu.edu.tw/page/%E5%B8%B8%E8%A6%8B%E5%95%8F%E9%A1%8C%E8%88%87%E8%A7%A3%E7%AD%94-y294B2o02s6q"
)
ISU_DOWNLOADS_URL = (
    "https://oica.isu.edu.tw/page/%E8%A1%A8%E5%96%AE%E4%B8%8B%E8%BC%89-6s203nK125P9"
)
ISU_ADMISSION_RESULTS_URL = (
    "https://oica.isu.edu.tw/page/%E6%AD%B7%E5%B9%B4%E9%8C%84%E5%8F%96%E5%90%8D%E5%96%AE-58u131J2z9M2"
)
ISU_COST_REF_SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/14w5Amw4wQzBUh1LI2Xj2m7eEGoZbmdQaI_HVhPEzWRI/htmlview"
)
ISU_OUTBOUND_SELECTION_RULES_PDF_URL = (
    "https://oica.isu.edu.tw/storage/files/5KGWFUmApkKrcC7r2uKfmaUqcMPROayp01WRTBiD.pdf"
)
ISU_MOE_XUEHAI_SELECTION_RULES_PDF_URL = (
    "https://oica.isu.edu.tw/storage/files/uCeTr1BtjbSFpZo5r1Z2VZaYiIcot3uW520kpPJU.pdf"
)
ISU_XUEHAI_SCHOLARSHIP_RULES_PDF_URL = (
    "https://oica.isu.edu.tw/storage/files/JWcDchnBY7mcsNUV15fdrbsiqNXmzZMqdb6opq3D.pdf"
)
ISU_MAINLAND_SCHOLARSHIP_RULES_PDF_URL = (
    "https://oica.isu.edu.tw/storage/files/loZLXWMAzzGVVF7MQj38fhdZo69iSefE65QO3qaT.pdf"
)
ISU_XUEWEN_SCHOLARSHIP_RULES_PDF_URL = (
    "https://www.isu.edu.tw/upload/654/3/20220829-MOE-Scholarship-Regulations.pdf"
)
ISU_JAPAN_SISTER_LIST_PDF_URL = (
    "https://oica.isu.edu.tw/storage/files/Pnq9b9VMODWbiJw6BVdjpN7EBXMY8TTrwiu28CJ3.pdf"
)
ISU_CREDIT_APPROVAL_FORM_DOC_URL = (
    "https://oica.isu.edu.tw/storage/files/CyDv16tauPxLhbW491g2hv9c5x42CCWiam2nN0JA.doc"
)
ISU_CREDIT_TRANSFER_FORM_DOC_URL = (
    "https://oica.isu.edu.tw/storage/files/dnLg5CuBYnPAJf9c63fGpCjfjfwWdBevIx3BzUx7.doc"
)
ISU_RETURN_PROCEDURE_PDF_URL = (
    "https://oica.isu.edu.tw/storage/files/0hUyXldM3VM1XPRfNORKw5LlBOQkfnbWTvXXKquS.pdf"
)
ISU_RETURN_REPORT_DOC_URL = (
    "https://oica.isu.edu.tw/storage/files/vdjPK5ZiX4SN1YuA28rlKk9U2iK4XZF0TjQCwetW.doc"
)

ISU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 42.0),
    "ielts": ("IELTS", 4.0),
    "toefl_itp": ("TOEFL ITP/PBT", 457.0),
    "toeic": ("TOEIC", 550.0),
}


def is_isu(school_name: str | None) -> bool:
  school = resolve_university(school_name)
  if school is not None and school.id == ISU.id:
    return True
  normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
  return normalized in {
      "義守大學",
      "義大",
      "義守",
      "isu",
      "i-shou university",
      "ishou university",
  }


def _is_graduate(degree_level: str | None) -> bool:
  text = (degree_level or "").strip()
  return any(token in text for token in ("碩", "博", "研究"))


def isu_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
  degree = (degree_level or "").strip()
  year = (current_year or "").strip()
  if not degree:
    return (
        "needs_confirmation",
        (
            "尚未提供目前學制與年級；依《義守大學學生赴境外交換研修甄選辦法》第 2 條：申請人須為具有本校學籍之大學部（大二以上）及研究所（碩一以上）在學學生；延修生、休學學生及當學期畢業者，除有特殊原因外，不得提出申請。"
        ),
    )
  if any(
      token in degree or token in year
      for token in ("延修", "延畢", "休學", "學分班", "選修生")
  ):
    return (
        "fail",
        (
            f"已填報 {degree}{f'（{year}）' if year else ''}；依《義守大學學生赴境外交換研修甄選辦法》第 2 條第 2 項，延修生、休學學生及當學期畢業者，除有特殊原因外，不得提出赴境外交換研修申請。"
        ),
    )
  is_grad = _is_graduate(degree)
  if not is_grad and year in {
      "大一",
      "大一上",
      "大一下",
      "一年級",
      "一年級上學期",
      "一年級下學期",
  }:
    return (
        "fail",
        (
            f"已填報 {degree}（{year}）；依《義守大學學生赴境外交換研修甄選辦法》第 2 條規定，大學部申請人須為「大學部二年級以上」之在學學生。建議於大一期間準備外語檢定並參與國際處說明會，於升大二後之 8 月或 2 月梯次提出申請。"
        ),
    )
  grad_note = (
      "（提醒：出國交流期間須維持義守大學學籍並繳交全額學雜費，每學期修習課程以不低於 9 學分為原則；跨國雙聯學位如英國諾丁漢特倫特大學、美國奧克拉荷馬州立大學、香港理工大學等須符合雙聯協議修業學分規定）"
      if is_grad
      else "（提醒：美國南佛羅里達大學限學士後醫學系外國學生四年級暑期臨床見習；日本梅花女子大學僅收女生；赴大陸結盟學校一學期研修團每學期須至少修習 16 學分，其餘海外交換每學期以不低於 9 學分為原則）"
  )
  return (
      "pass",
      (
          f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合《義守大學學生赴境外交換研修甄選辦法》第 2 條（大學部大二以上／研究所碩一以上）及雙聯學制之在學身分規定{grad_note}。"
      ),
  )


def isu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
  score_min = 60.0
  gpa_min = 2.0
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
    details.append(f"班／系排名百分比前 {class_rank_percent:g}%")
    if class_rank_percent <= 40.0:
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
            "尚未填寫歷年學業平均、GPA 或班／系排名百分比；依《義守大學學生赴境外交換研修甄選辦法》、《義守大學辦理教育部學海飛颺及學海惜珠計畫甄選辦法》及《學海助學金／學文助學金設置辦法》：（1）申請交換生須在校期間學業及操行成績優良（歷年平均及格 60 分以上，部分歐美日韓名校與雙聯學位要求 GPA 2.5–3.0 即 70–80 分以上）；（2）申請教育部《學海飛颺／惜珠獎學金》須操行成績 80 分以上無懲處且前一學期學業成績於該系所該年級前 40% 或班級排名前 30%；（3）申請《義守大學學海助學金（短期交流）》或《學文助學金（大陸研修團）》須成績達該系年級或全班前 50%。"
        ),
    )

  if passes_general:
    tier_notes: list[str] = []
    if (academic_gpa is not None and academic_gpa >= 3.0) or (
        academic_score is not None and academic_score >= 75.0
    ):
      tier_notes.append(
          "已達歐美日韓重點姐妹校（GPA 2.75–3.0／平均 75 分）與跨國雙聯學位高階學業門檻"
      )
    else:
      tier_notes.append(
          "符合義守大學校內交換基本學業標準（平均 60 分／GPA 2.0 以上），惟部分歐美雙聯學位與日韓名校要求 GPA 2.5–3.0 以上"
      )
    if passes_xuehai:
      tier_notes.append(
          "且排名達前 40% 以內，符合《義守大學辦理教育部學海飛颺及學海惜珠計畫甄選辦法》學業排名資格"
      )
    return (
        "pass",
        f"已填報 {summary}；符合義守大學出國交換研修甄選學業標準（{'；'.join(tier_notes)}）。",
    )

  return (
      "needs_confirmation",
      (
          f"已填報 {summary}；未達學業及格標準（60 分／GPA 2.0）或前 50% 排名門檻，依《義守大學學生赴境外交換研修甄選辦法》第 2 條與《學海助學金／學文助學金辦法》，建議先提升學期平均成績並確認目標姐妹校之個別 GPA 要求。"
      ),
  )


def isu_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
  test = (language_test or "").strip().lower()
  if partner_country in {"中國大陸", "中國", "澳門"} and (
      not test or language_score is None
  ):
    return (
        "pass",
        (
            "申請赴中國大陸（浙江大學、南京大學、武漢大學、山東大學、四川大學、吉林大學、蘭州大學等 95 校）或澳門（澳門科技大學、澳門城市大學、澳門理工大學）交換姐妹校為中文授課，依《義守大學學生赴境外交換研修甄選辦法》第 2 條第 3 款免附外語檢定證明（註：若申請《學文助學金》大陸一學期研修團者，仍須通過本校英語能力與資訊能力畢業檢定標準）。"
        ),
    )
  if not test or language_score is None:
    return (
        "needs_confirmation",
        (
            "尚未填寫外語能力檢定成績。依《義守大學學生赴境外交換研修甄選辦法》第 2 條第 3 款：除赴以中文為主要授課語言之學校外，外語能力應符合交流學校規定；如交流學校無外語能力規定，應以符合本校英語能力畢業資格檢定標準（CEFR B1：TOEIC 550 / TOEFL iBT 42 / TOEFL ITP 457 / IELTS 4.0）為原則：（1）英語組與雙聯學位：法國巴黎 EDH 集團接受義守大學出具之 CEFR B2 證明、美國密蘇里大學堪薩斯分校 ALI 課程免托福或雅思；美國南伊利諾大學 SIUC 要求 iBT 68 / IELTS 6.0、西來大學要求 iBT 69 / IELTS 5.5、聖道大學要求 iBT 79 / IELTS 6.5 / TOEIC 650；英國考文垂大學与諾丁漢特倫特大學要求 IELTS 6.0–6.5；法國 NEOMA、Audencia、EDHEC、德國杜塞道夫大學、奧地利 MCI、芬蘭 Haaga-Helia、立陶宛維陶瑪納大學要求 CEFR B2（iBT 72–80 / IELTS 5.5–6.0）；香港理工大學要求 iBT 80 / IELTS 6.0；（2）日本組（31 校）：埼玉大學、秋田國際教養大學 AIU、立命館亞洲太平洋大學 APU、關西國際大學、崇城大學可憑英語成績申請，京都府立大學、和歌山大學、帝京大學、東洋學園大學、駒澤大學等要求 JLPT N2–N3；（3）韓國組（20 校）：可選修英語授課（CEFR B1–B2）或韓語授課（TOPIK 2–4 級）。"
        ),
    )
  if test in ISU_ENGLISH_MINIMUMS:
    label, minimum = ISU_ENGLISH_MINIMUMS[test]
    passed = language_score >= minimum
    tier_note = "達義守大學英語能力畢業資格檢定基準（CEFR B1）"
    if (
        (test == "toefl" and language_score >= 80)
        or (test == "ielts" and language_score >= 6.0)
        or (test == "toefl_itp" and language_score >= 550)
        or (test == "toeic" and language_score >= 785)
    ):
      tier_note = "達 CEFR B2 高階門檻，符合香港理工大學、英國諾丁漢特倫特大學與考文垂大學、法國北方高等商學院 EDHEC、南特商學院 Audencia、諾歐商學院 NEOMA、德國杜塞道夫大學、美國聖道大學、南伊利諾大學 SIUC、聖地牙哥州立大學等全部歐美亞英語授課交換與雙聯學位門檻"
    elif (
        (test == "toefl" and language_score >= 68)
        or (test == "ielts" and language_score >= 5.5)
        or (test == "toefl_itp" and language_score >= 520)
        or (test == "toeic" and language_score >= 650)
    ):
      tier_note = "符合美國南伊利諾大學卡本岱爾校區（iBT 68）、美國西來大學（iBT 69 / IELTS 5.5）、聖道大學（TOEIC 650）、法國巴黎 EDH 集團及多數亞太與歐洲英語授課姐妹校門檻（英國考文垂與諾丁漢特倫特需 IELTS 6.0、香港理工需 iBT 80 / IELTS 6.0）"
    return (
        "pass" if passed else "fail",
        (
            f"{label} {language_score:g} {'符合' if passed else '未達'}義守大學《學生赴境外交換研修甄選辦法》外語採計標準（最低基準：{label} {minimum:g}；{tier_note}）。"
        ),
    )
  if test == "jlpt":
    level = int(language_score)
    passed = 1 <= level <= 5
    if level <= 2:
      tier_note = f"JLPT N{level} 符合日本京都府立大學、和歌山大學、帝京大學、東洋學園大學、駒澤大學、松本大學、明海大學、梅花女子大學、追手門學院大學、大阪產業大學、神戶學院大學、天理大學、福井大學、山口大學等全部 31 所日本姐妹校日語門檻"
    elif level == 3:
      tier_note = "JLPT N3 符合日本東洋學園大學、松本大學、明海大學、梅花女子大學、追手門學院大學、天理大學、西九州大學等 N3 門檻姐妹校（京都府立大學、和歌山大學、駒澤大學等要求 N2 以上）"
    else:
      tier_note = f"已具 JLPT N{level} 基礎日語能力，建議申請關西國際大學、崇城大學或搭配英語成績申請埼玉大學、AIU、APU 等英語授課學程（日語授課組多要求 JLPT N2–N3）"
    return (
        "pass" if passed else "fail",
        f"JLPT N{level} {'符合' if passed else '未達'}義守大學日本姐妹校交換日語檢定基準（{tier_note}）。",
    )
  if test == "topik":
    level = int(language_score)
    passed = 1 <= level <= 6
    if level >= 3:
      tier_note = "符合韓國高麗大學世宗校區、慶熙大學、韓國外國語大學、建國大學、東國大學、仁川大學、嘉泉大學、翰林大學、順天鄉大學、東亞大學等全部 20 所韓國交換姐妹校韓語授課門檻"
    elif level == 2:
      tier_note = "符合韓國嘉泉大學、翰林大學、順天鄉大學、東亞大學、大邱保健大學等基礎韓語門檻（部分韓國名校韓語授課學程要求 TOPIK 3–4 級，或可選修英語授課學程）"
    else:
      tier_note = "已具 TOPIK 1 級基礎韓語檢定成績，建議選修韓國姐妹校英語授課課程或語學堂課程"
    return (
        "pass" if passed else "fail",
        f"TOPIK {level} 級{'符合' if passed else '未達'}義守大學韓國姐妹校交換外語基準（{tier_note}）。",
    )
  return (
      "needs_confirmation",
      f"已填報語言檢定 {language_test}（{language_score:g}）；請對照義守大學國際及兩岸事務處《交換姐妹校名冊》與《日本姐妹校一覽表》確認目標姐妹校語言門檻。",
  )
