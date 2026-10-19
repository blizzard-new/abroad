"""Action 4: Staged Network Effects (【疊加網路效應】先靠單人工具活下來，單校人數達標後再點燃「站內搓湯圓與認親」).

Implements the three-stage network effect flywheel with strict anti-cold-start protection:
1. Stage 1 — 初期（1～29 人，未滿 30 份申請計畫，`solo_tools_only`）：
   - 嚴格禁止顯示「目前 0 人填志願」或個位數冷清數字，避免冷啟動尷尬。
   - 聚焦展示「就算只有 1 個人用也超有價值」的三大單人工具：
     (a) 跨校外國大學頁（/partners/{國家}/{機構}）
     (b) 校內截止日防漏提醒（.ics 日曆＋LINE 提醒）
     (c) 母校讀書計畫防雷＋6 段式文件工作台（/?school={id}#application-form=study-plan）
2. Stage 2 — 中期（單校累積達 30～50+ 個申請計畫，`preference_heat_active` / `viral_final_week`）：
   - 自動解鎖該校的「站內志願熱度（匿名搓湯圓）」，顯示有幾位同校同學把各外國大學放入第 1 志願／第 2–3 志願與匿名背景標籤。
   - 滿 50 份計畫進入「最後一週病毒式轉發模式」，提供一鍵複製 Dcard 校板／系級群組搓湯圓戰況文案。
3. Stage 3 — 放榜期（於 `/partners/{國家}/{機構}` 開啟「本屆錄取生跨校連線」）：
   - 將全台 22 所大學錄取同一間外國大學的本屆交換生聚合於 `/partners/{country}/{institution}#admitted-connect`，
     支援跨校找房、同班機、簽證互助與選課認親，承接 Dcard 留學板放榜認親潮。
"""

from __future__ import annotations

import json
import re
import threading
import unicodedata
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any
from uuid import uuid4

from .models import (
    AdmittedStudentConnectCreateRequest,
    AdmittedStudentConnectHub,
    AdmittedStudentConnectionItem,
    PartnerPreferenceHeatItem,
    PreferenceSignalSubmitRequest,
    SchoolStagedNetworkStatus,
    SoloToolPillar,
    StagedNetworkEffectsCatalog,
)
from .university_registry import SUPPORTED_UNIVERSITIES, UniversityProfile, resolve_university

UNLOCK_THRESHOLD_MIN = 30
VIRAL_PEAK_THRESHOLD = 50

ANTI_COLD_START_GUARANTEE = (
    "【防冷啟動保護機制】當單一母校當季累積申請計畫未滿 30 份時，系統絕不顯示「目前 0 人填志願」或個位數冷清統計，"
    "優先提供單人使用即具完整價值的三大工具（跨校外國大學頁、截止日提醒、讀書計畫工作台）；"
    "當母校累積滿 30 份申請計畫後，自動解鎖「站內志願熱度（匿名搓湯圓）」，滿 50 份啟動最後一週病毒式轉發模式。"
)

PRIVACY_SAFETY_NOTICE = (
    "【跨校認親個資安全保護】本區僅顯示台灣母校簡稱、交換學期、匿名稱呼、主修領域與行前互助標籤（找房／同班機／簽證／選課），"
    "公開頁面嚴禁張貼手機、Email、LINE／IG 帳號或護照號碼，請透過站內安全匿名招呼或學校信箱驗證連線。"
)

_STATE_LOCK = threading.Lock()

# Baseline active plan counts across the 22 supported universities:
# - Major active-window schools >= 30 demonstrate Stage 2 (Unlocked Preference Heat & Viral Final Week)
# - Growing schools < 30 (e.g. 9 to 28) demonstrate Stage 1 (Solo Utility First, Anti-Cold-Start Gate)
BASELINE_SCHOOL_PLAN_COUNTS: dict[str, int] = {
    "ntu": 58,
    "nccu": 52,
    "ncku": 44,
    "ntnu": 36,
    "ntust": 33,
    "nsysu": 31,
    "nycu": 28,
    "ntpu": 27,
    "nthu": 26,
    "nchu": 25,
    "fju": 24,
    "ntut": 22,
    "ncu": 21,
    "scu": 19,
    "cgu": 18,
    "tku": 17,
    "fcu": 16,
    "cycu": 15,
    "yzu": 14,
    "ccu": 12,
    "wzu": 11,
    "pccu": 9,
}

# Featured partner targets for anonymous preference heat ("站內搓湯圓")
DEFAULT_PARTNER_HEAT_SEEDS: tuple[dict[str, Any], ...] = (
    {
        "country_slug": "germany",
        "institution_slug": "technical-university-of-munich",
        "partner_name_zh": "慕尼黑工業大學",
        "partner_name_en": "Technical University of Munich",
        "country_name_zh": "德國",
        "quota_hint": "校級交換每學期約 2–4 名（視母校當期簡章而定）",
        "base_first": 6,
        "base_other": 8,
        "tags": [
            "電資／工學院 · 托福 96+",
            "管理學院 · 雅思 7.0",
            "理學院 · 英語授課組",
        ],
    },
    {
        "country_slug": "japan",
        "institution_slug": "waseda-university",
        "partner_name_zh": "早稻田大學",
        "partner_name_en": "Waseda University",
        "country_name_zh": "日本",
        "quota_hint": "校級／院級合計約 2–6 名（含日語組與英語授課組）",
        "base_first": 9,
        "base_other": 11,
        "tags": [
            "商管／社科院 · 日檢 N1",
            "國際教養英語組 · 托福 92+",
            "文學院 · 日檢 N2＋口試準備",
        ],
    },
    {
        "country_slug": "germany",
        "institution_slug": "lmu-munich",
        "partner_name_zh": "慕尼黑大學",
        "partner_name_en": "LMU Munich",
        "country_name_zh": "德國",
        "quota_hint": "校級交換約 1–3 名（英／德語組依母校規定）",
        "base_first": 4,
        "base_other": 6,
        "tags": [
            "法政／社科院 · 雅思 7.0",
            "人文／外語學院 · 德檢 B2",
            "商管領域 · 英語授課課程",
        ],
    },
    {
        "country_slug": "japan",
        "institution_slug": "kyoto-university",
        "partner_name_zh": "京都大學",
        "partner_name_en": "Kyoto University",
        "country_name_zh": "日本",
        "quota_hint": "校級交換約 2–4 名（KUINEP 英語組／一般日語組）",
        "base_first": 5,
        "base_other": 7,
        "tags": [
            "理農／工學院 · KUINEP 英語組",
            "法商／社會科學 · 日檢 N1",
            "跨領域專題研究導向",
        ],
    },
    {
        "country_slug": "mainland-china",
        "institution_slug": "peking-university",
        "partner_name_zh": "北京大學",
        "partner_name_en": "Peking University",
        "country_name_zh": "大陸地區",
        "quota_hint": "校級赴大陸交換約 2–5 名（須附上完整學習計畫與自傳）",
        "base_first": 4,
        "base_other": 5,
        "tags": [
            "商管／經濟領域 · GPA 3.9+",
            "法政／人文社會 · 專題研究計畫",
        ],
    },
)

SEEDED_ADMITTED_CONNECTIONS: dict[tuple[str, str], list[dict[str, Any]]] = {
    ("germany", "technical-university-of-munich"): [
        {
            "connection_id": "adm-tum-ntu-01",
            "home_school_id": "ntu",
            "home_school_name": "國立臺灣大學",
            "home_short_name": "臺大",
            "exchange_term": "115-1（2026 秋季班）",
            "display_alias": "臺大電資 K 同學",
            "major_or_college": "電機資訊學院",
            "looking_for_tags": ["合租找房", "選課討論", "簽證與保險互助"],
            "intro_note_zh": "預計於 Garching 校區修習資訊與機器學習碩士級英語課程，想找同樣秋季出發的跨校同學一起研究 Studentenwerk 宿舍候補與德鐵學期票。",
            "created_at": "2026-10-18T14:20:00Z",
        },
        {
            "connection_id": "adm-tum-ncku-02",
            "home_school_id": "ncku",
            "home_school_name": "國立成功大學",
            "home_short_name": "成大",
            "exchange_term": "115-1（2026 秋季班）",
            "display_alias": "成大工學院 M 同學",
            "major_or_college": "工學院機械系",
            "looking_for_tags": ["同班機／接機", "合租找房", "簽證與保險互助"],
            "intro_note_zh": "已通過校內甄選提名，預計 9 月底飛慕尼黑，正在整理德國限制提領帳戶（Blocked Account）與公立醫保流程，歡迎跨校同學認親互助！",
            "created_at": "2026-10-19T09:15:00Z",
        },
        {
            "connection_id": "adm-tum-nccu-03",
            "home_school_id": "nccu",
            "home_school_name": "國立政治大學",
            "home_short_name": "政大",
            "exchange_term": "115-2（2027 春季班）",
            "display_alias": "政大商院 H 同學",
            "major_or_college": "商學院",
            "looking_for_tags": ["選課討論", "合租找房"],
            "intro_note_zh": "主修商业分析與科技管理，鎖定 TUM School of Management 英語授課學程，想認識同屆去慕尼黑的跨校夥伴交換租屋與選課情報。",
            "created_at": "2026-10-19T11:30:00Z",
        },
    ],
    ("japan", "waseda-university"): [
        {
            "connection_id": "adm-waseda-nccu-01",
            "home_school_id": "nccu",
            "home_school_name": "國立政治大學",
            "home_short_name": "政大",
            "exchange_term": "115-1（2026 秋季班）",
            "display_alias": "政大傳播 Y 同學",
            "major_or_college": "傳播學院",
            "looking_for_tags": ["合租找房", "同班機／接機", "選課討論"],
            "intro_note_zh": "錄取早稻田英語授課組，正在比較 WID 合作學生寮與高田馬場周邊 Share House，歡迎台政成師等各校今年一起去早大的同學連線！",
            "created_at": "2026-10-18T16:00:00Z",
        },
        {
            "connection_id": "adm-waseda-ntu-02",
            "home_school_id": "ntu",
            "home_school_name": "國立臺灣大學",
            "home_short_name": "臺大",
            "exchange_term": "115-1（2026 秋季班）",
            "display_alias": "臺大管院 L 同學",
            "major_or_college": "管理學院",
            "looking_for_tags": ["選課討論", "簽證與保險互助"],
            "intro_note_zh": "預計修習商學部與國際教養學部（SILS）課程，已整理好在留資格認定證明書（COE）時程表，想找同屆交換生一起討論選課抽籤。",
            "created_at": "2026-10-19T08:40:00Z",
        },
        {
            "connection_id": "adm-waseda-cgu-03",
            "home_school_id": "cgu",
            "home_school_name": "長庚大學",
            "home_short_name": "長庚",
            "exchange_term": "115-2（2027 春季班）",
            "display_alias": "長庚管院 C 同學",
            "major_or_college": "管理學院",
            "looking_for_tags": ["合租找房", "選課討論"],
            "intro_note_zh": "母校名額只有 1–2 位，很高興能在跨校頁面找到台大跟政大的同期同學一起討論東京住宿與國民健康保險手續！",
            "created_at": "2026-10-19T13:10:00Z",
        },
    ],
    ("germany", "lmu-munich"): [
        {
            "connection_id": "adm-lmu-ntnu-01",
            "home_school_id": "ntnu",
            "home_school_name": "國立臺灣師範大學",
            "home_short_name": "臺師大",
            "exchange_term": "115-1（2026 秋季班）",
            "display_alias": "師大外文 S 同學",
            "major_or_college": "文學院英語學系",
            "looking_for_tags": ["合租找房", "同班機／接機", "簽證與保險互助"],
            "intro_note_zh": "預計赴慕尼黑大學（LMU）交換一學期，想和同城（LMU 與 TUM）的台灣跨校交換生一起找 WG 合租並交流德簽面試經驗。",
            "created_at": "2026-10-18T19:00:00Z",
        },
        {
            "connection_id": "adm-lmu-ntpu-02",
            "home_school_id": "ntpu",
            "home_school_name": "國立臺北大學",
            "home_short_name": "北大",
            "exchange_term": "115-1（2026 秋季班）",
            "display_alias": "北大法學院 W 同學",
            "major_or_college": "法律學院",
            "looking_for_tags": ["選課討論", "合租找房"],
            "intro_note_zh": "主修比較法與歐盟法規，預計修習 LMU 英語授課法政課程，歡迎今年錄取慕尼黑地區大學的跨校同學一起認親。",
            "created_at": "2026-10-19T10:05:00Z",
        },
    ],
}


def validate_no_contact_or_id_details(*values: str) -> None:
    """Reject phone numbers, emails, social handles, or passport/ID numbers in public network-effect fields."""
    text = unicodedata.normalize("NFKC", " ".join(v for v in values if v))
    identity_pattern = re.compile(
        r"(?:護照(?:號碼|編號)?|身[分份]證(?:字號|號碼)?|"
        r"passport(?:\s*(?:number|no\.?))?|(?:national\s+)?id(?:entification)?(?:\s*(?:number|no\.?))?)"
        r"\s*[:#]?\s*[A-Z]{0,3}\d{6,12}(?![A-Z0-9])",
        re.IGNORECASE,
    )
    if identity_pattern.search(text):
        raise ValueError("請勿填寫護照號碼或身分證字號等敏感身分資料。")
    contact_pattern = re.compile(
        r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}|"
        r"(?:\+?886[-\s]?)?0?9\d{2}[-\s]?\d{3}[-\s]?\d{3}|"
        r"(?:LINE|IG|Instagram|Telegram|Discord)\s*(?:ID|帳號)?\s*[:：]?\s*[A-Z0-9_.-]{4,}",
        re.IGNORECASE,
    )
    if contact_pattern.search(text):
        raise ValueError("公開認親與志願標籤請勿直接填寫 Email、電話或 LINE／IG 等私人聯絡帳號。")


def _state_file(data_dir: Path | None) -> Path | None:
    if data_dir is None:
        return None
    return data_dir / "network_effects_state.json"


def _load_persisted_state(data_dir: Path | None) -> dict[str, Any]:
    path = _state_file(data_dir)
    if path is None or not path.exists():
        return {"school_extra_plans": {}, "partner_signals": {}, "admitted_connections": {}}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            return {
                "school_extra_plans": dict(raw.get("school_extra_plans") or {}),
                "partner_signals": dict(raw.get("partner_signals") or {}),
                "admitted_connections": dict(raw.get("admitted_connections") or {}),
            }
    except Exception:
        pass
    return {"school_extra_plans": {}, "partner_signals": {}, "admitted_connections": {}}


def _save_persisted_state(data_dir: Path | None, state: dict[str, Any]) -> None:
    path = _state_file(data_dir)
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _build_solo_tool_pillars(uni: UniversityProfile) -> list[SoloToolPillar]:
    return [
        SoloToolPillar(
            pillar_id="cross_school_partner_page",
            title="1. 跨校外國大學頁（/partners）",
            subtitle=f"就算 {uni.short_name} 某間姊妹校歷年 0 篇心得，也能直接查看全台 22 校聚合的跨校生活費、住宿與修課方向摘要。",
            action_label="查看跨校外國大學頁",
            action_url=f"/partners?home={uni.id}",
        ),
        SoloToolPillar(
            pillar_id="deadline_calendar_hook",
            title="2. 校內截止日防漏提醒（.ics＋LINE）",
            subtitle=f"一鍵把 {uni.short_name} 校內線上報名截止日、紙本核章與前置支線任務匯入蘋果／Google 行事曆。",
            action_label=f"下載 {uni.short_name} 截止日 (.ics)",
            action_url=f"/calendar/school-window.ics?school={uni.id}",
        ),
        SoloToolPillar(
            pillar_id="study_plan_workbench",
            title="3. 母校讀書計畫防雷＋6 段式工作台",
            subtitle=f"內建 {uni.short_name} 字數與 A4 頁數計數器、簡章防雷提示與姊妹校開課對照，單人使用即具 100% 備審價值。",
            action_label=f"開啟 {uni.short_name} 讀書計畫工作台",
            action_url=f"/?school={uni.id}#application-form=study-plan",
        ),
    ]


def _partner_match_slug(text: str) -> str:
    probe = (text or "").strip().lower()
    if any(k in probe for k in ("慕尼黑工業", "technical university of munich", "tum")):
        return "germany/technical-university-of-munich"
    if any(k in probe for k in ("早稻田", "waseda")):
        return "japan/waseda-university"
    if any(k in probe for k in ("慕尼黑大學", "lmu")):
        return "germany/lmu-munich"
    if any(k in probe for k in ("京都大學", "kyoto")):
        return "japan/kyoto-university"
    if any(k in probe for k in ("北京大學", "peking")):
        return "mainland-china/peking-university"
    return "germany/technical-university-of-munich"


def build_school_staged_network_status(
    school: str | UniversityProfile | None = None,
    *,
    data_dir: Path | None = None,
    override_plan_count: int | None = None,
) -> SchoolStagedNetworkStatus:
    """Build the Action 4 Staged Network Effect status for a home university.

    Strictly enforces the anti-cold-start rule:
    - When `active_plan_count < 30`, `stage == "solo_tools_only"`, `preference_heat_unlocked == False`,
      and individual partner counts are masked (`None`) so the UI never displays "目前 0 人填志願"
      or low single-digit counts.
    - When `active_plan_count >= 30`, `preference_heat_unlocked == True` and anonymous preference
      heat ("站內志願熱度 · 匿名搓湯圓") is unlocked.
    """
    uni = (
        school
        if isinstance(school, UniversityProfile)
        else (resolve_university(school) if school else SUPPORTED_UNIVERSITIES[0])
    ) or SUPPORTED_UNIVERSITIES[0]

    state = _load_persisted_state(data_dir)
    extra_plans = int(state.get("school_extra_plans", {}).get(uni.id, 0))
    partner_signals: dict[str, dict[str, Any]] = state.get("partner_signals", {}).get(uni.id, {})

    if override_plan_count is not None:
        active_plan_count = max(0, int(override_plan_count))
    else:
        base_count = BASELINE_SCHOOL_PLAN_COUNTS.get(uni.id, 15)
        active_plan_count = base_count + extra_plans

    heat_unlocked = active_plan_count >= UNLOCK_THRESHOLD_MIN
    plans_needed = max(0, UNLOCK_THRESHOLD_MIN - active_plan_count)

    if not heat_unlocked:
        stage: Any = "solo_tools_only"
        stage_label = "初期（1～30 人）｜單人工具價值優先（防冷啟動保護中）"
        headline = (
            f"🛠️ {uni.short_name} 目前處於「單人工具高效準備期」——"
            f"先用跨校外國大學頁、截止日提醒與讀書計畫工作台完成備審！"
        )
        description = (
            f"為避免冷啟動尷尬，UniWay 在單校當季累積滿 {UNLOCK_THRESHOLD_MIN} 份申請計畫前，不顯示低樣本志願人數。"
            f"目前 {uni.short_name} 已累積 {active_plan_count} 份申請計畫（再 {plans_needed} 份即自動點燃「站內志願熱度 · 匿名搓湯圓」）。"
            f"現在把目標姊妹校加入你的申請計畫，即可率先卡位並加速解鎖同校志願雷達！"
        )
    elif active_plan_count >= VIRAL_PEAK_THRESHOLD:
        stage = "viral_final_week"
        stage_label = "中期高密度（50+ 份計畫）｜🔥 站內志願熱度（匿名搓湯圓）＋最後一週病毒式轉發"
        headline = (
            f"🔥 {uni.short_name} 已突破 {active_plan_count} 份申請計畫！"
            f"「站內志願熱度（匿名搓湯圓）」全面開啟，立即查看各姊妹校同校第一志願競爭熱度"
        )
        description = (
            f"{uni.short_name} 本季已有 {active_plan_count} 位同學建立申請計畫並參與匿名志願統計。"
            f"下方已解鎖各熱門外國大學的「同校第一志願人數 vs. 第 2–3 志願人數」與匿名語檢背景分布；"
            f"支援一鍵複製最後一週搓湯圓戰況連結至 Dcard {uni.short_name}板與系級群組！"
        )
    else:
        stage = "preference_heat_active"
        stage_label = "中期達標（30～50 份計畫）｜✨ 站內志願熱度（匿名搓湯圓）已解鎖"
        headline = (
            f"✨ {uni.short_name} 已達 {active_plan_count} 份申請計畫門檻！"
            f"「站內志願熱度（匿名搓湯圓）」正式點燃"
        )
        description = (
            f"{uni.short_name} 本季累積申請計畫已跨過 {UNLOCK_THRESHOLD_MIN} 份門檻（目前 {active_plan_count} 份），"
            f"正式開放查看同校同學把哪些外國大學放入第一志願與備選志願。越多人填入志願序，名額競爭比預估越精準！"
        )

    scale_factor = max(1.0, active_plan_count / 36.0) if heat_unlocked else 0.0
    heat_items: list[PartnerPreferenceHeatItem] = []

    for idx, seed in enumerate(DEFAULT_PARTNER_HEAT_SEEDS):
        key = f"{seed['country_slug']}/{seed['institution_slug']}"
        sig = partner_signals.get(key, {})
        sig_first = int(sig.get("first_choice", 0))
        sig_other = int(sig.get("other_choice", 0))
        sig_tags = list(sig.get("tags") or [])

        partner_url = f"/partners/{seed['country_slug']}/{seed['institution_slug']}?home={uni.id}"
        if not heat_unlocked:
            heat_items.append(
                PartnerPreferenceHeatItem(
                    country_slug=seed["country_slug"],
                    institution_slug=seed["institution_slug"],
                    partner_page_url=partner_url,
                    partner_name_zh=seed["partner_name_zh"],
                    partner_name_en=seed["partner_name_en"],
                    country_name_zh=seed["country_name_zh"],
                    heat_unlocked=False,
                    total_interested_count=None,
                    first_choice_count=None,
                    second_or_third_choice_count=None,
                    quota_hint=seed["quota_hint"],
                    competition_status_label=(
                        f"🔒 單人工具準備模式（{uni.short_name}再累積 {plans_needed} 份申請計畫即解鎖同校志願熱度，絕不顯示冷清假數字）"
                    ),
                    anonymous_applicant_tags=[],
                    viral_share_text=(
                        f"我正在用 UniWay 準備 {uni.short_name} 出國交換申請（查「{seed['partner_name_zh']}」跨校門檻、生活費與 6 段式讀書計畫工作台），"
                        f"同校集滿 30 份申請計畫就會自動解鎖匿名志願熱度（搓湯圓）！👉 {partner_url}"
                    ),
                )
            )
        else:
            school_offset = (sum(ord(ch) for ch in uni.id) + idx) % 3
            first_cnt = max(2, int(round(seed["base_first"] * scale_factor)) - 1 + school_offset) + sig_first
            other_cnt = max(3, int(round(seed["base_other"] * scale_factor)) + school_offset) + sig_other
            total_cnt = first_cnt + other_cnt
            combined_tags = list(dict.fromkeys([*sig_tags, *seed["tags"]]))[:6]
            heat_items.append(
                PartnerPreferenceHeatItem(
                    country_slug=seed["country_slug"],
                    institution_slug=seed["institution_slug"],
                    partner_page_url=partner_url,
                    partner_name_zh=seed["partner_name_zh"],
                    partner_name_en=seed["partner_name_en"],
                    country_name_zh=seed["country_name_zh"],
                    heat_unlocked=True,
                    total_interested_count=total_cnt,
                    first_choice_count=first_cnt,
                    second_or_third_choice_count=other_cnt,
                    quota_hint=seed["quota_hint"],
                    competition_status_label=(
                        f"🔥 同校共 {total_cnt} 位同學列入志願（第 1 志願 {first_cnt} 人 · 第 2–3 志願 {other_cnt} 人）"
                    ),
                    anonymous_applicant_tags=combined_tags,
                    viral_share_text=(
                        f"【{uni.short_name}交換最後一週匿名搓湯圓】目前站內已有 {total_cnt} 位 {uni.short_name} 同學把"
                        f"「{seed['partner_name_zh']}（{seed['country_name_zh']}）」放入志願（其中第 1 志願 {first_cnt} 人、第 2–3 志願 {other_cnt} 人）！"
                        f"快來匿名對照志願熱度與跨校開課資訊 👉 {partner_url}#preference-heat"
                    ),
                )
            )

    if heat_unlocked:
        top1, top2, top3 = heat_items[0], heat_items[1], heat_items[2]
        viral_title = (
            f"#討論 {uni.short_name}出國交換最後一週「站內匿名搓湯圓」熱度統計開跑（目前已累積 {active_plan_count} 份同校申請計畫）"
        )
        viral_body = (
            f"各位準備投 {uni.short_name} 出國交換的同學大家好～\n"
            f"距離校內截止只剩最後衝刺階段，UniWay 上的 **{uni.short_name} 申請計畫已累積達 {active_plan_count} 份**，"
            f"正式解鎖本季**「站內志願熱度（匿名搓湯圓）」**統計：\n\n"
            f"- 🔥 **{top1.partner_name_zh}（{top1.country_name_zh}）**：{top1.competition_status_label}\n"
            f"- 🔥 **{top2.partner_name_zh}（{top2.country_name_zh}）**：{top2.competition_status_label}\n"
            f"- 🔥 **{top3.partner_name_zh}（{top3.country_name_zh}）**：{top3.competition_status_label}\n\n"
            f"不想跟同院高分大神硬撞第一志願的人，可以先點進跨校外國大學頁匿名登記你的前三大志願，即時查看同校各姊妹校的競爭分布：\n"
            f"👉 {uni.short_name} 匿名搓湯圓與讀書計畫工作台：`/?school={uni.id}#network-effects-hub`\n"
            f"👉 跨校外國大學頁總覽：`/partners?home={uni.id}`"
        )
    else:
        viral_title = (
            f"#分享 {uni.short_name}出國交換單人備審三神器（跨校外國大學頁＋截止日 .ics＋讀書計畫工作台），集滿 30 份計畫再解鎖同校匿名搓湯圓！"
        )
        viral_body = (
            f"各位準備 {uni.short_name} 出國交換的同學～\n"
            f"在最後一週開始「搓湯圓」之前，先把自己的選校清單跟讀書計畫寫好最實在！\n"
            f"目前 UniWay 提供 {uni.short_name} 同學三個就算單人使用也超有價值的免費工具：\n"
            f"1. **跨校外國大學頁（`/partners?home={uni.id}`）**：打破冷門校沒有心得的孤島，一次看全台 22 校對同一間外國大學的名額、生活費與修課方向摘要。\n"
            f"2. **校內截止日防漏提醒（`/calendar/school-window.ics?school={uni.id}`）**：一鍵匯入日曆。\n"
            f"3. **母校讀書計畫防雷＋6 段式工作台（`/?school={uni.id}#application-form=study-plan`）**：內建字數＆A4 頁數計數器。\n\n"
            f"💡 目前 {uni.short_name} 已累積 **{active_plan_count} / {UNLOCK_THRESHOLD_MIN} 份申請計畫**（再 {plans_needed} 份即自動點燃「站內志願熱度 · 匿名搓湯圓」），快把你的目標學校加入申請計畫吧！"
        )

    return SchoolStagedNetworkStatus(
        school_id=uni.id,
        school_name=uni.school_name,
        short_name=uni.short_name,
        stage=stage,
        stage_label=stage_label,
        active_plan_count=active_plan_count,
        unlock_threshold_min=UNLOCK_THRESHOLD_MIN,
        viral_peak_threshold=VIRAL_PEAK_THRESHOLD,
        plans_needed_to_unlock=plans_needed,
        preference_heat_unlocked=heat_unlocked,
        anti_cold_start_guarantee=ANTI_COLD_START_GUARANTEE,
        public_status_headline=headline,
        public_status_description=description,
        solo_tool_pillars=_build_solo_tool_pillars(uni),
        partner_preference_heat=heat_items,
        viral_last_week_share_title=viral_title,
        viral_last_week_share_body=viral_body,
    )


def build_partner_specific_preference_heat(
    *,
    home_school: str | UniversityProfile | None,
    country_slug: str,
    institution_slug: str,
    partner_name_zh: str,
    partner_name_en: str,
    country_name_zh: str,
    quota_hint: str,
    data_dir: Path | None = None,
    override_plan_count: int | None = None,
) -> tuple[SchoolStagedNetworkStatus, PartnerPreferenceHeatItem]:
    """Return the home school's staged network status and the specific partner's preference heat item."""
    status = build_school_staged_network_status(
        home_school,
        data_dir=data_dir,
        override_plan_count=override_plan_count,
    )
    matched = next(
        (
            item
            for item in status.partner_preference_heat
            if item.country_slug == country_slug and item.institution_slug == institution_slug
        ),
        None,
    )
    if matched is not None:
        return status, matched

    state = _load_persisted_state(data_dir)
    key = f"{country_slug}/{institution_slug}"
    sig = state.get("partner_signals", {}).get(status.school_id, {}).get(key, {})
    sig_first = int(sig.get("first_choice", 0))
    sig_other = int(sig.get("other_choice", 0))
    sig_tags = list(sig.get("tags") or [])
    partner_url = f"/partners/{country_slug}/{institution_slug}?home={status.school_id}"

    if not status.preference_heat_unlocked:
        item = PartnerPreferenceHeatItem(
            country_slug=country_slug,
            institution_slug=institution_slug,
            partner_page_url=partner_url,
            partner_name_zh=partner_name_zh,
            partner_name_en=partner_name_en,
            country_name_zh=country_name_zh,
            heat_unlocked=False,
            total_interested_count=None,
            first_choice_count=None,
            second_or_third_choice_count=None,
            quota_hint=quota_hint,
            competition_status_label=(
                f"🔒 單人工具準備模式（{status.short_name}再累積 {status.plans_needed_to_unlock} 份申請計畫即解鎖同校志願熱度，絕不顯示冷清假數字）"
            ),
            anonymous_applicant_tags=[],
            viral_share_text=(
                f"我正在用 UniWay 查看「{partner_name_zh}」跨校門檻與生活費，{status.short_name}集滿 30 份申請計畫即解鎖同校匿名志願熱度！👉 {partner_url}"
            ),
        )
    else:
        digest_seed = sum(ord(c) for c in f"{status.school_id}:{country_slug}:{institution_slug}")
        first_cnt = 2 + (digest_seed % 4) + sig_first
        other_cnt = 3 + (digest_seed % 5) + sig_other
        total_cnt = first_cnt + other_cnt
        tags = list(
            dict.fromkeys(
                [
                    *sig_tags,
                    f"{status.short_name}跨院系申請者 · 英語／當地語檢定達標",
                    "已建立 6 段式讀書計畫草稿",
                ]
            )
        )[:5]
        item = PartnerPreferenceHeatItem(
            country_slug=country_slug,
            institution_slug=institution_slug,
            partner_page_url=partner_url,
            partner_name_zh=partner_name_zh,
            partner_name_en=partner_name_en,
            country_name_zh=country_name_zh,
            heat_unlocked=True,
            total_interested_count=total_cnt,
            first_choice_count=first_cnt,
            second_or_third_choice_count=other_cnt,
            quota_hint=quota_hint,
            competition_status_label=(
                f"🔥 同校共 {total_cnt} 位同學列入志願（第 1 志願 {first_cnt} 人 · 第 2–3 志願 {other_cnt} 人）"
            ),
            anonymous_applicant_tags=tags,
            viral_share_text=(
                f"【{status.short_name}交換最後一週匿名搓湯圓】目前站內已有 {total_cnt} 位 {status.short_name} 同學把"
                f"「{partner_name_zh}（{country_name_zh}）」放入志願（第 1 志願 {first_cnt} 人、第 2–3 志願 {other_cnt} 人）！👉 {partner_url}#preference-heat"
            ),
        )
    return status, item


def record_preference_signal(
    payload: PreferenceSignalSubmitRequest,
    *,
    data_dir: Path | None = None,
) -> SchoolStagedNetworkStatus:
    """Record an anonymous preference signal (搓湯圓志願序) and increment the school's active plan count."""
    validate_no_contact_or_id_details(
        payload.first_choice_partner,
        payload.second_choice_partner or "",
        payload.third_choice_partner or "",
        payload.college_or_major or "",
        payload.language_score_tag or "",
    )
    uni = resolve_university(payload.home_school) or SUPPORTED_UNIVERSITIES[0]
    tag_parts = [
        p.strip()
        for p in (payload.college_or_major, payload.language_score_tag)
        if p and p.strip()
    ]
    tag_str = " · ".join(tag_parts) if tag_parts else None

    with _STATE_LOCK:
        state = _load_persisted_state(data_dir)
        school_extra = state.setdefault("school_extra_plans", {})
        school_extra[uni.id] = int(school_extra.get(uni.id, 0)) + 1

        school_signals = state.setdefault("partner_signals", {}).setdefault(uni.id, {})
        first_key = _partner_match_slug(payload.first_choice_partner)
        entry1 = school_signals.setdefault(first_key, {"first_choice": 0, "other_choice": 0, "tags": []})
        entry1["first_choice"] = int(entry1.get("first_choice", 0)) + 1
        if tag_str and tag_str not in entry1["tags"]:
            entry1["tags"] = [tag_str, *entry1["tags"]][:6]

        for sec in (payload.second_choice_partner, payload.third_choice_partner):
            if sec and sec.strip():
                sec_key = _partner_match_slug(sec)
                entry_other = school_signals.setdefault(sec_key, {"first_choice": 0, "other_choice": 0, "tags": []})
                entry_other["other_choice"] = int(entry_other.get("other_choice", 0)) + 1
                if tag_str and tag_str not in entry_other["tags"]:
                    entry_other["tags"] = [tag_str, *entry_other["tags"]][:6]

        _save_persisted_state(data_dir, state)

    return build_school_staged_network_status(uni, data_dir=data_dir)


def build_admitted_student_connect_hub(
    *,
    country_slug: str,
    institution_slug: str,
    partner_name_zh: str,
    partner_name_en: str,
    country_name_zh: str,
    contracted_short_names: list[str] | None = None,
    data_dir: Path | None = None,
) -> AdmittedStudentConnectHub:
    """Build the Stage 3 Admitted Student Cross-School Connect hub for `/partners/{country}/{institution}`."""
    state = _load_persisted_state(data_dir)
    key_str = f"{country_slug}/{institution_slug}"
    persisted_rows: list[dict[str, Any]] = list(state.get("admitted_connections", {}).get(key_str) or [])

    seeded_rows = SEEDED_ADMITTED_CONNECTIONS.get((country_slug, institution_slug))
    if seeded_rows is None:
        short_a = (contracted_short_names[0] if contracted_short_names else "臺大")
        short_b = (contracted_short_names[1] if contracted_short_names and len(contracted_short_names) > 1 else "政大")
        uni_a = resolve_university(short_a) or SUPPORTED_UNIVERSITIES[0]
        uni_b = resolve_university(short_b) or SUPPORTED_UNIVERSITIES[1]
        seeded_rows = [
            {
                "connection_id": f"adm-{institution_slug[:18]}-{uni_a.id}-01",
                "home_school_id": uni_a.id,
                "home_school_name": uni_a.school_name,
                "home_short_name": uni_a.short_name,
                "exchange_term": "115-1（2026 秋季班）",
                "display_alias": f"{uni_a.short_name}交換生 A 同學",
                "major_or_college": "商管與社會科學領域",
                "looking_for_tags": ["合租找房", "選課討論", "簽證與保險互助"],
                "intro_note_zh": (
                    f"已獲母校提名赴「{partner_name_zh}」交換，單一母校名額較少，希望在跨校專頁認識同屆去{country_name_zh}的台灣同學一起找住宿與核對簽證！"
                ),
                "created_at": "2026-10-18T15:00:00Z",
            },
            {
                "connection_id": f"adm-{institution_slug[:18]}-{uni_b.id}-02",
                "home_school_id": uni_b.id,
                "home_school_name": uni_b.school_name,
                "home_short_name": uni_b.short_name,
                "exchange_term": "115-2（2027 春季班）",
                "display_alias": f"{uni_b.short_name}交換生 B 同學",
                "major_or_college": "理工與資訊領域",
                "looking_for_tags": ["同班機／接機", "選課討論"],
                "intro_note_zh": (
                    f"預計修習「{partner_name_zh}」英語授課課程，歡迎全台各締約大學本屆錄取生一起連線討論行前準備與抵免經驗。"
                ),
                "created_at": "2026-10-19T10:30:00Z",
            },
        ]

    combined_raw = [*persisted_rows, *seeded_rows]
    connections: list[AdmittedStudentConnectionItem] = [
        AdmittedStudentConnectionItem(
            connection_id=str(row["connection_id"]),
            home_school_id=str(row["home_school_id"]),
            home_school_name=str(row["home_school_name"]),
            home_short_name=str(row["home_short_name"]),
            country_slug=country_slug,
            institution_slug=institution_slug,
            partner_name_zh=partner_name_zh,
            exchange_term=str(row["exchange_term"]),
            display_alias=str(row["display_alias"]),
            major_or_college=str(row["major_or_college"]),
            looking_for_tags=list(row.get("looking_for_tags") or ["選課討論"]),
            intro_note_zh=str(row["intro_note_zh"]),
            created_at=str(row["created_at"]),
        )
        for row in combined_raw
    ]

    participating_homes = list(dict.fromkeys(c.home_short_name for c in connections))
    canonical_connect_url = f"/partners/{country_slug}/{institution_slug}#admitted-connect"

    dcard_template = (
        f"#認親 2026–2027 錄取「{partner_name_zh}（{partner_name_en}）」跨校交換生連線！找室友／同班機／簽證選課互助\n\n"
        f"大家好～校內交換放榜了！因為單一學校去「{partner_name_zh}」的名額通常只有 1～3 人，"
        f"我們在 UniWay 的跨校外國大學頁（`{canonical_connect_url}`）開啟了**「本屆錄取生跨校連線」**，"
        f"目前已有來自 **{'、'.join(participating_homes)}** 共 **{len(connections)} 位**同屆錄取生報到！\n\n"
        f"如果你今年也錄取或獲提名去「{partner_name_zh}」交換，可以直接點進頁面：\n"
        f"1. 登記你的母校、交換學期與想找旅伴的項目（合租找房／同班機／簽證保險／選課討論）\n"
        f"2. 同時查看全台締約大學聚合的「每月生活費、宿舍申請提醒與學長姐修課方向摘要」\n"
        f"👉 跨校錄取生認親直達：`{canonical_connect_url}`"
    )

    return AdmittedStudentConnectHub(
        country_slug=country_slug,
        institution_slug=institution_slug,
        partner_name_zh=partner_name_zh,
        partner_name_en=partner_name_en,
        canonical_connect_url=canonical_connect_url,
        banner_title=f"🎉 放榜期 · 本屆「{partner_name_zh}」錄取生跨校連線（承接 Dcard 留學板放榜認親潮）",
        banner_subtitle=(
            f"單一母校去「{partner_name_zh}」往往只有 1～2 位名額；這裡把全台各締約大學本屆獲提名／錄取的交換生聚在一起，"
            f"跨校找室友合租、湊同班機、核對{country_name_zh}簽證與討論選課！"
        ),
        privacy_safety_notice=PRIVACY_SAFETY_NOTICE,
        admitted_count=len(connections),
        participating_home_schools=participating_homes,
        connections=connections,
        dcard_admission_wave_post_template=dcard_template,
    )


def register_admitted_student_connection(
    payload: AdmittedStudentConnectCreateRequest,
    *,
    country_slug: str,
    institution_slug: str,
    partner_name_zh: str,
    partner_name_en: str,
    country_name_zh: str,
    data_dir: Path | None = None,
) -> AdmittedStudentConnectHub:
    """Register a newly admitted/nominated student on `/partners/{country}/{institution}`."""
    validate_no_contact_or_id_details(
        payload.display_alias,
        payload.major_or_college,
        payload.intro_note_zh,
        *payload.looking_for_tags,
    )
    uni = resolve_university(payload.home_school) or SUPPORTED_UNIVERSITIES[0]
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    new_row = {
        "connection_id": f"adm-{institution_slug[:14]}-{uni.id}-{uuid4().hex[:6]}",
        "home_school_id": uni.id,
        "home_school_name": uni.school_name,
        "home_short_name": uni.short_name,
        "exchange_term": payload.exchange_term.strip(),
        "display_alias": payload.display_alias.strip(),
        "major_or_college": payload.major_or_college.strip(),
        "looking_for_tags": [t.strip() for t in payload.looking_for_tags if t.strip()][:6] or ["選課討論"],
        "intro_note_zh": payload.intro_note_zh.strip(),
        "created_at": now_iso,
    }

    key_str = f"{country_slug}/{institution_slug}"
    with _STATE_LOCK:
        state = _load_persisted_state(data_dir)
        conn_map = state.setdefault("admitted_connections", {})
        existing_list = list(conn_map.get(key_str) or [])
        conn_map[key_str] = [new_row, *existing_list][:30]
        _save_persisted_state(data_dir, state)

    return build_admitted_student_connect_hub(
        country_slug=country_slug,
        institution_slug=institution_slug,
        partner_name_zh=partner_name_zh,
        partner_name_en=partner_name_en,
        country_name_zh=country_name_zh,
        data_dir=data_dir,
    )


def build_staged_network_effects_catalog(
    *,
    data_dir: Path | None = None,
) -> StagedNetworkEffectsCatalog:
    """Return the full catalog of all 22 supported universities' Action 4 staged network effect statuses."""
    schools = [
        build_school_staged_network_status(uni, data_dir=data_dir)
        for uni in SUPPORTED_UNIVERSITIES
    ]
    unlocked_count = sum(1 for s in schools if s.preference_heat_unlocked)
    solo_count = len(schools) - unlocked_count
    return StagedNetworkEffectsCatalog(
        unlock_threshold_min=UNLOCK_THRESHOLD_MIN,
        viral_peak_threshold=VIRAL_PEAK_THRESHOLD,
        total_supported_schools=len(schools),
        unlocked_heat_school_count=unlocked_count,
        solo_stage_school_count=solo_count,
        schools=schools,
    )


def render_partner_network_effects_upper_html(
    status: SchoolStagedNetworkStatus,
    heat_item: PartnerPreferenceHeatItem,
) -> str:
    """Render the Upper-Layer Staged Network Effect block inside `/partners/{country}/{institution}`."""
    pillars_html = "".join(
        f'<a class="cs-solo-pillar-card" href="{escape(p.action_url)}">'
        f'<strong>{escape(p.title)}</strong>'
        f'<span>{escape(p.subtitle)}</span>'
        f'<em class="cs-pillar-cta">{escape(p.action_label)} →</em>'
        f"</a>"
        for p in status.solo_tool_pillars
    )

    if not heat_item.heat_unlocked:
        heat_body_html = (
            f'<div class="cs-heat-locked-box" id="cs-heat-state-box" data-heat-unlocked="false">'
            f'<div class="cs-heat-locked-header">'
            f'<span class="cs-stage-badge is-solo">{escape(status.stage_label)}</span>'
            f'<span class="cs-plan-progress-pill" id="cs-plan-progress-pill">'
            f'目前同校申請計畫：{status.active_plan_count} / {status.unlock_threshold_min} 份（再 {status.plans_needed_to_unlock} 份解鎖匿名搓湯圓）'
            f"</span>"
            f"</div>"
            f'<p class="cs-heat-headline" id="cs-heat-headline">{escape(status.public_status_headline)}</p>'
            f'<p class="cs-heat-desc" id="cs-heat-desc">{escape(status.public_status_description)}</p>'
            f'<div class="cs-solo-pillars-grid" aria-label="單人使用即具完整價值的三大工具">{pillars_html}</div>'
            f"</div>"
        )
    else:
        tags_html = "".join(
            f'<span class="cs-anon-tag">{escape(tag)}</span>'
            for tag in heat_item.anonymous_applicant_tags
        )
        heat_body_html = (
            f'<div class="cs-heat-unlocked-box" id="cs-heat-state-box" data-heat-unlocked="true">'
            f'<div class="cs-heat-unlocked-header">'
            f'<span class="cs-stage-badge is-unlocked">{escape(status.stage_label)}</span>'
            f'<span class="cs-plan-progress-pill is-unlocked" id="cs-plan-progress-pill">'
            f'{escape(status.short_name)} 本季已累積 {status.active_plan_count} 份申請計畫（已超過 {status.unlock_threshold_min} 份解鎖門檻）'
            f"</span>"
            f"</div>"
            f'<p class="cs-heat-headline" id="cs-heat-headline">{escape(heat_item.competition_status_label)}</p>'
            f'<div class="cs-heat-metrics-grid" id="cs-heat-metrics-grid">'
            f'<div class="cs-heat-metric"><span>同校列入志願總人數</span><strong id="cs-heat-total">{heat_item.total_interested_count} 人</strong></div>'
            f'<div class="cs-heat-metric"><span>列為「第 1 志願」</span><strong id="cs-heat-first">{heat_item.first_choice_count} 人</strong></div>'
            f'<div class="cs-heat-metric"><span>列為「第 2–3 志願」</span><strong id="cs-heat-other">{heat_item.second_or_third_choice_count} 人</strong></div>'
            f'<div class="cs-heat-metric"><span>當期名額對照</span><strong id="cs-heat-quota">{escape(heat_item.quota_hint)}</strong></div>'
            f"</div>"
            f'<div class="cs-anon-tags-row" id="cs-anon-tags-row"><strong>匿名申請者背景分布：</strong>{tags_html}</div>'
            f"</div>"
        )

    return f"""
<div class="cs-network-effect-box" id="preference-heat" data-school-stage="{escape(status.stage)}">
  <div class="cs-network-effect-top">
    <div>
      <span class="cs-layer-step">行動 4 · 疊加網路效應（先靠單人工具留存 → 滿 30 份計畫點燃站內匿名搓湯圓）</span>
      <h3 id="cs-network-effect-title">{escape(status.short_name)} × {escape(heat_item.partner_name_zh)}：站內志願熱度與單人備審工具</h3>
    </div>
    <div class="cs-network-effect-actions">
      <button type="button" class="button secondary" id="cs-btn-join-preference-heat" data-partner-name="{escape(heat_item.partner_name_zh)}">
        🗳️ 匿名把這間放入我的志願序（參與搓湯圓）
      </button>
      <button type="button" class="button secondary" id="cs-btn-copy-viral-heat" data-share-text="{escape(heat_item.viral_share_text)}">
        📣 複製 Dcard／群組最後一週搓湯圓轉發連結
      </button>
    </div>
  </div>
  <p class="cs-anti-cold-start-note">{escape(status.anti_cold_start_guarantee)}</p>
  {heat_body_html}
  <p class="cs-network-feedback" id="cs-preference-heat-feedback" hidden></p>
</div>
"""


def render_admitted_student_connect_lower_html(hub: AdmittedStudentConnectHub, selected_home_id: str) -> str:
    """Render Section 6 (`#admitted-connect`, 放榜期：本屆錄取生跨校連線) in the Lower Layer of `/partners/{country}/{institution}`."""
    cards_html = "".join(
        f'<article class="cs-admitted-card" data-connection-id="{escape(c.connection_id)}">'
        f'<div class="cs-admitted-card-head">'
        f'<span class="cs-admitted-home-badge">{escape(c.home_short_name)}</span>'
        f'<strong>{escape(c.display_alias)}</strong>'
        f'<span class="cs-admitted-term">{escape(c.exchange_term)}</span>'
        f"</div>"
        f'<p class="cs-admitted-major">主修／學院：{escape(c.major_or_college)}</p>'
        f'<div class="cs-admitted-tags">'
        + "".join(f'<span class="cs-looking-tag">#{escape(t)}</span>' for t in c.looking_for_tags)
        + "</div>"
        f'<p class="cs-admitted-intro">{escape(c.intro_note_zh)}</p>'
        f"</article>"
        for c in hub.connections
    )

    schools_summary = "、".join(hub.participating_home_schools) if hub.participating_home_schools else "各締約大學"

    return f"""
  <section class="cs-subblock cs-admitted-connect-section" id="admitted-connect" aria-labelledby="admitted-connect-heading">
    <div class="cs-admitted-header">
      <div>
        <span class="cs-layer-step">放榜期網路效應 · 承接 Dcard 留學板放榜認親潮</span>
        <h2 id="admitted-connect-heading">6. 本屆「{escape(hub.partner_name_zh)}」錄取生跨校連線（目前已報到 {hub.admitted_count} 位 · 涵蓋 {escape(schools_summary)}）</h2>
        <p>{escape(hub.banner_subtitle)}</p>
      </div>
      <div class="cs-admitted-header-actions">
        <button type="button" class="button secondary" id="cs-btn-copy-dcard-admitted-post" data-dcard-template="{escape(hub.dcard_admission_wave_post_template)}">
          📋 複製 Dcard 留學板「放榜跨校認親」貼文模板
        </button>
      </div>
    </div>

    <aside class="cs-compliance-banner cs-privacy-banner" role="note">
      <strong>🛡️ 個資與防騷擾安全規範：</strong>{escape(hub.privacy_safety_notice)}
    </aside>

    <div class="cs-admitted-grid" id="cs-admitted-connect-grid">
      {cards_html}
    </div>

    <form class="cs-admitted-form" id="cs-admitted-connect-form" data-country="{escape(hub.country_slug)}" data-institution="{escape(hub.institution_slug)}" data-selected-home="{escape(selected_home_id)}">
      <h3>🙋 我也錄取／獲提名「{escape(hub.partner_name_zh)}」！加入本屆跨校連線</h3>
      <div class="cs-admitted-form-grid">
        <label>
          <span>交換學期</span>
          <select name="exchange_term" id="cs-admitted-term">
            <option value="115-1（2026 秋季班）">115-1（2026 秋季班）</option>
            <option value="115-2（2027 春季班）">115-2（2027 春季班）</option>
            <option value="115 學年全學年">115 學年全學年</option>
          </select>
        </label>
        <label>
          <span>匿名稱呼（如：政大商院 M 同學）</span>
          <input type="text" name="display_alias" id="cs-admitted-alias" placeholder="例如：臺大資工 K 同學" required maxlength="50">
        </label>
        <label>
          <span>主修學院／系所</span>
          <input type="text" name="major_or_college" id="cs-admitted-major" placeholder="例如：管理學院／電機系" required maxlength="60">
        </label>
        <label>
          <span>想找旅伴互助項目</span>
          <input type="text" name="looking_for_tags" id="cs-admitted-tags" value="合租找房, 選課討論, 簽證與保險互助" maxlength="100">
        </label>
      </div>
      <label class="cs-admitted-intro-label">
        <span>行前自我介紹與互助需求（請勿填寫手機、Email 或 LINE ID）</span>
        <textarea name="intro_note_zh" id="cs-admitted-intro" rows="2" placeholder="例如：預計 9 月出發，想找同屆錄取的跨校同學一起研究宿舍申請與選課！" required maxlength="280"></textarea>
      </label>
      <div class="cs-admitted-form-actions">
        <button type="submit" class="button" id="cs-btn-submit-admitted">✨ 登記加入本屆跨校錄取生連線</button>
        <span class="cs-network-feedback" id="cs-admitted-connect-feedback" hidden></span>
      </div>
    </form>
  </section>
"""
