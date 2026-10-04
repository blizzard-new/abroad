from __future__ import annotations

from pathlib import Path
from datetime import timedelta

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"

LOCAL_AI_MODE_ENV = "EXCHANGE_LOCAL_AI_MODE"
LOCAL_AI_PROTOTYPE_MODE = "prototype"
LOCAL_AI_DEFAULT_BASE_URL = "http://127.0.0.1:11434"
LOCAL_AI_DEFAULT_CHAT_MODEL = "gemma4:12b"
LOCAL_AI_DEFAULT_EMBEDDING_MODEL = "embeddinggemma"
LOCAL_AI_DEFAULT_CONTEXT_WINDOW = 16_384
LOCAL_AI_DEFAULT_MAX_OUTPUT_TOKENS = 1_024
LOCAL_AI_DEFAULT_MAX_INPUT_CHARS = 60_000
LOCAL_AI_DEFAULT_REQUEST_TIMEOUT_SECONDS = 35.0

STUDENT_VERIFICATION_OAUTH_STATE_TTL = timedelta(minutes=10)
STUDENT_VERIFICATION_PROVIDER_HTTP_TIMEOUT_SECONDS = 20

CGU_START_URL = "https://www.cgu.edu.tw/oia-ch"
ALLOWED_DOMAIN_SUFFIX = "cgu.edu.tw"

RELEVANT_KEYWORDS = [
    "國際事務處",
    "國際處",
    "交換學生",
    "交換",
    "出國",
    "研修",
    "自費研修",
    "雙聯",
    "雙學位",
    "補助",
    "獎學金",
    "心得",
    "FAQ",
    "faq",
    "可申請學校",
    "說明會",
    "申請公告",
    "校內申請",
    "選送",
    "oia",
]

GENERIC_DISCOVERY_KEYWORDS = {"國際事務處", "國際處", "oia"}

EXCLUDED_URL_PARTS = [
    "recruit_intl",
    "admission",
    "/Home/Sitemap",
]

EXCLUDED_TITLE_KEYWORDS = [
    "申請本校",
    "非學位生來校",
    "境外學生招生",
    "外國學生在長庚",
    "國際學生招生",
    "成員介紹",
    "網站地圖",
    "學期交換",
    "研究實習",
]

EXCLUDED_TEXT_KEYWORDS = [
    "長庚大學歡迎外國學生",
    "申請至本校",
    "合作校提名",
    "母校的推薦資格",
    "母校獲得更多資訊",
    "來校交換",
    "接待短期交換生",
    "因撰寫論文來校短期研究",
]

BOILERPLATE_LINE_HINTS = [
    "交通資訊",
    "桃園機場捷運",
    "校車時刻表",
    "聯絡資訊",
    "合作機構",
    "國際處成員",
    "Copyright",
    "© Copyright",
    "33302桃園市龜山區文化一路259號",
    "電話:",
    "電話：",
    "FAX:",
    "E-mail",
    "瀏覽人次",
    "回上一頁",
]

ATTACHMENT_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
    ".ppt",
    ".pptx",
}
