from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Literal

from .tku_university import PROFILE as TKU_PROFILE


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
    academic_score_minimum: float | None
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
TKU = UniversityProfile(**TKU_PROFILE)

NTU = UniversityProfile(
    id="ntu",
    school_name="國立臺灣大學",
    short_name="臺大",
    english_name="National Taiwan University",
    aliases=("國立臺灣大學", "國立台灣大學", "臺灣大學", "台灣大學", "臺大", "台大", "NTU", "National Taiwan University"),
    hero_image="/static/assets/ntu-campus.svg",
    official_url="https://studyabroad.ntu.edu.tw/",
    coverage_note="已整理116-1校級甄選、文件、補助與289個合作項目；合作校本期名額與未核實條件標示待確認。",
    support_level="basic",
    partner_count_hint=289,
    # NTU uses undergraduate GPA OR class rank, with no home GPA gate for graduates.
    academic_score_minimum=None,
    student_card_signals=("國立臺灣大學", "國立台灣大學", "NATIONALTAIWANUNIVERSITY", "NTU"),
    colleges=("文學院", "理學院", "社會科學院", "醫學院", "工學院", "生物資源暨農學院", "管理學院", "公共衛生學院", "電機資訊學院", "法律學院", "生命科學院", "國際政經學院"),
)


NCU = UniversityProfile(
    id="ncu",
    school_name="國立中央大學",
    short_name="中央",
    english_name="National Central University",
    aliases=("國立中央大學", "中央大學", "中央", "中大", "NCU", "National Central University"),
    hero_image="/static/assets/ncu-campus.svg",
    official_url="https://oia.ncu.edu.tw/p/412-1026-1872.php?Lang=zh-tw",
    coverage_note="116學年度第一梯次簡章與2026/10/13最新交換姐妹校列表已公告（11/16開放線上申請）；外校當期條件逐項待核對。",
    support_level="basic",
    partner_count_hint=214,
    academic_score_minimum=None,
    student_card_signals=("國立中央大學", "NATIONALCENTRALUNIVERSITY", "NCU"),
    # https://www.ncu.edu.tw/p/412-1000-87.php?Lang=zh-tw — checked 2026-10-08.
    colleges=("文學院", "理學院", "工學院", "管理學院", "資訊電機學院", "地球科學學院", "客家學院", "生醫理工學院", "永續與綠能科技研究學院", "松濤全人學院"),
)


FJU = UniversityProfile(
    id="fju",
    school_name="天主教輔仁大學",
    short_name="輔大",
    english_name="Fu Jen Catholic University",
    aliases=(
        "天主教輔仁大學",
        "輔仁大學",
        "輔仁",
        "輔大",
        "FJU",
        "Fu Jen Catholic University",
    ),
    hero_image="/static/assets/fju-campus.svg",
    official_url="https://iscoie.fju.edu.tw/generalServices.jsp?labelID=39",
    coverage_note="完整支援：已整理116-1說明會與甄選規定、234所姊妹校專頁條件，並附115-2及115-1名額表供規劃參考（116-1名額預計11月底公告、12月收件）。",
    support_level="full",
    partner_count_hint=234,
    academic_score_minimum=70,
    student_card_signals=("天主教輔仁大學", "輔仁大學", "FUJENCATHOLICUNIVERSITY", "FJU"),
    # https://www.fju.edu.tw/academics.jsp — checked 2026-10-16.
    colleges=(
        "文學院",
        "藝術學院",
        "傳播學院",
        "教育與運動健康學院",
        "醫學院",
        "理工學院",
        "外語學院",
        "民生學院",
        "法律學院",
        "社會科學院",
        "管理學院",
        "織品服裝學院",
        "全人教育課程中心",
        "進修部",
    ),
)


SCU = UniversityProfile(
    id="scu",
    school_name="東吳大學",
    short_name="東吳",
    english_name="Soochow University",
    aliases=(
        "東吳大學",
        "私立東吳大學",
        "東吳",
        "SCU",
        "Soochow University",
        "Soochow University (Taiwan)",
    ),
    hero_image="/static/assets/scu-campus.svg",
    official_url="https://icae.scu.edu.tw/zh-hant/outbound-exchange/intro",
    coverage_note="完整支援：116學年度校級赴境外（國外126校、大陸62校、英美自費研修3校，共191校）現正開放線上申請（2026/09/14–11/16 12:00截止）。",
    support_level="full",
    partner_count_hint=191,
    academic_score_minimum=65,
    student_card_signals=("東吳大學", "SOOCHOWUNIVERSITY", "SCU"),
    # https://www-ch.scu.edu.tw/units-academic2 — checked 2026-10-16.
    colleges=(
        "人文社會學院",
        "外國語文學院",
        "理學院",
        "法學院",
        "商學院",
        "巨量資料管理學院",
    ),
)


NTNU = UniversityProfile(
    id="ntnu",
    school_name="國立臺灣師範大學",
    short_name="臺師大",
    english_name="National Taiwan Normal University",
    aliases=(
        "國立臺灣師範大學",
        "國立台灣師範大學",
        "臺灣師範大學",
        "台灣師範大學",
        "臺師大",
        "台師大",
        "師大",
        "NTNU",
        "National Taiwan Normal University",
    ),
    hero_image="/static/assets/ntnu-campus.svg",
    official_url="https://bds.oia.ntnu.edu.tw/bds/web/OUT",
    coverage_note="完整支援：116-1（2027春季出國）甄選簡章與236所合作校名額表已公告（線上申請 2026/11/01–11/15），並整合174校歷屆交換心得與四語組條件。",
    support_level="full",
    partner_count_hint=236,
    academic_score_minimum=60,
    student_card_signals=("國立臺灣師範大學", "國立台灣師範大學", "NATIONALTAIWANNORMALUNIVERSITY", "NTNU"),
    # https://bds.oia.ntnu.edu.tw/api/v1/ss/col — checked 2026-10-16.
    colleges=(
        "教育學院",
        "文學院",
        "理學院",
        "藝術學院",
        "科技與工程學院",
        "運動與休閒學院",
        "國際與社會科學學院",
        "音樂學院",
        "管理學院",
        "跨域科技產業創新研究學院",
    ),
)


SUPPORTED_UNIVERSITIES = (CGU, NTPU, NTU, CCU, NCU, TKU, FJU, SCU, NTNU)
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
