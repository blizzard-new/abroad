"""Server-owned platform access; public profile fields never grant privileges.

Reading the exchange catalogue needs no account. An account carries a school: the app opens on that catalogue and the
school is shown on what the account posts. The school is the one the account holder picked (or the one their school mail
domain names); nobody checks enrolment, so what it is based on is reported separately (``school_basis``). To keep people
from hopping between school boards, a picked school cannot be changed again for ``SCHOOL_CHANGE_LOCK``.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
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
    "cgu": ("cgu.edu.tw", "mail.cgu.edu.tw", "gap.cgu.edu.tw"),
    "ntpu": ("ntpu.edu.tw", "gm.ntpu.edu.tw", "mail.ntpu.edu.tw"),
    "ntu": ("ntu.edu.tw", "g.ntu.edu.tw", "mail.ntu.edu.tw"),
    "ccu": ("ccu.edu.tw", "alum.ccu.edu.tw", "g.ccu.edu.tw", "mail.ccu.edu.tw"),
    "ncu": ("ncu.edu.tw", "cc.ncu.edu.tw", "g.ncu.edu.tw", "mail.ncu.edu.tw"),
    "tku": ("tku.edu.tw", "gms.tku.edu.tw", "o365.tku.edu.tw", "mail.tku.edu.tw", "s00.tku.edu.tw"),
    "fju": ("fju.edu.tw", "mail.fju.edu.tw", "gapp.fju.edu.tw", "m365.fju.edu.tw"),
    "scu": ("scu.edu.tw", "gm.scu.edu.tw", "alumni.scu.edu.tw"),
    "ntnu": ("ntnu.edu.tw", "gapps.ntnu.edu.tw", "std.ntnu.edu.tw"),
    "cycu": ("cycu.edu.tw", "ice.cycu.edu.tw", "cycu.org.tw"),
    "ntust": ("ntust.edu.tw", "mail.ntust.edu.tw", "gapps.ntust.edu.tw"),
    "yzu": ("yzu.edu.tw", "saturn.yzu.edu.tw", "mail.yzu.edu.tw"),
    "fcu": ("fcu.edu.tw", "o365.fcu.edu.tw", "mail.fcu.edu.tw"),
    "nsysu": ("nsysu.edu.tw", "mail.nsysu.edu.tw", "student.nsysu.edu.tw", "g-mail.nsysu.edu.tw"),
    "nchu": ("nchu.edu.tw", "smail.nchu.edu.tw", "mail.nchu.edu.tw", "dragon.nchu.edu.tw"),
    "ntut": ("ntut.edu.tw", "mail.ntut.edu.tw", "tmail.ntut.edu.tw", "ntut.org.tw"),
    "nccu": ("nccu.edu.tw", "g.nccu.edu.tw", "mail2.nccu.edu.tw"),
    "ncku": ("ncku.edu.tw", "mail.ncku.edu.tw", "gs.ncku.edu.tw", "email.ncku.edu.tw"),
    "nycu": ("nycu.edu.tw", "c.nycu.edu.tw", "m.nycu.edu.tw", "gm.ym.edu.tw", "ym.edu.tw", "nctu.edu.tw"),
    "nthu": ("nthu.edu.tw", "gapp.nthu.edu.tw", "m112.nthu.edu.tw", "m113.nthu.edu.tw", "m114.nthu.edu.tw", "m115.nthu.edu.tw", "oz.nthu.edu.tw"),
    "pccu": ("pccu.edu.tw", "ulive.pccu.edu.tw", "dep.pccu.edu.tw", "g.pccu.edu.tw"),
    "wzu": ("wzu.edu.tw", "mail.wzu.edu.tw", "gap.wzu.edu.tw"),
    "nkust": ("nkust.edu.tw", "gm.nkust.edu.tw", "std.nkust.edu.tw"),
    "yuntech": ("yuntech.edu.tw", "gemail.yuntech.edu.tw", "live.yuntech.edu.tw"),
    "ntou": ("ntou.edu.tw", "mail.ntou.edu.tw", "email.ntou.edu.tw"),
    "ncue": ("ncue.edu.tw", "gm.ncue.edu.tw", "cc.ncue.edu.tw", "mail.ncue.edu.tw"),
    "nknu": ("nknu.edu.tw", "mail.nknu.edu.tw", "stu.nknu.edu.tw", "gm.nknu.edu.tw"),
    "tmu": ("tmu.edu.tw", "my2.tmu.edu.tw", "mail.tmu.edu.tw", "gap.tmu.edu.tw"),
    "csmu": ("csmu.edu.tw", "live.csmu.edu.tw", "gm.csmu.edu.tw", "mail.csmu.edu.tw"),
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
    value = (account.verified_university or "").strip()
    university = resolve_university(value) if value else None
    return university.school_name if university else None


def community_author_display_name(account: UserAccount, mode) -> str | None:
    """Derive bylines from server fields; a catalogue choice proves no enrolment."""
    mode = getattr(mode, "value", mode)
    if mode == "anonymous":
        return "匿名學生"
    if mode == "real_name":
        return account.display_name
    school = verified_university(account)
    if not school:
        return None
    if mode == "verified_school":
        return f"{school}學生"
    if mode == "verified_department" and account.verified_department:
        return f"{school} {account.verified_department}學生"
    return None


def university_community_board(value: str | None) -> UniversityProfile | None:
    """Recognize current IDs, school names, and the prior university:<id> alias."""
    if not value or not value.strip():
        return None
    target = value.strip().removeprefix("university:").strip()
    return resolve_university(target) if target else None


def is_university_community_post(post) -> bool:
    return (getattr(post.board_kind, "value", post.board_kind) == "university_exchange"
            or university_community_board(post.board_id or post.school_name) is not None)


def can_read_university_community(account: UserAccount | None) -> bool:
    return bool(account and account.email_verified)


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


SCHOOL_CHANGE_LOCK = timedelta(days=3)


def school_change_locked_until(account: UserAccount | None, now: datetime | None = None) -> datetime | None:
    """When the account may pick another school; None when it may do so now.

    Picking a school for the first time is never locked, and neither is an account whose pick was not timestamped
    (accounts made before the lock existed).
    """
    if not account:
        return None
    current = (account.home_university or "").strip()
    changed_at = getattr(account, "home_university_changed_at", None)
    if not current or current == HOME_UNIVERSITY_UNSET or changed_at is None:
        return None
    if changed_at.tzinfo is None:
        changed_at = changed_at.replace(tzinfo=timezone.utc)
    until = changed_at + SCHOOL_CHANGE_LOCK
    return until if until > (now or datetime.now(timezone.utc)) else None
