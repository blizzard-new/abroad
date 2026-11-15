# 2026-11-15 每日雙篇驗收

Asia/Taipei 批次，隔離分支 `codex/seo-daily-20261115`，base main `aa2d1424d1645308b479bee648eb056a9e956f8e`。完成兩篇完整文章與配圖，待同一個新 PR 審閱；未合併、部署或申請索引。

| 文章／候選方向 | slug | 與既有內容分工 |
| --- | --- | --- |
| 日本交換生防災怎麼準備？地震避難、離線聯絡卡與宿舍檢查表（6：抵達與生活準備） | `japan-earthquake-preparedness` | 處理日本官方防災資訊用途、住宿風險、聯絡備案與速報限制；與第一週行政報到、住址登記及住宿費用分工。 |
| 用 AI 練英文改寫怎麼做？原意、限定詞與引用 Prompt（17：AI 英文學習） | `ai-english-paraphrasing-practice` | 產出保留必要意思的新表達與來源標示；與閱讀理解問答、本人作文最小文法訂正及個人語氣寫作分工。 |

選題依編輯判斷，無使用者 Search Console、搜尋量或排名資料。已讀最新 workflow、backlog、51 篇庫存及相關全文，無適用祖先或 tracked AGENTS。核對全部 12 個待審 PR 的說明、範圍及完整分頁檔案清單；#351 兩篇英文簡報／多益時態仍待審，視為已選並排除，沒有匯入其文章、資產或實作。其餘 11 個是 CGU demo 或來源提案，沒有同意圖文章。開始及提交前同日 PR 為空，提交前最近 100 個全狀態 PR、12 個 open head 及 main 再查，未變。#78／#92 已合併且 main 祖先關係已驗證，無基礎相依。10/30 `exchange-study-plan` 更新 `97de3fda` 未重做，沒有三品牌實測就不製造比較。

原 51 篇 JSON、URL、published／modified 位元相同，本分支共 53 篇；#351 未合併內容不計入。新增兩篇直接回答、摘要、H1/H2、目錄、實用表、原創 HTML 五步圖、FAQ、來源日期、相關文章及母校／目的地／選校工具連結。沿用 canonical、Article／Breadcrumb JSON-LD、社群與 Sitemap，未改 renderer、CSS 或 JavaScript。手機表格保留原生橫捲，FAQ 原生可開合。

## 來源與教材

15 個實際引用的一手來源均 HTTP 200 且實讀對應正文。防災採消防廳八個具體子頁、氣象廳速報原理／限制、JNTO 防災與避難所說明。未把導覽頁、只回成功狀態的頁面或未閱讀的圖片當成正文證據。住宅室內保護與搖晃後確認出口分開；地方災害、海嘯與現場指示有適用範圍。沒有實際宿舍或路線認證、緊急服務可用性、採購用量、醫藥劑量、費用與校方期限的無據斷言。表格含自填欄位，需本人以所在地方政府、校方及住宿當期資料完成。

東京都 `/book/` 回 HTTP 200，實際卻是維護畫面，屬內容失敗，未引用或宣稱讀過年度手冊。警視廳探索網址及氣象廳猜測的 `eew4.html` 回 404，均排除；後者循真正官方連結讀取可用的 `eew3.html`。未偽造官方存檔。未明示修訂日的頁面記本次快照，不把查核日叫新版年份。

改寫篇實讀 Purdue OWL 的改寫／摘要／引用與來源原則、OpenAI 提示與準確性限制；未重製翻譯講義、原範文、完整六步或特定引句比例規則。OpenAI 相對更新分別保留 `26 days ago`／`23 days ago`，不反推絕對發布日。三輪可填 Prompt、A／B 虛構社團文字、錯誤稿、參考改寫、意思表與人工清單皆本篇原創。A 的六類主要偏移及額外未據費用、B 的四項意思逐項覆核，尤其 may／must、not required／prohibited 與 undecided／confirmed。這是人工教材查核，非模型輸出、品牌比較、學生試驗、官方成績、專家評分或 AI 偵測規避方法。來源卡不捏造 DOI、作者或頁碼，課程 AI 規範須依本人實際要求確認。

## 照片與目視

新增 Thibeau Viaene／Pexels 日本街道（20343263）與 Charlotte May／Pexels 標記英文紙本（5965889）兩張專用真實攝影，ID 不在原庫存或攝影紀錄，也不同於待審 #351 的 7869057／374820。來源頁／ImageObject／相機資訊與授權已核對，原 JPEG 與成品已目視；1536×1024 WebP 分別 310,860／62,034 bytes，低於 450 KB。僅校正 EXIF 方向、RGB／LANCZOS 中心裁切與 quality83／method6 壓縮，無生成、重繪或變色。人物與場景不宣稱為實際交換生、避難路線、校園、受災現場或本篇練習內容。

已檢視全部 15 張最終圖：桌面、320px 手機、兩圖、兩圖解、八個內容段及 3:2／2:1 裁切。中英文與 Prompt 可讀，主體保留；手機表格可左右捲至完整欄位。長區塊截圖暫隱固定頁首／裝飾線以免拼接遮字，實際產品頁、完整畫面及測試斷言未改。

## 實際驗證

| 檢查 | 結果 |
| --- | --- |
| `scripts/check_editorial.py --base-ref origin/main` | 53 篇、0 errors |
| 六模組 SEO 單元／整合／release gate | 180 passed（81.60 秒） |
| 三模組桌面／手機 E2E | 63 passed（188.14 秒） |
| 兩篇 × 320／390／1440、關閉 JavaScript | 六組通過；目錄、原生 FAQ、照片／來源、手機實際橫捲、相關與選校連結、canonical／JSON-LD |
| Wheel、逐檔及 checkout 外載入 | 53 JSON、53 WebP、全部 58 CSS、481 字型目錄檔與閱讀程式資產，共 646 唯一檔相同；外部可載入 53 篇及新 slug |

以上各執行一次通過，未把重試當額外覆蓋；內容與圖片測前固定、最終雜湊相同。Wheel 2,528,285,391 bytes，只留任務 cache；建置期間空間吃緊，僅刪除先前任務的可重建 wheel 快取，建置 exit 0、套件驗證通過，未刪他人原始檔或變更。其餘學校素材未全面重驗。這是本地功能與閱讀驗收，非 production、搜尋成效、已收錄或真實 Core Web Vitals。

- [來源版本／正文與排除原因](seo-editorial-sources-2026-11-15.json)、[原創教材／安全範圍](seo-editorial-exercises-2026-11-15.json)
- [攝影授權](seo-editorial-photography-2026-11-15.json)、[51 篇原文雜湊](seo-editorial-inventory-2026-11-15.json)、[PR／同日查核](seo-editorial-pr-audit-2026-11-15.json)
- [完整 gate](seo-editorial-checks-2026-11-15.json)、[命令與測試輸出](seo-editorial-tests-2026-11-15.txt)、[套件逐檔](seo-editorial-package-2026-11-15.json)
- [瀏覽器／15 圖雜湊](seo-editorial-browser-2026-11-15.json)、[桌面](seo-previews-2026-11-15/desktop-1440.jpg)、[手機](seo-previews-2026-11-15/mobile-320.jpg)、[裁切](seo-previews-2026-11-15/photography-crops.jpg)

PR、遠端 CI 與任務附件狀態於建立後回填；不宣稱已發布。
