from __future__ import annotations

import hashlib
import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import requests

from .ai_gateway import ai_embedding_model, ai_enabled, ai_provider_name, embed_texts
from .models import DocumentChunk, ProcessedPage, RagIndexStatus, RagSearchHit
from .settings import DEFAULT_DATA_DIR
from .storage import data_paths, load_document_chunks, save_document_chunks


MAX_CHUNK_CHARS = 900
CHUNK_OVERLAP_CHARS = 120
EMBEDDING_BATCH_SIZE = 100


def build_rag_index(
    pages: list[ProcessedPage],
    data_dir: Path = DEFAULT_DATA_DIR,
    *,
    use_embeddings: bool = True,
    sync_supabase: bool = True,
) -> RagIndexStatus:
    chunks = build_document_chunks(pages)
    previous = {row.id: row for row in load_document_chunks(data_dir)}
    embedding_model = ai_embedding_model() if use_embeddings and ai_enabled() else ""

    pending_indexes: list[int] = []
    for index, chunk in enumerate(chunks):
        cached = previous.get(chunk.id)
        if (
            cached
            and cached.content_hash == chunk.content_hash
            and cached.embedding
            and cached.embedding_model == embedding_model
        ):
            chunks[index] = chunk.model_copy(
                update={
                    "embedding": cached.embedding,
                    "embedding_model": cached.embedding_model,
                }
            )
        elif embedding_model:
            pending_indexes.append(index)

    for start in range(0, len(pending_indexes), EMBEDDING_BATCH_SIZE):
        indexes = pending_indexes[start : start + EMBEDDING_BATCH_SIZE]
        vectors = embed_texts([chunks[index].text for index in indexes])
        if vectors is None or len(vectors) != len(indexes):
            break
        for index, vector in zip(indexes, vectors, strict=True):
            chunks[index] = chunks[index].model_copy(
                update={"embedding": vector, "embedding_model": embedding_model}
            )

    save_document_chunks(chunks, data_dir)
    if sync_supabase and supabase_configured():
        _sync_supabase(chunks)
    return rag_index_status(data_dir)


def build_document_chunks(pages: Iterable[ProcessedPage]) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []
    for page in pages:
        content = "\n\n".join(
            value.strip()
            for value in (page.summary, page.text)
            if value and value.strip()
        )
        seen: set[str] = set()
        for index, text in enumerate(split_document_text(content), start=1):
            normalized = _compact(text)
            if (
                len(normalized) < 20
                or normalized in seen
                or not _is_outbound_chunk(page, normalized)
            ):
                continue
            seen.add(normalized)
            digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
            identity = f"{page.source_url}|{page.content_hash}|{index}|{digest}"
            chunks.append(
                DocumentChunk(
                    id=hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24],
                    source_url=page.source_url,
                    source_title=page.title,
                    section=f"{_category_label(page.category.value)} {index}",
                    text=normalized,
                    published_at=page.published_at,
                    last_checked=page.crawled_at,
                    category=page.category,
                    content_hash=digest,
                )
            )
    return chunks


def split_document_text(
    text: str,
    *,
    max_chars: int = MAX_CHUNK_CHARS,
    overlap_chars: int = CHUNK_OVERLAP_CHARS,
) -> list[str]:
    normalized = re.sub(r"[ \t]+", " ", str(text or ""))
    normalized = re.sub(r"\n{3,}", "\n\n", normalized).strip()
    if not normalized:
        return []

    units: list[str] = []
    for paragraph in re.split(r"\n\s*\n|\n", normalized):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        if len(paragraph) <= max_chars:
            units.append(paragraph)
            continue
        units.extend(
            part.strip()
            for part in re.split(r"(?<=[。！？；.!?;])\s*", paragraph)
            if part.strip()
        )

    chunks: list[str] = []
    current = ""
    for unit in units:
        if len(unit) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            step = max(1, max_chars - overlap_chars)
            chunks.extend(unit[start : start + max_chars] for start in range(0, len(unit), step))
            continue
        candidate = f"{current}\n{unit}".strip() if current else unit
        if len(candidate) <= max_chars:
            current = candidate
            continue
        chunks.append(current)
        overlap = current[-overlap_chars:] if overlap_chars else ""
        current = f"{overlap}\n{unit}".strip()
        if len(current) > max_chars:
            current = unit
    if current:
        chunks.append(current)
    return chunks


def search_document_chunks(
    question: str,
    data_dir: Path = DEFAULT_DATA_DIR,
    *,
    pages: list[ProcessedPage] | None = None,
    limit: int = 8,
) -> list[RagSearchHit]:
    chunks = load_document_chunks(data_dir)
    if not chunks and pages:
        build_rag_index(pages, data_dir, use_embeddings=False, sync_supabase=False)
        chunks = load_document_chunks(data_dir)
    if not chunks:
        return []

    query_vector: list[float] | None = None
    if any(chunk.embedding for chunk in chunks) and ai_enabled():
        embedded = embed_texts([question])
        if embedded:
            query_vector = embedded[0]

    if query_vector and supabase_configured():
        remote = _search_supabase(query_vector, limit=limit)
        if remote:
            return remote
    return _search_local(question, chunks, query_vector=query_vector, limit=limit)


def rag_index_status(data_dir: Path = DEFAULT_DATA_DIR) -> RagIndexStatus:
    chunks = load_document_chunks(data_dir)
    path = data_paths(data_dir)["document_chunks"]
    built_at = (
        datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        if path.exists()
        else None
    )
    embedded = [chunk for chunk in chunks if chunk.embedding]
    return RagIndexStatus(
        store="supabase_pgvector" if supabase_configured() else "local_jsonl",
        chunk_count=len(chunks),
        embedded_count=len(embedded),
        source_count=len({chunk.source_url for chunk in chunks}),
        built_at=built_at,
        embedding_model=(embedded[0].embedding_model if embedded else None),
        provider=ai_provider_name(),
    )


def supabase_configured() -> bool:
    return bool(
        os.environ.get("SUPABASE_URL", "").strip()
        and os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    )


def _search_local(
    question: str,
    chunks: list[DocumentChunk],
    *,
    query_vector: list[float] | None,
    limit: int,
) -> list[RagSearchHit]:
    terms = _query_terms(question)
    candidates: list[tuple[float, str, DocumentChunk]] = []
    for chunk in chunks:
        keyword_raw = _keyword_score(terms, chunk)
        keyword_score = min(1.0, keyword_raw / 18.0)
        semantic_score = 0.0
        if query_vector and chunk.embedding and len(query_vector) == len(chunk.embedding):
            semantic_score = max(0.0, _cosine_similarity(query_vector, chunk.embedding))

        if semantic_score and keyword_score:
            score = 0.72 * semantic_score + 0.28 * keyword_score
            match_type = "hybrid"
        elif semantic_score:
            score = semantic_score
            match_type = "semantic"
        else:
            score = keyword_score
            match_type = "keyword"

        threshold = 0.24 if semantic_score else 0.01
        if score >= threshold and (keyword_raw > 0 or semantic_score >= 0.30):
            candidates.append((score, match_type, chunk))

    candidates.sort(key=lambda row: (-row[0], row[2].source_title.casefold()))
    return [
        RagSearchHit(chunk=chunk, score=min(1.0, score), match_type=match_type)
        for score, match_type, chunk in candidates[: max(1, limit)]
    ]


def _keyword_score(terms: set[str], chunk: DocumentChunk) -> float:
    title = _normal(chunk.source_title)
    section = _normal(chunk.section)
    body = _normal(chunk.text)
    return sum(
        (7 if term in title else 0)
        + (3 if term in section else 0)
        + (1 if term in body else 0)
        for term in terms
    )


def _query_terms(question: str) -> set[str]:
    value = _normal(question)
    terms = set(re.findall(r"[a-z0-9][a-z0-9._+-]{1,}|[\u4e00-\u9fff]{2,}", value))
    for term in list(terms):
        if re.fullmatch(r"[\u4e00-\u9fff]+", term):
            for size in (2, 3, 4):
                terms.update(
                    term[index : index + size]
                    for index in range(max(0, len(term) - size + 1))
                )
    expansions = {
        "文件": {"申請表", "同意書", "計畫書", "成績單", "推薦信"},
        "資格": {"成績", "學制", "學院", "門檻"},
        "英文": {"語言", "toeic", "ielts", "toefl", "duolingo"},
        "補助": {"獎學金", "學海", "領航者", "經費"},
        "截止": {"期限", "申請期間", "日期"},
        "住宿": {"宿舍", "租屋", "housing"},
        "費用": {"生活費", "預算", "學費", "cost"},
        "流程": {"申請步驟", "提名", "送件"},
    }
    for trigger, additions in expansions.items():
        if trigger in value:
            terms.update(additions)
    return {term for term in terms if len(term) >= 2}


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        return 0.0
    return numerator / (left_norm * right_norm)


def _sync_supabase(chunks: list[DocumentChunk]) -> bool:
    rows = [_supabase_row(chunk) for chunk in chunks if chunk.embedding]
    if not rows:
        return False
    url, headers = _supabase_connection()
    try:
        for start in range(0, len(rows), 100):
            response = requests.post(
                f"{url}/rest/v1/document_chunks?on_conflict=id",
                headers={**headers, "Prefer": "resolution=merge-duplicates"},
                json=rows[start : start + 100],
                timeout=45,
            )
            response.raise_for_status()
    except requests.RequestException:
        return False
    return True


def _search_supabase(query_vector: list[float], *, limit: int) -> list[RagSearchHit]:
    url, headers = _supabase_connection()
    try:
        response = requests.post(
            f"{url}/rest/v1/rpc/match_document_chunks",
            headers=headers,
            json={
                "query_embedding": query_vector,
                "match_threshold": 0.24,
                "match_count": max(1, limit),
                "filter_school": "長庚大學",
            },
            timeout=20,
        )
        response.raise_for_status()
        rows = response.json()
    except (requests.RequestException, ValueError):
        return []
    hits: list[RagSearchHit] = []
    for row in rows if isinstance(rows, list) else []:
        try:
            score = float(row.pop("similarity"))
            chunk = DocumentChunk.model_validate(row)
            hits.append(RagSearchHit(chunk=chunk, score=score, match_type="semantic"))
        except (KeyError, TypeError, ValueError):
            continue
    return hits


def _supabase_connection() -> tuple[str, dict[str, str]]:
    url = os.environ.get("SUPABASE_URL", "").strip().rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    return url, {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def _supabase_row(chunk: DocumentChunk) -> dict[str, object]:
    return {
        "id": chunk.id,
        "school_name": chunk.school_name,
        "source_url": chunk.source_url,
        "source_title": chunk.source_title,
        "section": chunk.section,
        "text": chunk.text,
        "published_at": chunk.published_at,
        "last_checked": chunk.last_checked.isoformat(),
        "category": chunk.category.value,
        "content_hash": chunk.content_hash,
        "embedding": chunk.embedding,
        "embedding_model": chunk.embedding_model,
    }


def _category_label(value: str) -> str:
    return {
        "exchange_application": "交換申請",
        "scholarship": "補助與獎學金",
        "partner_school": "合作學校",
        "experience_report": "出國心得",
        "faq": "常見問題",
        "info_session": "說明會",
        "deadline": "截止日期",
    }.get(value, "官方資料")


def _is_outbound_chunk(page: ProcessedPage, text: str) -> bool:
    title = _normal(page.title)
    body = _normal(text)
    incoming_markers = (
        "境外生申請入學",
        "來長庚交換",
        "外國學生來臺",
        "在台就學",
        "在臺就學",
        "入境台灣",
        "入境臺灣",
        "外僑居留",
        "預計在台停留",
        "預計在臺停留",
        "長庚大學核發的入學",
        "原屬學校之國際事務",
        "離開長庚大學",
    )
    if any(marker in title or marker in body for marker in incoming_markers):
        return False
    if "簽證資訊" in title and any(
        marker in body for marker in ("居留簽證", "停留簽證", "外僑", "入境")
    ):
        return False

    generic_title = title in {"國際事務處", "最新公告", "國際處公告"}
    outbound_markers = (
        "出國",
        "赴外",
        "海外",
        "國外學校",
        "交換申請",
        "校內申請",
        "選送",
        "合作學校",
        "合作校",
        "雙聯",
        "雙學位",
        "學海",
        "短期學分",
        "海外實習",
        "返國",
    )
    if generic_title and not any(marker in body for marker in outbound_markers):
        return False
    return True


def _normal(value: object) -> str:
    return re.sub(r"\s+", "", str(value or "")).casefold()


def _compact(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()
