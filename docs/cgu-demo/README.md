# UniWay CGU｜長庚大學專屬 UniWay

這個版本以已合入 main 的 [PR #299](https://github.com/blizzard-new/abroad/pull/299)（`87277daf`）為 UI/UX 基準，直接共用 UniWay 的 `static/index.html`、首頁、導覽、學校搜尋、收藏比較、日曆、文件工作台及「我的申請」元件。首頁保留原有風格，學校搜尋及「我的申請」沿用 PR #299 的局部升級；長庚是唯一母校。另附展示控制列、來源說明與每位訪客的虛構學生工作區。未新增依賴、資料庫或付費服務。

## 實際範圍

| 功能 | 展示行為 |
| --- | --- |
| 原平台首頁、地球、搜尋、學校詳細頁 | 同一份 HTML、CSS、JS，母校固定長庚；保留主題與響應式設計 |
| 長庚資料 | 77 筆歷史瀏覽項目，混合交換、自費、雙學位及院級參考；不是 77 所當期可申請校。當期名額、目的校日期與語言待確認 |
| 收藏與比較 | 使用原有 UI、workspace 與隔離的瀏覽器偏好 |
| 我的申請 | 原有計畫建立、今日下一步、準備清單、路徑地圖、進度及版本衝突處理；新增六階段的準備建議 |
| 準備工作台 | 沿用 PR #299 的個人任務、筆記、個人目標日期與貼上虛構通知後的待辦草稿；規則整理不稱為 AI。附件解析與私人上傳停用 |
| 示範申請 | 林小程（虛構），Lincoln University，116 學年度／2027 秋季研究目標；不保證當期開放。重複載入保留進度 |
| 日曆 | 原介面及個人行程；不將歷史目的校日期轉成當期官方截止日。外部日曆同步停用 |
| 文件 | 原工作台與官方文件入口保留；未發布內容維持原有閘門。私人文件上傳、正式送件停用 |
| 論壇／評價 | 保留原入口與空白狀態，不匯入正式用戶資料，不開放對外發文 |
| AI／校方串接 | 規劃中，未呼叫模型或校方 API；來源說明內有三階段合作構想 |

六階段為探索與選校、校內申請、面試與放榜、姊妹校申請、出發準備、抵達與返國。由原 `application_path.py` 的 renderer、帳號草稿儲存及版本控制處理；勾選代表自己的準備紀錄。非 Lincoln 目標不繼承 Lincoln 的要求，來源缺漏顯示待確認。

## 本機預演與重設

```sh
PATH="$PWD/.venv/bin:$PATH" PORT=8765 sh scripts/run_cgu_demo.sh
```

開啟 `http://127.0.0.1:8765/`。底部「載入示範申請」會建立或載入原平台計畫；「重設我的展示資料」需確認，只重設目前瀏覽器的展示帳號。展示 Cookie 有效 24 小時；**重新整理可保留，服務重啟或 Cookie 過期會失去展示工作區**。這不是長期學生帳號，請勿輸入真實個資。

初次啟動與載入沿用完整平台，需預留暖機時間；現場先開啟網站確認完成載入，再進入 190 秒操作。獨立啟動指令：

```sh
uvicorn exchange_info.cgu_demo:create_demo_app --factory --host 127.0.0.1 --port 8765 --workers 1 --no-proxy-headers
```

## 隔離方式

- demo factory 必須在**獨立 process** 啟動；若已匯入正常 API 或帶 production／Supabase／OAuth／SMTP／OpenAI credentials，拒絕啟動。先清除 `EXCHANGE_*`，建立自有暫存目錄，再初始化共用 API；不讀取或掛載正式 data directory。
- 每個瀏覽器一個沒有 email、密碼或校方驗證狀態的虛構帳號。重用原有 JSONL 帳號與加密草稿；非新增資料庫。展示進程最多 500 個帳號，滿時回 503，需維護時重啟。
- 使用 `uniway_cgu_demo_session` 的 HTTPOnly、SameSite Strict、host-only Cookie。剝除外來 Cookie、Authorization、匿名 token，只將展示 token 交給內層 API；不接收或設定正式 session cookie。
- `localStorage` 及 `sessionStorage` 都使用 `uniway-cgu-platform:` namespace。重設只刪除此 namespace 與該展示帳號／草稿；不對全站原始 storage 呼叫清空。儲存被封鎖時顯示暫存限制。
- 寫入採允許清單、同 Origin 驗證、內容大小上限；私人上傳、OAuth、驗證信、正式送件、社群發布、AI 呼叫及外部日曆同步回 403。原 UI 有對應停用及說明。
- 長庚 catalogue 只讀取已驗證雜湊的 bundled snapshot，停用背景更新。所有當期名額／截止日欄位收斂為待確認；保留歷史參考來源。
- 回應有 noindex 與原有 CSP；動態資料 no-store，公開靜態資產可快取一小時。noindex 不是存取控制，預設是可公開操作的虛構展示。

主程式增加可選的 catalogue、dashboard、旅程內容與母校 scope 注入點；一般 `create_app()` 預設維持原流程。共用程式修正「名額待確認」應計入待確認，而非不開放／資格不符，並同步收藏後的比較按鈕狀態。原版 HTML 與所有樣式不另複製維護。

## 審查後部署至 demo.uniway-tw.com

本次未部署、未修改 DNS、未合併、未改正式資料、未開自動合併。

1. 審查 PR、來源與測試，決定公開展示或加上既有代理／平台的服務端存取控制。不可用前端硬編碼密碼。
2. 在既有平台建立**新的服務／容器**，使用獨立環境，不掛正式資料卷、不複製正式 secrets。沿用專案 Python 工具鏈，啟動 demo factory，`CGU_DEMO_HOST=0.0.0.0`，單一 worker。每次重啟都是新展示資料。
3. 參考 `deploy/cgu-demo/demo.env.example`。HTTPS 設 `CGU_DEMO_SECURE_COOKIE=1`。反向代理需保留 Host，因寫入 Origin 必須與服務看到的 base URL 一致；若 TLS 在代理終止，須設定 uvicorn 只信任該代理 IP 的 forwarded headers，不能信任所有 IP。先在暫時網域驗證 Cookie Secure、Origin、reset 與來源。
4. 健康檢查 `/health` 應為 `mode=cgu-demo`、`ui=shared-uniway-platform`、`persistence=isolated-temporary-runtime`。驗證正式 Cookie 不會恢復帳號、其他訪客不能讀到自己的進度、私人上傳回 403。
5. 經使用者授權後才設定 demo.uniway-tw.com、自訂網域與 DNS／HTTPS。實際 CNAME 由服務平台提供，不能預先猜測。只導向展示服務，不代理正式 API。
6. 預演後載入固定示範計畫。若要回復，只停止展示服務或回復其 commit。主站頁尾未啟用展示連結。

既有完整 wheel 約 2.3 GiB；需確認平台 artifact／磁碟與 build 限制。既有 TLS gate 的預設 Playwright Node 在此環境未通過；使用 SHA-256 核對過的 Node 24.22.1 後通過，部署時需使用符合 gate 的持久化 runtime，不可照抄本機 `/tmp` 路徑或放寬稽核。完整 Docker、真實代理 HTTPS 與遠端部署尚未驗證。

- [實作盤點](implementation-plan.md)
- [資料來源與限制](sources.md)
- [7 分鐘操作腳本／答詢](demo-script.md)
- [測試與截圖](validation.md)
