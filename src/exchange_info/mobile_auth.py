"""Browser OAuth handoff to an installed app, bound to S256 PKCE.

Only a two-minute, single-use authorization code crosses the app link. The
account session itself is issued through HTTPS after verifying the app secret.
The existing shared transient store provides atomic consumption across workers.
"""
from __future__ import annotations

import base64
import hashlib
import secrets
from datetime import timedelta
from typing import Callable
from urllib.parse import urlencode

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field

from .legal_pages import TERMS_VERSION
from .models import AccountSession, UserAccount, utc_now
from .transient_auth import TransientAuthState, TransientAuthStateKind

MOBILE_CALLBACK = "tw.uniway.app://auth"
MOBILE_PROVIDER = "mobile-session"


class MobileSessionExchange(BaseModel):
    code: str = Field(min_length=43, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")
    code_verifier: str = Field(min_length=43, max_length=128, pattern=r"^[A-Za-z0-9._~-]+$")


def pkce_challenge(verifier: str) -> str:
    return base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest()).decode().rstrip("=")


def mobile_handoff_url(app: FastAPI, account_id: str, challenge: str, state: str) -> str:
    code = secrets.token_urlsafe(32)
    app.state.transient_auth_store.save_state(TransientAuthState(
        state_hash=hashlib.sha256(code.encode()).hexdigest(),
        kind=TransientAuthStateKind.OAUTH_LOGIN,
        provider_id=MOBILE_PROVIDER,
        account_id=account_id,
        session_id=challenge,
        expires_at=utc_now() + timedelta(minutes=2),
    ))
    return f"{MOBILE_CALLBACK}?{urlencode({'code': code, 'state': state})}"


def register_mobile_auth_routes(app: FastAPI, issue_session: Callable[[UserAccount], AccountSession]) -> None:
    @app.get("/auth/mobile/config")
    def mobile_config(response: Response) -> dict:
        response.headers["Cache-Control"] = "no-store"
        return {"enabled": True, "terms_version": TERMS_VERSION,
                "redirect_uri": MOBILE_CALLBACK, "pkce_method": "S256"}

    @app.post("/auth/mobile/exchange", response_model=AccountSession)
    def exchange(payload: MobileSessionExchange, response: Response) -> AccountSession:
        response.headers["Cache-Control"] = "no-store"
        response.headers["Pragma"] = "no-cache"
        record = app.state.transient_auth_store.consume_state(
            hashlib.sha256(payload.code.encode()).hexdigest(),
            TransientAuthStateKind.OAUTH_LOGIN,
            expected_provider_id=MOBILE_PROVIDER,
            expected_session_id=pkce_challenge(payload.code_verifier),
        )
        if record is None or record.account_id is None:
            raise HTTPException(status_code=401, detail="手機登入驗證已失效，請重新登入。")
        account = app.state.account_repository.find_account_by_id(record.account_id)
        if account is None:
            raise HTTPException(status_code=401, detail="找不到這個帳號。")
        return issue_session(account)
