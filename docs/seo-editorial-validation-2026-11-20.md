# 2026-11-20 每日雙篇驗收

Asia/Taipei 批次，隔離分支 `codex/seo-daily-20261120`，base main `21c9dde902506e79ac2da99b3d33d0838ae3cd0b`。兩篇完整原創繁體中文圖文文章、圖片及驗收完成，待同一個新 PR 審閱；未合併、部署或要求索引。

| 文章／候選方向 | slug | 獨立任務 |
| --- | --- | --- |
| 交換成績單怎麼拿？以 Lund Ladok 為例，確認下載、驗證與收件方式（12：返國文件） | `exchange-transcript-of-records` | 四種文件、登錄核對、公開產製步驟、數位驗證及缺件／人工簽名／非現有學生的窗口；與返國總表及學分對照分工。 |
| 多益 Part 5 介系詞與連接詞怎麼分？because、although、despite 與原創題解析（20：多益準備） | `toeic-part-five-prepositions-conjunctions` | 片語／子句接法、原因／讓步、the fact that、名詞內部子句與語意不足；六題 24 選項、逐項解析與換句，與字族、時態及代名詞分工。 |

開始實際時鐘 2026-11-20 00:00:04 UTC，即台北 11/20 08:00:04；最初環境日期還顯示 UTC 11/19，以實際台北日期建立新批次。初次 shell 尚無可用執行環境，`wait_for_environment` 回覆 ready 後成功繼續。昨日 #400 已合併，追蹤信與學術短講兩篇已在 main 並排除重做；merge commit 就是本批 base。#78／#92 與 #399 合併祖先均核對。最新 main 已包含申請流程修正，本次測試使用其當前程式與 fixture，沒有搬入其他分支或重作待審批次。

讀最新 workflow、backlog、63 篇身份／標題與相關全文（返國／抵免、三篇 Part 5），祖先及 tracked tree 無 AGENTS；open PR 為空，開始前無同日分支／PR，提交前 main 未變、open 仍空，最近 100 全狀態 PR 無本日 SEO 批次。選題為編輯判斷，沒有 Search Console、搜尋量、排名或成效資料。原 63 篇 JSON、URL、published／modified 位元相同，共 65 篇；10/30 study-plan `97de3fda` 未重做，不製造三工具比較。

兩篇均有直接回答、三點摘要、H1/H2、目錄、表格／清單、原創 HTML 五步圖、FAQ、來源／日期、相關文章及母校／目的地／工具連結。沿用 canonical、Article／Breadcrumb、社群、Sitemap、原生 FAQ、手機橫捲，未改 renderer、CSS 或 JS。

## 來源、版本及內容檢核

九個文章引用一手來源均可讀 HTTP 200 且實讀正文／PDF。成績單篇讀 Lund 中央 Ladok 頁（2026-09-02）、incoming exchange 頁（2026-10-22）、離校頁（2026-05-29），及臺北市立大學返國文件頁（未見獨立更新日）。逐項核對 Official／National official transcript、anticipated participation／registration 四種類型、My pages 資料更新、Transcripts and certificates／Create 的產製選單、個人識別號＋verification code 的官方驗證與比對 PDF、人工簽名及非現有學生窗口。沒有登入、產製或驗證任何人的資料，也未宣稱實測 Ladok 私人介面。

通常考後約一個月可見是 Lund 頁面的概略說明，不當成每課期限；沒有計算個案核發日、帳號停用日或保證電子格式都被母校接受。可驗證與母校已收件／補件／抵免分開。臺北市大的成績未到備注預計繳交時間只作該校案例，不推為普遍延期或其他返國程序可暫停。未引用 Lund Science 2022 舊頁的三個月驗證或紙本申請規則為通則。三門課、兩門已登錄、一門待確認是原創假設；不補成通過、不算抵免或成績；查詢範本未寄出。原檔不自行貼章或簽名，個人識別與驗證資訊只交必要官方窗口。

文法篇實讀臺灣多益官方結構表與 Part 5 directions（30 題、缺字／片語四選一），與 Speaking／Writing 分開。British Council 的讓步與名詞片語正文核對 despite／in spite of、although／even though、-ing、the fact that、關係子句；不依留言或教材年份猜新版本。BBC 官方站 PDF `Because / because of` 標示 ©2007，下載、全文讀取並目視第 1 頁，僅作穩定文法對照，不說成 2026 多益命題規則。PDF 渲染有 Fontconfig cache 不可寫警告，工具 exit0、實際圖文完整可讀；沒有將原表、雨天／魚／生病例句轉載到網站。

兩個 Cambridge 探索頁因 Cloudflare403 不可讀，已完全排除，不依摘要引用，也不聲稱有官方存檔；替代資料為已實讀的 British Council 正文及有可核對年份的 BBC 官方存檔。PolyU 2019 頁另讀但未採用其中把句首 Because 一概視為差風格的斷言；BBC2015電子書故事及測驗也未使用。

六題答案依序 B、D、A、C、B、C。原因名詞片語／完整子句、讓步名詞／完整子句、fact 名詞與內部 that 子句、多字片語均按給定選項拆解。the fact that 後有動詞不等於空格直接帶整個有限子句；語意不足的 report was short／read it twice 例承認 because／although 可有不同合理意思，不硬選唯一答案。小團隊的 Although／Despite having 改寫保留 studio 主體；另一個自寫 delay 關係子句例說明整組名詞依附，無官方題目／教材故事翻寫。6×4＝24 選項；沒有文法占比、費用、ECTS、期限換算、真實學生／專家／模型實測或分數預測。

## 攝影與畫面

George Pak／Pexels 文件整理（7972276）與 cottonbro studio／Pexels 紅筆訂正（5185084），兩個 ID 不在原庫存／來源紀錄。核對來源頁 ImageObject、創作者、原 JPEG 與 Pexels License；讀網站使用／修改、選擇性署名與禁止冒稱背書、不當描繪、原樣轉售或素材再分發等限制。成品 1536×1024 WebP，84,486／120,940 bytes，均低於 450 KB；EXIF 方向、RGB／LANCZOS 中心 fit、quality83／method6，無生成、重繪或變色。文法 alt 只描述可見手稿與紅色刪改，沒有猜文具類型；兩篇圖說均非真實學生、Ladok、正式成績單或多益評分紀錄。

15 張最終畫面實際目視：桌面 1440、手機 320、兩照片、兩圖解、八重點段、3:2／2:1 裁切。手、便條、筆、文件、電腦與紅色刪改主體保留；中英文、四類文件、產製與驗證流程、缺件範本、文法結構及六題解析／換句可讀。表格實際橫捲，頁面無溢出。長區塊截圖暫隱固定頁首／裝飾線避免拼接遮字，實際產品、完整畫面與斷言未改。

| 檢查 | 實際結果 |
| --- | --- |
| `scripts/check_editorial.py --base-ref origin/main` | 65 篇、0 errors |
| 六模組 SEO 單元／整合／release gate | 193 passed（101.36 秒） |
| 三模組桌面／手機 E2E | 76 passed（224.53 秒） |
| 兩篇 × 320／390／1440、JavaScript 關閉 | 六組通過，含目錄、FAQ、圖片／credit、實際橫捲、相關及母校／目的地／工具、canonical／JSON-LD |
| 重建 wheel、逐檔及 checkout 外匯入 | 65 JSON、65 WebP、全部 59 CSS、481 字型目錄檔及閱讀資產，共 671 唯一檔一致；外部載入 65 篇及新 slug |

各檢查一次完整通過，文章與圖片測前固定、最終雜湊相同，未以重跑膨脹覆蓋。最新 main uv.lock 建本批隔離 venv，`uv sync --frozen --extra dev` 完成，Python 3.12.14、soupsieve 4.1.1，未改共用 venv。Wheel 2,529,767,488 bytes 只留 cache；建置空間不足前已移除自己完成且乾淨的 11/16 checkout 及昨日可重建 wheel，保留分支／Git 歷史／PR／來源與證據，未動他人未提交變更。本地驗收不代表正式部署、已收錄、搜尋成效或真實 Core Web Vitals。

- [來源／HTTP／版本與限制](seo-editorial-sources-2026-11-20.json)、[文件／原創題檢核](seo-editorial-exercises-2026-11-20.json)
- [攝影授權](seo-editorial-photography-2026-11-20.json)、[63 篇原文雜湊](seo-editorial-inventory-2026-11-20.json)、[PR／日期查核](seo-editorial-pr-audit-2026-11-20.json)
- [完整 gate](seo-editorial-checks-2026-11-20.json)、[命令／輸出](seo-editorial-tests-2026-11-20.txt)、[套件逐檔](seo-editorial-package-2026-11-20.json)
- [瀏覽器／15 圖雜湊](seo-editorial-browser-2026-11-20.json)、[桌面](seo-previews-2026-11-20/desktop-1440.jpg)、[手機](seo-previews-2026-11-20/mobile-320.jpg)、[裁切](seo-previews-2026-11-20/photography-crops.jpg)

[PR #401](https://github.com/blizzard-new/abroad/pull/401) 已建立，OPEN、非 draft、MERGEABLE。完整內容 head `5f68aa04fdb7e1eba1e4891fb1b043308898af17`；後續只回填本驗收、PR audit 與 backlog，產品雜湊不變。此內容 head 兩個 TLS trust regression image 檢查仍進行中，Supabase Preview skipped；不宣稱遠端 CI 全通過，以 PR 最新狀態為準。

任務附加 `codex_app.attach_artifact` 等待 40 秒無回覆，`list_artifacts` 等待 10 秒也無回覆，因此附件未確認；實際 PR URL、head 與待審狀態已另行核對。未宣稱附加成功，未合併、部署或要求索引。
