"""Wave 4 Public Read-Only JSON API & OpenAPI 3.1.0 Specification (/api/public/...).

Designed for ChatGPT Custom GPT Actions, Claude MCP Server, and external AI assistants.
Security & privacy guarantees:
- Read-only (GET / HEAD / OPTIONS only).
- Strictly public institutional data: zero session/cookie/account/workspace/admin imports or reads.
- Explicit source attribution and mandatory disclaimer in every payload.
"""
from __future__ import annotations

import threading
from collections.abc import Callable, Mapping
from time import monotonic
from typing import Any

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse, Response

from .cross_school_partners import build_cross_school_entity_index
from .models import CatalogueSourceStatus, PartnerUniversity
from .tools_and_data_core import (
    MANDATORY_DISCLAIMER,
    build_all_71_school_deadlines,
    summarize_71_schools_overview,
)
from .tools_wave3 import match_eligibility_radar, search_reverse_partners
from .university_registry import SUPPORTED_UNIVERSITIES, UniversityProfile, resolve_university


PUBLIC_API_HEADERS: dict[str, str] = {
    "Cache-Control": "public, max-age=120",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
    "Access-Control-Allow-Headers": "Accept, Content-Type",
    "X-Robots-Tag": "noindex, nofollow",
}


def _public_json(payload: dict[str, Any], status_code: int = 200) -> JSONResponse:
    return JSONResponse(payload, status_code=status_code, headers=PUBLIC_API_HEADERS)


def build_public_openapi_31_spec(origin: str) -> dict[str, Any]:
    """Return a clean, self-contained OpenAPI 3.1.0 document suitable for ChatGPT Actions."""
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "UniWay Taiwan Student Exchange Public Read-Only API",
            "version": "1.0.0",
            "summary": "全台 71 所大學出國交換合作校、語言門檻與校內截止日公開唯讀 API",
            "description": (
                "提供外部 AI 助理（如 ChatGPT Custom GPT Actions、Claude MCP 等）查詢台灣 71 所大專校院公開交換學生合作校、"
                "跨校海外名校反查、語言檢定門檻初篩與校內申請截止日。本 API 僅提供公開校務整理資料，不涉及任何個人帳號或隱私資訊。"
                f"{MANDATORY_DISCLAIMER}"
            ),
            "termsOfService": f"{origin}/terms",
        },
        "servers": [
            {
                "url": origin,
                "description": "UniWay 公開唯讀伺服器",
            }
        ],
        "paths": {
            "/api/public/stats/overview": {
                "get": {
                    "operationId": "getExchangeOverview",
                    "summary": "取得全台 71 所大學交換資料庫總體統計摘要",
                    "description": "回傳收錄之台灣大學總數、去重海外合作大學數、涵蓋國家地區數與引用規範。",
                    "responses": {
                        "200": {
                            "description": "成功回傳全台交換資料庫總覽統計",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/OverviewResponse"}}},
                        }
                    },
                }
            },
            "/api/public/schools": {
                "get": {
                    "operationId": "searchTaiwaneseSchools",
                    "summary": "搜尋或列出台灣 71 所支援母校與交換資源規模",
                    "description": "依中英文校名、縮寫（如 ntu, nccu）或公私立屬性查詢台灣母校的合作校數、國家數與國際處官方連結。",
                    "parameters": [
                        {"name": "q", "in": "query", "required": False, "description": "校名或代碼關鍵字（如：臺大、政大、ntu、nccu）", "schema": {"type": "string"}},
                        {"name": "sector", "in": "query", "required": False, "description": "公私立篩選：all / public / private", "schema": {"type": "string", "enum": ["all", "public", "private"], "default": "all"}},
                        {"name": "limit", "in": "query", "required": False, "description": "回傳筆數上限（1–71）", "schema": {"type": "integer", "minimum": 1, "maximum": 71, "default": 71}},
                    ],
                    "responses": {
                        "200": {
                            "description": "符合條件之台灣母校清單",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/SchoolListResponse"}}},
                        }
                    },
                }
            },
            "/api/public/partners/filter": {
                "get": {
                    "operationId": "filterPartnerSchools",
                    "summary": "依台灣母校、語言檢定成績、預算與洲別篩選達標海外合作校",
                    "description": "查詢指定台灣母校（如 ntu, nccu）資料庫中明確列載符合語言檢定門檻之海外合作大學清單。",
                    "parameters": [
                        {"name": "home", "in": "query", "required": False, "description": "台灣母校代碼或名稱（如 ntu, nccu, 國立臺灣大學）", "schema": {"type": "string", "default": "ntu"}},
                        {"name": "test", "in": "query", "required": False, "description": "語言檢定種類", "schema": {"type": "string", "enum": ["ielts", "toefl", "toeic", "cefr", "jlpt"], "default": "ielts"}},
                        {"name": "score", "in": "query", "required": False, "description": "檢定分數或等級（如 6.5, 85, 800, B2, N2）", "schema": {"type": "string", "default": "6.5"}},
                        {"name": "gpa", "in": "query", "required": False, "description": "目前 GPA（0.0–4.3）", "schema": {"type": "number", "minimum": 0, "maximum": 4.3, "default": 3.5}},
                        {"name": "budget", "in": "query", "required": False, "description": "每學期台幣總預算上限（0 代表不限）", "schema": {"type": "integer", "minimum": 0, "default": 0}},
                        {"name": "region", "in": "query", "required": False, "description": "洲別篩選", "schema": {"type": "string", "enum": ["all", "asia", "europe", "americas", "oceania"], "default": "all"}},
                        {"name": "open_only", "in": "query", "required": False, "description": "是否僅篩選當期名單列載合作校", "schema": {"type": "boolean", "default": False}},
                        {"name": "limit", "in": "query", "required": False, "description": "回傳合作校筆數上限（1–50）", "schema": {"type": "integer", "minimum": 1, "maximum": 50, "default": 20}},
                    ],
                    "responses": {
                        "200": {
                            "description": "母校合作校語言與條件篩選結果",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/PartnerFilterResponse"}}},
                        }
                    },
                }
            },
            "/api/public/partners/reverse-lookup": {
                "get": {
                    "operationId": "reverseLookupPartnerUniversity",
                    "summary": "輸入海外大學名稱，反查全台 71 校有哪些台灣母校與其締約",
                    "description": "依海外大學中英文名稱（如：早稻田、慕尼黑、Waseda、TUM）與國家代碼反查台灣締約大學名單、開放狀態與語言門檻。",
                    "parameters": [
                        {"name": "q", "in": "query", "required": False, "description": "海外大學中英文關鍵字", "schema": {"type": "string", "default": "早稻田"}},
                        {"name": "country", "in": "query", "required": False, "description": "國家英文代碼（如 all, japan, germany, united-states）", "schema": {"type": "string", "default": "all"}},
                        {"name": "limit", "in": "query", "required": False, "description": "回傳海外大學筆數上限（1–25）", "schema": {"type": "integer", "minimum": 1, "maximum": 25, "default": 10}},
                    ],
                    "responses": {
                        "200": {
                            "description": "海外大學跨校締約反查結果",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ReverseLookupResponse"}}},
                        }
                    },
                }
            },
            "/api/public/deadlines": {
                "get": {
                    "operationId": "getSchoolDeadlines",
                    "summary": "查詢台灣各大學出國交換校內申請截止日與官方簡章連結",
                    "description": "依學校關鍵字、截止月份（1–12 或 pending）或受理狀態查詢校內交換甄選期限。",
                    "parameters": [
                        {"name": "school", "in": "query", "required": False, "description": "台灣母校代碼或名稱關鍵字", "schema": {"type": "string"}},
                        {"name": "month", "in": "query", "required": False, "description": "月份（all、1..12 或 pending）", "schema": {"type": "string", "default": "all"}},
                        {"name": "status", "in": "query", "required": False, "description": "狀態篩選（all / active / pending / closed）", "schema": {"type": "string", "enum": ["all", "active", "pending", "closed"], "default": "all"}},
                        {"name": "limit", "in": "query", "required": False, "description": "回傳筆數上限（1–71）", "schema": {"type": "integer", "minimum": 1, "maximum": 71, "default": 71}},
                    ],
                    "responses": {
                        "200": {
                            "description": "台灣大學交換申請截止日清單",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/DeadlinesResponse"}}},
                        }
                    },
                }
            },
        },
        "components": {
            "schemas": {
                "OverviewResponse": {
                    "type": "object",
                    "required": ["university_count", "unique_foreign_institutions", "unique_countries", "disclaimer"],
                    "properties": {
                        "university_count": {"type": "integer"},
                        "public_count": {"type": "integer"},
                        "private_count": {"type": "integer"},
                        "total_partner_pages": {"type": "integer"},
                        "unique_foreign_institutions": {"type": "integer"},
                        "unique_countries": {"type": "integer"},
                        "data_hub_url": {"type": "string"},
                        "tools_hub_url": {"type": "string"},
                        "disclaimer": {"type": "string"},
                    },
                },
                "SchoolListResponse": {
                    "type": "object",
                    "required": ["count", "items", "disclaimer"],
                    "properties": {
                        "count": {"type": "integer"},
                        "items": {"type": "array", "items": {"type": "object"}},
                        "disclaimer": {"type": "string"},
                    },
                },
                "PartnerFilterResponse": {
                    "type": "object",
                    "required": ["home_id", "home_name", "direct_match_count", "items", "disclaimer"],
                    "properties": {
                        "home_id": {"type": "string"},
                        "home_name": {"type": "string"},
                        "home_url": {"type": "string"},
                        "language_conversion": {"type": "object"},
                        "gpa_check": {"type": "string"},
                        "scoped_total": {"type": "integer"},
                        "direct_match_count": {"type": "integer"},
                        "equiv_match_count": {"type": "integer"},
                        "items": {"type": "array", "items": {"type": "object"}},
                        "disclaimer": {"type": "string"},
                    },
                },
                "ReverseLookupResponse": {
                    "type": "object",
                    "required": ["query", "matched_total", "items", "disclaimer"],
                    "properties": {
                        "query": {"type": "string"},
                        "country": {"type": "string"},
                        "matched_total": {"type": "integer"},
                        "items": {"type": "array", "items": {"type": "object"}},
                        "disclaimer": {"type": "string"},
                    },
                },
                "DeadlinesResponse": {
                    "type": "object",
                    "required": ["count", "items", "disclaimer"],
                    "properties": {
                        "count": {"type": "integer"},
                        "items": {"type": "array", "items": {"type": "object"}},
                        "disclaimer": {"type": "string"},
                    },
                },
            }
        },
    }


def register_public_ai_api_routes(
    router: APIRouter,
    *,
    settings: Any,
    catalogue_loader: Callable[[UniversityProfile], tuple[list[PartnerUniversity], CatalogueSourceStatus | None]],
    availability_labels: Mapping[str, str],
) -> None:
    lock = threading.Lock()
    cache_state: dict[str, Any] = {
        "ov_at": 0.0,
        "ov": None,
        "ent_at": 0.0,
        "entities": None,
    }

    def get_overview() -> dict[str, Any]:
        with lock:
            if cache_state["ov"] is not None and monotonic() - cache_state["ov_at"] < 60.0:
                return cache_state["ov"]
            d = summarize_71_schools_overview(catalogue_loader)
            cache_state["ov"] = d
            cache_state["ov_at"] = monotonic()
            return d

    def get_entities() -> Mapping[Any, Any]:
        with lock:
            if cache_state["entities"] is not None and monotonic() - cache_state["ent_at"] < 60.0:
                return cache_state["entities"]
            ents, _ = build_cross_school_entity_index(catalogue_loader, require_complete=True)
            cache_state["entities"] = ents
            cache_state["ent_at"] = monotonic()
            return ents

    @router.options("/api/public/{rest_of_path:path}")
    def public_api_cors_preflight(rest_of_path: str) -> Response:
        return Response(status_code=204, headers=PUBLIC_API_HEADERS)

    @router.api_route("/api/public/openapi.json", methods=["GET", "HEAD"])
    def public_openapi_spec() -> JSONResponse:
        return _public_json(build_public_openapi_31_spec(settings.origin))

    @router.api_route("/api/public/stats/overview", methods=["GET", "HEAD"])
    def public_stats_overview() -> JSONResponse:
        ov = get_overview()
        return _public_json({
            "university_count": ov["university_count"],
            "public_count": ov["public_count"],
            "private_count": ov["private_count"],
            "total_partner_pages": ov["total_partner_pages"],
            "unique_foreign_institutions": ov["unique_foreign_institutions"],
            "unique_countries": ov["unique_countries"],
            "data_hub_url": f"{settings.origin}/data",
            "tools_hub_url": f"{settings.origin}/tools",
            "disclaimer": MANDATORY_DISCLAIMER,
        })

    @router.api_route("/api/public/schools", methods=["GET", "HEAD"])
    def public_schools_list(
        q: str = Query(default=""),
        sector: str = Query(default="all"),
        limit: int = Query(default=71, ge=1, le=71),
    ) -> JSONResponse:
        ov = get_overview()
        rows = list(ov["schools"])
        if sector == "public":
            rows = [r for r in rows if r["sector"] == "公立"]
        elif sector == "private":
            rows = [r for r in rows if r["sector"] == "私立"]

        q_clean = q.strip().casefold()
        if q_clean:
            rows = [
                r for r in rows
                if q_clean in r["school_id"].casefold()
                or q_clean in r["school_name"].casefold()
                or q_clean in r["short_name"].casefold()
                or q_clean in r["english_name"].casefold()
            ]

        items = [
            {
                "school_id": r["school_id"],
                "school_name": r["school_name"],
                "short_name": r["short_name"],
                "english_name": r["english_name"],
                "sector": r["sector"],
                "partner_page_count": r["partner_page_count"],
                "country_count": r["country_count"],
                "open_listed_count": r["open_listed_count"],
                "school_url": f"{settings.origin}{r['school_path']}",
                "official_url": r["official_url"],
                "latest_checked": r["latest_checked"],
            }
            for r in rows[:limit]
        ]
        return _public_json({
            "count": len(items),
            "items": items,
            "disclaimer": MANDATORY_DISCLAIMER,
        })

    @router.api_route("/api/public/partners/filter", methods=["GET", "HEAD"])
    def public_partners_filter(
        home: str = Query(default="ntu"),
        test: str = Query(default="ielts"),
        score: str = Query(default="6.5"),
        gpa: float = Query(default=3.5, ge=0.0, le=4.3),
        budget: int = Query(default=0, ge=0, le=2000000),
        region: str = Query(default="all"),
        open_only: bool = Query(default=False),
        limit: int = Query(default=20, ge=1, le=50),
    ) -> JSONResponse:
        uni = resolve_university(home) or SUPPORTED_UNIVERSITIES[0]
        partners, _ = catalogue_loader(uni)
        res = match_eligibility_radar(
            uni,
            partners,
            availability_labels,
            test=test,
            score=score,
            gpa=gpa,
            budget_twd=budget,
            region=region,
            open_only="open" if open_only else "all",
        )
        # Re-slice from full direct/equiv samples cleanly up to limit
        items = [
            {
                "school_name": it["school_name"],
                "country": it["country"],
                "matched_rule": it["matched_rule"],
                "availability": it["availability"],
                "budget_tag": it["budget_tag"],
                "partner_url": f"{settings.origin}{it['partner_url']}",
            }
            for it in (res["direct_samples"] + res["equiv_samples"])[:limit]
        ]
        return _public_json({
            "home_id": res["home_id"],
            "home_name": res["home_name"],
            "home_url": f"{settings.origin}{res['home_school_url']}",
            "language_conversion": {
                "input": res["conversion"]["input_display"],
                "cefr": res["conversion"]["cefr"],
                "ielts_range": res["conversion"]["ielts_range"],
                "toefl_range": res["conversion"]["toefl_range"],
                "toeic_range": res["conversion"]["toeic_range"],
            },
            "gpa_check": res["gpa_check_label"],
            "scoped_total": res["scoped_total"],
            "direct_match_count": res["direct_count"],
            "equiv_match_count": res["equiv_count"],
            "items": items,
            "disclaimer": MANDATORY_DISCLAIMER,
        })

    @router.api_route("/api/public/partners/reverse-lookup", methods=["GET", "HEAD"])
    def public_partners_reverse_lookup(
        q: str = Query(default="早稻田"),
        country: str = Query(default="all"),
        limit: int = Query(default=10, ge=1, le=25),
    ) -> JSONResponse:
        res = search_reverse_partners(get_entities(), availability_labels, q=q, country=country, limit=limit)
        items = []
        for r in res["results"]:
            items.append({
                "display_title": r["display_title"],
                "school_name_zh": r["school_name_zh"],
                "school_name_en": r["school_name_en"],
                "country_zh": r["country_zh"],
                "country_slug": r["country_slug"],
                "contracted_count": r["contracted_count"],
                "open_home_count": r["open_home_count"],
                "canonical_url": f"{settings.origin}{r['canonical_path']}",
                "contracting_taiwan_schools": [
                    {
                        "home_id": ag["home_id"],
                        "home_name": ag["home_name"],
                        "short_name": ag["short_name"],
                        "status": ag["status"],
                        "quota": ag["quota"],
                        "language": ag["language"],
                        "partner_url": f"{settings.origin}{ag['partner_url']}",
                        "source_url": ag["source_url"],
                    }
                    for ag in r["agreements"]
                ],
            })
        return _public_json({
            "query": res["q"],
            "country": res["country"],
            "matched_total": res["matched_total"],
            "items": items,
            "disclaimer": MANDATORY_DISCLAIMER,
        })

    @router.api_route("/api/public/deadlines", methods=["GET", "HEAD"])
    def public_deadlines(
        school: str = Query(default=""),
        month: str = Query(default="all"),
        status: str = Query(default="all"),
        limit: int = Query(default=71, ge=1, le=71),
    ) -> JSONResponse:
        rows = list(build_all_71_school_deadlines())
        m_clean = month.strip().lower()
        if m_clean == "pending":
            rows = [r for r in rows if not r["all_months"]]
        elif m_clean.isdigit() and 1 <= int(m_clean) <= 12:
            mi = int(m_clean)
            rows = [r for r in rows if mi in r["all_months"]]

        st_clean = status.strip().lower()
        if st_clean == "active":
            rows = [r for r in rows if r["status_code"] in {"open", "upcoming", "action_required"}]
        elif st_clean == "pending":
            rows = [r for r in rows if r["status_code"] == "needs_confirmation"]
        elif st_clean == "closed":
            rows = [r for r in rows if r["status_code"] in {"closed", "reference_only"}]

        s_clean = school.strip().casefold()
        if s_clean:
            rows = [
                r for r in rows
                if s_clean in r["school_id"].casefold()
                or s_clean in r["school_name"].casefold()
                or s_clean in r["short_name"].casefold()
            ]

        items = [
            {
                "school_id": r["school_id"],
                "school_name": r["school_name"],
                "short_name": r["short_name"],
                "sector": r["sector"],
                "round_title": r["round_title"],
                "deadline_iso": r["deadline_iso"],
                "deadline_display": r["deadline_display"],
                "status_code": r["status_code"],
                "status_label": r["status_label"],
                "date_status_label": r["date_status_label"],
                "school_url": f"{settings.origin}/schools/{r['school_id']}",
                "source_url": r["source_url"],
                "checked_date": r["checked_date"],
            }
            for r in rows[:limit]
        ]
        return _public_json({
            "count": len(items),
            "items": items,
            "disclaimer": MANDATORY_DISCLAIMER,
        })
