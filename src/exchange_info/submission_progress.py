from __future__ import annotations

from .models import (
    AccountSubmissionProgress,
    ApplicationSubmissionMethod,
    SubmissionProgressTransitionRequest,
    utc_now,
)


_PAPER_METHODS = {
    ApplicationSubmissionMethod.PAPER,
    ApplicationSubmissionMethod.MIXED,
}

_CONTEXT_FIELDS = (
    "title",
    "responsible_unit",
    "send_by_at",
    "arrival_deadline_at",
    "note",
)


def _submission_context(
    current: AccountSubmissionProgress | None,
    request: SubmissionProgressTransitionRequest,
) -> dict[str, object]:
    if current is None:
        return {field: getattr(request, field) for field in _CONTEXT_FIELDS}

    changed_fields = [
        field
        for field in _CONTEXT_FIELDS
        if getattr(current, field) != getattr(request, field)
    ]
    if changed_fields:
        raise ValueError(
            "送件規定已和開始記錄時不同，請重新載入官方流程後再操作。"
        )
    return {field: getattr(current, field) for field in _CONTEXT_FIELDS}


def transition_submission_progress(
    current: AccountSubmissionProgress | None,
    request: SubmissionProgressTransitionRequest,
) -> AccountSubmissionProgress:
    if request.method == ApplicationSubmissionMethod.UNKNOWN:
        raise ValueError("送件方式仍待確認，暫時不能記錄完成進度。")
    if current is not None and current.method != request.method:
        raise ValueError("送件方式已變更，請先撤銷舊進度再重新開始。")
    if current is None and request.action != "start":
        raise ValueError("這個送件步驟尚未開始，請先標記為準備中。")
    if request.action != "confirm_receipt" and request.proof_metadata is not None:
        raise ValueError("收件證明只能在確認收件時記錄。")

    progress = current or AccountSubmissionProgress(
        title=request.title,
        method=request.method,
    )
    now = utc_now()
    common = {
        **_submission_context(current, request),
        "recorded_by": "student",
        "platform_submitted": False,
        "updated_at": now,
    }

    if request.action == "start":
        if progress.status != "not_started":
            raise ValueError("只有尚未開始的送件步驟可以開始準備。")
        return progress.model_copy(
            update={**common, "status": "preparing", "started_at": now}
        )

    if request.action == "submit":
        if progress.status != "preparing":
            raise ValueError("請先標記為準備中，才能記錄已送出。")
        return progress.model_copy(
            update={**common, "status": "submitted", "submitted_at": now}
        )

    if request.action == "confirm_receipt":
        if progress.status != "submitted":
            raise ValueError("只有已送出的步驟可以確認收件。")
        if request.proof_metadata is None:
            raise ValueError("確認收件時至少要記錄一種收件證明 metadata。")
        proof_metadata = request.proof_metadata.model_copy(
            update={
                "reference": (
                    request.proof_metadata.reference.strip()
                    if request.proof_metadata.reference
                    else None
                ),
                "file_name": (
                    request.proof_metadata.file_name.strip()
                    if request.proof_metadata.file_name
                    else None
                ),
                "content_type": (
                    request.proof_metadata.content_type.strip().lower()
                    if request.proof_metadata.content_type
                    else None
                ),
                "source": "student_reported",
                "original_file_stored": False,
                "recorded_at": now,
            }
        )
        return progress.model_copy(
            update={
                **common,
                "status": "receipt_confirmed",
                "proof_metadata": proof_metadata,
                "receipt_confirmed_at": now,
            }
        )

    if request.action == "complete":
        can_complete = progress.status == "receipt_confirmed" or (
            progress.status == "submitted" and progress.method not in _PAPER_METHODS
        )
        if not can_complete:
            if progress.method in _PAPER_METHODS and progress.status == "submitted":
                raise ValueError("紙本或混合送件必須先確認已送達，不能只以寄出日標記完成。")
            raise ValueError("目前狀態還不能標記完成。")
        return progress.model_copy(
            update={**common, "status": "completed", "completed_at": now}
        )

    if request.action == "revert":
        if progress.status == "completed":
            previous = (
                "receipt_confirmed"
                if progress.receipt_confirmed_at or progress.proof_metadata
                else "submitted"
            )
            return progress.model_copy(
                update={**common, "status": previous, "completed_at": None}
            )
        if progress.status == "receipt_confirmed":
            return progress.model_copy(
                update={
                    **common,
                    "status": "submitted",
                    "proof_metadata": None,
                    "receipt_confirmed_at": None,
                    "completed_at": None,
                }
            )
        if progress.status == "submitted":
            return progress.model_copy(
                update={
                    **common,
                    "status": "preparing",
                    "submitted_at": None,
                    "proof_metadata": None,
                    "receipt_confirmed_at": None,
                    "completed_at": None,
                }
            )
        if progress.status == "preparing":
            return progress.model_copy(
                update={
                    **common,
                    "status": "not_started",
                    "started_at": None,
                    "submitted_at": None,
                    "proof_metadata": None,
                    "receipt_confirmed_at": None,
                    "completed_at": None,
                }
            )
        raise ValueError("尚未開始的送件步驟沒有可撤銷的進度。")

    raise ValueError("不支援的送件進度操作。")
