"""CGU's home application for 116-1, as verified against the notice and selection guide."""

from datetime import datetime, timezone

CHECKED_AT = datetime(2026, 11, 18, 15, 41, tzinfo=timezone.utc)
NOTICE = "https://www.cgu.edu.tw/oia-ch/Subject/Detail/85785?nodeId=15817"
GUIDE = "https://www.cgu.edu.tw/oia-ch/Contents?nodeId=15656"
APPLICATION_FORM = "https://forms.gle/JbdGkA9i7wkNdtvX8"
UPLOAD_FORM = "https://forms.gle/VzHD2wPxQHDZvfQ37"
DEADLINE = "線上申請與第二份表單的 PDF 上傳均須於 2026/12/21 17:00 前完成，免交紙本。"
STEPS = (
    f"第一步：填寫出國研修申請表（交換及雙聯共用，{APPLICATION_FORM}）。",
    "第二步：從電子信箱下載申請表及家長同意書。申請表由導師或指導教授簽名，同意書由家長或監護人簽名。",
    f"第三步：將簽名文件與其他應備資料掃描或拍成清晰 PDF，透過文件繳交表逐項上傳（{UPLOAD_FORM}）。",
)
REQUIRED_DOCUMENTS = (
    "長庚大學選送學生出國研修申請表（導師或指導教授簽名）",
    "家長或監護人同意書（家長或監護人簽名）",
    "中文歷年成績單正本（含歷年學業平均及班級排名百分比）",
    "本校在學證明（由 iCGU 系統下載）",
    "外國語文能力證明（尚未取得成績可附檢定報名證明並註明預計取得日期）",
    "讀書計畫（中文即可，格式不限，一頁即可）",
)
CONDITIONAL_DOCUMENTS = (
    "申請非本校境外合作大學者須附該校申請或許可紀錄",
    "管理學院曾修習 EMI 課程者須附修課資料",
    "其他有利審查的資料（非必要，多份請合併為一個 PDF）",
)
