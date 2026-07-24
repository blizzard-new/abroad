from __future__ import annotations

from exchange_info.ai_gateway import (
    EMBEDDINGS_URL,
    RESPONSES_URL,
    ai_embedding_model,
    ai_model,
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

    output = structured_response(
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
    vectors = embed_texts(["交換申請"])

    assert get_provider() is not None
    assert ai_model("fast") == "fast-model"
    assert ai_model("advanced") == "advanced-model"
    assert ai_embedding_model() == "embedding-model"
    assert output == {"answer": "ok"}
    assert vectors == [[0.25, 0.75]]
    assert requests[0][0] == RESPONSES_URL
    assert requests[0][1]["model"] == "advanced-model"
    assert requests[0][1]["store"] is False
    assert requests[1][0] == EMBEDDINGS_URL


def test_unknown_provider_disables_ai_without_falling_back(monkeypatch) -> None:
    monkeypatch.setenv("AI_PROVIDER", "unsupported")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    assert get_provider() is None
    assert structured_response(
        schema_name="test",
        schema={},
        instructions="test",
        input_text="test",
    ) is None
