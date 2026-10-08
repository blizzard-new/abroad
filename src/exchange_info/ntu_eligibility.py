"""NTU's home selection gate, independent of partner admission rules."""
from __future__ import annotations

from .university_registry import NTU, resolve_university


def is_ntu(school_name: str) -> bool:
    university = resolve_university(school_name)
    return university is not None and university.id == NTU.id


def ntu_academic_check(
    degree_level: str | None, academic_gpa: float | None, class_rank_percent: float | None,
) -> tuple[str, str]:
    """A missing alternative cannot prove failure of an OR condition."""
    degree = degree_level or ""
    if "在職" in degree:
        return "fail", "116-1校級甄選不接受在職專班申請。"
    if any(term in degree for term in ("研究所", "研究生", "碩士", "博士", "碩一", "博一")):
        return "pass", "研究生無校內甄選成績門檻；合作校成績與其他資格仍須另外確認。"
    if not any(term in degree for term in ("大學部", "學士", "大二", "大三", "大四")):
        return "needs_confirmation", "請先確認學制；學士生以學年GPA至少2.44或班排前50%擇一符合，研究生無校內成績門檻。"
    rule = "學士生以114學年度學年GPA至少2.44或班排前50%擇一符合；例外年度依簡章及名次證明。"
    if (academic_gpa is not None and academic_gpa >= 2.44) or (class_rank_percent is not None and class_rank_percent <= 50):
        return "pass", "符合校內成績擇一門檻。" + rule + "學籍及合作校資格仍須確認。"
    if academic_gpa is not None and class_rank_percent is not None:
        return "fail", "目前填寫的GPA與班排名皆未達校內成績門檻。" + rule
    return "needs_confirmation", "尚缺可證明符合擇一門檻的GPA或班排名；百分制平均不能代替GPA。" + rule
