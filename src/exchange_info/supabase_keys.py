"""How the server identifies itself to Supabase."""
from __future__ import annotations


def supabase_key_headers(key: str) -> dict[str, str]:
    """Request headers carrying a server-side Supabase key.

    The newer ``sb_secret_...`` keys are not JWTs, so Supabase wants them in ``apikey`` only; the older
    ``service_role`` JWT is sent in ``apikey`` and as a Bearer token. Either kind works with the same setting.
    """
    key = (key or "").strip()
    if key.startswith("sb_"):
        return {"apikey": key}
    return {"apikey": key, "Authorization": f"Bearer {key}"}
