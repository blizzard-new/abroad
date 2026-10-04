from __future__ import annotations

import re
from collections.abc import Iterable


URL_PATTERN = re.compile(r"https?://[^\s）)]+", re.IGNORECASE)
ENGLISH_WORD_PATTERN = re.compile(r"[A-Za-z][A-Za-z'-]*")


DEADLINE_OVERRIDES = {
    "Semester 1 (February - June): 30 September of previous year Semester 2 (July - November): 30 March of current year": (
        "第一學期（2 月至 6 月）：前一年 9 月 30 日；"
        "第二學期（7 月至 11 月）：當年 3 月 30 日"
    ),
    "winter semester /whole academic year: 05/31 summer semester: 11/15": (
        "冬季學期／全學年：5 月 31 日；夏季學期：11 月 15 日"
    ),
    "First Semester and Full Year: 30th June Second Semester: 30th November": (
        "第一學期／全學年：6 月 30 日；第二學期：11 月 30 日"
    ),
    "Summer semester(April-September): mid-December to 15 January Winter semester(October-March): mid-May to 15 July": (
        "夏季學期（4 月至 9 月）：12 月中旬至 1 月 15 日；"
        "冬季學期（10 月至 3 月）：5 月中旬至 7 月 15 日"
    ),
}


PHRASE_TRANSLATIONS: tuple[tuple[str, str], ...] = (
    ("or at least 2 undergraduate Korean language classes completed", "或已修畢至少 2 門大學部韓語課程"),
    ("Restricted to third-year and above students majoring in Information, Science, or Engineering-related fields.", "限資訊、科學或工程相關科系大三以上學生。"),
    ("For Undergraduate Students Only", "限大學部學生"),
    ("for master's course and doctoral course", "碩士班與博士班"),
    ("for undergraduate", "大學部"),
    ("Japanese Language and Culture", "日本語言與文化"),
    ("Global Business program", "全球商務學程"),
    ("Ceramics", "陶藝"),
    ("undergraduate Korean language classes completed", "門大學部韓語課程修畢"),
    ("minimum overall band score of", "總分至少"),
    ("minimum score of", "至少"),
    ("no sub-score bellow", "各單項不得低於"),
    ("no sub-score below", "各單項不得低於"),
    ("Option A", "方案 A"),
    ("Option B", "方案 B"),
    (
        "The university does not offer modules from the Faculty of Dentistry, Medicine and Pharmacy for mobility program.",
        "交換計畫不開放牙醫、醫學與藥學院課程。",
    ),
    (
        "Undergraduate students are not eligible to take postgraduate modules, but Postgraduate students are allowed to take both undergraduate and postgraduate modules.",
        "大學部學生不得選修研究所課程；研究生可選修大學部及研究所課程。",
    ),
    (
        "Business and Computer Engineering majors are mainly taught in English. For students who major in others could be difficult to take their major classes.",
        "商學與電腦工程主修多數課程採英語授課；其他主修學生可能較難選到本系專業課程。",
    ),
    (
        "Classes are taught in Spanish. No certificate of level is required, although a B1 level is recommended.",
        "課程以西班牙文授課；不強制繳交語言證明，但建議具備 CEFR B1 程度。",
    ),
    (
        "The undergraduate student must have completed at least one year full-time study at CGU.",
        "大學部學生須已在長庚大學完成至少 1 年全時修業。",
    ),
    (
        "The graduate student must have completed at least half year full-time study at the Home University.",
        "研究生須已在原就讀學校完成至少半年全時修業。",
    ),
    (
        "No English language proficiency requirement.",
        "不要求英語能力證明。",
    ),
    (
        "Students with English language coursework required must enroll in either 3 or 6 credits of English for Academic Purposes (EAP) as determined by UWM.",
        "如校方判定需加修英語課程，學生須依 UWM 安排修讀 3 或 6 學分的學術英語（EAP）。",
    ),
    (
        "TOEFL iBT 79, IELTS 6.5 or Duolingo 120 or with English language coursework required",
        "英語門檻擇一：TOEFL iBT 79、IELTS 6.5、Duolingo 120，或由校方判定須加修英語課程",
    ),
    (
        "TOEFL iBT 65, IELTS 5.0 or Duolingo 95",
        "英語成績達 TOEFL iBT 65、IELTS 5.0 或 Duolingo 95",
    ),
    (
        "over TOEFL IBT 70 or IELTS 5.5 or TOEIC 700 score is required",
        "TOEFL iBT 70、IELTS 5.5 或 TOEIC 700 以上，三者擇一",
    ),
    (
        "B1 in French or English",
        "法文或英文須達 CEFR B1",
    ),
    (
        "3.0 out of 4.0 or 2.3 out of 3.0 (for undergraduate level) - 3.25 out of 4.0 (for graduate level)",
        "大學部 GPA 須達 3.0／4.0 或 2.3／3.0；研究所 GPA 須達 3.25／4.0",
    ),
    (
        "GPA of at least 3.0/4.0 (or equivalent), or rank among the top 30% of their school",
        "GPA 至少 3.0／4.0（或同等成績），或在原就讀學校排名前 30%。",
    ),
    (
        "Have sufficient Japanese language proficiency to take courses offered in Japanese, equivalent to passing Japanese-Language Proficiency Test (JLPT) N2 or higher.",
        "修讀日語授課課程者，日語能力須達 JLPT N2 以上或同等程度。",
    ),
    (
        "Have sufficient English proficiency to take courses offered in English, equivalent to CEFR B2, TOEFL iBT 72 or IELTS 5.5 or higher",
        "修讀英語授課課程者，英語能力須達 CEFR B2、TOEFL iBT 72 或 IELTS 5.5 以上",
    ),
    (
        "with English language proficiency for B2, TOEFL iBT 72, IELTS 5.0, TOEIC 750 or equivalent to undertake undergraduate programs",
        "申請大學部課程：英語須達 CEFR B2、TOEFL iBT 72、IELTS 5.0、TOEIC 750 或同等程度。",
    ),
    (
        "B2, TOEFL iBT 83, IELTS 5.5, TOEIC 790 or equivalent to undertake graduate programs",
        "申請研究所課程：英語須達 CEFR B2、TOEFL iBT 83、IELTS 5.5、TOEIC 790 或同等程度。",
    ),
    (
        "Scanned application form filled out and signed by applicant and Home Institution",
        "申請人與原就讀學校填寫並簽署的申請表掃描檔；",
    ),
    ("Official grade transcripts for all university studies", "所有大學就讀期間的正式成績單；"),
    (
        "(including grade transcript and diploma from bachelor degree studies), English version",
        "包含學士階段成績單與學位證書，須提供英文版；",
    ),
    (
        "A list of the courses you are currently taking (you can write it yourself)",
        "目前修讀課程清單，可自行製作；",
    ),
    ("The personal identification page of your passport", "護照個人資料頁；"),
    ("Additional form for exchange students", "交換學生附加表格；"),
    ("Official academic transcripts indicating grades", "載有各科成績的正式歷年成績單；"),
    ("Official Academic transcript", "正式歷年成績單；"),
    ("Official University Transcript", "正式大學成績單；"),
    ("Official transcripts in English", "英文版正式成績單；"),
    ("Documentation of English proficiency", "英語能力證明；"),
    ("Transcript of Records", "歷年成績單；"),
    ("Evidence of previous courses, grades, and duration of the study", "修課科目、成績與修業期間證明；"),
    ("Enrollment certificate of home university", "原就讀學校在學證明；"),
    ("Certificate of enrollment from the home university", "原就讀學校在學證明；"),
    ("Letter from your home University confirming English language ability", "原就讀學校開立的英語能力證明；"),
    ("Proof of English proficiency", "英語能力證明；"),
    ("Evidence of English language proficiency", "英語能力證明；"),
    ("Valid proof of their English level for non-native speakers", "非英語母語者的有效英語能力證明；"),
    ("A letter of motivation in French (or in English)", "法文或英文動機信；"),
    ("A Curriculum vitae in French (or in English)", "法文或英文履歷；"),
    ("A motivation letter (written in English - max. 400 words)", "英文動機信，最多 400 字；"),
    ("Letter of intent/Statement of purpose/ Motivation letter", "意向書、讀書計畫或動機信；"),
    ("Statement of purpose (0.5 - 1 page)", "0.5 至 1 頁讀書計畫；"),
    ("Motivation letter", "動機信；"),
    ("Letter of intent", "意向書；"),
    ("Statement of purpose", "讀書計畫；"),
    ("Curriculum vitae", "履歷；"),
    ("CV (resume)", "履歷；"),
    ("A short CV", "簡短履歷；"),
    ("Copy of passport or ID card", "護照或身分證件影本；"),
    ("Copy of passport (first page)", "護照首頁影本；"),
    ("Scanned copy of a valid passport", "有效護照掃描檔；"),
    ("Birth certificate translated into French or English", "法文或英文版出生證明；"),
    ("Three Identical Photos 3*4 cm", "3 張 3×4 公分相同證件照；"),
    (
        "(formal photo: polite dress, light background, and neutral facial expression)",
        "照片須穿著整齊、使用淺色背景並保持自然表情；",
    ),
    (
        "Medical Certificate issued within the last 6 months up to the date of application submission",
        "申請日前 6 個月內開立的健康證明；",
    ),
    ("Letter(s) of Recommendation (1 - 3 referees)", "1 至 3 封推薦信；"),
    ("Application Check list", "申請文件檢核表；"),
    ("Photo JPG", "JPG 格式證件照；"),
    ("Name of high school and year graduated", "高中校名及畢業年份；"),
    ("Your last transcripts of records", "最近一期歷年成績單；"),
    ("Application Form (Form 1)", "申請表（表格 1）；"),
    ("Form 1", "表格 1"),
    ("Form 2", "表格 2"),
    ("Form 3", "表格 3"),
    ("Valid at least 6 months after the end of the semester abroad", "護照效期須超過交換學期結束後至少 6 個月；"),
    ("Copy of ID or passport (plus digital passport photo)", "身分證或護照影本，另附電子證件照；"),
    ("Passport must be valid for at least the duration of program +3 months", "護照效期須涵蓋整個計畫期間，並多保留至少 3 個月；"),
    ("(waived for native speakers of English).", "英語母語者免附；"),
    ("waived for native speakers of English", "英語母語者免附"),
    (
        "If students are enrolled in non-English speaking degree program with partner university, they are requested to submit an English language proficiency test: TOEFL 72 I.B.T. or IELTS 6.0 and above",
        "若原學位課程並非英語授課，須繳交英語證明：TOEFL iBT 72 或 IELTS 6.0 以上；",
    ),
    ("only passport for Non-European students", "非歐洲學生僅可使用護照；"),
    (
        "students will not need to upload this document on our application. However, we highly recommend students bring this document with them as it will be needed for certain French administrative procedures",
        "線上申請時不必上傳出生證明，但建議隨身攜帶，以供法國部分行政程序使用；",
    ),
    ("Official ID photograph", "正式證件照；"),
    (
        "and have studied Japanese language for at least one (1) year in total",
        "且累計學習日語至少 1 年",
    ),
    (
        "and have studied Japanese language for at least one（1）year in total",
        "且累計學習日語至少 1 年",
    ),
    ("course selection form", "選課預審表"),
    ("Junior Year Program in English", "英語大三交換計畫"),
    ("Cooperative Laboratory Study Program", "合作實驗室研究計畫"),
    ("No students will be guaranteed student housing", "校方不保證提供學生宿舍；"),
    (
        "All student exchange stays at the Faculty of Medicine and Health that involves training practice/placements in the health services during the spring semester 2022 are cancelled.",
        "醫學與健康學院於 2022 春季取消涉及醫療機構實習或實務訓練的交換安排；",
    ),
    ("Practice/placements", "實務訓練或實習；"),
    ("Internships", "實習；"),
    ("Field studies", "田野實習；"),
    ("Clinical practice", "臨床實習；"),
    ("Any equivalent schemes for student exchange at the MH faculty", "醫學與健康學院其他同類交換實習；"),
    ("This includes:", "包含以下類型："),
    ("Register new international applicant", "註冊新的國際申請者帳號"),
    ("Login International Applicant", "國際申請者登入"),
    ("application portal", "線上申請系統"),
    ("Academic Calendar", "校曆"),
    ("Specific requirements for each master's programme", "各碩士學程的個別入學條件"),
    ("American Semester Abroad Program", "美國海外學期計畫"),
    ("Master of Embedded and Cyber-Physical Systems", "嵌入式與網實整合系統碩士"),
    ("degree conferred", "正式授予學位"),
    ("Year 1 estimated cost", "第 1 年預估費用"),
    ("Application and tuition fees for master's studies", "碩士申請費與學費"),
    ("Tuition & Fees", "學費與費用"),
    ("CSOM/CSE surcharge", "CSOM／CSE 附加費"),
    ("CSOM／CSE surcharge", "CSOM／CSE 附加費"),
    ("program fee", "計畫費"),
    ("Physical Therapy", "物理治療"),
    ("Medical campus", "醫學校區"),
    ("Fact Sheet", "交換計畫說明"),
    ("European level", "CEFR 歐洲語言分級"),
    ("2nd Level", "N2"),
    ("Scores for TOEFL or IELTS:", "TOEFL 或 IELTS 成績門檻請見："),
    ("with no subscorebelow 5.5", "各單項不得低於 5.5"),
    ("with English language proficiency for B2", "英語能力須達 CEFR B2"),
    (
        "Søknadsweb選擇Norwegian University of Science and Technology",
        "進入 Søknadsweb 後選擇「挪威科技大學」",
    ),
    ("email", "電子郵件"),
    ("Semester", "學期"),
    ("Korean Track", "韓語授課組"),
    ("EnglishTrack", "英語授課組"),
    ("English Track", "英語授課組"),
    ("Entry Requirements", "入學門檻"),
    ("Study Content", "修課內容"),
    ("1 semester or 1 academic year", "1 學期或 1 學年"),
    ("1 semester or 1 year", "1 學期或 1 學年"),
    ("one semester or one academic year", "1 學期或 1 學年"),
    ("one semester", "1 學期"),
    ("1 semester", "1 學期"),
    ("one academic year", "1 學年"),
    ("1 academic year", "1 學年"),
    ("of previous year", "（前一年）"),
    ("of current year", "（當年）"),
    ("undergraduate level", "大學部"),
    ("graduate level", "研究所"),
    ("postgraduate modules", "研究所課程"),
    ("undergraduate modules", "大學部課程"),
    ("home University", "原就讀學校"),
    ("Home Institution", "原就讀學校"),
    ("English language coursework required", "須加修英語課程"),
    ("English for Academic Purposes", "學術英語"),
    ("Japanese-Language Proficiency Test", "日本語能力試驗"),
    ("English language proficiency", "英語能力"),
    ("French or English", "法文或英文"),
    ("taught in English", "採英語授課"),
    ("taught in Spanish", "採西班牙文授課"),
    ("or equivalent", "或同等成績"),
    ("or higher", "以上"),
    ("score is required", "為必要門檻"),
    ("is required", "為必要條件"),
    ("is recommended", "為建議條件"),
    ("recommended", "建議"),
    ("overall", "總分"),
    ("with no individual band less than", "各單項不得低於"),
    ("with no subscore below", "各單項不得低於"),
    ("at least", "至少"),
    ("full-time study", "全時修業"),
    ("previous year", "前一年"),
    ("current year", "當年"),
    ("whole academic year", "全學年"),
    ("Full Year", "全學年"),
    ("First Semester", "第一學期"),
    ("Second Semester", "第二學期"),
    ("Winter Semester", "冬季學期"),
    ("winter semester", "冬季學期"),
    ("Summer Semster", "夏季學期"),
    ("Summer semester", "夏季學期"),
    ("Semester 1", "第一學期"),
    ("Semester 2", "第二學期"),
)


MONTHS = {
    "January": "1 月",
    "February": "2 月",
    "March": "3 月",
    "April": "4 月",
    "May": "5 月",
    "June": "6 月",
    "July": "7 月",
    "August": "8 月",
    "September": "9 月",
    "October": "10 月",
    "November": "11 月",
    "December": "12 月",
    "Jan.": "1 月",
    "Sept.": "9 月",
}


def build_partner_student_summary(
    *,
    study_period: str | None,
    application_deadline: str | None,
    eligibility: str | None,
    application_info: str | None,
    tuition_info: str | None,
) -> dict[str, object]:
    source_text = " ".join(
        value or ""
        for value in [study_period, application_deadline, eligibility, application_info, tuition_info]
    )
    return {
        "study_period": translate_partner_text(study_period or "") or None,
        "application_deadline": translate_deadline(application_deadline or "") or None,
        "eligibility_points": localize_points(eligibility or ""),
        "application_steps": localize_points(application_info or ""),
        "tuition_points": localize_points(tuition_info or ""),
        "translated_from_english": contains_english_prose(source_text),
    }


def translate_deadline(text: str) -> str:
    normalized = _normalize_dashes(_normalize_space(text))
    if not normalized:
        return ""
    override = DEADLINE_OVERRIDES.get(normalized)
    if override:
        return override
    return translate_partner_text(normalized)


def localize_points(text: str) -> list[str]:
    if not text.strip():
        return []
    lincoln_points = _translate_lincoln_options(text)
    if lincoln_points:
        return lincoln_points
    working = text.replace("；", "\n").replace("•", "\n")
    working = re.sub(r"\((\d{1,2})\)\s*", r"\n\1. ", working)
    working = re.sub(
        r"(?<!\d)(?<![A-Za-z])(\d{1,2})[.、](?!\d)\s*",
        r"\n\1. ",
        working,
    )
    source_parts = [part.strip() for part in working.splitlines() if part.strip()]
    points: list[str] = []
    for source in source_parts:
        source = re.sub(r"^\d{1,2}[.]\s*", "", source).strip()
        translated = translate_partner_text(source)
        for point in re.split(r"\s*[；]\s*", translated):
            sentences = re.split(r"(?<=。)\s+", point)
            for sentence in sentences:
                cleaned = _clean_point(sentence)
                if cleaned and cleaned not in points:
                    points.append(cleaned)
    return points


def _translate_lincoln_options(text: str) -> list[str]:
    if not all(marker.lower() in text.lower() for marker in ("Option A", "Option B", "IELTS")):
        return []
    matches = re.findall(
        r"Option\s+([AB]).*?IELTS\s+(\d+(?:\.\d+)?)\s+overall,?\s*"
        r"with no individual band less than\s+(\d+(?:\.\d+)?).*?"
        r"Study Content:\s*(\d+)\s+or\s+(\d+)(?:\s+x)?\s*"
        r"(?:courses\s+in\s+)?(?:undergraduate\s+level\s*)?"
        r"(?:\((\d+)\s+level\s+recommended\)|(\d+)\s+level\s+courses)?",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if len(matches) != 2:
        return []

    points: list[str] = []
    if "符合長庚大學" in text:
        points.append("須先符合長庚大學「領航者補助作業要點」及校內甄選規定。")
    for option, overall, minimum, course_min, course_max, recommended, fixed_level in matches:
        points.append(
            f"方案 {option.upper()} 語言門檻：IELTS 總分 {overall}，"
            f"各單項不得低於 {minimum}（或同等英語成績）。"
        )
        if fixed_level:
            course_text = f"選修 {course_min} 至 {course_max} 門 {fixed_level} 級課程。"
        elif recommended:
            course_text = (
                f"選修 {course_min} 至 {course_max} 門大學部課程，"
                f"建議以 {recommended} 級課程為主。"
            )
        else:
            course_text = f"選修 {course_min} 至 {course_max} 門課程。"
        points.append(f"方案 {option.upper()} 修課要求：{course_text}")
    return points


def translate_partner_text(text: str) -> str:
    value = _normalize_dashes(_normalize_space(text))
    if not value:
        return ""
    value, urls = _protect_urls(value)
    for source, target in PHRASE_TRANSLATIONS:
        pattern = re.escape(source)
        if source[0].isalnum():
            pattern = rf"(?<![A-Za-z0-9]){pattern}"
        if source[-1].isalnum():
            pattern = rf"{pattern}(?![A-Za-z0-9])"
        value = re.sub(pattern, target, value, flags=re.IGNORECASE)

    for month, translated in MONTHS.items():
        # "may be requested" is a possibility, not a reference to May.
        pattern = (r"(?:(?<=\d )May\b|(?<=mid-)May\b|\bMay(?=\s+\d))"
                   if month == "May" else rf"\b{re.escape(month)}\b")
        value = re.sub(pattern, translated, value, flags=re.IGNORECASE)

    value = re.sub(
        r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(1|2|3|4|5|6|7|8|9|10|11|12)\s+月\b",
        lambda match: f"{match.group(2)} 月 {int(match.group(1))} 日",
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(r"\bmid-(\d{1,2})\s+月\b", r"\1 月中旬", value, flags=re.IGNORECASE)
    value = re.sub(r"\b(\d+)\s+or\s+(\d+)\s+courses\b", r"\1 至 \2 門課程", value, flags=re.IGNORECASE)
    value = re.sub(r"\b(\d+)\s+or\s+(\d+)\s+x\s+(\d+)\s+level\b", r"\1 至 \2 門 \3 級課程", value, flags=re.IGNORECASE)
    value = re.sub(r"\b(\d+)\s+level\b", r"\1 級", value, flags=re.IGNORECASE)
    value = re.sub(r"\bBand\s+(\d+(?:\.\d+)?)\b", r"總分 \1", value, flags=re.IGNORECASE)
    value = re.sub(r"\bmax[.]?\s*(\d+)\s*words\b", r"最多 \1 字", value, flags=re.IGNORECASE)
    value = re.sub(r"\s+([，。；：）])", r"\1", value)
    value = re.sub(r"([（])\s+", r"\1", value)
    value = re.sub(r"。\s*[,，]+", "，", value)
    value = re.sub(r"\)\s*[.]", "）。", value)
    value = re.sub(r"[.。]{2,}", "。", value)
    value = re.sub(r"(?<!\d)[.](?!\d)", "。", value)
    value = re.sub(r"(?<!\d)(\d+)\s*(學期|學年)", r"\1 \2", value)
    value = re.sub(r"\s{2,}", " ", value).strip(" ;")
    value = re.sub(r"(限大學部(?:學生)?)\s*\(限大學部學生\)", r"\1", value)
    value = re.sub(r"限大學部\s*限大學部學生", "限大學部學生", value)
    return _restore_urls(value, urls)


def contains_english_prose(text: str) -> bool:
    without_urls = URL_PATTERN.sub(" ", text)
    tokens = [token.lower() for token in ENGLISH_WORD_PATTERN.findall(without_urls)]
    ignored = {
        "ielts",
        "toefl",
        "ibt",
        "itp",
        "toeic",
        "cefr",
        "jlpt",
        "topik",
        "gpa",
        "pte",
        "duolingo",
        "cambridge",
        "english",
        "test",
        "band",
        "score",
        "cv",
        "asap",
        "jype",
        "colabs",
        "eap",
        "ets",
        "ntnu",
        "uwm",
        "cgu",
    }
    prose = [token for token in tokens if token not in ignored and len(token) > 1]
    return len(prose) >= 4


def merge_student_summaries(summaries: Iterable[dict[str, object]]) -> dict[str, object]:
    rows = list(summaries)
    return {
        "study_period": _join_values(row.get("study_period") for row in rows),
        "application_deadline": _join_values(row.get("application_deadline") for row in rows),
        "eligibility_points": _join_points(row.get("eligibility_points") for row in rows),
        "application_steps": _join_points(row.get("application_steps") for row in rows),
        "tuition_points": _join_points(row.get("tuition_points") for row in rows),
        "translated_from_english": any(bool(row.get("translated_from_english")) for row in rows),
    }


def _join_values(values: Iterable[object]) -> str | None:
    unique = list(dict.fromkeys(str(value).strip() for value in values if value and str(value).strip()))
    return "；".join(unique) or None


def _join_points(groups: Iterable[object]) -> list[str]:
    points: list[str] = []
    for group in groups:
        if not isinstance(group, list):
            continue
        for point in group:
            value = str(point).strip()
            if value and value not in points:
                points.append(value)
    return points


def _protect_urls(text: str) -> tuple[str, list[str]]:
    urls: list[str] = []

    def replace(match: re.Match[str]) -> str:
        urls.append(match.group(0))
        return f"__URL_{len(urls) - 1}__"

    return URL_PATTERN.sub(replace, text), urls


def _restore_urls(text: str, urls: list[str]) -> str:
    for index, url in enumerate(urls):
        text = text.replace(f"__URL_{index}__", url)
    return text


def _normalize_dashes(text: str) -> str:
    return text.replace("–", "-").replace("—", "-").replace("−", "-")


def _normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _clean_point(text: str) -> str:
    value = re.sub(r"^[\-–—•]+\s*", "", text).strip(" 。;")
    value = re.sub(r"^\(\s*", "", value)
    value = value.replace("申請的語文條件:", "語言條件如下：")
    value = re.sub(r"\s{2,}", " ", value)
    if not value or not re.search(r"[A-Za-z0-9\u3400-\u9fff]", value):
        return ""
    if value[-1] not in "。！？：" and not URL_PATTERN.fullmatch(value):
        value += "。"
    return value
