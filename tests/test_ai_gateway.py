from __future__ import annotations

import os

from exchange_info.ai_gateway import (
    AI_RUNTIME_PAUSED_REASON,
    AI_RUNTIME_STATE,
    EMBEDDINGS_URL,
    RESPONSES_URL,
    OpenAIProvider,
    ai_embedding_model,
    ai_enabled,
    ai_model,
    ai_runtime_state,
    build_local_prototype_provider,
    embed_texts,
    get_provider,
    structured_response,
)


class _Response:
    def __init__(self, body: dict) -> None:
        self.body = body

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self.body


def test_openai_provider_supports_model_tiers_and_embeddings(monkeypatch) -> None:
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_FAST_MODEL", "fast-model")
    monkeypatch.setenv("OPENAI_ADVANCED_MODEL", "advanced-model")
    monkeypatch.setenv("OPENAI_EMBEDDING_MODEL", "embedding-model")
    requests: list[tuple[str, dict]] = []

    def fake_post(url: str, **kwargs):
        requests.append((url, kwargs["json"]))
        if url == EMBEDDINGS_URL:
            return _Response({"data": [{"index": 0, "embedding": [0.25, 0.75]}]})
        return _Response({"output_text": '{"answer":"ok"}'})

    monkeypatch.setattr("exchange_info.ai_gateway.requests.post", fake_post)

    provider = OpenAIProvider("test-key")
    output = provider.structured_output(
        schema_name="test",
        schema={
            "type": "object",
            "properties": {"answer": {"type": "string"}},
            "required": ["answer"],
            "additionalProperties": False,
        },
        instructions="Only test data.",
        input_text="test",
        tier="advanced",
    )
    vectors = provider.embed(["交換申請"])

    assert provider.fast_model == "fast-model"
    assert provider.advanced_model == "advanced-model"
    assert provider.embedding_model == "embedding-model"
    assert output == {"answer": "ok"}
    assert vectors == [[0.25, 0.75]]
    assert requests[0][0] == RESPONSES_URL
    assert requests[0][1]["model"] == "advanced-model"
    assert requests[0][1]["store"] is False
    assert requests[1][0] == EMBEDDINGS_URL


def test_runtime_stays_paused_even_when_external_ai_environment_is_present(
    monkeypatch,
) -> None:
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    calls: list[str] = []

    def unexpected_post(url: str, **kwargs):
        calls.append(url)
        raise AssertionError("paused runtime must not make an external AI request")

    monkeypatch.setattr("exchange_info.ai_gateway.requests.post", unexpected_post)

    assert AI_RUNTIME_STATE == "paused"
    assert ai_runtime_state() == "paused"
    assert "目前暫緩" in AI_RUNTIME_PAUSED_REASON
    assert ai_enabled() is False
    assert get_provider() is None
    assert ai_model("fast") == ""
    assert ai_embedding_model() == ""
    assert structured_response(
        schema_name="test",
        schema={},
        instructions="test",
        input_text="test",
    ) is None
    assert embed_texts(["交換申請"]) is None
    assert calls == []


def test_local_provider_foundation_activates_product_runtime_in_prototype_mode(
    monkeypatch,
) -> None:
    monkeypatch.setenv("EXCHANGE_LOCAL_AI_MODE", "prototype")
    monkeypatch.setenv("EXCHANGE_ENVIRONMENT", "development")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    monkeypatch.setenv("OLLAMA_CHAT_MODEL", "gemma4:12b")
    monkeypatch.setenv("OLLAMA_EMBEDDING_MODEL", "embeddinggemma")

    provider = build_local_prototype_provider(dict(os.environ))

    assert provider is not None
    assert provider.name == "ollama_local"
    assert get_provider() is not None
    assert ai_enabled() is True
