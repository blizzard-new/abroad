from __future__ import annotations

import re

from .university_registry import NTUB, resolve_university

NTUB_OIA_HOME_URL = "https://oia.ntub.edu.tw/"
NTUB_EXCHANGE_RULES_URL = "https://oia.ntub.edu.tw/p/412-1006-3152.php?Lang=zh-tw"
NTUB_EXCHANGE_QUOTAS_URL = "https://oia.ntub.edu.tw/p/412-1006-14367.php?Lang=zh-tw"
NTUB_OVERSEAS_PARTNERS_URL = "https://oia.ntub.edu.tw/p/412-1006-3316.php?Lang=zh-tw"
NTUB_SCHOLARSHIPS_URL = "https://oia.ntub.edu.tw/p/412-1006-15226.php?Lang=zh-tw"
NTUB_FAQ_URL = "https://oia.ntub.edu.tw/p/412-1006-15230.php?Lang=zh-tw"
NTUB_RETURN_URL = "https://oia.ntub.edu.tw/p/412-1006-15228.php?Lang=zh-tw"
NTUB_EXPERIENCES_URL = "https://oia.ntub.edu.tw/p/412-1006-15229.php?Lang=zh-tw"
NTUB_EXPERIENCE_PORTAL_URL = "https://exchangestd.ntub.edu.tw/school-exchange"
NTUB_PARTNER_PORTAL_URL = "https://exchangestd.ntub.edu.tw/school"
NTUB_REGULATIONS_URL = "https://oia.ntub.edu.tw/p/412-1006-14345.php?Lang=zh-tw"
NTUB_DOWNLOADS_URL = "https://oia.ntub.edu.tw/p/412-1006-3153.php?Lang=zh-tw"
NTUB_DUAL_DEGREE_URL = "https://oia.ntub.edu.tw/p/412-1006-11974.php?Lang=zh-tw"
NTUB_INFO_SESSION_116_URL = (
    "https://oia.ntub.edu.tw/p/406-1006-123163,r1240.php?Lang=zh-tw"
)
NTUB_INFO_SESSION_PPTX_URL = (
    "https://oia.ntub.edu.tw/var/file/6/1006/img/1539/337014036.pptx"
)
NTUB_LANGUAGE_SCORE_TABLE_PDF_URL = (
    "https://oia.ntub.edu.tw/var/file/6/1006/img/1539/108293427.pdf"
)
NTUB_GUIDELINES_PDF_URL = (
    "https://oia.ntub.edu.tw/var/file/6/1006/attach/39/pta_96764_8295994_18840.pdf"
)
NTUB_SELECTION_REGULATIONS_PDF_URL = (
    "https://oia.ntub.edu.tw/var/file/6/1006/attach/49/pta_42801_9504163_01196.pdf"
)
NTUB_XUEHAI_FEIYANG_PDF_URL = (
    "https://oia.ntub.edu.tw/var/file/6/1006/attach/35/pta_85778_2722872_37311.pdf"
)
NTUB_XUEHAI_XIZHU_PDF_URL = (
    "https://oia.ntub.edu.tw/var/file/6/1006/attach/38/pta_105840_8968500_20775.pdf"
)
NTUB_WANG_CHUN_MAN_PDF_URL = (
    "https://oia.ntub.edu.tw/var/file/6/1006/img/1539/937380972.pdf"
)
NTUB_DUAL_DEGREE_PDF_URL = (
    "https://oia.ntub.edu.tw/var/file/6/1006/img/1650/782543344.pdf"
)

NTUB_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 65.0),
    "ielts": ("IELTS", 5.5),
}


def is_ntub(school_name: str | None) -> bool:
  school = resolve_university(school_name)
  if school is not None and school.id == NTUB.id:
    return True
  normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
  return normalized in {
      "國立臺北商業大學",
      "國立台北商業大學",
      "臺北商業大學",
      "台北商業大學",
      "北商大",
      "北商",
      "臺北商大",
      "台北商大",
      "ntub",
      "national taipei university of business",
  }


def _is_graduate(degree_level: str | None) -> bool:
  text = (degree_level or "").strip()
  return any(token in text for token in ("碩", "博", "研究"))


def ntub_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
  degree = (degree_level or "").strip()
  year = (current_year or "").strip()
  if not degree:
    return (
        "needs_confirmation",
        (
            "尚未提供目前學制與年級；依《國立臺北商業大學學生申請交換生及雙聯學位生作業要點》及國際處《申請資格與規定》：申請人須為本校在學學生，且符合各學制年級門檻（研究所一年級下學期含以上、二技一年級下學期含以上、四技二年級含以上、五專四年級含以上；四技一年級、二技一年級上學期、五專一至三年級、研究所一年級上學期及境外學生不得申請）。"
        ),
    )
  if any(
      token in degree or token in year
      for token in ("學分班", "選修生", "休學", "境外生", "陸生", "僑生", "外籍生")
  ):
    return (
        "fail",
        (
            f"已填報 {degree}{f'（{year}）' if year else ''}；依北商大《申請資格與規定》與《交換生甄選作業辦法》，休學生、無正式學籍選讀生及境外學生不得申請出國交換計畫。"
        ),
    )
  is_grad = _is_graduate(degree)
  if is_grad and year in {"碩一上", "博一上", "研一上", "一年級上學期"}:
    return (
        "fail",
        (
            f"已填報 {degree}（{year}）；依北商大《申請資格與規定》，研究所（碩士班、博士班）須一年級下學期（含）以上始得申請，研究所一年級上學期不接受申請。"
        ),
    )
  if not is_grad and year in {
      "大一",
      "大一上",
      "大一下",
      "四技一",
      "四技一上",
      "四技一下",
      "二技一上",
      "五專一",
      "五專二",
      "五專三",
      "專一",
      "專二",
      "專三",
  }:
    return (
        "fail",
        (
            f"已填報 {degree}（{year}）；依北商大《申請資格與規定》，大學部四技須二年級（含）以上、二技須一年級下學期（含）以上、五專須四年級（含）以上；四技一年級、二技一年級上學期及五專一至三年級不接受申請。"
        ),
    )
  grad_note = (
      "（提醒：北商大研究所學生交換期間以一學期為限；且韓國光雲大學、韓國中央大學、加拿大麥迪森海特學院、希爾克學院不開放研究生申請，捷克理工大學馬薩里克高等研究所則限研究生申請）"
      if is_grad
      else "（提醒：德國凱撒斯勞斯滕應用科技大學限四技三年級含以上或二技一年級下學期含以上申請，專科部不得申請；捷克理工大學馬薩里克高等研究所限研究生申請）"
  )
  return (
      "pass",
      (
          f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合國立臺北商業大學出國交換學生甄選及雙聯學位計畫之在學學制與年級規定{grad_note}。"
      ),
  )


def ntub_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
  score_min = 80.0
  gpa_min = 3.3
  rank_max = 70.0
  xuehai_rank_max = 40.0
  details: list[str] = []
  passes_score = False
  passes_rank = False
  passes_xuehai = False

  if academic_score is not None:
    details.append(f"學業總平均 {academic_score:g} 分")
    if academic_score >= score_min:
      passes_score = True
      passes_xuehai = True
  if academic_gpa is not None:
    details.append(f"GPA {academic_gpa:g}")
    if academic_gpa >= gpa_min:
      passes_score = True
      passes_xuehai = True
  if class_rank_percent is not None:
    details.append(f"歷年平均班級名次前 {class_rank_percent:g}%")
    if class_rank_percent <= rank_max:
      passes_rank = True
    if class_rank_percent <= xuehai_rank_max:
      passes_xuehai = True

  summary = "、".join(details)
  if (
      academic_score is None
      and academic_gpa is None
      and class_rank_percent is None
  ):
    return (
        "needs_confirmation",
        (
            "尚未填寫學業總平均、GPA 或班級排名百分比；依北商大《申請資格與規定》與《學生申請交換生及雙聯學位生作業要點》：（1）前一學年每學期操行成績均須達 A（約 80 分）以上，且無小過以上處分；（2）歷年學業成績總平均須達 80 分以上，或歷年平均班級名次百分比在前 70% 以內；（3）若欲申請教育部《學海飛颺》獎助學金，在校學業總平均須達 80 分以上或歷年平均班級名次前 40% 以內。"
        ),
    )

  if passes_score or passes_rank:
    xuehai_note = (
        "同時符合教育部《學海飛颺》獎助學金學業門檻（總平均 80 分以上或歷年平均班級名次前 40% 以內）及《學海惜珠》／《王春滿清寒助學金》申請基準"
        if passes_xuehai
        else "符合北商大交換生甄選學業門檻（歷年平均班級名次前 70% 以內）；惟若欲申請教育部《學海飛颺》獎助學金，須達總平均 80 分以上或歷年平均班級名次前 40% 以內"
    )
    return (
        "pass",
        (
            f"已填報 {summary}；符合國立臺北商業大學交換生甄選學業標準（總平均 80 分以上或歷年平均班級名次百分比前 70% 以內，且前一學年每學期操行成績均為 A 以上；{xuehai_note}）。"
        ),
    )

  return (
      "fail",
      (
          f"已填報 {summary}；未達國立臺北商業大學《申請資格與規定》之學業門檻（歷年總平均須達 80 分以上，或歷年平均班級名次百分比在前 70% 以內）。"
      ),
  )


def ntub_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
  test = (language_test or "").strip().lower()
  if partner_country in {"中國大陸", "香港", "澳門"} and (
      not test or language_score is None
  ):
    return (
        "pass",
        (
            f"申請赴{partner_country}合作姊妹校（含吉林大學、南京大學、南開大學、北京科技大學、中南財經政法大學、東北大學、西北農林科技大學、北京師範大學、蘭州大學、蘇州大學、福州大學、首都經濟貿易大學等 36 所大陸地區姊妹校）免附外語檢定證明；若有外語檢定成績仍可依《外語成績積分對照表》列計書面審查外語能力積分（30%）。"
        ),
    )
  if not test or language_score is None:
    return (
        "needs_confirmation",
        (
            "尚未填寫外語檢定成績。依北商大《申請資格與規定》與《外語成績積分對照表》：（1）英語組姊妹校只接受 TOEFL iBT 或 IELTS 成績（不接受多益 TOEIC！），最低門檻為韓國天主教大學 TOEFL iBT 65 / IELTS 5.5、美國匹茲堡州立大學 iBT 68 / IELTS 6.0、一般英語授課姊妹校 iBT 73 / IELTS 5.5、荷蘭薩克森與海牙應科大／德國萊茵瓦爾應科大／捷克牛頓大學／法國雷恩商學院雙聯／澳洲雪梨科技大學雙聯 iBT 80 / IELTS 6.0、捷克理工大學馬薩里克高等研究所 iBT 87 / IELTS 6.5、美國舊金山州立大學 3+1+1 雙聯 iBT 88 / IELTS 6.5、德國萊茵瓦爾應科大研究生 iBT 100 / IELTS 6.5；（2）日語組姊妹校要求 JLPT N2 以上（新潟大學須同時具備 JLPT N2 及 TOEFL iBT 73 或 IELTS 5.5；小樽商科大學可擇一繳交）；（3）韓語組姊妹校要求 TOPIK 3 級以上或 TOEFL iBT 73 / IELTS 5.5；（4）大陸地區姊妹校免附外語檢定。"
        ),
    )
  if test in NTUB_ENGLISH_MINIMUMS:
    label, minimum = NTUB_ENGLISH_MINIMUMS[test]
    passed = language_score >= minimum
    adv_note = "符合韓國天主教大學英語組最低門檻（TOEFL iBT 65 / IELTS 5.5）"
    if (test == "toefl" and language_score >= 100) or (
        test == "ielts" and language_score >= 6.5
    ):
      adv_note = "符合北商大全部英語組交換與雙聯學位姊妹校最高標準（含德國萊茵瓦爾應用科技大學研究生 iBT 100 / IELTS 6.5、美國舊金山州立大學 3+1+1 雙聯 iBT 88 / IELTS 6.5、捷克理工大學馬薩里克高等研究所 iBT 87 / IELTS 6.5、荷蘭薩克森與海牙應科大／法國雷恩商學院／澳洲雪梨科技大學 iBT 80 / IELTS 6.0）及《學海飛颺》CEFR B2 門檻"
    elif (test == "toefl" and language_score >= 88) or (
        test == "ielts" and language_score >= 6.5
    ):
      adv_note = "符合美國舊金山州立大學 3+1+1 雙聯（iBT 88 / IELTS 6.5）、捷克理工大學馬薩里克高等研究所（iBT 87 / IELTS 6.5）及荷德法澳捷主流英語姊妹校（iBT 80 / IELTS 6.0），惟德國萊茵瓦爾應科大研究生要求 TOEFL iBT 100 或 IELTS 6.5"
    elif (test == "toefl" and language_score >= 80) or (
        test == "ielts" and language_score >= 6.0
    ):
      adv_note = "符合荷蘭薩克森應科大、海牙應科大、德國萊茵瓦爾應科大（大學部）、捷克牛頓大學、法國雷恩商學院雙聯、澳洲雪梨科技大學雙聯（TOEFL iBT 80 / IELTS 6.0）及《學海飛颺》CEFR B2 門檻，以及美加德奧捷日韓一般英語組姊妹校（iBT 73 / IELTS 5.5）"
    elif (test == "toefl" and language_score >= 73) or (
        test == "ielts" and language_score >= 5.5
    ):
      adv_note = "符合北商大一般英語組姊妹校標準（TOEFL iBT 73 / IELTS 5.5，含加拿大麥迪森海特學院、希爾克學院、德國凱撒斯勞斯滕應科大、巴登符騰堡雙元制大學、奧地利庫夫シュ泰因應科大、捷克奧스트拉瓦大學、日本小樽商科大學、韓國慶北／光雲／全北／東亞／中央／翰林大學、泰國清邁大學等）"
    elif test == "toefl" and language_score >= 68:
      adv_note = "符合美國匹茲堡州立大學交換門檻（TOEFL iBT 68）與韓國天主教大學門檻（TOEFL iBT 65）；一般英語組姊妹校要求 TOEFL iBT 73 以上"
    return (
        "pass" if passed else "fail",
        (
            f"{label} {language_score:g} {'符合' if passed else '未達'}國立臺北商業大學英語組交換與雙聯計畫外語基準（最低門檻：{label} {minimum:g}；{adv_note}）。"
        ),
    )
  if test == "toeic":
    if partner_country in {"中國大陸", "香港", "澳門"}:
      return (
          "pass",
          (
              f"TOEIC {language_score:g}：申請赴{partner_country}姊妹校免附外語檢定，且多益成績可依北商大《外語成績積分對照表》換算書面審查外語能力積分（30%，如 TOEIC 550 折算 60 分、785 折算 80 分、945 折算 95 分）。"
          ),
      )
    return (
        "fail",
        (
            f"已填報 TOEIC {language_score:g}；依北商大《申請資格與規定》明文規定：「英語組姊妹校只接受托福（TOEFL iBT）或雅思（IELTS）成績，不接受多益（TOEIC）成績！（日語組及韓語組亦同）」。多益成績僅可作為大陸地區姊妹校書面審查外語積分（30%）或雙聯學位個別採認項目。"
        ),
    )
  if test == "jlpt":
    level = int(language_score)
    passed = level in (1, 2)
    tier_note = (
        "符合日本千葉商科大學、小樽商科大學、人間環境大學、亞細亞大學等日語組姊妹校 JLPT N2 以上門檻及《學海飛颺》CEFR B2（JLPT N2）基準（提醒：日本新潟大學要求同時具備 JLPT N2 及 TOEFL iBT 73 或 IELTS 5.5）"
        if passed
        else "北商大日語組姊妹校及《學海飛颺》赴日獎助均要求 JLPT N2（含）以上"
    )
    return (
        "pass" if passed else "fail",
        f"JLPT N{level} {'符合' if passed else '未達'}國立臺北商業大學日語組姊妹校檢定要求（{tier_note}）。",
    )
  if test == "topik":
    level = int(language_score)
    passed = 3 <= level <= 6
    bonus_note = (
        "符合韓國慶北大學、光雲大學、全北大學、東亞大學等韓語組姊妹校 TOPIK 3 級以上門檻（光雲大學及東亞大學韓語授課建議或要求 TOPIK 3–4 級；韓國中央大學、天主教大學、翰林大學則採認英語組 TOEFL iBT / IELTS 成績）"
        if passed
        else "北商大韓語組姊妹校要求 TOPIK 3 級（含）以上（或改以 TOEFL iBT 73 / IELTS 5.5 申請英語組）"
    )
    return (
        "pass" if passed else "fail",
        f"TOPIK {level} 級{'符合' if passed else '未達'}國立臺北商業大學韓語組姊妹校檢定基準（{bonus_note}）。",
    )
  return (
      "needs_confirmation",
      f"已填報語言檢定 {language_test}（{language_score:g}）；請對照北商大《申請資格與規定》及《外語成績積分對照表》確認是否符合目標姊妹校指定語組標準（英語組僅採認 TOEFL iBT 或 IELTS）。",
  )
