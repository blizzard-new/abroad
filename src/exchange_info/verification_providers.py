from __future__ import annotations

import base64
import hashlib
import os
import re
import secrets
from dataclasses import dataclass
from typing import Literal, Mapping
from urllib.parse import quote, urlencode

from .models import (
    StudentVerificationMethod,
    StudentVerificationProviderAvailability,
    StudentVerificationProviderStatus,
)
from .university_registry import CGU, NTPU, require_university


ProviderProtocol = Literal["student_card", "google_oidc", "entra_oidc", "email_otp", "school_sso"]


class VerificationProviderError(ValueError):
    """Raised when a provider configuration or returned identity is unsafe."""


@dataclass(frozen=True)
class StudentVerificationProviderPolicy:
    id: str
    school_name: str
    method: StudentVerificationMethod
    label: str
    protocol: ProviderProtocol
    reason: str
    source_urls: tuple[str, ...]
    allowed_email_domains: tuple[str, ...] = ()
    email_pattern: str | None = None
    configuration_prefix: str | None = None
    configurable: bool = False
    partnership_required: bool = False
    supporting_only: bool = False

    @property
    def redirect_based(self) -> bool:
        return self.protocol in {"google_oidc", "entra_oidc", "school_sso"}


CGU_EMAIL_RULES = "https://www.cgu.edu.tw/regulation/ServerFile/Get/6731e095-b2f1-4564-b74b-e72deab39cd9"
CGU_ENTRA_GUIDE = "https://www.cgu.edu.tw/faq/Contents?nodeId=18826"
CGU_GOOGLE_NOTICE = "https://www.cgu.edu.tw/ic/Subject/Detail/35050?nodeId=11240"
NTPU_GOOGLE_RULES = "https://cms-carrier.ntpu.edu.tw/uploads/Google_Apps_for_Education_G_Suite_49d2ee084e.pdf"
NTPU_ENTRA_GUIDE = "https://m365.ntpu.edu.tw/en/guide"


PROVIDER_POLICIES: tuple[StudentVerificationProviderPolicy, ...] = (
    StudentVerificationProviderPolicy(
        id="cgu-student-card",
        school_name=CGU.school_name,
        method=StudentVerificationMethod.STUDENT_CARD,
        label="學生證正反面",
        protocol="student_card",
        reason="目前可在本平台進行一次性辨識，原圖不保存。",
        source_urls=(CGU_EMAIL_RULES,),
    ),
    StudentVerificationProviderPolicy(
        id="cgu-entra",
        school_name=CGU.school_name,
        method=StudentVerificationMethod.MICROSOFT_ENTRA,
        label="長庚 Microsoft 365",
        protocol="entra_oidc",
        reason=(
            "官方說明學生與畢業校友都可使用 @cgu.edu.tw；"
            "只驗證帳號無法證明目前在學，需校方提供在學 claim 後才能啟用。"
        ),
        source_urls=(CGU_ENTRA_GUIDE, CGU_EMAIL_RULES),
        allowed_email_domains=("cgu.edu.tw",),
        email_pattern=r"^[a-z0-9._-]+@cgu\.edu\.tw$",
        partnership_required=True,
    ),
    StudentVerificationProviderPolicy(
        id="cgu-google-workspace",
        school_name=CGU.school_name,
        method=StudentVerificationMethod.GOOGLE_WORKSPACE,
        label="長庚 Google Workspace",
        protocol="google_oidc",
        reason="官方公告可確認服務存在，但沒有可供平台驗證當下在學狀態的 claim。",
        source_urls=(CGU_GOOGLE_NOTICE,),
        allowed_email_domains=("gap.cgu.edu.tw",),
        partnership_required=True,
    ),
    StudentVerificationProviderPolicy(
        id="cgu-school-email",
        school_name=CGU.school_name,
        method=StudentVerificationMethod.SCHOOL_EMAIL,
        label="長庚校方 Email OTP",
        protocol="email_otp",
        reason="長庚學生畢業後仍可保留帳號，Email OTP 只能作為輔助因子，不單獨授予在學資格。",
        source_urls=(CGU_EMAIL_RULES,),
        allowed_email_domains=("cgu.edu.tw",),
        email_pattern=r"^[a-z0-9._-]+@cgu\.edu\.tw$",
        supporting_only=True,
    ),
    StudentVerificationProviderPolicy(
        id="cgu-school-sso",
        school_name=CGU.school_name,
        method=StudentVerificationMethod.SCHOOL_SSO,
        label="長庚校方 SSO",
        protocol="school_sso",
        reason="需校方合作登記正式 redirect URI 並提供在學狀態 claim。",
        source_urls=(CGU_ENTRA_GUIDE,),
        partnership_required=True,
    ),
    StudentVerificationProviderPolicy(
        id="ntpu-student-card",
        school_name=NTPU.school_name,
        method=StudentVerificationMethod.STUDENT_CARD,
        label="學生證正反面",
        protocol="student_card",
        reason="目前可在本平台進行一次性辨識，原圖不保存。",
        source_urls=(NTPU_GOOGLE_RULES,),
    ),
    StudentVerificationProviderPolicy(
        id="ntpu-entra",
        school_name=NTPU.school_name,
        method=StudentVerificationMethod.MICROSOFT_ENTRA,
        label="臺北大學 Microsoft 365",
        protocol="entra_oidc",
        reason=(
            "校方租戶 App 設定完成後，才能以正式重新導向驗證 "
            "s+學號@ms.ntpu.edu.tw；本平台不接收 Microsoft 或校務密碼。"
        ),
        source_urls=(NTPU_ENTRA_GUIDE,),
        allowed_email_domains=("ms.ntpu.edu.tw",),
        email_pattern=r"^s[0-9]+@ms\.ntpu\.edu\.tw$",
        configuration_prefix="EXCHANGE_NTPU_STUDENT_ENTRA",
        configurable=True,
    ),
    StudentVerificationProviderPolicy(
        id="ntpu-google-workspace",
        school_name=NTPU.school_name,
        method=StudentVerificationMethod.GOOGLE_WORKSPACE,
        label="臺北大學 Google Workspace",
        protocol="google_oidc",
        reason=(
            "學生帳號由校方建立，但畢業後仍保留部分 Google 服務；"
            "單靠 hosted domain 不足以證明目前在學。"
        ),
        source_urls=(NTPU_GOOGLE_RULES,),
        allowed_email_domains=("gm.ntpu.edu.tw",),
        email_pattern=r"^s[0-9]+@gm\.ntpu\.edu\.tw$",
        partnership_required=True,
    ),
    StudentVerificationProviderPolicy(
        id="ntpu-school-email",
        school_name=NTPU.school_name,
        method=StudentVerificationMethod.SCHOOL_EMAIL,
        label="臺北大學校方 Email OTP",
        protocol="email_otp",
        reason="預留寄送至校方學生信箱的驗證流程；正式啟用前需確認信箱生命週期與郵件可達性。",
        source_urls=(NTPU_GOOGLE_RULES,),
        allowed_email_domains=("gm.ntpu.edu.tw", "webmail.ntpu.edu.tw"),
        email_pattern=r"^s[0-9]+@(gm|webmail)\.ntpu\.edu\.tw$",
        partnership_required=True,
    ),
    StudentVerificationProviderPolicy(
        id="ntpu-school-sso",
        school_name=NTPU.school_name,
        method=StudentVerificationMethod.SCHOOL_SSO,
        label="臺北大學校方 SSO",
        protocol="school_sso",
        reason="需校方合作登記正式 redirect URI 與在學狀態 claim，目前不開放。",
        source_urls=(NTPU_ENTRA_GUIDE,),
        partnership_required=True,
    ),
)


def verification_provider_policy(provider_id: str) -> StudentVerificationProviderPolicy:
    normalized = provider_id.strip().lower()
    for policy in PROVIDER_POLICIES:
        if policy.id == normalized:
            return policy
    raise VerificationProviderError("不支援這個學生身分驗證方式。")


def _runtime_values(
    policy: StudentVerificationProviderPolicy,
    environment: Mapping[str, str],
) -> dict[str, str]:
    if not policy.configuration_prefix:
        return {}
    prefix = policy.configuration_prefix
    return {
        "client_id": environment.get(f"{prefix}_CLIENT_ID", "").strip(),
        "client_secret": environment.get(f"{prefix}_CLIENT_SECRET", "").strip(),
        "tenant_id": environment.get(f"{prefix}_TENANT_ID", "").strip(),
    }


def verification_provider_status(
    policy: StudentVerificationProviderPolicy,
    environment: Mapping[str, str] | None = None,
) -> StudentVerificationProviderStatus:
    environment = os.environ if environment is None else environment
    configured = _runtime_values(policy, environment)
    if policy.protocol == "student_card":
        enabled = True
        availability = StudentVerificationProviderAvailability.AVAILABLE
    elif policy.supporting_only:
        enabled = False
        availability = StudentVerificationProviderAvailability.SUPPORTING_ONLY
    elif policy.partnership_required:
        enabled = False
        availability = StudentVerificationProviderAvailability.SCHOOL_PARTNERSHIP_REQUIRED
    elif policy.configurable:
        enabled = bool(
            configured.get("client_id")
            and configured.get("client_secret")
            and configured.get("tenant_id")
        )
        availability = (
            StudentVerificationProviderAvailability.AVAILABLE
            if enabled
            else StudentVerificationProviderAvailability.CONFIGURATION_REQUIRED
        )
    else:
        enabled = False
        availability = StudentVerificationProviderAvailability.SCHOOL_PARTNERSHIP_REQUIRED
    reason = policy.reason
    if enabled and policy.protocol == "entra_oidc":
        reason = (
            "已完成平台端設定；驗證時會離開本站前往校方 Microsoft "
            "登入頁，本平台不會看到或保存校務密碼。"
        )
    return StudentVerificationProviderStatus(
        id=policy.id,
        school_name=policy.school_name,
        method=policy.method,
        label=policy.label,
        enabled=enabled,
        availability=availability,
        reason=reason,
        redirect_based=policy.redirect_based,
        allowed_email_domains=list(policy.allowed_email_domains),
        source_urls=list(policy.source_urls),
    )


def verification_provider_statuses(
    school_name: str | None = None,
    environment: Mapping[str, str] | None = None,
) -> list[StudentVerificationProviderStatus]:
    selected_school = None
    if school_name is not None:
        selected_school = require_university(school_name).school_name
    return [
        verification_provider_status(policy, environment)
        for policy in PROVIDER_POLICIES
        if selected_school is None or policy.school_name == selected_school
    ]


def provider_runtime_configuration(
    policy: StudentVerificationProviderPolicy,
    environment: Mapping[str, str] | None = None,
) -> dict[str, str]:
    environment = os.environ if environment is None else environment
    status = verification_provider_status(policy, environment)
    if not status.enabled or not policy.redirect_based:
        raise VerificationProviderError(status.reason)
    values = _runtime_values(policy, environment)
    if policy.protocol == "entra_oidc":
        tenant_id = values.get("tenant_id", "")
        if not re.fullmatch(r"[a-zA-Z0-9.-]{3,120}", tenant_id):
            raise VerificationProviderError("校方 Microsoft tenant 設定無效。")
    return values


def new_pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return verifier, challenge


def authorization_url(
    policy: StudentVerificationProviderPolicy,
    configuration: Mapping[str, str],
    *,
    redirect_uri: str,
    state: str,
    code_challenge: str,
) -> str:
    common = {
        "client_id": configuration["client_id"],
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid profile email",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "prompt": "select_account",
    }
    if policy.protocol == "entra_oidc":
        tenant = quote(configuration["tenant_id"], safe="")
        return (
            f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize?"
            f"{urlencode(common)}"
        )
    if policy.protocol == "google_oidc":
        if policy.allowed_email_domains:
            common["hd"] = policy.allowed_email_domains[0]
        return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(common)}"
    raise VerificationProviderError("這個驗證方式不是可開啟的 OAuth 流程。")


def token_endpoint(
    policy: StudentVerificationProviderPolicy,
    configuration: Mapping[str, str],
) -> str:
    if policy.protocol == "entra_oidc":
        tenant = quote(configuration["tenant_id"], safe="")
        return f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
    if policy.protocol == "google_oidc":
        return "https://oauth2.googleapis.com/token"
    raise VerificationProviderError("這個 provider 沒有 OAuth token endpoint。")


def userinfo_endpoint(policy: StudentVerificationProviderPolicy) -> str:
    if policy.protocol == "entra_oidc":
        return "https://graph.microsoft.com/oidc/userinfo"
    if policy.protocol == "google_oidc":
        return "https://openidconnect.googleapis.com/v1/userinfo"
    raise VerificationProviderError("這個 provider 沒有 OIDC UserInfo endpoint。")


def validate_provider_identity(
    policy: StudentVerificationProviderPolicy,
    claims: Mapping[str, object],
) -> str:
    if not str(claims.get("sub") or "").strip():
        raise VerificationProviderError("校方帳號沒有回傳穩定的使用者識別碼。")
    if policy.protocol == "google_oidc" and claims.get("email_verified") is not True:
        raise VerificationProviderError("校方帳號沒有回傳已驗證 Email。")
    email = str(claims.get("email") or claims.get("preferred_username") or "").strip().casefold()
    if not email or "@" not in email:
        raise VerificationProviderError("校方帳號沒有回傳可驗證的 Email。")
    domain = email.rsplit("@", 1)[1]
    if domain not in policy.allowed_email_domains:
        raise VerificationProviderError("這個帳號不屬於所選學校的允許網域。")
    if policy.email_pattern and not re.fullmatch(policy.email_pattern, email, re.IGNORECASE):
        raise VerificationProviderError("這個帳號不符合該校學生帳號格式。")
    if policy.protocol == "google_oidc":
        hosted_domain = str(claims.get("hd") or "").strip().casefold()
        if hosted_domain != domain:
            raise VerificationProviderError("Google hosted domain 與允許學校不符。")
    return email
