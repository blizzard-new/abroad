# 2026-11-21 每日雙篇驗收

台北日期 2026-11-21，隔離分支 `codex/seo-daily-20261121`，base main `21c9dde902506e79ac2da99b3d33d0838ae3cd0b`。兩篇完整原創繁體中文文章與攝影、HTML 圖解及驗收完成，已建立同一個待審 [PR #402](https://github.com/blizzard-new/abroad/pull/402)。未合併、部署、寄信、致電或要求索引。

| 文章／候選方向 | slug | 獨立用途 |
| --- | --- | --- |
| 交換申請的英語授課證明怎麼辦？MOI、EMI 與語言資格核對表（4） | `exchange-medium-of-instruction` | 文件實際涵蓋範圍、母校開立與接收方接受條件、TUM 官方表單閱讀、兩個假設案例與兩封可填詢問範本。 |
| 用 AI 練英文電話怎麼做？轉接、留言與回電資訊的 Prompt（17） | `ai-english-phone-messages` | 轉接與不在兩條分支、第三人可轉交留言、兩張原創角色卡、三輪 Prompt、前後修改與人工複習。 |

開始時鐘 UTC 11/21 00:02:04＝Asia/Taipei 08:02:04。讀取最新 workflow／backlog、63 篇庫存及相關全文；main 的英語選課與資格篇、澄清與追蹤信篇已比對。適用上層與 main tracked tree 無 AGENTS。#78／#92 已合併祖先核對，無未合併基礎相依。開始前同日全狀態 PR、本地及遠端分支皆無；提交前再查 main、open heads 及最近 100 個全狀態 PR。

唯一待審 #401 是 11/20 的成績單與多益連接結構，完整說明與 30 檔清單已查，head `26bbdb21387b554ab2b42c5bbd48f66f8ef4f0f9`。兩題均視為已選並排除；本批直接基於 main，沒有匯入 #401 的兩篇。API 的 merge_commit_sha 是待審測試合併，不誤記為已合併。主庫存 63＋本批 2＝65 篇，原 63 篇 JSON、URL、published／modified 位元相同。10/30 study-plan `97de3fda` 未重做，也未製造三品牌比較。選題為編輯判斷，沒有 Search Console、搜尋量、排名或流量資料。

MOI 篇是具體的證據申請／收件工作流程，與挑選英語課、資格總覽及待審成績單分工；電話篇是接線分支與第三人訊息轉交，與修補語意不明、一般英文學習及書面追蹤信分工。沒有將既有頁換年份、工具名或標題重發。兩篇均有直接回答、摘要、H1/H2／目錄、表格／清單、五步 HTML 圖解、FAQ、來源與適用日期、相關文章，以及母校／目的地／選校工具連結。沿用 canonical、Article／Breadcrumb JSON-LD、社群標記、Sitemap、原生 FAQ 與手機橫捲；無 renderer、CSS 或 JS 改動。

## 來源與教材查核

七個文章引用的一手來源均 HTTP 200 且實讀正文或 PDF。清大註冊組服務公告核對中英文證明、不同 EMI 認證層級及取得畢業證書後申請，未見獨立修訂日期；僅用於說明部分 EMI 修課與整學程授課語言不能畫等號。另讀自 2025-06-05 調整的費用公告，發現版本差異，因此不沿用早期收費／天數作 2026 承諾，也沒有替個人核准申請資格。舊官方文件 PDF 的 EMI 列雖可讀，但未作現行費用或辦理天數依據。

TUM 的交換申請頁完整語言證據段落核對依修課語言／院系、測驗或母校簽署表、另開明列等級文件及不採語言自評測驗。B1／B2 僅作該校要求須依院系查的案例，不自認讀者程度。實讀官方單頁 Confirmation of Language Skills：母校承辦／語言中心、承辦與申請人欄、能力及授課語言分欄、日期簽署。申請頁實際連結的 international.tum.de PDF 與引用 global.tum.de PDF 位元相同；表內無修訂年月。沒有登入、填報、取得證明或個案豁免，沒有校章、簽名或正式文件仿製。

兩個文件案例、證據表與未寄送詢問稿皆原創：甲的三門英文課不能證明整學程，乙的可申請文件路徑不能當已獲認定；開立、提交、收件與通過分開。沒有費用、學分、分數或截止日計算。

電話篇實讀 British Council Leaving a message 的教學說明、完整 Transcript、A2 標示與練習入口；初次廣義 selector 擷取到頁尾，已改定位 article 並閱讀實際教學正文後才寫作。不依使用者留言／投票日期猜修訂日，沒有播放音訊或轉載官方人物、電話、專案故事。OpenAI 提示原則與準確性說明當日分別顯示 Updated: last month／29 days ago，保留相對版本。只採背景、迭代與查核回饋原則，不外推語音方案、價格、地區功能或品牌排名。

兩張角色卡、轉接／留言分支、第三人留言單、三輪可填 Prompt、壞稿／改稿及回饋反例均人工編寫。A 是詢問是否自備 sketchbook 並請 email 回覆，B 是詢問 digital portfolio 是否可用；兩者都未提供期限、核准或費用。不把 will put through 當已接通、不把代收當目標已讀、不把請求當決定。反例不是品牌實測，文字練習不是聽力或 CEFR 分數；所有聯絡資料為虛構 example.com，未聯絡任何第三人。

## 攝影、閱讀與套件

兩張新增且未用於 main 或待審 #401 的真實攝影：Mikhail Nilov／Pexels（8730979，文件翻閱）及 MART PRODUCTION／Pexels（8872649，電話與筆記）。實讀來源頁 ImageObject、創作者、原 JPEG 與 Pexels License 的網站使用／修改、可選署名與禁止不當描繪、背書、原樣轉售、素材再分發、商標等限制。文中具署名與圖說，不冒稱真實學生、證明、校園、窗口或工具通話。

成品 1536×1024 WebP，58,986／145,200 bytes，均低於 450 KB；僅 EXIF 方向、RGB、LANCZOS 中心裁切及 quality83／method6，無生成、重繪或變色。目視 15 張最終畫面：桌面 1440、手機 320、兩照片、兩 HTML 圖解、八重點段、3:2／2:1 裁切。中英文、Prompt、對話、表格與核對清單可讀；文件／握筆及聽筒／筆記主體保留。手機三張表各實際橫捲、頁面不溢出。長區塊截圖暫隱固定頁首／裝飾線，避免拼接覆字；產品、完整畫面與斷言未改。

| 檢查 | 實際結果 |
| --- | --- |
| `scripts/check_editorial.py --base-ref origin/main` | 65 篇，0 errors |
| 六模組 SEO 單元／整合／release gate | 193 passed（94.04 秒） |
| 三模組桌面／手機 E2E | 76 passed（218.07 秒） |
| 兩篇 × 320／390／1440、JavaScript 關閉 | 六組通過；目錄、FAQ、圖片／credit、實際橫捲、相關導航、母校／目的地／工具、canonical／JSON-LD |
| 重建 wheel、逐檔及 checkout 外匯入 | 65 JSON、65 WebP、全部 59 CSS、481 字型目錄檔及閱讀資產，共 671 唯一檔一致；外部匯入 65 篇與新 slug |

各檢查一次完整通過，文章／圖片在測前固定，最終雜湊相同。隔離 venv 使用最新 main 的 frozen lock，未改共用 venv；wheel 2,529,767,909 bytes 只留 task cache。建置期間為保留空間，只移除自己昨日可重建的 wheel cache（2,529,767,488 bytes），未動待審 #401 checkout、文章、來源或證據；本次 build 暫存於套件核對成功後移除，未動他人變更。本地測試不是正式部署、Google 收錄、搜尋成效或真實 Core Web Vitals。

- [來源／HTTP／版本](seo-editorial-sources-2026-11-21.json)、[案例與教材檢核](seo-editorial-exercises-2026-11-21.json)
- [攝影授權](seo-editorial-photography-2026-11-21.json)、[63 篇原文雜湊](seo-editorial-inventory-2026-11-21.json)、[PR 與日期查核](seo-editorial-pr-audit-2026-11-21.json)
- [Gate](seo-editorial-checks-2026-11-21.json)、[測試命令／輸出](seo-editorial-tests-2026-11-21.txt)、[套件逐檔](seo-editorial-package-2026-11-21.json)
- [瀏覽器／15 圖雜湊](seo-editorial-browser-2026-11-21.json)、[桌面](seo-previews-2026-11-21/desktop-1440.jpg)、[手機](seo-previews-2026-11-21/mobile-320.jpg)、[裁切](seo-previews-2026-11-21/photography-crops.jpg)

[PR #402](https://github.com/blizzard-new/abroad/pull/402) 已建立（OPEN、非 draft），初始內容 head `73dfd3437971546ba381ad96186b646761721e45`、30 檔，GitHub 顯示 MERGEABLE。此 head 兩個 TLS trust regression image 檢查進行中、Supabase Preview skipped；以 PR 最新狀態為準。任務附加工具呼叫 40 秒未回覆，附件查詢另 10 秒也未回覆，附加狀態未確認；PR 建立與連結已獨立核對，不假稱附加成功。後續只回填三份紀錄，文章／圖片／CSS 雜湊仍與測前相同，不重複跑相同測試。未合併或部署。
