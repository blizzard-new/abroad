import base64
from io import BytesIO

from fastapi.testclient import TestClient
from pypdf import PdfReader, PdfWriter

from exchange_info.api import create_app
from exchange_info.storage import ensure_data_dirs


def _study_plan_payload(copies: int = 1) -> dict[str, object]:
    return {
        "context": {
            "school_name": "長庚大學",
            "target_school": "林肯大學 Lincoln University",
            "target_country": "紐西蘭",
            "program_type": "exchange",
            "academic_year": "116",
            "semester": "第一學期",
            "flags": [],
        },
        "profile": {
            "student_name_zh": "王小明",
            "student_id": "B1234567",
            "department": "資訊管理學系",
        },
        "answers": {
            "study-plan": {
                "motivation": "希望透過交換培養跨文化合作能力。",
                "school_reason": "課程與我的學習方向相符。",
                "learning_goals": "完成專業課程並提升英文溝通能力。",
                "course_plan": "修習資料分析與跨文化管理課程。",
                "expected_outcomes": "完成課程並分享交換經驗。",
                "return_plan": "返國後完成學分採認與成果分享。",
            }
        },
        "selections": [{"template_id": "study-plan", "copies": copies}],
    }


def test_application_center_resolves_conditional_documents(tmp_path) -> None:
    data_dir = tmp_path / "data"
    ensure_data_dirs(data_dir)
    client = TestClient(create_app(data_dir))

    base = client.get(
        "/application-center/templates",
        params={"program_type": "exchange"},
    ).json()
    subsidized = client.get(
        "/application-center/templates",
        params={"program_type": "exchange", "flags": "subsidy,military_service"},
    ).json()

    assert any(row["id"] == "study-plan" for row in base)
    assert all(row["id"] != "subsidy-receipt" for row in base)
    assert any(row["id"] == "subsidy-receipt" for row in subsidized)
    assert any(row["id"] == "military-service-overseas" for row in subsidized)


def test_application_manifest_reports_missing_fields_and_print_copies(tmp_path) -> None:
    data_dir = tmp_path / "data"
    ensure_data_dirs(data_dir)
    client = TestClient(create_app(data_dir))
    payload = _study_plan_payload(copies=3)

    complete = client.post("/application-center/manifest", json=payload)
    assert complete.status_code == 200
    assert complete.json()["ready_to_generate"] is True
    assert complete.json()["total_printed_copies"] == 3

    payload["answers"]["study-plan"].pop("motivation")  # type: ignore[index]
    incomplete = client.post("/application-center/manifest", json=payload)
    assert incomplete.status_code == 200
    assert incomplete.json()["ready_to_generate"] is False
    assert "申請動機" in incomplete.json()["items"][0]["missing_required_fields"]


def test_application_center_generates_a_printable_pdf_packet(tmp_path) -> None:
    data_dir = tmp_path / "data"
    ensure_data_dirs(data_dir)
    client = TestClient(create_app(data_dir))

    response = client.post("/application-center/pdf", json=_study_plan_payload(copies=2))

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["cache-control"] == "no-store"
    assert response.content.startswith(b"%PDF")
    assert len(PdfReader(BytesIO(response.content)).pages) >= 3


def test_short_term_templates_are_tied_to_official_form_numbers(tmp_path) -> None:
    data_dir = tmp_path / "data"
    ensure_data_dirs(data_dir)
    client = TestClient(create_app(data_dir))

    templates = client.get(
        "/application-center/templates",
        params={"program_type": "short_term_credit"},
    ).json()

    official = {row["official_form_number"] for row in templates if row["official_layout"]}
    assert official == {"2B0001001", "2B0001002", "2B0001003", "2B0001004"}
    assert all(row["source_url"].startswith("https://www.cgu.edu.tw/") for row in templates)


def test_required_uploads_need_real_file_payloads_and_minimum_photo_count(tmp_path) -> None:
    data_dir = tmp_path / "data"
    ensure_data_dirs(data_dir)
    client = TestClient(create_app(data_dir))

    templates = client.get(
        "/application-center/templates",
        params={"program_type": "short_term_credit"},
    ).json()
    report = next(row for row in templates if row["id"] == "short-term-report-2b0001004")
    photo_field = next(row for row in report["fields"] if row["id"] == "activity_photos")
    assert photo_field["min_files"] == 4
    assert photo_field["max_files"] == 4

    profile: dict[str, object] = {}
    answers: dict[str, object] = {}
    png = "data:image/png;base64," + base64.b64encode(b"valid-image-payload").decode("ascii")
    for field in report["fields"]:
        if not field["required"]:
            continue
        if field["field_type"] == "files":
            value: object = [{"name": f"photo-{index}.png", "type": "image/png", "data_url": png} for index in range(3)]
        elif field["field_type"] == "date":
            value = "2026-08-01"
        elif field["field_type"] == "checkbox":
            value = True
        elif field["field_type"] == "number":
            value = 1
        elif field["field_type"] == "select":
            value = field["options"][0]
        else:
            value = "測試內容"
        if field["reusable_profile_key"]:
            profile[field["reusable_profile_key"]] = value
        else:
            answers[field["id"]] = value

    payload = {
        "context": {"school_name": "長庚大學", "program_type": "short_term_credit", "flags": []},
        "profile": profile,
        "answers": {report["id"]: answers},
        "selections": [{"template_id": report["id"], "copies": 1}],
    }
    incomplete = client.post("/application-center/manifest", json=payload)
    assert incomplete.status_code == 200
    assert "至少 4 張照片與圖說" in incomplete.json()["items"][0]["missing_required_fields"]

    answers["activity_photos"].append({"name": "photo-4.png", "type": "image/png", "data_url": png})  # type: ignore[union-attr]
    complete = client.post("/application-center/manifest", json=payload)
    assert complete.status_code == 200
    assert complete.json()["ready_to_generate"] is True


def test_uploaded_pdf_is_appended_to_each_printed_document(tmp_path) -> None:
    data_dir = tmp_path / "data"
    ensure_data_dirs(data_dir)
    client = TestClient(create_app(data_dir))
    attachment = BytesIO()
    attachment_writer = PdfWriter()
    attachment_writer.add_blank_page(width=72, height=72)
    attachment_writer.write(attachment)
    attachment_data_url = "data:application/pdf;base64," + base64.b64encode(attachment.getvalue()).decode("ascii")
    payload = {
        "context": {"school_name": "長庚大學", "program_type": "dual_degree", "flags": []},
        "profile": {
            "student_name_zh": "王小明",
            "student_id": "B1234567",
            "college": "管理學院",
            "department": "資訊管理學系",
            "degree_level": "大學部",
        },
        "answers": {
            "dual-enrollment": {
                "overseas_institution": "Partner University",
                "dual_degree_program": "Dual Degree Program",
                "planned_start_date": "2026-09-01",
                "planned_end_date": "2027-06-30",
                "admission_notice": [{"name": "admission.pdf", "type": "application/pdf", "data_url": attachment_data_url}],
            }
        },
        "selections": [{"template_id": "dual-enrollment", "copies": 2}],
    }

    response = client.post("/application-center/pdf", json=payload)

    assert response.status_code == 200
    assert len(PdfReader(BytesIO(response.content)).pages) >= 5

    payload["answers"]["dual-enrollment"]["admission_notice"] = [{"name": "admission.pdf", "type": "application/pdf"}]  # type: ignore[index]
    manifest = client.post("/application-center/manifest", json=payload)
    assert manifest.json()["ready_to_generate"] is False
