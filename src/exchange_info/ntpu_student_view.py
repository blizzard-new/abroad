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
from .student_view import _merge_partner_universities


NTPU_OIA_URL = "https://new.ntpu.edu.tw/oia"
NTPU_FILES_URL = "https://new.ntpu.edu.tw/oia/files"
NTPU_SISTER_SCHOOL_URL = "https://new.ntpu.edu.tw/oia/sister-school"
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
NTPU_SOURCE_CHECKED_AT = datetime(2026, 7, 20, tzinfo=timezone.utc)


NTPU_OFFICIAL_DATA_DIR = Path(__file__).resolve().parent / "official_data" / "ntpu"


PARTNER_PDFS = (
    ("英語組", NTPU_115_ENGLISH_PARTNERS_URL, 121, "115-english-partners.pdf"),
    ("日語組", NTPU_115_JAPANESE_PARTNERS_URL, 16, "115-japanese-partners.pdf"),
    ("中文組", NTPU_115_CHINESE_PARTNERS_URL, 19, "115-chinese-partners.pdf"),
)


COUNTRY_PREFIXES = (
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
    (r"捷克\s*Czech", "捷克"),
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
        return before_group.strip(" ，,")

    marker = re.search(
        r"\s+(?=(?:限|具備|建議|相當於|主修|僅|日本語能力試驗|"
        r"TOEFL|IELTS|大學[:：]|學士[:：]|碩士[:：]|\d+\.[A-Z]|無\s+(?:無|\d)))",
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
    period_match = re.search(r"(?:1|一)學期(?:\s*(?:或|/|／)\s*(?:1|一)學年)?", details)
    study_period = period_match.group(0) if period_match else "依當期名額表"
    quota_matches = re.findall(r"\b(\d{1,2})\s+(?=(?:1|一)學期)", details)
    quota = f"{quota_matches[-1]} 名上限" if quota_matches else None
    if re.search(r"限大學部|undergraduate students only", details, re.IGNORECASE):
        degree_levels = "大學部"
    elif re.search(r"研究生|碩士|master|doctoral", details, re.IGNORECASE):
        degree_levels = "大學部、研究所"
    else:
        degree_levels = "大學部、研究所（依合作校規定）"
    college_match = re.search(r"限(.{2,80}?)(?:學生|申請)", details)
    colleges = college_match.group(1).strip(" ：:，,") if college_match else "依合作校規定"
    eligibility = details[:1200] or "申請資格、語言與名額依 115 學年度官方名額表。"
    return PartnerUniversity(
        program_type=f"交換學生（{language_group}）",
        country=country,
        school_name=school_name,
        colleges=colleges,
        degree_levels=degree_levels,
        study_period=study_period,
        quota=quota,
        eligibility=eligibility,
        application_deadline="校內甄選原則於每年 10/1–10/31 或 4/1–4/30；以當期公告為準。",
        application_info="同一梯次擇一語組，最多填列 5 個志願；通過校內甄選後仍須經合作校審查。",
        tuition_info="交換期間須保留臺北大學學籍並依規定繳費；合作校學費是否免繳以個別協議為準。",
        source_url=source_url,
        student_summary_zh=PartnerStudentSummary(
            study_period=study_period,
            application_deadline="每年 10 月或 4 月受理，依當期公告。",
            eligibility_points=[eligibility[:360]],
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
        if "\n序號 國別" in block:
            block = block.split("\n序號 國別", 1)[0]
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
        "英語組": NTPU_115_ENGLISH_PARTNERS_URL,
        "日語組": NTPU_115_JAPANESE_PARTNERS_URL,
        "中文組": NTPU_115_CHINESE_PARTNERS_URL,
    }
    return [
        PartnerUniversity(
            program_type=f"交換學生（{group}）",
            country=country,
            school_name=school_name,
            colleges="依合作校規定",
            degree_levels="大學部、研究所（依合作校規定）",
            study_period="1 學期或 1 學年（依名額表）",
            eligibility="離線備援摘要；請開啟官方 115 學年度名額表核對資格、語言與名額。",
            application_deadline="校內甄選原則於每年 10 月或 4 月受理；以當期公告為準。",
            application_info="同一梯次擇一語組，最多填列 5 個志願。",
            tuition_info="交換期間須保留臺北大學學籍並依規定繳費。",
            source_url=source_by_group[group],
        )
        for group, country, school_name in FALLBACK_PARTNERS
    ]


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
        return _fallback_partner_universities()
    merged = _merge_partner_universities(rows)
    return merged if len(merged) >= 100 else _fallback_partner_universities()


def _reference(title: str, url: str, category: PageCategory) -> SourceReference:
    return SourceReference(title=title, source_url=url, category=category)


def _item(title: str, details: list[str], source: SourceReference) -> StudentInfoItem:
    return StudentInfoItem(title=title, details=details, source=source)


def ntpu_document_explanations() -> list[RuleExplanation]:
    guidelines = _reference(
        "臺北大學 115 學年度赴外交換生申請簡章",
        NTPU_115_ANNOUNCEMENT_URL,
        PageCategory.EXCHANGE_APPLICATION,
    )
    scholarship = _reference(
        "115 學年度學海飛颺／惜珠獎學金公告",
        NTPU_115_SCHOLARSHIP_URL,
        PageCategory.SCHOLARSHIP,
    )
    return [
        RuleExplanation(
            title="臺北大學 115 學年度赴外交換生申請簡章",
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
            document_url=NTPU_115_GUIDELINES_URL,
            document_type="甄選簡章",
            full_text_extracted=True,
        ),
        RuleExplanation(
            title="115 學年度交換名額一覽表（英語組）",
            summary="英語組合作校的科系限制、語言門檻、GPA、名額與交換期程。",
            key_points=["各校門檻不同，申請前須逐校核對。", "CEFR B2 約對應 TOEIC 785、IELTS 5.5、TOEFL iBT 72 或 Duolingo 100。", "宿舍不保證提供。"],
            applies_to=["英語組", "合作校", "語言門檻", "交換名額"],
            source=guidelines,
            document_url=NTPU_115_ENGLISH_PARTNERS_URL,
            document_type="合作校名額表",
            full_text_extracted=True,
        ),
        RuleExplanation(
            title="115 學年度交換名額一覽表（日語組）",
            summary="日語組合作校的 JLPT、科系限制、GPA、名額與交換期程。",
            key_points=["各校多以 JLPT N1 至 N4 設定門檻。", "部分學程另有限定學院或學制。", "接待學校保有最後審查及調整名額的權利。"],
            applies_to=["日語組", "合作校", "JLPT", "交換名額"],
            source=guidelines,
            document_url=NTPU_115_JAPANESE_PARTNERS_URL,
            document_type="合作校名額表",
            full_text_extracted=True,
        ),
        RuleExplanation(
            title="115 學年度交換名額一覽表（中文組）",
            summary="中文組合作校的地區、申請限制、名額與交換期程。",
            key_points=["以當期公告列出的學校與名額為準。", "部分學校限臺籍生、日間部或特定年級與專業。", "大陸地區交換期程依公告辦理。"],
            applies_to=["中文組", "合作校", "交換名額"],
            source=guidelines,
            document_url=NTPU_115_CHINESE_PARTNERS_URL,
            document_type="合作校名額表",
            full_text_extracted=True,
        ),
        RuleExplanation(
            title="115 學年度學海飛颺／惜珠獎學金公告",
            summary="臺北大學 115 學年度教育部學海飛颺與學海惜珠校內申請資格及送件方式。",
            key_points=[
                "須具中華民國國籍並在臺設有戶籍，且於薦送學校就讀一學期以上。",
                "學海惜珠另須符合弱勢資格，並達系所前 40% 或班級前 30%。",
                "不得同時領取我國政府其他出國補助或赴外學校獎學金。",
                "115 學年度本梯次已於 2026 年 3 月 6 日 17:00 截止。",
            ],
            applies_to=["學海飛颺", "學海惜珠", "赴外研修補助"],
            source=scholarship,
            document_url=NTPU_115_SCHOLARSHIP_URL,
            document_type="獎學金公告",
            full_text_extracted=True,
        ),
    ]


def build_ntpu_student_dashboard(
    *,
    partner_universities: list[PartnerUniversity] | None = None,
) -> StudentDashboard:
    guidelines = _reference(
        "臺北大學 115 學年度赴外交換生申請簡章",
        NTPU_115_ANNOUNCEMENT_URL,
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
        last_checked=NTPU_SOURCE_CHECKED_AT,
        academic_score_minimum=75,
        academic_score_rule="前一學年平均 75 分以上；大學部亦可用班排前 50% 符合基本門檻。",
        language_score_minimums={},
        application_periods=[
            _item(
                "秋季／全學年交換校內甄選",
                ["原則於每年 9 月底公告。", "線上申請與文件上傳通常為 10 月 1 日至 10 月 31 日。", "面試通常於 11 月下旬，結果於 12 月公告。", "下一梯次仍須以國際處最新公告為準。"],
                guidelines,
            ),
            _item(
                "春季交換校內甄選",
                ["原則於每年 3 月底公告。", "線上申請與文件上傳通常為 4 月 1 日至 4 月 30 日。", "面試通常於 5 月下旬，結果於 6 月公告。", "歐美學校春季可能於 1 月上旬開學，應先核對課程與學籍安排。"],
                guidelines,
            ),
        ],
        program_overview=[
            _item("校級赴外交換", ["保留臺北大學正式學籍，到合作校交換 1 學期或 1 學年。", "原則上繳交臺北大學學雜費並免繳合作校學費；個別協議另有規定時除外。"], guidelines),
            _item("三個語組", ["英語組、日語組、中文組擇一申請。", "每梯次最多填列 5 個志願，依總成績與志願序分發。"], guidelines),
            _item("甄選與合作校複審", ["書審 30%、研修計畫 30%、面試 40%。", "校內總分低於 70 分不予推薦。", "校內推薦不等同合作校正式錄取。"], guidelines),
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
            _item("教育部學海飛颺／惜珠", ["115 學年度本梯次申請已於 2026 年 3 月 6 日 17:00 截止。", "學海惜珠另有弱勢資格與成績排名條件。", "不得同時領取我國政府其他出國補助或赴外學校獎學金。", "下一年度日期、名額與文件須等待國際處新公告。"], scholarship),
        ],
        document_explanations=documents,
        rule_explanations=documents,
        partner_universities=partners,
        sources=[guidelines, files, scholarship, _reference("臺北大學姊妹校", NTPU_SISTER_SCHOOL_URL, PageCategory.PARTNER_SCHOOL)],
    )


def ntpu_exchange_info(partners: list[PartnerUniversity] | None = None) -> ExchangeInfo:
    partner_rows = partners if partners is not None else fetch_ntpu_partner_universities()
    return ExchangeInfo(
        school_name="國立臺北大學",
        program_type=["校級赴外交換", "英語組", "日語組", "中文組", "學海飛颺", "學海惜珠"],
        academic_year=["115學年度"],
        semester=["秋季", "春季", "一學期", "一學年"],
        application_period=["秋季／全學年：原則 10 月 1 日至 10 月 31 日", "春季：原則 4 月 1 日至 4 月 30 日", "確切期限依國際處當期公告"],
        eligibility=["大學部二年級以上或研究生", "前一學年平均 75 分以上；大學部亦可用班排前 50%", "須符合合作校個別規定"],
        language_requirement=["同一梯次擇一語組", "英語組與日語組須檢附有效官方語言成績", "門檻依合作校名額表"],
        required_documents=["線上申請表", "有效語言證明", "交換研修計畫書", "歷年正式成績單"],
        scholarship_info=["教育部學海飛颺／惜珠；日期與條件依當年度公告"],
        partner_universities=[row.school_name for row in partner_rows],
        source_urls=[NTPU_115_ANNOUNCEMENT_URL, NTPU_115_GUIDELINES_URL, NTPU_FILES_URL],
        last_checked=NTPU_SOURCE_CHECKED_AT,
    )


def ntpu_processed_pages() -> list[ProcessedPage]:
    rows = [
        (
            "臺北大學 115 學年度赴外交換生申請簡章",
            NTPU_115_ANNOUNCEMENT_URL,
            PageCategory.EXCHANGE_APPLICATION,
            "115學年度校內申請期間為2025年10月1日9時至10月31日16時。秋季或全學年交換通常於10月受理，春季交換通常於4月受理。申請資格為大學部二年級以上、碩博士班及進修學士班二年級以上，前一學年平均75分以上；大學部亦可用班排前50%。同一梯次只能選英語、日語或中文一組，最多填列5個志願。應繳文件包括線上申請表、有效官方語言成績、交換研修計畫書及正式成績單。書審30%、研修計畫30%、面試40%，總分低於70分不予推薦。",
        ),
        (
            "臺北大學交換生錄取後與返國流程",
            NTPU_115_GUIDELINES_URL,
            PageCategory.EXCHANGE_APPLICATION,
            "校內推薦不等同合作校錄取。獲推薦後須依期限繳交錄取確認書及家長同意書，再依合作校要求送件。出國前完成選課行前申請表與離校程序；抵達合作校一個月內回報當地聯絡資料；返國一個月內繳交交換心得，並憑正式成績單與課程大綱申請學分採認。",
        ),
        (
            "115 學年度學海飛颺／惜珠獎學金公告",
            NTPU_115_SCHOLARSHIP_URL,
            PageCategory.SCHOLARSHIP,
            "115學年度學海飛颺與學海惜珠本梯次於2026年3月6日17時截止。申請人須具中華民國國籍並在臺設有戶籍，且於薦送學校就讀一學期以上。學海惜珠另有弱勢資格及系所前40%或班級前30%的成績要求。不得同時領取我國政府其他出國補助或赴外學校獎學金。",
        ),
    ]
    pages: list[ProcessedPage] = []
    for title, url, category, text in rows:
        pages.append(
            ProcessedPage(
                title=title,
                source_url=url,
                published_at="2025/09/26" if category == PageCategory.EXCHANGE_APPLICATION else "2026/03/03",
                text=text,
                summary=text[:220],
                category=category,
                attachments=[Attachment(url=NTPU_115_GUIDELINES_URL, filename="臺北大學115學年度赴外交換生申請簡章.pdf", content_type="application/pdf")] if category == PageCategory.EXCHANGE_APPLICATION else [],
                crawled_at=NTPU_SOURCE_CHECKED_AT,
                content_hash=hashlib.sha256(f"{title}\n{text}".encode("utf-8")).hexdigest(),
            )
        )
    return pages
