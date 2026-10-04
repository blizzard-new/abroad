#!/usr/bin/env python3
"""LAI-09: Benchmark script for local AI performance.

Usage:
    uv run python scripts/benchmark_local_ai.py

Requires: Ollama running with gemma4:12b loaded.
"""
import json
import os
import subprocess
import sys
import time

import requests

OLLAMA_BASE = "http://127.0.0.1:11434"
MODEL = "gemma4:12b"

TEST_QUESTIONS = [
    "請用繁體中文說明什麼是交換學生計畫？",
    "申請交換學生需要準備哪些文件？",
    "讀書計畫應該包含哪些重要內容？",
    "如何計算交換學生期間的生活費預算？",
    "IELTS 和 TOEFL 的差異是什麼？",
    "交換學生的學分如何轉換回母校？",
    "推薦信應該請誰寫比較好？",
    "交換學生保險需要注意什麼？",
    "如何選擇適合自己的交換學校？",
    "交換學生面試通常會問什麼問題？",
]


def check_ollama():
    try:
        r = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=5)
        tags = r.json()
        models = [m.get("name", "") for m in tags.get("models", [])]
        if not any(MODEL in m for m in models):
            print(f"ERROR: Model {MODEL} not found. Available: {models}")
            sys.exit(1)
        print(f"Ollama OK. Model {MODEL} found.")
    except Exception as e:
        print(f"ERROR: Cannot connect to Ollama at {OLLAMA_BASE}: {e}")
        sys.exit(1)


def get_vram():
    """Read VRAM usage via nvidia-smi."""
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total",
             "--format=csv,noheader,nounits"],
            encoding="utf-8",
        )
        used, total = out.strip().split(", ")
        return int(used), int(total)
    except Exception:
        return None, None


def benchmark_question(prompt, timeout=90):
    start = time.time()
    try:
        r = requests.post(
            f"{OLLAMA_BASE}/api/generate",
            json={"model": MODEL, "prompt": prompt, "stream": False},
            timeout=timeout,
        )
        elapsed = time.time() - start
        data = r.json()
        return {
            "success": r.status_code == 200,
            "latency_s": round(elapsed, 2),
            "response_length": len(data.get("response", "")),
            "eval_count": data.get("eval_count", 0),
        }
    except Exception as e:
        return {
            "success": False,
            "latency_s": round(time.time() - start, 2),
            "error": str(e),
        }


def main():
    print("=" * 60)
    print("LAI-09 Local AI Benchmark")
    print("=" * 60)
    check_ollama()

    vram_before = get_vram()
    if vram_before[0]:
        print(f"VRAM before: {vram_before[0]} / {vram_before[1]} MB")

    results = []
    for i, q in enumerate(TEST_QUESTIONS):
        print(f"\n[{i+1}/{len(TEST_QUESTIONS)}] {q[:30]}...")
        r = benchmark_question(q)
        results.append(r)
        status = "OK" if r["success"] else "FAIL"
        print(f"  {status} - {r['latency_s']}s", end="")
        if r["success"]:
            print(f" - {r['response_length']} chars")
        else:
            print(f" - {r.get('error', 'unknown')}")

    vram_after = get_vram()
    if vram_after[0]:
        print(f"\nVRAM after: {vram_after[0]} / {vram_after[1]} MB")

    latencies = [r["latency_s"] for r in results if r["success"]]
    if latencies:
        latencies.sort()
        p95_idx = int(len(latencies) * 0.95)
        p95 = latencies[min(p95_idx, len(latencies) - 1)]
        print(f"\n--- Results ---")
        print(f"Success: {len(latencies)}/{len(results)}")
        print(f"Mean latency: {sum(latencies)/len(latencies):.1f}s")
        print(f"p95 latency:  {p95:.1f}s (target: <30s)")
        print(f"Max latency:  {max(latencies):.1f}s")
    else:
        print("\nNo successful responses!")

    # Save results
    out_path = os.path.join("docs", "local-ai-benchmark-results.md")
    os.makedirs("docs", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# LAI-09 Benchmark Results\n\n")
        f.write(f"Model: {MODEL}\n")
        f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M')}\n\n")
        if vram_before[0]:
            f.write(f"VRAM: {vram_before[0]}->{vram_after[0]} / {vram_before[1]} MB\n\n")
        f.write("| # | Question | Latency | Status |\n")
        f.write("|---|---|---|---|\n")
        for i, (q, r) in enumerate(zip(TEST_QUESTIONS, results)):
            st = "Pass" if r["success"] else "Fail"
            f.write(f"| {i+1} | {q[:25]}... | {r['latency_s']}s | {st} |\n")
        if latencies:
            f.write(f"\np95: {p95:.1f}s | Mean: {sum(latencies)/len(latencies):.1f}s\n")
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
