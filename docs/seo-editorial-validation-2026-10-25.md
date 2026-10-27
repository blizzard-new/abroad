# 2026-10-25 每日兩篇：來源與驗收

批次日期採 Asia/Taipei。隔離分支 `codex/seo-daily-20261025` 基於最新 main `252f633c4b4d859b3d7ca20df2005ec2208a8e8f`；提交前再次 fetch，main 未變。兩篇完整文章同屬 [待審 PR #132](https://github.com/blizzard-new/abroad/pull/132)，非草稿、未合併。選題依使用者候選池 19、12 及編輯判斷，沒有使用者提供的 Search Console、搜尋量或排名資料。

## 選題與文章

| 題目／路徑 | 正文可見字元 | 內容 |
| --- | ---: | --- |
| 托福滿分目標怎麼準備？2026 新制題型、6 分制與練習計畫 `/guides/toefl-ibt-preparation` | 4,673 | 新版分科任務與尺度、分級練習、原創英文修改示例、可調整讀書計畫 |
| 交換返國後要做什麼？文件繳交、學習成果與下學期安排清單 `/guides/exchange-return-checklist` | 3,880 | 多窗口交接、缺件處理、真實成果整理、下學期安排與可填寫追蹤表 |

每篇有直接回答的開頭、三項摘要、五個實質 H2、目錄、表格／清單、五步原創 HTML 圖解、一張文中真實攝影、四組 FAQ、官方來源與四個相關指南。沿用 renderer 的 H1、canonical、社群資料、Article/Breadcrumb JSON-LD、Sitemap 及母校／目的地／選校工具連結，沒有新增路由清單或 renderer 分支。

已讀 main 十九篇、所有待審 PR #119、#122、#126、#127、#131，以及基礎 #78、流程 #92 的狀態。#78、#92、#117 已合併，因此直接基於 main。#119 的英語授課／改選及 #122 的面試／住宿通勤四題均視為已選，不重做或納入本批，也無相依要求。開始前及提交前均查詢當日分支的所有狀態 PR，未有另一個 10/25 批次。

托福篇與一般英文學習、多益和正式語言資格分工；返國篇專注交接與成果，不重寫既有抵免篇的 ECTS／課程比較。既有十九篇的內容、網址、原始刊載日期及 lastmod 保持原值。兩篇新增文章的 published／modified／checked 為本次實際產文與查核的 2026-10-25。

## 官方來源與適用範圍

[來源台帳](seo-editorial-sources-2026-10-25.json) 保存五個正式引用的要求／解析網址、HTTP 狀態、版本、SHA-256、短證據、對應主張及限制。實際讀取頁面或 PDF 的相關內文，不以搜尋摘要代替。

- ETS 現行 Test Content 及 Understanding Scores：當日 HTTP 200；採 2026-01-21 起的更新版 TOEFL iBT，1–6、半級距、四科平均取半級距及過渡期對照總分。現行頁未明示修訂日期；不套用其他 TOEFL 產品，不自行線性換算。
- ETS 2026 Update 規格 PDF：18 頁，讀取封面、第 3 頁適性說明及第 4–7 頁任務表。第 3 頁有上線前規格可能微調的註記；現行 HTML 控制題型判讀，本文未將 PDF 預估題數、時長、原始點數寫成固定規則，也未聲稱讀完所有章節。官方約兩小時的預留說明與原創短時練習分開。
- 東華大學交換出返國程序：當日 HTTP 200，核對返國手續／心得、課務與補助分區、成果建議方向。頁上 2026-06-05 為秋季行前簡報更新日，不能當整份返國規則修訂日；未讀附件，不引用附件內容。
- 臺北市立大學交換文件頁：當日 HTTP 200，核對返國紙本／電子文件、成績未到的備注說明及教務／選課繳費分工。沒有將該校天數、照片數量或待遇當成其他學校通則。

臺大候選來源 `https://studyabroad.ntu.edu.tw/exchange-student/after-returning-to-school/` 回覆 HTTP 503，已完全排除；沒有用搜尋摘要、未核對存檔或推測補上臺大規定。文章的返國案例僅依兩個成功讀取的官方頁，這項來源失敗不留下待補的文章主張。ETS prepare 與機構尺度頁僅作資料發現／交叉核對，不宣稱測過其下載或付費服務。

沒有引用未核對費用、報名／返國共同期限、學校語言門檻、獎學金金額或簽證要求。練習、短文、時間安排與成果例子是原創編輯示例，未冒充真題、官方評分、學生訪談或專家審核；個人採認與返國要求仍應核對自己的適用通知。

算式逐項驗算：四科假設 `(5+5.5+5.5+5)/4=5.25`，依 ETS 明示例取半級距為 5.5；每日 `10+20+20+10=60` 分鐘，五天 `60×5=300` 分鐘，即 5 小時。示例不預測正式成績，也不保證固定天數或最高級距。

## 攝影與原創圖解

[圖片台帳](seo-editorial-photography-2026-10-25.json) 保存 Pexels 原始頁、作者、下載網址、授權查核、來源／成品雜湊、尺寸、壓縮及裁切紀錄。兩個照片頁及 Pexels License 均實際讀取；無生成圖、紙感插畫或合成。

| 文中配圖 | 作者／來源編號 | 交付尺寸 | WebP 大小 |
| --- | --- | --- | ---: |
| `toefl-study-photo.webp` | Zen Chung／Pexels 5538618 | 1536×1024 | 111,030 bytes |
| `exchange-return-photo.webp` | Polina Tankilevitch／Pexels 6929190 | 1536×1024 | 113,380 bytes |

合計 224,410 bytes，各張低於 450 KB。以真實學習／資料整理情境配合文章，不稱人物為真實考生、返國學生或官方場景。兩篇均有與畫面吻合的 alt、情境圖說、作者及可點擊來源，renderer 設定尺寸與 lazy loading。

已目視素材接觸表的 3:2／2:1 裁切，以及桌面和手機的閱讀畫面。兩個原創 HTML 圖解分別說明「定版本到換題檢查」及「盤點到接回課表」，手機直排五步可讀，不依賴圖中文字辨識或 JavaScript。此為產文代理自行檢視，並非第三方人工作業或專家審核。

## 實際驗證

| 驗證 | 結果 |
| --- | --- |
| `PYTHONPATH=src python scripts/check_editorial.py --base-ref origin/main` | 通過，21 篇、errors 空陣列；[完整輸出](seo-editorial-checks-2026-10-25.json) |
| 六個 SEO／release gate 單元與整合測試檔 | 98 passed，34.65 秒 |
| 三個 SEO 瀏覽器測試檔 | 31 passed，99.41 秒；Chromium `/usr/bin/chromium` |
| 兩篇各 320／390／1440 px，停用 JavaScript | 6/6 通過；[逐頁結果](seo-editorial-browser-2026-10-25.json) |
| `uv build --wheel`、套件內容比較、checkout 外載入 | 通過，21 JSON＋21 圖片＋renderer／CSS／package init 共 45 檔；[完整輸出](seo-editorial-package-2026-10-25.json) |
| `git diff --check` | 通過 |

單元／整合命令包含 `tests/test_seo_articles.py`、`tests/test_seo.py`、`tests/test_seo_content.py`、`tests/test_seo_quality.py`、`tests/test_seo_reporting.py`、`tests/test_editorial_release_gate.py`。瀏覽器命令包含 `tests/e2e/test_seo_articles.py`、`tests/e2e/test_seo_pages.py`、`tests/e2e/test_seo_analytics.py`。

額外六個 viewport 檢查採正式 `create_app` 與拋棄式資料目錄：HTTP 200、單一 H1、canonical、Article/Breadcrumb JSON-LD、目錄實際點擊、原生 FAQ 開啟、攝影自然寬度 1536／alt／lazy／出處、母校／目的地／工具連結、相關文章導航及頁面無橫向溢出。手機實際改變 table scrollLeft，托福四表、返國三表均可橫向捲動。這些是本機實驗室驗證，未聲稱正式站 Core Web Vitals 或 Google 收錄結果。

套件比對使用實際建出的 wheel，逐檔比較文章 JSON、WebP、CSS、renderer 與 init 的 bytes；抽出內容後在來源 checkout 外以該套件 import，成功載入二十一篇及兩個新 slug。未將大型 wheel、原始官方全文、PDF、下載原圖或 scratch 放入 PR。

目視證據：[桌面](seo-previews-2026-10-25/desktop-1440.jpg)、[320 手機](seo-previews-2026-10-25/mobile-320.jpg)、[托福照片](seo-previews-2026-10-25/toefl-study-photo-390.jpg)、[返國照片](seo-previews-2026-10-25/exchange-return-photo-390.jpg)、[托福圖解](seo-previews-2026-10-25/toefl-ibt-preparation-diagram-390.jpg)、[返國圖解](seo-previews-2026-10-25/exchange-return-checklist-diagram-390.jpg)。原始來源回應、測試 log、完整頁面截圖與 wheel 暫存於本次工作區 `/workspace/scratch/uniway-seo-20261025/`，PR 保留可審查台帳及選定證據。

本批只建立待審 PR，未自動合併、部署 Windows 正式站、寄送任何模板或要求 Google 批量建立索引。文章完成與排程執行不代表已上線或已收錄。

建立 PR 後已呼叫任務的 `attach_artifact` 工具，20 秒內沒有回覆；附件狀態無法確認，未宣稱已附加成功。GitHub PR 本身已成功建立，連結如上；此工具限制不影響 PR 內的文章、來源與驗收檔。
