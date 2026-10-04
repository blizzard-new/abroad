from __future__ import annotations

import json
import math
import os
import threading
from dataclasses import dataclass
from typing import Any, Literal, Mapping, Sequence
from urllib.parse import urlsplit

import requests
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError

from .settings import (
    LOCAL_AI_DEFAULT_BASE_URL,
    LOCAL_AI_DEFAULT_CHAT_MODEL,
    LOCAL_AI_DEFAULT_CONTEXT_WINDOW,
    LOCAL_AI_DEFAULT_EMBEDDING_MODEL,
    LOCAL_AI_DEFAULT_MAX_INPUT_CHARS,
    LOCAL_AI_DEFAULT_MAX_OUTPUT_TOKENS,
    LOCAL_AI_DEFAULT_REQUEST_TIMEOUT_SECONDS,
    LOCAL_AI_MODE_ENV,
    LOCAL_AI_PROTOTYPE_MODE,
)


LocalModelTier = Literal["fast", "advanced"]
_ALLOWED_LOOPBACK_HOSTS = {"127.0.0.1", "::1", "localhost"}
_DEVELOPMENT_ENVIRONMENT = "development"


class LocalAIConfigurationError(ValueError):
    """Raised for a local AI setting that would cross the prototype boundary."""


@dataclass(frozen=True)
class LocalAISettings:
    base_url: str = LOCAL_AI_DEFAULT_BASE_URL
    chat_model: str = LOCAL_AI_DEFAULT_CHAT_MODEL
    embedding_model: str = LOCAL_AI_DEFAULT_EMBEDDING_MODEL
    context_window: int = LOCAL_AI_DEFAULT_CONTEXT_WINDOW
    max_output_tokens: int = LOCAL_AI_DEFAULT_MAX_OUTPUT_TOKENS
    max_input_chars: int = LOCAL_AI_DEFAULT_MAX_INPUT_CHARS
    request_timeout_seconds: float = LOCAL_AI_DEFAULT_REQUEST_TIMEOUT_SECONDS


@dataclass(frozen=True)
class LocalAIHealth:
    available: bool
    version: str | None = None
    chat_model_present: bool = False
    embedding_model_present: bool = False
    reason: str | None = None


def load_local_ai_settings(
    environment: Mapping[str, str] | None = None,
) -> LocalAISettings | None:
    """Load the explicitly enabled development prototype configuration.

    A missing mode keeps the provider disabled. Invalid or unsafe values raise so
    the factory can fail closed without silently switching hosts or models.
    """

    values = os.environ if environment is None else environment
    mode = values.get(LOCAL_AI_MODE_ENV, "").strip().casefold()
    if not mode:
        return None
    if mode != LOCAL_AI_PROTOTYPE_MODE:
        raise LocalAIConfigurationError("unsupported local AI mode")

    runtime = values.get("EXCHANGE_ENVIRONMENT", "development").strip().casefold()
    if runtime != _DEVELOPMENT_ENVIRONMENT:
        return None

    base_url = _validated_loopback_url(
        values.get("OLLAMA_BASE_URL", LOCAL_AI_DEFAULT_BASE_URL).strip()
    )
    chat_model = values.get(
        "OLLAMA_CHAT_MODEL", LOCAL_AI_DEFAULT_CHAT_MODEL
    ).strip()
    embedding_model = values.get(
        "OLLAMA_EMBEDDING_MODEL", LOCAL_AI_DEFAULT_EMBEDDING_MODEL
    ).strip()
    _require_exact_local_model(chat_model, LOCAL_AI_DEFAULT_CHAT_MODEL, "chat")
    _require_exact_local_model(
        embedding_model,
        LOCAL_AI_DEFAULT_EMBEDDING_MODEL,
        "embedding",
    )

    return LocalAISettings(
        base_url=base_url,
        chat_model=chat_model,
        embedding_model=embedding_model,
        context_window=_bounded_integer(
            values,
            "OLLAMA_CONTEXT_WINDOW",
            LOCAL_AI_DEFAULT_CONTEXT_WINDOW,
            minimum=2_048,
            maximum=32_768,
        ),
        max_output_tokens=_bounded_integer(
            values,
            "OLLAMA_MAX_OUTPUT_TOKENS",
            LOCAL_AI_DEFAULT_MAX_OUTPUT_TOKENS,
            minimum=32,
            maximum=2_048,
        ),
        max_input_chars=_bounded_integer(
            values,
            "OLLAMA_MAX_INPUT_CHARS",
            LOCAL_AI_DEFAULT_MAX_INPUT_CHARS,
            minimum=1_000,
            maximum=100_000,
        ),
        request_timeout_seconds=_bounded_float(
            values,
            "OLLAMA_REQUEST_TIMEOUT_SECONDS",
            LOCAL_AI_DEFAULT_REQUEST_TIMEOUT_SECONDS,
            minimum=1.0,
            maximum=120.0,
        ),
    )


def create_local_prototype_provider(
    environment: Mapping[str, str] | None = None,
    *,
    session: requests.Session | None = None,
) -> LocalGemmaProvider | None:
    """Create the isolated provider only for an explicit safe prototype setup."""

    try:
        settings = load_local_ai_settings(environment)
    except LocalAIConfigurationError:
        return None
    if settings is None:
        return None
    return LocalGemmaProvider(settings, session=session)


class LocalGemmaProvider:
    """Loopback-only Ollama adapter for the LAI-00 through LAI-03 foundation."""

    name = "ollama_local"

    def __init__(
        self,
        settings: LocalAISettings,
        *,
        session: requests.Session | None = None,
    ) -> None:
        normalized_base_url = _validated_loopback_url(settings.base_url)
        if normalized_base_url != settings.base_url:
            raise LocalAIConfigurationError("Ollama URL must already be normalized")
        _require_exact_local_model(
            settings.chat_model,
            LOCAL_AI_DEFAULT_CHAT_MODEL,
            "chat",
        )
        _require_exact_local_model(
            settings.embedding_model,
            LOCAL_AI_DEFAULT_EMBEDDING_MODEL,
            "embedding",
        )
        if not 2_048 <= settings.context_window <= 32_768:
            raise LocalAIConfigurationError("unsafe context window")
        if not 32 <= settings.max_output_tokens <= 2_048:
            raise LocalAIConfigurationError("unsafe output token limit")
        if not 1_000 <= settings.max_input_chars <= 100_000:
            raise LocalAIConfigurationError("unsafe input character limit")
        if (
            not math.isfinite(settings.request_timeout_seconds)
            or not 1.0 <= settings.request_timeout_seconds <= 120.0
        ):
            raise LocalAIConfigurationError("unsafe request timeout")
        self.settings = settings
        self.fast_model = settings.chat_model
        self.advanced_model = settings.chat_model
        self.embedding_model = settings.embedding_model
        self._session = session or requests.Session()
        if isinstance(self._session, requests.Session):
            # Do not let proxy environment variables reroute loopback prompts,
            # including when a caller injects a preconfigured requests session.
            self._session.trust_env = False
        self._inference_slot = threading.BoundedSemaphore(value=1)

    def health_check(self, *, timeout: float = 3.0) -> LocalAIHealth:
        request_timeout = _bounded_request_timeout(
            timeout,
            self.settings.request_timeout_seconds,
        )
        try:
            version_response = self._session.get(
                f"{self.settings.base_url}/api/version",
                timeout=request_timeout,
            )
            version_response.raise_for_status()
            version_body = version_response.json()
            tags_response = self._session.get(
                f"{self.settings.base_url}/api/tags",
                timeout=request_timeout,
            )
            tags_response.raise_for_status()
            tags_body = tags_response.json()
        except (requests.RequestException, ValueError, TypeError):
            return LocalAIHealth(available=False, reason="ollama_unavailable")

        version = version_body.get("version") if isinstance(version_body, dict) else None
        model_names = _model_names(tags_body)
        chat_present = _model_is_present(self.fast_model, model_names)
        embedding_present = _model_is_present(self.embedding_model, model_names)
        available = bool(version and chat_present and embedding_present)
        reason = None
        if not version:
            reason = "invalid_version_response"
        elif not chat_present:
            reason = "chat_model_missing"
        elif not embedding_present:
            reason = "embedding_model_missing"
        return LocalAIHealth(
            available=available,
            version=str(version).strip() if version else None,
            chat_model_present=chat_present,
            embedding_model_present=embedding_present,
            reason=reason,
        )

    def structured_output(
        self,
        *,
        schema_name: str,
        schema: dict[str, Any],
        instructions: str,
        input_text: str,
        tier: LocalModelTier = "fast",
        timeout: float = 35,
        cancel_event: threading.Event | None = None,
    ) -> dict[str, Any] | None:
        del schema_name, tier
        clean_instructions = str(instructions).strip()
        clean_input = str(input_text).strip()
        if (
            not clean_instructions
            or not clean_input
            or len(clean_instructions) + len(clean_input)
            > self.settings.max_input_chars
        ):
            return None
        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError:
            return None
        if cancel_event is not None and cancel_event.is_set():
            return None
        if not self._inference_slot.acquire(blocking=False):
            return None
        try:
            if cancel_event is not None and cancel_event.is_set():
                return None
            response = self._session.post(
                f"{self.settings.base_url}/api/chat",
                json={
                    "model": self.fast_model,
                    "messages": [
                        {"role": "system", "content": clean_instructions},
                        {"role": "user", "content": clean_input},
                    ],
                    "stream": False,
                    "think": False,
                    "format": schema,
                    "options": {
                        "temperature": 0,
                        "num_ctx": self.settings.context_window,
                        "num_predict": self.settings.max_output_tokens,
                    },
                    "keep_alive": "5m",
                },
                timeout=_bounded_request_timeout(
                    timeout,
                    self.settings.request_timeout_seconds,
                ),
            )
            response.raise_for_status()
            body = response.json()
        except (requests.RequestException, ValueError, TypeError):
            return None
        finally:
            self._inference_slot.release()

        if cancel_event is not None and cancel_event.is_set():
            return None
        if not isinstance(body, dict):
            return None
        message = body.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str) or not content.strip():
            return None
        try:
            parsed = json.loads(content)
            Draft202012Validator(schema).validate(parsed)
        except (json.JSONDecodeError, SchemaError, ValidationError):
            return None
        return parsed if isinstance(parsed, dict) else None

    def embed(
        self,
        texts: Sequence[str],
        *,
        timeout: float = 45,
        cancel_event: threading.Event | None = None,
    ) -> list[list[float]] | None:
        clean_texts = [str(text).strip() for text in texts]
        if (
            not clean_texts
            or any(not text for text in clean_texts)
            or sum(len(text) for text in clean_texts) > self.settings.max_input_chars
        ):
            return None
        if cancel_event is not None and cancel_event.is_set():
            return None
        if not self._inference_slot.acquire(blocking=False):
            return None
        try:
            if cancel_event is not None and cancel_event.is_set():
                return None
            response = self._session.post(
                f"{self.settings.base_url}/api/embed",
                json={
                    "model": self.embedding_model,
                    "input": clean_texts,
                    "truncate": False,
                },
                timeout=_bounded_request_timeout(
                    timeout,
                    self.settings.request_timeout_seconds,
                ),
            )
            response.raise_for_status()
            body = response.json()
        except (requests.RequestException, ValueError, TypeError):
            return None
        finally:
            self._inference_slot.release()

        if cancel_event is not None and cancel_event.is_set():
            return None
        rows = body.get("embeddings") if isinstance(body, dict) else None
        if not isinstance(rows, list) or len(rows) != len(clean_texts):
            return None
        vectors: list[list[float]] = []
        expected_size: int | None = None
        for row in rows:
            if not isinstance(row, list) or not row:
                return None
            try:
                vector = [float(value) for value in row]
            except (TypeError, ValueError):
                return None
            if not all(math.isfinite(value) for value in vector):
                return None
            if expected_size is None:
                expected_size = len(vector)
            elif len(vector) != expected_size:
                return None
            vectors.append(vector)
        return vectors


def _validated_loopback_url(value: str) -> str:
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as error:
        raise LocalAIConfigurationError("invalid Ollama URL") from error
    if (
        parsed.scheme.casefold() != "http"
        or parsed.hostname not in _ALLOWED_LOOPBACK_HOSTS
        or port != 11434
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise LocalAIConfigurationError("Ollama must use the fixed loopback endpoint")
    normalized_hostname = (
        "127.0.0.1" if parsed.hostname == "localhost" else parsed.hostname
    )
    host = f"[{normalized_hostname}]" if normalized_hostname == "::1" else normalized_hostname
    return f"http://{host}:11434"


def _require_exact_local_model(value: str, expected: str, label: str) -> None:
    lowered = value.casefold()
    if not value or "cloud" in lowered or value != expected:
        raise LocalAIConfigurationError(f"unsupported local {label} model")


def _bounded_integer(
    environment: Mapping[str, str],
    name: str,
    default: int,
    *,
    minimum: int,
    maximum: int,
) -> int:
    raw = environment.get(name, "").strip()
    try:
        value = int(raw) if raw else default
    except ValueError as error:
        raise LocalAIConfigurationError(f"invalid {name}") from error
    if not minimum <= value <= maximum:
        raise LocalAIConfigurationError(f"unsafe {name}")
    return value


def _bounded_float(
    environment: Mapping[str, str],
    name: str,
    default: float,
    *,
    minimum: float,
    maximum: float,
) -> float:
    raw = environment.get(name, "").strip()
    try:
        value = float(raw) if raw else default
    except ValueError as error:
        raise LocalAIConfigurationError(f"invalid {name}") from error
    if not math.isfinite(value) or not minimum <= value <= maximum:
        raise LocalAIConfigurationError(f"unsafe {name}")
    return value


def _bounded_request_timeout(requested: float, configured: float) -> float:
    try:
        value = float(requested)
    except (TypeError, ValueError):
        return configured
    if not math.isfinite(value) or value <= 0:
        return configured
    return min(value, configured)


def _model_names(body: object) -> set[str]:
    if not isinstance(body, dict) or not isinstance(body.get("models"), list):
        return set()
    names: set[str] = set()
    for row in body["models"]:
        if not isinstance(row, dict):
            continue
        for key in ("name", "model"):
            value = row.get(key)
            if isinstance(value, str) and value.strip():
                names.add(value.strip())
    return names


def _model_is_present(expected: str, names: set[str]) -> bool:
    return expected in names or (
        ":" not in expected and f"{expected}:latest" in names
    )
