"""The profile tells the page who may moderate, so students never probe the admin endpoint (and get a 403)."""
from exchange_info.api import _account_profile, _is_content_admin_account
from exchange_info.models import UserAccount


def account(email: str, account_id: str = "acct-1") -> UserAccount:
    return UserAccount(id=account_id, display_name="測試", email=email)


def test_students_are_not_content_admins(monkeypatch) -> None:
    monkeypatch.setenv("EXCHANGE_CONTENT_ADMIN_EMAILS", "admin@example.com")
    monkeypatch.delenv("EXCHANGE_PLATFORM_ADMIN_ACCOUNT_IDS", raising=False)
    assert _is_content_admin_account(account("student@example.com")) is False
    assert _account_profile(account("student@example.com")).is_content_admin is False


def test_listed_email_is_a_content_admin_regardless_of_case(monkeypatch) -> None:
    monkeypatch.setenv("EXCHANGE_CONTENT_ADMIN_EMAILS", " Admin@Example.com , other@example.com")
    monkeypatch.delenv("EXCHANGE_PLATFORM_ADMIN_ACCOUNT_IDS", raising=False)
    assert _account_profile(account("admin@example.com")).is_content_admin is True


def test_platform_admin_ids_count_too(monkeypatch) -> None:
    monkeypatch.delenv("EXCHANGE_CONTENT_ADMIN_EMAILS", raising=False)
    monkeypatch.setenv("EXCHANGE_PLATFORM_ADMIN_ACCOUNT_IDS", "acct-9")
    assert _account_profile(account("anyone@example.com", "acct-9")).is_content_admin is True
    assert _account_profile(account("anyone@example.com", "acct-1")).is_content_admin is False


def test_without_any_setting_nobody_is_an_admin(monkeypatch) -> None:
    monkeypatch.delenv("EXCHANGE_CONTENT_ADMIN_EMAILS", raising=False)
    monkeypatch.delenv("EXCHANGE_PLATFORM_ADMIN_ACCOUNT_IDS", raising=False)
    assert _is_content_admin_account(account("admin@example.com")) is False
