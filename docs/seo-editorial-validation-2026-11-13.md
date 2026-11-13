# 2026-11-13 每日兩篇驗收

Asia/Taipei 批次，隔離分支 `codex/seo-daily-20261113`，base main `661a4546ffc48abf7bd908a9fe500bf22968634d`。PR：待建立。本批不合併、不部署、不寄信或要求 Google 建立索引；產出不代表已上線／收錄。

## 內容與分工

| 題目 | slug | 候選方向／獨立意圖 |
| --- | --- | --- |
| 交換預算遇到匯率變動怎麼算？換匯方向、情境表與資金缺口 | `exchange-currency-budget` | 11：外幣待付款、已持有與未換部分、買賣方向、費用位置及代數缺口。與整體成本／補助周轉、三方案取捨分工。 |
| 用 AI 練英文發音怎麼做？字典核對、重音練習與錄音 Prompt | `ai-english-pronunciation-practice` | 17：說話者的字典詞性／重音依據與錄音證據；與聽者聽寫、對話澄清、四技能總覽及 TOEFL 重述任務分工。 |

選題依編輯判斷，無使用者 Search Console、搜尋量或排名資料。讀取最新 workflow、backlog、49 篇庫存及相關全文；查無適用祖先或 tracked AGENTS。全部 16 個 open PR 的範圍與完整分頁檔案清單已核對：14 個資料稽核提案、一個 CGU 展示實作、一個展示影片，無 editorial 文章／renderer／workflow 變更。提交前 main 與全部 head 未變，同日全狀態 PR 為空。#78／#92／#329 合併提交為 main 祖先，昨天兩篇已在 main，未重做；10/30 study-plan `97de3fda` 未重做，無三品牌比較實測，不捏造結果。

原 49 篇 JSON、網址、published、modified 逐位元相同，新增後共 51 篇。新文章沿用 canonical、Article／Breadcrumb、social metadata、Sitemap、原生 FAQ 與手機橫捲表格。兩篇各有直接回答、摘要、目錄、表格、原創 HTML 五步圖、FAQ、來源／適用日期、相關文章及母校／目的地／選校連結。

## 來源、計算與限制

六個實際引用官方／出版者來源均 HTTP 200 並實讀適用範圍。臺銀只支持欄位、方向及參考限制；牌告頁的舊 banner 與最新掛牌時間不同，未取其數值當即時成交。所有示例金額／匯率／費用均為假設，沒有行情預測、銀行交易或費率比較。

日圓需求 600,000－可用持有 200,000＝尚需 400,000；乘 0.21／0.23／0.25 得 84,000／92,000／100,000 TWD，相對另有 90,000 TWD 為餘 6,000／缺 2,000／缺 10,000（費用前）。加歷史換匯支出 42,000 為 126,000／134,000／142,000；不是交換總成本。每 0.01 差額為 4,000；費用前界線 0.225，另付假設 1,000 TWD 後為 0.2225。獨立換回示例 10,000×0.23－10,000×0.20＝300 TWD，未混進主情境。全部用 Decimal 另算並核對預期值。

發音篇實讀 TeachingEnglish 新頁正文、Merriam-Webster record 動詞與名詞（1）、OpenAI 明確提示／逐輪修訂及誤答查證說明。三輪 Prompt、填寫素材、預期文字回覆、錯誤回饋與修正、新句與檢查表為編輯自寫。字典符號與大小寫教學記號分開，不冒稱音訊、語音工具／方案／地區或模型實測，不從文字／辨識結果給正式發音、CEFR 或分數結論。

探索來源中 Cambridge／LearnEnglish Sounds Right 回 403，三個舊 British Council／TeachingEnglish 路徑回 404，均未引用；改用實際可讀的新 TeachingEnglish 頁與 Merriam-Webster，沒有虛構官方存檔。未轉載語音／圖表，沒有聲學測試；真實錄音品質與當時工具功能由使用者另核對。相對更新日保留原樣，不反推假發布日期。

## 攝影與目視

新增兩張 Pexels 真實授權照片：Kaboompics.com 的 4386339、Vlada Karpovich 的 4050291。來源 ID 不在原文章／攝影紀錄，原 JPEG 與授權頁已查核；成品 1536×1024 WebP，75,532／135,078 bytes。RGB／LANCZOS 中心裁切、quality83／method6，無生成、重繪或變色。保留自然色、alt、尺寸、lazy loading、圖說與作者來源；素材不當真實學生、報價或發音成效。

已目視全部 15 張最終圖：桌面／320px、兩張文中圖、兩個圖解、八段長內容、3:2／2:1 裁切。文字、金額、Prompt、重音符號與圖說可讀。只有長區塊截圖暫隱固定頁首及裝飾線，避免拼接蓋字；產品頁面、完整畫面及斷言未改。

## 驗證

| 檢查 | 實際結果 |
| --- | --- |
| `scripts/check_editorial.py --base-ref origin/main` | 51 篇，0 errors |
| 六模組 SEO 單元／整合／release gate | 178 passed，首次通過 |
| 三模組桌面／手機 E2E | 61 passed，首次通過 |
| 兩篇 × 320／390／1440、關閉 JavaScript | 六組通過；目錄、FAQ、圖片與來源、橫捲、相關與選校連結、canonical／JSON-LD |
| wheel／逐檔核對／checkout 外載入 | 51 JSON、51 專用 WebP、57 CSS、481 字型目錄檔案及其他閱讀資產，共 641 唯一檔逐位元相同；外部載入 51 篇及新 slug 成功 |

Wheel 2,527,828,832 bytes，只留任務 cache；字型目錄 CSS 計數已去重，未全面重驗其他學校素材。內容與圖片先固定再驗收，最終雜湊相同。這些是本地閱讀與套件檢查，不是 production／搜尋排名／真實 Core Web Vitals。

- [來源、版本、實讀範圍與失敗網址](seo-editorial-sources-2026-11-13.json)
- [全部數學與假設](seo-editorial-currency-examples-2026-11-13.json)
- [攝影授權與成品雜湊](seo-editorial-photography-2026-11-13.json)
- [49 篇庫存與原文雜湊](seo-editorial-inventory-2026-11-13.json)
- [16 個待審 PR 與同日查核](seo-editorial-pr-audit-2026-11-13.json)
- [完整 gate](seo-editorial-checks-2026-11-13.json)、[各檢查命令／輸出](seo-editorial-tests-2026-11-13.txt)
- [瀏覽器結果與 15 張截圖雜湊](seo-editorial-browser-2026-11-13.json)、[套件逐檔清單](seo-editorial-package-2026-11-13.json)
- [桌面](seo-previews-2026-11-13/desktop-1440.jpg)、[手機](seo-previews-2026-11-13/mobile-320.jpg)、[裁切](seo-previews-2026-11-13/photography-crops.jpg)

PR／遠端 CI 與任務附件狀態於建立後回填；不宣稱已發布。
