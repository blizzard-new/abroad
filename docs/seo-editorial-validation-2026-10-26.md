# 2026-10-26 每日兩篇：來源與驗收

日期採 Asia/Taipei。隔離分支 `codex/seo-daily-20261026` 基於最新 main `252f633c4b4d859b3d7ca20df2005ec2208a8e8f`；驗收後再次 fetch，main 未變。兩篇完整文章同屬 [待審 PR #133](https://github.com/blizzard-new/abroad/pull/133)，非草稿、未合併。選題是使用者候選 7、11，依編輯判斷，沒有 Search Console、搜尋量或排名資料。

## 文章與搜尋意圖

| 題目／新增路徑 | 正文可見字元 | 原創實用內容 |
| --- | ---: | --- |
| 交換獎學金核定後要做什麼？在外義務、研修變更與證據追蹤表 `/guides/exchange-scholarship-obligations` | 4,281 | 義務卡、修課／身分追蹤、事件及決定權整理、未寄送詢問模板、用途別證據與回顧流程 |
| 預算有限怎麼規劃交換？資金上限、三方案取捨與可行性檢查 `/guides/exchange-limited-budget` | 4,416 | 必要學習條件與資金界線、三方案假設、倒推門檻、取捨順序及可填寫決策卡 |

每篇有直接回答、三項摘要、五個實質 H2、目錄、表格及清單、原創五步 HTML 圖解、授權文中攝影、四組 FAQ、官方來源及四篇相關文章。沿用既有 renderer/schema 的 canonical、Article/Breadcrumb JSON-LD、社群標記、Sitemap、母校／目的地／選校工具連結，無路由、CSS 或 JavaScript 改動。

選題前讀 main 十九篇與所有待審 PR #119、#122、#126、#127、#131、#132。#119 的英語授課／改選、#122 的面試／通勤、#132 的托福／返國，共六題視為已選並排除；未納入其文章或依賴其合併。#78、#92、#117 已合併。開始前及驗收後均查詢當日分支的所有狀態 PR，沒有另一個 10/26 批次。

補助篇面向核定後仍在研修中的學生，處理條件與變動管理；既有 `exchange-scholarships` 保留尋找、申請及初步撥款概覽，待審返國篇保留結束後交接。有限預算篇面向已有固定資源上限、需要篩選方案的學生；既有 `exchange-budget` 保留估總額、成本／現金分類與付款時序，待審通勤篇保留路線費用／時間比較。新文不重建上述完整教學，也不使用換年份、換品牌或國家近似頁湊數。

既有十九篇內容、網址、原始出版日及 lastmod 均未改動。兩篇新增文的 published／modified／checked 為本次實際產文與來源查核日 2026-10-26。

## 來源與限制

[來源台帳](seo-editorial-sources-2026-10-26.json) 保存五個引用來源的要求／解析網址、HTTP 200、版本、SHA-256、短證據及對應主張。已實際閱讀相關內文與上下文，沒有以搜尋摘要代替核對。

- 銘傳 115 學海公告：頁內明示 2026 秋季／2027 春季，未見整頁修訂日；引用注意事項中的本人契約、在外學籍與研修義務。不引用金額、期限或語言分數，未讀附件。
- 中山獎助 FAQ：當日現行頁，未見整頁修訂日；核對資金來源、核定後變更、不同計畫修課及核銷分工。不套用其金額、門數、撥款天數或返國期限，不讀取附件作主張。
- 臺北市立大學核定公告：內文日期 115-07-02（2026-07-02），只作該輪分期履行與變更程序案例。不宣稱仍受理、不搬用學分換算、比例、期限或返還條件；沒有讀取獲獎名單與附件。
- 赫爾辛基大學出國交換規劃：閱讀學習／學期、目的地選擇及資金段落，未見整頁修訂日；用於說明必要學習限制與旅費、補助、生活費需共同考量。不將該校出國生資格、補助與學分要求套到臺灣學生。
- Hanken 交換生財務頁：閱讀完整財務與月估計上下文，未見修訂日或估計年度；僅引用資金覆蓋整段及個人支出不同的提醒，不轉載租金、交通價或補助敘述為本人的報價或規則。

教育部 FAQ 第二頁成功連線，但列表只有題名而非完整答案，只作資料發現，不引用或推測答案。本文沒有未查證費用、共同期限、語言資格、獎學金金額或簽證要求；所有個案仍須核對本期通知、本人核定及契約。每月回顧為編輯方法，不是官方共同月報義務。假設紀錄不是學生心得、訪談、模型實測、專家審核或資格判定；沒有寄送詢問模板。

有限預算篇全部金額為原創新臺幣假設，不是行情、匯率換算、官方平均或足夠出國的保證。假設期間五個月、交換專用上限 200,000 元、備用額 20,000 元；母校學費與臺灣固定支出僅在該假設中另已安排，文章明示不得忽略真實待付項目。

台帳逐項驗算二十項，包括：可規劃支出 `200000−20000=180000`；A／B／C 含備用資金為 235,000／190,000／170,000 元；A 刪去自選支出仍需 205,000 元，差 5,000 元；倒推月必要支出 `(180000−45000)/5=27000`。B 另增加必要支出 15,000 元後同樣需 205,000 元。C 即使便宜，假設必要課程缺口未解決，因此不判定可行。

## 攝影與版面

[圖片來源台帳](seo-editorial-photography-2026-10-26.json) 保存來源頁、作者、ImageObject 原始尺寸、下載網址、來源／成品雜湊及 Pexels License 查核。兩個照片頁和完整授權頁皆 HTTP 200、實際讀取；未用生成圖或紙感插畫。

| 圖片 | 作者／Pexels 編號 | 原始尺寸 | 交付 WebP |
| --- | --- | --- | --- |
| `exchange-obligations-photo.webp` | RDNE Stock project／6170644 | 6083×4055 | 1536×1024，67,708 bytes |
| `limited-budget-photo.webp` | Keira Burton／6147045 | 6000×4000 | 1536×1024，188,518 bytes |

合計 256,226 bytes，各低於 450 KB。使用 Pexels CDN 自然裁切及 Pillow WebP 壓縮，無修圖合成。已目視 3:2／2:1 裁切，月曆書寫及桌邊討論主體保留；alt 與畫面吻合，圖說揭露素材情境，未稱真實獲獎者、申請者或官方文件。renderer 保留 1536×1024 尺寸、lazy loading、作者與可點擊來源。

五步原創 HTML 圖解分別解釋在外義務回顧與固定預算篩選，手機直排可讀。桌面、手機、攝影、圖說、圖解與表格已由產文代理目視檢視，不宣稱第三方人工或專家審核。

## 驗證結果與已處理失敗

| 驗證 | 最終結果 |
| --- | --- |
| `scripts/check_editorial.py --base-ref origin/main` | 通過，21 篇，errors 空陣列；[完整輸出](seo-editorial-checks-2026-10-26.json) |
| 六個 SEO 單元／整合及 release gate 測試檔 | 98 passed，36.00 秒，重跑無警告 |
| 三個 SEO 瀏覽器測試檔 | 31 passed，91.23 秒；Chromium `/usr/bin/chromium` |
| 兩篇各 320／390／1440 px、停用 JavaScript | 6/6 通過；[逐頁結果](seo-editorial-browser-2026-10-26.json) |
| wheel 內容逐檔比較及 checkout 外載入 | 通過，21 JSON＋21 WebP＋renderer／CSS／init，共 45 檔；[完整輸出](seo-editorial-package-2026-10-26.json) |
| `git diff --check` | 通過 |

命令使用 `PYTHONPATH=src` 與 `/workspace/abroad/.venv/bin/python`。單元／整合檔為 `tests/test_seo_articles.py`、`test_seo.py`、`test_seo_content.py`、`test_seo_quality.py`、`test_seo_reporting.py`、`test_editorial_release_gate.py`；瀏覽器檔為 `tests/e2e/test_seo_articles.py`、`test_seo_pages.py`、`test_seo_analytics.py`。`PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium` 指定實際 Chromium。

首輪 `uv build --wheel` 在複製既有大型圖片集時因 `No space left on device` 失敗；同輪 98 個測試通過，但 pytest cache 因空間不足產生警告。首輪瀏覽器 fixture 在載入本機開發金鑰時，因解碼長度非 32 bytes 中止；未讀取或輸出任何金鑰內容，也不假定此錯誤一定由磁碟造成。已刪除本次失敗 build 暫存及自己過去驗證過的 wheel；另確認 10/23 產文 worktree 乾淨、HEAD 與已推送遠端一致後，以一般 `git worktree remove` 移除該 checkout，保留分支與待審 PR。未清理原始 `/workspace/abroad` 或他人的未提交變更。

回收空間後，重跑單元與瀏覽器測試時各使用獨立的 `EXCHANGE_INFO_DATA_DIR` 測試暫存目錄，避免共用 import 時的本機開發資料；fixture 照常運作，未停用功能或改測試斷言。最終測試及 wheel 均成功，前述失敗 log 另保存，沒有當作通過輸出覆蓋。建置產物僅用於驗證，未修改套件收檔設定。

額外六個畫面採正式 `create_app` 與拋棄式資料目錄，檢查 HTTP 200、單一 H1、canonical、Article/Breadcrumb、目錄點擊、原生 FAQ、實際照片載入與出處、母校／目的地／工具連結、相關文章導航及頁面無橫向溢出。手機實際改變表格 scrollLeft：補助三表、預算四表均可捲動。這些是本機實驗室結果，未宣稱正式站 Core Web Vitals 或 Google 收錄。

套件使用 `uv build --wheel` 實際建置，逐檔比較 45 個檔案 bytes；抽出套件後，在來源 checkout 外 import 成功，載入二十一篇及兩個新 slug。大型 wheel、原始官方全文、下載原圖與 scratch 不放入 PR。

目視證據：[桌面](seo-previews-2026-10-26/desktop-1440.jpg)、[320 手機](seo-previews-2026-10-26/mobile-320.jpg)、[補助攝影](seo-previews-2026-10-26/exchange-obligations-photo-390.jpg)、[預算攝影](seo-previews-2026-10-26/limited-budget-photo-390.jpg)、[補助圖解](seo-previews-2026-10-26/exchange-scholarship-obligations-diagram-390.jpg)、[預算圖解](seo-previews-2026-10-26/exchange-limited-budget-diagram-390.jpg)。原始回應、測試 log、完整截圖與套件驗證暫存於 `/workspace/scratch/uniway-seo-20261026/`，PR 保留來源台帳與選定證據。

## 後續候選與交付範圍

[選題清單](seo-editorial-backlog.md) 已盤點全部二十個方向。原池剩下的候選 13 應優先擴充 `exchange-study-plan`，不能另建近似頁；候選 15 需要 Claude／ChatGPT／Gemini 同任務、可核對日期／版本／方案的實測，目前沒有這份證據。下一批若無新獨立候選或測試資料，應回報不足，不能靠重做待審題目或拆分既有文完成兩篇數量。本批兩題已選，後續排除。

本次未自動合併、部署 Windows 正式伺服器、寄信或要求 Google 建立索引。待審 PR 與排程完成不代表文章已上線或被收錄。

建立 PR 後已呼叫任務 `attach_artifact` 工具，20 秒內沒有回覆；附件狀態無法確認，未宣稱成功。GitHub PR 本身已成功建立，連結如上，文章與證據均在該 PR 內。
