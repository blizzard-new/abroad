from __future__ import annotations

import re

from .ai_gateway import structured_response
from exchange_info.redaction import redact_pii
from .models import DocumentRewriteRequest, DocumentRewriteResult


class DocumentRewriteUnavailable(RuntimeError):
    pass


ACTION_INSTRUCTIONS = {
    "formalize": "調整為適合交換申請文件的正式繁體中文，保留原意與第一人稱語氣。",
    "translate_en": "翻譯為自然、正式的英文申請文件，不保留中文說明。",
    "shorten": "在不刪除關鍵事實的前提下壓縮內容，優先移除重複與空泛語句。",
    "grammar": "保留原語言與內容，只修正文法、標點、用字和不通順句子。",
}


def rewrite_document(payload: DocumentRewriteRequest) -> DocumentRewriteResult:
    action_instruction = ACTION_INSTRUCTIONS[payload.action]
    word_limit = payload.target_word_limit
    response = structured_response(
        schema_name="application_document_rewrite",
        schema={
            "type": "object",
            "properties": {
                "draft": {"type": "string"},
                "changes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 6,
                },
                "warnings": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 5,
                },
            },
            "required": ["draft", "changes", "warnings"],
            "additionalProperties": False,
        },
        instructions=(
            "你是台灣大學生的交換申請文件編輯助手。"
            f"任務：{action_instruction}"
            "只能改寫使用者提供的內容，不得新增經歷、課程、成績、學校規定、日期、數字或動機。"
            "人名、學校名、課程名、分數及金額必須保留；原文資訊不足或自相矛盾時放入 warnings，不得自行補齊。"
            "changes 只列實際做過的修改，每點簡短。不要在 draft 前後加說明。"
        ),
        input_text=(
            f"文件類型：{payload.document_type}\n"
            f"目標字數：{word_limit if word_limit else '未指定'}\n"
            f"目標學校／情境：{payload.school_context or '未提供'}\n\n"
            f"學生原文：\n{redact_pii(payload.text)}"
        ),
        tier="advanced",
        timeout=50,
    )
    if not isinstance(response, dict):
        raise DocumentRewriteUnavailable("AI 改寫服務目前未啟用或暫時無法連線。")

    draft = str(response.get("draft", "")).strip()
    if len(draft) < 10:
        raise DocumentRewriteUnavailable("AI 沒有產生可用的建議稿，請稍後再試。")
    changes = _clean_rows(response.get("changes"), limit=6)
    warnings = _clean_rows(response.get("warnings"), limit=5)
    if word_limit and _word_count(draft) > word_limit:
        warnings.append(f"建議稿仍超過目標 {word_limit} 字，送出前請再精簡。")
    return DocumentRewriteResult(
        action=payload.action,
        draft=draft[:24_000],
        changes=changes,
        warnings=list(dict.fromkeys(warnings))[:5],
    )


def _clean_rows(value: object, *, limit: int) -> list[str]:
    if not isinstance(value, list):
        return []
    return [
        re.sub(r"\s+", " ", str(item)).strip()[:300]
        for item in value[:limit]
        if str(item).strip()
    ]


def _word_count(text: str) -> int:
    latin_words = re.findall(r"[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*", text)
    chinese_chars = re.findall(r"[\u3400-\u9fff]", text)
    return len(latin_words) + len(chinese_chars)
