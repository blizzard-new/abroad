from __future__ import annotations

from dataclasses import asdict
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from PIL import Image

from exchange_info.api import create_app
from exchange_info.student_verification import (
    StudentCardVerification,
    StudentCardVerificationError,
    verify_student_cards,
)


def _card_image(color: tuple[int, int, int]) -> bytes:
    stream = BytesIO()
    Image.new("RGB", (900, 560), color).save(stream, format="JPEG")
    return stream.getvalue()


def _register(client: TestClient, email: str) -> dict:
    dispatched = client.post(
        "/auth/email-verification/request",
        json={"email": email},
    )
    assert dispatched.status_code == 202
    code = dispatched.json()["development_code"]
    confirmed = client.post(
        "/auth/email-verification/confirm",
        json={"email": email, "code": code},
    )
    assert confirmed.status_code == 200
    registered = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "correct-horse-2026",
            "display_name": "準備交換的學生",
            "email_verification_token": confirmed.json()["verification_token"],
            "accept_terms": True,
        },
    )
    assert registered.status_code == 201
    return registered.json()


def _headers(session: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {session['access_token']}"}


def _verification_request(
    client: TestClient,
    headers: dict[str, str],
    *,
    front: bytes = b"front-student-card-sentinel",
    back: bytes = b"back-student-card-sentinel",
):
    return client.post(
        "/auth/student-verification",
        headers=headers,
        data={"school_name": "長庚大學", "consent": "true"},
        files={
            "front": ("front.jpg", front, "image/jpeg"),
            "back": ("back.jpg", back, "image/jpeg"),
        },
    )


def _disk_snapshot(data_dir: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(data_dir)): path.read_bytes()
        for path in data_dir.rglob("*")
        if path.is_file()
    }


def test_card_ocr_returns_only_canonical_department() -> None:
    front_ocr = "長庚大學\n姓名 王小明\n學號 B12345678\n資訊工程學系\n學生證"
    back_ocr = "STUDENT CARD\nVALID 2026"
    with patch(
        "exchange_info.student_verification._ocr",
        side_effect=[front_ocr, back_ocr],
    ):
        result = verify_student_cards(
            _card_image((230, 238, 246)),
            _card_image((80, 100, 120)),
            expected_school="長庚大學",
            school_signals=("長庚大學",),
        )

    assert result.department_name == "資訊工程學系"
    assert "學系可辨識" in result.checks
    retained = repr(asdict(result))
    assert "王小明" not in retained
    assert "B12345678" not in retained
    assert front_ocr not in retained


def test_ambiguous_card_ocr_keeps_school_only() -> None:
    with patch(
        "exchange_info.student_verification._ocr",
        side_effect=["長庚大學\n學生證\n姓名 王小明", "STUDENT CARD\nVALID 2026"],
    ):
        result = verify_student_cards(
            _card_image((230, 238, 246)),
            _card_image((80, 100, 120)),
            expected_school="長庚大學",
            school_signals=("長庚大學",),
        )

    assert result.department_name is None
    assert "學系可辨識" not in result.checks


def test_success_persists_only_minimal_verification_fields(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))
    session = _register(client, "privacy-success@example.com")
    headers = _headers(session)
    front = b"FRONT_IMAGE_SENTINEL Wang-Xiao-Ming B12345678 OCR-FULL-TEXT"
    back = b"BACK_IMAGE_SENTINEL PRIVATE-CARD-DATA"
    verification = StudentCardVerification(
        school_name="長庚大學",
        department_name="資訊工程學系",
        checks=("正反面不同", "校名可辨識", "學系可辨識"),
    )
    with patch("exchange_info.api.verify_student_cards", return_value=verification):
        requested = _verification_request(
            client,
            headers,
            front=front,
            back=back,
        )

    assert requested.status_code == 201
    payload = requested.json()
    assert payload["images_retained"] is False
    assert payload["ocr_text_retained"] is False
    assert payload["student_number_retained"] is False
    assert payload["verification_method"] == "student_card"
    assert payload["department_name"] == "資訊工程學系"

    confirmed = client.post(
        "/auth/student-verification/confirm",
        headers=headers,
        json={"verification_token": payload["verification_token"]},
    )
    assert confirmed.status_code == 200
    profile = confirmed.json()
    assert profile["verified_university"] == "長庚大學"
    assert profile["verified_department"] == "資訊工程學系"
    assert profile["student_verification_method"] == "student_card"
    assert profile["student_verified_at"]

    persisted = b"\n".join(_disk_snapshot(tmp_path).values())
    for secret in (
        front,
        back,
        b"Wang-Xiao-Ming",
        b"B12345678",
        b"OCR-FULL-TEXT",
        b"PRIVATE-CARD-DATA",
    ):
        assert secret not in persisted
    account_file = (tmp_path / "processed" / "user_accounts.jsonl").read_text(
        encoding="utf-8"
    )
    assert '"verified_university":"長庚大學"' in account_file
    assert '"verified_department":"資訊工程學系"' in account_file
    assert '"student_verification_method":"student_card"' in account_file
    assert "正反面不同" not in account_file


def test_failed_verification_leaves_no_new_files_or_card_data(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))
    session = _register(client, "privacy-failure@example.com")
    headers = _headers(session)
    before = _disk_snapshot(tmp_path)
    front = b"FAILED_FRONT_IMAGE_SENTINEL B87654321"
    back = b"FAILED_BACK_IMAGE_SENTINEL OCR-PRIVATE"
    with patch(
        "exchange_info.api.verify_student_cards",
        side_effect=StudentCardVerificationError("無法辨識學生證"),
    ):
        response = _verification_request(
            client,
            headers,
            front=front,
            back=back,
        )

    assert response.status_code == 422
    after = _disk_snapshot(tmp_path)
    assert after == before
    persisted = b"\n".join(after.values())
    assert front not in persisted
    assert back not in persisted


def test_verification_token_is_bound_to_issuing_account(tmp_path: Path) -> None:
    app = create_app(tmp_path)
    owner_client = TestClient(app)
    attacker_client = TestClient(app)
    owner = _register(owner_client, "verification-owner@example.com")
    attacker = _register(attacker_client, "verification-attacker@example.com")
    verification = StudentCardVerification(
        school_name="長庚大學",
        checks=("正反面不同", "校名可辨識"),
    )
    with patch("exchange_info.api.verify_student_cards", return_value=verification):
        requested = _verification_request(owner_client, _headers(owner))
    assert requested.status_code == 201
    token = requested.json()["verification_token"]

    stolen = attacker_client.post(
        "/auth/student-verification/confirm",
        headers=_headers(attacker),
        json={"verification_token": token},
    )
    assert stolen.status_code == 403
    assert "不屬於目前登入帳號" in stolen.json()["detail"]

    owner_confirmation = owner_client.post(
        "/auth/student-verification/confirm",
        headers=_headers(owner),
        json={"verification_token": token},
    )
    assert owner_confirmation.status_code == 200
    assert owner_confirmation.json()["student_status_verified"] is True


def test_deleting_account_revokes_outstanding_verification_token(tmp_path: Path) -> None:
    app = create_app(tmp_path)
    owner_client = TestClient(app)
    other_client = TestClient(app)
    owner = _register(owner_client, "verification-delete@example.com")
    other = _register(other_client, "verification-other@example.com")
    verification = StudentCardVerification(
        school_name="長庚大學",
        checks=("正反面不同", "校名可辨識"),
    )
    with patch("exchange_info.api.verify_student_cards", return_value=verification):
        requested = _verification_request(owner_client, _headers(owner))
    token = requested.json()["verification_token"]

    deleted = owner_client.delete("/auth/me", headers=_headers(owner))
    assert deleted.status_code == 204
    revoked = other_client.post(
        "/auth/student-verification/confirm",
        headers=_headers(other),
        json={"verification_token": token},
    )
    assert revoked.status_code == 403
    assert "已失效" in revoked.json()["detail"]
