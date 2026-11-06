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
    coverage_note="完整支援試點：已套用交換申請流程、116 學年度三語組官方名額表（校內申請 10/23 17:00 已截止）、2026/10/22 學海飛颺與惜珠甄選辦法修正公告及 10/12 法國 EFREI 交換說明會；法律學院院級交換（10/30 11:00 截止，僅適用法律院）與校級預告／商院公告讀取缺口分開標示。",
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
    coverage_note="已整理116-1校級甄選時程（11/3 10:00–11/9 16:00線上報名、12/2成績公布、12/7一階志願截止）、文件、補助、289個合作項目與德國哥廷根大學交換說明會（頁尾10/30–10/31維護通知經核實為2022舊版彈窗；OIA正式列表oia.ntu.edu.tw/outgoing/school.list與9個候選詳頁讀取異常時保留10/22成功基準，不等於名額恢復）；合作校本期名額與未核實條件標示待確認。",
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
    coverage_note="116學年度第一梯次簡章（2026-09-05公告，11/16 09:00開放線上申請至12/04 12:00）與2026/10/22最新交換姐妹校列表（116exchangeschoollist-1022.pdf，較10/13版移除北方高等商業學院EDHEC後共214列）已公告；外校當期條件逐項待核對。",
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
    coverage_note="完整支援：116-1（2027春季出國）甄選簡章與236所合作校名額表（29頁／285條目／96學程）已公告（線上申請 2026/11/01–11/15，赴外交換專區入口 bds.oia.ntnu.edu.tw/bds/web/OUT 與 outgoing-apply 正常運作；若由國際處主網巡查未尋獲子系統入口或遇短暫連線異常時保留已核實基準），並整合174校歷屆交換心得與四語組條件；院級公告正文截斷，不將院級名額併入校級。",
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
    official_url="https://oia.cycu.edu.tw/?p=6336",
    coverage_note="完整支援：出國交換介紹頁（?p=6336，未列發布日期、名額或截止日）仍連結「115-2 (2027春季班)赴國際姊妹校交換 第二梯次遴選公告」（?p=9903，20校共50名、GPA 3.0以上，9/24開放填表、10/7 12:00截止收紙本、10/14面試，與已截止紀錄無衝突），最新公告頁（?page_id=99，諮詢公告正文首次建檔僅作基準）另載 2026-10-21「教育部選送學生出國研修或國外專業實習補助要點（學海計畫）說明會」（校內師生可自行報名，列表未寫日期細節），頁面上尚未出現 116-1（2027秋季班）遴選公告；連同赴大陸交換共89所合作校、Fact Sheet及36校歷屆交換心得已完整整合。",
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
    official_url="https://oia.ntust.edu.tw/p/405-1060-62102,c9056.php?Lang=zh-tw",
    coverage_note="完整支援：116-1（2027秋季班）赴海外交換學生計畫甄選簡章（_中文_20260915.pdf，歐美亞〔不含中國大陸〕澳姐妹校，線上申請 2026/12/03 10:00–12/07 15:00；報名主系統 stu88/fall2027 恢復讀取且與10/22基準一致，當期正式名額待開放期間核對）與 115-2（2027春季班）海外暨大陸參考簡章、237所合作校條件名額表及126校歷屆交換心得已完整整合。",
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
    coverage_note="收錄90校交換參考資料；母校指定規則部分查核，正式Google名額表讀取失敗時保留10/21最後成功基準（不推論今日名額無變），個別接待校及其餘內容仍待確認。",
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
    coverage_note="完整支援：115-1選送（2027春季班）與115-2選送（2027秋季班）出國研修系統（oiasap）共161所合作校名額、課程目錄與95校歷屆心得／錄取紀錄已完整整合；日台獎學金2026/10/27 10:00校內期限已到（列表移除、詳頁變空，保留10/26核實基準不推論取消或改期）。",
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
    coverage_note="完整支援：國際處最新公告列表已發布正式簡章「2027-2028 其他國家與地區出國交換甄選簡章」（p/405-1308-384608,c20621.php，列表日期標2026/10/21、內頁未標日期；同日另有甄選時程&4場線上說明會公告384613：10/29、10/31 20:00–21:30及11/4、11/5 12:00–13:30）：系統申請 2026/11/03 09:00 至 11/17 17:00，審核及補正至 11/20 17:00，甄選結果預計 2027 年 1 月第 2 週公告；名額載明「以國際處最新簡章公告為準」，交換校資訊和志願表 10/29 公布（待 10/29 公布後核對，以各校官方公告為準）；附件為依 115/10/07 修正之甄選要點（438775412.pdf）與有利審查資料表、研修計畫書等空白表格，連同赴日本、大陸簡章、218所合作校Fact Sheet、西灣領航獎助及1,823篇歷屆交換心得已完整整合。",
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
    official_url="https://www.oia.nchu.edu.tw/index.php/zh/5-global-mobility-tw/5-1-exchange-student-program-tw/5-1-1-application-guildeline-tw",
    coverage_note="完整支援：116學年度第1學期（Fall 2027秋季班）出國交換甄選簡章（第一步學生線上申請 2026/09/23–10/23 12:00 已截止；第二步指導教授／導師線上推薦信 10/30 12:00 截止、退補件 11/06 23:59 截止）、226所海外及大陸交換合作校名額與Fact Sheet、希望之橋暨學海系列獎學金、548篇學長姐交換心得影音及422人次錄取榜單已完整整合。",
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
    coverage_note="已收錄206筆合作方案及10/29出國交換說明會（p/406-1032-157886,r2255.php）；母校指定條文部分查核，116正式簡章、逐校現行名額、收件期限、資格、生活與來源仍待核對。",
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
    coverage_note="完整支援：115-1／115-2 校級赴國外（八大語組，10/31口試公告post/118、11/2 16:00語檢上傳截止；動態公告目錄保留10/25之39筆成功基準）及赴大陸地區交換學生甄選簡章、266所合作姊妹校名額與語言門檻、6項赴外交換暨學海系列獎助學金及589篇歷屆學長姐交換心得報告已完整整合。",
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
    official_url="https://oia.ncku.edu.tw/p/404-1032-229870.php?Lang=zh-tw",
    coverage_note="已核對 116-1 簡章（107138261.pdf，2026/10/30–11/19 16:00 線上申請）與當期校級一覽表（97 筆當期開放、92 筆舊資料待重查）；赴外交換生專區已改版為 404-1032-229870.php，116-1 甄選公告（406-1032-306703,r3333.php，2026/10/16 更新）另載 2026/10/23 說明暨分享會（芬蘭圖爾庫大學、奧地利因斯布魯克大學、日本東北大學返國學長姐分享）。",
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
    coverage_note="已核對國際處出國交換申請公告列表（module=nycu0006&id=286）：2026/10/07 公告「116年度第一梯次臺灣聯合大學系統（UST）交換學生計畫」校內收件至 2026/12/31（週四）16:00 截止（PDF 寄至 ex-out@nycu.edu.tw）；2026/10/13 轉知政大辦理「2027 臺灣與阿拉伯聯合大公國（阿聯）青年交流計畫」遴選（全額補助機票及食宿）；116 學年度校級出國交換簡章尚未公布（最新校級為 115-2，已於 2026/07/10 截止）。243 筆合作資料中 182 筆對上 115-2 已截止名額表、4 筆對上 116 台聯大第一梯次方案。",
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
    coverage_note="完整支援：2027秋／2028春校級海外及赴陸港澳出國交換暨116-1台灣聯合大學系統交換計畫簡章、176所合作姊妹校（含A/B/C/D第一志願熱門程度分級、動態表142條目puid/11521及九州大學、大阪工業大學詳頁基準，不同名額單位分列不混加）名額與門檻、5項出國交換暨學海系列獎助學金及328篇歷屆學長姐返國成果報告書已完整整合。",
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
    official_url="https://mccd.pccu.edu.tw/p/406-1300-148804,r2247.php?Lang=zh-tw",
    coverage_note="已部分核對各甄選管道、國合組47筆參考名額與大陸文教處2027春季班赴大陸交換生甄選第二階段公告（https://mccd.pccu.edu.tw/p/406-1300-148804,r2247.php?Lang=zh-tw 、列表頁 https://mccd.pccu.edu.tw/p/16-1300-147944.php?Lang=zh-tw ，報名至2026/11/03 17:00，正文115-2／PDF 115-1矛盾保留待確認；國合部RPage入口 https://oima.pccu.edu.tw/p/412-1008-14612.php?Lang=zh-tw ，舊版靜態入口 oima.pccu.edu.tw/exchanges.htm 與 en/study-abroad-detail5.htm 不含當期收件表單或讀取失敗）；135筆合作方案的個別接待校條件及生活資料仍待核實。",
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
    coverage_note="已核對115-2一招與2026/10/05 10:07公告之二招簡章（一般組 d020 article/530752、c015 article/530796；語言學習組 d020 article/530751、c015 article/530797，報名延後至 2026/10/13 23:59 截止）及《二招-115-2交換學生招收名額一覽表（一般組）》（持續更新，含匈牙利布達佩斯城市大學與韓國啟明大學資訊更新），並收錄首頁 2026/10/14 發布「(二招)115-2 校級交換生報名成功名單」（article/530925，內容為報名成功名單／初步資格審核，非錄取結果，最後由接待校決定是否錄取）、2026/10/05 國合處公告「115年度第2次教育部學海飛颺獎助學金開放系級交換生申請」（article/530756，2026/11/16 截止）與 10/20 轉知政大 2027 臺阿聯青年交流計畫（article/531074）；首頁尚無 116-1 一招公告。128筆對上官方名單校名，個別名額、學費與語檢仍待逐校核實；147筆舊衍生卡片停用。",
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
    coverage_note="已核對赴外交換生專頁（unit-4-374-21.html）116學年度校級出國交換甄選時程（2026/11/09 12:00–12/01 16:00 線上申請、12/27 16:00 補繳正式語檢、2027/02/01–02/12 甄選審查、02/22 16:00 公告結果、02/26 16:00 意願確認；2026/10/28 建工校區出國研修說明會）及115校級簡章：97筆僅對應115校級或2023院系表校名與參考欄位（116交換校資料陸續更新中）；學海飛颺名額視當年度補助經費而定（無固定名額）。",
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
    official_url="https://oicaweb.ncue.edu.tw/p/412-1019-1171.php?Lang=zh-tw",
    coverage_note="完整支援：國際暨兩岸事務處（有效RPage站台代碼1019：出國交換總覽 p/412-1019-1171.php、非大陸交換 p/412-1019-1220.php、大陸港澳交換 p/412-1019-1219.php）116學年度（2027秋季、2028春季）赴國外非大陸姊妹校交換研修暨教育部學海飛颺／惜珠甄選簡章、2027年春季班（115-2學期）及 115-1 赴大陸及港澳地區姊妹校交換計畫、跨國雙聯學制與全球共 108 所合作姊妹校（23 個國家與地區）名額與語檢門檻、教育部學海系列獎補助暨 409 篇學長姐返國交換心得已完整整合。",
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
    coverage_note="已整合國際事務處首頁（https://oia.nknu.edu.tw/）與赴外交換專頁（exchange-programs.php）：（1）首頁 2026-10-01 公告「大陸地區（含港澳地區）姊妹校2027年春季班交換申請資訊（1001更新）」（news-detail.php?id=460，校內收件至 2026/10/16 已截止），首頁／公告標題列出北京師範大學、香港教育大學、澳門城市大學、西南大學、華中師範大學、華東師範大學、南京師範大學、東北師範大學等 8 校，惟內文編號 1–8 及附件第 7 項實列「南京大學（2 名，10/13 截止）」而非「南京師範大學」（平台同步標註標題與內文校名差異）；（2）exchange-programs.php 目前僅放 115 年說明會簡報與手冊（檔名日期 20251027／20251029，簡報載 115 年 11/11–12/31 線上申請，甄選作業流程 PDF 另載每年 12/15 前，頁面本身未直接寫出每年 11/11–12/31 或姊妹校數量），尚未放上 116 年說明會資料（2026-10-21 已公告 116 年學海計畫說明會 news-detail.php?id=496：11/18 和平校區活動中心二樓演講廳、11/20 燕巢校區寰宇大樓二樓會議室，報名 https://reurl.cc/DYQVXQ）；（3）143 所合作姊妹校名冊彙整自《姊妹校一覽》（sister-schools.php，五大洲／地區分頁共 161 筆條目去重後 143 校，含 115 手冊表列 23 所海外交換校與陸港澳／雙聯共 36 所重點校及 107 所締約校）。",
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
    coverage_note="已依臺北醫學大學國際事務處《在學期間出國交流指南》（tmu-student-outbound-exchange）及《盟校一覽》（partners-list）核實：指南頁表列教育部學海飛颺／惜珠與學海築夢／新南向學海築夢校內收件期限均為每年 1 月 15 日（115 年度專題簡報與二次徵求 PDF 另載第一梯次 1/16、第二梯次 9/7，均已截止）、校內《境外研修暨見實習獎勵辦法》收件期限為每年 1 月 15 日及 5 月 15 日（最新獎學金訊息停留在 2026-08-25 AIT 留學美國教育展）；指南頁內對學海飛颺／惜珠出國期程存在「總表列三個月以上、同頁 FAQ 寫一個月以上（學海築夢反之）」之文字不一致；雙聯學位依指南頁 FAQ 為「超過 30 個」（雙聯專頁細目共 33 項）；201 所國際盟校名冊係彙整自《盟校一覽》（partners-list）專頁。",
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
    coverage_note="完整支援：國際事務處 116 學年度（2027–2028）赴美國聖馬丁大學（每學期 3 名免學費）、美國密西根州奧克蘭大學（每年 15 名 ASAP 交換暨生物學 4+1/4+2 學碩連讀）、日本德島文理大學（每學期 2 名免學費＋PP 升學研究所計畫 1 名免學費）甄選（2026/10/22 17:00 收件截止，2026/11/02–11/06 面試）、2026/10/26 首頁公告「2026 海外交換生研修心得分享座談會」（10 月共 6 場，開放報名中）、「教育部學海計畫說明會」與「116 年 Young 飛全球行動計畫培訓營」（首頁未標發布日期、截止日或名額）、教育部 116 年度學海飛颺／惜珠獎學金（2027/01/06 截止，每人補助 5萬–30萬元）、2027春季美國路易斯安那州立大學醫學中心（LSUHSC）研究獎學金（每月 USD 2,500）、跨國雙聯學位與全球共 124 所合作姊妹校及教學醫院語檢門檻、書審配分（40%/35%/20%/5%）暨 31 篇歷屆海外研修心得報告已完整整合。",
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
    official_url="https://cmucia.cmu.edu.tw/s_exchange.html",
    coverage_note="已整合國際事務處首頁（https://cmucia.cmu.edu.tw/）、「交換學生」專頁（https://cmucia.cmu.edu.tw/s_exchange.html）、表格下載《2023日本交換學生說明會簡報》（https://cmucia.cmu.edu.tw/doc/202212281100421.pdf，載於 download.php?Page=3 本國學生分類）與中醫大法規資料庫：（1）國際事務處首頁與最新消息第 1 頁（10 則，最近一則為 2026-10-16）均為僑外生、華語測驗等轉知，尚無 115–116 學年度出國交換、雙聯或學海計畫最新甄選公告；（2）「交換學生」頁（s_exchange.html）為舊版靜態頁，僅列北見工業大學（每年最多 3 名）與香港教育大學（每年最多 4 名），期限一年，參與人數統計至 2011–2018 年（共 21 名），並連結《中國醫藥大學補助交換學生出國實施辦法》（statute_detail.php?sn=622）與申請表（doc/exchange/exchange_attach.odt），該頁本身未提北海道大學、補助金額、資格或當期截止日；（3）平台所列「日本北海道大學每年 5 名（大學部修滿 2 學年、IELTS 6.5 或 TOEFL iBT 79）」實際出自國際處表格下載之《2023日本交換學生說明會簡報》（doc/202212281100421.pdf），而來回經濟艙機票＋每月 NT$5,000 生活費補助（全校每年至多 12 名、每學院至多 2 名）、大學部每學期至少修 2 門課且滿 4 學分及返國 2 週內繳交心得報告等規定則出自法規《補助交換學生出國實施辦法》（sn=622，115.04.09 修正）；（4）跨國雙聯學位（母法 sn=616，含 USC、杜蘭、喬治亞州立、南卡羅萊納、格里菲斯、紐卡索、南達科塔州立等雙聯獎助細則）及物治系 115-1 海外臨床實習（cmupt.cmu.edu.tw/news/753，10/12 17:00 報名截止、2027/01/10–01/30 實習）等 174 所合作機構資料均附實際法規與院系來源連結。",
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
    coverage_note="完整支援：國際事務處首頁（ciae2.kmu.edu.tw，2026/10/28 巡檢）收錄「116 年教育部學海計畫說明會」（未標日期；內頁南區場 11/13 於高醫大第一教學大樓 B1）、「2027 日本台灣交流協會獎學金（短期生）」（截止 2026/11/05）、「教育部補助學生赴海外參加國際學術及技能競賽（2026 下學期）」（校內截止 2026/11/10）、「校內徵件：教育部青年百億海外圓夢基金（116 年第 2 梯次）」、「歐盟聯合碩士學位（EMJM）獎學金說明會」、教育部「2027 人文及社會科學領域海外研修人才培育計畫」申請公告（標題未寫日期）、「2027 臺灣與阿拉伯聯合大公國青年交流計畫」（11/02 截止）、TaiwanGPS 海外經驗分享與留學推廣線上說明會（10/14、10/22）、2026 青年百億海外圓夢基金成果展（10/30–11/01 高雄展覽館 N1）、AIT 留學美國教育展轉知與「教育部海外留學獎學金及相關資源」資訊分享（另有 TEEP 構想徵求截止 2026/10/30，屬外籍生來臺計畫而非出國交換），並整合醫學院網站（cmed.kmu.edu.tw）公告之 2027 海外臨床見實習（21 校 64+ 名）、校級赴日本順天堂大學長期交換生計畫、10 校跨國雙聯學位、各學院海外見實習、115 年度博士生千里馬出國研究計畫與全球共 188 所合作姊妹校及教學醫院語檢門檻暨 56 篇歷屆師生海外研修心得報告。",
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
    official_url="https://iee.mcu.edu.tw/",
    coverage_note="完整支援：國際教育交流處首頁（https://iee.mcu.edu.tw/）近期公告「海外留學說明會」（2026-10-20 發布，分類：出國交換與留學）、「2027 臺灣與阿拉伯聯合大公國青年交流計畫」（2026-10-14）與「2026 韓國首爾嘉泉大學冬季韓語營」（2026-10-05），並整合 116 學年度（2027秋季／2028春季）海外交換學生計畫（65 所開放姊妹校，依 2027–2028 姊妹校名冊 PDF 載明秋季班 2027/03/03、春季班 2027/09/20 截止）、10 校 14 個跨國雙學位項目、2027 春季班赴大陸頂尖大學交換計畫（42 所高校，第三次公告已於 2026/10/23 12:00 截止、預計 10/27 放榜）、教育部 116 學海飛颺／惜珠獎學金與全球共 202 所合作姊妹校語檢門檻、保證金 NT$5,000 與家長同意書公證規定暨 126 篇歷屆學長姐返國研修心得報告。",
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
    official_url="https://oia.ntub.edu.tw/p/405-1006-57507,c3152.php?Lang=zh-tw",
    coverage_note="已整合國立臺北商業大學國際事務處「出國交換學生」、「雙聯學位」、「交換學生獎補助金申請辦法」與「法規專區」官方資料：（1）甄選梯次與說明會：〈姊妹校交換作業辦法〉頁（p/405-1006-57507,c3152.php，115.10.12 更新懶人包）載明每年分兩梯次收件——11 月梯次（11/1–11/30 收件，遇例假日順延一天，於申請之隔年度出國交換一學期或一學年，實際交換期間依接待學校之學期起迄時間為主；官網未寫「8–9 月或 2 月出發」）、5 月梯次（5/1–5/31 收件，開放 11 月梯次剩餘名額，二技及研究所學生優先，於申請之隔年度第 2 學期出國交換一學期）；「116 學年度交換生申請說明會」已於 115/10/12（一）12:10–13:20 舉辦（臺北校區圖書館 B1 國際行銷講堂、桃園校區 Google Meet 同步，線上表單報名，p/406-1006-120272,r1.php）。（2）申請資格與甄選配分：申請人須為研究所、二技一年級第二學期以上、四技二年級以上或五專四年級以上之學生，且符合下列其中一項——①在校學業總平均 80 分以上，且前一學年每學期操性（操行）成績都在 A 以上；②歷年班級名次在前 70%，且前一學年每學期操性（操行）成績都在 A 以上；外語成績須在 2 年內有效且只接受托福（TOEFL iBT）或雅思（IELTS）；〈交換生甄選作業辦法〉頁（p/406-1006-77262,r134.php）僅放一份 PDF（檔名含 1081114），頁面本身無配分條文，而「海外組：外語成績 60%＋歷年學業平均 20%＋歷年班級名次百分比 20%；大陸組：學業平均 50%＋班級名次百分比 50%」配分比例係出自《學生申請交換生及雙聯學位生作業要點》（p/406-1006-91803,r134.php 附件 PDF 第七點）與 115.10.12 交換懶人包簡報（337014036.pptx）。（3）姊妹校與雙聯學位：〈姐妹校名單及交換名額〉頁（p/405-1006-57515,c3152.php）共 49 列（美國峽谷學院列 2 次：一般課程、銜接課程，實際 48 所當期交換校、分布 20 國，並註明「交換生甄選名額於每年 11 月重新計算」），連同〈雙聯學位〉5 校及〈海外合作學校名錄〉（p/405-1006-57536,c3159.php）其餘 42 所正式締約姊妹校，全庫共 93 所合作校。（4）獎助學金與最新消息：〈交換學生獎補助金申請辦法〉頁（p/405-1006-57516,c3152.php）列學海飛颺（110.08.26，238565761.pdf）與學海惜珠（115.07.23，562348656.pdf）兩份審查要點（頁面未直接印出金額），《王春滿清寒短期研修交流助學金》（115.05.26 修正，每人補助 NT$ 25,000）出自〈法規專區〉（937380972.pdf）；最新消息尚無 11 月梯次甄選公告，新公告有「10/20 舊金山州立大學 3+1+1 學碩士雙聯學制說明會」（120031）及兩則冬季交流活動轉知（全北大學冬令營 120605、卡加利大學 120600，皆非交換甄選公告）。",
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

NCNU = UniversityProfile(
    id="ncnu",
    school_name="國立暨南國際大學",
    short_name="暨大",
    english_name="National Chi Nan University",
    aliases=(
        "ncnu",
        "國立暨南國際大學",
        "國立暨南大學",
        "暨南國際大學",
        "暨南大學",
        "暨南",
        "暨大",
        "NCNU",
        "National Chi Nan University",
    ),
    hero_image="/static/assets/ncnu-campus.svg",
    official_url="https://oia.ncnu.edu.tw/p/412-1017-269.php?Lang=zh-tw",
    coverage_note="完整支援：已整合國立暨南國際大學國際及兩岸事務處「海外姊妹校交換生申請流程」、「姊妹校交換生申請截止日期」、「赴大陸及港澳地區交換生」、「跨國雙聯學位」、「出國獎學金（教育部學海計畫、校內補助）」與「法規及表單下載」官方資料：（1）甄選梯次與積分制度：海外交換分秋季班（每年 2–3 月校內收件提名）與春季班（每年 9–10 月校內收件提名），大陸港澳交換分春季班（9–11 月）與秋季班（2–4 月，香港教育大學僅 4 月開放）；校內甄選依《選送學生出國研修積分計算要點》（112.06.14 修正通過，滿分 30 分）採計主要語言 10 分（B2 為 8 分、B1 為 5 分、A2 為 2 分）、次要語言 3 分、學業成績 10 分（10 × [100% − 班排%]）、院推薦排序加分 1–4 分與國際學伴／社團 3 分。（2）合作姊妹校與雙聯學位：完整收錄《姊妹校交換生資訊》總表 142 所海外開放交換校、20 所大陸港澳交換姊妹校、4 所跨國雙聯學位合作校（美國加州大學河濱分校 UCR 3+1+MS、法國雷恩商學院、加拿大紐芬蘭紀念大學、泰國農業大學）及全球締約姊妹校地圖 KML 50 所參考校，全庫共 212 所合作姊妹校（橫跨 38 國／地區）。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺》／《學海惜珠》、校內《選送優秀學生出國補助要點》（114.07.22 修正，歐美最高 10 萬、亞太最高 7 萬）、雙聯學位 10 萬元完業獎勵金、《國外學分換算表》（2 ECTS = 1 學分、4 CATS = 1 學分）及 29 所合作大學共 100 篇歷屆學長姐交換心得報告。",
    support_level="full",
    partner_count_hint=212,
    academic_score_minimum=70,
    student_card_signals=(
        "國立暨南國際大學",
        "暨南國際大學",
        "暨大",
        "NATIONALCHINANUNIVERSITY",
        "NCNU",
    ),
    # https://www.ncnu.edu.tw/p/412-1000-1228.php?Lang=zh-tw — checked 2026-10-27.
    colleges=(
        "人文學院",
        "管理學院",
        "科技學院",
        "教育學院",
        "水沙連學院",
        "護理暨健康福祉學院",
    ),
)

NDHU = UniversityProfile(
    id="ndhu",
    school_name="國立東華大學",
    short_name="東華",
    english_name="National Dong Hwa University",
    aliases=(
        "ndhu",
        "國立東華大學",
        "東華大學",
        "東華",
        "NDHU",
        "National Dong Hwa University",
    ),
    hero_image="/static/assets/ndhu-campus.svg",
    official_url="https://oia.ndhu.edu.tw/p/412-1027-21499.php?Lang=zh-tw",
    coverage_note="完整支援：已整合國立東華大學國際事務處「出國交換計畫（甄選簡章及說明會、出國交換補助、申請系統及交換學校一覽表、校內甄選後程序、交換出返國程序、交換心得&影片、Q&A）」、「雙聯學位（校級、院系級、新南向專班）」與「規章辦法」官方資料：（1）甄選時程與審查配分：每年分兩次辦理校內甄選——第一次甄選於秋季學期初辦理（2027年第一次甄選線上申請為 2026/08/17 17:00 至 2026/10/05 17:00，申請 115-2 春季班及 116-1 秋季班出國交換；因出國交換申請系統 ias.ndhu.edu.tw 進行 PHP 資安漏洞修補維護，校內推薦結果公告由 2026/10/27 12:00 順延至 2026/10/30 12:00）、第二次甄選於春季學期初辦理（申請同年秋季班剩餘名額）；申請人須於出國就讀時為二年級（含）以上在學學位生且前一學期或歷年 GPA 達 2.5（滿分 4.5）以上，最少選填 2 個、最多 6 個志願，以首次申請出國交換者優先分發；校內書面審查總成績＝學業表現 20%＋任務企劃書 35%＋讀書計畫 35%＋資料加分 10%，另具國際處接待義工證明加 1 分、修畢全球研究與國際事務學程加 1 分。（2）合作姊妹校、先鋒計畫與雙聯學位：完整收錄 163 所全球與大陸合作姊妹校（橫跨 22 國，含 10 校「國際移動力先鋒計畫」免學費暨高額獎學金重點校、19 校校院級雙聯學位合作校及 41 所大陸交換姊妹校）。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺》／《學海惜珠》、校內《國際交換學生出國計畫作業辦法》出國交換獎助學金（依當年度經費提供 1萬–15萬元不等，申請資格為歷年 GPA 達 3.3 以上且具外語檢定證明）、《學生出國選修課程實施辦法》（歐洲 ECTS × 1/2、英國 CATS × 1/4、美日陸 1:1 折算）及 92 所合作大學共 496 篇歷屆學長姐交換與海外研修心得報告。",
    support_level="full",
    partner_count_hint=163,
    academic_score_minimum=70,
    student_card_signals=(
        "國立東華大學",
        "東華大學",
        "NATIONALDONGHWAUNIVERSITY",
        "NDHU",
    ),
    # https://www.ndhu.edu.tw/p/412-1000-10164.php?Lang=zh-tw — checked 2026-10-28.
    colleges=(
        "人文社會科學學院",
        "理工學院",
        "管理學院",
        "花師教育學院",
        "藝術學院",
        "原住民民族學院",
        "環境暨海洋學院",
        "洄瀾學院",
    ),
)

THU = UniversityProfile(
    id="thu",
    school_name="東海大學",
    short_name="東海",
    english_name="Tunghai University",
    aliases=(
        "thu",
        "東海大學",
        "東海",
        "THU",
        "Tunghai University",
        "Tunghai",
    ),
    hero_image="/static/assets/thu-campus.svg",
    official_url="https://oir.thu.edu.tw/front/301_ex_overview/302_Out_EX_Prog/302_1_Qualifica?lang=tw",
    coverage_note="完整支援：已整合東海大學國際暨兩岸合作處（OIR）《2027年春學期／2026年秋學期赴全球姊妹校交換甄試簡章》、《交換甄選辦法重大更新通知（2025.11.18）》、《國際暨兩岸姊妹校名錄》、《國際合作協議資料庫》與《赴海外雙聯學位》官方資料：（1）甄試時程、分組與取消口試量化計分新制：每年春、秋兩學期初辦理校內長期交換甄試（春季班於每年 9–10 月辦理，如 2027 春學期甄試為 2026/09/07–10/05 報名、10/15 唱名選填學校、10/15–10/23 繳交推薦資格確認書與 10,000 元保證金；秋季班於每年 2–3 月辦理，如 2026 秋學期甄試為 2026/02/23–03/13 報名、03/27 唱名選校）。申請人須為修業滿一學期之在學學生（不含碩士在職專班），報名時分「全球暨港澳組（歷年 GPA 2.5 以上）」及「大陸組（歷年 GPA 2.0 以上）」兩組計分，自 2026 秋學期甄試起取消口試項目，總成績＝歷年學期班排名百分比平均 20%＋外語能力 30%（依 Level A 30% 至 Level G 4% 計分表擇最優採計，大陸組不計分）＋歷年學期 GPA 平均 15%＋學行優良表現 35%（含國際交流活動、國際接待志工、修習 EMI 課程占比達 30%/40%/50%、培力英檢 BESTEP 成績證明），完成基本勞作教育達畢業門檻者另加總分 5 分；依總分高低現場唱名當場決定選填學校。（2）合作姊妹校與雙聯學位：完整收錄 274 所全球與兩岸合作姊妹校（橫跨 31 國與地區，含 130 所當期開放申請之全球／大陸交換姊妹校與雙聯合作校、13 所美國名校跨國雙聯學位［天普、羅德島、北帕克、SUNY ESF、安得烈、艾克朗、UT Dallas、羅格斯、UIUC、南佛羅里達、密西根弗林特、聖湯瑪士、聖荷西州立］及 ACUCA／UMAP／Erasmus+ 交換專案）。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺》（2026/10/12–11/16）、《學海惜珠》（每年 3/10、9/15）、《高等教育深耕計畫國際移動力活動獎補助（國際移動躍升計畫）》（每年 3月、9月兩梯次）、《學生參加英語檢定考試補助辦法》（最高補助 NT$ 15,000）及 31 所合作大學共 80 篇歷屆學長姐交換與雙聯心得報告。",
    support_level="full",
    partner_count_hint=274,
    academic_score_minimum=70,
    student_card_signals=(
        "東海大學",
        "TUNGHAIUNIVERSITY",
        "TUNGHAI",
        "THU",
    ),
    # https://www.thu.edu.tw/web/pages/page.php?sc=2&idm=2 — checked 2026-10-28.
    colleges=(
        "文學院",
        "理學院",
        "工學院",
        "管理學院",
        "社會科學院",
        "農業暨健康學院",
        "創意設計暨藝術學院",
        "法律學院",
        "國際學院",
    ),
)

SHU = UniversityProfile(
    id="shu",
    school_name="世新大學",
    short_name="世新",
    english_name="Shih Hsin University",
    aliases=("shu", "世新大學", "世新", "SHU", "Shih Hsin University", "Shih Hsin"),
    hero_image="/static/assets/shu-campus.svg",
    official_url="https://global.web.shu.edu.tw/%e5%ad%b8%e7%94%9f%e4%ba%a4%e6%b5%81-%e8%b5%b4%e5%a4%96%e7%a0%94%e4%bf%ae/",
    coverage_note="完整支援：已整合世新大學國際暨兩岸事務處（Global Affairs Office）與兩岸事務處（OCSE）《2027春季班／2026秋季班赴外及赴陸交換甄選簡章》、《2027春季班外國姊妹校交換申請手冊》、《世新大學選送學生出國研修甄選辦法》、《學生出國選修課程實施辦法》與《雙聯學制專區》官方資料：（1）甄選時程與雙軌窗口：國際處每年辦理兩梯次赴國外（非大陸地區）交換甄選（春季班於前一年 9–10 月報名、秋季班於當年 2–3 月報名），兩岸事務處同步辦理赴大陸及港澳地區交換生甄選；申請人須為本校在學滿一學期以上之學士班及碩博士班學生，赴國外交換一般須歷年平均 75 分（GPA 3.0）或班排前 50%、赴大陸交換一般須歷年平均 70 分以上且操行 80 分以上。（2）合作姊妹校與雙聯學位：完整收錄 177 所全球與兩岸合作姊妹校（橫跨 29 國與地區，含 58 所當期開放申請之國外及大陸交換／雙聯合作校、英國蘇塞克斯大學／西英格蘭大學及美國威斯康辛大學河瀑分校等跨國雙聯學位）。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺》、《學海惜珠》、校內《選送學生出國研修獎助學金》及 49 所合作大學共 244 篇歷屆學長姐交換與雙聯心得報告。",
    support_level="full",
    partner_count_hint=177,
    academic_score_minimum=75,
    student_card_signals=(
        "世新大學",
        "SHIHHSINUNIVERSITY",
        "SHIHHSIN",
        "SHU",
    ),
    # https://www.shu.edu.tw/SHU-All-Units.aspx — checked 2026-10-30.
    colleges=(
        "新聞傳播學院",
        "管理學院",
        "人文社會學院",
        "法律學院",
    ),
)

PU = UniversityProfile(
    id="pu",
    school_name="靜宜大學",
    short_name="靜宜",
    english_name="Providence University",
    aliases=("pu", "靜宜大學", "靜宜", "PU", "Providence University", "Providence"),
    hero_image="/static/assets/pu-campus.svg",
    official_url="https://411.pu.edu.tw/p/426-1073-4.php?Lang=zh-tw",
    coverage_note="完整支援：已整合靜宜大學國際暨兩岸事務處（OIA）與 411 遊留學中心（出國研修組）《各洲別交換學校一覽表（15 個地區專頁）》、《跨國雙聯學制專區（16 校）》、《ISEP 國際交換學生計畫》、《五大洲締約姊妹校名錄 Excel》、《學生出國研修辦法》、《遴選交換學生作業要點》與《出國交換學生學分換算準則》官方資料：（1）三梯次校內初審、免繳雜費與強制抵免規定：每學期分三梯次辦理出國研修校內初審（春季班出國於前一年 8月／9月／10月辦理，如 115-2 為 2026/08/03–08/23、08/24–09/20、09/21–10/11，初審通過者於 10/30 前繳交《境外研修同意書》；秋季班出國於當年 2月底／3月底／4月底辦理；雙聯學制秋季班 3/31 截止；ISEP 秋季班 1 月中、春季班 7 月底截止）。大一新生可於大一下申請、大二上出國（延畢生亦得申請互惠交換），在學期間出國交換須繳交靜宜全額學費、免繳雜費；返國後次學期開學 2 個月內強制規定「至少須抵免一科（至少 1 學分）」（換算準則：美日陸 1:1、歐洲 ECTS÷2、英國 CATS÷4）。（2）合作姊妹校、ISEP 與 16 校雙聯學位：完整收錄 275 所全球與大陸合作姊妹校（橫跨 5 大洲 48 個國家與地區，含 230 所當期開放申請之交換與雙聯合作校、ISEP 全球逾 300 校互惠食宿交換，以及美、英、德、法、日、澳 16 所跨國雙聯學位合作校）。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺》、《學海惜珠》、校內《E.A.G.L.E. 築夢基金》（亞洲上限 2 萬／非亞上限 3 萬）、《學生出國研修獎助學金辦法》及 118 所合作大學共 299 篇歷屆學長姐交換與研修心得報告 PDF。",
    support_level="full",
    partner_count_hint=275,
    academic_score_minimum=70,
    student_card_signals=(
        "靜宜大學",
        "PROVIDENCEUNIVERSITY",
        "PROVIDENCE",
        "PU",
    ),
    # https://www.pu.edu.tw/p/412-1000-1047.php?Lang=zh-tw — checked 2026-10-30.
    colleges=(
        "外語暨人文創意學院",
        "社會科學院",
        "理學院",
        "管理學院",
        "資訊學院",
        "國際學院",
    ),
)

USC = UniversityProfile(
    id="usc",
    school_name="實踐大學",
    short_name="實踐",
    english_name="Shih Chien University",
    aliases=("usc", "實踐大學", "實踐", "USC", "Shih Chien University", "Shih Chien"),
    hero_image="/static/assets/usc-campus.svg",
    official_url="https://uscoia.usc.edu.tw/p/412-1049-1331.php?Lang=zh-tw",
    coverage_note="完整支援：已整合實踐大學國際暨兩岸事務處（OIA）《115學年度第2學期出國交換、雙聯學制暨海外自費研修簡章（含中國大陸地區交換）》、《交換及海外自費研修學校一覽表（125 校）》、《雙聯學制學校一覽表（20 校 28 學程）》、《實踐大學出國交換學生報名系統（oia-exchange.vercel.app）》、《辦理學生赴境外大學研修要點》、《與境外大學辦理雙聯學制實施辦法》與《出國留學獎學金辦法》官方資料：（1）兩階段校內甄選、在學學費與最低修習學分規定：每學期分兩階段於線上報名系統（oia-exchange.vercel.app）收件（春季班出國於前一年 9–10月辦理，如 115-2 第一階段 2026/09/01–10/01、第二階段 2026/10/19–10/29 17:00，陸港澳僅限第一階段；秋季班出國於當年 2–3月辦理），申請人須填寫 3 個志願並完成系主任與院長（或國際學程主任）核章。大一、大二及大三上可申請學士班交換（大四申請須簽署延畢切結書），歷年學業總平均須達 75 分以上或班排名前 50%、歷年操行平均 80 分以上；出國期間須辦理實踐大學註冊並繳交全額學雜費，每學期至少修習相當於實踐 6 學分（研究所至少 1 科 3 學分）且至少 1 門須為所屬學系專業課程（學分換算：美日韓陸 1:1、歐洲 ECTS×0.5、英國 CATS×0.25）。（2）合作姊妹校與 20 校 28 項雙聯學制：完整收錄 125 所全球與大陸合作姊妹校（橫跨 27 個國家與地區，含 101 所海外交換／雙聯／自費研修校與 24 所大陸地區交換姊妹校，以及英、美、加、澳、法、德、奧、瑞士、日、韓、馬、泰 20 所跨國雙聯學位合作大學共 28 個 3+1／2+2／1+1 雙聯學程）。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺》、《學海惜珠》、校內《出國留學獎學金》（生活費補助、最高可加碼全額學雜費減免）及 74 所合作大學共 288 篇歷屆學長姐出國交換與雙聯研修心得報告 PDF。",
    support_level="full",
    partner_count_hint=125,
    academic_score_minimum=75,
    student_card_signals=(
        "實踐大學",
        "SHIHCHIENUNIVERSITY",
        "SHIH CHIEN UNIVERSITY",
        "USC",
    ),
    # https://www.usc.edu.tw/ — checked 2026-10-30 (臺北校區：民生學院、設計學院、管理學院、國際學程；高雄校區：商學與資訊學院、文化與創意學院).
    colleges=(
        "民生學院",
        "設計學院",
        "管理學院",
        "法學院",
        "國際學程",
        "商學與資訊學院",
        "文化與創意學院",
    ),
)

NUK = UniversityProfile(
    id="nuk",
    school_name="國立高雄大學",
    short_name="高大",
    english_name="National University of Kaohsiung",
    aliases=(
        "nuk",
        "國立高雄大學",
        "高雄大學",
        "高大",
        "NUK",
        "National University of Kaohsiung",
    ),
    hero_image="/static/assets/nuk-campus.svg",
    official_url="https://dia.nuk.edu.tw/p/412-1034-4130.php?Lang=zh-tw",
    coverage_note="完整支援：已整合國立高雄大學國際事務處（DIA）《2027春季與2026秋季出國交換說明會簡報》、《出國交換名額表與申請條件一覽表》、《交換學生甄選作業要點》、《選送優秀學生出國研修之語文能力證明標準》、《33國國際姊妹校統計與名錄》、《跨國雙聯學制（8校）》與《教育部學海飛颺／惜珠獎學金語文標準》官方資料：（1）兩梯次校內甄選、百分制評分與語檢補件規定：每年分兩次辦理出國交換校內甄選（秋季班暨教育部學海飛颺／惜珠第一次申請於前一年 12 月底至 1 月初收件、2 月中旬語檢補件、3 月底前公布薦送名單；春季班於前一年 6 月底至 7 月初收件，如 115-2 為 2026/06/25–07/07、08/11–08/18 語檢補件、9 月底前公布薦送名單）。限非當學期畢業且申請／出國就讀時為大二（含）以上之高大日間學制學士班、碩士班、博士班在學學生（轉學生須於高大有 2 學期以上成績）。校內甄選依大學部「歷年班排 65%＋自傳研修計畫與有利審查資料 35%」、研究所「歷年班排 35%＋自傳研修計畫 35%＋指導教授推薦函 30%」評分，總分達 70 分（含）以上始獲考慮薦送資格（交換期限最長一年，不得申請延長）。（2）合作姊妹校與 8 校雙聯學制：完整收錄 280 所全球與大陸合作姊妹校（橫跨 33 個國家與地區，含 169 所當期開放申請之交換與雙聯合作校，以及美國密西根大學迪爾伯恩分校、美國肯恩大學、英國丹地大學、英國羅浮堡大學、英國亞伯丁大學、印尼丹戎布拉大學、蒙古新蒙古科技大學、中國福州大學共 8 所跨國雙聯學位合作校）。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺》、《學海惜珠》、JASSO／GKS 與姊妹校住宿減免及 35 所合作大學共 58 篇歷屆學長姐返國心得報告與校內薦送紀錄。",
    support_level="full",
    partner_count_hint=280,
    academic_score_minimum=70,
    student_card_signals=(
        "國立高雄大學",
        "高雄大學",
        "NATIONALUNIVERSITYOFKAOHSIUNG",
        "NATIONAL UNIVERSITY OF KAOHSIUNG",
        "NUK",
    ),
    # https://www.nuk.edu.tw/p/412-1000-221.php?Lang=zh-tw — checked 2026-10-30.
    colleges=(
        "人文社會科學院",
        "法學院",
        "管理學院",
        "理學院",
        "工學院",
        "創新學院",
    ),
)

NCYU = UniversityProfile(
    id="ncyu",
    school_name="國立嘉義大學",
    short_name="嘉大",
    english_name="National Chiayi University",
    aliases=(
        "ncyu",
        "國立嘉義大學",
        "嘉義大學",
        "嘉大",
        "NCYU",
        "National Chiayi University",
    ),
    hero_image="/static/assets/ncyu-campus.svg",
    official_url="https://www.ncyu.edu.tw/oia/Contents?nodeId=57877",
    coverage_note="完整支援：已整合國立嘉義大學國際事務處（OIA）《114學年度交換學生計畫說明會簡報（2026秋季／2027春季）》、《國立嘉義大學薦外交換學生審查要點》、《薦外姊妹校交換學生獎補助金發放要點》、《2026海外研修手冊》、《2026薦外交換生手冊》、《英語能力檢定測驗門檻對照表》、《國外締約學校一覽表（140校）》與《雙聯學位推動現況（8校13專案）》官方資料：（1）兩梯次校內甄選、量化計分與系所務會議認證規定：每年分兩梯次辦理薦外交換校內甄選（秋季班出國於前一年 12月收件、次年 2–3月公布錄取；春季班出國於前一年 5–6月收件，如 2027春季班為 2026/05/01–06/15 收件、09–10月公布錄取）。限學士班二年級以上、碩士班一年級以上、博士班一年級以上在學學生（轉學生須於嘉大修滿一學期且具成績），在校成績須達全班前 20% 以內，或學期平均大學部 75 分（含）以上、研究生 80 分（含）以上；每人至多選填 2 志願學校，進修課程規劃須檢附系、所務會議同意之會議紀錄。審查計分：非華語地區為「班級排名百分比 40%＋語言能力 40%（A級 40%、B級 36%、C級 32%、D級 24%）＋讀書計畫 20%」，華語地區免附語檢（班排 80%＋讀書計畫 20%）。（2）合作姊妹校與 8 校 13 專案雙聯學制：完整收錄 140 所全球與大陸合作姊妹校（橫跨 25 國與地區，含 48 所當期開放申請之交換與雙聯合作校，以及美國堪薩斯州立大學、楊斯鎮州立大學、斯托克頓大學、英國亞伯丁大學、日本尾道市立大學、香川大學、泰國湄州大學、印尼布勞爪哇大學共 8 所跨國雙聯學位合作校 13 個院系專案）。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺》、《學海惜珠》、校內《薦外姊妹校交換學生獎補助金》、日本 JASSO 與韓國姊妹校學宿費減免，以及 20 所合作大學共 95 篇歷屆學長姐返國交換與海外研修心得報告。",
    support_level="full",
    partner_count_hint=140,
    academic_score_minimum=75,
    student_card_signals=(
        "國立嘉義大學",
        "嘉義大學",
        "嘉大",
        "NATIONALCHIAYIUNIVERSITY",
        "NATIONAL CHIAYI UNIVERSITY",
        "NCYU",
    ),
    # https://www.ncyu.edu.tw/ncyu/Subject?nodeId=834 — checked 2026-10-30.
    colleges=(
        "師範學院",
        "人文藝術學院",
        "管理學院",
        "農學院",
        "理工學院",
        "生命科學院",
        "獸醫學院",
    ),
)

NUTC = UniversityProfile(
    id="nutc",
    school_name="國立臺中科技大學",
    short_name="中科大",
    english_name="National Taichung University of Science and Technology",
    aliases=(
        "nutc",
        "國立臺中科技大學",
        "國立台中科技大學",
        "臺中科技大學",
        "台中科技大學",
        "中科大",
        "臺中科大",
        "台中科大",
        "NUTC",
        "National Taichung University of Science and Technology",
    ),
    hero_image="/static/assets/nutc-campus.svg",
    official_url="https://oia.nutc.edu.tw/p/412-1026-8514.php?Lang=zh-tw",
    coverage_note="完整支援：已整合國立臺中科技大學國際事務處（OIA）《六大區域合作姊妹校名冊（140校）》、《2026/2027春秋季班日本與韓國姊妹校交換留學簡章》、《學生赴大陸地區協議學校研習申請簡章》、《114/115年度教育部選送優秀學生赴國外研修／專業實習學海系列計畫校內申請作業公告》、《學生申請教育部學海系列計畫審查要點》、《教師申請學海築夢計畫及新南向學海築夢計畫審查要點》與《高教深耕計畫國際專章補助國際交流活動要點》官方資料：（1）兩梯次出國交換甄選、五專部四五年級與學碩士班資格及返國志願服務規定：每年分春季班（前一年 9–10月收件，如 2027春季班為 2026/09/14–10/30 收件）與秋季班（當年 3–5月收件）辦理出國交換留學甄選，並於每年 1–3月初辦理教育部學海飛颺／惜珠／築夢校內甄選（115年度為 01/07 說明會、01/08–03/02 學院初審、03/04 國際處收件截止）。限已就讀本校一學期以上之日間部與進修部非應屆畢業在籍學生（學士班、碩士班及五專部四年級(含)以上，不含五專 1–3 年級生、延修生及在職專班生），國外交換各科成績須達 70 分以上且操行 80 分以上（赴大陸協議學校歷年學業總平均及操行均須達 80 分以上）；交換期間於中科大註冊繳費保留學籍並享姊妹校學費互免，赴日韓交換生於留學期間須投稿國際處粉專（1學期5篇、1學年10篇），返國後須繳交心得報告並完成國際處志願服務 20 小時。（2）六大區域 140 所合作姊妹校與英國雙聯學位：完整收錄日本 20 校、韓國 5 校、東南亞與南亞 33 校、歐美 23 校、大洋洲 4 校、大陸與澳門 55 校共 140 所合作姊妹校（橫跨 19 個國家與地區，含 39 所當期開放申請之交換與雙聯合作校，以及英國西蘇格蘭大學 UWS 1 年制榮譽學士／碩士雙聯學位與瑞士 BHMS 帶薪實習專案）。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺》（每人補助 5 萬至 30 萬元）、《學海惜珠》、《學海築夢／新南向學海築夢》、高教深耕國際專章、日本 JASSO 及 8 所合作大學共 31 篇歷屆學長姐返國交換心得報告。",
    support_level="full",
    partner_count_hint=140,
    academic_score_minimum=70,
    student_card_signals=(
        "國立臺中科技大學",
        "國立台中科技大學",
        "臺中科技大學",
        "台中科技大學",
        "NATIONALTAICHUNGUNIVERSITYOFSCIENCEANDTECHNOLOGY",
        "NATIONAL TAICHUNG UNIVERSITY OF SCIENCE AND TECHNOLOGY",
        "NUTC",
    ),
    # https://www.nutc.edu.tw/p/412-1000-88.php — checked 2026-10-31.
    colleges=(
        "商學院",
        "設計學院",
        "資訊與流通學院",
        "智慧產業學院",
        "語文學院",
        "中護健康學院",
    ),
)

NFU = UniversityProfile(
    id="nfu",
    school_name="國立虎尾科技大學",
    short_name="虎科大",
    english_name="National Formosa University",
    aliases=(
        "nfu",
        "國立虎尾科技大學",
        "虎尾科技大學",
        "虎尾科大",
        "虎科大",
        "NFU",
        "National Formosa University",
    ),
    hero_image="/static/assets/nfu-campus.svg",
    official_url="https://oia.nfu.edu.tw/zh-tw/ia/out/outexchange/out-exchangeschools",
    coverage_note="完整支援：已整合國立虎尾科技大學國際事務處（OIA）《亞洲／歐洲／美洲／大洋洲海外姊妹校名冊（152校）》、《國立虎尾科技大學海外姊妹校交換學生一覽表（115.06）》、《115學年度第2學期選送優秀學生出國研修（交換學生／學海飛颺／學海惜珠）甄選簡章》、《3+1+1雙聯學制專區》、《甄選學生赴國外研修作業要點》、《學生出國研修獎助要點》與《CEF與各項英檢對照表》官方資料：（1）兩梯次校內甄選、學業及語文門檻與每學期9學分修課規定：每年分兩梯次（春季班於前一年9月收件、秋季班於當年3–4月收件，如115-2春季班於115/09/30截止收件、115/10/14面試、115/10/16放榜；115-2學海惜珠於115/07/01截止收件）辦理校內甄選，限在學非應屆畢業生（大一至大三學士生、碩一碩士生、博一至博二博士生，不含在職專班生、大陸籍學生及外籍學生，交換期間不得辦理畢業），前學年學業總平均成績須達75分以上或班排名前50%且操行成績平均達80分以上，語文能力須達CEFR B1以上（TOEIC 550 / TOEFL iBT 42 / TOEFL ITP 457 / IELTS 4.0，或日檢N1–N4、韓檢TOPIK 3級）且面試成績須達70分以上；出國交換期間於虎科大完成註冊選課保留學籍並享姊妹校學費互免，每學期至少須選修9學分（或18 ECTS）以上專業課程，返國後一個月內繳交國外修讀學分抵免申請表及研修心得報告並配合國際處宣導活動。（2）四大洲 152 所合作姊妹校與雙聯學制：完整收錄亞洲 118 校（日本 33 校、越南 28 校、印尼 14 校、韓國 10 校、泰國 9 校、馬來西亞 7 校、印度 6 校、菲律賓 6 校、以色列 2 校、香港／土耳其／蒙古各 1 校）、歐洲 20 校（德國 7 校、法國 5 校、捷克 3 校、俄羅斯 2 校、西班牙／奧地利／羅馬尼亞各 1 校）、美洲 11 校（美國 8 校、加拿大 2 校、祕魯 1 校）與大洋洲 3 校（澳洲 3 校）共 152 所姊妹校（橫跨 28 個國家與地區，含 30 所當期開放申請之交換及美國密西根大學迪爾伯恩分校 UM-Dearborn、羅德島大學 URI 3+1+1 學碩雙聯學位與 UNLV 暑期研習合作校）。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺》、《學海惜珠》、《學海築夢／新南向學海築夢》、虎科大《學生出國研修獎助要點》校內機票與生活費獎助學金，以及 12 所合作姊妹校共 13 篇歷屆學長姐返國研修心得與分享會紀錄。",
    support_level="full",
    partner_count_hint=152,
    academic_score_minimum=75,
    student_card_signals=(
        "國立虎尾科技大學",
        "虎尾科技大學",
        "虎科大",
        "NATIONALFORMOSAUNIVERSITY",
        "NATIONAL FORMOSA UNIVERSITY",
        "NFU",
    ),
    # https://www.nfu.edu.tw/zh/academic — checked 2026-10-31.
    colleges=(
        "工程學院",
        "電機資訊學院",
        "管理學院",
        "文理學院",
        "航空學院",
    ),
)

UTAIPEI = UniversityProfile(
    id="utaipei",
    school_name="臺北市立大學",
    short_name="北市大",
    english_name="University of Taipei",
    aliases=(
        "utaipei",
        "ut",
        "臺北市立大學",
        "台北市立大學",
        "北市大",
        "UTaipei",
        "UT",
        "University of Taipei",
    ),
    hero_image="/static/assets/utaipei-campus.svg",
    official_url="https://international.utaipei.edu.tw/p/412-1006-6691.php?Lang=zh-tw",
    coverage_note="完整支援：已整合臺北市立大學國際事務處（OIA）全球教育交流組《海外姊妹校一覽表（226校）》、《116學年度第1學期赴外姊妹校交換學生甄選簡章（86校）》、《115學年度第2學期赴外姊妹校交換學生甄選簡章（84校）》、《境外雙聯學位專區（11校24系）》、《學生赴外研修甄選暨獎補助要點》、《學生出國選修課程實施要點》、《辦理教育部學海系列計畫審查作業要點》與《各項英檢與CEFR架構對照表》官方資料：（1）兩梯次校內甄選、A/B/C/D四類優先順序与每學期6學分修課規定：每年分兩梯次（春季班於前一年4月收件、秋季班於前一年10月收件，如116-1秋季班於2026/10/05 14:00至2026/10/30 17:00收件、2026/12/31前放榜、2027/01/29放棄截止；115-2春季班於2026/04/10至04/30收件並錄取48名）辦理甄選，限於本校就讀一學期以上之在學學士班（出國時須為大二以上）及碩博士班（非當學期畢業）學生（不含在職專班及休學生），前一學期操行成績須達80分以上且無申誡以上處分及違反性平法／重大違法紀錄（須簽署行為確認聲明書），依A類（前一學期班排前40%）、B類（專業著作／重要展演／全國或國際競賽獲獎）、C類（一般申請者）、D類（同一學制第二次申請者）四類優先順序及總成績（書審40%＋面試60%）分發（至多填5志願）；非華語國家外語能力須達CEFR B1以上（GEPT中級 / TOEIC 550 / TOEFL iBT 42［新制3分］ / TOEFL ITP 433 / IELTS 4.0 / Duolingo 60，或日檢JLPT N1–N3、韓檢TOPIK 2–4級；中國大陸免附外語檢定）；交換期間於北市大完成註冊繳費並免繳姊妹校學費，每學期至少修習相當於本校6學分課程（暑期3學分；歐洲2 ECTS折算1學分，累計上限畢業總學分1/4）。（2）全球41國／地區226所合作姊妹校與11校24系雙聯學制：完整收錄中國大陸62校、美國23校、韓國20校、日本19校、馬來西亞9校、法國9校、波蘭7校、德國6校、捷克6校、泰國5校、越南5校、印尼5校、英國4校等共226所合作大學（含92所當期開放申請之交換與雙聯合作校，以及美國SWOSU/IUP/Troy、英國University of Essex［12系所］/Trinity Laban/Nottingham、紐西蘭奧克蘭大學、泰國朱拉隆功大學、馬來西亞馬來亞大學、哈薩克Satbayev、加拿大Western共11校24個雙聯學位學程）。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺》（含本校最少20%配合款）、《學海惜珠》、《學海築夢／新南向學海築夢》、北市大《返國生活獎補助》（亞洲最高NT$15,000、非亞洲最高NT$30,000，依8級優先順序核給），以及66所合作大學共421篇歷年出國交換學生研修心得報告與錄取紀錄。",
    support_level="full",
    partner_count_hint=226,
    academic_score_minimum=None,
    student_card_signals=(
        "臺北市立大學",
        "台北市立大學",
        "北市大",
        "UNIVERSITYOFTAIPEI",
        "UNIVERSITY OF TAIPEI",
        "UTAIPEI",
    ),
    # https://www.utaipei.edu.tw/ — checked 2026-10-31.
    colleges=(
        "教育學院",
        "人文藝術學院",
        "理學院",
        "體育學院",
        "市政管理學院",
    ),
)

NTCU = UniversityProfile(
    id="ntcu",
    school_name="國立臺中教育大學",
    short_name="中教大",
    english_name="National Taichung University of Education",
    aliases=(
        "ntcu",
        "國立臺中教育大學",
        "國立台中教育大學",
        "臺中教育大學",
        "台中教育大學",
        "中教大",
        "NTCU",
        "National Taichung University of Education",
    ),
    hero_image="/static/assets/ntcu-campus.svg",
    official_url="https://oia.ntcu.edu.tw/data/15",
    coverage_note="完整支援：已整合國立臺中教育大學國際及兩岸事務暨研究發展處（OIA）《締結姐妹校名單（263校）》、《交換學校名額表》、《116學年度與115學年度第3次選送學生出國研修簡章》、《甄選學生出國研修要點》、《補助學生赴外國大學（機構）選修課程要點》、《與外國大學校院辦理雙聯學制辦法》、《教育部學海飛颺／惜珠甄選簡章》及歷年出國研修心得報告。",
    support_level="full",
    partner_count_hint=263,
    academic_score_minimum=None,
    student_card_signals=(
        "國立臺中教育大學",
        "國立台中教育大學",
        "中教大",
        "NATIONALTAICHUNGUNIVERSITYOFEDUCATION",
        "NATIONAL TAICHUNG UNIVERSITY OF EDUCATION",
        "NTCU",
    ),
    # https://www.ntcu.edu.tw/ — checked 2026-10-31.
    colleges=(
        "教育學院",
        "人文學院",
        "理學院",
        "管理學院",
    ),
)

TNUA = UniversityProfile(
    id="tnua",
    school_name="國立臺北藝術大學",
    short_name="北藝大",
    english_name="Taipei National University of the Arts",
    aliases=(
        "tnua",
        "國立臺北藝術大學",
        "國立台北藝術大學",
        "臺北藝術大學",
        "台北藝術大學",
        "北藝大",
        "TNUA",
        "Taipei National University of the Arts",
    ),
    hero_image="/static/assets/tnua-campus.svg",
    official_url="https://oia.tnua.edu.tw/",
    coverage_note="完整支援：已整合國立臺北藝術大學國際事務處（OIA）《四大洲姊妹校申請資訊表（90校）》、《116學年度姊妹校交換學生甄選簡章》、《選送學生出國進修與交流甄選辦法》、《選送學生赴外交換行政契約書》、《Shared Campus 校園共享專案》、《UMAP 亞太大學交流會》、《學海飛颺暨學海惜珠補助甄選作業流程》及 106–114 學年度共 130 篇出國交換研修心得報告。",
    support_level="full",
    partner_count_hint=90,
    academic_score_minimum=None,
    student_card_signals=(
        "國立臺北藝術大學",
        "國立台北藝術大學",
        "北藝大",
        "TAIPEINATIONALUNIVERSITYOFTHEARTS",
        "TAIPEI NATIONAL UNIVERSITY OF THE ARTS",
        "TNUA",
    ),
    # https://w3.tnua.edu.tw/academics/ — checked 2026-11-01.
    colleges=(
        "音樂學院",
        "美術學院",
        "戲劇學院",
        "舞蹈學院",
        "電影與新媒體學院",
        "文化資源學院",
        "人文學院",
    ),
)

NTUA = UniversityProfile(
    id="ntua",
    school_name="國立臺灣藝術大學",
    short_name="臺藝大",
    english_name="National Taiwan University of Arts",
    aliases=(
        "ntua",
        "國立臺灣藝術大學",
        "國立台灣藝術大學",
        "臺灣藝術大學",
        "台灣藝術大學",
        "臺藝大",
        "台藝大",
        "臺藝",
        "台藝",
        "NTUA",
        "National Taiwan University of Arts",
    ),
    hero_image="/static/assets/ntua-campus.svg",
    official_url="https://international.ntua.edu.tw/",
    coverage_note="完整支援：已整合國立臺灣藝術大學國際事務處（OIA）《交換學校一覽表（102校）》、《116學年度第1學期交換學生計畫甄選簡章》、《國立臺灣藝術大學交換學生甄選要點》、《辦理教育部學海系列計畫補助作業要點》、《與境外大學合作辦理雙聯學制實施辦法》及 102–113 學年度共 56 校 345 篇出國交換研修心得報告。",
    support_level="full",
    partner_count_hint=102,
    academic_score_minimum=80.0,
    student_card_signals=(
        "國立臺灣藝術大學",
        "國立台灣藝術大學",
        "臺藝大",
        "台藝大",
        "NATIONALTAIWANUNIVERSITYOFARTS",
        "NATIONAL TAIWAN UNIVERSITY OF ARTS",
        "NTUA",
    ),
    # https://www.ntua.edu.tw/ — checked 2026-11-01.
    colleges=(
        "美術學院",
        "設計學院",
        "傳播學院",
        "表演藝術學院",
        "人文學院",
    ),
)


NTUE = UniversityProfile(
    id="ntue",
    school_name="國立臺北教育大學",
    short_name="國北教大",
    english_name="National Taipei University of Education",
    aliases=(
        "ntue",
        "國立臺北教育大學",
        "國立台北教育大學",
        "臺北教育大學",
        "台北教育大學",
        "國北教大",
        "國北教",
        "國北師",
        "北教大",
        "NTUE",
        "National Taipei University of Education",
    ),
    hero_image="/static/assets/ntue-campus.svg",
    official_url="https://oia.ntue.edu.tw/p/412-1066-2258.php?Lang=zh-tw",
    coverage_note="完整支援：已整合國立臺北教育大學研發處國際事務組（OIA）《海外姊妹校一覽表（143校）》、《115學年度赴海外姊妹校交換生甄選簡章（69校）》、《114學年度赴海外姊妹校大學交換甄選簡章》、《113學年度赴海外姊妹校大學交換甄選簡章》、《學生赴境外大學修讀雙聯學位實施要點》、《日本兵庫教育大學碩士班雙聯學位甄選簡章》、《法國社會科學高等學院（EHESS）博士雙聯學位計畫》、《學生出國選修課程實施要點》、《115年度教育部學海惜珠甄選簡章》、《應具語言能力參考標準》與《NTUE薦外交換心得專區（233篇）》官方資料：（1）七大語組甄選制度、學業及語文門檻與每學期2門課／6學分規定：每年11月公告簡章、12月收件（如115學年度於114/12/01至12/12 16:00收件並繳交報名費NT$500，115/01/06筆試40%［含英文或各語組2題申論題］、115/01/07–01/08面試60%［含書審及學業成績］，總成績未滿60分不予錄取，115/02/23前公告錄取名單、115/03/02 16:00前截止申請更改交換期間或放棄；116學年度出國交換系列說明會於2026/09/29線上及2026/11/03實體舉辦），限本校大學部二年級以上（大一及轉學生尚未有本校成績者除外）及研究所碩博士班在學學生（不含在職專班生及領有臺灣獎學金者；公費生須經師資培育處、分發縣市政府及教育部同意展延分發並暫停公費；應屆畢業生須經系所主管同意且符合延畢規定），歷年在校成績總平均須達75分（含）以上或GPA 3.0以上（學海惜珠另須班級排名前50%，成績單須註明班級排名），分為英文組、日文組、韓文組、越文組、法文組、德文組、中文組共7組（每人限擇一組報考，德瑞奧9校標註▲者由英文組及德文組共用名額）；非華語組須具備英文CEFR B1（TOEFL iBT 42–71 / IELTS 4.0–5.5 / TOEIC 550–750）、日檢JLPT N3（部分學校N2/N1，常磐大學秋季班N5）、韓檢TOPIK 2–3級、法檢DELF B1–B2、德檢TestDaF TDN3 / B1–B2或越檢IVPT A/B級；交換期間須完成國北教大註冊選課並免繳姊妹校學費（部分學校如法蘭克福大學需自付雜費、法國巴黎索邦大學需自費法語密集班、韓國部分學校需修讀韓語課程），每學期至少修習2門課或6學分且不得超過畢業學分1/3。（2）全球25國／地區143所合作姊妹校與雙聯學位：完整收錄日本29校、中國大陸20校、美國17校、越南14校、韓國10校、馬來西亞7校、德國6校、印尼6校、捷克4校、奧地利4校、法國4校、泰國4校、新加坡3校、菲律賓2校、波蘭2校、澳洲2校、瑞士2校及英國／立陶宛／西班牙／芬蘭／俄羅斯／智利／加拿大各1校共143所合作大學（含69所當期開放交換申請之姊妹校，以及日本兵庫教育大學碩士班雙聯學位、法國社會科學高等學院EHESS博士雙聯學位）。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺》、《學海惜珠》、國北教大國際交流獎助學金（依地區與期限補助NT$10,000至NT$80,000）及芝山博愛獎助學金，以及橫跨12國共233篇歷屆學長姐返國交換心得報告（102–113學年度）。",
    support_level="full",
    partner_count_hint=143,
    academic_score_minimum=75,
    student_card_signals=(
        "國立臺北教育大學",
        "國立台北教育大學",
        "臺北教育大學",
        "台北教育大學",
        "國北教大",
        "NATIONALTAIPEIUNIVERSITYOFEDUCATION",
        "NATIONAL TAIPEI UNIVERSITY OF EDUCATION",
        "NTUE",
    ),
    # https://www.ntue.edu.tw/p/412-1000-778.php?Lang=zh-tw — checked 2026-10-31.
    colleges=(
        "教育學院",
        "人文藝術學院",
        "理學院",
        "國際學位學程",
    ),
)


NCUT = UniversityProfile(
    id="ncut",
    school_name="國立勤益科技大學",
    short_name="勤益科大",
    english_name="National Chin-Yi University of Technology",
    aliases=(
        "ncut",
        "國立勤益科技大學",
        "勤益科技大學",
        "勤益科大",
        "國立勤益科大",
        "勤益",
        "NCUT",
        "National Chin-Yi University of Technology",
        "Chin-Yi University of Technology",
    ),
    hero_image="/static/assets/ncut-campus.svg",
    official_url="https://oia.ncut.edu.tw/p/412-1030-6648.php?Lang=zh-tw",
    coverage_note="完整支援：已整合國立勤益科技大學國際事務處（OIA）國際合作組《海外姊妹校締約一覽表（134校）》、《選送學生出國交換研修申請簡章與姊妹校名額表（33校）》、《雙聯學制合作專區（日本國立東北大學、國立岩手大學、加拿大皇家大學 RRU、越南大南大學）》、《選送學生出國研修辦法》、《辦理學生抵免學分辦法》、《推動學生參與國際化多元學習補助要點》與《學海計畫暨校內出國補助 Q&A》官方資料：（1）兩梯次校內甄選、學業操行門檻與每學期修課規定：每年分兩梯次（春季班於前一年9–10月收件、秋季班於當年度2–3月收件，如115-1秋季班第一梯次於2026/03/20截止、第二梯次延長至2026/03/31 12:00截止；115-2春季班於2026/09–10月收件）辦理甄選，限於本校就讀滿一學期以上之具正式學籍在學四技、二技及碩博士班學生（不含在職專班及休學生），歷年學業成績總平均須達70分（或GPA 2.5）以上、操行成績平均達80分以上且無小過以上處分紀錄；外語能力依各姊妹校規定須達英語CEFR B1–B2（TOEIC 550–785 / TOEFL iBT 42–80 / TOEFL ITP 457–543 / IELTS 4.0–6.0 / GEPT中級以上）、日檢JLPT N1–N5或韓檢TOPIK 2–3級以上（中國大陸姊妹校免附外語檢定）；交換期間於勤益科大完成註冊繳費並免繳姊妹校學費，每學期至少修習2門或6學分專業課程。（2）全球20國／地區134所合作姊妹校與4校跨國雙聯學制：完整收錄越南28校、日本23校、中國大陸22校、印尼17校、美國9校、韓國9校、印度6校、馬來西亞5校、菲律賓4校等共134所合作大學（含33所當期開放申請之出國交換與雙聯合作校，以及日本國立東北大學材料科學雙聯博士、國立岩手大學理工學府雙聯碩士、加拿大皇家大學 RRU 2+2 雙聯學士、越南大南大學雙聯碩士）。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺》、《學海惜珠》、《學海築夢／新南向學海築夢》、勤益科大《推動學生參與國際化多元學習補助》（含生活費與來回機票補助），以及23所合作大學共41篇歷年出國交換學生研修心得報告、影片與錄取紀錄。",
    support_level="full",
    partner_count_hint=134,
    academic_score_minimum=70.0,
    student_card_signals=(
        "國立勤益科技大學",
        "勤益科技大學",
        "勤益科大",
        "NATIONAL CHIN-YI UNIVERSITY OF TECHNOLOGY",
        "CHIN-YI UNIVERSITY OF TECHNOLOGY",
        "NCUT",
    ),
    # https://www.ncut.edu.tw/ — checked 2026-11-01.
    colleges=(
        "工程學院",
        "電資學院",
        "管理學院",
        "人文創意學院",
        "通識教育學院",
    ),
)


NPUST = UniversityProfile(
    id="npust",
    school_name="國立屏東科技大學",
    short_name="屏科大",
    english_name="National Pingtung University of Science and Technology",
    aliases=(
        "npust",
        "國立屏東科技大學",
        "屏東科技大學",
        "屏科大",
        "屏東科大",
        "NPUST",
        "National Pingtung University of Science and Technology",
    ),
    hero_image="/static/assets/npust-campus.svg",
    official_url="https://oia2.npust.edu.tw/go-abroad/",
    coverage_note="完整支援：已整合國立屏東科技大學國際事務處（OIA）《本國生出國專區》、《學生赴國外姊妹校交換與研習申請審查作業要點（114.12.18修正）》、《出國雙聯學位制名冊》、《國外姊妹校及大陸港澳合作學校一覽表》及教務處《辦理跨國雙聯學位制實施辦法（114.12.01修正）》官方資料：（1）校內甄選時程與資格：每學期初受理次學期赴外交換申請（秋季班每年 3 月底前送國際處、春季班每年 9 月底前送國際處），限大二（含）以上或碩博班在學學生（不含在職專班），操行成績平均 80 分以上、歷年學業成績平均 70 分以上或班排名前 50%，並具備相當全民英檢中級初試、TOEIC 550、TOEFL iBT 42、IELTS 4.0、JLPT N2 或姊妹校指定語檢門檻；審查採書面審查 30%（自傳、出國學習計畫、成績單及英外語證明）與面試 70%（含英外語能力、學習規劃及溝通反應）。（2）合作姊妹校與雙聯學位：完整收錄 309 所全球及兩岸港澳合作大學（橫跨 49 國與地區，含 30 所當期開放申請之出國交換與跨國雙聯學位姊妹校［日、韓、德、法、捷克、義、西、泰、馬、印尼、越、陸及美加英澳雙聯校］及 279 所簽署學術合作 MOU 之姊妹校）。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺／惜珠／築夢／新南向學海築夢》、《校內學生出國交換與研習獎助學金》（亞洲最高 NT$35,000、歐美澳非最高 NT$70,000）及 32 所合作大學共 37 篇歷屆學長姐赴外交換與實習心得報告。",
    support_level="full",
    partner_count_hint=309,
    academic_score_minimum=70,
    student_card_signals=(
        "國立屏東科技大學",
        "屏東科技大學",
        "NATIONALPINGTUNGUNIVERSITYOFSCIENCEANDTECHNOLOGY",
        "NPUST",
    ),
    # https://www.npust.edu.tw/ — checked 2026-10-31.
    colleges=(
        "農學院",
        "工學院",
        "管理學院",
        "人文暨社會科學院",
        "國際學院",
        "獸醫學院",
        "達人學院",
    ),
)

NKUHT = UniversityProfile(
    id="nkuht",
    school_name="國立高雄餐旅大學",
    short_name="高餐大",
    english_name="National Kaohsiung University of Hospitality and Tourism",
    aliases=(
        "nkuht",
        "國立高雄餐旅大學",
        "高雄餐旅大學",
        "高餐大",
        "高餐",
        "NKUHT",
        "National Kaohsiung University of Hospitality and Tourism",
    ),
    hero_image="/static/assets/nkuht-campus.svg",
    official_url="https://iao.nkuht.edu.tw/p/412-1005-857.php?Lang=zh-tw",
    coverage_note="完整支援：已整合國立高雄餐旅大學國際事務處（OIA）《海外留學交換平台（2027-28 交換學生與雙聯學位簡章）》、《辦理學生海外實習及留學補充規定（113.06.05修正）》、《115年度教育部學海飛颺及學海惜珠計畫甄選簡章》及《遠航圓夢助學金實施辦法》官方資料：（1）校內甄選時程與資格：免學費交換生為三年級出國交換一學年、自費交換生及 1+1 雙聯碩士為三年級或研究所出國一學年，115-1 起跑（2026/09/17 留學說明會、2026/10–12 校內報名收件、2027/02–03 國際處公告錄取名單與姊妹校提名），歷年操行成績須無小過以上紀錄、學業成績總平均達 75 分以上（或班排名前 20%–30%），並具備多益、托福、雅思、全民英檢、日檢 JLPT N2–N3 或韓檢 TOPIK 等語檢證明。（2）合作姊妹校與雙聯學位：完整收錄 40 所海外餐旅觀光名校（橫跨 15 國，含 31 所 2027-28 開放申請之免學費交換、自費交換與瑞士 SHMS／César Ritz、英國 UCB、美國天普大學及南卡羅來納大學 1+1 雙聯碩士合作校，以及 9 所重點海外合作大學）。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺／學海惜珠》（歐洲最高補助 NT$120,000、美加最高 NT$150,000）、《高餐大遠航圓夢助學金》（最高 NT$200,000）及 17 所合作大學共 19 篇歷屆學長姐赴外交換與雙聯實習心得報告。",
    support_level="full",
    partner_count_hint=40,
    academic_score_minimum=75,
    student_card_signals=(
        "國立高雄餐旅大學",
        "高雄餐旅大學",
        "NATIONALKAOHSIUNGUNIVERSITYOFHOSPITALITYANDTOURISM",
        "NKUHT",
    ),
    # https://www.nkuht.edu.tw/p/412-1000-322.php?Lang=zh-tw — checked 2026-11-02.
    colleges=(
        "餐旅學院",
        "觀光學院",
        "廚藝學院",
        "國際學院",
        "全人教育學院",
    ),
)


CJCU = UniversityProfile(
    id="cjcu",
    school_name="長榮大學",
    short_name="長大",
    english_name="Chang Jung Christian University",
    aliases=(
        "cjcu",
        "長榮大學",
        "長榮",
        "長大",
        "CJCU",
        "Chang Jung Christian University",
    ),
    hero_image="/static/assets/cjcu-campus.svg",
    official_url="https://dweb.cjcu.edu.tw/oia/article/3030",
    coverage_note="完整支援：已整合長榮大學國際處國際合作組（OIA）《115學年度校級國際交換生甄選簡章》、《校級國際交換生學校一覽表（79校）》、《海外雙聯學位學校列表（8校12學程）》、《全球與兩岸締約姊妹校名錄（193校）》、《長榮大學赴外研修生作業要點》、《長榮大學學生出國期間學業及學籍處理要點》、《長榮大學海外雙聯學制實施辦法》、《長榮大學推展學生國際學術交流獎補助辦法》与《長榮大學短期交流補助作業要點》官方資料：（1）校內甄選時程、資格與四組配分：115學年度校級國際交換生甄選自 2026/10/01 至 2026/11/27 17:00 受理（10/02 12:10 舉辦說明會、12/04 公告面試時間表、12/11 辦理分組面試、12/16 公告第一階段錄取名單、12/21 第一階段錄取確認截止、12/31 公告最終錄取名單），申請人出國就讀時須於本校修業滿一學年（含）以上且前一學年度學業平均成績達 70 分（含）以上；評比採「面試 40%」（英韓組、英語組、中文組、日語組）＋「書面資料 60%」（前一學年度操行成績 10%＋前一學年度學業成績 10%＋自傳及讀書計畫 15%＋語文證明 10%＋其他相關資料 15%），錄取生（除日語組與中國地區外）須參加並通過語文教育中心「交換生英語加強課程」（第 1–9 週），交換期間每學期至少修習相當本校 9 學分或 3 門課程（不含體育課）且至少 6 學分或 2 門課程及格。（2）全球 26 國與地區 193 所合作姊妹校與 8 校跨國雙聯學位：完整收錄 88 所常態開放申請之校級交換與雙聯學位學校（含日本鎮西學院大學、創價大學與韓國韓信大學「免學費＋免住宿費」，印尼蘇吉甲普拉納塔天主教大學印尼政府獎學金，以及英國女王大學 QUB、諾丁漢特倫特大學 NTU、法國雷恩商學院、澳洲西雪梨大學、美國北德州大學 UNT、馬來西亞砂拉越科技大學 UTS、泰國清邁皇家大學 CMRU 等雙聯學位）及 105 所正式締約姊妹校。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺／惜珠》（前學年平均達 75 分或班排前 25%）、《長榮大學推展學生國際學術交流獎補助金》（前學年平均及格或班排前 50%）、《短期交流補助》（每人最高 NT$40,000），以及 42 所合作大學共 145 篇歷屆學長姐返國交換心得報告與 35 份官方 Fact Sheet。",
    support_level="full",
    partner_count_hint=193,
    academic_score_minimum=70.0,
    student_card_signals=(
        "長榮大學",
        "CHANGJUNGCHRISTIANUNIVERSITY",
        "CHANG JUNG CHRISTIAN UNIVERSITY",
        "CJCU",
    ),
    # https://www.cjcu.edu.tw/tw/acad.php — checked 2026-11-02.
    colleges=(
        "管理學院",
        "健康科學學院",
        "人文社會學院",
        "資訊暨設計學院",
        "安全衛生科學學院",
        "永續教育學院",
        "環境教育國際實驗學院",
        "神學院",
        "PLUS學院",
        "博雅教育學部",
    ),
)


NQU = UniversityProfile(
    id="nqu",
    school_name="國立金門大學",
    short_name="金大",
    english_name="National Quemoy University",
    aliases=(
        "nqu",
        "國立金門大學",
        "金門大學",
        "金大",
        "國立金門技術學院",
        "金門技術學院",
        "NQU",
        "National Quemoy University",
    ),
    hero_image="/static/assets/nqu-campus.svg",
    official_url="https://oica.nqu.edu.tw/",
    coverage_note="完整支援：已整合國立金門大學國際暨兩岸事務處（OICA）與教務處註冊組《國際交換學校一覽表（39校）》、《大陸地區交換學校一覽表與姊妹校名冊（25校）》、《115學年度第一／二階段國際交換學生甄選簡章》、《2027春季班（115-2）赴國內及大陸地區交換學生甄選簡章》、《國立金門大學學生國際交流甄選要點》、《國立金門大學學生出國交換實施要點》、《國立金門大學科目學分抵免辦法》、《115年度教育部學海飛颺及學海惜珠計畫甄選簡章》及 31 校共 317 篇歷屆赴外與赴大陸交換學生心得報告。",
    support_level="full",
    partner_count_hint=64,
    academic_score_minimum=70.0,
    student_card_signals=(
        "國立金門大學",
        "金門大學",
        "金大",
        "NATIONALQUEMOYUNIVERSITY",
        "NATIONAL QUEMOY UNIVERSITY",
        "NQU",
    ),
    # https://www.nqu.edu.tw/ — checked 2026-11-02.
    colleges=(
        "人文社會學院",
        "管理學院",
        "理工學院",
        "健康護理學院",
    ),
)


ISU = UniversityProfile(
    id="isu",
    school_name="義守大學",
    short_name="義大",
    english_name="I-Shou University",
    aliases=(
        "isu",
        "義守大學",
        "義大",
        "義守",
        "ISU",
        "I-Shou University",
        "IShou University",
    ),
    hero_image="/static/assets/isu-campus.svg",
    official_url="https://oica.isu.edu.tw/page/%E5%87%BA%E5%9C%8B%E4%BA%A4%E6%8F%9B-NlHq3RuLdDcK",
    coverage_note="完整支援：已整合義守大學國際及兩岸事務處（OICA）《出國交換暨雙聯學位專區》、《交換姐妹校名冊》、《雙聯學位學校列表（11 校）》、《全球與兩岸合作姐妹校名錄》、《海外交換費用參考表》、《義守大學學生赴境外交換研修甄選辦法》、《義守大學辦理教育部學海飛颺及學海惜珠計畫甄選辦法》、《義守大學學海助學金設置及甄選作業辦法》、《義守大學赴大陸校際交換獎學金辦法》與《義守大學學文助學金設置及甄選作業辦法》官方資料：（1）校內甄選時程與資格：每年 2 月開放第一梯次（秋季班出國交換一學期或一學年）及每年 8 月開放第二梯次（春季班出國交換一學期）校內甄選，限大二以上或碩一以上在學學生，出國期間維持本校學籍並繳交義守大學全額學雜費，每學期修習至少 9 學分（大陸研修團至少 16 學分），外語能力應符合交流學校規定或通過本校英語畢業資格檢定標準（CEFR B1 / TOEIC 550 / TOEFL iBT 42 / IELTS 4.0）。（2）合作姐妹校與雙聯學位：完整收錄 181 所全球及兩岸港澳有效締約姐妹校（橫跨 33 國與地區，含英、美、港、日、韓、陸 11 所跨國雙聯學位合作校）。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺／惜珠》（系前 40% 或班前 30%）、《義守大學學海助學金》、《赴大陸校際交換獎學金》、《義守大學學文助學金》（交流團、暑期學習團公費／部分公費與一學期大陸研修團）、《歐盟 Erasmus+ 獎學金》及 13 所合作大學共 18 篇歷屆學長姐交換心得報告与 12 份官方 Fact Sheet。",
    support_level="full",
    partner_count_hint=181,
    academic_score_minimum=60,
    student_card_signals=(
        "義守大學",
        "義大",
        "ISHOUUNIVERSITY",
        "I-SHOUUNIVERSITY",
        "ISU",
    ),
    # https://www.isu.edu.tw/ — checked 2026-11-02.
    colleges=(
        "智慧科技學院",
        "工學院",
        "管理學院",
        "傳播與設計學院",
        "國際學院",
        "觀光餐旅學院",
        "醫學院",
        "醫學科技學院",
        "原住民族學院",
        "通識教育中心",
    ),
)


FGU = UniversityProfile(
    id="fgu",
    school_name="佛光大學",
    short_name="佛大",
    english_name="Fo Guang University",
    aliases=(
        "fgu",
        "佛光大學",
        "佛大",
        "佛光",
        "FGU",
        "Fo Guang University",
    ),
    hero_image="/static/assets/fgu-campus.svg",
    official_url="https://oica.fgu.edu.tw/zh_tw/exchange/20",
    coverage_note="完整支援：已整合佛光大學國際暨兩岸事務處（OICA，雲起樓 112 室）《115學年度第一學期交換生／雙學位甄選說明會簡報》、《認識 2+2 Program（佛光山系統大學美國西來大學 University of the West 台美雙學位）》、《英國國立密德薩斯大學 Middlesex University 3+1／1+1 雙聯學位說明會簡報》、《佛光大學赴中國大陸以外國家及地區交換學生甄選辦法（A06-004）》、《佛光大學赴大陸交換學生甄選辦法（A06-005）》、《佛光大學學生參與西來大學 2+2 計畫實施辦法》、《佛光大學林陸素琦女士海外留學獎勵基金設置與管理辦法》、《佛光大學學海無涯國際交流獎助學金設置與管理辦法》、《佛光大學辦理國內外學校學生交流學習執行要點》與《歷屆海外交換及台美雙學位甄選錄取榜單與分享會簡報》官方資料：（1）兩梯次校內甄選時程、75分／全班前50%學業門檻與圖書館 EASY TEST iBT 測驗規定：每學期初（9–10月及2–3月）辦理次學期赴海外及大陸交換生暨雙聯學位校內甄選（如 115-1 甄選說明會於 2026/09/23 舉辦、申請文件繳交截止日為 2026/10/08），限具本校正式學籍之在學學生（大學部大二以上或碩博班碩一以上，大一下可報名大二交換，大一／大二可報名西來大學 2+2 雙學位），前一學期學業平均成績須達 75 分（約 GPA 3.0）以上且操行成績達 80 分以上（申請中國人民大學、南京大學、東南大學、四川大學、北京交通大學等大陸 985/211 重點名校須達全班排名前 20% 以內）；報名海外交換或雙學位者須於校內甄選前先完成圖書館線上英文模擬測驗「EASY TEST iBT 托福題型」並繳交成績單，外語能力依姊妹校規定須達英語 TOEFL iBT 61–80 / IELTS 5.5–6.5 / TOEIC 550–750、日檢 JLPT N3–N2 或韓檢 TOPIK 2–3 級（大陸姊妹校免附外語檢定）；交換期間於佛光大學完成註冊繳費並免繳姊妹校學費（日本花園大學與韓國金剛大學另提供免住宿費、美國西來大學交換生每學期最高獎助 US$3,500、2+2 雙學位生每學期最高獎助 US$7,500）。（2）全球 13 國／地區 52 所合作姊妹校與佛光山教團系統大學：完整收錄美國 3 校（西來大學、休士頓大學清湖分校、春山學院）、英國 1 校（國立密德薩斯大學）、德國 1 校（漢堡大學）、澳洲 1 校（南天大學）、紐西蘭 1 校（奧塔哥大學）、日本 2 校（龍谷大學、花園大學）、韓國 12 校（京畿大學、東國大學首爾校區、東國大學 WISE 校區、慶尚國立大學、金剛大學、東明大學、昌原國立大學、威德大學、新羅大學、中央僧伽大學、建國大學、京東大學）、泰國 2 校（正大管理學院、ม่โจ้大學 Maejo University）、馬來西亞 1 校（拉曼大學）、菲律賓 2 校（拉普拉普宿霧國際大學、光明大學）、印度 1 校（德里大學）、緬甸 1 校（龐道烏國際大學）、香港 1 校（香港教育大學）及中國大陸 23 校（中國人民大學、南京大學、北京交通大學、上海大學、四川大學、深圳大學、華中師範大學、鄭州大學、西北師範大學、陽光學院、東南大學、煙台大學、揚州大學、合肥工業大學、集美大學、廣東海洋大學、福建技術師範學院、海南大學、南京理工大學、濟南大學、陝西師範大學、雲南大學、青海民族大學）共 52 所合作大學（含 50 所當期開放申請之交換與雙聯合作校）。（3）四大獎助學金體系與學長姐經驗傳承：涵蓋教育部《學海飛颺／學海惜珠》、《林陸素琦女士海外留學獎勵基金》、《學海無涯國際交流獎助學金》與《西來大學 2+2 計畫獎學金》，以及 26 所合作大學共 30 篇歷屆交換生與雙學位生錄取榜單及分享會心得紀錄。",
    support_level="full",
    partner_count_hint=52,
    academic_score_minimum=75.0,
    student_card_signals=(
        "佛光大學",
        "佛大",
        "FOGUANGUNIVERSITY",
        "FO GUANG UNIVERSITY",
        "FGU",
    ),
    # https://website.fgu.edu.tw/zh_tw/academics — checked 2026-11-02.
    colleges=(
        "人文學院",
        "社會科學院",
        "管理學院",
        "創意與科技學院",
        "樂活產業學院",
        "佛教學院",
    ),
)


NUU = UniversityProfile(
    id="nuu",
    school_name="國立聯合大學",
    short_name="聯大",
    english_name="National United University",
    aliases=(
        "nuu",
        "國立聯合大學",
        "聯合大學",
        "聯大",
        "NUU",
        "National United University",
    ),
    hero_image="/static/assets/nuu-campus.svg",
    official_url="https://oia.nuu.edu.tw/p/412-1068-1242.php",
    coverage_note="完整支援：已整合國立聯合大學研究發展處國際及兩岸事務組（OIA）《國際交換學生作業要點（109.03.03修正）》、《國際學術交流實施辦法（110.05.25修正）》、《雙聯學制實施辦法（106.02.18）》、《學生赴國外研修留學國語言能力參考標準》、《補助學生參與境外學術交流及研習服務經費管理要點》、《「學海系列計畫」甄選作業要點（114.01.16修正）》、《學生於締約學校修讀課程學分與成績轉換參考表》、《交換學校一覽表（128校）》及《全球締約姊妹校名錄》官方資料：（1）兩梯次校內甄選、「出國交換當時」年級系所認定、分組配分與NT$ 3,000保證金規定：每年1月（第一梯次，結合12/15–2/14教育部學海飛颺／惜珠期程，得申請一學期或一學年）及8月（第二梯次春季班，僅得申請一學期）辦理校內甄選，具本校大學部及研究所學籍之在學學生（不含在職生）皆可申請，惟各姊妹校之年級與系所限制以「出國交換當時」之學籍身分與年級為準；甄選採計總分未達60分不予推薦（赴大陸以外地區大學部採計在校成績50%＋外語20%＋自傳10%＋讀書計畫15%＋其他5%、研究所採計在校成績30%＋外語20%＋自傳20%＋讀書計畫25%＋其他5%；赴大陸地區免計外語，大學部採計在校成績60%＋自傳15%＋讀書計畫20%＋其他5%、研究所採計在校成績40%＋自傳25%＋讀書計畫30%＋其他5%）；錄取後20日內須繳交保證金NT$ 3,000，交換期間每學期大學部至少修讀3門課程及格、研究所至少修讀1門課程及格，返國後14日內繳交返國程序單與中英文心得並完成20小時國際組服務後全額退還。（2）全球21國／地區128所合作姊妹校、日本國立高專（NIT）聯盟與6校美法加雙聯學位：完整收錄128所合作姊妹校（含29所常態開放申請之交換、雙聯與日本高專暑期研習合作校，涵蓋日本宇部、高知、新居濱、阿南、木更津、明石、小山、釧路等國立高專及甲南大學、愛知教育大學，韓國仁荷大學、昌原國立大學、高麗網路大學，美國霜堡州立大學 FSU 2+2、佛羅里達理工學院 FIT 2+2、樹城州立大學 Boise State 2+2、南猶他大學 SUU、明尼蘇達州立大學曼卡托分校，加拿大安大略理工大學、卡加利大學，法國南特理工大學、薩瓦勃朗峰大學，德國馬德堡大學，馬來西亞拉曼大學 UTAR，泰國吞武里蒙庫國王科技大學 KMUTT，越南胡志明市經濟大學 UEH，印尼總統大學、迪波內戈羅大學及蒙古全球領袖大學）。（3）獎助學金體系：涵蓋教育部《學海飛颺／學海惜珠／學海築夢／新南向學海築夢》、聯大《補助學生參與境外學術交流經費》（亞太最高NT$ 15,000、歐美最高NT$ 25,000–35,000、團隊最高NT$ 100,000）、日本JASSO獎學金及美國雙聯學位獎學金（FSU每學期USD 3,000、FIT每學期USD 5,000–7,000、SUU USD 4,250）。",
    support_level="full",
    partner_count_hint=128,
    academic_score_minimum=60,
    student_card_signals=(
        "國立聯合大學",
        "聯合大學",
        "NATIONALUNITEDUNIVERSITY",
        "NATIONAL UNITED UNIVERSITY",
        "NUU",
    ),
    # https://www.nuu.edu.tw/p/412-1000-745.php?Lang=zh-tw — checked 2026-11-02.
    colleges=(
        "理工學院",
        "電機資訊學院",
        "管理學院",
        "客家研究學院",
        "人文與社會學院",
        "設計學院",
    ),
)


TNNUA = UniversityProfile(
    id="tnnua",
    school_name="國立臺南藝術大學",
    short_name="南藝大",
    english_name="Tainan National University of the Arts",
    aliases=(
        "tnnua",
        "國立臺南藝術大學",
        "國立台南藝術大學",
        "臺南藝術大學",
        "台南藝術大學",
        "南藝大",
        "南藝",
        "TNNUA",
        "Tainan National University of the Arts",
    ),
    hero_image="/static/assets/tnnua-campus.svg",
    official_url="https://oia.tnnua.edu.tw/p/412-1007-1052.php?Lang=zh-tw",
    coverage_note="完整支援：已整合國立臺南藝術大學國際事務處（OIA）《海外姊妹校締約一覽表（63校）》、《115學年度第一學期赴國外及大陸地區姊妹校交換生甄選公告》、《國立臺南藝術大學選送學生出國研修與交流甄選辦法（113.06.03修正）》、《學生修讀國外與港澳地區雙聯學位實施辦法（112.01.03修正）》、《辦理教育部學海飛颺、學海惜珠及學海築夢補助作業要點》、《選送學生赴國外研修獎助學金審查原則》與《海外研修暨學海築夢經驗分享（38篇）》官方資料：（1）兩階段校內甄選、系所書審與外語口試門檻：每年分兩學期（秋季班於前一年9–10月、春季班於當年度2–4月，如115-1秋季班於2025/09/17公告、10/14截止收件、10/29面試，115-2春季班於2026/02/13啟動春季提名）辦理甄選，限本校日間學制大學部二年級以上、七年一貫制學士班五年級以上及碩博士班就讀一學期以上之在學學生（不含碩士班在職專班、休學生及外籍學位生）；第一階段「系所書面初審」（占50%，含歷年成績與研修計畫30%、專業作品與成就20%）須經系所會議通過且初審成績達40分（滿分50分）以上始得進入複審，第二階段「校內口試複審」（占50%，含面試表現30%、語言能力含1–2分鐘擬赴國家語言自我介紹20%），兩階段總成績須達80分（含）以上始得錄取；外語能力依《外國語文能力對照表》建議達英語 TOEFL iBT 79 / IELTS 6.0、日檢 JLPT N2、韓檢 TOPIK 3級、法語 DELF/TCF B1、德語 B1 / TestDaF TDN3 或西語 DELE B1 以上（中國大陸姊妹校免附外語檢定）；交換期間須完成南藝大註冊繳費並免繳姊妹校學費，每學期至少修習1門專業課程。（2）全球21國／地區63所合作姊妹校與跨國雙聯學位：完整收錄中國大陸25校、美國6校、日本4校、印尼4校、韓國3校、法國3校、奧地利2校、捷克2校、新加坡2校、泰國2校及德、義、西、瑞士、波蘭、愛沙尼亞、保加利亞、澳洲、越南、哈薩克各1校共63所合作藝術與綜合大學（含29所開放學期交換與雙聯學位之姊妹校，以及美國舊金山藝術學院 SFAI 雙聯學位與《學生修讀國外與港澳地區雙聯學位實施辦法》）。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺》（學業總平均80分／GPA 3.0以上）、《學海惜珠》、《學海築夢／新南向學海築夢》及南藝大《選送學生赴國外研修獎助學金審查原則》，以及18所合作大學與海外博物館／古物修復機構共38篇歷屆學長姐出國交換與學海築夢實習心得報告。",
    support_level="full",
    partner_count_hint=63,
    academic_score_minimum=80.0,
    student_card_signals=(
        "國立臺南藝術大學",
        "國立台南藝術大學",
        "南藝大",
        "TAINAN NATIONAL UNIVERSITY OF THE ARTS",
        "TAINANNATIONALUNIVERSITYOFTHEARTS",
        "TNNUA",
    ),
    # https://www.tnnua.edu.tw/p/412-1000-91.php?Lang=zh-tw — checked 2026-11-03.
    colleges=(
        "音樂學院",
        "視覺藝術學院",
        "音像藝術學院",
        "文博學院",
        "跨域創生學院",
    ),
)


TPCU = UniversityProfile(
    id="tpcu",
    school_name="臺北城市科技大學",
    short_name="城市科大",
    english_name="Taipei City University of Science and Technology",
    aliases=(
        "tpcu",
        "臺北城市科技大學",
        "台北城市科技大學",
        "城市科大",
        "北城科大",
        "臺北城市科大",
        "台北城市科大",
        "城市大學",
        "北台科大",
        "北台科學技術學院",
        "光武工專",
        "TPCU",
        "Taipei City University of Science and Technology",
    ),
    hero_image="/static/assets/tpcu-campus.svg",
    official_url="https://ieec.tpcu.edu.tw/",
    coverage_note="完整支援：已整合臺北城市科技大學國際事務處（國際交流中心）、商管學院、民生學院、工程學院與研究發展處《海外留學姊妹校總表》、《學生出國研修辦法（106.06.19修訂）》、《與境外大學辦理雙聯學制實施辦法（105.09.14教育部備查）》、《教育部獎助大專校院選送學生出國研修—學海飛颺、學海惜珠校內甄選辦法（108.01.21修訂）》、《教育部獎助大專校院國外專業實習計畫—學海築夢及新南向學海築夢校內甄選辦法（115.01.05修訂）》及《學生海外實習及研習輔導要點（106.10.30修訂）》官方資料：（1）校內甄選資格、錄取確認與修課抵免：申請出國交換研修者須為就讀本校滿一學年以上且非當學期畢業之在學學生（不含境外碩士專班；學海計畫須在學滿一學期以上且不含在職專班生），無小過以上處分紀錄，前一學年學業平均總成績達 60 分以上、操行平均總成績達 75 分以上；錄取生於公告隔天至國際事務處報到、1 週內繳交錄取確認書；海外研習一學期上課總學分不得少於 10 學分，返國後當學期開學 1 週內辦理學分抵免。（2）海外合作姊妹校與跨國雙聯學制：完整收錄 18 所日、韓、紐、英、美官方合作姊妹校（含日本城西國際大學、神戶國際大學、鹿兒島國際大學、國立琉球大學、日本經濟大學、北海道星槎道都大學、國立德島大學、十文字學園女子大學、國立宇都宮大學、昭和音樂大學；韓國信韓大學、富川大學；紐西蘭國際太平洋大學 IPU New Zealand；英國伯明翰大學學院 UCB；美國加州峽谷大學、曼徹普利敦州立大學、聖保羅學院、明州西南州立大學，其中 11 校提供 2+2／3+1／1 年雙聯學位）。（3）獎助學金與留學榜單：涵蓋教育部《學海飛颺／惜珠》（補助 NT$50,000–300,000）、《學海築夢／新南向學海築夢》海外實習獎助及 18 所合作大學共 38 篇歷屆交換雙聯榜單與研修紀錄。",
    support_level="full",
    partner_count_hint=18,
    academic_score_minimum=60.0,
    student_card_signals=(
        "臺北城市科技大學",
        "台北城市科技大學",
        "城市科大",
        "TAIPEICITYUNIVERSITYOFSCIENCEANDTECHNOLOGY",
        "TPCU",
    ),
    # https://www.tpcu.edu.tw/p/412-1000-485.php?Lang=zh-tw — checked 2026-11-03.
    colleges=(
        "工程學院",
        "商管學院",
        "民生學院",
    ),
)


AU = UniversityProfile(
    id="au",
    school_name="真理大學",
    short_name="真理",
    english_name="Aletheia University",
    aliases=(
        "au",
        "真理大學",
        "真理",
        "真大",
        "AU",
        "Aletheia University",
        "Oxford College Tamsui",
    ),
    hero_image="/static/assets/au-campus.svg",
    official_url="https://cia.au.edu.tw/p/403-1022-109353.php?Lang=zh-tw",
    coverage_note="完整支援：已整合真理大學國際事務中心（CIA）《交換計畫專區》、《雙聯學制專區》、《短期研修專區》、《姐妹校一覽》、《法規與獎學金辦法》與《學海計畫專區》官方資料：（1）校內甄選時程與資格：依《真理大學交換學生出國甄選辦法（教-P-806）》、《2027春季／2026秋季國外姐妹校交換學生實施計畫》與《2026~2027日本姐妹校交換生實施計畫》，限就讀滿一學年以上之大學部與研究所在學學生（大二、碩二以上），前一學期學業成績全班前 50% 為原則且操行 80 分以上，報名繳交 NT$3,000 行政處理費，交換期間繳交真理大學全額學雜費且每學期修習至少 9 學分；日本交換組要求三年內通過 JLPT N2 以上（日本多摩大學可憑 JLPT N2 或 TOEIC 600 申請）。（2）合作姐妹校與雙聯學位：完整收錄 80 所全球及兩岸港澳有效締約姐妹校（橫跨 14 國與地區，含 31 所當期開放申請之出國交換與雙聯學位合作校，涵蓋英國密德薩斯大學、英國西英格蘭大學 UWE Bristol 及西班牙赫羅納大學觀光學院 EUHT StPOL 雙聯學制）。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺／惜珠／築夢／新南向學海築夢》、《真理大學交換學生出國獎學金辦法（P-01-510）》、《外國語言遊學獎助學金（P-01-509）》、《國際志工服務獎助學金（P-01-513）》、《特殊貢獻獎助學金（P-01-526）》及 14 所合作大學共 88 篇歷屆學長姐返國交換心得報告。",
    support_level="full",
    partner_count_hint=80,
    academic_score_minimum=60,
    student_card_signals=(
        "真理大學",
        "真理",
        "ALETHEIAUNIVERSITY",
        "ALETHEIA",
        "AU",
    ),
    # https://www.au.edu.tw/ — checked 2026-11-03.
    colleges=(
        "人文學院",
        "觀光休閒與運動學院",
        "管理與資訊學院",
        "財經學院",
        "通識教育中心",
    ),
)


KNU = UniversityProfile(
    id="knu",
    school_name="開南大學",
    short_name="開南",
    english_name="Kainan University",
    aliases=(
        "knu",
        "開南大學",
        "開南",
        "KNU",
        "Kainan University",
    ),
    hero_image="/static/assets/knu-campus.svg",
    official_url="https://knuoica.knu.edu.tw/p/406-1004-59525,r30.php?Lang=zh-tw",
    coverage_note="完整支援：已整合開南大學國際及兩岸事務處（OICA）《海外交換、日本交換、大陸交換與跨國雙聯學位簡章》、《全球姊妹校名冊（88校）》、《開南大學與境外大學校院辦理跨國雙學位制實施辦法》、《開南大學選派優秀學生赴國外研修獎助學金執行要點》及《海外研修與雙聯學位學生心得專區（43校121篇）》官方資料：（1）兩階段校內甄選、學業與語言門檻：每年分兩梯次（秋季班 9～10 月初、春季班 2～3 月中旬；大陸交換秋季班 3～4 月、春季班 10～11 月）辦理甄選，限大學部日間部及進修學士班 1～3 年級、碩士班 1 年級在學學生（轉學生須於本校就讀滿一學年；不含碩士在職專班及應屆畢業生），一般海外、日本及大陸交換歷年每學期學業平均達 75 分（GPA 2.75）以上，雙聯學位（富山、札幌國際、威斯康辛河瀑）與教育部學海系列獎學金須達 80 分（GPA 3.0）以上且操行成績達 82 分以上（佛羅倫斯美國大學 AUF 雙聯門檻為 GPA 2.5）；語言能力須達英語組 TOEIC 500 / IELTS 4.5 / TOEFL iBT 61 / ITP 500（日本全英授課須 TOEIC 600 / IELTS 5.0，AIU 須 TOEIC 785 / iBT 71）、日語組 JLPT N3～N1（島根、德島、愛媛、弘前、山口、名櫻、神戶國際、星城可 N3，多數國立與私立名校須 N2，御茶水女子大學及富山雙聯須 N1）或韓語組 TOPIK 3 級（大陸交換免附外語檢定）；採第一階段書面審查與第二階段面試。（2）全球 15 國／地區 88 所姊妹校與 5 校跨國雙聯學位：完整收錄 70 所常態開放交換與雙聯學校及 18 所學術合作姊妹校，日本高達 42 校（含御茶水女子大學、奈良女子大學、東京海洋大學、富山大學、弘前大學、山形大學、島根大學、山口大學、香川大學、愛媛大學、德島大學、琉球大學等 12 所日本國立大學及秋田國際教養大學 AIU、北九州市立大學、名櫻大學、尾道市立大學等 6 所公立名校），並提供日本國立富山大學（2+2 雙學士，免繳日方學費！）、日本札幌國際大學（2+2／1+1 雙學士）、美國威斯康辛大學河瀑分校 UW-River Falls（2+2 雙學士）、美國密蘇里科技大學 Missouri S&T（3+1.5 學碩雙聯）及義大利佛羅倫斯美國大學 AUF（2+2／3+1 雙學士，觀光餐旅直抵 69 學分且首學期減免學費）等 5 校雙聯學位。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺／惜珠》、《開南大學選派優秀學生赴國外研修獎助學金》及 43 所合作大學共 121 篇歷屆學長姐出國交換與雙聯研修心得報告。",
    support_level="full",
    partner_count_hint=88,
    academic_score_minimum=75.0,
    student_card_signals=(
        "開南大學",
        "KAINANUNIVERSITY",
        "KAINAN UNIVERSITY",
        "KNU",
    ),
    # https://www.knu.edu.tw/ — checked 2026-11-03.
    colleges=(
        "商學院",
        "觀光運輸學院",
        "資訊媒體學院",
        "人文社會學院",
        "健康照護管理學院",
        "法律學院",
    ),
)


NUTN = UniversityProfile(
    id="nutn",
    school_name="國立臺南大學",
    short_name="南大",
    english_name="National University of Tainan",
    aliases=(
        "nutn",
        "國立臺南大學",
        "國立台南大學",
        "臺南大學",
        "台南大學",
        "南大",
        "國立臺南師範學院",
        "臺南師範學院",
        "南師",
        "NUTN",
        "National University of Tainan",
    ),
    hero_image="/static/assets/nutn-campus.svg",
    official_url="https://oia.nutn.edu.tw/?page_id=971",
    coverage_note="完整支援：已整合國立臺南大學國際事務處國際事務組（OIA，府城校區誠正大樓 3 樓 B302 室）《116學年度出國交換學生甄選簡章》、《115學年度第1、2學期出國交換學生甄選簡章》、《2026-2027美國天普大學（Temple University）3+2學碩雙聯學位申請公告與Fact Sheet》、《四大洲締約姊妹校名錄（114校）》、《國立臺南大學選送學生出國研修辦法》、《國立臺南大學選送優秀學生出國研修獎學金審查作業要點》、《高教深耕計畫補助學生赴國外進行國際交流實施要點》、《學生進行國外教育見習教育實習及國際史懷哲計畫要點》與《海外教育計畫網站（ESA）暨南大新聞電子報海外交流報導（33校49篇）》官方資料：（1）兩梯次校內甄選、100%書面審查與全班前50%獎學金同步核定機制：每年分兩梯次（第1梯次11月15日至11月30日受理次學年度秋季班／全學年交換、第2梯次4月1日至4月20日受理當學年度春季班交換）於海外教育計畫網站（ESA）線上填報並送交紙本至B302室，限大學部一年級（含）以上、碩博士班一年級（含）以上之在學學生（含進修部；出國就讀時須在本校就讀至少一學期，修業年限內限交換一次，下學年將順利畢業者不得申請）；採100%書面審查（在校成績及名次百分比、外語檢定證明、1,000–1,500字中文自傳與讀書計畫、最多5項優良表現，至多填3志願），凡在校學業成績平均達全班前50%且具CEFR B1以上外語證明者，無須另備文件即由甄選委員會一併審查校內交換生獎學金及教育部學海飛颺／惜珠獎學金。（2）全球19國／地區114所合作姊妹校與美國天普大學3+2雙聯學位：完整收錄25所最新簡章開放申請之交換與雙聯合作校及89所正式締約姊妹校，日本涵蓋大阪公立大學、北海道大學、岡山大學、埼玉大學、長崎大學、順天堂大學（N2或iBT 72）及獨協大學、金澤星稜大學（日語密集課程JLPT N5即可申請！），韓國東國、崇實、天主教關東、德成女子大學與捷克赫拉德茨克拉洛韋大學、波蘭歐波蘭大學採計英語CEFR B1（TOEIC 550 / iBT 42 / IELTS 4.0）或TOPIK 3級，美國中央阿肯色大學UCA（iBT 79，音樂系可附個人演奏曲目免英檢！）、奧特本大學、密蘇里大學堪薩斯分校UMKC及美國天普大學（Temple University）3+2學碩雙聯學位（DBMD，大三以上GPA 3.0、免GRE、享最高USD 10,000獎學金）。（3）四大獎助學金體系與海外實踐報導：涵蓋《校內交換學生獎學金》（亞洲每學期最高NT$25,000、非亞洲每學期最高NT$40,000）、教育部《學海飛颺／學海惜珠／學海築夢／新南向學海築夢》、《高教深耕國際交流與公開展演競試補助》（最高NT$30,000）及《國外教育見習與國際史懷哲計畫》，並收錄33所合作大學共49篇歷屆海外交流報導與研修指南。",
    support_level="full",
    partner_count_hint=114,
    academic_score_minimum=75.0,
    student_card_signals=(
        "國立臺南大學",
        "國立台南大學",
        "臺南大學",
        "台南大學",
        "南大",
        "NATIONALUNIVERSITYOFTAINAN",
        "NATIONAL UNIVERSITY OF TAINAN",
        "NUTN",
    ),
    # https://www.nutn.edu.tw/teaching.html — checked 2026-11-06.
    colleges=(
        "教育學院",
        "人文學院",
        "理工學院",
        "環境與生態學院",
        "藝術學院",
        "管理學院",
    ),
)


NIU = UniversityProfile(
    id="niu",
    school_name="國立宜蘭大學",
    short_name="宜大",
    english_name="National Ilan University",
    aliases=(
        "niu",
        "國立宜蘭大學",
        "宜蘭大學",
        "宜大",
        "國立宜蘭技術學院",
        "國立宜蘭農工專科學校",
        "宜蘭農專",
        "宜蘭農校",
        "NIU",
        "National Ilan University",
    ),
    hero_image="/static/assets/niu-campus.svg",
    official_url="https://oia.niu.edu.tw/p/404-1014-9618.php",
    coverage_note="完整支援：已整合國立宜蘭大學國際事務處（OIA，行政大樓 5 樓）《學生赴境外研習暨交換申請資訊簡章》、《美國密西根大學迪爾伯恩分校 UM-Dearborn 3+2／1+1 雙聯學位專頁》、《學生境外學習手冊（Students Go Global Guidebook）》、《四大洲及大陸地區締約姊妹校名錄（97校）》、《國立宜蘭大學學生赴境外研修甄選作業要點》、《國立宜蘭大學與境外大學辦理雙聯學制實施辦法》、《國立宜蘭大學學生赴境外研修獎補助要點》、《國立宜蘭大學學海系列方案甄選及補助要點》與《國立宜蘭大學學生參與國際性活動獎補助要點》官方資料：（1）兩梯次校內甄選、大學部全班前 60%／研究生 75 分門檻與每學期 4 學分或 2 門課規定：每年分兩梯次（秋季班 2 月初至 3 月底、春季班 9 月初至 10 月底）受理次學期赴境外（含大陸）交換甄選，限具本校學籍之日間學制學生（非中華民國籍學生不得交換至原屬國家），大學部前一學期學業成績須為全班前 60%、研究生學業成績平均達 75 分以上，且前一學期操行成績達 75 分以上無重大違紀事件；外語能力依各姊妹校規定（英語組 TOEIC 500–785 / IELTS 5.0–6.0 / TOEFL iBT 70–80、日語組 JLPT N5–N1、韓語組 TOPIK 3 級、大陸地區免外語檢定）；交換期間繳交宜大學雜費、免繳姊妹校學雜費，每學期至少修讀 4 學分或 2 門課程，抵達姊妹校 14 天內回報國外聯絡方式，返國後 1 個月內繳交至少 3 頁中文心得報告電子檔並配合經驗分享會及接待來校交換生。（2）全球 19 國／地區 97 所合作姊妹校與 9 校跨國雙聯學位：完整收錄 84 所常態開放申請之交換、雙聯與自費研修合作校及 13 所正式締約姊妹校，涵蓋美國密西根大學迪爾伯恩分校（UM-Dearborn 3+2 學碩／1+1 雙碩士，GPA 3.0、iBT 80–84 / IELTS 6.5，享本州生 1.2 倍學費減免）、美國伊利諾大學香檳分校（UIUC 環工／化材雙聯）、加拿大英屬哥倫比亞大學（UBC 森資系 2+2 雙學士）、瑞士 SHMS 瑞士酒店管理大學與 César Ritz 凱撒里茲酒店管理大學（休健系 3+1／2+1+1／3+2 雙聯含 4–6 個月有薪實習）、印尼日惹大學（UGM 雙聯）與阿瑪加雅大學（UAJY 建研所 1+1 雙碩士）、越南胡志明市理工大學（HCMUT 化工雙聯）及大陸福州大學（經管學院 1+1 雙碩士）等 9 校雙聯學位。（3）四大獎助學金體系與返國心得：涵蓋教育部《學海飛颺／學海惜珠》（大學部前 40%、研究生 80 分以上，補助 NT$50,000–450,000）、《學海築夢／新南向學海築夢》、《校內學生赴境外研修獎補助》（歐美非最高 NT$30,000、紐澳 NT$25,000、亞洲 NT$15,000、大陸港澳 NT$10,000，另加重點學校獎助 NT$3,000–5,000 與語文成績獎助最高 NT$4,000）及《參與國際性活動獎補助》，並收錄 22 所合作大學共 38 篇歷屆學長姐出國交換與雙聯學位心得分享紀錄。",
    support_level="full",
    partner_count_hint=97,
    academic_score_minimum=75.0,
    student_card_signals=(
        "國立宜蘭大學",
        "宜蘭大學",
        "宜大",
        "NATIONALILANUNIVERSITY",
        "NATIONAL ILAN UNIVERSITY",
        "NIU",
    ),
    # https://www.niu.edu.tw/p/412-1000-84.php?Lang=zh-tw — checked 2026-11-05.
    colleges=(
        "人文及管理學院",
        "工學院",
        "生物資源學院",
        "電機資訊學院",
        "博雅學部",
    ),
)


NPTU = UniversityProfile(
    id="nptu",
    school_name="國立屏東大學",
    short_name="屏大",
    english_name="National Pingtung University",
    aliases=(
        "nptu",
        "國立屏東大學",
        "屏東大學",
        "屏大",
        "國立屏東教育大學",
        "屏東教育大學",
        "屏教大",
        "國立屏東商業技術學院",
        "屏東商業技術學院",
        "屏商技",
        "屏商",
        "屏師",
        "NPTU",
        "National Pingtung University",
    ),
    hero_image="/static/assets/nptu-campus.svg",
    official_url="https://ccd.nptu.edu.tw/p/412-1091-12234.php?Lang=zh-tw",
    coverage_note="完整支援：已整合國立屏東大學國際事務處（OIA，下設國際合作組與大陸事務組）《115年出國交換甄選簡章》、《116學年度出國交換／實習三校區說明會公告（2026/12/08–12/10，報名至 11/30 17:00）》、《115年第1次教育部學海築夢及新南向學海築夢甄選簡章》、《跨國雙聯學位專區（英、美、捷、日、泰 7 校）》、《學生出國有關學業及學籍處理要點（114.03.27修正）》、《與境外大學校院辦理雙聯學制實施辦法（114.05.22修正）》、《學生抵免學分要點（115.10.22修正）》、《與外國學制學分轉換準則》、《學海計畫學生生活費核銷支給數額標準表》及《出國交換學生心得分享專區（20校61篇）》官方資料：（1）四大推薦計畫、語檢門檻與雙軌送件：每年 12 月舉辦三校區說明會、1–2 月收件、2 月下旬 17:00 截止、3 月初面試，分為【教育部學海飛颺】（本國籍就讀滿一學期一般生、歷年成績班排前 50% 內、操行平均 80 分以上且無申誡以上處分）、【教育部學海惜珠】（同飛颺條件並具低收／中低收／特殊境遇／身障等資格）、【本校「菁英育才」補助（校友捐款）】（無班排前 50% 限制，惟「每學期」操行皆須達 80 分以上，補助生活費每月 NT$10,000 最高 5 個月＋機票費最高 NT$30,000，合計最高 NT$80,000）及【自費交換】（含在職生與進修生）；非日語組須達 CEFR B1（TOEIC 550 / TOEFL iBT 42 / ITP 460 / IELTS 4.0 / GEPT 中級初試），日語組須達 JLPT N2（校內甄選時得先以非日語 B1＋師長簽署《日本語力評價表》替代）；至多填寫 5 所志願學校，紙本送交屏商行政大樓 3F 國際合作組並將合併 PDF 寄至 vida2022@mail.nptu.edu.tw；交換期間於屏大完成註冊且大學部每學期至少修 1 門課（姬路獨協大學須修 7 門課以上），返國次學期期末考前一次辦理學分抵免（1 NPTU＝2 ECTS＝4 CATS＝4 澳洲學分）。（2）全球 24 國／地區 172 所合作姊妹校與 7 校跨國雙聯學位：完整收錄 41 所常態開放申請之交換與雙聯合作校（含日本宮崎大學、弘前大學、大阪教育大學、兵庫教育大學、室蘭工業大學、和歌山大學、鹿兒島大學、香川大學、山形大學、信州大學等 10 所日本國立大學與麗澤、姬路獨協、廣島修道、山陽學園、日本經濟大學，捷克 UHK 10 名、TBU、TUL、CTU，德國 ASH Berlin，義大利帕維亞大學，韓國外國語大學 HUFS，馬來亞大學 UM，以及泰國程逸皇家大學等 4 校「免學費＋免住宿費」優惠）及英國密德薩斯大學（3+1／1+1）、美國北阿拉巴馬大學（3+1／2+2／1+1）、美國西來大學（2+2／1+1）、捷克 UHK（1+1）、捷克 TBU（1+1）、泰國宋卡王子大學（2+2）、泰國蒙庫國王科技大學 KMUTT（1+1）等 7 校雙聯學位。（3）返國心得：完整收錄 20 所合作大學共 61 篇歷屆學長姐出國交換與海外研修心得報告。",
    support_level="full",
    partner_count_hint=172,
    academic_score_minimum=60.0,
    student_card_signals=(
        "國立屏東大學",
        "屏東大學",
        "NATIONALPINGTUNGUNIVERSITY",
        "NATIONAL PINGTUNG UNIVERSITY",
        "NPTU",
    ),
    # https://www.nptu.edu.tw/p/412-1000-2972.php?Lang=zh-tw — checked 2026-11-05.
    colleges=(
        "管理學院",
        "資訊學院",
        "教育學院",
        "人文社會學院",
        "理學院",
        "國際學院",
        "大武山學院",
    ),
)


NPU = UniversityProfile(
    id="npu",
    school_name="國立澎湖科技大學",
    short_name="澎科大",
    english_name="National Penghu University of Science and Technology",
    aliases=(
        "npu",
        "國立澎湖科技大學",
        "澎湖科技大學",
        "澎科大",
        "澎湖科大",
        "NPU",
        "National Penghu University of Science and Technology",
    ),
    hero_image="/static/assets/npu-campus.svg",
    official_url="https://www.npu.edu.tw/content.aspx?id=273",
    coverage_note="完整支援：已整合國立澎湖科技大學研究發展處國際事務組（ORD International Affairs Section）《交換學生赴國外（含大陸地區）姊妹校就讀選薦辦法（108.09.19修正通過）》、《辦理教育部鼓勵大專校院選送學生出國研修（學海飛颺、學海惜珠）審查要點（115.03.25通過）》、《辦理教育部鼓勵大專校院選送學生國外專業實習（學海築夢、新南向學海築夢）審查要點（115.03.25通過）》、《獎助學生境外研修及參訪辦法（108.12.19修正通過）》、《辦理雙聯學制實施辦法（104.11.30教育部備查）》、《國際合作姊妹校一覽表》、《與本校簽訂學生交流協議書清冊》及各姊妹校交換入學簡章官方資料：（1）兩梯次校內選薦、40%/40%/20% 量化評分與系務會議課程認可規定：每年分秋季班（3月1日至3月31日校內收件，5月15日／5月30日前向姊妹校完成提名）與春季班（9月1日至9月30日校內收件，11月15日／11月30日前向姊妹校完成提名）辦理出國交換甄選，並於每年 2–3 月辦理教育部學海系列計畫校內甄選；限已就讀本校一學期以上且非當學期畢業之在學學生（含四技、二技、五專部專四及專五、碩士班，不含國內及境外在職專班生），擬進修課程須先檢附所屬系所課程委員會或系務會議同意之會議紀錄；由研發長召集教務長及各學院委員組成「學術合作審查小組」，依「在校成績 40%、語文能力 40%、讀書計畫 20%」評分，總分達 70 分（含）以上始得由校長名義寄發推薦函；外語能力須符合交換學校或本校自訂標準（英文 TOEIC 550 / IELTS 4.0 / TOEFL ITP 457 / iBT 42，日文 JLPT N4 / J.TEST E 級；學海築夢實習為 TOEIC 400 / GEPT 中級 / JLPT N4 且操行平均 80 分以上；大陸地區交換免附外語能力證明）。（2）全球與大陸 12 國／地區 37 所高等教育合作姊妹校與 3 校跨國雙聯學位：完整收錄 18 所簽署學生交流協議與雙聯學位之常態開放申請學校（日本國立琉球大學、馬來西亞拉曼大學 UTAR、越南峴港大學、越南孫德勝大學、泰國湄州大學、泰國朱拉隆功大學、菲律賓甲米地州立大學、美國匹茲堡州立大學，以及大陸中國海洋大學、上海海洋大學、浙江海洋大學、集美大學、汕頭大學、龍岩學院、浙江越秀外國語學院、黎明職業大學、廣州航海學院、深圳職業技術大學）與 19 所學術合作備忘錄（MOU）姊妹校（含日本長崎大學、菲律賓大學系統、印尼亞齊大學、瑞士教育集團 SEG、馬紹爾群島學院、貝里斯大學等），並提供美國匹茲堡州立大學（2+2 雙學士）、越南孫德勝大學（觀休、海運雙聯學士）及泰國湄州大學（雙聯學位）跨國雙聯通道（學士累計修業滿 32 個月、碩士滿 12 個月）。（3）獎助學金與研修指南：涵蓋教育部《學海飛颺／學海惜珠》（每人平均獎助 NT$ 50,000–300,000，含本校 20% 配合款）、《學海築夢／新南向學海築夢》、校內《獎助學生境外研修及參訪辦法》（每人補助 NT$ 5,000–15,000）及 13 所合作大學共 13 篇海外研修指南與交流紀錄。",
    support_level="full",
    partner_count_hint=37,
    academic_score_minimum=70.0,
    student_card_signals=(
        "國立澎湖科技大學",
        "澎湖科技大學",
        "澎科大",
        "NATIONALPENGHUUNIVERSITYOFSCIENCEANDTECHNOLOGY",
        "NATIONAL PENGHU UNIVERSITY OF SCIENCE AND TECHNOLOGY",
        "NPU",
    ),
    # https://www.npu.edu.tw/submenu.aspx?id=149 — checked 2026-11-06.
    colleges=(
        "海洋資源暨工程學院",
        "觀光休閒學院",
        "人文暨管理學院",
        "博雅教育學院",
    ),
)


NTUNHS = UniversityProfile(
    id="ntunhs",
    school_name="國立臺北護理健康大學",
    short_name="國北護",
    english_name="National Taipei University of Nursing and Health Sciences",
    aliases=(
        "ntunhs",
        "國立臺北護理健康大學",
        "國立台北護理健康大學",
        "臺北護理健康大學",
        "台北護理健康大學",
        "國北護",
        "北護",
        "北護大",
        "國立臺北護理學院",
        "NTUNHS",
        "National Taipei University of Nursing and Health Sciences",
    ),
    hero_image="/static/assets/ntunhs-campus.svg",
    official_url="https://icsed-rnd.ntunhs.edu.tw/",
    coverage_note="完整支援：已整合國立臺北護理健康大學研究發展處國際暨兩岸教育中心《雙聯學制專區（英美澳6校9學程）》、《海外長短期交換專區》、《教育部學海飛颺／惜珠／築夢專區》、《五大洲締約姊妹校名錄（84校）》、《學生出國期間有關學業及學籍處理要點（112.11.01修正）》、《學生抵免學分處理辦法（115.06.24修正）》及《歷屆雙聯、交換與海外實習心得報告（24校33篇）》官方資料：（1）校內甄選資格、臨床實習同意與在學註冊規定：限日間部四技（2～4年級）、二技、學士後護理系、碩士班及博士班在學學生（不含在職專班），在校歷年平均達 GPA 2.0（百分制 70 分）以上，申請教育部學海飛颺／惜珠獎學金以班排前 50% 及操行 80 分以上無懲戒紀錄優先；因考量各系專業必修與醫院臨床實習排程，交換生及雙聯生皆須經所屬系所同意始得出國，出國進修以二年為限且交換期間須維持北護在學註冊學籍（不得休學）；校內甄選採書面審查（40%–60%，曾任國際學伴 International Buddy 者加分）與中英文面試（40%–60%）。（2）全球 21 國／地區 84 所合作姊妹校與英美澳 6 校 9 學程雙聯學位：完整收錄 37 所常態開放雙聯、長短期交換與海外實習合作校及 47 所五大洲締約姊妹校，涵蓋澳洲昆士蘭大學 UQ（護理雙學士／護理碩士／聽力學碩士／社工碩士雙聯，IELTS 7.0）、美國奧本大學 Auburn（護理 MSN 碩士暨 PhD 博士雙聯，IELTS 6.5）、英國西英格蘭大學 UWE（護理雙學士 IELTS 6.5、資管 3+1 雙學士 IELTS 6.0）、澳洲昆士蘭科技大學 QUT（資管 2+2 雙學士 IELTS 6.5）、澳洲迪肯大學 Deakin（健管 3.5+1.5 MBA 醫療管理雙聯 IELTS 6.5）及澳洲墨爾本威廉安格利斯學院 WAI（休健航空空服／旅遊管理雙聯 IELTS 6.0），以及捷克奧斯特拉瓦大學醫學院、立陶宛 KVK、日本名古屋市立大學、縣立廣島大學、東京都立大學 HIIP（免費荒川校區宿舍）、紐西蘭梅西大學、韓國大邱保健大學（免費雙人房宿舍）等。（3）獎助學金與返國心得：涵蓋教育部《學海飛颺／惜珠／築夢／新南向學海築夢》及 24 所合作大學共 33 篇歷屆學長姐心得報告。",
    support_level="full",
    partner_count_hint=84,
    academic_score_minimum=70.0,
    student_card_signals=(
        "國立臺北護理健康大學",
        "國立台北護理健康大學",
        "國北護",
        "NATIONALTAIPEIUNIVERSITYOFNURSINGANDHEALTHSCIENCES",
        "NATIONAL TAIPEI UNIVERSITY OF NURSING AND HEALTH SCIENCES",
        "NTUNHS",
    ),
    # https://www.ntunhs.edu.tw/ — checked 2026-11-06.
    colleges=(
        "護理學院",
        "健康科技學院",
        "人類發展與健康學院",
        "智慧健康照護跨領域學院",
    ),
)


NTTU = UniversityProfile(
    id="nttu",
    school_name="國立臺東大學",
    short_name="東大",
    english_name="National Taitung University",
    aliases=(
        "nttu",
        "國立臺東大學",
        "國立台東大學",
        "臺東大學",
        "台東大學",
        "東大",
        "NTTU",
        "National Taitung University",
    ),
    hero_image="/static/assets/nttu-campus.svg",
    official_url="https://rd.nttu.edu.tw/p/412-1007-9902.php?Lang=zh-tw",
    coverage_note="完整支援：已整合國立臺東大學研究發展處國際事務中心（COIA）《2025–2027 赴境外姊妹校交換生暨雙聯學位甄選簡章與名額一覽表》、《國際暨大陸地區締約姊妹校名錄（59校）》、《辦理學生申請出國進修或交換作業要點》、《學生出國進修獎助學金要點（含附件一 CEFR B1/B2 語言基準表）》、《與境外大學校院辦理雙聯學制實施辦法》、《學生出國期間有關學業及學籍處理辦法》、《學生抵免學分要點》及《出國交換生暨學海築夢心得分享專區（12校58篇）》官方資料：（1）校內甄選時程、在學資格與評分權重：每學期分兩梯次（春季班於前一年 9 月中旬截止，如 2027 春季班於 2026/09/15 中午 12:00 截止、10/15 放榜；秋季班於當年 3 月中旬截止，如 2026 秋季班於 2026/03/20 中午 12:00 截止）受理報名，限本校二年級（含）以上之在學學位生（含學士班大二至大四、碩士班、博士班；不含大一新生、當學期畢業生、延畢生及在職專班學生；大四申請交換以一學期為限），採「書面資料審查 50%＋面試（含外語口試）50%」擇優錄取。（2）全球 15 國／地區 59 所合作姊妹校與日本 2 校跨國雙聯學士學位：完整收錄 15 所當期開放申請之國際與大陸重點交換及雙聯姊妹校（含美國加州西來大學［每期 15 名，至多 12 學分學費半價減免］、日本仙台大學［交換 4–6 名＋2.5+2 雙聯學士 2 名］、日本琵琶湖成蹊體育運動大學［春季班 1.5+2+1 雙聯學士 1 名］、日本天理大學［1 名，免學費、免宿舍費且免水電瓦斯費！］、韓國國立順天大學［2–4 名，免韓檢］、韓國高神大學［1–2 名，免韓檢］、韓國釜山教育大學［3 名，TOPIK 2 級］、捷克茲林托馬斯巴塔大學［5 名，CEFR B2，保證提供低廉宿舍］，以及大陸華東師範大學、蘭州大學、華中師範大學、西南大學、東北師範大學、中央民族大學、鄭州大學等 7 所 985/211 重點名校）及 44 所正式締約姊妹校。（3）最高 30 萬元出國進修獎助學金與教育部學海計畫：涵蓋校內《學生出國進修獎助學金》（攻讀雙聯學位或交換生每人每年最高補助 NT$300,000、短期修讀學分最高 NT$80,000、短期語言進修最高 NT$20,000；學士班須各學期班排前 50% 且具 CEFR B1 外語證明，碩博士班須系所推薦且具 CEFR B2 外語證明）、教育部《學海飛颺》、《學海惜珠》、《學海築夢／新南向學海築夢》及 12 所合作大學共 58 篇歷屆學長姐交換、雙聯與海外實習心得報告。",
    support_level="full",
    partner_count_hint=59,
    academic_score_minimum=70.0,
    student_card_signals=(
        "國立臺東大學",
        "國立台東大學",
        "臺東大學",
        "台東大學",
        "NATIONALTAITUNGUNIVERSITY",
        "NATIONAL TAITUNG UNIVERSITY",
        "NTTU",
    ),
    # https://www.nttu.edu.tw/p/412-1000-1495.php?Lang=zh-tw — checked 2026-11-06.
    colleges=(
        "人文學院",
        "師範學院",
        "理工學院",
        "跨領域學位學程",
    ),
)


SUPPORTED_UNIVERSITIES = (CGU, NTPU, NTU, CCU, NCU, TKU, FJU, SCU, NTNU, CYCU, NTUST, YZU, FCU, NSYSU, NCHU, NTUT, NCCU, NCKU, NYCU, NTHU, PCCU, WZU, NKUST, YUNTECH, NTOU, NCUE, NKNU, TMU, CSMU, CMU, KMU, MCU, NTUB, NCNU, NDHU, THU, SHU, PU, USC, NUK, NCYU, NUTC, NFU, UTAIPEI, NTCU, TNUA, NTUA, NTUE, NCUT, NPUST, CJCU, NQU, ISU, FGU, NKUHT, NUU, TNNUA, TPCU, AU, KNU, NUTN, NIU, NPTU, NPU, NTUNHS, NTTU)
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
