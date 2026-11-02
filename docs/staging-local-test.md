# 本機測試版（離線版）

目的：改完程式、開了 PR 之後，**先在自己電腦上看成果**，確認沒問題才合併或更新到伺服器。測試版跑的是同一份程式碼，但資料全是虛構的，不會連到 Render 或 Supabase。（程式本身若會抓取公開學校網頁，測試版也一樣會抓。）

## 需要什麼

- Python 3.11 以上、Git。
- 已經 clone 這個專案（這個專案的 `src` 資料夾有 3 GB 以上，**測試版不會再複製一份**，所以不需要額外的硬碟空間，也不會等很久）。
- 第一次啟動會建立虛擬環境並安裝套件，約 3–10 分鐘，畫面會一直捲動，這是正常的；之後很快。

## 第一次使用

在**命令提示字元（cmd）或 PowerShell**，進到專案資料夾。測試版的程式現在放在 PR 的分支上，所以要先切過去：

```bat
cd 你的專案資料夾
git fetch origin claude/funny-dirac-43frw3
git checkout claude/funny-dirac-43frw3
git pull
```

然後啟動（Windows 建議用 `py -3`；如果提示找不到 `py`，改用 `python`）：

```bat
py -3 scripts\staging.py up
```

看到下面這段，才可以開瀏覽器：

```
=== UniWay 測試版已啟動 ===
網址      http://127.0.0.1:8800
```

網頁底部會有紅色的「測試版」標籤。**如果啟動後畫面完全沒有任何文字，請把你的 `py -3 --version`、`git --version`、`dir scripts\staging.py` 的輸出貼給我。** 新版啟動器一開始就會印出進度，不會再沉默。

## 常用指令

| 想做什麼 | 指令 |
| --- | --- |
| 看目前資料夾裡的程式（最快，沒有任何 git 動作） | `py -3 scripts\staging.py up` |
| 看某個 PR 的最新內容 | `py -3 scripts\staging.py up --pr 211` |
| 看某個分支 | `py -3 scripts\staging.py up --branch claude/funny-dirac-43frw3` |
| 看目前的正式版程式碼 | `py -3 scripts\staging.py up --ref origin/main` |
| PR 有新 commit 就自動更新並重啟 | `py -3 scripts\staging.py up --pr 211 --watch` |
| 清空測試資料，下次重新建立虛構帳號 | `py -3 scripts\staging.py reset` |
| 上次異常結束，切回原本的分支 | `py -3 scripts\staging.py restore` |
| 刪掉虛擬環境與測試資料 | `py -3 scripts\staging.py clean` |
| 換埠號 | 加上 `--port 8810` |

按 `Ctrl+C` 停止。

### `--pr`、`--branch`、`--ref` 做了什麼

它們會在**你現有的資料夾**裡 `git checkout` 到那個版本（只更動有差異的檔案），停止時自動切回你原本的分支。
- 如果你的資料夾有**尚未提交的修改**，會拒絕切換，不會弄丟任何東西。這時請先 commit 或 `git stash`，或改用不帶 `--pr` 的 `up`。
- 直接關掉命令提示字元視窗時，來不及切回；之後在專案資料夾執行 `py -3 scripts\staging.py restore` 就會切回。

## 測試帳號

密碼都是 `Staging!2026`。

| 帳號 | 情境 |
| --- | --- |
| `a-first@staging.test` | A：第一次使用，沒有任何計畫 |
| `b-one-plan@staging.test` | B：有一個目標學校，已完成幾項、有一份寫到一半的草稿 |
| `c-two-plans@staging.test` | C：同時有兩份計畫（不同學校、不同學期） |

情境 D（手機）：用 B 或 C 登入，再用瀏覽器開發者工具的手機模擬。測試版只開放本機 `127.0.0.1`，同一個網路上的其他裝置連不到。

## 隔離保證

- 啟動前會移除終端機裡所有 `EXCHANGE_*`、`SUPABASE*`、`GOOGLE_OAUTH*`、`RENDER*` 環境變數，所以即使你的終端機設定過正式環境的金鑰，也不會被用到。
- 資料存在 `.staging/data`（已加入 `.gitignore`），使用程式內建的本機 JSONL 儲存。
- 只有 Email 登入（正式站只開放 Google）。測試版沒有 Google 登入。
- **不會複製正式站的使用者資料。** 「把正式版抓下來」指的是程式碼與程式內建的學校資料，不包含帳號、文件庫、論壇內容等雲端資料庫內容。

## 限制

- 學校目錄與名額使用程式內建資料，不一定和正式站此刻看到的相同。
- 沒有 Google 登入、沒有雲端文件庫、沒有推播與寄信。
- `--watch` 每 30 秒檢查一次遠端；PR 若有衝突或 CI 失敗仍會抓下來，測試版只代表「那份程式碼」。
- **Windows 實機尚未驗證**（開發環境是 Linux）。啟動器只用標準函式庫與 `pathlib`，並處理 Windows 的虛擬環境路徑，但第一次在 Windows 執行時如果出現錯誤，請貼給我。

## 建議的工作流程

1. 修改完成，開 PR，**維持 draft**。
2. 在自己電腦執行 `py -3 scripts\staging.py up --pr <編號> --watch`。
3. 逐一確認三個情境。
4. 滿意後才把 PR 標示為可審查並合併，再更新伺服器。

## 疑難排解

| 狀況 | 處理 |
| --- | --- |
| `埠 8800 已被使用` | 加上 `--port 8801` |
| `找不到 scripts\staging_runner.py` | 還沒切到有這個檔案的分支，照「第一次使用」的 git 指令執行 |
| `找不到 git` | 安裝 Git for Windows 後重開命令提示字元 |
| 套件安裝失敗 | 確認 Python 版本 ≥ 3.11；刪掉 `.staging\venv`（`clean`）後重跑；把最後幾行貼給我 |
| 想從頭來 | `reset`；或 `clean` 刪掉全部 |
| 看不到「測試版」標籤 | 重新整理頁面；標籤只加在 HTML 頁面，不加在 API 回應 |
