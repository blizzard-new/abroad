# UniWay CGU｜長庚大學專屬展示版（demo.uniway-tw.com）

這個版本直接共用 UniWay 的 `static/index.html`、首頁、導覽、學校搜尋、收藏比較、日曆、文件工作台及「我的申請」元件；長庚大學為固定母校，隱藏空白的「論壇」與「用戶評價」入口，並將「切換就讀學校」改為固定顯示「長庚大學」。另提供 `SchoolConnector` 抽象校方介接層與 `MockCguConnector` 模擬實作、展示控制列、來源說明與每位訪客獨立的虛構學生工作區。未修改 `pyproject.toml` 或 `uv.lock`，一般 `create_app()` 行為與正式主站完全不變，沒有新增資料庫、付費服務、AI 模型呼叫或外部網路連線。

## 實際範圍

| 功能 | 展示行為 |
| --- | --- |
| 原平台首頁、地球、搜尋、學校詳細頁 | 同一份 HTML、CSS、JS，母校固定顯示「長庚大學」；保留深淺色主題與響應式設計 |
| 長庚合作校與期限資料 | 與 `content.json` 及 UniWay 主站同步 **78 所合作校**（含 66 所交換計畫、14 所雙學位計畫，其中含 2 所管理學院院級參考合作校）、表列名額、語言門檻、領航者補助要點（規章 `2B00004`）及 **116-1 校內申請截止日 2026/12/21 17:00** |
| 收藏與比較 | 使用原有 UI、workspace 與隔離的瀏覽器偏好 |
| 我的申請與官方期限 | 原有計畫建立、今日下一步、六階段準備清單與版本衝突處理；「下一個已確認的官方期限」固定顯示 **116-1 校內申請截止 2026/12/21 17:00** 並附國際處公告來源 |
| 送交國際處（模擬） | 位於「我的申請」，固定標示「模擬・尚未與校方串接」。依官方 5 項文件（線上申請表、家長同意書、語文證明、含排名的中文歷年成績單、一頁讀書計畫）做完整性預檢；缺件列出缺漏項目且不可送出，齊全後送出產生 `SIM-` 收件編號與狀態時間軸（已送出→已收件→要求補件／初審通過），並註明實際申請仍須填線上表單並繳交紙本 |
| 檔案雜湊登錄（無內容寫入） | 模擬送件選檔只記錄 `filename`、`size`、`content_type` 與 `sha256`；位元組於記憶體算完雜湊即丟棄，磁碟不保存檔案內容，並標示「展示版不保存檔案內容，請勿上傳真實個資」 |
| 問國際處 | 先以關鍵字比對 `demo_data/content.json` 與工作區收錄之規則與 FAQ，命中時顯示答案、官方來源連結與「規則式比對，非 AI」；未命中或點選「仍要詢問承辦」時建立 `SIM-` 詢問單進入模擬收件匣 |
| 返國心得 | 依國際處學期報告表四段（出國前準備、上課情形、日常生活、課外活動及其他），每段即時顯示字數並要求至少 300 字；可填影片網址（不上傳影片）與勾選「同意公開給學弟妹」。送出後可匯出列印版，經模擬承辦核可且同意公開者顯示於該合作校詳細頁「學長姐心得（示範資料）」 |
| 校方介接規格頁 | 導覽列「校方介接」列出 `SchoolConnector` 四個標準方法（`submit_application`、`send_inquiry`、`submit_return_report`、`get_status`）之用途、送出／回傳欄位、需校方提供項目與目前狀態（一律為「模擬」），並說明三階段合作（不需校方配合／小型試辦／需校方資訊單位） |
| 國際處視角（模擬） | 底部控制列「切換為國際處視角」開啟三個模擬收件匣（申請、詢問、返國心得）與統計列（各校志願數、缺件數、最常被問的問題），預載 5 筆明確標示之虛構資料；承辦執行確認收件、要求補件、回覆詢問、加入 FAQ、核可心得公開皆即時反映至學生端狀態與通知鈴鐺 |
| 準備工作台／日曆／文件 | 保留個人任務、筆記、個人目標日期、通知文字整理與 `.ics` 匯出；私人檔案庫上傳、附件解析與外部日曆同步停用 |
| 論壇／用戶評價 | 展示版隱藏空白的「論壇」與「用戶評價」入口，不匯入正式用戶資料，不開放公開發文 |

六階段為探索與選校、校內申請、面試與放榜、姊妹校申請、出發準備、抵達與返國。未來若與校方資訊單位對接真實 API，只需替換 `SchoolConnector` 實作類別，無須重寫前端流程。

## 本機預演與重設

```sh
PATH="$PWD/.venv/bin:$PATH" PORT=8765 sh scripts/run_cgu_demo.sh
```

開啟 `http://127.0.0.1:8765/`。底部「載入示範申請」會建立或載入原平台計畫；「切換為國際處視角」可在同一瀏覽器體驗學生端與承辦端雙向互動；「重設我的展示資料」需確認，會一併清除目前瀏覽器的展示申請計畫、模擬送件、檔案雜湊、詢問單、自訂 FAQ、返國心得、承辦操作紀錄與通知。展示 Cookie 有效 24 小時；**重新整理可保留，服務重啟或 Cookie 過期會清除展示工作區**。請勿輸入真實個資。

獨立啟動指令：

```sh
uvicorn exchange_info.cgu_demo:create_demo_app --factory --host 127.0.0.1 --port 8765 --workers 1 --no-proxy-headers
```

## 隔離方式

- demo factory 必須在**獨立 process** 啟動；若已匯入正常 API 或帶 production／Supabase／OAuth／SMTP／OpenAI credentials，拒絕啟動。先清除 `EXCHANGE_*`，建立自有暫存目錄，再初始化共用 API；不讀取或掛載正式 data directory。
- 每個瀏覽器一個沒有 email、密碼或校方驗證狀態的虛構帳號。重用原有 JSONL 帳號、加密草稿與展示暫存目錄內的 `cgu_connector` 工作區；非新增資料庫。展示進程最多 500 個帳號，滿時回 503。
- 使用 `uniway_cgu_demo_session` 的 HTTPOnly、SameSite Strict、host-only Cookie。剝除外來 Cookie、Authorization、匿名 token，只將展示 token 交給內層 API；不接收或設定正式 session cookie。
- `localStorage` 及 `sessionStorage` 都使用 `uniway-cgu-platform:` namespace。重設只刪除此 namespace 與該展示帳號／模擬連接器工作區；不對全站原始 storage 呼叫清空。
- 寫入採允許清單、同 Origin 驗證、256 KB 內容大小上限；模擬送件選檔以記憶體 `BytesParser` 解析並計算 SHA-256 後立即捨棄原始位元組，絕不寫入磁碟。私人檔案庫上傳、OAuth、驗證信、正式送件、社群發布、AI 呼叫及外部日曆同步一律回 403。
- 長庚 catalogue 只讀取已驗證雜湊的 bundled snapshot（78 所合作校），停用背景網路更新，不對任何長庚或外部系統發出網路請求，亦不使用長庚校徽或宣稱校方背書。
- 回應有 `noindex` 與原有 CSP（禁止 inline script 與 inline event attributes）；動態資料 `no-store`，公開靜態資產可快取一小時。

## Windows 獨立展示站（demo.uniway-tw.com）

長庚展示站以獨立 checkout、獨立 Docker Compose 專案（`uniway-cgu-demo`）與專用 image 運行於 Windows 主機 loopback 埠，經 Caddy 反向代理提供 `https://demo.uniway-tw.com`，與正式主站 `https://app.uniway-tw.com` 完全隔離。完整維運與手動更新步驟見 [Windows 操作指南](windows-deployment.md)：

- `start-windows.ps1` 建置固定 commit 的 image，只啟動展示容器，並驗證隔離、保存與重設；沒有自動 Git 更新，未經明確手動執行不會變更線上服務。
- `publish-windows.ps1` 預設只產生與驗證 Caddy 候選設定；明確加 `-Apply` 才套用。
- HTTPS 設定 `CGU_DEMO_PUBLIC_ORIGIN=https://demo.uniway-tw.com`；代理保留 Host，uvicorn 維持 `--no-proxy-headers`。寫入驗證固定 HTTPS Origin 與 Host，Cookie 強制 Secure，不信任客戶端 forwarded headers。
- `/health` 提供 `mode=cgu-demo`、`ui=shared-uniway-platform` 及 image revision。

相關文件：

- [實作盤點](implementation-plan.md)
- [資料來源與限制](sources.md)
- [展示操作腳本／答詢](demo-script.md)
- [測試與截圖](validation.md)
