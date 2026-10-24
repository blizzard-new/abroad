from __future__ import annotations

from typing import Any


TEXT_SEARCH_BACKENDS = ("brave", "yahoo")


def search_text(
    query: str,
    *,
    max_results: int,
    timeout_seconds: float,
) -> list[dict[str, Any]]:
    """Search bounded backends sequentially and merge unique results.

    DDGS automatic mode can wait for every provider thread after its public
    timeout has elapsed. Selecting one backend per request keeps one slow
    provider from stalling an entire partner-school research batch.
    """
    try:
        from .search_transport import RequestsDDGS as DDGS
    except ImportError:
        return []
    client = DDGS(timeout=max(1, int(timeout_seconds)))
    try:
        backend_rows: list[list[dict[str, Any]]] = []
        for backend in TEXT_SEARCH_BACKENDS:
            try:
                rows = client.text(
                    query,
                    region="wt-wt",
                    safesearch="moderate",
                    max_results=max(3, max_results),
                    backend=backend,
                )
            except Exception:
                continue
            if rows:
                backend_rows.append(list(rows))
        merged: dict[str, dict[str, Any]] = {}
        longest = max((len(rows) for rows in backend_rows), default=0)
        for index in range(longest):
            for rows in backend_rows:
                if index >= len(rows):
                    continue
                row = rows[index]
                url = str(row.get("href") or row.get("url") or "").strip()
                key = url or f"{row.get('title', '')}|{row.get('body', '')}"
                if key and key not in merged:
                    merged[key] = row
                if len(merged) >= max(1, max_results):
                    return list(merged.values())
        return list(merged.values())[: max(1, max_results)]
    finally:
        client.close()


def search_videos(
    query: str,
    *,
    max_results: int,
    timeout_seconds: float,
) -> list[dict[str, Any]]:
    try:
        from .search_transport import RequestsDDGS as DDGS
    except ImportError:
        return []
    try:
        with DDGS(timeout=max(1, int(timeout_seconds))) as client:
            return list(client.videos(
                query,
                region="wt-wt",
                safesearch="moderate",
                max_results=max_results,
                backend="duckduckgo",
            ))
    except Exception:
        return []
