"""Shared conservative interpretation of published college/degree scopes."""
from __future__ import annotations

import re
import unicodedata


def _normal(value: object) -> str:
    return " ".join(unicodedata.normalize("NFKC", str(value or "")).strip().casefold().split())


def scope_needs_confirmation(scope: str | None) -> bool:
    return not scope or scope.strip().casefold() in {"無", "none", "n/a", "na", "--", "—", "待補"} or any(
        term in scope.casefold() for term in ("待確認", "依當期", "依協議", "依合作", "另洽", "未提供", "不含", "除外", "excluding", "except")
    )


def college_scope_needs_confirmation(scope: str | None) -> bool:
    if scope_needs_confirmation(scope):
        return True
    # A misplaced degree/quota field is missing college evidence, not a rejection.
    return not any(term in scope.casefold() for term in (
        "學院", "全校", "不限", "四院皆可", "工程", "工學", "管理", "商", "人文", "法律", "法學", "理學", "社科", "社會", "醫", "生命", "資訊", "藝術",
        "engineering", "business", "management", "law", "science", "humanities", "arts", "medicine", "faculty", "college",
    )) and not re.search(r"\ball\b", scope, re.IGNORECASE)


def degree_scope_needs_confirmation(scope: str | None) -> bool:
    if scope_needs_confirmation(scope):
        return True
    return not any(term in scope.casefold() for term in (
        "大學部", "學士", "本科", "研究所", "碩士", "博士", "不限", "全校", "undergraduate", "bachelor", "graduate", "master", "doctoral", "phd",
    ))


def college_scope_matches(scope: str | None, target: str) -> bool:
    if not scope:
        return True
    normalized = _normal(scope)
    if any(term in normalized for term in ["不限", "全校", "各學院", "四院皆可"]) or re.search(r"\ball\b", scope, re.IGNORECASE):
        return True
    target_value = _normal(target)
    aliases = {
        "醫學院": ["醫學", "medicine", "medical"],
        "工學院": ["工學", "工程", "engineering"],
        "法律學院": ["法律", "法學", "law"],
        "智慧運算學院": ["智慧運算", "資訊", "computer", "informatics"],
        "管理學院": ["管理", "商學", "business", "management"],
        "資訊工程學系": ["資訊", "電腦", "computer", "informatics"],
    }
    candidates = [target_value, *aliases.get(target, [])]
    return any(candidate and _normal(candidate) in normalized for candidate in candidates)


def degree_scope_matches(scope: str | None, target: str) -> bool:
    if not scope:
        return True
    normalized = _normal(scope)
    aliases = {
        "大學部": ["大學部", "學士", "undergraduate", "bachelor"],
        "碩士班": ["碩士", "研究所", "master", "graduate"],
        "博士班": ["博士", "研究所", "doctoral", "phd", "graduate"],
        "研究所": ["研究所", "碩士", "博士", "graduate", "master", "doctoral", "phd"],
    }
    values = aliases.get(target, [target])
    return any(
        bool(re.search(r"(?<![a-z])" + re.escape(value) + r"(?![a-z])", scope.casefold()))
        if re.fullmatch(r"[a-z]+", value) else _normal(value) in normalized
        for value in values
    )


