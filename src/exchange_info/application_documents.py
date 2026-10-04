from __future__ import annotations

import base64
import hashlib
import hmac
import html
import io
import json
import os
import re
import shutil
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Literal

from docx import Document
from docx.shared import Inches
from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .models import (
    ApplicationCenterContext,
    ApplicationCopyType,
    ApplicationDocumentCatalog,
    ApplicationDocumentCatalogItem,
    ApplicationDocumentSelection,
    ApplicationDocumentTemplate,
    ApplicationFieldPreviewItem,
    ApplicationFieldType,
    ApplicationFormField,
    ApplicationPacketManifest,
    ApplicationPacketAttachmentItem,
    ApplicationPacketManifestItem,
    ApplicationPacketRequest,
    ApplicationRuleContext,
    ApplicationSupportStatus,
    ApplicationWorkflowReviewStatus,
    UniversityApplicationWorkflow,
)
from .application_rules import select_application_workflow
from .university_registry import NTPU, require_university


FLOW_SOURCE_URL = "https://www.cgu.edu.tw/oia-ch/Subject?nodeId=15680"
INITIAL_SOURCE_URL = "https://www.cgu.edu.tw/oia-ch/Subject/Detail/56388?nodeId=15680"
PREDEPARTURE_SOURCE_URL = "https://www.cgu.edu.tw/oia-ch/Subject/Detail/56390?nodeId=15680"
SHORT_TERM_SOURCE_URL = (
    "https://www.cgu.edu.tw/regulation/RegulationManagement/RegulationDetail/"
    "188edb21-5c53-4cbe-9e55-81089f90528b"
)
SOURCE_CHECKED_AT = datetime(2026, 7, 16, tzinfo=timezone.utc)
NTPU_SOURCE_CHECKED_AT = datetime(2026, 7, 20, tzinfo=timezone.utc)
NTPU_EXCHANGE_GUIDELINES_URL = (
    "https://cms-carrier.ntpu.edu.tw/uploads/"
    "2026_2027_Academic_Year_Outbound_Exchange_Program_Guidelines_1e5870e83d.pdf"
)


@dataclass(frozen=True)
class _AttachmentPayload:
    field_id: str
    field_label: str
    file_name: str
    media_type: str
    raw: bytes
    page_count: int | None
    placement: Literal["after_document", "inside_document"]
SHORT_TERM_SOURCE_CHECKED_AT = datetime(2026, 7, 29, tzinfo=timezone.utc)
CGU_OFFICIAL_FORM_DOWNLOADS = {
    "2B0001001": "https://www.cgu.edu.tw/regulation/ServerFile/Get/bee3b146-0cb7-4095-8441-cbf5913cb245",
    "2B0001002": "https://www.cgu.edu.tw/regulation/ServerFile/Get/401314f7-0304-431f-8432-ff219f4bf434",
    "2B0001003": "https://www.cgu.edu.tw/regulation/ServerFile/Get/3436f7fa-57fa-4581-a354-e4056de768f6",
    "2B0001004": "https://www.cgu.edu.tw/regulation/ServerFile/Get/c738f57d-1808-4103-a2ef-e903ce1e1926",
}


def _field(
    field_id: str,
    label: str,
    *,
    field_type: ApplicationFieldType = ApplicationFieldType.TEXT,
    required: bool = False,
    profile: str | None = None,
    placeholder: str | None = None,
    help_text: str | None = None,
    options: Iterable[str] = (),
    sensitive: bool = False,
    max_length: int | None = None,
    min_files: int = 0,
    max_files: int = 6,
) -> ApplicationFormField:
    return ApplicationFormField(
        id=field_id,
        label=label,
        field_type=field_type,
        required=required,
        reusable_profile_key=profile,
        placeholder=placeholder,
        help_text=help_text,
        options=list(options),
        sensitive=sensitive or field_type == ApplicationFieldType.FILES,
        max_length=max_length,
        min_files=min_files,
        max_files=max_files,
    )


PROFILE_FIELDS = [
    _field("student_name_zh", "中文姓名", required=True, profile="student_name_zh"),
    _field("student_name_en", "護照英文姓名", required=True, profile="student_name_en"),
    _field("student_id", "學號", required=True, profile="student_id"),
    _field("college", "學院", required=True, profile="college"),
    _field("department", "系所／學程", required=True, profile="department"),
    _field("degree_level", "學制", required=True, profile="degree_level", field_type=ApplicationFieldType.SELECT, options=("大學部", "碩士班", "博士班")),
    _field("year_level", "年級", required=True, profile="year_level", field_type=ApplicationFieldType.SELECT, options=("一年級", "二年級", "三年級", "四年級", "五年級以上")),
    _field("email", "Email", required=True, profile="email", field_type=ApplicationFieldType.EMAIL),
    _field("phone", "手機", required=True, profile="phone", field_type=ApplicationFieldType.TEL),
]


def _template(
    template_id: str,
    title: str,
    short_title: str,
    *,
    category: str,
    stage: str,
    description: str,
    fields: list[ApplicationFormField],
    source_url: str,
    copies: int = 1,
    destinations: Iterable[str] = (),
    signatures: Iterable[str] = (),
    stamps: Iterable[str] = (),
    program_types: Iterable[str] = ("exchange", "dual_degree", "internship"),
    flags: Iterable[str] = (),
    conditional_note: str | None = None,
    official_layout: bool = False,
    official_form_number: str | None = None,
    official_file_name: str | None = None,
    official_download_url: str | None = None,
    paper_size: str = "A4",
    print_sides: Literal["single_sided", "double_sided", "confirm_official"] | None = None,
    print_note: str | None = None,
    attachment_field_order: Iterable[str] = (),
    version: str = "2026-07-16",
) -> ApplicationDocumentTemplate:
    file_field_ids = [
        field.id for field in fields if field.field_type == ApplicationFieldType.FILES
    ]
    ordered_attachment_fields = list(attachment_field_order) or file_field_ids
    if not set(ordered_attachment_fields) <= set(file_field_ids):
        raise ValueError(f"{template_id} 的附件順序包含非檔案欄位。")
    resolved_print_sides = print_sides or (
        "confirm_official" if official_layout else "single_sided"
    )
    resolved_print_note = print_note
    if resolved_print_note is None:
        resolved_print_note = (
            "官方未明確標示單雙面，請依當期表格與承辦單位指示列印。"
            if resolved_print_sides == "confirm_official"
            else "系統整理頁以 A4 單面列印；校方另有格式時以官方最新版為準。"
        )
    return ApplicationDocumentTemplate(
        id=template_id,
        title=title,
        short_title=short_title,
        category=category,
        stage=stage,
        description=description,
        fields=fields,
        default_copies=copies,
        destinations=list(destinations),
        signatures=list(signatures),
        stamps=list(stamps),
        program_types=list(program_types),
        condition_flags=list(flags),
        conditional_note=conditional_note,
        official_layout=official_layout,
        official_form_number=official_form_number,
        official_file_name=official_file_name,
        official_download_url=(
            official_download_url
            or CGU_OFFICIAL_FORM_DOWNLOADS.get(official_form_number or "")
        ),
        paper_size=paper_size,
        print_sides=resolved_print_sides,
        print_note=resolved_print_note,
        attachment_field_order=ordered_attachment_fields,
        source_url=source_url,
        source_checked_at=(
            SHORT_TERM_SOURCE_CHECKED_AT
            if official_form_number in CGU_OFFICIAL_FORM_DOWNLOADS
            else SOURCE_CHECKED_AT
        ),
        version=version,
    )


def _profile_subset(*field_ids: str) -> list[ApplicationFormField]:
    selected = set(field_ids)
    return [field.model_copy(deep=True) for field in PROFILE_FIELDS if field.id in selected]


APPLICATION_TEMPLATES = [
    _template(
        "exchange-application-data",
        "校內交換申請資料整理表",
        "校內申請資料",
        category="申請",
        stage="校內申請",
        description="先整理線上申請會用到的個人、成績、語言與志願資料；正式送出仍在長庚公告的線上表單完成。",
        fields=[
            *PROFILE_FIELDS,
            _field("academic_average", "歷年學業平均", required=True, field_type=ApplicationFieldType.NUMBER),
            _field("class_rank_percent", "班級排名百分比", field_type=ApplicationFieldType.NUMBER, help_text="大學部學生填寫"),
            _field("language_test", "語言檢定", required=True, field_type=ApplicationFieldType.SELECT, options=("TOEIC", "IELTS", "TOEFL iBT", "Duolingo", "JLPT", "DELF", "其他")),
            _field("language_score", "語言成績／級別", required=True),
            _field("language_result_date", "成績取得日或預計取得日", required=True, field_type=ApplicationFieldType.DATE),
            _field("school_choices", "申請志願順序", required=True, field_type=ApplicationFieldType.TEXTAREA, placeholder="每行一間學校，依志願順序填寫", max_length=1500),
            _field("supporting_achievements", "其他有利審查資料", field_type=ApplicationFieldType.TEXTAREA, placeholder="獲獎、專題、社團或國際經驗，沒有可留白", max_length=2500),
        ],
        source_url=INITIAL_SOURCE_URL,
        destinations=("學生自存備份", "長庚線上申請表填寫參考"),
    ),
    _template(
        "guardian-consent",
        "交換研修家長／監護人同意資料表",
        "家長同意書",
        category="同意書",
        stage="校內申請",
        description="填好學生與監護人資料後產生列印版；官方同意書會在填完校內線上申請後寄至學生信箱。",
        fields=[
            *_profile_subset("student_name_zh", "student_id", "college", "department", "year_level"),
            _field("guardian_name", "家長／監護人姓名", required=True, profile="guardian_name"),
            _field("guardian_relation", "與學生關係", required=True, profile="guardian_relation"),
            _field("guardian_id_number", "家長／監護人身分證字號", required=True, profile="guardian_id_number", sensitive=True, help_text="只用於產生文件，請勿出現在公開貼文"),
            _field("planned_start_date", "預計出國日期", required=True, field_type=ApplicationFieldType.DATE),
            _field("planned_end_date", "預計返國日期", required=True, field_type=ApplicationFieldType.DATE),
            _field("overseas_institution", "海外學校／機構", required=True),
        ],
        source_url=INITIAL_SOURCE_URL,
        destinations=("長庚大學國際事務處",),
        signatures=("家長或監護人親筆簽名", "簽署日期"),
        conditional_note="官方版本會在完成線上申請後寄至申請信箱，送件前請核對最新版。",
    ),
    _template(
        "study-plan",
        "交換研修讀書計畫",
        "讀書計畫",
        category="計畫書",
        stage="校內申請",
        description="依長庚目前公開要求產生一頁中文讀書計畫，也可保留英文欄位供合作校申請重用。",
        fields=[
            *_profile_subset("student_name_zh", "student_id", "department"),
            _field("motivation", "申請動機", required=True, field_type=ApplicationFieldType.TEXTAREA, help_text="說明交換和你的學習方向、職涯目標有什麼關聯。", max_length=1800),
            _field("school_reason", "選擇這間學校的原因", required=True, field_type=ApplicationFieldType.TEXTAREA, help_text="具體寫出課程、師資或資源，不只描述國家與城市。", max_length=1800),
            _field("learning_goals", "研修目標", required=True, field_type=ApplicationFieldType.TEXTAREA, help_text="列出可驗證的語言、專業與跨文化目標。", max_length=1800),
            _field("course_plan", "預計修讀課程與安排", required=True, field_type=ApplicationFieldType.TEXTAREA, help_text="填入課名、學分與預計抵免方式；正式選課仍以合作校為準。", max_length=2200),
            _field("expected_outcomes", "預期成果", required=True, field_type=ApplicationFieldType.TEXTAREA, help_text="例如完成課程、作品、檢定或成果分享。", max_length=1600),
            _field("return_plan", "返國後規劃", required=True, field_type=ApplicationFieldType.TEXTAREA, help_text="說明學分採認、成果分享及後續學習安排。", max_length=1600),
            _field("english_version", "英文版讀書計畫（選填）", field_type=ApplicationFieldType.TEXTAREA, help_text="合作校要求英文版時可填；系統不會自行翻譯或改寫你的申請內容。", max_length=8000),
        ],
        source_url=INITIAL_SOURCE_URL,
        destinations=("校內初審資料", "合作校申請資料（如要求）"),
    ),
    _template(
        "selection-consent",
        "校內初審同意聲明資料表",
        "同意聲明書",
        category="聲明書",
        stage="校內初審通過後",
        description="確認接受校內推薦結果及後續申請責任；正式格式與期限以國際處通知為準。",
        fields=[
            *_profile_subset("student_name_zh", "student_id", "department", "email"),
            _field("nominated_school", "獲推薦學校", required=True),
            _field("acknowledge_deadlines", "我了解須自行完成合作校申請與期限", required=True, field_type=ApplicationFieldType.CHECKBOX),
            _field("acknowledge_costs", "我了解簽證、機票、保險及生活費等責任", required=True, field_type=ApplicationFieldType.CHECKBOX),
        ],
        source_url=INITIAL_SOURCE_URL,
        destinations=("長庚大學國際事務處",),
        signatures=("學生親筆簽名", "簽署日期"),
        conditional_note="初審結果公告後才需要，請依國際處當次通知期限送件。",
    ),
    _template(
        "course-preapproval",
        "學生赴境外修課與學分預選資料表",
        "課程預選／抵免",
        category="課程",
        stage="錄取後／出國前",
        description="把海外課程、學分與預計抵免科目先整理成表，方便與導師、授課老師及系所確認。",
        fields=[
            *_profile_subset("student_name_zh", "student_id", "college", "department", "degree_level"),
            _field("overseas_institution", "海外學校", required=True),
            _field("study_period", "研修期間", required=True),
            _field("overseas_courses", "海外課程與學分", required=True, field_type=ApplicationFieldType.TEXTAREA, placeholder="每行：課號｜課名｜學分", max_length=4000),
            _field("credit_mapping", "預計採認／抵免方式", required=True, field_type=ApplicationFieldType.TEXTAREA, placeholder="每行：海外課程 → 長庚課程或選修學分", max_length=4000),
            _field("advisor_name", "導師／授課教師", required=True),
        ],
        source_url=PREDEPARTURE_SOURCE_URL,
        copies=2,
        destinations=("系所／學程辦公室", "教務處註冊組或研教組"),
        signatures=("學生親筆簽名", "導師或授課教師簽名"),
        stamps=("系主任／所長核章", "相關行政單位核章"),
        conditional_note="官方申請表未包含在目前公開下載檔中，本頁先產生完整資料整理表。",
    ),
    _template(
        "dual-enrollment",
        "雙重學籍申請資料表",
        "雙重學籍申請",
        category="雙聯學位",
        stage="錄取後／出國前",
        description="僅雙聯學位學生需要，整理兩校、修讀期間與錄取資料，列印後附上國外大學錄取通知。",
        fields=[
            *_profile_subset("student_name_zh", "student_id", "college", "department", "degree_level"),
            _field("overseas_institution", "合作大學", required=True),
            _field("dual_degree_program", "雙聯學位計畫名稱", required=True),
            _field("planned_start_date", "開始日期", required=True, field_type=ApplicationFieldType.DATE),
            _field("planned_end_date", "預計完成日期", required=True, field_type=ApplicationFieldType.DATE),
            _field("admission_notice", "國外大學錄取通知", required=True, field_type=ApplicationFieldType.FILES, help_text="PDF 或圖片；列印時仍須附上完整通知"),
        ],
        source_url=PREDEPARTURE_SOURCE_URL,
        copies=2,
        destinations=("系所／學程辦公室", "教務處"),
        signatures=("學生親筆簽名",),
        stamps=("系所與院級核章",),
        program_types=("dual_degree",),
        conditional_note="只有修讀雙聯學位者需要。",
    ),
    _template(
        "overseas-affidavit",
        "出國研修切結書資料表",
        "出國研修切結書",
        category="切結書",
        stage="錄取後／出國前",
        description="確認保險、安全、學籍、聯繫及遵守兩校規定等責任，列印後由學生親簽。",
        fields=[
            *_profile_subset("student_name_zh", "student_id", "department", "email", "phone"),
            _field("overseas_institution", "海外學校", required=True),
            _field("overseas_address", "海外住宿地址", required=True, field_type=ApplicationFieldType.TEXTAREA, max_length=500),
            _field("emergency_contact", "緊急聯絡人", required=True, profile="emergency_contact"),
            _field("emergency_phone", "緊急聯絡電話", required=True, profile="emergency_phone", field_type=ApplicationFieldType.TEL),
            _field("insurance_provider", "保險公司／方案", required=True),
            _field("acknowledge_rules", "我已閱讀並同意遵守出國研修規定", required=True, field_type=ApplicationFieldType.CHECKBOX),
        ],
        source_url=PREDEPARTURE_SOURCE_URL,
        destinations=("長庚大學國際事務處",),
        signatures=("學生親筆簽名", "簽署日期"),
    ),
    _template(
        "military-service-overseas",
        "在學役男奉派或推薦出國資料表",
        "役男出國申請",
        category="出國程序",
        stage="錄取後／出國前",
        description="出國日前八週整理役男出國申請資料，並搭配已核簽的境外修課申請表辦理。",
        fields=[
            *_profile_subset("student_name_zh", "student_id", "college", "department", "year_level"),
            _field("id_number", "身分證字號", required=True, profile="id_number", sensitive=True),
            _field("birth_date", "出生日期", required=True, profile="birth_date", field_type=ApplicationFieldType.DATE, sensitive=True),
            _field("passport_number", "護照號碼", required=True, profile="passport_number", sensitive=True),
            _field("destination_country", "前往國家", required=True),
            _field("overseas_institution", "海外學校／機構", required=True),
            _field("planned_start_date", "出國日期", required=True, field_type=ApplicationFieldType.DATE),
            _field("planned_end_date", "返國日期", required=True, field_type=ApplicationFieldType.DATE),
        ],
        source_url=PREDEPARTURE_SOURCE_URL,
        copies=2,
        destinations=("系所／學程與院級核簽", "學務處生輔組"),
        signatures=("學生親筆簽名",),
        stamps=("系所與院級核章",),
        flags=("military_service",),
        conditional_note="只有具有在學役男身分者需要，須在出國日前八週辦理。",
    ),
    _template(
        "predeparture-notice",
        "出國通報資料表",
        "出國通報",
        category="出國程序",
        stage="錄取後／出國前",
        description="將出國日期、航班、住宿與緊急聯絡資料整理完成，再依長庚公告連結填寫正式線上通報單。",
        fields=[
            *_profile_subset("student_name_zh", "student_id", "email", "phone"),
            _field("passport_number", "護照號碼", required=True, profile="passport_number", sensitive=True),
            _field("destination_country", "研修國家", required=True),
            _field("overseas_institution", "海外學校", required=True),
            _field("departure_flight", "去程航班", required=True),
            _field("planned_start_date", "出國日期", required=True, field_type=ApplicationFieldType.DATE),
            _field("planned_end_date", "預計返國日期", required=True, field_type=ApplicationFieldType.DATE),
            _field("overseas_address", "海外住宿地址", required=True, field_type=ApplicationFieldType.TEXTAREA, max_length=500),
            _field("emergency_contact", "緊急聯絡人", required=True, profile="emergency_contact"),
            _field("emergency_phone", "緊急聯絡電話", required=True, profile="emergency_phone", field_type=ApplicationFieldType.TEL),
        ],
        source_url=PREDEPARTURE_SOURCE_URL,
        destinations=("長庚出國通報線上表單", "學生自存備份"),
        conditional_note="正式通報單須在出國前一個月於長庚公告的 Google 表單送出。",
    ),
    _template(
        "subsidy-receipt",
        "出國研修補助個人收據",
        "補助個人收據",
        category="補助",
        stage="補助核定後",
        description="產生兩份個人收據；依校方公開說明，金額與日期留白，列印後由學生本人親簽。",
        fields=[
            *_profile_subset("student_name_zh", "student_id", "department"),
            _field("id_number", "身分證字號", required=True, profile="id_number", sensitive=True),
            _field("mailing_address", "通訊地址", required=True, profile="mailing_address", field_type=ApplicationFieldType.TEXTAREA, max_length=500),
            _field("bank_last_five", "本人帳戶末五碼", required=True, sensitive=True, help_text="完整帳戶仍以校務資訊系統資料為準"),
            _field("subsidy_program", "補助計畫", required=True, field_type=ApplicationFieldType.SELECT, options=("長庚大學領航者補助", "教育部學海惜珠", "其他")),
        ],
        source_url=PREDEPARTURE_SOURCE_URL,
        copies=2,
        destinations=("長庚大學國際事務處",),
        signatures=("學生本人親筆簽名（每份都要）",),
        conditional_note="金額與日期依官方要求保留空白，收到承辦人通知後再辦理。",
        flags=("subsidy",),
        version="2026-10-03",
    ),
    _template(
        "administrative-contract",
        "出國研修補助行政契約資料表",
        "補助行政契約",
        category="補助",
        stage="補助核定後",
        description="把契約共用資料一次填入並產生一式三份；學生簽署後送國際處辦理學校蓋印。",
        fields=[
            *_profile_subset("student_name_zh", "student_id", "college", "department", "email", "phone"),
            _field("id_number", "身分證字號", required=True, profile="id_number", sensitive=True),
            _field("mailing_address", "通訊地址", required=True, profile="mailing_address", field_type=ApplicationFieldType.TEXTAREA, max_length=500),
            _field("overseas_institution", "研修學校", required=True),
            _field("destination_country", "研修國家", required=True),
            _field("study_period", "研修期間", required=True),
            _field("subsidy_program", "補助計畫", required=True, field_type=ApplicationFieldType.SELECT, options=("長庚大學領航者補助", "教育部學海惜珠", "其他")),
            _field("approved_amount", "核定補助金額", required=True, field_type=ApplicationFieldType.NUMBER),
        ],
        source_url=PREDEPARTURE_SOURCE_URL,
        copies=3,
        destinations=("長庚大學國際事務處（辦理用印）",),
        signatures=("學生親筆簽名（每份都要）",),
        stamps=("長庚大學用印",),
        flags=("subsidy",),
        conditional_note="依實際獲核定的補助類型選用國際處提供的最新版契約（長庚大學領航者補助作業要點行政契約書，或教育部學海惜珠之行政契約書）。",
        version="2026-10-03",
    ),
    _template(
        "arrival-checkin",
        "抵達國外報到資料表",
        "抵達國外報到",
        category="海外期間",
        stage="抵達後 14 天內",
        description="整理抵達日期、當地地址與緊急聯絡方式，再填入長庚公告的抵達國外報到表。",
        fields=[
            *_profile_subset("student_name_zh", "student_id", "email", "phone"),
            _field("overseas_institution", "海外學校", required=True),
            _field("arrival_date", "抵達日期", required=True, field_type=ApplicationFieldType.DATE),
            _field("overseas_address", "海外住宿地址", required=True, field_type=ApplicationFieldType.TEXTAREA, max_length=500),
            _field("local_phone", "當地電話", required=True, field_type=ApplicationFieldType.TEL),
            _field("emergency_contact", "緊急聯絡人", required=True, profile="emergency_contact"),
            _field("emergency_phone", "緊急聯絡電話", required=True, profile="emergency_phone", field_type=ApplicationFieldType.TEL),
        ],
        source_url=FLOW_SOURCE_URL,
        destinations=("長庚抵達國外報到線上表單", "學生自存備份"),
        conditional_note="須於抵達國外後 14 天內完成官方線上表單。",
    ),
    _template(
        "semester-report",
        "海外研修學期／學季報告",
        "學期／學季報告",
        category="海外期間",
        stage="海外研修期間",
        description="一年以上研修者在第一學期／學季結束後整理課程、生活與進度，產生上傳用報告。",
        fields=[
            *_profile_subset("student_name_zh", "student_id", "department"),
            _field("overseas_institution", "海外學校", required=True),
            _field("reporting_period", "報告期間", required=True),
            _field("courses_summary", "本期修課與學習進度", required=True, field_type=ApplicationFieldType.TEXTAREA, max_length=4500),
            _field("life_summary", "生活與適應狀況", required=True, field_type=ApplicationFieldType.TEXTAREA, max_length=3500),
            _field("issues_and_support", "遇到的問題與需要協助事項", field_type=ApplicationFieldType.TEXTAREA, max_length=2500),
            _field("activity_photos", "照片與圖說", field_type=ApplicationFieldType.FILES, help_text="最多 4 張，產生 PDF 時會排入報告", max_files=4),
        ],
        source_url=FLOW_SOURCE_URL,
        destinations=("長庚海外研修報告線上表單",),
        flags=("full_year",),
        conditional_note="就讀一學年以上者，第一學期／學季結束後 30 天內完成。",
    ),
    _template(
        "return-report",
        "出國研修返國心得與成果報告",
        "返國成果報告",
        category="返國",
        stage="返國後",
        description="把海外期間累積的筆記、照片與影片連結整理成可上傳及列印的返國成果報告。",
        fields=[
            *_profile_subset("student_name_zh", "student_id", "department"),
            _field("overseas_institution", "海外學校", required=True),
            _field("study_period", "研修期間", required=True),
            _field("courses_summary", "修課與學習成果", required=True, field_type=ApplicationFieldType.TEXTAREA, max_length=4500),
            _field("life_summary", "生活與文化適應", required=True, field_type=ApplicationFieldType.TEXTAREA, max_length=3500),
            _field("reflection", "心得與給學弟妹的建議", required=True, field_type=ApplicationFieldType.TEXTAREA, max_length=4500),
            _field("video_url", "心得影片連結", field_type=ApplicationFieldType.TEXT),
            _field("activity_photos", "照片與圖說", field_type=ApplicationFieldType.FILES, help_text="最多 4 張，產生 PDF 時會排入報告", max_files=4),
        ],
        source_url=FLOW_SOURCE_URL,
        destinations=("長庚大學國際事務處", "學生個人備份"),
    ),
    _template(
        "credit-transfer",
        "返國學分採認資料表",
        "返國學分採認",
        category="返國",
        stage="返國後",
        description="整理海外成績、課綱與預選結果，方便向系所與教務單位辦理學分採認。",
        fields=[
            *_profile_subset("student_name_zh", "student_id", "college", "department", "degree_level"),
            _field("overseas_institution", "海外學校", required=True),
            _field("completed_courses", "已完成課程與成績", required=True, field_type=ApplicationFieldType.TEXTAREA, placeholder="每行：課號｜課名｜學分｜成績", max_length=5000),
            _field("requested_mapping", "申請採認方式", required=True, field_type=ApplicationFieldType.TEXTAREA, placeholder="每行：海外課程 → 長庚課程或選修學分", max_length=5000),
            _field("transcript_attachment", "海外正式成績單", required=True, field_type=ApplicationFieldType.FILES),
            _field("syllabus_attachment", "課綱／授課內容", required=True, field_type=ApplicationFieldType.FILES),
        ],
        source_url=FLOW_SOURCE_URL,
        copies=2,
        destinations=("系所／學程辦公室", "教務處註冊組或研教組"),
        signatures=("學生親筆簽名",),
        stamps=("系所審核", "教務單位核章"),
    ),
    _template(
        "short-term-application-2b0001001",
        "長庚大學補助學生參加境外短期學分課程申請表",
        "短期課程申請表",
        category="短期學分",
        stage="短期課程申請",
        description="依長庚正式 2B0001001 範本填入教師、課程、海外機構、補助與學生名冊資料。",
        fields=[
            _field("application_date", "申請日期", required=True, field_type=ApplicationFieldType.DATE),
            _field("teacher_name", "申請教師姓名", required=True),
            _field("teacher_unit", "申請單位", required=True),
            _field("overseas_course_name", "境外課程名稱", required=True),
            _field("cgu_course_name", "本校課程名稱", required=True),
            _field("course_start_date", "課程開始日", required=True, field_type=ApplicationFieldType.DATE),
            _field("course_end_date", "課程結束日", required=True, field_type=ApplicationFieldType.DATE),
            _field("institution_name_zh", "海外學校／機構中文名稱", required=True),
            _field("institution_name_en", "海外學校／機構英文名稱", required=True),
            _field("institution_country", "國家", required=True),
            _field("contact_name", "海外聯絡人", required=True),
            _field("contact_phone", "海外聯絡電話", required=True, field_type=ApplicationFieldType.TEL),
            _field("contact_email", "海外聯絡 Email", required=True, field_type=ApplicationFieldType.EMAIL),
            _field("institution_address", "海外機構地址", required=True, field_type=ApplicationFieldType.TEXTAREA, max_length=700),
            _field("student_count", "參與學生人數", required=True, field_type=ApplicationFieldType.NUMBER),
            _field("airfare_per_student", "每位學生機票補助預估", required=True, field_type=ApplicationFieldType.NUMBER),
            _field("total_subsidy", "全團補助總額（新台幣）", required=True, field_type=ApplicationFieldType.NUMBER),
            _field("student_roster", "學生名冊", required=True, field_type=ApplicationFieldType.TEXTAREA, placeholder="每行：姓名｜學號｜系別｜生理性別｜Email（最多 5 人）", max_length=3000),
        ],
        source_url=SHORT_TERM_SOURCE_URL,
        destinations=("長庚大學國際事務處",),
        signatures=("申請教師簽名",),
        stamps=("申請單位核章",),
        program_types=("short_term_credit",),
        official_layout=True,
        official_form_number="2B0001001",
        official_file_name="2B0001001_長庚大學補助學生參加境外短期學分課程申請表.docx",
        version="2025-10-28",
    ),
    _template(
        "short-term-plan-2b0001002",
        "長庚大學補助學生參加境外短期學分課程計畫書",
        "短期課程計畫書",
        category="短期學分",
        stage="短期課程申請",
        description="依長庚正式 2B0001002 範本填入動機、執行方式、遴選資格、成果與返國義務。",
        fields=[
            _field("motivation", "動機與目標", required=True, field_type=ApplicationFieldType.TEXTAREA, max_length=3500),
            _field("implementation", "執行方式、時間、地點", required=True, field_type=ApplicationFieldType.TEXTAREA, max_length=3500),
            _field("selection_criteria", "學生遴選資格", required=True, field_type=ApplicationFieldType.TEXTAREA, max_length=2800),
            _field("expected_outcomes", "預期成效", required=True, field_type=ApplicationFieldType.TEXTAREA, max_length=2800),
            _field("return_obligations", "學生返國義務", required=True, field_type=ApplicationFieldType.TEXTAREA, max_length=2800),
            _field("other_information", "其他資料", field_type=ApplicationFieldType.TEXTAREA, max_length=2000),
        ],
        source_url=SHORT_TERM_SOURCE_URL,
        destinations=("長庚大學國際事務處",),
        program_types=("short_term_credit",),
        official_layout=True,
        official_form_number="2B0001002",
        official_file_name="2B0001002_長庚大學補助學生參加境外短期學分課程計畫書.docx",
        version="2025-10-28",
    ),
    _template(
        "short-term-guardian-consent-2b0001003",
        "長庚大學補助學生參加境外短期學分課程家長或監護人同意書",
        "短期課程家長同意書",
        category="短期學分",
        stage="短期課程申請",
        description="依長庚正式 2B0001003 範本填入學生、監護人、課程日期與海外機構，簽名欄保持空白。",
        fields=[
            *_profile_subset("student_name_zh", "student_id", "college", "department", "year_level"),
            _field("guardian_name", "家長／監護人姓名", required=True, profile="guardian_name"),
            _field("guardian_relation", "與學生關係", required=True, profile="guardian_relation"),
            _field("guardian_id_number", "家長／監護人身分證字號", required=True, profile="guardian_id_number", sensitive=True),
            _field("course_start_date", "課程開始日", required=True, field_type=ApplicationFieldType.DATE),
            _field("course_end_date", "課程結束日", required=True, field_type=ApplicationFieldType.DATE),
            _field("overseas_institution", "海外學校／機構", required=True),
        ],
        source_url=SHORT_TERM_SOURCE_URL,
        destinations=("長庚大學國際事務處",),
        signatures=("家長或監護人親筆簽名", "簽署日期"),
        program_types=("short_term_credit",),
        official_layout=True,
        official_form_number="2B0001003",
        official_file_name="2B0001003_長庚大學補助學生參加境外短期學分課程家長或監護人同意書.docx",
        version="2025-10-28",
    ),
    _template(
        "short-term-report-2b0001004",
        "長庚大學補助學生參加境外短期學分課程報告",
        "短期課程成果報告",
        category="短期學分",
        stage="短期課程返國後",
        description="依長庚正式 2B0001004 範本填入課程、活動、成果、心得、照片圖說及影片連結。",
        fields=[
            *_profile_subset("student_name_zh", "student_id"),
            _field("cgu_course_name", "本校課程名稱", required=True),
            _field("overseas_institution", "學校／機構／企業名稱", required=True),
            _field("course_start_date", "課程開始日", required=True, field_type=ApplicationFieldType.DATE),
            _field("course_end_date", "課程結束日", required=True, field_type=ApplicationFieldType.DATE),
            _field("activities", "課程經過及活動", required=True, field_type=ApplicationFieldType.TEXTAREA, max_length=4500),
            _field("outcomes", "課程成果", required=True, field_type=ApplicationFieldType.TEXTAREA, max_length=3500),
            _field("reflection", "心得與建議", required=True, field_type=ApplicationFieldType.TEXTAREA, max_length=4500),
            _field("video_url", "1 分鐘影片雲端連結", required=True),
            _field("activity_photos", "至少 4 張照片與圖說", required=True, field_type=ApplicationFieldType.FILES, help_text="選擇 4 張照片；系統會排入正式報告", min_files=4, max_files=4),
            _field("other_information", "其他", field_type=ApplicationFieldType.TEXTAREA, max_length=1800),
        ],
        source_url=SHORT_TERM_SOURCE_URL,
        destinations=("長庚大學國際事務處",),
        program_types=("short_term_credit",),
        official_layout=True,
        official_form_number="2B0001004",
        official_file_name="2B0001004_長庚大學補助學生參加境外短期學分課程報告.docx",
        version="2025-10-28",
    ),
]


def _ntpu_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    if template.id.startswith("short-term-"):
        return None
    replacements = (
        ("長庚大學", "國立臺北大學"),
        ("長庚", "臺北大學"),
        ("抵達後 14 天內", "抵達後 1 個月內"),
    )

    def replace(value: str) -> str:
        for original, updated in replacements:
            value = value.replace(original, updated)
        return value

    updates: dict[str, Any] = {
        "title": replace(template.title),
        "short_title": replace(template.short_title),
        "description": replace(template.description),
        "stage": replace(template.stage),
        "source_url": NTPU_EXCHANGE_GUIDELINES_URL,
        "destinations": [replace(value) for value in template.destinations],
        "signatures": [replace(value) for value in template.signatures],
        "stamps": [replace(value) for value in template.stamps],
        "conditional_note": replace(template.conditional_note) if template.conditional_note else None,
        "fields": [
            field.model_copy(
                deep=True,
                update={
                    "label": replace(field.label),
                    "placeholder": replace(field.placeholder) if field.placeholder else None,
                    "help_text": replace(field.help_text) if field.help_text else None,
                    "options": (
                        ["教育部學海飛颺", "教育部學海惜珠", "其他"]
                        if field.id == "subsidy_program"
                        else [replace(option) for option in field.options]
                    ),
                },
            )
            for field in template.fields
        ],
        "official_layout": False,
        "official_form_number": None,
        "official_file_name": None,
        "official_download_url": None,
        "version": "116學年度",
        "source_checked_at": NTPU_SOURCE_CHECKED_AT,
    }
    ntpu_overrides: dict[str, dict[str, Any]] = {
        "exchange-application-data": {
            "description": "整理臺北大學赴外交換線上申請所需的個人、成績、語言與志願資料；正式送出仍須在校方系統完成並上傳簽名申請表。",
            "destinations": ["臺北大學赴外交換生線上申請系統", "指定文件上傳表單", "學生自存備份"],
        },
        "guardian-consent": {
            "stage": "校內甄選通過後",
            "description": "獲校內推薦後，依國際處通知整理家長同意資料並完成親筆簽名。",
            "destinations": ["國立臺北大學國際事務處", "學生自存備份"],
        },
        "study-plan": {
            "description": "依所選語組撰寫交換研修計畫，包含學習背景、申請動機與未來研修規劃；A4 自由格式，最多 5,000 字。",
        },
        "selection-consent": {
            "title": "校內甄選錄取確認資料表",
            "short_title": "錄取確認",
            "stage": "校內甄選通過後",
            "description": "依國際處通知確認接受或放棄分發結果；接受後不得自行更換合作校。",
        },
        "course-preapproval": {
            "title": "出國選課行前申請資料表",
            "short_title": "出國選課行前申請",
            "description": "出國前先整理預計修課與學分採認方向，送系所及相關單位核章；返國後仍須依正式成績單與課程大綱辦理採認。",
        },
        "predeparture-notice": {
            "title": "出國前行程與緊急聯絡資料表",
            "short_title": "行前聯絡資料",
            "stage": "出國前",
            "description": "出國前整理航班、住宿、保險與緊急聯絡資料，作為個人行前檢查及臨時聯繫備份。",
            "destinations": ["學生自存備份"],
            "conditional_note": "此為準備工具；是否須另向校方通報，以國際處當期通知為準。",
        },
        "arrival-checkin": {
            "stage": "抵達後 1 個月內",
            "description": "抵達合作校 1 個月內回報當地聯絡資料與生活狀況，建立緊急聯絡網。",
            "destinations": ["國立臺北大學國際事務處", "學生自存備份"],
        },
        "return-report": {
            "description": "返國 1 個月內整理交換心得與成果，依國際處指定方式繳交。",
            "destinations": ["國立臺北大學國際事務處", "學生個人備份"],
        },
    }
    updates.update(ntpu_overrides.get(template.id, {}))
    return template.model_copy(deep=True, update=updates)


def _templates_for_school(school_name: str) -> list[ApplicationDocumentTemplate]:
    university = require_university(school_name)
    if university.id != NTPU.id:
        return [template.model_copy(deep=True) for template in APPLICATION_TEMPLATES]
    return [
        adapted
        for template in APPLICATION_TEMPLATES
        if (adapted := _ntpu_template(template)) is not None
    ]


def all_application_templates(
    school_name: str = "長庚大學",
) -> list[ApplicationDocumentTemplate]:
    return _templates_for_school(school_name)


def templates_for_context(context: ApplicationCenterContext) -> list[ApplicationDocumentTemplate]:
    flags = set(context.flags)
    return [
        template.model_copy(deep=True)
        for template in _templates_for_school(context.school_name)
        if context.program_type in template.program_types
        and set(template.condition_flags).issubset(flags)
    ]


def build_application_document_catalog(
    context: ApplicationCenterContext,
    workflows: Iterable[UniversityApplicationWorkflow],
) -> ApplicationDocumentCatalog:
    """Build a source-backed document catalog without guessing missing fields."""

    contact_unit = f"{context.school_name}國際事務處／所屬系所"
    workflow = select_application_workflow(
        workflows,
        ApplicationRuleContext(
            home_university=context.school_name,
            partner_university=context.target_school,
            college=context.college,
            department=context.department,
            academic_year=context.academic_year,
            application_round=context.application_round,
        ),
    )
    if workflow is None:
        return ApplicationDocumentCatalog(
            context=context,
            contact_unit=contact_unit,
        )

    workflow_is_published = (
        workflow.review_status == ApplicationWorkflowReviewStatus.PUBLISHED
    )
    items: list[ApplicationDocumentCatalogItem] = []
    sequence = 0
    for step in sorted(workflow.steps, key=lambda row: row.order):
        for requirement in step.document_requirements:
            sequence += 1
            needs_confirmation = (
                not workflow_is_published
                or step.needs_confirmation
                or requirement.needs_confirmation
            )
            official_form_url = (
                requirement.official_form_url
                if str(requirement.official_form_url or "").startswith("https://")
                else None
            )
            source_urls = list(
                dict.fromkeys(
                    [
                        *requirement.source_urls,
                        *([official_form_url] if official_form_url else []),
                        *step.source_urls,
                    ]
                )
            )
            identity = "|".join(
                (
                    context.school_name,
                    workflow.school_name,
                    str(step.order),
                    requirement.name,
                    str(sequence),
                )
            )
            items.append(
                ApplicationDocumentCatalogItem(
                    id=hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20],
                    sequence=sequence,
                    phase=step.phase,
                    step_title=step.title,
                    name=requirement.name,
                    copies=requirement.copies,
                    copy_type=requirement.copy_type,
                    signatures=requirement.signatures,
                    stamps=requirement.stamps,
                    official_form_url=official_form_url,
                    source_urls=source_urls,
                    source_checked_at=step.checked_at or workflow.last_checked,
                    support_status=(
                        ApplicationSupportStatus.NEEDS_CONFIRMATION
                        if needs_confirmation
                        else ApplicationSupportStatus.VERIFIED
                    ),
                    needs_confirmation=needs_confirmation,
                    download_available=bool(
                        official_form_url and not needs_confirmation
                    ),
                    contact_unit=(
                        step.confirmation_contact
                        or step.responsible_unit
                        or contact_unit
                        if needs_confirmation
                        else None
                    ),
                )
            )

    return ApplicationDocumentCatalog(
        context=context,
        workflow_found=True,
        workflow_coverage_status=workflow.coverage_status,
        workflow_review_status=workflow.review_status,
        academic_year=workflow.academic_year,
        application_round=workflow.application_round,
        items=items,
        contact_unit=contact_unit,
    )


def _has_value(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict, set)):
        return bool(value)
    return True


def _file_values(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return [value] if value else []


def _decode_data_url(
    value: Any,
    *,
    accepted_types: tuple[str, ...] = (),
) -> tuple[str, bytes] | None:
    data_url = value.get("data_url") if isinstance(value, dict) else value
    if not isinstance(data_url, str) or not data_url.startswith("data:") or "," not in data_url:
        return None
    header, encoded = data_url.split(",", 1)
    mime_type = header[5:].split(";", 1)[0].lower()
    if ";base64" not in header.lower():
        return None
    if accepted_types and mime_type not in accepted_types:
        return None
    try:
        raw = base64.b64decode(encoded, validate=True)
    except Exception:
        return None
    if not raw or len(raw) > 8 * 1024 * 1024:
        return None
    return mime_type, raw


def _attachment_file_name(
    value: Any,
    field: ApplicationFormField,
    index: int,
    media_type: str,
) -> str:
    supplied = value.get("name") or value.get("filename") if isinstance(value, dict) else None
    name = re.split(r"[\\/]", str(supplied or ""))[-1]
    name = re.sub(r"[\x00-\x1f\x7f]", "", name).strip()
    if name:
        return name[:255]
    extension = {
        "application/pdf": "pdf",
        "image/jpeg": "jpg",
        "image/png": "png",
    }[media_type]
    return f"{field.label}-{index}.{extension}"


def _inspect_attachment_payload(
    field: ApplicationFormField,
    value: Any,
    index: int,
) -> _AttachmentPayload | None:
    decoded = _decode_data_url(
        value,
        accepted_types=("application/pdf", "image/jpeg", "image/png"),
    )
    if decoded is None:
        return None
    media_type, raw = decoded
    page_count: int | None = None
    placement: Literal["after_document", "inside_document"]
    try:
        if media_type == "application/pdf":
            page_count = len(PdfReader(io.BytesIO(raw)).pages)
            if page_count < 1 or page_count > 200:
                return None
            placement = "after_document"
        else:
            width, height = ImageReader(io.BytesIO(raw)).getSize()
            if width < 1 or height < 1 or width * height > 40_000_000:
                return None
            placement = "inside_document"
    except Exception:
        return None
    return _AttachmentPayload(
        field_id=field.id,
        field_label=field.label,
        file_name=_attachment_file_name(value, field, index, media_type),
        media_type=media_type,
        raw=raw,
        page_count=page_count,
        placement=placement,
    )


def _attachment_payloads(
    field: ApplicationFormField,
    value: Any,
) -> tuple[list[_AttachmentPayload], str | None]:
    values = _file_values(value)
    payloads = [
        payload
        for index, item in enumerate(values[: field.max_files], start=1)
        if (payload := _inspect_attachment_payload(field, item, index)) is not None
    ]
    if len(values) > field.max_files:
        return payloads, f"最多只能加入 {field.max_files} 個檔案。"
    if len(payloads) != len(values):
        return payloads, "含有無法讀取或格式不符的檔案，請重新選擇 PDF、JPG 或 PNG。"
    return payloads, None


def _has_field_value(field: ApplicationFormField, value: Any) -> bool:
    if field.field_type != ApplicationFieldType.FILES:
        return _has_value(value)
    valid_files, _ = _attachment_payloads(field, value)
    minimum = max(field.min_files, 1 if field.required else 0)
    return len(valid_files) >= minimum


def answer_for_field(
    field: ApplicationFormField,
    profile: dict[str, Any],
    answers: dict[str, Any],
) -> Any:
    value = answers.get(field.id)
    if _has_value(value):
        return value
    if field.reusable_profile_key:
        return profile.get(field.reusable_profile_key)
    return value


def _attachment_fields_in_order(
    template: ApplicationDocumentTemplate,
) -> list[ApplicationFormField]:
    file_fields = {
        field.id: field
        for field in template.fields
        if field.field_type == ApplicationFieldType.FILES
    }
    ordered = [
        file_fields[field_id]
        for field_id in template.attachment_field_order
        if field_id in file_fields
    ]
    included = {field.id for field in ordered}
    ordered.extend(
        field
        for field in template.fields
        if field.field_type == ApplicationFieldType.FILES and field.id not in included
    )
    return ordered


def _canonical_review_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {
            str(key): _canonical_review_value(item)
            for key, item in sorted(value.items(), key=lambda row: str(row[0]))
            if key != "source_file"
        }
    if isinstance(value, (list, tuple)):
        return [_canonical_review_value(item) for item in value]
    return str(value)


def _field_is_blank(field: ApplicationFormField, value: Any) -> bool:
    if field.field_type != ApplicationFieldType.FILES:
        return not _has_value(value)
    payloads, _ = _attachment_payloads(field, value)
    return not payloads


def _review_content_sha256(
    request: ApplicationPacketRequest,
    template: ApplicationDocumentTemplate,
    selection: ApplicationDocumentSelection,
    review_key: bytes | None = None,
) -> str:
    answers = request.answers.get(template.id, {})
    snapshot = {
        "schema": "application-review-v1",
        "context": request.context.model_dump(mode="json"),
        "template": {
            "id": template.id,
            "version": template.version,
            "copies": selection.copies,
            "paper_size": template.paper_size,
            "print_sides": template.print_sides,
            "print_note": template.print_note,
            "destinations": template.destinations,
            "signatures": template.signatures,
            "stamps": template.stamps,
            "attachment_field_order": template.attachment_field_order,
        },
        "fields": [
            {
                "id": field.id,
                "value": _canonical_review_value(
                    answer_for_field(field, request.profile, answers)
                ),
            }
            for field in template.fields
        ],
    }
    encoded = json.dumps(
        snapshot,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    if review_key is not None:
        return hmac.new(review_key, encoded, hashlib.sha256).hexdigest()
    return hashlib.sha256(encoded).hexdigest()


def build_packet_manifest(
    request: ApplicationPacketRequest,
    *,
    review_key: bytes | None = None,
) -> ApplicationPacketManifest:
    applicable = {template.id: template for template in templates_for_context(request.context)}
    selections = request.selections or [
        ApplicationDocumentSelection(template_id=template.id, copies=template.default_copies)
        for template in applicable.values()
    ]
    items: list[ApplicationPacketManifestItem] = []
    for selection in selections:
        template = applicable.get(selection.template_id)
        if template is None:
            continue
        answers = request.answers.get(template.id, {})
        field_values = {
            field.id: answer_for_field(field, request.profile, answers)
            for field in template.fields
        }
        attachment_payloads: list[_AttachmentPayload] = []
        attachment_errors: dict[str, str] = {}
        for field in _attachment_fields_in_order(template):
            payloads, error = _attachment_payloads(field, field_values.get(field.id))
            attachment_payloads.extend(payloads)
            if error:
                attachment_errors[field.id] = error
        review_content_sha256 = _review_content_sha256(
            request,
            template,
            selection,
            review_key,
        )
        preview_fields = []
        for field in template.fields:
            value = field_values[field.id]
            preview_fields.append(
                ApplicationFieldPreviewItem(
                    field_id=field.id,
                    label=field.label,
                    field_type=field.field_type,
                    required=field.required,
                    sensitive=field.sensitive,
                    display_value=_format_value(value),
                    is_blank=_field_is_blank(field, value),
                    validation_error=attachment_errors.get(field.id),
                )
            )
        missing = [
            field.label
            for field in template.fields
            if field.required and not _has_field_value(field, field_values[field.id])
        ]
        attachments = [
            ApplicationPacketAttachmentItem(
                order=index,
                field_id=payload.field_id,
                field_label=payload.field_label,
                file_name=payload.file_name,
                media_type=payload.media_type,
                page_count=payload.page_count,
                placement=payload.placement,
            )
            for index, payload in enumerate(attachment_payloads, start=1)
        ]
        items.append(
            ApplicationPacketManifestItem(
                template_id=template.id,
                title=template.title,
                copies=selection.copies,
                template_version=template.version,
                review_content_sha256=review_content_sha256,
                reviewed=(
                    selection.reviewed_version == template.version
                    and selection.reviewed_content_sha256 == review_content_sha256
                ),
                preview_fields=preview_fields,
                destinations=template.destinations,
                signatures=template.signatures,
                stamps=template.stamps,
                paper_size=template.paper_size,
                print_sides=template.print_sides,
                print_note=template.print_note,
                attachment_order=list(dict.fromkeys(item.field_label for item in attachments)),
                attachments=attachments,
                invalid_attachment_fields=[
                    f"{field.label}：{attachment_errors[field.id]}"
                    for field in _attachment_fields_in_order(template)
                    if field.id in attachment_errors
                ],
                source_url=template.source_url,
                official_layout=template.official_layout,
                missing_required_fields=missing,
            )
        )
    return ApplicationPacketManifest(
        school_name=request.context.school_name,
        target_school=request.context.target_school,
        items=items,
        total_printed_copies=sum(item.copies for item in items),
        ready_to_generate=bool(items)
        and all(
            not item.missing_required_fields
            and not item.invalid_attachment_fields
            and item.reviewed
            for item in items
        ),
        source_checked_at=(
            NTPU_SOURCE_CHECKED_AT
            if require_university(request.context.school_name).id == NTPU.id
            else SOURCE_CHECKED_AT
        ),
    )


def _register_pdf_font() -> tuple[str, str]:
    regular = "ApplicationCJK"
    bold = "ApplicationCJKBold"
    candidates = [
        # Prefer the standalone TTF. ReportLab can reuse it across the separate
        # cover and document PDFs; Windows TTC fonts may corrupt later subsets.
        (Path("C:/Windows/Fonts/NotoSansTC-VF.ttf"), Path("C:/Windows/Fonts/NotoSansTC-VF.ttf")),
        (Path("C:/Windows/Fonts/kaiu.ttf"), Path("C:/Windows/Fonts/kaiu.ttf")),
        (Path("C:/Windows/Fonts/msjh.ttc"), Path("C:/Windows/Fonts/msjhbd.ttc")),
    ]
    for regular_path, bold_path in candidates:
        try:
            if regular not in pdfmetrics.getRegisteredFontNames():
                from reportlab.pdfbase.ttfonts import TTFont

                pdfmetrics.registerFont(TTFont(regular, str(regular_path)))
                pdfmetrics.registerFont(TTFont(bold, str(bold_path)))
            return regular, bold
        except Exception:
            continue
    if "MSung-Light" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(UnicodeCIDFont("MSung-Light"))
    return "MSung-Light", "MSung-Light"


def _styles() -> dict[str, ParagraphStyle]:
    regular, bold = _register_pdf_font()
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "ApplicationTitle",
            parent=base["Title"],
            fontName=bold,
            fontSize=22,
            leading=30,
            textColor=colors.HexColor("#17212B"),
            alignment=TA_LEFT,
            spaceAfter=10,
        ),
        "subtitle": ParagraphStyle(
            "ApplicationSubtitle",
            parent=base["Heading2"],
            fontName=bold,
            fontSize=13,
            leading=20,
            textColor=colors.HexColor("#0A73C9"),
            spaceBefore=8,
            spaceAfter=8,
        ),
        "body": ParagraphStyle(
            "ApplicationBody",
            parent=base["BodyText"],
            fontName=regular,
            fontSize=10.5,
            leading=17,
            textColor=colors.HexColor("#111827"),
            spaceAfter=5,
        ),
        "small": ParagraphStyle(
            "ApplicationSmall",
            parent=base["BodyText"],
            fontName=regular,
            fontSize=8.5,
            leading=13,
            textColor=colors.HexColor("#3F4B57"),
        ),
        "label": ParagraphStyle(
            "ApplicationLabel",
            parent=base["BodyText"],
            fontName=bold,
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#263442"),
        ),
        "center": ParagraphStyle(
            "ApplicationCenter",
            parent=base["BodyText"],
            fontName=bold,
            fontSize=10,
            leading=15,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#17212B"),
        ),
    }


def _paragraph(value: Any, style: ParagraphStyle) -> Paragraph:
    text = str(value or "").strip().replace("\n", "<br/>")
    return Paragraph(html.escape(text) if "<br/>" not in text else "<br/>".join(html.escape(part) for part in str(value or "").splitlines()), style)


def _format_value(value: Any) -> str:
    if value is True:
        return "已確認"
    if value is False or value is None:
        return ""
    if isinstance(value, list):
        names = []
        for item in value:
            if isinstance(item, dict):
                names.append(str(item.get("name") or item.get("filename") or "附件"))
            elif isinstance(item, str) and item.startswith("data:"):
                names.append("已附圖片")
            else:
                names.append(str(item))
        return "、".join(names)
    if isinstance(value, dict):
        return "、".join(f"{key}: {item}" for key, item in value.items())
    return str(value)


def _pdf_document(
    story: list[Any],
    *,
    title: str,
    margins: tuple[float, float, float, float] = (18 * mm, 18 * mm, 18 * mm, 18 * mm),
) -> bytes:
    buffer = io.BytesIO()
    left, right, top, bottom = margins
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        title=title,
        author="台灣大學生交換指南",
        leftMargin=left,
        rightMargin=right,
        topMargin=top,
        bottomMargin=bottom,
    )
    doc.build(story)
    return buffer.getvalue()


def _manifest_cover(request: ApplicationPacketRequest, manifest: ApplicationPacketManifest) -> bytes:
    styles = _styles()
    program_labels = {
        "exchange": "學期／學年交換",
        "dual_degree": "雙聯學位",
        "internship": "海外實習",
        "short_term_credit": "境外短期學分課程",
    }
    story: list[Any] = [
        Paragraph("交換申請列印包", styles["title"]),
        Paragraph("系統只協助填表與整理送件，不會替學生向學校或外部系統送出申請。", styles["body"]),
        Spacer(1, 5 * mm),
    ]
    summary = [
        [Paragraph("目前學校", styles["label"]), Paragraph(request.context.school_name, styles["body"])],
        [Paragraph("目標學校", styles["label"]), Paragraph(request.context.target_school or "尚未指定", styles["body"])],
        [Paragraph("計畫／學期", styles["label"]), Paragraph(f"{program_labels.get(request.context.program_type, request.context.program_type)} · {request.context.academic_year or '未填'} {request.context.semester or ''}", styles["body"])],
        [Paragraph("列印總份數", styles["label"]), Paragraph(str(manifest.total_printed_copies), styles["body"])],
    ]
    summary_table = Table(summary, colWidths=[35 * mm, 125 * mm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EEF7FF")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#C6D5E2")),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D8E2EA")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.extend([summary_table, Spacer(1, 8 * mm), Paragraph("列印與送件清單", styles["subtitle"])])
    print_side_labels = {
        "single_sided": "單面",
        "double_sided": "雙面",
        "confirm_official": "待確認官方單雙面規定",
    }
    rows = [[
        Paragraph("文件", styles["label"]),
        Paragraph("份數", styles["label"]),
        Paragraph("列印與附件", styles["label"]),
        Paragraph("交件與簽核", styles["label"]),
    ]]
    for item in manifest.items:
        actions = [*(f"交至：{value}" for value in item.destinations), *(f"簽名：{value}" for value in item.signatures), *(f"核章：{value}" for value in item.stamps)]
        attachment_details = [
            (
                f"{attachment.order}. {attachment.field_label}：{attachment.file_name}"
                + (
                    f"（PDF {attachment.page_count} 頁，接在文件後）"
                    if attachment.placement == "after_document"
                    else "（排入文件內）"
                )
            )
            for attachment in item.attachments
        ]
        print_details = [
            f"紙張：{item.paper_size}",
            f"單雙面：{print_side_labels[item.print_sides]}",
            "附件順序：" + ("；".join(attachment_details) if attachment_details else "無"),
        ]
        if item.print_note:
            print_details.append(item.print_note)
        rows.append([
            Paragraph(html.escape(item.title), styles["body"]),
            Paragraph(str(item.copies), styles["center"]),
            Paragraph("<br/>".join(html.escape(value) for value in print_details), styles["small"]),
            Paragraph("<br/>".join(html.escape(value) for value in actions) or "學生自存", styles["small"]),
        ])
    table = Table(rows, colWidths=[46 * mm, 14 * mm, 52 * mm, 48 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E9F4FD")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#C4D3DF")),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D6E0E8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.extend([
        table,
        Spacer(1, 8 * mm),
        Paragraph("列印後待辦", styles["subtitle"]),
        Paragraph("1. 依上表的份數、紙張與單雙面設定列印，每一份文件都要附上該列所列附件。", styles["small"]),
        Paragraph("2. 依編號放置附件，再完成本人、家長、教授或系所需要的簽名與核章。", styles["small"]),
        Paragraph("3. 由學生依上表交件單位與當期公告自行送件；本系統沒有代替學生送出申請。", styles["small"]),
        Paragraph("列印後請逐份確認簽名、日期、附件與核章。官方規定可能調整，送件前仍須核對來源頁及承辦人通知。", styles["small"]),
        Paragraph("這份 PDF 只在本次請求中產生並回傳，伺服器不會永久保存；若要跨裝置保存，必須在私人文件庫另外同意。", styles["small"]),
        Paragraph(f"資料來源最後檢查：{manifest.source_checked_at.astimezone().strftime('%Y/%m/%d')}", styles["small"]),
    ])
    return _pdf_document(story, title="交換申請列印包")


def _data_url_image(value: Any, max_width: float = 70 * mm, max_height: float = 50 * mm) -> Image | None:
    decoded = _decode_data_url(
        value,
        accepted_types=("image/jpeg", "image/png"),
    )
    if decoded is None:
        return None
    try:
        _, raw = decoded
        image = Image(io.BytesIO(raw))
        ratio = min(max_width / image.imageWidth, max_height / image.imageHeight, 1)
        image.drawWidth = image.imageWidth * ratio
        image.drawHeight = image.imageHeight * ratio
        return image
    except Exception:
        return None


def _uploaded_pdf_attachments(
    template: ApplicationDocumentTemplate,
    request: ApplicationPacketRequest,
) -> list[bytes]:
    answers = request.answers.get(template.id, {})
    attachments: list[bytes] = []
    for field in _attachment_fields_in_order(template):
        value = answer_for_field(field, request.profile, answers)
        payloads, _ = _attachment_payloads(field, value)
        attachments.extend(
            payload.raw
            for payload in payloads
            if payload.media_type == "application/pdf"
        )
    return attachments


def _generic_template_pdf(
    template: ApplicationDocumentTemplate,
    request: ApplicationPacketRequest,
    copy_number: int,
) -> bytes:
    styles = _styles()
    answers = request.answers.get(template.id, {})
    story: list[Any] = [
        Paragraph(html.escape(template.title), styles["title"]),
        Paragraph(
            f"第 {copy_number} 份／共 {next((item.copies for item in request.selections if item.template_id == template.id), template.default_copies)} 份",
            styles["small"],
        ),
        Spacer(1, 3 * mm),
    ]
    if not template.official_layout:
        story.append(Paragraph("資料整理列印版", styles["subtitle"]))
        story.append(Paragraph("此頁依公開要求整理填寫資料；若校方另提供正式表格，請將本頁內容轉入最新版正式表格。", styles["small"]))
        story.append(Spacer(1, 4 * mm))
    rows: list[list[Any]] = []
    photo_values: list[Any] = []
    for field in template.fields:
        value = answer_for_field(field, request.profile, answers)
        if field.field_type == ApplicationFieldType.FILES:
            values = value if isinstance(value, list) else ([value] if value else [])
            photo_values.extend(item for item in values if _data_url_image(item) is not None)
        formatted = _format_value(value)
        rows.append([
            Paragraph(html.escape(field.label), styles["label"]),
            Paragraph(html.escape(formatted).replace("\n", "<br/>") or "&nbsp;", styles["body"]),
        ])
    table = Table(rows, colWidths=[47 * mm, 113 * mm], repeatRows=0)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F3F7FA")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#BCCAD6")),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D7E0E7")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(table)
    if photo_values:
        story.extend([PageBreak(), Paragraph("照片附件", styles["subtitle"])])
        images = []
        for value in photo_values[:8]:
            picture = _data_url_image(value)
            if picture:
                caption = value.get("name", "照片") if isinstance(value, dict) else "照片"
                images.append(KeepTogether([picture, Paragraph(html.escape(caption), styles["small"]), Spacer(1, 4 * mm)]))
        story.extend(images)
    if template.signatures or template.stamps:
        story.extend([Spacer(1, 8 * mm), Paragraph("列印後完成", styles["subtitle"])])
        action_rows = []
        for kind, labels in (("簽名", template.signatures), ("核章", template.stamps)):
            for label in labels:
                action_rows.append([
                    Paragraph(f"{kind}｜{html.escape(label)}", styles["label"]),
                    Paragraph("\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000", styles["body"]),
                ])
        action_table = Table(action_rows, colWidths=[65 * mm, 95 * mm], rowHeights=[18 * mm] * len(action_rows))
        action_table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#9BAAB6")),
            ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#C7D1D8")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(action_table)
    story.extend([
        Spacer(1, 6 * mm),
        Paragraph(f"官方來源：{html.escape(template.source_url)}", styles["small"]),
        Paragraph(f"範本版本：{html.escape(template.version)} · 最後檢查：{template.source_checked_at.astimezone().strftime('%Y/%m/%d')}", styles["small"]),
    ])
    return _pdf_document(story, title=template.title)


def _set_cell(table: Any, row: int, column: int, value: Any) -> None:
    table.cell(row, column).text = str(value or "")


def _append_cell(table: Any, row: int, column: int, value: Any) -> None:
    cell = table.cell(row, column)
    cell.add_paragraph(str(value or ""))


def _days_between(start: str, end: str) -> int | str:
    try:
        left = datetime.strptime(start, "%Y-%m-%d")
        right = datetime.strptime(end, "%Y-%m-%d")
        return (right - left).days + 1
    except Exception:
        return ""


def _fill_official_docx(
    template: ApplicationDocumentTemplate,
    request: ApplicationPacketRequest,
    source_path: Path,
    target_path: Path,
) -> None:
    shutil.copy2(source_path, target_path)
    document = Document(target_path)
    values = {
        field.id: answer_for_field(field, request.profile, request.answers.get(template.id, {}))
        for field in template.fields
    }
    if template.official_form_number == "2B0001001":
        table = document.tables[0]
        _set_cell(table, 0, 1, values.get("teacher_name"))
        _set_cell(table, 0, 7, values.get("teacher_unit"))
        _set_cell(table, 1, 1, values.get("overseas_course_name"))
        _set_cell(table, 2, 1, values.get("cgu_course_name"))
        start, end = str(values.get("course_start_date") or ""), str(values.get("course_end_date") or "")
        _set_cell(table, 3, 1, f"自 {start} 至 {end}，共計 {_days_between(start, end)} 天")
        _set_cell(table, 4, 1, f"中文：{values.get('institution_name_zh', '')}（{values.get('institution_country', '')}）")
        _set_cell(table, 5, 1, f"英文：{values.get('institution_name_en', '')}")
        _set_cell(table, 6, 1, f"聯絡人：{values.get('contact_name', '')}　電話：{values.get('contact_phone', '')}　電子信箱：{values.get('contact_email', '')}")
        _set_cell(table, 7, 1, f"地址：{values.get('institution_address', '')}")
        _set_cell(table, 8, 1, f"學生人數：{values.get('student_count', '')}")
        _set_cell(table, 9, 3, f"機票費：{values.get('airfare_per_student', '')} 元 × {values.get('student_count', '')} 人")
        _set_cell(table, 10, 3, f"{values.get('total_subsidy', '')} 元")
        roster = [line for line in str(values.get("student_roster") or "").splitlines() if line.strip()]
        for offset, line in enumerate(roster[:5], start=12):
            columns = [part.strip() for part in re.split(r"[|｜,，\t]", line)]
            for column, value in zip((1, 2, 4, 6, 8), columns):
                _set_cell(table, offset, column, value)
        for paragraph in document.paragraphs:
            if paragraph.text.strip().startswith("申請日："):
                paragraph.text = f"申請日：{values.get('application_date', '')}"
    elif template.official_form_number == "2B0001002":
        table = document.tables[0]
        for row, key in enumerate(("motivation", "implementation", "selection_criteria", "expected_outcomes", "return_obligations", "other_information")):
            _append_cell(table, row, 0, values.get(key))
    elif template.official_form_number == "2B0001003":
        college = re.sub(r"學院$", "", str(values.get("college") or ""))
        department = re.sub(r"(?:學系|研究所|系|所)$", "", str(values.get("department") or ""))
        replacement = (
            f"本人（家長或監護人姓名）{values.get('guardian_name', '')} 已充分瞭解赴境外短期學分課程之學習、生活狀況及相關條件，"
            f"同意敝子弟 {values.get('student_name_zh', '')} 現就讀貴校 {college} 院 {department} 系（所）"
            f"{values.get('year_level', '')}（學號：{values.get('student_id', '')}），參加貴校辦理之境外短期學分課程，"
            f"計畫於 {values.get('course_start_date', '')} 至 {values.get('course_end_date', '')} 赴 {values.get('overseas_institution', '')} 學習。"
        )
        for paragraph in document.paragraphs:
            text = paragraph.text.strip()
            if text.startswith("本人(家長或監護人姓名)"):
                paragraph.text = replacement
            elif text.startswith("赴") and "機構" in text:
                paragraph.text = ""
            elif text.startswith("家長/監護人簽名"):
                paragraph.text = "家長／監護人簽名：_______________________"
            elif text.startswith("與學生關係"):
                paragraph.text = f"與學生關係：{values.get('guardian_relation', '')}"
            elif text.startswith("身分證字號"):
                paragraph.text = f"身分證字號：{values.get('guardian_id_number', '')}"
            elif text.startswith("日") and "期" in text:
                paragraph.text = "日　　　期：____________________________"
    elif template.official_form_number == "2B0001004":
        table = document.tables[0]
        _set_cell(table, 0, 1, values.get("student_name_zh"))
        _set_cell(table, 0, 3, values.get("student_id"))
        _set_cell(table, 1, 1, values.get("cgu_course_name"))
        _set_cell(table, 2, 1, values.get("overseas_institution"))
        _set_cell(table, 3, 1, f"{values.get('course_start_date', '')} 至 {values.get('course_end_date', '')}")
        _append_cell(table, 4, 0, values.get("activities"))
        _append_cell(table, 5, 0, values.get("outcomes"))
        _append_cell(table, 6, 0, f"{values.get('reflection', '')}\n影片：{values.get('video_url', '')}")
        _append_cell(table, 7, 0, values.get("other_information"))
        for index, item in enumerate(_file_values(values.get("activity_photos"))[:4], start=1):
            decoded = _decode_data_url(
                item,
                accepted_types=("image/jpeg", "image/png"),
            )
            if decoded is None:
                continue
            _, raw = decoded
            try:
                paragraph = table.cell(4, 0).add_paragraph()
                paragraph.add_run().add_picture(io.BytesIO(raw), width=Inches(2.35))
                name = item.get("name") if isinstance(item, dict) else None
                paragraph.add_run(f"\n照片 {index}：{name or '活動照片'}")
            except Exception:
                continue
    document.save(target_path)


def _word_docx_to_pdf(docx_path: Path, pdf_path: Path) -> bool:
    if os.name != "nt":
        return False
    try:
        import pythoncom
        import win32com.client

        pythoncom.CoInitialize()
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        opened = word.Documents.Open(str(docx_path.resolve()), ReadOnly=False, AddToRecentFiles=False)
        try:
            opened.ExportAsFixedFormat(str(pdf_path.resolve()), 17)
        finally:
            opened.Close(False)
            word.Quit()
            pythoncom.CoUninitialize()
        return pdf_path.exists() and pdf_path.stat().st_size > 1000
    except Exception:
        try:
            word.Quit()  # type: ignore[possibly-undefined]
        except Exception:
            pass
        try:
            pythoncom.CoUninitialize()  # type: ignore[possibly-undefined]
        except Exception:
            pass
        return False


def _official_template_pdf(
    template: ApplicationDocumentTemplate,
    request: ApplicationPacketRequest,
    raw_files_dir: Path,
) -> bytes | None:
    if not template.official_file_name:
        return None
    source = raw_files_dir / template.official_file_name
    if not source.exists():
        return None
    with tempfile.TemporaryDirectory(prefix="exchange-form-") as directory:
        workdir = Path(directory)
        docx_path = workdir / "filled.docx"
        pdf_path = workdir / "filled.pdf"
        _fill_official_docx(template, request, source, docx_path)
        if not _word_docx_to_pdf(docx_path, pdf_path):
            return None
        return pdf_path.read_bytes()


def generate_application_packet_pdf(
    request: ApplicationPacketRequest,
    *,
    raw_files_dir: Path,
    review_key: bytes | None = None,
) -> tuple[bytes, ApplicationPacketManifest]:
    manifest = build_packet_manifest(request, review_key=review_key)
    if not manifest.items:
        raise ValueError("請至少選擇一份要產生的文件。")
    missing = [
        f"{item.title}：{', '.join(item.missing_required_fields)}"
        for item in manifest.items
        if item.missing_required_fields
    ]
    if missing:
        raise ValueError("仍有必填欄位未完成。" + "；".join(missing))
    invalid_attachments = [
        f"{item.title}：{', '.join(item.invalid_attachment_fields)}"
        for item in manifest.items
        if item.invalid_attachment_fields
    ]
    if invalid_attachments:
        raise ValueError("仍有附件無法加入列印包。" + "；".join(invalid_attachments))
    unreviewed = [item.title for item in manifest.items if not item.reviewed]
    if unreviewed:
        raise ValueError(
            "仍有文件尚未完成目前內容的「我已核對」，或核對後資料已變更："
            + "、".join(unreviewed)
        )
    applicable = {template.id: template for template in templates_for_context(request.context)}
    writer = PdfWriter()
    # Keep every reader alive until write(). PdfWriter tracks cloned objects by
    # reader identity; temporary readers can be garbage-collected and have their
    # ids reused, which can attach the cover's font resources to later pages.
    source_readers: list[PdfReader] = []

    def append_pdf(pdf_bytes: bytes) -> None:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        source_readers.append(reader)
        for page in reader.pages:
            writer.add_page(page)

    append_pdf(_manifest_cover(request, manifest))
    for item in manifest.items:
        template = applicable[item.template_id]
        official = _official_template_pdf(template, request, raw_files_dir) if template.official_layout else None
        attachments = _uploaded_pdf_attachments(template, request)
        for copy_number in range(1, item.copies + 1):
            rendered = official or _generic_template_pdf(template, request, copy_number)
            append_pdf(rendered)
            for attachment in attachments:
                append_pdf(attachment)
    writer.add_metadata(
        {
            "/Title": "交換申請列印包",
            "/Author": "台灣大學生交換指南",
            "/Subject": "待學生核對、列印、簽名與送件的申請文件套件",
        }
    )
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue(), manifest
