"""Preview or submit one changed public UniWay URL to IndexNow."""

import argparse
import os
from urllib.parse import urlsplit

import requests

from exchange_info.indexnow import valid_indexnow_key
from exchange_info.seo import SeoSettings

INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="Absolute HTTPS URL of a changed public page")
    parser.add_argument("--submit", action="store_true", help="Send the request. The default only previews.")
    args = parser.parse_args(argv)

    raw_key = os.environ.get("INDEXNOW_KEY", "").strip()
    if not raw_key:
        print("IndexNow skipped: INDEXNOW_KEY is unset.")
        return 0
    key = valid_indexnow_key(raw_key)
    if not key:
        parser.error("INDEXNOW_KEY must contain 8 to 128 ASCII letters, digits or hyphens.")

    settings = SeoSettings.from_environment()
    origin = urlsplit(settings.origin)
    try:
        target = urlsplit(args.url)
        same_origin = (
            target.scheme == "https"
            and target.hostname == origin.hostname
            and (target.port or 443) == (origin.port or 443)
            and not target.username
            and target.password is None
        )
    except ValueError:
        same_origin = False
    if not same_origin or any(c.isspace() or c in "\\?#" for c in args.url):
        parser.error("Use a canonical HTTPS page URL on EXCHANGE_PUBLIC_BASE_URL, without a query or fragment.")

    if not args.submit:
        print("IndexNow preview: 1 URL. Use --submit to send it.")
        return 0
    if not settings.indexable:
        parser.error("Submission requires an indexable site environment.")

    try:
        response = requests.post(
            INDEXNOW_ENDPOINT,
            json={
                "host": origin.hostname,
                "key": key,
                "keyLocation": f"{settings.origin}/{key}.txt",
                "urlList": [args.url],
            },
            timeout=10,
            allow_redirects=False,
        )
    except requests.RequestException:
        print("IndexNow request failed before a response was received.")
        return 1
    if response.status_code not in (200, 202):
        print(f"IndexNow rejected the request (HTTP {response.status_code}).")
        return 1
    print(f"IndexNow accepted the notification (HTTP {response.status_code}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
