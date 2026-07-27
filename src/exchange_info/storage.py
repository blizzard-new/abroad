from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, TypeVar

from pydantic import BaseModel

from .models import (
    AccountSessionRecord,
    AnonymousIdentity,
    CollectionAudit,
    CommunityAnswer,
    CommunityBlock,
    CommunityPost,
    CommunityPostComment,
    CommunityQuestion,
    CommunityReport,
    DestinationProfile,
    DocumentChunk,
    ExchangeInfo,
    ExperienceSubmission,
    PartnerResearchRecord,
    ProcessedPage,
    PrivateConversation,
    PrivateMessage,
    PublicChatMessage,
    RawPage,
    StudentExperienceSource,
    StructuredSourceRecord,
    UniversityApplicationWorkflow,
    UserAccount,
)
from .settings import DEFAULT_DATA_DIR
from .school_identity import school_identity_key

T = TypeVar("T", bound=BaseModel)

PACKAGE_DIR = Path(__file__).resolve().parent
BUNDLED_NTPU_DIR = PACKAGE_DIR / "official_data" / "ntpu"


def _include_bundled_defaults(data_dir: Path) -> bool:
    try:
        return Path(data_dir).resolve() == Path(DEFAULT_DATA_DIR).resolve()
    except OSError:
        return Path(data_dir) == Path(DEFAULT_DATA_DIR)


def _merge_rows(
    bundled: Iterable[T],
    local: Iterable[T],
    *,
    key,
) -> list[T]:
    """Merge a tracked baseline with machine-local refreshes; local rows win."""

    merged = {key(row): row for row in bundled}
    merged.update({key(row): row for row in local})
    return list(merged.values())


def _with_explicit_destination_gaps(profile: DestinationProfile) -> DestinationProfile:
    """Keep an honest, visible answer for official details that are not public."""

    defaults = {
        "housing_summary": (
            "官方網站未公開可可靠核對的交換生住宿資訊；請以合作校最新 fact sheet、"
            "錄取通知或住宿單位通知為準。"
        ),
        "cost_summary": (
            "官方網站未公開可可靠核對的交換生生活費金額；請依最新 fact sheet、"
            "住宿型態及個人生活方式另行估算。"
        ),
        "transport_summary": (
            "官方網站未公開可可靠核對的到校交通說明；獲錄取後請依合作校行前資料"
            "及當地公共運輸官方資訊規劃。"
        ),
        "campus_life_summary": (
            "官方網站未公開足以核對的交換生校園生活資訊；請以國際處迎新通知與"
            "學生服務單位最新公告為準。"
        ),
    }
    update = {
        field: value
        for field, value in defaults.items()
        if not str(getattr(profile, field, "") or "").strip()
    }
    return profile.model_copy(update=update) if update else profile


def data_paths(data_dir: Path = DEFAULT_DATA_DIR) -> dict[str, Path]:
    data_dir = Path(data_dir)
    return {
        "raw": data_dir / "raw",
        "raw_pages": data_dir / "raw" / "pages.jsonl",
        "raw_files": data_dir / "raw_files",
        "processed": data_dir / "processed",
        "processed_pages": data_dir / "processed" / "pages.jsonl",
        "exchange_info": data_dir / "processed" / "exchange_info.json",
        "document_chunks": data_dir / "processed" / "document_chunks.jsonl",
        "structured_sources": data_dir / "processed" / "structured_sources.jsonl",
        "student_experiences": data_dir / "processed" / "student_experiences.jsonl",
        "application_workflows": data_dir / "processed" / "application_workflows.jsonl",
        "partner_research": data_dir / "processed" / "partner_research.jsonl",
        "community_questions": data_dir / "processed" / "community_questions.jsonl",
        "community_answers": data_dir / "processed" / "community_answers.jsonl",
        "community_identities": data_dir / "processed" / "community_identities.jsonl",
        "community_posts": data_dir / "processed" / "community_posts.jsonl",
        "community_post_comments": data_dir / "processed" / "community_post_comments.jsonl",
        "public_chat_messages": data_dir / "processed" / "public_chat_messages.jsonl",
        "private_conversations": data_dir / "processed" / "private_conversations.jsonl",
        "private_messages": data_dir / "processed" / "private_messages.jsonl",
        "community_blocks": data_dir / "processed" / "community_blocks.jsonl",
        "community_reports": data_dir / "processed" / "community_reports.jsonl",
        "experience_submissions": data_dir / "processed" / "experience_submissions.jsonl",
        "collection_audits": data_dir / "processed" / "collection_audits.jsonl",
        "destination_profiles": data_dir / "processed" / "destination_profiles.jsonl",
        "user_accounts": data_dir / "processed" / "user_accounts.jsonl",
        "account_sessions": data_dir / "processed" / "account_sessions.jsonl",
    }


def ensure_data_dirs(data_dir: Path = DEFAULT_DATA_DIR) -> dict[str, Path]:
    paths = data_paths(data_dir)
    paths["raw"].mkdir(parents=True, exist_ok=True)
    paths["raw_files"].mkdir(parents=True, exist_ok=True)
    paths["processed"].mkdir(parents=True, exist_ok=True)
    return paths


def write_jsonl(path: Path, rows: Iterable[BaseModel]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(row.model_dump_json() + "\n")
            count += 1
    return count


def read_jsonl(path: Path, model: type[T]) -> list[T]:
    if not path.exists():
        return []
    rows: list[T] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(model.model_validate_json(line))
    return rows


def save_json(path: Path, row: BaseModel) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(row.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_raw_pages(data_dir: Path = DEFAULT_DATA_DIR) -> list[RawPage]:
    return read_jsonl(data_paths(data_dir)["raw_pages"], RawPage)


def save_raw_pages(rows: Iterable[RawPage], data_dir: Path = DEFAULT_DATA_DIR) -> int:
    return write_jsonl(data_paths(data_dir)["raw_pages"], rows)


def load_processed_pages(data_dir: Path = DEFAULT_DATA_DIR) -> list[ProcessedPage]:
    return read_jsonl(data_paths(data_dir)["processed_pages"], ProcessedPage)


def save_processed_pages(
    rows: Iterable[ProcessedPage], data_dir: Path = DEFAULT_DATA_DIR
) -> int:
    return write_jsonl(data_paths(data_dir)["processed_pages"], rows)


def load_document_chunks(data_dir: Path = DEFAULT_DATA_DIR) -> list[DocumentChunk]:
    return read_jsonl(data_paths(data_dir)["document_chunks"], DocumentChunk)


def save_document_chunks(
    rows: Iterable[DocumentChunk], data_dir: Path = DEFAULT_DATA_DIR
) -> int:
    return write_jsonl(data_paths(data_dir)["document_chunks"], rows)


def load_structured_sources(
    data_dir: Path = DEFAULT_DATA_DIR,
) -> list[StructuredSourceRecord]:
    return read_jsonl(data_paths(data_dir)["structured_sources"], StructuredSourceRecord)


def save_structured_sources(
    rows: Iterable[StructuredSourceRecord], data_dir: Path = DEFAULT_DATA_DIR
) -> int:
    return write_jsonl(data_paths(data_dir)["structured_sources"], rows)


def load_exchange_info(data_dir: Path = DEFAULT_DATA_DIR) -> ExchangeInfo | None:
    path = data_paths(data_dir)["exchange_info"]
    if not path.exists():
        return None
    return ExchangeInfo.model_validate_json(path.read_text(encoding="utf-8"))


def save_exchange_info(
    info: ExchangeInfo, data_dir: Path = DEFAULT_DATA_DIR
) -> ExchangeInfo:
    save_json(data_paths(data_dir)["exchange_info"], info)
    return info


def load_student_experiences(
    data_dir: Path = DEFAULT_DATA_DIR,
) -> list[StudentExperienceSource]:
    return read_jsonl(data_paths(data_dir)["student_experiences"], StudentExperienceSource)


def save_student_experiences(
    rows: Iterable[StudentExperienceSource], data_dir: Path = DEFAULT_DATA_DIR
) -> int:
    return write_jsonl(data_paths(data_dir)["student_experiences"], rows)


def merge_student_experiences(
    rows: Iterable[StudentExperienceSource], data_dir: Path = DEFAULT_DATA_DIR
) -> list[StudentExperienceSource]:
    merged = {row.content_hash: row for row in load_student_experiences(data_dir)}
    for row in rows:
        merged[row.content_hash] = row
    ordered = sorted(
        merged.values(),
        key=lambda row: (row.school_name, row.discovered_at),
        reverse=True,
    )
    save_student_experiences(ordered, data_dir)
    return ordered


def replace_school_experiences(
    school_name: str,
    rows: Iterable[StudentExperienceSource],
    data_dir: Path = DEFAULT_DATA_DIR,
) -> list[StudentExperienceSource]:
    school_key = school_identity_key(school_name)
    replacement = {row.content_hash: row for row in rows}
    replacement_hashes = set(replacement)
    retained = [
        row
        for row in load_student_experiences(data_dir)
        if school_identity_key(row.school_name) != school_key
        and row.content_hash not in replacement_hashes
    ]
    ordered = sorted(
        [*retained, *replacement.values()],
        key=lambda row: (row.school_name, row.discovered_at),
        reverse=True,
    )
    save_student_experiences(ordered, data_dir)
    return ordered


def load_application_workflows(
    data_dir: Path = DEFAULT_DATA_DIR,
) -> list[UniversityApplicationWorkflow]:
    local = read_jsonl(
        data_paths(data_dir)["application_workflows"], UniversityApplicationWorkflow
    )
    if not _include_bundled_defaults(data_dir):
        return local
    bundled = read_jsonl(
        BUNDLED_NTPU_DIR / "application_workflows.jsonl",
        UniversityApplicationWorkflow,
    )
    return _merge_rows(
        bundled,
        local,
        key=lambda row: (
            school_identity_key(row.home_university),
            school_identity_key(row.school_name),
        ),
    )


def save_application_workflows(
    rows: Iterable[UniversityApplicationWorkflow],
    data_dir: Path = DEFAULT_DATA_DIR,
) -> int:
    return write_jsonl(data_paths(data_dir)["application_workflows"], rows)


def replace_application_workflow(
    workflow: UniversityApplicationWorkflow,
    data_dir: Path = DEFAULT_DATA_DIR,
) -> list[UniversityApplicationWorkflow]:
    school_key = school_identity_key(workflow.school_name)
    home_key = school_identity_key(workflow.home_university)
    retained = [
        row
        for row in load_application_workflows(data_dir)
        if (
            school_identity_key(row.school_name),
            school_identity_key(row.home_university),
        )
        != (school_key, home_key)
    ]
    ordered = sorted(
        [*retained, workflow],
        key=lambda row: (row.home_university.casefold(), row.school_name.casefold()),
    )
    save_application_workflows(ordered, data_dir)
    return ordered


def load_collection_audits(
    data_dir: Path = DEFAULT_DATA_DIR,
) -> list[CollectionAudit]:
    return read_jsonl(data_paths(data_dir)["collection_audits"], CollectionAudit)


def save_collection_audits(
    rows: Iterable[CollectionAudit], data_dir: Path = DEFAULT_DATA_DIR
) -> int:
    return write_jsonl(data_paths(data_dir)["collection_audits"], rows)


def upsert_collection_audit(
    audit: CollectionAudit, data_dir: Path = DEFAULT_DATA_DIR
) -> list[CollectionAudit]:
    school_key = school_identity_key(audit.school_name)
    collector_key = audit.collector.strip().casefold()
    home_key = school_identity_key(audit.home_university or "")
    retained = [
        row
        for row in load_collection_audits(data_dir)
        if (
            school_identity_key(row.school_name),
            row.collector.strip().casefold(),
            school_identity_key(row.home_university or ""),
        )
        != (school_key, collector_key, home_key)
    ]
    ordered = sorted(
        [*retained, audit],
        key=lambda row: (
            (row.home_university or "").casefold(),
            row.collector.casefold(),
            row.school_name.casefold(),
        ),
    )
    save_collection_audits(ordered, data_dir)
    return ordered


def load_destination_profiles(
    data_dir: Path = DEFAULT_DATA_DIR,
) -> list[DestinationProfile]:
    local = read_jsonl(
        data_paths(data_dir)["destination_profiles"], DestinationProfile
    )
    if not _include_bundled_defaults(data_dir):
        return local
    bundled = read_jsonl(
        BUNDLED_NTPU_DIR / "destination_profiles.jsonl", DestinationProfile
    )
    return [
        _with_explicit_destination_gaps(row)
        for row in _merge_rows(
        bundled,
        local,
        key=lambda row: school_identity_key(row.school_name),
        )
    ]


def load_partner_research(
    data_dir: Path = DEFAULT_DATA_DIR,
) -> list[PartnerResearchRecord]:
    local = read_jsonl(
        data_paths(data_dir)["partner_research"], PartnerResearchRecord
    )
    if not _include_bundled_defaults(data_dir):
        return local
    bundled = read_jsonl(
        BUNDLED_NTPU_DIR / "partner_research.jsonl", PartnerResearchRecord
    )
    return _merge_rows(
        bundled,
        local,
        key=lambda row: (
            school_identity_key(row.home_university),
            school_identity_key(row.school_name),
        ),
    )


def save_partner_research(
    rows: Iterable[PartnerResearchRecord], data_dir: Path = DEFAULT_DATA_DIR
) -> int:
    return write_jsonl(data_paths(data_dir)["partner_research"], rows)


def upsert_partner_research(
    record: PartnerResearchRecord, data_dir: Path = DEFAULT_DATA_DIR
) -> list[PartnerResearchRecord]:
    school_key = school_identity_key(record.school_name)
    home_key = school_identity_key(record.home_university)
    retained = [
        row
        for row in load_partner_research(data_dir)
        if (
            school_identity_key(row.school_name),
            school_identity_key(row.home_university),
        )
        != (school_key, home_key)
    ]
    ordered = sorted(
        [*retained, record],
        key=lambda row: (row.home_university.casefold(), row.school_name.casefold()),
    )
    save_partner_research(ordered, data_dir)
    return ordered


def save_destination_profiles(
    rows: Iterable[DestinationProfile], data_dir: Path = DEFAULT_DATA_DIR
) -> int:
    return write_jsonl(data_paths(data_dir)["destination_profiles"], rows)


def upsert_destination_profile(
    profile: DestinationProfile, data_dir: Path = DEFAULT_DATA_DIR
) -> list[DestinationProfile]:
    school_key = school_identity_key(profile.school_name)
    retained = [
        row
        for row in load_destination_profiles(data_dir)
        if school_identity_key(row.school_name) != school_key
    ]
    ordered = sorted(
        [*retained, profile],
        key=lambda row: row.school_name.casefold(),
    )
    save_destination_profiles(ordered, data_dir)
    return ordered


def load_community_questions(
    data_dir: Path = DEFAULT_DATA_DIR,
) -> list[CommunityQuestion]:
    return read_jsonl(data_paths(data_dir)["community_questions"], CommunityQuestion)


def save_community_questions(
    rows: Iterable[CommunityQuestion], data_dir: Path = DEFAULT_DATA_DIR
) -> int:
    return write_jsonl(data_paths(data_dir)["community_questions"], rows)


def append_community_question(
    question: CommunityQuestion, data_dir: Path = DEFAULT_DATA_DIR
) -> CommunityQuestion:
    rows = [*load_community_questions(data_dir), question]
    save_community_questions(rows, data_dir)
    return question


def load_community_answers(
    data_dir: Path = DEFAULT_DATA_DIR,
) -> list[CommunityAnswer]:
    return read_jsonl(data_paths(data_dir)["community_answers"], CommunityAnswer)


def save_community_answers(
    rows: Iterable[CommunityAnswer], data_dir: Path = DEFAULT_DATA_DIR
) -> int:
    return write_jsonl(data_paths(data_dir)["community_answers"], rows)


def append_community_answer(
    answer: CommunityAnswer, data_dir: Path = DEFAULT_DATA_DIR
) -> CommunityAnswer:
    rows = [*load_community_answers(data_dir), answer]
    save_community_answers(rows, data_dir)
    return answer


def _append_row(path_key: str, row: T, model: type[T], data_dir: Path) -> T:
    path = data_paths(data_dir)[path_key]
    rows = read_jsonl(path, model)
    write_jsonl(path, [*rows, row])
    return row


def load_anonymous_identities(data_dir: Path = DEFAULT_DATA_DIR) -> list[AnonymousIdentity]:
    return read_jsonl(data_paths(data_dir)["community_identities"], AnonymousIdentity)


def save_anonymous_identities(
    rows: Iterable[AnonymousIdentity], data_dir: Path = DEFAULT_DATA_DIR
) -> int:
    return write_jsonl(data_paths(data_dir)["community_identities"], rows)


def append_anonymous_identity(identity: AnonymousIdentity, data_dir: Path = DEFAULT_DATA_DIR) -> AnonymousIdentity:
    return _append_row("community_identities", identity, AnonymousIdentity, data_dir)


def load_user_accounts(data_dir: Path = DEFAULT_DATA_DIR) -> list[UserAccount]:
    return read_jsonl(data_paths(data_dir)["user_accounts"], UserAccount)


def save_user_accounts(
    rows: Iterable[UserAccount], data_dir: Path = DEFAULT_DATA_DIR
) -> int:
    return write_jsonl(data_paths(data_dir)["user_accounts"], rows)


def load_account_sessions(
    data_dir: Path = DEFAULT_DATA_DIR,
) -> list[AccountSessionRecord]:
    return read_jsonl(data_paths(data_dir)["account_sessions"], AccountSessionRecord)


def save_account_sessions(
    rows: Iterable[AccountSessionRecord], data_dir: Path = DEFAULT_DATA_DIR
) -> int:
    return write_jsonl(data_paths(data_dir)["account_sessions"], rows)


def load_community_posts(data_dir: Path = DEFAULT_DATA_DIR) -> list[CommunityPost]:
    return read_jsonl(data_paths(data_dir)["community_posts"], CommunityPost)


def append_community_post(post: CommunityPost, data_dir: Path = DEFAULT_DATA_DIR) -> CommunityPost:
    return _append_row("community_posts", post, CommunityPost, data_dir)


def load_community_post_comments(data_dir: Path = DEFAULT_DATA_DIR) -> list[CommunityPostComment]:
    return read_jsonl(data_paths(data_dir)["community_post_comments"], CommunityPostComment)


def append_community_post_comment(comment: CommunityPostComment, data_dir: Path = DEFAULT_DATA_DIR) -> CommunityPostComment:
    return _append_row("community_post_comments", comment, CommunityPostComment, data_dir)


def load_public_chat_messages(data_dir: Path = DEFAULT_DATA_DIR) -> list[PublicChatMessage]:
    return read_jsonl(data_paths(data_dir)["public_chat_messages"], PublicChatMessage)


def append_public_chat_message(message: PublicChatMessage, data_dir: Path = DEFAULT_DATA_DIR) -> PublicChatMessage:
    return _append_row("public_chat_messages", message, PublicChatMessage, data_dir)


def load_private_conversations(data_dir: Path = DEFAULT_DATA_DIR) -> list[PrivateConversation]:
    return read_jsonl(data_paths(data_dir)["private_conversations"], PrivateConversation)


def save_private_conversations(rows: Iterable[PrivateConversation], data_dir: Path = DEFAULT_DATA_DIR) -> int:
    return write_jsonl(data_paths(data_dir)["private_conversations"], rows)


def append_private_conversation(conversation: PrivateConversation, data_dir: Path = DEFAULT_DATA_DIR) -> PrivateConversation:
    return _append_row("private_conversations", conversation, PrivateConversation, data_dir)


def load_private_messages(data_dir: Path = DEFAULT_DATA_DIR) -> list[PrivateMessage]:
    return read_jsonl(data_paths(data_dir)["private_messages"], PrivateMessage)


def append_private_message(message: PrivateMessage, data_dir: Path = DEFAULT_DATA_DIR) -> PrivateMessage:
    return _append_row("private_messages", message, PrivateMessage, data_dir)


def load_community_blocks(data_dir: Path = DEFAULT_DATA_DIR) -> list[CommunityBlock]:
    return read_jsonl(data_paths(data_dir)["community_blocks"], CommunityBlock)


def append_community_block(block: CommunityBlock, data_dir: Path = DEFAULT_DATA_DIR) -> CommunityBlock:
    return _append_row("community_blocks", block, CommunityBlock, data_dir)


def append_community_report(report: CommunityReport, data_dir: Path = DEFAULT_DATA_DIR) -> CommunityReport:
    return _append_row("community_reports", report, CommunityReport, data_dir)


def load_experience_submissions(
    data_dir: Path = DEFAULT_DATA_DIR,
) -> list[ExperienceSubmission]:
    return read_jsonl(
        data_paths(data_dir)["experience_submissions"], ExperienceSubmission
    )


def save_experience_submissions(
    rows: Iterable[ExperienceSubmission], data_dir: Path = DEFAULT_DATA_DIR
) -> int:
    return write_jsonl(data_paths(data_dir)["experience_submissions"], rows)


def append_experience_submission(
    submission: ExperienceSubmission, data_dir: Path = DEFAULT_DATA_DIR
) -> ExperienceSubmission:
    rows = [*load_experience_submissions(data_dir), submission]
    save_experience_submissions(rows, data_dir)
    return submission
