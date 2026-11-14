# 2026-11-14 每日兩篇驗收

Asia/Taipei 批次，隔離分支 `codex/seo-daily-20261114`，base main `aa2d1424d1645308b479bee648eb056a9e956f8e`。PR：[#351](https://github.com/blizzard-new/abroad/pull/351)（OPEN、非 draft、未合併）。不合併、不部署 Windows 正式伺服器、不寄信或要求 Google 建立索引；產文不代表上線／收錄。

## 文章與分工

| 完整題目 | slug | 候選方向／獨立意圖 |
| --- | --- | --- |
| 用 AI 練英文簡報怎麼做？主線、講稿修改與問答 Prompt | `ai-english-presentation-practice` | 17：聽眾、主張與支點、提案狀態、畫面提示及主題問答；與自介經歷、澄清對話及發音錄音分工。 |
| 多益 Part 5 時態題怎麼判斷？時間線、完成式與原創題解析 | `toeic-part-five-verb-tenses` | 20：參照時點、完成／延續／進行與子句關係；與 Part 5 詞性、Part 6 篇章銜接及 Part 7 跨文件證據分工。 |

選題依編輯判斷，沒有使用者 Search Console、搜尋量或排名資料。已讀最新 workflow、backlog、51 篇庫存與相關全文；無適用祖先或 tracked AGENTS。開始及提交前 open PR 為空、同日全狀態 PR 為空，本地／遠端無同日分支後才建立；main 未變。#346 已合併，昨天兩篇已在 main，排除重做；#78／#92／#346 合併提交的 main 祖先關係已驗證。10/30 study-plan `97de3fda` 未重做，無三品牌比較實測，不製造結果。

原 51 篇 JSON、URL、published／modified 雜湊相同，新增後共 53 篇。每篇有直接回答、摘要、H1/H2、目錄、表格、原創 HTML 五步圖、FAQ、來源與日期、相關文章及母校／目的地／選校工具連結。未改 renderer／JS／CSS；沿用 canonical、Article／Breadcrumb JSON-LD、社群與 Sitemap、手機橫捲表格及原生 FAQ。

## 來源與原創素材

11 個實際引用來源全部 HTTP 200 並實讀適用正文。UNC 的目的／聽眾／主張與清楚轉場、British Council 簡報短句／提示／錄音，以及 OpenAI 的明確背景／逐輪修訂／誤答查證，只作一般依據；未重製、翻譯其講義、影片、逐字稿或工作紙。來源相對更新保留原文，不反推發布日，沒有冒稱觀看影片或量測音訊。

簡報篇的任務卡、三輪可填 Prompt、虛構未試行提案、弱稿／修改稿、預期文字回覆、兩組問答與新任務流程由編輯自寫。區分安排、理由、未知與已證明效果；不造調查、效率、組員同意、老師背書、模型輸出、錄音秒數、投影片檔案或工具／方案／地區比較。課程 AI 規範按本人實際要求確認。

多益篇明示 TOEIC Listening & Reading，與 Speaking／Writing 分開。實讀臺灣官方當期 Part 5 30 題與四選一 directions，另讀 British Council 一般過去、現在完成、過去完成、過去進行與時間子句正文；不依留言／互動答案，不轉載官方題目。六題、24 選項逐項核對，答案 B／D／A／C／B／A；有完整理由與 on Monday 資訊不足例，不硬製造唯一答案、不將副詞當絕對公式。6×4＝24 已另核對，未捏造考點占比、難度、提分或原始正確率換分。

Kent 與一個舊時間子句網址回 404，均排除；簡報採可讀 UNC／British Council，時間子句循官方 `/node/1439` 連到實際可讀的新 canonical 頁。沒有虛構官方存檔。實際費用、資格、簽證、獎學金或校方期限均未無據斷言。

## 照片與閱讀畫面

新增 Pavel Danilyuk／Pexels 白板說明（7869057）及 Burst／Pexels 書寫筆記（374820）兩張專用真實攝影，來源 ID 不在原文章或攝影記錄。實讀來源／ImageObject／授權，檢視原 JPEG 與成品；1536×1024 WebP，41,210／77,962 bytes。RGB／LANCZOS 中心裁切、quality83／method6，無生成、重繪或變色。初選握手圖 3184465 因不夠貼題排除，未出貨。

alt、尺寸、lazy loading、圖說、作者與連結均核對；素材不當真實課堂、學生、考題或成效。已目視全部 15 張最終圖：桌面、320px 手機、兩圖、兩圖解、八段內容及 3:2／2:1 裁切。文字／Prompt／解析可讀，主體保留。只在長區塊截圖暫隱固定頁首／裝飾線，避免拼接蓋字；實際產品頁、完整畫面及斷言未改。

## 實際驗證

| 檢查 | 結果 |
| --- | --- |
| `scripts/check_editorial.py --base-ref origin/main` | 53 篇、0 errors |
| 六模組 SEO 單元／整合／release gate | 180 passed，首次通過 |
| 三模組桌面／手機 E2E | 63 passed，首次通過 |
| 兩篇 × 320／390／1440，JavaScript 關閉 | 六組通過；目錄、FAQ、照片／來源、實際橫捲、相關與選校連結、canonical／JSON-LD |
| Wheel、逐檔核對、checkout 外載入 | 53 JSON、53 專用 WebP、全部 58 CSS、481 字型目錄檔案及其他閱讀資產，共 646 唯一檔相同；外部可載入 53 篇及新 slug |

Wheel 2,528,030,515 bytes，只留任務 cache；字型目錄 CSS 已去重，其他學校素材未全面重驗。內容與圖片先固定再測，最終雜湊相同；這是本地閱讀驗收，不是 production、搜尋成效或真實 Core Web Vitals。

- [來源版本／正文範圍／限制](seo-editorial-sources-2026-11-14.json)、[原創練習／答案核對](seo-editorial-exercises-2026-11-14.json)
- [攝影授權](seo-editorial-photography-2026-11-14.json)、[51 篇原文雜湊](seo-editorial-inventory-2026-11-14.json)、[PR／同日查核](seo-editorial-pr-audit-2026-11-14.json)
- [完整 gate](seo-editorial-checks-2026-11-14.json)、[命令及輸出](seo-editorial-tests-2026-11-14.txt)、[套件逐檔](seo-editorial-package-2026-11-14.json)
- [瀏覽器與 15 圖雜湊](seo-editorial-browser-2026-11-14.json)、[桌面](seo-previews-2026-11-14/desktop-1440.jpg)、[手機](seo-previews-2026-11-14/mobile-320.jpg)、[裁切](seo-previews-2026-11-14/photography-crops.jpg)

PR #351 已由 GitHub 核對：開啟、非草稿、尚未合併、可合併，兩篇同屬本日唯一 PR。初查兩項 image CI 進行中，Supabase Preview skipped，不宣稱遠端 CI 全通過。已呼叫任務附件工具，40 秒內未回傳；附件清單查詢 10 秒亦未回傳，無法確認附加成功。PR 建立與網址已獨立核對，不宣稱已發布。
