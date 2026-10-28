"""Your phone line to the office, through a Telegram bot you create yourself.

- Talking: every message you send the bot goes to Leo, the chief, exactly like the chat tab, and everything Leo says
  comes back to your phone.
- Notifications: a draft waiting for you (with its picture and 核准／退回 buttons), a post that was held back or
  failed, a post that went out.
- Only the chat paired with `uv run office auth telegram` is listened to; anyone else who finds the bot gets no answer.
- The bot asks Telegram for new messages itself (long polling), so the computer needs no public address.

The buttons do what the inbox buttons do, pressed by you; Leo still cannot approve anything.
"""

from __future__ import annotations

import json
import queue
import secrets
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

import httpx

from .store import now_utc

API = "https://api.telegram.org"
PAIR_TTL = timedelta(minutes=15)
CHANNEL = {"threads": "Threads", "instagram": "IG", "youtube": "YouTube", "github": "GitHub"}
FORMAT = {"text": "貼文", "reply": "留言回覆", "carousel": "輪播", "reel": "Reels", "story": "限動", "short": "Shorts", "long": "長影片",
          "data_update": "資料更新提案"}
CAPTION_LIMIT, TEXT_LIMIT = 1024, 4096
WELCOME = (
    "已連上 UniWay 行銷辦公室 ✅\n\n"
    "直接打字就是跟總管 Leo 說話，例如：\n・今天進度如何？\n・開工\n・#3 開頭再口語一點\n・明天多做獎學金的題目\n\n"
    "有草稿等你核准、貼文發出去或出問題時，我會傳到這裡。"
)


class TelegramError(RuntimeError):
    def __init__(self, message: str, code: int = 0):
        super().__init__(message)
        self.code = code


def _run_in_thread(target: Callable, *args) -> None:
    threading.Thread(target=target, args=args, daemon=True, name="telegram-chief").start()


class TelegramBridge:
    def __init__(self, office, http: httpx.Client | None = None, spawn: Callable = _run_in_thread):
        self.office = office
        self.token = office.settings.telegram_bot_token
        self.http = http or httpx.Client(timeout=httpx.Timeout(70.0, connect=15.0))
        self.spawn = spawn
        self.outbox: queue.Queue = queue.Queue()
        self.stop = threading.Event()
        self._offset = 0
        self._talk = threading.Lock()  # one conversation with the chief at a time, in order
        self._last_error = ""

    # ---- Telegram's Bot API ----
    def call(self, method: str, files: dict | None = None, **params) -> Any:
        url = f"{API}/bot{self.token}/{method}"
        try:
            if files:
                data = {k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v) for k, v in params.items()}
                response = self.http.post(url, data=data, files=files)
            else:
                response = self.http.post(url, json=params)
            body = response.json()
        except (httpx.HTTPError, ValueError) as error:  # the URL carries the token, so it never goes into the message
            raise TelegramError(f"連不上 Telegram（{type(error).__name__}）") from None
        if not body.get("ok"):
            raise TelegramError(f"Telegram {method}：{body.get('description', '失敗')}", int(body.get("error_code") or 0))
        return body.get("result")

    def _try(self, method: str, **params) -> Any:
        try:
            return self.call(method, **params)
        except TelegramError:
            return None

    @property
    def chat_id(self) -> str:
        return self.office.store.get("telegram_chat_id") or ""

    def bot_name(self) -> str:
        return self.call("getMe")["username"]

    def send(self, text: str, *, chat_id: str = "", buttons: list | None = None, photo: Path | None = None) -> None:
        chat_id = chat_id or self.chat_id
        if not chat_id:
            return
        markup = {"inline_keyboard": [buttons]} if buttons else None
        extra = {"reply_markup": markup} if markup else {}
        if photo and photo.is_file():
            try:
                self.call("sendPhoto", files={"photo": (photo.name, photo.read_bytes(), "image/jpeg")}, chat_id=chat_id,
                          caption=_cut(text, CAPTION_LIMIT), **extra)
                return
            except TelegramError:
                pass  # too big or unreadable: the text still goes out
        self.call("sendMessage", chat_id=chat_id, text=_cut(text, TEXT_LIMIT), link_preview_options={"is_disabled": True}, **extra)

    # ---- pairing your phone ----
    def new_pairing_code(self) -> str:
        code = secrets.token_urlsafe(9)
        self.office.store.set("telegram_pair", json.dumps({"code": code, "at": now_utc()}))
        return code

    def pairing_open(self, code: str) -> bool:
        pending = json.loads(self.office.store.get("telegram_pair") or "{}")
        return pending.get("code") == code

    def _pair(self, chat: str, code: str, user: dict) -> None:
        pending = json.loads(self.office.store.get("telegram_pair") or "{}")
        fresh = pending.get("code") and datetime.now(timezone.utc) - datetime.fromisoformat(pending["at"]) < PAIR_TTL
        if code and fresh and secrets.compare_digest(code, pending["code"]):
            store = self.office.store
            store.set("telegram_chat_id", chat)
            store.set("handle:telegram", user.get("username") or user.get("first_name") or "")
            store.set("telegram_pair", "{}")
            self.send(WELCOME, chat_id=chat)
        elif chat == self.chat_id:
            self.send("已經連上了，直接打字跟 Leo 說話就好。")

    # ---- messages from your phone ----
    def poll_once(self, timeout: int = 50, *, pairing_only: bool = False) -> int:
        updates = self.call("getUpdates", offset=self._offset, timeout=timeout, allowed_updates=["message", "callback_query"])
        for update in updates:
            self._offset = update["update_id"] + 1
            message = update.get("message") or {}
            if pairing_only and not (message.get("text") or "").startswith("/start"):
                continue
            try:
                self.handle(update)
            except Exception as error:  # noqa: BLE001 - one bad message must not stop the line
                self.office.bus.emit("chief", "log", f"Telegram 訊息處理失敗：{error}")
        return len(updates)

    def handle(self, update: dict) -> None:
        if "callback_query" in update:
            self._button(update["callback_query"])
            return
        message = update.get("message") or {}
        chat = str((message.get("chat") or {}).get("id", ""))
        text = (message.get("text") or "").strip()
        if text.startswith("/start"):
            self._pair(chat, text.partition(" ")[2].strip(), message.get("from") or {})
            return
        if not chat or chat != self.chat_id:
            return  # not the boss: say nothing at all
        if not text:
            self.send("我現在只看得懂文字訊息喔。")
            return
        self._try("sendChatAction", chat_id=chat, action="typing")
        self.spawn(self._talk_to_chief, text[:2000])

    def _talk_to_chief(self, text: str) -> None:
        # The answer reaches the phone through on_event, like everything else the chief says.
        with self._talk:
            self.office.staff["chief"].handle(text)

    def _button(self, query: dict) -> None:
        message = query.get("message") or {}
        chat = str((message.get("chat") or {}).get("id", ""))
        if not chat or chat != self.chat_id:
            return
        action, _, raw = (query.get("data") or "").partition(":")
        office = self.office
        try:
            draft_id = int(raw)
            if action == "approve":
                note = f"已核准，{self._when(office.approve(draft_id))}發出"
            elif action == "reject":
                office.reject(draft_id, "從手機退回")
                note = "已退回"
            else:
                return
        except (KeyError, ValueError) as error:
            note = "找不到這則" if isinstance(error, KeyError) else str(error)
        self._try("answerCallbackQuery", callback_query_id=query.get("id", ""), text=note[:190])
        if message.get("message_id"):
            self._try("editMessageReplyMarkup", chat_id=chat, message_id=message["message_id"], reply_markup={"inline_keyboard": []})
        self.send(f"#{raw} {note}")

    def _when(self, draft: dict) -> str:
        scheduled = draft.get("scheduled_at")
        if not scheduled or datetime.fromisoformat(scheduled) <= datetime.now(timezone.utc) + timedelta(minutes=1):
            return "下一輪（30 秒內）"
        local = datetime.fromisoformat(scheduled).astimezone(self.office.settings.timezone)
        today = datetime.now(self.office.settings.timezone).date()
        day = "今天" if local.date() == today else "明天" if local.date() == today + timedelta(days=1) else local.strftime("%m/%d")
        return f"{day} {local:%H:%M} "

    # ---- notifications ----
    def on_event(self, event: dict) -> None:
        if not self.chat_id:
            return
        if event.get("kind") == "chat" and event.get("sender") == "chief":
            self.outbox.put({"text": event["message"]})
        elif event.get("kind") == "draft" and event.get("draft"):
            draft = event["draft"]
            key = f"telegram:draft:{draft['id']}"
            if self.office.store.get(key) == draft["status"]:
                return
            self.office.store.set(key, draft["status"])
            message = self.draft_message(draft)
            if message:
                self.outbox.put(message)

    def draft_message(self, draft: dict) -> dict | None:
        status = draft["status"]
        label = f"#{draft['id']}｜{CHANNEL[draft['channel']]} {FORMAT.get(draft['format'], draft['format'])}"
        link = f"\n\n打開辦公室：{self.office.settings.office_url}" if self.office.settings.office_url else ""
        proposal = draft["format"] == "data_update"
        if status == "pending_approval":
            when = f"｜{self._when(draft).strip()}" if draft.get("scheduled_at") else ""
            text = f"{'📮 資料更新提案等你核准' if proposal else '📝 等你核准'} {label}{when}\n{draft['title']}\n\n{_preview(draft)}"
            return {"text": text + link, "photo": self._picture(draft),
                    "buttons": _decide(draft["id"], "✅ 核准並開 draft PR" if proposal else "✅ 核准")}
        if status == "needs_changes":
            issues = "\n".join(f"・{issue}" for issue in ((draft.get("review") or {}).get("issues") or [])[:3])
            text = (f"⚠️ 需要你看一下 {label}\n{draft['title']}\n\n{issues}\n\n"
                    + ("先點開官方來源確認，沒問題再核准；不要就退回。" if proposal else f"要重寫就跟我說「#{draft['id']} 改成…」，或照樣核准。"))
            if proposal:
                text += f"\n\n{_preview(draft)}"
            return {"text": text + link, "buttons": _decide(draft["id"], "照樣核准並開 draft PR" if proposal else "照樣核准")}
        if status == "published":
            dry = "\n（模擬發佈，沒有真的送出）" if draft.get("note") else ""
            if proposal:
                return {"text": f"📮 draft PR 開好了 {label}\n{draft['title']}\n{draft.get('remote_url') or ''}{dry}\n\n合併要你自己到 GitHub 按。".rstrip()}
            return {"text": f"🚀 已發出 {label}\n{draft['title']}\n{draft.get('remote_url') or ''}{dry}".rstrip()}
        if status == "failed":
            return {"text": f"❌ 發佈失敗 {label}\n{draft['title']}\n\n{(draft.get('error') or '')[:300]}{link}"}
        return None

    def _picture(self, draft: dict) -> Path | None:
        media = draft.get("media") or {}
        ref = (media.get("images") or [None])[0] or media.get("poster") or media.get("image")
        if not ref:
            return None
        try:
            return self.office.media_file(ref)
        except ValueError:
            return None

    def flush(self) -> None:
        while True:
            try:
                message = self.outbox.get_nowait()
            except queue.Empty:
                return
            self._deliver(message)

    def _deliver(self, message: dict) -> None:
        try:
            self.send(message["text"], buttons=message.get("buttons"), photo=message.get("photo"))
        except TelegramError as error:
            self._report(f"Telegram 通知沒送出：{error}")

    # ---- running inside `office serve` ----
    def start(self) -> threading.Event:
        self.office.bus.listen(self.on_event)
        threading.Thread(target=self._poll_loop, daemon=True, name="telegram-poll").start()
        threading.Thread(target=self._send_loop, daemon=True, name="telegram-send").start()
        return self.stop

    def _poll_loop(self) -> None:
        while not self.stop.is_set():
            try:
                self.poll_once()
                self._last_error = ""
            except TelegramError as error:
                hint = "（另一個程式也在收這個機器人的訊息，例如 office auth telegram）" if error.code == 409 else ""
                self._report(f"{error}{hint}")
                self.stop.wait(60 if error.code == 401 else 10)

    def _send_loop(self) -> None:
        while not self.stop.is_set():
            try:
                message = self.outbox.get(timeout=1)
            except queue.Empty:
                continue
            self._deliver(message)

    def _report(self, line: str) -> None:
        if line != self._last_error:  # say it once, not every retry
            self._last_error = line
            self.office.bus.emit("chief", "log", line)


def _decide(draft_id: int, approve_label: str) -> list[dict]:
    return [{"text": approve_label, "callback_data": f"approve:{draft_id}"}, {"text": "↩️ 退回", "callback_data": f"reject:{draft_id}"}]


def _preview(draft: dict) -> str:
    payload, fmt = draft.get("payload") or {}, draft["format"]
    if fmt == "data_update":
        suggestion = f"\n\n建議更新：{payload['suggested_update']}" if payload.get("suggested_update") else ""
        return f"{payload.get('detail', '')}{suggestion}\n\n官方來源：{payload.get('source_url') or '（沒有附）'}\n{payload.get('author', '')} 巡查發現"
    if fmt == "reply":
        return f"@{payload.get('username') or '訪客'}：{payload.get('comment_text', '')}\n\n→ {payload.get('text', '')}"
    if draft["channel"] == "threads":
        first = f"\n\n第一則留言：{payload['first_reply']}" if payload.get("first_reply") else ""
        return f"{payload.get('text', '')}{first}"
    if draft["channel"] == "youtube":
        return payload.get("description", "")[:400]
    return payload.get("caption_full") or payload.get("caption") or ""


def _cut(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"
