from __future__ import annotations

import json
import os
import tempfile
import threading
from concurrent.futures import Future
from functools import wraps
from inspect import signature
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Generator, Iterable, TextIO, TypeVar

from pydantic import BaseModel

from .models import (
    AccountNotification,
    AccountSessionRecord,
    AnonymousIdentity,
    CollectionAudit,
    CommunityAnswer,
    CommunityBlock,
    CommunityModerationAudit,
    CommunityPost,
    CommunityPostComment,
    CommunityPublishEvent,
    CommunityQuestion,
    CommunityReport,
    DestinationProfile,
    DocumentChunk,
    EmailVerificationChallenge,
    ExchangeInfo,
    ExperienceSubmission,
    NotificationDelivery,
    PartnerResearchRecord,
    ProcessedPage,
    PrivateConversation,
    PrivateMessage,
    PublicChatMessage,
    RawPage,
    StudentExperienceSource,
    StructuredSourceRecord,
    ApplicationWorkflowRevision,
    ApplicationFormDraftRecord,
    UniversityApplicationWorkflow,
    UserAccount,
    VaultAuditRecord,
    VaultConsentRecord,
    VaultDocumentRecord,
    VaultDocumentVersionRecord,
)
from .settings import DEFAULT_DATA_DIR
from .school_identity import school_identity_key, school_program_identity_key
from .university_registry import CCU, CGU, CMU, CSMU, CYCU, FCU, FJU, KMU, MCU, NCCU, NCHU, NCKU, NCNU, NCUE, NCUT, NCYU, NDHU, NFU, NKNU, NKUST, NPUST, NQU, NSYSU, NTHU, NTNU, NTOU, NTPU, NTU, NTUB, NTUE, NUTC, NTUST, NTUT, NCU, NUK, NYCU, PCCU, PU, SCU, SHU, THU, TKU, TMU, USC, UTAIPEI, NTCU, TNUA, NTUA, WZU, YUNTECH, YZU
from .workflow_structuring import structure_application_workflow
from .workflow_identity import workflow_storage_key

T = TypeVar("T", bound=BaseModel)

PACKAGE_DIR = Path(__file__).resolve().parent
BUNDLED_NTPU_DIR = PACKAGE_DIR / "official_data" / "ntpu"
BUNDLED_TKU_DIR = PACKAGE_DIR / "official_data" / "tku"
BUNDLED_CGU_DIR = PACKAGE_DIR / "official_data" / "cgu"
BUNDLED_CCU_DIR = PACKAGE_DIR / "official_data" / "ccu"
BUNDLED_NTU_DIR = PACKAGE_DIR / "official_data" / "ntu"
BUNDLED_NCU_DIR = PACKAGE_DIR / "official_data" / "ncu"
BUNDLED_FJU_DIR = PACKAGE_DIR / "official_data" / "fju"
BUNDLED_SCU_DIR = PACKAGE_DIR / "official_data" / "scu"
BUNDLED_NTNU_DIR = PACKAGE_DIR / "official_data" / "ntnu"
BUNDLED_CYCU_DIR = PACKAGE_DIR / "official_data" / "cycu"
BUNDLED_NTUST_DIR = PACKAGE_DIR / "official_data" / "ntust"
BUNDLED_YZU_DIR = PACKAGE_DIR / "official_data" / "yzu"
BUNDLED_FCU_DIR = PACKAGE_DIR / "official_data" / "fcu"
BUNDLED_NSYSU_DIR = PACKAGE_DIR / "official_data" / "nsysu"
BUNDLED_NCHU_DIR = PACKAGE_DIR / "official_data" / "nchu"
BUNDLED_NTUT_DIR = PACKAGE_DIR / "official_data" / "ntut"
BUNDLED_NCCU_DIR = PACKAGE_DIR / "official_data" / "nccu"
BUNDLED_NCKU_DIR = PACKAGE_DIR / "official_data" / "ncku"
BUNDLED_NYCU_DIR = PACKAGE_DIR / "official_data" / "nycu"
BUNDLED_NTHU_DIR = PACKAGE_DIR / "official_data" / "nthu"
BUNDLED_PCCU_DIR = PACKAGE_DIR / "official_data" / "pccu"
BUNDLED_WZU_DIR = PACKAGE_DIR / "official_data" / "wzu"
BUNDLED_NKUST_DIR = PACKAGE_DIR / "official_data" / "nkust"
BUNDLED_YUNTECH_DIR = PACKAGE_DIR / "official_data" / "yuntech"
BUNDLED_NTOU_DIR = PACKAGE_DIR / "official_data" / "ntou"
BUNDLED_NCUE_DIR = PACKAGE_DIR / "official_data" / "ncue"
BUNDLED_NKNU_DIR = PACKAGE_DIR / "official_data" / "nknu"
BUNDLED_TMU_DIR = PACKAGE_DIR / "official_data" / "tmu"
BUNDLED_CSMU_DIR = PACKAGE_DIR / "official_data" / "csmu"
BUNDLED_CMU_DIR = PACKAGE_DIR / "official_data" / "cmu"
BUNDLED_KMU_DIR = PACKAGE_DIR / "official_data" / "kmu"
BUNDLED_MCU_DIR = PACKAGE_DIR / "official_data" / "mcu"
BUNDLED_NTUB_DIR = PACKAGE_DIR / "official_data" / "ntub"
BUNDLED_NCNU_DIR = PACKAGE_DIR / "official_data" / "ncnu"
BUNDLED_NDHU_DIR = PACKAGE_DIR / "official_data" / "ndhu"
BUNDLED_THU_DIR = PACKAGE_DIR / "official_data" / "thu"
BUNDLED_SHU_DIR = PACKAGE_DIR / "official_data" / "shu"
BUNDLED_PU_DIR = PACKAGE_DIR / "official_data" / "pu"
BUNDLED_USC_DIR = PACKAGE_DIR / "official_data" / "usc"
BUNDLED_NUK_DIR = PACKAGE_DIR / "official_data" / "nuk"
BUNDLED_NCYU_DIR = PACKAGE_DIR / "official_data" / "ncyu"
BUNDLED_NUTC_DIR = PACKAGE_DIR / "official_data" / "nutc"
BUNDLED_NFU_DIR = PACKAGE_DIR / "official_data" / "nfu"
BUNDLED_UTAIPEI_DIR = PACKAGE_DIR / "official_data" / "utaipei"
BUNDLED_NTCU_DIR = PACKAGE_DIR / "official_data" / "ntcu"
BUNDLED_TNUA_DIR = PACKAGE_DIR / "official_data" / "tnua"
BUNDLED_NTUA_DIR = PACKAGE_DIR / "official_data" / "ntua"

BUNDLED_NTUE_DIR = PACKAGE_DIR / "official_data" / "ntue"

BUNDLED_NCUT_DIR = PACKAGE_DIR / "official_data" / "ncut"

BUNDLED_NPUST_DIR = PACKAGE_DIR / "official_data" / "npust"
BUNDLED_NQU_DIR = PACKAGE_DIR / "official_data" / "nqu"

_STORAGE_LOCKS_GUARD = threading.Lock()
_STORAGE_LOCKS: dict[str, threading.RLock] = {}


def _storage_lock_key(path: Path) -> str:
    # Keep the in-process lock identity independent of whether a parent directory
    # or target file already exists. Path.resolve() can consult the Windows
    # filesystem and produce a different spelling while concurrent writers are
    # creating the path, which would briefly split one file across two locks.
    key = os.path.abspath(os.fspath(Path(path)))
    return os.path.normcase(key) if os.name == "nt" else key


def _storage_lock(path: Path) -> threading.RLock:
    key = _storage_lock_key(path)
    with _STORAGE_LOCKS_GUARD:
        lock = _STORAGE_LOCKS.get(key)
        if lock is None:
            lock = threading.RLock()
            _STORAGE_LOCKS[key] = lock
        return lock


@contextmanager
def storage_path_lock(path: Path) -> Generator[None, None, None]:
    """Serialize same-process access to a local fallback storage path."""

    with _storage_lock(path):
        yield


def _atomic_text_writer(path: Path, *, encoding: str) -> tuple[TextIO, Path]:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        text=True,
    )
    temporary = Path(temporary_name)
    try:
        handle = os.fdopen(descriptor, "w", encoding=encoding, newline="")
    except BaseException:
        os.close(descriptor)
        temporary.unlink(missing_ok=True)
        raise
    return handle, temporary


def _application_workflow_key(
    workflow: UniversityApplicationWorkflow,
) -> tuple[str, str, str, str, str]:
    return (
        school_identity_key(workflow.home_university),
        school_identity_key(workflow.school_name),
        str(workflow.program_type or "").strip().casefold(),
        str(workflow.academic_year or "").strip().casefold(),
        str(workflow.application_round or "").strip().casefold(),
    )


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


def merge_application_workflows(
    baseline: Iterable[UniversityApplicationWorkflow],
    overrides: Iterable[UniversityApplicationWorkflow],
) -> list[UniversityApplicationWorkflow]:
    """Merge workflow catalogs while treating a generic local row as an override.

    A reviewed runtime row may intentionally omit ``program_type`` because it
    applies to every program for the same school, year, and round. In that case
    it replaces a more specifically labelled bundled baseline instead of
    competing with it during rule selection.
    """

    # Every row is indexed once by the three things a later override can match it on, so each override removes what it
    # replaces by lookup instead of re-deriving the keys of every row (that took seconds for the bundled catalogue).
    rows: dict[int, UniversityApplicationWorkflow] = {}
    by_key: dict[tuple, set[int]] = {}
    by_scope: dict[tuple, set[int]] = {}
    by_storage: dict[str, set[int]] = {}
    indexed: dict[int, tuple[tuple, tuple, str]] = {}
    next_id = 0

    def add(row: UniversityApplicationWorkflow) -> None:
        nonlocal next_id
        key = _application_workflow_key(row)
        scope = (key[0], key[1], key[3], key[4])
        storage = workflow_storage_key(row)
        rows[next_id] = row
        indexed[next_id] = (key, scope, storage)
        by_key.setdefault(key, set()).add(next_id)
        by_scope.setdefault(scope, set()).add(next_id)
        by_storage.setdefault(storage, set()).add(next_id)
        next_id += 1

    def remove(row_id: int) -> None:
        key, scope, storage = indexed.pop(row_id)
        del rows[row_id]
        by_key[key].discard(row_id)
        by_scope[scope].discard(row_id)
        by_storage[storage].discard(row_id)

    for row in baseline:
        add(row)
    for override in overrides:
        override_key = _application_workflow_key(override)
        governance_key = override.governance_key
        replaced = set(by_key.get(override_key, ()))
        if governance_key:
            replaced |= by_storage.get(governance_key, set())
        if not override_key[2]:
            replaced |= by_scope.get((override_key[0], override_key[1], override_key[3], override_key[4]), set())
        for row_id in replaced:
            remove(row_id)
        add(override)
    return list(rows.values())


def _with_explicit_destination_gaps(profile: DestinationProfile) -> DestinationProfile:
    """Keep an honest, visible answer for official details that are not public."""

    if profile.home_university == CCU.school_name:
        # CCU keeps reviewed field statuses and true nulls. Unverified public
        # research cannot be rewritten as an official non-publication claim.
        return profile
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


def _destination_profile_key(profile: DestinationProfile) -> tuple[str, str]:
    return (
        school_identity_key(profile.home_university or CGU.school_name),
        school_program_identity_key(profile.school_name),
    )


def _scope_legacy_destination_profiles(
    rows: Iterable[DestinationProfile],
    data_dir: Path,
) -> list[DestinationProfile]:
    """Recover home-school provenance for rows written before it was stored.

    The original product only supported CGU, so an unscoped row with no audit
    is assigned to CGU. A row with exactly one audited home is assigned there.
    Ambiguous rows stay unscoped so the API can fail closed instead of sharing
    one research result across universities.
    """

    homes_by_school: dict[str, set[str]] = {}
    for audit in read_jsonl(
        data_paths(data_dir)["collection_audits"],
        CollectionAudit,
    ):
        if audit.collector != "destinations" or not audit.home_university:
            continue
        homes_by_school.setdefault(
            school_program_identity_key(audit.school_name),
            set(),
        ).add(audit.home_university)

    scoped: list[DestinationProfile] = []
    for row in rows:
        if row.home_university:
            scoped.append(row)
            continue
        homes = homes_by_school.get(school_program_identity_key(row.school_name), set())
        if len(homes) == 1:
            scoped.append(
                row.model_copy(update={"home_university": next(iter(homes))})
            )
        elif not homes:
            scoped.append(
                row.model_copy(update={"home_university": CGU.school_name})
            )
        else:
            scoped.append(row)
    return scoped


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
        "application_workflow_revisions": (
            data_dir / "processed" / "application_workflow_revisions.jsonl"
        ),
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
        "community_publish_events": data_dir / "processed" / "community_publish_events.jsonl",
        "community_moderation_audits": data_dir / "processed" / "community_moderation_audits.jsonl",
        "experience_submissions": data_dir / "processed" / "experience_submissions.jsonl",
        "collection_audits": data_dir / "processed" / "collection_audits.jsonl",
        "destination_profiles": data_dir / "processed" / "destination_profiles.jsonl",
        "destination_profile_reviews": (
            data_dir / "processed" / "destination_profile_reviews.jsonl"
        ),
        "destination_profile_promotions": (
            data_dir / "processed" / "destination_profile_promotions.jsonl"
        ),
        "destination_profile_rollbacks": (
            data_dir / "processed" / "destination_profile_rollbacks.jsonl"
        ),
        "user_accounts": data_dir / "processed" / "user_accounts.jsonl",
        "account_sessions": data_dir / "processed" / "account_sessions.jsonl",
        "account_notifications": data_dir / "processed" / "account_notifications.jsonl",
        "notification_deliveries": data_dir / "processed" / "notification_deliveries.jsonl",
        "private_auth": data_dir / "private_auth",
        "email_verification_secret": data_dir / "private_auth" / ".local-email-secret",
        "email_verifications": data_dir / "private_auth" / "email_verifications.jsonl",
        "private_vault": data_dir / "private_vault",
        "vault_blobs": data_dir / "private_vault" / "blobs",
        "vault_master_key": data_dir / "private_vault" / ".local-master-key",
        "vault_documents": data_dir / "private_vault" / "documents.jsonl",
        "vault_versions": data_dir / "private_vault" / "versions.jsonl",
        "vault_consents": data_dir / "private_vault" / "consents.jsonl",
        "vault_audits": data_dir / "private_vault" / "audit.jsonl",
        "private_form_drafts": data_dir / "private_form_drafts",
        "form_drafts": data_dir / "private_form_drafts" / "drafts.jsonl",
    }


def ensure_data_dirs(data_dir: Path = DEFAULT_DATA_DIR) -> dict[str, Path]:
    paths = data_paths(data_dir)
    paths["raw"].mkdir(parents=True, exist_ok=True)
    paths["raw_files"].mkdir(parents=True, exist_ok=True)
    paths["processed"].mkdir(parents=True, exist_ok=True)
    paths["private_auth"].mkdir(parents=True, exist_ok=True)
    paths["private_vault"].mkdir(parents=True, exist_ok=True)
    paths["vault_blobs"].mkdir(parents=True, exist_ok=True)
    paths["private_form_drafts"].mkdir(parents=True, exist_ok=True)
    return paths


def write_jsonl(path: Path, rows: Iterable[BaseModel]) -> int:
    with storage_path_lock(path):
        count = 0
        handle, temporary = _atomic_text_writer(path, encoding="utf-8")
        try:
            with handle:
                for row in rows:
                    handle.write(row.model_dump_json() + "\n")
                    count += 1
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
        return count


def read_jsonl(path: Path, model: type[T], *, transform: Callable[[T], T] | None = None) -> list[T]:
    with storage_path_lock(path):
        if not path.exists():
            return []
        rows: list[T] = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                row = model.model_validate_json(line)
                rows.append(transform(row) if transform else row)
        return rows


def save_json(path: Path, row: BaseModel) -> None:
    with storage_path_lock(path):
        handle, temporary = _atomic_text_writer(path, encoding="utf-8")
        try:
            with handle:
                json.dump(
                    row.model_dump(mode="json"),
                    handle,
                    ensure_ascii=False,
                    indent=2,
                )
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise


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


# Parsing and structuring the catalogue (about 1,400 workflows) and merging it took seconds on every request, so the result
# is kept and reused for as long as the files it came from are unchanged. The signature is read before the files are, so a
# file replaced mid-read is simply read again next time. Callers get their own list; the workflows in it are shared and are
# only ever copied (model_copy), never edited in place.
_WORKFLOW_CACHE_LIMIT = 8
_workflow_cache_lock = threading.Lock()
_workflow_cache: dict[tuple, list[UniversityApplicationWorkflow]] = {}
_workflow_cache_builds: dict[tuple, Future] = {}


def _file_signature(path: Path) -> tuple[int, int] | None:
    try:
        stat = path.stat()
    except OSError:
        return None
    return (stat.st_mtime_ns, stat.st_size)


def file_signature(path: Path) -> tuple[int, int] | None:
    """Modification time and size, or None when the file is missing; changes whenever the file is rewritten."""

    return _file_signature(path)


def _cached_workflows(key: tuple, build) -> list[UniversityApplicationWorkflow]:
    with _workflow_cache_lock:
        cached = _workflow_cache.get(key)
        if cached is not None:
            return list(cached)
        pending = _workflow_cache_builds.get(key)
        owns_build = pending is None
        if owns_build:
            pending = Future()
            _workflow_cache_builds[key] = pending
    if not owns_build:
        return list(pending.result())
    # A cold page requests the same catalogue concurrently. Parse it once;
    # other signatures can still build independently, and nested local/bundled
    # catalogue reads do not hold the cache lock while they build or wait.
    try:
        cached = build()
        with _workflow_cache_lock:
            while len(_workflow_cache) >= _WORKFLOW_CACHE_LIMIT:
                _workflow_cache.pop(next(iter(_workflow_cache)))
            _workflow_cache[key] = cached
        pending.set_result(cached)
        return list(cached)
    except BaseException as error:
        pending.set_exception(error)
        raise
    finally:
        with _workflow_cache_lock:
            _workflow_cache_builds.pop(key, None)


def workflow_catalog_token(data_dir: Path = DEFAULT_DATA_DIR) -> tuple:
    """Changes whenever the files the catalogue for ``data_dir`` is built from change."""

    path = data_paths(data_dir)["application_workflows"]
    return (str(path), _file_signature(path), _include_bundled_defaults(data_dir), _bundled_workflow_signature())


def cached_workflow_catalog(key: tuple, build) -> list[UniversityApplicationWorkflow]:
    """``build()`` once per ``key``; each caller gets its own list of the same (never edited in place) workflows."""

    return _cached_workflows(key, build)


def _bundled_workflow_paths() -> tuple[Path, ...]:
    return tuple(directory / "application_workflows.jsonl" for directory in (BUNDLED_NTPU_DIR, BUNDLED_CGU_DIR, BUNDLED_NTU_DIR, BUNDLED_CCU_DIR, BUNDLED_NCU_DIR, BUNDLED_TKU_DIR, BUNDLED_FJU_DIR, BUNDLED_SCU_DIR, BUNDLED_NTNU_DIR, BUNDLED_CYCU_DIR, BUNDLED_NTUST_DIR, BUNDLED_YZU_DIR, BUNDLED_FCU_DIR, BUNDLED_NSYSU_DIR, BUNDLED_NCHU_DIR, BUNDLED_NTUT_DIR, BUNDLED_NCCU_DIR, BUNDLED_NCKU_DIR, BUNDLED_NYCU_DIR, BUNDLED_NTHU_DIR, BUNDLED_PCCU_DIR, BUNDLED_WZU_DIR, BUNDLED_NKUST_DIR, BUNDLED_YUNTECH_DIR, BUNDLED_NTOU_DIR, BUNDLED_NCUE_DIR, BUNDLED_NKNU_DIR, BUNDLED_TMU_DIR, BUNDLED_CSMU_DIR, BUNDLED_CMU_DIR, BUNDLED_KMU_DIR, BUNDLED_MCU_DIR, BUNDLED_NTUB_DIR, BUNDLED_NCNU_DIR, BUNDLED_NDHU_DIR, BUNDLED_THU_DIR, BUNDLED_SHU_DIR, BUNDLED_PU_DIR, BUNDLED_USC_DIR, BUNDLED_NUK_DIR, BUNDLED_NCYU_DIR, BUNDLED_NUTC_DIR, BUNDLED_NFU_DIR, BUNDLED_UTAIPEI_DIR, BUNDLED_NTCU_DIR, BUNDLED_TNUA_DIR, BUNDLED_NTUA_DIR, BUNDLED_NTUE_DIR, BUNDLED_NCUT_DIR, BUNDLED_NPUST_DIR, BUNDLED_NQU_DIR))


def _bundled_workflow_signature() -> tuple:
    return tuple((str(path), _file_signature(path)) for path in _bundled_workflow_paths())


def _locked_governance_io(function):
    parameters = signature(function)
    @wraps(function)
    def locked(*args, **kwargs):
        from .governance_commands import local_governance_lock
        data_dir = parameters.bind_partial(*args, **kwargs).arguments.get("data_dir", DEFAULT_DATA_DIR)
        with local_governance_lock(data_dir):
            return function(*args, **kwargs)
    return locked


@_locked_governance_io
def load_application_workflows(
    data_dir: Path = DEFAULT_DATA_DIR,
) -> list[UniversityApplicationWorkflow]:
    path = data_paths(data_dir)["application_workflows"]
    include_bundled = _include_bundled_defaults(data_dir)
    key = ("local", str(path), _file_signature(path), include_bundled, _bundled_workflow_signature() if include_bundled else None)

    def build() -> list[UniversityApplicationWorkflow]:
        local = read_jsonl(path, UniversityApplicationWorkflow, transform=structure_application_workflow)
        if not include_bundled:
            return local
        return merge_application_workflows(
            load_bundled_application_workflows(),
            local,
        )

    return _cached_workflows(key, build)


def load_bundled_application_workflows() -> list[UniversityApplicationWorkflow]:
    """Load the tracked official workflow baseline without runtime data-dir rules."""

    def build() -> list[UniversityApplicationWorkflow]:
        # Structure each row while reading it. Keeping the entire raw six-school
        # graph alongside its structured copy retains both during the cold load.
        return [
            row
            for path in _bundled_workflow_paths()
            for row in read_jsonl(path, UniversityApplicationWorkflow, transform=structure_application_workflow)
        ]

    return _cached_workflows(("bundled", _bundled_workflow_signature()), build)


@_locked_governance_io
def save_application_workflows(
    rows: Iterable[UniversityApplicationWorkflow],
    data_dir: Path = DEFAULT_DATA_DIR,
) -> int:
    return write_jsonl(data_paths(data_dir)["application_workflows"], rows)


@_locked_governance_io
def replace_application_workflow(
    workflow: UniversityApplicationWorkflow,
    data_dir: Path = DEFAULT_DATA_DIR,
) -> list[UniversityApplicationWorkflow]:
    workflow = structure_application_workflow(workflow)
    workflow_key = _application_workflow_key(workflow)
    retained = [
        row
        for row in load_application_workflows(data_dir)
        if (
            _application_workflow_key(row) != workflow_key
            and not (
                workflow.governance_key
                and workflow_storage_key(row) == workflow.governance_key
            )
        )
    ]
    ordered = sorted(
        [*retained, workflow],
        key=lambda row: (
            row.home_university.casefold(),
            row.school_name.casefold(),
            str(row.academic_year or "").casefold(),
            str(row.application_round or "").casefold(),
        ),
    )
    save_application_workflows(ordered, data_dir)
    return ordered


@_locked_governance_io
def load_application_workflow_revisions(
    data_dir: Path = DEFAULT_DATA_DIR,
) -> list[ApplicationWorkflowRevision]:
    return read_jsonl(
        data_paths(data_dir)["application_workflow_revisions"],
        ApplicationWorkflowRevision,
    )


@_locked_governance_io
def save_application_workflow_revisions(
    rows: Iterable[ApplicationWorkflowRevision],
    data_dir: Path = DEFAULT_DATA_DIR,
) -> int:
    return write_jsonl(data_paths(data_dir)["application_workflow_revisions"], rows)


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
    collector_key = audit.collector.strip().casefold()
    identity = school_program_identity_key if collector_key == "destinations" else school_identity_key
    school_key = identity(audit.school_name)
    home_key = school_identity_key(audit.home_university or "")
    retained = [
        row
        for row in load_collection_audits(data_dir)
        if (
            identity(row.school_name),
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


_DEFAULT_READ_JSONL = read_jsonl
_destination_profiles_cache_lock = threading.Lock()
_destination_profiles_cache: dict[tuple, list[DestinationProfile]] = {}
_partner_research_cache_lock = threading.Lock()
_partner_research_cache: dict[tuple, list[PartnerResearchRecord]] = {}


def _bundled_destination_entries(home_key: str | None) -> tuple[tuple[Path, str], ...]:
    return tuple(
        (directory / "destination_profiles.jsonl", bundle_home)
        for directory, bundle_home in (
            (BUNDLED_NTPU_DIR, NTPU.school_name),
            (BUNDLED_TKU_DIR, TKU.school_name),
            (BUNDLED_CGU_DIR, CGU.school_name),
            (BUNDLED_NTU_DIR, NTU.school_name),
            (BUNDLED_CCU_DIR, CCU.school_name),
            (BUNDLED_NCU_DIR, NCU.school_name),
            (BUNDLED_FJU_DIR, FJU.school_name),
            (BUNDLED_SCU_DIR, SCU.school_name),
            (BUNDLED_NTNU_DIR, NTNU.school_name),
            (BUNDLED_CYCU_DIR, CYCU.school_name),
            (BUNDLED_NTUST_DIR, NTUST.school_name),
            (BUNDLED_YZU_DIR, YZU.school_name),
            (BUNDLED_FCU_DIR, FCU.school_name),
            (BUNDLED_NSYSU_DIR, NSYSU.school_name),
            (BUNDLED_NCHU_DIR, NCHU.school_name),
            (BUNDLED_NTUT_DIR, NTUT.school_name),
            (BUNDLED_NCCU_DIR, NCCU.school_name),
            (BUNDLED_NCKU_DIR, NCKU.school_name),
            (BUNDLED_NYCU_DIR, NYCU.school_name),
            (BUNDLED_NTHU_DIR, NTHU.school_name),
            (BUNDLED_PCCU_DIR, PCCU.school_name),
            (BUNDLED_WZU_DIR, WZU.school_name),
            (BUNDLED_NKUST_DIR, NKUST.school_name),
            (BUNDLED_YUNTECH_DIR, YUNTECH.school_name),
            (BUNDLED_NTOU_DIR, NTOU.school_name),
            (BUNDLED_NCUE_DIR, NCUE.school_name),
            (BUNDLED_NKNU_DIR, NKNU.school_name),
            (BUNDLED_TMU_DIR, TMU.school_name),
            (BUNDLED_CSMU_DIR, CSMU.school_name),
            (BUNDLED_CMU_DIR, CMU.school_name),
            (BUNDLED_KMU_DIR, KMU.school_name),
            (BUNDLED_MCU_DIR, MCU.school_name),
            (BUNDLED_NTUB_DIR, NTUB.school_name),
            (BUNDLED_NCNU_DIR, NCNU.school_name),
            (BUNDLED_NDHU_DIR, NDHU.school_name),
            (BUNDLED_THU_DIR, THU.school_name),
            (BUNDLED_SHU_DIR, SHU.school_name),
            (BUNDLED_PU_DIR, PU.school_name),
            (BUNDLED_USC_DIR, USC.school_name),
            (BUNDLED_NUK_DIR, NUK.school_name),
            (BUNDLED_NCYU_DIR, NCYU.school_name),
            (BUNDLED_NUTC_DIR, NUTC.school_name),
            (BUNDLED_NFU_DIR, NFU.school_name),
            (BUNDLED_UTAIPEI_DIR, UTAIPEI.school_name),
            (BUNDLED_NTCU_DIR, NTCU.school_name),
            (BUNDLED_TNUA_DIR, TNUA.school_name),
            (BUNDLED_NTUA_DIR, NTUA.school_name),
            (BUNDLED_NTUE_DIR, NTUE.school_name),
            (BUNDLED_NCUT_DIR, NCUT.school_name),
            (BUNDLED_NPUST_DIR, NPUST.school_name),
            (BUNDLED_NQU_DIR, NQU.school_name),
        )
        if home_key is None or school_identity_key(bundle_home) == home_key
    )


@_locked_governance_io
def load_destination_profiles(
    data_dir: Path = DEFAULT_DATA_DIR,
    *,
    include_bundled_baseline: bool | None = None,
    home_university: str | None = None,
) -> list[DestinationProfile]:
    paths = data_paths(data_dir)
    home_key = school_identity_key(home_university) if home_university else None
    include_bundled = (
        _include_bundled_defaults(data_dir)
        if include_bundled_baseline is None
        else include_bundled_baseline
    )
    entries = _bundled_destination_entries(home_key) if include_bundled else ()
    use_cache = read_jsonl is _DEFAULT_READ_JSONL
    cache_key = (
        str(paths["destination_profiles"]),
        _file_signature(paths["destination_profiles"]),
        _file_signature(paths["raw_pages"]),
        _file_signature(paths["processed_pages"]),
        include_bundled,
        home_key,
        tuple((str(p), _file_signature(p)) for p, _ in entries),
    ) if use_cache else None
    if cache_key is not None:
        with _destination_profiles_cache_lock:
            cached = _destination_profiles_cache.get(cache_key)
        if cached is not None:
            return [row.model_copy(deep=True) for row in cached]

    local = _scope_legacy_destination_profiles(
        read_jsonl(
            paths["destination_profiles"],
            DestinationProfile,
        ),
        data_dir,
    )
    if home_key:
        local = [row for row in local if not row.home_university
                 or school_identity_key(row.home_university) == home_key]
    if not include_bundled:
        if cache_key is not None:
            with _destination_profiles_cache_lock:
                if len(_destination_profiles_cache) >= 32:
                    _destination_profiles_cache.pop(next(iter(_destination_profiles_cache)))
                _destination_profiles_cache[cache_key] = local
        return [row.model_copy(deep=True) for row in local] if cache_key is not None else local
    bundled = [
        row.model_copy(update={"home_university": bundle_home})
        for path, bundle_home in entries
        for row in read_jsonl(
            path,
            DestinationProfile,
        )
    ]
    result = [
        _with_explicit_destination_gaps(row)
        for row in _merge_rows(
            bundled,
            local,
            key=_destination_profile_key,
        )
    ]
    if cache_key is not None:
        with _destination_profiles_cache_lock:
            if len(_destination_profiles_cache) >= 32:
                _destination_profiles_cache.pop(next(iter(_destination_profiles_cache)))
            _destination_profiles_cache[cache_key] = result
        return [row.model_copy(deep=True) for row in result]
    return result


def load_partner_research(
    data_dir: Path = DEFAULT_DATA_DIR,
    *,
    include_bundled_baseline: bool | None = None,
) -> list[PartnerResearchRecord]:
    local_path = data_paths(data_dir)["partner_research"]
    include_bundled = (
        _include_bundled_defaults(data_dir)
        if include_bundled_baseline is None
        else include_bundled_baseline
    )
    bundled_paths = tuple(
        directory / "partner_research.jsonl"
        for directory in (BUNDLED_NTPU_DIR, BUNDLED_NTU_DIR, BUNDLED_NCU_DIR, BUNDLED_FJU_DIR, BUNDLED_SCU_DIR, BUNDLED_NTNU_DIR, BUNDLED_CYCU_DIR, BUNDLED_NTUST_DIR, BUNDLED_YZU_DIR, BUNDLED_FCU_DIR, BUNDLED_NSYSU_DIR, BUNDLED_NCHU_DIR, BUNDLED_NTUT_DIR, BUNDLED_NCCU_DIR, BUNDLED_NCKU_DIR, BUNDLED_NYCU_DIR, BUNDLED_NTHU_DIR, BUNDLED_PCCU_DIR, BUNDLED_WZU_DIR, BUNDLED_NKUST_DIR, BUNDLED_YUNTECH_DIR, BUNDLED_NTOU_DIR, BUNDLED_NCUE_DIR, BUNDLED_NKNU_DIR, BUNDLED_TMU_DIR, BUNDLED_CSMU_DIR, BUNDLED_CMU_DIR, BUNDLED_KMU_DIR, BUNDLED_MCU_DIR, BUNDLED_NTUB_DIR, BUNDLED_NCNU_DIR, BUNDLED_NDHU_DIR, BUNDLED_THU_DIR, BUNDLED_SHU_DIR, BUNDLED_PU_DIR, BUNDLED_USC_DIR, BUNDLED_NUK_DIR, BUNDLED_NCYU_DIR, BUNDLED_NUTC_DIR, BUNDLED_NFU_DIR, BUNDLED_UTAIPEI_DIR, BUNDLED_NTCU_DIR, BUNDLED_TNUA_DIR, BUNDLED_NTUA_DIR, BUNDLED_NTUE_DIR, BUNDLED_NCUT_DIR, BUNDLED_NPUST_DIR, BUNDLED_NQU_DIR)
    ) if include_bundled else ()
    use_cache = read_jsonl is _DEFAULT_READ_JSONL
    cache_key = (
        str(local_path),
        _file_signature(local_path),
        include_bundled,
        tuple((str(p), _file_signature(p)) for p in bundled_paths),
    ) if use_cache else None
    if cache_key is not None:
        with _partner_research_cache_lock:
            cached = _partner_research_cache.get(cache_key)
        if cached is not None:
            return list(cached)

    local = read_jsonl(local_path, PartnerResearchRecord)
    if not include_bundled:
        if cache_key is not None:
            with _partner_research_cache_lock:
                if len(_partner_research_cache) >= 16:
                    _partner_research_cache.pop(next(iter(_partner_research_cache)))
                _partner_research_cache[cache_key] = local
        return list(local)
    bundled = [
        row
        for path in bundled_paths
        for row in read_jsonl(path, PartnerResearchRecord)
    ]
    result = _merge_rows(
        bundled,
        local,
        key=lambda row: (
            school_identity_key(row.home_university),
            school_identity_key(row.school_name),
        ),
    )
    if cache_key is not None:
        with _partner_research_cache_lock:
            if len(_partner_research_cache) >= 16:
                _partner_research_cache.pop(next(iter(_partner_research_cache)))
            _partner_research_cache[cache_key] = result
    return list(result)


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


@_locked_governance_io
def save_destination_profiles(
    rows: Iterable[DestinationProfile], data_dir: Path = DEFAULT_DATA_DIR
) -> int:
    return write_jsonl(data_paths(data_dir)["destination_profiles"], rows)


def upsert_destination_profile(
    profile: DestinationProfile, data_dir: Path = DEFAULT_DATA_DIR
) -> list[DestinationProfile]:
    profile_key = _destination_profile_key(profile)
    retained = [
        row
        for row in load_destination_profiles(
            data_dir,
            include_bundled_baseline=False,
        )
        if _destination_profile_key(row) != profile_key
    ]
    ordered = sorted(
        [*retained, profile],
        key=lambda row: (
            (row.home_university or CGU.school_name).casefold(),
            row.school_name.casefold(),
        ),
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
    return _append_row(
        "community_questions",
        question,
        CommunityQuestion,
        data_dir,
    )


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
    return _append_row(
        "community_answers",
        answer,
        CommunityAnswer,
        data_dir,
    )


def _append_row(path_key: str, row: T, model: type[T], data_dir: Path) -> T:
    path = data_paths(data_dir)[path_key]
    with storage_path_lock(path):
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


def load_email_verifications(
    data_dir: Path = DEFAULT_DATA_DIR,
) -> list[EmailVerificationChallenge]:
    return read_jsonl(
        data_paths(data_dir)["email_verifications"],
        EmailVerificationChallenge,
    )


def save_email_verifications(
    rows: Iterable[EmailVerificationChallenge],
    data_dir: Path = DEFAULT_DATA_DIR,
) -> int:
    return write_jsonl(data_paths(data_dir)["email_verifications"], rows)


def load_account_notifications(
    data_dir: Path = DEFAULT_DATA_DIR,
) -> list[AccountNotification]:
    return read_jsonl(data_paths(data_dir)["account_notifications"], AccountNotification)


def save_account_notifications(
    rows: Iterable[AccountNotification], data_dir: Path = DEFAULT_DATA_DIR
) -> int:
    return write_jsonl(data_paths(data_dir)["account_notifications"], rows)


def load_notification_deliveries(
    data_dir: Path = DEFAULT_DATA_DIR,
) -> list[NotificationDelivery]:
    return read_jsonl(
        data_paths(data_dir)["notification_deliveries"], NotificationDelivery
    )


def save_notification_deliveries(
    rows: Iterable[NotificationDelivery], data_dir: Path = DEFAULT_DATA_DIR
) -> int:
    return write_jsonl(data_paths(data_dir)["notification_deliveries"], rows)


def load_application_form_drafts(
    data_dir: Path = DEFAULT_DATA_DIR,
) -> list[ApplicationFormDraftRecord]:
    return read_jsonl(data_paths(data_dir)["form_drafts"], ApplicationFormDraftRecord)


def save_application_form_drafts(
    rows: Iterable[ApplicationFormDraftRecord], data_dir: Path = DEFAULT_DATA_DIR
) -> int:
    return write_jsonl(data_paths(data_dir)["form_drafts"], rows)


def load_vault_documents(
    data_dir: Path = DEFAULT_DATA_DIR,
) -> list[VaultDocumentRecord]:
    return read_jsonl(data_paths(data_dir)["vault_documents"], VaultDocumentRecord)


def save_vault_documents(
    rows: Iterable[VaultDocumentRecord], data_dir: Path = DEFAULT_DATA_DIR
) -> int:
    return write_jsonl(data_paths(data_dir)["vault_documents"], rows)


def load_vault_versions(
    data_dir: Path = DEFAULT_DATA_DIR,
) -> list[VaultDocumentVersionRecord]:
    return read_jsonl(
        data_paths(data_dir)["vault_versions"], VaultDocumentVersionRecord
    )


def save_vault_versions(
    rows: Iterable[VaultDocumentVersionRecord], data_dir: Path = DEFAULT_DATA_DIR
) -> int:
    return write_jsonl(data_paths(data_dir)["vault_versions"], rows)


def load_vault_consents(
    data_dir: Path = DEFAULT_DATA_DIR,
) -> list[VaultConsentRecord]:
    return read_jsonl(data_paths(data_dir)["vault_consents"], VaultConsentRecord)


def save_vault_consents(
    rows: Iterable[VaultConsentRecord], data_dir: Path = DEFAULT_DATA_DIR
) -> int:
    return write_jsonl(data_paths(data_dir)["vault_consents"], rows)


def load_vault_audits(
    data_dir: Path = DEFAULT_DATA_DIR,
) -> list[VaultAuditRecord]:
    return read_jsonl(data_paths(data_dir)["vault_audits"], VaultAuditRecord)


def save_vault_audits(
    rows: Iterable[VaultAuditRecord], data_dir: Path = DEFAULT_DATA_DIR
) -> int:
    return write_jsonl(data_paths(data_dir)["vault_audits"], rows)


def load_community_posts(data_dir: Path = DEFAULT_DATA_DIR) -> list[CommunityPost]:
    return read_jsonl(data_paths(data_dir)["community_posts"], CommunityPost)


def save_community_posts(
    rows: Iterable[CommunityPost], data_dir: Path = DEFAULT_DATA_DIR
) -> int:
    return write_jsonl(data_paths(data_dir)["community_posts"], rows)


def append_community_post(post: CommunityPost, data_dir: Path = DEFAULT_DATA_DIR) -> CommunityPost:
    return _append_row("community_posts", post, CommunityPost, data_dir)


def load_community_post_comments(data_dir: Path = DEFAULT_DATA_DIR) -> list[CommunityPostComment]:
    return read_jsonl(data_paths(data_dir)["community_post_comments"], CommunityPostComment)


def save_community_post_comments(
    rows: Iterable[CommunityPostComment], data_dir: Path = DEFAULT_DATA_DIR
) -> int:
    return write_jsonl(data_paths(data_dir)["community_post_comments"], rows)


def append_community_post_comment(comment: CommunityPostComment, data_dir: Path = DEFAULT_DATA_DIR) -> CommunityPostComment:
    return _append_row("community_post_comments", comment, CommunityPostComment, data_dir)


def load_public_chat_messages(data_dir: Path = DEFAULT_DATA_DIR) -> list[PublicChatMessage]:
    return read_jsonl(data_paths(data_dir)["public_chat_messages"], PublicChatMessage)


def save_public_chat_messages(
    rows: Iterable[PublicChatMessage], data_dir: Path = DEFAULT_DATA_DIR
) -> int:
    return write_jsonl(data_paths(data_dir)["public_chat_messages"], rows)


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


def save_private_messages(
    rows: Iterable[PrivateMessage], data_dir: Path = DEFAULT_DATA_DIR
) -> int:
    return write_jsonl(data_paths(data_dir)["private_messages"], rows)


def append_private_message(message: PrivateMessage, data_dir: Path = DEFAULT_DATA_DIR) -> PrivateMessage:
    return _append_row("private_messages", message, PrivateMessage, data_dir)


def load_community_blocks(data_dir: Path = DEFAULT_DATA_DIR) -> list[CommunityBlock]:
    return read_jsonl(data_paths(data_dir)["community_blocks"], CommunityBlock)


def save_community_blocks(
    rows: Iterable[CommunityBlock], data_dir: Path = DEFAULT_DATA_DIR
) -> int:
    return write_jsonl(data_paths(data_dir)["community_blocks"], rows)


def append_community_block(block: CommunityBlock, data_dir: Path = DEFAULT_DATA_DIR) -> CommunityBlock:
    return _append_row("community_blocks", block, CommunityBlock, data_dir)


def load_community_reports(data_dir: Path = DEFAULT_DATA_DIR) -> list[CommunityReport]:
    return read_jsonl(data_paths(data_dir)["community_reports"], CommunityReport)


def save_community_reports(
    rows: Iterable[CommunityReport], data_dir: Path = DEFAULT_DATA_DIR
) -> int:
    return write_jsonl(data_paths(data_dir)["community_reports"], rows)


def append_community_report(report: CommunityReport, data_dir: Path = DEFAULT_DATA_DIR) -> CommunityReport:
    return _append_row("community_reports", report, CommunityReport, data_dir)


def load_community_publish_events(
    data_dir: Path = DEFAULT_DATA_DIR,
) -> list[CommunityPublishEvent]:
    return read_jsonl(
        data_paths(data_dir)["community_publish_events"],
        CommunityPublishEvent,
    )


def save_community_publish_events(
    rows: Iterable[CommunityPublishEvent], data_dir: Path = DEFAULT_DATA_DIR
) -> int:
    return write_jsonl(data_paths(data_dir)["community_publish_events"], rows)


def load_community_moderation_audits(
    data_dir: Path = DEFAULT_DATA_DIR,
) -> list[CommunityModerationAudit]:
    return read_jsonl(
        data_paths(data_dir)["community_moderation_audits"],
        CommunityModerationAudit,
    )


def save_community_moderation_audits(
    rows: Iterable[CommunityModerationAudit],
    data_dir: Path = DEFAULT_DATA_DIR,
) -> int:
    return write_jsonl(data_paths(data_dir)["community_moderation_audits"], rows)


def append_community_moderation_audit(
    audit: CommunityModerationAudit, data_dir: Path = DEFAULT_DATA_DIR
) -> CommunityModerationAudit:
    return _append_row(
        "community_moderation_audits",
        audit,
        CommunityModerationAudit,
        data_dir,
    )


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
    return _append_row(
        "experience_submissions",
        submission,
        ExperienceSubmission,
        data_dir,
    )
