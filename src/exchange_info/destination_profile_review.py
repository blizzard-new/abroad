from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Protocol
from urllib.parse import urlencode

import requests

from .supabase_keys import supabase_key_headers
from .models import (
    DestinationProfile,
    DestinationProfilePublicationHistory,
    DestinationProfilePublicationState,
    DestinationProfilePromotionEvent,
    DestinationProfilePromotionRequest,
    DestinationProfileRollbackEvent,
    DestinationProfileRollbackRequest,
    DestinationProfileReviewBatchChecklistRow,
    DestinationProfileReviewBatchRow,
    DestinationProfileReviewDecision,
    DestinationProfileReviewEvent,
    DestinationProfileReviewQueue,
    DestinationProfileReviewRow,
    DestinationProfileReviewSection,
    DestinationProfileReviewSubmitRequest,
    utc_now,
)
from .school_identity import school_identity_key
from .settings import DEFAULT_DATA_DIR
from .storage import data_paths, read_jsonl, storage_path_lock, write_jsonl


_SECOND_REVIEW_NOTICE = "尚未完成第二位真人內容審查"
_DESTINATION_REVIEW_BATCH_SCHEMA_VERSION = 2
REQUIRED_DESTINATION_PROFILE_REVIEW_SECTIONS = (
    DestinationProfileReviewSection(
        key="identity_location",
        label="學校與地點",
        description="核對合作校名稱、國家、城市與校區適用範圍。",
    ),
    DestinationProfileReviewSection(
        key="cost",
        label="生活費與費用界線",
        description="核對金額、幣別、期間、方案身分與不得跨年度套用的限制。",
    ),
    DestinationProfileReviewSection(
        key="housing",
        label="住宿",
        description="核對住宿類型、價格、申請方式，以及協助不等於床位保證。",
    ),
    DestinationProfileReviewSection(
        key="transport",
        label="交通",
        description="核對校區、票價、免費範圍與資料年度。",
    ),
    DestinationProfileReviewSection(
        key="campus_life",
        label="校園生活",
        description="核對服務對象、校區與交換生適用限制。",
    ),
    DestinationProfileReviewSection(
        key="student_guide",
        label="生活指南段落",
        description="逐段核對文字、證據類型、警語及來源連結。",
    ),
    DestinationProfileReviewSection(
        key="first_72_hours",
        label="抵達 72 小時",
        description="核對抵達後待辦、時間點、證據類型與來源。",
    ),
    DestinationProfileReviewSection(
        key="packing",
        label="臺灣出發前準備",
        description="核對攜帶物品與不得由一般經驗冒充官方要求的界線。",
    ),
    DestinationProfileReviewSection(
        key="buy_after_arrival",
        label="抵達後採買",
        description="核對當地採買建議、適用地點與證據類型。",
    ),
    DestinationProfileReviewSection(
        key="coverage_boundary",
        label="查核狀態與警語",
        description="核對 official_partial／official_verified 與 coverage note 是否相符。",
    ),
    DestinationProfileReviewSection(
        key="official_sources",
        label="全部官方來源",
        description="逐一開啟並確認來源仍可存取、為官方頁且直接支持對應敘述。",
    ),
    DestinationProfileReviewSection(
        key="last_checked",
        label="最後查核時間",
        description="確認查核時間來自這次真人核對，並足以代表目前內容。",
    ),
)
_REQUIRED_SECTION_KEYS = tuple(
    section.key for section in REQUIRED_DESTINATION_PROFILE_REVIEW_SECTIONS
)


class DestinationProfileReviewConflictError(ValueError):
    pass


class DestinationProfileReviewStore(Protocol):
    backend_name: str

    def list_events(self) -> list[DestinationProfileReviewEvent]: ...

    def save_event(
        self,
        event: DestinationProfileReviewEvent,
    ) -> DestinationProfileReviewEvent: ...

    def list_promotion_events(self) -> list[DestinationProfilePromotionEvent]: ...

    def save_promotion_event(
        self,
        event: DestinationProfilePromotionEvent,
    ) -> DestinationProfilePromotionEvent: ...

    def list_rollback_events(self) -> list[DestinationProfileRollbackEvent]: ...

    def save_rollback_event(
        self,
        event: DestinationProfileRollbackEvent,
    ) -> DestinationProfileRollbackEvent: ...


class LocalDestinationProfileReviewStore:
    backend_name = "local-jsonl"

    def __init__(self, data_dir: Path = DEFAULT_DATA_DIR) -> None:
        self.path = data_paths(Path(data_dir))["destination_profile_reviews"]
        self.promotion_path = data_paths(Path(data_dir))[
            "destination_profile_promotions"
        ]
        self.rollback_path = data_paths(Path(data_dir))[
            "destination_profile_rollbacks"
        ]

    def list_events(self) -> list[DestinationProfileReviewEvent]:
        return read_jsonl(self.path, DestinationProfileReviewEvent)

    def save_event(
        self,
        event: DestinationProfileReviewEvent,
    ) -> DestinationProfileReviewEvent:
        with storage_path_lock(self.path):
            events = read_jsonl(self.path, DestinationProfileReviewEvent)
            if any(existing.id == event.id for existing in events):
                return next(existing for existing in events if existing.id == event.id)
            invalidated_after = _review_invalidation_cutoffs(
                read_jsonl(
                    self.promotion_path,
                    DestinationProfilePromotionEvent,
                ),
                read_jsonl(
                    self.rollback_path,
                    DestinationProfileRollbackEvent,
                ),
            ).get(
                (
                    _profile_identity_key(
                        event.home_university,
                        event.school_name,
                    ),
                    event.profile_content_hash,
                )
            )
            same_reviewer_history = [
                existing
                for existing in events
                if _profile_identity_key(
                    existing.home_university,
                    existing.school_name,
                )
                == _profile_identity_key(event.home_university, event.school_name)
                and existing.profile_content_hash == event.profile_content_hash
                and existing.reviewer_id.casefold() == event.reviewer_id.casefold()
                and (
                    invalidated_after is None
                    or existing.reviewed_at > invalidated_after
                )
            ]
            latest = max(
                same_reviewer_history,
                key=lambda row: (row.reviewed_at, row.id),
                default=None,
            )
            if (
                latest
                and latest.decision == event.decision
                and latest.note == event.note
                and latest.reviewed_source_urls == event.reviewed_source_urls
                and latest.reviewed_section_keys == event.reviewed_section_keys
            ):
                return latest
            if latest and event.supersedes_event_id != latest.id:
                event = event.model_copy(
                    update={"supersedes_event_id": latest.id}
                )
            write_jsonl(
                self.path,
                sorted(
                    [*events, event],
                    key=lambda row: (row.reviewed_at, row.id),
                ),
            )
        return event

    def list_promotion_events(self) -> list[DestinationProfilePromotionEvent]:
        return read_jsonl(self.promotion_path, DestinationProfilePromotionEvent)

    def save_promotion_event(
        self,
        event: DestinationProfilePromotionEvent,
    ) -> DestinationProfilePromotionEvent:
        with storage_path_lock(self.promotion_path):
            events = read_jsonl(
                self.promotion_path,
                DestinationProfilePromotionEvent,
            )
            existing = next(
                (
                    row
                    for row in events
                    if row.id == event.id
                ),
                None,
            )
            if existing:
                return existing
            write_jsonl(
                self.promotion_path,
                sorted(
                    [*events, event],
                    key=lambda row: (row.promoted_at, row.id),
                ),
            )
        return event

    def list_rollback_events(self) -> list[DestinationProfileRollbackEvent]:
        return read_jsonl(self.rollback_path, DestinationProfileRollbackEvent)

    def save_rollback_event(
        self,
        event: DestinationProfileRollbackEvent,
    ) -> DestinationProfileRollbackEvent:
        with storage_path_lock(self.rollback_path):
            events = read_jsonl(
                self.rollback_path,
                DestinationProfileRollbackEvent,
            )
            existing = next(
                (
                    row
                    for row in events
                    if row.id == event.id
                    or row.rolled_back_from_event_id
                    == event.rolled_back_from_event_id
                ),
                None,
            )
            if existing:
                return existing
            write_jsonl(
                self.rollback_path,
                sorted(
                    [*events, event],
                    key=lambda row: (row.rolled_back_at, row.id),
                ),
            )
        return event


class SupabaseDestinationProfileReviewStore:
    backend_name = "supabase"

    def __init__(
        self,
        url: str,
        service_role_key: str,
        *,
        request_func=requests.request,
    ) -> None:
        if not url.strip().casefold().startswith("https://"):
            raise ValueError("Supabase URL 必須使用 HTTPS。")
        self.url = url.rstrip("/")
        self.service_role_key = service_role_key
        self.request_func = request_func

    @property
    def headers(self) -> dict[str, str]:
        return {
            **supabase_key_headers(self.service_role_key),
            "Content-Type": "application/json",
        }

    def list_events(self) -> list[DestinationProfileReviewEvent]:
        response = self._request(
            "GET",
            "destination_profile_review_events",
            params={"select": "event_payload", "order": "reviewed_at.asc,id.asc"},
        )
        return [
            DestinationProfileReviewEvent.model_validate(row["event_payload"])
            for row in response.json()
        ]

    def save_event(
        self,
        event: DestinationProfileReviewEvent,
    ) -> DestinationProfileReviewEvent:
        self._request(
            "POST",
            "destination_profile_review_events",
            headers={"Prefer": "return=minimal"},
            json={
                "id": event.id,
                "profile_key": _profile_identity_key(
                    event.home_university,
                    event.school_name,
                ),
                "profile_content_hash": event.profile_content_hash,
                "reviewer_id": event.reviewer_id,
                "decision": event.decision.value,
                "reviewed_at": event.reviewed_at.isoformat(),
                "event_payload": event.model_dump(mode="json"),
            },
        )
        return event

    def list_promotion_events(self) -> list[DestinationProfilePromotionEvent]:
        response = self._request(
            "GET",
            "destination_profile_promotion_events",
            params={"select": "event_payload", "order": "promoted_at.asc,id.asc"},
        )
        return [
            DestinationProfilePromotionEvent.model_validate(row["event_payload"])
            for row in response.json()
        ]

    def save_promotion_event(
        self,
        event: DestinationProfilePromotionEvent,
    ) -> DestinationProfilePromotionEvent:
        self._request(
            "POST",
            "destination_profile_promotion_events",
            headers={"Prefer": "return=minimal"},
            json={
                "id": event.id,
                "profile_key": _profile_identity_key(
                    event.home_university,
                    event.school_name,
                ),
                "source_profile_content_hash": event.source_profile_content_hash,
                "promoted_profile_content_hash": event.promoted_profile_content_hash,
                "promoted_by_id": event.promoted_by_id,
                "promoted_at": event.promoted_at.isoformat(),
                "event_payload": event.model_dump(mode="json"),
            },
        )
        return event

    def list_rollback_events(self) -> list[DestinationProfileRollbackEvent]:
        response = self._request(
            "GET",
            "destination_profile_rollback_events",
            params={"select": "event_payload", "order": "rolled_back_at.asc,id.asc"},
        )
        return [
            DestinationProfileRollbackEvent.model_validate(row["event_payload"])
            for row in response.json()
        ]

    def save_rollback_event(
        self,
        event: DestinationProfileRollbackEvent,
    ) -> DestinationProfileRollbackEvent:
        self._request(
            "POST",
            "destination_profile_rollback_events",
            headers={"Prefer": "return=minimal"},
            json={
                "id": event.id,
                "profile_key": _profile_identity_key(
                    event.home_university,
                    event.school_name,
                ),
                "rolled_back_promotion_event_id": (
                    event.rolled_back_promotion_event_id
                ),
                "rolled_back_from_event_id": event.rolled_back_from_event_id,
                "restored_promotion_event_id": event.restored_promotion_event_id,
                "rolled_back_by_id": event.rolled_back_by_id,
                "rolled_back_at": event.rolled_back_at.isoformat(),
                "event_payload": event.model_dump(mode="json"),
            },
        )
        return event

    def _request(
        self,
        method: str,
        table: str,
        *,
        headers: dict[str, str] | None = None,
        **kwargs,
    ):
        response = self.request_func(
            method,
            f"{self.url}/rest/v1/{table}",
            headers={**self.headers, **(headers or {})},
            timeout=20,
            **kwargs,
        )
        response.raise_for_status()
        return response


def create_destination_profile_review_store(
    data_dir: Path = DEFAULT_DATA_DIR,
) -> DestinationProfileReviewStore:
    url = (
        os.environ.get("EXCHANGE_SUPABASE_URL")
        or os.environ.get("SUPABASE_URL")
        or ""
    ).strip()
    key = (
        os.environ.get("EXCHANGE_SUPABASE_SECRET_KEY")
        or os.environ.get("SUPABASE_SECRET_KEY")
        or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        or ""
    ).strip()
    if url and key:
        return SupabaseDestinationProfileReviewStore(url, key)
    return LocalDestinationProfileReviewStore(data_dir)


def _profile_identity_key(home_university: str, school_name: str) -> str:
    return (
        f"{school_identity_key(home_university)}::"
        f"{school_identity_key(school_name)}"
    )


def _profile_sort_key(profile: DestinationProfile) -> tuple[str, str]:
    return (
        (profile.home_university or "").casefold(),
        profile.school_name.casefold(),
    )


def destination_profile_content_hash(profile: DestinationProfile) -> str:
    serialized = json.dumps(
        profile.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def _review_invalidation_cutoffs(
    promotion_events: list[DestinationProfilePromotionEvent],
    rollback_events: list[DestinationProfileRollbackEvent],
) -> dict[tuple[str, str], datetime]:
    promotions_by_id = {event.id: event for event in promotion_events}
    cutoffs: dict[tuple[str, str], datetime] = {}
    for rollback in rollback_events:
        promotion = promotions_by_id.get(rollback.rolled_back_promotion_event_id)
        if promotion is None:
            raise ValueError("生活情報復原事件所指的升級版本不存在。")
        key = (
            _profile_identity_key(
                promotion.home_university,
                promotion.school_name,
            ),
            promotion.source_profile_content_hash,
        )
        cutoffs[key] = max(
            rollback.rolled_back_at,
            cutoffs.get(key, rollback.rolled_back_at),
        )
    return cutoffs


def _publication_timeline(
    promotion_events: list[DestinationProfilePromotionEvent],
    rollback_events: list[DestinationProfileRollbackEvent],
) -> list[
    tuple[
        datetime,
        str,
        str,
        DestinationProfilePromotionEvent | DestinationProfileRollbackEvent,
    ]
]:
    timeline = [
        (event.promoted_at, event.id, "promotion", event)
        for event in promotion_events
    ]
    timeline.extend(
        (event.rolled_back_at, event.id, "rollback", event)
        for event in rollback_events
    )
    return sorted(timeline, key=lambda row: (row[0], row[1]))


def _resolve_profile_publication_state(
    candidate: DestinationProfile,
    promotion_events: list[DestinationProfilePromotionEvent],
    rollback_events: list[DestinationProfileRollbackEvent],
    *,
    stop_before_event_id: str | None = None,
) -> tuple[
    DestinationProfile,
    DestinationProfilePromotionEvent | None,
    tuple[str, DestinationProfilePromotionEvent | DestinationProfileRollbackEvent]
    | None,
]:
    current_profile = candidate
    active_promotion: DestinationProfilePromotionEvent | None = None
    latest: tuple[
        str,
        DestinationProfilePromotionEvent | DestinationProfileRollbackEvent,
    ] | None = None
    promotions_by_id = {event.id: event for event in promotion_events}
    for _, event_id, event_type, event in _publication_timeline(
        promotion_events,
        rollback_events,
    ):
        if event_id == stop_before_event_id:
            break
        if event_type == "promotion":
            promotion = event
            if not isinstance(promotion, DestinationProfilePromotionEvent):
                raise ValueError("生活情報公開歷程的升級事件格式錯誤。")
            if (
                destination_profile_content_hash(promotion.promoted_profile)
                != promotion.promoted_profile_content_hash
            ):
                raise ValueError("生活情報升級事件的公開內容指紋不一致。")
            current_profile = promotion.promoted_profile
            active_promotion = promotion
            latest = (event_type, promotion)
            continue
        rollback = event
        if not isinstance(rollback, DestinationProfileRollbackEvent):
            raise ValueError("生活情報公開歷程的復原事件格式錯誤。")
        if (
            active_promotion is None
            or rollback.rolled_back_promotion_event_id != active_promotion.id
        ):
            raise ValueError("生活情報復原事件沒有對應目前有效的升級版本。")
        if latest is None or rollback.rolled_back_from_event_id != latest[1].id:
            raise ValueError("生活情報復原事件沒有接在目前公開歷程之後。")
        if (
            destination_profile_content_hash(current_profile)
            != rollback.previous_profile_content_hash
        ):
            raise ValueError("生活情報復原事件的復原前內容指紋不一致。")
        if (
            destination_profile_content_hash(rollback.restored_profile)
            != rollback.restored_profile_content_hash
        ):
            raise ValueError("生活情報復原事件的復原後內容指紋不一致。")
        restored_promotion = None
        if rollback.restored_promotion_event_id:
            restored_promotion = promotions_by_id.get(
                rollback.restored_promotion_event_id
            )
            if restored_promotion is None:
                raise ValueError("生活情報復原事件指定的舊升級版本不存在。")
            if (
                restored_promotion.promoted_profile_content_hash
                != rollback.restored_profile_content_hash
            ):
                raise ValueError("生活情報復原事件與指定舊升級版本不一致。")
        current_profile = rollback.restored_profile
        active_promotion = restored_promotion
        latest = (event_type, rollback)
    return current_profile, active_promotion, latest


def build_destination_profile_publication_history(
    profiles: list[DestinationProfile],
    promotion_events: list[DestinationProfilePromotionEvent],
    rollback_events: list[DestinationProfileRollbackEvent],
    *,
    home_university: str | None = None,
) -> DestinationProfilePublicationHistory:
    selected = [
        profile
        for profile in profiles
        if home_university is None or profile.home_university == home_university
    ]
    profile_by_identity = {
        _profile_identity_key(profile.home_university or "", profile.school_name): profile
        for profile in selected
        if profile.home_university
    }
    event_identities = {
        _profile_identity_key(event.home_university, event.school_name)
        for event in [*promotion_events, *rollback_events]
        if home_university is None or event.home_university == home_university
    }
    missing = event_identities.difference(profile_by_identity)
    if missing:
        raise ValueError("生活情報公開歷程找不到對應的目前候選資料。")
    items: list[DestinationProfilePublicationState] = []
    for identity in sorted(event_identities):
        candidate = profile_by_identity[identity]
        promotions = [
            event
            for event in promotion_events
            if _profile_identity_key(event.home_university, event.school_name)
            == identity
        ]
        rollbacks = [
            event
            for event in rollback_events
            if _profile_identity_key(event.home_university, event.school_name)
            == identity
        ]
        current_profile, active_promotion, latest = (
            _resolve_profile_publication_state(candidate, promotions, rollbacks)
        )
        latest_type = latest[0] if latest else None
        latest_event = latest[1] if latest else None
        latest_actor = None
        latest_at = None
        if isinstance(latest_event, DestinationProfilePromotionEvent):
            latest_actor = latest_event.promoted_by_display_name
            latest_at = latest_event.promoted_at
        elif isinstance(latest_event, DestinationProfileRollbackEvent):
            latest_actor = latest_event.rolled_back_by_display_name
            latest_at = latest_event.rolled_back_at
        candidate_hash = destination_profile_content_hash(candidate)
        items.append(
            DestinationProfilePublicationState(
                home_university=candidate.home_university or "待確認",
                school_name=candidate.school_name,
                current_candidate_content_hash=candidate_hash,
                current_public_profile_content_hash=(
                    destination_profile_content_hash(current_profile)
                ),
                current_public_profile=current_profile,
                active_promotion_event_id=(
                    active_promotion.id if active_promotion else None
                ),
                latest_event_id=latest_event.id if latest_event else None,
                latest_event_type=latest_type,
                latest_actor_display_name=latest_actor,
                latest_event_at=latest_at,
                candidate_changed_since_publication=(
                    bool(active_promotion)
                    and active_promotion.source_profile_content_hash != candidate_hash
                ),
                can_rollback=(
                    active_promotion is not None and latest_type == "promotion"
                ),
                promotion_history=sorted(
                    promotions,
                    key=lambda row: (row.promoted_at, row.id),
                ),
                rollback_history=sorted(
                    rollbacks,
                    key=lambda row: (row.rolled_back_at, row.id),
                ),
            )
        )
    return DestinationProfilePublicationHistory(
        home_university=home_university,
        profile_with_history_count=len(items),
        active_promotion_count=sum(
            item.active_promotion_event_id is not None for item in items
        ),
        promotion_event_count=sum(len(item.promotion_history) for item in items),
        rollback_event_count=sum(len(item.rollback_history) for item in items),
        items=sorted(
            items,
            key=lambda row: (row.home_university.casefold(), row.school_name.casefold()),
        ),
    )


def destination_profile_publication_integrity_issues(
    profiles: list[DestinationProfile],
    review_events: list[DestinationProfileReviewEvent],
    promotion_events: list[DestinationProfilePromotionEvent],
    rollback_events: list[DestinationProfileRollbackEvent],
) -> list[str]:
    """Return fail-closed issues across the append-only destination ledger."""

    issues: list[str] = []
    try:
        build_destination_profile_publication_history(
            profiles,
            promotion_events,
            rollback_events,
        )
    except ValueError as exc:
        issues.append(str(exc))

    review_ids = [event.id for event in review_events]
    if len(review_ids) != len(set(review_ids)):
        issues.append("生活情報審查事件識別重複。")
    publication_ids = [
        event.id for event in [*promotion_events, *rollback_events]
    ]
    if len(publication_ids) != len(set(publication_ids)):
        issues.append("生活情報升級或復原事件識別重複。")

    reviews_by_id = {event.id: event for event in review_events}
    profile_identities = {
        _profile_identity_key(profile.home_university or "", profile.school_name)
        for profile in profiles
        if profile.home_university
    }
    for review in review_events:
        review_identity = _profile_identity_key(
            review.home_university,
            review.school_name,
        )
        if review_identity not in profile_identities:
            issues.append(
                f"生活情報審查事件 {review.id} 找不到對應的目前候選資料。"
            )
        if not review.supersedes_event_id:
            continue
        previous = reviews_by_id.get(review.supersedes_event_id)
        if (
            previous is None
            or previous.id == review.id
            or _profile_identity_key(
                previous.home_university,
                previous.school_name,
            )
            != review_identity
            or previous.profile_content_hash != review.profile_content_hash
            or previous.reviewer_id.casefold() != review.reviewer_id.casefold()
            or previous.reviewed_at > review.reviewed_at
        ):
            issues.append(
                f"生活情報審查事件 {review.id} 的取代鏈不完整。"
            )

    promotions_by_id = {event.id: event for event in promotion_events}
    for promotion in promotion_events:
        identity = _profile_identity_key(
            promotion.home_university,
            promotion.school_name,
        )
        evidence = [
            reviews_by_id.get(event_id)
            for event_id in promotion.review_event_ids
        ]
        if any(event is None for event in evidence):
            issues.append(
                f"生活情報升級事件 {promotion.id} 參照不存在的審查事件。"
            )
            continue
        reviewed = [event for event in evidence if event is not None]
        reviewer_ids = {event.reviewer_id.casefold() for event in reviewed}
        invalidated_after = max(
            (
                rollback.rolled_back_at
                for rollback in rollback_events
                for rolled_back_promotion in [
                    promotions_by_id.get(
                        rollback.rolled_back_promotion_event_id
                    )
                ]
                if rolled_back_promotion is not None
                and rollback.rolled_back_at < promotion.promoted_at
                and _profile_identity_key(
                    rolled_back_promotion.home_university,
                    rolled_back_promotion.school_name,
                )
                == identity
                and rolled_back_promotion.source_profile_content_hash
                == promotion.source_profile_content_hash
            ),
            default=None,
        )
        effective_reviews = _current_profile_reviews(
            sorted(
                [
                    event
                    for event in review_events
                    if _profile_identity_key(
                        event.home_university,
                        event.school_name,
                    )
                    == identity
                    and event.profile_content_hash
                    == promotion.source_profile_content_hash
                    and event.reviewed_at <= promotion.promoted_at
                    and (
                        invalidated_after is None
                        or event.reviewed_at > invalidated_after
                    )
                ],
                key=lambda row: (row.reviewed_at, row.id),
            )
        )
        effective_approval_ids = {
            event.id
            for event in effective_reviews
            if event.decision == DestinationProfileReviewDecision.APPROVE
        }
        if (
            len(reviewed) < 2
            or len(reviewer_ids) < 2
            or reviewer_ids
            != {value.casefold() for value in promotion.reviewer_ids}
            or promotion.promoted_by_id.casefold() not in reviewer_ids
            or len(effective_approval_ids) < 2
            or any(
                event.decision
                != DestinationProfileReviewDecision.APPROVE
                for event in effective_reviews
            )
            or effective_approval_ids != set(promotion.review_event_ids)
            or any(
                _profile_identity_key(
                    event.home_university,
                    event.school_name,
                )
                != identity
                or event.profile_content_hash
                != promotion.source_profile_content_hash
                or event.snapshot_fingerprint != promotion.snapshot_fingerprint
                or event.decision != DestinationProfileReviewDecision.APPROVE
                or event.reviewed_at > promotion.promoted_at
                for event in reviewed
            )
        ):
            issues.append(
                f"生活情報升級事件 {promotion.id} 未精確綁定兩位有效審查者。"
            )

    seen_rollbacks: set[tuple[str, str, str, str]] = set()
    for rollback in rollback_events:
        rollback_key = (
            _profile_identity_key(
                rollback.home_university,
                rollback.school_name,
            ),
            rollback.rolled_back_from_event_id,
            rollback.rolled_back_promotion_event_id,
            rollback.restored_promotion_event_id or "",
        )
        if rollback_key in seen_rollbacks:
            issues.append("同一生活情報公開狀態存在重複復原事件。")
        seen_rollbacks.add(rollback_key)

    return list(dict.fromkeys(issues))


def apply_destination_profile_promotions(
    profiles: list[DestinationProfile],
    promotion_events: list[DestinationProfilePromotionEvent],
    rollback_events: list[DestinationProfileRollbackEvent] | None = None,
) -> list[DestinationProfile]:
    """Overlay the current audited public snapshot without mutating candidates."""

    merged = {
        _profile_identity_key(profile.home_university or "", profile.school_name): profile
        for profile in profiles
        if profile.home_university
    }
    history = build_destination_profile_publication_history(
        profiles,
        promotion_events,
        rollback_events or [],
    )
    for item in history.items:
        merged[
            _profile_identity_key(item.home_university, item.school_name)
        ] = item.current_public_profile
    return sorted(merged.values(), key=_profile_sort_key)


def _snapshot_fingerprint(
    profiles: list[DestinationProfile],
    *,
    home_university: str | None,
) -> str:
    payload = {
        "home_university": home_university,
        "profiles": [
            profile.model_dump(mode="json")
            for profile in sorted(profiles, key=_profile_sort_key)
        ],
    }
    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def _review_gap_codes(profile: DestinationProfile) -> list[str]:
    gaps = ["coverage_not_verified"]
    if _SECOND_REVIEW_NOTICE in profile.coverage_note:
        gaps.append("second_review_required")
    if not profile.sources:
        gaps.append("missing_sources")
    if any(not source.source_url.startswith("https://") for source in profile.sources):
        gaps.append("insecure_sources")
    if profile.last_checked is None:
        gaps.append("missing_last_checked")
    return gaps


def _profile_review_history(
    profile: DestinationProfile,
    events: list[DestinationProfileReviewEvent],
    *,
    not_before: datetime | None = None,
) -> list[DestinationProfileReviewEvent]:
    if not profile.home_university:
        return []
    identity = _profile_identity_key(profile.home_university, profile.school_name)
    content_hash = destination_profile_content_hash(profile)
    return sorted(
        [
            event
            for event in events
            if _profile_identity_key(event.home_university, event.school_name)
            == identity
            and event.profile_content_hash == content_hash
            and (not_before is None or event.reviewed_at > not_before)
        ],
        key=lambda row: (row.reviewed_at, row.id),
    )


def _current_profile_reviews(
    review_history: list[DestinationProfileReviewEvent],
) -> list[DestinationProfileReviewEvent]:
    latest_by_reviewer: dict[str, DestinationProfileReviewEvent] = {}
    for event in review_history:
        latest_by_reviewer[event.reviewer_id.casefold()] = event
    return sorted(
        latest_by_reviewer.values(),
        key=lambda row: (row.reviewed_at, row.reviewer_id.casefold()),
    )


def build_destination_profile_review_queue(
    profiles: list[DestinationProfile],
    *,
    home_university: str | None = None,
    review_events: list[DestinationProfileReviewEvent] | None = None,
    promotion_events: list[DestinationProfilePromotionEvent] | None = None,
    rollback_events: list[DestinationProfileRollbackEvent] | None = None,
    current_reviewer_id: str | None = None,
) -> DestinationProfileReviewQueue:
    events = review_events or []
    promotions = promotion_events or []
    rollbacks = rollback_events or []
    selected = [
        profile
        for profile in profiles
        if home_university is None or profile.home_university == home_university
    ]
    fingerprint = _snapshot_fingerprint(
        selected,
        home_university=home_university,
    )
    publication_history = build_destination_profile_publication_history(
        selected,
        promotions,
        rollbacks,
        home_university=home_university,
    )
    promotions_by_id = {event.id: event for event in promotions}
    active_promotions = [
        promotions_by_id[item.active_promotion_event_id]
        for item in publication_history.items
        if item.active_promotion_event_id
    ]
    promoted_source_hashes = {
        (
            _profile_identity_key(event.home_university, event.school_name),
            event.source_profile_content_hash,
        )
        for event in active_promotions
    }
    review_invalidated_after = _review_invalidation_cutoffs(
        promotions,
        rollbacks,
    )

    def profile_has_current_promotion(profile: DestinationProfile) -> bool:
        if not profile.home_university:
            return False
        return (
            _profile_identity_key(profile.home_university, profile.school_name),
            destination_profile_content_hash(profile),
        ) in promoted_source_hashes

    pending = [
        profile
        for profile in selected
        if profile.coverage_status != "official_verified"
        and not profile_has_current_promotion(profile)
    ]
    pending_with_gaps = [
        (profile, _review_gap_codes(profile))
        for profile in pending
    ]
    pending_with_gaps.sort(
        key=lambda pair: (
            -len(pair[1]),
            pair[0].last_checked.isoformat() if pair[0].last_checked else "",
            *_profile_sort_key(pair[0]),
        )
    )
    items: list[DestinationProfileReviewRow] = []
    for index, (profile, gaps) in enumerate(pending_with_gaps, start=1):
        identity = _profile_identity_key(
            profile.home_university or "",
            profile.school_name,
        )
        profile_hash = destination_profile_content_hash(profile)
        review_history = _profile_review_history(
            profile,
            events,
            not_before=review_invalidated_after.get((identity, profile_hash)),
        )
        current_reviews = _current_profile_reviews(review_history)
        approvals = [
            review
            for review in current_reviews
            if review.decision == DestinationProfileReviewDecision.APPROVE
        ]
        change_requests = [
            review
            for review in current_reviews
            if review.decision == DestinationProfileReviewDecision.CHANGES_REQUIRED
        ]
        ready = len(approvals) >= 2 and not change_requests
        if change_requests:
            progress = "changes_required"
        elif ready:
            progress = "ready_for_promotion"
        elif approvals:
            progress = "partial"
        else:
            progress = "unstarted"
        current_reviewer_review = next(
            (
                review
                for review in current_reviews
                if current_reviewer_id
                and review.reviewer_id.casefold() == current_reviewer_id.casefold()
            ),
            None,
        )
        items.append(
            DestinationProfileReviewRow(
                snapshot_fingerprint=fingerprint,
                priority_order=index,
                home_university=profile.home_university or "待確認",
                school_name=profile.school_name,
                country=profile.country,
                city=profile.city,
                coverage_status=profile.coverage_status,
                review_gap_codes=gaps,
                last_checked=profile.last_checked,
                source_count=len(profile.sources),
                source_titles=[source.title for source in profile.sources],
                source_urls=[source.source_url for source in profile.sources],
                coverage_note=profile.coverage_note,
                profile_content_hash=profile_hash,
                profile=profile,
                review_history=review_history,
                current_reviews=current_reviews,
                review_approval_count=len(approvals),
                review_change_request_count=len(change_requests),
                review_progress=progress,
                current_reviewer_decision=(
                    current_reviewer_review.decision
                    if current_reviewer_review
                    else None
                ),
                ready_for_promotion=ready,
            )
        )
    return DestinationProfileReviewQueue(
        snapshot_fingerprint=fingerprint,
        home_university=home_university,
        home_universities=sorted(
            {
                profile.home_university
                for profile in selected
                if profile.home_university
            },
            key=str.casefold,
        ),
        total_profile_count=len(selected),
        verified_profile_count=sum(
            profile.coverage_status == "official_verified"
            or profile_has_current_promotion(profile)
            for profile in selected
        ),
        pending_review_count=len(items),
        explicit_second_review_required_count=sum(
            _SECOND_REVIEW_NOTICE in profile.coverage_note
            for profile in pending
        ),
        total_source_count=sum(len(profile.sources) for profile in selected),
        pending_source_count=sum(len(profile.sources) for profile in pending),
        review_started_profile_count=sum(bool(item.current_reviews) for item in items),
        ready_for_promotion_count=sum(item.ready_for_promotion for item in items),
        change_requested_profile_count=sum(
            item.review_progress == "changes_required" for item in items
        ),
        current_review_event_count=sum(len(item.current_reviews) for item in items),
        review_sections=list(REQUIRED_DESTINATION_PROFILE_REVIEW_SECTIONS),
        items=items,
    )


def destination_profile_review_content_fingerprint(
    queue: DestinationProfileReviewQueue,
) -> str:
    """Hash pending membership and content while excluding review progress."""

    canonical = json.dumps(
        {
            "review_batch_schema_version": _DESTINATION_REVIEW_BATCH_SCHEMA_VERSION,
            "home_university": queue.home_university,
            "profiles": [
                {
                    "home_university": item.home_university,
                    "school_name": item.school_name,
                    "profile_content_hash": item.profile_content_hash,
                }
                for item in queue.items
            ],
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_destination_profile_review_batch_rows(
    queue: DestinationProfileReviewQueue,
    *,
    batch_size: int = 10,
) -> list[DestinationProfileReviewBatchRow]:
    """Split one university's live queue into deterministic review batches."""

    if not 1 <= batch_size <= 50:
        raise ValueError("每個生活情報審查批次必須包含 1 至 50 筆資料。")
    if queue.home_university is None and queue.items:
        raise ValueError("生活情報審查批次必須指定一所母校。")
    review_fingerprint = destination_profile_review_content_fingerprint(queue)
    rows: list[DestinationProfileReviewBatchRow] = []
    for index, item in enumerate(queue.items):
        batch_number = index // batch_size + 1
        batch_start = (batch_number - 1) * batch_size
        batch_profile_count = min(batch_size, len(queue.items) - batch_start)
        batch_id = (
            f"destination-{review_fingerprint[:12]}-"
            f"{batch_size:03d}-{batch_number:03d}"
        )
        batch_workbench_path = "/admin/content-review?" + urlencode(
            {
                "destination_home": item.home_university,
                "destination_batch": batch_id,
                "destination_batch_size": batch_size,
                "destination_snapshot": review_fingerprint,
            }
        )
        batch_checklist_path = (
            "/admin/destination-profile-review-batches/"
            f"{batch_id}/checklist.csv?"
            + urlencode(
                {
                    "home_university": item.home_university,
                    "batch_size": batch_size,
                    "expected_snapshot": review_fingerprint,
                }
            )
        )
        rows.append(
            DestinationProfileReviewBatchRow(
                queue_snapshot_fingerprint=queue.snapshot_fingerprint,
                review_content_fingerprint=review_fingerprint,
                batch_id=batch_id,
                batch_number=batch_number,
                batch_profile_count=batch_profile_count,
                batch_position=index % batch_size + 1,
                priority_order=item.priority_order,
                home_university=item.home_university,
                school_name=item.school_name,
                country=item.country,
                city=item.city,
                coverage_status=item.coverage_status,
                review_gap_codes=item.review_gap_codes,
                source_count=item.source_count,
                source_titles=item.source_titles,
                source_urls=item.source_urls,
                coverage_note=item.coverage_note,
                profile_content_hash=item.profile_content_hash,
                review_approval_count=item.review_approval_count,
                review_change_request_count=item.review_change_request_count,
                required_review_count=item.required_review_count,
                review_progress=item.review_progress,
                ready_for_promotion=item.ready_for_promotion,
                batch_workbench_path=batch_workbench_path,
                batch_checklist_path=batch_checklist_path,
                student_view_path=item.student_view_path,
            )
        )
    return rows


def _unique_destination_source_urls(values: list[str]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = value.strip()
        key = normalized.casefold()
        if normalized and key not in seen:
            seen.add(key)
            output.append(normalized)
    return output


def _destination_checklist_items_content(items: list[object]) -> tuple[str, list[str]]:
    if not items:
        return "目前沒有項目；須確認確實不適用或仍待補齊。", []
    details: list[str] = []
    source_urls: list[str] = []
    for item in items:
        item_sources = list(getattr(item, "source_urls", []) or [])
        source_urls.extend(item_sources)
        details.append(
            "｜".join(
                [
                    str(getattr(item, "title", "未命名項目")),
                    str(getattr(item, "detail", "未提供內容")),
                    f"時間：{getattr(item, 'timing', None) or '待確認'}",
                    f"證據：{getattr(item, 'evidence_type', None) or '待確認'}",
                    f"來源：{'、'.join(item_sources) if item_sources else '未列'}",
                ]
            )
        )
    return " || ".join(details), _unique_destination_source_urls(source_urls)


def _destination_profile_review_section_content(
    profile: DestinationProfile,
    section_key: str,
) -> tuple[str, list[str]]:
    if section_key == "identity_location":
        return (
            "；".join(
                [
                    f"母校：{profile.home_university or '待確認'}",
                    f"合作校：{profile.school_name}",
                    f"國家：{profile.country or '待確認'}",
                    f"城市／校區：{profile.city or '待確認'}",
                ]
            ),
            [],
        )
    if section_key == "cost":
        return profile.cost_summary or "目前未提供生活費內容。", []
    if section_key == "housing":
        return profile.housing_summary or "目前未提供住宿內容。", []
    if section_key == "transport":
        return profile.transport_summary or "目前未提供交通內容。", []
    if section_key == "campus_life":
        return profile.campus_life_summary or "目前未提供校園生活內容。", []
    if section_key == "student_guide":
        details: list[str] = []
        source_urls: list[str] = []
        for section in profile.student_guide_sections:
            source_urls.extend(section.source_urls)
            details.append(
                "｜".join(
                    [
                        section.title,
                        section.summary,
                        f"重點：{'、'.join(section.points) if section.points else '未列'}",
                        f"證據：{section.evidence_type}",
                        f"警語：{section.caution or '未列'}",
                        f"來源：{'、'.join(section.source_urls) if section.source_urls else '未列'}",
                    ]
                )
            )
        for photo in profile.guide_photos:
            source_urls.append(photo.source_url)
            details.append(
                "｜".join(
                    [
                        f"照片：{photo.alt}",
                        photo.caption,
                        f"圖片：{photo.image_url}",
                        f"來源：{photo.source_url}",
                    ]
                )
            )
        return (
            " || ".join(details) if details else "目前沒有生活指南段落或照片。",
            _unique_destination_source_urls(source_urls),
        )
    if section_key == "first_72_hours":
        return _destination_checklist_items_content(profile.first_72_hours)
    if section_key == "packing":
        return _destination_checklist_items_content(profile.packing_from_taiwan)
    if section_key == "buy_after_arrival":
        return _destination_checklist_items_content(profile.buy_after_arrival)
    if section_key == "coverage_boundary":
        return (
            f"查核狀態：{profile.coverage_status}；查核註記：{profile.coverage_note}",
            [],
        )
    if section_key == "official_sources":
        details = []
        for source in profile.sources:
            category = getattr(source.category, "value", source.category)
            details.append(
                "｜".join(
                    [
                        source.title,
                        source.source_url,
                        f"分類：{category or '未分類'}",
                        f"摘要：{source.summary or '未提供'}",
                    ]
                )
            )
        return (
            " || ".join(details) if details else "目前沒有官方來源。",
            [source.source_url for source in profile.sources],
        )
    if section_key == "last_checked":
        return (
            profile.last_checked.isoformat()
            if profile.last_checked is not None
            else "目前未提供最後查核時間。",
            [],
        )
    raise ValueError(f"未知的生活情報審查區塊：{section_key}")


def build_destination_profile_review_batch_checklist_rows(
    queue: DestinationProfileReviewQueue,
    *,
    batch_id: str,
    batch_size: int = 10,
) -> list[DestinationProfileReviewBatchChecklistRow]:
    """Expand one live batch into every source and fixed section reviewers attest."""

    batch_rows = [
        row
        for row in build_destination_profile_review_batch_rows(
            queue,
            batch_size=batch_size,
        )
        if row.batch_id == batch_id
    ]
    if not batch_rows:
        return []
    queue_items = {row.profile_content_hash: row for row in queue.items}
    output: list[DestinationProfileReviewBatchChecklistRow] = []
    for batch_row in batch_rows:
        queue_item = queue_items.get(batch_row.profile_content_hash)
        if queue_item is None:
            raise ValueError(
                "產生生活情報逐項查核表期間 profile 已變更；請重新下載。"
            )
        profile = queue_item.profile
        checklist_position = 0
        for source_index, source in enumerate(profile.sources, start=1):
            checklist_position += 1
            category = getattr(source.category, "value", source.category)
            output.append(
                DestinationProfileReviewBatchChecklistRow(
                    queue_snapshot_fingerprint=queue.snapshot_fingerprint,
                    review_content_fingerprint=(
                        batch_row.review_content_fingerprint
                    ),
                    batch_id=batch_row.batch_id,
                    batch_number=batch_row.batch_number,
                    batch_position=batch_row.batch_position,
                    checklist_position=checklist_position,
                    home_university=batch_row.home_university,
                    school_name=batch_row.school_name,
                    country=batch_row.country,
                    city=batch_row.city,
                    profile_content_hash=batch_row.profile_content_hash,
                    item_type="official_source",
                    item_key=f"source:{source_index:03d}",
                    item_label=source.title,
                    item_description=(
                        "逐一開啟並確認來源仍可存取、為官方頁，且直接支持目前敘述。"
                    ),
                    candidate_content=(
                        f"分類：{category or '未分類'}；"
                        f"摘要：{source.summary or '未提供'}"
                    ),
                    source_urls=[source.source_url],
                    batch_workbench_path=batch_row.batch_workbench_path,
                    student_view_path=batch_row.student_view_path,
                )
            )
        for section in REQUIRED_DESTINATION_PROFILE_REVIEW_SECTIONS:
            checklist_position += 1
            candidate_content, source_urls = (
                _destination_profile_review_section_content(profile, section.key)
            )
            output.append(
                DestinationProfileReviewBatchChecklistRow(
                    queue_snapshot_fingerprint=queue.snapshot_fingerprint,
                    review_content_fingerprint=(
                        batch_row.review_content_fingerprint
                    ),
                    batch_id=batch_row.batch_id,
                    batch_number=batch_row.batch_number,
                    batch_position=batch_row.batch_position,
                    checklist_position=checklist_position,
                    home_university=batch_row.home_university,
                    school_name=batch_row.school_name,
                    country=batch_row.country,
                    city=batch_row.city,
                    profile_content_hash=batch_row.profile_content_hash,
                    item_type="content_section",
                    item_key=section.key,
                    item_label=section.label,
                    item_description=section.description,
                    candidate_content=candidate_content,
                    source_urls=source_urls,
                    batch_workbench_path=batch_row.batch_workbench_path,
                    student_view_path=batch_row.student_view_path,
                )
            )
    return output


def record_destination_profile_review(
    store: DestinationProfileReviewStore,
    profiles: list[DestinationProfile],
    request: DestinationProfileReviewSubmitRequest,
    *,
    reviewer_id: str,
    reviewer_display_name: str,
) -> DestinationProfileReviewEvent:
    queue = build_destination_profile_review_queue(
        profiles,
        home_university=request.home_university,
        review_events=store.list_events(),
        promotion_events=store.list_promotion_events(),
        rollback_events=store.list_rollback_events(),
        current_reviewer_id=reviewer_id,
    )
    if request.expected_snapshot != queue.snapshot_fingerprint:
        raise DestinationProfileReviewConflictError(
            "這份生活情報審查畫面已過期；請重新載入目前內容。"
        )
    target = next(
        (
            item
            for item in queue.items
            if school_identity_key(item.school_name)
            == school_identity_key(request.school_name)
        ),
        None,
    )
    if target is None:
        raise ValueError("找不到這筆待審生活情報，或它已完成資料升級。")
    if request.expected_profile_content_hash != target.profile_content_hash:
        raise DestinationProfileReviewConflictError(
            "這筆生活情報內容已變更；請重新開啟並逐項核對。"
        )
    expected_sources = [source.source_url for source in target.profile.sources]
    submitted_sources = [value.strip() for value in request.reviewed_source_urls]
    if (
        len(submitted_sources) != len(expected_sources)
        or {value.casefold() for value in submitted_sources}
        != {value.casefold() for value in expected_sources}
    ):
        raise ValueError("必須逐一核對並提交目前版本的全部官方來源。")
    submitted_sections = [value.strip() for value in request.reviewed_section_keys]
    if (
        len(submitted_sections) != len(_REQUIRED_SECTION_KEYS)
        or set(submitted_sections) != set(_REQUIRED_SECTION_KEYS)
    ):
        raise ValueError("必須逐項核對這筆生活情報的全部內容區塊。")
    if request.decision == DestinationProfileReviewDecision.APPROVE:
        blocking_gaps = {
            "missing_sources",
            "insecure_sources",
            "missing_last_checked",
        }.intersection(target.review_gap_codes)
        if blocking_gaps:
            raise ValueError(
                "這筆資料仍缺官方來源、安全網址或查核時間，只能要求修正。"
            )
    previous = next(
        (
            event
            for event in target.current_reviews
            if event.reviewer_id.casefold() == reviewer_id.casefold()
        ),
        None,
    )
    normalized_note = request.note.strip()
    normalized_sources = expected_sources
    normalized_sections = list(_REQUIRED_SECTION_KEYS)
    if (
        previous
        and previous.decision == request.decision
        and previous.note == normalized_note
        and previous.reviewed_source_urls == normalized_sources
        and previous.reviewed_section_keys == normalized_sections
    ):
        return previous
    event = DestinationProfileReviewEvent(
        home_university=target.home_university,
        school_name=target.school_name,
        profile_content_hash=target.profile_content_hash,
        snapshot_fingerprint=queue.snapshot_fingerprint,
        reviewer_id=reviewer_id,
        reviewer_display_name=reviewer_display_name,
        decision=request.decision,
        note=normalized_note,
        reviewed_source_urls=normalized_sources,
        reviewed_section_keys=normalized_sections,
        reviewed_at=utc_now(),
        supersedes_event_id=previous.id if previous else None,
    )
    return store.save_event(event)


def _promoted_coverage_note(profile: DestinationProfile) -> str:
    original = profile.coverage_note.replace(_SECOND_REVIEW_NOTICE, "")
    original = original.strip(" \t\r\n；;，,。")
    promotion_note = (
        "已由兩位不同內容審查者逐一核對全部官方來源與內容區塊，"
        "並由內容負責人確認升級；仍請以最新官方公告為準。"
    )
    return f"{original}；{promotion_note}" if original else promotion_note


def promote_destination_profile(
    store: DestinationProfileReviewStore,
    profiles: list[DestinationProfile],
    request: DestinationProfilePromotionRequest,
    *,
    promoted_by_id: str,
    promoted_by_display_name: str,
) -> DestinationProfilePromotionEvent:
    promotions = store.list_promotion_events()
    rollbacks = store.list_rollback_events()
    identity = _profile_identity_key(
        request.home_university,
        request.school_name,
    )
    publication_history = build_destination_profile_publication_history(
        profiles,
        promotions,
        rollbacks,
        home_university=request.home_university,
    )
    publication_state = next(
        (
            item
            for item in publication_history.items
            if _profile_identity_key(item.home_university, item.school_name)
            == identity
        ),
        None,
    )
    if publication_state and publication_state.active_promotion_event_id:
        active = next(
            event
            for event in promotions
            if event.id == publication_state.active_promotion_event_id
        )
        if (
            active.source_profile_content_hash
            == request.expected_profile_content_hash
        ):
            return active

    queue = build_destination_profile_review_queue(
        profiles,
        home_university=request.home_university,
        review_events=store.list_events(),
        promotion_events=promotions,
        rollback_events=rollbacks,
        current_reviewer_id=promoted_by_id,
    )
    if request.expected_snapshot != queue.snapshot_fingerprint:
        raise DestinationProfileReviewConflictError(
            "這份生活情報升級畫面已過期；請重新載入目前內容。"
        )
    target = next(
        (
            item
            for item in queue.items
            if school_identity_key(item.school_name)
            == school_identity_key(request.school_name)
        ),
        None,
    )
    if target is None:
        raise ValueError("找不到這筆可升級的生活情報，或它已完成升級。")
    if request.expected_profile_content_hash != target.profile_content_hash:
        raise DestinationProfileReviewConflictError(
            "這筆生活情報內容已變更；請重新確認雙審證據。"
        )
    if not target.ready_for_promotion:
        raise ValueError("必須先有兩位不同審查者核可，且目前不能有修正要求。")
    approvals = [
        review
        for review in target.current_reviews
        if review.decision == DestinationProfileReviewDecision.APPROVE
    ]
    if promoted_by_id.casefold() not in {
        review.reviewer_id.casefold() for review in approvals
    }:
        raise ValueError("內容負責人必須是目前兩位有效核可者之一。")
    promoted_profile = target.profile.model_copy(
        update={
            "coverage_status": "official_verified",
            "coverage_note": _promoted_coverage_note(target.profile),
            "last_checked": max(review.reviewed_at for review in approvals),
        }
    )
    promoted_hash = destination_profile_content_hash(promoted_profile)
    event = DestinationProfilePromotionEvent(
        home_university=target.home_university,
        school_name=target.school_name,
        source_profile_content_hash=target.profile_content_hash,
        promoted_profile_content_hash=promoted_hash,
        snapshot_fingerprint=queue.snapshot_fingerprint,
        review_event_ids=[review.id for review in approvals],
        reviewer_ids=[review.reviewer_id for review in approvals],
        promoted_by_id=promoted_by_id,
        promoted_by_display_name=promoted_by_display_name,
        note=request.note.strip(),
        promoted_at=utc_now(),
        promoted_profile=promoted_profile,
    )
    return store.save_promotion_event(event)


def rollback_destination_profile(
    store: DestinationProfileReviewStore,
    profiles: list[DestinationProfile],
    request: DestinationProfileRollbackRequest,
    *,
    rolled_back_by_id: str,
    rolled_back_by_display_name: str,
) -> DestinationProfileRollbackEvent:
    promotions = store.list_promotion_events()
    rollbacks = store.list_rollback_events()
    identity = _profile_identity_key(
        request.home_university,
        request.school_name,
    )
    existing = next(
        (
            event
            for event in rollbacks
            if _profile_identity_key(
                event.home_university,
                event.school_name,
            )
            == identity
            and event.rolled_back_from_event_id
            == request.expected_latest_publication_event_id
        ),
        None,
    )
    if existing:
        return existing
    history = build_destination_profile_publication_history(
        profiles,
        promotions,
        rollbacks,
        home_university=request.home_university,
    )
    state = next(
        (
            item
            for item in history.items
            if _profile_identity_key(item.home_university, item.school_name)
            == identity
        ),
        None,
    )
    if state is None or not state.can_rollback:
        raise ValueError("目前沒有可復原的生活情報升級版本。")
    if (
        state.active_promotion_event_id
        != request.expected_active_promotion_event_id
        or state.latest_event_id
        != request.expected_latest_publication_event_id
    ):
        raise DestinationProfileReviewConflictError(
            "生活情報公開歷程已變更；請重新載入目前版本。"
        )
    if (
        state.current_public_profile_content_hash
        != request.expected_public_profile_content_hash
    ):
        raise DestinationProfileReviewConflictError(
            "學生目前看到的生活情報已變更；請重新確認後再復原。"
        )
    candidate = next(
        (
            profile
            for profile in profiles
            if profile.home_university
            and _profile_identity_key(
                profile.home_university,
                profile.school_name,
            )
            == identity
        ),
        None,
    )
    if candidate is None:
        raise ValueError("找不到這筆生活情報目前的候選資料。")
    profile_promotions = [
        event
        for event in promotions
        if _profile_identity_key(event.home_university, event.school_name)
        == identity
    ]
    profile_rollbacks = [
        event
        for event in rollbacks
        if _profile_identity_key(event.home_university, event.school_name)
        == identity
    ]
    restored_profile, restored_promotion, _ = _resolve_profile_publication_state(
        candidate,
        profile_promotions,
        profile_rollbacks,
        stop_before_event_id=state.active_promotion_event_id,
    )
    event = DestinationProfileRollbackEvent(
        home_university=state.home_university,
        school_name=state.school_name,
        rolled_back_from_event_id=state.latest_event_id or "",
        rolled_back_promotion_event_id=state.active_promotion_event_id,
        restored_promotion_event_id=(
            restored_promotion.id if restored_promotion else None
        ),
        previous_profile_content_hash=state.current_public_profile_content_hash,
        restored_profile_content_hash=destination_profile_content_hash(
            restored_profile
        ),
        rolled_back_by_id=rolled_back_by_id,
        rolled_back_by_display_name=rolled_back_by_display_name,
        note=request.note.strip(),
        rolled_back_at=utc_now(),
        restored_profile=restored_profile,
    )
    return store.save_rollback_event(event)
