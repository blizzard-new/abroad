"""Stand-ins for the claude, codex and agy command lines, written into a temporary bin folder by the tests.

Each one answers by the schema it is asked for, records how it was called in $FAKE_LOG, and can be told to fail or
stall through environment variables, so the brains are tested without any account."""

from __future__ import annotations

import json
import os
import stat
import sys
from pathlib import Path

ANSWERS = {
    "ResearchNotes": {"findings": [{"topic": "交換生在問語言檢定", "insight": "很多人問居家版成績收不收", "source_url": "https://www.dcard.tw/f/exchange"}]},
    "DayPlan": {"theme": "語言檢定", "whiteboard": ["Threads：語言檢定"], "items": [
        {"channel": "threads", "format": "text", "pillar": "value", "angle": "pain", "topic": "語言檢定怎麼選", "brief": "先看目標學校", "source_url": ""},
    ]},
    "ThreadsDraft": {"text": "語言檢定還沒考的交換生看這裡 🙋\n\n先看目標學校收哪一種", "topic_tag": "交換學生", "first_reply": "篩選合作校 👉 app.uniway-tw.com"},
    "CarouselDraft": {"slides": [{"kind": "cover", "title": "語言檢定怎麼選", "body": "先收藏"}, {"kind": "point", "title": "先看學校", "body": "每間要求不同"},
                                 {"kind": "cta", "title": "收藏起來", "body": "連結在主頁"}],
                      "caption": "語言檢定怎麼選，連結在主頁", "hashtags": ["#交換學生"], "art_prompt": "行李箱與護照"},
    "VideoScript": {"title": "語言檢定", "scenes": [
        {"kind": "hook", "heading": "語言檢定怎麼選", "lines": ["30 秒看懂"], "seconds": 3},
        {"kind": "point", "heading": "先看學校", "lines": ["每間要求不同"], "seconds": 6},
        {"kind": "point", "heading": "注意期限", "lines": ["成績有效期限"], "seconds": 6},
        {"kind": "point", "heading": "預留重考", "lines": ["提早排考試"], "seconds": 6},
        {"kind": "stat", "heading": "UniWay", "lines": ["33 所大學"], "seconds": 5},
        {"kind": "cta", "heading": "從這裡出發", "lines": ["app.uniway-tw.com"], "seconds": 5}],
        "caption": "語言檢定怎麼選", "hashtags": ["#交換學生"], "youtube_title": "語言檢定怎麼選 #Shorts", "youtube_description": "app.uniway-tw.com"},
    "Review": {"approved": True, "issues": [], "notes": ["語氣自然"]},
    "Insights": {"notes": ["痛點開頭的 Threads 互動最好"]},
    "ReplyBatch": {"replies": []},
    "Ping": {"ok": True},
    "Report": {"summary": "大家最近在問語言檢定的期限", "points": ["托福有效期兩年", "很多人問居家版"], "sources": ["https://www.dcard.tw/f/exchange"]},
}

SCRIPT = r'''#!{python}
import json, os, sys, time
from pathlib import Path
sys.path.insert(0, {here!r})
from fake_cli import answer
args = sys.argv[1:]
stdin = "" if sys.stdin is None or sys.stdin.isatty() else sys.stdin.read()
with open(os.environ["FAKE_LOG"], "a", encoding="utf-8") as log:
    log.write(json.dumps({{"tool": {tool!r}, "args": args, "stdin": stdin, "cwd": os.getcwd(),
                          "api_key": os.environ.get("ANTHROPIC_API_KEY")}}, ensure_ascii=False) + "\n")
if os.environ.get("FAKE_FAIL") == {tool!r}:
    sys.stderr.write("not logged in\n"); sys.exit(1)
if os.environ.get("FAKE_STALL") == {tool!r}:
    time.sleep(30)
answer({tool!r}, args, stdin)
'''


def title_from(args: list[str], text: str) -> str:
    if "--json-schema" in args:
        return json.loads(args[args.index("--json-schema") + 1])["title"]
    if "--output-schema" in args:
        return json.loads(Path(args[args.index("--output-schema") + 1]).read_text(encoding="utf-8"))["title"]
    marker = text.rfind('"title": "')
    return text[marker + 10 : text.index('"', marker + 10)]


def answer(tool: str, args: list[str], stdin: str) -> None:
    if tool == "codex" and "--output-schema" not in args:  # image generation
        sample = os.environ.get("FAKE_ART")
        Path("art.png").write_bytes(Path(sample).read_bytes() if sample else b"\x89PNG\r\n\x1a\n" + b"0" * 64)
        print("art.png")
        return
    prompt = args[args.index("-p") + 1] if tool == "agy" else stdin
    title = title_from(args, prompt)
    data = dict(ANSWERS.get(title, {}))
    if title == "ChiefReply":
        data = json.loads(os.environ.get("FAKE_CHIEF") or '{"reply": "好的", "actions": []}')
    if title == "Preflight":
        hold = os.environ.get("FAKE_PREFLIGHT") == "hold"
        data = {"go": not hold, "reason": "官方公告剛改了日期" if hold else "沒問題"}
    if tool == "claude":
        print(json.dumps({"type": "result", "is_error": False, "result": "", "structured_output": data}, ensure_ascii=False))
    elif tool == "codex":
        Path(args[args.index("-o") + 1]).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        print("done")
    else:
        print("好的，以下是結果：\n```json\n" + json.dumps(data, ensure_ascii=False) + "\n```")


def install(folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    for tool in ("claude", "codex", "agy"):
        path = folder / tool
        path.write_text(SCRIPT.format(python=sys.executable, here=str(Path(__file__).parent), tool=tool), encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return folder
