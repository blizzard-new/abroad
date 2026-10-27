from __future__ import annotations

import hashlib
import io
import re
from datetime import datetime, timezone
from pathlib import Path

import requests
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from .models import (
    ApplicationPeriodAudience,
    ApplicationPeriodDateStatus,
    ApplicationPeriodItem,
    ApplicationPeriodStatus,
    Attachment,
    ExchangeInfo,
    PageCategory,
    PartnerStudentSummary,
    PartnerUniversity,
    ProcessedPage,
    RuleExplanation,
    SourceReference,
    StudentDashboard,
    StudentInfoItem,
)
from .student_view import TAIPEI_TIMEZONE, _application_period_status, _merge_partner_universities
from .partner_localization import contains_english_prose, localize_points


NTPU_OIA_URL = "https://new.ntpu.edu.tw/oia"
NTPU_FILES_URL = "https://new.ntpu.edu.tw/oia/files"
NTPU_SISTER_SCHOOL_URL = "https://new.ntpu.edu.tw/oia/sister-school"
NTPU_CURRENT_SISTER_SCHOOLS_URL = "https://new.ntpu.edu.tw/oia/sister-schools"
NTPU_115_ANNOUNCEMENT_URL = "https://new.ntpu.edu.tw/news/68d5e81963f5a608851f74c1"
NTPU_115_GUIDELINES_URL = (
    "https://cms-carrier.ntpu.edu.tw/uploads/"
    "2026_2027_Academic_Year_Outbound_Exchange_Program_Guidelines_1e5870e83d.pdf"
)
NTPU_115_ENGLISH_PARTNERS_URL = (
    "https://cms-carrier.ntpu.edu.tw/uploads/115_1003_f908ed3fae.pdf"
)
NTPU_115_JAPANESE_PARTNERS_URL = (
    "https://cms-carrier.ntpu.edu.tw/uploads/115_da8ac19670.pdf"
)
NTPU_115_CHINESE_PARTNERS_URL = (
    "https://cms-carrier.ntpu.edu.tw/uploads/115_1014_dd8dc7eafd.pdf"
)
NTPU_115_SCHOLARSHIP_URL = (
    "https://new.ntpu.edu.tw/oia/news/69a65f4263f5a608851fb013/"
    "%E3%80%90%E5%BB%B6%E9%95%B7%E7%94%B3%E8%AB%8B%E5%85%AC%E5%91%8A%E3%80%91"
    "115%E5%AD%B8%E5%B9%B4%E5%BA%A6%E3%80%8C%E5%AD%B8%E6%B5%B7%E9%A3%9B%E9%A2%BA"
    "%E6%83%9C%E7%8F%A0%E3%80%8D%E7%8D%8E%E5%AD%B8%E9%87%91%E5%BB%B6%E9%95%B7"
    "%E5%8F%97%E7%90%86%E8%87%B3115%E5%B9%B43%E6%9C%886%E6%97%A5%E4%BA%9417%3A00%EF%BC%81"
)
NTPU_SOURCE_CHECKED_AT = datetime(2026, 7, 27, tzinfo=timezone.utc)
NTPU_116_ANNOUNCEMENT_URL = (
    "https://new.ntpu.edu.tw/oia/news/6ab396bf7085cb4f0c81831f"
)
NTPU_116_GUIDELINES_URL = "https://cms-carrier.ntpu.edu.tw/uploads/116_16e535159d.pdf"
NTPU_116_GUIDELINES_EN_URL = (
    "https://cms-carrier.ntpu.edu.tw/uploads/"
    "Guidelines_for_the_Selection_of_Outbound_Exchange_Students_for_Academic_Year_2027_4dc2483feb.pdf"
)
NTPU_116_ENGLISH_PARTNERS_URL = "https://cms-carrier.ntpu.edu.tw/uploads/116_0924_da1dafe9d0.pdf"
NTPU_116_JAPANESE_PARTNERS_URL = "https://cms-carrier.ntpu.edu.tw/uploads/116_26b28374db.pdf"
NTPU_116_CHINESE_PARTNERS_URL = "https://cms-carrier.ntpu.edu.tw/uploads/116_6524fec218.pdf"
NTPU_MOE_SCHOLARSHIP_AMENDMENT_URL = (
    "https://new.ntpu.edu.tw/oia/news/6ad986a07085cb4f0c818c5e"
)
NTPU_MOE_SCHOLARSHIP_AMENDMENT_PDF_URL = (
    "https://cms-carrier.ntpu.edu.tw/uploads/1151021_c627bfee0e.pdf"
)
NTPU_MOE_SCHOLARSHIP_DIFF_PDF_URL = (
    "https://cms-carrier.ntpu.edu.tw/uploads/1151015_9e06704aa6.pdf"
)
NTPU_EFREI_INFO_SESSION_URL = (
    "https://new.ntpu.edu.tw/oia/news/6acc5d0d7085cb4f0c818840"
)
NTPU_LAW_COLLEGE_EXCHANGE_URL = "https://www.law.ntpu.edu.tw/news/j1p0rQCYhCHb"
NTPU_SCHOOL_PREVIEW_BULLETIN_URL = (
    "https://bulletin.ntpu.edu.tw/bulletin_content.php?no=20260707133939366861"
)
NTPU_116_CHECKED_AT = datetime(2026, 10, 27, tzinfo=timezone.utc)


NTPU_OFFICIAL_DATA_DIR = Path(__file__).resolve().parent / "official_data" / "ntpu"


# The current cycle's quota sheets. The 115 sheets stay bundled for history.
PARTNER_PDFS = (
    ("英語組", NTPU_116_ENGLISH_PARTNERS_URL, 133, "116-english-partners.pdf"),
    ("日語組", NTPU_116_JAPANESE_PARTNERS_URL, 16, "116-japanese-partners.pdf"),
    ("中文組", NTPU_116_CHINESE_PARTNERS_URL, 21, "116-chinese-partners.pdf"),
)


# The quota sheets list the schools that students may apply to in that cycle.
# NTPU's sister-school database (updated 2026-07-03) also lists the following
# student-exchange agreements, but those schools do not appear in the 116
# quota sheets.  Keep them visible without presenting them as open choices.
# (Eleven agreements that appeared here for 115 now have 116 quotas.)
NTPU_EXCHANGE_AGREEMENTS_WITHOUT_QUOTA = (
    ("大陸地區", "山東大學", "學術交流、學生交換", "校級"),
    ("大陸地區", "北京科技大學", "學術交流、學生交換", "校級"),
    ("大陸地區", "西南政法大學", "學術交流、學生交換", "校級"),
    ("大陸地區", "東華理工大學", "學術交流、學生交換", "校級"),
    ("大陸地區", "華東政法大學", "學術交流、學生交換", "院級"),
    ("大陸地區", "暨南大學", "學術交流、學生交換", "校級"),
    ("大陸地區", "蘭州大學", "學術交流、學生交換", "校級"),
    ("日本", "大阪大學法學研究科、法學部、大學院高等司法研究科暨大學院國際公共政策研究科", "學術交流、學生交換", "院級"),
    ("日本", "日本信州大學經法學部", "學術交流、學生交換", "院級"),
    ("日本", "東北大學", "學術交流、學生交換", "院級"),
    ("日本", "金澤大學", "學術交流、學生交換", "院級"),
    ("韓國", "梨花女子大學", "學術交流、學生交換", "校級"),
    ("越南", "越南融促大學", "學術交流、學生交換", "校級"),
    ("越南", "芹苴大學－經濟學院", "學術交流、學生交換", "校級／院級"),
    ("泰國", "泰國東方大學", "學術交流、學生交換", "校級"),
    ("泰國", "泰國清邁大學", "學術交流、學生交換", "校級"),
    ("印度", "印度吉特卡拉大學", "學術交流、學生交換", "校級"),
    ("印度", "印度阿努拉格大學", "學術交流、學生交換", "校級"),
    ("印度", "卡倫亞技術與科學研究所", "學術交流、學生交換", "校級"),
    ("印尼", "印尼迪安努斯萬托羅大學", "學術交流、學生交換", "校級"),
    ("菲律賓", "黎剎系統大學", "學生交換", "校級"),
    ("香港", "香港理工大學", "學術交流、學生交換", "系級"),
    ("美國", "北愛荷華大學", "學術交流、學生交換", "校級"),
    ("美國", "密蘇里大學藝術與科學學院", "學術交流、學生交換", "院級／系級"),
    ("美國", "新墨西哥州立大學", "學生交換", "校級"),
    ("加拿大", "勞倫森大學", "學術交流、學生交換", "院級"),
    ("加拿大", "英屬哥倫比亞大學", "學術交流、學生交換", "校級"),
    ("巴西", "高等廣告與行銷學院", "學術交流、學生交換", "校級"),
    ("羅馬尼亞", "奧維第烏斯大學", "學術交流、學生交換", "校級"),
    ("羅馬尼亞", "蒂米什拉西部大學", "師生交換", "校級"),
    ("波蘭", "格但斯克科技大學", "學術交流、學生交換", "校級"),
    ("德國", "明斯特大學", "學術交流、學生交換", "院級"),
    ("法國", "女性高等綜合理工學院", "學生交換", "校級"),
    ("挪威", "奧斯陸大學（犯罪學與社會學法系）", "學術交流、學生交換", "校級"),
    ("土耳其", "阿提巴斯大學", "學術交流、學生交換", "校級"),
    ("土耳其", "埃斯基謝希爾技術大學", "學術交流、學生交換", "校級"),
    ("摩洛哥", "卡薩布蘭卡管理學院", "學術交流、學生交換", "校級"),
)


NTPU_EXCHANGE_AGREEMENTS_WITHOUT_115_QUOTA = NTPU_EXCHANGE_AGREEMENTS_WITHOUT_QUOTA  # backward-compatible name


COUNTRY_PREFIXES = (
    (r"柬埔寨(?:\s*Cambodia)?", "柬埔寨"),
    (r"匈牙利(?:\s*Hungary)?", "匈牙利"),
    (r"馬來西亞\s*Malaysia", "馬來西亞"),
    (r"新加坡\s*Singapore", "新加坡"),
    (r"哈薩克\s*Republic\s*of\s*Kazakhstan", "哈薩克"),
    (r"阿爾巴尼亞\s*Republic\s*of\s*Albania", "阿爾巴尼亞"),
    (r"孟加拉\s*People'?s\s*Republic\s*of\s*Bangladesh", "孟加拉"),
    (r"羅馬尼亞\s*Romania", "羅馬尼亞"),
    (r"斯洛伐克\s*(?:Slovania|Slovakia)", "斯洛伐克"),
    (r"立陶宛\s*Lithuania", "立陶宛"),
    (r"瑞士\s*Switzerland", "瑞士"),
    (r"荷蘭\s*Netherlands", "荷蘭"),
    (r"菲律賓\s*Philippines", "菲律賓"),
    (r"香港\s*Hong\s*Kong", "香港"),
    (r"日本\s*Japan", "日本"),
    (r"韓國\s*Korea", "韓國"),
    (r"越南\s*Vietnam", "越南"),
    (r"泰國\s*Thailand", "泰國"),
    (r"緬甸\s*Myanmar", "緬甸"),
    (r"印尼\s*Indonesia", "印尼"),
    (r"加拿大(?:\s*Canada)?", "加拿大"),
    (r"美國\s*America", "美國"),
    (r"英國\s*U\.?K", "英國"),
    (r"捷克\s*Czech(?:\s*Republic)?", "捷克"),
    (r"奧地利\s*Austria", "奧地利"),
    (r"義大利\s*Italia", "義大利"),
    (r"波蘭\s*Poland", "波蘭"),
    (r"法國\s*France", "法國"),
    (r"瑞典\s*Sweden", "瑞典"),
    (r"挪威\s*Norway", "挪威"),
    (r"土耳其\s*Turkey", "土耳其"),
    (r"西班牙\s*Spain", "西班牙"),
    (r"德國\s*Germany", "德國"),
    (r"比利時\s*Belgium", "比利時"),
    (r"俄羅斯\s*Russia", "俄羅斯"),
    (r"拉脫維亞\s*Latvia", "拉脫維亞"),
    (r"印度\s*India", "印度"),
    (r"蒙古\s*Mongolia", "蒙古"),
    (r"大陸地區", "大陸地區"),
    (r"日本", "日本"),
)


FALLBACK_PARTNERS = (
    ("英語組", "日本", "關西學院大學 Kwansei Gakuin University"),
    ("英語組", "日本", "佐賀大學 Saga University"),
    ("英語組", "韓國", "蔚山科技大學 Ulsan National Institute of Science and Technology"),
    ("英語組", "韓國", "漢陽大學 ERICA Hanyang University ERICA"),
    ("英語組", "泰國", "法政大學 Thammasat University"),
    ("英語組", "新加坡", "新加坡社科大學 Singapore University of Social Sciences"),
    ("英語組", "美國", "天普大學 Temple University"),
    ("英語組", "英國", "愛丁堡大學 The University of Edinburgh"),
    ("英語組", "法國", "諾歐商學院 NEOMA Business School"),
    ("英語組", "法國", "歐洲知識經濟與管理學院 SKEMA Business School"),
    ("英語組", "德國", "漢堡商學院 HSBA Hamburg School of Business Administration"),
    ("英語組", "香港", "香港城市大學人文社會科學院 College of Liberal Arts and Social Sciences, City University of Hong Kong"),
    ("日語組", "日本", "一橋大學 Hitotsubashi University"),
    ("日語組", "日本", "明治大學 Meiji University"),
    ("日語組", "日本", "中央大學 Chuo University"),
    ("日語組", "日本", "筑波大學 The University of Tsukuba"),
    ("中文組", "大陸地區", "上海財經大學"),
    ("中文組", "大陸地區", "中國人民大學"),
    ("中文組", "大陸地區", "武漢大學"),
    ("中文組", "大陸地區", "南京大學"),
)


def _compact(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _row_positions(text: str, row_count: int) -> list[tuple[int, int, int]]:
    positions: list[tuple[int, int, int]] = []
    cursor = 0
    for number in range(1, row_count + 1):
        match = re.search(rf"(?m)^{number}\s+", text[cursor:])
        if match is None:
            continue
        start = cursor + match.start()
        body_start = cursor + match.end()
        positions.append((number, start, body_start))
        cursor = body_start
    return positions


def _country_and_body(block: str, language_group: str) -> tuple[str, str]:
    compact = _compact(block)
    if language_group == "中文組":
        return "大陸地區", re.sub(r"^大陸地區\s*", "", compact)
    for pattern, country in COUNTRY_PREFIXES:
        match = re.match(pattern, compact, re.IGNORECASE)
        if match:
            return country, compact[match.end() :].strip()
    return ("日本", compact) if language_group == "日語組" else ("未標示", compact)


def _school_name(body: str, language_group: str) -> str:
    if language_group == "中文組":
        before_group = re.split(r"\s+中文組\s+", body, maxsplit=1)[0]
        locations = (
            "上海市", "天津市", "北京市", "重慶市", "山東省濟南市", "黑龍江省哈爾濱市",
            "湖北省武漢市", "吉林省長春市", "四川省成都市", "江蘇省南京市", "陝西省西安市",
            "福建省廈門市",
        )
        for location in locations:
            flexible_location = r"\s*".join(re.escape(char) for char in location)
            before_group = re.sub(rf"\s+{flexible_location}$", "", before_group)
        return re.sub(r"\s+", "", before_group.strip(" ，,"))

    marker = re.search(
        r"\s+(?=(?:限|具備|建議|相當於|主修|須為主修|僅|日本語能力試驗|"
        r"TOEFL|IELTS|多益\s*[\(（]?TOEIC|To study in English|"
        r"大學(?:部)?\s*[:：]|學士\s*[:：]|碩士\s*[:：]|英語\s*track\s*[:：]|"
        r"大三以上|課程以西班牙語為主|法律、商管|選修非語言課程|"
        r"\d+\.[A-Z]|無(?:\s+(?:無|\d|日本語|建議|大學|英語|具備)|$)))",
        body,
        re.IGNORECASE,
    )
    candidate = body[: marker.start()] if marker else body
    candidate = re.sub(r"\s+", " ", candidate).strip(" ，,")
    candidate = candidate.replace("（", "(").replace("）", ")")
    if len(candidate) > 220:
        candidate = candidate[:220].rsplit(" ", 1)[0]
    if candidate.count("(") > candidate.count(")"):
        candidate += ")" * (candidate.count("(") - candidate.count(")"))
    return candidate


def _partner_from_block(
    block: str,
    *,
    language_group: str,
    source_url: str,
) -> PartnerUniversity | None:
    country, body = _country_and_body(block, language_group)
    school_name = _school_name(body, language_group)
    if len(school_name) < 2:
        return None
    details = _compact(body[len(school_name) :])
    period_match = re.search(
        r"(?<!第)(?:(?:1|一)學期(?:\s*(?:或|/|／)\s*(?:1|一)學?年)?|(?:1|一)學年)",
        details,
    )
    study_period = period_match.group(0) if period_match else "依當期名額表"
    if language_group == "中文組":
        zh_quota_match = re.search(r"中文組\s+(\d{1,2})\b", details)
        quota_matches = [zh_quota_match.group(1)] if zh_quota_match else []
    else:
        quota_matches = re.findall(
            r"\b(\d{1,2})(?:\s*\([^)]*\))?\s+(?=(?<!第)(?:1|一)學(?:期|年))",
            details,
        )
    if quota_matches:
        quota = f"{quota_matches[-1]} 名上限"
    elif "自費訪問生" in details or re.search(
        r"(?:^|\s)-\s+(?=(?<!第)(?:1|一)學(?:期|年))", details
    ):
        quota = "無免學費交換名額（自費訪問／依簡章備註）"
    else:
        quota = "當期名額表未列明人數；請洽臺北大學國際處確認。"
    if re.search(
        r"限大學部|限學士(?:生|班)|undergraduate students only|restricted to\s*undergraduate students",
        details,
        re.IGNORECASE,
    ):
        degree_levels = "大學部"
    elif re.search(r"研究生|碩士|master|doctoral", details, re.IGNORECASE):
        degree_levels = "大學部、研究所"
    else:
        degree_levels = "大學部、研究所（依合作校規定）"
    college_match = re.search(
        r"(?<![只申請資格])限(?!學習領域)([^。；\n()（）]{2,40}?(?:學院|學系|系|院|領域))(?:學生|學士生|申請)?",
        details,
    )
    colleges = college_match.group(1).strip(" ：:，,") if college_match else "依合作校規定"
    eligibility = details[:1200] or "申請資格、語言與名額依 116 學年度官方名額表。"
    return PartnerUniversity(
        program_type=f"交換學生（{language_group}）",
        country=country,
        school_name=school_name,
        colleges=colleges,
        degree_levels=degree_levels,
        study_period=study_period,
        quota=quota,
        eligibility=eligibility,
        application_deadline="116 學年度校內申請 2026/10/01–10/23 17:00（國際處公告）；之後梯次以當期公告為準。",
        application_info="同一梯次擇一語組，最多填列 5 個志願；通過校內甄選後仍須經合作校審查。",
        tuition_info="交換期間須保留臺北大學學籍並依規定繳費；合作校學費是否免繳以個別協議為準。",
        source_url=source_url,
        student_summary_zh=PartnerStudentSummary(
            study_period=study_period,
            application_deadline="每年 10 月或 4 月受理，依當期公告。",
            eligibility_points=localize_points(eligibility),
            translated_from_english=contains_english_prose(eligibility),
            application_steps=["校內線上申請與文件上傳", "書審與語組面試", "依總成績及志願分發", "合作校複審"],
            tuition_points=["交換期間須保留臺北大學學籍", "住宿、生活、保險與交通費由學生負擔"],
        ),
    )


def parse_ntpu_partner_pdf(
    text: str,
    *,
    language_group: str,
    source_url: str,
    row_count: int,
) -> list[PartnerUniversity]:
    positions = _row_positions(text, row_count)
    rows: list[PartnerUniversity] = []
    for index, (_, _, body_start) in enumerate(positions):
        end = positions[index + 1][1] if index + 1 < len(positions) else len(text)
        block = text[body_start:end]
        for marker in (
            "\n序號 國別",
            "\n116學年度交換學校資訊一覽表",
            "\n注意事項:",
            "\n重要留意事項",
            "\n註:",
        ):
            if marker in block:
                block = block.split(marker, 1)[0]
        partner = _partner_from_block(
            block,
            language_group=language_group,
            source_url=source_url,
        )
        if partner:
            rows.append(partner)
    return rows


def _fallback_partner_universities() -> list[PartnerUniversity]:
    source_by_group = {
        "英語組": NTPU_116_ENGLISH_PARTNERS_URL,
        "日語組": NTPU_116_JAPANESE_PARTNERS_URL,
        "中文組": NTPU_116_CHINESE_PARTNERS_URL,
    }
    return [
        PartnerUniversity(
            program_type=f"交換學生（{group}）",
            country=country,
            school_name=school_name,
            colleges="依合作校規定",
            degree_levels="大學部、研究所（依合作校規定）",
            study_period="1 學期或 1 學年（依名額表）",
            eligibility="離線備援摘要；請開啟官方 116 學年度名額表核對資格、語言與名額。",
            application_deadline="校內甄選原則於每年 10 月或 4 月受理；以當期公告為準。",
            application_info="同一梯次擇一語組，最多填列 5 個志願。",
            tuition_info="交換期間須保留臺北大學學籍並依規定繳費。",
            source_url=source_by_group[group],
        )
        for group, country, school_name in FALLBACK_PARTNERS
    ]


def _agreement_only_partner_universities() -> list[PartnerUniversity]:
    availability_note = (
        "臺北大學現行合作學校資料庫列有學生交換合約，但未列入 116 學年度交換名額表；"
        "是否開放、名額與資格須以當期赴外交換簡章為準。"
    )
    return [
        PartnerUniversity(
                program_type="交換合作協議",
            availability_status="agreement_only",
            availability_note=availability_note,
            agreement_type=agreement_type,
            agreement_level=agreement_level,
            country=country,
            school_name=school_name,
            colleges=agreement_level,
                degree_levels="待當期簡章確認",
            study_period="本期未公告",
            quota="本期未開放交換名額",
            eligibility=availability_note,
            application_deadline="目前未列入 116 學年度交換名額表；請留意下一期公告。",
            application_info=(
                "這是合作關係備查資料，不代表目前可直接申請；"
                "請先確認臺北大學國際事務處最新赴外交換名額表。"
            ),
            tuition_info="學費、減免與其他費用須以未來當期簡章及合作校公告為準。",
            source_url=NTPU_CURRENT_SISTER_SCHOOLS_URL,
            student_summary_zh=PartnerStudentSummary(
                study_period="本期未公告",
                application_deadline="目前未列入 116 學年度交換名額表。",
                eligibility_points=[availability_note],
                application_steps=[
                    "先確認最新赴外交換名額表是否已開放這所學校",
                    "開放後再依當期簡章完成校內甄選與合作校申請",
                ],
                tuition_points=["費用與學費減免須待當期簡章確認"],
            ),
        )
        for country, school_name, agreement_type, agreement_level in (
            NTPU_EXCHANGE_AGREEMENTS_WITHOUT_QUOTA
        )
    ]


def _with_current_exchange_agreements(
    open_partners: list[PartnerUniversity],
) -> list[PartnerUniversity]:
    return [*open_partners, *_agreement_only_partner_universities()]


def fetch_ntpu_partner_universities(timeout_seconds: float = 8.0) -> list[PartnerUniversity]:
    rows: list[PartnerUniversity] = []
    headers = {
        "User-Agent": "taiwan-exchange-info/0.1 (official public information reader)",
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    }
    try:
        for language_group, source_url, row_count, filename in PARTNER_PDFS:
            local_file = NTPU_OFFICIAL_DATA_DIR / filename
            if local_file.is_file():
                content = local_file.read_bytes()
            else:
                response = requests.get(
                    source_url,
                    headers=headers,
                    timeout=timeout_seconds,
                )
                response.raise_for_status()
                content = response.content
            reader = PdfReader(io.BytesIO(content))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            rows.extend(
                parse_ntpu_partner_pdf(
                    text,
                    language_group=language_group,
                    source_url=source_url,
                    row_count=row_count,
                )
            )
    except (requests.RequestException, OSError, ValueError, PdfReadError):
        return _with_current_exchange_agreements(_fallback_partner_universities())
    merged = _merge_partner_universities(rows)
    open_partners = merged if len(merged) >= 100 else _fallback_partner_universities()
    return _with_current_exchange_agreements(open_partners)


def _reference(title: str, url: str, category: PageCategory) -> SourceReference:
    return SourceReference(title=title, source_url=url, category=category)


def _item(title: str, details: list[str], source: SourceReference) -> StudentInfoItem:
    return StudentInfoItem(title=title, details=details, source=source)


def _period(
    title: str,
    details: list[str],
    source: SourceReference,
    *,
    application_round: str,
) -> ApplicationPeriodItem:
    return ApplicationPeriodItem(
        title=title,
        details=details,
        source=source,
        scope="recurring_reference",
        program_types=["exchange"],
        academic_year="115",
        application_round=application_round,
        audience=ApplicationPeriodAudience.ALL_STUDENTS,
        date_status=ApplicationPeriodDateStatus.REFERENCE_ONLY,
        status=ApplicationPeriodStatus.REFERENCE_ONLY,
        status_note="這是 115 學年度簡章所列的原則性時程，不是下一梯次的精確日期。",
        deadline_note="等待國際處發布下一梯次公告後，才能建立精確期限與提醒。",
        reminder_eligible=False,
        checked_at=NTPU_SOURCE_CHECKED_AT,
    )


def ntpu_document_explanations() -> list[RuleExplanation]:
    guidelines = _reference(
        "臺北大學 116 學年度赴外交換生申請簡章",
        NTPU_116_GUIDELINES_URL,
        PageCategory.EXCHANGE_APPLICATION,
    )
    scholarship = _reference(
        "115 學年度學海飛颺／惜珠獎學金公告",
        NTPU_115_SCHOLARSHIP_URL,
        PageCategory.SCHOLARSHIP,
    )
    return [
        RuleExplanation(
            title="臺北大學 116 學年度赴外交換生申請簡章",
            summary="校內甄選的資格、文件、語組、面試、志願分發，以及錄取後到返國的完整流程。",
            key_points=[
                "大學部二年級以上、碩博士班及進修學士班二年級以上可申請。",
                "前一學年平均 75 分以上；大學部亦可用班排前 50% 符合基本門檻。",
                "同一梯次只能選英語、日語或中文其中一組，最多填列 5 個志願。",
                "書審成績 30%、研修計畫 30%、面試 40%；總分低於 70 分不予推薦。",
                "通過校內甄選只代表獲推薦，最終錄取權仍在合作校。",
            ],
            applies_to=["赴外交換", "校內甄選", "英語組", "日語組", "中文組"],
            source=guidelines,
            document_url=NTPU_116_GUIDELINES_URL,
            document_type="甄選簡章",
            full_text_extracted=True,
        ),
        RuleExplanation(
            title="116 學年度交換名額一覽表（英語組）",
            summary="英語組合作校的科系限制、語言門檻、GPA、名額與交換期程。",
            key_points=["各校門檻不同，申請前須逐校核對。", "CEFR B2 約對應 TOEIC 785、IELTS 5.5、TOEFL iBT 72 或 Duolingo 100。", "宿舍不保證提供。"],
            applies_to=["英語組", "合作校", "語言門檻", "交換名額"],
            source=guidelines,
            document_url=NTPU_116_ENGLISH_PARTNERS_URL,
            document_type="合作校名額表",
            full_text_extracted=True,
        ),
        RuleExplanation(
            title="116 學年度交換名額一覽表（日語組）",
            summary="日語組合作校的 JLPT、科系限制、GPA、名額與交換期程。",
            key_points=["各校多以 JLPT N1 至 N4 設定門檻。", "部分學程另有限定學院或學制。", "接待學校保有最後審查及調整名額的權利。"],
            applies_to=["日語組", "合作校", "JLPT", "交換名額"],
            source=guidelines,
            document_url=NTPU_116_JAPANESE_PARTNERS_URL,
            document_type="合作校名額表",
            full_text_extracted=True,
        ),
        RuleExplanation(
            title="116 學年度交換名額一覽表（中文組）",
            summary="中文組合作校的地區、申請限制、名額與交換期程。",
            key_points=["以當期公告列出的學校與名額為準。", "部分學校限臺籍生、日間部或特定年級與專業。", "大陸地區交換期程依公告辦理。"],
            applies_to=["中文組", "合作校", "交換名額"],
            source=guidelines,
            document_url=NTPU_116_CHINESE_PARTNERS_URL,
            document_type="合作校名額表",
            full_text_extracted=True,
        ),
        RuleExplanation(
            title="115 學年度學海飛颺／惜珠獎學金公告",
            summary="臺北大學 115 學年度教育部學海飛颺與學海惜珠校內申請資格及送件方式（另請對照 2026/10/22 最新甄選辦法修正公告）。",
            key_points=[
                "須具中華民國國籍並在臺設有戶籍，且於薦送學校就讀一學期以上。",
                "學海惜珠另須符合弱勢資格，並達系所前 40% 或班級前 30%。",
                "115 學年度舊版原列不得同時領取我國政府其他出國補助或赴外學校獎學金；2026/10/22 修正公告已刪除第三條「須未獲得交換／訪問學校獎學金」限制（仍不得同時領取我國政府其他出國補助）。",
                "115 學年度本梯次已於 2026 年 3 月 6 日 17:00 截止。",
            ],
            applies_to=["學海飛颺", "學海惜珠", "赴外研修補助"],
            source=scholarship,
            document_url=NTPU_115_SCHOLARSHIP_URL,
            document_type="獎學金公告",
            full_text_extracted=True,
        ),
        RuleExplanation(
            title="2026/10/22 修正公告：國立臺北大學辦理教育部補助選送學生出國研修學海飛颺與學海惜珠甄選辦法",
            summary="國際處於 2026/10/22 公告修正學海飛颺與學海惜珠甄選辦法第 3、6、7、12 條（115/10/15 行政會議通過、115/10/21 北大國字第 1152700297 號函發布）。",
            key_points=[
                "修正第三條第(三)款：刪除原「且未獲得交換／訪問學校獎學金」限制，保留「未同時獲得我國政府預算所提供各類出國獎學金（留學貸款不在此限）」。",
                "修正第六條第(五)款、第七條第(六)款：其他有助審查文件明列含獲國外研修學校入學許可、擔任國際學伴等。",
                "增訂第十二條第(五)款：研修課程應以攻讀學位有關之專業學分為原則；赴非英語系國家得以英語及當地國語言修習，惟不得全數修習當地國語言課程。",
                "增訂第十二條第(六)款：國外大學校院辦理之暑修或語言課程不在本要點補助範圍內。",
            ],
            applies_to=["學海飛颺", "學海惜珠", "赴外研修補助", "甄選辦法修正"],
            source=_reference(
                "2026/10/22 學海飛颺與學海惜珠甄選辦法部分條文修正公告",
                NTPU_MOE_SCHOLARSHIP_AMENDMENT_URL,
                PageCategory.SCHOLARSHIP,
            ),
            document_url=NTPU_MOE_SCHOLARSHIP_AMENDMENT_PDF_URL,
            document_type="法規修正公告",
            full_text_extracted=True,
        ),
        RuleExplanation(
            title="2026/10/12 公告：法國巴黎計算機電子工程師學院（EFREI）交換說明會",
            summary="國際處於 2026/10/12 公告舉辦法國姊妹校 EFREI 交換學生計畫說明會。",
            key_points=[
                "說明會時間：2026/10/23（五）12:10–13:00（已舉辦）。",
                "說明會地點：三峽校區圖書館 2 樓思巢。",
                "由 EFREI 亞洲區國際合作負責人來校介紹學校特色、交換計畫及申請注意事項，提供免費餐盒（限額 40 名）。",
            ],
            applies_to=["赴外交換", "英語組", "法國交換", "EFREI"],
            source=_reference(
                "法國巴黎計算機電子工程師學院 EFREI 交換說明會公告",
                NTPU_EFREI_INFO_SESSION_URL,
                PageCategory.EXCHANGE_APPLICATION,
            ),
            document_url=NTPU_EFREI_INFO_SESSION_URL,
            document_type="說明會公告",
            full_text_extracted=True,
        ),
    ]


def _ntpu_116_period(reference_time: datetime | None = None) -> ApplicationPeriodItem:
    """The 116 round dates, taken only from the announcement's own title."""

    now = reference_time or datetime.now(timezone.utc)
    if now.utcoffset() is None:
        now = now.replace(tzinfo=timezone.utc)
    opens_at = datetime(2026, 10, 1, 0, 0, tzinfo=TAIPEI_TIMEZONE)
    deadline_at = datetime(2026, 10, 23, 17, 0, tzinfo=TAIPEI_TIMEZONE)
    status = _application_period_status(now, opens_at=opens_at, deadline_at=deadline_at)
    return ApplicationPeriodItem(
        title="116學年度赴外交換校內申請",
        details=[
            "國際處 2026/09/24 公告 116 學年度赴外交換簡章；申請日期自 2026/10/01 起至 2026/10/23 17:00 止。",
            "簡章、英文版選送辦法與英語、日語、中文三組名額一覽表已隨公告發布。",
            "合作校名單與名額已更新為 116 學年度名額表（英語 133 列、日語 16 列、中文 21 列）；各校資格與限制仍以名額表原文為準。",
            "簡章載明：線上申請送出後，須於 2026/10/23 17:00 前將簽名申請表上傳至指定 Google 表單，逾期視為申請未完成。",
            "公告時程載明：11 月中旬公布面試時間表，2026/11/23、11/25 舉行英語組面試，2026/11/27 舉行中、日語組面試，12 月下旬公告甄選結果。",
        ],
        source=SourceReference(
            title="116學年度赴外交換簡章公告",
            source_url=NTPU_116_ANNOUNCEMENT_URL,
            category=PageCategory.EXCHANGE_APPLICATION,
        ),
        scope="home_application",
        program_types=["exchange"],
        academic_year="116",
        application_round="秋季／全學年梯次",
        audience=ApplicationPeriodAudience.ALL_STUDENTS,
        opens_at=opens_at,
        deadline_at=deadline_at,
        date_status=ApplicationPeriodDateStatus.VERIFIED_EXACT,
        status=status,
        status_note={
            ApplicationPeriodStatus.UPCOMING: "本梯次尚未開放；請先準備校內文件，不要提前送件。",
            ApplicationPeriodStatus.OPEN: "本梯次正在受理；請在截止前完成線上申請與文件上傳。",
            ApplicationPeriodStatus.CLOSED: "本梯次已截止；不能沿用這組日期送件。",
        }[status],
        deadline_note="截止時間載於 116 學年度簡章與公告標題；流程尚待人工審核發布，因此暫不建立提醒，請另行記下日期。",
        reminder_eligible=False,
        checked_at=NTPU_116_CHECKED_AT,
    )


def build_ntpu_student_dashboard(
    *,
    partner_universities: list[PartnerUniversity] | None = None,
    reference_time: datetime | None = None,
) -> StudentDashboard:
    guidelines = _reference(
        "臺北大學 116 學年度赴外交換生申請簡章",
        NTPU_116_GUIDELINES_URL,
        PageCategory.EXCHANGE_APPLICATION,
    )
    files = _reference("臺北大學國際事務處檔案下載", NTPU_FILES_URL, PageCategory.EXCHANGE_APPLICATION)
    scholarship = _reference(
        "115 學年度學海飛颺／惜珠獎學金公告",
        NTPU_115_SCHOLARSHIP_URL,
        PageCategory.SCHOLARSHIP,
    )
    partners = partner_universities if partner_universities is not None else fetch_ntpu_partner_universities()
    documents = ntpu_document_explanations()
    return StudentDashboard(
        school_name="國立臺北大學",
        last_checked=NTPU_116_CHECKED_AT,
        academic_score_minimum=75,
        academic_score_rule="前一學年平均 75 分以上；大學部亦可用班排前 50% 符合基本門檻。",
        language_score_minimums={},
        application_periods=[
            _ntpu_116_period(reference_time),
            _period(
                "秋季／全學年交換校內甄選",
                ["原則於每年 9 月底公告。", "115 學年度簡章的線上申請與文件上傳為 10 月 1 日至 10 月 31 日；116 學年度已公告為 10 月 1 日至 10 月 23 日 17 時，以上一項為準。", "面試通常於 11 月下旬，結果於 12 月公告。", "下一梯次仍須以國際處最新公告為準。"],
                guidelines,
                application_round="秋季／全學年梯次",
            ),
            _period(
                "春季交換校內甄選",
                ["原則於每年 3 月底公告。", "線上申請與文件上傳通常為 4 月 1 日至 4 月 30 日。", "面試通常於 5 月下旬，結果於 6 月公告。", "歐美學校春季可能於 1 月上旬開學，應先核對課程與學籍安排。"],
                guidelines,
                application_round="春季梯次",
            ),
        ],
        program_overview=[
            _item("校級赴外交換", ["保留臺北大學正式學籍，到合作校交換 1 學期或 1 學年。", "原則上繳交臺北大學學雜費並免繳合作校學費；個別協議另有規定時除外。"], guidelines),
            _item("三個語組", ["英語組、日語組、中文組擇一申請。", "每梯次最多填列 5 個志願，依總成績與志願序分發。"], guidelines),
            _item("甄選與合作校複審", ["書審 30%、研修計畫 30%、面試 40%。", "校內總分低於 70 分不予推薦。", "校內推薦不等同合作校正式錄取。"], guidelines),
            _item(
                "法國巴黎計算機電子工程師學院（EFREI）交換說明會（2026/10/12 公告）",
                [
                    "國際處於 2026/10/12 公告舉辦法國姊妹校 EFREI 交換說明會（時間：2026/10/23 12:10–13:00，地點：三峽校區圖書館 2F 思巢）。",
                    "由 EFREI 亞洲區國際合作負責人介紹課程與交換申請要點；116 學年度英語組名額與門檻仍依官方名額表為準。",
                ],
                _reference(
                    "法國巴黎計算機電子工程師學院 EFREI 交換說明會公告",
                    NTPU_EFREI_INFO_SESSION_URL,
                    PageCategory.EXCHANGE_APPLICATION,
                ),
            ),
            _item(
                "院級交換分流與讀取缺口說明（法律院 10/30 11:00 截止僅限法律院）",
                [
                    "法律學院院級交換公告（https://www.law.ntpu.edu.tw/news/j1p0rQCYhCHb ）正文、表單及三份 PDF 與既有基準一致，2026/10/30 11:00 截止僅適用法律學院學生，不可混為全校校級截止日。",
                    "校級預告公告（https://bulletin.ntpu.edu.tw/bulletin_content.php?no=20260707133939366861 ）及商學院院級公告／時程圖於 2026/10/27 重試仍讀取失敗，保留最後成功查核基準，不推論取消或改期。",
                ],
                _reference(
                    "國立臺北大學法律學院院級交換公告（僅適用法律院）",
                    NTPU_LAW_COLLEGE_EXCHANGE_URL,
                    PageCategory.EXCHANGE_APPLICATION,
                ),
            ),
        ],
        eligibility=[
            _item("學籍與年級", ["大學部及進修學士班須二年級以上。", "碩士、博士與碩士在職專班學生可申請。", "交換期間須保留學籍並依規定繳費；休學或已畢業者不具交換資格。"], guidelines),
            _item("校內學業門檻", ["前一學年平均成績 75 分以上。", "大學部學生亦可用前一學年班排前 50% 符合基本門檻。", "仍須同時符合志願合作校的 GPA、科系、年級及其他限制。"], guidelines),
            _item("身分限制", ["僑生、陸生及外國學生不得申請前往原國籍國家交換。", "同一梯次只能申請一個語組。", "總交換期間原則上不得超過一學年。"], guidelines),
        ],
        language_requirements=[
            _item("有效官方語言成績", ["英語組與日語組須在期限內上傳仍在效期內的官方成績。", "TOEFL、IELTS 等通常有效 2 年；JLPT 及部分歐語檢定依發證規則辦理。", "成績在校內申請與合作校送件時都須符合效期與門檻。"], guidelines),
            _item("依合作校逐校核對", ["英語組、日語組各校門檻不同，系統會依名額表顯示已知條件。", "中文組也可能有身分、科系或年級限制。", "合作校保有修改門檻及最終審查的權利。"], guidelines),
        ],
        required_documents=[
            _item("校內甄選文件", ["線上申請表與志願序。", "有效官方語言能力證明。", "交換研修計畫書：含學習背景、申請動機與未來研修規劃，使用所選語組語言，A4 自由格式、最多 5,000 字。", "歷年正式成績單；大學部須含班級排名，一年級碩士生另附完整大學成績單。"], guidelines),
            _item("獲推薦後", ["依期限繳交錄取確認書及家長同意書。", "再依合作校要求準備提名後申請文件；合作校審查通常需 2 至 3 個月。"], guidelines),
            _item("出國前、抵達與返國", ["出國前完成出國選課行前申請表與離校程序。", "抵達合作校 1 個月內回報當地地址、電話與生活狀況。", "返國 1 個月內向國際處繳交交換心得，並向系所與註冊組申請學分採認。"], files),
        ],
        scholarship_info=[
            _item(
                "2026/10/22 修正公告：學海飛颺與學海惜珠甄選辦法部分條文修正",
                [
                    "國際處於 2026/10/22 公告修正「國立臺北大學辦理教育部補助選送學生出國研修學海飛颺與學海惜珠甄選辦法」（115/10/15 第 86 次行政會議通過）。",
                    "刪除第三條第(三)款「且未獲得交換／訪問學校獎學金」限制（仍不得同時獲得我國政府預算提供之各類出國獎學金）。",
                    "修正第六條第(五)款與第七條第(六)款：其他有助審查文件明列含國外研修學校入學許可、擔任國際學伴等。",
                    "增訂第十二條第(五)、(六)款：應以攻讀學位相關專業學分為原則，赴非英語系國家得以英語及當地國語言修習惟不得全數修習當地國語言課程；國外暑修或純語言課程不在補助範圍內。",
                ],
                _reference(
                    "2026/10/22 學海飛颺與學海惜珠甄選辦法部分條文修正公告",
                    NTPU_MOE_SCHOLARSHIP_AMENDMENT_URL,
                    PageCategory.SCHOLARSHIP,
                ),
            ),
            _item("教育部學海飛颺／惜珠（115 學年度梯次歷史參考）", ["115 學年度本梯次申請已於 2026 年 3 月 6 日 17:00 截止。", "學海惜珠另有弱勢資格與成績排名條件。", "下一年度申請日期、名額與文件須等待國際處新公告，並適用 2026/10/22 修正後甄選辦法。"], scholarship),
        ],
        document_explanations=documents,
        rule_explanations=documents,
        partner_universities=partners,
        sources=[
            guidelines,
            files,
            scholarship,
            _reference(
                "2026/10/22 學海飛颺與學海惜珠甄選辦法修正公告",
                NTPU_MOE_SCHOLARSHIP_AMENDMENT_URL,
                PageCategory.SCHOLARSHIP,
            ),
            _reference(
                "法國巴黎計算機電子工程師學院 EFREI 交換說明會公告",
                NTPU_EFREI_INFO_SESSION_URL,
                PageCategory.EXCHANGE_APPLICATION,
            ),
            _reference("臺北大學姊妹校", NTPU_SISTER_SCHOOL_URL, PageCategory.PARTNER_SCHOOL),
        ],
    )


def ntpu_exchange_info(partners: list[PartnerUniversity] | None = None) -> ExchangeInfo:
    partner_rows = partners if partners is not None else fetch_ntpu_partner_universities()
    return ExchangeInfo(
        school_name="國立臺北大學",
        program_type=["校級赴外交換", "英語組", "日語組", "中文組", "學海飛颺", "學海惜珠"],
        academic_year=["116學年度"],
        semester=["秋季", "春季", "一學期", "一學年"],
        application_period=[
            "116 學年度（秋季／全學年）：2026/10/01 至 2026/10/23 17:00（已截止）",
            "法律學院院級交換：2026/10/30 11:00 截止（僅適用法律學院，不可混為全校截止日；校級預告與商院公告讀取失敗時保留既有基準）",
            "法國巴黎計算機電子工程師學院（EFREI）交換說明會：2026/10/23 12:10–13:00（2026/10/12 公告）",
            "春季：原則 4 月，確切期限依國際處當期公告",
        ],
        eligibility=["大學部二年級以上或研究生", "前一學年平均 75 分以上；大學部亦可用班排前 50%", "須符合合作校個別規定"],
        language_requirement=["同一梯次擇一語組", "英語組與日語組須檢附有效官方語言成績", "門檻依合作校名額表"],
        required_documents=["線上申請表", "有效語言證明", "交換研修計畫書", "歷年正式成績單"],
        scholarship_info=[
            "教育部學海飛颺／惜珠：2026/10/22 公告修正甄選辦法（刪除未獲交換校獎學金限制、增訂第12條專業學分與排除暑修／純語言課程規定）；申請日期依當年度公告"
        ],
        partner_universities=[row.school_name for row in partner_rows],
        source_urls=[
            NTPU_116_ANNOUNCEMENT_URL,
            NTPU_116_GUIDELINES_URL,
            NTPU_MOE_SCHOLARSHIP_AMENDMENT_URL,
            NTPU_MOE_SCHOLARSHIP_AMENDMENT_PDF_URL,
            NTPU_EFREI_INFO_SESSION_URL,
            NTPU_LAW_COLLEGE_EXCHANGE_URL,
            NTPU_SCHOOL_PREVIEW_BULLETIN_URL,
            NTPU_FILES_URL,
        ],
        last_checked=NTPU_116_CHECKED_AT,
    )


def ntpu_processed_pages() -> list[ProcessedPage]:
    rows = [
        (
            "臺北大學 116 學年度赴外交換生申請簡章",
            NTPU_116_ANNOUNCEMENT_URL,
            PageCategory.EXCHANGE_APPLICATION,
            "116學年度校內申請期間為2026年10月1日至10月23日17時；線上申請送出後，須於2026年10月23日下午5時前將簽名申請表上傳至指定Google表單，逾期視為申請未完成。春季交換通常於4月受理。申請資格為大學部二年級以上、碩博士班及進修學士班二年級以上，前一學年平均75分以上；大學部亦可用班排前50%。同一梯次只能選英語、日語或中文一組，最多填列5個志願。應繳文件包括線上申請表、有效官方語言成績、交換研修計畫書及正式成績單。書審30%、研修計畫30%、面試40%，總分低於70分不予推薦。",
        ),
        (
            "臺北大學交換生錄取後與返國流程",
            NTPU_116_GUIDELINES_URL,
            PageCategory.EXCHANGE_APPLICATION,
            "校內推薦不等同合作校錄取。獲推薦後須依期限繳交錄取確認書及家長同意書，再依合作校要求送件。出國前完成選課行前申請表與離校程序；抵達合作校一個月內回報當地聯絡資料；返國一個月內繳交交換心得，並憑正式成績單與課程大綱申請學分採認。",
        ),
        (
            "2026/10/22 修正公告：國立臺北大學辦理教育部補助選送學生出國研修學海飛颺與學海惜珠甄選辦法",
            NTPU_MOE_SCHOLARSHIP_AMENDMENT_URL,
            PageCategory.SCHOLARSHIP,
            "國際處於2026年10月22日發布修正公告（115年10月15日第86次行政會議通過、115年10月21日北大國字第1152700297號函發布），修正學海飛颺與學海惜珠甄選辦法第3、6、7、12條：刪除第三條第(三)款「且未獲得交換／訪問學校獎學金」限制（仍不得同時領取我國政府預算提供之各類出國獎學金）；第6、7條其他有助審查文件明列含獲國外研修學校入學許可、擔任國際學伴等；增訂第12條第(五)、(六)款，研修課程應以攻讀學位有關之專業學分為原則，赴非英語系國家得以英語及當地國語言修習惟不得全數修習當地國語言課程，且國外大學校院辦理之暑修或語言課程不在補助範圍內。",
        ),
        (
            "法國巴黎計算機電子工程師學院 EFREI 交換說明會公告",
            NTPU_EFREI_INFO_SESSION_URL,
            PageCategory.EXCHANGE_APPLICATION,
            "國際處於2026年10月12日公告：2026年10月23日（五）12:10至13:00於三峽校區圖書館2樓思巢舉辦法國巴黎計算機電子工程師學院（EFREI）交換說明會，邀請EFREI亞洲區國際合作負責人來校介紹學校特色、交換計畫與申請流程。",
        ),
        (
            "115 學年度學海飛颺／惜珠獎學金公告",
            NTPU_115_SCHOLARSHIP_URL,
            PageCategory.SCHOLARSHIP,
            "115學年度學海飛颺與學海惜珠本梯次於2026年3月6日17時截止。申請人須具中華民國國籍並在臺設有戶籍，且於薦送學校就讀一學期以上。學海惜珠另有弱勢資格及系所前40%或班級前30%的成績要求。2026/10/22修正公告已刪除未獲交換校獎學金之限制。",
        ),
    ]
    pages: list[ProcessedPage] = []
    for title, url, category, text in rows:
        pages.append(
            ProcessedPage(
                title=title,
                source_url=url,
                published_at="2026/09/24" if category == PageCategory.EXCHANGE_APPLICATION else "2026/03/03",
                text=text,
                summary=text[:220],
                category=category,
                attachments=[Attachment(url=NTPU_116_GUIDELINES_URL, filename="臺北大學116學年度赴外交換生申請簡章.pdf", content_type="application/pdf")] if category == PageCategory.EXCHANGE_APPLICATION else [],
                crawled_at=NTPU_116_CHECKED_AT,
                content_hash=hashlib.sha256(f"{title}\n{text}".encode("utf-8")).hexdigest(),
            )
        )
    return pages
