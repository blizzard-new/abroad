# 2026-11-02 SEO 雙篇驗收

日期採 Asia/Taipei。隔離分支 `codex/seo-daily-20261102`，基於 main `8a3efc91e92f61629322c7db229f42c5db1d4438`；兩篇完整圖文與必要驗收完成，同屬本日一個待審 PR（建立後補連結）。沒有合併或部署。

## 兩個獨立問題與內容分工

| 新文章 | slug | 原創實作內容 |
| --- | --- | --- |
| 托福 Listen and Repeat 怎麼練？聽後重述、錄音訂正與分級練習 | `toefl-listen-and-repeat` | 三個自寫英文句子、假設重述差異、錄音對照表、分級與十五分鐘練習；四個官方來源 |
| 多益 Part 7 雙篇、三篇閱讀怎麼練？跨篇證據與原創題組解析 | `toeic-part-seven-multiple-passages` | 三份自寫英文文件、四題選擇題、逐題證據鏈、條件試算與錯因表；三個官方來源 |

選題在使用者原候選 19、20 之內，依編輯判斷，沒有 Search Console 成效、搜尋量或排名證據。開始時查核 main 的 27 篇及目前全部待審 PR #209、#210、#211、#212；四者均無 editorial JSON 變更。#78、#92 已合併；#168 在 2026-11-01 合併，本批使用包含該 renderer 的最新 main。沒有適用的 `AGENTS.md`。

重新閱讀 `toefl-ibt-preparation` 與 `toeic-listening-reading-preparation` 全文後，確認它們處理版本、整體診斷與讀書計畫，對重述及跨篇閱讀只有概述。本批以具體任務的實作、完整新材料與逐項解析提供獨立用途。先前「方向已有文章，因此候選不足」的盤點過於概括，本次明確修正；不是新增品牌頁、重做總覽或為數量拆短文。每篇都有直接回答的開頭、三項摘要、目錄、實用表格、五步原創 HTML 圖解、四題 FAQ、官方來源及相關文章。

原 27 篇 JSON、既有 URL、刊載日與 modified／lastmod 不變；新增文章的 published／modified／checked 均為 2026-11-02，總數 29。保留 renderer 的 canonical、Article／Breadcrumb JSON-LD、社群標記、Sitemap、原生 FAQ、手機可捲動表格與母校／目的地／選校工具入口；無程式、路由、CSS 或資料庫遷移變更。10/30 的讀書計畫更新保留在原分支，未挪用、重做或算入本批；本批沒有三工具比較。

## 官方來源與原創練習

[來源／主張清單](seo-editorial-sources-2026-11-02.json) 記錄實際 HTTP 結果、查核日期、回應 SHA-256、版本與限制。

- 托福：實讀 ETS 現行口說頁、內容頁、成績／2026-01-21 更新說明，以及 18 頁 `2026 Update` 規格 PDF。使用 PDF 實體第 7 頁任務表及第 16–18 頁口說說明，另讀封面與規格微調限制。以現行 HTML 核對重述任務，不套用原始點數、預估時長、逐字扣分或練習估分公式。
- 多益：實讀台灣官方內容頁與 7-3、7-4 範例的文件、問題及答案。只確認雙篇／三篇形式與閱讀時間範圍，不轉載官方題組文字、人物或數據。租借規則、R418 訂單、顧客要求、題目與解析全由 UniWay 自寫。
- 官方 HTML 未顯示確切修訂日期，標示當日讀取版本；未將來源查核當作舊文重要修訂。七個引用來源均成功讀取，沒有用搜尋摘要代替正文，也沒有使用無法驗證的存檔。

原創練習不是 ETS 真題、正式模考、實際考生紀錄、訪談或專家評分。托福例子是文字分析，沒有偽造錄音或根據文字給發音成績；無預讀的練習須使用有權使用的音檔或同伴朗讀，已讀句子要另標。多益三文件題組中，移除寄送仍是顧客要求；新總額明示以商家接受為條件，不推定已核准或退款。

逐項獨立驗算：24×3＝72；72×10%＝7.20；72－7.20＝64.80；64.80＋8＝72.80；兩總額差 8。練習時段 2＋3＋4＋4＋2＝15、2＋6＋8＋4＝20 分鐘。金額是虛構閱讀材料，時間是編輯安排；不是價格、考場計時、分數或進步承諾。沒有新增費用、期限、校方語言門檻、獎學金或簽證要求。

## 圖片與目視驗收

沿用未改動像素的兩張已上版 Pexels 攝影：Zen Chung 的 `toefl-study-photo.webp`（111,030 bytes）及 PNW Production 的 `writing-photo.webp`（88,086 bytes），皆 1536×1024、低於 450 KB。當日重新閱讀兩素材頁及完整 Pexels License，保留作者、來源、授權與限制，見[攝影來源紀錄](seo-editorial-photography-2026-11-02.json)。沒有生成新圖或替換圖片，不將素材人物與筆記宣稱考生、真題、正式考場或成績案例。

已由產文代理實際開啟檢查原圖、3:2／2:1 裁切、桌機與手機閱讀圖、兩張原生 HTML 圖解、照片與圖說，以及原創英文材料／問題／解析。中文、英文、算式與圖說可讀，手機長表格有可操作的橫向捲動，整頁無水平溢出。沒有聲稱人類或專家審查。補充局部截圖使用相同 production page shell 與 stylesheet；最初未套殼的暫存截圖曾產生編碼／樣式錯誤，已重建並覆寫，該問題不在產品頁面。

- [桌機 1440](seo-previews-2026-11-02/desktop-1440.jpg)、[手機 320](seo-previews-2026-11-02/mobile-320.jpg)、[照片裁切](seo-previews-2026-11-02/photo-crops.jpg)
- [托福五步圖](seo-previews-2026-11-02/toefl-listen-and-repeat-diagram-390.jpg)、[多益五步圖](seo-previews-2026-11-02/toeic-part-seven-multiple-passages-diagram-390.jpg)
- [原創多益文件](seo-previews-2026-11-02/toeic-part-seven-multiple-passages-original-documents-390.jpg)、[問題](seo-previews-2026-11-02/toeic-part-seven-multiple-passages-practice-questions-390.jpg)、[解析](seo-previews-2026-11-02/toeic-part-seven-multiple-passages-answers-and-calculation-390.jpg)
- [托福句子與訂正表](seo-previews-2026-11-02/toefl-listen-and-repeat-original-sentences-390.jpg)

## 實際測試與套件

| 檢查 | 結果 |
| --- | --- |
| `scripts/check_editorial.py --base-ref origin/main` | 29 篇、零錯誤；[完整報告](seo-editorial-checks-2026-11-02.json) |
| SEO 單元／整合／發行 gate | 135 passed，87.01 秒 |
| Chromium E2E | 39 passed，179.77 秒 |
| 新文額外閱讀檢查 | 兩篇 × 320／390／1440 px，JavaScript 關閉，6／6 通過；[瀏覽器紀錄](seo-editorial-browser-2026-11-02.json) |
| Wheel | `uv build --wheel` 成功；29 JSON＋27 張不重複 WebP＋CSS／renderer／初始化檔，共 59 檔逐位元一致；checkout 外解包載入 29 篇且新文存在；[套件報告](seo-editorial-package-2026-11-02.json) |

SEO 執行範圍為 `tests/test_seo_articles.py`、`test_seo.py`、`test_seo_content.py`、`test_seo_quality.py`、`test_seo_reporting.py`、`test_editorial_release_gate.py`；E2E 為 `tests/e2e/test_seo_articles.py`、`test_seo_pages.py`、`test_seo_analytics.py`。使用既有 Python 虛擬環境、`PYTHONPATH=src`、隔離資料目錄與 `/usr/bin/chromium`。[完整 pytest 輸出](seo-editorial-tests-2026-11-02.txt) 隨批次保存。

瀏覽器另核對 HTTP 200、唯一 H1、canonical、Article／Breadcrumb、目錄跳轉、FAQ 展開、圖片 lazy loading／尺寸／alt／來源、母校／目的地／選校工具及相關文章導航。每篇在兩種手機寬度都有三個表格實際可水平捲動；桌機不溢出。這是本機驗收，不是現場 Core Web Vitals、Google 收錄或排名證據。大型 wheel 保留於工作區暫存，不加入 Git；只清理已驗收的舊任務暫存 wheel 與本批 build 輸出，原共享 checkout 的工作不變。

## 交付邊界

待審內容為本批兩篇及來源、圖片、截圖、測試與選題紀錄。正式站需在審閱合併後依使用者流程另外發布；本次未合併、未部署 Windows 正式伺服器、未寄信或批量要求 Google 索引，不宣稱排程完成即已上線／收錄。沒有未查證的核心制度主張待填補；稿件仍待 PR 審閱。
