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
    coverage_note="已整理116-1公告、申請表及237筆合作校／交換方案。附表名額與條件供規劃參考，當期開放及接待校要求仍須逐項確認；116-1名額預計11月底公告。",
    support_level="full",
    partner_count_hint=237,
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
    academic_score_minimum=None,
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
    academic_score_minimum=None,
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

CYCU = UniversityProfile(
    id="cycu",
    school_name="中原大學",
    short_name="中原",
    english_name="Chung Yuan Christian University",
    aliases=(
        "cycu",
        "中原大學",
        "中原",
        "CYCU",
        "Chung Yuan Christian University",
    ),
    hero_image="/static/assets/cycu-campus.svg",
    official_url="https://oia.cycu.edu.tw/?page_id=2956&lang=zh",
    coverage_note="完整支援：115-2（2027春季出國）國際暨兩岸交換計畫與89所合作校名額、Fact Sheet及36校歷屆交換心得已完整整合。",
    support_level="full",
    partner_count_hint=89,
    academic_score_minimum=None,
    student_card_signals=("中原大學", "CHUNGYUANCHRISTIANUNIVERSITY", "CYCU"),
    # https://www.cycu.edu.tw/ — checked 2026-10-16.
    colleges=(
        "理學院",
        "工學院",
        "商學院",
        "法學院",
        "設計學院",
        "人文與教育學院",
        "電機資訊學院",
        "智慧運算與量子資訊學院",
        "半導體產業學院",
    ),
)

NTUST = UniversityProfile(
    id="ntust",
    school_name="國立臺灣科技大學",
    short_name="臺科大",
    english_name="National Taiwan University of Science and Technology",
    aliases=(
        "ntust",
        "國立臺灣科技大學",
        "國立台灣科技大學",
        "臺灣科技大學",
        "台灣科技大學",
        "臺科大",
        "台科大",
        "NTUST",
        "Taiwan Tech",
        "National Taiwan University of Science and Technology",
    ),
    hero_image="/static/assets/ntust-campus.svg",
    official_url="https://www.oia.ntust.edu.tw/p/412-1060-8921.php?Lang=zh-tw",
    coverage_note="完整支援：115-2（2027春季班）海外暨大陸交換生甄選簡章、237所合作校條件名額表及126校歷屆交換心得已完整整合。",
    support_level="full",
    partner_count_hint=237,
    academic_score_minimum=None,
    student_card_signals=("國立臺灣科技大學", "國立台灣科技大學", "NATIONALTAIWANUNIVERSITYOFSCIENCEANDTECHNOLOGY", "TAIWANTECH", "NTUST"),
    # https://www.ntust.edu.tw/ — checked 2026-10-16.
    colleges=(
        "工程學院",
        "電資學院",
        "管理學院",
        "設計學院",
        "人文社會學院",
        "應用科技學院",
        "產學創新學院",
    ),
)

YZU = UniversityProfile(
    id="yzu",
    school_name="元智大學",
    short_name="元智",
    english_name="Yuan Ze University",
    aliases=(
        "yzu",
        "元智大學",
        "私立元智大學",
        "元智",
        "YZU",
        "Yuan Ze University",
    ),
    hero_image="/static/assets/yzu-campus.svg",
    official_url="https://gao.yzu.edu.tw/index.php/tw/guo-ji-jiao-liu2/fu-wai-jiao-huan",
    coverage_note="收錄90校交換參考資料；母校指定規則部分查核，個別接待校及其餘內容仍待確認。",
    support_level="full",
    partner_count_hint=90,
    academic_score_minimum=70,
    student_card_signals=("元智大學", "YUANZEUNIVERSITY", "YZU"),
    # https://www.yzu.edu.tw/ — checked 2026-10-17.
    colleges=(
        "工程學院",
        "電機通訊學院",
        "資訊學院",
        "管理學院",
        "人文社會學院",
        "醫護學院",
    ),
)

FCU = UniversityProfile(
    id="fcu",
    school_name="逢甲大學",
    short_name="逢甲",
    english_name="Feng Chia University",
    aliases=(
        "fcu",
        "逢甲大學",
        "私立逢甲大學",
        "逢甲",
        "FCU",
        "Feng Chia University",
    ),
    hero_image="/static/assets/fcu-campus.svg",
    official_url="https://oia.fcu.edu.tw/sap/introduction/",
    coverage_note="完整支援：115-1選送（2027春季班）與115-2選送（2027秋季班）出國研修系統（oiasap）共161所合作校名額、課程目錄與95校歷屆心得／錄取紀錄已完整整合。",
    support_level="full",
    partner_count_hint=161,
    academic_score_minimum=None,
    student_card_signals=("逢甲大學", "FENGCHIAUNIVERSITY", "FCU"),
    # https://www.fcu.edu.tw/ & https://oiasap.fcu.edu.tw/v2/details/colleges — checked 2026-10-17.
    colleges=(
        "工程與科學學院",
        "商學院",
        "人文社會學院",
        "資訊電機學院",
        "建設學院",
        "金融學院",
        "國際科技與管理學院",
        "建築專業學院",
        "創能學院",
        "經營管理學院",
    ),
)

NSYSU = UniversityProfile(
    id="nsysu",
    school_name="國立中山大學",
    short_name="中山",
    english_name="National Sun Yat-sen University",
    aliases=(
        "nsysu",
        "國立中山大學",
        "中山大學",
        "中山",
        "NSYSU",
        "National Sun Yat-sen University",
    ),
    hero_image="/static/assets/nsysu-campus.svg",
    official_url="https://oia.nsysu.edu.tw/p/412-1308-20539.php?Lang=zh-tw",
    coverage_note="完整支援：2026–2027與2027–2028赴日本、其他國家與地區及中國大陸出國交換甄選簡章、218所合作校名額與Fact Sheet、西灣領航自動獎助及1,823篇歷屆交換心得與錄取名單已完整整合。",
    support_level="full",
    partner_count_hint=218,
    academic_score_minimum=None,
    student_card_signals=("國立中山大學", "中山大學", "NATIONALSUNYATSENUNIVERSITY", "NSYSU"),
    # https://www.nsysu.edu.tw/p/412-1000-88.php?Lang=zh-tw — checked 2026-10-18.
    colleges=(
        "文學院",
        "理學院",
        "工學院",
        "管理學院",
        "海洋科學學院",
        "社會科學院",
        "西灣學院",
        "醫學院",
        "半導體及重點科技研究學院",
        "國際金融研究學院",
    ),
)

NCHU = UniversityProfile(
    id="nchu",
    school_name="國立中興大學",
    short_name="中興",
    english_name="National Chung Hsing University",
    aliases=(
        "nchu",
        "國立中興大學",
        "中興大學",
        "中興",
        "興大",
        "NCHU",
        "National Chung Hsing University",
    ),
    hero_image="/static/assets/nchu-campus.svg",
    official_url="https://www.oia.nchu.edu.tw/index.php/2-uncategorised/154-1-1-exchange-info",
    coverage_note="完整支援：116學年度第1學期（秋季班）出國交換甄選簡章、226所海外及大陸交換合作校名額與Fact Sheet、希望之橋暨學海系列獎學金、548篇學長姐交換心得影音及422人次錄取榜單已完整整合。",
    support_level="full",
    partner_count_hint=226,
    academic_score_minimum=60,
    student_card_signals=("國立中興大學", "中興大學", "NATIONALCHUNGHSINGUNIVERSITY", "NCHU"),
    # https://www.nchu.edu.tw/about-route-map/mid/85 — checked 2026-10-18.
    colleges=(
        "文學院",
        "農業暨自然資源學院",
        "理學院",
        "工學院",
        "生命科學院",
        "獸醫學院",
        "管理學院",
        "法政學院",
        "電機資訊學院",
        "醫學院",
        "創新產業暨國際學院",
        "循環經濟研究學院",
    ),
)

NTUT = UniversityProfile(
    id="ntut",
    school_name="國立臺北科技大學",
    short_name="北科大",
    english_name="National Taipei University of Technology",
    aliases=(
        "ntut",
        "國立臺北科技大學",
        "國立台北科技大學",
        "臺北科技大學",
        "台北科技大學",
        "臺北科大",
        "台北科大",
        "北科大",
        "北科",
        "NTUT",
        "Taipei Tech",
        "National Taipei University of Technology",
    ),
    hero_image="/static/assets/ntut-campus.svg",
    official_url="https://oia.ntut.edu.tw/p/412-1032-9242.php?Lang=zh-tw",
    coverage_note="已收錄206筆合作方案；母校指定條文部分查核，逐校現行名額、資格、生活與來源仍待核對。",
    support_level="full",
    partner_count_hint=206,
    academic_score_minimum=None,
    student_card_signals=("國立臺北科技大學", "臺北科技大學", "NATIONALTAIPEIUNIVERSITYOFTECHNOLOGY", "TAIPEITECH", "NTUT"),
    # https://www.ntut.edu.tw/p/404-1007-85216.php — checked 2026-10-18.
    colleges=(
        "機電學院",
        "電資學院",
        "工程學院",
        "管理學院",
        "設計學院",
        "人文與社會科學學院",
        "創新前瞻科技研究學院",
    ),
)

NCCU = UniversityProfile(
    id="nccu",
    school_name="國立政治大學",
    short_name="政大",
    english_name="National Chengchi University",
    aliases=(
        "nccu",
        "國立政治大學",
        "政治大學",
        "政大",
        "NCCU",
        "Chengchi University",
        "National Chengchi University",
    ),
    hero_image="/static/assets/nccu-campus.svg",
    official_url="https://outbound.nccu.edu.tw/",
    coverage_note="完整支援：115-1／115-2 校級赴國外（八大語組）及赴大陸地區交換學生甄選簡章、266所合作姊妹校名額與語言門檻、6項赴外交換暨學海系列獎助學金及589篇歷屆學長姐交換心得報告已完整整合。",
    support_level="full",
    partner_count_hint=266,
    academic_score_minimum=None,
    student_card_signals=("國立政治大學", "政治大學", "NATIONALCHENGCHIUNIVERSITY", "NCCU"),
    # https://www.nccu.edu.tw/p/412-1000-86.php?Lang=zh-tw — checked 2026-10-18.
    colleges=(
        "文學院",
        "理學院",
        "社會科學學院",
        "法學院",
        "商學院",
        "外國語文學院",
        "傳播學院",
        "國際事務學院",
        "教育學院",
        "創新國際學院",
        "資訊學院",
        "X實驗學院",
        "國際金融學院",
    ),
)

NCKU = UniversityProfile(
    id="ncku",
    school_name="國立成功大學",
    short_name="成大",
    english_name="National Cheng Kung University",
    aliases=(
        "ncku",
        "國立成功大學",
        "成功大學",
        "成大",
        "NCKU",
        "Cheng Kung University",
        "National Cheng Kung University",
    ),
    hero_image="/static/assets/ncku-campus.svg",
    official_url="https://oia.ncku.edu.tw/p/404-1032-227700.php?Lang=zh-tw",
    coverage_note="完整支援：116-1（2027秋季班）及115-1／115-2校級出國與赴大陸地區交換學生甄選簡章、211所合作姊妹校名額與語言門檻、6項赴外交換暨學海系列獎助學金及357篇歷屆學長姐交換心得報告已完整整合。",
    support_level="full",
    partner_count_hint=211,
    academic_score_minimum=77,
    student_card_signals=("國立成功大學", "成功大學", "NATIONALCHENGKUNGUNIVERSITY", "NCKU"),
    # https://www.ncku.edu.tw/p/412-1000-85.php?Lang=zh-tw — checked 2026-10-18.
    colleges=(
        "文學院",
        "理學院",
        "工學院",
        "管理學院",
        "醫學院",
        "社會科學院",
        "電機資訊學院",
        "規劃與設計學院",
        "生物科學與科技學院",
        "智慧半導體及永續製造學院",
        "敏求智慧運算學院",
    ),
)

NYCU = UniversityProfile(
    id="nycu",
    school_name="國立陽明交通大學",
    short_name="陽明交大",
    english_name="National Yang Ming Chiao Tung University",
    aliases=(
        "nycu",
        "國立陽明交通大學",
        "陽明交通大學",
        "陽明交大",
        "NYCU",
        "國立交通大學",
        "國立陽明大學",
        "NCTU",
        "YM",
        "Yang Ming Chiao Tung University",
        "National Yang Ming Chiao Tung University",
    ),
    hero_image="/static/assets/nycu-campus.svg",
    official_url="https://oia.nycu.edu.tw/oia/ch/app/data/list?module=nycu0006&id=286",
    coverage_note="243筆合作資料部分查核：182筆對上115-2已截止名額表；116台聯大分案核對，個別接待校條件及全部欄位尚未核實。",
    support_level="full",
    partner_count_hint=243,
    academic_score_minimum=None,
    student_card_signals=(
        "國立陽明交通大學",
        "陽明交通大學",
        "陽明交大",
        "NATIONALYANGMINGCHIAOTUNGUNIVERSITY",
        "NYCU",
        "NCTU",
    ),
    # https://www.nycu.edu.tw/nycu/ch/app/artwebsite/view?module=artwebsite&id=459&serno=750e3d3e-8ef2-4801-a100-e8733052689b — checked 2026-10-19.
    colleges=(
        "人文藝術與社會學院",
        "工學院",
        "工程生物科學學院",
        "牙醫學院",
        "生命科學院",
        "生物醫學暨工程學院",
        "光電學院",
        "科技法律學院",
        "客家文化學院",
        "理學院",
        "產學創新研究學院",
        "國際半導體產業學院",
        "智慧科學暨綠能學院",
        "電機學院",
        "資訊學院",
        "管理學院",
        "醫學院",
        "藥物科學院",
        "護理學院",
        "博雅書苑",
    ),
)

NTHU = UniversityProfile(
    id="nthu",
    school_name="國立清華大學",
    short_name="清大",
    english_name="National Tsing Hua University",
    aliases=(
        "nthu",
        "國立清華大學",
        "清華大學",
        "清大",
        "NTHU",
        "Tsing Hua University",
        "National Tsing Hua University",
    ),
    hero_image="/static/assets/nthu-campus.svg",
    official_url="https://oga.site.nthu.edu.tw/p/412-1524-18680.php?Lang=zh-tw",
    coverage_note="完整支援：2027秋／2028春校級海外及赴陸港澳出國交換暨116-1台灣聯合大學系統交換計畫簡章、176所合作姊妹校（含A/B/C/D第一志願熱門程度分級）名額與門檻、5項出國交換暨學海系列獎助學金及328篇歷屆學長姐返國成果報告書已完整整合。",
    support_level="full",
    partner_count_hint=176,
    academic_score_minimum=None,
    student_card_signals=(
        "國立清華大學",
        "清華大學",
        "NATIONALTSINGHUAUNIVERSITY",
        "NTHU",
    ),
    # https://www.nthu.edu.tw/units/education — checked 2026-10-19.
    colleges=(
        "理學院",
        "工學院",
        "原子科學院",
        "人文社會學院",
        "生命科學暨醫學院",
        "電機資訊學院",
        "科技管理學院",
        "竹師教育學院",
        "藝術學院",
        "台北政經學院",
        "永續學院",
        "半導體研究學院",
        "清華學院",
    ),
)

PCCU = UniversityProfile(
    id="pccu",
    school_name="中國文化大學",
    short_name="文大",
    english_name="Chinese Culture University",
    aliases=(
        "pccu",
        "中國文化大學",
        "文化大學",
        "文化",
        "文大",
        "PCCU",
        "Chinese Culture University",
    ),
    hero_image="/static/assets/pccu-campus.svg",
    official_url="https://oima.pccu.edu.tw/exchanges.htm",
    coverage_note="已部分核對各甄選管道、國合組47筆參考名額與赴陸第二階段公告；135筆合作方案的個別接待校條件及生活資料仍待核實。",
    support_level="basic",
    partner_count_hint=135,
    academic_score_minimum=None,
    student_card_signals=(
        "中國文化大學",
        "文化大學",
        "CHINESECULTUREUNIVERSITY",
        "PCCU",
    ),
    # https://www.pccu.edu.tw/wwwJson/GetCRLvl1.json — checked 2026-10-19.
    colleges=(
        "文學院",
        "國際暨外語學院",
        "理工學院",
        "法學院",
        "社會科學院",
        "環境規劃暨生物資源學院",
        "商學院",
        "新聞暨傳播學院",
        "藝術學院",
        "教育學院",
        "體育運動健康學院",
        "永續創新學院",
    ),
)

WZU = UniversityProfile(
    id="wzu",
    school_name="文藻外語大學",
    short_name="文藻",
    english_name="Wenzao Ursuline University of Languages",
    aliases=(
        "wzu",
        "文藻外語大學",
        "文藻外語學院",
        "文藻外大",
        "文藻",
        "WZU",
        "Wenzao Ursuline University of Languages",
        "Wenzao",
    ),
    hero_image="/static/assets/wzu-campus.svg",
    official_url="https://d020.wzu.edu.tw/article/530752",
    coverage_note="115-2母校共用規則部分核對；147筆方案的當期名額、接待校資格、生活資訊及其他主張仍待逐項查證。",
    support_level="full",
    partner_count_hint=147,
    academic_score_minimum=None,
    student_card_signals=(
        "文藻外語大學",
        "文藻",
        "WENZAOURSULINEUNIVERSITYOFLANGUAGES",
        "WZU",
    ),
    # https://www.wzu.edu.tw/ — checked 2026-10-19.
    colleges=(
        "國際文教暨涉外事務學院",
        "歐亞語文學院",
        "新媒體暨管理學院",
        "華語學院",
        "吳甦樂人文學院",
    ),
)

NKUST = UniversityProfile(
    id="nkust",
    school_name="國立高雄科技大學",
    short_name="高科大",
    english_name="National Kaohsiung University of Science and Technology",
    aliases=(
        "nkust",
        "國立高雄科技大學",
        "高雄科技大學",
        "高科大",
        "NKUST",
        "National Kaohsiung University of Science and Technology",
    ),
    hero_image="/static/assets/nkust-campus.svg",
    official_url="https://oia.nkust.edu.tw/unit-4-374-21.html",
    coverage_note="已部分核對115校級簡章及97筆歷史表對應；107筆方案的116當期接待校條件與生活資料仍待核實。",
    support_level="basic",
    partner_count_hint=107,
    academic_score_minimum=None,
    student_card_signals=(
        "國立高雄科技大學",
        "高雄科技大學",
        "高科大",
        "NATIONALKAOHSIUNGUNIVERSITYOFSCIENCEANDTECHNOLOGY",
        "NKUST",
    ),
    # https://www.nkust.edu.tw/p/412-1000-1495.php?Lang=zh-tw — checked 2026-10-20.
    colleges=(
        "工學院",
        "智慧機電學院",
        "電機與資訊學院",
        "海事學院",
        "水圈學院",
        "商業智慧學院",
        "管理學院",
        "海洋商務學院",
        "財務金融學院",
        "創新設計學院",
        "外語學院",
        "共同教育學院",
    ),
)

YUNTECH = UniversityProfile(
    id="yuntech",
    school_name="國立雲林科技大學",
    short_name="雲科大",
    english_name="National Yunlin University of Science and Technology",
    aliases=(
        "yuntech",
        "nyust",
        "國立雲林科技大學",
        "雲林科技大學",
        "雲科大",
        "YunTech",
        "YUNTECH",
        "NYUST",
        "National Yunlin University of Science and Technology",
    ),
    hero_image="/static/assets/yuntech-campus.svg",
    official_url="https://tdx.yuntech.edu.tw/",
    coverage_note="112筆合作紀錄；母校規則及108筆115-2校名對應部分核對，個別接待校、生活資訊與其他欄位待查，不能宣稱完整核實。",
    support_level="basic",
    partner_count_hint=112,
    academic_score_minimum=None,
    student_card_signals=(
        "國立雲林科技大學",
        "雲林科技大學",
        "雲科大",
        "NATIONALYUNLINUNIVERSITYOFSCIENCEANDTECHNOLOGY",
        "YUNTECH",
        "NYUST",
    ),
    # https://www.yuntech.edu.tw/ — checked 2026-10-20.
    colleges=(
        "工程學院",
        "管理學院",
        "設計學院",
        "人文與科學學院",
        "未來學院",
    ),
)

NTOU = UniversityProfile(
    id="ntou",
    school_name="國立臺灣海洋大學",
    short_name="海大",
    english_name="National Taiwan Ocean University",
    aliases=(
        "ntou",
        "國立臺灣海洋大學",
        "國立台灣海洋大學",
        "臺灣海洋大學",
        "台灣海洋大學",
        "海洋大學",
        "海大",
        "NTOU",
        "National Taiwan Ocean University",
    ),
    hero_image="/static/assets/ntou-campus.svg",
    official_url="https://oia.ntou.edu.tw/p/412-1022-6958.php?Lang=zh-tw",
    coverage_note="123筆合作紀錄；母校規則及45筆已截止名單中文校名部分核對，個別接待校、生活資訊與其餘欄位待查，不是完整驗證。",
    support_level="basic",
    partner_count_hint=123,
    academic_score_minimum=None,
    student_card_signals=(
        "國立臺灣海洋大學",
        "臺灣海洋大學",
        "海大",
        "NATIONALTAIWANOCEANUNIVERSITY",
        "NTOU",
    ),
    # https://www.ntou.edu.tw/academics — checked 2026-10-20.
    colleges=(
        "海運暨管理學院",
        "生命科學院",
        "海洋科學與資源學院",
        "工學院",
        "電機資訊學院",
        "人文社會科學院",
        "海洋法律與政策學院",
        "國際學院",
    ),
)

NCUE = UniversityProfile(
    id="ncue",
    school_name="國立彰化師範大學",
    short_name="彰師大",
    english_name="National Changhua University of Education",
    aliases=(
        "ncue",
        "國立彰化師範大學",
        "彰化師範大學",
        "彰化師大",
        "彰師大",
        "彰師",
        "NCUE",
        "National Changhua University of Education",
    ),
    hero_image="/static/assets/ncue-campus.svg",
    official_url="https://oicaweb.ncue.edu.tw/p/412-1002-1171.php?Lang=zh-tw",
    coverage_note="完整支援：國際暨兩岸事務處 116學年度（2027秋季、2028春季）赴國外非大陸姊妹校交換研修暨教育部學海飛颺／惜珠甄選簡章、2027年春季班（115-2學期）及 115-1 赴大陸及港澳地區姊妹校交換計畫、跨國雙聯學制與全球共 108 所合作姊妹校（中國大陸、美國、印尼、德國、日本、韓國、法國、泰國、英國、捷克、西班牙、馬來西亞、加拿大、澳洲、土耳其、香港、烏拉圭、俄羅斯、羅馬尼亞、瑞士、蒙古、阿拉伯聯合大公國、越南等 23 個國家與地區）名額與語檢門檻、教育部學海系列獎補助暨 409 篇學長姐返國交換心得已完整整合。",
    support_level="full",
    partner_count_hint=108,
    academic_score_minimum=70,
    student_card_signals=(
        "國立彰化師範大學",
        "彰化師範大學",
        "彰師大",
        "NATIONALCHANGHUAUNIVERSITYOFEDUCATION",
        "NCUE",
    ),
    # https://www.ncue.edu.tw/p/412-1000-867.php?Lang=zh-tw — checked 2026-10-20.
    colleges=(
        "教育學院",
        "理學院",
        "工學院",
        "管理學院",
        "社會科學暨體育學院",
        "文學院",
        "技術及職業教育學院",
    ),
)

NKNU = UniversityProfile(
    id="nknu",
    school_name="國立高雄師範大學",
    short_name="高師大",
    english_name="National Kaohsiung Normal University",
    aliases=(
        "nknu",
        "國立高雄師範大學",
        "高雄師範大學",
        "高雄師大",
        "高師大",
        "高師",
        "NKNU",
        "National Kaohsiung Normal University",
    ),
    hero_image="/static/assets/nknu-campus.svg",
    official_url="https://oia.nknu.edu.tw/exchange-programs.php",
    coverage_note="完整支援：國際事務處赴外交換研修暨教育部學海飛颺／惜珠計畫甄選（每年 11/11–12/31 線上申請）、大陸地區（含港澳地區）姊妹校交換計畫（2027春季班及2026秋季班）、境外大學跨校雙聯學制與全球共 143 所合作姊妹校（含 36 所當期開放交換及雙聯名額校、107 所正式締約姊妹校，橫跨美、德、法、捷、瑞、奧、英、西、波、匈、俄、斯、巴、澳、日、韓、泰、菲、越、印、馬、印度、蒙、大陸及港澳等 26 個國家與地區）名額與語檢門檻、出國選修課程與學分抵免規定暨 16 篇學長姐返國交換心得已完整整合。",
    support_level="full",
    partner_count_hint=143,
    academic_score_minimum=70,
    student_card_signals=(
        "國立高雄師範大學",
        "高雄師範大學",
        "高師大",
        "NATIONALKAOHSIUNGNORMALUNIVERSITY",
        "NKNU",
    ),
    # https://w3.nknu.edu.tw/ — checked 2026-10-20.
    colleges=(
        "教育學院",
        "文學院",
        "理學院",
        "科技學院",
        "藝術學院",
    ),
)

TMU = UniversityProfile(
    id="tmu",
    school_name="臺北醫學大學",
    short_name="北醫大",
    english_name="Taipei Medical University",
    aliases=(
        "tmu",
        "臺北醫學大學",
        "台北醫學大學",
        "北醫大",
        "北醫",
        "臺北醫大",
        "台北醫大",
        "TMU",
        "Taipei Medical University",
    ),
    hero_image="/static/assets/tmu-campus.svg",
    official_url="https://oge.tmu.edu.tw/zh-hant/%e5%ad%b8%e7%94%9f%e4%ba%a4%e6%b5%81/tmu-student-outbound-exchange/",
    coverage_note="完整支援：國際事務處國際盟校組 2026（民國115）年教育部學海飛颺／學海惜珠／學海築夢／新南向學海築夢計畫（第一梯次 1/16、第二梯次 9/7 截止）、校內《境外研修暨見實習獎勵辦法》獎學金（每年 1/15、5/15 兩梯次截止）、7 大學院 32 個跨國雙聯學位學制（涵蓋美、加、法、義、丹、日、澳、印尼等 18 所名校）與全球共 201 所合作盟校及教學醫院（含 34 所當期開放交換、見實習及雙聯學位校與 167 所正式締約盟校，橫跨歐、美、亞、大洋、非 37 個國家與地區）語檢門檻、學分抵免規定暨 55 篇歷屆學長姐海外交流與臨床見實習心得報告已完整整合。",
    support_level="full",
    partner_count_hint=201,
    academic_score_minimum=75,
    student_card_signals=(
        "臺北醫學大學",
        "台北醫學大學",
        "北醫大",
        "TAIPEIMEDICALUNIVERSITY",
        "TMU",
    ),
    # https://www.tmu.edu.tw/ — checked 2026-10-20.
    colleges=(
        "醫學院",
        "口腔醫學院",
        "藥學院",
        "護理學院",
        "公共衛生學院",
        "醫學科技學院",
        "人文暨社會科學院",
        "管理學院",
        "醫學工程學院",
        "營養學院",
        "跨領域學院",
    ),
)

CSMU = UniversityProfile(
    id="csmu",
    school_name="中山醫學大學",
    short_name="中山醫",
    english_name="Chung Shan Medical University",
    aliases=(
        "csmu",
        "中山醫學大學",
        "中山醫大",
        "中山醫",
        "CSMU",
        "Chung Shan Medical University",
    ),
    hero_image="/static/assets/csmu-campus.svg",
    official_url="https://oia.csmu.edu.tw/?Lang=zh-tw",
    coverage_note="完整支援：國際事務處 116 學年度（2027–2028）赴美國聖馬丁大學（每學期 3 名免學費）、美國密西根州奧克蘭大學（每年 15 名 ASAP 交換暨生物學 4+1/4+2 學碩連讀）、日本德島文理大學（每學期 2 名免學費＋PP 升學研究所計畫 1 名免學費）甄選（2026/10/22 截止）、教育部 116 年度學海飛颺／惜珠獎學金（2027/01/06 截止，每人補助 5萬–30萬元）、2027春季美國路易斯安那州立大學醫學中心（LSUHSC）研究獎學金（每月 USD 2,500）、跨國雙聯學位（安德魯大學、杜肯大學）與全球共 124 所合作姊妹校及教學醫院（含 49 所當期開放交換、雙聯、研究及臨床見實習重點機構與 75 所正式締約姊妹校，橫跨 26 個國家與地區）語檢門檻、書審配分（40%/35%/20%/5%）暨 31 篇歷屆學長姐與師長海外研修心得報告已完整整合。",
    support_level="full",
    partner_count_hint=124,
    academic_score_minimum=75,
    student_card_signals=(
        "中山醫學大學",
        "中山醫大",
        "中山醫",
        "CHUNGSHANMEDICALUNIVERSITY",
        "CSMU",
    ),
    # https://www.csmu.edu.tw/ — checked 2026-10-21.
    colleges=(
        "醫學院",
        "口腔醫學院",
        "醫學科技學院",
        "健康管理學院",
    ),
)

CMU = UniversityProfile(
    id="cmu",
    school_name="中國醫藥大學",
    short_name="中醫大",
    english_name="China Medical University",
    aliases=(
        "cmu",
        "中國醫藥大學",
        "中醫大",
        "中國醫大",
        "中國醫",
        "CMU",
        "China Medical University",
    ),
    hero_image="/static/assets/cmu-campus.svg",
    official_url="https://cmucia.cmu.edu.tw/",
    coverage_note="完整支援：國際事務處與 9 大學院 115–116 學年度（2026–2028）校級赴日本北海道大學（每年 5 名免學費＋中醫大補助來回經濟艙機票與每月 NT$5,000 生活費）、日本北見工業大學（每年 3 名免學費＋機票與每月 NT$5,000 生活費）、香港教育大學（每年 4 名免學費）交換生計畫、7 校 11 個跨國雙聯學位暨專案獎助學金（澳洲紐卡索大學護理博士最高補助 NT$50萬、美國南加州大學 USC 藥學系 MS 與凱克醫學院 MD/MPH 雙聯最高補助 NT$45萬、美國杜蘭大學 MD/MPH 雙聯最高補助 NT$40萬、美國喬治亞州立大學雙聯最高補助 NT$35萬、美國南卡羅萊納大學 3+2 學碩與 MD/MPH 雙聯及澳洲格里菲斯大學全球公衛碩士雙聯最高補助 NT$30萬、美國南達科塔州立大學營養學系 2+2 雙學士補助 2 年中醫大全額學雜費）、健康照護學院物理治療學系 115-1 海外臨床專業實習（新加坡中央醫院 4 名、神戶中央市民醫院 2 名、關西電力醫院 2 名、順天堂醫院 2 名，2027/01/10–01/30 實習）與全球共 174 所合作姊妹校及教學醫院（含 38 所當期開放交換、雙聯、海外臨床見實習與學海築夢重點機構及 136 所正式締約姊妹校，橫跨 31 個國家與地區）語檢門檻、學業 A-（GPA 3.0／80 分）與操行 80 分規定暨 27 篇歷屆師生海外研修心得報告已完整整合。",
    support_level="full",
    partner_count_hint=174,
    academic_score_minimum=80,
    student_card_signals=(
        "中國醫藥大學",
        "中醫大",
        "中國醫大",
        "中國醫",
        "CHINAMEDICALUNIVERSITY",
        "CMU",
    ),
    # https://www.cmu.edu.tw/academic.php — checked 2026-10-21.
    colleges=(
        "醫學院",
        "中醫學院",
        "藥學院",
        "公共衛生學院",
        "健康照護學院",
        "生命科學院",
        "牙醫學院",
        "醫學工程學院",
        "人文與科技學院",
    ),
)

KMU = UniversityProfile(
    id="kmu",
    school_name="高雄醫學大學",
    short_name="高醫大",
    english_name="Kaohsiung Medical University",
    aliases=(
        "kmu",
        "高雄醫學大學",
        "高醫大",
        "高醫",
        "高雄醫大",
        "KMU",
        "Kaohsiung Medical University",
    ),
    hero_image="/static/assets/kmu-campus.svg",
    official_url="https://ciae2.kmu.edu.tw/index.php/zh-tw",
    coverage_note="完整支援：國際事務處與 7 大學院 115–116 學年度（2026–2028）醫學院 2027 海外臨床見實習（21 校 64+ 名：美國哈佛醫學院 6 名［免見習費與申請費＋KMU-Harvard Foundation USD 500＋北美校友會 NT$15,000］、希望之城 4 名、羅格斯 2 名、梅哈里 2 名、夏威夷大學 1 名、德國科隆大學 4 名、澳洲邦德大學 4 名、日本京都大學 2 名、慶應義塾大學 3 名、東京醫科大學 2 名［免學費＋免費住宿］、神戶大學 3 名、德島 3 名、信州 2 名、愛媛 4 名、藤田醫大 2 名、韓國首爾大學 2 名、亞洲大學 4 名、香港大學 4 名、新加坡國立大學 4 名、南洋理工大學 4 名、泰國宋卡王子大學 4 名）、校級赴日本順天堂大學長期交換生計畫（JLCSP / LAP 免學費）、10 校跨國雙聯學位（瑞典烏普薩拉大學每年 6 名免學費、匈牙利賽蓋德大學每年 3 名免學費＋免費住宿、日本熊本大學 2026/09 新簽醫學博士雙聯、美國加州大學爾灣分校 UCI、City of Hope、法國艾克斯-馬賽大學、澳洲格里菲斯大學、泰國朱拉隆功大學藥學雙聯博士每年 2 名免學費、瑪希朵大學、清邁大學）、口腔醫學院／藥學院／護理學院／健康科學院（含瑞典卡羅林斯卡醫學院 KI 3 名、美國南加大 USC 6 名、約翰霍普金斯醫院 4 名、新加坡陳篤生醫院 6 名）／人社院海外見實習、115 年度博士生千里馬出國研究計畫（最高補助 NT$50萬）、國際處出國研習補助（歐美非機票最高 NT$5萬＋月領 NT$2.5萬）與全球共 188 所合作姊妹校及教學醫院（含 56 所當期開放交換、雙聯与臨床見實習重點機構及 132 所正式締約姊妹校，橫跨 30 個國家與地區）語檢門檻暨 56 篇歷屆師生海外研修心得報告已完整整合。",
    support_level="full",
    partner_count_hint=188,
    academic_score_minimum=60,
    student_card_signals=(
        "高雄醫學大學",
        "高醫大",
        "高醫",
        "高雄醫大",
        "KAOHSIUNGMEDICALUNIVERSITY",
        "KMU",
    ),
    # https://www.kmu.edu.tw/ — checked 2026-10-21.
    colleges=(
        "醫學院",
        "口腔醫學院",
        "藥學院",
        "護理學院",
        "健康科學院",
        "生命科學院",
        "人文社會科學院",
    ),
)

MCU = UniversityProfile(
    id="mcu",
    school_name="銘傳大學",
    short_name="銘傳",
    english_name="Ming Chuan University",
    aliases=(
        "mcu",
        "銘傳大學",
        "銘傳",
        "北銘",
        "桃銘",
        "MCU",
        "Ming Chuan University",
    ),
    hero_image="/static/assets/mcu-campus.svg",
    official_url="https://iee.mcu.edu.tw/zh-hant/",
    coverage_note="完整支援：國際教育交流處（IEE）與僑陸事務組 116 學年度（2027秋季／2028春季）海外交換學生計畫（65 所開放姊妹校，秋季班 2027/03/03、春季班 2027/09/20 截止）、10 校 14 個跨國雙學位項目（含英國艾塞克斯大學 3+1 學碩雙學位 £6,500 獎學金＋早鳥 £1,000 減免、西英格蘭大學雙學位 £2,000 獎學金、美國塞基諾州立大學 2+2 BBA 與 1+1 MBA、德州大學聖安東尼奧分校 3.5+1.5 財金學碩、紐約市立大學約翰傑伊學院 1+1 雙碩士、林肯紀念大學 2+2、法國雷恩商學院 3+1 學士與 MSc、日本產業能率大學 2+2、韓國水原大學 2+2、泰國東方大學 2+2）、2027 春季班赴大陸頂尖大學交換計畫（42 所 985／211／知名高校，第三次公告至 2026/10/23 12:00 截止）、教育部 116 學海飛颺／惜珠獎學金與全球共 202 所合作姊妹校（含 113 所當期開放申請學校及 89 所正式締約姊妹校，橫跨 23 個國家與地區）語檢門檻、保證金 NT$5,000 與家長同意書公證規定暨 126 篇歷屆學長姐返國研修心得報告已完整整合。",
    support_level="full",
    partner_count_hint=202,
    academic_score_minimum=70,
    student_card_signals=(
        "銘傳大學",
        "銘傳",
        "MINGCHUANUNIVERSITY",
        "MCU",
    ),
    # https://web.mcu.edu.tw/zh-hant/academics-2/ — checked 2026-10-21.
    colleges=(
        "管理學院",
        "傳播學院",
        "法律學院",
        "金融科技學院",
        "電機資訊學院",
        "設計學院",
        "人文社會科學暨教育學院",
        "觀光學院",
        "健康暨醫學工程學院",
        "國際學院",
    ),
)

NTUB = UniversityProfile(
    id="ntub",
    school_name="國立臺北商業大學",
    short_name="北商大",
    english_name="National Taipei University of Business",
    aliases=(
        "ntub",
        "國立臺北商業大學",
        "國立台北商業大學",
        "臺北商業大學",
        "台北商業大學",
        "北商大",
        "北商",
        "臺北商大",
        "台北商大",
        "NTUB",
        "National Taipei University of Business",
    ),
    hero_image="/static/assets/ntub-campus.svg",
    official_url="https://oia.ntub.edu.tw/p/412-1006-3152.php?Lang=zh-tw",
    coverage_note="完整支援：國際事務處 115–116 學年度海外及大陸地區交換學生甄選計畫（第一梯次春季班約 9–10 月、第二梯次秋季班約 2–3 月收件，115-2 甄選說明會 2026/10/14 12:15 舉辦）、11 所跨國雙聯學位項目（美國匹茲堡州立大學 3+1+1 雙學士＋MBA 與 1+1 財金雙碩士、明尼蘇達州立大學曼徹斯特分校 2+2、舊金山州立大學 3+1+1、威斯康辛大學河瀑分校 2+2、法國雷恩商學院 3+1 雙學士與 3+1.5 碩士、德國凱撒斯勞斯滕應科大雙碩士、巴登符騰堡雙元制大學雙學士、英國哈德斯菲爾德大學 3+1、瑞士 BHMS 3+1、澳洲皇家墨爾本理工大學 RMIT 2+2、雪梨科技大學 UTS 雙學士與學碩）、教育部學海飛颺／學海惜珠與《王春滿清寒短期研修交流助學金》（最高補助 NT$20萬）及全球共 93 所合作姊妹校（含 51 所當期開放申請學校與 42 所正式締約姊妹校，橫跨 18 個國家與地區）語檢門檻、書審 60%＋面試 40% 配分規定暨 295 篇歷屆學長姐返國交換心得報告已完整整合。",
    support_level="full",
    partner_count_hint=93,
    academic_score_minimum=80,
    student_card_signals=(
        "國立臺北商業大學",
        "臺北商業大學",
        "北商大",
        "NATIONALTAIPEIUNIVERSITYOFBUSINESS",
        "NTUB",
    ),
    # https://www.ntub.edu.tw/p/412-1000-1129.php?Lang=zh-tw — checked 2026-10-22.
    colleges=(
        "財經學院",
        "管理學院",
        "國際行銷學院",
        "創新設計與經營學院",
    ),
)


SUPPORTED_UNIVERSITIES = (CGU, NTPU, NTU, CCU, NCU, TKU, FJU, SCU, NTNU, CYCU, NTUST, YZU, FCU, NSYSU, NCHU, NTUT, NCCU, NCKU, NYCU, NTHU, PCCU, WZU, NKUST, YUNTECH, NTOU, NCUE, NKNU, TMU, CSMU, CMU, KMU, MCU, NTUB)
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
