"""What a draft is called and how it reads in a notification, shared by the Telegram line and the phone app."""

from __future__ import annotations

CHANNEL = {"threads": "Threads", "instagram": "IG", "youtube": "YouTube", "github": "GitHub"}
FORMAT = {"text": "貼文", "reply": "留言回覆", "carousel": "輪播", "reel": "Reels", "story": "限動", "short": "Shorts", "long": "長影片",
          "data_update": "資料更新提案"}


def cut(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def label(draft: dict) -> str:
    return f"#{draft['id']}｜{CHANNEL[draft['channel']]} {FORMAT.get(draft['format'], draft['format'])}"


def preview_text(draft: dict) -> str:
    payload, fmt = draft.get("payload") or {}, draft["format"]
    if fmt == "data_update":
        if payload.get("verified_by"):
            check = f"\n\n🔎 {payload['verified_by']} 驗證：需要更新平台\n{payload.get('verdict_reason', '')}"
        elif payload.get("verification_note"):
            check = f"\n\n⚠️ 沒有完成二次驗證：{payload['verification_note']}"
        else:
            check = "\n\n（沒有指定驗證員，只有巡查同事的說法）"
        edits = payload.get("edits") or []
        if edits:
            changes = "\n\n建議修改：\n" + "\n".join(f"{n}. {e.get('target', '')}\n   目前：{e.get('current', '')}\n   改成：{e.get('proposed', '')}" for n, e in enumerate(edits[:4], 1))
        else:
            changes = f"\n\n建議更新：{payload['suggested_update']}" if payload.get("suggested_update") else ""
        return f"{payload.get('detail', '')}{check}{changes}\n\n官方來源：{payload.get('source_url') or '（沒有附）'}\n{payload.get('author', '')} 巡查發現"
    if fmt == "reply":
        return f"@{payload.get('username') or '訪客'}：{payload.get('comment_text', '')}\n\n→ {payload.get('text', '')}"
    if draft["channel"] == "threads":
        first = f"\n\n第一則留言：{payload['first_reply']}" if payload.get("first_reply") else ""
        return f"{payload.get('text', '')}{first}"
    if draft["channel"] == "youtube":
        return payload.get("description", "")[:400]
    return payload.get("caption_full") or payload.get("caption") or ""


def notification(draft: dict) -> dict | None:
    """The headline and body a phone shows for a draft in this state; None for states that need no notice."""
    status, proposal = draft["status"], draft["format"] == "data_update"
    name = label(draft)
    if status == "pending_approval":
        return {"title": f"{'📮 資料更新提案等你核准' if proposal else '📝 等你核准'} {name}", "text": f"{draft['title']}\n\n{preview_text(draft)}".strip()}
    if status == "needs_changes":
        issues = "\n".join(f"・{issue}" for issue in ((draft.get("review") or {}).get("issues") or [])[:3])
        return {"title": f"⚠️ 需要你看一下 {name}", "text": f"{draft['title']}\n\n{issues}".strip()}
    if status == "published":
        dry = "（模擬發佈，沒有真的送出）" if draft.get("note") else ""
        head = "📮 draft PR 開好了" if proposal else "🚀 已發出"
        return {"title": f"{head} {name}", "text": f"{draft['title']}\n{draft.get('remote_url') or ''}{dry}".strip()}
    if status == "failed":
        return {"title": f"❌ 發佈失敗 {name}", "text": f"{draft['title']}\n\n{(draft.get('error') or '')[:300]}".strip()}
    return None
