from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class UniversityProfile:
    id: str
    school_name: str
    short_name: str
    english_name: str
    aliases: tuple[str, ...]
    hero_image: str
    official_url: str
    coverage_note: str
    support_level: Literal["full", "basic", "pending"]
    partner_count_hint: int
    academic_score_minimum: float
    student_card_signals: tuple[str, ...]
    colleges: tuple[str, ...] = ()


CGU = UniversityProfile(
    id="cgu",
    school_name="長庚大學",
    short_name="長庚",
    english_name="Chang Gung University",
    aliases=("長庚大學", "長庚", "CGU", "Chang Gung University"),
    hero_image="/static/assets/cgu-campus.jpg",
    official_url="https://www.cgu.edu.tw/oia-ch",
    coverage_note="完整支援試點：已整理長庚大學交換、補助、文件與合作校申請流程。",
    support_level="full",
    partner_count_hint=75,
    academic_score_minimum=70,
    student_card_signals=("長庚大學", "CHANGGUNGUNIVERSITY", "CGU"),
    # Official academic units, checked 2026-09-29:
    # https://www.cgu.edu.tw/academic/Contents?nodeId=17720
    colleges=("醫學院", "工學院", "管理學院", "智慧運算學院"),
)


NTPU = UniversityProfile(
    id="ntpu",
    school_name="國立臺北大學",
    short_name="臺北大學",
    english_name="National Taipei University",
    aliases=(
        "國立臺北大學",
        "臺北大學",
        "台北大學",
        "北大",
        "NTPU",
        "National Taipei University",
    ),
    hero_image="/static/assets/ntpu-campus.jpg",
    official_url="https://new.ntpu.edu.tw/oia",
    coverage_note="完整支援試點：已套用交換申請流程與 116 學年度三語組官方名額表。",
    support_level="full",
    partner_count_hint=169,
    academic_score_minimum=75,
    student_card_signals=(
        "國立臺北大學",
        "臺北大學",
        "台北大學",
        "NATIONALTAIPEIUNIVERSITY",
        "NTPU",
    ),
    # Official college directory, checked 2026-09-29:
    # https://udb.moe.edu.tw/ulist/Institution?id=000021E714C0
    colleges=(
        "法律學院", "商學院", "公共事務學院", "社會科學學院",
        "人文學院", "電機資訊學院", "永續創新國際學院",
    ),
)


CCU = UniversityProfile(
    id="ccu", school_name="國立中正大學", short_name="中正大學",
    english_name="National Chung Cheng University",
    aliases=("國立中正大學", "中正大學", "中正", "CCU", "National Chung Cheng University"),
    hero_image="", official_url="https://oia.ccu.edu.tw/",
    coverage_note="已核對2027春季校級薦外交換；灰字參考與空白名額分開，三梯次校內收件已截止。",
    support_level="basic", partner_count_hint=52, academic_score_minimum=70,
    student_card_signals=("國立中正大學", "NATIONALCHUNGCHENGUNIVERSITY", "CCU"),
    # Official directory, checked 2026-10-08:
    # https://s2.exam.ccu.edu.tw/ccuee_intro/stu/intro_index.php
    colleges=("文學院", "理學院", "社會科學院", "工學院", "管理學院", "法學院", "教育學院"),
)

SUPPORTED_UNIVERSITIES = (CGU, NTPU, CCU)
DEFAULT_UNIVERSITY = CGU


def _alias_key(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value or "").casefold()
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", normalized)


_UNIVERSITY_BY_ALIAS = {
    _alias_key(alias): university
    for university in SUPPORTED_UNIVERSITIES
    for alias in (*university.aliases, university.school_name)
}


def resolve_university(value: str | None) -> UniversityProfile | None:
    if value is None or not value.strip():
        return DEFAULT_UNIVERSITY
    return _UNIVERSITY_BY_ALIAS.get(_alias_key(value))


def require_university(value: str | None) -> UniversityProfile:
    university = resolve_university(value)
    if university is None:
        supported = "、".join(item.school_name for item in SUPPORTED_UNIVERSITIES)
        raise ValueError(f"目前支援的學校為：{supported}。")
    return university


def is_home_university(value: str | None) -> bool:
    return resolve_university(value) is not None
