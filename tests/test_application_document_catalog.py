from cgu_catalogue_fixture import fixed_cgu_catalogue
from datetime import datetime, timezone

from exchange_info.application_documents import all_application_templates
from exchange_info.models import (
    ApplicationCopyType,
    ApplicationDocumentRequirement,
    ApplicationStep,
    ApplicationSupportStatus,
    ApplicationWorkflowReviewStatus,
    PartnerUniversity,
    UniversityApplicationWorkflow,
)
from exchange_info.storage import ensure_data_dirs, replace_application_workflow
from test_application_documents_api import _authenticated_client


def _partner(school_name: str) -> PartnerUniversity:
    return PartnerUniversity(
        program_type="交換學生",
        availability_status="open",
        country="測試國家",
        school_name=school_name,
        source_url="https://example.edu/partners",
    )


def _workflow(
    home_school: str,
    school_name: str,
    *,
    review_status: ApplicationWorkflowReviewStatus,
) -> UniversityApplicationWorkflow:
    checked_at = datetime(2026, 7, 29, tzinfo=timezone.utc)
    return UniversityApplicationWorkflow(
        home_university=home_school,
        school_name=school_name,
        academic_year="116",
        application_round="第一梯次",
        review_status=review_status,
        published_at=(
            checked_at
            if review_status == ApplicationWorkflowReviewStatus.PUBLISHED
            else None
        ),
        last_checked=checked_at,
        coverage_status="official_verified",
        steps=[
            ApplicationStep(
                order=1,
                phase="校內申請",
                title="送交申請資料",
                responsible_party="學生",
                responsible_unit=f"{home_school}國際事務處",
                summary="依當期公告完成送件。",
                support_status=ApplicationSupportStatus.VERIFIED,
                checked_at=checked_at,
                source_urls=["https://example.edu/guidelines"],
                document_requirements=[
                    ApplicationDocumentRequirement(
                        name="官方申請表",
                        copies=2,
                        copy_type=ApplicationCopyType.ORIGINAL,
                        signatures=["學生親筆簽名"],
                        stamps=["系所核章"],
                        official_form_url="https://example.edu/forms/application.docx",
                        source_urls=["https://example.edu/guidelines"],
                    ),
                    ApplicationDocumentRequirement(
                        name="當期語言能力證明",
                        copy_type=ApplicationCopyType.DIGITAL,
                        source_urls=["https://example.edu/guidelines"],
                        needs_confirmation=True,
                    ),
                ],
            )
        ],
    )


def test_catalog_exposes_only_confirmed_official_form_as_download(
    tmp_path,
    monkeypatch,
) -> None:
    ensure_data_dirs(tmp_path)
    partner = _partner("測試合作校 Example University")
    replace_application_workflow(
        _workflow(
            "長庚大學",
            partner.school_name,
            review_status=ApplicationWorkflowReviewStatus.PUBLISHED,
        ),
        tmp_path,
    )
    monkeypatch.setattr('exchange_info.api.create_cgu_catalogue', fixed_cgu_catalogue(lambda: [partner]))
    client = _authenticated_client(tmp_path)

    response = client.get(
        "/application-center/catalog",
        params={
            "school": "長庚大學",
            "target_school": partner.school_name,
            "department": "資訊工程學系",
            "academic_year": "116",
            "application_round": "第一梯次",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["workflow_found"] is True
    assert payload["workflow_review_status"] == "published"
    assert payload["context"]["department"] == "資訊工程學系"
    official, unconfirmed = payload["items"]
    assert official["download_available"] is True
    assert official["official_form_url"].endswith("application.docx")
    assert official["copies"] == 2
    assert official["copy_type"] == "original"
    assert official["signatures"] == ["學生親筆簽名"]
    assert official["stamps"] == ["系所核章"]
    assert unconfirmed["download_available"] is False
    assert unconfirmed["needs_confirmation"] is True
    assert unconfirmed["contact_unit"] == "長庚大學國際事務處"


def test_unpublished_workflow_never_exposes_download_as_confirmed(
    tmp_path,
    monkeypatch,
) -> None:
    ensure_data_dirs(tmp_path)
    partner = _partner("尚待審合作校 Pending University")
    replace_application_workflow(
        _workflow(
            "國立臺北大學",
            partner.school_name,
            review_status=ApplicationWorkflowReviewStatus.LEGACY,
        ),
        tmp_path,
    )
    monkeypatch.setattr(
        "exchange_info.api.fetch_ntpu_partner_universities",
        lambda: [partner],
    )
    client = _authenticated_client(tmp_path, home_school="國立臺北大學")

    response = client.get(
        "/application-center/catalog",
        params={
            "school": "國立臺北大學",
            "target_school": partner.school_name,
            "academic_year": "116",
            "application_round": "第一梯次",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["workflow_review_status"] == "legacy"
    assert payload["items"]
    assert all(item["needs_confirmation"] for item in payload["items"])
    assert all(not item["download_available"] for item in payload["items"])


def test_cgu_official_short_term_forms_have_current_download_sources() -> None:
    templates = all_application_templates("長庚大學")
    official = [template for template in templates if template.official_layout]

    assert {template.official_form_number for template in official} == {
        "2B0001001",
        "2B0001002",
        "2B0001003",
        "2B0001004",
    }
    assert all(template.official_download_url for template in official)
    assert all(
        template.official_download_url.startswith(
            "https://www.cgu.edu.tw/regulation/ServerFile/Get/"
        )
        for template in official
    )
    assert all(template.source_checked_at.date().isoformat() == "2026-07-29" for template in official)
    assert all(
        template.official_download_url is None
        for template in all_application_templates("國立臺北大學")
    )
