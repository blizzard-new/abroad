"""Student-facing writing help for application document fields.

Two layers, deliberately kept apart so students never mistake advice for a rule:

* ``FIELD_GUIDANCE`` explains what a field is asking and how to answer it. Any
  character range in it is system advice, not a school requirement.
* ``WRITING_RULES`` records length and format rules that the school's own
  guidelines state for a whole document. Every entry names the official
  document it was checked against; a school without an entry has simply not
  been checked, and the form says so rather than implying there is no rule.
"""

from __future__ import annotations

from .models import (
    ApplicationDocumentTemplate,
    ApplicationFieldGuidance,
    ApplicationFieldType,
    ApplicationFormField,
    ApplicationWritingRules,
)

_STUDY_PLAN_FIELDS = [
    "motivation",
    "school_reason",
    "learning_goals",
    "course_plan",
    "expected_outcomes",
    "return_plan",
]
_RETURN_REPORT_FIELDS = ["courses_summary", "life_summary", "reflection"]


def _guide(
    summary: str,
    *,
    tips: tuple[str, ...] = (),
    outline: tuple[str, ...] = (),
    example: str | None = None,
    format_note: str | None = None,
    recommended: tuple[int, int] | None = None,
) -> ApplicationFieldGuidance:
    return ApplicationFieldGuidance(
        summary=summary,
        tips=list(tips),
        outline=list(outline),
        example=example,
        format_note=format_note,
        recommended_min_chars=recommended[0] if recommended else None,
        recommended_max_chars=recommended[1] if recommended else None,
    )


_PASSPORT_NOTE = "照護照資料頁填寫，大小寫、空格與連字號都要一致。"

# Keyed by field id. Fields that mean something different inside a template
# (same id, different document) are overridden in TEMPLATE_FIELD_GUIDANCE.
FIELD_GUIDANCE: dict[str, ApplicationFieldGuidance] = {
    "motivation": _guide(
        "說明你為什麼想交換，以及它和你的學習方向、職涯目標有什麼關聯。",
        tips=(
            "先寫你目前的學習背景或遇到的瓶頸，再說交換能補上什麼。",
            "用具體經驗佐證（修過的課、專題、社團、打工），不要只寫「開拓視野」「體驗文化」。",
            "不要和「選擇這間學校的原因」重複；這一欄聚焦在「為什麼要交換」。",
        ),
        outline=("我的學習背景與興趣", "目前想突破的限制", "交換如何幫助我的學習與職涯"),
        example="我就讀經濟系，修過《國際貿易》後發現課堂案例多來自歐美，對其他市場缺少第一手理解。希望透過一學期交換修習相關課程，並把觀察運用在畢業專題。",
        recommended=(300, 600),
    ),
    "school_reason": _guide(
        "具體寫出這間學校的課程、師資或資源，如何對應你的學習需求，不只描述國家與城市。",
        tips=(
            "到該校官網找 2–3 門你想修的課，或你有興趣的教授、研究中心，直接點名寫出。",
            "說明這些資源為什麼是本校沒有或很少的。",
            "城市與生活環境可以提，但不要當成唯一理由。",
        ),
        outline=("該校和我領域相關的課程、師資或資源", "與本校相比的差異", "我預計怎麼運用"),
        example="貴校開設《Behavioral Finance》與《Asian Economic Development》，本校沒有對應課程，且貴校研究中心定期舉辦業界講座，符合我想了解實務應用的需求。",
        recommended=(300, 600),
    ),
    "learning_goals": _guide(
        "列出可驗證的語言、專業與跨文化目標。",
        tips=(
            "分成語言、專業、跨文化（或生活）三類，各寫 1–2 個目標。",
            "目標要能檢驗：用數量或成果表達，例如修畢 3 門專業課、完成一份報告。",
            "避免只寫「提升英文」「增加國際觀」這類無法檢查的目標。",
        ),
        outline=("語言目標", "專業學習目標", "跨文化或個人成長目標"),
        example="語言：結束前能用英文完成一次 10 分鐘課堂簡報。專業：修畢 3 門與主修相關的課並取得及格成績。跨文化：加入一個當地社團並與在地學生合作一項活動。",
        recommended=(250, 500),
    ),
    "course_plan": _guide(
        "填入預計修讀的課名、學分與預計抵免方式；正式選課仍以合作校為準。",
        tips=(
            "先到合作校官網查最新課程清單與開課學期，課名盡量用官方原文。",
            "每門課寫：課名、學分、預計抵免本校哪一類（必修、選修或通識）。",
            "多列幾門備案課程，因為實際開課可能變動。",
            "能否抵免以系所審核為準，可先請系辦確認。",
        ),
        format_note="建議每行一門課：課名｜學分｜預計抵免方式",
        example="Behavioral Finance｜3 學分｜預計抵免專業選修\nAsian Economic Development｜3 學分｜預計抵免選修",
    ),
    "expected_outcomes": _guide(
        "寫出交換結束時「拿得出來」的成果，例如完成課程、作品、檢定或成果分享。",
        tips=(
            "盡量具體：學分數、語言檢定、作品、報告或分享會。",
            "與前面的研修目標一一對應，審查者才看得出規劃是完整的。",
        ),
        outline=("學業成果", "語言或技能成果", "可分享或延伸的成果"),
        example="取得 12 學分並完成一份跨國比較報告；返國後在系上舉辦一場交換經驗分享。",
        recommended=(150, 400),
    ),
    "return_plan": _guide(
        "說明返國後的學分採認、成果分享及後續學習安排。",
        tips=(
            "寫出返國後學分抵免的流程與你預計辦理的時間。",
            "說明你會如何回饋學校或學弟妹，例如分享會、心得、協助新生。",
            "連結到畢業專題、升學或就業規劃。",
        ),
        outline=("學分採認安排", "成果分享方式", "後續學習或職涯規劃"),
        recommended=(150, 400),
    ),
    "english_version": _guide(
        "合作校要求英文版時才需要填寫，內容應與中文版一致。",
        tips=(
            "先完成中文版，再自行翻譯，或請老師、國際處協助檢查文法。",
            "系統不會自動翻譯或改寫你的內容。",
            "合作校若有指定表格或字數，以對方規定為準。",
        ),
    ),
    "school_choices": _guide(
        "依志願順序列出你要申請的學校。",
        tips=(
            "第一行是第一志願，依序往下排。",
            "使用學校官方名稱，並確認該校當期有名額、符合語言與成績門檻。",
            "可填的志願數以學校簡章規定為準。",
        ),
        format_note="每行一間學校，依志願順序填寫。",
    ),
    "supporting_achievements": _guide(
        "列出對申請有幫助的獲獎、專題、社團或國際經驗；沒有可留白。",
        tips=(
            "挑和申請最相關的 3–5 項，寫明時間、你的角色與成果。",
            "有證明文件的項目優先列出。",
            "系統不會替你補寫內容，留白就是留白。",
        ),
        example="2025 校內專題競賽第二名（擔任組長，負責資料分析）。",
    ),
    "autobiography": _guide(
        "介紹你的成長背景、學習經歷與個人特質，讓審查者認識你。",
        tips=(
            "用 2–3 個關鍵經驗串起來，不要寫成流水帳。",
            "每個經驗說明你做了什麼、學到什麼。",
            "結尾連結到你為什麼想出國交換。",
        ),
        outline=("成長與學習背景", "關鍵經驗與收穫", "個人特質與未來方向"),
    ),
    "study_plan": _guide(
        "說明交換期間要修什麼課、怎麼安排學習，以及和你主修的關聯。",
        tips=(
            "寫出想修的課程或研究主題，並說明為什麼選它們。",
            "安排學習的時間順序，例如前半學期適應、後半學期專題。",
            "連結到返國後的學習或畢業規劃。",
        ),
        outline=("預計修讀的課程或主題", "學習安排", "與主修及返國後的連結"),
    ),
    "completed_courses": _guide(
        "列出在合作校已修完的課程與成績。",
        tips=(
            "課號、課名、學分與成績請照合作校正式成績單填寫。",
            "不要自行推估或換算成績，成績以正式成績單為準。",
        ),
        format_note="每行一門課：課號｜課名｜學分｜成績",
    ),
    "overseas_courses": _guide(
        "列出你在合作校預計修習的課程與學分。",
        tips=(
            "課號與課名請用合作校官方原文。",
            "學分填合作校的學分數，不要自行換算成本校學分。",
        ),
        format_note="每行一門課：課號｜課名｜學分",
    ),
    "credit_mapping": _guide(
        "寫出每門海外課程預計對應到本校的哪一門課或哪一類學分。",
        tips=(
            "每行對應一門海外課程。",
            "能否採認以系所與教務處審核為準，建議先向系辦確認。",
        ),
        format_note="每行：海外課程 → 本校課程或選修學分",
    ),
    "requested_mapping": _guide(
        "寫出你申請採認的方式：每門海外課程對應到本校哪一門課或哪一類學分。",
        tips=(
            "每行對應一門海外課程，課名與成績單上的一致。",
            "最終能否採認以系所與教務處審核為準。",
        ),
        format_note="每行：海外課程 → 本校課程或選修學分",
    ),
    "issues_and_support": _guide(
        "寫出遇到的問題，以及需要學校協助的事項；沒有可留白。",
        tips=(
            "只寫需要協助或值得提醒的問題，例如選課、住宿、簽證、安全或健康。",
            "寫明發生時間與目前狀況，承辦人才能判斷怎麼協助。",
        ),
    ),
    "mailing_address": _guide(
        "請填你收件方便的完整通訊地址。",
        format_note="包含郵遞區號、縣市、路街與樓層。",
    ),
    "overseas_address": _guide(
        "請填你在海外的住宿地址。",
        tips=("與住宿合約或住宿證明上的地址一致。", "地址用當地語言或英文書寫。"),
        format_note="包含街道、門牌、城市、郵遞區號與國家。",
    ),
    "institution_address": _guide(
        "請填海外學校或機構的完整地址。",
        format_note="包含街道、城市、郵遞區號與國家，與官方資料一致。",
    ),
    "student_name_zh": _guide("請填你的中文全名。", format_note="與學生證、在學證明上的姓名一致。"),
    "student_name_en": _guide("請填護照上的英文姓名。", format_note=_PASSPORT_NOTE),
    "passport_number": _guide(
        "請填你的護照號碼。",
        tips=("多數國家要求入境時護照剩餘效期達 6 個月以上，請依目的國規定確認。",),
        format_note=_PASSPORT_NOTE,
    ),
    "id_number": _guide("請填你的身分證字號。", format_note="國民身分證為 1 個英文字母加 9 位數字。"),
    "student_id": _guide("請填你的學號。", format_note="與學生證上的學號一致。"),
    "college": _guide("請填就讀學院全名。", format_note="與在學證明一致。"),
    "department": _guide("請填就讀系所或學程全名。", format_note="與在學證明一致，例如「經濟學系」。"),
    "email": _guide("請填你會固定查看的信箱。", tips=("學校或合作校的聯絡可能寄到這裡，請避免填寫常漏看的信箱。",)),
    "phone": _guide("請填隨時可聯絡到你的手機號碼。", format_note="例如 0912-345-678。"),
    "emergency_contact": _guide(
        "請填出國期間能聯絡到的家人或監護人。",
        tips=("請事先告知對方，並確認對方會接陌生來電或訊息。",),
    ),
    "emergency_phone": _guide("請填緊急聯絡人的電話。", format_note="海外撥打時需加國碼，例如 +886。"),
    "language_score": _guide(
        "照成績單上的分數或級別填寫。",
        format_note="例如 TOEFL iBT 85、IELTS 6.5、JLPT N2。",
    ),
    "class_rank_percent": _guide(
        "請填成績單上的班級排名百分比。",
        tips=("以教務處核發的成績單為準；排名 ÷ 班級人數 × 100 可用來自行估算。",),
    ),
    "academic_average": _guide(
        "請照教務處成績單填寫歷年學業平均。",
        tips=("小數位數與成績單一致，不要自行四捨五入。",),
    ),
    "study_period": _guide(
        "請填預計研修期間。",
        format_note="例如 2027/02–2027/06，實際日期依合作校行事曆。",
    ),
    "planned_start_date": _guide(
        "先填預估日期即可。",
        tips=("日期依合作校學期行事曆與機票安排調整。",),
    ),
    "planned_end_date": _guide(
        "先填預估日期即可。",
        tips=("日期依合作校學期行事曆與機票安排調整。",),
    ),
    "departure_flight": _guide(
        "請填去程航班資訊。",
        format_note="航空公司、航班號碼、起飛日期與時間，例如 BR189，2027/02/01 10:30。",
    ),
    "video_url": _guide(
        "請貼上可以開啟的影片連結。",
        tips=("使用 YouTube 或雲端硬碟連結，並先確認權限設為可檢視。",),
    ),
    "overseas_institution": _guide(
        "請填合作學校或機構的官方名稱。",
        tips=("與錄取通知或合作校名單上的名稱一致。",),
    ),
}

# (template id, field id) -> guidance, for fields whose id is reused with a
# different meaning in another document.
TEMPLATE_FIELD_GUIDANCE: dict[tuple[str, str], ApplicationFieldGuidance] = {
    ("return-report", "courses_summary"): _guide(
        "列出你實際修過的課程，以及從中學到的內容與成果。",
        tips=(
            "依課名列出：課名、學分、成績或完成情形。",
            "挑 1–2 門最有收穫的課，寫上授課方式、作業與你的學習心得。",
            "對照當初的研修目標，說明達成了多少。",
        ),
    ),
    ("return-report", "life_summary"): _guide(
        "寫出在當地的生活與文化適應經驗。",
        tips=(
            "從住宿、交通、飲食、人際中挑最有感的 2–3 件事。",
            "用具體事件說明你如何適應文化差異。",
            "可以附上對下一位學弟妹有用的生活資訊。",
        ),
    ),
    ("return-report", "reflection"): _guide(
        "寫下你的整體心得，並給學弟妹具體建議。",
        tips=(
            "分享「我學到什麼」與「如果重來我會怎麼做」。",
            "給學弟妹的建議越具體越好：行前準備、選課、預算、生活提醒。",
            "避免寫入你或他人的個資，也不要放未經查證的評論。",
        ),
        outline=("最大的收穫", "遇到的困難與解法", "給學弟妹的建議"),
    ),
    ("semester-report", "courses_summary"): _guide(
        "報告本期的修課進度與學習狀況。",
        tips=(
            "列出已修與在修課程，以及目前進度。",
            "學習上的困難另寫在「遇到的問題與需要協助事項」。",
        ),
    ),
    ("semester-report", "life_summary"): _guide(
        "報告目前的生活與適應狀況。",
        tips=("簡述住宿、安全與健康狀況，以及和當地的互動。",),
    ),
    ("short-term-plan-2b0001002", "motivation"): _guide(
        "說明辦理這個境外短期課程的動機與學生學習目標。",
        tips=("寫出教學需求，以及課程和本校課程的關聯。",),
    ),
    ("short-term-plan-2b0001002", "implementation"): _guide(
        "說明課程怎麼進行：方式、時間與地點。",
        tips=("日期與上方課程起迄日一致。", "寫明合作機構與上課地點。"),
    ),
    ("short-term-plan-2b0001002", "selection_criteria"): _guide(
        "說明參加課程的學生要符合哪些資格，以及如何遴選。",
        tips=("條件要具體，例如年級、成績或語言門檻。",),
    ),
    ("short-term-plan-2b0001002", "expected_outcomes"): _guide(
        "說明課程結束後預期達成的成效。",
        tips=("與學習目標對應，盡量用可檢驗的成果表達。",),
    ),
    ("short-term-plan-2b0001002", "return_obligations"): _guide(
        "說明學生返國後需要完成的義務。",
        tips=("例如繳交心得報告、成果分享，依校方規定填寫。",),
    ),
    ("short-term-plan-2b0001002", "other_information"): _guide(
        "補充上面欄位沒有涵蓋、但審查需要知道的資料；沒有可留白。",
    ),
    ("short-term-report-2b0001004", "activities"): _guide(
        "依時間順序簡述課程經過與活動。",
        tips=("按日期或階段寫，並註明授課機構與參與方式。",),
    ),
    ("short-term-report-2b0001004", "outcomes"): _guide(
        "寫出課程帶來的具體成果。",
        tips=("可包含完成的作業、作品、證書或學到的技能。",),
    ),
    ("short-term-report-2b0001004", "reflection"): _guide(
        "寫下你的心得，並給之後參加的同學建議。",
        tips=("分享收穫與困難，建議越具體越好。",),
    ),
    ("short-term-report-2b0001004", "other_information"): _guide(
        "補充其他想說明的事；沒有可留白。",
    ),
}


def _rules(
    rules: tuple[str, ...],
    *,
    evidence: str,
    minimum: int | None = None,
    maximum: int | None = None,
    count_fields: list[str] | None = None,
    count_note: str | None = None,
) -> ApplicationWritingRules:
    return ApplicationWritingRules(
        rules=list(rules),
        min_chars=minimum,
        max_chars=maximum,
        count_field_ids=list(count_fields or []),
        count_note=count_note,
        evidence=evidence,
    )


_NOT_COLLECTED = ApplicationWritingRules(
    rules=[
        "目前沒有查到這間學校對這份文件公開的字數或格式規定。",
        "欄位旁的字數上限與建議只是系統的參考，不是學校規定；送件前請向國際處或當期簡章確認。",
    ],
    verified=False,
)

# Documents students write long answers for; only these get the "not collected" notice.
_NARRATIVE_TEMPLATES = {"study-plan", "return-report"}

# (university id, template id) -> rules published by that school. Each entry
# restates wording found in the school's official page or guidelines (named in
# ``evidence``). A school or document without an entry here has not been
# checked, and the form says so instead of guessing.
WRITING_RULES: dict[tuple[str, str], ApplicationWritingRules] = {
    ("ntpu", "study-plan"): _rules(
        (
            "計畫書以 A4 紙直式橫書，合計 5,000 字以內，格式自訂。",
            "內容須包含個人學經歷、申請動機、未來學習計畫與發展。",
            "依申請語組繳交：英文組繳英文計畫書、中文組繳中文計畫書、日文組繳日文計畫書。",
        ),
        evidence="臺北大學 116 學年度赴外交換簡章（申請步驟及應繳文件）",
        maximum=5000,
        count_fields=_STUDY_PLAN_FIELDS,
        count_note="學校規定的是整份計畫書合計；這裡只合計下方各欄。",
    ),
    ("ntu", "study-plan"): _rules(
        (
            "出國交換計畫書：A4 兩面，至少 500 字，中文或英文。",
            "履歷表另備：A4 兩面，中文或英文，無標準格式。",
        ),
        evidence="臺大 116-1 校級出國交換簡章（應繳文件）",
        minimum=500,
        count_fields=_STUDY_PLAN_FIELDS,
        count_note="學校規定的是整份計畫書；這裡只合計下方各欄。",
    ),
    ("fju", "study-plan"): _rules(
        (
            "116-1（2027秋季班）書審資料：中文讀書計畫（只需繳交一份中文版，不需繳交英文版，至少 500 字，格式不拘，兩頁為限）與中文簡歷（就學、工作及社團經驗，格式不拘，兩頁為限），合併為單一 PDF 電子檔（勿超過 20MB）上傳至線上申請系統。",
            "舊版一般規定（labelID=43）：讀書計畫（Study Plan）及自傳 A4 雙面列印，不超過 2 頁（4 面）。",
        ),
        evidence="輔仁大學 116-1（2027秋季班）赴姊妹校交換學生申請公告（newsID=1062）與申請應備文件規範",
        minimum=500,
        count_fields=_STUDY_PLAN_FIELDS,
        count_note="學校規定的是整份中文讀書計畫（至少 500 字，兩頁為限）；這裡只合計下方各欄。",
    ),
    ("fju", "return-report"): _rules(
        ("返國後 1 個月內繳交 2,000 字以上的交換心得報告與成績單。",),
        evidence="輔仁大學：交換學生獎學金補助辦法與經費說明",
        minimum=2000,
        count_fields=_RETURN_REPORT_FIELDS,
        count_note="學校規定的是整份心得報告；這裡只合計下方各欄。",
    ),
    ("scu", "study-plan"): _rules(
        (
            "自傳或履歷 1 份，約 2,000 字，合併為單一 PDF 上傳（上限 5MB）。",
            "交換研修動機及讀書計畫一校一份，各約 2,000 字以內。",
            "赴外交換須同時撰寫中文 Form A 與外文 Form B，依志願序將所有中文表格排在前、外文表格在後，合併為單一 PDF。",
        ),
        evidence="東吳大學：線上申請系統備審文件規範",
    ),
    ("scu", "return-report"): _rules(
        ("返臺後 1 個月內繳交 1,500–2,000 字的心得報告。",),
        evidence="東吳大學：赴外與赴陸港澳交換獎助學金及經費規定",
        minimum=1500,
        maximum=2000,
        count_fields=_RETURN_REPORT_FIELDS,
        count_note="學校規定的是整份心得報告；這裡只合計下方各欄。",
    ),
    ("ntnu", "study-plan"): _rules(
        (
            "自傳與出國學習計畫以中文或外文撰寫，格式不限。",
            "中英文合計須介於 500 至 5,000 字之間；建議另附外文版本約 500 至 2,500 字。",
            "自傳及出國學習計畫占甄選評分 20%。",
        ),
        evidence="臺灣師範大學：線上申請系統應備文件與報名費繳交規範",
        minimum=500,
        maximum=5000,
        count_fields=_STUDY_PLAN_FIELDS,
        count_note="學校的字數是「自傳＋出國學習計畫」合計；這裡只合計下方的計畫欄位，自傳字數請另外加進去。",
    ),
    ("fcu", "study-plan"): _rules(
        (
            "研修計畫（簡章附件二）中文或英文均可，字數至少 1,000 字。",
            "內容含動機、修課規劃與預期效益。",
        ),
        evidence="逢甲大學國際事務處「選送學生出國研修」頁（簡章附件說明）",
        minimum=1000,
        count_fields=_STUDY_PLAN_FIELDS,
        count_note="學校規定的是整份研修計畫；這裡只合計下方各欄。",
    ),
    ("fcu", "return-report"): _rules(
        ("返國後 1 個月內繳交 2,000 字以上的研習報告書。",),
        evidence="逢甲大學國際事務處「選送學生出國研修」頁（簡章附件說明）",
        minimum=2000,
        count_fields=_RETURN_REPORT_FIELDS,
        count_note="學校規定的是整份研習報告書；這裡只合計下方各欄。",
    ),
    ("ncu", "return-report"): _rules(
        (
            "辦理返校手續時繳交 Word 電子檔心得報告，原文為「至少 800-1500 字」。",
            "內容需包含交換計畫的執行狀況及至少 4 張照片。",
        ),
        evidence="中央大學 116 學年度第一梯次甄選簡章（交換生義務）",
        minimum=800,
        count_fields=_RETURN_REPORT_FIELDS,
        count_note="簡章寫「至少 800-1500 字」，上限是否強制請向國際處確認，這裡只檢查 800 字下限。",
    ),
    ("ccu", "study-plan"): _rules(
        (
            "研修計畫書中文或英文皆可，須包含自傳、讀書計畫與申請動機。",
            "不限格式，每項約 A4 一頁。",
        ),
        evidence="中正大學 2027 春季交換簡章（申請文件）",
    ),
    ("cycu", "study-plan"): _rules(
        (
            "須繳交中文及英文讀書計畫（Study Plan），以及中文及英文自傳（Autobiography）。",
            "電子檔須依國際處規定的格式寄送。",
        ),
        evidence="中原大學：出國交換申請應繳紙本與電子備審文件",
    ),
    ("yzu", "return-report"): _rules(
        (
            "完成交換返國後 2 週內，繳交 1,500 字以上的研修心得報告與 6 張照片，並完成學分抵免，NT$5,000 保證金才會全額無息退還。",
        ),
        evidence="元智大學：交換學生申請資格、系排50%＋英檢50%評選、保證金與最低修課學分",
        minimum=1500,
        count_fields=_RETURN_REPORT_FIELDS,
        count_note="學校規定的是整份心得報告；這裡只合計下方各欄，照片要另外放滿 6 張。",
    ),
    ("cycu", "return-report"): _rules(
        (
            "領取《中原大學學生赴海外姊妹校交換學習助學辦法》助學金者，須於返國後二週內向國際暨兩岸教育處提交研習成果報告書辦理核銷，並出席交換生說明會。",
            "官方資料沒有公布心得報告的字數、照片張數或授權格式；請依國際處通知準備。",
        ),
        evidence="中原大學學生赴海外姊妹校交換學習助學辦法第六條",
    ),
    ("yzu", "study-plan"): _rules(
        (
            "須繳交中英文讀書計畫（Study Plan），並可附其他有利審查資料（個人履歷 CV、獲獎或社團證明）。",
            "赴大陸地區交換者，須含 500 字以上的中文讀書計畫。",
        ),
        evidence="元智大學：出國交換第一階段與第二階段應繳文件及切結書規範",
    ),
    ("nccu", "study-plan"): _rules(
        (
            "校級國際薦外交換：交換計畫書與履歷表（含簡歷及自傳）須分為 2 份文件撰寫，合計占甄選總成績 20%；限以電腦繕打、A4 直式橫書，每份各至少 500 字、以 2 頁為限（超出 2 頁之內容不予計分），皆應以報考語組之語言撰寫。",
            "校級赴大陸地區交換：個人自傳 1,000 字以內、研究／學習計畫 3,000 字以內（格式不拘，超過字數者恕不受理；書面成績占總成績 35%）。",
        ),
        evidence="政治大學 115 學年度第 1 學期校級國際薦外交換生甄選簡章與赴大陸地區交換生甄選簡章",
        minimum=500,
        maximum=3000,
        count_fields=_STUDY_PLAN_FIELDS,
        count_note="校級國際薦外交換規定交換計畫書至少 500 字（以 2 頁為限）；赴大陸地區交換規定研究／學習計畫 3,000 字以內（個人自傳另為 1,000 字以內）。這裡只合計下方計畫書各欄。",
    ),
    ("nccu", "return-report"): _rules(
        (
            "返國後 2 個月內須依國合處「交換學生心得報告表」格式繳交交換心得報告電子檔至 outbound@nccu.edu.tw，並於返國 2 年內完成國際活動義工服務至少 1 次（大陸交換為參與至少 2 項兩岸交流活動），始無息全額退還 NT$5,000 保證金。",
            "官方簡章與行前須知沒有公布交換心得報告的字數下限；請依國合處當期公告格式撰寫。",
        ),
        evidence="政治大學 115-1 錄取校級赴外交換生行前須知與赴大陸地區交換生甄選簡章",
    ),
    ("ncku", "study-plan"): _rules(
        (
            "須就所選填志願學校之「第一志願」分別擬訂中文及英文讀書或研究計畫（占校內甄選總成績 25%），以及中文及英文自傳（含學、經歷，與其餘表現合計占總成績 25%）。",
            "連同申請表、志願表、歷年成績單與外語能力證明依序合併為單一 PDF 檔（上限 50MB）上傳；官方簡章沒有公布讀書計畫或自傳的字數與頁數上限。",
        ),
        evidence="成功大學 116 學年第 1 學期校級薦外交換學生計畫簡章（申請資料與審查方式）",
    ),
    ("ncku", "return-report"): _rules(
        (
            "交換結束返國後 2 個月內，須依規定格式完成交換生心得報告（繳交可編輯之 Word 及 PDF 檔各乙份），連同交換校成績單及返國問卷調查寄至國際處業務承辦人信箱，始得辦理 NT$8,000 保證金（低收／中低收入戶 NT$2,000）退還。",
            "領取跨國雙向研修獎助學金者，須於赴外研修結束之日起 1 個月內繳交出國報告書；官方簡章與獎助辦法沒有公布心得報告的固定字數下限。",
        ),
        evidence="成功大學 116 學年第 1 學期校級薦外交換學生計畫簡章與跨國雙向研修獎助學金補助辦法",
    ),
    ("nsysu", "study-plan"): _rules(
        (
            "須下載國際處「研修計畫書空白表格」填寫並上傳 PDF（占甄選總分 20%，未提供者此項目以零分計）。",
            "赴其他國家與地區須含中、英文各以 1 頁 A4 為限；赴日本須含中文及日文各 1 頁 A4；赴中國大陸以中文 1–2 頁 A4 撰寫，須含修課規劃與讀書計畫。",
        ),
        evidence="中山大學第 55 屆出國交換學生甄選簡章（美加歐亞紐澳、日本、中國大陸）",
    ),
    ("nsysu", "return-report"): _rules(
        (
            "交換期滿返國後 2 個月內須繳交返國報告書（含中文 1,500–2,000 字、英文 1,000–1,500 字雙語心得及 4 張具圖說照片；赴中國交換者免附英文心得）及正式成績單查驗，並參加國際處交流推廣活動，始核發交換學生證明書。",
        ),
        evidence="中山大學第 55 屆出國交換學生甄選簡章（錄取後義務與返國報告書規範）",
        minimum=1500,
        maximum=2000,
        count_fields=_RETURN_REPORT_FIELDS,
        count_note="學校規定中文心得 1,500–2,000 字、英文心得 1,000–1,500 字（赴中國交換免附英文心得），並須附 4 張具圖說照片；這裡只合計下方中文心得各欄。",
    ),
    ("nchu", "study-plan"): _rules(
        (
            "校內交換甄選《自傳及讀書計畫》（赴國外組占總成績 30%、赴大陸組占 45%）：格式無限定，至多 A4 大小三面；以「第一志願」為目標撰寫，內容須含「個人特質與經歷」及「交換計畫與未來展望」兩大核心。",
            "有填寫海外地區學校者須繳交英文版，僅申請大陸地區學校者中英文皆可；另申請赴外研修獎學金之「赴國外研修計劃書」須以中文撰寫、長度無限制（官方說明簡報建議 1,000–1,500 字，單一檔案勿超過 2MB）。",
        ),
        evidence="中興大學 2027 秋季班出國交換學生甄選簡章與赴外獎學金申請說明簡報",
    ),
    ("nchu", "return-report"): _rules(
        (
            "交換期滿返國後 2 個月內須繳交交換心得報告（《選送學生出國交換甄選辦法》第十三條另載返校後 1 個月內），且畢業前須參與國際處分享活動至少 3 小時。",
            "領取赴外研修獎學金者須於學期結束後 2 週內繳交心得報告（含至少 4 張照片，內容以修課內容為主）辦理第二次撥款；官方簡章沒有公布心得報告的固定字數下限。",
        ),
        evidence="中興大學 2027 秋季班出國交換學生甄選簡章與赴外獎學金申請說明簡報",
    ),
    ("ntut", "study-plan"): _rules(
        (
            "校內交換甄選《研修計畫》：格式不拘，於 1 頁 A4 內簡述申請目的與預期效益，無需針對特定學校撰寫，前往非大陸地區者建議以英文撰寫。",
            "另申請教育部「學海惜珠」計畫者，須加附中文 1 至 2 頁之「赴國外研修動機及企圖心、前瞻性」及中文 1,000–1,500 字之「赴國外研修計劃書」（含個人自傳、赴國外研修之目標與計畫、預期出國研修課程與目前學習之相關性及未來展望）。",
        ),
        evidence="臺北科技大學國際事務處「出國交換 STEP 1 校內甄選」與獎學金申請說明",
    ),
    ("ntut", "return-report"): _rules(
        (
            "研修結束返國後 2 週內（《學生出國研修獎學金發放辦法》第六條另載 1 個月內／同一會計年度內）須繳交「心得報告及調查表」與研修照片圖檔 5 張（須為本人與國外友人活動或與校門、校徽等合影，勿提供風景照）。",
            "一般生（無獎學金）及校內獎學金生為 2,000 字以上；教育部學海飛颺、學海惜珠及臺奧高教種籽基金受獎生為 3,000 字以上（學海受獎生另須於返國後 2 週內上傳至教育部選送人才出國研修服務網）。",
        ),
        evidence="臺北科技大學國際事務處「出國交換 STEP 3 出國前後注意事項」與學生出國研修獎學金發放辦法",
        minimum=2000,
        count_fields=_RETURN_REPORT_FIELDS,
        count_note="一般生及校內獎學金生須達 2,000 字以上，教育部學海飛颺／惜珠及臺奧受獎生須達 3,000 字以上，並附研修照片 5 張；這裡以 2,000 字為下限合計下方各欄。",
    ),
    ("ntust", "study-plan"): _rules(
        (
            "歐美亞澳交換簡章規定：須繳交中、英文讀書計畫各一份，以及中、英文自傳各一份；格式不拘，每份篇幅約 1–2 頁，請分別將中、英文版合併為一份 PDF 檔案後上傳（勿加密）。",
            "讀書計畫可針對特定國家或學校撰寫，亦可廣泛敘明目前為止的學習計畫、交換期間以及交換後之規劃；自傳應敘明成長或學習歷程、個性特質或興趣及申請交換的原因。",
            "校內書面審查總分僅計外語能力 60%、在校學業表現 20%、課外表現證明 20%，讀書計畫與自傳不另計分。",
        ),
        evidence="臺灣科技大學 115 學年度第 2 學期歐美亞澳交換學生甄選簡章",
    ),
    ("ntust", "return-report"): _rules(
        (
            "交換計畫結束後 30 天（1 個月）內應返校辦理報到，並完成研修心得報告及照片繳交至國際事務處（赴中國大陸交換須於返臺後 1 個月內完成研修心得報告紙本及電子檔；領取學海飛颺或臺科選優交換生獎學金者須辦畢返校手續、上傳心得報告並檢具成績單與核銷單據後始核撥獎學金）。",
            "官方簡章沒有公布研修心得報告的固定字數或照片張數下限；請依國際事務處線上心得分享系統規定填寫。",
        ),
        evidence="臺灣科技大學 115 學年度第 2 學期歐美亞澳與大陸地區交換學生甄選簡章",
    ),
    ("nycu", "study-plan"): _rules(
        (
            "須繳交中英文自傳與中英文讀書計畫（國外及港澳地區：大學部自傳 10%＋讀書計畫 15%、研究所自傳 20%＋讀書計畫 25%；大陸地區：大學部自傳 15%＋讀書計畫 20%、研究所自傳 25%＋讀書計畫 30%）。",
            "總分相同時，「讀書計畫」為僅次於志願序之第二優先參酌項目；請具體規劃擬修讀之專業課程（大學部每學期至少 3 門、研究所至少 2 門）。",
        ),
        evidence="國立陽明交通大學學生申請出國交換計畫簡章（審查評分項目與同分參酌順序）",
    ),
    ("nycu", "return-report"): _rules(
        (
            "須按期繳交兩階段報告：（1）期中報告：於姐妹校開學後 2 個月內（春季班 4/30 前、秋季班 10/31 前）；（2）期末報告：於交換結束後 1 個月內（春季班 7/31 前、秋季班 1/31 前），並附 3–5 張交換生活照片。",
            "須完成期中報告、期末報告且於姐妹校修習之專業課程全數及格，始無息退還新臺幣 10,000 元保證金。",
        ),
        evidence="國立陽明交通大學學生申請出國交換計畫簡章（第拾壹點、保證金及報告繳交規定）",
    ),
    ("nthu", "study-plan"): _rules(
        (
            "須同時繳交「中文及外文（英文或交換國語言）」之讀書計畫（Study Plan）與自傳（Autobiography）。",
            "讀書計畫須具體列出擬於目標姊妹校修讀之課程規劃列表（海外交換大學部每學期／學季至少 3 門課程及格、研究所至少 1 門研究所課程及格；獲獎學金者須為本科相關專業課程；陸港澳交換大學部至少 9 學分及格）。",
        ),
        evidence="國立清華大學 2027秋／2028春 出國交換生甄選簡章（申請資料及修課規定）",
    ),
    ("nthu", "return-report"): _rules(
        (
            "返國後 1 個月內須繳交四項返國文件：（1）返國報告單、（2）成果報告書（交換心得，授權公開供學弟妹參考）、（3）姊妹校正式成績單、（4）回程登機證存根（獲獎生另須提供 3 分鐘影音檔）。",
            "完成返國文件繳交及系所學分抵免後，於當年度 10–11 月無息退還新臺幣 8,000 元行政處理費（保證金）。",
        ),
        evidence="國立清華大學 2027秋／2028春 出國交換生甄選簡章（返國義務與保證金退費規定）",
    ),
    ("pccu", "study-plan"): _rules(
        (
            "須繳交中、外文讀書計畫（Study Plan）與中、外文自傳（Autobiography）各乙份，各約 1,000 字。",
            "請具體規劃擬於姊妹校修習之課程（依《中國文化大學學生赴境外修讀課程實施要點》及交換簡章規定，出國交換期間每學期至少須修讀 6 學分或 2 門以上課程）。",
        ),
        evidence="中國文化大學出國交換生申請簡章及各語文系交換學生甄選簡章（應繳文件與修課規定）",
    ),
    ("pccu", "return-report"): _rules(
        (
            "交換期滿返國後 1 個月內，須向國際暨兩岸事務處（或所屬語文系辦）繳交交換學生心得報告電子檔（含修課、生活、住宿經驗與多張照片）及《交換生心得報告授權同意書》。",
            "領取《中國文化大學拓展國際視野獎學金》或教育部學海飛颺／惜珠補助者，須完成返國心得報告與相關核銷程序始得結案。",
        ),
        evidence="中國文化大學學生赴境外大學研修獎助學金辦法及交換生心得報告授權同意書",
    ),
    ("wzu", "study-plan"): _rules(
        (
            "須繳交中文讀書計畫（含留學動機，約 1,000 字）與外文讀書計畫（含留學動機，以第一志願組別語言撰寫，約 1,000 字）各乙份。",
            "請具體規劃擬於姊妹校修習之課程（依《文藻外語大學學生出國或赴大陸地區進修作業要點》規定，學士班及專科部出國交換期間每學期至少應修習 6 學分或 3 門課以上且成績及格，碩士班至少修習 1 門課且成績及格，始得申請保證金全額無息退還）。",
        ),
        evidence="文藻外語大學 115 學年度第 2 學期出國暨赴大陸地區交換學生校內甄試簡章（報名檢附資料與保證金退費規定）",
        minimum=1000,
        count_fields=_STUDY_PLAN_FIELDS,
        count_note="簡章規定中文讀書計畫與外文讀書計畫各約 1,000 字；這裡合計下方各欄字數供參考。",
    ),
    ("wzu", "return-report"): _rules(
        (
            "返國後 1 個月內，須向國際暨兩岸合作處繳交約 1,000 字之交換學生研修心得報告（含修課、住宿、生活與文化交流經驗及照片）並簽署授權同意書。",
            "須完成學分抵免（學士班／專科部每學期至少 6 學分或 3 門課及格、碩士班至少 1 門課及格）及心得報告繳交，始得申請無息退還新臺幣 10,000 元保證金。",
        ),
        evidence="文藻外語大學 115 學年度第 2 學期出國暨赴大陸地區交換學生校內甄試簡章（保證金退費與返國義務）",
        minimum=1000,
        count_fields=_RETURN_REPORT_FIELDS,
        count_note="學校規定的是整份交換研修心得報告（約 1,000 字）；這裡只合計下方各欄。",
    ),
    ("nkust", "study-plan"): _rules(
        (
            "須繳交中文與英文（或研修國語言）自傳及讀書計畫各乙份（約 1,000 字），具體說明申請動機、第一志願姊妹校專業領域契合度、擬修習之課程清單與返國後學習銜接。",
            "依高科大甄選比序規定，第一志願專業領域契合度佔總分 50%（無外語要求之大陸姊妹校佔 60%），請務必詳述個人主修背景與目標姊妹校系所課程之關聯。",
        ),
        evidence="國立高雄科技大學 115 學年度選送學生赴境外大學研修甄選簡章（報名應繳文件與甄選比序規定）",
        minimum=1000,
        count_fields=_STUDY_PLAN_FIELDS,
        count_note="建議中英文自傳及讀書計畫合計達 1,000 字以上；這裡合計下方各欄字數供參考。",
    ),
    ("nkust", "return-report"): _rules(
        (
            "返國後 1 個月內，須向國際事務處國際關係組繳交約 1,500–2,000 字之赴境外大學研修心得報告（含修課、住宿、生活適應與文化交流照片）並完成教育部學海計畫或校內獎助學金線上報告上傳。",
            "領取教育部學海飛颺／惜珠或高科大高教深耕境外研修獎助學金者，須同時檢附電子機票、登機證正本、護照出入境章影本及姊妹校正式成績單辦理核銷結案。",
        ),
        evidence="國立高雄科技大學選送學生出國研修辦法與獎助學生赴境外大學校院研修要點（返國核銷與義務）",
        minimum=1500,
        count_fields=_RETURN_REPORT_FIELDS,
        count_note="學校規定的是整份境外大學研修心得報告（建議 1,500 字以上）；這裡只合計下方各欄。",
    ),
    ("yuntech", "study-plan"): _rules(
        (
            "須繳交中文與英文自傳及出國讀書計畫各乙份（約 1,000 字），具體說明申請動機、擬修讀之專業課程清單、語言學習目標與返國後學分抵免及職涯發展規劃。",
            "若同時申請《王秋雄榮譽博士補助德日美交流或進修獎助金》，讀書計畫中須明確規劃大學部每學期至少修習 3 門或 6–9 學分（18 ECTS）且成績達 B 以上、研究所每學期至少修習 2 門或 4–8 學分（12 ECTS）及格。",
        ),
        evidence="國立雲林科技大學國際交換學生實施要點、非大陸地區交換學生評分標準表與王秋雄榮譽博士獎助金實施要點",
        minimum=1000,
        count_fields=_STUDY_PLAN_FIELDS,
        count_note="建議中英文自傳及出國讀書計畫合計達 1,000 字以上；這裡合計下方各欄字數供參考。",
    ),
    ("yuntech", "return-report"): _rules(
        (
            "交換期滿返國後，須向國際事務處繳交出國交換學生心得報告（約 1,500–2,000 字，含修課、住宿、生活開銷與文化交流照片）及問卷，以辦理 NT$3,000 保證金無息退還與獎助學金尾款核銷。",
            "領取《王秋雄榮譽博士德日美獎助金》、《教育部學海飛颺／惜珠》或《雲科大出國交流補助》者，須同時檢附姊妹校正式成績單、護照出入境章影本、登機證存根及電子機票收據。",
        ),
        evidence="國立雲林科技大學國際交換學生實施要點與學生出國交流或進修補助要點（返國義務與保證金退還規定）",
        minimum=1500,
        count_fields=_RETURN_REPORT_FIELDS,
        count_note="學校規定的是整份出國交換研修心得報告（建議 1,500 字以上）；這裡只合計下方各欄。",
    ),
    ("ntou", "study-plan"): _rules(
        (
            "海大國際事務處規定《中文自傳》與《外國留學研修計畫書》各約 1,000–1,500 字，須詳述個人學習背景、赴外動機、擬於志願姊妹校修習之專業課程（每學期至少應修習相當於海大 6 學分以上課程或進行論文研究）與返國學分採認規劃。",
            "欲申請教育部《學海飛颺》或《海大校內赴姊妹校交換獎補助》者，報名時必須一併填繳《經費分析表》（附件五），未繳交者視同放棄申請校內一切獎學金；全套文件須以 A4 單面列印（不裝訂，置於透明 L 型資料夾）並先轉為單一 PDF 寄至 `marberthsu@email.ntou.edu.tw`。",
        ),
        evidence="國立臺灣海洋大學 2027 年春/秋季赴姊妹校交換生計畫甄選簡章、自傳範例、外國留學研修計畫書範例與經費分析表範例",
        minimum=1000,
        maximum=3000,
        count_fields=_STUDY_PLAN_FIELDS,
        count_note="海大規定自傳與外國留學研修計畫書各約 1,000–1,500 字；這裡合計下方各欄字數供參考。",
    ),
    ("ntou", "return-report"): _rules(
        (
            "交換期滿返國後 1 個月內，須依《返國核銷檢核表》向國際事務處繳交 1,500–2,000 字《赴外研修心得報告》（含至少 4 張在國外研修與生活照片）及完成線上電子問卷。",
            "領取《教育部學海飛颺／惜珠》或《海大校內赴姊妹校交換獎補助》者，須同時檢附登機證正本、電子機票收據、護照出入境章影本及姊妹校正式成績單辦理核銷；逾期未完成核銷者將追回全額獎補助款。",
        ),
        evidence="國立臺灣海洋大學學生赴國外研修施行細則、學海系列計畫補助施行細則與返國核銷檢核表",
        minimum=1500,
        maximum=2000,
        count_fields=_RETURN_REPORT_FIELDS,
        count_note="學校規定的是整份赴外研修心得報告（1,500–2,000 字，含照片 4 張以上）；這裡只合計下方各欄。",
    ),
}

SCHOOL_WRITING_RULE_SOURCES: dict[str, tuple[str, str]] = {
    "cgu": ("https://www.cgu.edu.tw/oia-ch/Contents?nodeId=15656", "2026-10-03"),
    "ntpu": ("https://cms-carrier.ntpu.edu.tw/uploads/116_16e535159d.pdf", "2026-10-03"),
    "ntu": ("https://studyabroad.ntu.edu.tw/wp-content/uploads/2026/07/116-1-Selection-Guidelines_CH.pdf", "2026-10-07"),
    "ccu": ("https://oia.ccu.edu.tw/var/file/8/1008/attach/78/pta_54384_797227_45763.pdf", "2026-10-08"),
    "ncu": ("https://oia.ncu.edu.tw/static/file/26/1026/img/277/116exchangenotice.pdf", "2026-10-15"),
    "tku": ("https://oieie.tku.edu.tw/oieie/?page_id=55", "2026-10-08"),
    "fju": ("https://iscoie.fju.edu.tw/newsDetail.jsp?newsID=1062&newsClassID=14", "2026-10-20"),
    "scu": ("https://icae.scu.edu.tw/zh-hant/outbound-exchange/itnl/AYapply", "2026-10-16"),
    "ntnu": ("https://bds.oia.ntnu.edu.tw/bds/web/outgoing-apply", "2026-10-16"),
    "cycu": ("https://oia.cycu.edu.tw/?p=6338", "2026-10-16"),
    "ntust": ("https://www.oia.ntust.edu.tw/var/file/60/1060/img/2204/20260317.pdf", "2026-10-16"),
    "yzu": ("https://gao.yzu.edu.tw/index.php/tw/2016-03-04-08-13-53/2016-03-07-08-52-41", "2026-10-17"),
    "fcu": ("https://oia.fcu.edu.tw/sap/introduction/", "2026-10-17"),
    "nsysu": ("https://oia.nsysu.edu.tw/p/412-1308-20730.php?Lang=zh-tw", "2026-10-18"),
    "nchu": ("https://oia.nchu.edu.tw/images/File/02_Exchange_Program/5-1-1/Exchange_Program_Guidelines_for_Fall_Semester_2027_TW.pdf", "2026-10-18"),
    "ntut": ("https://oia.ntut.edu.tw/p/412-1032-9238.php?Lang=zh-tw", "2026-10-18"),
    "nccu": ("https://outbound.nccu.edu.tw/media/files/f353edca-d805-48ac-a6c9-9f66cf925c9e", "2026-10-18"),
    "ncku": ("https://oia.ncku.edu.tw/var/file/32/1032/img/107138261.pdf", "2026-10-18"),
    "nycu": ("https://oia.nycu.edu.tw/oia/ch/app/data/doc?module=nycu0006&detailNo=1442785684455690240&type=s", "2026-10-19"),
    "nthu": ("https://oga.site.nthu.edu.tw/var/file/524/1524/img/2027F2028Sapplicationguideline-CH.pdf", "2026-10-19"),
    "pccu": ("https://oima.pccu.edu.tw/Upload/202607/learning_2026071112283509.pdf", "2026-10-19"),
    "wzu": ("https://d020.wzu.edu.tw/article/529354", "2026-10-19"),
    "nkust": ("https://oia.nkust.edu.tw/p/412-1030-5591.php?Lang=zh-tw", "2026-10-20"),
    "yuntech": ("https://tdx.yuntech.edu.tw/images/International_Exchange_Students/Outgoing/Non_mainland_China_area/%E5%9C%8B%E7%AB%8B%E9%9B%B2%E6%9E%97%E7%A7%91%E6%8A%80%E5%A4%A7%E5%AD%B8%E5%9C%8B%E9%9A%9B%E4%BA%A4%E6%8F%9B%E5%AD%B8%E7%94%9F%E5%AF%A6%E6%96%BD%E8%A6%81%E9%BB%9E20250422.pdf", "2026-10-20"),
    "ntou": ("https://oia.ntou.edu.tw/var/file/22/1022/img/1029/779655790.pdf", "2026-10-20"),
}

for (_uni_id, _tpl_id), _rule_entry in list(WRITING_RULES.items()):
    _src_meta = SCHOOL_WRITING_RULE_SOURCES.get(_uni_id)
    if _src_meta and (_rule_entry.source_url is None or _rule_entry.last_checked_at is None):
        WRITING_RULES[(_uni_id, _tpl_id)] = _rule_entry.model_copy(
            update={
                "source_url": _rule_entry.source_url or _src_meta[0],
                "last_checked_at": _rule_entry.last_checked_at or _src_meta[1],
            }
        )


def guidance_for_field(
    template_id: str,
    field: ApplicationFormField,
) -> ApplicationFieldGuidance | None:
    if field.field_type in (ApplicationFieldType.FILES, ApplicationFieldType.CHECKBOX):
        return None
    specific = TEMPLATE_FIELD_GUIDANCE.get((template_id, field.id))
    if specific is not None:
        return specific
    # Short-term course forms reuse generic ids with different meanings; only
    # their explicit entries above apply.
    if template_id.startswith("short-term-"):
        return None
    return FIELD_GUIDANCE.get(field.id)


def apply_writing_guidance(
    university_id: str,
    template: ApplicationDocumentTemplate,
) -> ApplicationDocumentTemplate:
    """Attach field guidance and school writing rules; idempotent and in place."""

    for field in template.fields:
        if field.guidance is None:
            field.guidance = guidance_for_field(template.id, field)
    if template.writing_rules is None:
        template.writing_rules = WRITING_RULES.get((university_id, template.id))
        if template.writing_rules is None and template.id in _NARRATIVE_TEMPLATES:
            src_meta = SCHOOL_WRITING_RULE_SOURCES.get(university_id)
            checked_date = (
                src_meta[1]
                if src_meta
                else template.source_checked_at.strftime("%Y-%m-%d")
            )
            source_url = (
                src_meta[0]
                if src_meta
                else (template.source_url if template.source_url.startswith("https://") else None)
            )
            template.writing_rules = _NOT_COLLECTED.model_copy(
                update={
                    "source_url": source_url,
                    "last_checked_at": checked_date,
                }
            )
    return template

