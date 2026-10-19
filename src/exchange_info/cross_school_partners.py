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
from typing import Any
from urllib.parse import quote, unquote, urlencode

from .destination_tips import canonical_country, guide_for_country
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
)
from .school_identity import school_identity_key
from .university_registry import SUPPORTED_UNIVERSITIES, UniversityProfile, resolve_university
from .verified_window_deadlines import get_verified_school_window_card

COPYRIGHT_COMPLIANCE_NOTICE = (
    "【著作權與資料合規聲明】本頁所有跨校生活費、住宿、修課方向與學長姐經驗皆由 UniWay 以自有結構化方式重新整理重點摘要，"
    "絕不轉載、不複製學長姐心得全文或各校簡章 PDF 原文；每一項摘要均附上官方或公開原文連結與查核日期，請點擊原出處閱讀完整內容。"
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
    }
)

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
                category="living_cost",
                title="慕尼黑每月生活費結構化參考（約 1,100–1,400 歐元）",
                summary_zh="依慕尼黑工業大學（TUM）國際處與 DAAD 官方生活費指南整理，慕尼黑為德國生活成本最高城市之一，交換生每月建議準備約 1,100 至 1,400 歐元。",
                bullets=[
                    "每月總預算約 1,100–1,400 歐元（折合新臺幣約 38,500–49,000 元，視住宿類型浮動）。",
                    "住宿與房租：公立學生宿舍約 400–550 歐元／月；私人合租公寓（WG）多落在 650–900 歐元／月。",
                    "強制項目：德國 30 歲以下學生公立醫保約 120–130 歐元／月、學期雜費（Semester Fee）每學期約 85 歐元、廣播電視費（Rundfunkbeitrag）每月 18.36 歐元。",
                ],
                origin_label="官方費用指南結構化整理",
                source_title="TUM Global & Alumni Office — Cost of Living in Munich",
                source_url="https://www.international.tum.de/en/global/coming-to-tum/living-in-munich/",
                last_checked_at="2026-10-18",
            ),
        ),
        housing_points=(
            CrossSchoolStructuredPoint(
                category="housing",
                title="TUM 交換生住宿申請提醒與校區分布",
                summary_zh="TUM 不保證所有交換生皆能分發校內宿舍，Studierendenwerk München Oberbayern 服務名額採抽籤或配額制，建議獲母校提名後立即同步啟動校外合租搜尋。",
                bullets=[
                    "熱門宿舍區包含 Studentenstadt Freimann 與 Olympiazentrum，通勤至市中心校區或 Garching 理工校區便利。",
                    "由於資訊、機械、物理等學院位於 Garching 校區（U6 地鐵終點），找房時建議沿 U3／U6 地鐵線向北或市區規劃。",
                    "防詐提醒：慕尼黑租屋市場極為競爭，切勿在未實際看房或確認房東身分前預先跨國匯出押金。",
                ],
                origin_label="官方住宿頁＋跨校學長姐提醒整理",
                source_title="TUM Accommodation for Exchange Students",
                source_url="https://www.international.tum.de/en/global/coming-to-tum/accommodation/",
                last_checked_at="2026-10-18",
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
        experience_points=(
            CrossSchoolStructuredPoint(
                category="experience_digest",
                title="跨校赴慕尼黑工大交換重點整理：期末考一試定勝負與提早找房",
                summary_zh="綜合全台多校理工與商管交換生公開經驗，TUM 課程學術強度高、多數專業課以期末考 100% 計分，且開學前一個月的迎新與找房期是適應關鍵。",
                bullets=[
                    "評分制度：德國理工課程常無平時小考或作業加分，期末筆試（Klausur）占總成績 100%，報名考試須於 TUMonline 期限內個別登記。",
                    "生活實務：抵達慕尼黑後須先完成市政廳入籍（KVR Anmeldung）、啟動限制提領帳戶與學生醫保，建議出國前先預約辦理時段。",
                    "社交與旅遊：可報名 TUMi（TUM International）舉辦的巴伐利亞文化體驗、新天鵝堡與阿爾卑斯山健行活動，快速結識各國交換生。",
                ],
                origin_label="跨校公開經驗結構化摘要",
                source_title="TUM International (TUMi) Orientation & Exchange Guide",
                source_url="https://www.international.tum.de/en/global/tumi/",
                last_checked_at="2026-10-18",
            ),
        ),
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
                category="living_cost",
                title="東京早稻田每月生活費結構化參考（約 120,000–160,000 日圓）",
                summary_zh="依早稻田大學留學中心（CIE）與 JASSO 東京地區統計整理，赴早稻田交換每月生活費（不含來回機票）約需 120,000 至 160,000 日圓。",
                bullets=[
                    "每月總預算約 120,000–160,000 日圓（折合新臺幣約 26,000–35,000 元）。",
                    "住宿費：早稻田學生寮（如 WISH）或共立合作宿舍（WID）每月約 55,000–90,000 日圓（水電與供餐方案依寮別另計）。",
                    "日常開支：伙食費約 35,000–45,000 日圓／月、日本國民健康保險約 2,000 日圓／月、手機網路與地鐵通勤約 8,000–15,000 日圓／月。",
                ],
                origin_label="官方留學中心費用參考整理",
                source_title="Waseda University Center for International Education (CIE)",
                source_url="https://www.waseda.jp/inst/cie/en/exchange/application",
                last_checked_at="2026-10-18",
            ),
        ),
        housing_points=(
            CrossSchoolStructuredPoint(
                category="housing",
                title="早稻田國際學生寮（WISH／WID）與住宿申請提醒",
                summary_zh="早稻田提供中野國際學生寮（WISH）及多處 WID 合作學生會館（含早稻田、高田馬場、所澤等），惟床位採志願抽籤，須留意申請截止日早於放榜。",
                bullets=[
                    "WISH（Waseda International Student House）：位於中野站附近，為 4 人一組共用客廳之單人雅房，含豐富 RA 國際交流活動。",
                    "WID（Waseda International Dormitory）：由共立メンテナンス營運，多數提供早晚供餐方案，適合希望固定控制餐費的同學。",
                    "申請提醒：校級交換（CIE）與院系級交換可選宿舍清單可能不同，未抽中校方宿舍者可透過早稻田 Student Housing Center 媒合民間租屋。",
                ],
                origin_label="官方宿舍中心與跨校經驗整理",
                source_title="Waseda University Residence Life Center",
                source_url="https://www.waseda.jp/inst/rlc/en/",
                last_checked_at="2026-10-18",
            ),
        ),
        course_points=(
            CrossSchoolStructuredPoint(
                category="courses",
                title="學長姐常修課程方向：SILS 國際教養、政經商學與 CJL 日語課",
                summary_zh="早稻田交換分為英語授課學程與日語授課學部，並開放交換生加選日本語教育研究中心（CJL）各級別日語課程。",
                bullets=[
                    "英語授課方向：國際教養學部（SILS）、政治經濟學部（SPSE）、商學部與理工學部英語模組，涵蓋亞太政經、日本流行文化與國際商管。",
                    "日語密集強化：CJL 提供 Level 1–8 綜合日語與主題日語（商務日語、漢字、發音、日本社會討論），採電腦志願抽籤選課。",
                    "選課注意：早稻田選課採三階段電腦抽籤制（非先搶先贏），熱門課須分散風險填報，並滿足簽證要求之每週最低授課時數。",
                ],
                origin_label="跨校修課方向與 CIE 選課規範整理",
                source_title="Waseda CIE Exchange Program Curriculum & CJL",
                source_url="https://www.waseda.jp/inst/cie/en/exchange",
                last_checked_at="2026-10-18",
            ),
        ),
        experience_points=(
            CrossSchoolStructuredPoint(
                category="experience_digest",
                title="跨校赴早稻田交換重點整理：ICC 國際交流活動與學部門檻差異",
                summary_zh="全台共有逾 10 所大學與早稻田締約（含校級與院級），跨校學長姐普遍推薦善用 ICC（異文化交流中心）活動融入日本學生圈，並提前核對各學部語檢分數。",
                bullets=[
                    "門檻差異：同一間早稻田大學，英語組通常要求 TOEFL iBT 79–90 或 IELTS 6.0–6.5，日語組多要求 JLPT N1（部分學部接受 N2），各學部規定分開計算。",
                    "校園融入：Waseda ICC 每週舉辦語言交換午餐、地方文化參訪與企業見學，是認識日本本地生最直接的管道。",
                    "生活實務：高田馬場至早稻田正門步行約 20 分鐘，多數同學會購買二手腳踏車或辦理都營巴士／東京メトロ通學定期券。",
                ],
                origin_label="跨校公開經驗結構化摘要",
                source_title="Waseda Interdisciplinary Cultural Center (ICC)",
                source_url="https://www.waseda.jp/inst/icc/en/",
                last_checked_at="2026-10-18",
            ),
        ),
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


def build_cross_school_entity_index(
    catalogue_loader: Callable[[UniversityProfile], tuple[list[PartnerUniversity], CatalogueSourceStatus | None]],
) -> tuple[dict[tuple[str, str], AggregatedPartnerEntity], dict[tuple[str, str], tuple[str, str]]]:
    """Unify partner records across all supported Taiwanese universities into shared (country_slug, institution_slug) entities."""
    raw_records: list[tuple[UniversityProfile, PartnerUniversity, str, str]] = []
    for uni in SUPPORTED_UNIVERSITIES:
        try:
            partners, _ = catalogue_loader(uni)
        except Exception:
            continue
        for p in partners:
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
        availability_label="、".join(statuses),
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
                last_checked_at=digest.written_at,
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
    primary_checked_at = (
        contracted_agreements[0].deadline_last_checked_at if contracted_agreements else "2026-10-18"
    )
    country_guide = guide_for_country(entity.country_name_zh)

    # 1. Living Cost Reference (ensure every school has a structured, source-backed summary)
    if not living_points:
        cost_hint = COUNTRY_DEFAULT_CURRENCY_HINT.get(
            entity.country_name_zh,
            f"赴{entity.country_name_zh}交換建議分列計算住宿、伙食、當地交通、強制醫療保險與簽證財力證明。",
        )
        tuition_notes = [
            f"{a.home_short_name}：{a.tuition_info[:90]}"
            for a in contracted_agreements
            if a.tuition_info
        ][:3]
        cost_bullets = [cost_hint]
        if tuition_notes:
            cost_bullets.append("跨校學費協議摘要：" + "；".join(tuition_notes))
        else:
            cost_bullets.append("校級交換生原則上繳交台灣母校學雜費、免繳合作校學費（自費研修方案除外，請依各母校簡章核對）。")
        if country_guide:
            for topic in country_guide.topics:
                if topic.topic in {"payment", "health_insurance"} and topic.tips:
                    cost_bullets.append(f"【{topic.title}】{topic.tips[0].title}：{topic.tips[0].detail[:95]}")
                    if topic.tips[0].sources:
                        primary_source_url = topic.tips[0].sources[0].url
                        primary_checked_at = topic.tips[0].checked_at
                    break

        living_points.append(
            CrossSchoolStructuredPoint(
                category="living_cost",
                title=f"{entity.school_name_zh}（{entity.country_name_zh}）跨校生活費與預算結構化參考",
                summary_zh=(
                    f"綜合{entity.country_name_zh}官方留學參考與全台 {len(contracted_agreements)} 所締約大學交換資料整理："
                    f"{cost_hint}。實際開支視校內宿舍分配與個人消費習慣而定。"
                )[:430],
                bullets=cost_bullets[:5],
                origin_label="跨校締約資料與官方預算參考整理",
                source_title=f"{entity.country_name_zh}交換預算與締約母校官方依據",
                source_url=primary_source_url,
                last_checked_at=primary_checked_at,
            )
        )

    # 2. Housing Reference
    if not housing_points:
        housing_notes = [
            f"{a.home_short_name}列載：{a.housing_info[:100]}"
            for a in contracted_agreements
            if a.housing_info
        ][:3]
        housing_bullets: list[str] = []
        if housing_notes:
            housing_bullets.extend(housing_notes)
        else:
            housing_bullets.append(
                f"多數{entity.country_name_zh}合作校於母校完成提名（Nomination）後，才會寄發宿舍申請連結或 Fact Sheet 住宿代碼。"
            )
        if country_guide:
            for topic in country_guide.topics:
                if topic.topic == "housing" and topic.tips:
                    for tip in topic.tips[:2]:
                        housing_bullets.append(f"【{tip.title}】{tip.detail[:110]}")
                    break
        housing_bullets.append("提醒：獲得母校交換提名不等於保證分發校內宿舍，請勿在收到正式住宿確認前預付不可退還的校外押金。")
        housing_points.append(
            CrossSchoolStructuredPoint(
                category="housing",
                title=f"{entity.school_name_zh} 宿舍與落地住宿申請重點整理",
                summary_zh=(
                    f"彙整全台締約大學對「{entity.school_name_zh}」之住宿欄紀錄與{entity.country_name_zh}落地規範，"
                    "請於通過母校甄選後第一時間核對當期 Fact Sheet 之宿舍申請期限。"
                )[:430],
                bullets=housing_bullets[:5],
                origin_label="跨校締約住宿紀錄與行前指南整理",
                source_title=f"{entity.school_name_zh} 締約母校交換資訊與官方來源",
                source_url=primary_source_url,
                last_checked_at=primary_checked_at,
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
            course_bullets.append("各母校開放申請學制：" + "、".join(degree_notes) + "。")
        college_notes = list(
            dict.fromkeys(
                f"{a.home_short_name}：{a.colleges[:70]}"
                for a in contracted_agreements
                if a.colleges
            )
        )[:3]
        if college_notes:
            course_bullets.append("學院／系所選課範圍：" + "；".join(college_notes) + "。")

        # Check raw PartnerUniversity.course_restrictions across all contracting schools
        restriction_notes: list[str] = []
        for home_id, p_list in entity.home_rows.items():
            for p in p_list:
                if p.course_restrictions and p.course_restrictions.strip():
                    restriction_notes.append(p.course_restrictions.strip()[:110])
        restriction_notes = list(dict.fromkeys(restriction_notes))[:2]
        if restriction_notes:
            course_bullets.extend(f"選課限制摘要：{r}" for r in restriction_notes)

        lang_notes = list(
            dict.fromkeys(
                f"{a.home_short_name}（{a.language_requirement_summary[:70]}）"
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
                title=f"{entity.school_name_zh} 跨校可修讀領域、授課語言與選課限制摘要",
                summary_zh=(
                    f"聚合全台 {len(contracted_agreements)} 所締約大學針對「{entity.school_name_zh}」列載之可申請學院、學制、語檢條件與選課限制，"
                    "協助在撰寫讀書計畫前快速定位可修課方向。"
                )[:430],
                bullets=course_bullets[:5],
                origin_label="全台締約母校簡章與選課條件彙整",
                source_title=f"{entity.school_name_zh} 跨校締約條件官方來源",
                source_url=primary_source_url,
                last_checked_at=primary_checked_at,
            )
        )

    # 4. Cross-School Experience / Preparation Digest
    if not exp_points:
        contracted_names = "、".join(a.home_short_name for a in contracted_agreements[:8])
        exp_bullets = [
            f"全台共有 {len(contracted_agreements)} 所支援大學與「{entity.school_name_zh}」締約（含：{contracted_names}），即使單一母校歷年心得較少，亦可跨校比對各校語檢與名額條件。",
            "讀書計畫準備建議：建議明確列出 3–5 門於該校官網查得之當學期英語或當地語授課課程名稱，並說明與母校畢業學分之銜接。",
        ]
        if country_guide and country_guide.topics:
            first_topic = country_guide.topics[0]
            if first_topic.tips:
                exp_bullets.append(f"【{first_topic.title}提醒】{first_topic.tips[0].title}：{first_topic.tips[0].detail[:100]}")
        exp_points.append(
            CrossSchoolStructuredPoint(
                category="experience_digest",
                title=f"破除單校資訊孤島：{entity.school_name_zh} 跨校申請與行前準備重點",
                summary_zh=(
                    f"透過跨校聚合全台 {len(contracted_agreements)} 所締約大學之官方交換資料與{entity.country_name_zh}行前實務，"
                    "將原本分散於各校國際處系統的門檻、名額與修課限制整合於同一頁面。"
                )[:430],
                bullets=exp_bullets[:5],
                origin_label="跨校聚合情報整理",
                source_title=f"{entity.school_name_zh} 締約母校官方交換頁面",
                source_url=primary_source_url,
                last_checked_at=primary_checked_at,
            )
        )

    return living_points, housing_points, course_points, exp_points


def build_cross_school_partner_page_data(
    *,
    country: str,
    institution: str,
    selected_home: str | None,
    catalogue_loader: Callable[[UniversityProfile], tuple[list[PartnerUniversity], CatalogueSourceStatus | None]],
) -> CrossSchoolPartnerPageData | None:
    """Resolve (country, institution) across all supported universities and return the 2-layer page payload."""
    entities, alias_lookup = build_cross_school_entity_index(catalogue_loader)
    c_slug, _c_zh = resolve_country_slug_and_zh(country)
    inst_raw = unquote(institution or "").strip()
    inst_lower = inst_raw.lower()
    inst_slugified = slugify_english_name(inst_raw)

    canonical_key = (
        alias_lookup.get((c_slug, inst_lower))
        or alias_lookup.get((c_slug, inst_slugified))
        or (
            (c_slug, inst_lower)
            if (c_slug, inst_lower) in entities
            else None
        )
    )
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
    )


def build_cross_school_partner_directory(
    *,
    catalogue_loader: Callable[[UniversityProfile], tuple[list[PartnerUniversity], CatalogueSourceStatus | None]],
    country: str | None = None,
    q: str | None = None,
    home: str | None = None,
    limit: int = 120,
) -> CrossSchoolPartnerDirectory:
    entities, _ = build_cross_school_entity_index(catalogue_loader)
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
            else COUNTRY_DEFAULT_CURRENCY_HINT.get(
                ent.country_name_zh,
                f"聚合 {len(short_names)} 所母校締約方案與{ent.country_name_zh}費用參考",
            )
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
                has_living_cost_digest=True,
                has_housing_digest=True,
                has_course_digest=True,
                experience_count=max(1, len(ent.curated.experience_points) if ent.curated else 1),
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
        if not points:
            problems.append(f"{section_name} must not be empty")
        for idx, pt in enumerate(points):
            where = f"{section_name}[{idx}]"
            if len(pt.summary_zh) > 450:
                problems.append(f"{where}: summary_zh exceeds 450 chars")
            if not pt.bullets:
                problems.append(f"{where}: bullets must not be empty")
            if not pt.source_url.startswith(("https://", "http://")):
                problems.append(f"{where}: invalid source_url {pt.source_url}")
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", pt.last_checked_at):
                problems.append(f"{where}: invalid last_checked_at {pt.last_checked_at}")
            combined = " ".join([pt.title, pt.summary_zh, *pt.bullets])
            if "全台第一" in combined:
                problems.append(f"{where}: contains forbidden claim '全台第一'")
            if re.search(r"[A-Za-z][A-Za-z ,'’\-]{95,}", combined):
                problems.append(f"{where}: contains unparaphrased long English paragraph")
    return problems


def _render_structured_points_html(points: list[CrossSchoolStructuredPoint]) -> str:
    cards: list[str] = []
    for pt in points:
        bullets_html = "".join(f"<li>{escape(b)}</li>" for b in pt.bullets)
        cards.append(
            f'<article class="cs-intel-card" data-category="{escape(pt.category)}">'
            f'<div class="cs-intel-header">'
            f'<span class="cs-origin-badge">{escape(pt.origin_label)}</span>'
            f'<span class="cs-checked-badge">最後查核／整理：{escape(pt.last_checked_at)}</span>'
            f"</div>"
            f"<h3>{escape(pt.title)}</h3>"
            f'<p class="cs-intel-summary">{escape(pt.summary_zh)}</p>'
            f'<ul class="cs-intel-bullets">{bullets_html}</ul>'
            f'<p class="cs-intel-source">'
            f'<span>來源依據：{escape(pt.source_title)}</span> · '
            f'<a href="{escape(pt.source_url)}" target="_blank" rel="noopener noreferrer" data-official-source>'
            f"查閱官方／公開原文連結 ↗</a>"
            f"</p>"
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
</section>

<p class="cs-bottom-links">
  <a href="/partners/{escape(data.country_slug)}">查看{escape(data.country_name_zh)}全部跨校合作大學</a> ·
  <a href="/partners">返回跨校外國大學總覽</a> ·
  <a href="/schools">依台灣母校瀏覽交換指南</a>
</p>
<script type="application/json" id="cs-home-agreements-data">{agreements_json}</script>
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
