"""Server-owned platform access; public profile fields never grant privileges.

Reading the exchange catalogue needs no account. An account only carries a school so the
app can open on the right catalogue; what the school is based on is reported separately
(``school_basis``) and never widens what the account may write.
"""
from __future__ import annotations

import os
from typing import TYPE_CHECKING, Literal

from .university_registry import SUPPORTED_UNIVERSITIES, UniversityProfile, resolve_university

if TYPE_CHECKING:
    from .models import UserAccount

# Stored in ``home_university`` while a Google account has no school the server can infer.
HOME_UNIVERSITY_UNSET = "尚未選擇"

# Mail domains that belong to a supported university (subdomains included). The domain only
# shows which school an address is from: student, alumni and staff addresses look alike,
# so it is never treated as proof of current enrolment.
SCHOOL_EMAIL_DOMAINS: dict[str, tuple[str, ...]] = {
    "cgu": ("cgu.edu.tw",),
    "ntpu": ("ntpu.edu.tw",),
}

SchoolBasis = Literal["student_verified", "school_email", "self_declared"]


def is_platform_admin(account: UserAccount | None) -> bool:
    allowed = {
        value.strip()
        for value in os.environ.get("EXCHANGE_PLATFORM_ADMIN_ACCOUNT_IDS", "").split(",")
        if value.strip()
    }
    return bool(account and account.id in allowed)


def school_from_email(email: str | None) -> UniversityProfile | None:
    """The supported university an address belongs to; callers pass only provider-verified mail."""
    if not email or "@" not in email:
        return None
    domain = email.rpartition("@")[2].strip().lower()
    for university in SUPPORTED_UNIVERSITIES:
        for suffix in SCHOOL_EMAIL_DOMAINS.get(university.id, ()):
            if domain == suffix or domain.endswith(f".{suffix}"):
                return university
    return None


def verified_university(account: UserAccount | None) -> str | None:
    """The school a student card or school sign-in proved; nothing else counts."""
    if not account or not account.student_status_verified:
        return None
    university = resolve_university(account.verified_university) if account.verified_university else None
    return university.school_name if university else None


def catalog_home_university(account: UserAccount | None) -> str | None:
    """The supported school this account opens on: the verified one, else the one it chose."""
    if not account:
        return None
    verified = verified_university(account)
    if verified:
        return verified
    declared = (account.home_university or "").strip()
    if not declared or declared == HOME_UNIVERSITY_UNSET:
        return None
    university = resolve_university(declared)
    return university.school_name if university else None


def school_basis(account: UserAccount | None) -> SchoolBasis | None:
    school = catalog_home_university(account)
    if not account or not school:
        return None
    if verified_university(account):
        return "student_verified"
    from_email = school_from_email(account.email) if account.email_verified else None
    if from_email and from_email.school_name == school:
        return "school_email"
    return "self_declared"


def can_use_university(account: UserAccount | None, school: str) -> bool:
    """Writing as a student of ``school`` needs a verified school (or the platform admin)."""
    target = resolve_university(school)
    return bool(target and (
        is_platform_admin(account) or verified_university(account) == target.school_name
    ))
