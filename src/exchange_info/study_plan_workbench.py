"""Action 3: Mother-school study-plan anti-pitfall & document workbench integration.

Combines:
1. Verified 10-week window deadlines and writing rules (Action 1)
2. Cross-school partner course directions from /partners/{country}/{institution} (Action 2)
3. School-specific study-plan anti-pitfall alerts, 6-step high-score writing framework,
   and Dcard school-board launch drafts (Action 3).
"""

from __future__ import annotations

from typing import Callable

from .application_writing_guidance import SCHOOL_WRITING_RULE_SOURCES, WRITING_RULES
from .cross_school_partners import (
    build_cross_school_partner_directory,
    build_cross_school_partner_page_data,
)
from .models import (
    CatalogueSourceStatus,
    DcardSchoolBoardLaunchDraft,
    PartnerUniversity,
    StudyPlanPartnerCourseLookup,
    StudyPlanPitfallRule,
    StudyPlanSixStepSection,
    StudyPlanWorkbenchCatalog,
    StudyPlanWorkbenchPayload,
)
from .university_registry import SUPPORTED_UNIVERSITIES, UniversityProfile, resolve_university
from .verified_window_deadlines import (
    WINDOW_END_DATE,
    WINDOW_START_DATE,
    get_verified_school_window_card,
)

SIX_STEP_STUDY_PLAN_GUIDE: list[StudyPlanSixStepSection] = [
    StudyPlanSixStepSection(
        step_number=1,
        field_id="motivation",
        heading="第 1 段｜申請動機（從目前學習瓶頸切入）",
        recommended_min_chars=300,
        recommended_max_chars=600,
        anti_cliche_warning="❌ 忌寫罐頭文：只寫「從小嚮往出國、想開拓國際視野、體驗當地文化」，審查委員一天看上百份同質文字。",
        high_score_formula="✅ 高分公式：我在主修領域修過什麼具體課程／專題 → 發現什麼研究或實務視角缺口 → 為什麼這趟交換能補上這塊拼圖。",
        outline=[
            "我的主修背景與已修過的核心課程／專題經驗",
            "目前在國內學習遇到的瓶頸或缺少的跨國實證視角",
            "這趟交換如何銜接我的學術方向與職涯目標",
        ],
        example_zh=(
            "我就讀經濟學系，修習《國際貿易理論與政策》與大三專題後，發現國內教材案例多集中於歐美市場，"
            "對於東亞綠色供應鏈轉型缺少第一手產業觀察。希望透過一學期交換修習當地產業分析課程，將跨國比較成果運用於大四畢業專題。"
        ),
    ),
    StudyPlanSixStepSection(
        step_number=2,
        field_id="school_reason",
        heading="第 2 段｜選擇該校的原因（點名 2–3 門真實課程或研究中心）",
        recommended_min_chars=300,
        recommended_max_chars=600,
        anti_cliche_warning="❌ 忌幫對方學校寫維基百科：只介紹該校建校幾年、QS 排名第幾、城市風景多美，卻沒寫出與你科系的具體連結。",
        high_score_formula="✅ 高分公式：直接對照 UniWay /partners 跨校頁與姊妹校官網點名 2–3 門原文課名或實驗室 ＋ 說明為何本校無此資源 ＋ 我預計如何運用。",
        outline=[
            "點名目標姊妹校開設的 2–3 門具體原文課程、學程或研究中心",
            "這些課程或研究資源與本校現有課程的互補差異",
            "我的語言檢定成績與先修背景為何足以修習這些課程",
        ],
        example_zh=(
            "貴校商學院開設全英語授課之《Behavioral Finance》與《Asian Economic Development》，本校目前無對應之實證研討課；"
            "加上貴校每學期與當地企業合辦產業工作坊，能直接補足我在跨國財務實務分析上的研究需求。"
        ),
    ),
    StudyPlanSixStepSection(
        step_number=3,
        field_id="learning_goals",
        heading="第 3 段｜研修目標（拆成語言、專業、跨文化三點並量化）",
        recommended_min_chars=250,
        recommended_max_chars=500,
        anti_cliche_warning="❌ 忌寫無法檢驗的空話：只寫「提升英文能力、多交外國朋友、增進獨立生活能力」，沒有任何量化標準。",
        high_score_formula="✅ 高分公式：拆成「語言目標、專業學習目標、跨文化／實務目標」三項，每一項都加上可驗證的數字或交付成果。",
        outline=[
            "語言目標（例如：全外文完成 15 分鐘課堂專題簡報、通過檢定級數）",
            "專業學習目標（例如：修畢至少 3 門主修相關課程、達到母校最低及格門檻）",
            "跨文化與校園參與目標（例如：參與 1 個當地學術社團或跨國小組專案）",
        ],
        example_zh=(
            "語言：學期末能以全英文完成 15 分鐘專業課堂簡報與小論文。專業：修畢至少 3 門（9 學分）與主修相關之專業課程並全數及格。"
            "跨文化：加入當地國際學生組織（如 ESN 或Buddy Program）並完成一項跨國團隊專案。"
        ),
    ),
    StudyPlanSixStepSection(
        step_number=4,
        field_id="course_plan",
        heading="第 4 段｜預計修課與抵免規劃（對照 /partners 姊妹校開課資訊）",
        recommended_min_chars=None,
        recommended_max_chars=None,
        anti_cliche_warning="❌ 忌只寫模糊領域：沒寫出預計修幾學分、也沒確認母校每學期最低修課門檻（多數母校規定至少 6 學分或 2–3 門課及格才退保證金）。",
        high_score_formula="✅ 高分公式：以「海外原文課名｜學分數｜預計抵免本校類別（必修／專業選修／通識）」條列，並多列 2 門備案課程以防開課異動。",
        outline=[
            "核心擬修課程 3–4 門（含原文課名、ECTS/學分數、對應本校抵免類別）",
            "備案課程 1–2 門（展現已預先查核選課限制與衝堂風險）",
            "符合母校最低修課門檻與保證金退費／獎學金核銷規定之說明",
        ],
        example_zh=(
            "Behavioral Finance｜3 學分（6 ECTS）｜預計抵免系定專業選修\n"
            "Asian Economic Development｜3 學分（6 ECTS）｜預計抵免系定專業選修\n"
            "Academic Writing and Presentation｜3 學分｜預計抵免外語／通識學分\n"
            "International Marketing（備案課程）｜3 學分｜預計抵免商管選修"
        ),
    ),
    StudyPlanSixStepSection(
        step_number=5,
        field_id="expected_outcomes",
        heading="第 5 段｜預期成果（寫出交換結束時拿得出來的具體產出）",
        recommended_min_chars=150,
        recommended_max_chars=400,
        anti_cliche_warning="❌ 忌與第 3 段重複喊口號：若沒有具體產出物，審查委員無法判斷計畫可行性。",
        high_score_formula="✅ 高分公式：一一對應第 3 段目標，列出「學分成績單、跨國比較期末報告、語言檢定進階成績、返國分享素材」等具體成果。",
        outline=[
            "學業成果（取得目標學分數與正式成績單）",
            "研究或作品成果（完成跨國比較報告、專題數據或作品集）",
            "語言與人脈成果（專業外語簡報能力、跨國同儕與師長學術連結）",
        ],
        example_zh=(
            "1. 取得至少 12 學分及格成績單並完成系所專業選修採認；2. 完成一份結合當地產業案例之跨國比較期末報告作為大四專題章節；"
            "3. 整理選課與住宿實務筆記回饋校內學弟妹。"
        ),
    ),
    StudyPlanSixStepSection(
        step_number=6,
        field_id="return_plan",
        heading="第 6 段｜返國後學習連結（學分採認、校內回饋與畢業／職涯規劃）",
        recommended_min_chars=150,
        recommended_max_chars=400,
        anti_cliche_warning="❌ 忌寫到交換結束就停住：學校選送交換生非常重視「返國義務履行（心得報告、分享會）」與「對母校學習的延伸效益」。",
        high_score_formula="✅ 高分公式：明確寫出返國後辦理學分抵免與心得繳交時程 ＋ 如何回饋母校國際處／系上分享會 ＋ 如何銜接畢業專題、研究所或職涯。",
        outline=[
            "返國後 1–2 個月內完成心得報告繳交與學分抵免之時程",
            "參與母校國際處交換經驗分享會或國際志工活動之回饋計畫",
            "與畢業專題、碩士班研究或跨國職涯之具體銜接",
        ],
        example_zh=(
            "返國後將於 1 個月內完成學分抵免申請與交換心得報告繳交，主動報名國際處交換經驗分享會提供選課與預算實務建議；"
            "並將交換期間修習之實證分析方法直接應用於大四畢業論文與後續研究所深造。"
        ),
    ),
]


# School-specific anti-pitfall metadata & Dcard launch positioning
SCHOOL_PITFALL_SPECS: dict[str, dict[str, object]] = {
    "nccu": {
        "dcard_board": "Dcard 政治大學板 ＋ 留學板",
        "max_a4_pages_hint": 2.0,
        "scoring_weight_headline": "校級國際薦外：交換計畫書＋履歷表占總成績 20%（語檢 30%、口試 30%、在校成績 20%）；赴大陸書審占 35%",
        "recommended_publish_window": "截止前 2～3 週（秋季二招／115-2 春季甄選前夕重點發布）",
        "post_title": "#分享 政大出國交換讀書計畫千萬別超過 2 頁！國合處簡章「超頁不計分＆分檔規定」防雷整理（附政大專屬字數計數器＋姊妹校開課對照）",
        "pitfalls": [
            {
                "rule_id": "nccu-two-page-hard-cap",
                "severity": "critical",
                "badge_label": "⚠️ 超頁直接不計分",
                "pitfall_title": "校級國際薦外：計畫書與履歷須分為 2 份文件，每份各至少 500 字、限 2 頁 A4（超出 2 頁之內容不予計分！）",
                "detail_zh": (
                    "政大國合處校級國際薦外簡章明載：交換計畫書與履歷表（含簡歷及自傳）須分為 2 份文件撰寫，合計占甄選總成績 20%。"
                    "限以電腦繕打、A4 直式橫書，每份各至少 500 字、以 2 頁為限（超出 2 頁之內容不予計分），且皆應以報考語組之語言撰寫。"
                ),
                "scoring_weight": "交換計畫書＋履歷表占 20%（語檢 30%、口試 30%、在校成績 20%）",
                "format_and_limit": "分為 2 份文件、A4 直式橫書、每份至少 500 字、上限 2 頁 A4（超頁不計分）",
            },
            {
                "rule_id": "nccu-mainland-word-cap",
                "severity": "critical",
                "badge_label": "⚠️ 超字數恕不受理",
                "pitfall_title": "校級赴大陸地區交換：個人自傳 1,000 字以內、研究／學習計畫 3,000 字以內（超過字數者恕不受理）",
                "detail_zh": "政大赴大陸地區交換生甄選簡章規定：個人自傳 1,000 字以內、研究／學習計畫 3,000 字以內，超過字數者恕不受理；書面成績占總成績 35%。",
                "scoring_weight": "赴大陸交換書面審查占總成績 35%",
                "format_and_limit": "自傳 1,000 字內、研究／學習計畫 3,000 字內（超字不受理）",
            },
        ],
    },
    "ncku": {
        "dcard_board": "Dcard 成功大學板 ＋ 留學板",
        "max_a4_pages_hint": 2.0,
        "scoring_weight_headline": "中英文讀書或研究計畫占 25% ＋ 中英文自傳與其餘表現占 25%（書審合計高達總成績 50%！）",
        "recommended_publish_window": "116-1 申請季／截止前 2～3 週重點發布",
        "post_title": "#分享 成大校級出國交換「讀書計畫＋自傳占總分 50%」！簡章規定必鎖定第一志願寫中英雙語（附 6 段式工作台＆姊妹校開課查詢）",
        "pitfalls": [
            {
                "rule_id": "ncku-50pct-first-choice-bilingual",
                "severity": "critical",
                "badge_label": "🔥 書審占總分 50%",
                "pitfall_title": "讀書計畫（25%）＋自傳與表現（25%）合計占 50%！且須針對「第一志願」分別擬訂中、英文雙語版本",
                "detail_zh": (
                    "成大校級薦外簡章規定：須就所選填志願學校之「第一志願」分別擬訂中文及英文讀書或研究計畫（占總成績 25%），"
                    "以及中文及英文自傳（含學經歷，與其餘表現合計占總成績 25%），連同申請文件依序合併為單一 PDF 檔（上限 50MB）上傳。"
                ),
                "scoring_weight": "中英文讀書計畫 25% ＋ 中英文自傳與其餘表現 25%（書審合計占 50%）",
                "format_and_limit": "鎖定第一志願撰寫中、英文讀書計畫與中、英文自傳，全數合併為單一 PDF（上限 50MB）",
            },
        ],
    },
    "ntust": {
        "dcard_board": "Dcard 臺灣科技大學板 ＋ 留學板",
        "max_a4_pages_hint": 2.0,
        "scoring_weight_headline": "校內書審總分：外語能力 60%＋在校成績 20%＋課外表現證明 20%（讀書計畫與自傳占 0% 但為必繳門檻！）",
        "recommended_publish_window": "截止前 2～3 週重點發布",
        "post_title": "#分享 台科大出國交換「讀書計畫占總分 0%、外語檢定占 60%」？幫大家抓出簡章真實配重＆中英雙語 1–2 頁快速完稿工具",
        "pitfalls": [
            {
                "rule_id": "ntust-zero-weight-mandatory-gate",
                "severity": "critical",
                "badge_label": "💡 占 0% 但必繳門檻",
                "pitfall_title": "校內書審讀書計畫與自傳占 0%（外語能力占 60%、在校成績 20%、課外表現 20%），但仍須繳交中英文各 1–2 頁！",
                "detail_zh": (
                    "台科大歐美亞澳交換簡章明載：須繳交中、英文讀書計畫各一份，以及中、英文自傳各一份（每份約 1–2 頁，中、英文版分別合併為 PDF 上傳）。"
                    "但校內書審總分僅計外語能力 60%＋在校學業表現 20%＋課外表現證明 20%，讀書計畫屬必繳資格門檻，切勿花兩週雕琢而漏掉整理 20% 的課外表現證明！"
                ),
                "scoring_weight": "讀書計畫與自傳占 0%（外語能力 60%＋在校學業 20%＋課外表現證明 20%）",
                "format_and_limit": "中、英文讀書計畫各一份＋中、英文自傳各一份，每份約 1–2 頁（勿加密 PDF）",
            },
        ],
    },
    "ntu": {
        "dcard_board": "Dcard 臺灣大學板 ＋ 留學板",
        "max_a4_pages_hint": 2.0,
        "scoring_weight_headline": "出國交換計畫書（A4 兩面、至少 500 字）＋ 履歷表（A4 兩面）為書面審查核心項目",
        "recommended_publish_window": "116 年度第 1 學期甄選截止（11/24 16:00）前 2～3 週（11/03～11/15）",
        "post_title": "#分享 台大 116-1 校級交換 11/24 下午 4 點截止！出國交換計畫書「至少 500 字、限 A4 兩面」防雷與姊妹校修課對照工具",
        "pitfalls": [
            {
                "rule_id": "ntu-study-plan-two-sides-500-chars",
                "severity": "critical",
                "badge_label": "⚠️ 限 A4 兩面＋16:00 截止",
                "pitfall_title": "出國交換計畫書限 A4 兩面、至少 500 字；且線上申請與繳費皆於截止日下午 16:00 關閉（非 23:59！）",
                "detail_zh": (
                    "台大校級出國交換簡章規定：出國交換計畫書須為 A4 兩面、至少 500 字（中文或英文）；履歷表另備 A4 兩面。"
                    "特別注意線上報名系統與報名費繳交皆在截止日下午 16:00 整截止，千萬別等到晚上才上傳！"
                ),
                "scoring_weight": "校級甄選書審（出國交換計畫書＋履歷表）搭配歷年成績與語檢門檻",
                "format_and_limit": "出國交換計畫書 A4 兩面、至少 500 字；履歷表另備 A4 兩面",
            },
        ],
    },
    "ntnu": {
        "dcard_board": "Dcard 臺灣師範大學板 ＋ 留學板",
        "max_a4_pages_hint": 4.0,
        "scoring_weight_headline": "自傳及出國學習計畫占甄選總分 20%（中英文合計須介於 500～5,000 字）",
        "recommended_publish_window": "2027 秋季班甄選截止（12/04 17:00）前 2～3 週（11/13～11/25）",
        "post_title": "#分享 師大出國交換 12/4 截止！「自傳＋學習計畫占 20%、限 500～5,000 字」防雷整理＆線上字數計數工作台",
        "pitfalls": [
            {
                "rule_id": "ntnu-500-to-5000-chars-and-stamp",
                "severity": "critical",
                "badge_label": "⚠️ 占 20%＋500–5,000 字",
                "pitfall_title": "自傳＋出國學習計畫占總分 20%，中英文合計須介於 500～5,000 字之間（建議另附外文版 500～2,500 字）",
                "detail_zh": (
                    "台師大赴外交換簡章規定：自傳與出國學習計畫合計須介於 500 至 5,000 字之間，占甄選評分 20%；"
                    "且線上填報完成後列印之紙本申請表須經系所核章，連同報名費收據於截止日 17:00 前送達國際處。"
                ),
                "scoring_weight": "自傳及出國學習計畫占甄選總分 20%",
                "format_and_limit": "中英文合計 500～5,000 字（建議另附外文版 500～2,500 字）",
            },
        ],
    },
    "ntpu": {
        "dcard_board": "Dcard 臺北大學板 ＋ 留學板",
        "max_a4_pages_hint": 4.0,
        "scoring_weight_headline": "計畫書合計 5,000 字以內，須依申請語組（英／中／日）語言撰寫",
        "recommended_publish_window": "116 學年度第 1 梯次截止（12/29）前 2～3 週（12/08～12/18）",
        "post_title": "#分享 北大 116 出國交換 12/29 截止！計畫書「5,000 字上限＋依語組語言撰寫＋隔日紙本核章」防雷包＆文件工作台",
        "pitfalls": [
            {
                "rule_id": "ntpu-5000-char-cap-and-language-group",
                "severity": "critical",
                "badge_label": "⚠️ 限 5,000 字內＋語組語言",
                "pitfall_title": "計畫書以 A4 直式橫書合計 5,000 字以內，英文組繳英文、中文組繳中文、日文組繳日文！",
                "detail_zh": (
                    "台北大赴外交換簡章規定：計畫書合計 5,000 字以內，內容須含個人學經歷、申請動機、未來學習計畫與發展，"
                    "並嚴格依申請語組語言撰寫；線上截止隔日 17:00 前紙本核章須送達國際處。"
                ),
                "scoring_weight": "書面計畫書與歷年成績、語言能力及面試綜合評比",
                "format_and_limit": "A4 直式橫書、整份計畫書合計 5,000 字以內、依申請語組語言撰寫",
            },
        ],
    },
    "nsysu": {
        "dcard_board": "Dcard 中山大學板 ＋ 留學板",
        "max_a4_pages_hint": 2.0,
        "scoring_weight_headline": "研修計畫書占甄選總分 20%（未提供者此項目以 0 分計！）",
        "recommended_publish_window": "春季／秋季甄選截止前 2～3 週重點發布",
        "post_title": "#分享 中山出國交換「研修計畫書占 20%、未交 0 分」！中英／中日各限 1 頁 A4 規定整理＆寫作工作台",
        "pitfalls": [
            {
                "rule_id": "nsysu-official-blank-form-1page",
                "severity": "critical",
                "badge_label": "⚠️ 必用官方空白表＋各限 1 頁",
                "pitfall_title": "須下載國際處「研修計畫書空白表格」填寫（占 20%，未交 0 分）；赴歐美亞紐澳中英文各限 1 頁 A4、赴日中日間各限 1 頁 A4",
                "detail_zh": (
                    "中山大學出國交換簡章規定：須使用國際處空白表格填寫並上傳 PDF（占甄選總分 20%）。"
                    "赴歐美亞紐澳須含中、英文各以 1 頁 A4 為限；赴日本須含中、日文各 1 頁 A4；赴中國大陸以中文 1–2 頁 A4 撰寫。"
                ),
                "scoring_weight": "研修計畫書占甄選總分 20%（未提供者以 0 分計）",
                "format_and_limit": "國際處指定空白表格；中＋英（或中＋日）各 1 頁 A4 為限（赴陸中文 1–2 頁 A4）",
            },
        ],
    },
    "nchu": {
        "dcard_board": "Dcard 中興大學板 ＋ 留學板",
        "max_a4_pages_hint": 3.0,
        "scoring_weight_headline": "《自傳及讀書計畫》赴國外組占總成績 30%、赴大陸組占 45%（以第一志願為目標撰寫）",
        "recommended_publish_window": "截止前 2～3 週重點發布",
        "post_title": "#分享 中興出國交換《自傳及讀書計畫》占 30%～45%！「至多 A4 三面＋鎖定第一志願英文版」防雷整理＆文件工作台",
        "pitfalls": [
            {
                "rule_id": "nchu-three-pages-first-choice",
                "severity": "critical",
                "badge_label": "🔥 占 30%–45%＋限 A4 三面",
                "pitfall_title": "《自傳及讀書計畫》至多 A4 大小三面，須以「第一志願」為目標撰寫，有填海外學校須繳交英文版！",
                "detail_zh": (
                    "中興大學交換簡章規定：《自傳及讀書計畫》赴國外組占總成績 30%、赴大陸組占 45%，至多 A4 大小三面，"
                    "須含「個人特質與經歷」及「交換計畫與未來展望」兩大核心；另申請赴外獎學金之中文計劃書建議 1,000–1,500 字（單檔勿超過 2MB）。"
                ),
                "scoring_weight": "赴國外組占總成績 30%、赴大陸組占總成績 45%",
                "format_and_limit": "至多 A4 大小三面、鎖定第一志願撰寫（填海外學校須交英文版）",
            },
        ],
    },
    "ntut": {
        "dcard_board": "Dcard 臺北科技大學板 ＋ 留學板",
        "max_a4_pages_hint": 1.0,
        "scoring_weight_headline": "校內甄選《研修計畫》限 1 頁 A4 內；學海惜珠另須 1,000–1,500 字中文計劃書",
        "recommended_publish_window": "2027 秋季班校內甄選（11–12 月）截止前 2～3 週",
        "post_title": "#分享 北科大出國交換 STEP 1 校內甄選！「研修計畫限 1 頁 A4＋系主任與院長雙核章」防雷整理＆文件工作台",
        "pitfalls": [
            {
                "rule_id": "ntut-one-page-a4-and-dean-stamp",
                "severity": "critical",
                "badge_label": "⚠️ 限 1 頁 A4＋雙重簽章",
                "pitfall_title": "校內甄選《研修計畫》須於 1 頁 A4 內簡述申請目的與預期效益（非大陸地區建議以英文撰寫）",
                "detail_zh": (
                    "北科大國際處 STEP 1 校內甄選規定：《研修計畫》於 1 頁 A4 內簡述申請目的與預期效益（無需針對特定學校，非大陸建議用英文）；"
                    "若申請學海惜珠另須加附 1–2 頁動機與 1,000–1,500 字中文赴國外研修計劃書。紙本申請表須完成系主任與院長核章。"
                ),
                "scoring_weight": "校內書審（研修計畫、成績單、外語檢定）與面試綜合評選",
                "format_and_limit": "校內甄選《研修計畫》1 頁 A4 內；學海惜珠計劃書 1,000–1,500 字",
            },
        ],
    },
    "nycu": {
        "dcard_board": "Dcard 陽明交通大學板 ＋ 留學板",
        "max_a4_pages_hint": 2.0,
        "scoring_weight_headline": "國外組：大學部自傳 10%＋讀書計畫 15%、研究所自傳 20%＋讀書計畫 25%（同分時讀書計畫為第二優先參酌！）",
        "recommended_publish_window": "第 1 梯次截止（12/15 16:00）前 2～3 週（11/24～12/05）",
        "post_title": "#分享 陽明交大出國交換 12/15 截止！總分相同時「讀書計畫是第二優先參酌項目」＆每學期至少 3 門專業課規劃工具",
        "pitfalls": [
            {
                "rule_id": "nycu-tiebreaker-and-min-courses",
                "severity": "critical",
                "badge_label": "🔥 同分參酌關鍵＋中英雙語",
                "pitfall_title": "須繳交中英文自傳與中英文讀書計畫（研究所合計占 45%），且總分相同時「讀書計畫」為僅次於志願序之第二優先參酌項目！",
                "detail_zh": (
                    "陽明交大出國交換簡章規定：國外及港澳地區大學部自傳 10%＋讀書計畫 15%、研究所自傳 20%＋讀書計畫 25%；"
                    "讀書計畫須具體規劃擬修讀之專業課程（大學部每學期至少 3 門、研究所至少 2 門，全數及格始退還 NT$10,000 保證金）。"
                ),
                "scoring_weight": "國外組大學部合計 25%、研究所合計 45%（同分時讀書計畫為第二優先參酌）",
                "format_and_limit": "中英文自傳＋中英文讀書計畫；大學部規劃每學期至少 3 門專業課、研究所至少 2 門",
            },
        ],
    },
    "nthu": {
        "dcard_board": "Dcard 清華大學板 ＋ 留學板",
        "max_a4_pages_hint": 2.0,
        "scoring_weight_headline": "須同時繳交「中文及外文」讀書計畫與自傳，並具體列出目標姊妹校修課清單",
        "recommended_publish_window": "春季／秋季梯次截止前 2～3 週重點發布",
        "post_title": "#分享 清大出國交換讀書計畫防雷！必交「中＋外文雙語讀書計畫與自傳」＆目標姊妹校至少 3 門課修課規劃工具",
        "pitfalls": [
            {
                "rule_id": "nthu-bilingual-course-list-requirement",
                "severity": "critical",
                "badge_label": "⚠️ 中外文雙語＋具體課表",
                "pitfall_title": "須同時繳交中文及外文（英文或交換國語言）讀書計畫與自傳，並具體列出目標姊妹校擬修課程列表！",
                "detail_zh": (
                    "清大出國交換簡章規定：須同時繳交中、外文讀書計畫與自傳，讀書計畫須具體列出擬於目標姊妹校修讀之課程規劃列表"
                    "（海外交換大學部每學期／學季至少 3 門課程及格、研究所至少 1 門研究所課程及格；獲獎學金者須為本科相關專業課程）。"
                ),
                "scoring_weight": "校內書審（中、外文讀書計畫、自傳、歷年成績與語檢能力）",
                "format_and_limit": "中文＋外文讀書計畫與自傳；須列目標姊妹校具體課程列表（大學部至少 3 門課）",
            },
        ],
    },
    "ncu": {
        "dcard_board": "Dcard 中央大學板 ＋ 留學板",
        "max_a4_pages_hint": 2.0,
        "scoring_weight_headline": "線上上傳讀書計畫與備審 PDF，且紙本申請表須經系所核章於截止日中午 12:00 前送達",
        "recommended_publish_window": "申請截止前 2～3 週重點發布",
        "post_title": "#分享 中央大學出國交換「中午 12:00 截止」別記錯！讀書計畫 6 段式工作台＆姊妹校修課對照整理",
        "pitfalls": [
            {
                "rule_id": "ncu-noon-deadline-and-return-report",
                "severity": "critical",
                "badge_label": "⚠️ 中午 12:00 截止＋系所核章",
                "pitfall_title": "線上報名與紙本核章皆為截止日中午 12:00 整截止（非 23:59）！返國心得報告須達 800–1,500 字並附 4 張照片",
                "detail_zh": (
                    "中央大學交換簡章規定：線上系統填報與系所核章紙本送件皆在截止日中午 12:00 截止；"
                    "讀書計畫未公布硬性字數上限，但建議控制在 1,000–2,000 字（約 1–2 頁 A4）並明確列出目標姊妹校修課計畫。"
                ),
                "scoring_weight": "校內書面審查（讀書計畫、成績單、語言能力證明）",
                "format_and_limit": "未訂硬性字數上限（系統提供 6 段式架構與 A4 頁數換算）；返國報告至少 800–1,500 字",
            },
        ],
    },
    "ccu": {
        "dcard_board": "Dcard 中正大學板 ＋ 留學板",
        "max_a4_pages_hint": 3.0,
        "scoring_weight_headline": "研修計畫書須包含「自傳、讀書計畫、申請動機」三項，每項約 A4 一頁",
        "recommended_publish_window": "截止前 2～3 週重點發布",
        "post_title": "#分享 中正大學出國交換研修計畫書「自傳＋讀書計畫＋動機各約 A4 一頁」防雷整理＆線上寫作工作台",
        "pitfalls": [
            {
                "rule_id": "ccu-three-sections-one-page-each",
                "severity": "high",
                "badge_label": "⚠️ 三大項各約 A4 一頁",
                "pitfall_title": "研修計畫書中英文皆可，須包含「自傳、讀書計畫與申請動機」，每項約 A4 一頁",
                "detail_zh": "中正大學交換簡章規定：研修計畫書須同時包含自傳、讀書計畫與申請動機三大項目，不限格式，每項篇幅約 A4 一頁。",
                "scoring_weight": "校內書審（研修計畫書、歷年成績與外語能力證明）",
                "format_and_limit": "含自傳、讀書計畫、申請動機三項，每項約 A4 一頁",
            },
        ],
    },
    "cgu": {
        "dcard_board": "Dcard 長庚大學板 ＋ 留學板",
        "max_a4_pages_hint": 2.0,
        "scoring_weight_headline": "校內書審重視目標姊妹校修課對照與語檢門檻，紙本申請表須經系主任與院長雙重核章",
        "recommended_publish_window": "秋季／春季甄選窗口開放前 2～3 週重點發布",
        "post_title": "#分享 長庚大學出國交換讀書計畫怎麼寫？對照台政成學長姐跨校修課情報＋6 段式文件工作台整理",
        "pitfalls": [
            {
                "rule_id": "cgu-department-dean-stamps-and-course-match",
                "severity": "high",
                "badge_label": "⚠️ 系主任＋院長雙重核章",
                "pitfall_title": "紙本申請表須預留系主任與院長雙重核章時間；讀書計畫建議對照跨校姊妹校開課方向撰寫",
                "detail_zh": (
                    "長庚大學出國交換申請須將線上填報文件列印後送請系主任與院長核章；"
                    "雖然官方未公布讀書計畫硬性字數上限，但透過 UniWay /partners 跨校頁參考台大、政大、成大赴同一姊妹校的修課方向寫進計畫書，能大幅提升書審說服力。"
                ),
                "scoring_weight": "校內書面審查與面試綜合評比",
                "format_and_limit": "未訂硬性字數上限（建議 1,000–2,000 字、約 1–2 頁 A4），紙本須經系主任與院長核章",
            },
        ],
    },
    "fju": {
        "dcard_board": "Dcard 輔仁大學板 ＋ 留學板",
        "max_a4_pages_hint": 4.0,
        "scoring_weight_headline": "讀書計畫及自傳以 A4 雙面列印，不超過 2 頁（4 面），依申請語組語言撰寫",
        "recommended_publish_window": "116-1 校級交換（11–12 月收件）截止前 2～3 週",
        "post_title": "#分享 輔大出國交換讀書計畫＆自傳「A4 雙面列印不超過 2 頁（4 面）」防雷整理＋6 段式寫作工作台",
        "pitfalls": [
            {
                "rule_id": "fju-two-sheets-four-sides-language-group",
                "severity": "critical",
                "badge_label": "⚠️ 限 2 頁（4 面）＋語組語言",
                "pitfall_title": "讀書計畫（Study Plan）及自傳：A4 雙面列印，不超過 2 頁（4 面），須依語組語言撰寫！",
                "detail_zh": (
                    "輔仁大學交換簡章規定：讀書計畫及自傳以 A4 雙面列印，不超過 2 頁（4 面）；"
                    "外語組以英文或交換國語言撰寫、日語組以日文或英文撰寫、中語組以中文撰寫。返國後 1 個月內另須繳交 2,000 字以上心得報告。"
                ),
                "scoring_weight": "校內書審（讀書計畫及自傳、歷年成績、語檢證明）與面試",
                "format_and_limit": "A4 雙面列印不超過 2 頁（4 面）；返國報告 2,000 字以上",
            },
        ],
    },
    "scu": {
        "dcard_board": "Dcard 東吳大學板 ＋ 留學板",
        "max_a4_pages_hint": 2.0,
        "scoring_weight_headline": "自傳約 2,000 字；交換動機及讀書計畫「一校一份」各約 2,000 字以內（中文 Form A＋外文 Form B）",
        "recommended_publish_window": "第 2 波甄選截止（11/19 12:00）前 2～3 週（10/28～11/10）",
        "post_title": "#分享 東吳出國交換 11/19 中午 12 點截止！讀書計畫「一校一份、Form A＋Form B 各 2,000 字內」防雷＆文件工作台",
        "pitfalls": [
            {
                "rule_id": "scu-one-per-school-form-a-form-b",
                "severity": "critical",
                "badge_label": "⚠️ 一校一份＋Form A/B 雙表",
                "pitfall_title": "交換動機及讀書計畫須「一校一份」（各約 2,000 字以內），且赴外須同時撰寫中文 Form A 與外文 Form B！",
                "detail_zh": (
                    "東吳大學國合處規定：自傳或履歷 1 份約 2,000 字；交換研修動機及讀書計畫「一校一份」各約 2,000 字以內。"
                    "赴外交換須同時撰寫中文 Form A 與外文 Form B，依志願序將所有中文表格排在前、外文表格在後，合併為單一 PDF（上限 5MB），並於 11/19 中午 12:00 前完成上傳。"
                ),
                "scoring_weight": "校內書面審查（自傳、各志願校 Form A/B 讀書計畫、語檢與成績）及面試",
                "format_and_limit": "自傳約 2,000 字；讀書計畫一校一份各約 2,000 字內（單一 PDF 上限 5MB）",
            },
        ],
    },
    "fcu": {
        "dcard_board": "Dcard 逢甲大學板 ＋ 留學板",
        "max_a4_pages_hint": 2.0,
        "scoring_weight_headline": "研修計畫（簡章附件二）中英文均可，字數至少 1,000 字",
        "recommended_publish_window": "116 學年度交換甄選（11–12 月）截止前 2～3 週",
        "post_title": "#分享 逢甲大學出國交換「研修計畫至少 1,000 字」防雷整理！內建 1,000 字計數器＋6 段式寫作工作台",
        "pitfalls": [
            {
                "rule_id": "fcu-min-1000-chars-attachment2",
                "severity": "critical",
                "badge_label": "⚠️ 至少 1,000 字下限",
                "pitfall_title": "研修計畫（簡章附件二）字數至少須達 1,000 字，含動機、修課規劃與預期效益！",
                "detail_zh": (
                    "逢甲大學國際處規定：研修計畫（簡章附件二）中文或英文均可，字數至少 1,000 字，內容須含動機、修課規劃與預期效益；"
                    "返國後 1 個月內另須繳交 2,000 字以上的研習報告書。"
                ),
                "scoring_weight": "校內書審（附件二研修計畫、成績與語檢證明）及面試",
                "format_and_limit": "研修計畫至少 1,000 字；返國研習報告書至少 2,000 字",
            },
        ],
    },
    "yzu": {
        "dcard_board": "Dcard 元智大學板 ＋ 留學板",
        "max_a4_pages_hint": 2.0,
        "scoring_weight_headline": "第一階段校內評比：系排名 50%＋英檢 50%；須繳交中英文讀書計畫（赴陸須含 500 字以上中文讀書計畫）",
        "recommended_publish_window": "115-2 赴陸截止（10/25）及歐美亞澳申請季前 2～3 週",
        "post_title": "#分享 元智出國交換「第一階段系排 50%＋英檢 50%」！中英文讀書計畫＆赴陸 500 字下限防雷工作台",
        "pitfalls": [
            {
                "rule_id": "yzu-rank-english-50-50-and-deposit",
                "severity": "critical",
                "badge_label": "💡 系排 50%＋英檢 50%",
                "pitfall_title": "第一階段評比為系排 50%＋英檢 50%！須交中英文讀書計畫（赴陸須含 500 字以上中文版），返國 2 週內交 1,500 字報告＋6 張照片退保證金",
                "detail_zh": (
                    "元智大學交換簡章規定：須繳交中英文讀書計畫（赴大陸地區交換者須含 500 字以上中文讀書計畫）；"
                    "且返國後 2 週內須繳交 1,500 字以上研修心得報告與 6 張照片並完成學分抵免，NT$5,000 保證金始全額無息退還。"
                ),
                "scoring_weight": "第一階段校內評比：系排名 50% ＋ 英檢成績 50%",
                "format_and_limit": "中英文讀書計畫（赴陸中文至少 500 字）；返國報告至少 1,500 字＋6 張照片",
            },
        ],
    },
    "cycu": {
        "dcard_board": "Dcard 中原大學板 ＋ 留學板",
        "max_a4_pages_hint": 2.0,
        "scoring_weight_headline": "須繳交中、英文讀書計畫與中、英文自傳電子檔（非大陸地區面試占 40%，其中讀書計畫細項占 20%）",
        "recommended_publish_window": "春季／秋季收件截止前 2～3 週重點發布",
        "post_title": "#分享 中原大學出國交換「中英文雙語讀書計畫＋自傳」準備攻略！面試占 40%（讀書計畫細項占 20%）工作台整理",
        "pitfalls": [
            {
                "rule_id": "cycu-bilingual-study-plan-and-interview",
                "severity": "high",
                "badge_label": "⚠️ 中英雙語電子檔＋面試 20%",
                "pitfall_title": "須同時繳交中文及英文讀書計畫、中文及英文自傳電子檔，且非大陸地區面試中讀書計畫細項占 20%！",
                "detail_zh": (
                    "中原大學出國交換規定：須繳交中、英文讀書計畫（Study Plan）與中、英文自傳（Autobiography），"
                    "電子檔須依國際處規定格式寄送；領取助學金者返國後二週內須提交研習成果報告書辦理核銷。"
                ),
                "scoring_weight": "非大陸地區面試占 40%（其中讀書計畫細項占 20%）",
                "format_and_limit": "中文＋英文讀書計畫、中文＋英文自傳電子檔與紙本",
            },
        ],
    },
    "tku": {
        "dcard_board": "Dcard 淡江大學板 ＋ 留學板",
        "max_a4_pages_hint": 2.0,
        "scoring_weight_headline": "依申請語組準備中、外文讀書計畫，嚴格核對各姊妹校語檢與 GPA 門檻",
        "recommended_publish_window": "校內補招／正式甄選窗口開放前 2～3 週重點發布",
        "post_title": "#分享 淡江出國交換選校＆讀書計畫攻略！400+ 間合作校門檻篩選＋6 段式讀書計畫工作台整理",
        "pitfalls": [
            {
                "rule_id": "tku-language-group-and-study-plan",
                "severity": "high",
                "badge_label": "⚠️ 語組門檻＋修課對照",
                "pitfall_title": "各語組姊妹校對 GPA 與語檢（TOEFL/IELTS/JLPT/N1-N2）有嚴格分流，讀書計畫須鎖定目標校開課方向撰寫",
                "detail_zh": (
                    "淡江大學海外留學交換選擇極多，審查時高度重視學生語檢成績是否符合目標校要求，以及讀書計畫是否具體列出擬於該姊妹校修習之科目與回國學分抵免規劃。"
                ),
                "scoring_weight": "校內書審（讀書計畫、歷年成績、語言檢定）與面試",
                "format_and_limit": "依申請語組準備中、外文讀書計畫（建議 1,000–2,000 字、約 1–2 頁 A4）",
            },
        ],
    },
    "pccu": {
        "dcard_board": "Dcard 中國文化大學板 ＋ 留學板",
        "max_a4_pages_hint": 2.0,
        "scoring_weight_headline": "須繳交中、外文讀書計畫與中、外文自傳各乙份（各約 1,000 字），每學期至少修 6 學分或 2 門課",
        "recommended_publish_window": "115-2／116-1 甄選窗口開放前 2～3 週重點發布",
        "post_title": "#分享 文化大學出國交換「中外文讀書計畫＋自傳各約 1,000 字」防雷整理＆6 段式文件工作台",
        "pitfalls": [
            {
                "rule_id": "pccu-1000-chars-and-min-6-credits",
                "severity": "critical",
                "badge_label": "⚠️ 中外文各約 1,000 字",
                "pitfall_title": "須繳交中、外文讀書計畫與中、外文自傳各乙份（各約 1,000 字），且交換期間每學期至少須修讀 6 學分或 2 門課！",
                "detail_zh": (
                    "文化大學出國交換簡章規定：須繳交中、外文讀書計畫與中、外文自傳各約 1,000 字，"
                    "並具體規劃擬於姊妹校修習之課程（每學期至少須修讀 6 學分或 2 門以上課程）。"
                ),
                "scoring_weight": "校內書審（中外文讀書計畫、中外文自傳、成績與語檢）及面試",
                "format_and_limit": "中、外文讀書計畫與自傳各約 1,000 字；每學期至少修 6 學分或 2 門課",
            },
        ],
    },
    "wzu": {
        "dcard_board": "Dcard 文藻外語大學板 ＋ 留學板",
        "max_a4_pages_hint": 2.0,
        "scoring_weight_headline": "中文讀書計畫（約 1,000 字）＋第一志願組別外文讀書計畫（約 1,000 字），學士班每學期至少修 6 學分或 3 門課及格",
        "recommended_publish_window": "115-2 第二次招募志願分發（10/28–11/03）與下期甄選前 2～3 週",
        "post_title": "#分享 文藻出國交換「中外文讀書計畫各約 1,000 字＋每學期至少 3 門課退保證金」防雷＆文件工作台",
        "pitfalls": [
            {
                "rule_id": "wzu-1000-chars-bilingual-and-deposit-courses",
                "severity": "critical",
                "badge_label": "⚠️ 中外文各 1,000 字＋保證金門檻",
                "pitfall_title": "須繳交中文讀書計畫（約 1,000 字）與第一志願組別外文讀書計畫（約 1,000 字），且學士班每學期至少須修 6 學分或 3 門課及格始退保證金！",
                "detail_zh": (
                    "文藻外語大學交換簡章規定：須繳交中文讀書計畫（含留學動機，約 1,000 字）與外文讀書計畫（以第一志願組別語言撰寫，約 1,000 字）各乙份；"
                    "學士班及專科部每學期至少應修習 6 學分或 3 門課以上且及格，返國 1 個月內交 1,000 字心得報告，始無息退還 NT$10,000 保證金。"
                ),
                "scoring_weight": "校內書審（中外文讀書計畫、歷年成績、外語檢定）與口試",
                "format_and_limit": "中文讀書計畫約 1,000 字＋外文讀書計畫約 1,000 字；返國報告約 1,000 字",
            },
        ],
    },
}


def _build_partner_lookup_from_cross_school(
    home_id: str,
    country: str,
    institution: str,
    catalogue_loader: Callable[[UniversityProfile], tuple[list[PartnerUniversity], CatalogueSourceStatus | None]],
) -> StudyPlanPartnerCourseLookup | None:
    page_data = build_cross_school_partner_page_data(
        country=country,
        institution=institution,
        selected_home=home_id,
        catalogue_loader=catalogue_loader,
    )
    if page_data is None:
        return None
    agr = page_data.selected_home_agreement
    living_hint = (
        page_data.living_cost_references[0].summary_zh
        if page_data.living_cost_references
        else f"請參考 {page_data.canonical_path} 跨校生活費整理"
    )
    suggested_lines: list[str] = []
    for pt in page_data.course_direction_references:
        for b in pt.bullets[:3]:
            clean_b = b.strip()
            if clean_b:
                suggested_lines.append(
                    f"{page_data.school_name_zh} 專業課程（{clean_b[:48]}）｜3 學分｜預計抵免系定專業選修"
                )
    if not suggested_lines:
        suggested_lines = [
            f"{page_data.school_name_zh} 主修領域英語授課課程 A｜3 學分｜預計抵免系定專業選修",
            f"{page_data.school_name_zh} 跨文化／區域研究課程 B｜3 學分｜預計抵免通識或選修學分",
        ]
    return StudyPlanPartnerCourseLookup(
        partner_school_name_zh=page_data.school_name_zh,
        partner_school_name_en=page_data.school_name_en,
        country_name_zh=page_data.country_name_zh,
        country_slug=page_data.country_slug,
        institution_slug=page_data.institution_slug,
        cross_school_partner_path=f"{page_data.canonical_path}?home={home_id}",
        contracted_home_count=page_data.contracted_home_count,
        quota_summary=agr.quota_summary,
        language_requirement_summary=agr.language_requirement_summary,
        degree_levels=agr.degree_levels,
        colleges=agr.colleges,
        course_direction_points=page_data.course_direction_references,
        living_cost_hint=living_hint[:430],
        suggested_course_plan_lines=suggested_lines[:4],
    )


def _resolve_target_partner_lookup(
    home_id: str,
    target_partner: str | None,
    catalogue_loader: Callable[[UniversityProfile], tuple[list[PartnerUniversity], CatalogueSourceStatus | None]],
) -> tuple[StudyPlanPartnerCourseLookup | None, list[StudyPlanPartnerCourseLookup]]:
    flagship_pairs = [
        ("germany", "technical-university-of-munich"),
        ("japan", "waseda-university"),
        ("germany", "lmu-munich"),
    ]
    featured: list[StudyPlanPartnerCourseLookup] = []
    for c_slug, i_slug in flagship_pairs:
        lookup = _build_partner_lookup_from_cross_school(home_id, c_slug, i_slug, catalogue_loader)
        if lookup is not None:
            featured.append(lookup)

    selected: StudyPlanPartnerCourseLookup | None = None
    if target_partner and target_partner.strip():
        q = target_partner.strip()
        # First check if q matches one of the flagship lookups
        for item in featured:
            if (
                q.lower() in item.partner_school_name_zh.lower()
                or q.lower() in item.partner_school_name_en.lower()
                or q.lower() == item.institution_slug
            ):
                selected = item
                break
        if selected is None:
            directory = build_cross_school_partner_directory(
                catalogue_loader=catalogue_loader,
                q=q,
                limit=5,
            )
            if directory.items:
                top = directory.items[0]
                selected = _build_partner_lookup_from_cross_school(
                    home_id, top.country_slug, top.institution_slug, catalogue_loader
                )

    if selected is None and featured:
        selected = featured[0]

    return selected, featured


def _build_dcard_launch_draft(
    uni: UniversityProfile,
    spec: dict[str, object],
    online_deadline: str,
    paper_deadline: str,
    study_plan_limit: str,
    in_window: bool,
    window_status: str,
    pitfalls: list[StudyPlanPitfallRule],
    source_url: str,
    last_checked_at: str,
) -> DcardSchoolBoardLaunchDraft:
    workbench_link = f"/?school={uni.id}#application-form=study-plan"
    partner_hub_link = f"/partners?home={uni.id}"
    pitfall_bullets = [
        f"{p.badge_label}｜{p.pitfall_title}（評分與配重：{p.scoring_weight}）"
        for p in pitfalls
    ]
    pitfall_md = "\n".join(f"- **{b}**" for b in pitfall_bullets)

    markdown_body = f"""各位 {uni.short_name} 的同學大家好～
正在準備出國交換校內甄選的人，動筆寫讀書計畫前請先核對國際處當期簡章（最後查核日：`{last_checked_at}`），千萬別踩到格式或配重地雷：

### ⚠️ 1. 先給價值：{uni.short_name} 交換簡章最容易踩雷的規定
- **校內線上報名截止日**：{online_deadline}
- **紙本繳件／核章規定**：{paper_deadline}
- **讀書計畫字數／頁數與配重規定**：{study_plan_limit}
{pitfall_md}
- 🔗 **官方 HTTPS 簡章來源**：{source_url}

---

### 🛠️ 2. 再給工具：{uni.short_name} 專屬「申請文件工作台」＋跨校姊妹校開課對照（完全免費）
為了不讓大家在十幾個國際處 PDF 之間切到崩潰，我們把 **{uni.school_name}** 的官方規定直接做進 UniWay 的「申請文件工作台」裡了：
1. **內建 {uni.short_name} 字數＆A4 頁數即時換算出太陽計數器**：邊打字邊看目前合計字數與約幾頁 A4，不怕超頁或未達下限。
2. **6 段式高分讀書計畫寫作提示**：把「申請動機、選校理由、量化研修目標、預計修課與抵免、預期成果、返國連結」拆成 6 個結構化欄位，每欄都有避開罐頭文的公式與範例。
3. **直接對照 `/partners` 頁的全台跨校姊妹校開課資訊**：寫第 2 段「選校理由」與第 4 段「修課規劃」時，可直接在工作台右側切換目標姊妹校（如慕尼黑工大、早稻田等），查看跨校學長姐曾修過的課程方向、生活費與住宿提醒（全數為結構化重點摘要＋官方／公開原文連結），寫完直接匯出 Word（`.docx`）或 PDF！

👉 **{uni.short_name} 讀書計畫工作台直達入口**：`{workbench_link}`
👉 **跨校外國大學頁（查姊妹校開課方向與生活費）**：`{partner_hub_link}`
"""

    return DcardSchoolBoardLaunchDraft(
        school_id=uni.id,
        school_name=uni.school_name,
        short_name=uni.short_name,
        dcard_board_name=str(spec.get("dcard_board", f"Dcard {uni.short_name}板 ＋ 留學板")),
        in_next_10_weeks_window=in_window,
        window_status=window_status,
        recommended_publish_window=str(spec.get("recommended_publish_window", "截止前 2～3 週")),
        post_title=str(spec.get("post_title", f"#分享 {uni.short_name}出國交換讀書計畫防雷整理＆6 段式文件工作台")),
        pitfall_hook_bullets=pitfall_bullets,
        workbench_deep_link=workbench_link,
        partner_hub_deep_link=partner_hub_link,
        markdown_body=markdown_body,
    )


def build_study_plan_workbench_payload(
    school: str | UniversityProfile | None = None,
    *,
    target_partner: str | None = None,
    catalogue_loader: Callable[[UniversityProfile], tuple[list[PartnerUniversity], CatalogueSourceStatus | None]] | None = None,
) -> StudyPlanWorkbenchPayload:
    """Build the Action 3 Study Plan Anti-Pitfall + Workbench payload for a given home university."""
    uni = (
        school
        if isinstance(school, UniversityProfile)
        else (resolve_university(school) if school else SUPPORTED_UNIVERSITIES[0])
    ) or SUPPORTED_UNIVERSITIES[0]

    window_card = get_verified_school_window_card(uni.id)
    writing_rule = WRITING_RULES.get((uni.id, "study-plan"))
    src_meta = SCHOOL_WRITING_RULE_SOURCES.get(
        uni.id,
        (window_card.online_deadline.source_url, window_card.online_deadline.last_checked_at),
    )
    source_url = (writing_rule.source_url if writing_rule and writing_rule.source_url else None) or src_meta[0]
    last_checked_at = (
        (writing_rule.last_checked_at if writing_rule and writing_rule.last_checked_at else None)
        or src_meta[1]
    )

    spec = SCHOOL_PITFALL_SPECS.get(uni.id, SCHOOL_PITFALL_SPECS["cgu"])
    raw_pitfalls = list(spec.get("pitfalls", []))
    pitfalls = [
        StudyPlanPitfallRule(
            rule_id=str(item["rule_id"]),
            severity=item.get("severity", "critical"),  # type: ignore[arg-type]
            badge_label=str(item["badge_label"]),
            pitfall_title=str(item["pitfall_title"]),
            detail_zh=str(item["detail_zh"]),
            scoring_weight=str(item["scoring_weight"]),
            format_and_limit=str(item["format_and_limit"]),
            source_url=source_url,
            last_checked_at=last_checked_at,
        )
        for item in raw_pitfalls
    ]

    selected_lookup = None
    featured_lookups: list[StudyPlanPartnerCourseLookup] = []
    if catalogue_loader is not None:
        selected_lookup, featured_lookups = _resolve_target_partner_lookup(
            uni.id, target_partner, catalogue_loader
        )

    dcard_draft = _build_dcard_launch_draft(
        uni=uni,
        spec=spec,
        online_deadline=window_card.online_deadline.value_text,
        paper_deadline=window_card.paper_deadline.value_text,
        study_plan_limit=window_card.study_plan_limit.value_text,
        in_window=window_card.in_ten_week_window,
        window_status=window_card.window_status,
        pitfalls=pitfalls,
        source_url=source_url,
        last_checked_at=last_checked_at,
    )

    return StudyPlanWorkbenchPayload(
        school_id=uni.id,
        school_name=uni.school_name,
        short_name=uni.short_name,
        in_next_10_weeks_window=window_card.in_ten_week_window,
        online_deadline_text=window_card.online_deadline.value_text,
        paper_deadline_text=window_card.paper_deadline.value_text,
        official_study_plan_limit_text=window_card.study_plan_limit.value_text,
        min_chars=writing_rule.min_chars if writing_rule else None,
        max_chars=writing_rule.max_chars if writing_rule else None,
        estimated_chars_per_a4_page=900,
        max_a4_pages_hint=float(spec["max_a4_pages_hint"]) if spec.get("max_a4_pages_hint") is not None else None,
        scoring_weight_headline=str(spec.get("scoring_weight_headline", window_card.study_plan_limit.value_text)),
        pitfalls=pitfalls,
        six_step_guide=SIX_STEP_STUDY_PLAN_GUIDE,
        selected_partner_lookup=selected_lookup,
        featured_partner_lookups=featured_lookups,
        dcard_launch_draft=dcard_draft,
        workbench_url=f"/?school={uni.id}#application-form=study-plan",
        source_url=source_url,
        last_checked_at=last_checked_at,
    )


def build_study_plan_workbench_catalog(
    *,
    only_active_10_week_window: bool = False,
    catalogue_loader: Callable[[UniversityProfile], tuple[list[PartnerUniversity], CatalogueSourceStatus | None]] | None = None,
) -> StudyPlanWorkbenchCatalog:
    """Return the full catalog of study-plan anti-pitfall & Dcard launch payloads across supported universities."""
    schools: list[StudyPlanWorkbenchPayload] = []
    active_count = 0
    for uni in SUPPORTED_UNIVERSITIES:
        payload = build_study_plan_workbench_payload(uni, catalogue_loader=catalogue_loader)
        if payload.in_next_10_weeks_window:
            active_count += 1
        if only_active_10_week_window and not payload.in_next_10_weeks_window:
            continue
        schools.append(payload)

    return StudyPlanWorkbenchCatalog(
        reference_date=WINDOW_START_DATE,
        window_end_date=WINDOW_END_DATE,
        total_supported_schools=len(SUPPORTED_UNIVERSITIES),
        active_10_week_window_count=active_count,
        six_step_guide=SIX_STEP_STUDY_PLAN_GUIDE,
        schools=schools,
    )
