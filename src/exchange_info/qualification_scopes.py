"""Shared conservative interpretation of published college/degree scopes."""
from __future__ import annotations

import re
import unicodedata

_HOME_ELIGIBILITY_PAREN_RE = re.compile(
    r"[（(]\s*校內報名資格[：:][^）)]*[）)]"
)
_DEFERRED_PAREN_RE = re.compile(
    r"[（(][^）)]*(?:依當期|依協議|依合作|依簡章|依該校)[^）)]*[）)]"
)
_NEGATED_CLAUSE_RE = re.compile(
    r"(?:※?\s*(?:不含|不開放|不接受|不包括|限不含)[^；;。，,）)]*"
    r"|[^；;。，,（(]*除外"
    r"|\b(?:excluding|except(?:\s+for)?|not\s+open\s+to)\b[^.;,)]*)",
    re.IGNORECASE,
)
_DEFERRED_CLAUSE_RE = re.compile(
    r"依(?:當期|協議|合作|簡章|該校)[^；;。，,）)]*"
)

_EMPTY_TOKENS = {"", "無", "none", "n/a", "na", "--", "—", "待補"}
_UNCONDITIONAL_PENDING_TERMS = (
    "待確認",
    "跨期資料待核對",
    "請洽",
    "另洽",
    "未提供",
    "尚待",
    "待公告",
    "限特定",
    "部分學院",
    "部分院系",
    "部分系所",
    "特定院系",
)
_COLLEGE_POSITIVE_TERMS = (
    "學院",
    "全校",
    "不限",
    "四院皆可",
    "學系",
    "學程",
    "工程",
    "工學",
    "管理",
    "商",
    "人文",
    "法律",
    "法學",
    "理學",
    "社科",
    "社會",
    "醫",
    "藥",
    "護",
    "生命",
    "資訊",
    "電機",
    "藝術",
    "設計",
    "教育",
    "外語",
    "傳播",
    "農",
    "engineering",
    "business",
    "management",
    "law",
    "science",
    "humanities",
    "arts",
    "medicine",
    "nursing",
    "pharmacy",
    "design",
    "education",
    "faculty",
    "college",
    "department",
)
_DEGREE_POSITIVE_TERMS = (
    "大學部",
    "學士",
    "本科",
    "大一",
    "大二",
    "大三",
    "大四",
    "四技",
    "二技",
    "五專",
    "研究所",
    "碩士",
    "碩班",
    "碩博",
    "博士",
    "博班",
    "不限",
    "全校",
    "undergraduate",
    "bachelor",
    "graduate",
    "master",
    "doctoral",
    "phd",
)


def _positive_scope_text(scope: str | None) -> str:
    if not scope:
        return ""
    cleaned = unicodedata.normalize("NFKC", str(scope))
    cleaned = _HOME_ELIGIBILITY_PAREN_RE.sub(" ", cleaned)
    cleaned = _DEFERRED_PAREN_RE.sub(" ", cleaned)
    cleaned = _NEGATED_CLAUSE_RE.sub(" ", cleaned)
    cleaned = _DEFERRED_CLAUSE_RE.sub(" ", cleaned)
    return " ".join(cleaned.strip().casefold().split())


def partner_scope_needs_confirmation(partner: object, field: str) -> bool:
    evidence = getattr(partner, "field_evidence", {}).get(field)
    if evidence is not None and evidence.status != "verified_current":
        return True
    scope = getattr(partner, field, None)
    check = college_scope_needs_confirmation if field == "colleges" else degree_scope_needs_confirmation
    return check(scope)


def _coupled_scope_options(partner: object) -> list | None:
    """Return only complete, current and consistently sourced pairs."""
    options = getattr(partner, "program_options", [])
    evidence = getattr(partner, "field_evidence", {})
    if not options:
        return None
    if any(evidence.get(k) is None or evidence[k].status != "verified_current" for k in ["colleges", "degree_levels"]):
        return None
    urls = {evidence[k].source_url for k in ["colleges", "degree_levels"]}
    if any(
        option.source_url not in urls
        or college_scope_needs_confirmation(option.colleges)
        or degree_scope_needs_confirmation(option.degree_levels)
        for option in options
    ):
        return None
    return options


def coupled_academic_scope_matches(partner: object, college: str | None, degree: str | None) -> bool | None:
    """Apply sourced pairs; an unspecified graduate degree can remain unknown."""
    options = _coupled_scope_options(partner)
    if not college or not degree or options is None:
        return None
    matches = [degree_scope_matches(option.degree_levels, degree) for option in options
               if college_scope_matches(option.colleges, college)]
    return True if True in matches else None if None in matches else False


def resolved_degree_level(degree: str | None, current_year: str | None = None) -> str | None:
    """Refine the legacy graduate choice only when the year identifies its degree."""
    if degree != "研究所":
        return degree
    year = _normal(current_year)
    master = "碩士" in year or bool(re.search(r"\bmaster(?:'s)?\b", year))
    doctoral = "博士" in year or bool(re.search(r"\b(?:ph\.?d\.?|doctoral)\b", year))
    if master != doctoral:
        return "碩士班" if master else "博士班"
    return degree


def partner_degree_scope_matches(partner: object, college: str | None, degree: str) -> bool | None:
    # None can mean a valid pair whose graduate subtype is unknown. Do not then
    # fall back to the union of all colleges, which would allow Law doctorates.
    if college and _coupled_scope_options(partner) is not None:
        return coupled_academic_scope_matches(partner, college, degree)
    return degree_scope_matches(getattr(partner, "degree_levels", None), degree)


def _normal(value: object) -> str:
    return " ".join(unicodedata.normalize("NFKC", str(value or "")).strip().casefold().split())


def scope_needs_confirmation(scope: str | None) -> bool:
    if not scope or scope.strip().casefold() in _EMPTY_TOKENS:
        return True
    lowered = unicodedata.normalize("NFKC", scope).casefold()
    if any(term in lowered for term in _UNCONDITIONAL_PENDING_TERMS):
        return True
    positive = _positive_scope_text(scope)
    if not positive or positive in _EMPTY_TOKENS:
        return True
    return False


def college_scope_needs_confirmation(scope: str | None) -> bool:
    if scope_needs_confirmation(scope):
        return True
    positive = _positive_scope_text(scope)
    # A misplaced degree/quota field is missing college evidence, not a rejection.
    return not any(term in positive for term in _COLLEGE_POSITIVE_TERMS) and not re.search(r"\ball\b", positive, re.IGNORECASE)


def degree_scope_needs_confirmation(scope: str | None) -> bool:
    if scope_needs_confirmation(scope):
        return True
    positive = _positive_scope_text(scope)
    return not any(term in positive for term in _DEGREE_POSITIVE_TERMS)


def college_scope_matches(scope: str | None, target: str) -> bool:
    if not scope:
        return True
    normalized = _positive_scope_text(scope) or _normal(scope)
    if any(term in normalized for term in ["不限", "全校", "各學院", "四院皆可"]) or re.search(r"\ball\b", normalized, re.IGNORECASE):
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


def degree_scope_matches(scope: str | None, target: str) -> bool | None:
    if not scope:
        return True
    normalized = _positive_scope_text(scope)
    if not normalized:
        return False
    if any(term in normalized for term in ["不限學制", "不限年級", "各學制"]) or normalized in {"不限", "全校"}:
        return True
    if target == "研究所":
        if degree_scope_matches(scope, "碩士班") and degree_scope_matches(scope, "博士班"):
            return True
        if degree_scope_matches(scope, "碩士班") or degree_scope_matches(scope, "博士班"):
            return None
        return False
    aliases = {
        "大學部": ["大學部", "學士", "本科", "大一", "大二", "大三", "大四", "四技", "二技", "五專", "undergraduate", "bachelor"],
        "碩士班": ["碩士", "碩班", "碩博", "研究所", "master", "graduate"],
        "博士班": ["博士", "博班", "碩博", "研究所", "doctoral", "phd", "graduate"],
        "研究所": ["研究所", "碩士", "碩班", "碩博", "博士", "博班", "graduate", "master", "doctoral", "phd"],
    }
    values = aliases.get(target, [target])
    return any(
        bool(re.search(r"(?<![a-z])" + re.escape(value) + r"(?![a-z])", normalized))
        if re.fullmatch(r"[a-z]+", value) else _normal(value) in normalized
        for value in values
    )
