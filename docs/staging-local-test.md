# 本機測試版（離線版）

目的：改完程式、開了 PR 之後，**先在自己電腦上看成果**，確認沒問題才合併。測試版跑的是同一份程式碼，但資料全是虛構的，不會連到 Render 或 Supabase。（程式本身若會抓取公開學校網頁，測試版也一樣會抓。）

## 為什麼需要

`render.yaml` 設定 `branch: main`、`autoDeployTrigger: commit`：任何合併到 `main` 的內容都會自動部署到正式站。所以「合併」就等於「上線」。測試版讓你在合併之前看到結果。

## 需要什麼

- Python 3.11 以上、Git（Windows 請在 PowerShell 或「命令提示字元」使用 `python`；macOS／Linux 用 `python3`）。
- 已經 clone 這個專案。第一次啟動會建立虛擬環境並安裝套件，約需幾分鐘；之後很快。

## 用法

在專案根目錄執行：

```bash
python scripts/staging.py up --pr 211
```

啟動後會印出網址（預設 `http://127.0.0.1:8800`）與三個虛構帳號。用瀏覽器開網址，頁面底部有紅色的「測試版」標籤。

| 想看什麼 | 指令 |
| --- | --- |
| 某個 PR 的最新內容 | `python scripts/staging.py up --pr 211` |
| 某個分支 | `python scripts/staging.py up --branch claude/funny-dirac-43frw3` |
| 目前正式版（`origin/main`） | `python scripts/staging.py up` |
| 你現在資料夾裡的內容（包含還沒 commit 的修改） | `python scripts/staging.py up --here` |
| PR 有新 commit 就自動更新並重啟 | `python scripts/staging.py up --pr 211 --watch` |
| 清空測試資料，下次重新建立虛構帳號 | `python scripts/staging.py reset` |
| 刪掉整個測試版（程式副本、虛擬環境、資料） | `python scripts/staging.py clean` |
| 換埠號 | 加上 `--port 8810` |

按 `Ctrl+C` 停止。

## 測試帳號

密碼都是 `Staging!2026`。

| 帳號 | 情境 |
| --- | --- |
| `a-first@staging.test` | A：第一次使用，沒有任何計畫 |
| `b-one-plan@staging.test` | B：有一個目標學校，已完成幾項、有一份寫到一半的草稿 |
| `c-two-plans@staging.test` | C：同時有兩份計畫（不同學校、不同學期） |

情境 D（手機）：用 B 或 C 登入，再用瀏覽器的手機模擬，或用手機連到同一個區域網路的電腦（預設只開放本機 `127.0.0.1`，要用手機看請自行評估風險）。

## 隔離保證

- 啟動前會移除終端機裡所有 `EXCHANGE_*`、`SUPABASE*`、`GOOGLE_OAUTH*`、`RENDER*` 環境變數，所以即使你的終端機設定過正式環境的金鑰，也不會被用到。
- 資料存在 `.staging/data`（已加入 `.gitignore`），使用程式內建的本機 JSONL 儲存。
- 只有 Email 登入（正式站只開放 Google）。測試版沒有 Google 登入。
- **不會複製正式站的使用者資料。** 「把正式版抓下來」指的是程式碼與程式內建的學校資料，不包含帳號、文件庫、論壇內容等雲端資料庫內容。
- 程式只監聽 `127.0.0.1`，同一個網路上的其他人連不到。

## 它怎麼做的

- 要看 PR／分支時，會用 `git worktree` 在 `.staging/app` 放一份該版本的程式碼，不會動你目前的工作目錄。
- 啟動器 `scripts/staging.py` 管理程式碼與虛擬環境；`scripts/staging_runner.py` 負責隔離環境、建立虛構帳號，並在每個 HTML 頁面底部加上「測試版」標籤。**兩支都不修改網站本身。**
- `pyproject.toml` 或 `uv.lock` 有變動時，會自動重新安裝套件。

## 限制

- 學校目錄與名額使用程式內建資料，不一定和正式站此刻看到的相同。
- 沒有 Google 登入、沒有雲端文件庫、沒有推播與寄信。
- `--watch` 每 30 秒檢查一次遠端；PR 若有衝突或 CI 失敗仍會抓下來，測試版只代表「那份程式碼」。
- 沒有在 Windows 實機測試過（開發環境是 Linux）。啟動器只用標準函式庫與 `pathlib`，路徑與虛擬環境位置有處理 Windows，但第一次在 Windows 執行時請留意錯誤訊息。

## 建議的工作流程

1. 修改完成，開 PR，**維持 draft**。
2. 在自己電腦執行 `python scripts/staging.py up --pr <編號> --watch`。
3. 逐一確認三個情境。
4. 滿意後再把 PR 標示為可審查並合併。
5. 較大的介面改動加功能旗標，預設關閉；合併後正式站不變，旗標打開才上線。

## 疑難排解

| 狀況 | 處理 |
| --- | --- |
| `埠 8800 已被使用` | 加上 `--port 8801` |
| 套件安裝失敗 | 確認 Python 版本 ≥ 3.11；刪掉 `.staging/venv` 後重跑 |
| 想從頭來 | `python scripts/staging.py reset`；或 `clean` 刪掉全部 |
| 看不到「測試版」標籤 | 重新整理頁面；標籤只加在 HTML 頁面，不加在 API 回應 |
