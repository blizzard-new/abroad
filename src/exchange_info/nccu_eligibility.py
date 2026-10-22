from __future__ import annotations

import re

from .university_registry import NCCU, resolve_university

NCCU_OUTBOUND_URL = "https://outbound.nccu.edu.tw/"
NCCU_GUIDELINES_PDF_URL = "https://outbound.nccu.edu.tw/media/files/f353edca-d805-48ac-a6c9-9f66cf925c9e"
NCCU_PARTNERS_URL = "https://outbound.nccu.edu.tw/student-outgoing-list"
NCCU_PARTNERS_XLSX_URL = "https://outbound.nccu.edu.tw/get_file/6909abcb86a87"
NCCU_MAINLAND_URL = "https://oic.nccu.edu.tw/Post/119"
NCCU_MAINLAND_PDF_URL = "https://oic.nccu.edu.tw/Home/Download?FileId=AC94A5C6-1ED6-421D-AD29-F673F2418670"
NCCU_EXPERIENCE_URL = "https://oic.nccu.edu.tw/Experience"
NCCU_SCHOLARSHIP_URL = "https://outbound.nccu.edu.tw/student-outgoing-scholarship"
NCCU_REGULATION_PDF_URL = "https://oic.nccu.edu.tw/File/Download/712"

# The scoring conversion table is not a universal host admission threshold.
NCCU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {}


def is_nccu(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == NCCU.id:
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "國立政治大學",
        "政治大學",
        "政大",
        "nccu",
        "national chengchi university",
    }


def _is_graduate(degree_level: str | None) -> bool:
    text = (degree_level or "").strip()
    return any(token in text for token in ("碩", "博", "研究"))


def nccu_degree_check(
    degree_level: str | None, current_year: str | None = None,
    *, partner_country: str | None = None,
) -> tuple[str, str]:
    degree, year = (degree_level or "").strip(), (current_year or "").strip()
    if not degree or not partner_country:
        return "needs_confirmation", "須確認學制、目前學期及國際／大陸交換計畫；兩項計畫的申請與出國學期規定不同。"
    if any(token in degree for token in ("在職", "專班")):
        return "needs_confirmation", "本輪簡章未列此類專班一律不得申請，請向國合處核對學籍及目標交換計畫；不據此自動排除。"
    if not any(token in degree for token in ("學士", "大學", "碩", "博", "研究")):
        return "needs_confirmation", "尚未確認是否屬政大學士、碩士或博士班正式學籍。"
    if not _is_graduate(degree) and any(token in year for token in ("大一上", "一年級上")):
        return "fail", "政大學士班須就讀第二學期起才能報名，第一學期新生尚不符合。"
    if not year or (not _is_graduate(degree) and year in {"大一", "一年級", "1"}):
        return "needs_confirmation", "學士班須第二學期起報名，國際組碩博士班第一學期起可報名；請確認目前學期。"
    if partner_country in {"中國大陸", "大陸地區"} and year in {"碩一", "碩一上", "博一", "博一上", "一年級", "1"}:
        return "needs_confirmation", "大陸交換簡章申請資格段列碩博一下學期起申請，所附通則另列研究所第一學期起；請向大陸事務組確認當期資格。"
    return "pass", "符合已提供的基本學制／年級範圍；國際組學士班第二學期、碩博士第一學期起可報名，交換時須維持原錄取學制及在學身分。國籍、轉學生及合作校限制仍須另核對。"


def nccu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
    *, partner_country: str | None = None,
) -> tuple[str, str]:
    if not degree_level or not partner_country:
        return "needs_confirmation", "須確認學制及國際／大陸交換計畫，不能套用統一平均分數或 GPA 門檻。"
    if partner_country in {"中國大陸", "大陸地區"}:
        return "needs_confirmation", "大陸組錄取門檻為口試35%、學業30%、書審35%的甄試總分達75；單憑學業平均、GPA或排名不能判定錄取門檻。"
    if _is_graduate(degree_level):
        if academic_score is None:
            return "needs_confirmation", "國際組研究生採在校期間累計平均；未達70分時該項為0且不予推薦。新生GPA須先依原分級及簡章附錄換算，不能以固定GPA或班排名替代。"
        if academic_score < 70:
            return "fail", "國際組研究所在校期間累計平均未達70分，依簡章該項得0分，不予推薦。"
        return "pass", "國際組研究所在校期間累計平均達70分；僅確認此項非零分門檻，其他甄試及合作校條件另核對。"
    if class_rank_percent is None or not 0 < class_rank_percent <= 100:
        return "needs_confirmation", "國際組學士班以歷年班排名百分比換算（101減班排百分比，占總分20%），平均分數或GPA不可替代排名證明。"
    return "pass", "國際組學士班依歷年班排名換算在校成績，未設共同70分或前50%門檻；語檢30%、在校成績20%、計畫與履歷20%、口試30%，各項不得缺考或為0分，合作校另有標準。"


def nccu_language_check(
    language_test: str | None,
    language_score: float | None,
    *, partner_country: str | None = None,
) -> tuple[str, str]:
    if partner_country in {"中國大陸", "大陸地區"}:
        return "pass", "大陸組簡章的語言證明列於非必要參考資料；此結論僅指校內繳件，仍須核對合作校修課要求。"
    test = (language_test or "").strip().lower()
    if test == "toeic":
        return "fail", "政大本期國際交換英語組僅接受TOEFL iBT（不接受MyBest拼分）與IELTS學術組，不受理TOEIC；報考其他語組須提供相應證明。"
    if not test or language_score is None:
        return "needs_confirmation", "須提供報考語組之語言證明，先登錄全人系統並將截圖與成績合併上傳；各合作校總分及單項門檻仍須逐校核對。"
    if test == "jlpt" and language_score not in {1, 2, 3}:
        return "fail", "本期日語甄試換算表列JLPT N1、N2、N3；未列N4、N5，不能視為可計分資格。"
    if test == "topik" and language_score not in {3, 4, 5, 6}:
        return "fail", "本期韓語甄試換算表列TOPIK 3至6級；其他級別不能依此表判定可計分。"
    return "needs_confirmation", f"已填{language_test} {language_score:g}；甄試換算表僅供計分，不能證明達目標合作校的語組、總分、小分及效期要求，須逐校確認。"
