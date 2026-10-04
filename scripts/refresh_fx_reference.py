"""Refresh the bundled reference exchange rates (TWD per one unit of currency).

The app never calls a rate service while serving requests. Run this by hand when
the reference needs to be newer; the file records the provider, the provider's
own update time and the terms page, and the app labels every converted figure as
a rough reference rather than a quoted rate.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

URL = "https://open.er-api.com/v6/latest/TWD"
OUTPUT = Path(__file__).resolve().parents[1] / "src/exchange_info/official_data/fx_reference.json"
CURRENCIES = (
    "USD", "EUR", "JPY", "GBP", "AUD", "NZD", "SGD", "CAD", "CHF", "HKD", "CNY", "KRW",
    "THB", "MYR", "IDR", "INR", "PHP", "VND", "SEK", "NOK", "DKK", "PLN", "CZK", "HUF",
    "RON", "TRY", "AED", "ILS", "ZAR", "BRL", "MXN", "ARS", "CLP", "COP", "PEN", "RUB",
)


def main() -> int:
    request = Request(URL, headers={"User-Agent": "exchange-info-fx-refresh/1.0"})
    with urlopen(request, timeout=30) as response:  # noqa: S310 - fixed https URL
        payload = json.load(response)
    if payload.get("result") != "success":
        print("rate service did not return success", file=sys.stderr)
        return 1
    per_twd = payload["rates"]
    rates = {
        code: round(1 / per_twd[code], 6)
        for code in CURRENCIES
        if per_twd.get(code)
    }
    document = {
        "base": "TWD",
        "meaning": "TWD per one unit of the currency; a rough reference, not a quoted bank rate.",
        "provider": payload.get("provider"),
        "terms_of_use": payload.get("terms_of_use"),
        "attribution": "Rates By Exchange Rate API (https://www.exchangerate-api.com)",
        "provider_updated_at": payload.get("time_last_update_utc"),
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rates": dict(sorted(rates.items())),
    }
    OUTPUT.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(rates)} rates to {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
