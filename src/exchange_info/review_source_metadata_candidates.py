from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .models import ApplicationWorkflowSourceMetadataResearchCandidate
from .source_url_policy import canonical_source_url_identity


SOURCE_METADATA_RESEARCH_CANDIDATES_PATH = (
    Path(__file__).resolve().parent
    / "official_data"
    / "review"
    / "source_metadata_research_candidates.json"
)


class _SourceMetadataResearchCandidateManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1]
    review_status: Literal["human_review_required"]
    publication_effect: Literal["none"]
    approvals_created: Literal[False]
    public_student_data_changed: Literal[False]
    expected_candidate_count: int = Field(ge=1)
    expected_verified_exact_source_count: int = Field(ge=0)
    expected_source_unavailable_count: int = Field(ge=0)
    items: list[ApplicationWorkflowSourceMetadataResearchCandidate] = Field(
        min_length=1
    )

    @model_validator(mode="after")
    def validate_manifest(self) -> "_SourceMetadataResearchCandidateManifest":
        if len(self.items) != self.expected_candidate_count:
            raise ValueError("來源中繼資料研究候選數量與 manifest 宣告不一致。")
        if (
            sum(item.research_status == "verified_exact_source" for item in self.items)
            != self.expected_verified_exact_source_count
        ):
            raise ValueError("已核對原始來源數量與 manifest 宣告不一致。")
        if (
            sum(item.research_status == "source_unavailable" for item in self.items)
            != self.expected_source_unavailable_count
        ):
            raise ValueError("失效來源數量與 manifest 宣告不一致。")
        source_keys = [
            canonical_source_url_identity(item.source_url) for item in self.items
        ]
        if len(source_keys) != len(set(source_keys)):
            raise ValueError("同一原網址不可重複建立來源中繼資料研究候選。")
        return self


@lru_cache(maxsize=1)
def load_source_metadata_research_candidates() -> tuple[
    ApplicationWorkflowSourceMetadataResearchCandidate, ...
]:
    manifest = _SourceMetadataResearchCandidateManifest.model_validate_json(
        SOURCE_METADATA_RESEARCH_CANDIDATES_PATH.read_text(encoding="utf-8")
    )
    return tuple(manifest.items)


def source_metadata_research_candidate_for_url(
    source_url: str,
) -> ApplicationWorkflowSourceMetadataResearchCandidate | None:
    source_key = canonical_source_url_identity(source_url)
    if not source_key:
        return None
    return next(
        (
            item
            for item in load_source_metadata_research_candidates()
            if canonical_source_url_identity(item.source_url) == source_key
        ),
        None,
    )
