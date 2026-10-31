"""Cross-school foreign partner university pages (/partners/{country}/{institution}).

Implements Action 2 (【築護城河】打造跨校外國大學頁):
- Shared entity keyed by (canonical country + foreign institution identity) across all supported
  Taiwanese home universities.
- Two-layer page architecture:
  1. Upper Layer (母校規則層): Switch between any Taiwanese home university (NTU, NCCU, NTNU, CGU, etc.)
     to inspect current-round quota, language threshold, eligibility, and verified internal deadlines
     with mandatory official HTTPS source links and last-checked dates.
  2. Lower Layer (全台跨校情報層): Aggregates cross-school intelligence across all contracting Taiwanese
     universities, structured into:
     - 全台締約大學清單與各校門檻對照
     - 跨校生活費參考
     - 住宿資訊與申請提醒
     - 學長姐曾修過的課程方向與跨校公開經驗摘要
- Strict copyright compliance: Never copies or republishes full student essays or raw PDF paragraphs;
  every item is a concise, self-written structured summary in Traditional Chinese accompanied by its
  official or public source URL and last-checked date.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass, field
from html import escape
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote, urlencode

from .destination_tips import canonical_country
from .experience_digests import _load as load_bundled_experience_digests
from .models import (
    CatalogueSourceStatus,
    CrossSchoolConversionHooks,
    CrossSchoolHomeAgreement,
    CrossSchoolPartnerDirectory,
    CrossSchoolPartnerPageData,
    CrossSchoolPartnerSummaryItem,
    CrossSchoolStructuredPoint,
    PartnerUniversity,
    SourceReference,
)
from .school_identity import school_identity_key
from .staged_network_effects import (
    build_admitted_student_connect_hub,
    build_partner_specific_preference_heat,
    render_admitted_student_connect_lower_html,
    render_partner_network_effects_upper_html,
)
from .university_registry import SUPPORTED_UNIVERSITIES, UniversityProfile, resolve_university
from .verified_window_deadlines import get_verified_school_window_card

COPYRIGHT_COMPLIANCE_NOTICE = (
    "【著作權與資料合規聲明】本頁所有跨校生活費、住宿、修課方向與學長姐經驗皆由 UniWay 以自有結構化方式重新整理重點摘要，"
    "絕不轉載、不複製學長姐心得全文或各校簡章 PDF 原文；摘要附來源連結及核對狀態；尚待核實的內容會明確標示。請點擊原出處確認完整條件與適用學期。"
)

AVAILABILITY_LABELS: dict[str, str] = {
    "open": "當期名單列載（請確認母校受理時窗）",
    "agreement_only": "締約合作校參考（非當期開放名額）",
    "departmental_reference": "院系級合作參考",
    "not_open": "本期未開放",
    "needs_confirmation": "名額與開放狀態待確認",
    "zero_quota": "本期零名額",
    "fee_paying": "自費研修方案",
    "closed": "本期已截止",
    "reference_only": "歷史／參考資料",
    "quota_unconfirmed": "本期名額待確認",
    "not_contracted": "此母校目前未列載此合作校",
}

COUNTRY_SLUGS: dict[str, str] = {
    "日本": "japan",
    "韓國": "south-korea",
    "德國": "germany",
    "美國": "united-states",
    "英國": "united-kingdom",
    "法國": "france",
    "大陸地區": "mainland-china",
    "香港": "hong-kong",
    "新加坡": "singapore",
    "加拿大": "canada",
    "澳洲": "australia",
    "荷蘭": "netherlands",
    "瑞士": "switzerland",
    "瑞典": "sweden",
    "西班牙": "spain",
    "義大利": "italy",
    "奧地利": "austria",
    "比利時": "belgium",
    "波蘭": "poland",
    "捷克": "czechia",
    "馬來西亞": "malaysia",
    "泰國": "thailand",
    "越南": "vietnam",
    "紐西蘭": "new-zealand",
    "芬蘭": "finland",
    "丹麥": "denmark",
    "挪威": "norway",
    "愛爾蘭": "ireland",
    "葡萄牙": "portugal",
    "匈牙利": "hungary",
    "土耳其": "turkey",
    "俄羅斯": "russia",
    "印度": "india",
    "印尼": "indonesia",
    "菲律賓": "philippines",
    "墨西哥": "mexico",
    "巴西": "brazil",
    "立陶宛": "lithuania",
    "拉脫維亞": "latvia",
    "羅馬尼亞": "romania",
    "斯洛伐克": "slovakia",
    "哈薩克": "kazakhstan",
    "蒙古": "mongolia",
    "緬甸": "myanmar",
    "摩洛哥": "morocco",
    "柬埔寨": "cambodia",
    "智利": "chile",
    "以色列": "israel",
    "澳門": "macau",
    "冰島": "iceland",
    "愛沙尼亞": "estonia",
    "阿拉伯聯合大公國": "united-arab-emirates",
    "希臘": "greece",
    "秘魯": "peru",
    "巴基斯坦": "pakistan",
    "烏茲別克": "uzbekistan",
    "哥倫比亞": "colombia",
    "斯洛維尼亞": "slovenia",
    "多明尼加": "dominican-republic",
    "巴拿馬": "panama",
    "巴哈馬": "bahamas",
    "馬拉威": "malawi",
    "阿根廷": "argentina",
    "瓜地馬拉": "guatemala",
    "迦納": "ghana",
    "阿爾巴尼亞": "albania",
    "巴布亞紐幾內亞": "papua-new-guinea",
    "聖克里斯多福及尼維斯": "saint-kitts-and-nevis",
    "南非": "south-africa",
    "索羅門群島": "solomon-islands",
    "法屬玻里尼西亞": "french-polynesia",
    "伊朗": "iran",
    "埃及": "egypt",
    "克羅埃西亞": "croatia",
    "約旦": "jordan",
    "科索沃": "kosovo",
    "哥斯大黎加": "costa-rica",
    "肯亞": "kenya",
    "辛巴威": "zimbabwe",
    "汶萊": "brunei",
    "安道爾": "andorra",
    "史瓦帝尼": "eswatini",
    "奈及利亞": "nigeria",
    "烏克蘭": "ukraine",
    "列支敦士登": "liechtenstein",
    "巴拉圭": "paraguay",
    "摩納哥": "monaco",
    "烏拉圭": "uruguay",
    "阿曼": "oman",
    "賽普勒斯": "cyprus",
    "尼泊爾": "nepal",
    "台灣": "taiwan",
    "孟加拉": "bangladesh",
    "安地卡及巴布達": "antigua-and-barbuda",
    "斯里蘭卡": "sri-lanka",
    "盧森堡": "luxembourg",
    "厄瓜多": "ecuador",
}

SLUG_TO_COUNTRY_ZH: dict[str, str] = {slug: zh for zh, slug in COUNTRY_SLUGS.items()}
SLUG_TO_COUNTRY_ZH.update(
    {
        "korea": "韓國",
        "usa": "美國",
        "us": "美國",
        "uk": "英國",
        "china": "大陸地區",
        "prc": "大陸地區",
        "czech-republic": "捷克",
        "uae": "阿拉伯聯合大公國",
        "macao": "澳門",
        "俄羅斯聯邦": "俄羅斯",
        "russian-federation": "俄羅斯",
        "斯洛法克": "斯洛伐克",
        "列支敦斯登": "列支敦士登",
        "臺灣": "台灣",
    }
)
# Map legacy inst-<12hex> country hashes (generated when a Chinese country name lacked a slug)
# back to their canonical Chinese country names so old URLs can 301-redirect cleanly.
for _country_zh, _canonical_zh in (
    *((_zh, _zh) for _zh in COUNTRY_SLUGS),
    ("俄羅斯聯邦", "俄羅斯"),
    ("斯洛法克", "斯洛伐克"),
    ("列支敦斯登", "列支敦士登"),
    ("臺灣", "台灣"),
):
    _legacy_country_hash = f"inst-{hashlib.sha256(_country_zh.encode('utf-8')).hexdigest()[:12]}"
    SLUG_TO_COUNTRY_ZH.setdefault(_legacy_country_hash, _canonical_zh)

COUNTRY_DEFAULT_CURRENCY_HINT: dict[str, str] = {
    "日本": "每月生活費約 100,000–150,000 日圓（含住宿、伙食與國民健康保險，依城市而異）",
    "韓國": "每月生活費約 800,000–1,300,000 韓元（含宿舍或校外租屋、餐費與交通）",
    "德國": "每月生活費約 950–1,350 歐元（含房租、公立學生醫保與學期交通費，依城市而異）",
    "美國": "每月生活費約 1,400–2,400 美元（含校內外住宿、伙食方案與強制醫療保險）",
    "英國": "每月生活費約 1,100–1,600 英鎊（倫敦地區較高，含住宿、飲食與日常交通）",
    "法國": "每月生活費約 850–1,300 歐元（含 CROUS 或租屋、餐費與交通卡，可查 CAF 房補資格）",
    "大陸地區": "每月生活費約 2,500–4,500 人民幣（校內住宿費相對低廉，主要為伙食與日常支出）",
    "香港": "每月生活費約 7,000–12,000 港幣（校內宿位競爭激烈，校外租屋成本顯著較高）",
    "新加坡": "每月生活費約 1,300–2,200 新幣（視是否抽中校內宿舍或須於校外租屋而定）",
    "加拿大": "每月生活費約 1,400–2,200 加幣（含住宿、飲食、省級或校方醫療保險與冬季衣物）",
    "澳洲": "每月生活費約 1,800–2,600 澳幣（含住宿、飲食、交通與海外學生健康保險 OSHC）",
    "荷蘭": "每月生活費約 1,000–1,400 歐元（荷蘭學生房源極為吃緊，務必於獲提名後立即申請住宿）",
    "瑞士": "每月生活費約 1,600–2,300 瑞士法郎（含學生宿舍、飲食、交通與強制健康保險）",
    "瑞典": "每月生活費約 9,500–12,500 瑞典克朗（含學生房租、飲食與大眾運輸定期票）",
    "西班牙": "每月生活費約 850–1,250 歐元（馬德里與巴塞隆納租屋較高，其他城市相對親民）",
    "義大利": "每月生活費約 850–1,300 歐元（米蘭、羅馬房租較高，須留意稅號 Codice Fiscale 與居留手續）",
    "奧地利": "每月生活費約 950–1,300 歐元（建議透過 OeAD Student Housing 提早登記宿舍）",
    "捷克": "每月生活費約 14,000–22,000 捷克克朗（校內雙人房宿舍費用親民，生活成本相對歐洲西岸低）",
    "波蘭": "每月生活費約 2,500–4,000 波蘭茲羅提（校內宿舍實惠，生活與歐洲跨國交通便利）",
}


@dataclass(frozen=True)
class CuratedInstitutionSpec:
    country_zh: str
    institution_slug: str
    school_name_zh: str
    school_name_en: str
    official_website: str
    match_tokens: tuple[str, ...]
    living_cost_points: tuple[CrossSchoolStructuredPoint, ...] = ()
    housing_points: tuple[CrossSchoolStructuredPoint, ...] = ()
    course_points: tuple[CrossSchoolStructuredPoint, ...] = ()
    experience_points: tuple[CrossSchoolStructuredPoint, ...] = ()


CURATED_SPECS: tuple[CuratedInstitutionSpec, ...] = (
    CuratedInstitutionSpec(
        country_zh="德國",
        institution_slug="technical-university-of-munich",
        school_name_zh="慕尼黑工業大學",
        school_name_en="Technical University of Munich",
        official_website="https://www.tum.de/en/",
        match_tokens=(
            "慕尼黑工業大學",
            "technical university of munich",
            "technische universität münchen",
            "technische universitaet muenchen",
            "tum",
        ),
        living_cost_points=(
            CrossSchoolStructuredPoint(
                category='living_cost',
                title='慕尼黑生活費：官方建議每月至少 1,200 歐元（不含休閒活動）',
                summary_zh='TUM 交換生行前頁建議，在慕尼黑每月至少準備 1,200 歐元，包含房租但不含休閒活動。本摘要為官網一般預算參考，不是個人支出保證或其他校區的統一標準。',
                bullets=['最低生活預算與居留財力證明是不同用途，不應把財力證明門檻當作足夠生活費；本頁不以未註明日期的匯率換算新臺幣。', '住宿費須依房源確認：交換生 Service Package 專頁列月租 400–600 歐元及可退押金 500–900 歐元；並非所有交換生都能取得該房源。', '行前總覽的公營宿舍概估為 300–400 歐元，與 Service Package 專頁的 400–600 歐元不同。兩頁適用房源未完全一致，應以實際分配與合約為準；醫保及學期費另核對身分、校區與當期公告。'],
                origin_label='官方預算參考（校區與房源須核對）',
                source_title='Preparing for your stay at TUM - International exchange students - TUM Global',
                source_url='https://www.global.tum.de/en/global/exchangestudents/general-information-for-international-students/preparing-your-stay/',
                last_checked_at='2026-10-21',
                source_published_at=None,
                verification_status='verified_reference',
                related_sources=[{'title': 'Accommodation service for international exchange students - TUM Global', 'source_url': 'https://www.global.tum.de/en/global/accommodation/', 'category': None, 'summary': None}],
            ),
        ),
        housing_points=(
            CrossSchoolStructuredPoint(
                category='housing',
                title='TUM 交換生住宿：依交換管道與校區申請',
                summary_zh='TUM 本身沒有校內住宿；學生服務機構（Studierendenwerk München Oberbayern）提供的有限宿位優先保留給 TUMexchange。其他交換管道不保證有房，須按自己的計畫與校區查核。',
                bullets=['TUMexchange 指非歐洲大學的校級協議交換，不能僅憑學院級合作判定符合。申請表 Further information 欄仍須表示接受 Service Package 的意願。', 'Erasmus+、學院及其他交換計畫也可表示興趣；有剩餘宿位才依內部程序分配。冬季自七月中、夏季自一月中通知接受或拒絕，不能把排候補當作保證。', '慕尼黑／Garching 與 Freising 的房源依就讀校區安排；Heilbronn、Straubing 應洽各校區窗口。不要把所有宿舍都當成同一校區的通勤選項。', 'Service Package 月租 400–600 歐元、可退押金 500–900 歐元。簽回住宿接受函後須在期限內支付前三個月租金與押金，才能完成保留；勿把一般防詐建議誤作官方宿舍一律不可預付。'],
                origin_label='官方交換生住宿程序參考',
                source_title='Accommodation service for international exchange students - TUM Global',
                source_url='https://www.global.tum.de/en/global/accommodation/',
                last_checked_at='2026-10-21',
                source_published_at=None,
                verification_status='verified_reference',
                related_sources=[],
            ),
        ),
        course_points=(
            CrossSchoolStructuredPoint(
                category="courses",
                title="學長姐常修課程方向與 TUMonline 選課規範",
                summary_zh="TUM 工程、資工與管理學院提供豐富英語授課模組（主に碩士層級與高年級課程），交換生須透過 TUMonline 系統查閱各學期開課語言與校區。",
                bullets=[
                    "熱門修課方向：Informatics（人工智慧、軟體工程）、電機與電腦工程、機械航太、TUM School of Management 科技管理課程。",
                    "學分限制：多數台灣締約校與 TUM 交換辦法要求交換生至少 50%–60% 學分須選修自所屬交換學院（Host School/Department）。",
                    "語言支援：TUM Language Center 提供免費德語密集先修班與學期德語課，跨校學長姐普遍推薦選修以利日常生活與學分採計。",
                ],
                origin_label="跨校修課方向與官方選課規範整理",
                source_title="TUM Exchange Students — Course Selection & TUMonline",
                source_url="https://www.international.tum.de/en/global/Exchange-students/",
                last_checked_at="2026-10-18",
            ),
        ),
        experience_points=(),
    ),
    CuratedInstitutionSpec(
        country_zh="日本",
        institution_slug="waseda-university",
        school_name_zh="早稻田大學",
        school_name_en="Waseda University",
        official_website="https://www.waseda.jp/top/en/",
        match_tokens=(
            "早稻田大學",
            "早稻田",
            "waseda university",
        ),
        living_cost_points=(
            CrossSchoolStructuredPoint(
                category='living_cost',
                title='早稻田 2027 交換：財力證明與生活預算分開確認',
                summary_zh='2027 交換簡章的財力證明要求為每年超過 1,440,000 日圓，或每學期超過 720,000 日圓。這是申請證明門檻，不是實際每月生活費估算；當期生活總預算仍須按住宿與個人支出另查。',
                bullets=['2027 春季入學的證明須於 2026/10/01 當日或之後開立；2027 秋季入學須於 2027/01/01 當日或之後開立，並透過 Speed Visa 提交。', '可用本人銀行餘額證明，或資助人的銀行餘額證明加支付費用誓約；資助人須與 Speed Visa 登記一致。必要時可合併獎學金／貸款證明，並提交所有相關文件。', '股票、ETF 等金融商品估值不一定列入餘額，簡章要求準備足額現金存款。原頁所列每月 120,000–160,000 日圓及新臺幣換算，尚未由本輪已讀來源證實，暫不作確定預算。', '交換生宿舍租金與水電等費用已另列於住宿欄；房型、一次性費用、餐費、交通與保險須分別確認，不能把部分宿舍租金當作完整生活費。'],
                origin_label='2027 官方財力要求（生活總預算待確認）',
                source_title='Waseda Exchange Programs 2027 Guidelines — Proof of Financial Viability',
                source_url='https://www.waseda.jp/inst/cie/assets/uploads/2026/06/ba8ac5b2898a045bc89b972436d4b2ba.pdf',
                last_checked_at='2026-10-21',
                source_published_at=None,
                verification_status='verified_reference',
                related_sources=[],
            ),
        ),
        housing_points=(
            CrossSchoolStructuredPoint(
                category='housing',
                title='早稻田交換生宿舍：三種宿舍、抽籤及當期申請',
                summary_zh='官方交換生住宿頁列早大寮、早稻田奉仕園與西早稻田留學生寮；申請採抽籤且不保證錄取。一般學生寮介紹不能直接代替交換生的適用宿舍與申請條件。',
                bullets=['早大寮（Sodai-ryo）北棟月租 54,000–62,000 日圓、南棟 63,000 日圓；兩者另有每月 8,000 日圓水電等費用。', '奉仕園 3 號館月租 69,000–72,000 日圓，另 9,900 日圓、實際電費及設施服務費；5 號館月租 52,000–66,000 日圓，另 13,200 日圓及設施服務費。', '西早稻田一般單人房月租 72,000 日圓、另 11,000 日圓；大單人房 85,000 日圓、另 13,000 日圓。各寮其他一次性費用與繳費方式須另查，不能視為全包價。', '目前申請頁適用 2026 秋季：日本時間 5/29 10:00 至 6/17 10:00，已截止。至少住宿一學期；只修一季課程者不適用。尚未收到交換入學許可者可先申請，最終未獲許可則取消；下一期日期仍待確認。'],
                origin_label='官方交換生住宿參考（申請頁為 2026 秋季）',
                source_title='Dormitories for Exchange Students  –  Student Affairs Section, Student Dormitory Desk, Waseda University',
                source_url='https://www.waseda.jp/inst/rlc/en/student_dormitory/exchange/',
                last_checked_at='2026-10-21',
                source_published_at=None,
                verification_status='verified_reference',
                related_sources=[{'title': 'Exchange Students  –  Student Affairs Section, Student Dormitory Desk, Waseda University', 'source_url': 'https://www.waseda.jp/inst/rlc/en/undergraduate/application/exchange/', 'category': None, 'summary': None}],
            ),
        ),
        course_points=(
            CrossSchoolStructuredPoint(
                category='courses',
                title='早稻田 2027 選課：學部限制與日語跨修分開確認',
                summary_zh='適用 2027 春／秋入學的校級交換一般說明；不是雙聯或所有院級協議的共同規則。選課於計畫開始後辦理，讀書計畫所列課程不代表已選上，也不保證滿足母校所需學分。',
                bullets=['原則以錄取學部課程為主，跨學部或全校開放課程須符合個別限制；部分超額課程才採抽籤，不能概括為所有課程一律三階段抽籤。', '一般簡章強烈建議每週約 6 門課、約 10 小時；SILS、FSE、CSE 英語學部另明定每週至少 10 小時。不可把一般建議寫成全校共同硬門檻。', '全校開放課程中的 CJL 日語跨修每學期上限通常為 8 學分，SILS 為 7；JLP 日語專修另依其專章，不套這個跨修上限。', 'CJL Level Check Test 的日語分級為 1–7；日語課採日語授課，學部課程與語言課的學分及要求須分別查看。', '各學部／研究科的語檢、GPA、年級、開放科目與入學季不同；母校提名不保證能選修所有課程。以下分列 2027 英語／日語大學部、研究所及 JLP 已讀條件；各母校協議適用範圍及附連結的個別課表仍須核對。'],
                origin_label='2027 接待校原文參考（母校方案另核對）',
                source_title='Waseda 2027 Guidelines — Course Registration, pp.15–16',
                source_url='https://www.waseda.jp/inst/cie/assets/uploads/2026/06/ba8ac5b2898a045bc89b972436d4b2ba.pdf',
                last_checked_at='2026-10-21',
                source_published_at=None,
                verification_status='verified_reference',
                related_sources=[{'title': '2027 英語學部條件', 'source_url': 'https://www.waseda.jp/inst/cie/assets/uploads/2026/06/e4b83beb6ee3607bf5992252db1e8fae.pdf', 'category': None, 'summary': None}, {'title': '2027 JLP 日語專修條件', 'source_url': 'https://www.waseda.jp/inst/cie/assets/uploads/2026/06/b75696f8758143b83f82a77f1d5d6315.pdf', 'category': None, 'summary': None}, {'title': '2027 日語學部條件', 'source_url': 'https://www.waseda.jp/inst/cie/assets/uploads/2026/06/d52d923019011eab359629ebd4f0703e.pdf', 'category': None, 'summary': None}, {'title': '2027 英語研究所條件', 'source_url': 'https://www.waseda.jp/inst/cie/assets/uploads/2026/06/4b4370d1666c886d96b8573cebd8d1fa.pdf', 'category': None, 'summary': None}, {'title': '2027 日語研究所條件', 'source_url': 'https://www.waseda.jp/inst/cie/assets/uploads/2026/06/dc3c48dd16c2b85ac8d7a74ba31fcafe.pdf', 'category': None, 'summary': None}],
            ),
            CrossSchoolStructuredPoint(
                category='courses',
                title='早稻田 2027 英語學部：依學部查核門檻',
                summary_zh='以下是英語授課大學部的指定門檻，仍須同時符合各校提名與學部其他規定。TOEFL 新舊制按原表 2026/01/21 前後考試日期欄列示，並非平台自行換算；不套用研究所或日語學部。',
                bullets=['SPSE 政治經濟、SSS（TAISI）社會科學、SILS 國際教養：GPA 3.0/4.0；TOEFL iBT 舊制 80／新制 4，或 IELTS 6.0；不接受 ITP 或 TOEIC L&R。', 'SOC 商學：GPA 3.0/4.0；TOEFL iBT 舊制 61／新制 3.5、ITP 500、IELTS 5.0 或 TOEIC L&R 620。須以商學課程為主，每學期至多 24 學分，英語課程數有限。', 'FSE 基幹理工、CSE 創造理工：GPA 3.0/4.0；TOEFL iBT 舊制 80／新制 4.5、IELTS 6.5 或 TOEIC L&R 730，不接受 ITP。入學時須為母校大三以上且主修相符，每學期至多 20 學分。', 'FSE 僅列數學／應用數理、資訊理工／資訊通信；CSE 僅列土木環境，機械不可申請。兩者不可跨主修或修日語學部課程；全校開放課限 GEC／CJL，畢業研究與實驗課不開放。', 'CMS 文化構想 JCulP：GPA 3.5/4.0；TOEFL iBT 舊制 95／新制 5，或 IELTS 7.0，不接受 ITP 或 TOEIC。僅九月入學；四月不開放。', 'SILS 四月入學限一學期，須修至少 8 學分中／高階 SILS 講授課，不可修入門或 Seminar；日語 6 學分是強烈建議。SSS 不可修 Seminar 或海外田野課，SPSE 也有指定必修與研討課限制。', 'GPA 不四捨五入。原表排除 TOEIC IP、IELTS General／One Skill Retake、TOEFL Home Edition／Essentials／MyBest、Duolingo 與 Cambridge；語檢豁免須另對照一般簡章及學部條件，不能只憑國籍或英語授課就判定。'],
                origin_label='2027 接待校原文參考（母校方案另核對）',
                source_title='Waseda AY2027 Undergraduate Schools — English based Program, pp.1–7',
                source_url='https://www.waseda.jp/inst/cie/assets/uploads/2026/06/e4b83beb6ee3607bf5992252db1e8fae.pdf',
                last_checked_at='2026-10-21',
                source_published_at=None,
                verification_status='verified_reference',
                related_sources=[],
            ),
            CrossSchoolStructuredPoint(
                category='courses',
                title='早稻田 2027 JLP：日語專修資格與學分',
                summary_zh='JLP 是日語專修計畫，與一般學部交換生跨修 CJL 不同。大學部 GPA 為 2.5/4.0；研究生該欄標 N/A，不能據此推定母校也沒有成績要求。',
                bullets=['入學前須有至少一學年、相當於 150 小時以上的校內／日語學校日語學習經驗；無上述機構學習經驗者，可依原文提交官方日語檢定或母校日語教師等開立的能力證明。', '完成半年計畫須 13 學分、一年須 26 學分，只計 CJL 與 GEC 的指定日本語教育科目，不是把所有外系學分都算入完成要求。', '每學期 CJL 最多 14 學分；全校開放及其他學部課程合計另限最多 4 學分、2 門課，仍有選課限制，也不保證能選滿。', '所有課程以日語授課；讀書計畫須說明學習日語的理由。選拔會看全部課程成績，不能只看日語科目；百分制約 65 分只是來源的概略參考，不取代正式 GPA 判定。'],
                origin_label='2027 接待校原文參考（母校方案另核對）',
                source_title='Waseda AY2027 Requirements for Japanese Language Program, p.1',
                source_url='https://www.waseda.jp/inst/cie/assets/uploads/2026/06/b75696f8758143b83f82a77f1d5d6315.pdf',
                last_checked_at='2026-10-21',
                source_published_at=None,
                verification_status='verified_reference',
                related_sources=[],
            ),
            CrossSchoolStructuredPoint(
                category='courses',
                title='早稻田 2027 日語學部：JLPT、GPA 與入學季',
                summary_zh='這份日語授課大學部表列 12 個學部，均要求 JLPT N1。政治經濟與三個理工學部要求 GPA 3.0/4.0、不可四捨五入；其他八個學部的 GPA 欄為 No Requirements，僅代表接待學部這一欄沒有門檻，母校提名條件仍須另查。',
                bullets=['法學部僅四月入學；教育學部僅四月入學且須交換一年，通常一年至多 40 學分，小學教育／理學科相關課程上限為 44。教育學部的研討或論文課須另獲系所許可，不能選有先修條件的課程。', '基幹、創造、先進理工須與母校主修相符，只能修錄取系所課程，不可跨系或選英語學程；畢業研究、論文、實驗室與實驗課不開放。全校開放課僅可選 GEC、CJL。', '三個日語理工學部每學期最多 20 學分、每週至少 10 小時；修季課程也須在各學期達到每週時數。先進理工的電氣・情報生命工學科不開放申請。', '日語商學部每學期最多 24 學分，可選其英語課程，TOEIC 620／舊制 TOEFL iBT 61 是建議能力。日語社會科學與文化構想亦可修各自英語課程，原表未另要求英語檢定；不代表以英語組入學的門檻相同。', '日語政治經濟可選英語課程，原表建議舊制 TOEFL iBT 80；實習、部分研討、語言及指定必修課不開放。成績單不能要求提前於春季 9/1、秋季 3/1 發出，遇週末順延至工作日。', '人間科學在所澤校區；運動科學列所澤與東伏見。這兩學部附件課表明列為舊年度參考，秋季入學請於七月、春季入學於二月向學部查詢最新課表。'],
                origin_label='2027 接待校日語大學部條件（母校方案另核對）',
                source_title='Waseda AY2027 Undergraduate Schools — Japanese based Program, pp.2–10',
                source_url='https://www.waseda.jp/inst/cie/assets/uploads/2026/06/d52d923019011eab359629ebd4f0703e.pdf',
                last_checked_at='2026-10-21',
                source_published_at=None,
                verification_status='verified_reference',
                related_sources=[],
            ),
            CrossSchoolStructuredPoint(
                category='courses',
                title='早稻田 2027 英語研究所：語檢與個別資格',
                summary_zh='適用 2027 春／秋校級交換研究所。TOEFL 舊／新分數依原表 2026/01/21 前後考試日期分列，並非自行換算；原表未釐清當日邊界，當日應考者須向校方確認。所有列載研究科均不收 ITP；No Requirements 只代表該接待研究科的 GPA 欄，不能免除母校門檻。',
                bullets=['政治學、經濟學：TOEFL iBT 舊 90／新 4.5、IELTS 6.5 或 TOEIC L&R 900；英語學位授課的母校證明信可作能力證明，使用檢定時須為正式考場測驗。申請前不必先取得指導教授同意。', '法學 LL.M.：GPA 3.0/4.0，不四捨五入；TOEFL 舊 92／新 5.0、IELTS 7.0 或 TOEIC L&R 900。至少三年法學高等教育；每年最多 40 學分，日語課程另須教師同意與 JLPT N1。', 'GSICCS 國際文化與傳播：TOEFL 舊 95／新 5.0 或 IELTS 7.0，不收 TOEIC；母校英語能力證明信不能替代檢定。交換生不安排指導教授，也不可選 Directed Research、Seminar I／II 或 Specialized 課程。', 'GSAPS 亞太研究：TOEFL 舊 86／新 4.5 或 IELTS 6.5，不收 TOEIC。WBS 商管：TOEFL 舊 92／新 4.5、IELTS 6.5 或 TOEIC L&R 900；WBS 可依原文使用母校英語學位授課證明。', 'WBS 另要求至少三年全職工作經驗，實習與兼職不計；入學前須在母校 MA／MBA 完成至少一年、兩學期。每學期上限 20 學分，不含 CJL。', 'FSE 基幹理工、CSE 創造理工、ASE 先進理工及 IPS 情報生產系統：TOEFL 舊 80／新 4.5、IELTS 6.5 或 TOEIC L&R 730；均須申請前取得指導教授同意，不能只憑語檢達標判定可申請。', '人間科學 EDICS：TOEFL 舊 80／新 4.5 或 IELTS 6.0；運動科學：TOEFL 舊 80／新 4.0 或 IELTS 6.0。兩者不收 TOEIC，均須指導教授同意；所澤／東伏見校區不能當作早稻田主校區。', '英語理工僅博士開放的領域：FSE 材料科學；CSE 建築、工業與經營系統、商業設計與管理；ASE 核能共同專攻。其餘可選領域仍依該研究科原表，不可把「理工」理解為全部系所。'],
                origin_label='2027 接待校研究所條件（母校方案另核對）',
                source_title='Waseda AY2027 Graduate Schools — English based Program, pp.1–14',
                source_url='https://www.waseda.jp/inst/cie/assets/uploads/2026/06/4b4370d1666c886d96b8573cebd8d1fa.pdf',
                last_checked_at='2026-10-21',
                source_published_at=None,
                verification_status='verified_reference',
                related_sources=[],
            ),
            CrossSchoolStructuredPoint(
                category='courses',
                title='早稻田 2027 日語研究所：N1 例外與研究指導',
                summary_zh='日語研究所表列 18 個研究科，全部 GPA 欄為 No Requirements；仍須符合母校提名規定。多數要求 JLPT N1，但理工、IPS 與社會科學博士有個別規則，不能一律套 N1，也不能把沒有統一語檢門檻理解成不需日語能力。',
                bullets=['政治學、經濟學、法學、教育、商學、GSAPS、日本語教育、會計及 WBS 要求 N1，申請前通常不必先取得教授同意；會計所另提醒不一定提供研究指導，且僅接受碩士。', '社會科學要求 JLPT N1 分數高於 100；博士無統一語檢門檻，但語言程度須經指導教授認可。申請前不要求教授同意，校方審查時洽詢教授，不能保證指定指導人。', 'FSE、CSE、ASE 與 IPS 語言欄為 No Requirements，均須先取得教授同意。環境能源、文學、人間科學與運動科學要求 N1，並須指導教授同意。', '日語 FSE 的材料科學、CSE 的建築／工業與經營系統／商業設計與管理、ASE 的核能共同專攻可申請碩士與博士，與英語管道不同。ASE 先進生命醫科學共同專攻僅博士、僅四月；先進健康科學共同專攻僅博士。', '法學日語管道不可修英語 LL.M. 課，博士除 CJL 外不辦理課程選修；日語法學每年最多 32 學分。文學研究科的全校開放課也限 CJL，不可跨其他學部／研究科。', '教育研究科高度教職實踐專攻僅春季碩士；通常每年上限 36 學分，該專攻為 39。全校開放課每學期最多 8 學分；跨所屬專攻另有 8 學分限制，必須依選課類別確認。', '日本語教育 GSJAL：指定理論研究科目每學期至多 10 學分，排除日本語教育學入門及日本語教育研究方法論；其他學部／中心合計整段交換期間最多 4 學分。規劃於 2027 開辦的登錄日本語教員養成課程，即使通過認證也不開放交換生。', '日語 WBS 同樣要求三年全職工作經驗（不含實習／兼職）、母校 MA／MBA 至少一年兩學期，每學期 20 學分不含 CJL。商學 GSC 須至少修一門該所課，每學期至多 20 學分、外所每年最多 10；會計每學期最多 24、全校開放課每年最多 10。'],
                origin_label='2027 接待校研究所條件（母校方案另核對）',
                source_title='Waseda AY2027 Graduate Schools — Japanese based Program, pp.1–15',
                source_url='https://www.waseda.jp/inst/cie/assets/uploads/2026/06/dc3c48dd16c2b85ac8d7a74ba31fcafe.pdf',
                last_checked_at='2026-10-21',
                source_published_at=None,
                verification_status='verified_reference',
                related_sources=[],
            ),
            CrossSchoolStructuredPoint(
                category='courses',
                title='早稻田 2027 研究所：研討課、學分與校區限制',
                summary_zh='以下限制須和各研究科語言門檻一起閱讀。文件內部分課表連結仍是 2025／2026 年度示例；並未因此確認 2027 每門課都會開設。母校所需學分、個別課表與指導教授接收名額仍須另外核對。',
                bullets=['政治學與經濟學的研究指導研討課原則供正式學位生；交換生若獲教師同意，只能以非正式 Moodle External User 旁聽，該研討課不列入成績報告或成績單。', 'GSAPS 的規定不同：碩士除 zemi 外至少修一門一般 GSAPS 課；博士不強制修一般講授課。每學期至多 14 學分，不含 CJL。碩博士每週必須參與指定教授的 zemi，不給學分但有成績並列成績單；缺席可得 F，不因母校沒有論文而免除。', 'GSICCS 只開放指定 Basic／Related 講授課，仍可能有不開放項目；每學期至多 14 學分、不含 CJL。全校開放課限 CJL，其他研究科另限最多 4 學分、2 門課；不保證錄取所有志願課。', '三個理工研究科限所屬專攻課程，選課需教授同意；全校開放課限 CJL，不可跨其他學部／研究科。每學期上限 20 學分，沒有最低學分但必須登記研究指導；英語管道也不保證每門課都能用英語修讀。', 'IPS 位於福岡縣北九州校區。聯繫教授時須表明是校際協議下的非學位碩／博士交換；碩士每學期原則至少 12、最多 14 學分，指定課程須教授同意，博士研究指導由所辦登記。', '人間科學英語 EDICS 可修的英語課有限，錄取後須與教授確認；改修日語課須 N1。日語運動科學跨修英語課須事先許可；這兩所修全校開放課可能需個別洽詢。環境能源的碩士跨其他研究科最多 4 學分、2 門課。', '英語研究所共同排除 TOEIC IP、IELTS General／One Skill Retake、TOEFL Home Edition／Essentials／MyBest、Duolingo 與 Cambridge。GSICCS 另不接受 TOEFL Paper Edition、IELTS Online／Indicator 等非指定考場測驗；不可把一般豁免套到明文不接受的研究科。', 'GSAPS 申請時須選擇希望指導教授；錄取後只能參加所方指派的一門 zemi，不能任意改換。課表標示的 zemi 8 學分只適用正式學位生，交換生仍為零學分；教師當期接收及完整課表須另查。'],
                origin_label='2027 接待校研究所條件（母校方案另核對）',
                source_title='Waseda AY2027 Graduate Requirements — program-specific course restrictions',
                source_url='https://www.waseda.jp/inst/cie/assets/uploads/2026/06/4b4370d1666c886d96b8573cebd8d1fa.pdf',
                last_checked_at='2026-10-21',
                source_published_at=None,
                verification_status='verified_reference',
                related_sources=[{'title': '2027 日語研究所原表', 'source_url': 'https://www.waseda.jp/inst/cie/assets/uploads/2026/06/dc3c48dd16c2b85ac8d7a74ba31fcafe.pdf', 'category': None, 'summary': None}, {'title': 'GSAPS 交換生必讀說明：課程、zemi 與指導教授（13 頁）', 'source_url': 'https://waseda.app.box.com/file/2117124954762?s=hq4ze8trlsmi0056xuu1m4j4gbwlh6zj', 'category': None, 'summary': None}],
            ),
        ),
        experience_points=(),
    ),
    CuratedInstitutionSpec(
        country_zh="德國",
        institution_slug="lmu-munich",
        school_name_zh="慕尼黑大學",
        school_name_en="Ludwig-Maximilians-Universität München",
        official_website="https://www.lmu.de/en/",
        match_tokens=(
            "慕尼黑大學",
            "德國慕尼黑大學",
            "ludwig-maximilians-universität münchen",
            "ludwig-maximilians-universitaet muenchen",
            "lmu munich",
        ),
        living_cost_points=(
            CrossSchoolStructuredPoint(
                category="living_cost",
                title="慕尼黑大學（LMU）每月生活費結構化參考（約 1,100–1,400 歐元）",
                summary_zh="依 LMU International Office 官方建議，慕尼黑生活成本較高，交換生每月生活預算（含房租、醫保与餐食）約需 1,100 至 1,400 歐元。",
                bullets=[
                    "每月總支出約 1,100–1,400 歐元，其中房租占比最高（私人租屋常達 650–900 歐元／月）。",
                    "每學期須繳納 Studierendenwerk 學期社會費（約 85 歐元），可加購德國全國青年學期交通票。",
                    "30 歲以下交換生須投保德國法定公立學生健康保險（約 120–130 歐元／月）。",
                ],
                origin_label="官方費用指南結構化整理",
                source_title="LMU Munich — Living Costs for International Students",
                source_url="https://www.lmu.de/en/workspace-for-students/international-office/incoming-exchange-students/",
                last_checked_at="2026-10-18",
            ),
        ),
        housing_points=(
            CrossSchoolStructuredPoint(
                category="housing",
                title="LMU 住宿分配機制與 Studierendenwerk 申請提醒",
                summary_zh="LMU 本身不直接經營宿舍，而是將部分 Studierendenwerk München 宿位名額分配予交換生；未獲分配者須自行透過私人市場或 WG 平台找房。",
                bullets=[
                    "申請 LMU 交換網報時，務必於期限內勾選住宿需求；宿位採隨機抽籤，約僅部分交換生能抽中。",
                    "LMU 主校區位於 Geschwister-Scholl-Platz（U3/U6 Universität 站），沿地鐵 U3/U6 或 U2 線找房通勤最為便利。",
                ],
                origin_label="官方住宿資訊整理",
                source_title="LMU Incoming Exchange — Housing in Munich",
                source_url="https://www.lmu.de/en/workspace-for-students/international-office/incoming-exchange-students/",
                last_checked_at="2026-10-18",
            ),
        ),
        course_points=(
            CrossSchoolStructuredPoint(
                category="courses",
                title="學長姐常修課程方向：人文社科、商管經濟、法律與德語課程",
                summary_zh="LMU 在商管經濟、政治社會、傳播、法律與自然科學領域均設有英語授課課程（LSF 系統可篩選授課語言），亦提供各級德語學習資源。",
                bullets=[
                    "選課透過 LSF 課程目錄查詢；各學院對交換生跨院選課比例有不同規定（通常至少 50% 學分須在提名院系修讀）。",
                    "IUCM 提供學期前德語密集班（Intensive German Course）與學期伴隨德語課。",
                ],
                origin_label="跨校修課方向與 LSF 規範整理",
                source_title="LMU Munich Course Catalogue (LSF) & Exchange Academic Info",
                source_url="https://www.lmu.de/en/workspace-for-students/international-office/incoming-exchange-students/",
                last_checked_at="2026-10-18",
            ),
        ),
    ),
)


def _strip_country_prefix(name_zh: str, country_zh: str) -> str:
    cleaned = name_zh.strip()
    cleaned = re.sub(r"\s*無\s*$", "", cleaned).strip()
    for prefix in (country_zh, "韓國", "南韓", "日本", "德國", "美國", "英國", "法國", "大陸地區", "中國"):
        if prefix and cleaned.startswith(prefix) and len(cleaned) >= len(prefix) + 3:
            rest = cleaned[len(prefix) :].strip()
            if rest.endswith(("大學", "學院", "學校", "大學校區")):
                return rest
    return cleaned


def split_bilingual_school_name(raw_name: str, country_zh: str = "") -> tuple[str, str]:
    """Extract (school_name_zh, school_name_en) from a raw PartnerUniversity.school_name."""
    normalized = re.sub(r"\s+", " ", unicodedata.normalize("NFKC", raw_name or "")).strip()
    normalized = re.sub(r"\s*\([^()]*(?:交換學生計畫|訪問學生計畫)[^()]*\)\s*$", "", normalized).strip()
    normalized = re.sub(r"\s*無\s*$", "", normalized).strip()

    en_match = re.search(r"[A-Za-z][A-Za-z0-9\s,&.'’\-–—/()ÜüÖöÄäßéèêëàâîïôûùçñíóúÁÉÍÓÚ]*", normalized)
    zh_chars = "".join(re.findall(r"[\u3400-\u9fff]+", normalized))

    if en_match and zh_chars:
        en_start = en_match.start()
        prefix = normalized[:en_start].strip(" ()（）[]【】,，;；-–—")
        suffix = normalized[en_start:].strip(" ()（）[]【】,，;；-–—")
        trailing_zh = re.search(r"[\u3400-\u9fff]{2,}", suffix)
        if trailing_zh and not prefix:
            en_part = suffix[: trailing_zh.start()].strip(" ()（）[]【】,，;；-–—")
            zh_part = suffix[trailing_zh.start() :].strip(" ()（）[]【】,，;；-–—")
        else:
            zh_part = prefix or zh_chars
            en_part = re.sub(r"[\u3400-\u9fff]+", " ", suffix).strip(" ()（）[]【】,，;；-–—")
            en_part = re.sub(r"\s+", " ", en_part).strip()
        zh_clean = _strip_country_prefix(zh_part, country_zh)
        return (zh_clean or en_part, en_part or zh_clean)

    if zh_chars:
        zh_clean = _strip_country_prefix(normalized, country_zh)
        return (zh_clean, zh_clean)

    return (normalized, normalized)


def slugify_english_name(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value or "")
    ascii_text = (
        decomposed.replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("Ä", "ae")
        .replace("Ö", "oe")
        .replace("Ü", "ue")
        .replace("ß", "ss")
    )
    ascii_only = "".join(ch for ch in ascii_text if not unicodedata.combining(ch))
    tokens = re.findall(r"[a-z0-9]+", ascii_only.lower())
    if not tokens:
        digest_hex = hashlib.sha256((value or "partner").encode("utf-8")).hexdigest()[:12]
        return f"inst-{digest_hex}"
    return "-".join(tokens)[:96].strip("-")


def resolve_country_slug_and_zh(country_input: str | None) -> tuple[str, str]:
    raw = unquote(country_input or "").strip()
    if not raw:
        return ("other", "海外地區")
    lower = raw.lower()
    if lower in SLUG_TO_COUNTRY_ZH:
        zh = SLUG_TO_COUNTRY_ZH[lower]
        return (COUNTRY_SLUGS[zh], zh)
    zh = canonical_country(raw)
    if zh in COUNTRY_SLUGS:
        return (COUNTRY_SLUGS[zh], zh)
    slug = slugify_english_name(zh)
    return (slug, zh)


def _norm_zh_key(value: str, country_zh: str) -> str:
    zh, _ = split_bilingual_school_name(value, country_zh)
    only_cjk = "".join(re.findall(r"[\u3400-\u9fffA-Za-z0-9]", zh)).lower()
    return only_cjk


def _norm_en_key(value: str, country_zh: str) -> str:
    _, en = split_bilingual_school_name(value, country_zh)
    if re.search(r"[\u3400-\u9fff]", en) and not re.search(r"[A-Za-z]{3,}", en):
        return ""
    decomposed = unicodedata.normalize("NFKD", en)
    kept = "".join(ch for ch in decomposed if not unicodedata.combining(ch) and ch.isalnum()).lower()
    return kept if len(kept) >= 4 else ""


def _legacy_partner_id(partner: PartnerUniversity) -> str:
    identity = f"{partner.country or ''}|{school_identity_key(partner.school_name)}"
    return hashlib.sha256(identity.encode()).hexdigest()[:20]


def resolve_partner_cross_school_path(
    partner: PartnerUniversity,
    *,
    home_id: str | None = None,
) -> str:
    """Return the canonical cross-school path (/partners/{country_slug}/{institution_slug}) for a partner row."""
    c_slug, c_zh = resolve_country_slug_and_zh(partner.country)
    legacy_key = _legacy_partner_id(partner)
    if _ENTITY_INDEX_CACHE:
        entities, alias_lookup = next(reversed(_ENTITY_INDEX_CACHE.values()))
        canonical_key = alias_lookup.get((c_slug, legacy_key))
        if canonical_key and canonical_key in entities:
            base_path = entities[canonical_key].canonical_path
            return f"{base_path}?{urlencode({'home': home_id})}" if home_id else base_path
    curated = _match_curated_spec(c_zh, partner.school_name)
    if curated is not None:
        inst_slug = curated.institution_slug
    else:
        _zh, en = split_bilingual_school_name(partner.school_name, c_zh)
        inst_slug = (
            slugify_english_name(en)
            if re.search(r"[A-Za-z]{3,}", en)
            else f"inst-{legacy_key[:12]}"
        )
    base_path = f"/partners/{c_slug}/{inst_slug}"
    return f"{base_path}?{urlencode({'home': home_id})}" if home_id else base_path


def _match_curated_spec(country_zh: str, raw_name: str) -> CuratedInstitutionSpec | None:
    lowered = unicodedata.normalize("NFKC", raw_name or "").lower()
    zh, en = split_bilingual_school_name(raw_name, country_zh)
    candidates = {lowered, zh.lower(), en.lower()}
    for spec in CURATED_SPECS:
        if spec.country_zh != country_zh:
            continue
        for token in spec.match_tokens:
            tok = token.lower()
            if tok in candidates or (len(tok) >= 4 and any(tok in cand for cand in candidates)):
                # Keep Munich University (LMU) distinct from Technical University of Munich (TUM)
                if spec.institution_slug == "lmu-munich" and ("工業" in raw_name or "technical" in lowered or "technische" in lowered):
                    continue
                return spec
    return None


@dataclass
class AggregatedPartnerEntity:
    country_slug: str
    country_name_zh: str
    institution_slug: str
    school_name_zh: str
    school_name_en: str
    official_website: str | None = None
    curated: CuratedInstitutionSpec | None = None
    home_rows: dict[str, list[PartnerUniversity]] = field(default_factory=dict)
    aliases: set[str] = field(default_factory=set)

    @property
    def canonical_path(self) -> str:
        return f"/partners/{self.country_slug}/{self.institution_slug}"

    @property
    def display_title(self) -> str:
        if self.school_name_zh and self.school_name_en and self.school_name_zh != self.school_name_en:
            return f"{self.school_name_zh}（{self.school_name_en}）"
        return self.school_name_zh or self.school_name_en


_ENTITY_INDEX_CACHE: dict[
    tuple[tuple[str, int, str, str, str], ...],
    tuple[dict[tuple[str, str], AggregatedPartnerEntity], dict[tuple[str, str], tuple[str, str]]],
] = {}


def build_cross_school_entity_index(
    catalogue_loader: Callable[[UniversityProfile], tuple[list[PartnerUniversity], CatalogueSourceStatus | None]],
    *,
    require_complete: bool = False,
) -> tuple[dict[tuple[str, str], AggregatedPartnerEntity], dict[tuple[str, str], tuple[str, str]]]:
    """Unify partner records across all supported Taiwanese universities into shared (country_slug, institution_slug) entities."""
    loaded_by_uni: list[tuple[UniversityProfile, list[PartnerUniversity]]] = []
    signature_parts: list[tuple[str, int, str, str, str]] = []
    for uni in SUPPORTED_UNIVERSITIES:
        try:
            partners, _ = catalogue_loader(uni)
        except Exception:
            if require_complete:
                raise
            continue
        partner_list = list(partners) if partners else []
        loaded_by_uni.append((uni, partner_list))
        first_name = partner_list[0].school_name if partner_list else ""
        last_name = partner_list[-1].school_name if partner_list else ""
        first_status = partner_list[0].availability_status if partner_list else ""
        signature_parts.append((uni.id, len(partner_list), first_name, last_name, first_status))

    cache_key = tuple(signature_parts)
    cached = _ENTITY_INDEX_CACHE.get(cache_key)
    if cached is not None:
        return cached

    raw_records: list[tuple[UniversityProfile, PartnerUniversity, str, str]] = []
    for uni, partner_list in loaded_by_uni:
        for p in partner_list:
            c_slug, c_zh = resolve_country_slug_and_zh(p.country)
            raw_records.append((uni, p, c_slug, c_zh))

    by_country: dict[str, list[tuple[UniversityProfile, PartnerUniversity, str]]] = {}
    for uni, p, c_slug, c_zh in raw_records:
        by_country.setdefault(c_slug, []).append((uni, p, c_zh))

    entities: dict[tuple[str, str], AggregatedPartnerEntity] = {}
    alias_lookup: dict[tuple[str, str], tuple[str, str]] = {}

    for c_slug, items in by_country.items():
        if not items:
            continue
        c_zh = items[0][2]
        n = len(items)
        parent = list(range(n))

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a: int, b: int) -> None:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[rb] = ra

        key_owners: dict[str, int] = {}
        for idx, (_uni, p, _czh) in enumerate(items):
            spec = _match_curated_spec(c_zh, p.school_name)
            keys: list[str] = []
            if spec is not None:
                keys.append(f"curated:{spec.institution_slug}")
            else:
                zh_k = _norm_zh_key(p.school_name, c_zh)
                en_k = _norm_en_key(p.school_name, c_zh)
                id_k = school_identity_key(p.school_name)
                if zh_k and re.search(r"[\u3400-\u9fff]{2,}", zh_k):
                    keys.append(f"zh:{zh_k}")
                if en_k:
                    keys.append(f"en:{en_k}")
                if id_k:
                    keys.append(f"id:{id_k}")
            for k in keys:
                if k in key_owners:
                    union(idx, key_owners[k])
                else:
                    key_owners[k] = idx

        clusters: dict[int, list[tuple[UniversityProfile, PartnerUniversity]]] = {}
        for idx, (uni, p, _czh) in enumerate(items):
            clusters.setdefault(find(idx), []).append((uni, p))

        used_slugs: set[str] = set()
        for cluster_rows in clusters.values():
            curated = None
            best_zh = ""
            best_en = ""
            website = None
            all_aliases: set[str] = set()

            for _uni, p in cluster_rows:
                if curated is None:
                    curated = _match_curated_spec(c_zh, p.school_name)
                zh, en = split_bilingual_school_name(p.school_name, c_zh)
                if zh and re.search(r"[\u3400-\u9fff]", zh):
                    if not best_zh or (len(zh) < len(best_zh) and len(zh) >= 3):
                        best_zh = zh
                if en and re.search(r"[A-Za-z]{3,}", en):
                    if not best_en or ("Technical University" in en and "Technical University" not in best_en):
                        best_en = en
                if not website and p.website and p.website.startswith(("https://", "http://")):
                    website = p.website

                all_aliases.add(p.school_name.strip().lower())
                all_aliases.add(zh.strip().lower())
                all_aliases.add(en.strip().lower())
                all_aliases.add(slugify_english_name(en))
                all_aliases.add(_legacy_partner_id(p))
                if zh.endswith("大學") and len(zh) > 3:
                    all_aliases.add(zh[:-2].strip().lower())

            if curated is not None:
                best_zh = curated.school_name_zh
                best_en = curated.school_name_en
                website = website or curated.official_website
                inst_slug = curated.institution_slug
                for tok in curated.match_tokens:
                    all_aliases.add(tok.lower())
                    all_aliases.add(slugify_english_name(tok))
            else:
                best_zh = best_zh or best_en or cluster_rows[0][1].school_name
                best_en = best_en or best_zh
                base_slug = (
                    slugify_english_name(best_en)
                    if re.search(r"[A-Za-z]{3,}", best_en)
                    else f"inst-{_legacy_partner_id(cluster_rows[0][1])[:12]}"
                )
                inst_slug = base_slug
                suffix_counter = 2
                while inst_slug in used_slugs:
                    inst_slug = f"{base_slug}-{suffix_counter}"
                    suffix_counter += 1

            used_slugs.add(inst_slug)
            all_aliases.add(inst_slug)

            home_rows: dict[str, list[PartnerUniversity]] = {}
            for uni, p in cluster_rows:
                home_rows.setdefault(uni.id, []).append(p)

            entity = AggregatedPartnerEntity(
                country_slug=c_slug,
                country_name_zh=c_zh,
                institution_slug=inst_slug,
                school_name_zh=best_zh,
                school_name_en=best_en,
                official_website=website,
                curated=curated,
                home_rows=home_rows,
                aliases={a for a in all_aliases if a},
            )
            canonical_key = (c_slug, inst_slug)
            entities[canonical_key] = entity
            for alias in entity.aliases:
                alias_lookup[(c_slug, alias)] = canonical_key

    if len(_ENTITY_INDEX_CACHE) >= 8:
        _ENTITY_INDEX_CACHE.clear()
    _ENTITY_INDEX_CACHE[cache_key] = (entities, alias_lookup)
    return entities, alias_lookup


def _build_home_agreement(
    uni: UniversityProfile,
    rows: list[PartnerUniversity] | None,
) -> CrossSchoolHomeAgreement:
    window_card = get_verified_school_window_card(uni.id)
    if not rows:
        return CrossSchoolHomeAgreement(
            home_id=uni.id,
            home_school_name=uni.school_name,
            home_short_name=uni.short_name,
            has_agreement=False,
            partner_display_name=None,
            program_types=[],
            availability_status="not_contracted",
            availability_label=AVAILABILITY_LABELS["not_contracted"],
            quota_summary="此母校當期公開名單未列載這間外國大學（可參考下方其他締約大學方案與跨校經驗）",
            language_requirement_summary="無（此母校未列載此合作校）",
            eligibility_summary="請先確認母校是否有院系級交換或短期訪問計畫",
            internal_online_deadline=window_card.online_deadline.value_text,
            internal_paper_deadline=window_card.paper_deadline.value_text,
            study_plan_limit=window_card.study_plan_limit.value_text,
            deadline_source_url=window_card.online_deadline.source_url,
            deadline_last_checked_at=window_card.online_deadline.last_checked_at,
            partner_source_url=uni.official_url,
            school_partner_seo_path=None,
        )

    primary = rows[0]
    program_types = list(dict.fromkeys(r.program_type for r in rows if r.program_type))
    statuses = list(
        dict.fromkeys(
            AVAILABILITY_LABELS.get(r.availability_status, r.availability_status) for r in rows
        )
    )
    quotas = list(dict.fromkeys(r.quota.strip() for r in rows if r.quota and r.quota.strip()))
    quota_text = "；".join(quotas) if quotas else "名額未公開列載（請依母校當期簡章與選校系統確認）"
    if primary.academic_year or primary.application_round:
        round_tag = " ".join(filter(None, [primary.academic_year, primary.application_round]))
        quota_text = f"[{round_tag}] {quota_text}"

    lang_reqs = list(
        dict.fromkeys(
            r.language_requirement.strip()
            for r in rows
            if r.language_requirement and r.language_requirement.strip()
        )
    )
    lang_text = (
        "；".join(lang_reqs)[:500]
        if lang_reqs
        else "母校公開名單未單獨列載此校語檢分數，請依母校語組通則與合作校 Fact Sheet 核對"
    )

    elig_reqs = list(
        dict.fromkeys(r.eligibility.strip() for r in rows if r.eligibility and r.eligibility.strip())
    )
    elig_text = (
        "；".join(elig_reqs)[:500]
        if elig_reqs
        else "須符合母校出國交換生甄選辦法之在學年級、GPA 與學業排名門檻"
    )

    degrees = "；".join(dict.fromkeys(r.degree_levels for r in rows if r.degree_levels)) or None
    colleges = "；".join(dict.fromkeys(r.colleges for r in rows if r.colleges)) or None
    study_period = "；".join(dict.fromkeys(r.study_period for r in rows if r.study_period)) or None
    tuition = "；".join(dict.fromkeys(r.tuition_info for r in rows if r.tuition_info)) or None
    housing = "；".join(dict.fromkeys(r.housing_info for r in rows if r.housing_info)) or None

    p_source = next(
        (r.source_url for r in rows if r.source_url and r.source_url.startswith(("https://", "http://"))),
        window_card.online_deadline.source_url,
    )
    return CrossSchoolHomeAgreement(
        home_id=uni.id,
        home_school_name=uni.school_name,
        home_short_name=uni.short_name,
        has_agreement=True,
        partner_display_name=primary.school_name,
        program_types=program_types,
        availability_status=primary.availability_status,
        availability_label="、".join(statuses)[:120],
        quota_summary=quota_text[:390],
        language_requirement_summary=lang_text[:590],
        eligibility_summary=elig_text[:590],
        degree_levels=degrees,
        colleges=colleges,
        study_period=study_period,
        tuition_info=tuition,
        housing_info=housing,
        internal_online_deadline=window_card.online_deadline.value_text,
        internal_paper_deadline=window_card.paper_deadline.value_text,
        study_plan_limit=window_card.study_plan_limit.value_text,
        deadline_source_url=window_card.online_deadline.source_url,
        deadline_last_checked_at=window_card.online_deadline.last_checked_at,
        partner_source_url=p_source,
        school_partner_seo_path=f"/schools/{uni.id}/partners/{_legacy_partner_id(primary)}",
    )


def _match_bundled_digests_for_entity(entity: AggregatedPartnerEntity) -> list[CrossSchoolStructuredPoint]:
    digests, sources = load_bundled_experience_digests()
    results: list[CrossSchoolStructuredPoint] = []
    entity_zh_norm = _norm_zh_key(entity.school_name_zh, entity.country_name_zh)
    entity_en_norm = _norm_en_key(entity.school_name_en, entity.country_name_zh)

    for url, meta in sources.items():
        digest = digests.get(url)
        if digest is None:
            continue
        meta_country = canonical_country(meta.get("country", ""))
        if meta_country != entity.country_name_zh:
            continue
        meta_school = meta.get("school_name", "")
        m_zh = _norm_zh_key(meta_school, entity.country_name_zh)
        m_en = _norm_en_key(meta_school, entity.country_name_zh)
        matched = False
        if entity_zh_norm and m_zh and (entity_zh_norm == m_zh or entity_zh_norm in m_zh or m_zh in entity_zh_norm):
            matched = True
        elif entity_en_norm and m_en and (entity_en_norm == m_en or entity_en_norm in m_en or m_en in entity_en_norm):
            matched = True
        if not matched:
            continue

        bullets: list[str] = []
        for sec in digest.sections[:3]:
            if sec.points:
                bullets.append(f"【{sec.heading}】{sec.points[0][:120]}")
        for tip in digest.tips[:2]:
            bullets.append(f"【學長姐提醒】{tip[:120]}")
        if not bullets:
            bullets.append(digest.overview[:120])

        results.append(
            CrossSchoolStructuredPoint(
                category="experience_digest",
                title=digest.title_zh[:150],
                summary_zh=digest.overview[:420],
                bullets=bullets[:5],
                origin_label=f"公開經驗結構化整理（{meta.get('platform', '公開來源')}）",
                source_title=meta.get("title") or digest.title_zh,
                source_url=url,
                source_published_at=digest.written_at,
            )
        )
    return results


def _synthesize_cross_school_intelligence(
    entity: AggregatedPartnerEntity,
    contracted_agreements: list[CrossSchoolHomeAgreement],
) -> tuple[
    list[CrossSchoolStructuredPoint],
    list[CrossSchoolStructuredPoint],
    list[CrossSchoolStructuredPoint],
    list[CrossSchoolStructuredPoint],
]:
    living_points: list[CrossSchoolStructuredPoint] = []
    housing_points: list[CrossSchoolStructuredPoint] = []
    course_points: list[CrossSchoolStructuredPoint] = []
    exp_points: list[CrossSchoolStructuredPoint] = []

    if entity.curated is not None:
        living_points.extend(entity.curated.living_cost_points)
        housing_points.extend(entity.curated.housing_points)
        course_points.extend(entity.curated.course_points)
        exp_points.extend(entity.curated.experience_points)

    exp_points.extend(_match_bundled_digests_for_entity(entity))

    primary_source_url = next(
        (
            a.partner_source_url
            for a in contracted_agreements
            if a.partner_source_url and a.partner_source_url.startswith("https://")
        ),
        contracted_agreements[0].deadline_source_url if contracted_agreements else "https://studyabroad.ntu.edu.tw/",
    )
    # Deadline review dates do not establish a review of host-school facts.
    related_sources = [
        SourceReference(title=f"{a.home_short_name}交換資料（當期適用性待確認）", source_url=a.partner_source_url)
        for a in contracted_agreements
        if a.partner_source_url and a.partner_source_url.startswith(("https://", "http://"))
    ]

    # A country default and an unrelated official link do not establish a
    # university's cost of living. Keep the gap visible until it has evidence.
    if not living_points:
        cost_hint = "本校當期生活費金額尚未核實；請分別確認住宿、伙食、交通、保險及簽證所需費用。"
        tuition_notes = [
            f"{a.home_short_name}列載參考：{a.tuition_info}"
            for a in contracted_agreements
            if a.tuition_info
        ][:3]
        cost_bullets = [cost_hint]
        if tuition_notes:
            cost_bullets.extend(tuition_notes)
        else:
            cost_bullets.append("尚無本方案學費規定的摘要，母校與接待校的繳費義務須分別確認。")

        living_points.append(
            CrossSchoolStructuredPoint(
                category="living_cost",
                title=f"{entity.school_name_zh}（{entity.country_name_zh}）跨校生活費與預算結構化參考",
                summary_zh=(
                    f"{entity.school_name_zh}：{cost_hint}"
                    "以下母校資料僅作查詢線索，不能代替接待校當期費用說明。"
                )[:430],
                bullets=cost_bullets[:5],
                origin_label="費用待核實",
                source_title="母校交換資料查詢入口（非生活費金額證據）",
                source_url=primary_source_url,
                verification_status="reference_only",
                related_sources=related_sources,
            )
        )

    # 2. Housing Reference
    if not housing_points:
        housing_notes = [
            f"{a.home_short_name}列載參考：{a.housing_info}"
            for a in contracted_agreements
            if a.housing_info
        ][:3]
        housing_bullets: list[str] = [
            "本校當期住宿申請資格、宿位保證、費用與截止日尚未完成核實；母校提名不能作為住宿已獲核配的證據。"
        ]
        if housing_notes:
            housing_bullets.extend(housing_notes)
        else:
            housing_bullets.append(
                "目前沒有可對應本校的母校住宿欄紀錄；需補查接待校當期交換生住宿說明。"
            )
        housing_points.append(
            CrossSchoolStructuredPoint(
                category="housing",
                title=f"{entity.school_name_zh} 住宿資料與待確認項目",
                summary_zh=(
                    f"{entity.school_name_zh}：以下最多列出三所母校的住宿欄原有紀錄作為查詢線索，"
                    "尚未獨立核實接待校當期規定；不代表住宿保證或完整申請程序。"
                )[:430],
                bullets=housing_bullets[:5],
                origin_label="住宿待核實",
                source_title="母校交換資料查詢入口（非當期住宿核實證據）",
                source_url=primary_source_url,
                verification_status="reference_only",
                related_sources=related_sources,
            )
        )

    # 3. Course Directions & Restrictions
    if not course_points:
        course_bullets: list[str] = []
        degree_notes = list(
            dict.fromkeys(
                f"{a.home_short_name}（{a.degree_levels}）"
                for a in contracted_agreements
                if a.degree_levels
            )
        )[:5]
        if degree_notes:
            course_bullets.append("母校表列學制參考（適用學期及身分待確認）：" + "、".join(degree_notes) + "。")
        college_notes = list(
            dict.fromkeys(
                f"{a.home_short_name}：{a.colleges}"
                for a in contracted_agreements
                if a.colleges
            )
        )[:3]
        if college_notes:
            course_bullets.append("母校表列學院／系所參考（不等於接待校當期可選課程）：" + "；".join(college_notes) + "。")

        # Check raw PartnerUniversity.course_restrictions across all contracting schools
        restriction_notes: list[str] = []
        for home_id, p_list in entity.home_rows.items():
            for p in p_list:
                if p.course_restrictions and p.course_restrictions.strip():
                    restriction_notes.append(p.course_restrictions.strip())
        restriction_notes = list(dict.fromkeys(restriction_notes))[:2]
        if restriction_notes:
            course_bullets.extend(f"選課限制摘要：{r}" for r in restriction_notes)

        lang_notes = list(
            dict.fromkeys(
                f"{a.home_short_name}（{a.language_requirement_summary}）"
                for a in contracted_agreements
                if "未單獨列載" not in a.language_requirement_summary
            )
        )[:3]
        if lang_notes:
            course_bullets.append("跨校語檢與授課門檻參考：" + "；".join(lang_notes) + "。")
        if not course_bullets:
            course_bullets.append("選課須同時滿足台灣母校最低修課學分規定與合作校當學期對交換生開放之科目清單。")

        course_points.append(
            CrossSchoolStructuredPoint(
                category="courses",
                title=f"{entity.school_name_zh} 母校表列學制、語言與選課條件參考",
                summary_zh=(
                    f"{len(contracted_agreements)} 所母校有「{entity.school_name_zh}」相關紀錄；此處僅展示部分母校欄位，完整條件請切換上方母校查看。"
                    "各母校規則與適用年度可能不同，尚未獨立核實接待校當期課表、授課語言及選課資格。"
                )[:430],
                bullets=course_bullets[:5],
                origin_label="母校表列參考，接待校待核實",
                source_title="母校交換資料查詢入口（非當期選課核實證據）",
                source_url=primary_source_url,
                verification_status="reference_only",
                related_sources=related_sources,
            )
        )

    # A generated preparation checklist is not a student's experience report.
    # Leave experience_digests empty when no matching report was found.

    return living_points, housing_points, course_points, exp_points


def build_cross_school_partner_page_data(
    *,
    country: str,
    institution: str,
    selected_home: str | None,
    catalogue_loader: Callable[[UniversityProfile], tuple[list[PartnerUniversity], CatalogueSourceStatus | None]],
    data_dir: Path | None = None,
    override_plan_count: int | None = None,
    require_complete: bool = False,
) -> CrossSchoolPartnerPageData | None:
    """Resolve (country, institution) across all supported universities and return the 2-layer page payload."""
    entities, alias_lookup = build_cross_school_entity_index(catalogue_loader, require_complete=require_complete)
    c_slug, _c_zh = resolve_country_slug_and_zh(country)
    inst_raw = unquote(institution or "").strip()
    inst_lower = inst_raw.lower()
    inst_slugified = slugify_english_name(inst_raw)

    canonical_key = (
        ((c_slug, inst_lower) if (c_slug, inst_lower) in entities else None)
        or alias_lookup.get((c_slug, inst_lower))
        or alias_lookup.get((c_slug, inst_slugified))
    )
    legacy_id = re.fullmatch(r"inst-([0-9a-f]{12})|([0-9a-f]{20})", inst_lower)
    if legacy_id and (c_slug, inst_lower) in entities:
        canonical_key = (c_slug, inst_lower)
    elif legacy_id:
        # Older pages without an English name used the first 12 hex characters
        # of a catalogue partner ID, and school partner links previously used the
        # full 20-hex partner ID. Only recover an unambiguous exact prefix;
        # never guess if the original partner disappeared or a prefix collides.
        prefix = legacy_id.group(1) or legacy_id.group(2)
        candidates = {
            key for key, entity in entities.items()
            if key[0] == c_slug and any(
                _legacy_partner_id(row).startswith(prefix)
                for rows in entity.home_rows.values() for row in rows
            )
        }
        if len(candidates) != 1:
            return None
        canonical_key = candidates.pop()
    if canonical_key is None:
        # Fallback: try matching by normalized Chinese or English name within the country
        zh_probe = _norm_zh_key(inst_raw, _c_zh)
        en_probe = _norm_en_key(inst_raw, _c_zh)
        for (cand_c, cand_i), ent in entities.items():
            if cand_c != c_slug:
                continue
            ent_zh = _norm_zh_key(ent.school_name_zh, ent.country_name_zh)
            ent_en = _norm_en_key(ent.school_name_en, ent.country_name_zh)
            if (zh_probe and ent_zh and (zh_probe == ent_zh or zh_probe in ent_zh)) or (
                en_probe and ent_en and (en_probe == ent_en or en_probe in ent_en)
            ):
                canonical_key = (cand_c, cand_i)
                break

    if canonical_key is None or canonical_key not in entities:
        return None

    entity = entities[canonical_key]
    all_agreements: list[CrossSchoolHomeAgreement] = []
    contracted_agreements: list[CrossSchoolHomeAgreement] = []

    for uni in SUPPORTED_UNIVERSITIES:
        rows = entity.home_rows.get(uni.id)
        agreement = _build_home_agreement(uni, rows)
        all_agreements.append(agreement)
        if agreement.has_agreement:
            contracted_agreements.append(agreement)

    resolved_home = resolve_university(selected_home) if selected_home else None
    if resolved_home is not None:
        selected_home_id = resolved_home.id
    elif contracted_agreements:
        selected_home_id = contracted_agreements[0].home_id
    else:
        selected_home_id = SUPPORTED_UNIVERSITIES[0].id

    selected_agreement = next(
        (a for a in all_agreements if a.home_id == selected_home_id),
        all_agreements[0],
    )

    living_refs, housing_refs, course_refs, exp_digests = _synthesize_cross_school_intelligence(
        entity, contracted_agreements
    )

    selected_uni = next(u for u in SUPPORTED_UNIVERSITIES if u.id == selected_home_id)
    compare_query = urlencode({"home": selected_uni.school_name, "compare": entity.school_name_zh})
    draft_query = urlencode({"home": selected_uni.school_name, "draft_school": entity.school_name_zh})
    conversion_hooks = CrossSchoolConversionHooks(
        free_tier_note="瀏覽各母校門檻與全台跨校情報完全免費免登入；登入後可跨裝置保存比較清單與讀書計畫草稿。",
        compare_list_cta_label="⭐ 收藏至跨校比較清單（一鍵登入保存）",
        study_plan_draft_cta_label="📝 儲存這間學校的讀書計畫草稿（一鍵登入保存）",
        login_redirect_url=f"/?{compare_query}#partners",
        compare_action_url=f"/?{compare_query}#partners",
        study_plan_action_url=f"/?{draft_query}#documents",
    )

    network_status, partner_heat = build_partner_specific_preference_heat(
        home_school=selected_uni,
        country_slug=entity.country_slug,
        institution_slug=entity.institution_slug,
        partner_name_zh=entity.school_name_zh,
        partner_name_en=entity.school_name_en,
        country_name_zh=entity.country_name_zh,
        quota_hint=selected_agreement.quota_summary,
        data_dir=data_dir,
        override_plan_count=override_plan_count,
    )
    admitted_connect = build_admitted_student_connect_hub(
        country_slug=entity.country_slug,
        institution_slug=entity.institution_slug,
        partner_name_zh=entity.school_name_zh,
        partner_name_en=entity.school_name_en,
        country_name_zh=entity.country_name_zh,
        contracted_short_names=[a.home_short_name for a in contracted_agreements],
        data_dir=data_dir,
    )

    return CrossSchoolPartnerPageData(
        country_slug=entity.country_slug,
        country_name_zh=entity.country_name_zh,
        institution_slug=entity.institution_slug,
        canonical_path=entity.canonical_path,
        school_name_zh=entity.school_name_zh,
        school_name_en=entity.school_name_en,
        display_title=entity.display_title,
        official_website=entity.official_website,
        selected_home_id=selected_home_id,
        selected_home_agreement=selected_agreement,
        contracted_home_count=len(contracted_agreements),
        total_supported_home_count=len(SUPPORTED_UNIVERSITIES),
        contracted_home_schools=contracted_agreements,
        all_home_agreements=all_agreements,
        living_cost_references=living_refs,
        housing_references=housing_refs,
        course_direction_references=course_refs,
        experience_digests=exp_digests,
        copyright_compliance_notice=COPYRIGHT_COMPLIANCE_NOTICE,
        conversion_hooks=conversion_hooks,
        selected_home_network_status=network_status,
        selected_home_partner_heat=partner_heat,
        admitted_student_connect=admitted_connect,
    )


def build_cross_school_partner_directory(
    *,
    catalogue_loader: Callable[[UniversityProfile], tuple[list[PartnerUniversity], CatalogueSourceStatus | None]],
    country: str | None = None,
    q: str | None = None,
    home: str | None = None,
    limit: int = 120,
    require_complete: bool = False,
) -> CrossSchoolPartnerDirectory:
    entities, _ = build_cross_school_entity_index(catalogue_loader, require_complete=require_complete)
    target_country_slug = None
    target_country_zh = None
    if country and country.strip():
        target_country_slug, target_country_zh = resolve_country_slug_and_zh(country)
        if not any(ent.country_slug == target_country_slug for ent in entities.values()):
            return CrossSchoolPartnerDirectory(
                total_partner_count=0,
                multi_school_partner_count=0,
                total_supported_home_count=len(SUPPORTED_UNIVERSITIES),
                selected_country_slug=target_country_slug,
                selected_country_name_zh=target_country_zh,
                countries=[],
                items=[],
            )

    resolved_home = resolve_university(home) if home and home.strip() else None
    query = (q or "").strip().lower()
    uni_short_by_id = {u.id: u.short_name for u in SUPPORTED_UNIVERSITIES}

    country_counts: dict[str, dict[str, Any]] = {}
    for ent in entities.values():
        bucket = country_counts.setdefault(
            ent.country_slug,
            {
                "country_slug": ent.country_slug,
                "country_name_zh": ent.country_name_zh,
                "partner_count": 0,
                "multi_school_count": 0,
            },
        )
        bucket["partner_count"] += 1
        if len(ent.home_rows) >= 2:
            bucket["multi_school_count"] += 1

    countries_sorted = sorted(
        country_counts.values(),
        key=lambda c: (-c["multi_school_count"], -c["partner_count"], c["country_slug"]),
    )

    filtered: list[AggregatedPartnerEntity] = []
    for ent in entities.values():
        if target_country_slug and ent.country_slug != target_country_slug:
            continue
        if resolved_home and resolved_home.id not in ent.home_rows:
            continue
        if query:
            haystack = f"{ent.school_name_zh} {ent.school_name_en} {ent.country_name_zh} {ent.institution_slug}".lower()
            if query not in haystack and not any(query in alias for alias in ent.aliases):
                continue
        filtered.append(ent)

    filtered.sort(
        key=lambda ent: (
            0 if ent.curated is not None else 1,
            -len(ent.home_rows),
            ent.country_slug,
            ent.institution_slug,
        )
    )

    total_count = len(filtered)
    multi_count = sum(1 for ent in filtered if len(ent.home_rows) >= 2)

    items: list[CrossSchoolPartnerSummaryItem] = []
    for ent in filtered[:limit]:
        short_names = [
            uni_short_by_id[h_id]
            for u in SUPPORTED_UNIVERSITIES
            for h_id in (u.id,)
            if h_id in ent.home_rows
        ]
        cost_hint = (
            ent.curated.living_cost_points[0].title
            if ent.curated and ent.curated.living_cost_points
            else "本校當期生活費金額尚未核實"
        )
        items.append(
            CrossSchoolPartnerSummaryItem(
                country_slug=ent.country_slug,
                country_name_zh=ent.country_name_zh,
                institution_slug=ent.institution_slug,
                canonical_path=ent.canonical_path,
                school_name_zh=ent.school_name_zh,
                school_name_en=ent.school_name_en,
                display_title=ent.display_title,
                contracted_home_count=len(short_names),
                contracted_home_short_names=short_names,
                has_living_cost_digest=bool(ent.curated and ent.curated.living_cost_points),
                has_housing_digest=True,
                has_course_digest=True,
                experience_count=(
                    len(ent.curated.experience_points) if ent.curated else 0
                ) + len(_match_bundled_digests_for_entity(ent)),
                sample_cost_hint=cost_hint[:220],
            )
        )

    return CrossSchoolPartnerDirectory(
        total_partner_count=total_count,
        multi_school_partner_count=multi_count,
        total_supported_home_count=len(SUPPORTED_UNIVERSITIES),
        selected_country_slug=target_country_slug,
        selected_country_name_zh=target_country_zh,
        countries=countries_sorted,
        items=items,
    )


def validate_cross_school_partner_compliance(data: CrossSchoolPartnerPageData) -> list[str]:
    """Verify strict copyright compliance and source provenance rules on a cross-school partner page."""
    problems: list[str] = []
    if "全台第一" in data.copyright_compliance_notice:
        problems.append("copyright_compliance_notice contains forbidden claim")

    for section_name, points in (
        ("living_cost_references", data.living_cost_references),
        ("housing_references", data.housing_references),
        ("course_direction_references", data.course_direction_references),
        ("experience_digests", data.experience_digests),
    ):
        if not points and section_name != "experience_digests":
            problems.append(f"{section_name} must not be empty")
        for idx, pt in enumerate(points):
            where = f"{section_name}[{idx}]"
            if len(pt.summary_zh) > 450:
                problems.append(f"{where}: summary_zh exceeds 450 chars")
            if not pt.bullets:
                problems.append(f"{where}: bullets must not be empty")
            if not pt.source_url.startswith(("https://", "http://")):
                problems.append(f"{where}: invalid source_url {pt.source_url}")
            if pt.last_checked_at is not None and not re.match(r"^\d{4}-\d{2}-\d{2}$", pt.last_checked_at):
                problems.append(f"{where}: invalid last_checked_at {pt.last_checked_at}")
            if pt.verification_status.startswith("verified_") and pt.last_checked_at is None:
                problems.append(f"{where}: verified content requires its own review date")
            combined = " ".join([pt.title, pt.summary_zh, *pt.bullets])
            if "全台第一" in combined:
                problems.append(f"{where}: contains forbidden claim '全台第一'")
            if re.search(r"[A-Za-z][A-Za-z ,'’\-]{95,}", combined):
                problems.append(f"{where}: contains unparaphrased long English paragraph")
    return problems


def _render_structured_points_html(points: list[CrossSchoolStructuredPoint]) -> str:
    if not points:
        return '<p class="cs-intel-empty">尚未收錄可對應本校的資料。</p>'
    cards: list[str] = []
    for pt in points:
        bullets_html = "".join(f"<li>{escape(b)}</li>" for b in pt.bullets)
        if pt.verification_status.startswith("verified_") and pt.last_checked_at:
            date_label = f"查核日期：{pt.last_checked_at}"
        elif pt.last_checked_at:
            date_label = f"既有整理日期：{pt.last_checked_at}（本輪待複核）"
        else:
            date_label = "本項內容尚待核實"
        if pt.source_published_at:
            date_label += f"；來源日期：{pt.source_published_at}"
        related_html = "".join(
            f'<li><a href="{escape(source.source_url)}" target="_blank" rel="noopener noreferrer">'
            f'{escape(source.title)}</a></li>'
            for source in pt.related_sources
            if source.source_url.startswith(("https://", "http://"))
        )
        related_html = f'<ul class="cs-related-sources">{related_html}</ul>' if related_html else ""
        cards.append(
            f'<article class="cs-intel-card" data-category="{escape(pt.category)}">'
            f'<div class="cs-intel-header">'
            f'<span class="cs-origin-badge">{escape(pt.origin_label)}</span>'
            f'<span class="cs-checked-badge">{escape(date_label)}</span>'
            f"</div>"
            f"<h3>{escape(pt.title)}</h3>"
            f'<p class="cs-intel-summary">{escape(pt.summary_zh)}</p>'
            f'<ul class="cs-intel-bullets">{bullets_html}</ul>'
            f'<p class="cs-intel-source">'
            f'<span>來源依據：{escape(pt.source_title)}</span> · '
            f'<a href="{escape(pt.source_url)}" target="_blank" rel="noopener noreferrer" data-official-source>'
            f"查閱官方／公開原文連結 ↗</a>"
            f"</p>"
            f"{related_html}"
            f"</article>"
        )
    return '<div class="cs-intel-grid">' + "".join(cards) + "</div>"


def render_cross_school_partner_page_body(data: CrossSchoolPartnerPageData) -> str:
    """Render the two-layer HTML body for /partners/{country}/{institution}."""
    sel = data.selected_home_agreement
    switcher_pills = "".join(
        f'<a class="cs-home-pill{" is-active" if a.home_id == sel.home_id else ""}{" is-contracted" if a.has_agreement else " is-uncontracted"}" '
        f'href="{escape(data.canonical_path)}?home={escape(a.home_id)}" '
        f'data-home-switch="{escape(a.home_id)}">'
        f"{escape(a.home_short_name)}"
        f'{" ✓" if a.has_agreement else ""}'
        f"</a>"
        for a in data.all_home_agreements
    )

    options_html = "".join(
        f'<option value="{escape(a.home_id)}"{" selected" if a.home_id == sel.home_id else ""}>'
        f'{escape(a.home_school_name)}（{"有締約" if a.has_agreement else "未列載此校"}）'
        f"</option>"
        for a in data.all_home_agreements
    )

    contracted_rows_html = "".join(
        f'<tr class="{"is-selected-home" if a.home_id == sel.home_id else ""}">'
        f'<td><strong><a href="{escape(data.canonical_path)}?home={escape(a.home_id)}">{escape(a.home_school_name)}</a></strong></td>'
        f"<td>{escape(a.availability_label)}</td>"
        f"<td>{escape(a.quota_summary)}</td>"
        f"<td>{escape(a.language_requirement_summary)}</td>"
        f"<td>{escape(a.degree_levels or '依簡章')}</td>"
        f'<td><a href="{escape(a.partner_source_url or a.deadline_source_url)}" target="_blank" rel="noopener noreferrer" data-official-source>母校來源 ↗</a>'
        + (
            f' · <a href="{escape(a.school_partner_seo_path)}">母校專頁</a>'
            if a.school_partner_seo_path
            else ""
        )
        + "</td></tr>"
        for a in data.contracted_home_schools
    )

    agreements_json = (
        json.dumps(
            {a.home_id: a.model_dump(mode="json") for a in data.all_home_agreements},
            ensure_ascii=False,
        )
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )

    network_heat_map: dict[str, Any] = {}
    for a in data.all_home_agreements:
        st, ht = build_partner_specific_preference_heat(
            home_school=a.home_id,
            country_slug=data.country_slug,
            institution_slug=data.institution_slug,
            partner_name_zh=data.school_name_zh,
            partner_name_en=data.school_name_en,
            country_name_zh=data.country_name_zh,
            quota_hint=a.quota_summary,
        )
        network_heat_map[a.home_id] = {
            "status": st.model_dump(mode="json"),
            "heat": ht.model_dump(mode="json"),
        }
    network_heat_json = (
        json.dumps(network_heat_map, ensure_ascii=False)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )

    upper_network_html = (
        render_partner_network_effects_upper_html(
            data.selected_home_network_status,
            data.selected_home_partner_heat,
        )
        if data.selected_home_network_status and data.selected_home_partner_heat
        else ""
    )
    lower_admitted_html = (
        render_admitted_student_connect_lower_html(
            data.admitted_student_connect,
            sel.home_id,
        )
        if data.admitted_student_connect
        else ""
    )

    website_link = (
        f' · <a href="{escape(data.official_website)}" target="_blank" rel="noopener noreferrer" data-official-source>外國大學官方網站 ↗</a>'
        if data.official_website
        else ""
    )

    return f"""
<p class="eyebrow">跨校外國大學整合專頁 · {escape(data.country_name_zh)}（/partners/{escape(data.country_slug)}/{escape(data.institution_slug)}）</p>
<h1>{escape(data.display_title)} 交換門檻、跨校名額與生活費指南</h1>
<p class="lead">
  打破單一大學冷門校「0 篇心得」的資訊孤島！目前全台支援的 {data.total_supported_home_count} 所大學中，共有
  <strong>{data.contracted_home_count} 所台灣的大學</strong>與「{escape(data.school_name_zh)}」締約。
  上半部可切換你的母校查看當期名額、語檢門檻與校內截止日；下半部聚合全台跨校生活費、住宿、修課方向與公開經驗摘要。{website_link}
</p>

<aside class="cs-compliance-banner" role="note" aria-label="著作權與資料合規聲明">
  <strong>📜 結構化摘要與著作權合規鐵律：</strong>{escape(data.copyright_compliance_notice)}
</aside>

<section class="cs-layer cs-upper-layer" id="home-rule-layer" aria-labelledby="upper-layer-heading">
  <div class="cs-layer-header">
    <span class="cs-layer-step">上半部 · 母校規則層</span>
    <h2 id="upper-layer-heading">切換你的母校：查看對「{escape(data.school_name_zh)}」的當期名額、語檢門檻與校內截止日</h2>
  </div>

  <div class="cs-home-switcher-bar">
    <label for="partner-home-switcher"><strong>選擇你的就讀母校：</strong></label>
    <select id="partner-home-switcher" aria-label="選擇你的就讀母校">
      {options_html}
    </select>
    <span class="cs-switcher-hint">點擊下方母校標籤亦可直接切換：</span>
  </div>
  <nav class="cs-home-pills" aria-label="母校快速切換">{switcher_pills}</nav>

  <div class="cs-selected-home-card" id="selected-home-rule-card" data-selected-home="{escape(sel.home_id)}">
    <div class="cs-selected-home-head">
      <div>
        <span class="cs-home-badge" id="cs-home-badge">{escape(sel.home_school_name)}</span>
        <strong class="cs-status-pill" id="cs-availability-label">{escape(sel.availability_label)}</strong>
      </div>
      <div class="cs-selected-home-links">
        <a id="cs-partner-source-link" href="{escape(sel.partner_source_url or sel.deadline_source_url)}" target="_blank" rel="noopener noreferrer" data-official-source>
          官方名額／簡章來源（HTTPS）↗
        </a>
        <span class="cs-checked-tag" id="cs-deadline-checked-at">最後查核日期：{escape(sel.deadline_last_checked_at)}</span>
      </div>
    </div>

    <dl class="cs-rule-grid">
      <div class="cs-rule-box">
        <dt>當期名額與開放狀態</dt>
        <dd id="cs-quota-summary">{escape(sel.quota_summary)}</dd>
      </div>
      <div class="cs-rule-box">
        <dt>語言檢定門檻</dt>
        <dd id="cs-language-summary">{escape(sel.language_requirement_summary)}</dd>
      </div>
      <div class="cs-rule-box">
        <dt>申請資格與可申請學制／學院</dt>
        <dd id="cs-eligibility-summary">
          {escape(sel.eligibility_summary)}
          {f"<br><small>學制：{escape(sel.degree_levels)}</small>" if sel.degree_levels else ""}
          {f"<br><small>學院：{escape(sel.colleges)}</small>" if sel.colleges else ""}
        </dd>
      </div>
      <div class="cs-rule-box">
        <dt>母校校內線上報名截止日</dt>
        <dd>
          <span id="cs-online-deadline">{escape(sel.internal_online_deadline)}</span>
          <br>
          <small>
            <a id="cs-deadline-source-link" href="{escape(sel.deadline_source_url)}" target="_blank" rel="noopener noreferrer" data-official-source>
              母校國際處官方來源 ↗
            </a>
            · 最後查核：<span id="cs-deadline-checked-inline">{escape(sel.deadline_last_checked_at)}</span>
          </small>
        </dd>
      </div>
      <div class="cs-rule-box">
        <dt>母校紙本繳件截止日／送件規定</dt>
        <dd id="cs-paper-deadline">{escape(sel.internal_paper_deadline)}</dd>
      </div>
      <div class="cs-rule-box">
        <dt>母校讀書計畫字數／頁數上限</dt>
        <dd id="cs-study-plan-limit">{escape(sel.study_plan_limit)}</dd>
      </div>
    </dl>
  </div>

  <div class="cs-conversion-hook" id="partner-conversion-hook" aria-label="收藏比較清單與儲存讀書計畫草稿">
    <div class="cs-conversion-copy">
      <strong>💡 免費查門檻，登入保存你的跨校申請資產</strong>
      <p>{escape(data.conversion_hooks.free_tier_note)}</p>
    </div>
    <div class="cs-conversion-actions">
      <a class="button cs-cta-compare" id="cs-btn-save-compare" href="{escape(data.conversion_hooks.compare_action_url)}" data-partner-school="{escape(data.school_name_zh)}" data-partner-country="{escape(data.country_name_zh)}">
        {escape(data.conversion_hooks.compare_list_cta_label)}
      </a>
      <a class="button secondary cs-cta-draft" id="cs-btn-save-draft" href="{escape(data.conversion_hooks.study_plan_action_url)}" data-partner-school="{escape(data.school_name_zh)}">
        {escape(data.conversion_hooks.study_plan_draft_cta_label)}
      </a>
      <a class="button secondary" href="/calendar/school-window.ics?school={escape(sel.home_id)}" id="cs-btn-download-ics">
        📅 一鍵匯入母校截止日（.ics）
      </a>
    </div>
  </div>
  {upper_network_html}
</section>

<section class="cs-layer cs-lower-layer" id="cross-school-intelligence-layer" aria-labelledby="lower-layer-heading">
  <div class="cs-layer-header">
    <span class="cs-layer-step">下半部 · 全台跨校情報層（破除單校 0 篇心得孤島）</span>
    <h2 id="lower-layer-heading">全台 {data.contracted_home_count} 所締約大學跨校情報聚合：生活費、住宿、課程方向與公開經驗摘要</h2>
    <p>即使你的母校歷年較少人去「{escape(data.school_name_zh)}」，也能直接參考全台各締約大學的公開經驗摘要與官方實務資料。</p>
  </div>

  <section class="cs-subblock" id="cross-school-living-cost">
    <h2>1. 跨校生活費參考（結構化整理＋官方／公開原文連結）</h2>
    {_render_structured_points_html(data.living_cost_references)}
  </section>

  <section class="cs-subblock" id="cross-school-housing">
    <h2>2. 住宿資訊與宿舍申請提醒</h2>
    {_render_structured_points_html(data.housing_references)}
  </section>

  <section class="cs-subblock" id="cross-school-courses">
    <h2>3. 學長姐曾修過的課程方向與選課限制</h2>
    {_render_structured_points_html(data.course_direction_references)}
  </section>

  <section class="cs-subblock" id="cross-school-experiences">
    <h2>4. 跨校公開經驗結構化重點摘要（附原文連結，絕不轉載全文）</h2>
    {_render_structured_points_html(data.experience_digests)}
  </section>

  <section class="cs-subblock" id="cross-school-contracted-universities">
    <h2>5. 全台有哪些大學跟「{escape(data.school_name_zh)}」締約（共 {data.contracted_home_count} 校門檻對照）</h2>
    <div class="cs-table-wrap">
      <table class="cs-agreement-table">
        <thead>
          <tr>
            <th>台灣締約母校</th>
            <th>當期資料狀態</th>
            <th>當期名額摘要</th>
            <th>語言門檻摘要</th>
            <th>可申請學制</th>
            <th>官方依據與母校專頁</th>
          </tr>
        </thead>
        <tbody>
          {contracted_rows_html}
        </tbody>
      </table>
    </div>
  </section>
  {lower_admitted_html}
</section>

<p class="cs-bottom-links">
  <a href="/partners/{escape(data.country_slug)}">查看{escape(data.country_name_zh)}全部跨校合作大學</a> ·
  <a href="/partners">返回跨校外國大學總覽</a> ·
  <a href="/schools">依台灣母校瀏覽交換指南</a>
</p>
<script type="application/json" id="cs-home-agreements-data">{agreements_json}</script>
<script type="application/json" id="cs-home-network-heat-data">{network_heat_json}</script>
"""


def render_cross_school_partner_directory_body(directory: CrossSchoolPartnerDirectory) -> str:
    """Render the HTML body for /partners or /partners/{country}."""
    heading = (
        f"{directory.selected_country_name_zh}跨校合作外國大學總覽（共 {directory.total_partner_count} 所）"
        if directory.selected_country_name_zh
        else f"跨校外國合作大學總覽｜整合全台 {directory.total_supported_home_count} 所大學締約情報與經驗摘要"
    )
    country_nav = "".join(
        f'<li><a href="/partners/{escape(c["country_slug"])}">'
        f'<strong>{escape(c["country_name_zh"])}</strong> '
        f'<span>共 {c["partner_count"]} 校（{c["multi_school_count"]} 校為多校共同締約）</span>'
        f"</a></li>"
        for c in directory.countries[:24]
    )

    cards = "".join(
        f'<li>'
        f'<a href="{escape(item.canonical_path)}">'
        f'<strong>{escape(item.display_title)}</strong>'
        f'<span>{escape(item.country_name_zh)} · 全台 {item.contracted_home_count} 校締約（{escape("、".join(item.contracted_home_short_names[:6]))}{"…" if len(item.contracted_home_short_names) > 6 else ""}）</span>'
        f"</a>"
        f"<p>{escape(item.sample_cost_hint)}</p>"
        f"</li>"
        for item in directory.items
    )

    return f"""
<p class="eyebrow">跨校外國大學頁 · 破除單校心得孤島 · 100% 結構化摘要＋原文連結</p>
<h1>{escape(heading)}</h1>
<p class="lead">
  以「國家＋外國大學機構 ID」為核心，將全台 {directory.total_supported_home_count} 所大學的當期名額、語檢門檻、校內截止日，
  與跨校生活費參考、住宿資訊、修課方向及公開經驗結構化摘要整合於同一頁面。
</p>
<aside class="cs-compliance-banner" role="note">
  <strong>📜 著作權合規原則：</strong>{escape(COPYRIGHT_COMPLIANCE_NOTICE)}
</aside>
<h2>依國家探索跨校合作外國大學</h2>
<ul class="cards">{country_nav}</ul>
<h2>跨校熱門與多校締約外國大學（點擊查看上下雙層跨校情報）</h2>
<ul class="cards">{cards}</ul>
<p><a href="/schools">依台灣就讀母校查看交換學校指南</a> · <a href="/destinations">查看國家交換預算指南</a></p>
"""
