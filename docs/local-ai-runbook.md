# Local AI Runbook

## Prerequisites

- Windows 10/11 with NVIDIA GPU (16GB+ VRAM recommended)
- Ollama installed: https://ollama.com/download
- Python 3.11+ with uv

## Setup

```bash
# 1. Install Ollama (if not already)
winget install Ollama.Ollama

# 2. Pull required models
ollama pull gemma4:12b
ollama pull embeddinggemma

# 3. Verify models
ollama list
```

## Starting

```bash
# Ollama starts automatically as a service on Windows
# Verify it's running:
curl http://127.0.0.1:11434/api/tags
```

## Stopping

```bash
# Stop Ollama service
taskkill /IM ollama.exe /F

# Or via services.msc -> Ollama -> Stop
```

## Running Benchmarks

```bash
cd C:\Users\User\OneDrive\文件\留學
uv run python scripts/benchmark_local_ai.py
```

Results saved to `docs/local-ai-benchmark-results.md`.

## Running Tests

```bash
# All AI tests
uv run pytest tests/test_ai_privacy.py tests/test_b4_04_ai_limits.py tests/test_lai_10_security_audit.py -v

# Reliability tests (requires running Ollama)
uv run pytest tests/integration/test_local_ai_runtime.py -v
```

## Troubleshooting

| Issue | Solution |
|---|---|
| Ollama not responding | Check `http://127.0.0.1:11434` in browser |
| Model not found | Run `ollama pull gemma4:12b` |
| OOM / GPU memory | Close other GPU apps, reduce context |
| Slow responses | Ensure GPU is being used (check nvidia-smi) |
| Port conflict | Change OLLAMA_HOST env var |

## Recovery After Failure

1. Kill Ollama: `taskkill /IM ollama.exe /F`
2. Wait 5 seconds
3. Restart: `ollama serve` or restart via services.msc
4. Verify: `curl http://127.0.0.1:11434/api/tags`
