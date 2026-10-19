from __future__ import annotations

import math
import re

from .university_registry import WZU, resolve_university

WZU_OICC_HUB_URL = "https://c015.wzu.edu.tw/"
WZU_IED_HUB_URL = "https://d020.wzu.edu.tw/"
WZU_OUTBOUND_GUIDE_URL = "https://d020.wzu.edu.tw/article/492285"
WZU_R1_ANNOUNCEMENT_URL = "https://d020.wzu.edu.tw/article/529152"
WZU_R2_ANNOUNCEMENT_URL = "https://d020.wzu.edu.tw/article/529354"
WZU_R1_115_1_ANNOUNCEMENT_URL = "https://d020.wzu.edu.tw/article/524735"
WZU_PARTNER_INFO_URL = "https://d020.wzu.edu.tw/category/154399"
WZU_EXP_ALBUM_URL = "https://d020.wzu.edu.tw/album/list/152198"
WZU_UMAP_URL = "https://d020.wzu.edu.tw/article/517638"
WZU_ACUCA_URL = "https://d020.wzu.edu.tw/article/517642"
WZU_SCHOLARSHIP_HUB_URL = "https://d020.wzu.edu.tw/category/152197"
WZU_REGULATIONS_URL = "https://d020.wzu.edu.tw/category/152182"
WZU_SOSA_URL = "https://d020.wzu.edu.tw/category/152202"

WZU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 60.0),
    "ielts": ("IELTS", 5.0),
    "toeic": ("TOEIC", 550.0),
}


def is_wzu(school_name: str | None) -> bool:
  school = resolve_university(school_name)
  if school is not None and school.id == WZU.id:
    return True
  normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
  return normalized in {
      "文藻外語大學",
      "文藻外語學院",
      "文藻外大",
      "文藻",
      "wzu",
      "wenzao",
      "wenzao ursuline university of languages",
  }


def _is_graduate(degree_level: str | None) -> bool:
  text = (degree_level or "").strip()
  return any(token in text for token in ("碩", "博", "研究"))


def wzu_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
  degree = (degree_level or "").strip()
  year = (current_year or "").strip()
  if not degree:
    return (
        "needs_confirmation",
        (
            "尚未提供目前學制與年級；《文藻外語大學學生出國交換實施辦法》及甄選簡章規定：申請人須為本校日間部及進修部正式在學學生（出國交換期間須為五專部四年級下學期至五年級、四技部二年級下學期至四年級、二技部三年級下學期至四年級或研究所碩士班一年級下學期至四年級）。"
        ),
    )
  if any(token in degree for token in ("在職", "學分班", "休學")):
    return (
        "needs_confirmation",
        f"已填報 {degree}；《文藻外語大學學生出國交換實施辦法》以日間部及進修部正式學位生為主，在職專班或特殊學制請先向國際暨兩岸合作處（國際交流組）確認是否適用當期交換簡章。",
    )
  is_grad = _is_graduate(degree)
  if not is_grad and year in {"一年級", "大一", "1", "專一", "專二", "專三"}:
    return (
        "fail",
        (
            f"已填報 {degree}（{year}）；依《文藻外語大學學生出國交換實施辦法》及出國交換生甄選簡章規定，出國交換期間五專部須達四年級下學期至五年級、四技部須達二年級下學期至四年級，目前年級尚未符合申請門檻。"
        ),
    )
  return (
      "pass",
      f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合文藻外語大學出國交換學生學制與年級規定（出國交換期間須維持文藻在學學籍並完成註冊繳交全額學雜費，延畢生出國期間亦須繳交全額學雜費）。",
  )


def wzu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
  details: list[str] = []
  truncated_score: int | None = None
  general_ok = False
  lang_group_ok = False

  if academic_score is not None:
    truncated_score = math.floor(academic_score)
    details.append(
        f"歷年學業總平均 {academic_score:g} 分（依簡章認列至個位數為 {truncated_score} 分）"
    )
    if truncated_score >= 70:
      general_ok = True
      lang_group_ok = True
    elif truncated_score >= 65:
      lang_group_ok = True
  if academic_gpa is not None:
    details.append(f"GPA {academic_gpa:g}")
    if academic_gpa >= 2.7:
      general_ok = True
      lang_group_ok = True
    elif academic_gpa >= 2.3:
      lang_group_ok = True
  if class_rank_percent is not None:
    details.append(f"班/系排名前 {class_rank_percent:g}%")

  summary = "、".join(details)
  if (
      academic_score is None
      and academic_gpa is None
      and class_rank_percent is None
  ):
    return (
        "needs_confirmation",
        (
            "尚未填寫歷年學業平均成績；文藻外語大學出國交換生甄選簡章規定：（1）一般組（140 校）：歷年學業總平均須達 70"
            " 分（含）以上、操行總平均達 80 分（含）以上且無小過以上紀錄；（2）語言學習組（7 所自費語言中心）：歷年學業總平均須達 65"
            " 分（含）以上、操行總平均達 80"
            " 分（含）以上（分數皆認列至個位數，小數點後不採計亦不四捨五入；教育部學海飛颺與學海惜珠須達學業總平均 75 分以上）。"
        ),
    )

  if general_ok:
    xuehai_note = (
        "同時符合教育部學海飛颺／學海惜珠學業門檻（75 分以上，學海惜珠文藻另加碼 20% 配合款）及文藻出國交換獎助學金資格"
        if (truncated_score is not None and truncated_score >= 75)
        else (
            "符合文藻出國交換獎助學金資格（五專／四技／碩士 1 萬、二技及五專直升四技最高 5 萬）；若欲申請教育部學海飛颺或學海惜珠須達歷年學業總平均"
            " 75 分以上"
        )
    )
    return (
        "pass",
        (
            f"已填報 {summary}；符合文藻外語大學「一般組（70 分以上）」及「語言學習組（65 分以上）」學業成績門檻（一般組甄選資格涵蓋語言學習組，可於撕榜時優先跨選；{xuehai_note}；另請確認歷年操行成績總平均達"
            " 80 分以上且無小過以上紀錄，上海外國語大學等少數姊妹校另要求學業平均達 80 分）。"
        ),
    )

  if lang_group_ok:
    return (
        "needs_confirmation",
        (
            f"已填報 {summary}；達文藻外語大學「語言學習組（歷年學業總平均 65 分以上・共 7 所自費語言中心：美國加州大學爾灣分校推廣教育學院、法國昂熱"
            " CIDEF、法國維琪卡維蘭 CAVILAM、奧地利維也納大學語言中心、西班牙薩拉曼卡／巴塞隆納自治大學／卡斯提亞拉曼查語言中心）」報考門檻，惟未達「一般組（70"
            " 分以上，認列至個位數不四捨五入）」門檻。"
        ),
    )

  return (
      "fail",
      (
          f"已填報 {summary}；未達文藻外語大學出國交換最低學業成績標準（一般組須達歷年總平均 70 分以上、語言學習組須達 65"
          " 分以上，認列至個位數，小數點後不採計亦不四捨五入）。"
      ),
  )


def wzu_language_check(
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
            "申請赴中國大陸 10 所姊妹校（北京外大、上海外大、中國傳媒、中央民族、大連外大、廣東外語外貿、西南財大等）免附外語檢定證明（惟第一階段書審仍採計英語能力"
            " 10% 與第二外語能力 10% 配分，建議檢附語檢證書以提升書審總分）。"
        ),
    )
  if not test or language_score is None:
    return (
        "needs_confirmation",
        (
            "尚未填寫外語檢定成績。文藻外語大學出國交換第一階段書審（50%）同時採計「英語能力檢定（10%）」與「第二外語能力檢定（10%）」：（1）英語組（40"
            " 校）接受 TOEFL iBT（60–88）、IELTS（5.0–6.5）、TOEIC（550–800）或全民英檢／CSEPT；（2）日語組（31"
            " 校）要求 JLPT N1–N4；（3）法語組（24 校）要求 DELF/TCF A2–B2；（4）德語組（9 校）要求德語"
            " B1–B2；（5）西語組（14 校）要求 DELE/SIELE A2–B2；（6）華語暨東南亞語組要求 TOPIK 2–4"
            " 級或英語／東南亞語檢定。"
        ),
    )
  if test in WZU_ENGLISH_MINIMUMS:
    label, minimum = WZU_ENGLISH_MINIMUMS[test]
    passed = language_score >= minimum
    return (
        "pass" if passed else "fail",
        f"{label} {language_score:g} {'符合' if passed else '未達'}文藻外語大學英語組及東南亞／歐洲全英授課姊妹校基本英語門檻（{minimum:g}；注意英美加歐部分姊妹校要求 TOEFL iBT 79–88、IELTS 6.0–6.5 或 TOEIC 700–790，請對照各校名額表規定）。",
    )
  if test == "jlpt":
    passed = 1.0 <= language_score <= 4.0
    level = int(language_score)
    tier_note = (
        "符合立教、明治學院、立命館、創價、名古屋市立等 N1 要求及所有 N2–N4 日本姊妹校門檻"
        if level == 1
        else (
            "符合京都外大、名古屋外大（月領 6 萬日圓獎學金）、東洋（IUEP 月領 5.1 萬日圓）、清泉（月領 4 萬日圓）、關西外大、桃山學院、金城學院、拓殖等大多數日本姊妹校 N2 門檻"
            if level == 2
            else (
                "符合名古屋外大（N3）、清泉大學（N3 月領 2 萬日圓）、鹿兒島純心大學（N3 月領 3 萬日圓）、長崎外國語大學、文教大學、神田外語大學別科等 N3 姊妹校門檻"
                if level == 3
                else (
                    "符合長崎純心大學、志學館大學、沖繩基督教學院大學或日本姊妹校別科／語言課程之 N4 門檻（多數日本學部交換課程須達 N2–N3 以上）"
                )
            )
        )
    )
    return (
        "pass" if passed else "fail",
        f"JLPT N{level} {'符合' if passed else '未達'}文藻外語大學日語組（31 所日本姊妹校）日語檢定門檻（{tier_note}）。",
    )
  if test == "topik":
    passed = 1.0 <= language_score <= 6.0
    return (
        "pass" if passed else "fail",
        f"TOPIK {int(language_score)} 級 {'符合' if passed else '未達'}文藻外語大學華語暨東南亞語組／英語組赴韓國 10 所姊妹校（崇實、漢陽 ERICA、誠信女大、釜山外大、釜山天主教、大邱韓醫、忠北、翰林、順天鄉、天安外大）韓語檢定採計標準。",
    )
  return (
      "needs_confirmation",
      (
          f"已填寫 {language_test} {language_score:g}；請對照《文藻外語大學出國交換生甄選學校名額一覽表》（{WZU_R2_ANNOUNCEMENT_URL}：支援法語"
          " DELF/TCF A2–B2、德語 TestDaF/Goethe B1–B2、西語 DELE/SIELE A2–B2、全民英檢、CSEPT"
          " 及越／印／泰語檢定）確認是否符合志願姊妹校規定。"
      ),
  )
