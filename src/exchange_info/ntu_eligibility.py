"""NTU's home selection gate, independent of partner admission rules."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from .models import HomeSelectionRules, PartnerUniversity
from .university_registry import NTU, resolve_university


@lru_cache(maxsize=1)
def ntu_home_rules() -> dict:
    return json.loads((Path(__file__).parent / "official_data/ntu/home_rules.json").read_text(encoding="utf-8"))


def ntu_selection_rules() -> HomeSelectionRules:
    return HomeSelectionRules.model_validate(ntu_home_rules()["selection_rules"])


def ntu_language_check(test: str | None, score: float | None) -> tuple[str, str]:
    rules = ntu_home_rules()
    minimum = rules["language_score_minimums"].get(test or "")
    if minimum is not None and score is not None:
        status = "pass" if score >= minimum else "needs_confirmation"
        detail = f"所填英語分數{'達到' if status == 'pass' else '未達'}一般組該測驗基本門檻{minimum:g}；須為簡章接受的測驗類型及有效日期，合作校另訂要求。"
        if status != "pass":
            detail += "其他語組或GEPT／BESTEP等替代證明仍須確認。"
        return status, detail
    return "needs_confirmation", rules["language_groups"][0]["minimum"] + "；其他語組及替代證明另依簡章確認，TOEIC與Duolingo不可自動認定符合。"


def is_ntu(school_name: str) -> bool:
    university = resolve_university(school_name)
    return university is not None and university.id == NTU.id


def ntu_published_quota(partner: PartnerUniversity) -> bool:
    """Known NTU selection capacity still does not establish open registration."""
    evidence = partner.field_evidence.get("quota")
    return bool(partner.quota_status == "published" and evidence
                and evidence.status == "verified_current"
                and evidence.source_url == "https://oia.ntu.edu.tw/outgoing/school.list"
                and evidence.academic_year == "116" and evidence.application_round == "116-1")


def ntu_academic_check(
    degree_level: str | None, academic_gpa: float | None, class_rank_percent: float | None,
) -> tuple[str, str]:
    """A missing alternative cannot prove failure of an OR condition."""
    policy = ntu_selection_rules()
    degree = degree_level or ""
    if policy.exclude_in_service and "在職" in degree:
        return "fail", "116-1校級甄選不接受在職專班申請。"
    if policy.graduate_academic_exempt and any(term in degree for term in ("研究所", "研究生", "碩士", "博士", "碩一", "博一")):
        return "pass", "研究生無校內甄選成績門檻；合作校成績與其他資格仍須另外確認。"
    if not any(term in degree for term in ("大學部", "學士", "大二", "大三", "大四")):
        return "needs_confirmation", "請先確認學制；" + _academic_rule(policy)
    rule = _academic_rule(policy)
    # A rank is a positive share of the class; zero is not a valid top-percent rank.
    if class_rank_percent is not None and not 0 < class_rank_percent <= 100:
        class_rank_percent = None
    if (academic_gpa is not None and academic_gpa >= policy.undergraduate_gpa_minimum) or (class_rank_percent is not None and class_rank_percent <= policy.undergraduate_rank_maximum):
        return "pass", "符合校內成績擇一門檻。" + rule + "學籍及合作校資格仍須確認。"
    if academic_gpa is not None and class_rank_percent is not None:
        return "fail", "目前填寫的GPA與班排名皆未達校內成績門檻。" + rule
    return "needs_confirmation", "尚缺可證明符合擇一門檻的GPA或班排名；百分制平均不能代替GPA。" + rule


def _academic_rule(policy: HomeSelectionRules) -> str:
    return f"學士生以{policy.academic_reference_year}學年度學年GPA至少{policy.undergraduate_gpa_minimum:g}或班排前{policy.undergraduate_rank_maximum:g}%擇一符合；例外年度依簡章及名次證明。研究生無校內成績門檻。"
