from __future__ import annotations

import threading
from collections.abc import Callable

import pytest
import requests

from exchange_info.local_ai import (
    LocalAIConfigurationError,
    LocalAISettings,
    LocalGemmaProvider,
    create_local_prototype_provider,
    load_local_ai_settings,
)


PROTOTYPE_ENVIRONMENT = {
    "EXCHANGE_LOCAL_AI_MODE": "prototype",
    "EXCHANGE_ENVIRONMENT": "development",
}


class _Response:
    def __init__(self, body: object, error: requests.RequestException | None = None) -> None:
        self.body = body
        self.error = error

    def raise_for_status(self) -> None:
        if self.error is not None:
            raise self.error

    def json(self) -> object:
        return self.body


class _Session:
    def __init__(
        self,
        *,
        get_responses: list[_Response] | None = None,
        post_responses: list[_Response | requests.RequestException] | None = None,
    ) -> None:
        self.get_responses = list(get_responses or [])
        self.post_responses = list(post_responses or [])
        self.get_requests: list[tuple[str, float]] = []
        self.post_requests: list[tuple[str, dict, float]] = []

    def get(self, url: str, *, timeout: float) -> _Response:
        self.get_requests.append((url, timeout))
        return self.get_responses.pop(0)

    def post(self, url: str, *, json: dict, timeout: float) -> _Response:
        self.post_requests.append((url, json, timeout))
        response = self.post_responses.pop(0)
        if isinstance(response, requests.RequestException):
            raise response
        return response


def _provider(
    session: _Session,
    environment: dict[str, str] | None = None,
) -> LocalGemmaProvider:
    provider = create_local_prototype_provider(
        environment or PROTOTYPE_ENVIRONMENT,
        session=session,  # type: ignore[arg-type]
    )
    assert provider is not None
    return provider


def _answer_schema() -> dict:
    return {
        "type": "object",
        "properties": {"answer": {"type": "string"}},
        "required": ["answer"],
        "additionalProperties": False,
    }


def test_provider_requires_explicit_prototype_mode() -> None:
    assert create_local_prototype_provider({}) is None
    assert (
        create_local_prototype_provider(
            {"AI_PROVIDER": "ollama", "OLLAMA_CHAT_MODEL": "gemma4:12b"}
        )
        is None
    )
    assert (
        create_local_prototype_provider(
            {
                "EXCHANGE_LOCAL_AI_MODE": "prototype",
                "EXCHANGE_ENVIRONMENT": "production",
            }
        )
        is None
    )
    assert (
        create_local_prototype_provider(
            {
                "EXCHANGE_LOCAL_AI_MODE": "prototype",
                "EXCHANGE_ENVIRONMENT": "staging",
            }
        )
        is None
    )
    assert (
        create_local_prototype_provider(
            {"EXCHANGE_LOCAL_AI_MODE": "unexpected"}
        )
        is None
    )


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("OLLAMA_BASE_URL", "https://127.0.0.1:11434"),
        ("OLLAMA_BASE_URL", "http://192.168.1.50:11434"),
        ("OLLAMA_BASE_URL", "http://127.0.0.1:11434/api"),
        ("OLLAMA_BASE_URL", "http://127.0.0.1:11435"),
        ("OLLAMA_CHAT_MODEL", "gemma4:cloud"),
        ("OLLAMA_CHAT_MODEL", "gemma4:e4b"),
        ("OLLAMA_EMBEDDING_MODEL", "embeddinggemma:cloud"),
        ("OLLAMA_CONTEXT_WINDOW", "999999"),
        ("OLLAMA_REQUEST_TIMEOUT_SECONDS", "nan"),
    ],
)
def test_settings_reject_unsafe_local_configuration(name: str, value: str) -> None:
    environment = dict(PROTOTYPE_ENVIRONMENT)
    environment[name] = value

    with pytest.raises(LocalAIConfigurationError):
        load_local_ai_settings(environment)

    assert create_local_prototype_provider(environment) is None


def test_settings_accept_only_the_fixed_loopback_models() -> None:
    settings = load_local_ai_settings(
        {
            **PROTOTYPE_ENVIRONMENT,
            "OLLAMA_BASE_URL": "http://localhost:11434/",
            "OLLAMA_CHAT_MODEL": "gemma4:12b",
            "OLLAMA_EMBEDDING_MODEL": "embeddinggemma",
            "OLLAMA_CONTEXT_WINDOW": "8192",
            "OLLAMA_MAX_OUTPUT_TOKENS": "512",
            "OLLAMA_REQUEST_TIMEOUT_SECONDS": "20",
        }
    )

    assert settings is not None
    assert settings.base_url == "http://127.0.0.1:11434"
    assert settings.chat_model == "gemma4:12b"
    assert settings.embedding_model == "embeddinggemma"
    assert settings.context_window == 8192
    assert settings.max_output_tokens == 512
    assert settings.request_timeout_seconds == 20


def test_provider_constructor_cannot_bypass_loopback_validation() -> None:
    with pytest.raises(LocalAIConfigurationError):
        LocalGemmaProvider(
            LocalAISettings(base_url="http://192.168.1.50:11434")
        )


def test_provider_disables_proxy_environment_on_injected_requests_session() -> None:
    session = requests.Session()
    session.trust_env = True

    provider = LocalGemmaProvider(LocalAISettings(), session=session)

    assert provider._session is session
    assert session.trust_env is False


def test_health_check_requires_both_pinned_models() -> None:
    session = _Session(
        get_responses=[
            _Response({"version": "0.32.15"}),
            _Response(
                {
                    "models": [
                        {"name": "gemma4:12b"},
                        {"model": "embeddinggemma:latest"},
                    ]
                }
            ),
        ]
    )
    provider = _provider(session)

    health = provider.health_check(timeout=2)

    assert health.available is True
    assert health.version == "0.32.15"
    assert health.chat_model_present is True
    assert health.embedding_model_present is True
    assert health.reason is None
    assert session.get_requests == [
        ("http://127.0.0.1:11434/api/version", 2.0),
        ("http://127.0.0.1:11434/api/tags", 2.0),
    ]


def test_health_check_reports_missing_model_without_fallback() -> None:
    session = _Session(
        get_responses=[
            _Response({"version": "0.32.15"}),
            _Response({"models": [{"name": "gemma4:12b"}]}),
        ]
    )

    health = _provider(session).health_check()

    assert health.available is False
    assert health.chat_model_present is True
    assert health.embedding_model_present is False
    assert health.reason == "embedding_model_missing"


def test_structured_output_uses_schema_and_deterministic_local_options() -> None:
    schema = _answer_schema()
    session = _Session(
        post_responses=[
            _Response({"message": {"content": '{"answer":"只依官方來源"}'}})
        ]
    )
    provider = _provider(session)

    result = provider.structured_output(
        schema_name="grounded_answer",
        schema=schema,
        instructions="只能使用提供的來源。",
        input_text="來源摘錄",
        tier="advanced",
        timeout=10,
    )

    assert result == {"answer": "只依官方來源"}
    assert len(session.post_requests) == 1
    url, payload, timeout = session.post_requests[0]
    assert url == "http://127.0.0.1:11434/api/chat"
    assert timeout == 10.0
    assert payload["model"] == "gemma4:12b"
    assert payload["stream"] is False
    assert payload["think"] is False
    assert payload["format"] == schema
    assert payload["options"] == {
        "temperature": 0,
        "num_ctx": 16_384,
        "num_predict": 1_024,
    }
    assert payload["messages"] == [
        {"role": "system", "content": "只能使用提供的來源。"},
        {"role": "user", "content": "來源摘錄"},
    ]


@pytest.mark.parametrize(
    "response_factory",
    [
        lambda: _Response({"message": {"content": "not-json"}}),
        lambda: _Response({"message": {"content": '{"answer":1}'}}),
        lambda: _Response({"message": {"content": '{"answer":"ok","extra":1}'}}),
        lambda: _Response({"unexpected": "body"}),
        lambda: requests.Timeout("timeout"),
    ],
)
def test_structured_output_fails_closed_for_invalid_or_failed_responses(
    response_factory: Callable[[], _Response | requests.RequestException],
) -> None:
    session = _Session(post_responses=[response_factory()])

    result = _provider(session).structured_output(
        schema_name="grounded_answer",
        schema=_answer_schema(),
        instructions="只用來源",
        input_text="來源",
    )

    assert result is None


def test_structured_output_rejects_bad_schema_and_oversized_input_before_request() -> None:
    session = _Session()
    provider = _provider(
        session,
        {
            **PROTOTYPE_ENVIRONMENT,
            "OLLAMA_MAX_INPUT_CHARS": "1000",
        },
    )

    assert (
        provider.structured_output(
            schema_name="bad",
            schema={"type": "unknown"},
            instructions="test",
            input_text="test",
        )
        is None
    )
    assert (
        provider.structured_output(
            schema_name="large",
            schema=_answer_schema(),
            instructions="test",
            input_text="x" * 1001,
        )
        is None
    )
    assert session.post_requests == []


def test_single_inference_slot_returns_busy_without_request() -> None:
    session = _Session()
    provider = _provider(session)
    assert provider._inference_slot.acquire(blocking=False) is True
    try:
        result = provider.structured_output(
            schema_name="busy",
            schema=_answer_schema(),
            instructions="test",
            input_text="test",
        )
    finally:
        provider._inference_slot.release()

    assert result is None
    assert session.post_requests == []


def test_canceled_request_is_not_sent_or_returned() -> None:
    canceled_before_send = threading.Event()
    canceled_before_send.set()
    unused_session = _Session()
    provider = _provider(unused_session)

    assert (
        provider.structured_output(
            schema_name="canceled",
            schema=_answer_schema(),
            instructions="test",
            input_text="test",
            cancel_event=canceled_before_send,
        )
        is None
    )
    assert unused_session.post_requests == []

    canceled_while_waiting = threading.Event()

    class _CancelingSession(_Session):
        def post(self, url: str, *, json: dict, timeout: float) -> _Response:
            response = super().post(url, json=json, timeout=timeout)
            canceled_while_waiting.set()
            return response

    canceling_session = _CancelingSession(
        post_responses=[
            _Response({"message": {"content": '{"answer":"discard me"}'}})
        ]
    )

    assert (
        _provider(canceling_session).structured_output(
            schema_name="canceled",
            schema=_answer_schema(),
            instructions="test",
            input_text="test",
            cancel_event=canceled_while_waiting,
        )
        is None
    )
    assert len(canceling_session.post_requests) == 1


def test_embedding_uses_pinned_model_and_validates_vectors() -> None:
    session = _Session(
        post_responses=[
            _Response({"embeddings": [[0.1, 0.2], [0.3, 0.4]]})
        ]
    )
    provider = _provider(session)

    vectors = provider.embed(["交換申請", "官方文件"], timeout=12)

    assert vectors == [[0.1, 0.2], [0.3, 0.4]]
    url, payload, timeout = session.post_requests[0]
    assert url == "http://127.0.0.1:11434/api/embed"
    assert timeout == 12.0
    assert payload == {
        "model": "embeddinggemma",
        "input": ["交換申請", "官方文件"],
        "truncate": False,
    }


@pytest.mark.parametrize(
    "body",
    [
        {"embeddings": []},
        {"embeddings": [[0.1], [0.2, 0.3]]},
        {"embeddings": [[float("nan")]]},
        {"embeddings": [["invalid"]]},
        {"unexpected": []},
    ],
)
def test_embedding_rejects_invalid_vectors(body: dict) -> None:
    session = _Session(post_responses=[_Response(body)])

    assert _provider(session).embed(["one"]) is None
