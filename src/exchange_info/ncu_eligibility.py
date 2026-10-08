"""NCU's 116-1 home gate; reference partner text never becomes eligibility."""

from .university_registry import NCU, resolve_university

UNDERGRADUATE = (
    "大學部",
    "學士",
    "學士班",
    "大一",
    "大二",
    "大三",
    "大四",
    "大五",
    "大六",
)
GRADUATE = (
    "研究所",
    "研究生",
    "碩士",
    "碩士班",
    "博士",
    "博士班",
    "碩一",
    "碩二",
    "博一",
    "在職專班",
    "在職碩士班",
    "碩士在職專班",
)
SCORE_MINIMUMS = {**dict.fromkeys(UNDERGRADUATE, 60), **dict.fromkeys(GRADUATE, 70)}
EXCLUDED_YEARS = ["大五", "大六", "五年級", "六年級", "5", "6"]


def is_ncu(value: str | None) -> bool:
    school = resolve_university(value)
    return school is not None and school.id == NCU.id


def ncu_academic_check(
    degree: str | None, score: float | None, current_year: str | None = None
) -> tuple[str, str]:
    degree = (degree or "").strip()
    if degree in UNDERGRADUATE and (
        degree in EXCLUDED_YEARS or current_year in EXCLUDED_YEARS
    ):
        return "fail", "中央116-1不接受目前為大學部五、六年級學生（簡章第6頁）。"
    minimum = SCORE_MINIMUMS.get(degree)
    if minimum is None:
        return (
            "needs_confirmation",
            "學制未能確定；中央大學部平均60分、研究生70分，在職專班可申請但不具研修獎學金資格。",
        )
    if score is None:
        return (
            "needs_confirmation",
            f"尚未提供學業平均；中央此學制門檻為{minimum}分，不能以GPA換算代填。",
        )
    status = "pass" if score >= minimum else "fail"
    detail = f"學業平均{score:g}分，{'達到' if status == 'pass' else '未達'}中央{minimum}分門檻（簡章第6頁）。"
    if degree in UNDERGRADUATE and not current_year:
        return (
            "needs_confirmation" if status == "pass" else status
        ), detail + "仍須確認目前年級、至少一學年在學成績與交換期間學籍。"
    note = (
        "在職專班可申請但不具研修獎學金受領資格。"
        if degree in ("在職專班", "在職碩士班", "碩士在職專班")
        else ""
    )
    return (
        status,
        detail + note + "另須系所／導師或指導教授同意、在學成績及交換期間學籍。",
    )


def ncu_language_check(test: str | None, score: float | None) -> tuple[str, str]:
    return "needs_confirmation", (
        "中央校內必繳正式外語檢定成績，不限成績級數；英檢須在兩年效期內。"
        "TOEIC須含聽讀、IELTS須Academic；其他測驗及第三外語依簡章和志願校核對。"
        "只有分數無法確認正式證明與效期。外校語言門檻、單項與track另查，提名前須取得外校要求（簡章第4、6、7頁）。"
    )
