"""Turn the sourced cost summaries into comparable monthly figures, or say why not.

Only a clearly stated *monthly living* amount with a currency is extracted; the
original sentence is kept as evidence. A figure that is housing-only, partial,
undated-and-old, or flagged by the source as a historical benchmark is never
used to say a school fits a budget. Currency conversion uses the bundled
reference rates and is labelled as a rough reference.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Literal

from .models import DestinationProfile

_FX_PATH = Path(__file__).parent / "official_data" / "fx_reference.json"

_SYMBOLS = {
    "US$": "USD", "USD": "USD", "美元": "USD", "NZ$": "NZD", "NZD": "NZD", "A$": "AUD", "AU$": "AUD",
    "AUD": "AUD", "S$": "SGD", "SGD": "SGD", "C$": "CAD", "CAD": "CAD", "EUR": "EUR", "€": "EUR",
    "歐元": "EUR", "JPY": "JPY", "¥": "JPY", "日圓": "JPY", "日幣": "JPY", "NOK": "NOK", "SEK": "SEK",
    "PLN": "PLN", "CZK": "CZK", "HUF": "HUF", "GBP": "GBP", "£": "GBP", "英鎊": "GBP", "THB": "THB",
    "KRW": "KRW", "TWD": "TWD", "NT$": "TWD", "新台幣": "TWD", "CHF": "CHF", "MYR": "MYR", "RM": "MYR",
    "HKD": "HKD", "HK$": "HKD", "CNY": "CNY", "RMB": "CNY", "人民幣": "CNY", "IDR": "IDR", "INR": "INR",
    "PHP": "PHP", "VND": "VND", "AED": "AED", "TRY": "TRY", "RON": "RON", "DKK": "DKK",
}
_CURRENCY = "|".join(re.escape(key) for key in sorted(_SYMBOLS, key=len, reverse=True))
_NUMBER = r"\d[\d,]*(?:\.\d+)?"
_RANGE = r"[-–~〜至到]"
_PREFIX = re.compile(
    rf"(?P<cur>{_CURRENCY})\s?(?P<low>{_NUMBER})(?:\s?{_RANGE}\s?(?:{_CURRENCY})?\s?(?P<high>{_NUMBER}))?",
    re.IGNORECASE,
)
_MONTHLY = re.compile(r"每月|／月|/月|每個月|月預算|月生活|per month|monthly|a month", re.IGNORECASE)
_NOT_MONTHLY = re.compile(r"每週|／週|/週|每學期|／學期|/學期|每年|／年|/年|per week|per year|per semester|每學季|／日|/日|每日|每餐")
# A figure counts only when the sentence says it is the whole monthly living cost.
_TOTAL_PHRASE = re.compile(
    r"(?:平均)?每月(?:總)?(?:生活費|預算|準備|總計|生活成本|約需|需要)|月預算|總預算|預算|生活費(?:用)?|生活成本"
    r"|全部(?:支出|生活預算)|合計|住宿[、，及與和]\s*(?:飲食|餐食|餐費)[、，及與和]\s*交通"
)
_COMPONENTS = {
    "住宿": re.compile(r"住宿|租金|宿舍|房租|租屋"),
    "飲食": re.compile(r"飲食|餐"),
    "交通": re.compile(r"交通"),
    "水電網路": re.compile(r"水電|網路|電話"),
    "教材個人": re.compile(r"書籍|教材|個人支出|保險"),
}
_COMPONENT_WORDS = re.compile(r"住宿|租金|宿舍|房租|租屋|餐|交通|書籍|教材|保險|房|水電")
_EXCLUDED = re.compile(r"學位生|一般生|degree|非交換|大學部新生")
_PARTIAL = re.compile(r"不含|未含|不包含|扣除|另計|以外")
_HISTORICAL = re.compile(r"歷史|舊版|舊基準|舊金額|過時")
_YEAR = re.compile(r"(20[12]\d)")
_THOUSANDS_SPACE = re.compile(r"(?<=\d)[   ](?=\d{3}(?!\d))")
_MIN_CURRENT_YEAR = 2025


@dataclass(frozen=True)
class MonthlyCostEstimate:
    currency: str
    low: float
    high: float
    scope: Literal["total_living", "partial"]
    includes: tuple[str, ...]
    as_of_year: int | None
    outdated: bool
    evidence: str
    source_urls: tuple[str, ...] = field(default_factory=tuple)


@lru_cache(maxsize=1)
def fx_reference() -> dict:
    return json.loads(_FX_PATH.read_text(encoding="utf-8"))


def twd_per_unit(currency: str) -> float | None:
    if currency == "TWD":
        return 1.0
    return fx_reference().get("rates", {}).get(currency)


def _number(value: str) -> float:
    return float(value.replace(",", ""))


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"[。；\n]", text) if part.strip()]


def extract_monthly_estimates(profile: DestinationProfile) -> list[MonthlyCostEstimate]:
    """Return monthly living totals the source states outright, with evidence."""

    text = profile.cost_summary or ""
    sources = tuple(row.source_url for row in profile.sources if row.source_url)[:4]
    results: list[MonthlyCostEstimate] = []
    for raw in _sentences(text):
        sentence = _THOUSANDS_SPACE.sub("", raw)
        if _EXCLUDED.search(sentence):
            continue
        for phrase in _TOTAL_PHRASE.finditer(sentence):
            match = _PREFIX.search(sentence, phrase.start(), min(len(sentence), phrase.end() + 32))
            if match is None:
                continue
            currency = _SYMBOLS.get(match.group("cur")) or _SYMBOLS.get(match.group("cur").upper())
            if currency is None:
                continue
            tail = sentence[match.end(): match.end() + 10]
            between = sentence[phrase.end(): match.start()]
            before = sentence[max(0, phrase.start() - 12): phrase.start()] + between
            if _COMPONENT_WORDS.search(between) and not _PARTIAL.search(before):
                continue  # The figure belongs to a single cost item, not the total.
            if not _MONTHLY.search(sentence) or _NOT_MONTHLY.search(tail):
                continue
            low = _number(match.group("low"))
            high = _number(match.group("high")) if match.group("high") else low
            if high < low:
                low, high = high, low
            years = [int(year) for year in _YEAR.findall(sentence)]
            as_of = max(years) if years else None
            outdated = bool(_HISTORICAL.search(sentence)) or (
                as_of is not None and as_of < _MIN_CURRENT_YEAR
            )
            results.append(
                MonthlyCostEstimate(
                    currency=currency, low=low, high=high,
                    scope="partial" if _PARTIAL.search(before) else "total_living",
                    includes=tuple(name for name, rule in _COMPONENTS.items() if rule.search(sentence)),
                    as_of_year=as_of, outdated=outdated,
                    evidence=sentence[:220], source_urls=sources,
                )
            )
            break
    return results


def primary_estimate(estimates: list[MonthlyCostEstimate]) -> MonthlyCostEstimate | None:
    living = [row for row in estimates if row.scope == "total_living"]
    if not living:
        return None
    current = [row for row in living if not row.outdated]
    return (current or living)[0]


BudgetFit = Literal["within", "partly_within", "over", "unknown"]


def budget_fit(
    estimates: list[MonthlyCostEstimate],
    monthly_budget_twd: float | None,
    *,
    today: date | None = None,
) -> dict:
    """Compare a student's monthly budget (TWD) with the sourced monthly living cost.

    ``unknown`` always carries the reason. ``within`` means only that the sourced
    range sits under the budget; it excludes tuition, flights, visa, insurance
    and set-up costs, and is not a statement that the plan is affordable.
    """

    del today
    if not monthly_budget_twd:
        return {"status": "unknown", "reason": "尚未填寫每月預算。"}
    estimate = primary_estimate(estimates)
    if estimate is None:
        if estimates:
            return {
                "status": "unknown",
                "reason": "來源只列出住宿或部分項目，沒有完整的每月生活費，無法比對預算。",
            }
        return {"status": "unknown", "reason": "來源沒有可比對的每月生活費金額，請查官方費用頁。"}
    if estimate.outdated:
        return {
            "status": "unknown",
            "reason": "來源的每月生活費是舊年度或被標為歷史基準，不能直接拿來比對目前預算。",
            "estimate": _public(estimate, None),
        }
    rate = twd_per_unit(estimate.currency)
    if rate is None:
        return {
            "status": "unknown",
            "reason": f"沒有 {estimate.currency} 的參考匯率，無法換算成新台幣。",
            "estimate": _public(estimate, None),
        }
    low_twd, high_twd = estimate.low * rate, estimate.high * rate
    if high_twd <= monthly_budget_twd:
        status: BudgetFit = "within"
    elif low_twd <= monthly_budget_twd:
        status = "partly_within"
    else:
        status = "over"
    return {"status": status, "estimate": _public(estimate, rate), "low_twd": round(low_twd), "high_twd": round(high_twd)}


def _public(estimate: MonthlyCostEstimate, rate: float | None) -> dict:
    return {
        "currency": estimate.currency, "low": estimate.low, "high": estimate.high,
        "includes": list(estimate.includes), "as_of_year": estimate.as_of_year,
        "evidence": estimate.evidence, "source_urls": list(estimate.source_urls),
        "twd_per_unit": rate,
    }
