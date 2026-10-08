"""CCU-specific preparation templates. Generated pages are personal worksheets.

Official CCU DOC/ODT is linked for the signed application; no CGU form layout or
return deadline is reused. Partner-side forms still need nomination-time review.
"""

from .ccu_sources import CHECKED_AT, FORM_DOC_URL, GUARDIAN_URL, GUIDELINES_URL
from .models import ApplicationDocumentTemplate, ApplicationFormField


def _field(id, label, kind="text", required=True, **kwargs):
    return ApplicationFormField(
        id=id, label=label, field_type=kind, required=required, **kwargs
    )


def ccu_application_templates():
    rows = []
    specs = [
        (
            "exchange-application-data",
            "2027春季交換申請資料整理",
            "校內申請",
            "最多3志願，校級與院級交換擇一；請下載官方申請表完成所有簽章，生成頁為個人整理工具。",
            [
                _field(
                    "student_name_zh",
                    "中文姓名",
                    reusable_profile_key="student_name_zh",
                ),
                _field(
                    "student_name_en",
                    "護照英文姓名",
                    reusable_profile_key="student_name_en",
                ),
                _field("student_id", "學號", reusable_profile_key="student_id"),
                _field("department", "系所", reusable_profile_key="department"),
                _field("academic_gpa", "歷年GPA", "number"),
                _field("academic_score", "歷年总平均", "number"),
                _field("preferences", "3個志願及各計畫名稱", "textarea"),
            ],
            FORM_DOC_URL,
        ),
        (
            "study-plan",
            "2027春季研修計畫書",
            "校內申請",
            "每個志願一份，中英皆可；自傳、讀書計畫與申請動機每項約一頁A4（簡章第4頁）。",
            [
                _field("autobiography", "自傳", "textarea"),
                _field("study_plan", "讀書計畫", "textarea"),
                _field("motivation", "申請動機", "textarea"),
            ],
            None,
        ),
        (
            "ccu-cv",
            "交換履歷表",
            "校內申請",
            "列出學經歷、社團、課外活動、才藝及專長（第4頁）。",
            [_field("cv", "履歷內容", "textarea")],
            None,
        ),
        (
            "ccu-transcripts",
            "中英文歷年成績單及在學證明",
            "校內申請",
            "正式成績單須含GPA及系／班排名、教務處認證；在學證明一份（第3頁）。",
            [
                _field(
                    "documents",
                    "中英成績單及在學證明",
                    "files",
                    min_files=3,
                    sensitive=True,
                )
            ],
            None,
        ),
        (
            "ccu-language-proof",
            "外語檢定證明",
            "校內申請",
            "兩年內有效、符合志願計畫，可彩色影本（第3頁）。",
            [_field("documents", "有效語言證明", "files", min_files=1, sensitive=True)],
            None,
        ),
        (
            "ccu-recommendation",
            "教師推薦函準備紀錄",
            "校內申請",
            "每個志願至少一封，親筆簽名及彌封處簽名，封面寫對方英文校名；北海道HUSTEP須合作校指定格式（第4頁／學校資訊第37頁）。",
            [_field("status", "推薦人及彌封紙本準備狀態", "textarea")],
            None,
        ),
        (
            "ccu-graduation-audit",
            "畢業資格審核表準備紀錄",
            "條件適用：交換學期學士班四年級",
            "交換學期為大四者需繳交；未核實當期教務處下載入口，請向教務處索取（第4頁）。",
            [_field("status", "教務處正式表單及核章準備狀態", "textarea")],
            None,
        ),
        (
            "guardian-consent",
            "家長同意書資料整理",
            "校內錄取後",
            "錄取後依通知回覆意願並交家長同意書；請下載官方格式親筆簽章。",
            [
                _field(
                    "student_name_zh",
                    "學生姓名",
                    reusable_profile_key="student_name_zh",
                ),
                _field("guardian_name", "家長姓名", sensitive=True),
            ],
            GUARDIAN_URL,
        ),
    ]
    for id, title, stage, description, fields, download in specs:
        rows.append(
            ApplicationDocumentTemplate(
                id=id,
                title=title,
                short_title=title,
                category="交換申請",
                stage=stage,
                description=description,
                fields=fields,
                source_url=GUIDELINES_URL,
                source_checked_at=CHECKED_AT,
                version="2027春季（2026-08-18）",
                program_types=["exchange"],
                destinations=["學生自存備份", "國立中正大學國際事務處"],
                official_layout=False,
                official_download_url=download,
                print_sides="confirm_official",
                print_note="請依當期官方表格及承辦指示；生成頁為個人整理工具。",
                attachment_field_order=[
                    f.id for f in fields if f.field_type == "files"
                ],
            )
        )
    return rows
