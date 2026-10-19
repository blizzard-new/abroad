from __future__ import annotations

import re

from .university_registry import NYCU, resolve_university

NYCU_OUTBOUND_URL = "https://oia.nycu.edu.tw/oia/ch/app/artwebsite/view?module=artwebsite&id=1170&serno=f2dc9dee-6110-4c93-a952-2eeef32fd49c"
NYCU_PORTAL_URL = "https://oia-sys.nycu.edu.tw/outgoing"
NYCU_QUOTA_SHEET_URL = "https://docs.google.com/spreadsheets/d/1MjFpOfI77e4-yQWc3dHuukoR9MJB6ZndldtSFfXiyj4/edit?gid=114872685"
NYCU_CONTRACTS_SHEET_URL = "https://docs.google.com/spreadsheets/d/1XGeMX1F-niYApCrtge7n5f_YfsLZ1uZrp3ckdp-35UQ/edit?usp=sharing"
NYCU_DUAL_DEGREE_SHEET_URL = "https://docs.google.com/spreadsheets/d/10zt_cwrlv7HvZ6evw5NkIhS1tHhMjaxaUSB896nJBJ0/edit?usp=sharing"
NYCU_115_2_GUIDELINES_PDF_URL = "https://oia.nycu.edu.tw/oia/ch/app/data/doc?module=nycu0006&detailNo=1501852894511501312&type=s"
NYCU_115_1_GUIDELINES_PDF_URL = "https://oia.nycu.edu.tw/oia/ch/app/data/doc?module=nycu0006&detailNo=1442785684455690240&type=s"
NYCU_REGULATIONS_PDF_URL = "https://oia.nycu.edu.tw/oia/ch/app/data/doc?module=nycu0014&detailNo=1191618147807924224&type=s"
NYCU_SCHOLARSHIP_URL = "https://oia.nycu.edu.tw/oia/ch/app/artwebsite/view?module=artwebsite&id=1175&serno=0f51332c-414b-45c4-b08d-f5dc13fb6e77"
NYCU_EXPERIENCE_URL = "https://oia.nycu.edu.tw/oia/ch/app/data/list?module=nycu0008&id=307"
NYCU_UST_NOTICE_PDF_URL = "https://oia.nycu.edu.tw/oia/ch/app/data/doc?module=nycu0006&detailNo=1552119722735046656&type=s"

NYCU_ENGLISH_MINIMUMS: dict[str, tuple[str, float]] = {
    "toefl": ("TOEFL iBT", 79.0),
    "ielts": ("IELTS Academic", 6.0),
    "toeic": ("TOEIC 聽讀（另須含口說與寫作測驗）", 785.0),
}


def is_nycu(school_name: str | None) -> bool:
    school = resolve_university(school_name)
    if school is not None and school.id == NYCU.id:
        return True
    normalized = re.sub(r"\s+", " ", (school_name or "")).strip().lower()
    return normalized in {
        "國立陽明交通大學",
        "陽明交通大學",
        "陽明交大",
        "國立交通大學",
        "國立陽明大學",
        "nycu",
        "nctu",
        "ym",
        "yang ming chiao tung university",
        "national yang ming chiao tung university",
    }


def _is_graduate(degree_level: str | None) -> bool:
    text = (degree_level or "").strip()
    return any(token in text for token in ("碩", "博", "研究"))


def nycu_degree_check(
    degree_level: str | None, current_year: str | None = None
) -> tuple[str, str]:
    degree = (degree_level or "").strip()
    year = (current_year or "").strip()
    if not degree:
        return (
            "needs_confirmation",
            "尚未提供目前學制與年級；《國立陽明交通大學學生申請出國交換實施辦法》及出國交換計畫簡章規定：申請人須為本校正式學籍生，交換生不得為大學部一年級新生（大學部二年級以上、碩博班一年級以上可申請；國防部專案計畫「系統工程與科技學士學位學程」學生由國防部專案辦理，不適用校級交換辦法）。",
        )
    is_grad = _is_graduate(degree)
    if not is_grad and year in {"一年級", "大一", "1"}:
        return (
            "fail",
            f"已填報 {degree}（{year}）；依《國立陽明交通大學學生出國交換申請簽核表》及可交換學校名額表規定，交換生不得為大學部一年級新生（大學部學生須為二年級以上，碩博士班學生則自一年級起即可申請，碩博一新生未有本校成績者須上傳前一學位含畢業排名之成績單）。",
        )
    if "在職" in degree or "專班" in degree:
        return (
            "needs_confirmation",
            f"已填報 {degree}；陽明交大在職專班在學學生雖得依各姐妹校規定確認是否開放報名，惟依《國立陽明交通大學優秀學生出國交換獎學金辦法》（A類）規定，在職專班生及雙聯學位生不具校內出國交換獎學金申請資格。",
        )
    return (
        "pass",
        f"已填報學制為 {degree}{f'（{year}）' if year else ''}；符合國立陽明交通大學學生申請出國交換學制與年級資格（大學部二年級以上、碩博班一年級以上正式學籍生；各姐妹校系所限制以主修或雙主修為準，年級限制以出國交換時之年級為準）。",
    )


def nycu_academic_check(
    degree_level: str | None,
    academic_score: float | None,
    academic_gpa: float | None = None,
    class_rank_percent: float | None = None,
) -> tuple[str, str]:
    is_grad = _is_graduate(degree_level)
    details: list[str] = []
    score_ok = False
    gpa_ok = False
    rank_ok = False
    low_fail = False

    if academic_score is not None:
        details.append(f"平均成績 {academic_score:g} 分")
        if academic_score >= 70.0:
            score_ok = True
        elif academic_score < 60.0:
            low_fail = True
    if academic_gpa is not None:
        details.append(f"GPA {academic_gpa:g}")
        if academic_gpa >= 2.7:
            gpa_ok = True
        elif academic_gpa < 2.0:
            low_fail = True
    if class_rank_percent is not None:
        details.append(f"班/系排名前 {class_rank_percent:g}%")
        if class_rank_percent <= 50.0:
            rank_ok = True

    summary = "、".join(details)
    if (
        academic_score is None
        and academic_gpa is None
        and class_rank_percent is None
    ):
        return (
            "needs_confirmation",
            "尚未填寫學業平均成績、GPA 或班/系排名百分比；陽明交大校級出國交換書面審查總分須達 60 分以上（在校成績佔比：赴國外或港澳地區大學部 50%、研究所 30%；赴大陸地區大學部 60%、研究所 40%），多數歐美日韓姐妹校要求歷年 GPA 達 3.0 以上，且申請 A 類優秀學生出國交換獎學金須達大學部亞洲前 50%／非亞洲前 20% 或研究所 GPA 3.7 以上。",
        )

    if low_fail:
        return (
            "fail",
            f"已填報 {summary}；未達國立陽明交通大學出國交換書面審查及格基準（審查總分未達 60 分不予錄取）與姐妹校最低 GPA 門檻。",
        )

    if score_ok or gpa_ok or rank_ok or is_grad:
        sch_note = (
            "研究所歷年 GPA 達 3.7 以上可申請 A 類優秀學生出國交換獎學金"
            if is_grad
            else "大學部歷年班或系排名前 20%（赴非亞洲地區）或前 50%（赴亞洲地區）可申請 A 類優秀學生出國交換獎學金；平均成績 80 分（GPA 3.38）以上且修畢 3 門英語授課課程可申請 B 類獎學金"
        )
        return (
            "pass",
            f"已填報 {summary}；符合國立陽明交通大學校級出國交換申請基準（在校成績占書面審查 30%–60%，審查總分須達 60 分以上；請同步對照目標姐妹校於《出國交換名額表》所列之 GPA 門檻，且{sch_note}）。",
        )

    return (
        "needs_confirmation",
        f"已填報 {summary}；陽明交大雖未設全校統一最低 GPA 硬門檻（依各姐妹校規定為準，多數要求 GPA 3.0 以上），惟書面審查總分未達 60 分者不予錄取，建議優先選擇未設 GPA 限制之姐妹校。",
    )


def nycu_language_check(
    language_test: str | None,
    language_score: float | None,
    *,
    partner_country: str | None = None,
) -> tuple[str, str]:
    test = (language_test or "").strip().lower()
    if partner_country == "中國大陸" and (not test or language_score is None):
        return (
            "pass",
            "申請赴大陸地區交換者，陽明交大校內不強制要求檢附外語能力檢定證明（書面審查比重為：大學部在校成績 60%、自傳 15%、讀書計畫 20%、其他表現 5%；研究所在校成績 40%、自傳 25%、讀書計畫 30%、其他表現 5%）。",
        )
    if not test or language_score is None:
        return (
            "needs_confirmation",
            "尚未填寫外語檢定成績。《國立陽明交通大學學生申請出國交換計畫簡章》規定：申請赴國外或港澳地區交換者，不論該姐妹校是否訂有語言能力限制，皆須於申請截止日前提交有效語言能力成績證明（TOEFL iBT、IELTS Academic、全民英檢複試通過、包含口說與寫作測驗之 TOEIC，或交換校指定之日韓德法西語檢定）。",
        )
    if test in NYCU_ENGLISH_MINIMUMS:
        label, minimum = NYCU_ENGLISH_MINIMUMS[test]
        passed = language_score >= minimum
        toeic_note = (
            "（注意：陽明交大簡章明訂使用多益 TOEIC 申請出國交換或獎學金者，成績單必須同時包含「聽力、閱讀、口說與寫作」四項測驗；A 類與 B 類獎學金要求聽力 400、閱讀 385、口說 150、寫作 150 以上）"
            if test == "toeic"
            else "（A 類優秀學生出國交換獎學金門檻為 TOEFL iBT 83／IELTS 6.0；B 類獎學金門檻為 TOEFL iBT 87／IELTS 6.5）"
        )
        return (
            "pass" if passed else "needs_confirmation",
            f"{label} {language_score:g} {'符合多數英語授課姐妹校常見門檻' if passed else '已具備外語檢定證明（部分姐妹校未設最低分數門檻即可申請，惟多數歐美名校要求'} {minimum:g} 以上{'' if passed else '）'}{toeic_note}。請務必逐校核對《陽明交大出國交換名額表》各校語言限制欄位。",
        )
    if test == "jlpt":
        passed = 1.0 <= language_score <= 5.0
        return (
            "pass" if passed else "fail",
            f"JLPT N{int(language_score)} {'符合' if passed else '未達'}國立陽明交通大學赴日本交換日語檢定條件（日本姐妹校依校別要求 JLPT N1–N3 或英語檢定成績，請依出國交換名額表為準）。",
        )
    if test == "topik":
        passed = 1.0 <= language_score <= 6.0
        return (
            "pass" if passed else "fail",
            f"TOPIK {int(language_score)} 級 {'符合' if passed else '未達'}國立陽明交通大學赴韓國交換韓語檢定條件（韓國姐妹校多接受英語檢定或 TOPIK 2–4 級，請對照出國交換名額表）。",
        )
    return (
        "needs_confirmation",
        f"已填寫 {language_test} {language_score:g}；請對照國立陽明交通大學《學生申請出國交換名額表》（{NYCU_QUOTA_SHEET_URL}）各校指定語言能力限制。",
    )
