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
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Literal

from docx import Document
from docx.enum.table import WD_ROW_HEIGHT_RULE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Mm, Pt, RGBColor
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
from .application_writing_guidance import apply_writing_guidance
from .ccu_sources import CHECKED_AT as CCU_SOURCE_CHECKED_AT
from .ncu_document_conditions import document_applicability, preparation_state_key
from .university_registry import CMU, CSMU, CYCU, FCU, FJU, KMU, MCU, NCCU, NCHU, NCKU, NCNU, NCUE, NCYU, NDHU, NFU, NKNU, NKUST, NSYSU, NTHU, NTNU, NTOU, NTPU, NTU, NTUB, NUTC, NTUST, NTUT, NCU, NUK, NYCU, PCCU, PU, SCU, SHU, THU, TMU, USC, UTAIPEI, NTCU, WZU, YUNTECH, YZU, require_university, resolve_university
from .ntu_student_view import NTU_GUIDELINES_URL
from .ncu_student_view import NCU_GUIDELINES_URL, NCU_CHECKED_AT, NCU_FORMS_URL
from .fju_student_view import FJU_PROCESS_URL

FJU_SOURCE_CHECKED_AT = datetime(2026, 10, 16, tzinfo=timezone.utc)
SCU_SOURCE_CHECKED_AT = datetime(2026, 10, 16, tzinfo=timezone.utc)
NTNU_SOURCE_CHECKED_AT = datetime(2026, 10, 28, tzinfo=timezone.utc)
CYCU_SOURCE_CHECKED_AT = datetime(2026, 10, 28, tzinfo=timezone.utc)
NTUST_SOURCE_CHECKED_AT = datetime(2026, 10, 16, tzinfo=timezone.utc)
YZU_SOURCE_CHECKED_AT = datetime(2026, 10, 17, tzinfo=timezone.utc)
FCU_SOURCE_CHECKED_AT = datetime(2026, 10, 17, tzinfo=timezone.utc)
NSYSU_SOURCE_CHECKED_AT = datetime(2026, 10, 28, tzinfo=timezone.utc)
NCHU_SOURCE_CHECKED_AT = datetime(2026, 10, 18, tzinfo=timezone.utc)
NTUT_SOURCE_CHECKED_AT = datetime(2026, 10, 18, tzinfo=timezone.utc)
NCCU_SOURCE_CHECKED_AT = datetime(2026, 10, 18, tzinfo=timezone.utc)
NCKU_SOURCE_CHECKED_AT = datetime(2026, 10, 18, tzinfo=timezone.utc)
NYCU_SOURCE_CHECKED_AT = datetime(2026, 10, 19, tzinfo=timezone.utc)
NTHU_SOURCE_CHECKED_AT = datetime(2026, 10, 19, tzinfo=timezone.utc)
PCCU_SOURCE_CHECKED_AT = datetime(2026, 10, 19, tzinfo=timezone.utc)
WZU_SOURCE_CHECKED_AT = datetime(2026, 10, 19, tzinfo=timezone.utc)
NKUST_SOURCE_CHECKED_AT = datetime(2026, 10, 20, tzinfo=timezone.utc)
YUNTECH_SOURCE_CHECKED_AT = datetime(2026, 10, 20, tzinfo=timezone.utc)
NTOU_SOURCE_CHECKED_AT = datetime(2026, 10, 20, tzinfo=timezone.utc)
NCUE_SOURCE_CHECKED_AT = datetime(2026, 10, 20, tzinfo=timezone.utc)
NKNU_SOURCE_CHECKED_AT = datetime(2026, 10, 20, tzinfo=timezone.utc)
TMU_SOURCE_CHECKED_AT = datetime(2026, 10, 20, tzinfo=timezone.utc)
CSMU_SOURCE_CHECKED_AT = datetime(2026, 10, 21, tzinfo=timezone.utc)
CMU_SOURCE_CHECKED_AT = datetime(2026, 10, 21, tzinfo=timezone.utc)
KMU_SOURCE_CHECKED_AT = datetime(2026, 10, 21, tzinfo=timezone.utc)
MCU_SOURCE_CHECKED_AT = datetime(2026, 10, 21, tzinfo=timezone.utc)
NTUB_SOURCE_CHECKED_AT = datetime(2026, 10, 22, tzinfo=timezone.utc)
NCNU_SOURCE_CHECKED_AT = datetime(2026, 10, 27, tzinfo=timezone.utc)
NDHU_SOURCE_CHECKED_AT = datetime(2026, 10, 28, tzinfo=timezone.utc)
THU_SOURCE_CHECKED_AT = datetime(2026, 10, 28, tzinfo=timezone.utc)
SHU_SOURCE_CHECKED_AT = datetime(2026, 10, 30, tzinfo=timezone.utc)
PU_SOURCE_CHECKED_AT = datetime(2026, 10, 30, tzinfo=timezone.utc)
USC_SOURCE_CHECKED_AT = datetime(2026, 10, 30, tzinfo=timezone.utc)
NUK_SOURCE_CHECKED_AT = datetime(2026, 10, 30, tzinfo=timezone.utc)
NCYU_SOURCE_CHECKED_AT = datetime(2026, 10, 30, tzinfo=timezone.utc)
NUTC_SOURCE_CHECKED_AT = datetime(2026, 10, 31, tzinfo=timezone.utc)
NFU_SOURCE_CHECKED_AT = datetime(2026, 10, 31, tzinfo=timezone.utc)
UTAIPEI_SOURCE_CHECKED_AT = datetime(2026, 10, 31, tzinfo=timezone.utc)
NTCU_SOURCE_CHECKED_AT = datetime(2026, 10, 31, tzinfo=timezone.utc)


FLOW_SOURCE_URL = "https://www.cgu.edu.tw/oia-ch/Subject?nodeId=15680"
INITIAL_SOURCE_URL = "https://www.cgu.edu.tw/oia-ch/Subject/Detail/56388?nodeId=15680"
PREDEPARTURE_SOURCE_URL = "https://www.cgu.edu.tw/oia-ch/Subject/Detail/56390?nodeId=15680"
SHORT_TERM_SOURCE_URL = (
    "https://www.cgu.edu.tw/regulation/RegulationManagement/RegulationDetail/"
    "188edb21-5c53-4cbe-9e55-81089f90528b"
)
SOURCE_CHECKED_AT = datetime(2026, 7, 16, tzinfo=timezone.utc)
NTPU_SOURCE_CHECKED_AT = datetime(2026, 10, 3, tzinfo=timezone.utc)
NTU_SOURCE_CHECKED_AT = datetime(2026, 10, 7, tzinfo=timezone.utc)
NTPU_EXCHANGE_GUIDELINES_URL = (
    "https://cms-carrier.ntpu.edu.tw/uploads/116_16e535159d.pdf"
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


def _ntu_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    descriptions = {
        "exchange-application-data": "整理臺大116-1校級甄選個人資料與附件；正式報名須在校方甄選系統完成。學士生以學年GPA至少2.44或班排前50%擇一符合，研究生無校內成績門檻。",
        "study-plan": "撰寫臺大出國交換計畫書：中／英文、A4兩面、至少500字；履歷另備A4兩面。正式附件以當期簡章為準。",
        "course-preapproval": "整理預計修課、課程大綱與學分採認問題，向臺大所屬系所確認；這份準備表不代替校方正式表格。",
        "predeparture-notice": "整理航班、住宿、保險與緊急聯絡資料；正式繳交內容與期限依臺大當期行前通知。",
        "return-report": "整理交換學習與生活成果；正式心得格式、繳交方式與期限依臺大當期返國及補助通知。",
        "credit-transfer": "整理合作校成績單、課程大綱與學分採認需求；採認須依臺大所屬系所及教務規定辦理。",
    }
    if template.id not in descriptions:
        return None
    def adapt(value):
        if isinstance(value, str):
            return value.replace("長庚大學", "國立臺灣大學").replace("長庚", "臺大")
        if isinstance(value, list):
            return [adapt(item) for item in value]
        if isinstance(value, dict):
            return {key: adapt(item) for key, item in value.items()}
        return value
    payload = adapt(template.model_dump(mode="json"))
    language_groups = ["一般組", "日語組", "德語組", "法語組", "韓語組", "西語組", "中語組"]
    english_tests = ["TOEFL iBT（舊制120分）", "TOEFL iBT（新制6分）", "IELTS Academic", "GEPT", "BESTEP"]
    substitutes = ["母語證明（須先洽國際處）", "國外前一學位證明（須先洽國際處）"]
    group_tests = {
        "一般組": english_tests + ["其他簡章列明語言證明"] + substitutes,
        "日語組": ["JLPT"] + substitutes,
        "德語組": ["德語檢定", "FLPT（德語）"] + english_tests + substitutes,
        "法語組": ["法語檢定", "FLPT（法語）"] + english_tests + substitutes,
        "韓語組": ["TOPIK", "KLAT"] + english_tests + substitutes,
        "西語組": ["西語檢定", "FLPT（西語）"] + english_tests + substitutes,
        "中語組": ["TOCFL", "HSK"],
    }
    if template.id == "exchange-application-data":
        payload["fields"][0:0] = [
            _field("language_group", "臺大甄選語組", required=True,
                   field_type=ApplicationFieldType.SELECT, options=language_groups).model_dump(mode="json"),
            _field("international_degree_student", "是否為國際學位生", required=True,
                   field_type=ApplicationFieldType.SELECT, options=["否", "是"],
                   help_text="中語組一般申請者無校內語檢要求；國際學位生須提供TOCFL或HSK。合作校要求另查。").model_dump(mode="json"),
        ]
    for field in payload["fields"]:
        if field["id"] == "academic_average":
            field.update({"label": "適用學年GPA或班排名", "field_type": "text", "required": False,
                          "help_text": "學士生填名次證明上的GPA或前幾%；研究生可留空。此欄不用百分制平均代替GPA。"})
        if field["id"] in {"language_test", "language_score", "language_result_date"}:
            field["required"] = False
            field["required_when"] = [
                {"language_group": language_groups[:-1]},
                {"language_group": ["中語組"], "international_degree_student": ["是"]},
            ]
        if field["id"] == "language_test":
            field["options"] = list(dict.fromkeys(test for tests in group_tests.values() for test in tests))
            field["options_by_field"] = {"language_group": group_tests}
            field["help_text"] = "依116-1簡章第4個PDF頁的語組規定；TOEIC及Duolingo不列為臺大校內英語證明。替代證明須於報名前洽國際處，合作校仍可能要求語檢。"
        if field["id"] == "language_score":
            field["label"] = "語言成績／級別／替代證明說明"
        if field["id"] == "language_result_date":
            field["label"] = "實際考試日期／替代證明日期"
            field["help_text"] = "英語檢定須於2025-05-01（含）後考試取得；填實際考試日，預計取得日不能充作有效證明。替代證明填文件日期，效力須先洽國際處。"
    if template.id == "exchange-application-data":
        payload["fields"].append(_field("language_planned_result_date", "預計取得語檢成績日（規劃用）",
            field_type=ApplicationFieldType.DATE, help_text="僅供個人規劃，不代替實際考試日期或正式語言證明。").model_dump(mode="json"))
    payload.update({
        "description": descriptions[template.id], "stage": {
            "predeparture-notice": "出國前（依當期通知）", "return-report": "返國後（依當期通知）",
        }.get(template.id, "申請與文件準備（依當期通知）"),
        "source_url": NTU_GUIDELINES_URL, "source_checked_at": NTU_SOURCE_CHECKED_AT,
        "official_layout": False, "official_form_number": None, "official_file_name": None,
        "official_download_url": None, "version": "116-1準備工具-2026-10-08.3",
        "destinations": ["學生自存備份"], "signatures": [], "stamps": [],
        "conditional_note": "此為個人準備工具；正式表格、簽章、送件與期限以臺大當期系統及通知為準。系所推薦表由校方系統產生，研究生推薦信由系統邀請教授完成。",
    })
    return ApplicationDocumentTemplate.model_validate(payload)


def _ncu_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    descriptions = {
        "exchange-application-data": "整理中央116-1個人資料與校內附件；正式報名須完成校方線上申請、列印簽核及系所紙本繳件。大學部平均60分、研究生70分，在職專班可申請但無研修獎學金。",
        "study-plan": "個人研修與選課規劃工具；中央116-1校內必繳清單沒有列研修計畫。外校若要求，須依該校格式另備。",
        "course-preapproval": "出發前向中央所屬系所確認學分採認；依外校修課規定，無規定時至少兩門且一門專業課。學則另規定兩門或六學分，須分別核對。",
        "predeparture-notice": "出國前兩週完成中央行前程序單並繳文件；自行辦理護照、簽證、足額醫療／意外／急難救助保險及役男許可。此工具不代替中央正式表格。",
        "return-report": "返國後一週內填中央返校程序單；心得須WORD電子檔800–1500字並至少四張照片。此工具協助草擬，正式程序單須依國際處通知取得。",
        "credit-transfer": "整理外校原始成績證明與課程資料；依中央系所規定於畢業前完成採認，延畢生另核對校際選課兩階段程序及學雜費。",
    }
    if template.id not in descriptions:
        return None
    def adapt(value):
        if isinstance(value, str): return value.replace("長庚大學", "國立中央大學").replace("長庚", "中央")
        if isinstance(value, list): return [adapt(x) for x in value]
        if isinstance(value, dict): return {k:adapt(v) for k,v in value.items()}
        return value
    payload = adapt(template.model_dump(mode="json"))
    for field in payload["fields"]:
        if field["id"] == "degree_level" and field["options"]:
            field["options"] = list(dict.fromkeys([*field["options"], "在職碩士班"]))
        if field["id"] == "class_rank_percent":
            field["help_text"] = "中央校內須中文成績名次證明；本欄僅整理資料，不替代正式文件。"
        if field["id"] == "language_test":
            field["options"] = ["TOEFL iBT", "TOEFL ITP（第4頁；與第6頁PBT差異須確認）", "IELTS Academic", "GEPT（複試通過）", "TOEIC（聽讀）", "Linguaskill（實用組）", "BESTEP", "志願校接受之第三外語檢定"]
            field["help_text"] = "校內必繳正式外語檢定成績，不限分數級數；英文檢定须兩年內有效。簡章第4頁列ITP、第6頁列PBT，先向國際處確認。合作校規定之語檢另查，提名前須具備。"
        if field["id"] == "language_result_date":
            field["label"] = "實際考試日期"
            field["field_type"] = "date"
            field["help_text"] = "填已發生的實際考試日期；正式英檢在校內申請及外校送件時均須有效。預計日期或網路截圖不能代替校內必繳正式成績。"
    payload.update(description=descriptions[template.id], source_url=NCU_GUIDELINES_URL,
        source_checked_at=NCU_CHECKED_AT, official_layout=False, official_form_number=None,
        official_file_name=None, official_download_url=None, default_copies=1, signatures=[], stamps=[],
        stage={"predeparture-notice":"出國前兩週", "return-report":"返國後一週"}.get(template.id,"申請與文件準備"),
        version="116-1準備工具-2026-10-08.1", destinations=["學生自存備份"],
        conditional_note="此為個人準備工具；中央正式申請表由系統列印完成簽核。家長／個資同意書請用中央現行下載檔。校內文件與外校文件分開，份數與其他正式表格依承辦通知。")
    return ApplicationDocumentTemplate.model_validate(payload)


def application_field_required(field: ApplicationFormField, values: dict[str, Any]) -> bool:
    return field.required or any(
        all(str(values.get(key, "")) in allowed for key, allowed in clause.items())
        for clause in field.required_when
    )


def _ncu_language_validation(template: ApplicationDocumentTemplate, values: dict[str, Any]) -> dict[str, str]:
    if template.source_url != NCU_GUIDELINES_URL or template.id != "exchange-application-data":
        return {}
    errors = {}
    test = str(values.get("language_test") or "")
    allowed = next(field.options for field in template.fields if field.id == "language_test")
    if test and test not in allowed:
        errors["language_test"] = "請依中央116-1正式語檢種類選擇；外校接受的其他測驗不能直接取代校內必繳證明。"
    actual = str(values.get("language_result_date") or "")
    if actual:
        try:
            date = datetime.strptime(actual, "%Y-%m-%d").date()
            today = datetime.now(timezone.utc).date()
            if date > today:
                errors["language_result_date"] = "須填已發生的實際考試日期；預計日期不能代替正式語檢成績。"
            elif test and test != "志願校接受之第三外語檢定":
                try:
                    expiry = date.replace(year=date.year + 2)
                except ValueError:
                    expiry = date.replace(year=date.year + 2, day=28)
                if expiry < today:
                    errors["language_result_date"] = "英文檢定已超過中央兩年效期；實際送件當日亦須有效，請備妥正式成績。"
        except ValueError:
            errors["language_result_date"] = "請填有效的實際考試日期。"
    return errors


def _ntu_language_validation(template: ApplicationDocumentTemplate, values: dict[str, Any]) -> dict[str, str]:
    if template.source_url != NTU_GUIDELINES_URL or template.id != "exchange-application-data":
        return {}
    errors = {}
    test = str(values.get("language_test") or "")
    group = str(values.get("language_group") or "")
    for field in template.fields:
        if field.id in {"language_group", "international_degree_student"} and values.get(field.id) and values[field.id] not in field.options:
            errors[field.id] = "請選擇清單中的有效身分／語組。"
    test_field = next(field for field in template.fields if field.id == "language_test")
    allowed = test_field.options_by_field["language_group"].get(group, test_field.options)
    if test and test not in allowed:
        errors["language_test"] = "此語檢種類不適用所選臺大甄選語組；請依簡章提供證明。"
    if test in {"TOEFL iBT（舊制120分）", "TOEFL iBT（新制6分）", "IELTS Academic", "GEPT", "BESTEP"}:
        actual = str(values.get("language_result_date") or "")
        if actual:
            try:
                exam_date = datetime.strptime(actual, "%Y-%m-%d").date()
                if not datetime(2025, 5, 1).date() <= exam_date <= datetime.now(timezone.utc).date():
                    errors["language_result_date"] = "須填2025-05-01（含）後且已發生的實際考試日期；預計日期不具證明效力。"
            except ValueError:
                errors["language_result_date"] = "請填有效的實際考試日期。"
    return errors


def _fju_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    descriptions = {
        "exchange-application-data": "整理輔大出國交換個人基本資料、志願學校（最多 5 校）、歷年學業成績（總平均達 70 分或系排名前 50%）及外語能力檢定資料；正式送件須完成 Google 線上報名表並將系主任與院長簽章之紙本申請表送交耕莘樓 A113 國際學生中心。",
        "study-plan": "撰寫輔大校內甄選必繳之讀書計畫（Study Plan）與自傳（A4 雙面列印、不超過 2 頁／4 面；外語組以英文或交換國語言撰寫、日語組以日文或英文撰寫、中語組以中文撰寫）。",
        "course-preapproval": "出國前規劃於接待姊妹校修習之科目與學分（依輔大實施辦法第 10 條，每學期至少應修習相當於輔大 2 學分以上之科目），並先與所屬系所確認學分抵免原則。",
        "predeparture-notice": "錄取後確認繳交保證金 NT$10,000（大陸中語組免繳）、辦理接待校入學許可、學生簽證、海外醫療及意外保險與輔大在學註冊繳費。",
        "return-report": "返國後 1 個月內應繳交 2,000 字以上之交換學習心得報告與外校正式成績單，以辦理學分抵免及無息退還保證金。",
        "credit-transfer": "返國後檢附接待姊妹校核發之正式成績單與課程大綱，向所屬系所及教務處辦理國外修習科目學分採認。",
    }
    if template.id not in descriptions:
        return None
    def adapt(value):
        if isinstance(value, str):
            return value.replace("長庚大學", "天主教輔仁大學").replace("長庚", "輔大")
        if isinstance(value, list):
            return [adapt(x) for x in value]
        if isinstance(value, dict):
            return {k: adapt(v) for k, v in value.items()}
        return value
    payload = adapt(template.model_dump(mode="json"))
    for field in payload["fields"]:
        if field["id"] == "class_rank_percent":
            field["help_text"] = "輔大校內須檢附含歷年學業總平均及系排名百分比之中文歷年成績單正本（總平均達 70 分或系排名前 50%）。"
        if field["id"] == "language_test":
            field["options"] = ["TOEFL iBT（不接受 Home Edition）", "IELTS Academic", "JLPT（N1–N4）", "TOPIK", "DELF / DALF / TCF（法語）", "Goethe / TestDaF（德語）", "DELE（西語）", "TOEIC（僅供部分學校或換分參考）", "中語組免附外語檢定"]
            field["help_text"] = "英語組基本門檻為 TOEFL iBT 79 或 IELTS 6.0；外語組語檢成績佔甄選總分 25%（依 labelID=44 換分表 40–100 分計算）。"
    payload.update(
        description=descriptions[template.id],
        source_url="https://iscoie.fju.edu.tw/generalServices.jsp?labelID=43",
        source_checked_at=FJU_SOURCE_CHECKED_AT,
        official_layout=False,
        official_form_number=None,
        official_file_name=None,
        official_download_url=None,
        default_copies=1,
        signatures=["申請學生簽名", "系主任簽章", "學院院長簽章"] if template.id == "exchange-application-data" else [],
        stamps=[],
        stage={"predeparture-notice": "出國前準備", "return-report": "返國後一個月內"}.get(template.id, "校內甄選收件（A4左上角裝訂）"),
        version="116-1準備工具-2026-10-16.1",
        destinations=["耕莘樓 1 樓 A113 室（國際學生中心）", "學生自存備份"],
        conditional_note="此為個人準備工具；請先完成輔大 Google 線上報名表並使用國際學生中心當期公告之正式申請表、保證書與個資同意書，依序排列於左上角裝訂（勿用資料夾）。",
    )
    return ApplicationDocumentTemplate.model_validate(payload)


def _scu_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    descriptions = {
        "exchange-application-data": "整理東吳大學 116 學年度校級赴外／赴陸交換及自費研修之個人基本資料、志願序（最多 6 個志願，含學校與學期）、累計班排名／歷年平均成績及外語檢定資料；正式申請須於 2026/11/16 中午 12:00 前登入 https://api.sys.scu.edu.tw/exchange/Login.aspx 完成線上填報與 PDF 上傳（免交紙本）。",
        "study-plan": "撰寫東吳校內甄選必繳之自傳或履歷（約 2,000 字）與一校一份之交換研修動機及讀書計畫（各約 2,000 字以內；赴外交換須同時填寫中文 Form A 與外文 Form B 並依志願序將所有中文表格排在前、外文在後合併為單一 PDF；赴陸交換使用中文表格）。",
        "course-preapproval": "出國前規劃於接待協議校修習之科目（依東吳《學生出境期間有關學業及學籍處理辦法》，於境外每學期至少應修習 1 門課程；歐洲 2 個 ECTS 約等於東吳 1 學分），並先與所屬學系確認抵免原則。",
        "predeparture-notice": "獲推薦名單公告後 1 週內繳交家長親筆簽名之「東吳大學學生赴協議學校交換研習確認書」與保證金 NT$5,000，並辦理外校入學申請、學生簽證、海外保險與東吳日間部全額學雜費註冊。",
        "return-report": "交換結束返臺後 1 個月內應繳交 1,500–2,000 字之交換研習心得報告並分享經驗，且於開學 1 週內完成學分抵免（或申請不抵免學分）程序，始得無息退還保證金 NT$5,000。",
        "credit-transfer": "交換結束返臺後，至遲應於開學 1 週內檢附外校成績單與課程大綱完成抵免簽核手續（無須抵免學分者亦須辦理「申請不抵免學分」簽核）。",
    }
    if template.id not in descriptions:
        return None
    def adapt(value):
        if isinstance(value, str):
            return value.replace("長庚大學", "東吳大學").replace("長庚", "東吳")
        if isinstance(value, list):
            return [adapt(x) for x in value]
        if isinstance(value, dict):
            return {k: adapt(v) for k, v in value.items()}
        return value
    payload = adapt(template.model_dump(mode="json"))
    for field in payload["fields"]:
        if field["id"] == "class_rank_percent":
            field["help_text"] = "東吳大學部累計班排名須達前 85% 以內（學業採計：歷年平均×45%＋(1－累計班排名百分比)×100×55%）；碩博班入學後總平均須達 80 分以上；操行須達 80 分以上。舊生由國際處統一向電算中心查核，免自行上傳成績單。"
        if field["id"] == "language_test":
            field["options"] = ["TOEFL iBT / ITP", "IELTS Academic", "JLPT（N1–N3，2024/01/31後核發）", "TOEIC（不接受校園考）", "TOPIK（韓檢）", "DELF / DALF / TCF（法語）", "Goethe / TestDaF（德語）", "DELE（西語）", "赴大陸交換免附外語檢定"]
            field["help_text"] = "赴外交換須符合《116學年度校級赴外交換學校一覽表》目標學校任一語檢門檻（英歐語須為 2025/01/31 後核發、JLPT 為 2024/01/31 後核發，不接受多益校園考）。"
    payload.update(
        description=descriptions[template.id],
        source_url="https://icae.scu.edu.tw/zh-hant/outbound-exchange/itnl/AYapply",
        source_checked_at=SCU_SOURCE_CHECKED_AT,
        official_layout=False,
        official_form_number=None,
        official_file_name=None,
        official_download_url=None,
        default_copies=1,
        signatures=["家長／監護人簽名", "申請學生簽名"] if template.id == "predeparture-notice" else [],
        stamps=[],
        stage={"predeparture-notice": "錄取確認（1週內繳交確認書與保證金）", "return-report": "返臺後一個月內", "credit-transfer": "返臺開學一週內"}.get(template.id, "線上申請系統 PDF 上傳（免交紙本）"),
        version="116準備工具-2026-10-16.1",
        destinations=["東吳赴外交換線上申請系統（https://api.sys.scu.edu.tw/exchange/Login.aspx）", "國際與兩岸事務中心（雙溪 A313 / 城中 2110）"],
        conditional_note="此為個人準備工具；東吳校內甄選採全線上申請（免交紙本），各類文件請合併為單一 PDF 檔（上限 5MB，檔名僅限中英數字符號）上傳至 https://api.sys.scu.edu.tw/exchange/Login.aspx 。",
    )
    return ApplicationDocumentTemplate.model_validate(payload)


def _ntnu_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    descriptions = {
        "exchange-application-data": "整理國立臺灣師範大學 116-1（2027 春季出國）校級赴外交換生甄選之個人資料、志願序（四語組擇一組別報名，最多選填 10 個志願）、歷年成績與全英語授課（EMI）修課紀錄、語言檢定及報名費 NT$500 繳費收據；正式申請須於 2026/11/01–11/15 23:59:59 前登入 https://bds.oia.ntnu.edu.tw/bds/OE 完成線上填報與上傳（免繳紙本）。",
        "study-plan": "撰寫臺師大校級赴外交換必繳之「自傳與出國學習計畫」（合併為一份文件，占甄選總成績 20%；中文或外文撰寫、格式不限，線上上傳清單規定中英文合計須介於 500–5,000 字，建議加附外文版本約 500–2,500 字；簡章申請資料欄另載「一千字以上」，兩處規定不同時可寫滿 1,000 字以上並向國際處確認）。官方未規定內容項目，簡章 FAQ 說明重點是讓審查委員瞭解你的特質、背景、赴國外的研習計畫與自我期許。",
        "course-preapproval": "出國前規劃於接待姊妹校修習之科目（依臺師大簡章規定，赴外交換每學期至少須修習 2 門課程或 6 學分，歐洲 2 ECTS 折算臺師大 1 學分；赴大陸地區修習之學分不得採認或抵免師資培育職前教育專業課程學分）。",
        "predeparture-notice": "分發錄取後於系統完成線上確認（第 1 次分發 2026/12/11、第 2 次分發 12/15–12/18），並依姊妹校申請截止日準備外校入學申請文件、財力證明、護照、簽證與海外醫療及意外保險（確認錄取後無不可抗力放棄者須繳納 NT$5,000 行政手續費且在學期間不得再報名校級交換）。",
        "return-report": "交換期滿返國後 1 個月內於國際事務處系統上傳赴外交換學生返國心得報告及照片，並配合國際處經驗分享活動（若領取校內或教育部學海飛颺／惜珠獎助學金，須完成返國報告及核銷始撥付尾款）。",
        "credit-transfer": "交換期滿返國後，檢附接待姊妹校核發之正式成績單正本、修課大綱（Syllabus）及修課時數證明，依教務處與所屬系所規定辦理國外修習科目學分採認／抵免（大陸地區學分不得抵免師培專業課程）。",
    }
    if template.id not in descriptions:
        return None
    def adapt(value):
        if isinstance(value, str):
            return value.replace("長庚大學", "國立臺灣師範大學").replace("長庚", "臺師大")
        if isinstance(value, list):
            return [adapt(x) for x in value]
        if isinstance(value, dict):
            return {k: adapt(v) for k, v in value.items()}
        return value
    payload = adapt(template.model_dump(mode="json"))
    for field in payload["fields"]:
        if field["id"] == "class_rank_percent":
            field["help_text"] = "臺師大校級甄選「在校學業及相關表現」占 30%（含全英語授課 EMI 課程修習表現 5%：修滿 5 門以上得滿分 5%）；請準備教務處核發之最新歷年中文或英文成績單及名次證明。"
        if field["id"] == "language_test":
            field["options"] = ["TOEFL iBT（不採計 MyBest Scores）", "IELTS Academic", "JLPT（N1–N3）", "TOPIK（韓檢 2–6 級）", "TOEIC（僅部分學校採認）", "GEPT 全民英檢中高級以上", "DELF / DALF / TCF（法語）", "Goethe / TestDaF（德語）", "DELE（西語）", "中文組免附外語檢定"]
            field["help_text"] = "分「英歐語組、日語組、韓語組、中文組」四組擇一報名（語言能力占總成績 30%），須符合目標姊妹校於《116-1 赴外交換學校一覽表》所列標準，且不採計 TOEFL MyBest Scores 拼分成績。"
    payload.update(
        description=descriptions[template.id],
        source_url="https://bds.oia.ntnu.edu.tw/api/v1/pt/dl?f=/pt/contents/2014100104/doc_OE116-1%20SPRING2027-1013.pdf",
        source_checked_at=NTNU_SOURCE_CHECKED_AT,
        official_layout=False,
        official_form_number=None,
        official_file_name=None,
        official_download_url=None,
        default_copies=1,
        signatures=["申請學生簽名", "系所主管核章（线上列印申請表後簽核上傳）"] if template.id == "exchange-application-data" else [],
        stamps=[],
        stage={"predeparture-notice": "分發確認與外校提名送件", "return-report": "返國後一個月內", "credit-transfer": "返國開學後"}.get(template.id, "赴外交換生線上申請系統上傳（免交紙本）"),
        version="116-1準備工具-2026-10-16.1",
        destinations=["臺師大赴外交換生線上申請系統（https://bds.oia.ntnu.edu.tw/bds/OE）", "國際事務處學術合作組"],
        conditional_note="此為個人準備工具；臺師大校級赴外交換甄選採全線上申請（免繳紙本），請於 2026/11/01–11/15 23:59:59 前於 https://bds.oia.ntnu.edu.tw/bds/OE 填寫並列印申請表經系所核章後連同各項證明與 NT$500 繳費收據掃描上傳。",
    )
    return ApplicationDocumentTemplate.model_validate(payload)


def _cycu_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    descriptions = {
        "exchange-application-data": "整理中原大學 115-2（2027 春季出國）出國交換研修計畫之個人資料、志願學校、歷年學業成績（GPA 3.0 以上或班級排名前 30%；建築學系為前 50%）、外語能力檢定證明與保證人同意書資訊；正式申請須檢附導師、系主任、院長核章之校內申請表送交國際暨兩岸教育處（維澈樓 704 室）。",
        "study-plan": "撰寫中原大學出國交換甄選必繳之中文及英文讀書計畫（Study Plan）與中文及英文自傳，連同個人履歷表（CV）以國際處規定格式之電子檔寄送；官方資料未規定讀書計畫的內容項目或字數。非大陸地區的校內甄選面試表現占總成績 40%，其細項中讀書計畫占 20%。",
        "course-preapproval": "出國前規劃於接待姊妹校修習之科目（依中原大學《選送學生出國研習實施辦法》規定，出國交換期間每學期至少應修習二門科目或相當於中原大學六學分之課程，並填寫學生出國修習課程申請表經系所預審）。",
        "predeparture-notice": "通過校內甄選並獲推薦提名後，依姊妹校規定準備外校入學申請表、英文財力證明、有效護照、簽證、家長／保證人同意書及海外醫療與意外保險證明。",
        "return-report": "領取《中原大學學生赴海外姊妹校交換學習助學辦法》助學金者，須於返國後二週內向國際暨兩岸教育處提交研習成果報告書辦理核銷，並出席國際處辦理之交換生說明會；官方資料未公布心得報告的字數、照片或授權格式，請依國際處通知準備。",
        "credit-transfer": "交換期滿返國後，持接待姊妹校核發之正式成績單正本、修課大綱（Syllabus）及修課時數證明，依中原大學教務處與所屬學系規定辦理國外修習科目學分採認／抵免。",
    }
    if template.id not in descriptions:
        return None
    def adapt(value):
        if isinstance(value, str):
            return value.replace("長庚大學", "中原大學").replace("長庚", "中原")
        if isinstance(value, list):
            return [adapt(x) for x in value]
        if isinstance(value, dict):
            return {k: adapt(v) for k, v in value.items()}
        return value
    payload = adapt(template.model_dump(mode="json"))
    for field in payload["fields"]:
        if field["id"] == "class_rank_percent":
            field["help_text"] = "中原大學規定歷年學業總平均須達 GPA 3.0（平均 75 分）以上或班級排名前 30%（建築學系為歷年排名前 50% 且建築設計一～六均及格）；請檢附教務處核發之歷年中文與英文成績單正本（含排名百分比）。"
        if field["id"] == "language_test":
            field["options"] = ["TOEFL iBT", "IELTS Academic", "TOEIC", "JLPT（N1–N4）", "TOPIK（韓檢 2–6 級）", "DELF / DALF / TCF（法語）", "Goethe / TestDaF（德語）", "DELE（西語）", "赴大陸交換免附外語檢定"]
            field["help_text"] = "申請國際及香港姊妹校須檢附兩年內有效之外語能力檢定證明，並符合《中原大學出國交換研修申請學校一覽表》與各校 Fact Sheet 標準；申請大陸地區姊妹校免附外語檢定。"
    payload.update(
        description=descriptions[template.id],
        source_url="https://oia.cycu.edu.tw/?p=6336",
        source_checked_at=CYCU_SOURCE_CHECKED_AT,
        official_layout=False,
        official_form_number=None,
        official_file_name=None,
        official_download_url="https://oia.cycu.edu.tw/?page_id=2968&lang=zh",
        default_copies=1,
        signatures=["申請學生簽名", "家長／保證人簽章", "導師簽章", "系主任簽章", "院長簽章"] if template.id == "exchange-application-data" else [],
        stamps=[],
        stage={"predeparture-notice": "外校提名與簽證保險準備", "return-report": "返國後二週內（領取助學金者）", "credit-transfer": "返國開學後"}.get(template.id, "校內申請表件送件（維澈樓 704 室）"),
        version="115-2準備工具-2026-10-16.1",
        destinations=["中原大學國際暨兩岸教育處（維澈樓 704 室）", "所屬學系／學院辦公室"],
        conditional_note="此為個人準備工具；中原大學正式出國交換申請表件請自 https://oia.cycu.edu.tw/?page_id=2968&lang=zh 下載，完成導師、系主任及院長核章後於截止日前送交國際暨兩岸教育處（維澈樓 704 室）。",
    )
    return ApplicationDocumentTemplate.model_validate(payload)


def _ntust_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    descriptions = {
        "exchange-application-data": "整理國立臺灣科技大學 116-1（2027 秋季班）赴海外交換學生計畫甄選簡章（_中文_20260915.pdf）暨 115-2（2027 春季班）海外與大陸地區交換生甄選之個人資料、志願序、歷年成績與名次證明（海外交換須全班前 70%；大陸交換須大學部平均 75 分、研究所 80 分以上）及外語檢定成績（語言能力占總成績 60%、在校成績占 20%、課外表現占 20%）。",
        "study-plan": "撰寫臺科大出國交換甄選必繳之出國學習計畫書（Study Plan）與自傳（歐美亞澳簡章：中、英文讀書計畫與中、英文自傳各一份，格式不拘、每份約 1–2 頁；計畫書可針對特定國家或學校撰寫，亦可概述目前的學習規劃及交換期間與交換後的安排）。校內總積分僅計外語檢定 60%、在校學業 20%、課外表現證明 20%，計畫書與自傳不另計分。",
        "course-preapproval": "出國前規劃於接待姊妹校修習之科目（依臺科大《學生出國期間有關學業及學籍處理要點》規定，交換期間須維持臺科大在學學籍並依規定修課，返國後辦理學分採認抵免）。",
        "predeparture-notice": "放榜錄取後於期限內繳交《錄取資格確認書》（或放棄聲明書），並依國際處與姊妹校規定準備外校線上申請表、英文歷年成績單、英文在學證明、英文財力證明、護照、簽證與海外醫療保險。",
        "return-report": "交換期滿返國後 1 個月內，登入臺科大國際事務處出國交換學生心得分享系統（https://oia.ntust.edu.tw/p/404-1060-66857.php?Lang=zh-tw）填寫並上傳研修心得報告及照片，始得完成結案與獎學金尾款核銷。",
        "credit-transfer": "交換期滿返國後，檢附接待姊妹校核發之正式成績單正本、課程大綱（Syllabus）及學分時數證明，依臺科大教務處與所屬系所規定辦理國外修習科目學分採認／抵免。",
    }
    if template.id not in descriptions:
        return None
    def adapt(value):
        if isinstance(value, str):
            return value.replace("長庚大學", "國立臺灣科技大學").replace("長庚", "臺科大")
        if isinstance(value, list):
            return [adapt(x) for x in value]
        if isinstance(value, dict):
            return {k: adapt(v) for k, v in value.items()}
        return value
    payload = adapt(template.model_dump(mode="json"))
    for field in payload["fields"]:
        if field["id"] == "class_rank_percent":
            field["help_text"] = "臺科大海外交換規定歷年名次須在全班前 70% 以內（大陸地區交換為大學部歷年總平均 75 分以上、研究所 80 分以上）；在校學業成績占校內書審總分 20%。"
        if field["id"] == "language_test":
            field["options"] = ["TOEFL iBT", "IELTS Academic", "TOEIC", "GEPT 全民英檢中級複試以上", "JLPT（N1–N2）", "TOPIK（韓檢 3–6 級）", "TestDaF / Goethe（德語 B1+）", "DELF / TCF（法語 B1+）", "DELE（西語 B1+）", "赴大陸交換免附外語檢定"]
            field["help_text"] = "語言能力占校內甄選總分 60%（基本門檻：TOEIC 550 / TOEFL iBT 57 / IELTS 4.0 / JLPT N2 / CEFR B1；校內獎學金門檻：TOEIC 750 / TOEFL iBT 79 / IELTS 6.0 / JLPT N2；第二外語達 B1 另加總分 1 分）。"
    payload.update(
        description=descriptions[template.id],
        source_url="https://oia.ntust.edu.tw/p/405-1060-62102,c9056.php?Lang=zh-tw",
        source_checked_at=NTUST_SOURCE_CHECKED_AT,
        official_layout=False,
        official_form_number=None,
        official_file_name=None,
        official_download_url="https://oia.ntust.edu.tw/p/405-1060-62102,c9056.php?Lang=zh-tw",
        default_copies=1,
        signatures=["申請學生簽名", "指導教授簽名（研究生適用）", "系所主管核章"] if template.id == "exchange-application-data" else [],
        stamps=[],
        stage={"predeparture-notice": "錄取確認與外校提名送件", "return-report": "返國後一個月內", "credit-transfer": "返國開學後"}.get(template.id, "線上報名並列印申請表送交系所與國際處"),
        version="115-2準備工具-2026-10-16.1",
        destinations=["臺科大出國交換生報名系統", "國際事務處（國際大樓 IB-401）"],
        conditional_note="此為個人準備工具；臺科大出國交換生甄選須先完成線上報名並列印申請表，經系所（及指導教授）核章後連同備審資料於截止日前送交國際事務處。",
    )
    return ApplicationDocumentTemplate.model_validate(payload)


def _yzu_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    descriptions = {
        "exchange-application-data": "整理元智大學 115-2（2027 春季班）出國暨赴大陸地區交換學生志願表（CF-01-R1）與申請表（CF-02-R3）之個人基本資料、志願學校（校級至多 2 志願、管院院級至多 2 志願）、歷年學業總平均與排名百分比（GPA 2.5 或平均 65 分以上）、外語能力檢定證明（校級第一階段校內評比為系排名 50%＋英文檢定 50%）及保證金 NT$5,000 繳費資訊。",
        "study-plan": "撰寫元智大學出國交換甄選之中英文讀書計畫（Study Plan；赴大陸交換須含 500 字以上中文讀書計畫）；說明會簡報與申請表勾選清單另列英文自傳及英文學習計畫書為複審文件，請向全球事務處確認當期要求。CF-02-R3 為《出國交換學生申請表》（須經導師／指導教授及系所主任簽章），並非研修計畫書。第一階段校內評比公式（系排名 50%＋英文檢定 50%）不含讀書計畫與自傳；官方未公布計畫內容項目與字數規定（大陸交換之 500 字除外）。",
        "course-preapproval": "出國前填寫《學生境外選課申請單》（表單編號 1-51），依元智大學《學生境外選課實施要點》規定，大學部每學期至少修習相當於元智大學 6 學分、研究生至少修習 1 門課（3 學分），並經所屬學系預審核可。",
        "predeparture-notice": "通過校內甄選放榜後繳交《錄取資格確認書》（CF-04），並依全球事務處與姊妹校規定準備外校線上申請表、英文歷年成績單、英文財力證明、有效護照、簽證與海外醫療及意外保險證明。",
        "return-report": "交換期滿返國後 2 週內，向全球事務處繳交 1,500 字以上之研修心得報告與 6 張照片，並完成學分抵免後，NT$5,000 保證金始全額無息退還；領取獎助學金者另須依切結書（CF-04）第十七條於回國後 14 日內繳交電子機票、來回登機證正本及對方學校學生證副本等文件（切結書第十條另規定交換期滿後兩個月內須返回元智大學，此為返校期限，並非心得報告期限）。",
        "credit-transfer": "交換期滿返國後，持接待姊妹校核發之正式成績單正本、修課大綱（Syllabus）及修課時數證明，連同原核准之《學生境外選課申請單》（表單 1-51）向教務處與所屬學系辦理國外修習科目學分採認／抵免。",
    }
    if template.id not in descriptions:
        return None
    def adapt(value):
        if isinstance(value, str):
            return value.replace("長庚大學", "元智大學").replace("長庚", "元智")
        if isinstance(value, list):
            return [adapt(x) for x in value]
        if isinstance(value, dict):
            return {k: adapt(v) for k, v in value.items()}
        return value
    payload = adapt(template.model_dump(mode="json"))
    for field in payload["fields"]:
        if template.id == "return-report" and field["id"] == "activity_photos":
            field["max_files"] = 6
            field["help_text"] = "學校要求 6 張照片；最多 6 張，產生 PDF 或 Word 時會排入報告"
        if field["id"] == "class_rank_percent":
            field["help_text"] = "元智大學規定歷年學業總平均須達 65 分或 GPA 2.5 以上（管理學院院級為 GPA 2.75 以上）；校級第一階段校內評比以系排名占 50%；請檢附教務處核發之歷年中文與英文成績單正本（含排名百分比）。"
        if field["id"] == "language_test":
            field["options"] = ["TOEFL iBT", "IELTS Academic", "TOEIC", "JLPT（N1–N4）", "TOPIK（韓檢 1–6 級）", "DELF / DALF / TCF（法語）", "Goethe / TestDaF（德語）", "DELE（西語）", "赴大陸交換免附外語檢定"]
            field["help_text"] = "校級第一階段校內評比以英文檢定成績占 50%（基本門檻：TOEIC 550 / TOEFL iBT 57 / IELTS 4.5 / JLPT N4 / TOPIK 1級，且須符合各姊妹校申請門檻；管理學院院級為 TOEFL iBT 79 / IELTS 6.0 / TOEIC 750；赴大陸交換免附外語檢定）。"
    payload.update(
        description=descriptions[template.id],
        source_url="https://www.yzu.edu.tw/admin/ao/index.php/tw/2016-03-28-08-35-08/2016-05-06-03-07-02/1319-2026-09-09-02-40-50",
        source_checked_at=YZU_SOURCE_CHECKED_AT,
        official_layout=False,
        official_form_number="CF-01-R1" if template.id == "exchange-application-data" else ("1-51" if template.id == "course-preapproval" else None),
        official_file_name=None,
        official_download_url="https://www.yzu.edu.tw/admin/ao/index.php/tw/2016-03-28-08-35-08/2016-04-21-01-33-53",
        default_copies=1,
        signatures=["申請學生簽名", "家長／監護人簽章", "導師／指導教授簽章", "系所主管簽章"] if template.id == "exchange-application-data" else [],
        stamps=[],
        stage={"predeparture-notice": "錄取確認（CF-04）與外校提名送件", "return-report": "返國後 2 週內（辦理保證金退還）", "credit-transfer": "返國開學後"}.get(template.id, "線上填表並列印紙本送交全球事務處（七館 3 樓 R70306）"),
        version="115-2準備工具-2026-10-17.1",
        destinations=["元智大學全球事務處（七館 3 樓 R70306）", "管理學院國際事務辦公室（六館 R60404，管院院級適用）"],
        conditional_note="此為個人準備工具；元智大學正式出國交換申請表件（CF-01-R1、CF-02-R3 等）請自全球事務處表單下載區下載，完成導師及系主任核章並連同 NT$5,000 保證金繳費收據於截止日前送交全球事務處（R70306）。",
    )
    return ApplicationDocumentTemplate.model_validate(payload)


def _fcu_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    descriptions = {
        "exchange-application-data": "整理逢甲大學選送學生出國研修申請資訊簡表（oiasap 系統線上填報，至多 5 所志願學校）、家長同意書（附件一）、研究生指導教授同意書（附件三）、生輔組核章之在校獎懲紀錄、歷年成績單（GPA 3.0 以上）與外語檢定證明。",
        "study-plan": "撰寫逢甲大學出國研修簡章必繳之《研修計畫》（簡章附件二，中英文撰寫均可，字數至少 1,000 字；簡章要求分段詳述個人自傳、赴國外研修之動機、出國前於本校之研修學習計畫，及赴國外大學之研修學習計畫，有多個志願學校時請分校簡述）。",
        "course-preapproval": "規劃出國研修期間之選課清單與學分抵免預審（大學部一至三年級每學期至少 12 學分、大學部四年級至少 9 學分、碩博士班至少 3 學分；獲教育部學海飛颺／惜珠獎學金者須修讀至少 4 學分本科系相關專業課程）。",
        "predeparture-notice": "取得姊妹校正式入學許可（LOA）後 2 週內繳交保證金（獲獎助或學費互免交換生 NT$10,000、自費交換生 NT$5,000），並依國際事務處與姊妹校規定完成複審文件、宿舍申請、簽證及海外醫療及意外保險。",
        "return-report": "交換期滿返國後 1 個月內繳交 2,000 字以上之出國研習報告書，且修課及格率達 1/2 以上、學費互免／獲獎生完成每學期 50 小時（兩學期 100 小時）志工服務後，辦理保證金無息退還。",
        "credit-transfer": "交換期滿返國後，持接待姊妹校核發之正式成績單正本及修課大綱（Syllabus），依逢甲大學學生抵免學分辦法向所屬學系及教務處註冊課務組辦理學分抵免。",
    }
    if template.id not in descriptions:
        return None
    def adapt(value):
        if isinstance(value, str):
            return value.replace("長庚大學", "逢甲大學").replace("長庚", "逢甲")
        if isinstance(value, list):
            return [adapt(x) for x in value]
        if isinstance(value, dict):
            return {k: adapt(v) for k, v in value.items()}
        return value
    payload = adapt(template.model_dump(mode="json"))
    for field in payload["fields"]:
        if field["id"] == "class_rank_percent":
            field["help_text"] = "逢甲大學規定在校歷年總平均須達 GPA 3.0（含）以上（約 75 分以上），申請一學年學費互免交換者歷年系排名須達前 50%；初審時將依歷年系排名百分比自動審核「逢甲大學出國研修獎助學金」。"
        if field["id"] == "language_test":
            field["options"] = ["TOEFL iBT", "IELTS Academic", "TOEIC", "JLPT（N1–N3）", "TOPIK（韓檢 1–6 級）", "DELF / DALF / TCF（法語）", "Goethe / TestDaF（德語）", "DELE（西語）", "赴大陸交換免附外語檢定"]
            field["help_text"] = "申請國際及香港地區必繳（須為 2024/10/01 後考試取得並符合 oiasap 系統各校門檻）；申請大陸地區免附外語檢定證明。"
    payload.update(
        description=descriptions[template.id],
        source_url="https://oia.fcu.edu.tw/sap/introduction/",
        source_checked_at=FCU_SOURCE_CHECKED_AT,
        official_layout=False,
        official_form_number="附件一" if template.id == "exchange-application-data" else ("附件二" if template.id == "study-plan" else None),
        official_file_name=None,
        official_download_url="https://oiasap.fcu.edu.tw/",
        default_copies=1,
        signatures=["申請學生簽名", "家長親筆簽名（附件一）", "指導教授親筆簽名（附件三，研究生適用）"] if template.id == "exchange-application-data" else [],
        stamps=["學務處生活輔導組（行政二館一樓）獎懲紀錄確認章"] if template.id == "exchange-application-data" else [],
        stage={"predeparture-notice": "取得入學許可 2 週內繳交保證金與複審送件", "return-report": "返國後 1 個月內（含 50 小時志工服務）", "credit-transfer": "返國開學後"}.get(template.id, "於 oiasap 系統（https://oiasap.fcu.edu.tw/）全線上無紙化上傳"),
        version="115-1準備工具-2026-10-17.1",
        destinations=["逢甲大學國際事務處（行政二館 3 樓 304 室）", "逢甲大學出國研修申請系統（https://oiasap.fcu.edu.tw/）"],
        conditional_note="此為個人準備工具；逢甲大學正式出國研修申請採全線上無紙化作業，請於申請期間登入 https://oiasap.fcu.edu.tw/ 填報並上傳家長同意書、1,000 字以上研修計畫、生輔組核章獎懲紀錄、歷年成績單及外語檢定證明。",
    )
    return ApplicationDocumentTemplate.model_validate(payload)


def _nsysu_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    descriptions = {
        "exchange-application-data": "整理國立中山大學出國交換學生甄選系統（https://partners.oia.nsysu.edu.tw/exchange/login/user/）線上申請資料、志願表、中文歷年成績單（須註明歷年班排名）、合格語言檢定證明與有利審查資料（上限 10 項）。",
        "study-plan": "撰寫國立中山大學出國交換簡章必繳之《研修計畫書》（占甄選總成績 20%；赴其他國家須含中、英文各 1 頁 A4 為限，赴日本須含中、日文各 1 頁 A4，赴中國大陸以中文 1–2 頁 A4 撰寫，詳述選課與研究規劃）。",
        "course-preapproval": "規劃出國交換期間之修課清單與學分採認預審（每學期至少修習並通過 2 門課程，含至少 1 門專業課程；學海惜珠／乘風萬里受獎生須通過至少 3 門課程，並依 18 授課小時抵免 1 學分原則辦理）。",
        "predeparture-notice": "於校內放榜後規定期限內登入系統點選「確認錄取」並上傳本人及家長／監護人簽署之《錄取確認書（保證人同意書）》，確認「西灣領航計畫」自動獎助資格（每月 NT$10,000–15,000），並依提名通知辦理姊妹校複審、宿舍、簽證與海外保險。",
        "return-report": "交換期滿返國後 2 個月內繳交返國報告書（含中文 1,500–2,000 字、英文 1,000–1,500 字心得及 4 張具圖說照片；赴中國者免附英文心得）及正式成績單查驗，以領取交換學生證明書及核銷獎助學金尾款。",
        "credit-transfer": "交換期滿返國後，持交換學校核發之正式成績單正本及修課大綱（Syllabus），依《國立中山大學處理交換學生選課及成績作業要點》（18 授課小時抵免 1 學分）向所屬系所及教務處註冊課務組辦理學分採認。",
    }
    if template.id not in descriptions:
        return None
    def adapt(value):
        if isinstance(value, str):
            return value.replace("長庚大學", "國立中山大學").replace("長庚", "中山")
        if isinstance(value, list):
            return [adapt(x) for x in value]
        if isinstance(value, dict):
            return {k: adapt(v) for k, v in value.items()}
        return value
    payload = adapt(template.model_dump(mode="json"))
    for field in payload["fields"]:
        if field["id"] == "class_rank_percent":
            field["help_text"] = "國立中山大學出國交換書面審查採計「歷年班排名」（赴日本及其他國家占總分 30%、赴中國大陸占總分 60%，總成績未達 60 分不予錄取；碩一學生可以大學歷年成績單及班排名申請）。"
        if field["id"] == "language_test":
            field["options"] = ["TOEFL iBT（60+）", "IELTS Academic（5.0+）", "TOEIC（600+）", "Cambridge PET（154+）", "Duolingo（80+）", "BESTEP 培力英檢聽讀（170+）", "JLPT 日檢（N1–N5）", "DELF / Goethe / DELE（歐語 CEFR）", "赴中國大陸交換免附語檢"]
            field["help_text"] = "赴日本及其他國家語言能力占甄選總分 40%（須為報名截止日前 2 年內取得並符合交換校個別標準）；赴中國大陸本國籍學生免附語言檢定證明。"
    payload.update(
        description=descriptions[template.id],
        source_url="https://oia.nsysu.edu.tw/p/405-1308-384608,c20621.php?Lang=zh-tw",
        source_checked_at=NSYSU_SOURCE_CHECKED_AT,
        official_layout=False,
        official_form_number="志願表" if template.id == "exchange-application-data" else ("研修計畫書" if template.id == "study-plan" else None),
        official_file_name=None,
        official_download_url="https://partners.oia.nsysu.edu.tw/exchange/login/user/",
        default_copies=1,
        signatures=["申請學生親筆簽名", "父親、母親或監護人親筆簽章（錄取確認書／保證人同意書）"] if template.id == "exchange-application-data" else [],
        stamps=[],
        stage={"predeparture-notice": "錄取公告後線上確認並上傳錄取確認書", "return-report": "返國後 2 個月內繳交雙語報告書與成績單", "credit-transfer": "返國開學後（18 授課小時抵免 1 學分）"}.get(template.id, "於出國交換學生甄選系統（https://partners.oia.nsysu.edu.tw/exchange/login/user/）全線上上傳 PDF"),
        version="116準備工具-2026-10-28.1",
        destinations=["國立中山大學國際事務處學生交換事務組（行政大樓 2 樓 2004 室）", "管理學院職涯發展暨國際交流辦公室（管院院級適用）"],
        conditional_note="此為個人準備工具；國立中山大學正式出國交換申請採全線上作業（2027-2028 其他國家與地區正式簡章 https://oia.nsysu.edu.tw/p/405-1308-384608,c20621.php?Lang=zh-tw ：11/3 9:00 至 11/17 17:00 開放系統申請、審核及補正至 11/20 17:00，交換校資訊和志願表 10/29 公布），請於各線報名期間登入 https://partners.oia.nsysu.edu.tw/exchange/login/user/ 填報並上傳志願表、中文歷年成績單、2025/03/01 後測驗之語檢證明、研修計畫書（113882831.doc）及有利審查資料（302391853.doc）。",
    )
    return ApplicationDocumentTemplate.model_validate(payload)


def _nchu_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    descriptions = {
        "exchange-application-data": "整理國立中興大學出國計畫線上申請系統（https://oiawp.nchu.edu.tw/out-going-program-online-application/）應繳資料、交換學生申請表（海外最多 5 志願＋大陸最多 5 志願，經導師／指導教授及系主任／所長核章）、中文歷年成績單、歷年名次證明書、語檢證明、第一志願家長同意書與 2 份線上教師推薦函。",
        "study-plan": "撰寫國立中興大學出國交換簡章必繳之《自傳及讀書計畫》（至多 A4 三面，以第一志願學校為目標撰寫，含「個人特質與經歷」及「交換計畫與未來展望」；國外組占總成績 30%、大陸組占 45%，有填海外志願須交英文版）。",
        "course-preapproval": "規劃出國交換期間之修課清單與學分抵免預審（每學期至少應選修相當於中興大學 6 學分或修課時間 108 小時之課程；領取獎學金者須含至少 1 門與本系所專業相關之課程）。",
        "predeparture-notice": "於兩階段志願分發放榜後完成錄取資格確認，由國際處辦理姊妹校官方提名（Nomination），並於每年 2–3 月申請教育部學海飛颺／惜珠、中興大學選送學生赴海外研修獎學金或希望之橋獎學金，抵校後填報抵達通知單。",
        "return-report": "交換期滿返國後 2 個月內（領取獎學金者於返國後 2 週內）繳交交換學生心得報告，並於畢業前參與國際處舉辦之經驗分享活動至少 3 小時。",
        "credit-transfer": "交換期滿返國後 1 個月內，檢具接待校正式成績單辦理學分抵免（依《國立中興大學選送學生出國交換甄選辦法》第 14 條，不論是否採認學分，皆須跑完學分抵免程序始得辦理畢業離校手續）。",
    }
    if template.id not in descriptions:
        return None
    def adapt(value):
        if isinstance(value, str):
            return value.replace("長庚大學", "國立中興大學").replace("長庚", "中興")
        if isinstance(value, list):
            return [adapt(x) for x in value]
        if isinstance(value, dict):
            return {k: adapt(v) for k, v in value.items()}
        return value
    payload = adapt(template.model_dump(mode="json"))
    for field in payload["fields"]:
        if field["id"] == "class_rank_percent":
            field["help_text"] = "國立中興大學學士班申請人歷年在校總平均分數須達 60 分（含）以上，並須上傳歷年成績單與歷年名次證明書（國外組在校成績占 30%、大陸組占 50%；申請學海飛颺或興大海外研修獎學金者須歷年名次前 50% 或平均 80 分以上）。"
        if field["id"] == "language_test":
            field["options"] = ["TOEFL iBT（72+ / 新制 4+）", "TOEFL ITP（543+）", "IELTS Academic（5.5+）", "TOEIC（785+）", "JLPT 日檢（N1–N5）", "TOPIK 韓檢（1–6 級）", "德／法／西語檢定（CEFR）", "僅申請大陸地區姊妹校免附語檢"]
            field["help_text"] = "申請國外姊妹校外語能力占總成績 35%（須達 CEFR B2：TOEFL iBT 72 / ITP 543 / IELTS 5.5 / TOEIC 785，或非英語系國家接受之第二外語檢定）；僅申請大陸地區免附。"
    payload.update(
        description=descriptions[template.id],
        source_url="https://oia.nchu.edu.tw/images/File/02_Exchange_Program/5-1-1/Exchange_Program_Guidelines_for_Fall_Semester_2027_TW.pdf",
        source_checked_at=NCHU_SOURCE_CHECKED_AT,
        official_layout=False,
        official_form_number="交換學生申請表" if template.id == "exchange-application-data" else ("自傳及讀書計畫" if template.id == "study-plan" else None),
        official_file_name="outgoing_form.doc" if template.id == "exchange-application-data" else None,
        official_download_url="https://www.oia.nchu.edu.tw/images/File/02_Exchange_Program/5-1-1/outgoing_form.doc" if template.id == "exchange-application-data" else "https://oiawp.nchu.edu.tw/out-going-program-online-application/",
        default_copies=1,
        signatures=["申請學生親筆簽名", "導師或指導教授簽章", "系主任／所長核章", "法定代理人親筆簽名（第一志願家長同意書）"] if template.id == "exchange-application-data" else [],
        stamps=["所屬系所核章"] if template.id == "exchange-application-data" else [],
        stage={"predeparture-notice": "兩階段分發放榜確認後辦理提名與抵達通報", "return-report": "返國後 2 個月內（受獎生 2 週內）繳交心得報告", "credit-transfer": "返國後 1 個月內必辦學分抵免程序"}.get(template.id, "於出國計畫線上申請系統（https://oiawp.nchu.edu.tw/out-going-program-online-application/）上傳 JPG/PDF（單檔 2 MB 內）"),
        version="116準備工具-2026-10-18.1",
        destinations=["國立中興大學國際事務處學術交流組（行政大樓 3 樓）", "所屬系所辦公室（導師／指導教授與系主任／所長核章）"],
        conditional_note="此為個人準備工具；國立中興大學正式出國交換申請須先完成《交換學生申請表》導師／指導教授與系主任／所長核章，並於截止前登入 https://oiawp.nchu.edu.tw/out-going-program-online-application/ 完成上傳及設定 2 份線上教師推薦函。",
    )
    return ApplicationDocumentTemplate.model_validate(payload)


def _ntut_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    from .ntut_source_review import DOCS, OBLIGATIONS, SCHOLARSHIPS, STEP1, STEP2, STEP3
    descriptions = {
        "exchange-application-data": " ".join(DOCS[:3]),
        "study-plan": DOCS[3],
        "course-preapproval": OBLIGATIONS[1] + "出國前持課程資料與系所討論；不能把未核實的TOEFL57分條件加進校內初審。",
        "predeparture-notice": OBLIGATIONS[0],
        "return-report": OBLIGATIONS[2] + " " + OBLIGATIONS[3],
        "credit-transfer": "出國前與系所確認選課；返國以交換校成績單辦理D3學分抵免，實習抵免另附研修證明。",
    }
    if template.id not in descriptions:
        return None
    def adapt(value):
        if isinstance(value, str):
            return value.replace("長庚大學", "國立臺北科技大學").replace("長庚", "臺北科大")
        if isinstance(value, list):
            return [adapt(x) for x in value]
        if isinstance(value, dict):
            return {k: adapt(v) for k, v in value.items()}
        return value
    payload = adapt(template.model_dump(mode="json"))
    for field in payload["fields"]:
        if template.id == "return-report" and field["id"] == "activity_photos":
            field["max_files"] = 5
            field["help_text"] = "校方要求五張本人入鏡照片，JPG/JPEG/PNG另打包ZIP上傳；本工具報告中的照片不代替ZIP送件。"
        if field["id"] == "class_rank_percent":
            field["help_text"] = DOCS[1] + "校級交換無共同成績門檻；學海平均70分是另一項獎助條件。"
        if field["id"] == "language_test":
            field["options"] = ["TOEFL iBT", "IELTS Academic", "TOEIC", "JLPT", "TOPIK", "其他語檢（依接待校要求）"]
            field["help_text"] = "交換語檢依接待校；學海基本門檻另列IELTS5、舊制iBT60、TOEIC聽讀600等，不作普遍入學標準。"
    initial = template.id in {"exchange-application-data", "study-plan"}
    url = STEP1 if initial else STEP2 if template.id == "credit-transfer" else STEP3
    payload.update(
        description=descriptions[template.id], source_url=url,
        source_checked_at=datetime(2026, 10, 21, tzinfo=timezone.utc),
        official_layout=False, official_form_number=None, official_file_name=None,
        official_download_url=url, default_copies=1, signatures=[], stamps=[],
        stage="校級初審：簽名申請表與文件上傳指定連結" if initial else "行前或返國：依適用程序與通知辦理",
        version="校級交換準備工具-2026-10-21.1",
        destinations=["Step1電子郵件指定上傳連結"] if initial else ["依Step2／Step3適用程序辦理"],
        print_sides="confirm_official", print_note="一般校級初審不收紙本；行前核章、返國獎助核銷與院級流程另依公告。",
        conditional_note="本工具只協助整理；正式申請表須由校方平台產生並簽名上傳，工具輸出不能取代官方申請表。千葉設計學院與雙聯計畫另依各自規定。",
    )
    return ApplicationDocumentTemplate.model_validate(payload)


def _nccu_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    descriptions = {
        "exchange-application-data": "整理國立政治大學校級赴國外（八大語組）及赴大陸地區交換學生甄選應繳資料：iNCCU 線上報名表、語言能力檢定成績單正本（驗畢退還）及影本、英文在學證明正本、英文成績單正本（學士班另須附中文前學期全班排名百分比證明；赴大陸交換繳交中文成績單與排名證明）、交換計畫書與履歷表（含簡歷及自傳）、報名費新臺幣 700 元收據正本及家長（監護人）同意書。",
        "study-plan": "撰寫國立政治大學校級交換甄選必繳之《交換計畫書》與《履歷表（含簡歷及自傳）》（校級國際薦外交換：須分為 2 份文件撰寫，合計占甄選總成績 20%，限電腦繕打、A4 直式橫書，每份各至少 500 字、以 2 頁為限，超出 2 頁不予計分，皆以報考語組之語言撰寫；赴大陸交換：個人自傳 1,000 字以內、研究／學習計畫 3,000 字以內，超過字數恕不受理，書面審查占總成績 35%）。",
        "course-preapproval": "規劃出國交換期間之修課清單與學分採認預審（依《國立政治大學選送學生出國進修與交流實施辦法》及簡章規定，交換生於交換期間每學期至少須修習該校 1 門科目且成績及格；大陸交換大學部須修習 2 門以上、研究所至少 1 門，返國後檢附正式成績單及授課大綱辦理學分採認）。",
        "predeparture-notice": "於志願選填及放榜後完成錄取報到確認、繳納保證金新臺幣 5,000 元，配合國際合作事務處完成姊妹校官方提名（Nomination），並依《錄取校級赴外交換生行前須知》辦理役男出境、護照簽證、海外醫療及意外保險與政大註冊選課。",
        "return-report": "交換期滿返國後 2 個月內依規定格式繳交交換學生心得報告電子檔至國際合作事務處（outbound@nccu.edu.tw；官方未公布固定字數下限），並於返國 2 年內完成國際活動義工服務至少 1 次（大陸交換為參與至少 2 項兩岸交流活動），檢具交換學校修課及格證明辦理保證金 5,000 元無息退還。",
        "credit-transfer": "交換期滿返國後持交換姊妹校核發之正式成績單正本與修課大綱（Syllabus），依國立政治大學學生抵免學分辦法向所屬系所及教務處註冊組申請國外修習科目學分採認。",
    }
    if template.id not in descriptions:
        return None
    def adapt(value):
        if isinstance(value, str):
            return value.replace("長庚大學", "國立政治大學").replace("長庚", "政大")
        if isinstance(value, list):
            return [adapt(x) for x in value]
        if isinstance(value, dict):
            return {k: adapt(v) for k, v in value.items()}
        return value
    payload = adapt(template.model_dump(mode="json"))
    for field in payload["fields"]:
        if field["id"] == "class_rank_percent":
            field["help_text"] = "國立政治大學校級赴國外交換：研究生前學期總平均成績須達 70 分以上或 GPA 2.44 以上，學士班依前學期全班排名百分比換算在校成績（101 減去班排百分比，占總成績 20%）；赴大陸交換在校成績占 30%。"
        if field["id"] == "language_test":
            field["options"] = ["TOEFL iBT（75+）", "IELTS Academic（6.0+）", "JLPT 日檢（N1–N4）", "Goethe / TestDaF（德語 B1–C1）", "DELF / DALF / TCF（法語 B1–C1）", "DELE / SIELE（西語 B1–B2）", "TOPIK 韓檢（1–4 級）", "TORFL 俄語 / TÖMER 土語", "TOEIC（僅布拉格經濟大學、里昂三大及部分亞洲校採認）", "赴大陸交換免附外語檢定"]
            field["help_text"] = "政大校級赴國外交換分為八大語組（語言能力檢定成績占甄選總分 30%、口試占 30%、交換計畫書及履歷表占 20%、在校成績占 20%，不得跨語組選填志願），須繳交距離報名截止日兩年內有效之合格檢定正本查驗；赴大陸地區交換免附。"
    payload.update(
        description=descriptions[template.id],
        source_url="https://outbound.nccu.edu.tw/",
        source_checked_at=NCCU_SOURCE_CHECKED_AT,
        official_layout=False,
        official_form_number="校級交換生甄選報名表" if template.id == "exchange-application-data" else ("交換計畫書與履歷表" if template.id == "study-plan" else None),
        official_file_name=None,
        official_download_url="https://outbound.nccu.edu.tw/",
        default_copies=1,
        signatures=["申請學生親筆簽名", "家長或監護人親筆簽名（家長／監護人同意書）"] if template.id == "exchange-application-data" else [],
        stamps=["政大出納組收訖章或自動繳費機收據（報名費 700 元 / 保證金 5,000 元）"] if template.id == "exchange-application-data" else [],
        stage={"predeparture-notice": "志願分發放榜確認後繳交保證金 5,000 元與辦理提名", "return-report": "返國後 2 個月內繳交交換心得報告電子檔並完成義工服務退還保證金", "credit-transfer": "返國開學後持姊妹校正式成績單辦理學分抵免"}.get(template.id, "於 iNCCU 線上報名並上傳／繳交備審資料至國際合作事務處（行政大樓 8 樓）"),
        version="115準備工具-2026-10-19.1",
        destinations=["國立政治大學國際合作事務處（行政大樓 8 樓）", "所屬系所辦公室"],
        conditional_note="此為個人準備工具；國立政治大學校級交換甄選須先於 iNCCU 校園資訊系統完成線上報名，依當期簡章規定上傳交換計畫書及履歷表（各至少 500 字、2 頁為限），並於截止前完成報名費 700 元繳納與語言檢定正本查驗。",
    )
    return ApplicationDocumentTemplate.model_validate(payload)


def _ncku_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    descriptions = {
        "exchange-application-data": "整理國立成功大學校級薦外交換學生甄選應繳資料：核章申請表（須經系所單位主管核章）、線上志願表（最多選填 15 個志願）、歷年成績單（大學部須附歷年名次證明，總平均達 77 分以上或名次列全班前 50% 以內）、有效外語能力成績證明（前往中國學校交換者仍須提出本校要求之外語能力成績證明）、第一志願之中文及英文讀書或研究計畫、中文及英文自傳（含學、經歷）與優秀表現證明，依序合併為單一 PDF 檔案（上限 50MB）上傳至成大交換生報名系統。",
        "study-plan": "撰寫國立成功大學校級薦外交換甄選必繳之《中文及英文讀書或研究計畫》（占校內甄選總成績 25%）與《中文及英文自傳（含學、經歷）》（與其餘表現合計占總成績 25%）；須就所選填志願學校之「第一志願」分別擬訂中、英文版本，官方簡章未規定固定字數或頁數上限。",
        "course-preapproval": "規劃出國交換期間之修課清單與學分採認預審（依成大簡章規定，交換生於交換期間每學期至少須選修並通過 3 門學分課程，返國後檢附正式成績單及授課大綱向所屬系所及教務處辦理學分抵免）。",
        "predeparture-notice": "於甄選錄取公告後依限完成網路意願確認、繳交紙本家長同意書及繳納保證金新臺幣 8,000 元（低收／中低收入戶為 2,000 元；逾期未確認或確認後無故放棄者不退還），並配合國際事務處國際教育組完成姊妹校官方提名（Nomination）、簽證、海外保險與成大在學註冊選課。",
        "return-report": "交換期滿返國後兩個月內依規定格式完成交換生心得報告（繳交可編輯之 Word 及 PDF 檔各乙份；官方簡章未公布固定字數下限），連同交換校成績單及返國問卷調查寄至國際處業務承辦人信箱，經認定完成交換生義務後始得辦理保證金 8,000 元（低收／中低收入戶 2,000 元）退還；領取跨國雙向研修獎助學金者須於赴外研修結束之日起 1 個月內繳交出國報告書。",
        "credit-transfer": "交換期滿返國後持交換姊妹校核發之正式成績單正本與修課大綱（Syllabus），依國立成功大學學生抵免學分辦法向所屬系所及教務處註冊組申請國外修習科目學分採認。",
    }
    if template.id not in descriptions:
        return None
    def adapt(value):
        if isinstance(value, str):
            return value.replace("長庚大學", "國立成功大學").replace("長庚", "成大")
        if isinstance(value, list):
            return [adapt(x) for x in value]
        if isinstance(value, dict):
            return {k: adapt(v) for k, v in value.items()}
        return value
    payload = adapt(template.model_dump(mode="json"))
    for field in payload["fields"]:
        if field["id"] == "class_rank_percent":
            field["help_text"] = "國立成功大學校級交換：學士班前一學期止歷年學業總平均須達 77 分以上或歷年名次列全班人數前 50% 以內（須檢附歷年成績單及歷年名次證明，在校學業成績占校內甄選總成績 50%）；碩、博士班無最低平均或排名門檻，惟須檢附大學及研究所歷年成績單並經系所主管核章。"
        if field["id"] == "language_test":
            field["options"] = ["TOEFL iBT（72+ / CEFR B2）", "TOEFL ITP（543+ / CEFR B2）", "IELTS Academic（5.5+ / CEFR B2）", "TOEIC 聽讀（785+）＋說寫（口說 160+、寫作 150+）", "GEPT 全民英檢中高級複試通過", "Cambridge Main Suite FCE（B2 First）以上", "JLPT 日語檢定（N1–N3）", "TOPIK 韓語檢定", "Goethe / TestDaF（德語 B1+）", "DELF / DALF / TCF（法語 B1+）", "DELE / SIELE（西語 B1+）"]
            field["help_text"] = "申請英語系及非英語系國家（日韓德法西語組除外）須具備相當於 CEFR B2（高階級）以上之英語檢定成績且符合志願校門檻（不接受托福拼分 MyBest Scores，多益須同時具備聽讀 785 及說寫達標證明）；申請日韓德法西語組須符合各組或志願校門檻；欲前往中國學校交換者仍須提出本校要求之外語能力成績證明。"
    payload.update(
        description=descriptions[template.id],
        source_url="https://oia.ncku.edu.tw/var/file/32/1032/img/3271/424584871.pdf",
        source_checked_at=NCKU_SOURCE_CHECKED_AT,
        official_layout=False,
        official_form_number="出國交換生申請表" if template.id == "exchange-application-data" else ("第一志願中英文自傳與讀書或研究計畫" if template.id == "study-plan" else None),
        official_file_name=None,
        official_download_url="https://oia.ncku.edu.tw/p/404-1032-229870.php?Lang=zh-tw",
        default_copies=1,
        signatures=["申請學生親筆簽名", "系所單位主管簽章", "家長或監護人親筆簽名（錄取後繳交家長同意書）"] if template.id == "exchange-application-data" else [],
        stamps=["系所單位主管核章"] if template.id == "exchange-application-data" else [],
        stage={"predeparture-notice": "錄取公告後完成網路意願確認、繳交家長同意書與保證金 8,000 元", "return-report": "返國後兩個月內繳交交換心得報告 Word/PDF 檔與成績單退還保證金", "credit-transfer": "返國開學後持姊妹校正式成績單辦理學分抵免"}.get(template.id, "於成大赴外交換生報名系統完成線上填報並將第 1–6 項申請文件依序合併為單一 PDF 檔（上限 50MB）上傳"),
        version="116-1準備工具-2026-10-19.1",
        destinations=["國立成功大學赴外交換生線上報名系統", "國立成功大學國際事務處國際教育組（光復校區雲平大樓東棟 7 樓）"],
        conditional_note="此為個人準備工具；國立成功大學校級交換甄選採線上報名與單一 PDF 檔案上傳（檔案上限 50MB），請先於線上系統填寫並列印申請表完成系所單位主管核章，連同第一志願中英文讀書或研究計畫、中英文自傳、成績單與外語檢定證明依序合併上傳；錄取後另依限繳交家長同意書及保證金 8,000 元（低收／中低收入戶 2,000 元）。",
    )
    return ApplicationDocumentTemplate.model_validate(payload)


def _nycu_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    descriptions = {
        "exchange-application-data": "校級115學年度歷史參考：系統填報後上傳中文歷年成績單、中文在學證明、中文研修計畫、中文自傳、語檢、其他有利文件及簽核表；簽核表只有本人、導師／指導教授與系主任／所長三處簽章。116學年度校級新規格待確認，不能套用UST申請。",
        "study-plan": "校級115簡章要求中文研修計畫，包含擬修課列表；另附中文自傳。115-2公告允許中文非母語者使用英文，本輪未核實固定字數或頁數上限。UST須使用該計畫附件，不能用本工具取代。",
        "course-preapproval": "校級交換依實施辦法及接待校要求規劃課程，須取得系所採認；此準備工具不代表課程已核准。",
        "predeparture-notice": "校級115錄取後同意聲明與保證金另依當期通知；初審三處簽核不得與錄取後連帶保證人簽名混為一談。116及UST依各自公告辦理。",
        "return-report": "校級交換期中及期末心得依實施辦法、當期公告及實際研修期間繳交；附3至5張學校生活或活動照片。不能由本工具自動判定已符合保證金退還條件。",
        "credit-transfer": "交換結束後取得接待校正式成績單，回校登錄全部修課成績並向所屬系所申請學分採認；換算與採認依實施辦法及系所審核。",
    }
    if template.id not in descriptions:
        return None
    def adapt(value):
        if isinstance(value, str):
            return value.replace("長庚大學", "國立陽明交通大學").replace("長庚", "陽明交大")
        if isinstance(value, list):
            return [adapt(x) for x in value]
        if isinstance(value, dict):
            return {k: adapt(v) for k, v in value.items()}
        return value
    payload = adapt(template.model_dump(mode="json"))
    for field in payload["fields"]:
        if field["id"] == "class_rank_percent":
            field["help_text"] = "115校級簡章要求中文等第制成績單，大學部含精準排名；研究所新生無本校成績時提供前一學位含畢業排名成績單。審查總分60分不等於學業平均60分。"
        if field["id"] == "language_test":
            field["options"] = ["TOEFL iBT", "IELTS Academic", "TOEIC（須含口說及寫作）", "GEPT（複試通過）", "接待校接受的第三外語檢定"]
            field["help_text"] = "115校級國外及港澳組須語檢，分數依接待校，不能僅以名稱判通過；可先提供含姓名的成績截圖。UST另依各方案及語檢有效期要求。"
    payload.update(
        description=descriptions[template.id],
        source_url="https://oia.nycu.edu.tw/oia/ch/app/data/doc?module=nycu0006&detailNo=1501852894511501312&type=s",
        source_checked_at=datetime(2026, 10, 21, tzinfo=timezone.utc),
        official_layout=False, official_form_number=None, official_file_name=None,
        official_download_url="https://oia.nycu.edu.tw/oia/ch/app/data/doc?module=nycu0006&detailNo=1501852894419226624&type=s",
        default_copies=1,
        signatures=["申請人簽章", "導師／指導教授簽章", "系主任／所長簽章"] if template.id == "exchange-application-data" else [],
        stamps=[], stage="115校級交換歷史準備參考；116與UST須另核對當期文件",
        version="115校級參考-2026-10-21.1", destinations=["校級計畫依系統指定；UST另依電子郵件公告"],
        conditional_note="本工具不能取代官方申請表；來源為115學年度校級簡章，非116校級新簡章或UST表單。UST116第一梯次另須完整PDF於2026/12/31 16:00前寄承辦信箱，依其附件辦理。",
    )
    return ApplicationDocumentTemplate.model_validate(payload)


def _nthu_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    descriptions = {
        "exchange-application-data": "整理國立清華大學校級赴海外及陸港澳交換學生甄選應繳資料：線上申請表（於 https://oga-exchange.vm.nthu.edu.tw/ 填報至多 15 所志願校後匯出 PDF，經導師／指導教授及系所主管核章）、英文歷年成績單（大學部須含累計系排名百分比，須達 GPA 3.20 以上或系排前 50%）、有效外語能力證明（海外交換必備 TOEFL iBT 79+ 或 IELTS 6.5+ 或申請學校要求之同等語言檢定，且成績須於 2 年有效期內）、學習計畫書（Study Plan，中英文撰寫）、自傳（中英文撰寫）、推薦信 2 封及其他有助審查之佐證資料，按順序合併為單一 PDF 檔上傳。",
        "study-plan": "撰寫國立清華大學赴外交換甄選必繳之《學習計畫書（Study Plan）》與《自傳》（以中文及英文撰寫，具體說明交換動機、前五志願姊妹校之選校理由、擬修習專業課程清單與清大畢業學分銜接規劃、跨文化研究或學術交流目標，以及返國後之學習與經驗分享規劃）。",
        "course-preapproval": "規劃出國交換期間之修課清單與學分抵免預審（依國立清華大學出國期間有關學業及學籍處理要點，出國交換期間每學期至少須修習相當於清大 6 學分或至少 2 門課程，返國後持姊妹校正式成績單及課程大綱向系所及教務處註冊組申請學分抵免）。",
        "predeparture-notice": "於初審甄選結果公告後，依限於線上系統確認錄取資格並繳交計畫行政費新臺幣 2,000 元（一經繳交概不退費，經濟不利生檢附證明免繳）及保證金新臺幣 5,000 元（履行交換義務並繳交心得報告後無息退還），配合全球事務處全球移動力組完成姊妹校官方提名（Nomination），並視資格申請清大出國交換獎學金、教育部學海飛颺／學海惜珠或竹竹苗區圓夢獎助金。",
        "return-report": "交換期滿返國後 1 個月內，於全球事務處線上系統上傳交換學生心得報告（至少 2,000 字，含修課經驗、住宿生活、簽證與花費建議及至少 4 張具代表性之交換照片）並填寫問卷，經審核通過後始得辦理新臺幣 5,000 元保證金無息退還及領取後半額度獎學金。",
        "credit-transfer": "交換期滿返國後持姊妹校核發之正式成績單正本、修課大綱（Syllabus）與授課時數證明，依《國立清華大學出國期間有關學業及學籍處理要點》向所屬系所、院及教務處註冊組辦理國外修習科目學分抵免採認。",
    }
    if template.id not in descriptions:
        return None
    def adapt(value):
        if isinstance(value, str):
            return value.replace("長庚大學", "國立清華大學").replace("長庚", "清大")
        if isinstance(value, list):
            return [adapt(x) for x in value]
        if isinstance(value, dict):
            return {k: adapt(v) for k, v in value.items()}
        return value
    payload = adapt(template.model_dump(mode="json"))
    for field in payload["fields"]:
        if field["id"] == "class_rank_percent":
            field["help_text"] = "國立清華大學赴外交換學業成績門檻為「歷年累計 GPA 達 3.20 以上（T 分數 78 分）」或「歷年累計學業成績系排名百分比在前 50% 以內」；大學部申請人須檢附載明累計系排名百分比之英文歷年成績單。"
        if field["id"] == "language_test":
            field["options"] = ["TOEFL iBT（清大基本門檻 79+，不接受 MyBest Scores / Home Edition）", "IELTS Academic（清大基本門檻 6.5+，不接受 One Skill Retake）", "JLPT 日語檢定（N1 / N2，限申請日語授課組別）", "TOPIK 韓語檢定（3–6 級，限申請韓語授課組別）", "Goethe / TestDaF（德語 B1/B2+，限申請德語授課組別）", "DELF / DALF / TCF（法語 B1/B2+，限申請法語授課組別）", "DELE / SIELE（西語 B1/B2+，限申請西語授課組別）", "赴大陸交換免附外語檢定（港澳及海外交換必繳）"]
            field["help_text"] = "申請清大海外交換者，須檢附報名截止日前 2 年內有效之 TOEFL iBT 79 分以上或 IELTS Academic 6.5 以上（或欲申請姊妹校要求之日／韓／德／法／西語檢定）成績單；申請大陸地區交換免附外語檢定。"
    payload.update(
        description=descriptions[template.id],
        source_url="https://oga.site.nthu.edu.tw/p/412-1524-21359.php?Lang=zh-tw",
        source_checked_at=NTHU_SOURCE_CHECKED_AT,
        official_layout=False,
        official_form_number="出國交換學生線上申請表" if template.id == "exchange-application-data" else ("中英文學習計畫書與自傳" if template.id == "study-plan" else None),
        official_file_name=None,
        official_download_url="https://oga.site.nthu.edu.tw/p/406-1524-294575,r8946.php?Lang=zh-tw",
        default_copies=1,
        signatures=["申請學生親筆簽名", "導師或指導教授簽章", "系所（學位學程）主管簽章"] if template.id == "exchange-application-data" else [],
        stamps=["系所辦公室戳章"] if template.id == "exchange-application-data" else [],
        stage={"predeparture-notice": "初審放榜後線上確認錄取並繳交 2,000 元行政費與 5,000 元保證金", "return-report": "返國後 1 個月內上傳交換心得報告（2,000 字以上）退還保證金", "credit-transfer": "返國開學後持姊妹校正式成績單辦理學分抵免"}.get(template.id, "於清大全球處出國交換線上申請系統（https://oga-exchange.vm.nthu.edu.tw/）填報至多 15 個志願並合併單一 PDF 上傳"),
        version="115準備工具-2026-10-19.1",
        destinations=["國立清華大學出國交換生線上申請系統（https://oga-exchange.vm.nthu.edu.tw/）", "國立清華大學全球事務處全球移動力組（旺宏館 2 樓 246 室）"],
        conditional_note="此為個人準備工具；國立清華大學校級出國交換甄選採全線上填報與單一 PDF 檔案上傳，請先於線上系統填報至多 15 個志願並匯出申請表完成導師／指導教授及系所主管核章後，依檢核順序連同英文歷年成績單（含系排名）、2 年內有效外語檢定、中英文學習計畫書、中英文自傳及 2 封推薦信合併上傳至 https://oga-exchange.vm.nthu.edu.tw/ 。",
    )
    return ApplicationDocumentTemplate.model_validate(payload)


def _pccu_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    from .pccu_source_review import ACADEMIC, AWARDS, DOCS, GUIDE, LANGUAGE, OBLIGATIONS, PERIOD
    descriptions = {
        "exchange-application-data": "依申請管道分別備件。" + " ".join(DOCS[k][0] for k in ("oima", "jp", "kr", "mainland", "fr_ru")),
        "study-plan": DOCS["jp"][1] + " " + DOCS["kr"][1] + " " + DOCS["mainland"][0],
        "course-preapproval": OBLIGATIONS[1] + "赴陸名單另分可抵學分與不可抵學分方案，先向系所確認。",
        "predeparture-notice": "母校提名後仍須依接待校規定申請及取得錄取。" + OBLIGATIONS[0] + " ".join(AWARDS),
        "return-report": OBLIGATIONS[3],
        "credit-transfer": "持接待校正式成績單及課程資料，依所屬系所與教務處規定申請抵免。" + OBLIGATIONS[1],
    }
    if template.id not in descriptions:
        return None
    def adapt(value):
        if isinstance(value, str):
            return value.replace("長庚大學", "中國文化大學").replace("長庚", "文大")
        if isinstance(value, list):
            return [adapt(x) for x in value]
        if isinstance(value, dict):
            return {k: adapt(v) for k, v in value.items()}
        return value
    payload = adapt(template.model_dump(mode="json"))
    for field in payload["fields"]:
        if field["id"] == "class_rank_percent":
            field["help_text"] = ACADEMIC
        if field["id"] == "language_test":
            field["options"] = ["尚未取得正式語檢", "TOEFL iBT", "IELTS", "TOEIC", "JLPT", "TOPIK", "其他"]
            field["help_text"] = LANGUAGE
            field["required"] = False
        if field["id"] == "language_score":
            field["required"] = False
        if field["id"] == "english_version":
            field["help_text"] = "語言依管道：赴陸中文、韓文系中文或韓文、法文組中法文；其他依當期表單。"
            field["required"] = False
    payload.update(
        description=descriptions[template.id], source_url=GUIDE,
        source_checked_at="2026-10-21", official_layout=False,
        official_form_number=None, official_file_name=None, official_download_url=None,
        default_copies=1, signatures=[], stamps=[],
        stage="依所選管道及當期通知辦理，不共用簽章或截止時間。",
        version="部分來源核對-2026-10-21.1",
        destinations=["國合組／日文系／韓文系／法俄組／赴陸承辦，依所選管道"],
        conditional_note="個人準備工具，非官方申請表。" + PERIOD + "韓文系以電子郵件繳一份PDF；赴陸第二階段線上加紙本送大恩館310室。",
    )
    return ApplicationDocumentTemplate.model_validate(payload)


def _wzu_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    from .wzu_source_review import ACADEMIC, DOCS, GENERAL_PDF, LANGUAGE, OBLIGATIONS, PERIOD, SECOND
    descriptions = {
        "exchange-application-data": DOCS[0] + " " + DOCS[2],
        "study-plan": DOCS[1],
        "course-preapproval": OBLIGATIONS[0] + " " + OBLIGATIONS[3],
        "predeparture-notice": DOCS[3] + " " + OBLIGATIONS[3],
        "return-report": OBLIGATIONS[4],
        "credit-transfer": "返國後依所屬系科及教務處規定申請境外學分採認；出國前先確認擬修課程與抵免條件。" + OBLIGATIONS[4],
    }
    if template.id not in descriptions:
        return None
    def adapt(value):
        if isinstance(value, str):
            return value.replace("長庚大學", "文藻外語大學").replace("長庚", "文藻")
        if isinstance(value, list):
            return [adapt(x) for x in value]
        if isinstance(value, dict):
            return {k: adapt(v) for k, v in value.items()}
        return value
    payload = adapt(template.model_dump(mode="json"))
    for field in payload["fields"]:
        if field["id"] == "class_rank_percent":
            field["help_text"] = ACADEMIC + "上傳教務處用印之中文歷年成績單含排名，沒有要求所有初審者另繳英文版。"
        if field["id"] == "language_test":
            field["options"] = ["尚未取得正式語檢證明", "TOEFL iBT", "IELTS", "TOEIC", "JLPT", "其他正式語檢"]
            field["help_text"] = LANGUAGE
            field["required"] = False
        if field["id"] == "language_score":
            field["required"] = False
        if field["id"] == "english_version":
            field["label"] = "外文版本"
            field["help_text"] = "英語及華語暨東南亞語組用中文與英文，其他語組用中文與目標語言；與履歷其他內容合計五頁。"
        if field["id"] == "activity_photos":
            field["help_text"] = "此工具最多排入4張照片；不是校方要求張數，返國資料依當期通知。"
    payload.update(description=descriptions[template.id], source_url=SECOND,
        source_checked_at=datetime(2026, 10, 21, tzinfo=timezone.utc),
        official_layout=False, official_form_number="履歷表（包含自傳與學習計畫）" if template.id == "study-plan" else None,
        official_file_name=None, official_download_url=GENERAL_PDF, default_copies=1,
        signatures=[], stamps=[], version="115-2部分核對-2026-10-21.1",
        stage={"predeparture-notice": "分發後依通知繳交換意願切結書並辦理行前程序",
               "return-report": "抵達兩週內報到；返國兩週內線上繳返國資料",
               "credit-transfer": "返國依系科規定辦理抵免"}.get(template.id, "115-2線上初審準備"),
        destinations=["文藻國合處當期公告指定Google表單"],
        conditional_note="此為個人準備工具，初審使用當期Google表單。履歷包含自傳、學習計畫等合計A4五頁、12號字，不含附件；分發後本人及家長簽章另辦。" + PERIOD)
    return ApplicationDocumentTemplate.model_validate(payload)


def _nkust_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    from .nkust_source_review import ACADEMIC, AWARDS, DOCS, GUIDELINES, LANGUAGE, OBLIGATIONS, PERIOD
    descriptions = {
        "exchange-application-data": "以下為115校級歷史流程；116及院系級另依公告。" + " ".join(DOCS[:2]),
        "study-plan": DOCS[2],
        "course-preapproval": OBLIGATIONS[1],
        "predeparture-notice": DOCS[4] + OBLIGATIONS[0] + OBLIGATIONS[2],
        "return-report": OBLIGATIONS[3] + AWARDS[3],
        "credit-transfer": "赴外先與系所確認課程與抵免；返國依教務及系所規定辦理。" + OBLIGATIONS[1],
    }
    if template.id not in descriptions:
        return None
    def adapt(value):
        if isinstance(value, str):
            return value.replace("長庚大學", "國立高雄科技大學").replace("長庚", "高科大")
        if isinstance(value, list):
            return [adapt(x) for x in value]
        if isinstance(value, dict):
            return {k: adapt(v) for k, v in value.items()}
        return value
    payload = adapt(template.model_dump(mode="json"))
    for field in payload["fields"]:
        if field["id"] == "class_rank_percent":
            field["help_text"] = ACADEMIC
        if field["id"] == "language_test":
            field["options"] = ["TOEFL", "IELTS", "TOEIC", "JLPT", "TOPIK", "其他證明", "待確認是否需附"]
            field["help_text"] = LANGUAGE
            field["required"] = False
        if field["id"] in {"language_score", "english_version"}:
            field["required"] = False
        if field["id"] == "english_version":
            field["help_text"] = "115校級一般交換免附研修計畫；學海惜珠計畫篇幅約1000–1500字，未列所有文件須中英雙語。"
    payload.update(description=descriptions[template.id], source_url=GUIDELINES,
        source_checked_at="2026-10-21", official_layout=False, official_form_number=None,
        official_file_name=None, official_download_url=None, default_copies=1, signatures=[], stamps=[],
        stage="依申請年度及校級／院系級／雙聯管道確認",
        version="部分來源核對-2026-10-21.1", destinations=["高科大國際處或院系承辦，依申請管道"],
        conditional_note="此為個人準備工具。" + PERIOD + "115校級志願表簽章後掃描上傳，非全員裝訂紙本送件。")
    return ApplicationDocumentTemplate.model_validate(payload)


def _yuntech_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    from .yuntech_source_review import ACADEMIC, AWARDS, DOCS, GUIDELINES, LANGUAGE, MAINLAND_DOCS, OBLIGATIONS, PERIOD
    descriptions = {
        "exchange-application-data": " ".join(DOCS[:2] + MAINLAND_DOCS),
        "study-plan": DOCS[2] + "赴陸使用中文，依當期公告。",
        "course-preapproval": OBLIGATIONS[1] + AWARDS[4],
        "predeparture-notice": OBLIGATIONS[0] + OBLIGATIONS[2],
        "return-report": OBLIGATIONS[3] + AWARDS[5],
        "credit-transfer": OBLIGATIONS[1],
    }
    if template.id not in descriptions:
        return None
    def adapt(value):
        if isinstance(value, str):
            return value.replace("長庚大學", "國立雲林科技大學").replace("長庚", "雲科大")
        if isinstance(value, list):
            return [adapt(x) for x in value]
        if isinstance(value, dict):
            return {k: adapt(v) for k, v in value.items()}
        return value
    payload = adapt(template.model_dump(mode="json"))
    for field in payload["fields"]:
        if field["id"] == "class_rank_percent":
            field["help_text"] = ACADEMIC
        if field["id"] == "language_test":
            field["options"] = ["TOEIC", "TOEFL", "IELTS", "JLPT", "TOPIK", "其他證明", "赴陸適用文件待確認"]
            field["help_text"] = LANGUAGE
            field["required"] = False
        if field["id"] in {"language_score", "english_version"}:
            field["required"] = False
        if field["id"] == "english_version":
            field["help_text"] = DOCS[2]
    payload.update(description=descriptions[template.id], source_url=GUIDELINES,
        source_checked_at="2026-10-21", official_layout=False, official_form_number=None,
        official_file_name=None, official_download_url=None, default_copies=1,
        signatures=["申請人及指導老師或導師、系所與院主管（申請表）"] if template.id == "exchange-application-data" else [],
        stamps=[], stage="依非大陸／赴陸及申請或獎助階段備件",
        version="部分來源核對-2026-10-21.1", destinations=["雲科大國際事務處，依當期公告指定方式送件"],
        conditional_note="此為個人準備工具。" + PERIOD + " " + DOCS[3])
    return ApplicationDocumentTemplate.model_validate(payload)


def _ntou_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    from .ntou_source_review import ACADEMIC, AWARDS, BROCHURE, DOCS, LANGUAGE, MAINLAND_DOCS, OBLIGATIONS, PERIOD
    descriptions = {
        "exchange-application-data": " ".join(DOCS[:3] + MAINLAND_DOCS[:1]),
        "study-plan": DOCS[3] + DOCS[1],
        "course-preapproval": OBLIGATIONS[1] + AWARDS[4],
        "predeparture-notice": OBLIGATIONS[0] + OBLIGATIONS[3],
        "return-report": OBLIGATIONS[2] + AWARDS[3],
        "credit-transfer": OBLIGATIONS[1],
    }
    if template.id not in descriptions:
        return None
    def adapt(value):
        if isinstance(value, str):
            return value.replace("長庚大學", "國立臺灣海洋大學").replace("長庚", "海大")
        if isinstance(value, list):
            return [adapt(x) for x in value]
        if isinstance(value, dict):
            return {k: adapt(v) for k, v in value.items()}
        return value
    payload = adapt(template.model_dump(mode="json"))
    for field in payload["fields"]:
        if field["id"] == "class_rank_percent":
            field["help_text"] = ACADEMIC
        if field["id"] == "language_test":
            field["options"] = ["TOEFL（需確認分制）", "IELTS Academic", "TOEIC", "JLPT", "TOPIK", "其他語言證明", "赴陸依規定得免附"]
            field["help_text"] = LANGUAGE
            field["required"] = False
        if field["id"] in {"language_score", "english_version"}:
            field["required"] = False
        if field["id"] == "english_version":
            field["help_text"] = "非大陸可依第一志願選中文或英文一份，非全員中英文各份；赴陸另依公告。"
    payload.update(description=descriptions[template.id], source_url=BROCHURE,
        source_checked_at="2026-10-21", official_layout=False, official_form_number=None,
        official_file_name=None, official_download_url=None, default_copies=1,
        signatures=["申請人、系所及學院核章；研究生另指導教授"] if template.id == "exchange-application-data" else [],
        stamps=[], stage="依非大陸／赴陸及申請或獎助階段備件",
        version="部分來源核對-2026-10-21.1", destinations=["海大國際事務處，依各管道當期公告指定承辦與方式送件"],
        conditional_note="此為個人準備工具。" + PERIOD + DOCS[0])
    return ApplicationDocumentTemplate.model_validate(payload)


def _ncue_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    descriptions = {
        "exchange-application-data": "整理國立彰化師範大學出國交換學生暨學海飛颺／惜珠獎學金甄選應繳資料：1. 出國交換學生申請表（國外姊妹校至多填報 10 個志願、大陸地區姊妹校至多填報 3 個志願；須經家長或監護人簽章、導師或指導教授簽章及系所主管核章）與申請資料確認單、2. 中文歷年成績單正本（含學業總平均與班級排名百分比；操行成績平均須達 80 分以上且無小過以上處分，學海飛颺申請者學業總平均須達 80 分以上或班排前 30%）及英文歷年成績單正本、3. 符合報考語組及姊妹校門檻之有效外語檢定成績單影本（大陸地區免附）、4. 中文自傳（800 字以內）與中文讀書計畫（1,500 字以內）及外文自傳與讀書計畫（各 2 頁為限）、5. 師長推薦信 1 封（中英文皆可）、6. 有效護照基本資料頁影本與其他優秀表現證明；於截止日 15:00 前送交進德校區行政大樓 2 樓國際暨兩岸事務處。",
        "study-plan": "撰寫國立彰化師範大學交換生甄選必繳之《中文自傳》（800 字以內）與《中文讀書計畫》（1,500 字以內），並檢附英文（或留學國語言）自傳與讀書計畫（各以 2 頁為限；大陸地區交換生繳交中文自傳與讀書計畫合計 2,500 字以內）。書面資料審查佔校內初審總成績 35%，請具體說明出國動機、擬於志願姊妹校修習之專業領域課程（每學期至少須修讀 1 門課或進行論文研究）及返國後學分抵免與職涯銜接規劃。",
        "course-preapproval": "規劃赴境外姊妹校交換期間之修課清單與學分抵免預審（依《國立彰化師範大學學生出國交換學習實施要點》及《辦理學生抵免學分辦法》規定，出國交換期間須完成彰師大註冊並繳交全額學雜費，每學期於姊妹校至少須修習 1 門課程或進行論文研究；返國後持姊妹校正式成績單與課程大綱向系所及教務處註冊組申請學分採認）。",
        "predeparture-notice": "於國際暨兩岸事務處公告正備取名單後，依限繳交《錄取資格確認書》、《家長同意書》及新臺幣 3,000 元保證金（無正當理由放棄者沒收），配合國際合作組辦理姊妹校官方提名（Nomination）與外校入學申請；出國前須完成役男出境核准、購買涵蓋全期之海外醫療及意外保險、填寫出國程序單，並完成《教育部學海飛颺／惜珠》或《彰師大出國交換學生獎學金》行政契約簽署。",
        "return-report": "交換期滿返國抵臺（以桃園機場入境日計）後 2 週（14 日）內，須向國際暨兩岸事務處繳交 2,500 字以內之《交換學生返國心得報告》（含 5–6 張研修與生活照片，同時提供 Word 檔與 PDF 檔）及回國程序單，並檢附姊妹校正式成績單、護照出入境章影本、登機證正本與電子機票收據，辦理新臺幣 3,000 元保證金無息退還與獎學金尾款核銷（學海受獎生另須義務協助國際處推動國際化業務 8 小時及參加經驗分享會）。",
        "credit-transfer": "交換期滿返國後持姊妹校核發之正式成績單正本與修課大綱（Syllabus），依《國立彰化師範大學學生出國交換學習實施要點》及《辦理學生抵免學分辦法》向所屬系（所）及教務處註冊組辦理境外修習科目學分採認。",
    }
    if template.id not in descriptions:
        return None
    def adapt(value):
        if isinstance(value, str):
            return value.replace("長庚大學", "國立彰化師範大學").replace("長庚", "彰師大")
        if isinstance(value, list):
            return [adapt(x) for x in value]
        if isinstance(value, dict):
            return {k: adapt(v) for k, v in value.items()}
        return value
    payload = adapt(template.model_dump(mode="json"))
    for field in payload["fields"]:
        if field["id"] == "class_rank_percent":
            field["help_text"] = "彰師大《學生出國交換學習實施要點》規定在學期間操行成績平均須達 80 分以上且無小過以上處分（歷年學業成績佔校內初審 20%）；申請教育部《學海飛颺》獎學金者，歷年學業總平均須達 80 分以上或班級排名前 30%。請檢附含排名百分比之中英文歷年成績單正本。"
        if field["id"] == "language_test":
            field["options"] = ["TOEIC 聽讀測驗（英語組校內基準 550+；歐美紐澳多要求 B2=785+）", "TOEFL iBT（英語組校內基準 61+；歐美名校 72–80+）", "IELTS 學術組（英語組校內基準 5.0+；歐美名校 5.5–6.5+）", "GEPT 全民英檢（中高級初試以上）", "JLPT 日語能力試驗（日語組基準 N3+；明治／愛知／廣島／千葉／鳴門 N1–N2+）", "TOPIK 韓語能力測驗（韓語組基準 2 級以上；首爾市立／中央／釜山 3–4 級）", "Goethe / TestDaF 德語（B1–B2+）或 DELF 法語／DELE 西語（A2–B2+）", "大陸地區姊妹校（免附外語能力檢定證明）"]
            field["help_text"] = "依彰師大 116 學年度交換簡章規定，報考國外非大陸姊妹校須具備至少 CEFR B1（TOEIC 550 / TOEFL iBT 61 / IELTS 5.0 / GEPT 中高級初試 / JLPT N3 / TOPIK 2 級）或各姊妹校指定之更高外語門檻（外語能力佔校內初審 20%）。"
    payload.update(
        description=descriptions[template.id],
        source_url="https://oicaweb.ncue.edu.tw/p/406-1019-28981,r174.php?Lang=zh-tw",
        source_checked_at=NCUE_SOURCE_CHECKED_AT,
        official_layout=False,
        official_form_number="出國交換學生申請表、申請資料確認單與家長同意書" if template.id == "exchange-application-data" else ("中英文自傳（800字內）與讀書計畫（1,500字內）" if template.id == "study-plan" else None),
        official_file_name=None,
        official_download_url="https://oicaweb.ncue.edu.tw/var/file/19/1019/img/542278849.pdf",
        default_copies=1,
        signatures=["申請學生親筆簽名", "家長或監護人親筆簽章", "導師或指導教授簽章", "所屬系所主管簽章"] if template.id == "exchange-application-data" else [],
        stamps=["所屬系所辦公室核章"] if template.id == "exchange-application-data" else [],
        stage={"predeparture-notice": "錄取後繳交確認書、家長同意書及 $3,000 保證金並辦理提名與獎學金簽約", "return-report": "返國抵臺後 14 日內繳交 2,500 字內心得報告（Word+PDF）與核銷單據退還保證金", "credit-transfer": "返國後持姊妹校正式成績單辦理境外學分採認"}.get(template.id, "備齊紙本申請表與附件（經家長、導師／指導教授及系所主管簽章）於截止日 15:00 前送交進德校區行政大樓 2 樓國際暨兩岸事務處"),
        version="116準備工具-2026-10-20.1",
        destinations=["國立彰化師範大學國際暨兩岸事務處（進德校區行政大樓 2 樓）"],
        conditional_note="此為個人準備工具；彰師大出國交換甄選須於截止日（大陸春季班 115/10/27 15:00、國外非大陸 116 學年 116/01/13 15:00）前，將經家長、導師（或指導教授）及系所主管核章之申請表、申請資料確認單、中英文歷年成績單正本（含排名）、外語檢定證明、中英文自傳與讀書計畫及推薦信送交進德校區行政大樓 2 樓國際暨兩岸事務處（欲申請教育部學海飛颺／惜珠獎學金者須於校內收件截止日前一併繳交申請資料）。",
    )
    return ApplicationDocumentTemplate.model_validate(payload)


def _nknu_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    descriptions = {
        "exchange-application-data": "整理國立高雄師範大學選送學生出國研修暨學海飛颺／惜珠獎助學金甄選應繳資料：1. 出國交換／出國研修獎助學金申請表（須經指導教授或導師、系所主管及院長簽章推薦）、2. 家長或監護人同意書、3. 歷年成績單正本（含學業總平均、GPA 與班級排名；非大陸地區須附英文成績單，大陸地區附中文成績單；學士班須達 GPA 2.44／70 分以上且班排前 50%，碩博士班須達 GPA 3.38／80 分以上，操行 80 分以上且無記過處分）、4. 兩年內有效之外語能力檢定證明影本（大陸地區免附；申請校內獎助須達 CEFR B1／B2）、5. 出國研究計畫書與自傳（A4 兩頁為限；非大陸地區須以英文或該國語言撰寫）、6. 教師推薦信 2 封（非大陸地區須為英文或該國語言）；經系所及學院初審核章後，於截止日前送交和平校區行政大樓 6 樓國際事務處。",
        "study-plan": "撰寫國立高雄師範大學出國交換甄選必繳之《出國研究計畫書》與《自傳》（A4 兩頁為限），若申請非大陸地區之國外姊妹校，須使用英文或該國語言撰寫（大陸地區使用中文撰寫）。書面資料審查佔校內甄選總成績 35%，請具體說明出國動機、擬於志願姊妹校修習之專業領域課程、語言能力準備及返國後學分抵免與職涯銜接規劃。",
        "course-preapproval": "規劃赴境外姊妹校交換期間之修課清單與學分抵免預審（依《國立高雄師範大學學生出國期間有關學業及學籍處理要點》規定，出國交換期間須辦理高師大註冊並繳交全額學雜費；返國後持姊妹校正式成績單與課程大綱向系所及教務處申請境外修習科目學分採認）。",
        "predeparture-notice": "於國際事務處公告甄選錄取名單後，依限繳交《錄取資格確認書》及新臺幣 5,000 元保證金（無正當理由放棄者沒收，全額撥入校務基金），配合國際事務處辦理姊妹校官方提名（Nomination）與外校入學申請；出國前須完成役男出境核准、購買涵蓋全期之海外醫療及意外保險、填寫出國報告單，並完成《教育部學海飛颺／惜珠》或《高師大學生出國研修獎助學金》行政契約簽署。",
        "return-report": "交換期滿返國後 1 個月內，須向國際事務處繳交 3,000 字以上之《出國研修心得報告》電子檔（含研修生活照片 4 張以上），並檢附姊妹校正式成績單、護照出入境章影本、登機證正本與電子機票收據，辦理新臺幣 5,000 元保證金無息退還與獎助學金尾款核銷（受獎生並有義務配合參加出國研修經驗分享會）。",
        "credit-transfer": "交換期滿返國後持姊妹校核發之正式成績單正本與修課大綱（Syllabus），依《國立高雄師範大學學生出國期間有關學業及學籍處理要點》及《學生抵免學分辦法》向所屬系（所）及教務處辦理境外修習科目學分採認。",
    }
    if template.id not in descriptions:
        return None
    def adapt(value):
        if isinstance(value, str):
            return value.replace("長庚大學", "國立高雄師範大學").replace("長庚", "高師大")
        if isinstance(value, list):
            return [adapt(x) for x in value]
        if isinstance(value, dict):
            return {k: adapt(v) for k, v in value.items()}
        return value
    payload = adapt(template.model_dump(mode="json"))
    for field in payload["fields"]:
        if field["id"] == "class_rank_percent":
            field["help_text"] = "高師大《選送學生出國研修實施要點》規定：學士班歷年學業總平均須達 GPA 2.44（百分制 70 分）以上且班級排名前 50%，碩博士班歷年學業總平均須達 GPA 3.38（百分制 80 分）以上，操行 80 分以上且無記過處分（學業成績佔校內甄選 20%）。請檢附含 GPA 與排名之歷年成績單正本。"
        if field["id"] == "language_test":
            field["options"] = ["TOEIC 聽讀測驗（校內獎助亞洲 B1=550+／歐美紐澳 B2=785+）", "TOEFL iBT（校內獎助 B1=42+／歐美紐澳 B2=72+；雪梨／維多利亞 79–85+）", "IELTS 學術組（校內獎助 B1=4.0+／歐美紐澳 B2=5.5+；雪梨／維多利亞 6.0–6.5+）", "GEPT 全民英檢（中級複試 B1／中高級複試 B2 以上）", "JLPT 日語能力試驗（日本姊妹校 N3–N2+；大阪教育／法政／中央／三重 N2+）", "TOPIK 韓語能力測驗（韓國姊妹校 2–3 級以上；梨花／漢陽／韓國外大 3–4 級）", "Goethe / TestDaF 德語（B1–B2+）或 DELF 法語／DELE 西語（B1–B2+）", "大陸地區姊妹校（免附外語能力檢定證明）"]
            field["help_text"] = "依高師大《選送學生出國研修實施要點》與《學生出國研修獎助學金支給要點》規定，報考國外非大陸姊妹校須具備兩年內有效外語檢定證明（外語能力佔校內甄選 20%），申請校內出國研修獎助學金者須達 CEFR B1（亞洲地區）或 CEFR B2（歐美紐澳地區）。"
    payload.update(
        description=descriptions[template.id],
        source_url="https://oia.nknu.edu.tw/exchange-programs.php",
        source_checked_at=NKNU_SOURCE_CHECKED_AT,
        official_layout=False,
        official_form_number="出國交換／出國研修獎助學金申請表與家長同意書" if template.id == "exchange-application-data" else ("出國研究計畫書與自傳（A4兩頁為限）" if template.id == "study-plan" else None),
        official_file_name=None,
        official_download_url="https://oia.nknu.edu.tw/uploads/files/20251007113419_68e48a3b07252.doc",
        default_copies=1,
        signatures=["申請學生親筆簽名", "家長或監護人親筆簽章", "導師或指導教授簽章", "所屬系所主管簽章", "所屬學院院長簽章"] if template.id == "exchange-application-data" else [],
        stamps=["所屬系所辦公室核章", "所屬學院辦公室核章"] if template.id == "exchange-application-data" else [],
        stage={"predeparture-notice": "錄取後繳交確認書及 $5,000 保證金並辦理提名與獎助學金簽約", "return-report": "返國後 1 個月內繳交 3,000 字以上心得報告與核銷單據退還保證金", "credit-transfer": "返國後持姊妹校正式成績單辦理境外學分採認"}.get(template.id, "備齊紙本申請表與附件（經家長、導師／指導教授、系所主管及院長簽章）於截止日前送交和平校區行政大樓 6 樓國際事務處"),
        version="115準備工具-2026-10-20.1",
        destinations=["國立高雄師範大學國際事務處（和平校區行政大樓 6 樓）"],
        conditional_note="此為個人準備工具；高師大出國交換暨學海飛颺／惜珠獎助學金甄選須於截止日（秋季班每年 2 月底、春季班每年 9 月中旬至 10 月中旬）前，將經家長、導師（或指導教授）、系所主管及院長核章之申請表、歷年成績單正本（含 GPA 與班級排名）、有效外語檢定證明、出國研究計畫書與自傳（A4 兩頁內）及 2 封推薦信送交和平校區行政大樓 6 樓國際事務處。",
    )
    return ApplicationDocumentTemplate.model_validate(payload)


def _tmu_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    descriptions = {
        "exchange-application-data": "整理臺北醫學大學選送學生出國研修暨學海四項計畫（飛颺／惜珠／築夢／新南向築夢）及校內《境外研修暨見實習獎勵辦法》甄選應繳資料：1. 出國研修／境外研修獎補助申請表（須經指導教授或導師、系所主管及學院院長初審核章）、2. 歷年成績單正本（含學業總平均、GPA 與班／系排名；學海飛颺及惜珠須於北醫大就讀一學期以上且歷年成績達每系所排名前 40% 或每班排名前 30%［研究所免附排名］、操行成績 80 分以上；跨國雙聯學位須達 GPA 3.0／約 75 分以上）、3. 有效外語能力檢定證明影本（學海飛颺／惜珠英語系國家須達 TOEFL iBT 79 或 IELTS 5.5，非英語系國家須達 TOEFL iBT 75 或 IELTS 5.0，日語須達 JLPT N2；校內境外研修獎學金須達 CEFR B2［TOEFL iBT 72 / IELTS 5.5 / TOEIC 785］）、4. 出國研修計畫書與自傳（含動機、擬修習專業課程或臨床見實習與實驗室研究規劃）、5. 國外盟校入學許可或邀請函（Offer / Invitation Letter）、6. 師長推薦信與家長同意書；經各學院初審推薦排序後，於截止日前送交醫學綜合大樓後棟 4 樓國際事務處。",
        "study-plan": "撰寫臺北醫學大學出國交換、跨國雙聯、海外研究或臨床見實習必繳之《出國研修計畫書》與《個人自傳》。請具體說明赴外動機、擬於目標盟校修習之專業領域課程或臨床見實習／實驗室研究內容、外語能力準備，以及返國後學分抵免（授課滿 18 小時計 1 學分、實驗或見實習 36–54 小時計 1 學分）與醫學／生醫專業職涯銜接規劃。",
        "course-preapproval": "辦理赴境外大學校院修讀課程或見實習之《學生境外研修簽報表》教務備查與學分採認預審（依《臺北醫學大學學生境外修讀課程實施辦法》規定，修讀雙聯學位須於研修前 1 個月、修習學分或研究見實習須於研修前 3 個工作日由所屬系所檢具簽報表與雙方合作協議送教務處備查；境外研修期間必須辦理北醫大註冊，休學期間修習之學分不予採計；大陸地區醫事人員高等學校學分不予採認）。",
        "predeparture-notice": "於國際事務處或學院公告錄取及獎學金核定名單後，配合國際事務處完成國外盟校提名（Nomination）與外校入學許可取得；出國前須完成所屬系所《學生境外研修簽報表》送教務處備查、簽署《教育部學海計畫行政契約書》或《校內境外研修獎學金切結書》、購買涵蓋境外全期之海外醫療及意外保險（役男另辦緩徵出境），並確認已完成北醫大當學期註冊。",
        "return-report": "境外研修期滿返國後，學海計畫受獎生須於返國 14 日內登入教育部學海計畫資訊網填報問卷並上傳 1,000 字以內中／英文成果報告書（含研修照片 4 張以上），並於返國後 1 個月內檢附來回電子機票收據、登機證正本、護照出入境章影本、盟校正式成績單（或見實習證明）及成果報告書，向國際事務處辦理獎補助款核銷結案與參加經驗分享會。",
        "credit-transfer": "境外研修期滿返國後持國外盟校核發之正式成績單正本（或修業完成證明）與課程大綱（Syllabus），依《臺北醫學大學學生境外修讀課程實施辦法》及《學生抵免學分要點》（授課 18 小時計 1 學分，實驗、見實習 36–54 小時計 1 學分）向所屬系（所）、學院及教務處註冊組申請境外修習科目學分採認。",
    }
    if template.id not in descriptions:
        return None
    def adapt(value):
        if isinstance(value, str):
            return value.replace("長庚大學", "臺北醫學大學").replace("長庚", "北醫大")
        if isinstance(value, list):
            return [adapt(x) for x in value]
        if isinstance(value, dict):
            return {k: adapt(v) for k, v in value.items()}
        return value
    payload = adapt(template.model_dump(mode="json"))
    for field in payload["fields"]:
        if field["id"] == "class_rank_percent":
            field["help_text"] = "北醫大《教育部學海飛颺及學海惜珠甄選簡章》規定：須於北醫大就讀一學期以上，歷年成績達每系所排名前 40% 或每班排名前 30%（研究所免附排名），且操行成績達 80 分以上；申請跨國雙聯學位者歷年 GPA 須達 3.0（約 75 分）以上。請檢附含 GPA 與排名之歷年成績單正本。"
        if field["id"] == "language_test":
            field["options"] = ["TOEFL iBT（學海英語系國家 79+／非英語系 75+；校內獎學金 B2=72+；CWRU／OSU／USC 80–100+）", "IELTS 學術組（學海英語系國家 5.5+／非英語系 5.0+；校內獎學金 B2=5.5+；Kings／Dundee／Salford 6.0–6.5+）", "TOEIC 聽讀測驗（校內境外研修獎學金 CEFR B2=785+）", "GEPT 全民英檢（中高級複試 B2 以上）", "JLPT 日語能力試驗（學海日本盟校 N2+；東北／北海道／東京理科／九州 N2+）", "其他歐洲／東南亞外語檢定（依學海新南向築夢或盟校規定）", "大陸地區交流（大陸醫事人員高等學校學分不予採認，且不得涉及醫學人才培養）"]
            field["help_text"] = "依北醫大《教育部學海飛颺／惜珠甄選簡章》與《境外研修暨見實習獎勵辦法》規定：學海飛颺／惜珠英語系國家須達 TOEFL iBT 79 或 IELTS 5.5、非英語系國家須達 TOEFL iBT 75 或 IELTS 5.0、日語須達 JLPT N2；申請校內境外研修獎學金須達 CEFR B2（TOEFL iBT 72 / IELTS 5.5 / TOEIC 785）。"
    payload.update(
        description=descriptions[template.id],
        source_url="https://oge.tmu.edu.tw/tmu-goes-international/grants-overview/",
        source_checked_at=TMU_SOURCE_CHECKED_AT,
        official_layout=False,
        official_form_number="出國研修／境外研修獎補助申請表與學生境外研修簽報表" if template.id == "exchange-application-data" else ("出國研修計畫書與自傳" if template.id == "study-plan" else None),
        official_file_name=None,
        official_download_url="https://oge.tmu.edu.tw/wp-content/uploads/2025/11/%E6%95%99%E8%82%B2%E9%83%A8115%E5%B9%B4%E5%BA%A6%E9%81%B8%E9%80%81%E5%AD%B8%E7%94%9F%E5%87%BA%E5%9C%8B%E7%A0%94%E4%BF%AE%E8%A8%88%E7%95%AB%EF%BC%9A%E5%AD%B8%E6%B5%B7%E9%A3%9B%E9%A3%9B%E3%80%81%E5%AD%B8%E6%B5%B7%E6%83%9C%E7%8F%A0%E7%94%84%E9%81%B8%E7%B0%A1%E7%AB%A0.pdf",
        default_copies=1,
        signatures=["申請學生親筆簽名", "家長或監護人親筆簽章", "指導教授或導師簽章", "所屬系所主管簽章", "所屬學院院長簽章"] if template.id == "exchange-application-data" else [],
        stamps=["所屬系所辦公室核章", "所屬學院辦公室核章"] if template.id == "exchange-application-data" else [],
        stage={"predeparture-notice": "錄取後辦理系所《學生境外研修簽報表》教務處備查、盟校提名及獎學金簽約", "return-report": "返國 14 日內上傳學海 1,000 字內成果報告（含照片 4 張以上）並於 1 個月內完成核銷", "credit-transfer": "返國後持盟校正式成績單與課程大綱辦理境外學分採認"}.get(template.id, "先向所屬學院提交申請表件初審排序，再由學院於截止日（1月15日／5月15日／9月7日）前彙送醫學綜合大樓後棟 4 樓國際事務處"),
        version="115準備工具-2026-10-20.1",
        destinations=["臺北醫學大學所屬學院辦公室（初審推薦）", "臺北醫學大學國際事務處全球合作組（信義校區醫學綜合大樓後棟 4 樓）"],
        conditional_note="此為個人準備工具；北醫大教育部學海四項計畫（每年 12 月各學院收件、1 月 15 日國際處截止；第二次徵求 8 月各學院收件、9 月初截止）與校內《境外研修暨見實習獎勵辦法》（每年 1 月 15 日及 5 月 15 日截止）須先經系所與學院初審核章，出國前並須依《學生境外修讀課程實施辦法》由系所將《學生境外研修簽報表》送教務處備查（雙聯前 1 個月、修習學分或見實習前 3 個工作日）。",
    )
    return ApplicationDocumentTemplate.model_validate(payload)


def _csmu_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    descriptions = {
        "exchange-application-data": "整理中山醫學大學選送學生出國研修、跨國雙聯學位暨教育部學海四項計畫（學海飛颺／惜珠／築夢／新南向築夢）及校內《獎勵學生出國研修辦法》甄選應繳資料：1. 出國交換／雙聯學位／學海計畫申請表（須經導師或指導教授、所屬系所主管及學院院長初審核章）、2. 歷年成績單正本（含學業總平均、GPA 與班級／系所排名；學海飛颺及惜珠須於中山醫就讀一學期以上且歷年成績達系所前 40% 或班級前 30%［研究所免附排名］、操行成績 80 分以上；跨國雙聯學位及校級交換須達各專案規定 GPA，如奧克蘭大學生醫雙聯 GPA 3.2、安德魯大學 3.5+0.5+1 MBA GPA 2.50–2.75）、3. 有效外語能力檢定證明影本（例如奧克蘭大學生醫 4+1/4+2 雙聯 TOEFL iBT 79 / IELTS 6.5 / Duolingo 105、安德魯大學 MBA TOEFL iBT 80 / IELTS 6.5、日本姊妹校 JLPT N2–N3、韓國姊妹校 TOPIK 2–3 級或英語檢定證明）、4. 出國讀書計畫書與中英文自傳（含申請動機、擬於目標姊妹校修習之專業領域課程或臨床見實習／實驗室研究規劃）、5. 師長推薦信與家長同意書；經各系所與學院初審推薦後，於截止日前送交正心樓國際事務處。",
        "study-plan": "撰寫中山醫學大學出國交換、跨國雙聯（奧克蘭大學生醫系 4+1/4+2、安德魯大學 3.5+0.5+1 MBA、杜肯大學碩士銜接、德島文理大學 4+2 藥學雙聯）、海外研究（UCSD 暑期研究獎學金）或臨床見實習必繳之《出國讀書計畫書》與《個人自傳》。請具體說明赴外動機、擬於目標姊妹校修習之專業課程或臨床見實習／實驗室研究內容、外語能力準備，以及返國後學分抵免（依《中山醫學大學辦理學生境外學習及跨校修讀雙聯學位實施辦法》，兩校修業時間合計須達學士班至少 32 個月、碩士班至少 12 個月、博士班至少 24 個月，且於單一學校修習學分數不得低於畢業應修總學分數三分之一）與醫療健康專業職涯規劃。",
        "course-preapproval": "辦理赴境外大學校院修讀課程、跨國雙聯或臨床見實習之選課預審與教務核備（依《中山醫學大學辦理學生境外學習及跨校修讀雙聯學位實施辦法》與《學生抵免學分辦法》規定，出國前須由所屬系所及教務處確認擬修習科目與返國學分抵免對照；出國期間必須辦理中山醫學大學註冊並保有在學學籍；大陸地區醫事人員高等學校學分依教育部規定不予採認醫事國考資格）。",
        "predeparture-notice": "於國際事務處或學院公告錄取及獎學金核定名單後，配合國際事務處完成國外姊妹校提名（Nomination）與入學許可（Offer / Invitation Letter）取得；出國前須簽署《教育部學海計畫行政契約書》或《校內出國研修補助切結書》、完成役男緩徵出境申請、購買涵蓋境外全期之海外醫療及意外保險，並確認已完成中山醫當學期註冊。",
        "return-report": "境外研修期滿返國後，教育部學海計畫受獎生須於返國 14 日內登入教育部學海計畫資訊網填報問卷並上傳 1,000–2,000 字中／英文成果報告書（含研修與生活照片 4 張以上），並於返國後 1 個月內檢附來回電子機票收據、登機證正本、護照出入境章影本、姊妹校正式成績單（或見實習證明）及出國交換心得報告（提供國際事務處刊登於《出國交換學生經驗分享》專區），向國際事務處辦理獎補助款核銷結案及參加成果分享會。",
        "credit-transfer": "境外研修期滿返國後持國外姊妹校核發之正式成績單正本（或修業完成證明）與課程大綱（Syllabus），依《中山醫學大學辦理學生境外學習及跨校修讀雙聯學位實施辦法》及《學生抵免學分辦法》向所屬系（所）、學院及教務處註冊課務組申請境外修習科目學分採認。",
    }
    if template.id not in descriptions:
        return None
    def adapt(value):
        if isinstance(value, str):
            return value.replace("長庚大學", "中山醫學大學").replace("長庚", "中山醫")
        if isinstance(value, list):
            return [adapt(x) for x in value]
        if isinstance(value, dict):
            return {k: adapt(v) for k, v in value.items()}
        return value
    payload = adapt(template.model_dump(mode="json"))
    for field in payload["fields"]:
        if field["id"] == "class_rank_percent":
            field["help_text"] = "中山醫《教育部學海飛颺及學海惜珠甄選規定》與《獎勵學生出國研修辦法》：須於中山醫就讀一學期以上，歷年成績達系所前 40% 或班級前 30%（研究所免附排名），且操行成績達 80 分以上；申請奧克蘭大學生醫系 4+1/4+2 雙聯須達 GPA 3.2（約 80 分）、安德魯大學 3.5+0.5+1 MBA 須達 GPA 2.50–2.75。請檢附含 GPA 與排名之歷年成績單正本。"
        if field["id"] == "language_test":
            field["options"] = ["TOEFL iBT（奧克蘭大學雙聯 79+／安德魯大學 MBA 80+／學海飛颺 72–79+）", "IELTS 學術組（奧克蘭大學／安德魯大學雙聯 6.5+／學海飛颺 5.5+）", "Duolingo English Test（奧克蘭大學生醫雙聯 105+）", "TOEIC 聽讀測驗（校內出國研修補助 CEFR B1=550+／B2=785+）", "GEPT 全民英檢（中級複試 B1／中高級複試 B2 以上）", "JLPT 日語能力試驗（東京醫科齒科／東北／長崎／高崎健康福祉／目白／德島文理 N2–N3+）", "TOPIK 韓語能力測驗（高麗／嘉泉／乙支／水原 2–3 級以上或英語檢定）", "大陸與澳門姊妹校（免外語檢定；依各專案簡章辦理，大陸醫事學歷不予採認考照）"]
            field["help_text"] = "依中山醫《辦理學生境外學習及跨校修讀雙聯學位實施辦法》、《獎勵學生出國研修辦法》與各專案簡章規定：申請非華語區姊妹校交換、雙聯或學海計畫須檢附有效外語能力證明（如奧克蘭雙聯 TOEFL 79 / IELTS 6.5 / Duolingo 105、安德魯 MBA TOEFL 80 / IELTS 6.5、日本姊妹校 JLPT N2–N3）。"
    payload.update(
        description=descriptions[template.id],
        source_url="https://oia.csmu.edu.tw/p/412-1017-105.php?Lang=zh-tw",
        source_checked_at=CSMU_SOURCE_CHECKED_AT,
        official_layout=False,
        official_form_number="出國交換／雙聯學位／學海計畫申請表" if template.id == "exchange-application-data" else ("出國讀書計畫書與自傳" if template.id == "study-plan" else None),
        official_file_name=None,
        official_download_url="https://oia.csmu.edu.tw/p/412-1017-6339.php?Lang=zh-tw",
        default_copies=1,
        signatures=["申請學生親筆簽名", "家長或監護人親筆簽章", "導師或指導教授簽章", "所屬系所主管簽章", "所屬學院院長簽章"] if template.id == "exchange-application-data" else [],
        stamps=["所屬系所辦公室核章", "所屬學院辦公室核章"] if template.id == "exchange-application-data" else [],
        stage={"predeparture-notice": "錄取後辦理選課預審、姊妹校提名及學海或校內獎補助簽約", "return-report": "返國 14 日內上傳學海成果報告並於 1 個月內繳交交換經驗分享報告與核銷單據", "credit-transfer": "返國後持姊妹校正式成績單與課程大綱辦理境外學分採認"}.get(template.id, "備齊申請表與附件（經家長、導師／指導教授、系所主管及院長簽章）於截止日前送交正心樓國際事務處"),
        version="115準備工具-2026-10-21.1",
        destinations=["中山醫學大學所屬系所與學院辦公室（初審推薦）", "中山醫學大學國際事務處（臺中市南區建國北路一段110號正心樓）"],
        conditional_note="此為個人準備工具；中山醫教育部學海四項計畫（每年 2–3 月收件）、跨國雙聯學位（奧克蘭大學生醫系 4+1/4+2、安德魯大學 3.5+0.5+1 MBA、杜肯大學、德島文理大學 4+2）與校級交換／臨床見實習甄選須先經系所與學院核章，出國期間須維持中山醫在學註冊，且於單一學校修習學分數不得低於畢業應修總學分數三分之一。",
    )
    return ApplicationDocumentTemplate.model_validate(payload)


def _cmu_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    descriptions = {
        "exchange-application-data": "整理中國醫藥大學選送學生出國研修、跨國雙聯學位（Queen's University Belfast 4+1、KGI、Georgia State University、University of Texas Health Science Center at Houston 等 7 校 11 學程）暨教育部學海四項計畫（學海飛颺／惜珠／築夢／新南向築夢）及校內《獎勵學生出國研習及開拓國際視野辦法》甄選應繳資料：1. 出國交換／雙聯學位／學海計畫申請表（須經導師或指導教授、所屬系所主管及學院院長初審核章）、2. 歷年成績單正本（含學業總平均、GPA 與班級／系所排名；依《選送學生出國研修辦法》第四條，須於中國醫藥大學就讀滿一學年以上、歷年學業總平均達 80 分［GPA 3.0／A-］以上或名列全班前 20%，且前一學期操行成績達 80 分以上；學海飛颺須名列全班前 50%）、3. 有效外語能力檢定證明影本（校內最低基準為 TOEFL iBT 57 / ITP 500、IELTS 4.0、TOEIC 550 或 GEPT 中級複試；雙聯學位如英國貝爾法斯特女王大學須達 IELTS 6.5、日本姊妹校須達 JLPT N2–N3、韓國姊妹校須達 TOPIK 2–3 級或英語檢定）、4. 中英文自傳與出國研修讀書計畫書（含申請動機、擬於目標盟校修習之專業領域課程或海外臨床見實習／實驗室研究規劃）、5. 師長推薦信與家長同意書；經各系所與學院初審推薦排序後，於截止日前送交水湳校區卓越大樓國際事務處。",
        "study-plan": "撰寫中國醫藥大學出國交換、跨國雙聯學位（英國 Queen's University Belfast 藥學／生技 4+1、美國 Keck Graduate Institute 藥學／生醫、Georgia State University 物理治療／運醫、UTHealth Houston 公共衛生、法國圖盧茲大學等）、海外研究或醫牙中醫藥護物治臨床見實習必繳之《出國研修讀書計畫書》與《個人自傳》。請具體說明赴外動機、擬於目標盟校修習之專業課程或臨床見實習／實驗室研究內容、外語能力準備，以及返國後學分抵免（依《中國醫藥大學與境外大學校院辦理跨國雙聯學制實施辦法》，兩校修業時間合計須達學士班至少 32 個月、碩士班至少 12 個月、博士班至少 24 個月，且於兩校修習學分數合計須超過畢業應修總學分數三分之一）與醫藥生技專業職涯規劃。",
        "course-preapproval": "辦理赴境外大學校院修讀課程、跨國雙聯學位或海外臨床見實習之選課預審與教務核備（依《中國醫藥大學學生出國期間有關學業及學籍處理要點》與《辦理跨國雙聯學制實施辦法》規定，出國前須由所屬系所及教務處確認擬修習科目與返國學分抵免對照；出國研修期間必須維持中國醫藥大學在學註冊，休學期間修習之學分不予採認；大陸地區醫事人員高等學校學歷依教育部規定不予採認醫事國考資格）。",
        "predeparture-notice": "於國際事務處或各學院公告錄取及獎學金核定名單後，配合國際事務處完成國外盟校提名（Nomination）與入學許可（Offer / Invitation Letter）取得；出國前須簽署《教育部學海計畫行政契約書》或《校內出國研習補助切結書》、完成役男緩徵出境申請、購買涵蓋境外全期之海外醫療及意外保險，並確認已完成中國醫藥大學當學期註冊。",
        "return-report": "境外研修期滿返國後，教育部學海計畫受獎生須於返國 14 日內登入教育部學海計畫資訊網填報問卷並上傳 1,000–2,000 字中／英文成果報告書（含研修與生活照片 4 張以上），並於返國後 1 個月內檢附來回電子機票收據、登機證正本、護照出入境章影本、盟校正式成績單（或臨床見實習證明）及出國研修成果報告（提供國際事務處刊登於《出國交換／實習成果報告》專區），向國際事務處辦理獎補助款核銷結案及參加國際移動力成果分享會。",
        "credit-transfer": "境外研修期滿返國後持國外盟校核發之正式成績單正本（或修業完成證明）與課程大綱（Syllabus），依《中國醫藥大學學生出國期間有關學業及學籍處理要點》、《辦理跨國雙聯學制實施辦法》及《學生抵免學分辦法》向所屬系（所）、學院及教務處註冊課務組申請境外修習科目學分採認。",
    }
    if template.id not in descriptions:
        return None
    def adapt(value):
        if isinstance(value, str):
            return value.replace("長庚大學", "中國醫藥大學").replace("長庚", "中國醫")
        if isinstance(value, list):
            return [adapt(x) for x in value]
        if isinstance(value, dict):
            return {k: adapt(v) for k, v in value.items()}
        return value
    payload = adapt(template.model_dump(mode="json"))
    for field in payload["fields"]:
        if field["id"] == "class_rank_percent":
            field["help_text"] = "中國醫藥大學《選送學生出國研修辦法》第四條與《教育部學海飛颺及學海惜珠甄選簡章》規定：須於中國醫就讀滿一學年以上，歷年學業總平均達 80 分（GPA 3.0／A-）以上或名列全班前 20%（學海飛颺須名列全班前 50%），且前一學期操行成績達 80 分以上。請檢附含 GPA 與排名百分比之歷年成績單正本。"
        if field["id"] == "language_test":
            field["options"] = ["TOEFL iBT（中國醫基準 57+／學海飛颺及歐美雙聯 79–90+）", "TOEFL ITP（中國醫基準 500+）", "IELTS 學術組（中國醫基準 4.0+／學海飛颺 5.5–6.0+／QUB 雙聯 6.5+）", "TOEIC 聽讀測驗（中國醫基準 550+／校內獎補助 B2=785+）", "GEPT 全民英檢（中級複試 B1／中高級複試 B2 以上）", "JLPT 日語能力試驗（東京科學大學／京都／東北／北海道／長崎／日本藥科／新瀉醫療福祉 N2–N3+）", "TOPIK 韓語能力測驗（首爾大學／延世／高麗／成均館／慶熙／漢陽／中央／釜山 2–4 級或英語檢定）", "大陸與港澳姊妹校（免外語檢定；依各專案簡章辦理，大陸醫事學歷不予採認考照）"]
            field["help_text"] = "依中國醫藥大學《選送學生出國研修辦法》第四條與《獎勵學生出國研習及開拓國際視野辦法》規定：申請非華語區盟校交換、雙聯或學海計畫須檢附兩年內有效外語能力證明（校內基準 TOEFL iBT 57 / ITP 500、IELTS 4.0、TOEIC 550 或 GEPT 中級複試；雙聯學位與歐美名校須達 IELTS 6.0–6.5 或 TOEFL iBT 79–90+）。"
    payload.update(
        description=descriptions[template.id],
        source_url="https://cmucia.cmu.edu.tw/s_exchange.html",
        source_checked_at=CMU_SOURCE_CHECKED_AT,
        official_layout=False,
        official_form_number="出國交換／雙聯學位／學海計畫申請表" if template.id == "exchange-application-data" else ("出國研修讀書計畫書與自傳" if template.id == "study-plan" else None),
        official_file_name=None,
        official_download_url="https://cmucia.cmu.edu.tw/doc/exchange/exchange_attach.odt",
        default_copies=1,
        signatures=["申請學生親筆簽名", "家長或監護人親筆簽章", "導師或指導教授簽章", "所屬系所主管簽章", "所屬學院院長簽章"] if template.id == "exchange-application-data" else [],
        stamps=["所屬系所辦公室核章", "所屬學院辦公室核章"] if template.id == "exchange-application-data" else [],
        stage={"predeparture-notice": "錄取後辦理選課預審、盟校提名及學海或校內出國研習獎補助簽約", "return-report": "返國 14 日內上傳學海成果報告並於 1 個月內繳交交換／實習成果報告與核銷單據", "credit-transfer": "返國後持盟校正式成績單與課程大綱辦理境外學分採認"}.get(template.id, "備齊申請表與附件（經家長、導師／指導教授、系所主管及院長簽章）於截止日前送交水湳校區卓越大樓國際事務處"),
        version="115準備工具-2026-10-21.1",
        destinations=["中國醫藥大學所屬系所與學院辦公室（初審推薦）", "中國醫藥大學國際事務處（臺中市北屯區經貿路一段100號水湳校區卓越大樓）"],
        conditional_note="此為個人準備工具；中國醫藥大學教育部學海四項計畫（每年 12 月至翌年 2 月收件）、跨國雙聯學位（7 校 11 學程）與校級交換／臨床見實習甄選須先經系所與學院核章，出國期間須維持中國醫藥大學在學註冊，且修讀雙聯學位者於兩校修業時間合計須達學士班至少 32 個月、碩士班至少 12 個月、博士班至少 24 個月。",
    )
    return ApplicationDocumentTemplate.model_validate(payload)


def _kmu_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    descriptions = {
        "exchange-application-data": "整理高雄醫學大學選送學生出國研修、海外見實習暨教育部學海四項計畫（學海飛颺／惜珠／築夢／新南向築夢）、校內《學生國際移動力獎助金辦法》與各學院交換／雙聯學位（如杜肯大學藥學雙聯）甄選應繳資料：1. 國際事務處／各學院國際交換生或學海計畫申請表（須經導師或指導教授、所屬系所主管及學院院長初審核章；醫學院另須填具選填志願表與資料繳交檢核表）、2. 中英文歷年成績單正本（含學業總平均、GPA 與班級排名；依《選送學生出國研修辦法》第三條，須於高醫大就讀一學期以上且歷年學業總平均達 70 分［GPA 2.44］或班級排名前 50%，操行成績平均達 80 分以上且無懲處紀錄；申請學海飛颺者須達班排前 50% 或 GPA 3.0 以上，醫學院交換甄選佔總成績 40%）、3. 有效外語能力檢定證明影本（英語組須具 TOEFL iBT 69 / IELTS 6.0 / TOEIC 650 / 全民英檢中高級初試以上，日語組須具 JLPT N4 以上；醫學院日語組加分採計 N1–N5，歐美名校如賓州大學／哈佛／牛津／UCLA／杜肯雙聯須達 TOEFL iBT 80–100 或 IELTS 6.5–7.0）、4. 中英文自傳、個人履歷表（CV）與出國研修讀書／見實習計畫書（含申請動機、擬於目標姊妹校修習之專業領域課程或附設醫院海外臨床見實習／實驗室研究規劃）、5. 師長推薦信與家長同意書；經各系所與學院初審推薦排序後，於截止日前送交勵學大樓 4 樓國際事務處。",
        "study-plan": "撰寫高雄醫學大學出國交換、海外臨床見實習（醫學系 Clerkship、牙醫系、藥學系 APPE、護理系、物理治療、職能治療、呼吸治療、醫技、醫社、心理等）、海外實驗室研究或跨國雙聯學位（如美國杜肯大學 Duquesne University 藥學雙聯）必繳之《出國研修讀書／實習計畫書》與《中英文個人自傳／CV》。請具體說明赴外動機、擬於目標姊妹校修習之專業課程或臨床見實習科別／實驗室研究內容、外語能力準備，以及返國後學分抵免（依《高雄醫學大學學生出國期間有關學業及學籍處理要點》與《辦理跨國雙聯學制實施辦法》，兩校修業時間合計須達學士班至少 32 個月、碩士班至少 12 個月、博士班至少 24 個月，且於兩校修習學分數合計須超過畢業應修總學分數三分之一）與醫藥健康專業職涯規劃。",
        "course-preapproval": "辦理赴境外姊妹校修讀課程、跨國雙聯學位或海外臨床見實習之選課預審與教務核備（依《高雄醫學大學學生出國期間有關學業及學籍處理要點》與《辦理跨國雙聯學制實施辦法》規定，出國前須由所屬系所及教務處確認擬修習科目或臨床見實習學分與返國抵免對照；出國研修期間必須維持高雄醫學大學在學註冊，休學期間修習之學分不予採認；大陸地區醫事人員高等學校學歷依教育部規定不予採認醫事國考資格）。",
        "predeparture-notice": "於國際事務處或各學院公告錄取及獎學金核定名單後，配合國際事務處完成國外姊妹校提名（Nomination）、免疫接種與健康檢查證明（Immunization Record，歐美日醫牙藥護臨床見實習必備）及入學／見實習許可（Offer / Invitation Letter）取得；出國前須簽署《教育部學海計畫行政契約書》或《高醫大國際移動力獎助金切結書》、完成役男緩徵出境申請、購買涵蓋境外全期之海外醫療、意外及臨床實習責任保險（Malpractice Insurance），並確認已完成高雄醫學大學當學期註冊。",
        "return-report": "境外交換或見實習期滿返國後，教育部學海計畫受獎生須於返國 14 日內登入教育部學海計畫資訊網填報問卷並上傳 1,000–2,000 字中／英文成果報告書（含研修與臨床見實習照片 4 張以上），並於返國後 1 個月內檢附來回電子機票收據、登機證正本、護照出入境章影本、姊妹校正式成績單（或臨床見實習評估表／結業證書）及出國研修成果報告（提供國際事務處刊登於《學生國際交流經驗分享》專區），向國際事務處辦理獎補助款核銷結案及參加國際移動力成果分享會。",
        "credit-transfer": "境外交換或見實習期滿返國後持國外姊妹校核發之正式成績單正本（或臨床見實習評估表／修業完成證明）與課程大綱（Syllabus），依《高雄醫學大學學生出國期間有關學業及學籍處理要點》、《辦理跨國雙聯學制實施辦法》及《學生抵免學分辦法》向所屬系（所）、學院及教務處註冊課務組申請境外修習科目與實習學分採認。",
    }
    if template.id not in descriptions:
        return None
    def adapt(value):
        if isinstance(value, str):
            return value.replace("長庚大學", "高雄醫學大學").replace("長庚", "高醫大")
        if isinstance(value, list):
            return [adapt(x) for x in value]
        if isinstance(value, dict):
            return {k: adapt(v) for k, v in value.items()}
        return value
    payload = adapt(template.model_dump(mode="json"))
    for field in payload["fields"]:
        if field["id"] == "class_rank_percent":
            field["help_text"] = "高雄醫學大學《選送學生出國研修辦法》第三條與《教育部學海計畫甄選簡章》規定：須於高醫大就讀一學期以上，歷年學業總平均達 70 分（GPA 2.44）或班級排名前 50%（申請教育部學海飛颺者須達班級排名前 50% 或 GPA 3.0 以上），且操行成績平均達 80 分以上、在學期間無懲處紀錄。請檢附含 GPA 與班級排名百分比之中英文歷年成績單正本。"
        if field["id"] == "language_test":
            field["options"] = ["TOEFL iBT（高醫大英語組基準 69+／歐美臨床見實習及雙聯 79–100+）", "IELTS 學術組（高醫大英語組基準 6.0+／歐美名校及雙聯 6.5–7.0+）", "TOEIC 聽讀測驗（高醫大英語組基準 650+／校內獎助 CEFR B2=785+）", "GEPT 全民英檢（中高級初試以上）", "JLPT 日語能力試驗（高醫大日語組基準 N4+；醫學院加分採計 N1–N5；東大／東北／慶應／長崎／昭和 N2–N3+）", "其他歐洲／東南亞外語檢定（依學海新南向築夢或姊妹校規定）", "大陸與香港姊妹校（香港大學／香港中文大學須英語證明；大陸姊妹校免外語檢定，大陸醫事學歷不予採認考照）"]
            field["help_text"] = "依高雄醫學大學《選送學生出國研修辦法》、《學生國際移動力獎助金辦法》與各學院交換甄選簡章規定：申請英語組須具 TOEFL iBT 69、IELTS 6.0、TOEIC 650 或全民英檢中高級初試以上，申請日語組須具 JLPT N4 以上（醫學院日語組加分採計 N1–N5，部分日本姊妹校要求 N2–N3）。"
    payload.update(
        description=descriptions[template.id],
        source_url="https://ciae2.kmu.edu.tw/index.php/zh-tw",
        source_checked_at=KMU_SOURCE_CHECKED_AT,
        official_layout=False,
        official_form_number="出國交換／海外見實習／學海計畫申請表" if template.id == "exchange-application-data" else ("出國研修讀書／實習計畫書與自傳" if template.id == "study-plan" else None),
        official_file_name=None,
        official_download_url="https://ciae2.kmu.edu.tw/index.php/zh-tw",
        default_copies=1,
        signatures=["申請學生親筆簽名", "家長或監護人親筆簽章", "導師或指導教授簽章", "所屬系所主管簽章", "所屬學院院長簽章"] if template.id == "exchange-application-data" else [],
        stamps=["所屬系所辦公室核章", "所屬學院辦公室核章"] if template.id == "exchange-application-data" else [],
        stage={"predeparture-notice": "錄取後辦理選課預審、姊妹校提名、免疫體檢與責任保險及學海或校內獎助簽約", "return-report": "返國 14 日內上傳學海成果報告並於 1 個月內繳交交換／見實習成果報告與核銷單據", "credit-transfer": "返國後持姊妹校正式成績單或見實習評估表辦理境外學分採認"}.get(template.id, "備齊申請表與附件（經家長、導師／指導教授、系所主管及院長簽章）於截止日前送交所屬學院及勵學大樓 4 樓國際事務處"),
        version="115準備工具-2026-10-28.1",
        destinations=["高雄醫學大學所屬系所與學院辦公室（初審推薦）", "高雄醫學大學國際事務處（高雄市三民區十全一路100號勵學大樓4樓）"],
        conditional_note="此為個人準備工具；高雄醫學大學教育部學海四項計畫（每年 12 月至翌年 2 月收件）、校內《學生國際移動力獎助金辦法》、各學院海外交換與臨床見實習（如醫學院每年 9–10 月甄選）及跨國雙聯學位須先經系所與學院核章，出國期間須維持高醫大在學註冊，且修讀雙聯學位者於兩校修業時間合計須達學士班至少 32 個月、碩士班至少 12 個月、博士班至少 24 個月。",
    )
    return ApplicationDocumentTemplate.model_validate(payload)


def _mcu_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    descriptions = {
        "exchange-application-data": "整理銘傳大學選送學生出國研修（交換生／跨國雙聯學位）、大陸知名高校（985／211／省部共建）交換暨教育部學海計畫（學海飛颺／惜珠）及校內《甄選交換生獎助辦法》應繳資料：1. 出國研習線上申請表（於國教處線上表單完成填報後列印紙本，須經家長或監護人簽章同意，並送交系所主任核章推薦；每人最多可選填 5 所交換志願學校）、2. 中英文歷年成績單正本（含學業總平均、GPA 與班級排名；依《銘傳大學辦理學生出國研修實施細則》第三條，須於銘傳就讀滿一學期以上且歷年學業總平均達 70 分以上、操行成績平均達 80 分以上且無小過以上處分；申請教育部學海飛颺者須達歷年學業總平均 80 分以上或班排前 20%）、3. 兩年內有效之外語能力檢定證明影本（英語組基準為 TOEFL iBT 61 / IELTS 5.5 / TOEIC 550，歐美名校及雙聯學位須達 TOEFL iBT 79–80 / IELTS 6.0–6.5；日語組基準為 JLPT N2–N3；韓語組基準為 TOPIK 2–3 級或英語檢定；大陸高校交換免附外語檢定）、4. 中英文自傳與出國讀書計畫書（含申請動機、擬於目標姊妹校修習之專業領域課程及返國學分抵免與職涯規劃）、5. 師長推薦信與家長同意書；於截止日（秋季班 3 月中旬、春季班 9 月下旬）前送交台北校區 B 棟 2 樓或桃園校區 Q 棟 1 樓國際教育交流處。",
        "study-plan": "撰寫銘傳大學出國交換（歐美亞澳 65 所當期開放交換校及 42 所大陸 985／211 高校）與跨國雙聯學位（美國賽基諾州立大學／北阿拉巴馬大學／德州大學聖安東尼奧分校／紐約市立大學約翰杰刑事司法學院／林肯紀念大學、英國西英格蘭大學／諾桑比亞大學／艾塞克斯大學／巴斯思巴大學、日本產業能率大學等 10 校 14 學程）必繳之《出國讀書計畫書》與《中英文個人自傳》。請具體說明赴外動機、擬於目標姊妹校修習之專業課程、外語能力準備，以及返國後學分抵免（依《銘傳大學辦理學生出國研修實施細則》規定，出國期間須維持銘傳在學註冊，每學期至少修習相當於銘傳 6 學分或 2 門以上課程；深圳大學學分不得抵免）與國際職涯規劃。",
        "course-preapproval": "辦理赴境外姊妹校修讀交換課程或跨國雙聯學位之選課預審與教務核備（依《銘傳大學辦理學生出國研修實施細則》與《與境外大學校院辦理跨國雙聯學制實施辦法》規定，出國前須由所屬系所及教務處確認擬修習科目與返國學分抵免對照；出國研修期間必須辦理銘傳大學註冊並繳交全額學雜費［雙聯學位依兩校協議繳交］，且每學期至少應修習相當於銘傳 6 學分或 2 門以上課程；注意大陸地區深圳大學非教育部認可名冊，所修學分不得抵免銘傳畢業學分）。",
        "predeparture-notice": "於國際教育交流處公告甄選錄取名單（面試佔 50%、在校成績 30%、書審讀書計畫 20%）後，依限繳交《錄取資格確認書》、《家長同意書》及保證金，配合國際教育交流處或大陸教育交流處完成姊妹校官方提名（Nomination）與入學許可（Offer Letter）取得；出國前須參加行前說明會、簽署《教育部學海計畫行政契約書》或《銘傳大學交換生獎助切結書》、完成役男緩徵出境申請、購買涵蓋境外全期之海外醫療及意外保險，並確認已完成銘傳當學期註冊繳費。",
        "return-report": "境外交換或雙聯研修期滿返國後 2 週至 1 個月內，須向國際教育交流處（或大陸教育交流處）繳交 1,500–2,000 字以上之《出國研習／交換學生心得報告書》電子檔與紙本（含研修與生活照片 4–6 張以上，提供刊登於國教處《心得分享》專區），教育部學海受獎生另須於返國 14 日內登入學海計畫資訊網上傳成果報告與問卷，並檢附來回電子機票收據、登機證正本、護照出入境章影本及姊妹校正式成績單辦理獎助學金核銷與保證金退還。",
        "credit-transfer": "境外交換或雙聯研修期滿返國後持國外姊妹校核發之正式成績單正本與課程大綱（Syllabus），依《銘傳大學辦理學生出國研修實施細則》、《與境外大學校院辦理跨國雙聯學制實施辦法》及《學生抵免學分辦法》向所屬系（所）、學院及教務處註冊組申請境外修習科目學分採認（深圳大學學分不予採認）。",
    }
    if template.id not in descriptions:
        return None
    def adapt(value):
        if isinstance(value, str):
            return value.replace("長庚大學", "銘傳大學").replace("長庚", "銘傳")
        if isinstance(value, list):
            return [adapt(x) for x in value]
        if isinstance(value, dict):
            return {k: adapt(v) for k, v in value.items()}
        return value
    payload = adapt(template.model_dump(mode="json"))
    for field in payload["fields"]:
        if field["id"] == "class_rank_percent":
            field["help_text"] = "銘傳大學《辦理學生出國研修實施細則》第三條與《教育部學海飛颺甄選簡章》規定：須於銘傳就讀滿一學期以上，歷年學業總平均達 70 分以上、操行成績平均達 80 分以上且無小過以上處分（在校學業成績佔甄選總分 30%）；申請教育部學海飛颺獎學金者，歷年學業總平均須達 80 分以上或班級排名前 20%。請檢附含 GPA 與班級排名之中英文歷年成績單正本。"
        if field["id"] == "language_test":
            field["options"] = ["TOEFL iBT（銘傳英語組基準 61+／歐美名校及雙聯 79–80+）", "IELTS 學術組（銘傳英語組基準 5.5+／歐美名校及雙聯 6.0–6.5+）", "TOEIC 聽讀測驗（銘傳英語組基準 550+／部分歐亞姊妹校採計 600–785+）", "JLPT 日語能力試驗（銘傳日語組基準 N2–N3+；早稻田／明治／法政／中央／金澤／產能大雙聯 N1–N2+）", "TOPIK 韓語能力測驗（韓國姊妹校 2–4 級或英語檢定證明）", "歐洲語言檢定（德語 Goethe B1–B2／法語 DELF B1–B2，或修讀英語授課學程）", "大陸地區 985／211 高校交換（免外語檢定，依在學成績、讀書計畫與面試甄選）"]
            field["help_text"] = "依銘傳大學《辦理學生出國研修實施細則》與《2027-2028 交換學校資料庫一覽表》規定：申請英語組須具 TOEFL iBT 61、IELTS 5.5 或 TOEIC 550 以上（歐美名校與雙聯學位多要求 TOEFL iBT 79–80 或 IELTS 6.0–6.5），日語組須具 JLPT N2 或 N3 以上，韓語組須具 TOPIK 2–3 級或英語檢定。"
    payload.update(
        description=descriptions[template.id],
        source_url="https://iee.mcu.edu.tw/%e7%94%b3%e8%ab%8b%e8%a6%81%e9%bb%9e/",
        source_checked_at=MCU_SOURCE_CHECKED_AT,
        official_layout=False,
        official_form_number="出國研習交換生／雙聯學位／學海計畫申請表" if template.id == "exchange-application-data" else ("出國讀書計畫書與中英文自傳" if template.id == "study-plan" else None),
        official_file_name=None,
        official_download_url="https://iee.mcu.edu.tw/wp-content/uploads/sites/11/2026/02/MCU_Exchange_University_Database_Template_2027-2028.pdf",
        default_copies=1,
        signatures=["申請學生親筆簽名", "家長或監護人親筆簽章", "導師或指導教授簽章", "所屬系所主管簽章"] if template.id == "exchange-application-data" else [],
        stamps=["所屬系所辦公室核章"] if template.id == "exchange-application-data" else [],
        stage={"predeparture-notice": "錄取後繳交確認書、家長同意書與保證金並辦理姊妹校提名及學海／校內獎助簽約", "return-report": "返國 14 日內上傳學海報告並於 1 個月內繳交交換心得報告與核銷單據", "credit-transfer": "返國後持姊妹校正式成績單與課程大綱辦理境外學分採認"}.get(template.id, "完成線上申請並列印紙本（經家長及系所主管簽章）於截止日前送交台北校區 B 棟 2 樓或桃園校區 Q 棟 1 樓國際教育交流處"),
        version="116準備工具-2026-10-21.1",
        destinations=["銘傳大學國際教育交流處（台北校區 B 棟 2 樓／桃園校區 Q 棟 1 樓）", "銘傳大學大陸教育交流處（台北校區 H 棟 3 樓，大陸高校交換）"],
        conditional_note="此為個人準備工具；銘傳大學出國交換（秋季班每年 3 月中旬截止、春季班每年 9 月下旬截止，最多選填 5 所志願）、大陸知名高校交換與跨國雙聯學位須先完成線上填報並列印紙本經家長及系所主管簽章，出國期間須維持銘傳在學註冊且每學期至少修讀相當於銘傳 6 學分或 2 門以上課程（深圳大學學分不得抵免）。",
    )
    return ApplicationDocumentTemplate.model_validate(payload)


def _ntub_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    descriptions = {
        "exchange-application-data": "整理國立臺北商業大學海外及大陸地區交換學生、跨國雙聯學位暨教育部學海飛颺／惜珠與《王春滿清寒短期研修交流助學金》甄選應繳資料：1. 線上申請表與紙本核章表（於北商大出國交換學生申請系統 https://exchange.ntub.edu.tw/ 完成線上填報後列印紙本親筆簽名，送交系科所初審）、2. 家長或監護人切結書正本（2026 年版）、3. 出國進修計畫書（2026 年版，含自傳與讀書計畫，格式以 1,000–1,500 字為原則；依《學生申請交換生及雙聯學位生作業要點》p/406-1006-91803,r134.php 附件 PDF 第七點，需繳交外語證明之海外國家按「外語成績 60%＋在校歷年學業平均成績 20%＋在校歷年平均班級名次百分比 20%」計分，免附外語證明之大陸地區按「在校歷年學業平均成績 50%＋在校歷年平均班級名次百分比 50%」計分）、4. 歷年成績單正本（含學業總平均與歷年平均班級名次百分比；申請人須為研究所、二技一年級第二學期以上、四技二年級以上或五專四年級以上在學學生，且符合「在校學業總平均 80 分以上且前一學年每學期操行成績均為 A 以上」或「歷年平均班級名次前 70% 且前一學年每學期操行成績均為 A 以上」；申請學海飛颺須達總平均 80 分或班排前 40% 以內）、5. 2 年內有效外語能力檢定證明正本（英語組姊妹校只接受 TOEFL iBT 或 IELTS，不接受多益 TOEIC！日語組要求 JLPT N2 以上，韓語組要求 TOPIK 3 級以上；大陸地區姊妹校免附外語檢定）；將平台申請結果列印親筆簽名後，連同歷年成績單及正本外語成績單繳交至所屬系所。",
        "study-plan": "撰寫國立臺北商業大學交換生及雙聯學位甄選必繳之《出國進修計畫書》（2026 年版官方表格，含個人自傳與讀書計畫，1,000–1,500 字）。請具體說明赴外動機、擬於志願姊妹校修習之專業領域課程（出國期間每學期至少應修習與就讀系所相關之 2 門科目或 6 學分以上）、外語能力準備，以及返國後學分抵免與國際商管／創新設計職涯銜接規劃。",
        "course-preapproval": "辦理赴境外姊妹校修讀交換課程或跨國雙聯學位之選課預審與教務核備（依《國立臺北商業大學學生申請交換生及雙聯學位生作業要點》規定，出國交換期間須維持北商大在學註冊並繳交全額學雜費，每學期至少應選修與就讀系所相關之 2 門科目或 6 學分以上；研究所學生交換期間以一學期為限）。",
        "predeparture-notice": "於國際事務處公告甄選錄取名單（依總積分高低及志願序分發）後，依限繳交《錄取同意書》（2026 年版）及《赴海外交換及雙聯研修計畫行政契約書》（一式三份，領取獎助學金者適用），配合國際事務處完成姊妹校官方提名（Nomination）與外校入學申請；出國前須參加行前說明會、完成役男緩徵出境申請、購買涵蓋境外全期之海外醫療及意外保險，並確認已完成北商大當學期註冊繳費。",
        "return-report": "境外交換或雙聯研修期滿返國後 1 個月內，須填寫《返校報到單》並繳交至少 1,000 字以上之《交換生心得報告》（含至少 4 張照片，含上課照片 1 張），教育部學海計畫受獎生另須於返國 14 日內上傳成果報告至教育部學海計畫資訊網，並檢附來回電子機票收據、登機證正本、護照出入境紀錄及姊妹校正式成績單向國際事務處辦理獎助學金核銷與返校銷假。",
        "credit-transfer": "境外交換或雙聯研修期滿返國後持國外姊妹校核發之正式成績單正本與課程大綱（Syllabus），依《國立臺北商業大學學生申請交換生及雙聯學位生作業要點》及《學生抵免學分辦法》向所屬系（所）、學院及教務處申請境外修習科目學分採認。",
    }
    if template.id not in descriptions:
        return None
    def adapt(value):
        if isinstance(value, str):
            return value.replace("長庚大學", "國立臺北商業大學").replace("長庚", "北商大")
        if isinstance(value, list):
            return [adapt(x) for x in value]
        if isinstance(value, dict):
            return {k: adapt(v) for k, v in value.items()}
        return value
    payload = adapt(template.model_dump(mode="json"))
    for field in payload["fields"]:
        if field["id"] == "class_rank_percent":
            field["help_text"] = "北商大〈姊妹校交換作業辦法〉與《學生申請交換生及雙聯學位生作業要點》規定：申請人須為研究所、二技一年級第二學期以上、四技二年級以上或五專四年級以上在學學生，且符合「在校學業總平均 80 分以上且前一學年每學期操行成績均為 A 以上」或「歷年平均班級名次前 70% 且前一學年每學期操行成績均為 A 以上」（海外組甄選總積分：外語成績 60%＋歷年學業平均成績 20%＋歷年平均班級名次百分比 20%；大陸組：歷年學業平均成績 50%＋歷年平均班級名次百分比 50%）；申請教育部《學海飛颺》獎助學金者，須達總平均 80 分以上或歷年平均班級名次前 40% 以內。請檢附含總平均與歷年平均班級名次百分比之中文歷年成績單正本。"
        if field["id"] == "language_test":
            field["options"] = ["TOEFL iBT（英語組只接受托福或雅思！韓國天主教 65+／匹茲堡州立 68+／一般英語組 73+／荷德法澳雙聯 80+／捷克理工 87+／舊金山州立 88+／萊茵瓦爾碩士 100+）", "IELTS 學術組（英語組只接受托福或雅思！一般英語組 5.5+／匹茲堡州立及荷德法澳雙聯 6.0+／捷克理工及舊金山州立與萊茵瓦爾碩士 6.5+）", "JLPT 日語能力試驗（日語組千葉商大／小樽商大／人間環境／亞細亞 N2+；新潟大學須同時具備 N2 及 TOEFL 73 / IELTS 5.5）", "TOPIK 韓語能力測驗（韓語組慶北／光雲／全北／東亞 3 級以上，或以 TOEFL 73 / IELTS 5.5 申請英語組）", "大陸地區姊妹校（免附外語檢定證明；按歷年學業平均成績 50%＋歷年平均班級名次百分比 50% 計分）"]
            field["help_text"] = "依北商大〈姊妹校交換作業辦法〉明文規定：2 年內有效外語成績單，英文「只」接受托福（TOEFL iBT）或雅思（IELTS）成績，不接受多益（TOEIC）成績！外語成績佔海外組甄選總積分 60%（依《外語成績積分對照表》換算，最高 60 分；大陸地區免附外語檢定，按學業平均 50%＋班排 50% 計分）。"
    payload.update(
        description=descriptions[template.id],
        source_url="https://oia.ntub.edu.tw/p/405-1006-57507,c3152.php?Lang=zh-tw",
        source_checked_at=NTUB_SOURCE_CHECKED_AT,
        official_layout=False,
        official_form_number="出國進修計畫書（2026年版）、家長切結書與錄取同意書" if template.id == "exchange-application-data" else ("出國進修計畫書（2026年版，含自傳與讀書計畫）" if template.id == "study-plan" else None),
        official_file_name=None,
        official_download_url="https://oia.ntub.edu.tw/p/412-1006-3153.php?Lang=zh-tw",
        default_copies=1,
        signatures=["申請學生親筆簽名", "家長或監護人親筆簽章", "導師或指導教授簽章", "所屬系所主管簽章"] if template.id == "exchange-application-data" else [],
        stamps=["所屬系所辦公室核章"] if template.id == "exchange-application-data" else [],
        stage={"predeparture-notice": "錄取後繳交錄取同意書與行政契約書（一式三份）並辦理姊妹校提名", "return-report": "返國後 1 個月內繳交返校報到單與至少 1,000 字以上交換生心得報告（含至少 4 張照片）並完成核銷", "credit-transfer": "返國後持姊妹校正式成績單與課程大綱辦理境外學分採認"}.get(template.id, "於出國交換學生申請系統（exchange.ntub.edu.tw）完成線上申請並將簽名紙本連同歷年成績單與正本外語成績單繳交至所屬系所"),
        version="116準備工具-2026-10-28.1",
        destinations=["國立臺北商業大學各所屬系所（初審收件）", "國立臺北商業大學國際事務處（複審）"],
        conditional_note="此為個人準備工具；北商大海外及大陸地區交換學生甄選每年分兩梯次（每年 11/1–11/30［逢例假日順延一天，於申請之隔年度出國交換一學期或一學年］及 5/1–5/31［就 11 月申請梯次交換後剩餘名額，開放二技及研究所優先申請，於申請之隔年度第 2 學期出國交換一學期］），須先於出國交換學生申請系統（https://exchange.ntub.edu.tw/）完成線上填報，並將簽名紙本、2026 年版出國進修計畫書、家長切結書、歷年成績單正本（含班排百分比）及 2 年內有效外語檢定證明正本（英語組僅採認托福或雅思，不接受多益）繳交至所屬系所。",
    )
    return ApplicationDocumentTemplate.model_validate(payload)


def _ncnu_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    descriptions = {
        "exchange-application-data": "整理國立暨南國際大學出國交換學生、跨國雙聯學位暨教育部學海飛颺／惜珠與校內《學生出國研修獎助學金》甄選應繳資料：1. 出國交換學生申請表（經導師／指導教授及所屬系所主管核章，至多選填 3 至 5 所志願姊妹校）、2. 家長或監護人同意書正本、3. 中／英文研修計畫書與自傳（Study Plan & Autobiography，約 1,000–2,000 字；校內甄選依書面審查 50%［歷年學業成績、語言檢定、研修計畫］與口試 50% 評定）、4. 中／英文歷年成績單正本（含學業總平均或 GPA 及歷年班級名次百分比；校內交換基準為歷年平均 70 分以上或班排前 50% 且操行 80 分以上，申請教育部《學海飛颺》須達班排前 30% 或 GPA 3.0 以上）、5. 有效外語能力檢定證明影本（英語組基準為 TOEFL iBT 79／IELTS 6.0／TOEIC 750／全民英檢中高級，日語組為 JLPT N2–N3，韓語組為 TOPIK 2–4 級；大陸地區姊妹校免附外語檢定）、6. 教授推薦信及在學證明；於收件截止日前將紙本與電子檔送交行政大樓 3 樓國際及兩岸事務處國際合作組。",
        "study-plan": "撰寫國立暨南國際大學出國交換生、雙聯學位及學海飛颺甄選必繳之《中／英文出國研修計畫書與自傳》（Study Plan & Autobiography，約 1,000–2,000 字；書面審查佔甄選總分 50%）。請具體說明赴外動機、擬於志願姊妹校修習之專業領域課程（依《選送學生出國研修辦法》規定，出國交換期間須維持暨大在學註冊，每學期於姊妹校至少應修習相當於暨大 6 學分或 2 門以上課程）、外語能力準備，以及返國後學分抵免與職涯發展規劃。",
        "course-preapproval": "辦理赴境外姊妹校修讀交換課程或跨國雙聯學位之選課預審與教務核備（依《國立暨南國際大學選送學生出國研修辦法》規定，出國交換期間須完成暨大註冊並繳交全額學雜費，每學期至少應選修相當於暨大 6 學分或 2 門以上專業課程；雙聯學位生須依兩校雙聯協議修畢規定學分）。",
        "predeparture-notice": "於國際及兩岸事務處公告甄選錄取名單（書面審查 50%＋口試 50%）後，依限繳交《錄取資格確認書》及《家長同意書》，配合國際合作組完成姊妹校官方提名（Nomination）與外校入學申請；出國前須參加行前說明會、完成役男緩徵出境申請、簽署《教育部學海計畫或校內出國研修獎助行政契約書》、購買涵蓋境外全期之海外醫療及意外保險，並確認已完成暨大當學期註冊繳費。",
        "return-report": "境外交換或雙聯研修期滿返國後 1 個月內，須向國際及兩岸事務處繳交 1,500–2,000 字以上之《出國交換／研修心得報告書》（含研修與生活照片 4 張以上，供刊登於國際處《心得分享》專區），教育部學海計畫受獎生另須於返國 14 日內上傳成果報告至教育部學海計畫資訊網，並檢附來回電子機票收據、登機證正本、護照出入境紀錄及姊妹校正式成績單辦理獎助學金核銷與返校程序。",
        "credit-transfer": "境外交換或雙聯研修期滿返國後持國外姊妹校核發之正式成績單正本與課程大綱（Syllabus），依《國立暨南國際大學選送學生出國研修辦法》及《學生抵免學分辦法》向所屬系（所）、學院及教務處申請境外修習科目學分採認。",
    }
    if template.id not in descriptions:
        return None
    def adapt(value):
        if isinstance(value, str):
            return value.replace("長庚大學", "國立暨南國際大學").replace("長庚", "暨大")
        if isinstance(value, list):
            return [adapt(x) for x in value]
        if isinstance(value, dict):
            return {k: adapt(v) for k, v in value.items()}
        return value
    payload = adapt(template.model_dump(mode="json"))
    for field in payload["fields"]:
        if field["id"] == "class_rank_percent":
            field["help_text"] = "暨大《選送學生出國研修辦法》規定：歷年學業成績總平均須達 70 分以上（或歷年班級排名百分比前 50% 以內），且操行成績平均達 80 分以上；申請教育部《學海飛颺》獎助學金者，須達歷年學業成績班排前 30% 以內（或 GPA 3.0 以上）。請檢附含總平均與歷年班級名次百分比之中／英文歷年成績單正本。"
        if field["id"] == "language_test":
            field["options"] = ["TOEFL iBT（英語組一般基準 79+／部分姊妹校 61–72+／歐美雙聯 80–90+）", "IELTS 學術組（英語組一般基準 6.0+／部分姊妹校 5.5+／歐美雙聯 6.5+）", "TOEIC 多益測驗（校內英語組基準 750+ 或全民英檢中高級，惟須確認目標姊妹校是否接受 TOEIC）", "JLPT 日語能力試驗（日語組專門課程 N2+／日語研修或部分日本姊妹校 N3+）", "TOPIK 韓語能力測驗（韓語組韓國姊妹校 2–4 級以上，或以英語檢定申請英語授課課程）", "大陸地區姊妹校（免附外語檢定證明；以歷年學業成績、研修計畫與口試成績評選）"]
            field["help_text"] = "依暨大《選送學生出國研修辦法》及《115-2 出國交換學生申請簡章》規定：英語組姊妹校一般要求 TOEFL iBT 79、IELTS 6.0、TOEIC 750 或全民英檢中高級以上（實際依各姊妹校門檻為準），日語組要求 JLPT N2 或 N3 以上，韓語組要求 TOPIK 2–4 級以上。"
    payload.update(
        description=descriptions[template.id],
        source_url="https://oia.ncnu.edu.tw/p/412-1017-269.php?Lang=zh-tw",
        source_checked_at=NCNU_SOURCE_CHECKED_AT,
        official_layout=False,
        official_form_number="出國交換學生申請表、家長同意書與錄取確認書" if template.id == "exchange-application-data" else ("中／英文出國研修計畫書與自傳" if template.id == "study-plan" else None),
        official_file_name=None,
        official_download_url="https://oia.ncnu.edu.tw/p/412-1017-273.php?Lang=zh-tw",
        default_copies=1,
        signatures=["申請學生親筆簽名", "家長或監護人親筆簽章", "導師或指導教授簽章", "所屬系所主管簽章"] if template.id == "exchange-application-data" else [],
        stamps=["所屬系所辦公室核章"] if template.id == "exchange-application-data" else [],
        stage={"predeparture-notice": "錄取後繳交錄取確認書與學海／校內獎助行政契約書並辦理姊妹校提名", "return-report": "返國後 1 個月內繳交 1,500–2,000 字以上出國研修心得報告書並完成獎助核銷", "credit-transfer": "返國後持姊妹校正式成績單與課程大綱辦理境外學分採認"}.get(template.id, "備齊核章紙本申請表與必繳附件於截止日前送交行政大樓 3 樓國際及兩岸事務處國際合作組"),
        version="116準備工具-2026-10-27.1",
        destinations=["國立暨南國際大學國際及兩岸事務處國際合作組（行政大樓 3 樓）"],
        conditional_note="此為個人準備工具；暨大出國及赴大陸地區交換學生甄選每年分兩梯次（秋季班約每年 2–3 月、春季班約每年 9–10 月截止），須檢附經家長及系所主管簽章之申請表、中英文歷年成績單正本（含班排）、中英文研修計畫與自傳及有效外語檢定證明送交國際及兩岸事務處。",
    )
    return ApplicationDocumentTemplate.model_validate(payload)


def _ndhu_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    descriptions = {
        "exchange-application-data": "整理國立東華大學國際暨大陸地區出國交換學生、國際移動力先鋒計畫、跨國雙聯學位暨教育部學海飛颺／惜珠與校內《出國交換獎助學金》甄選應繳資料：1. 線上申請表（於出國交換學生申請系統 http://ias.ndhu.edu.tw/intstud/ 選填 2 至 6 個志願，首次申請者優先分發）、2. 家長或監護人同意書正本、3. 讀書計畫（Study Plan，佔書審總分 35%）與任務企劃書（Mission Proposal，佔書審總分 35%，規劃於交換期間推廣臺灣與東華或執行跨文化任務）、4. 中／英文歷年成績單正本（含 GPA，前一學期或歷年平均 GPA 須達 2.5／4.5 以上；申請校內出國交換獎助學金須歷年 GPA 達 3.3 以上）、5. 有效外語能力檢定證明影本（與學業成績合計佔書審 20%；英語組基準為 TOEFL iBT 61–80／IELTS 5.5–6.5／TOEIC 650–785，日語組為 JLPT N1–N3，韓語組為 TOPIK 2–4 級；大陸地區姊妹校免附外語檢定）、6. 其他優秀表現佐證資料（佔書審 10%；具國際處接待義工證明加總分 1 分、修畢全球研究與國際事務學程加總分 1 分）。",
        "study-plan": "撰寫國立東華大學出國交換生、先鋒計畫、雙聯學位及出國交換獎助學金甄選必繳之《讀書計畫（Study Plan，佔書審 35%）與任務企劃書（Mission Proposal，佔書審 35%）》（兩項合計佔校內書面審查總分 70%）。讀書計畫請具體說明赴外動機、擬於志願姊妹校修習之課程（依《國際交換學生出國計畫作業辦法》規定，交換期間須維持東華在學註冊，每學期至少修讀 2 門課［含 1 門專業課程、1 門非專業課程］且成績及格）與返國學分抵免規劃；任務企劃書請說明預計於海外交換期間執行之臺灣與東華校園推廣或跨文化專題計畫。",
        "course-preapproval": "辦理赴境外姊妹校修讀交換課程或跨國雙聯學位之選課預審與教務核備（依《國立東華大學國際交換學生出國計畫作業辦法》與《學生出國選修課程實施辦法》規定，出國交換期間須完成東華註冊並繳交全額學雜費，每學期至少修讀 2 門課［含 1 門專業課程、1 門非專業課程］且及格；歐洲 ECTS 學分 × 1/2、英國 CATS 學分 × 1/4、美日陸約 1:1 折算）。",
        "predeparture-notice": "於國際事務處公告甄選錄取名單（2027年第一次甄選於 2026/10/30 12:00 公告）後，依限於 2026/10/27～11/02 完成線上確認並繳交《家長同意書》，配合全球移動組完成姊妹校官方提名（Nomination）與外校入學申請；出國前須參加行前說明會、完成《出國程序單》、簽署《教育部學海計畫或校內出國交換獎助行政契約書》、購買涵蓋境外全期之海外醫療及意外保險（保額至少新臺幣 100 萬元以上），並確認已完成東華當學期註冊繳費。",
        "return-report": "境外交換或雙聯研修期滿返國後 1 個月內（春季班於 3 月 31 日前、秋季班於 10 月 31 日前），須向國際事務處繳交《回國程序單》、姊妹校正式成績單、1,500–2,000 字之《出國交換學生心得報告》（含任務企劃書執行成果與照片 4 張以上）及 5 頁以上簡報或 3–5 分鐘影片，並檢附來回電子機票收據、登機證正本及護照出入境紀錄辦理獎助學金核銷。",
        "credit-transfer": "境外交換或雙聯研修期滿返國後 1 個月內持國外姊妹校核發之正式成績單正本與課程大綱（Syllabus），依《國立東華大學學生出國選修課程實施辦法》（歐洲 2 ECTS 折算 1 學分、英國 4 CATS 折算 1 學分、美日陸約 1:1 折算）向所屬系（所）、學院及教務處申請境外修習科目學分採認。",
    }
    if template.id not in descriptions:
        return None
    def adapt(value):
        if isinstance(value, str):
            return value.replace("長庚大學", "國立東華大學").replace("長庚", "東華")
        if isinstance(value, list):
            return [adapt(x) for x in value]
        if isinstance(value, dict):
            return {k: adapt(v) for k, v in value.items()}
        return value
    payload = adapt(template.model_dump(mode="json"))
    for field in payload["fields"]:
        if field["id"] == "class_rank_percent":
            field["help_text"] = "東華《2027年第一次國際交換學生甄選簡章》與《國際交換學生出國計畫作業辦法》規定：前一學期或歷年平均 GPA 須達 2.5（滿分 4.5，約百分制 70 分）以上；申請校內出國交換獎助學金者，歷年平均 GPA 須達 3.3 以上且具外語檢定證明。請檢附含 GPA 之中／英文歷年成績單正本。"
        if field["id"] == "language_test":
            field["options"] = ["TOEFL iBT（英語組一般基準 61–79+／歐美澳名校與雙聯學位 79–90+）", "IELTS 學術組（英語組一般基準 5.5–6.0+／歐美澳名校與雙聯學位 6.0–6.5+）", "TOEIC 多益測驗（校內英語組與亞洲英語授課學程基準 650–785+）", "JLPT 日語能力試驗（日語組北海道／東北／青山／立教／廣島等 N1–N2+，部分日本姊妹校接受 N3+）", "TOPIK 韓語能力測驗（韓語組中央／韓外大／首爾市立／慶北／全南等 2–4 級以上）", "大陸地區姊妹校（中文授課免附外語檢定證明；若有外語成績仍可納入書審 20% 評分）"]
            field["help_text"] = "依東華《2027年第一次國際交換學生甄選簡章》規定：學業成績與外語能力合計佔校內書面審查 20%，申請國際交換及校內獎助學金均須檢附符合志願校門檻之有效外語能力證明（大陸交換免附）。"
    payload.update(
        description=descriptions[template.id],
        source_url="https://oia.ndhu.edu.tw/p/412-1027-21499.php?Lang=zh-tw",
        source_checked_at=NDHU_SOURCE_CHECKED_AT,
        official_layout=False,
        official_form_number="出國交換學生線上申請表（2–6志願）、家長同意書與出返國程序單" if template.id == "exchange-application-data" else ("讀書計畫（35%）與任務企劃書（35%）" if template.id == "study-plan" else None),
        official_file_name=None,
        official_download_url="https://oia.ndhu.edu.tw/p/412-1027-21500.php?Lang=zh-tw",
        default_copies=1,
        signatures=["申請學生親筆簽名", "家長或監護人親筆簽章", "導師或系所主管簽章"] if template.id == "exchange-application-data" else [],
        stamps=["所屬系所辦公室核章"] if template.id == "exchange-application-data" else [],
        stage={"predeparture-notice": "於 2026/10/27～11/02 完成線上錄取確認、簽署行政契約書與辦理出國程序單", "return-report": "返國後 1 個月內（春季班 3/31 前、秋季班 10/31 前）繳交回國程序單、1,500–2,000 字心得報告與簡報／影片", "credit-transfer": "返國後 1 個月內持姊妹校正式成績單與課程大綱辦理境外學分採認"}.get(template.id, "於出國交換申請系統 ias.ndhu.edu.tw 完成線上填報（2–6志願）並上傳書審文件"),
        version="116準備工具-2026-10-28.1",
        destinations=["國立東華大學國際事務處全球移動組（花蓮縣壽豐鄉大學路二段 1 號行政大樓 601 室）"],
        conditional_note="此為個人準備工具；東華出國交換學生甄選每年分兩梯次（第一次於 8–10 月申請次年春季班及秋季班，第二次於 2–3 月申請同年秋季班剩餘名額），須於 http://ias.ndhu.edu.tw/intstud/ 選填 2–6 個志願並上傳讀書計畫（35%）、任務企劃書（35%）、歷年成績單（GPA 2.5+）與外語檢定證明。",
    )
    return ApplicationDocumentTemplate.model_validate(payload)


def _thu_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    descriptions = {
        "exchange-application-data": "整理東海大學赴全球姊妹校交換甄試（分為「全球暨港澳組」與「大陸組」）、美國 13 校跨國雙聯學位暨教育部學海飛颺／惜珠與校內《高教深耕國際移動力活動獎補助》甄選應繳資料：1. 線上申請表與紙本送件檢核表（須經系主任或指導教授簽章；自 2026 年秋季甄試起取消口試，改依書面加權總分排序並參加「現場唱名選填學校」）、2. 家長同意書正本及報名費新臺幣 500 元繳費收據（至總務處出納組繳交，報名後概不退還）、3. 歷年成績單與歷年學期名次證明書正本（全球暨港澳組歷年 GPA 須達 2.5 以上，大陸組歷年 GPA 須達 2.0 以上；甄試成績含歷年學期班排名百分比平均 20%＋歷年學期 GPA 平均 15%）、4. 有效外語能力檢定證明（佔甄試成績 30%，採認 TOEFL ITP 430+／TOEFL iBT 42+／IELTS 5.0+／CEFR B1–C2／JLPT N5–N1／TOPIK 1–6 級；大陸組免附且外語 0%）、5. 學行優良表現佐證資料（佔甄試成績 35%，最多列計 7 項，含培力英檢 BESTEP、EMI 全英授課及格、學業優良獎、社團幹部等）與基本勞作教育完成證明（加總分 5 分）。",
        "study-plan": "撰寫東海大學赴全球姊妹校交換甄試、雙聯學位及教育部學海飛颺／惜珠獎補助必繳之《出國學習計畫書》（約 1,000–2,000 字）。請具體說明赴外動機、擬於志願姊妹校修習之課程規劃（依《學生境外學習辦法》規定，交換期間須維持東海在學學籍並繳交東海全額學雜費，每學期於姊妹校至少須修讀 2 門課或 6 學分以上）、個人學行優良表現（EMI 修課、國際交流經驗或專業競賽成果），以及返國後學分抵免與職涯銜接規劃。",
        "course-preapproval": "辦理赴境外姊妹校修讀交換課程或美國雙聯學位之選課預審與教務核備（依《東海大學學生境外學習辦法》規定，出國交換期間須辦理東海註冊並繳交東海全額學雜費［自費交換生則同時繳交東海與姊妹校學雜費］，每學期至少修讀 2 門課或 6 學分以上；同一教育階段赴境外研修期限除雙聯學位外合計以一學年為限）。",
        "predeparture-notice": "於國際暨兩岸合作處公告甄試成績排序並完成「現場唱名選填學校」（2027 春季甄試於 2026/10/28 下午 2:00 舉行，本人或代理人須攜帶身分證或學生證正本出席，唱名三次未到視同棄權）後，繳交保證金新臺幣 10,000 元（至出納組繳交，完成交換返國繳交心得報告後無息退還；無故放棄者沒收）、配合國際處辦理姊妹校提名（Nomination）與外校入學申請，並完成行前說明會、役男緩徵出境及海外醫療保險。",
        "return-report": "境外交換或雙聯研修期滿返國後 1 個月內，須向國際暨兩岸合作處繳交 1,000–2,000 字以上之《返國交換學生研修心得報告書》（含研修與生活照片，供刊登於國際處《心得分享》專區）、姊妹校正式成績單及出入境證明，辦理保證金新臺幣 10,000 元無息退還與教育部學海計畫／高教深耕國際移動力獎補助核銷。",
        "credit-transfer": "境外交換或雙聯研修期滿返國後持國外姊妹校核發之正式成績單正本與課程大綱（Syllabus），依《東海大學學生境外學習辦法》及《學生抵免學分辦法》向所屬系（所）、學院及教務處註冊課務組申請境外修習科目學分採認。",
    }
    if template.id not in descriptions:
        return None
    def adapt(value):
        if isinstance(value, str):
            return value.replace("長庚大學", "東海大學").replace("長庚", "東海")
        if isinstance(value, list):
            return [adapt(x) for x in value]
        if isinstance(value, dict):
            return {k: adapt(v) for k, v in value.items()}
        return value
    payload = adapt(template.model_dump(mode="json"))
    for field in payload["fields"]:
        if field["id"] == "class_rank_percent":
            field["help_text"] = "東海《赴全球姊妹校交換甄試簡章》規定：全球暨港澳組歷年學期 GPA 須達 2.5（約 70 分）以上，大陸組歷年學期 GPA 須達 2.0 以上；甄試總分含歷年學期班排名百分比平均 20%＋歷年學期 GPA 平均 15%＋學行優良表現 35%（完成基本勞作教育另加總分 5 分）。請檢附歷年成績單與歷年學期名次證明書正本。"
        if field["id"] == "language_test":
            field["options"] = ["TOEFL iBT（Level A 114+ 30%／Level B 102+ 25%／Level C 95+ 20%／Level D 87+ 18%／Level E 72+ 15%／Level F 42+ 8%）", "IELTS 學術組（Level A 8.5+ 30%／Level B 7.5+ 25%／Level C 7.0+ 20%／Level D 6.5 18%／Level E 6.0 15%／Level F 5.0–5.5 8%）", "TOEFL ITP（Level B 660+ 25%／Level C 627+ 20%／Level D 585+ 18%／Level E 543+ 15%／Level F 460+ 8%／Level G 430+ 4%）", "JLPT 日語能力試驗（N1 滿分 Level A 30%／N1 合格 Level B 25%／N2 Level C 20%／N3 Level E 15%／N4 Level F 8%／N5 Level G 4%）", "TOPIK 韓語能力測驗（6級 Level A 30%／5級 Level B 25%／4級 Level D 18%／3級 Level E 15%／2級 Level F 8%／1級 Level G 4%）", "大陸組姊妹校（免附外語檢定證明；外語能力項目 30% 於大陸組一律不計分）"]
            field["help_text"] = "依東海《赴全球姊妹校交換甄試簡章》外語能力計分表（佔甄試總分 30%，擇最優單一成績採計）：採認 TOEFL ITP、TOEFL iBT、IELTS、CEFR 歐語檢定、JLPT 及 TOPIK（培力英檢 BESTEP 可於學行優良表現加 5 分；一般交換不採計 TOEIC）。"
    payload.update(
        description=descriptions[template.id],
        source_url="https://oir.thu.edu.tw/front/301_ex_overview/302_Out_EX_Prog/302_1_Qualifica?lang=tw",
        source_checked_at=THU_SOURCE_CHECKED_AT,
        official_layout=False,
        official_form_number="赴全球姊妹校交換甄試申請表、家長同意書與學行優良表現證明" if template.id == "exchange-application-data" else ("出國學習計畫書" if template.id == "study-plan" else None),
        official_file_name=None,
        official_download_url="https://oir.thu.edu.tw/upload/ck/files/2027%E5%B9%B4%E6%98%A5%E5%AD%B8%E6%9C%9F%E6%9D%B1%E6%B5%B7%E5%A4%A7%E5%AD%B8%E8%B5%B4%E5%85%A8%E7%90%83%E5%A7%8A%E5%A6%B9%E6%A0%A1%E4%BA%A4%E6%8F%9B%E7%94%84%E8%A9%A6%E7%B0%A1%E7%AB%A01012%E6%9B%B4.pdf",
        default_copies=1,
        signatures=["申請學生親筆簽名", "家長或監護人親筆簽章", "所屬系所主任或指導教授簽章"] if template.id == "exchange-application-data" else [],
        stamps=["所屬系所辦公室核章"] if template.id == "exchange-application-data" else [],
        stage={"predeparture-notice": "出席現場唱名選填學校並繳交保證金 $10,000 元，配合辦理姊妹校提名與入學申請", "return-report": "返國後 1 個月內繳交研修心得報告書與正式成績單辦理保證金 $10,000 元退還及獎補助核銷", "credit-transfer": "返國後持姊妹校正式成績單與課程大綱辦理境外學分採認"}.get(template.id, "完成線上報名並將核章紙本申請表、家長同意書、報名費 $500 收據、歷年成績單（含名次證明）與外語／學行優良證明送交國際暨兩岸合作處"),
        version="116準備工具-2026-10-28.1",
        destinations=["東海大學國際暨兩岸合作處境外學生事務組（臺中市西屯區臺灣大道四段 1727 號語文館 LF102）"],
        conditional_note="此為個人準備工具；東海大學赴全球姊妹校交換甄試每年分兩梯次（春季甄試約 9–10 月報名、秋季甄試約 2–3 月報名，自 2026 秋季甄試起取消口試），須完成線上申請並將核章紙本、報名費 500 元收據、歷年成績單與名次證明（全球暨港澳組 GPA 2.5+、大陸組 GPA 2.0+）、外語檢定（30%）與學行優良表現證明（35%）送交國際暨兩岸合作處，並依時出席「現場唱名選填學校」。",
    )
    return ApplicationDocumentTemplate.model_validate(payload)


def _shu_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    descriptions = {
        "exchange-application-data": "整理世新大學赴國外及大陸港澳姊妹校交換學生甄選、跨國雙聯學位暨教育部學海飛颺／惜珠與校內出國研修獎助學金應繳資料：1. 交換學生甄選申請表（須經系所主任簽章）、2. 家長或監護人同意書正本、3. 歷年成績單正本（含班／系排名百分比；赴國外交換一般須歷年平均 75 分或班排前 50%，赴大陸交換一般須歷年平均 70 分以上且操行 80 分以上）、4. 中英文自傳與出國研修讀書計畫書（約 1,000–1,500 字）、5. 有效外語能力檢定證明（英語組 TOEFL iBT 61–80／IELTS 5.5–6.5／TOEIC 600–750、日語組 JLPT N2–N3、韓語組 TOPIK 2–4 級；大陸及港澳地區免附外語檢定）與師長推薦信及相關獲獎／社團有利審查資料。",
        "study-plan": "撰寫世新大學赴國外及大陸港澳姊妹校交換甄選、雙聯學位及教育部學海飛颺／惜珠獎補助必繳之《出國研修讀書計畫書》（約 1,000–1,500 字）。請具體說明赴外動機、擬於志願姊妹校修習之傳播、管理、人文社會或法律專業課程規劃（依世新大學《學生出國選修課程實施辦法》規定，交換期間須維持世新在學學籍並繳交世新全額學雜費，每學期於姊妹校至少須修習相當於本校 6 學分或 2 門課以上）、語言準備及返國後學分抵免與職涯銜接規劃。",
        "course-preapproval": "辦理赴境外姊妹校修讀交換課程或雙聯學位之選課預審與教務核備（依《世新大學學生出國選修課程實施辦法》及《學生抵免學分辦法》規定，出國交換期間須辦理世新註冊並繳交全額學雜費，每學期至少修讀相當於本校 6 學分或 2 門課以上；出國交換以一學期或一學年為原則）。",
        "predeparture-notice": "獲國際暨兩岸事務處公告錄取後於期限內繳交《錄取確認書》與保證金新臺幣 5,000 元（完成交換返國繳交心得報告及辦理離校手續後無息退還；無故放棄者沒收），配合辦理姊妹校提名（Nomination）與外校入學申請，並完成行前說明會、役男出境緩徵及海外醫療與意外保險。",
        "return-report": "境外交換或雙聯研修期滿返國後 1 個月內，須向國際暨兩岸事務處（或兩岸事務處）繳交 1,500–2,000 字以上之《交換學生返國研修心得報告書》（含研修與生活照片至少 4–6 張，供刊登於國際處《歷屆交換生心得》專區）、姊妹校正式成績單及出入境證明，辦理保證金新臺幣 5,000 元無息退還與教育部學海計畫／校內獎助學金核銷。",
        "credit-transfer": "境外交換或雙聯研修期滿返國後持境外姊妹校核發之正式成績單正本、修業證明與課程大綱（Syllabus），依《世新大學學生出國選修課程實施辦法》及《學生抵免學分辦法》向所屬系（所）、院及教務處註冊課務組申請境外修習科目學分採認。",
    }
    if template.id not in descriptions:
        return None
    def adapt(value):
        if isinstance(value, str):
            return value.replace("長庚大學", "世新大學").replace("長庚", "世新")
        if isinstance(value, list):
            return [adapt(x) for x in value]
        if isinstance(value, dict):
            return {k: adapt(v) for k, v in value.items()}
        return value
    payload = adapt(template.model_dump(mode="json"))
    for field in payload["fields"]:
        if field["id"] == "class_rank_percent":
            field["help_text"] = "世新《選送學生出國研修甄選辦法》及簡章規定：赴國外交換歷年學業總平均一般須達 75 分（GPA 3.0）以上或班排名前 50%（赴大陸交換一般須達 70 分以上），且操行成績平均達 80 分以上；申請教育部學海飛颺者歷年成績須達班排名前 30%（或 GPA 3.2 以上）。請檢附含班／系排名之歷年成績單正本。"
        if field["id"] == "language_test":
            field["options"] = ["TOEFL iBT（一般交換 61–79+／歐美及雙聯 79–80+）", "IELTS 學術組（一般交換 5.5–6.0+／歐美及雙聯 6.0–6.5+）", "TOEIC 多益聽讀（亞洲及部分英語授課姊妹校採認 600–750+）", "JLPT 日語能力試驗（日本姊妹校一般要求 N2 或 N3 以上）", "TOPIK 韓語能力測驗（韓國語授課組要求 2–4 級以上；英語授課組可憑英檢申請）", "大陸及港澳地區姊妹校（免附外語檢定證明；以歷年學業成績、讀書計畫及面試審查）"]
            field["help_text"] = "依世新《赴國外姊妹校交換學生甄選簡章》規定：英語組採認 TOEFL iBT、IELTS、TOEIC 或全民英檢中高級；日語組採認 JLPT N1–N3；韓語組採認 TOPIK 2–6 級；赴大陸及港澳地區交換免外語檢定。"
    payload.update(
        description=descriptions[template.id],
        source_url="https://global.web.shu.edu.tw/%e5%ad%b8%e7%94%9f%e4%ba%a4%e6%b5%81-%e8%b5%b4%e5%a4%96%e7%a0%94%e4%bf%ae/",
        source_checked_at=SHU_SOURCE_CHECKED_AT,
        official_layout=False,
        official_form_number="交換學生甄選申請表、家長同意書與自傳讀書計畫" if template.id == "exchange-application-data" else ("出國研修讀書計畫書" if template.id == "study-plan" else None),
        official_file_name=None,
        official_download_url="https://global.web.shu.edu.tw/wp-content/uploads/sites/46/2026/09/2027%E6%98%A5%E5%AD%A3%E7%8F%AD%E8%B5%B4%E5%A4%96%E4%BA%A4%E6%8F%9B%E7%94%84%E9%81%B8%E7%B0%A1%E7%AB%A0.pdf",
        default_copies=1,
        signatures=["申請學生親筆簽名", "家長或監護人親筆簽章", "所屬系所主任或指導教授簽章"] if template.id == "exchange-application-data" else [],
        stamps=["所屬系所辦公室核章"] if template.id == "exchange-application-data" else [],
        stage={"predeparture-notice": "繳交錄取確認書與保證金 $5,000 元，配合辦理姊妹校提名與入學申請", "return-report": "返國後 1 個月內繳交研修心得報告書與正式成績單辦理保證金 $5,000 元退還及獎補助核銷", "credit-transfer": "返國後持姊妹校正式成績單與課程大綱辦理境外學分採認"}.get(template.id, "完成校內甄選報名並將核章紙本申請表、家長同意書、歷年成績單（含排名）、自傳、讀書計畫與外語檢定證明送交國際暨兩岸事務處（或兩岸事務處）"),
        version="116準備工具-2026-10-30.1",
        destinations=["世新大學國際暨兩岸事務處／兩岸事務處（臺北市文山區木柵路一段 17 巷 1 號舍我樓 R201／M201）"],
        conditional_note="此為個人準備工具；世新大學赴國外及大陸港澳姊妹校交換甄選每年分兩梯次（春季班約前一年 9–10 月報名、秋季班約當年 2–3 月報名），須將核章紙本申請表、家長同意書、歷年成績單（含班排）、中英文自傳、讀書計畫及外語檢定證明送交國際暨兩岸事務處（赴大陸及港澳送交兩岸事務處），並參加校內面試審查。",
    )
    return ApplicationDocumentTemplate.model_validate(payload)


def _pu_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    descriptions = {
        "exchange-application-data": "整理靜宜大學（411遊留學中心）出國交換、大陸交換、ISEP 國際交換計畫、跨國雙聯學位暨教育部學海飛颺／惜珠與 411 出國留學圓夢計畫應繳資料：1. 出國交換／雙聯研修申請表（須經系所主任簽章）、2. 家長或監護人同意書正本、3. 中英文歷年成績單正本（含班／系排名百分比；赴國外交換一般須歷年平均 70 分／GPA 2.5 以上或班排前 50%，歐美／ISEP／雙聯一般須 75 分／GPA 3.0 以上，且操行 80 分以上）、4. 中英文自傳與出國研修讀書計畫書（約 1,000–1,500 字）、5. 有效外語能力檢定證明（英語組 TOEFL iBT 61–79／IELTS 5.5–6.0／TOEIC 550–750、日語組 JLPT N2–N4、韓語組 TOPIK 2–4 級、西語 DELE A2–B2、法語 DELF／德語 Goethe；大陸地區交換免附外語檢定）與師長推薦信。",
        "study-plan": "撰寫靜宜大學赴國外及大陸姊妹校交換甄選、ISEP、雙聯學位及教育部學海飛颺／惜珠獎補助必繳之《出國研修讀書計畫書》（約 1,000–1,500 字）。請具體說明赴外動機、擬於志願姊妹校修習之專業或語言課程規劃（依靜宜大學《出國研修學生科目學分抵免辦法》規定，交換期間須維持靜宜在學註冊，交換生繳交靜宜全額學費並免繳雜費，且返國後至少須辦理抵免一科以上）、語言準備及返國後學分抵免與職涯銜接規劃。",
        "course-preapproval": "辦理赴境外姊妹校修讀交換課程、ISEP 或雙聯學位之選課預審與教務核備（依《靜宜大學與境外大學辦理雙聯學制實施辦法》及《出國研修學生科目學分抵免辦法》規定，交換生出國期間繳交靜宜全額學費並免繳雜費、雙聯生繳交靜宜全額學雜費；歐洲學分按 2 ECTS = 靜宜 1 學分、英國學分按 4 CATS = 靜宜 1 學分、美日韓及大陸按 1:1 換算，且返國後至少須抵免一科）。",
        "predeparture-notice": "獲國際暨兩岸事務處（411遊留學中心）公告錄取後於期限內完成錄取確認，配合辦理姊妹校或 ISEP 提名（Nomination）與外校入學申請，並完成行前說明會、役男出境緩徵及海外醫療與意外保險。",
        "return-report": "境外交換、ISEP 或雙聯研修期滿返國後 1 個月內，須向國際暨兩岸事務處（411遊留學中心）繳交 1,500–2,000 字以上之《出國交換／研修學生心得報告書》（含研修與生活照片至少 4–6 張，供刊登於 411 遊留學中心《經驗分享》專區）、姊妹校正式成績單及出入境證明，辦理教育部學海計畫／411 出國留學圓夢計畫／寰宇外語教育獎助學金核銷。",
        "credit-transfer": "境外交換、ISEP 或雙聯研修期滿返國後次學期開學兩個月內，須持境外姊妹校核發之正式成績單正本與課程大綱（Syllabus），依《靜宜大學出國研修學生科目學分抵免辦法》向所屬系（所）、院及綜合業務處申請境外修習科目學分抵免（強制規定至少須抵免一科）。",
    }
    if template.id not in descriptions:
        return None
    def adapt(value):
        if isinstance(value, str):
            return value.replace("長庚大學", "靜宜大學").replace("長庚", "靜宜")
        if isinstance(value, list):
            return [adapt(x) for x in value]
        if isinstance(value, dict):
            return {k: adapt(v) for k, v in value.items()}
        return value
    payload = adapt(template.model_dump(mode="json"))
    for field in payload["fields"]:
        if field["id"] == "class_rank_percent":
            field["help_text"] = "靜宜《出國研修辦法》及 411 遊留學中心甄選規定：赴國外及大陸交換歷年學業總平均一般須達 70 分（GPA 2.5）以上或班排名前 50%（歐美、ISEP 及雙聯學位一般須達 75 分／GPA 3.0 以上），且操行成績平均達 80 分以上；申請教育部學海飛颺者歷年成績須達班排名前 30%（或 GPA 3.0 以上）。請檢附含班／系排名之中英文歷年成績單正本。"
        if field["id"] == "language_test":
            field["options"] = ["TOEFL iBT（一般交換 61–79+／ISEP 及雙聯 79–80+）", "IELTS 學術組（一般交換 5.5–6.0+／ISEP 及雙聯 6.0–6.5+）", "TOEIC 多益聽讀（亞洲及部分英語授課姊妹校採認 550–750+）", "JLPT 日語能力試驗（日本姊妹校要求 N1–N4，一般交換要求 N2 或 N3 以上）", "TOPIK 韓語能力測驗（韓國姊妹校韓語授課組要求 2–4 級以上）", "DELE 西語檢定／DELF 法語檢定／Goethe 德語檢定（西語、法語、德語區姊妹校採認 A2–B2）", "大陸地區姊妹校（免附外語檢定證明；以歷年學業成績、讀書計畫及面試審查）"]
            field["help_text"] = "依靜宜 411 遊留學中心甄選規定：英語組採認 TOEFL iBT、IELTS、TOEIC 或全民英檢中高級；日語組採認 JLPT N1–N4；韓語組採認 TOPIK 2–6 級；西語組採認 DELE A2–B2；赴大陸地區交換免外語檢定。"
    payload.update(
        description=descriptions[template.id],
        source_url="https://411.pu.edu.tw/p/426-1073-4.php?Lang=zh-tw",
        source_checked_at=PU_SOURCE_CHECKED_AT,
        official_layout=False,
        official_form_number="411出國研修申請表、家長同意書與自傳讀書計畫" if template.id == "exchange-application-data" else ("出國研修讀書計畫書" if template.id == "study-plan" else None),
        official_file_name=None,
        official_download_url="https://411.pu.edu.tw/var/file/73/1073/img/1593/827651153.pdf",
        default_copies=1,
        signatures=["申請學生親筆簽名", "家長或監護人親筆簽章", "所屬系所主任或指導教授簽章"] if template.id == "exchange-application-data" else [],
        stamps=["所屬系所辦公室核章"] if template.id == "exchange-application-data" else [],
        stage={"predeparture-notice": "完成錄取確認並配合辦理姊妹校／ISEP 提名與外校入學申請", "return-report": "返國後 1 個月內繳交研修心得報告書與正式成績單辦理學海／圓夢獎助學金核銷", "credit-transfer": "返國後次學期開學兩個月內持正式成績單與課綱辦理學分抵免（至少須抵免一科）"}.get(template.id, "完成校內甄選報名並將核章紙本申請表、家長同意書、中英文歷年成績單（含排名）、自傳、讀書計畫與外語檢定證明送交國際暨兩岸事務處（411遊留學中心）"),
        version="116準備工具-2026-10-30.1",
        destinations=["靜宜大學國際暨兩岸事務處（411遊留學中心，臺中市沙鹿區臺灣大道七段 200 號主顧樓 111 室）"],
        conditional_note="此為個人準備工具；靜宜大學（411遊留學中心）每學期辦理三次出國交換生甄選（春季班為前一年 8 月底、9 月底、10 月底；秋季班為當年 2 月底、3 月底、4 月底；雙聯學位秋季入學為 3 月 31 日截止），交換生出國期間繳交靜宜全額學費並免繳雜費，返國後次學期開學兩個月內強制規定至少須抵免一科。",
    )
    return ApplicationDocumentTemplate.model_validate(payload)


def _usc_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    descriptions = {
        "exchange-application-data": "整理實踐大學（國際暨兩岸事務處 OIA）出國交換、雙聯學制、海外自費研修、中國大陸地區交換暨教育部學海飛颺／惜珠與校內出國留學獎學金應繳資料：1. 線上申請表（於實踐大學出國交換學生報名系統 oia-exchange.vercel.app 填寫最多 3 個志願後匯出 PDF，須經家長簽章、所屬學系主任及院長或國際學程主任核章）、2. 中文歷年成績單正本（含班排百分比；歷年學業總平均須達 75 分／GPA 3.0 以上或班排名前 50%，且歷年操行平均 80 分以上）、3. 中文或外文自傳及出國研修讀書計畫書（約 1,000–1,500 字）、4. 有效外語能力檢定證明（英語組 TOEFL iBT 61–80／IELTS 5.5–6.5／TOEIC 550–785、日語組 JLPT N1–N3、韓語組 TOPIK 2–4 級；中國大陸地區交換免附外語檢定）、5. 設計學院及相關專業學系申請者另須準備個人作品集（Portfolio）。",
        "study-plan": "撰寫實踐大學赴國外及大陸姊妹校交換甄選、雙聯學制、海外自費研修及教育部學海飛颺／惜珠獎補助必繳之《出國研修讀書計畫書》（約 1,000–1,500 字）。請具體說明赴外動機、擬於志願姊妹校修習之專業或語言課程規劃（依《實踐大學辦理學生赴境外大學研修要點》規定，交換期間須辦理實踐在學註冊並繳交全額學雜費，每學期至少應修習相當於實踐 6 學分——研究所至少 1 科 3 學分——且至少 1 門須為所屬學系專業課程）、語言準備及返國後學分抵免與職涯銜接規劃。",
        "course-preapproval": "辦理赴境外姊妹校修讀交換課程、雙聯學制或海外自費研修之選課預審與教務核備（依《實踐大學辦理學生赴境外大學研修要點》及《與境外大學辦理雙聯學制實施辦法》規定，出國前須填具《實踐大學出國研修學習協議書 Learning Agreement》及《境外研修學分認定申請表》經系主任核准；每學期至少修習相當於實踐 6 學分且含至少 1 門專業課程，學分換算：美日韓陸 1:1、歐洲 ECTS×0.5、英國 CATS×0.25）。",
        "predeparture-notice": "獲國際暨兩岸事務處公告甄選錄取後，須於規定期限內繳交《實踐大學出國交換學生錄取確認暨家長同意切結書》（大四申請者另須簽署延畢切結書），配合辦理姊妹校提名（Nomination）與外校入學申請，並參加行前說明會、辦理役男出境緩徵及投保海外醫療與意外保險。",
        "return-report": "境外交換、雙聯學制或海外自費研修期滿返國後 1 個月內，須依《實踐大學出國研修心得報告格式》向國際暨兩岸事務處繳交 1,500–2,000 字以上之《出國交換／雙聯研修學生心得報告書》（含研修與生活照片至少 4–6 張，供上傳至 OIA 歷屆交換學生心得分享雲端專區）、姊妹校正式成績單及出入境證明，辦理教育部學海飛颺／惜珠及校內出國留學獎學金核銷。",
        "credit-transfer": "境外交換、雙聯學制或自費研修期滿返國後開學規定期限內，須持境外姊妹校核發之正式成績單正本、課程大綱（Syllabus）及原核准之學習協議書，填具《實踐大學學生抵免學分申請書（境外研修專用）》向所屬學系（所）、院及教務處（或高雄校區教務組）申請境外修習科目學分採認與抵免。",
    }
    if template.id not in descriptions:
        return None
    def adapt(value):
        if isinstance(value, str):
            return value.replace("長庚大學", "實踐大學").replace("長庚", "實踐")
        if isinstance(value, list):
            return [adapt(x) for x in value]
        if isinstance(value, dict):
            return {k: adapt(v) for k, v in value.items()}
        return value
    payload = adapt(template.model_dump(mode="json"))
    for field in payload["fields"]:
        if field["id"] == "class_rank_percent":
            field["help_text"] = "實踐《辦理學生赴境外大學研修要點》及出國交換簡章規定：歷年學業總平均須達 75 分（GPA 3.0）以上或班排名前 50%，且歷年操行成績平均達 80 分以上；申請校內《出國留學獎學金》者須達 GPA 3.38 以上或班排名前 30%（加碼全額學雜費減免須達 GPA 3.75 以上或班排前 10%）；申請教育部學海飛颺者須達班排名前 30%。請檢附含班排名之中文歷年成績單正本。"
        if field["id"] == "language_test":
            field["options"] = ["TOEFL iBT（一般交換 61–79+／雙聯及歐美名校 79–80+）", "IELTS 學術組（一般交換 5.5–6.0+／雙聯及歐美名校 6.0–6.5+）", "TOEIC 多益聽讀（亞洲及部分歐洲英語授課姊妹校採認 550–785+）", "JLPT 日語能力試驗（日本姊妹校要求 N1–N3，一般交換要求 N2 或 N3 以上）", "TOPIK 韓語能力測驗（韓國姊妹校韓語授課組要求 2–4 級以上）", "法語 DELF／德語 Goethe／西語 DELE（歐洲母語授課組依姊妹校要求 A2–B2）", "中國大陸地區姊妹校（免附外語檢定證明；僅限第一階段申請，以歷年成績、讀書計畫與面試審查）"]
            field["help_text"] = "依實踐國際暨兩岸事務處（OIA）簡章及語言能力對照表：英語組採認 TOEFL iBT、IELTS、TOEIC 或全民英檢中高級；日語組採認 JLPT N1–N3；韓語組採認 TOPIK 2–6 級；赴中國大陸地區交換免外語檢定（僅於第一階段開放申請）。"
    payload.update(
        description=descriptions[template.id],
        source_url="https://uscoia.usc.edu.tw/p/412-1049-1331.php?Lang=zh-tw",
        source_checked_at=USC_SOURCE_CHECKED_AT,
        official_layout=False,
        official_form_number="出國交換線上報名表與家長同意書" if template.id == "exchange-application-data" else ("出國研修讀書計畫書" if template.id == "study-plan" else None),
        official_file_name=None,
        official_download_url="https://uscoia.usc.edu.tw/var/file/49/1049/img/1593/777101909.pdf",
        default_copies=1,
        signatures=["申請學生親筆簽名", "家長或監護人親筆簽章", "所屬學系（所）主任簽章", "所屬學院院長或國際學程主任簽章"] if template.id == "exchange-application-data" else [],
        stamps=["所屬學系（所）及學院辦公室核章"] if template.id == "exchange-application-data" else [],
        stage={"predeparture-notice": "完成錄取確認切結書繳交並配合辦理姊妹校提名與外校入學申請", "return-report": "返國後 1 個月內繳交出國研修心得報告書與正式成績單辦理學海／校內獎學金核銷", "credit-transfer": "返國後開學規定期限內持正式成績單、課綱與學習協議書辦理境外學分採認抵免"}.get(template.id, "於實踐大學出國交換學生報名系統（oia-exchange.vercel.app）完成線上填報（最多 3 個志願）並匯出申請表，經系主任與院長核章後連同備審資料上傳或送交國際暨兩岸事務處"),
        version="115-2準備工具-2026-10-30.1",
        destinations=["實踐大學國際暨兩岸事務處（臺北校區：臺北市中山區大直街 70 號 A 棟 4 樓；高雄校區：高雄市內門區大學路 200 號教學大樓 1 樓國際事務組）"],
        conditional_note="此為個人準備工具；實踐大學每學期分兩階段於線上報名系統（oia-exchange.vercel.app）辦理出國交換、雙聯學制暨海外自費研修甄選（如 115-2 第一階段 2026/09/01–10/01、第二階段 2026/10/19–10/29 17:00，中國大陸地區交換僅限第一階段申請），出國期間須繳交實踐全額學雜費，每學期至少修習相當於實踐 6 學分且至少 1 門為所屬學系專業課程。",
    )
    return ApplicationDocumentTemplate.model_validate(payload)


def _nuk_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    descriptions = {
        "exchange-application-data": "整理國立高雄大學（國際事務處國際交流組 DIA）校級赴境外交換生甄選、跨國雙聯學位暨教育部學海飛颺／惜珠與校內海外交換獎助學金應繳資料：1. 出國交換學生申請表（含基本資料表與志願表，須經本人簽名、家長或監護人簽章及所屬系所主任核章）、2. 家長同意書正本（研究所在職生可免）、3. 歷年中文成績單與英文成績單正本各乙份（須由教務處註冊組列印並載明班級排名與班級人數；學士班排名佔 65%，碩博班排名佔 35%）、4. 中英文讀書計畫及履歷表（佔 35%，含國際生活學伴、國際課輔學伴、夏日學校隊輔、SDG 志工大使等校內國際活動加分證明）、5. 有效外語能力檢定證明影本（TOEFL iBT 64／TOEFL ITP 510／IELTS 5.0／TOEIC 590／JLPT N3／TOPIK 3 級／法德西語 A1；赴大陸地區交換免附外語檢定）、6. 碩博士班研究生另須檢附指導教授推薦信（佔 30%）。",
        "study-plan": "撰寫國立高雄大學赴國外及大陸姊妹校交換甄選、跨國雙聯學位及教育部學海飛颺／惜珠獎補助必繳之《中英文讀書計畫及履歷表》（約 1,000–1,500 字，佔校內甄選總分 35%）。請具體說明赴外動機、個人學業與國際活動表現（如國際生活學伴、國際課輔學伴、夏日學校隊輔、SDG 志工大使）、擬於志願姊妹校修習之專業或語言課程規劃（依《國立高雄大學學生出國期間有關學業及學籍處理要點》規定，交換期間須維持高大在學註冊，每學期至少修讀相當於高大 6 學分或 2 門以上課程）、語言準備及返國後學分抵免與職涯銜接規劃。",
        "course-preapproval": "辦理赴境外姊妹校修讀交換課程或跨國雙聯學位之選課預審與教務核備（依《國立高雄大學學生出國期間有關學業及學籍處理要點》及《與國外大學校院辦理跨國雙聯學制實施辦法》規定，交換生出國期間須維持高大在學註冊並繳交高大平安保險費與學雜費，免繳姊妹校學費；每學期至少修讀相當於高大 6 學分或 2 門以上課程，歐洲學分按 2 ECTS = 高大 1 學分、美日韓及大陸按 1:1 換算）。",
        "predeparture-notice": "獲國際事務處公告甄選錄取後，須於規定期限內繳交《錄取資格確認書》及保證金新臺幣 3,000 元，配合辦理姊妹校提名（Nomination）與外校入學申請，並完成出國選課、役男出境緩徵及海外醫療與意外保險。",
        "return-report": "境外交換或雙聯研修期滿返國後兩個月內，須向國際事務處國際交流組繳交 2,000 字以上之《出國交換學生返國研修心得報告書》（含研修與生活照片至少 4–6 張，供刊登於國際處《心得分享》專區）、姊妹校正式成績單及出入境證明，始得辦理保證金新臺幣 3,000 元無息退還及教育部學海飛颺／惜珠與校內海外交換獎助學金核銷。",
        "credit-transfer": "境外交換或雙聯研修期滿返國後開學規定期限內，須持境外姊妹校核發之正式成績單正本與課程大綱（Syllabus），依《國立高雄大學學生出國期間有關學業及學籍處理要點》向所屬學系（所）、院及教務處註冊組申請境外修習科目學分採認與抵免。",
    }
    if template.id not in descriptions:
        return None
    def adapt(value):
        if isinstance(value, str):
            return value.replace("長庚大學", "國立高雄大學").replace("長庚", "高大")
        if isinstance(value, list):
            return [adapt(x) for x in value]
        if isinstance(value, dict):
            return {k: adapt(v) for k, v in value.items()}
        return value
    payload = adapt(template.model_dump(mode="json"))
    for field in payload["fields"]:
        if field["id"] == "class_rank_percent":
            field["help_text"] = "高大《選送學生出國研修審查作業要點》規定：學士班甄選總成績以「班排名（65%）＋讀書計畫（35%）」計算；碩博士班以「班排名（35%）＋讀書計畫（35%）＋指導教授推薦信（30%）」計算，總分須達 70 分以上始具錄取資格；申請教育部學海飛颺者須達班排名前 30%（或 GPA 3.0 以上）。請檢附教務處註冊組列印並載明班級排名與班級人數之中英文歷年成績單正本。"
        if field["id"] == "language_test":
            field["options"] = ["TOEFL iBT（校內標準 64+／學海計畫 68+／歐美及雙聯依姊妹校要求 79–90+）", "TOEFL ITP（校內標準 510+／學海計畫 520+／多所亞洲及歐洲姊妹校採認 500–550+）", "IELTS 學術組（校內標準 5.0+／學海計畫 5.5+／歐美及雙聯依姊妹校要求 6.0–6.5+）", "TOEIC 多益聽讀（校內標準 590+／學海計畫 700+）", "JLPT 日語能力試驗（校內標準 N3+／學海計畫 N2+／日本姊妹校多要求 N1–N3）", "TOPIK 韓語能力測驗（校內標準 3 級+／學海計畫 4 級+／首爾大學要求 5 級、崇實大學要求 4 級）", "法語 DELF／德語 Goethe／西語 DELE（校內標準 A1+／學海計畫 A2+／歐洲母語授課組依姊妹校要求 A2–B2）", "大陸地區姊妹校（免附外語檢定證明；以班排名、讀書計畫及推薦信審查）"]
            field["help_text"] = "依《國立高雄大學選送優秀學生出國研修之語文能力證明標準》：兩年內有效之英語組採認 TOEFL iBT 64+、TOEFL ITP 510+、IELTS 5.0+、TOEIC 590+ 或全民英檢中高級初試／中級複試；日語組 JLPT N3+；韓語組 TOPIK 3 級+；法德西語 A1+；越南語 B／B1+；赴大陸地區交換免附外語檢定。"
    payload.update(
        description=descriptions[template.id],
        source_url="https://dia.nuk.edu.tw/p/404-1034-54746.php?Lang=zh-tw",
        source_checked_at=NUK_SOURCE_CHECKED_AT,
        official_layout=False,
        official_form_number="出國交換學生申請表與家長同意書" if template.id == "exchange-application-data" else ("中英文讀書計畫及履歷表" if template.id == "study-plan" else None),
        official_file_name=None,
        official_download_url="https://dia.nuk.edu.tw/var/file/34/1034/img/397/939423886.docx",
        default_copies=1,
        signatures=["申請學生親筆簽名", "家長或監護人親筆簽章", "所屬學系（所）主任或指導教授簽章"] if template.id == "exchange-application-data" else [],
        stamps=["所屬學系（所）辦公室核章"] if template.id == "exchange-application-data" else [],
        stage={"predeparture-notice": "繳交錄取資格確認書與保證金 $3,000 元，配合辦理姊妹校提名與外校入學申請", "return-report": "返國後兩個月內繳交 2,000 字以上研修心得報告書與正式成績單辦理保證金 $3,000 元退還及獎補助核銷", "credit-transfer": "返國後開學規定期限內持正式成績單與課綱向系所及教務處註冊組辦理境外學分採認抵免"}.get(template.id, "將核章紙本申請表、家長同意書、中英文歷年成績單（含班排）、中英文讀書計畫與履歷表、外語檢定證明（及碩博指導教授推薦信）送交國際事務處國際交流組（行政大樓南棟 4 樓）"),
        version="115-1準備工具-2026-10-30.1",
        destinations=["國立高雄大學國際事務處國際交流組（81148 高雄市楠梓區高雄大學路 700 號 行政大樓南棟 4 樓）"],
        conditional_note="此為個人準備工具；國立高雄大學每學期辦理校級赴境外交換生甄選（如 115 學年度第 1 學期甄選於 2025/12/29–2026/02/26 17:00 收件，2026/03/13 公告錄取，2026/03/23 前繳交錄取資格確認書與保證金新臺幣 3,000 元），返國後兩個月內須繳交 2,000 字以上心得報告始得辦理保證金退還。",
    )
    return ApplicationDocumentTemplate.model_validate(payload)


def _ncyu_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    descriptions = {
        "exchange-application-data": "整理國立嘉義大學（國際事務處國際合作交流組 OIA）薦外交換學生甄選、跨國雙聯學位暨教育部學海飛颺／惜珠與校內《薦外姊妹校交換學生獎補助金》應繳資料：1. 國立嘉義大學薦外交換學生甄選申請表（含基本資料、最多 2 志願學校選填、進修課程規劃同意書與經費預算表；須經導師或指導教授、系所主管及學院院長核章，且進修課程需檢附該系、所務會議同意之會議紀錄）、2. 家長同意書正本（1141031更新版）、3. 歷年中文成績單與英文成績單正本（須含學期平均成績與全班排名百分比；在校成績須達全班前 20% 以內，或學期平均大學部 75 分［含］以上、研究生 80 分［含］以上；班級排名佔非華語地區 40%、華語地區 80%）、4. 讀書計畫（佔 20%，含申請動機、選課規劃、語言準備及預期效益）、5. 有效外語能力檢定證明影本（非華語地區佔 40%：英語 A級 TOEFL iBT 79–93／IELTS 6.5、B級 iBT 60–78／IELTS 6.0、C級 iBT 46–59／IELTS 5.5、D級 iBT 35–45／IELTS 5.0 或 CEFR B1 TOEIC 550+；日語 JLPT N1–N3；華語地區免附語檢）。",
        "study-plan": "撰寫國立嘉義大學薦外交換學生甄選、跨國雙聯學位及教育部學海飛颺／惜珠與校內交換獎補助金必繳之《讀書計畫》（佔校內審查總成績 20%，建議約 1,000–1,500 字）與《進修課程規劃同意書》（若選填 2 個志願學校，需分別撰寫 2 份課程規劃與經費預算表，並檢附所屬系、所務會議同意之會議紀錄）。請具體說明赴外動機、擬於志願姊妹校修習之專業領域或語言課程、外語能力準備，以及返國後學分抵免與職涯銜接規劃。",
        "course-preapproval": "辦理赴境外姊妹校修讀交換課程或跨國雙聯學位之《進修課程規劃同意書》系所務會議審議與教務核備（依《國立嘉義大學薦外交換學生審查要點》及《與國外大學校院辦理跨國雙聯學制實施辦法》規定，申請時所擬進修課程需檢附該系、所務會議同意之會議紀錄；交換期間須完成嘉大註冊並繳交學雜費，保有嘉大在學學籍，不得辦理休學或畢業）。",
        "predeparture-notice": "獲國際事務處公告甄選錄取後，配合國際合作交流組辦理姊妹校官方提名（Nomination）與外校入學申請；出國前須詳閱《國立嘉義大學海外研修手冊》與《薦外交換生手冊》、完成簽證申辦、役男出境緩徵、購買涵蓋海外全期之醫療及意外保險，並簽署《教育部學海飛颺／惜珠》或《國立嘉義大學薦外姊妹校交換學生獎補助金》契約。",
        "return-report": "境外交換或雙聯研修期滿返國後規定期限內，須依《國立嘉義大學薦外交換生手冊》及《薦外姊妹校交換學生獎補助金發放要點》向國際事務處繳交《交換學生返國研修心得報告書》（建議 1,500–2,000 字以上，含研修與生活照片，供收錄於嘉大國際處經驗分享專區與雲端資料庫）、姊妹校正式成績單、護照出入境章影本、登機證正本與電子機票收據，辦理教育部學海計畫及校內交換獎補助金尾款核銷。",
        "credit-transfer": "境外交換或雙聯研修期滿返國後開學規定期限內，須持境外姊妹校核發之正式成績單正本與課程大綱（Syllabus），依先前經系、所務會議審議通過之進修課程規劃及《國立嘉義大學學生抵免學分辦法》，向所屬學系（所）、院及教務處註冊與課務組申請境外修習科目學分採認與抵免。",
    }
    if template.id not in descriptions:
        return None
    def adapt(value):
        if isinstance(value, str):
            return value.replace("長庚大學", "國立嘉義大學").replace("長庚", "嘉大")
        if isinstance(value, list):
            return [adapt(x) for x in value]
        if isinstance(value, dict):
            return {k: adapt(v) for k, v in value.items()}
        return value
    payload = adapt(template.model_dump(mode="json"))
    for field in payload["fields"]:
        if field["id"] == "class_rank_percent":
            field["help_text"] = "嘉大《薦外交換學生審查要點》第二點及第五點規定：在校成績需達全班前 20% 以內，或學期平均成績大學部 75 分（含）以上、研究生 80 分（含）以上，且各科（含操行）成績須達及格標準。審查計分：非華語地區班級排名百分比佔 40%（前10%得40%、11–20%得37%、21–30%得35%），華語地區班級排名百分比佔 80%。請檢附載明班級排名百分比之中英文歷年成績單正本。"
        if field["id"] == "language_test":
            field["options"] = ["TOEFL iBT（A級 79–93 得40%／B級 60–78 得36%／C級 46–59 得32%／D級 35–45 得24%；歐洲B1門檻57+）", "IELTS 學術組（A級 6.5 得40%／B級 6.0 得36%／C級 5.5 得32%／D級 5.0 得24%）", "TOEIC 多益聽讀（CEFR B1=550+／CEFR B2=785+）", "TOEFL ITP（CEFR B1=460+／CEFR B2=543+）", "JLPT 日語能力試驗（A級 N1 得40%／B級 N2 得36%／C級 N3 得32%／D級 N4 得24%；日本姊妹校多要求 N2–N3）", "TOPIK 韓語能力測驗（韓國姊妹校韓語授課組要求 3–4 級以上）", "法語 DELF／德語 Goethe／西語 DELE（歐洲姊妹校母語授課組要求 B1–B2）", "華語地區姊妹校（中國大陸姊妹校免附語言測驗成績；以班排 80%＋讀書計畫 20% 審查）"]
            field["help_text"] = "依《國立嘉義大學薦外交換學生審查要點》第五點及《英語能力檢定測驗門檻對照表》：非華語地區語言能力佔審查總分 40%（分 A/B/C/D 四級給分），華語地區免附語言測驗成績。"
    payload.update(
        description=descriptions[template.id],
        source_url="https://www.ncyu.edu.tw/oia/Contents?nodeId=57878",
        source_checked_at=NCYU_SOURCE_CHECKED_AT,
        official_layout=False,
        official_form_number="薦外交換學生甄選申請表（1141031更新）與家長同意書" if template.id == "exchange-application-data" else ("讀書計畫與進修課程規劃同意書" if template.id == "study-plan" else None),
        official_file_name=None,
        official_download_url="https://www.ncyu.edu.tw/Uploads/Item/03db4fa7-b9e0-445d-88bb-0d9918b55249.pdf",
        default_copies=1,
        signatures=["申請學生親筆簽名", "家長或監護人親筆簽章", "導師或指導教授簽章", "所屬系（所）主管簽章", "所屬學院院長簽章"] if template.id == "exchange-application-data" else [],
        stamps=["所屬系（所）及學院辦公室核章（含系、所務會議同意進修課程規劃之會議紀錄）"] if template.id == "exchange-application-data" else [],
        stage={"predeparture-notice": "獲錄取後配合國際處辦理姊妹校提名與入學申請，完成行前手續與獎補助金簽約", "return-report": "返國後依限繳交研修心得報告書與正式成績單辦理學海／校內交換獎補助金核銷", "credit-transfer": "返國後開學規定期限內持正式成績單與課綱向系所及教務處辦理境外學分採認抵免"}.get(template.id, "備齊經系所及學院核章之申請表（含系、所務會議同意進修課程之會議紀錄）、家長同意書、中英文成績單（含班排）、讀書計畫與外語檢定證明送交國際事務處國際合作交流組（蘭潭校區行政大樓 3 樓）"),
        version="114準備工具-2026-10-30.1",
        destinations=["國立嘉義大學國際事務處國際合作交流組（600355 嘉義市東區學府路 300 號 蘭潭校區行政大樓 3 樓）"],
        conditional_note="此為個人準備工具；國立嘉義大學每年分兩梯次辦理薦外交換學生甄選（秋季班出國於前一年 12 月收件、春季班出國於前一年 5–6 月收件），每人最多可選填 2 志願學校，且進修課程規劃須檢附該系、所務會議同意之會議紀錄。",
    )
    return ApplicationDocumentTemplate.model_validate(payload)


def _nutc_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    descriptions = {
        "exchange-application-data": "整理國立臺中科技大學（國際事務處 OIA，三民校區中正大樓 1 樓 3105 室）出國交換留學甄選、大陸地區協議學校研習暨教育部學海飛颺／惜珠計畫應繳資料：1. 國立臺中科技大學交換留學申請表／赴大陸地區協議學校研習申請表／學海系列計畫申請表（貼妥 2 吋照片）、2. 家長同意書正本及個資提供同意書、3. 歷年成績單正本＋最近一學期含班級排名之中英文版成績單（國外交換各科 70 分以上、大陸交換歷年平均 80 分以上，操行平均皆須 80 分以上）、4. 中外文自傳與讀書計畫（含預計選修課程與本校抵免對應規劃；申請設計類學部另附作品集）、5. 有效外語能力檢定證明影本（日本 JLPT N2 以上；韓國全北大學 TOPIK 初級＋TOEIC 550、三育大學韓語證明；歐美及東南亞 GEPT 中級或 TOEFL iBT 60 / TOEIC 550 以上；大陸港澳免附）及教授推薦信。",
        "study-plan": "撰寫國立臺中科技大學出國交換留學、大陸協議學校研習及教育部學海飛颺／惜珠計畫必繳之《中、外文自傳與讀書計畫》（建議 1,000–1,500 字）。請具體說明留學動機、擬於姊妹校修習之專業科目與中科大對應抵免規劃、外語學習準備，以及留學期間配合國際處粉專投稿與返國後 20 小時國際交流志願服務規劃。",
        "course-preapproval": "辦理赴境外姊妹校修讀交換課程或英國西蘇格蘭大學（UWS）雙聯學位之選課與學分抵免預先規劃（交換期間須於國立臺中科技大學完成註冊並繳交全額學雜費以保留學籍；返國後 2 週內須持姊妹校正式成績單向所屬系所報到並向教務處註冊組辦理學分抵免）。",
        "predeparture-notice": "獲國際事務處公告甄選錄取後，配合國際事務處辦理姊妹校官方提名（Nomination）與外校入學申請（含財力證明與健康檢查表）；出國前須完成簽證申辦、役男出境緩徵、購買涵蓋全期之海外醫療及意外保險，獲教育部學海計畫補助者須於出國前 1 個月簽訂行政契約書。",
        "return-report": "境外交換研修期間赴日、韓交換生須定期投稿國際處粉絲專頁（1 學期至少 5 篇、1 學年至少 10 篇）；返國後 1 個月內須繳交中文心得報告電子檔、參加交換留學分享會並完成國際事務處志願服務 20 小時（獲教育部學海計畫補助者須於計畫結束後 2 週內至學海系統上傳 1500 字心得與問卷辦理經費核銷）。",
        "credit-transfer": "境外交換或雙聯研修期滿返國後 2 週內，須持境外姊妹校核發之正式成績單正本與課程大綱，向所屬系所報到並向教務處註冊組申請境外修習科目學分抵免。",
    }
    if template.id not in descriptions:
        return None
    def adapt(value):
        if isinstance(value, str):
            return value.replace("長庚大學", "國立臺中科技大學").replace("長庚", "中科大")
        if isinstance(value, list):
            return [adapt(x) for x in value]
        if isinstance(value, dict):
            return {k: adapt(v) for k, v in value.items()}
        return value
    payload = adapt(template.model_dump(mode="json"))
    for field in payload["fields"]:
        if field["id"] == "class_rank_percent":
            field["help_text"] = "中科大《學生申請教育部學海系列計畫審查要點》及交換簡章規定：國外交換留學各科成績皆須達 70 分以上且操行成績平均達 80 分以上；赴大陸協議學校歷年學業總平均及操行成績均須達 80 分以上。請同時檢附「歷年成績單正本」與「最近一學期含班級排名之中英文版成績單」。"
        if field["id"] == "language_test":
            field["options"] = ["JLPT 日語能力試驗（日本姊妹校規定須通過 N2 級及格以上；新潟大學經濟學部另須 TOEIC 550+）", "TOPIK 韓語能力測驗＋TOEIC 多益（全北大學須 TOPIK 初級＋TOEIC 550；三育大學須韓語能力證明，TOPIK 3級以上尤佳）", "TOEFL iBT / TOEIC / GEPT 全民英檢（歐美及東南亞姊妹校：GEPT 中級以上或 TOEFL iBT 60 / TOEIC 550–605 / IELTS 5.0–6.0）", "大陸及澳門地區協議學校（免附外語能力檢定證明，惟歷年學業總平均及操行均須達 80 分以上）"]
            field["help_text"] = "依《國立臺中科技大學學生申請教育部學海系列計畫審查要點》第四點第（十）款及各姊妹校交換留學簡章填報有效期限內之外語檢定成績。"
    payload.update(
        description=descriptions[template.id],
        source_url="https://oia.nutc.edu.tw/p/412-1026-8451.php?Lang=zh-tw",
        source_checked_at=NUTC_SOURCE_CHECKED_AT,
        official_layout=False,
        official_form_number="國立臺中科技大學交換留學申請表與家長同意書" if template.id == "exchange-application-data" else ("中外文自傳與讀書計畫" if template.id == "study-plan" else None),
        official_file_name=None,
        official_download_url="https://oia.nutc.edu.tw/var/file/26/1026/attach/98/pta_96597_1136748_50891.pdf",
        default_copies=1,
        signatures=["申請學生親筆簽名", "家長或監護人親筆簽名蓋章", "導師或指導教授簽章", "系（所、科）主任簽章"] if template.id == "exchange-application-data" else [],
        stamps=["所屬系（所、科）及學院辦公室核章"] if template.id == "exchange-application-data" else [],
        stage={"predeparture-notice": "獲錄取後配合國際處辦理姊妹校提名、入學申請與學海計畫行政契約簽署", "return-report": "留學期間定期投稿國際處粉專，返國後繳交中文心得報告、參加分享會並完成 20 小時志願服務", "credit-transfer": "返國後 2 週內持正式成績單向系所報到並向教務處註冊組辦理學分抵免"}.get(template.id, "備齊申請表、家長同意書、歷年含班排中英文成績單、自傳讀書計畫、語檢證書與推薦信送達三民校區中正大樓 1 樓 3105 室國際事務處"),
        version="115準備工具-2026-10-31.1",
        destinations=["國立臺中科技大學國際事務處（404336 臺中市北區三民路三段 129 號 中正大樓 1 樓 3105 室）"],
        conditional_note="此為個人準備工具；國立臺中科技大學春季班交換於前一年 9–10 月收件、秋季班交換於當年 3–5 月收件、教育部學海系列計畫於每年 1–3 月初收件（115年度為 3 月 4 日國際處截止）。",
    )
    return ApplicationDocumentTemplate.model_validate(payload)


def _nfu_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    descriptions = {
        "exchange-application-data": "整理國立虎尾科技大學（國際事務處 OIA，第一校區行政大樓 4 樓）選送優秀學生出國研修（交換學生／學海飛颺／學海惜珠）暨 3+1+1 雙聯學制應繳 13 項自檢資料：1. 交換學生甄選報名表（電腦打字、貼妥大頭照，至多可填 3 所志願校）、2. 申請時應附表件自檢表（置於首頁）、3. 歷年成績單（中文及英文版各乙份，須含班排名）、4. 歷年獎懲紀錄證明、5. 有效期限內語言能力證明影本（CEFR B1 以上：TOEIC 550 / TOEFL iBT 42 / TOEFL ITP 457 / IELTS 4.0，或日檢 N1–N4、韓檢 TOPIK 3 級）、6. 教授推薦信（中文或英文乙封）、7. 自傳（中文及英文各乙份）、8. 讀書計畫（中文及英文各乙份，含國外修習學分規劃）、9. 個人榮譽事項或特殊表現證明、10. 家長或監護人同意書、11. 有效護照影本、12. 歷屆曾參與國際處舉辦活動證明（加分用）、13. 中華民國國籍證明（身分證正反面影本；學海惜珠另附新式戶口名簿影本與低收／中低收入戶證明）。所有文件請以燕尾夾裝訂，勿使用訂書針或特殊裝訂。",
        "study-plan": "撰寫國立虎尾科技大學出國交換學生、3+1+1 雙聯學位及教育部學海飛颺／惜珠計畫必繳之《中文及英文讀書計畫》（各乙份）與《中文及英文自傳》（各乙份）。請具體說明留學動機、擬於姊妹校選修之專業課程（每學期至少須選修 9 學分或 18 ECTS 以上專業課程）、與虎科大課程之學分抵免對應規劃，以及海外生活適應與返國後學習規劃。",
        "course-preapproval": "辦理赴境外姊妹校修讀交換課程（每學期至少 9 學分或 18 ECTS 以上專業課程）或美國密西根大學迪爾伯恩分校（UM-Dearborn）、羅德島大學（URI）3+1+1 雙聯學位之選課與學分抵免預先規劃（出國期間須於國立虎尾科技大學完成註冊選課手續保留學籍，交換期間不得辦理畢業；返國後一個月內填寫「國立虎尾科技大學學生赴國外修讀學分抵免申請表」並檢附成績單正本送系所與教務處審核）。",
        "predeparture-notice": "獲國際事務處公告錄取後（面試成績須達 70 分以上），須於期限內繳交《錄取資格確認書》（無故放棄者於現就讀學制期間不得再申請本項甄選），配合國際處辦理姊妹校官方提名（Nomination）與外校入學申請；出國前須參加行前說明會、簽署切結書（及學海計畫行政契約書）、辦理簽證、役男出境緩徵並自行購買海外足額醫療及意外保險。",
        "return-report": "境外交換或雙聯研修期滿返國後一個月內，須向國際事務處繳交《國外研修心得報告》（供刊登於國際處網站及學海計畫資訊網）並配合國際處辦理國際教育宣導活動與出國研修說明會經驗分享，以完成《國立虎尾科技大學學生出國研修獎助要點》及教育部學海系列計畫獎助金核銷。",
        "credit-transfer": "境外交換或雙聯研修期滿返國後一個月內，須填寫「國立虎尾科技大學學生赴國外修讀學分抵免申請表」並檢附境外姊妹校核發之正式成績單正本與課程大綱，向所屬系（所）及教務處申請學分抵免。",
    }
    if template.id not in descriptions:
        return None
    def adapt(value):
        if isinstance(value, str):
            return value.replace("長庚大學", "國立虎尾科技大學").replace("長庚", "虎科大")
        if isinstance(value, list):
            return [adapt(x) for x in value]
        if isinstance(value, dict):
            return {k: adapt(v) for k, v in value.items()}
        return value
    payload = adapt(template.model_dump(mode="json"))
    for field in payload["fields"]:
        if field["id"] == "class_rank_percent":
            field["help_text"] = "虎科大《甄選學生赴國外研修作業要點》規定：申請人前學年學業總平均成績須達 75 分以上或班排名前 50%，且操行成績平均達 80 分以上（無小過以上處分）。請同時檢附含班排名之「歷年成績單中文版及英文版各乙份」與「歷年獎懲紀錄證明」。"
        if field["id"] == "language_test":
            field["options"] = ["TOEIC 多益聽讀（CEFR B1 門檻：總分 550 分以上；CEFR B2：總分 785 分以上）", "TOEFL iBT 網路測驗（CEFR B1 門檻：42 分以上；CEFR B2：72 分以上；美國 PSU 須 59+、UNLV 須 79+）", "TOEFL ITP 紙筆測驗（CEFR B1 門檻：457 分以上；CEFR B2：527 分以上；美國堪薩斯州大 KSU 須 550+）", "IELTS 雅思國際英語測驗（CEFR B1 門檻：4.0 以上；CEFR B2：5.5 以上；歐美大學多要求 5.5–6.5）", "JLPT 日語能力試驗（日本姊妹校依各校規定須通過 N1、N2、N3 或 N4 級以上）", "TOPIK 韓國語文能力測驗（韓國姊妹校依規定須通過 TOPIK 3 級以上或英語 CEFR B1–B2）"]
            field["help_text"] = "依虎科大《CEF與各項英檢對照表》及《海外姊妹校交換學生一覽表（115.06）》填報有效期限內之外語能力檢定證明。"
    payload.update(
        description=descriptions[template.id],
        source_url="https://oia.nfu.edu.tw/zh-tw/announcement/%E5%87%BA%E5%9C%8B%E4%BA%A4%E6%8F%9B-%E5%9C%8B%E7%AB%8B%E8%99%8E%E5%B0%BE%E7%A7%91%E6%8A%80%E5%A4%A7%E5%AD%B8115%E5%AD%B8%E5%B9%B4%E5%BA%A6%E7%AC%AC2%E5%AD%B8%E6%9C%9F%E9%81%B8%E9%80%81%E5%84%AA%E7%A7%80%E5%AD%B8%E7%94%9F%E5%87%BA%E5%9C%8B%E7%A0%94%E4%BF%AE-%E4%BA%A4%E6%8F%9B%E5%AD%B8%E7%94%9F-%E5%AD%B8%E6%B5%B7%E9%A3%9B%E9%A2%BA-%E7%94%84%E9%81%B8%E7%B0%A1%E7%AB%A0-30322703",
        source_checked_at=NFU_SOURCE_CHECKED_AT,
        official_layout=False,
        official_form_number="交換學生甄選報名表（含13項應附表件自檢表与家長同意書）" if template.id == "exchange-application-data" else ("中英文自傳與讀書計畫" if template.id == "study-plan" else None),
        official_file_name=None,
        official_download_url="https://oia.nfu.edu.tw/uploads/bulletin_file/file/684fd714298f3f4a19000909/%E4%BA%A4%E6%8F%9B%E5%AD%B8%E7%94%9F%E7%94%84%E9%81%B8%E5%A0%B1%E5%90%8D%E8%A1%A8.odt",
        default_copies=1,
        signatures=["申請人親筆簽名", "家長（或監護人）親筆簽名蓋章", "導師（或指導教授）簽章", "系（所）主任簽章"] if template.id == "exchange-application-data" else [],
        stamps=["所屬系（所）辦公室核章"] if template.id == "exchange-application-data" else [],
        stage={"predeparture-notice": "獲錄取後繳交錄取資格確認書、配合國際處辦理姊妹校提名、入學申請與切結書簽署", "return-report": "返國後一個月內繳交國外研修心得報告並配合國際處宣導活動辦理獎助金核銷", "credit-transfer": "返國後一個月內填寫赴國外修讀學分抵免申請表並持正式成績單向系所與教務處辦理學分抵免"}.get(template.id, "將13項應附表件依自檢表順序排列，以燕尾夾裝訂（勿用訂書針），送交第一校區行政大樓4樓國際事務處"),
        version="115-2準備工具-2026-10-31.1",
        destinations=["國立虎尾科技大學國際事務處（632301 雲林縣虎尾鎮文化路 64 號 第一校區行政大樓 4 樓）"],
        conditional_note="此為個人準備工具；國立虎尾科技大學每年分兩梯次辦理交換學生甄選（春季班於前一年 9 月底截止收件、10 月中旬面試；秋季班於當年 3–4 月收件），至多可填 3 所志願校。",
    )
    return ApplicationDocumentTemplate.model_validate(payload)


def _utaipei_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    descriptions = {
        "exchange-application-data": "整理臺北市立大學（國際事務處國際學生與海外研習組，博愛校區行政大樓 3 樓 309 室）赴境外及大陸港澳地區交換學生、雙聯學位暨教育部學海飛颺／惜珠計畫應繳申請表件：1. 校內報名表（電腦繕打、貼妥照片，經導師及系所主任簽章並加蓋系所戳章）、2. 家長同意書（申請人與家長或監護人親筆簽名蓋章）、3. 歷年成績單正本（含班／系排名或 GPA，英文交換須附英文成績單）、4. 歷年操行成績證明（操行平均達 80 分以上且無小過以上處分）、5. 語言能力檢定成績單影本（英語組 TOEFL iBT / IELTS / TOEIC、日語組 JLPT、韓語組 TOPIK；申請大陸及港澳地區姊妹校免附語檢）、6. 自傳與出國研修讀書計畫（中文或外文撰寫）、7. 教師推薦信（1–2 封）、8. 有效護照影本（大陸交換另備臺胞證）、9. 其他有利審查資料（競賽獲獎、社團幹部、國際志工或學海惜珠新式戶口名簿及低收／中低收入戶證明）。",
        "study-plan": "撰寫臺北市立大學赴境外（歐美亞紐澳）及大陸港澳姊妹校交換學生、雙聯學位及教育部學海飛颺／惜珠計畫必繳之《自傳與出國研修讀書計畫》。請具體說明申請動機、擬於姊妹校修讀之課程規劃（依規定大學部每學期至少修讀 6 學分或 2 門課、研究生至少 3 學分或 1 門課）、與北市大畢業學分抵免對應規劃，以及海外生活適應與返國後學習發展規劃。",
        "course-preapproval": "辦理赴境外姊妹校交換或 24 個系所雙聯學位計畫（美國 St. Cloud State、Indiana State、University of New Haven、Temple University、日本福岡工業大學、廣島大學、澳洲 Griffith University、法國 Audencia、奧地利維也納音樂暨表演藝術大學 MDW 等）之選課與學分抵免預先規劃（出國期間須於臺北市立大學完成註冊選課保留學籍；返國後於規定期限內依《臺北市立大學學生抵免學分要點》檢附正式成績單與課程大綱向系所及教務處申請學分抵免）。",
        "predeparture-notice": "獲國際事務處甄選錄取後，須於規定期限內繳交《錄取資格確認書》（逾期視同放棄，無故放棄者於同一學制內不得再次申請），配合國際處辦理姊妹校官方提名（Nomination）與外校入學申請；出國前須參加行前說明會、簽署切結書（及學海計畫或深耕獎助行政契約書）、辦理簽證、役男出境緩徵並投保足額海外醫療及意外保險。",
        "return-report": "境外交換或雙聯研修期滿返國後一個月內，須依規定向國際事務處繳交《赴境外研修心得報告》（約 1,500–3,000 字並附活動照片，供刊登於國際處出國交換生返國心得報告專區與教育部學海計畫資訊網），並配合國際處出席海外留學與交換生經驗分享說明會，始得完成校內深耕海外學習獎助學金或教育部學海系列計畫核銷。",
        "credit-transfer": "境外交換或雙聯研修期滿返國後，須填具臺北市立大學學分抵免申請表，並檢附境外合作大學核發之正式成績單正本及修習課程大綱，經所屬學系（所）審核通過後送教務處註冊組登錄抵免學分。",
    }
    if template.id not in descriptions:
        return None
    def adapt(value):
        if isinstance(value, str):
            return value.replace("長庚大學", "臺北市立大學").replace("長庚", "北市大")
        if isinstance(value, list):
            return [adapt(x) for x in value]
        if isinstance(value, dict):
            return {k: adapt(v) for k, v in value.items()}
        return value
    payload = adapt(template.model_dump(mode="json"))
    for field in payload["fields"]:
        if field["id"] == "class_rank_percent":
            field["help_text"] = "北市大規定：申請人歷年學業總平均建議達 GPA 3.0（或百分制 75 分）以上、操行成績平均達 80 分以上且無小過以上處分；申請教育部《學海飛颺》獎助者須達 GPA 3.2 以上或班排名前 30%。請檢附含班／系排名之歷年中英文成績單正本。"
        if field["id"] == "language_test":
            field["options"] = ["TOEFL iBT 網路測驗（校級英語組基準：61–79 分以上；歐美頂尖校及雙聯須 79–80 分以上）", "IELTS 雅思國際英語測驗（校級英語組基準：5.5–6.0 以上；歐美名校及雙聯須 6.0–6.5 以上）", "TOEIC 多益聽讀測驗（亞洲及部分歐洲姊妹校採認：550–785 分以上；部分歐美校不採認 TOEIC）", "JLPT 日語能力試驗（日本姊妹校依各校規定須通過 N1、N2、N3 或 N4 級以上）", "TOPIK 韓國語文能力測驗（韓國姊妹校依規定須通過 TOPIK 2–4 級以上或英語組門檻）", "大陸及港澳地區姊妹校交換（免附外語能力檢定證明，以歷年學業成績、讀書計畫與面試評分）"]
            field["help_text"] = "依臺北市立大學《境外姊妹校申請門檻與名額一覽表》及當期交換生甄選簡章填報有效期限內之外語能力檢定證明。"
    payload.update(
        description=descriptions[template.id],
        source_url="https://intl.utaipei.edu.tw/p/412-1080-9549.php?Lang=zh-tw",
        source_checked_at=UTAIPEI_SOURCE_CHECKED_AT,
        official_layout=False,
        official_form_number="出國交換學生甄選申請表（含家長同意書與應繳文件檢核表）" if template.id == "exchange-application-data" else ("自傳與出國研修讀書計畫" if template.id == "study-plan" else None),
        official_file_name=None,
        official_download_url="https://intl.utaipei.edu.tw/var/file/80/1080/img/1534/247824614.docx",
        default_copies=1,
        signatures=["申請學生親筆簽名", "家長（或監護人）親筆簽名蓋章", "導師（或指導教授）簽章", "系（所）主任簽章"] if template.id == "exchange-application-data" else [],
        stamps=["所屬學系（所）辦公室核章"] if template.id == "exchange-application-data" else [],
        stage={"predeparture-notice": "獲錄取後繳交錄取資格確認書、配合國際處辦理姊妹校提名、入學申請與切結書簽署", "return-report": "返國後一個月內繳交赴境外研修心得報告並配合國際處經驗分享會辦理獎助金核銷", "credit-transfer": "返國後檢附正式成績單與課程大綱向系所及教務處註冊組辦理學分抵免"}.get(template.id, "備齊校內申請表、家長同意書、歷年含排名中英文成績單、自傳讀書計畫、語檢證明與推薦信送交博愛校區行政大樓 3 樓 309 室國際事務處"),
        version="116-1準備工具-2026-10-31.1",
        destinations=["臺北市立大學國際事務處國際學生與海外研習組（100234 臺北市中正區愛國西路 1 號 博愛校區行政大樓 3 樓 309 室）"],
        conditional_note="此為個人準備工具；臺北市立大學每年分兩梯次辦理赴境外及大陸港澳交換學生甄選（第 1 學期出國於前一年 9–10 月收件、第 2 學期出國於前一年 2–3 月收件）。",
    )
    return ApplicationDocumentTemplate.model_validate(payload)


def _ntcu_template(template: ApplicationDocumentTemplate) -> ApplicationDocumentTemplate | None:
    descriptions = {
        "exchange-application-data": "整理國立臺中教育大學（國際及兩岸事務暨研究發展處國際交流組，民生校區行政樓 2 樓）選送學生出國研修、大陸及港澳地區交換暨教育部學海飛颺／惜珠計畫應繳申請表件：1. 申請繳交資料檢核表、2. 選送學生出國研修申請表（須經導師、系所主管及院長簽章）、3. 家長（監護人）同意書、4. 歷年中文成績單正本（含班級或系所排名）、5. 外語能力檢定證明影本（英語組 TOEFL iBT / IELTS / TOEIC、日語組 JLPT、韓語組 TOPIK；申請大陸及港澳地區免附外語檢定）、6. 出國研修計畫書與自傳、7. 有效護照影本及課外活動或競賽表現證明。",
        "study-plan": "撰寫國立臺中教育大學選送學生出國研修、雙聯學制暨教育部學海飛颺／惜珠計畫必繳之《出國研修計畫書與自傳》。請具體說明申請動機、目標姊妹校修課規劃（依中教大規定，出國研修期間每學期至少須選修相當於本校 6 學分或 2 門課程）、教育或專業領域學習目標，以及返國後學分抵免與職涯發展銜接規劃。",
        "course-preapproval": "辦理赴國外合作姊妹校交換或雙聯學制（美國得克薩斯州農工大學康莫斯分校 A&M-Commerce、印第安納波利斯大學 UIndy、英國倫敦大學金匠學院 Goldsmiths、紐西蘭奧克蘭大學等）之選課與學分抵免預先規劃（出國期間須於國立臺中教育大學完成註冊選課保留學籍；返國後依本校學生抵免學分辦法檢附正式成績單與課程大綱辦理學分抵免）。",
        "predeparture-notice": "獲國際及兩岸事務暨研究發展處甄選錄取後，須於期限內確認錄取資格、配合國研處辦理姊妹校提名（Nomination）與外校入學申請；出國前須參加行前說明會、簽署行政契約書與切結書、辦理簽證、役男出境緩徵並投保足額海外醫療及意外保險。",
        "return-report": "國外交換或雙聯研修期滿返國後規定期限內，須依《國立臺中教育大學甄選學生出國研修要點》及《補助學生赴外國大學（機構）選修課程要點》向國研處繳交《出國研修心得報告》（含研修照片，供刊登於國研處「交換生心得報告」專區與教育部學海計畫資訊網），並配合出席成果發表經驗分享會，始得完成獎助學金核銷。",
        "credit-transfer": "國外交換或雙聯研修期滿返國後，須填具國立臺中教育大學學分抵免申請表，並檢附境外姊妹校核發之正式成績單正本及修習課程大綱，經所屬學系（所）審核通過後送教務處註冊組登錄抵免學分。",
    }
    if template.id not in descriptions:
        return None
    def adapt(value):
        if isinstance(value, str):
            return value.replace("長庚大學", "國立臺中教育大學").replace("長庚", "中教大")
        if isinstance(value, list):
            return [adapt(x) for x in value]
        if isinstance(value, dict):
            return {k: adapt(v) for k, v in value.items()}
        return value
    payload = adapt(template.model_dump(mode="json"))
    for field in payload["fields"]:
        if field["id"] == "class_rank_percent":
            field["help_text"] = "中教大規定：申請人須為於本校就讀一學期以上之在學學士班（出國時大二以上）或碩博士班學生，操行成績達 80 分以上，校內甄選採書面資料審查（40%）與面試（60%）。請檢附含班級／系所排名之歷年成績單正本。"
        if field["id"] == "language_test":
            field["options"] = ["TOEFL iBT 網路測驗（校級英語基準：CEFR B1 / 42 分以上；歐美頂尖校及雙聯須 61–85 分以上）", "IELTS 雅思國際英語測驗（校級英語基準：4.0–5.5 以上；歐美名校及雙聯須 6.0–6.5 以上）", "TOEIC 多益聽讀測驗（亞洲及部分歐洲姊妹校採認：550–785 分以上）", "JLPT 日語能力試驗（日本姊妹校依規定須通過 N1、N2 或 N3 級以上）", "TOPIK 韓國語文能力測驗（韓國姊妹校依規定須通過 TOPIK 2–4 級以上或英語組門檻）", "大陸及港澳地區姊妹校交換（免附外語能力檢定證明，以歷年成績、研修計畫書與面試評分）"]
            field["help_text"] = "依國立臺中教育大學《交換學校名額表》及當期選送學生出國研修簡章填報有效期限內之外語能力檢定證明。"
    payload.update(
        description=descriptions[template.id],
        source_url="https://oia.ntcu.edu.tw/data/3",
        source_checked_at=NTCU_SOURCE_CHECKED_AT,
        official_layout=False,
        official_form_number="選送學生出國研修申請表（含家長同意書與申請繳交資料檢核表）" if template.id == "exchange-application-data" else ("出國研修計畫書與自傳" if template.id == "study-plan" else None),
        official_file_name=None,
        official_download_url="https://oia.ntcu.edu.tw/storage/media/S3bTXueM4iWNsPOi1AOCvf58NFK9qzfTCyH4UzkR.pdf",
        default_copies=1,
        signatures=["申請學生親筆簽名", "家長（或監護人）親筆簽名蓋章", "導師（或指導教授）簽章", "系（所）主管及院長簽章"] if template.id == "exchange-application-data" else [],
        stamps=["所屬學系（所）及學院辦公室核章"] if template.id == "exchange-application-data" else [],
        stage={"predeparture-notice": "獲錄取後確認資格、配合國研處辦理姊妹校提名、入學申請與行政契約書簽署", "return-report": "返國後規定期限內繳交出國研修心得報告並配合國研處成果分享會辦理獎助金核銷", "credit-transfer": "返國後檢附正式成績單與課程大綱向系所及教務處註冊組辦理學分抵免"}.get(template.id, "備齊申請繳交資料檢核表、申請表、家長同意書、歷年含排名成績單、研修計畫書、語檢證明送交民生校區行政樓 2 樓國研處國際交流組"),
        version="116-1準備工具-2026-10-31.1",
        destinations=["國立臺中教育大學國際及兩岸事務暨研究發展處國際交流組（403454 臺中市西區民生路 140 號 民生校區行政樓 2 樓）"],
        conditional_note="此為個人準備工具；國立臺中教育大學每年分梯次辦理選送學生出國研修暨教育部學海系列計畫甄選（秋季班於前一年 12 月至次年 2 月收件、春季班於前一年 9–10 月收件）。",
    )
    return ApplicationDocumentTemplate.model_validate(payload)


def _templates_for_school(school_name: str) -> list[ApplicationDocumentTemplate]:
    university_id = require_university(school_name).id
    return [
        apply_writing_guidance(university_id, template)
        for template in _school_templates(school_name)
    ]


def _school_templates(school_name: str) -> list[ApplicationDocumentTemplate]:
    university = require_university(school_name)
    if university.id == "ccu":
        from .ccu_application_documents import ccu_application_templates

        return ccu_application_templates()
    if university.id == NCU.id:
        return [adapted for template in APPLICATION_TEMPLATES if (adapted := _ncu_template(template)) is not None]
    if university.id == FJU.id:
        return [adapted for template in APPLICATION_TEMPLATES if (adapted := _fju_template(template)) is not None]
    if university.id == SCU.id:
        return [adapted for template in APPLICATION_TEMPLATES if (adapted := _scu_template(template)) is not None]
    if university.id == NTNU.id:
        return [adapted for template in APPLICATION_TEMPLATES if (adapted := _ntnu_template(template)) is not None]
    if university.id == CYCU.id:
        return [adapted for template in APPLICATION_TEMPLATES if (adapted := _cycu_template(template)) is not None]
    if university.id == NTUST.id:
        return [adapted for template in APPLICATION_TEMPLATES if (adapted := _ntust_template(template)) is not None]
    if university.id == YZU.id:
        return [adapted for template in APPLICATION_TEMPLATES if (adapted := _yzu_template(template)) is not None]
    if university.id == FCU.id:
        return [adapted for template in APPLICATION_TEMPLATES if (adapted := _fcu_template(template)) is not None]
    if university.id == NSYSU.id:
        return [adapted for template in APPLICATION_TEMPLATES if (adapted := _nsysu_template(template)) is not None]
    if university.id == NCHU.id:
        return [adapted for template in APPLICATION_TEMPLATES if (adapted := _nchu_template(template)) is not None]
    if university.id == NTUT.id:
        return [adapted for template in APPLICATION_TEMPLATES if (adapted := _ntut_template(template)) is not None]
    if university.id == NCCU.id:
        return [adapted for template in APPLICATION_TEMPLATES if (adapted := _nccu_template(template)) is not None]
    if university.id == NCKU.id:
        return [adapted for template in APPLICATION_TEMPLATES if (adapted := _ncku_template(template)) is not None]
    if university.id == NYCU.id:
        return [adapted for template in APPLICATION_TEMPLATES if (adapted := _nycu_template(template)) is not None]
    if university.id == NTHU.id:
        return [adapted for template in APPLICATION_TEMPLATES if (adapted := _nthu_template(template)) is not None]
    if university.id == PCCU.id:
        return [adapted for template in APPLICATION_TEMPLATES if (adapted := _pccu_template(template)) is not None]
    if university.id == WZU.id:
        return [adapted for template in APPLICATION_TEMPLATES if (adapted := _wzu_template(template)) is not None]
    if university.id == NKUST.id:
        return [adapted for template in APPLICATION_TEMPLATES if (adapted := _nkust_template(template)) is not None]
    if university.id == YUNTECH.id:
        return [adapted for template in APPLICATION_TEMPLATES if (adapted := _yuntech_template(template)) is not None]
    if university.id == NTOU.id:
        return [adapted for template in APPLICATION_TEMPLATES if (adapted := _ntou_template(template)) is not None]
    if university.id == NCUE.id:
        return [adapted for template in APPLICATION_TEMPLATES if (adapted := _ncue_template(template)) is not None]
    if university.id == NKNU.id:
        return [adapted for template in APPLICATION_TEMPLATES if (adapted := _nknu_template(template)) is not None]
    if university.id == TMU.id:
        return [adapted for template in APPLICATION_TEMPLATES if (adapted := _tmu_template(template)) is not None]
    if university.id == CSMU.id:
        return [adapted for template in APPLICATION_TEMPLATES if (adapted := _csmu_template(template)) is not None]
    if university.id == CMU.id:
        return [adapted for template in APPLICATION_TEMPLATES if (adapted := _cmu_template(template)) is not None]
    if university.id == KMU.id:
        return [adapted for template in APPLICATION_TEMPLATES if (adapted := _kmu_template(template)) is not None]
    if university.id == MCU.id:
        return [adapted for template in APPLICATION_TEMPLATES if (adapted := _mcu_template(template)) is not None]
    if university.id == NTUB.id:
        return [adapted for template in APPLICATION_TEMPLATES if (adapted := _ntub_template(template)) is not None]
    if university.id == NCNU.id:
        return [adapted for template in APPLICATION_TEMPLATES if (adapted := _ncnu_template(template)) is not None]
    if university.id == NDHU.id:
        return [adapted for template in APPLICATION_TEMPLATES if (adapted := _ndhu_template(template)) is not None]
    if university.id == THU.id:
        return [adapted for template in APPLICATION_TEMPLATES if (adapted := _thu_template(template)) is not None]
    if university.id == SHU.id:
        return [adapted for template in APPLICATION_TEMPLATES if (adapted := _shu_template(template)) is not None]
    if university.id == PU.id:
        return [adapted for template in APPLICATION_TEMPLATES if (adapted := _pu_template(template)) is not None]
    if university.id == USC.id:
        return [adapted for template in APPLICATION_TEMPLATES if (adapted := _usc_template(template)) is not None]
    if university.id == NUK.id:
        return [adapted for template in APPLICATION_TEMPLATES if (adapted := _nuk_template(template)) is not None]
    if university.id == NCYU.id:
        return [adapted for template in APPLICATION_TEMPLATES if (adapted := _ncyu_template(template)) is not None]
    if university.id == NUTC.id:
        return [adapted for template in APPLICATION_TEMPLATES if (adapted := _nutc_template(template)) is not None]
    if university.id == NFU.id:
        return [adapted for template in APPLICATION_TEMPLATES if (adapted := _nfu_template(template)) is not None]
    if university.id == UTAIPEI.id:
        return [adapted for template in APPLICATION_TEMPLATES if (adapted := _utaipei_template(template)) is not None]
    if university.id == NTCU.id:
        return [adapted for template in APPLICATION_TEMPLATES if (adapted := _ntcu_template(template)) is not None]
    if university.id == "tku":
        from .tku_documents import tku_application_templates
        return tku_application_templates()
    if university.id == NTU.id:
        return [adapted for template in APPLICATION_TEMPLATES if (adapted := _ntu_template(template)) is not None]
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
    if require_university(context.school_name).id == "tku" and (
        str(context.academic_year or "").strip() not in ("", "2027-2028")
        or str(context.application_round or "").strip() not in ("", "日語組第二次甄選")
    ):
        return []
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
    requirement_sources_only = resolve_university(context.school_name) == NCU
    items: list[ApplicationDocumentCatalogItem] = []
    sequence = 0
    stages = {
        "nomination": "合作校提名",
        "student_application": "合作校申請",
        "after_application": "合作校申請後補件（不等錄取）",
        "second_submission": "合作校第二次文件送件",
        "post_offer": "合作校錄取後",
        "after_dorm_assignment": "合作校宿舍分配後",
        "conditional_program": "合作校特定計畫文件",
    }
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
                        *(step.source_urls if not requirement_sources_only or not requirement.source_urls else []),
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
                    phase=(
                        step.phase if workflow.home_university == "淡江大學"
                        or requirement.stage in {"after_application", "second_submission"}
                        else stages.get(requirement.stage, step.phase)
                    ),
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
                    stage=requirement.stage,
                    conditional=requirement.conditional,
                    condition=requirement.condition,
                    official_form_verified=requirement.official_form_verified,
                    applicability_status=requirement.applicability_status,
                    applicability_year=requirement.applicability_year,
                    applicability_note=requirement.applicability_note,
                    download_available=bool(
                        official_form_url and (
                            not needs_confirmation or (
                                workflow.home_university in {"國立中正大學", "淡江大學"}
                                and requirement.official_form_verified
                            )
                        )
                    ),
                    contact_unit=(
                        step.confirmation_contact
                        or step.responsible_unit
                        or contact_unit
                        if needs_confirmation
                        else None
                    ),
                    applicability=document_applicability(
                        context.school_name, workflow.school_name, requirement,
                        context.partner_document_states.get(preparation_state_key(
                            workflow.school_name, context.academic_year, context.application_round, context.semester,
                        )),
                    ),
                )
            )

    result = ApplicationDocumentCatalog(
        context=context,
        workflow_found=True,
        workflow_coverage_status=workflow.coverage_status,
        workflow_review_status=workflow.review_status,
        academic_year=workflow.academic_year,
        application_round=workflow.application_round,
        items=items,
        contact_unit=contact_unit,
    )
    if workflow.home_university == "國立中正大學":
        result.disclaimer = "官方文件直連只表示來源及保存檔案已核實可讀；部分連結是指引，並非申請表。流程仍未發布、清單不完整，適用年度、計畫、條件及簽章須依逐項來源核對。"
    return result


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
        language_errors = {**_ntu_language_validation(template, field_values), **_ncu_language_validation(template, field_values)}
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
                    required=application_field_required(field, field_values),
                    sensitive=field.sensitive,
                    display_value=_format_value(value),
                    is_blank=_field_is_blank(field, value),
                    validation_error=attachment_errors.get(field.id) or language_errors.get(field.id),
                )
            )
        missing = [
            field.label
            for field in template.fields
            if application_field_required(field, field_values) and not _has_field_value(field, field_values[field.id])
        ]
        missing.extend(f"{field.label}：{language_errors[field.id]}" for field in template.fields if field.id in language_errors)
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
            CCU_SOURCE_CHECKED_AT
            if require_university(request.context.school_name).id == "ccu"
            else NCU_CHECKED_AT
            if require_university(request.context.school_name).id == NCU.id
            else datetime(2026, 10, 8, tzinfo=timezone.utc)
            if require_university(request.context.school_name).id == "tku"
            else NTU_SOURCE_CHECKED_AT
            if require_university(request.context.school_name).id == NTU.id
            else NTPU_SOURCE_CHECKED_AT
            if require_university(request.context.school_name).id == NTPU.id
            else SOURCE_CHECKED_AT
        ),
    )


def _register_pdf_font(home_school: str | None = None) -> tuple[str, str]:
    if home_school and require_university(home_school).id == "tku":
        # Embed the school adapter's CJK font so Chinese/Japanese preparation
        # answers remain visible without a viewer's optional external CMaps.
        regular = "TKUPreparationCJK"
        if regular not in pdfmetrics.getRegisteredFontNames():
            from reportlab.pdfbase.ttfonts import TTFont
            font_path = Path(__file__).parent / "official_data/tku/fonts/NotoSansCJKtc-Regular.ttf"
            pdfmetrics.registerFont(TTFont(regular, str(font_path)))
        return regular, regular
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


def _styles(home_school: str | None = None) -> dict[str, ParagraphStyle]:
    regular, bold = _register_pdf_font(home_school)
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
    styles = _styles(request.context.school_name)
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
    styles = _styles(request.context.school_name)
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


def _downloadable_manifest(
    request: ApplicationPacketRequest,
    *,
    review_key: bytes | None = None,
) -> ApplicationPacketManifest:
    """Build the manifest and refuse any export the student has not finished and reviewed."""

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
    return manifest


def generate_application_packet_pdf(
    request: ApplicationPacketRequest,
    *,
    raw_files_dir: Path,
    review_key: bytes | None = None,
) -> tuple[bytes, ApplicationPacketManifest]:
    manifest = _downloadable_manifest(request, review_key=review_key)
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


_DOCX_CJK_FONT = "Microsoft JhengHei"
_DOCX_LATIN_FONT = "Calibri"
_DOCX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


@dataclass(frozen=True)
class ApplicationWordPacket:
    """Editable export: one .docx for a single document, a .zip of .docx files otherwise."""

    content: bytes
    extension: Literal["docx", "zip"]
    media_type: str
    manifest: ApplicationPacketManifest
    file_names: list[str]


def _docx_run(
    paragraph: Any,
    text: str,
    *,
    bold: bool = False,
    size: float = 10.5,
    color: str | None = None,
) -> Any:
    run = paragraph.add_run(text)
    run.bold = bold
    run.font.size = Pt(size)
    run.font.name = _DOCX_LATIN_FONT
    run._element.rPr.rFonts.set(qn("w:eastAsia"), _DOCX_CJK_FONT)
    if color:
        run.font.color.rgb = RGBColor.from_string(color)
    return run


def _docx_text(paragraph: Any, text: str, **style: Any) -> None:
    lines = str(text).splitlines() or [""]
    for index, line in enumerate(lines):
        run = _docx_run(paragraph, line, **style)
        if index < len(lines) - 1:
            run.add_break()


def _docx_paragraph(document: Any, text: str, *, space_after: float = 4, **style: Any) -> Any:
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(space_after)
    _docx_text(paragraph, text, **style)
    return paragraph


def _docx_cell(cell: Any, text: str, **style: Any) -> None:
    paragraph = cell.paragraphs[0]
    paragraph.paragraph_format.space_before = Pt(3)
    paragraph.paragraph_format.space_after = Pt(3)
    _docx_text(paragraph, text, **style)


def _docx_two_column_table(document: Any, left: float, right: float) -> Any:
    table = document.add_table(rows=0, cols=2)
    table.style = "Table Grid"
    table.autofit = False
    table.columns[0].width, table.columns[1].width = Mm(left), Mm(right)
    return table


def _docx_shade(cell: Any, fill: str) -> None:
    shading = OxmlElement("w:shd")
    shading.set(qn("w:val"), "clear")
    shading.set(qn("w:color"), "auto")
    shading.set(qn("w:fill"), fill)
    cell._tc.get_or_add_tcPr().append(shading)


def _new_docx(title: str) -> Any:
    document = Document()
    section = document.sections[0]
    section.page_width, section.page_height = Mm(210), Mm(297)
    section.left_margin = section.right_margin = Mm(18)
    section.top_margin = section.bottom_margin = Mm(18)
    normal = document.styles["Normal"]
    normal.font.name = _DOCX_LATIN_FONT
    normal.font.size = Pt(10.5)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), _DOCX_CJK_FONT)
    document.core_properties.title = title
    document.core_properties.author = "台灣大學生交換指南"
    document.core_properties.subject = "待學生核對、列印、簽名與送件的申請文件草稿"
    return document


def _generic_template_docx(
    template: ApplicationDocumentTemplate,
    request: ApplicationPacketRequest,
    copies: int,
) -> bytes:
    answers = request.answers.get(template.id, {})
    document = _new_docx(template.title)
    _docx_paragraph(document, template.title, bold=True, size=20, color="17212B", space_after=2)
    _docx_paragraph(
        document,
        f"預計列印 {copies} 份 · {template.paper_size}",
        size=8.5,
        color="3F4B57",
        space_after=8,
    )
    if not template.official_layout:
        _docx_paragraph(document, "資料整理版", bold=True, size=13, color="0A73C9", space_after=2)
        _docx_paragraph(
            document,
            "此頁依公開要求整理填寫資料；若校方另提供正式表格，請將本頁內容轉入最新版正式表格。",
            size=8.5,
            color="3F4B57",
            space_after=8,
        )
    table = _docx_two_column_table(document, 45, 125)
    for field in template.fields:
        value = answer_for_field(field, request.profile, answers)
        label_cell, value_cell = table.add_row().cells
        label_cell.width, value_cell.width = Mm(45), Mm(125)
        _docx_shade(label_cell, "F3F7FA")
        _docx_cell(label_cell, field.label, bold=True, size=9.5, color="263442")
        _docx_cell(value_cell, _format_value(value))

    pictures: list[tuple[str, bytes]] = []
    pdf_attachments: list[_AttachmentPayload] = []
    for field in _attachment_fields_in_order(template):
        payloads, _ = _attachment_payloads(field, answer_for_field(field, request.profile, answers))
        for payload in payloads:
            if payload.media_type == "application/pdf":
                pdf_attachments.append(payload)
            else:
                pictures.append((payload.file_name, payload.raw))
    if pictures:
        _docx_paragraph(document, "照片附件", bold=True, size=13, color="0A73C9", space_after=4)
        for name, raw in pictures[:8]:
            try:
                document.add_picture(io.BytesIO(raw), width=Mm(70))
            except Exception:
                continue
            _docx_paragraph(document, name, size=8.5, color="3F4B57", space_after=6)
    if pdf_attachments:
        _docx_paragraph(document, "請另行附上的 PDF 附件", bold=True, size=13, color="0A73C9", space_after=2)
        _docx_paragraph(
            document,
            "Word 檔無法內嵌 PDF，列印時請依下列順序把這些檔案接在本文件後面。",
            size=8.5,
            color="3F4B57",
        )
        for index, payload in enumerate(pdf_attachments, start=1):
            _docx_paragraph(
                document,
                f"{index}. {payload.field_label}：{payload.file_name}（{payload.page_count} 頁）",
                size=9.5,
                space_after=2,
            )
    if template.signatures or template.stamps:
        _docx_paragraph(document, "列印後完成", bold=True, size=13, color="0A73C9", space_after=4)
        actions = _docx_two_column_table(document, 65, 105)
        for kind, labels in (("簽名", template.signatures), ("核章", template.stamps)):
            for label in labels:
                row = actions.add_row()
                row.height, row.height_rule = Mm(18), WD_ROW_HEIGHT_RULE.AT_LEAST
                row.cells[0].width, row.cells[1].width = Mm(65), Mm(105)
                _docx_cell(row.cells[0], f"{kind}｜{label}", bold=True, size=9.5, color="263442")
    _docx_paragraph(document, "", space_after=2)
    _docx_paragraph(document, f"官方來源：{template.source_url}", size=8.5, color="3F4B57", space_after=2)
    _docx_paragraph(
        document,
        f"範本版本：{template.version} · 最後檢查：{template.source_checked_at.astimezone().strftime('%Y/%m/%d')}",
        size=8.5,
        color="3F4B57",
        space_after=2,
    )
    _docx_paragraph(
        document,
        "下載、列印或修改這份文件不代表已送件、校方受理或錄取；送件前請再核對官方來源。",
        size=8.5,
        color="3F4B57",
    )
    output = io.BytesIO()
    document.save(output)
    return output.getvalue()


def _official_template_docx(
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
        filled = Path(directory) / "filled.docx"
        _fill_official_docx(template, request, source, filled)
        return filled.read_bytes()


def _word_file_stem(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z一-鿿_-]+", "-", value).strip("-") or "文件"


def generate_application_packet_docx(
    request: ApplicationPacketRequest,
    *,
    raw_files_dir: Path,
    review_key: bytes | None = None,
) -> ApplicationWordPacket:
    """Editable Word export with the same completeness and review gates as the PDF packet."""

    manifest = _downloadable_manifest(request, review_key=review_key)
    applicable = {template.id: template for template in templates_for_context(request.context)}
    documents: list[tuple[str, bytes]] = []
    for index, item in enumerate(manifest.items, start=1):
        template = applicable[item.template_id]
        content = (
            _official_template_docx(template, request, raw_files_dir)
            if template.official_layout
            else None
        ) or _generic_template_docx(template, request, item.copies)
        documents.append((f"{index:02d}-{_word_file_stem(item.title)}-列印{item.copies}份.docx", content))
    if len(documents) == 1:
        name, content = documents[0]
        return ApplicationWordPacket(content, "docx", _DOCX_MEDIA_TYPE, manifest, [name])
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for name, content in documents:
            bundle.writestr(name, content)
    return ApplicationWordPacket(
        archive.getvalue(),
        "zip",
        "application/zip",
        manifest,
        [name for name, _ in documents],
    )
