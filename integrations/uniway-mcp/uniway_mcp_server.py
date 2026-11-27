#!/usr/bin/env python3
"""UniWay Taiwan Student Exchange — Lightweight Stdio MCP Server.

Zero third-party dependencies required (runs on standard Python >=3.10).
Connects Claude Desktop, Cursor, Windsurf, or any Model Context Protocol (MCP) client
to UniWay's public read-only exchange API (/api/public/...).
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "uniway-taiwan-exchange", "version": "1.0.0"}
DEFAULT_BASE_URL = "https://app.uniway-tw.com"


def get_base_url() -> str:
    raw = os.environ.get("UNIWAY_BASE_URL", DEFAULT_BASE_URL).strip().rstrip("/")
    parsed = urllib.parse.urlsplit(raw)
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        return DEFAULT_BASE_URL
    if parsed.scheme == "http" and parsed.hostname not in {"127.0.0.1", "localhost"}:
        return DEFAULT_BASE_URL
    return raw


TOOLS_SCHEMA: list[dict[str, Any]] = [
    {
        "name": "get_exchange_overview",
        "description": "取得台灣 71 所大學出國交換公開資料庫總體統計摘要（大學數、去重海外姊妹校數、國家數與免責聲明）。",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "search_schools",
        "description": "搜尋台灣 71 所公私立大學之出國交換資源規模、合作校數量、涵蓋國家數與國際處官方網站。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "q": {"type": "string", "description": "台灣母校名稱或代碼關鍵字（如：臺大、政大、ntu、nccu）"},
                "sector": {"type": "string", "enum": ["all", "public", "private"], "default": "all"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 71, "default": 20},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "filter_partners",
        "description": "依就讀台灣母校、語言檢定成績（IELTS/TOEFL/TOEIC/CEFR/JLPT）、GPA、預算與洲別篩選明確達標之海外合作大學。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "home": {"type": "string", "description": "台灣母校代碼或校名（如 ntu, nccu, nthu）", "default": "ntu"},
                "test": {"type": "string", "enum": ["ielts", "toefl", "toeic", "cefr", "jlpt"], "default": "ielts"},
                "score": {"type": "string", "description": "分數或等級（如 6.5, 85, 800, B2, N2）", "default": "6.5"},
                "gpa": {"type": "number", "default": 3.5},
                "budget": {"type": "integer", "description": "每學期台幣預算上限（0 為不限）", "default": 0},
                "region": {"type": "string", "enum": ["all", "asia", "europe", "americas", "oceania"], "default": "all"},
                "open_only": {"type": "boolean", "default": False},
                "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 15},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "reverse_lookup_partner",
        "description": "輸入海外大學中英文名稱（如：早稻田、慕尼黑工大、Waseda、TUM），反查台灣哪幾所大學與其簽有交換合作及門檻。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "q": {"type": "string", "description": "海外大學中英文關鍵字"},
                "country": {"type": "string", "description": "國家英文代碼（如 all, japan, germany, united-states）", "default": "all"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 25, "default": 10},
            },
            "required": ["q"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_school_deadlines",
        "description": "查詢台灣 71 所大學出國交換校內申請截止日、受理狀態與國際處官方簡章連結。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "school": {"type": "string", "description": "學校名稱或代碼關鍵字（選填）"},
                "month": {"type": "string", "description": "截止月份（all、1..12 或 pending）", "default": "all"},
                "status": {"type": "string", "enum": ["all", "active", "pending", "closed"], "default": "all"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 71, "default": 25},
            },
            "additionalProperties": False,
        },
    },
]


def call_uniway_api(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    base = get_base_url()
    clean_params = {
        k: ("true" if v is True else ("false" if v is False else str(v)))
        for k, v in (params or {}).items()
        if v is not None and str(v) != ""
    }
    qs = ("?" + urllib.parse.urlencode(clean_params)) if clean_params else ""
    url = f"{base}{path}{qs}"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "uniway-mcp-server/1.0 (+https://app.uniway-tw.com)",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def execute_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    routes = {
        "get_exchange_overview": "/api/public/stats/overview",
        "search_schools": "/api/public/schools",
        "filter_partners": "/api/public/partners/filter",
        "reverse_lookup_partner": "/api/public/partners/reverse-lookup",
        "get_school_deadlines": "/api/public/deadlines",
    }
    if name not in routes:
        return {
            "isError": True,
            "content": [{"type": "text", "text": f"Unknown tool: {name}"}],
        }
    try:
        payload = call_uniway_api(routes[name], arguments)
        return {
            "isError": False,
            "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False, indent=2)}],
        }
    except urllib.error.HTTPError as exc:
        return {
            "isError": True,
            "content": [{"type": "text", "text": f"UniWay API HTTP {exc.code}: {exc.reason}"}],
        }
    except Exception as exc:
        return {
            "isError": True,
            "content": [{"type": "text", "text": f"UniWay API connection error: {exc}"}],
        }


def handle_rpc_message(msg: dict[str, Any]) -> dict[str, Any] | None:
    method = msg.get("method")
    msg_id = msg.get("id")

    # Notifications (no id) require no response
    if msg_id is None:
        return None

    if method == "initialize":
        req_proto = (msg.get("params") or {}).get("protocolVersion") or PROTOCOL_VERSION
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": req_proto,
                "capabilities": {"tools": {}},
                "serverInfo": SERVER_INFO,
            },
        }
    if method == "ping":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": TOOLS_SCHEMA}}
    if method == "tools/call":
        params = msg.get("params") or {}
        tool_name = str(params.get("name") or "")
        tool_args = params.get("arguments") or {}
        if not isinstance(tool_args, dict):
            tool_args = {}
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": execute_tool(tool_name, tool_args),
        }

    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


def main() -> int:
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            err = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}
            sys.stdout.write(json.dumps(err) + "\n")
            sys.stdout.flush()
            continue

        resp = handle_rpc_message(msg)
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
