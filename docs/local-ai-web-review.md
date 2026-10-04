# LAI-11: Local AI Web Prototype Review

## Architecture

- **Runtime**: Ollama 0.32.15+
- **Model**: `gemma4:12b` (Google Gemma 4, 12B parameters)
- **Embedding**: `embeddinggemma:latest`
- **Inference**: Loopback only (`http://127.0.0.1:11434`)
- **Hardware**: Windows, RTX 5060 Ti 16GB VRAM, ~64GB RAM

## Scope

This is a **single-user local prototype**. It is NOT a production deployment.

### What AI Does
- Advisor: explain, summarize, compare exchange programs (grounded in sources)
- Document check: review user documents for completeness
- Document rewrite: grammar/style polishing

### What AI Does NOT Do
- Override official rules
- Claim acceptance rates
- Guess missing deadline/eligibility values
- Store documents, prompts, or responses
- Connect to any cloud API

## Privacy & Security

| Check | Status |
|---|---|
| PII redacted from prompts | Implemented (redaction.py) |
| PII redacted from logs | Implemented (redact_for_logging) |
| No cloud fallback | Verified (gateway paused) |
| Loopback-only inference | Verified (OLLAMA_BASE_URL) |
| Fresh consent per file/change | Implemented (API layer) |
| Response headers private, no-store | Implemented (API layer) |

## Test Coverage

| Test File | Tests | Coverage |
|---|---|---|
| test_ai_privacy.py | 3 | PII redaction, consent enforcement |
| test_b4_04_ai_limits.py | 15+ | Redaction, log sanitization, injection |
| test_lai_10_security_audit.py | 10+ | SSRF, injection, log privacy, cleanup |
| test_local_ai.py | 15 | Provider, structured output, embedding |
| test_ai_gateway.py | 5 | Gateway state, provider selection |

## Performance (fill after running benchmark)

> Run `uv run python scripts/benchmark_local_ai.py` to populate.

| Metric | Target | Actual |
|---|---|---|
| Cold start (single question) | < 90s | TBD |
| Warm 10-question p95 | < 30s | TBD |
| OOM in fixed test set | 0 | TBD |
| VRAM peak | < 16GB | TBD |

## Known Limitations

1. Single-user only (no concurrent session support)
2. Model must be manually downloaded via `ollama pull gemma4:12b`
3. GPU required (CPU-only inference too slow for production)
4. No conversation history persistence
5. No streaming response support yet

## Decision Gate

Product owner can choose one of:
- [ ] **Approve**: proceed to Flutter integration planning
- [ ] **Fix**: list specific issues to address first
- [ ] **Reject**: document reasons and alternative direction

> Even if approved, this does NOT automatically enable production deployment
> or App integration. A separate specification is required.
