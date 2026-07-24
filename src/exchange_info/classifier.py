from __future__ import annotations

import re

from .models import PageCategory


CATEGORY_RULES: list[tuple[PageCategory, list[str]]] = [
    (
        PageCategory.DEADLINE,
        ["截止", "期限", "申請期間", "申請期限", "收件至", "開放申請至", "deadline"],
    ),
    (
        PageCategory.INFO_SESSION,
        ["說明會", "簡報", "講座", "session", "orientation"],
    ),
    (
        PageCategory.FAQ,
        ["FAQ", "faq", "常見問題", "問答", "Q&A", "q&a"],
    ),
    (
        PageCategory.EXPERIENCE_REPORT,
        ["心得", "心得分享", "經驗分享", "出國心得", "experience"],
    ),
    (
        PageCategory.SCHOLARSHIP,
        ["補助", "獎學金", "經費", "grant", "scholarship", "stipend"],
    ),
    (
        PageCategory.PARTNER_SCHOOL,
        ["可申請學校", "合作學校", "姊妹校", "partner", "university list", "協議"],
    ),
    (
        PageCategory.EXCHANGE_APPLICATION,
        ["交換學生", "校內申請", "出國研修", "自費研修", "雙聯", "雙學位", "選送", "申請須知"],
    ),
]


def classify_page(title: str, text: str, source_url: str = "") -> PageCategory:
    title_haystack = f"{title}\n{source_url}".lower()
    body_haystack = text.lower()
    best_category = PageCategory.OTHER
    best_score = 0

    for category, keywords in CATEGORY_RULES:
        score = 0
        for keyword in keywords:
            lowered = keyword.lower()
            if lowered in title_haystack:
                score += 4
            if lowered in body_haystack:
                score += 1
        if category == PageCategory.DEADLINE and re.search(
            r"(截止|期限|收件至|開放申請至|至\s*\d{1,2}\s*月\s*\d{1,2}\s*日)",
            text,
        ):
            score += 3
        if category == PageCategory.PARTNER_SCHOOL and any(
            keyword in title for keyword in ["可申請學校", "合作學校", "姊妹校"]
        ):
            score += 8
        if category == PageCategory.FAQ and any(keyword in title for keyword in ["FAQ", "常見問題"]):
            score += 8
        if category == PageCategory.INFO_SESSION and "說明會" in title:
            score += 8
        if score > best_score:
            best_score = score
            best_category = category

    return best_category
