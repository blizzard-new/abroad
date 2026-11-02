"""Comment keyword → private message, the thing Manychat does, built into the office.

Someone comments a keyword ("雅思") under one of our Instagram posts or Reels; the office answers with a private message
(a link, some material) through Instagram's "private reply", and, if the boss wants, with one short public line under the
comment. The boss sets the rules in the chat with Leo; the message is the boss's own text, never written by an AI on the fly.

What Meta allows, and what this module keeps to:
- A private reply can only answer a comment on our own post, once per comment, and within 7 days of the comment.
- The text is at most 1000 bytes (about 330 Chinese characters).
- Only comments written after a rule was made are answered (an old comment is not a request).

What it adds so that a mistake cannot become spam: one message per person per rule per day, a daily limit, nothing sent for a
keyword that is too common, and a stop (with a message to the boss) the moment Meta says the permission is missing.
"""

from __future__ import annotations

import json
import re
import threading
import unicodedata
from datetime import date, datetime, timedelta, timezone

from .brand import BANNED_PHRASES
from .platforms.base import PlatformError
from .store import Store

MAX_RULES = 10
MAX_KEYWORDS = 5
MESSAGE_BYTES = 1000
PUBLIC_REPLY_CHARS = 100
REPLY_WINDOW = timedelta(days=7)  # Meta: a private reply has to go out within 7 days of the comment
EDGE = timedelta(hours=12)  # so a comment older than 6.5 days is left alone
SAME_PERSON = timedelta(hours=24)  # one message per person per rule per day, however often they comment the keyword
PERMISSION_PAUSE = timedelta(minutes=30)  # after "no permission" the office tries again after this long (the boss may have fixed it)
LIMIT_PAUSE = timedelta(minutes=10)
GIVE_UP_AFTER = 5  # this many unexplained failures in a row end the scan

# Words that turn up in half the comments: a rule on one of them would message people who asked for nothing.
TOO_GENERIC = {
    "我", "你", "好", "想", "要", "有", "是", "的", "了", "嗎", "請", "讚", "推", "我要", "想要", "請問", "謝謝", "感謝", "加油", "好棒", "好看",
    "哈哈", "喜歡", "支持", "收到", "知道", "可以", "沒有", "不要", "怎麼", "什麼", "幫我", "私我", "分享", "like", "ok", "yes", "no", "hi", "hello",
}
URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)

_LOCK = threading.Lock()


def normalise(text) -> str:
    """Lower case, full-width turned to normal, spaces and punctuation dropped: "雅思 閱讀！" and "雅思閱讀" are the same."""
    return re.sub(r"[\W_]+", "", unicodedata.normalize("NFKC", str(text or "")).casefold())


# ---- the rules the boss sets ----
def rules(store: Store) -> list[dict]:
    try:
        value = json.loads(store.get("dm_rules") or "[]")
    except json.JSONDecodeError:
        return []
    return value if isinstance(value, list) else []


def _save(store: Store, records: list[dict]) -> None:
    store.set("dm_rules", json.dumps(records, ensure_ascii=False))


def clean_keywords(words: list[str]) -> list[str]:
    keys: list[str] = []
    for word in words:
        word = str(word or "").strip()
        if not word:
            continue
        norm = normalise(word)
        if len(norm) < 2:
            raise ValueError(f"關鍵字「{word}」太短，至少 2 個字")
        if norm in TOO_GENERIC:
            raise ValueError(f"關鍵字「{word}」太普通，留言裡太容易出現，會誤傳給一堆沒要資料的人；請換成更精準的詞，例如「雅思閱讀」")
        if norm not in {normalise(k) for k in keys}:
            keys.append(word)
    if not keys:
        raise ValueError("要用哪個關鍵字？學生留言這個字，就會收到私訊")
    if len(keys) > MAX_KEYWORDS:
        raise ValueError(f"一條規則最多 {MAX_KEYWORDS} 個關鍵字")
    return keys


def problems(message: str, public_reply: str) -> list[str]:
    """Why these texts cannot go out, as sentences for the boss; empty when they are fine."""
    issues = []
    size = len(message.encode("utf-8"))
    if not message.strip():
        issues.append("私訊內容是空的：請給我要傳的完整內容（含連結）")
    if size > MESSAGE_BYTES:
        issues.append(f"私訊太長：Instagram 一則私訊最多 {MESSAGE_BYTES} bytes（約 330 個中文字），這則是 {size} bytes")
    for phrase in BANNED_PHRASES:
        if phrase in message or phrase in public_reply:
            issues.append(f"不能使用「{phrase}」這類誇大或暗示官方背書的說法")
    if any(url.lower().startswith("http://") for url in URL_RE.findall(message)):
        issues.append("私訊裡的連結請用 https 開頭")
    if URL_RE.search(public_reply):
        issues.append("公開回覆裡不要放連結（連結放在私訊裡），公開貼連結容易被當成垃圾留言")
    if len(public_reply) > PUBLIC_REPLY_CHARS:
        issues.append(f"公開回覆太長：請控制在 {PUBLIC_REPLY_CHARS} 字內，例如「已私訊你，記得查看訊息 👀」")
    return issues


def add(store: Store, *, keywords: list[str], message: str, public_reply: str = "", offer: str = "", draft_id: int = 0,
        now: datetime | None = None) -> dict:
    keywords = clean_keywords(keywords)
    message, public_reply, offer = message.strip(), public_reply.strip(), offer.strip()
    issues = problems(message, public_reply)
    if issues:
        raise ValueError("；".join(issues))
    if draft_id:
        post = store.draft(draft_id)
        if not post or post["channel"] != "instagram" or post["format"] not in {"carousel", "reel"}:
            raise ValueError(f"#{draft_id} 不是 IG 輪播或 Reels：只有這兩種貼文可以設留言關鍵字（要所有 IG 貼文都適用就不用指定編號）")
    with _LOCK:
        records = rules(store)
        if len(records) >= MAX_RULES:
            raise ValueError(f"自動私訊規則最多 {MAX_RULES} 條，先刪掉不要的")
        # The same word may appear again only for a different post (a rule for one post wins over the rule for all of them).
        taken = {normalise(k): r["id"] for r in records if r["draft_id"] == draft_id for k in r["keywords"]}
        for key in keywords:
            if normalise(key) in taken:
                raise ValueError(f"「{key}」已經是 D{taken[normalise(key)]} 的關鍵字，同一個字不能有兩條規則")
        number = int(store.get("dm_next_id") or 0) + 1
        store.set("dm_next_id", str(number))
        record = {
            "id": number, "keywords": keywords, "message": message, "public_reply": public_reply, "offer": offer, "draft_id": draft_id,
            "created": (now or datetime.now(timezone.utc)).isoformat(timespec="seconds"), "sent": 0, "failed": 0, "last_sent": "",
        }
        _save(store, [*records, record])
    return record


def remove(store: Store, rule_id: int) -> dict:
    with _LOCK:
        records = rules(store)
        found = next((r for r in records if r["id"] == rule_id), None)
        if not found:
            raise ValueError(f"沒有編號 D{rule_id} 的自動私訊規則")
        _save(store, [r for r in records if r["id"] != rule_id])
    return found


def bump(store: Store, rule_id: int, *, sent: int = 0, failed: int = 0, when: str = "") -> None:
    with _LOCK:
        records = rules(store)
        for record in records:
            if record["id"] == rule_id:
                record["sent"] = record.get("sent", 0) + sent
                record["failed"] = record.get("failed", 0) + failed
                if sent and when:
                    record["last_sent"] = when
        _save(store, records)


def describe(record: dict, posts: dict[int, str] | None = None) -> str:
    keys = "、".join(f"「{k}」" for k in record["keywords"])
    scope = f"只限 #{record['draft_id']}" if record["draft_id"] else "所有 IG 貼文"
    public = f"｜公開回「{record['public_reply'][:20]}」" if record.get("public_reply") else ""
    return f"D{record['id']}｜留言 {keys}｜{scope}｜私訊：{record['message'][:30].replace(chr(10), ' ')}…{public}｜已私訊 {record.get('sent', 0)} 位"


def hooks(store: Store) -> list[str]:
    """What the writers may invite people to comment, from the boss's own rules ("留言「雅思」領雅思閱讀教材")."""
    return [f"留言「{r['keywords'][0]}」{r['offer']}" for r in rules(store) if r.get("offer")]


def match(candidates: list[dict], text: str) -> dict | None:
    """The first rule (a rule for one post before a rule for every post) whose keyword is in the comment."""
    seen = normalise(text)
    for record in sorted(candidates, key=lambda r: (not r["draft_id"], r["id"])):
        if any(normalise(key) in seen for key in record["keywords"]):
            return record
    return None


# ---- what has been done already ----
def handled(store: Store, comment_id: str) -> bool:
    return store.get(f"dm:{comment_id}") is not None


def mark(store: Store, comment_id: str, outcome: str) -> None:
    store.set(f"dm:{comment_id}", outcome)


def recently_messaged(store: Store, rule_id: int, who: str, now: datetime) -> bool:
    last = store.get(f"dm_person:{rule_id}:{who}") if who else None
    return bool(last) and now - datetime.fromisoformat(last) < SAME_PERSON


def mark_person(store: Store, rule_id: int, who: str, now: datetime) -> None:
    if who:
        store.set(f"dm_person:{rule_id}:{who}", now.isoformat(timespec="seconds"))


def sent_on(store: Store, day: date) -> int:
    return int(store.get(f"dm_count:{day.isoformat()}") or 0)


def count_sent(store: Store, day: date) -> None:
    store.set(f"dm_count:{day.isoformat()}", str(sent_on(store, day) + 1))


# ---- paused because Meta said no ----
def blocked(store: Store, now: datetime) -> str:
    """Why sending is paused right now (an empty string when it is not)."""
    until = store.get("dm_blocked_until")
    if until and now < datetime.fromisoformat(until):
        return store.get("dm_blocked_reason") or "暫停中"
    return ""


def block(store: Store, reason: str, now: datetime, pause: timedelta) -> bool:
    """Pause sending. True when this is a new pause (the boss should be told), False when it only extends one."""
    fresh = not blocked(store, now)
    store.set("dm_blocked_until", (now + pause).isoformat(timespec="seconds"))
    store.set("dm_blocked_reason", reason)
    return fresh


# ---- reading Meta's answers ----
def classify(error: PlatformError) -> str:
    """permission (the app or token may not message), token (expired), limit (slow down), gone (this comment cannot be answered), other."""
    text = str(error)
    code = re.search(r'"code"\s*:\s*(\d+)', text)
    sub = re.search(r'"error_subcode"\s*:\s*(\d+)', text)
    number, subcode = (int(code.group(1)) if code else 0), (int(sub.group(1)) if sub else 0)
    lowered = text.lower()
    slow = error.status == 429 or number in {4, 17, 32, 613, 80002, 80006} or "rate limit" in lowered or "too many" in lowered
    expired = number == 190 or error.status == 401 or ("access token" in lowered and ("expired" in lowered or "invalid" in lowered))
    forbidden = number in {10, 200, 3} or "does not have permission" in lowered or "permission" in lowered or "(#10)" in text or "(#200)" in text
    gone = (number == 100 and subcode in {33, 2534022, 2534014, 2018001}) or "does not exist" in lowered or "outside of allowed window" in lowered
    for kind, hit in (("limit", slow), ("token", expired), ("permission", forbidden), ("gone", gone)):
        if hit:
            return kind
    return "other"


def explain(kind: str) -> str:
    return {
        "permission": ("Meta 說這個帳號或這把權杖沒有私訊的權限（instagram_business_manage_messages）。要在 Meta 開發者後台把這個權限加進應用程式、"
                       "重新產生權杖後再跑 uv run office auth instagram；而且要私訊「沒有加入測試人員」的一般學生，這個權限要先通過 Meta 的應用程式審核（進階存取）。"),
        "token": "Instagram 權杖失效或過期：重新跑 uv run office auth instagram",
        "limit": "Meta 說呼叫太頻繁，稍後會自動再試",
    }.get(kind, "")


def comment_time(value) -> datetime | None:
    """Instagram writes "2026-11-02T06:05:00+0000"."""
    text = str(value or "").strip()
    for pattern in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z"):
        try:
            return datetime.strptime(text, pattern).astimezone(timezone.utc)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None
