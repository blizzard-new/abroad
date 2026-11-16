# 2026-11-16 每日雙篇驗收

Asia/Taipei 批次，隔離分支 `codex/seo-daily-20261116`，base main `cc576012cf3626696a4210d0d08397964dab60bd`。兩篇完整原創繁體中文圖文文章與驗收完成，已建立同一個 [PR #369](https://github.com/blizzard-new/abroad/pull/369) 待審；未合併、部署或要求索引。

| 文章／候選方向 | slug | 與既有內容分工 |
| --- | --- | --- |
| 托福 Listen to a Conversation 怎麼練？轉折、說話目的與原創題組解析（19：托福準備） | `toefl-listen-to-conversation` | 短對話理解與跨話輪的轉折／行動／未定狀態；與四科概覽、口說重述／訪談、聽寫辨認及 TOEIC 圖表對話分工。 |
| 用 AI 練英文語調怎麼做？句子焦點、意群與錄音 Prompt（17：AI 英文學習） | `ai-english-intonation-practice` | 整句意群、資訊焦點與音高目的；與字典／詞性詞重音、對話澄清、待審簡報主線及書面改寫分工。 |

編輯判斷選題，無使用者 Search Console、搜尋量或排名資料。讀取最新 workflow／backlog、51 篇庫存及相關全文；新 main 對前日的改動沒有 editorial 文章。無適用祖先或 tracked AGENTS。核對全部 13 個待審 PR 的說明、範圍與完整分頁檔案清單：#351 的英文簡報／多益時態、#363 的日本防災／AI 改寫四篇均已選，排除重做、未匯入；#368 為 CGU 操作、#367 為 uv.lock，其他為來源提案。開始前無同日分支／PR，提交前再查最近 100 個全狀態 PR、13 個 open head 及 main，皆未變、無同日批次。#78／#92 已合併且 main 祖先關係已驗證，無基礎相依。10/30 study-plan `97de3fda` 未重做，沒有三品牌測試就不製造比較。

原 51 篇 JSON、URL、刊載日與 lastmod 位元相同，本分支 53 篇，不計入待審四篇。新增直接回答、摘要、H1/H2、目錄、實用表、HTML 五步圖、FAQ、來源與查核日、相關文章及母校／目的地／選校工具連結。沿用 canonical、Article／Breadcrumb JSON-LD、社群標記、Sitemap、手機橫捲表格與原生 FAQ；沒有修改 renderer、JS 或 CSS。

## 實讀來源與原創教材

九個引用來源均 HTTP 200 並實讀：ETS 現行整體內容、聽力、成績，以及 2026 規格 PDF；British Council 語調、KU OpenText 第 4／5 章、OpenAI 提示與準確性說明。PDF 封面 2026 Update、實體第 3 頁的定稿前微調註記及第 5 頁 Listening 表（印刷頁碼 4）均查核，表格另渲染目視。未明示修訂日期的頁面記快照，不冒稱新年度版本；OpenAI 相對更新保留 `27 days ago`／`24 days ago`，不反推發布日。

ETS 聽力細頁導語寫 two task types，實際具名列四項；正文揭露此不一致，用整體內容表與規格交叉核對，不據此宣稱只有兩種題型。預估時長、題量、CEFR 目標及原始點數不作固定規則或自編題校準。成績頁僅採查實的 2026-01-21 起 1–6 分制與各機構要求，沒有引用費用、出分期限或換算自編答對率。

托福篇兩段虛構對話為全新原創，A 五話輪、B 六話輪，六題 × 四選項＝24，逐項驗算並核對 B／D／A／C／B／D 答案。解析區分改場地原因與後續設備問題、請人處理與自己完成、條件式備案、初始疑慮、安撫目的及待回覆報名狀態。不複製官方試題、不捏造真實校規或語氣。文字題明示為看稿語意練習；沒有提供、下載或宣稱聽過音檔，也不冒稱標準化聽力模考。兩段各三題是本篇工作紙配置，不是正式每段題數的斷言。

語調篇三輪可填 Prompt、Alex／map 對比、Noor／updated 換題、rehearsal 意群及 adapter 陳述／確認情境皆原創；未轉載來源範句、影片、音檔或圖表。大寫／斜線／音高提醒是文字計畫，不是假裝聲音證據；沒有唯一停頓秒數、所有問句升調、母語口音或正式程度保證。前後修改改善的是紀錄，反例與預期回饋是編輯設計，不是實際模型輸出或學生進步。KU 頁尾 CC BY 4.0 的例外不被拿來替第三方嵌入教材重新授權。兩個 British Council 探索網址 404 已排除，改採可讀 KU 章節及 British Council 語調頁，未偽造官方存檔或依留言立論。

## 攝影與目視

新增 George Pak／Pexels 交談（7972561）及 dlxmedia.hu／Pexels 錄音器（11901224）兩張專用真實攝影。來源 ID 不在原庫存／攝影紀錄，也不同於待審四篇。來源頁、ImageObject、相機資訊、原 JPEG 與授權均核對；成品 1536×1024 WebP，104,760／134,596 bytes，低於 450 KB。EXIF 方向校正、RGB／LANCZOS fit、quality83／method6；交談圖中心座標 (.5,.28) 保留臉與手，器材圖中心裁切，沒有生成、重繪或變色。

已檢視 15 張閱讀／裁切證據：桌面、320px 手機、兩圖、兩圖解、八個內容段與 3:2／2:1 裁切。中英文對話／選項／解析、三輪 Prompt、焦點與音高限制可讀；手機表格實際可橫捲。交談照片 alt 移除裁切後不可見的欄杆，改為成品可見的建築外交談／筆／資料夾，修改後完整重驗。素材不代表實際考生、ETS 場景、合作校、錄音結果或器材推薦。長區塊截圖暫隱固定頁首／裝飾線以免拼接遮字，實際產品頁、完整畫面及斷言未改。

## 最終驗證

| 檢查 | 最終結果 |
| --- | --- |
| `scripts/check_editorial.py --base-ref origin/main` | 53 篇、0 errors |
| 六模組 SEO 單元／整合／release gate | 180 passed（95.69 秒） |
| 三模組桌面／手機 E2E | 63 passed（212.11 秒） |
| 兩篇 × 320／390／1440、JavaScript 關閉 | 六組通過；目錄、FAQ、1536px 圖片／credit、實際橫捲、無頁面溢出、相關及母校／目的地／工具連結、canonical／JSON-LD |
| 最終 wheel、逐檔與 checkout 外載入 | 53 JSON、53 WebP、全部 58 CSS、481 字型目錄檔及閱讀資產，共 646 唯一檔相同；外部載入 53 篇及新 slug |

首輪 180 SEO／63 E2E／六組無 JavaScript／wheel 全通過後，目視精確化一處 alt，再完整重跑及重建最終套件，兩輪各自紀錄，未加總成額外覆蓋。最終內容與圖片先固定再驗證，雜湊相同。Wheel 2,528,163,182 bytes 僅留 cache；先清除舊任務的可重建 wheel 快取及已完成、乾淨且無未提交資料的 11/11 任務 checkout，以保留建置空間。未刪他人工作；Git 歷史、PR 及來源紀錄保留。其他學校素材未全面重驗。本地結果不是 production、已上線／收錄、搜尋排名或真實 Core Web Vitals。

- [來源版本／閱讀範圍／不一致與排除原因](seo-editorial-sources-2026-11-16.json)、[原創題目／語調案例核對](seo-editorial-exercises-2026-11-16.json)
- [攝影授權](seo-editorial-photography-2026-11-16.json)、[原 51 篇雜湊](seo-editorial-inventory-2026-11-16.json)、[PR 與同日查核](seo-editorial-pr-audit-2026-11-16.json)
- [完整 gate](seo-editorial-checks-2026-11-16.json)、[兩輪命令與輸出](seo-editorial-tests-2026-11-16.txt)、[套件逐檔](seo-editorial-package-2026-11-16.json)
- [瀏覽器與 15 圖雜湊](seo-editorial-browser-2026-11-16.json)、[桌面](seo-previews-2026-11-16/desktop-1440.jpg)、[手機](seo-previews-2026-11-16/mobile-320.jpg)、[裁切](seo-previews-2026-11-16/photography-crops.jpg)

已建立 [PR #369](https://github.com/blizzard-new/abroad/pull/369)，OPEN、非 draft、base main，初始內容 head `b136116c75e3b265cceb46c0cfd1fbc594f0c7dc`，GitHub 顯示 MERGEABLE，未合併。初始 image CI 兩項進行中，Supabase Preview skipped；文件回填後另查目前 head 的 CI，不能以本地測試冒稱遠端通過。任務附加工具 40 秒無回覆，附件列表另等 10 秒也無回覆，**任務附件未確認**；PR 連結與狀態由 GitHub 獨立驗證，未宣稱附加成功。未部署或要求索引。
