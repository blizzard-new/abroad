from exchange_info.classifier import classify_page
from exchange_info.models import PageCategory


def test_classify_deadline_takes_priority() -> None:
    category = classify_page(
        "115學年度交換學生申請公告",
        "即日起開放申請至6月10日止，請符合資格者踴躍申請。",
        "https://www.cgu.edu.tw/oia-ch/Subject/Detail/1",
    )

    assert category == PageCategory.DEADLINE


def test_classify_partner_school() -> None:
    category = classify_page(
        "可申請學校(交換學生、自費研修)",
        "長庚學生出交換學生可申請學校。",
    )

    assert category == PageCategory.PARTNER_SCHOOL


def test_classify_faq() -> None:
    assert classify_page("FAQ", "交換學生常見問題") == PageCategory.FAQ
