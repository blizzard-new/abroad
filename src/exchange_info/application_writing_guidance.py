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
            "讀書計畫（Study Plan）及自傳：A4 雙面列印，不超過 2 頁（4 面）。",
            "外語組以英文或交換國語言撰寫；日語組以日文或英文撰寫；中語組以中文撰寫。",
        ),
        evidence="輔仁大學：申請應備文件規範",
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
}


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
            template.writing_rules = _NOT_COLLECTED
    return template
