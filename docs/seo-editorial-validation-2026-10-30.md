# 2026-10-30 SEO 批次進度與驗收

日期為 Asia/Taipei。隔離分支 `codex/seo-daily-20261030`，驗證基準為 main `1648e3e629c577b4692dff2b9fac5188a73efc69`。**目前只完成一篇實質更新，第二篇尚未完成，因此未建立 PR；本文件不是兩篇批次完成或上線證明。**

## 已完成文章

| 項目 | 結果 |
| --- | --- |
| 標題 | 交換學生讀書計畫怎麼寫？AI Prompt、四段架構與排版步驟 |
| JSON／網址 | `src/exchange_info/editorial/exchange-study-plan.json`／`/guides/exchange-study-plan` |
| 處理方式 | 擴充既有候選 13，不新增網址；文章總數仍為 27 |
| 日期 | 原刊載日 2026-10-19 保留；重要修訂及來源查核日 2026-10-30 |
| 內容 | 5,687 字元的可見正文、7 節、3 張實用表格、5 步原創 HTML 圖解、4 題 FAQ、5 個官方來源 |

開頭直接回答如何完成讀書計畫，附三項摘要、目錄與母校、目的地、選校工具及相關文章連結。新增三輪可複製填寫 Prompt：先追問材料缺口、確認提綱後成稿、逐句核對；另有文件排版提示及人工 PDF 檢查表。假設材料、示範回覆重點與修改前後例子全部明示為人工教學，不冒充三工具實際輸出。排版數值是可調整的編輯示例，校方指定格式與當期 AI 規定優先。

原 canonical、Article／Breadcrumb JSON-LD、社群標記、Sitemap 與 renderer 沿用 main。其他 26 篇 JSON、既有圖片、CSS 與程式碼未改動；沒有新增資料庫遷移或第三方腳本。

## 來源與圖片

已實際讀取 OpenAI、Claude、Google 官方提示指引、東吳 115 年度公告及 Erasmus+ Learning Agreements 頁面，五者均 HTTP 200。各頁版本、日期、支援主張、回應 SHA-256 及適用範圍見[來源紀錄](seo-editorial-sources-2026-10-30.json)。東吳是 2026 年公告案例，不宣稱仍開放；Erasmus+ 規定不套用所有交換方案。沒有加入未查證的期限、費用、補助金額或語言門檻。

沿用 PNW Production 的 Pexels 攝影素材 `writing-photo.webp`，像素與檔案位元均不變：1536×1024、88,086 bytes。當日重讀素材頁及完整授權，保留作者、來源、授權與用途限制，見[攝影紀錄](seo-editorial-photography-2026-10-30.json)。圖說明示為素材，非本文申請者、AI 輸出、正式文件或錄取案例。已目視檢查 3:2 原圖、2:1 裁切、手機文中配圖與圖說；沒有使用已取代的紙感插畫。

## 實際驗證

| 檢查 | 結果及證據 |
| --- | --- |
| `PYTHONPATH=src python scripts/check_editorial.py --base-ref origin/main` | 通過；27 篇，零錯誤；[結構／資產／日期報告](seo-editorial-checks-2026-10-30.json) |
| SEO 單元、整合與發行 gate | `tests/test_seo_articles.py`、`test_seo.py`、`test_seo_content.py`、`test_seo_quality.py`、`test_seo_reporting.py`、`test_editorial_release_gate.py`：107 passed，56.52 秒 |
| Chromium 瀏覽器測試 | `tests/e2e/test_seo_articles.py`、`test_seo_pages.py`、`test_seo_analytics.py`：37 passed，150.37 秒 |
| 更新文章額外檢查 | 320、390、1440 px，JavaScript 關閉，3／3 通過；[瀏覽器報告](seo-editorial-browser-2026-10-30.json) |
| 套件 | `uv build --wheel` 成功；逐位元核對 27 JSON、27 WebP、renderer、CSS 與初始化檔，共 57 檔；在 checkout 外解包並成功載入 27 篇；[套件報告](seo-editorial-package-2026-10-30.json) |

額外瀏覽器檢查包含 HTTP 200、唯一 H1、canonical、Article／Breadcrumb、目錄跳轉、原生 FAQ 展開、照片自然尺寸與延後載入、來源連結、相關文章導航，以及母校／目的地／選校工具連結。兩種手機寬度各有三張表格實際可橫向捲動，整頁無水平溢出。這些是本機驗收，不能推論正式站狀態、Google 收錄、排名或真實使用者 Core Web Vitals。

驗證使用 `/workspace/abroad/.venv/bin/python` 與 `/usr/bin/chromium`；各測試使用隔離的暫存資料目錄。完整測試輸出暫存於 `/workspace/scratch/uniway-seo-20261030/unit-tests.log` 與 `e2e-tests.log`。大型 wheel 位於工作區暫存資料夾，不加入 Git。

## 目視證據

以下截圖及手機表格截圖已由產文代理實際開啟檢查：標題、段落、表格、圖解、照片及來源可讀；沒有聲稱專家或人類審稿。

- [桌機 1440 px](seo-previews-2026-10-30/desktop-1440.jpg)
- [手機 320 px](seo-previews-2026-10-30/mobile-320.jpg)
- [手機照片及圖說](seo-previews-2026-10-30/writing-photo-390.jpg)
- [手機五步圖解](seo-previews-2026-10-30/exchange-study-plan-diagram-390.jpg)
- [手機可捲動表格](seo-previews-2026-10-30/exchange-study-plan-table-390.jpg)

## 第二篇的具體限制

開始前查核 main 的 27 篇及所有待審 PR #168、#169、#174、#175；#168 涉及 SEO 中繼資料／renderer，沒有新增本池文章，本批不含該 PR 的程式變更。基礎 #78、流程 #92 及文章批次 #119、#122、#132、#133 均已合併。候選 1–12、14、16–20 已在 main 覆蓋（5、18 合併為面試文），共 18 個方向。本次完成候選 13 更新，候選 15 仍須 Claude／ChatGPT／Gemini 相同任務的可核對測試、日期、實際方案及可確認的版本；不能以官方功能介紹或人工範例冒充比較結果。

已向使用者詢問新增獨立題目或實測條件，尚未收到答覆。實際以未登入的 TinyFish 瀏覽器開啟 `https://claude.ai/new`，回報導向 `https://claude.ai/login`，出現登入選項及 Cloudflare／hCaptcha 驗證，未取得可用的聊天輸入框，未提交 Prompt。這是本次瀏覽器的存取限制，不推論所有地區或帳號皆不可用。[存取檢查紀錄](seo-editorial-tool-access-2026-10-30.json) 保存執行識別與限制；沒有解答 CAPTCHA、建立帳號、索取密碼、購買方案或偽造模型輸出。若使用者選擇提供登入條件，可透過 [TinyFish Profiles](https://agent.tinyfish.ai/profiles) 自行管理登入，不在對話傳送密碼。

第二篇未備妥前不建立只有一篇的批次 PR，不把此更新拆成兩頁。後續應續作同日分支，取得第二篇條件並完成必要驗收後，兩篇一起建立一個待審 PR 並附加到任務。

未合併、未部署 Windows 正式伺服器、未寄信給第三方、未批量要求 Google 索引；排程執行不代表已上線或已收錄。
