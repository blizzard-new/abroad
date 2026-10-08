"""Explicit NCU reference-document conditions; never infer rules from prose."""
from __future__ import annotations

import json
from pathlib import Path

from .models import DocumentApplicability, PartnerDocumentPreparationState
from .ncu_eligibility import is_ncu
from .school_identity import same_school

POLICIES = Path(__file__).parent / "official_data/ncu/document-conditions.json"


def preparation_state_key(school_name, academic_year=None, application_round=None, semester=None):
    return json.dumps([school_name, academic_year or "", application_round or "", semester or ""], ensure_ascii=False, separators=(",", ":"))


def document_applicability(home_university, partner_university, requirement, state=None):
    if not is_ncu(home_university):
        return None
    policies = json.loads(POLICIES.read_text(encoding="utf-8"))
    policy = next((p for p in policies if same_school(p["school_name"], partner_university)
                   and p["requirement_name"] == requirement.name), None)
    if policy is None:
        return None
    state = state or PartnerDocumentPreparationState()
    if policy["requires_on_campus_housing"] and state.housing_choice == "off_campus":
        status, reason = "not_applicable", "已選校外住宿；這項校內宿舍文件不適用。"
    elif state.host_admission_status == "not_accepted":
        status, reason = "deferred", "尚未取得外校錄取；錄取後再依接收通知準備，暫不列初次申請必繳。"
    elif state.host_admission_status == "unknown":
        status, reason = "needs_confirmation", "外校錄取狀態未知，先確認錄取階段。"
    elif policy["requires_on_campus_housing"] and state.housing_choice == "unknown":
        status, reason = "needs_confirmation", "已取得外校錄取，住宿選擇未知；先確認是否住校內宿舍。"
    else:
        status, reason = "applicable", "已符合這份參考文件的錄取／住宿條件，可依接收通知準備。"
    return DocumentApplicability(
        requirement_name=requirement.name,
        status=status,
        note=f"{reason} {policy['scope_note']} 116當期來源適用性仍待核實，條件符合不代表當期必繳已核准。",
        source_urls=policy["source_urls"],
    )
