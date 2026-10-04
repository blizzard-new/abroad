from __future__ import annotations

import json
import os
from typing import Any, Literal, Protocol, Sequence

import requests

from .local_ai import LocalGemmaProvider, create_local_prototype_provider


RESPONSES_URL = "https://api.openai.com/v1/responses"
EMBEDDINGS_URL = "https://api.openai.com/v1/embeddings"
ModelTier = Literal["fast", "advanced"]
AI_RUNTIME_STATE = "paused"
AI_RUNTIME_PAUSED_REASON = (
    "AI API 與本地 AI 目前暫緩；本機 provider 基礎已建立但尚未接入產品，"
    "伺服器仍只執行規則與來源整理。"
)


class LLMProvider(Protocol):
    """Small provider boundary so application code is not tied to one vendor."""

    name: str
    fast_model: str
    advanced_model: str
    embedding_model: str

    def structured_output(
        self,
        *,
        schema_name: str,
        schema: dict[str, Any],
        instructions: str,
        input_text: str,
        tier: ModelTier = "fast",
        timeout: float = 35,
    ) -> dict[str, Any] | None: ...

    def embed(
        self,
        texts: Sequence[str],
        *,
        timeout: float = 45,
    ) -> list[list[float]] | None: ...


class OpenAIProvider:
    name = "openai"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        legacy_model = os.environ.get("OPENAI_MODEL", "").strip()
        self.fast_model = (
            os.environ.get("OPENAI_FAST_MODEL", "").strip()
            or legacy_model
            or "gpt-5-mini"
        )
        self.advanced_model = (
            os.environ.get("OPENAI_ADVANCED_MODEL", "").strip()
            or legacy_model
            or self.fast_model
        )
        self.embedding_model = (
            os.environ.get("OPENAI_EMBEDDING_MODEL", "").strip()
            or "text-embedding-3-small"
        )

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def structured_output(
        self,
        *,
        schema_name: str,
        schema: dict[str, Any],
        instructions: str,
        input_text: str,
        tier: ModelTier = "fast",
        timeout: float = 35,
    ) -> dict[str, Any] | None:
        payload = {
            "model": self.advanced_model if tier == "advanced" else self.fast_model,
            "store": False,
            "instructions": instructions,
            "input": input_text,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "strict": True,
                    "schema": schema,
                }
            },
        }
        try:
            response = requests.post(
                RESPONSES_URL,
                headers=self.headers,
                json=payload,
                timeout=timeout,
            )
            response.raise_for_status()
            body = response.json()
        except (requests.RequestException, ValueError):
            return None

        output_text = _response_output_text(body)
        if not output_text:
            return None
        try:
            parsed = json.loads(output_text)
        except json.JSONDecodeError:
            return None
        return parsed if isinstance(parsed, dict) else None

    def embed(
        self,
        texts: Sequence[str],
        *,
        timeout: float = 45,
    ) -> list[list[float]] | None:
        clean_texts = [str(text).strip() for text in texts]
        if not clean_texts or any(not text for text in clean_texts):
            return None
        try:
            response = requests.post(
                EMBEDDINGS_URL,
                headers=self.headers,
                json={
                    "model": self.embedding_model,
                    "input": clean_texts,
                    "encoding_format": "float",
                },
                timeout=timeout,
            )
            response.raise_for_status()
            body = response.json()
        except (requests.RequestException, ValueError):
            return None

        rows = body.get("data")
        if not isinstance(rows, list):
            return None
        ordered = sorted(
            (row for row in rows if isinstance(row, dict)),
            key=lambda row: int(row.get("index", 0)),
        )
        vectors = [row.get("embedding") for row in ordered]
        if len(vectors) != len(clean_texts) or any(not isinstance(row, list) for row in vectors):
            return None
        return [[float(value) for value in row] for row in vectors]


def get_provider() -> LLMProvider | None:
    return build_local_prototype_provider(os.environ)


def build_local_prototype_provider(
    environment: dict[str, str] | None = None,
) -> LocalGemmaProvider | None:
    """Build the isolated LAI-00 through LAI-03 adapter without activating it.

    The product runtime continues to call :func:`get_provider`, which remains
    paused until the separately gated Advisor integration work begins.
    """

    return create_local_prototype_provider(environment)


def ai_runtime_state() -> str:
    mode = os.environ.get("EXCHANGE_LOCAL_AI_MODE", "").strip().lower()
    env = os.environ.get("EXCHANGE_ENVIRONMENT", "").strip().lower()
    if mode == "prototype" and env in ("development", "test"):
        return "prototype"
    return AI_RUNTIME_STATE


def ai_enabled() -> bool:
    if ai_runtime_state() == "paused":
        return False
    return get_provider() is not None


def ai_provider_name() -> str | None:
    if ai_runtime_state() == "paused":
        return None
    provider = get_provider()
    return provider.name if provider else None


def ai_model(tier: ModelTier = "fast") -> str:
    if ai_runtime_state() == "paused":
        return ""
    provider = get_provider()
    if provider is None:
        return ""
    return provider.advanced_model if tier == "advanced" else provider.fast_model


def ai_embedding_model() -> str:
    if ai_runtime_state() == "paused":
        return ""
    provider = get_provider()
    return provider.embedding_model if provider else ""


def structured_response(
    *,
    schema_name: str,
    schema: dict[str, Any],
    instructions: str,
    input_text: str,
    tier: ModelTier = "fast",
    timeout: float = 35,
) -> dict[str, Any] | None:
    provider = get_provider()
    if provider is None:
        return None
    return provider.structured_output(
        schema_name=schema_name,
        schema=schema,
        instructions=instructions,
        input_text=input_text,
        tier=tier,
        timeout=timeout,
    )


def embed_texts(
    texts: Sequence[str],
    *,
    timeout: float = 45,
) -> list[list[float]] | None:
    provider = get_provider()
    if provider is None:
        return None
    return provider.embed(texts, timeout=timeout)


def _response_output_text(body: dict[str, Any]) -> str:
    direct = body.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()
    for item in body.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if not isinstance(content, dict):
                continue
            if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                return content["text"].strip()
    return ""
