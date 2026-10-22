"""The real UniWay web app, set up for recording the tutorial video (see README.md).

    .venv/bin/python marketing/tutorial-video/demo_server.py [--port 8771] [--data-dir /tmp/uniway-tutorial-data]

Everything a visitor sees is the normal app and its normal data. Two things differ, and only in this process:
- Accounts, sessions and saved schools go to a throwaway data folder, never to data/.
- Sign-in is Google only, as on the live site, but Google itself is not contacted: the token exchange and the
  profile lookup answer with one made-up student (示範同學, a verified @cgu.edu.tw address). Everything on
  UniWay's side of the sign-in still runs: the terms check, the state cookie, the callback and picking the school
  from the email domain. The recorder skips Google's own account picker (record.py).
"""

from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path

import uvicorn

DEMO_USER = {
    "sub": "uniway-tutorial-demo",
    "email": "demo.student@cgu.edu.tw",
    "email_verified": True,
    "name": "示範同學",
}


class _Answer:
    def __init__(self, payload: dict) -> None:
        self._payload = payload
        self.status_code = 200

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


class _GoogleStandIn:
    """`requests` for exchange_info.api, except that Google's two sign-in calls get the demo student."""

    def __init__(self, real) -> None:
        self._real = real

    def __getattr__(self, name):
        return getattr(self._real, name)

    def post(self, url, *args, **kwargs):
        if url == "https://oauth2.googleapis.com/token":
            return _Answer({"access_token": "uniway-tutorial-demo"})
        return self._real.post(url, *args, **kwargs)

    def get(self, url, *args, **kwargs):
        if url == "https://openidconnect.googleapis.com/v1/userinfo":
            return _Answer(DEMO_USER)
        return self._real.get(url, *args, **kwargs)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8771)
    parser.add_argument("--data-dir", default="")
    args = parser.parse_args()

    data_dir = Path(args.data_dir or tempfile.mkdtemp(prefix="uniway-tutorial-"))
    data_dir.mkdir(parents=True, exist_ok=True)
    os.environ.update(
        {
            "EXCHANGE_INFO_DATA_DIR": str(data_dir),
            "EXCHANGE_AUTH_METHODS": "google",
            "EXCHANGE_ANALYTICS": "off",
            "GOOGLE_OAUTH_CLIENT_ID": "uniway-tutorial-demo",
            "GOOGLE_OAUTH_CLIENT_SECRET": "uniway-tutorial-demo",
        }
    )

    import exchange_info.api as api

    api.requests = _GoogleStandIn(api.requests)
    print(f"tutorial demo server: data in {data_dir}", flush=True)
    uvicorn.run(api.app, host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
