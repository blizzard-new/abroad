"""CGU edition of the existing UniWay platform, in a dedicated demo process."""
from __future__ import annotations

from abc import ABC, abstractmethod
import copy
from datetime import datetime, timedelta, timezone
from email import policy
from email.parser import BytesParser
import hashlib
import html
import json
import os
from pathlib import Path
import re
import secrets
import sys
import tempfile
import threading
import unicodedata
from contextlib import asynccontextmanager
from typing import Any
from urllib.parse import parse_qsl, quote, urlencode, urlsplit

from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

STATIC = Path(__file__).parent / "static"
CONTENT = Path(__file__).parent / "demo_data/content.json"
COOKIE = "uniway_cgu_demo_session"
HOME = "長庚大學"
SIM_BADGE = "模擬・尚未與校方串接"
UPLOAD_NOTICE = "展示版不保存檔案內容，請勿上傳真實個資"
TAIPEI_TZ = timezone(timedelta(hours=8))

OFFICIAL_REQUIRED_DOCS: list[dict[str, str]] = [
    {"key": "online_form", "title": "線上申請表", "description": "填妥校內交換／雙聯線上申請表（最多 2 個志願）"},
    {"key": "parent_consent", "title": "家長同意書", "description": "依國際處規定格式填寫並經家長／監護人簽章"},
    {"key": "language_proof", "title": "語文證明", "description": "多益 700 分（或同等外語檢定）及合作校規定語文證明"},
    {"key": "transcript", "title": "含排名的中文歷年成績單", "description": "含歷年學業平均與大學部班級排名百分比"},
    {"key": "study_plan", "title": "一頁讀書計畫", "description": "以 1 頁為原則，說明選校動機、修課規劃與預期成果"},
]
REQUIRED_DOC_MAP = {item["key"]: item for item in OFFICIAL_REQUIRED_DOCS}

RETURN_REPORT_SECTIONS: list[dict[str, str]] = [
    {"key": "preparation", "title": "出國前準備"},
    {"key": "academics", "title": "上課情形"},
    {"key": "daily_life", "title": "日常生活"},
    {"key": "extracurricular", "title": "課外活動及其他"},
]
MIN_REPORT_SECTION_CHARS = 300

STOPWORDS = (
    "請問", "想問", "我想問", "可以", "請問一下", "什麼", "怎麼", "如何", "是否", "需要", "嗎", "呢", "的", "了", "在", "有", "跟", "與", "或",
)


class ConnectorValidationError(ValueError):
    """Domain validation error returned as HTTP 422 by demo connector endpoints."""

    def __init__(self, message: str, *, extra: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.extra = extra or {}


def _now_taipei_iso() -> str:
    return datetime.now(TAIPEI_TZ).isoformat(timespec="seconds")


def _count_report_chars(text: str) -> int:
    return len(re.sub(r"\s+", "", str(text or "")))


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", str(text or "")).lower()
    return re.sub(r"[\s,.;:!?，。！？、；：「」『』（）()\[\]【】/\\·\-]+", "", normalized)


def _extract_auto_keywords(question: str) -> list[str]:
    cleaned = unicodedata.normalize("NFKC", str(question or "")).strip()
    for stop in STOPWORDS:
        cleaned = cleaned.replace(stop, " ")
    tokens = re.findall(r"[\u4e00-\u9fff]{2,6}|[a-zA-Z0-9]{2,20}", cleaned)
    seen: list[str] = []
    for tok in tokens:
        low = tok.lower()
        if len(low) >= 2 and low not in seen:
            seen.append(low)
    if not seen and question.strip():
        seen.append(_normalize_text(question)[:12])
    return seen[:8]


def _safe_external_url(raw: str) -> str:
    val = str(raw or "").strip()
    if not val:
        return ""
    parsed = urlsplit(val)
    if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password:
        raise ConnectorValidationError("影片網址僅支援 http:// 或 https:// 開頭之公開連結。")
    return val[:500]


def _parse_multipart_upload(content_type: str, body: bytes) -> tuple[str, str, str, bytes]:
    """Parse multipart/form-data strictly in memory so uploaded bytes never touch disk."""
    if not content_type.lower().startswith("multipart/form-data") or "boundary=" not in content_type.lower():
        raise ConnectorValidationError("請使用 multipart/form-data 選擇檔案。")
    header_bytes = f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("utf-8")
    msg = BytesParser(policy=policy.HTTP).parsebytes(header_bytes + body)
    if not msg.is_multipart():
        raise ConnectorValidationError("無效的檔案表單格式。")
    doc_key = ""
    filename = ""
    part_mime = "application/octet-stream"
    file_bytes: bytes | None = None
    for part in msg.iter_parts():
        if part.get_content_disposition() != "form-data":
            continue
        field_name = part.get_param("name", header="content-disposition") or ""
        part_filename = part.get_filename()
        payload_bytes = part.get_payload(decode=True) or b""
        if part_filename is not None or field_name == "file":
            filename = Path(str(part_filename or "document.bin")).name[:120] or "document.bin"
            part_mime = (part.get_content_type() or "application/octet-stream")[:100]
            file_bytes = payload_bytes
        elif field_name == "doc_key":
            doc_key = payload_bytes.decode("utf-8", errors="replace").strip()
    if not doc_key:
        raise ConnectorValidationError("缺少文件項目代碼（doc_key）。")
    if file_bytes is None or len(file_bytes) == 0:
        raise ConnectorValidationError("請選擇非空白檔案。")
    return doc_key, filename, part_mime, file_bytes


class SchoolConnector(ABC):
    """School integration contract. Replace MockCguConnector with a real API client when authorized."""

    @abstractmethod
    def submit_application(self, workspace_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Submit an internal exchange/dual-degree application after 5-document precheck."""

    @abstractmethod
    def send_inquiry(self, workspace_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Send a student question to the school OIA inquiry queue."""

    @abstractmethod
    def submit_return_report(self, workspace_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Submit a 4-section semester return report for OIA review."""

    @abstractmethod
    def get_status(self, workspace_id: str, receipt_id: str | None = None) -> dict[str, Any]:
        """Query application/inquiry/return-report status and notifications."""


class MockCguConnector(SchoolConnector):
    """Isolated demo implementation storing synthetic state inside the disposable demo workspace."""

    def __init__(self, storage_dir: Path, content_path: Path = CONTENT) -> None:
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.content_path = Path(content_path)
        self._lock = threading.RLock()
        self._content_cache: dict[str, Any] | None = None

    def _content(self) -> dict[str, Any]:
        if self._content_cache is None:
            self._content_cache = json.loads(self.content_path.read_text(encoding="utf-8"))
        return self._content_cache

    def _sources_by_id(self) -> dict[str, dict[str, str]]:
        return {row["id"]: row for row in self._content().get("sources", [])}

    def _workspace_path(self, workspace_id: str) -> Path:
        if not workspace_id:
            raise ConnectorValidationError("缺少有效展示工作區識別。")
        digest = hashlib.sha256(workspace_id.encode("utf-8")).hexdigest()[:28]
        return self.storage_dir / f"{digest}.json"

    def _initial_state(self) -> dict[str, Any]:
        seed = copy.deepcopy(self._content().get("oia_seed", {}))
        return {
            "sequence": 1001,
            "draft_files": {},
            "applications": seed.get("applications", []),
            "inquiries": seed.get("inquiries", []),
            "return_reports": seed.get("return_reports", []),
            "custom_faqs": [],
            "question_counts": seed.get("question_history", []),
            "notifications": [],
        }

    def _load(self, workspace_id: str) -> dict[str, Any]:
        path = self._workspace_path(workspace_id)
        if not path.exists():
            state = self._initial_state()
            self._save(workspace_id, state)
            return state
        return json.loads(path.read_text(encoding="utf-8"))

    def _save(self, workspace_id: str, state: dict[str, Any]) -> None:
        path = self._workspace_path(workspace_id)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)

    def _next_receipt(self, state: dict[str, Any], kind: str) -> str:
        seq = int(state.get("sequence", 1001))
        state["sequence"] = seq + 1
        return f"SIM-{kind}-{seq:04d}"

    def _push_notification(
        self,
        state: dict[str, Any],
        *,
        receipt_id: str,
        title: str,
        body: str,
        action_url: str = "#my-application",
    ) -> dict[str, Any]:
        item = {
            "id": f"sim-notif-{secrets.token_hex(6)}",
            "kind": "cgu_oia_sim",
            "badge": SIM_BADGE,
            "receipt_id": receipt_id,
            "title": title,
            "body": body,
            "action_url": action_url,
            "reminder_days": 0,
            "created_at": _now_taipei_iso(),
            "read_at": None,
        }
        state.setdefault("notifications", []).insert(0, item)
        return item

    def _bump_question_topic(self, state: dict[str, Any], topic: str) -> None:
        clean = str(topic or "").strip()[:80]
        if not clean:
            return
        rows = state.setdefault("question_counts", [])
        for row in rows:
            if row.get("topic") == clean:
                row["count"] = int(row.get("count", 0)) + 1
                return
        rows.append({"topic": clean, "count": 1})

    @staticmethod
    def _sanitize_doc_meta(doc_key: str, meta: dict[str, Any]) -> dict[str, Any]:
        if doc_key not in REQUIRED_DOC_MAP:
            raise ConnectorValidationError(f"未知的應備文件項目：{doc_key}")
        sha = str(meta.get("sha256") or "").strip().lower()
        if not re.fullmatch(r"[0-9a-f]{64}", sha):
            raise ConnectorValidationError("檔案 SHA-256 格式不正確。")
        size = int(meta.get("size") or 0)
        if size <= 0:
            raise ConnectorValidationError("檔案大小必須大於 0 位元組。")
        # Explicitly whitelist ONLY metadata keys; never persist raw content/bytes.
        return {
            "doc_key": doc_key,
            "doc_title": REQUIRED_DOC_MAP[doc_key]["title"],
            "filename": Path(str(meta.get("filename") or f"{doc_key}.pdf")).name[:120],
            "size": size,
            "content_type": str(meta.get("content_type") or "application/octet-stream")[:100],
            "sha256": sha,
            "uploaded_at": str(meta.get("uploaded_at") or _now_taipei_iso()),
        }

    def record_file_metadata(
        self,
        workspace_id: str,
        *,
        doc_key: str,
        filename: str,
        size: int,
        content_type: str,
        sha256: str,
    ) -> dict[str, Any]:
        with self._lock:
            state = self._load(workspace_id)
            record = self._sanitize_doc_meta(
                doc_key,
                {
                    "filename": filename,
                    "size": size,
                    "content_type": content_type,
                    "sha256": sha256,
                    "uploaded_at": _now_taipei_iso(),
                },
            )
            state.setdefault("draft_files", {})[doc_key] = record
            self._save(workspace_id, state)
            return {"badge": SIM_BADGE, "notice": UPLOAD_NOTICE, "file": record, "precheck": self._build_precheck(state["draft_files"])}

    def remove_file_metadata(self, workspace_id: str, doc_key: str) -> dict[str, Any]:
        if doc_key not in REQUIRED_DOC_MAP:
            raise ConnectorValidationError(f"未知的應備文件項目：{doc_key}")
        with self._lock:
            state = self._load(workspace_id)
            state.setdefault("draft_files", {}).pop(doc_key, None)
            self._save(workspace_id, state)
            return {"badge": SIM_BADGE, "removed": doc_key, "precheck": self._build_precheck(state["draft_files"])}

    def _build_precheck(self, files_map: dict[str, dict[str, Any]]) -> dict[str, Any]:
        provided = [files_map[d["key"]] for d in OFFICIAL_REQUIRED_DOCS if d["key"] in files_map]
        missing = [d for d in OFFICIAL_REQUIRED_DOCS if d["key"] not in files_map]
        return {
            "complete": len(missing) == 0,
            "required_count": len(OFFICIAL_REQUIRED_DOCS),
            "provided_count": len(provided),
            "required_documents": OFFICIAL_REQUIRED_DOCS,
            "provided_documents": provided,
            "missing_documents": missing,
        }

    def submit_application(self, workspace_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            state = self._load(workspace_id)
            merged_files = dict(state.get("draft_files", {}))
            incoming_docs = payload.get("documents")
            if isinstance(incoming_docs, dict):
                for key, val in incoming_docs.items():
                    if isinstance(val, dict):
                        merged_files[key] = self._sanitize_doc_meta(key, val)
            elif isinstance(incoming_docs, list):
                for val in incoming_docs:
                    if isinstance(val, dict) and val.get("doc_key"):
                        merged_files[str(val["doc_key"])] = self._sanitize_doc_meta(str(val["doc_key"]), val)

            precheck = self._build_precheck(merged_files)
            if not precheck["complete"]:
                missing_titles = "、".join(item["title"] for item in precheck["missing_documents"])
                raise ConnectorValidationError(
                    f"完整性預檢未通過，尚缺 {len(precheck['missing_documents'])} 項文件：{missing_titles}",
                    extra={"missing_documents": precheck["missing_documents"], "precheck": precheck},
                )

            pref1 = str(payload.get("preference_1") or "林肯大學 Lincoln University").strip()[:160]
            pref2 = str(payload.get("preference_2") or "").strip()[:160]
            if not pref1:
                raise ConnectorValidationError("請至少選擇第一志願合作校。")
            if pref2 and pref2 == pref1:
                raise ConnectorValidationError("第一志願與第二志願不可重複選擇同一所學校。")

            now_iso = _now_taipei_iso()
            receipt_id = self._next_receipt(state, "APP")
            record = {
                "receipt_id": receipt_id,
                "badge": SIM_BADGE,
                "owner": "student",
                "is_fictional": True,
                "fictional_label": "展示模擬送件",
                "student_name": "林小程（展示資料）",
                "department": "工學院・生物醫學工程學系 大三",
                "academic_year": str(payload.get("academic_year") or "116")[:12],
                "semester": str(payload.get("semester") or "116-1（2027 秋季出國）")[:40],
                "preference_1": pref1,
                "preference_2": pref2,
                "status": "submitted",
                "status_label": "已送出",
                "supplement_reason": "",
                "submitted_at": now_iso,
                "documents": [merged_files[d["key"]] for d in OFFICIAL_REQUIRED_DOCS],
                "timeline": [
                    {"step": "submitted", "label": "已送出", "state": "done", "at": now_iso, "note": "已完成 5 項官方文件預檢並送出模擬申請"},
                    {"step": "received", "label": "已收件", "state": "pending", "at": None, "note": "待國際處承辦確認收件"},
                    {"step": "review_result", "label": "要求補件／初審通過", "state": "pending", "at": None, "note": "待國際處承辦初審檢核"},
                ],
            }
            state["draft_files"] = merged_files
            state.setdefault("applications", []).insert(0, record)
            self._save(workspace_id, state)
            return record

    def search_faq(self, workspace_id: str, question: str) -> list[dict[str, Any]]:
        q_raw = str(question or "").strip()
        q_norm = _normalize_text(q_raw)
        if len(q_norm) < 2:
            raise ConnectorValidationError("請輸入至少 2 個字的問題內容。")

        sources = self._sources_by_id()
        content = self._content()
        with self._lock:
            state = self._load(workspace_id)
            candidates: list[dict[str, Any]] = []
            for item in state.get("custom_faqs", []):
                candidates.append(item)
            for faq in content.get("faqs", []):
                src = sources.get(faq.get("source", ""), {})
                candidates.append({
                    "id": faq["id"],
                    "topic": faq.get("topic") or faq["question"],
                    "question": faq["question"],
                    "keywords": faq.get("keywords", []),
                    "answer": faq["answer"],
                    "source_title": src.get("title", "長庚國際事務處公開公告"),
                    "source_url": src.get("url", "https://www.cgu.edu.tw/oia-ch/Contents?nodeId=15656"),
                })
            for idx, rule in enumerate(content.get("rules", []), 1):
                src = sources.get(rule.get("source", ""), {})
                candidates.append({
                    "id": f"rule-{idx}",
                    "topic": rule["title"],
                    "question": rule["title"],
                    "keywords": _extract_auto_keywords(rule["title"]),
                    "answer": rule["body"],
                    "source_title": src.get("title", "長庚國際事務處公開公告"),
                    "source_url": src.get("url", "https://www.cgu.edu.tw/oia-ch/Contents?nodeId=15656"),
                })

            matches: list[dict[str, Any]] = []
            seen_ids: set[str] = set()
            for cand in candidates:
                matched_kw = []
                for kw in cand.get("keywords", []):
                    kw_norm = _normalize_text(kw)
                    if kw_norm and (kw_norm in q_norm or (len(q_norm) >= 2 and q_norm in kw_norm)):
                        matched_kw.append(kw)
                if matched_kw and cand["id"] not in seen_ids:
                    seen_ids.add(cand["id"])
                    matches.append({
                        "id": cand["id"],
                        "topic": cand["topic"],
                        "question": cand["question"],
                        "answer": cand["answer"],
                        "source_title": cand["source_title"],
                        "source_url": cand["source_url"],
                        "matched_keywords": matched_kw,
                        "match_mode": "規則式比對，非 AI",
                        "score": len(matched_kw),
                    })
            matches.sort(key=lambda r: r["score"], reverse=True)
            if matches:
                self._bump_question_topic(state, matches[0]["topic"])
                self._save(workspace_id, state)
            return matches[:3]

    def send_inquiry(self, workspace_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        question = str(payload.get("question") or "").strip()
        if len(_normalize_text(question)) < 2:
            raise ConnectorValidationError("請輸入具體詢問內容（至少 2 個字）。")
        if len(question) > 1000:
            raise ConnectorValidationError("詢問內容請控制在 1,000 字以內。")
        with self._lock:
            state = self._load(workspace_id)
            now_iso = _now_taipei_iso()
            receipt_id = self._next_receipt(state, "INQ")
            topic = str(payload.get("topic") or question[:28]).strip()
            record = {
                "receipt_id": receipt_id,
                "badge": SIM_BADGE,
                "owner": "student",
                "is_fictional": True,
                "fictional_label": "展示模擬詢問",
                "student_name": "林小程（展示資料）",
                "department": "工學院・生物醫學工程學系 大三",
                "topic": topic,
                "question": question,
                "escalated_from_faq": bool(payload.get("escalated_from_faq", False)),
                "matched_faq_ids": [str(x) for x in (payload.get("matched_faq_ids") or [])][:5],
                "status": "pending",
                "status_label": "待承辦回覆",
                "created_at": now_iso,
                "reply": "",
                "replied_at": None,
                "added_to_faq": False,
            }
            self._bump_question_topic(state, topic)
            state.setdefault("inquiries", []).insert(0, record)
            self._save(workspace_id, state)
            return record

    def ask_or_inquire(self, workspace_id: str, question: str, *, force_inquiry: bool = False) -> dict[str, Any]:
        if force_inquiry:
            inquiry = self.send_inquiry(workspace_id, {"question": question, "escalated_from_faq": True})
            return {
                "badge": SIM_BADGE,
                "mode_label": "規則式比對，非 AI",
                "matched": False,
                "matches": [],
                "inquiry": inquiry,
            }
        matches = self.search_faq(workspace_id, question)
        if matches:
            return {
                "badge": SIM_BADGE,
                "mode_label": "規則式比對，非 AI",
                "matched": True,
                "matches": matches,
                "inquiry": None,
            }
        inquiry = self.send_inquiry(workspace_id, {"question": question, "escalated_from_faq": False})
        return {
            "badge": SIM_BADGE,
            "mode_label": "規則式比對，非 AI",
            "matched": False,
            "matches": [],
            "inquiry": inquiry,
        }

    def submit_return_report(self, workspace_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        partner_school = str(payload.get("partner_school") or "").strip()[:160]
        if not partner_school:
            raise ConnectorValidationError("請選擇研修合作校。")
        raw_sections = payload.get("sections")
        if not isinstance(raw_sections, dict):
            raise ConnectorValidationError("請填寫學期報告表四段內容。")

        clean_sections: dict[str, str] = {}
        char_counts: dict[str, int] = {}
        short_sections: list[dict[str, Any]] = []
        for sec in RETURN_REPORT_SECTIONS:
            key = sec["key"]
            val = str(raw_sections.get(key) or "").strip()
            if len(val) > 8000:
                raise ConnectorValidationError(f"「{sec['title']}」字數超過單段上限。")
            cnt = _count_report_chars(val)
            clean_sections[key] = val
            char_counts[key] = cnt
            if cnt < MIN_REPORT_SECTION_CHARS:
                short_sections.append({"key": key, "title": sec["title"], "count": cnt, "required": MIN_REPORT_SECTION_CHARS})

        if short_sections:
            summary = "、".join(f"{s['title']}（目前 {s['count']} 字，需滿 {MIN_REPORT_SECTION_CHARS} 字）" for s in short_sections)
            raise ConnectorValidationError(f"返國心得四段每段均須至少 {MIN_REPORT_SECTION_CHARS} 字：{summary}", extra={"short_sections": short_sections})

        video_url = _safe_external_url(str(payload.get("video_url") or ""))
        public_consent = bool(payload.get("public_consent", False))
        term = str(payload.get("term") or "116-1（2027 秋季）").strip()[:40]
        author_title = str(payload.get("author_title") or "工學院・生物醫學工程學系（示範資料）").strip()[:80]

        with self._lock:
            state = self._load(workspace_id)
            now_iso = _now_taipei_iso()
            receipt_id = self._next_receipt(state, "RPT")
            record = {
                "receipt_id": receipt_id,
                "badge": SIM_BADGE,
                "owner": "student",
                "is_fictional": True,
                "fictional_label": "展示模擬心得",
                "student_name": "林小程（展示資料）",
                "author_title": author_title,
                "partner_school": partner_school,
                "term": term,
                "sections": clean_sections,
                "char_counts": char_counts,
                "video_url": video_url,
                "public_consent": public_consent,
                "status": "pending_review",
                "status_label": "待審核",
                "published": False,
                "print_url": f"/demo/connector/return-reports/{receipt_id}/print",
                "submitted_at": now_iso,
                "approved_at": None,
            }
            state.setdefault("return_reports", []).insert(0, record)
            self._save(workspace_id, state)
            return record

    def get_return_report(self, workspace_id: str, receipt_id: str) -> dict[str, Any] | None:
        with self._lock:
            state = self._load(workspace_id)
            for item in state.get("return_reports", []):
                if item.get("receipt_id") == receipt_id:
                    return item
            return None

    def get_status(self, workspace_id: str, receipt_id: str | None = None) -> dict[str, Any]:
        with self._lock:
            state = self._load(workspace_id)
            if receipt_id:
                for collection in ("applications", "inquiries", "return_reports"):
                    for item in state.get(collection, []):
                        if item.get("receipt_id") == receipt_id:
                            return {"badge": SIM_BADGE, "collection": collection, "record": item}
                raise HTTPException(status_code=404, detail=f"找不到收件編號 {receipt_id}")

            notifications = state.get("notifications", [])
            unread = sum(1 for n in notifications if not n.get("read_at"))
            return {
                "badge": SIM_BADGE,
                "upload_notice": UPLOAD_NOTICE,
                "precheck": self._build_precheck(state.get("draft_files", {})),
                "draft_files": state.get("draft_files", {}),
                "applications": [a for a in state.get("applications", []) if a.get("owner") == "student"],
                "inquiries": [i for i in state.get("inquiries", []) if i.get("owner") == "student"],
                "return_reports": [r for r in state.get("return_reports", []) if r.get("owner") == "student"],
                "notifications": notifications,
                "unread_count": unread,
            }

    def get_oia_dashboard(self, workspace_id: str) -> dict[str, Any]:
        with self._lock:
            state = self._load(workspace_id)
            apps = state.get("applications", [])
            inqs = state.get("inquiries", [])
            rpts = state.get("return_reports", [])

            pref_counts: dict[str, int] = {}
            for app_row in apps:
                for key in ("preference_1", "preference_2"):
                    school = str(app_row.get(key) or "").strip()
                    if school:
                        pref_counts[school] = pref_counts.get(school, 0) + 1
            school_preferences = [
                {"school": k, "count": v}
                for k, v in sorted(pref_counts.items(), key=lambda kv: (-kv[1], kv[0]))
            ]
            missing_count = sum(1 for a in apps if a.get("status") == "supplement_requested")
            top_questions = sorted(
                state.get("question_counts", []),
                key=lambda row: (-int(row.get("count", 0)), str(row.get("topic", ""))),
            )[:5]
            seed_count = (
                sum(1 for a in apps if a.get("owner") == "seed")
                + sum(1 for i in inqs if i.get("owner") == "seed")
                + sum(1 for r in rpts if r.get("owner") == "seed")
            )
            return {
                "badge": SIM_BADGE,
                "seed_count": seed_count,
                "stats": {
                    "school_preferences": school_preferences,
                    "missing_count": missing_count,
                    "top_questions": top_questions,
                },
                "inboxes": {
                    "applications": apps,
                    "inquiries": inqs,
                    "return_reports": rpts,
                },
                "custom_faqs": state.get("custom_faqs", []),
            }

    def oia_action(self, workspace_id: str, action: str, receipt_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            state = self._load(workspace_id)
            now_iso = _now_taipei_iso()

            if action in ("confirm_receipt", "request_supplement", "approve_initial"):
                target = next((a for a in state.get("applications", []) if a.get("receipt_id") == receipt_id), None)
                if target is None:
                    raise HTTPException(status_code=404, detail=f"找不到申請案件 {receipt_id}")
                timeline = target.setdefault("timeline", [])
                recv_step = next((s for s in timeline if s.get("step") == "received"), None)
                rev_step = next((s for s in timeline if s.get("step") == "review_result"), None)

                if action == "confirm_receipt":
                    target["status"] = "received"
                    target["status_label"] = "已收件"
                    if recv_step:
                        recv_step.update(state="done", at=now_iso, note="國際處承辦已確認收件（模擬）")
                    notif = self._push_notification(
                        state,
                        receipt_id=receipt_id,
                        title=f"【模擬・國際處】申請案件 {receipt_id} 已確認收件",
                        body=f"志願「{target['preference_1']}」校內申請已由承辦確認收件，進入初審階段。",
                        action_url="#my-application",
                    )
                elif action == "request_supplement":
                    reason = str(payload.get("reason") or "").strip()[:400]
                    if not reason:
                        raise ConnectorValidationError("請填寫要求補件原因。")
                    target["status"] = "supplement_requested"
                    target["status_label"] = "要求補件"
                    target["supplement_reason"] = reason
                    if recv_step and recv_step.get("state") != "done":
                        recv_step.update(state="done", at=now_iso, note="國際處承辦已收件檢核")
                    if rev_step:
                        rev_step.update(label="要求補件", state="warning", at=now_iso, note=f"要求補件：{reason}")
                    notif = self._push_notification(
                        state,
                        receipt_id=receipt_id,
                        title=f"【模擬・要求補件】申請案件 {receipt_id} 需補件",
                        body=f"承辦補件說明：{reason}",
                        action_url="#my-application",
                    )
                else:  # approve_initial
                    target["status"] = "passed_initial"
                    target["status_label"] = "初審通過"
                    target["supplement_reason"] = ""
                    if recv_step and recv_step.get("state") != "done":
                        recv_step.update(state="done", at=now_iso, note="國際處承辦已確認收件")
                    if rev_step:
                        rev_step.update(label="初審通過", state="done", at=now_iso, note="初審文件檢核通過（模擬）")
                    notif = self._push_notification(
                        state,
                        receipt_id=receipt_id,
                        title=f"【模擬・初審通過】申請案件 {receipt_id} 初審通過",
                        body=f"志願「{target['preference_1']}」已完成模擬初審檢核。",
                        action_url="#my-application",
                    )
                self._save(workspace_id, state)
                return {"badge": SIM_BADGE, "record": target, "notification": notif}

            if action in ("reply_inquiry", "add_to_faq"):
                target = next((i for i in state.get("inquiries", []) if i.get("receipt_id") == receipt_id), None)
                if target is None:
                    raise HTTPException(status_code=404, detail=f"找不到詢問單 {receipt_id}")

                if action == "reply_inquiry":
                    reply = str(payload.get("reply") or "").strip()[:1500]
                    if not reply:
                        raise ConnectorValidationError("請輸入回覆內容。")
                    target["status"] = "replied"
                    target["status_label"] = "已回覆"
                    target["reply"] = reply
                    target["replied_at"] = now_iso
                    notif = self._push_notification(
                        state,
                        receipt_id=receipt_id,
                        title=f"【模擬・承辦回覆】詢問單 {receipt_id} 已獲回覆",
                        body=reply,
                        action_url="#ask-oia",
                    )
                    if payload.get("add_to_faq"):
                        self._upsert_custom_faq(state, target, payload.get("keywords"))
                    self._save(workspace_id, state)
                    return {"badge": SIM_BADGE, "record": target, "notification": notif}

                # action == "add_to_faq"
                reply = str(payload.get("reply") or target.get("reply") or "").strip()[:1500]
                if not reply:
                    raise ConnectorValidationError("請先填寫回覆內容，再加入 FAQ。")
                if not target.get("reply"):
                    target["reply"] = reply
                    target["status"] = "replied"
                    target["status_label"] = "已回覆"
                    target["replied_at"] = now_iso
                faq_item = self._upsert_custom_faq(state, target, payload.get("keywords"))
                notif = self._push_notification(
                    state,
                    receipt_id=receipt_id,
                    title=f"【模擬・FAQ 更新】詢問單 {receipt_id} 已整理納入常見問答",
                    body=f"問題「{target['question'][:40]}」之承辦回覆已加入工作區 FAQ 規則庫。",
                    action_url="#ask-oia",
                )
                self._save(workspace_id, state)
                return {"badge": SIM_BADGE, "record": target, "faq": faq_item, "notification": notif}

            if action == "approve_report":
                target = next((r for r in state.get("return_reports", []) if r.get("receipt_id") == receipt_id), None)
                if target is None:
                    raise HTTPException(status_code=404, detail=f"找不到返國心得 {receipt_id}")
                target["status"] = "approved"
                target["approved_at"] = now_iso
                target["published"] = bool(target.get("public_consent"))
                target["status_label"] = "已核可公開" if target["published"] else "已核可（學生未勾選公開）"
                action_url = f"#school={quote(target['partner_school'])}" if target["published"] else "#return-report"
                notif = self._push_notification(
                    state,
                    receipt_id=receipt_id,
                    title=f"【模擬・心得審核】返國心得 {receipt_id} 已核可",
                    body=(
                        f"「{target['partner_school']}」返國心得已核可並顯示於合作校詳細頁「學長姐心得（示範資料）」。"
                        if target["published"]
                        else f"「{target['partner_school']}」返國心得已核可結案（因未勾選同意公開，不對外顯示）。"
                    ),
                    action_url=action_url,
                )
                self._save(workspace_id, state)
                return {"badge": SIM_BADGE, "record": target, "notification": notif}

            raise ConnectorValidationError(f"不支援的承辦操作：{action}")

    def _upsert_custom_faq(self, state: dict[str, Any], inquiry: dict[str, Any], raw_keywords: Any = None) -> dict[str, Any]:
        if isinstance(raw_keywords, list) and raw_keywords:
            keywords = [str(k).strip() for k in raw_keywords if str(k).strip()][:10]
        elif isinstance(raw_keywords, str) and raw_keywords.strip():
            keywords = [k.strip() for k in re.split(r"[,，、\s]+", raw_keywords) if k.strip()][:10]
        else:
            keywords = _extract_auto_keywords(inquiry["question"])
        faq_id = f"faq-custom-{inquiry['receipt_id'].lower()}"
        faq_entry = {
            "id": faq_id,
            "topic": inquiry.get("topic") or inquiry["question"][:28],
            "question": inquiry["question"],
            "keywords": keywords,
            "answer": inquiry["reply"],
            "source_title": "長庚國際事務處｜校內申請選送須知（模擬承辦收錄 FAQ）",
            "source_url": "https://www.cgu.edu.tw/oia-ch/Contents?nodeId=15656",
        }
        custom_list = state.setdefault("custom_faqs", [])
        existing_idx = next((idx for idx, x in enumerate(custom_list) if x.get("id") == faq_id), None)
        if existing_idx is not None:
            custom_list[existing_idx] = faq_entry
        else:
            custom_list.insert(0, faq_entry)
        inquiry["added_to_faq"] = True
        return faq_entry

    def list_public_reports(self, workspace_id: str, school_name: str | None = None) -> list[dict[str, Any]]:
        with self._lock:
            state = self._load(workspace_id)
            approved = [
                r for r in state.get("return_reports", [])
                if r.get("status") == "approved" and r.get("public_consent") is True and r.get("published") is True
            ]
            if not school_name:
                return approved
            q_norm = _normalize_text(school_name)
            matched = []
            for r in approved:
                p_norm = _normalize_text(r.get("partner_school", ""))
                if p_norm and (p_norm == q_norm or q_norm in p_norm or p_norm in q_norm):
                    matched.append(r)
            return matched

    def mark_notification_read(self, workspace_id: str, notification_id: str) -> dict[str, Any] | None:
        with self._lock:
            state = self._load(workspace_id)
            for item in state.get("notifications", []):
                if item.get("id") == notification_id:
                    if not item.get("read_at"):
                        item["read_at"] = _now_taipei_iso()
                    self._save(workspace_id, state)
                    return item
            return None

    def mark_all_notifications_read(self, workspace_id: str) -> list[dict[str, Any]]:
        with self._lock:
            state = self._load(workspace_id)
            now_iso = _now_taipei_iso()
            for item in state.get("notifications", []):
                if not item.get("read_at"):
                    item["read_at"] = now_iso
            self._save(workspace_id, state)
            return state.get("notifications", [])

    def delete_notification(self, workspace_id: str, notification_id: str) -> bool:
        with self._lock:
            state = self._load(workspace_id)
            before = len(state.get("notifications", []))
            state["notifications"] = [n for n in state.get("notifications", []) if n.get("id") != notification_id]
            changed = len(state["notifications"]) != before
            if changed:
                self._save(workspace_id, state)
            return changed

    def clear_notifications(self, workspace_id: str) -> None:
        with self._lock:
            state = self._load(workspace_id)
            state["notifications"] = []
            self._save(workspace_id, state)

    def reset_workspace(self, workspace_id: str) -> None:
        with self._lock:
            path = self._workspace_path(workspace_id)
            if path.exists():
                path.unlink()


HERO_ONEPAGER_HTML = """
<div id="cgu-hero-onepager" class="cgu-hero-onepager" aria-label="長庚 116-1 校內申請重點總覽">
  <div class="cgu-onepager-grid">
    <article class="cgu-onepager-card is-highlight">
      <span class="cgu-onepager-kicker">校內申請期間</span>
      <strong>11/02–12/21 17:00</strong>
      <p>2026/11/02 開放線上表單，12/21 17:00 截止；紙本資料須於截止日前繳交國際事務處（預計 2027 秋季出國）。</p>
    </article>
    <article class="cgu-onepager-card">
      <span class="cgu-onepager-kicker">校內基本門檻</span>
      <strong>學業平均 70 分、多益 700</strong>
      <p>英文可採多益 700、IELTS 5.5、TOEFL iBT 72 或 Duolingo 105 等同級檢定；合作校門檻更高或未列多益者依該校規定。</p>
    </article>
    <article class="cgu-onepager-card">
      <span class="cgu-onepager-kicker">志願數與甄選流程</span>
      <strong>最多 2 個志願</strong>
      <div class="cgu-flow-steps" aria-label="申請流程">
        <span>校內甄選</span><i aria-hidden="true">→</i><span>學校提名</span><i aria-hidden="true">→</i><span>合作校申請</span>
      </div>
    </article>
    <article class="cgu-onepager-card is-wide">
      <span class="cgu-onepager-kicker">校內應備 5 份文件</span>
      <ol class="cgu-doc-pills">
        <li><b>1</b>線上申請表</li>
        <li><b>2</b>家長同意書</li>
        <li><b>3</b>語文證明</li>
        <li><b>4</b>含班級排名的中文成績單</li>
        <li><b>5</b>1 頁讀書計畫</li>
      </ol>
    </article>
  </div>
  <div class="cgu-onepager-foot">
    <div class="cgu-onepager-sources">
      <span>官方來源：</span>
      <a href="https://www.cgu.edu.tw/oia-ch/Subject/Detail/85785?nodeId=15817" target="_blank" rel="noopener noreferrer">116-1 交換及雙聯申請公告 ↗</a>
      <span aria-hidden="true">·</span>
      <a href="https://www.cgu.edu.tw/oia-ch/Contents?nodeId=15656" target="_blank" rel="noopener noreferrer">校內申請選送須知 ↗</a>
      <small>查核日期：2026-11-11</small>
    </div>
    <div class="cgu-onepager-actions">
      <button type="button" class="cgu-hero-cta is-primary" data-cgu-scroll="#cgu-dept-finder">我是哪個系？（36 系所）</button>
      <a class="cgu-hero-cta" href="#partners">搜尋 78 所合作校</a>
      <button type="button" class="cgu-hero-cta" data-cgu-scroll="#cgu-navigator-card">領航者補助說明</button>
    </div>
  </div>
</div>
"""

PRINT_SCRIPT_JS = """(() => {
  'use strict';
  const btn = document.getElementById('cgu-print-trigger');
  if (btn) btn.addEventListener('click', () => window.print());
})();
"""


def _render_report_print_html(report: dict[str, Any]) -> str:
    e = html.escape
    sections_html = []
    for idx, sec in enumerate(RETURN_REPORT_SECTIONS, 1):
        body_text = str(report.get("sections", {}).get(sec["key"], ""))
        cnt = _count_report_chars(body_text)
        paragraphs = "".join(f"<p>{e(line)}</p>" for line in body_text.splitlines() if line.strip()) or f"<p>{e(body_text)}</p>"
        sections_html.append(
            f"<section class='cgu-print-sec'><h2>{idx}. {e(sec['title'])} <small>（{cnt} 字）</small></h2>{paragraphs}</section>"
        )
    video = str(report.get("video_url") or "").strip()
    video_row = f"<a href='{e(video)}' target='_blank' rel='noopener noreferrer'>{e(video)}</a>" if video else "未填寫（展示版不上傳影片檔案）"
    consent_text = "已勾選同意公開給學弟妹" if report.get("public_consent") else "未勾選公開（僅供承辦審核結案）"
    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="robots" content="noindex,nofollow,noarchive" />
  <title>返國學期報告列印版｜{e(report.get('receipt_id', ''))}</title>
  <link rel="stylesheet" href="/static/cgu-demo.css?v=20261112-cgu-sim-1" />
</head>
<body class="cgu-print-body">
  <main class="cgu-print-sheet">
    <header class="cgu-print-header">
      <div class="cgu-print-badges">
        <span class="cgu-sim-badge">{e(SIM_BADGE)}</span>
        <span class="cgu-fictional-tag">{e(report.get('fictional_label', '展示模擬資料'))}</span>
      </div>
      <h1>長庚大學出國研修返國學期報告表（展示列印版）</h1>
      <p class="cgu-print-note">此列印版僅供展示預覽，尚未與校方串接；實際結案請依國際事務處規定於返國後 2 週內辦理。</p>
      <div class="cgu-print-actions">
        <button type="button" id="cgu-print-trigger" class="cgu-pill-action is-solid">列印／另存 PDF</button>
        <a href="/#return-report" class="cgu-pill-action">返回返國心得頁</a>
      </div>
    </header>
    <table class="cgu-print-meta">
      <tbody>
        <tr><th>模擬收件編號</th><td><strong>{e(report.get('receipt_id', ''))}</strong></td><th>目前審核狀態</th><td>{e(report.get('status_label', ''))}</td></tr>
        <tr><th>研修合作校</th><td>{e(report.get('partner_school', ''))}</td><th>研修學期</th><td>{e(report.get('term', ''))}</td></tr>
        <tr><th>填表人標示</th><td>{e(report.get('author_title', ''))}</td><th>送出時間</th><td>{e(report.get('submitted_at', ''))}</td></tr>
        <tr><th>分享影片網址</th><td>{video_row}</td><th>公開意願</th><td>{e(consent_text)}</td></tr>
      </tbody>
    </table>
    {''.join(sections_html)}
  </main>
  <script src="/demo/print.js" defer></script>
</body>
</html>"""


def public_origin(value: str) -> str:
    """A configured HTTPS origin, never inferred from forwarded request headers."""
    value = value.strip().rstrip('/')
    if not value:
        return ''
    parsed = urlsplit(value)
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password
            or parsed.path or parsed.query or parsed.fragment or parsed.port not in (None, 443)):
        raise ValueError('CGU_DEMO_PUBLIC_ORIGIN must be an HTTPS origin without a path or credentials')
    host = parsed.hostname.lower()
    return 'https://' + ('[' + host + ']' if ':' in host else host)


def platform_html() -> str:
    """Keep the platform DOM and asset order; only constrain school/identity copy."""
    soup = BeautifulSoup((STATIC / "index.html").read_text(encoding="utf-8"), "html.parser")
    soup.title.string = "UniWay CGU｜長庚大學交換申請平台"
    soup.head.append(soup.new_tag("meta", attrs={"name": "robots", "content": "noindex,nofollow,noarchive"}))
    soup.head.append(soup.new_tag("link", rel="stylesheet", href="/static/cgu-demo.css?v=20261112-cgu-sim-1"))
    script = soup.new_tag("script", src="/demo/bootstrap.js")
    soup.head.insert(0, script)
    # Initial static choices must also be CGU-only, before the registry request resolves.
    for item in soup.select('[data-home-school]'):
        if item.get('data-home-school') != HOME:
            item.decompose()
    for item in soup.select('.pr-supported'):
        item.decompose()

    # Hide empty Forum & User Review entrances in CGU demo while keeping underlying nodes intact for shared scripts.
    for selector in (
        '[data-public-route="forum"]',
        '[data-public-route="feedback"]',
        'a[href="#forum"]',
        'a[href="#feedback"]',
        'a[href="#university-posts"]',
        '.global-sidebar-nav',
        '.sidebar-board-list',
        '.pr-forum-preview',
        '#detail-tab-community',
    ):
        for node in soup.select(selector):
            node['hidden'] = ''

    # Add CGU demo navigation links: 問國際處、返國心得、校方介接
    public_nav = soup.select_one('.uniway-public-nav')
    if public_nav is not None:
        nav_snippet = BeautifulSoup(
            '<a href="#ask-oia" data-public-route="ask-oia"><i data-lucide="help-circle" aria-hidden="true"></i><span>問國際處</span></a>'
            '<a href="#return-report" data-public-route="return-report"><i data-lucide="book-open-check" aria-hidden="true"></i><span>返國心得</span></a>'
            '<a href="#school-connector" data-public-route="school-connector"><i data-lucide="plug-zap" aria-hidden="true"></i><span>校方介接</span></a>',
            'html.parser',
        )
        my_app_link = public_nav.select_one('a[href="#my-application"]')
        if my_app_link is not None:
            my_app_link.insert_after(nav_snippet)
        else:
            public_nav.append(nav_snippet)

    sidebar_nav = soup.select_one('.university-sidebar-nav')
    if sidebar_nav is not None:
        side_snippet = BeautifulSoup(
            '<a class="nav-item" href="#ask-oia" data-section="ask-oia" data-requires-home-school><i data-lucide="help-circle" aria-hidden="true"></i><span>問國際處</span></a>'
            '<a class="nav-item" href="#return-report" data-section="return-report" data-requires-home-school><i data-lucide="book-open-check" aria-hidden="true"></i><span>返國心得</span></a>'
            '<a class="nav-item" href="#school-connector" data-section="school-connector"><i data-lucide="plug-zap" aria-hidden="true"></i><span>校方介接</span></a>',
            'html.parser',
        )
        sidebar_nav.append(side_snippet)

    hero_title = soup.select_one('#home-landing-title')
    if hero_title is not None:
        hero_title.clear()
        hero_title.append('長庚 116-1 申請一頁看完')
        hero_title.append(soup.new_tag('br'))
        sub = soup.new_tag('span')
        sub.string = '2027 秋季出國 · 交換與雙學位校內甄選重點'
        hero_title.append(sub)
        banner = soup.new_tag('div', id='cgu-home-deadline-banner', attrs={'class': 'cgu-home-deadline-banner', 'hidden': ''})
        hero_title.insert_after(banner)
        onepager = BeautifulSoup(HERO_ONEPAGER_HTML, 'html.parser')
        banner.insert_after(onepager)
    hero_section = soup.select_one('#home-landing .pr-hero')
    if hero_section is not None:
        navigator_sec = soup.new_tag(
            'section',
            id='cgu-navigator-card',
            attrs={'class': 'pr-section cgu-navigator-section', 'aria-labelledby': 'cgu-navigator-title'},
        )
        dept_sec = soup.new_tag(
            'section',
            id='cgu-dept-finder',
            attrs={'class': 'pr-section cgu-dept-section', 'aria-labelledby': 'cgu-dept-title'},
        )
        hero_section.insert_after(navigator_sec)
        hero_section.insert_after(dept_sec)
    partners_head = soup.select_one('#partners .pr-explore-head')
    if partners_head is not None:
        mgmt_notice = soup.new_tag(
            'div',
            id='cgu-mgmt-channel-notice',
            attrs={'class': 'cgu-mgmt-notice', 'role': 'status', 'hidden': ''},
        )
        college_bar = soup.new_tag(
            'div',
            id='cgu-college-quick-bar',
            attrs={'class': 'cgu-college-bar', 'role': 'region', 'aria-label': '長庚學院快速篩選'},
        )
        program_tabs = soup.new_tag(
            'div',
            id='cgu-program-tabs',
            attrs={'class': 'cgu-program-tabs', 'role': 'tablist', 'aria-label': '交換與雙學位計畫分頁'},
        )
        partners_head.insert_after(mgmt_notice)
        partners_head.insert_after(college_bar)
        partners_head.insert_after(program_tabs)
    scholarship_summary = soup.select_one('#scholarship-match-summary')
    if scholarship_summary is not None:
        inline_nav = soup.new_tag('div', id='cgu-scholarships-navigator-card', attrs={'class': 'cgu-navigator-inline'})
        scholarship_summary.insert_before(inline_nav)

    # Inject simulated student submission panel inside #my-application route and dedicated pages inside #dashboard-view
    app_path_sec = soup.select_one('#application-path')
    if app_path_sec is not None:
        my_app_sim = soup.new_tag(
            'section',
            id='cgu-my-application-sim',
            attrs={
                'class': 'cgu-sim-hub',
                'data-university-page': 'my-application',
                'aria-labelledby': 'cgu-sim-submit-heading',
                'hidden': '',
            },
        )
        app_path_sec.insert_after(my_app_sim)

    dashboard_view = soup.select_one('#dashboard-view')
    if dashboard_view is not None:
        for page_id, sec_id, label in (
            ('school-connector', 'cgu-connector-spec-page', '校方介接規格'),
            ('ask-oia', 'cgu-ask-oia-page', '問國際處（模擬）'),
            ('return-report', 'cgu-return-report-page', '返國心得（模擬）'),
            ('oia-view', 'cgu-oia-console-page', '國際處視角（模擬）'),
        ):
            sec = soup.new_tag(
                'section',
                id=sec_id,
                attrs={
                    'class': 'page-section cgu-sim-page',
                    'data-university-page': page_id,
                    'aria-label': label,
                    'hidden': '',
                },
            )
            dashboard_view.append(sec)

    for legend in soup.select('.application-preference-fields legend'):
        legend.string = '準備志願序（最多兩所；依長庚官方規定）'
    for selector in (
        '#eligibility-preference-3', '#eligibility-preference-4', '#eligibility-preference-5',
        '#multi-plan-preferences select[name="preference_3"]',
        '#multi-plan-preferences select[name="preference_4"]',
        '#multi-plan-preferences select[name="preference_5"]',
    ):
        for field in soup.select(selector):
            parent_label = field.find_parent('label')
            if parent_label is not None:
                parent_label['hidden'] = ''
    term_labels = {
        '2027-spring': '2027 春季（115-2）',
        '2027-fall': '2027 秋季（116-1）',
        '2028-spring': '2028 春季（116-2）',
        '2028-fall': '2028 秋季（117-1）',
    }
    for value, text in term_labels.items():
        for opt in soup.select(f'#advisor-target-term option[value="{value}"]'):
            opt.string = text
    for opt in soup.select('#partner-term-tile option[value="fall"], #discovery-criteria-form select[name="term"] option[value="fall"]'):
        opt.string = '2027 秋季（116-1）'
    for opt in soup.select('#partner-term-tile option[value="spring"], #discovery-criteria-form select[name="term"] option[value="spring"]'):
        opt.string = '2027 春季（115-2）'
    for item in soup.select('.uniway-header-brand strong'):
        item.string = 'UniWay CGU'
    # Replace「切換就讀學校 / 選擇就讀學校」with fixed「長庚大學」display
    for item in soup.select('#school-switcher'):
        item['disabled'] = ''
        item['aria-label'] = '長庚大學'
        for attr in ('aria-haspopup', 'aria-controls', 'aria-expanded'):
            item.attrs.pop(attr, None)
        for small in item.select('small'):
            small.decompose()
        for chev in item.select('[data-lucide="chevron-down"]'):
            chev.decompose()
    for label in soup.select('#school-switcher-label, #mobile-school-label'):
        label.string = HOME
    for item in soup.select('#logout-button, #delete-account-button, #calendar-sync-button, #document-tab-vault, input[type=file]'):
        item['disabled'] = ''
        item['title'] = '展示未開放正式登入、私人文件或外部同步'
    for item in soup.select('[data-home-pick-school]'):
        item['disabled'] = ''
        item['title'] = '長庚大學專屬平台'
    snippet = BeautifulSoup('''<aside id="cgu-demo-strip" aria-label="長庚展示控制">
      <span><strong class="cgu-strip-sim-tag">模擬・尚未與校方串接</strong> 長庚專屬展示・虛構學生林小程（生物醫學工程學系 大三・多益 750）・重啟後清除</span>
      <button type="button" id="cgu-demo-oia-toggle" aria-pressed="false">切換為國際處視角</button>
      <button type="button" id="cgu-demo-info">來源與展示說明</button>
      <button type="button" id="cgu-demo-seed">載入示範申請</button>
      <button type="button" id="cgu-demo-reset">重設我的展示資料</button>
      </aside><dialog id="cgu-demo-dialog" aria-label="長庚專屬展示" aria-labelledby="cgu-demo-dialog-title">
      <h2 id="cgu-demo-dialog-title">長庚專屬展示</h2><div id="cgu-demo-dialog-body"></div>
      <p id="cgu-demo-status" role="status"></p><div class="button-row">
      <button type="button" class="primary-button" id="cgu-demo-confirm" hidden>確認重設</button>
      <button type="button" class="secondary-button" id="cgu-demo-close">關閉</button></div></dialog>''', 'html.parser')
    soup.body.append(snippet)
    soup.body.append(soup.new_tag('script', src='/static/cgu-demo.js?v=20261112-cgu-sim-1', defer=''))
    return str(soup)


def create_demo_app(connector_factory=None) -> FastAPI:
    # The shared module constructs its app on import. Prepare a disposable runtime
    # BEFORE importing it, and refuse use in an already-running normal API process.
    if 'exchange_info.api' in sys.modules:
        raise RuntimeError('CGU demo must run in a separate process; do not mount it in the production app')
    hosted_origin = public_origin(os.environ.get('CGU_DEMO_PUBLIC_ORIGIN', ''))
    if os.environ.get('EXCHANGE_ENVIRONMENT') == 'production' or any(
        value for name, value in os.environ.items()
        if name.startswith(('SUPABASE', 'GOOGLE_OAUTH', 'SMTP_', 'OPENAI_API_KEY'))
    ):
        raise RuntimeError('CGU demo refuses production/service credentials; use an isolated service environment')
    for name in list(os.environ):
        if name.startswith('EXCHANGE_'):
            del os.environ[name]
    runtime = tempfile.TemporaryDirectory(prefix='uniway-cgu-demo-')
    os.environ.update(EXCHANGE_INFO_DATA_DIR=runtime.name, EXCHANGE_ENVIRONMENT='development',
                      EXCHANGE_ANALYTICS='off', EXCHANGE_WARM_CACHES='off', EXCHANGE_AUTH_METHODS='email')
    if hosted_origin:
        os.environ['EXCHANGE_PUBLIC_BASE_URL'] = hosted_origin
    from . import api
    from .cgu_demo_content import FrozenCatalogue, journey_levels, source_dashboard
    from .models import (
        AccountApplicationWorkspace,
        AccountSelectionConditions,
        AccountSelectionProfile,
        AccountSessionRecord,
        ApplicationCenterContext,
        ProductAccessTier,
        UserAccount,
        utc_now,
    )

    runtime_root = Path(runtime.name)
    catalogue = FrozenCatalogue(runtime_root)
    connector: SchoolConnector = (
        connector_factory(runtime_root / 'cgu_connector')
        if connector_factory is not None
        else MockCguConnector(runtime_root / 'cgu_connector', content_path=CONTENT)
    )
    platform = api.create_app(runtime_root, cgu_catalogue_factory=lambda _: catalogue,
                              application_path_levels=journey_levels, fetch_dashboard_documents=False, university_scope=HOME,
                              cgu_dashboard_transform=source_dashboard)
    repository = platform.state.account_repository

    @asynccontextmanager
    async def lifespan(app):
        try:
            async with platform.router.lifespan_context(platform):
                yield
        finally:
            runtime.cleanup()

    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    app.state.runtime = runtime  # only this process owns and removes this directory
    app.state.platform = platform
    app.state.school_connector = connector
    lock = threading.Lock()

    def session(token):
        return repository.authenticate_by_token_hash(hashlib.sha256(token.encode()).hexdigest()) if token else None

    def require_account(request: Request):
        found = session(request.state.demo_token)
        if not found:
            raise HTTPException(401, '請先開啟展示首頁以建立隔離工作區。')
        return found[0]

    def new_session():
        if len(repository.list_accounts()) >= 500:
            raise HTTPException(503, '展示工作區已滿，請管理者於預演後重啟展示服務。')
        default_workspace = AccountApplicationWorkspace(
            home_school=HOME,
            application_context=ApplicationCenterContext(
                school_name=HOME,
                college='工學院',
                department='生物醫學工程學系',
                degree_level='大學部',
                academic_year='116',
                application_round='第1學期',
                semester='第一學期',
                flags=['subsidy'],
            ),
            selection_conditions=AccountSelectionConditions(
                profile=AccountSelectionProfile(
                    college='工學院',
                    department='生物醫學工程學系',
                    current_year='大三',
                    degree_level='大學部',
                    academic_score=78.0,
                    language_test='toeic',
                    language_score=750.0,
                    target_term='2027-fall',
                    needs_scholarship=True,
                    academic_year='116',
                    application_round='第1學期',
                ),
            ),
        )
        account = UserAccount(
            display_name='林小程（展示資料）',
            home_university=HOME,
            product_tier=ProductAccessTier.SUBSCRIPTION,
            application_workspaces=[default_workspace],
        )
        repository.save_account(account)
        token = secrets.token_urlsafe(40)
        repository.save_session(AccountSessionRecord(account_id=account.id,
            token_hash=hashlib.sha256(token.encode()).hexdigest(), expires_at=utc_now() + timedelta(hours=24)))
        return token

    def cookie(response, token, request):
        response.set_cookie(COOKIE, token, httponly=True, samesite='strict', secure=bool(hosted_origin) or os.environ.get('CGU_DEMO_SECURE_COOKIE') == '1' or request.url.scheme == 'https',
                            max_age=86400, path='/')

    @app.middleware('http')
    async def isolation(request: Request, call_next):
        path = request.url.path
        token = request.cookies.get(COOKIE, '')
        # Never forward production session, Authorization or anonymous credentials.
        request.scope['headers'] = [(k, v) for k, v in request.scope['headers']
            if k.lower() not in (b'cookie', b'authorization', b'x-anonymous-token')]
        if token:
            request.scope['headers'].append((b'cookie', f'{api.AUTH_COOKIE_NAME}={token}'.encode()))
        request.state.demo_token = token
        query = dict(parse_qsl(request.scope.get('query_string', b'').decode()))
        for key in ('home_school', 'home_university', 'home'):
            if key in query:
                query[key] = HOME
        if path in ('/student-dashboard', '/coverage', '/sources', '/documents', '/exchange-info',
                    '/deadlines', '/verified-window-deadlines', '/calendar/school-window.ics',
                    '/application-center/templates', '/application-center/catalog', '/network-effects/status'):
            query['school'] = HOME
        if path.startswith('/account/application-') or path == '/account/workspace':
            query['home_school'] = HOME
        if path.startswith('/cross-school-partners'):
            query['home'] = HOME
        request.scope['query_string'] = urlencode(query).encode()
        forbidden = path.startswith(('/admin', '/auth/oauth', '/auth/email', '/auth/register', '/auth/login',
            '/auth/student', '/auth/me', '/account/vault', '/calendar/feed', '/analytics', '/feedback',
            '/maintenance', '/docs', '/redoc', '/openapi.json'))
        plan_write = (path == '/account/application-paths' and request.method == 'POST') or (
            re.fullmatch(r'/account/application-paths/[^/]+/(?:profile|archive|workspace|steps/[^/]+)', path) and request.method == 'PUT') or (
            re.fullmatch(r'/account/application-paths/[^/]+/workspace/preview', path) and request.method == 'POST')
        connector_write = (
            (path in (
                '/demo/connector/files',
                '/demo/connector/applications',
                '/demo/connector/ask',
                '/demo/connector/inquiries',
                '/demo/connector/return-reports',
                '/demo/connector/oia/actions',
            ) and request.method == 'POST')
            or (re.fullmatch(r'/demo/connector/files/[a-z_]+', path) and request.method == 'DELETE')
            or (path == '/account/notifications/read-all' and request.method == 'PATCH')
            or (re.fullmatch(r'/account/notifications/[^/]+/read', path) and request.method == 'PATCH')
            or (path == '/account/notifications' and request.method == 'DELETE')
            or (re.fullmatch(r'/account/notifications/[^/]+', path) and request.method == 'DELETE')
        )
        allowed_write = plan_write or connector_write or (path == '/account/workspace' and request.method == 'PUT') or (
            path.startswith('/account/application-drafts/') and request.method in ('POST', 'PUT')) or (
            path in ('/application-plan', '/application-plan/evaluate', '/application-plan/schedule', '/advisor/plan',
                     '/application-center/pdf', '/application-center/docx', '/public-translations', '/auth/community-identity') and request.method == 'POST')
        if forbidden or (request.method not in ('GET', 'HEAD') and not allowed_write and path != '/demo/reset'):
            response = JSONResponse({'detail': '此展示尚未開放正式登入、私人文件、外部同步或送件。'}, status_code=403)
        elif request.method not in ('GET', 'HEAD') and (
            request.headers.get('origin') != (hosted_origin or str(request.base_url).rstrip('/'))
            or (hosted_origin and (request.url.hostname != urlsplit(hosted_origin).hostname
                                   or request.url.port not in (None, 443)))
        ):
            response = JSONResponse({'detail': '請由此展示網站操作。'}, status_code=403)
        else:
            if allowed_write:
                body = await request.body()
                if len(body) > 256_000:
                    return JSONResponse({'detail': '展示內容過大。'}, status_code=413)
                ctype = request.headers.get('content-type', '').lower()
                if not ctype.startswith('multipart/form-data'):
                    try:
                        payload = json.loads(body)
                    except (ValueError, TypeError):
                        payload = {}
                    if isinstance(payload, dict) and payload.get('home_school', HOME) != HOME:
                        return JSONResponse({'detail': '此站僅提供長庚大學情境。'}, status_code=422)
            response = await call_next(request)
        response.headers['X-Robots-Tag'] = 'noindex, nofollow, noarchive'
        response.headers['Cache-Control'] = ('public, max-age=3600' if path.startswith('/static/')
                                             and not path.endswith('.html') else 'no-store')
        for key, value in api._browser_security_headers().items():
            response.headers.setdefault(key, value)
        # The production cookie name never leaves this service.
        response.raw_headers = [(k, v) for k, v in response.raw_headers if not (
            k.lower() == b'set-cookie' and v.startswith(api.AUTH_COOKIE_NAME.encode() + b'='))]
        return response

    @app.get('/')
    @app.get('/cgu')
    def home(request: Request):
        token = request.state.demo_token
        with lock:
            if session(token) is None:
                token = new_session()
        response = HTMLResponse(platform_html())
        cookie(response, token, request)
        return response

    @app.get('/static/index.html')
    def static_home(request: Request):
        return home(request)

    @app.get('/demo/bootstrap.js')
    def bootstrap():
        return Response((STATIC / 'cgu-demo-bootstrap.js').read_text(encoding='utf-8'), media_type='text/javascript')

    @app.get('/demo/print.js')
    def print_script():
        return Response(PRINT_SCRIPT_JS, media_type='text/javascript')

    @app.get('/demo/content')
    def content():
        return json.loads(CONTENT.read_text(encoding='utf-8'))

    @app.get('/demo/connector/spec')
    def connector_spec():
        data = json.loads(CONTENT.read_text(encoding='utf-8'))
        return {
            'badge': SIM_BADGE,
            'connector_class': type(connector).__name__,
            'interface_class': SchoolConnector.__name__,
            **data.get('connector_spec', {}),
        }

    @app.get('/demo/connector/status')
    def connector_status(request: Request, receipt_id: str | None = None):
        account = require_account(request)
        return connector.get_status(account.id, receipt_id=receipt_id)

    @app.post('/demo/connector/files')
    async def connector_upload_file(request: Request):
        account = require_account(request)
        if not isinstance(connector, MockCguConnector):
            raise HTTPException(501, '目前連接器不支援展示雜湊登錄')
        try:
            body = await request.body()
            doc_key, filename, content_type, file_bytes = _parse_multipart_upload(
                request.headers.get('content-type', ''),
                body,
            )
            size = len(file_bytes)
            sha256 = hashlib.sha256(file_bytes).hexdigest()
            # Discard file content immediately after hashing in memory; never touch disk.
            del file_bytes
            del body
            return connector.record_file_metadata(
                account.id,
                doc_key=doc_key,
                filename=filename,
                size=size,
                content_type=content_type,
                sha256=sha256,
            )
        except ConnectorValidationError as exc:
            return JSONResponse({'detail': exc.message, **exc.extra}, status_code=422)

    @app.delete('/demo/connector/files/{doc_key}')
    def connector_delete_file(request: Request, doc_key: str):
        account = require_account(request)
        if not isinstance(connector, MockCguConnector):
            raise HTTPException(501, '目前連接器不支援展示雜湊移除')
        try:
            return connector.remove_file_metadata(account.id, doc_key)
        except ConnectorValidationError as exc:
            return JSONResponse({'detail': exc.message, **exc.extra}, status_code=422)

    @app.post('/demo/connector/applications')
    async def connector_submit_application(request: Request):
        account = require_account(request)
        try:
            payload = await request.json()
        except ValueError:
            payload = {}
        try:
            record = connector.submit_application(account.id, payload if isinstance(payload, dict) else {})
            return JSONResponse({'badge': SIM_BADGE, 'application': record}, status_code=201)
        except ConnectorValidationError as exc:
            return JSONResponse({'detail': exc.message, **exc.extra}, status_code=422)

    @app.post('/demo/connector/ask')
    async def connector_ask(request: Request):
        account = require_account(request)
        try:
            payload = await request.json()
        except ValueError:
            payload = {}
        if not isinstance(payload, dict):
            payload = {}
        try:
            if isinstance(connector, MockCguConnector):
                result = connector.ask_or_inquire(
                    account.id,
                    str(payload.get('question') or ''),
                    force_inquiry=bool(payload.get('force_inquiry', False)),
                )
                return result
            inquiry = connector.send_inquiry(account.id, payload)
            return {'badge': SIM_BADGE, 'mode_label': '規則式比對，非 AI', 'matched': False, 'matches': [], 'inquiry': inquiry}
        except ConnectorValidationError as exc:
            return JSONResponse({'detail': exc.message, **exc.extra}, status_code=422)

    @app.post('/demo/connector/inquiries')
    async def connector_send_inquiry(request: Request):
        account = require_account(request)
        try:
            payload = await request.json()
        except ValueError:
            payload = {}
        try:
            inquiry = connector.send_inquiry(account.id, payload if isinstance(payload, dict) else {})
            return JSONResponse({'badge': SIM_BADGE, 'inquiry': inquiry}, status_code=201)
        except ConnectorValidationError as exc:
            return JSONResponse({'detail': exc.message, **exc.extra}, status_code=422)

    @app.post('/demo/connector/return-reports')
    async def connector_submit_report(request: Request):
        account = require_account(request)
        try:
            payload = await request.json()
        except ValueError:
            payload = {}
        try:
            report = connector.submit_return_report(account.id, payload if isinstance(payload, dict) else {})
            return JSONResponse({'badge': SIM_BADGE, 'report': report}, status_code=201)
        except ConnectorValidationError as exc:
            return JSONResponse({'detail': exc.message, **exc.extra}, status_code=422)

    @app.get('/demo/connector/return-reports/{receipt_id}/print')
    def connector_print_report(request: Request, receipt_id: str):
        account = require_account(request)
        if not isinstance(connector, MockCguConnector):
            raise HTTPException(404, '找不到列印版')
        report = connector.get_return_report(account.id, receipt_id)
        if report is None:
            raise HTTPException(404, f'找不到返國心得 {receipt_id}')
        return HTMLResponse(_render_report_print_html(report))

    @app.get('/demo/connector/public-reports')
    def connector_public_reports(request: Request, school: str | None = None):
        found = session(request.state.demo_token)
        if not found or not isinstance(connector, MockCguConnector):
            return {'badge': SIM_BADGE, 'items': []}
        return {'badge': SIM_BADGE, 'items': connector.list_public_reports(found[0].id, school_name=school)}

    @app.get('/demo/connector/oia/dashboard')
    def connector_oia_dashboard(request: Request):
        account = require_account(request)
        if not isinstance(connector, MockCguConnector):
            raise HTTPException(501, '目前連接器未啟用模擬承辦後台')
        return connector.get_oia_dashboard(account.id)

    @app.post('/demo/connector/oia/actions')
    async def connector_oia_actions(request: Request):
        account = require_account(request)
        if not isinstance(connector, MockCguConnector):
            raise HTTPException(501, '目前連接器未啟用模擬承辦後台')
        try:
            payload = await request.json()
        except ValueError:
            payload = {}
        if not isinstance(payload, dict):
            payload = {}
        try:
            return connector.oia_action(
                account.id,
                str(payload.get('action') or ''),
                str(payload.get('receipt_id') or ''),
                payload,
            )
        except ConnectorValidationError as exc:
            return JSONResponse({'detail': exc.message, **exc.extra}, status_code=422)

    # Integrate simulated OIA notifications with the shared platform's notification bell endpoints
    @app.get('/account/notifications')
    def demo_notifications_list(request: Request, limit: int = 50):
        found = session(request.state.demo_token)
        if not found:
            return {'items': [], 'unread_count': 0}
        status_data = connector.get_status(found[0].id)
        items = status_data.get('notifications', [])[: max(1, min(limit, 100))]
        unread = sum(1 for item in items if not item.get('read_at'))
        return {'items': items, 'unread_count': unread}

    @app.patch('/account/notifications/read-all')
    def demo_notifications_read_all(request: Request):
        account = require_account(request)
        if isinstance(connector, MockCguConnector):
            items = connector.mark_all_notifications_read(account.id)
        else:
            items = []
        return {'items': items, 'unread_count': 0}

    @app.patch('/account/notifications/{notification_id}/read')
    def demo_notification_mark_read(request: Request, notification_id: str):
        account = require_account(request)
        if isinstance(connector, MockCguConnector):
            updated = connector.mark_notification_read(account.id, notification_id)
            if updated is not None:
                return updated
        raise HTTPException(404, '找不到通知項目')

    @app.delete('/account/notifications/{notification_id}')
    def demo_notification_delete(request: Request, notification_id: str):
        account = require_account(request)
        if isinstance(connector, MockCguConnector):
            connector.delete_notification(account.id, notification_id)
        return {'deleted': True}

    @app.delete('/account/notifications')
    def demo_notifications_clear(request: Request):
        account = require_account(request)
        if isinstance(connector, MockCguConnector):
            connector.clear_notifications(account.id)
        return {'items': [], 'unread_count': 0}

    @app.post('/demo/reset')
    def reset(request: Request):
        with lock:
            found = session(request.state.demo_token)
            if found:
                if isinstance(connector, MockCguConnector):
                    connector.reset_workspace(found[0].id)
                platform.state.form_draft_service.purge_account(found[0].id)
                repository.delete_account(found[0].id)
            token = new_session()
        response = JSONResponse({'reset': True})
        cookie(response, token, request)
        return response

    @app.get('/universities')
    def universities():
        from .models import SupportedUniversity
        from .university_registry import CGU
        return [SupportedUniversity(id='cgu', school_name=HOME, short_name='長庚',
            english_name=CGU.english_name, official_url=CGU.official_url,
            colleges=list(CGU.colleges), hero_image=CGU.hero_image,
            partner_count=len(catalogue.view().partners),
            coverage_note='78 所合作校已與主站同步（含中央當期名單與院級官方參考）；116-1 校內申請至 2026/12/21 17:00。')]

    @app.get('/auth/providers')
    def providers():
        return []

    @app.get('/health')
    def health():
        return {'status': 'ok', 'mode': 'cgu-demo', 'ui': 'shared-uniway-platform', 'persistence': 'isolated-temporary-runtime',
                'revision': os.environ.get('CGU_DEMO_REVISION', 'local')}

    @app.get('/robots.txt')
    def robots():
        return Response('User-agent: *\nDisallow: /\n', media_type='text/plain')

    app.mount('/static', StaticFiles(directory=STATIC), name='shared-static')
    app.mount('/', platform)
    return app
