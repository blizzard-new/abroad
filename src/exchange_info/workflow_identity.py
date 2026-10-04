from __future__ import annotations

import hashlib

from .models import UniversityApplicationWorkflow
from .school_identity import school_identity_key


def workflow_storage_key(workflow: UniversityApplicationWorkflow) -> str:
    """Return the immutable governance identity for one current workflow stream."""

    if workflow.governance_key:
        return workflow.governance_key
    identity = "|".join(
        (
            school_identity_key(workflow.home_university),
            school_identity_key(workflow.school_name),
            _normal(workflow.program_type),
            _normal(workflow.academic_year),
            _normal(workflow.application_round),
        )
    )
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()[:32]


def _normal(value: object) -> str:
    return " ".join(str(value or "").strip().casefold().split())
