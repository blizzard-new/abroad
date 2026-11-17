# 2026-11-17 每日雙篇驗收

Asia/Taipei 批次，隔離分支 `codex/seo-daily-20261117`，base main `ae68380d7ac1c503100696e3aaefd8960ed69239`。兩篇完整原創繁體中文圖文文章、配圖及驗收完成，已建立同一個 [PR #372](https://github.com/blizzard-new/abroad/pull/372) 待審；未合併、部署或要求索引。

| 文章／候選方向 | slug | 獨立任務 |
| --- | --- | --- |
| 交換課綱 Syllabus 怎麼看？評量權重、必做項目與作業高峰檢查表（4：交換課程判讀） | `exchange-course-syllabus-assessment` | 深讀版本、學習成果與評量證據、權重／各項門檻、未給分必做活動、跨課準備高峰。與英語授課／資格初篩、抵免及改課行政分工。 |
| 用 AI 練英文小組討論：表達立場、接話與不同意的 Prompt（17：AI 英文學習） | `ai-english-group-discussion` | 一輪一回應、立場理由、不同意與追問、有限共識。與澄清聽不懂、單向簡報、面試經歷、語調及書面改寫分工。 |

以實際時鐘換算批次：開始為 2026-11-16 23:55:46 UTC，即 11/17 07:55:46 台北，故不將 UTC 環境日期當 11/16 重試。#369 已合併，連同 #351／#363 的六篇均在 main，排除重做；main 祖先已驗證。讀取最新 workflow、backlog、57 篇庫存及相關全文；無適用祖先或 tracked AGENTS。僅有 open PR #371，已讀說明與全部 10 個檔案，為首頁調整，無 editorial 重疊。開始前無同日分支或 PR，提交前再查最近 100 個全狀態 PR、main 和 #371 head，未變且無當日批次。#78／#92 已合併，無基礎相依。10/30 study-plan `97de3fda` 未重做，沒有三品牌實測就不製造比較。

選題是編輯判斷，沒有使用者 Search Console、搜尋量、排名或成效資料。原 57 篇 JSON、URL、published／modified 位元相同，新增後共 59 篇。兩篇都有直接回答、三點摘要、H1/H2、目錄、表格與清單、原創 HTML 五步圖、FAQ、來源與日期、相關文章及母校／目的地／選校工具連結。沿用 canonical、Article／Breadcrumb JSON-LD、社群、Sitemap、手機橫捲與原生 FAQ；未修改 renderer、CSS 或 JS。

## 來源、版本與教材

八個引用來源全為 HTTP 200 且實讀對應正文。課綱篇讀 LTH EXTA27 2026/27 全文（決定 2026-04-08、生效 2026-05-18）、Lund 官網與目前連結的 2024 List of Rights PDF、SOL 評量說明。LTH 案例確有瑞典語教學及 T.I.M.E 特定身分條件，不以課名推定一般交換生可選；Assessment 列筆試／口試，該欄未列百分比，不自行補 50／50 或把 TH 尺度換百分制。

Lund PDF 封面標示 2024-01-18 核定，實讀實體第 8／10／12 頁（印刷 9／11／13）的課綱欄位、必做活動、5.7 評量資訊；第 10／12 頁另渲染目視。官網多院系例外及 SOL 頁尾 2023-08-18 一併記錄，不冒稱 2026 新規、不外推全球要求、個案豁免或補考／公告／成績期限。原始頁與 PDF 只留任務 cache，網站未轉載文件內攝影或整份政策。

配分與時間都是獨立原創假設，已用 Decimal 驗算：60%＋40%＝100%；80×0.60＝48、40×0.40＝16，合計 64；若另自訂每項至少 50，40 未達門檻，不能以總數判通過。此門檻、配分與分數非真實校規。時間例為 8＋5＋3＝16 小時，16－12＝4 小時缺口；12 是假設個人可用時間，不是 ECTS 或官方工作量。成果—任務表、識別卡、必做／高峰表與未寄送詢問均為本篇原創。

討論篇實讀 British Council 同意／不同意、優缺點的官方教學目的與文字稿；未依留言立論、未複製其設計／辦公室故事、台詞、工作紙或完整片語清單，也未宣稱觀看影片或播放音訊。B1／B2 是材料標籤，不是本人程度。OpenAI 具體背景／逐輪修訂／自信誤答與查證限制已核對，相對更新保留 `28 days ago`／`25 days ago`，不推定絕對發布日。

三輪可填 Prompt、三人讀書會 A／B 情境、弱稿／修改稿、五話輪及預期回饋都是獨立自寫；不是模型輸出、真實學生或會議紀錄。沒有成效資料，第三位未發言；夥伴只願試開場、後段保留，最後 yes 只是確認摘要反映其立場，不等於全員核准。換題另用概念圖／文字提要，尊重實際課程格式。文字與真實口頭練習、研究證據及正式評分分開，不造錄音、語音功能／方案／地區比較或保證進步。

## 攝影與閱讀畫面

新增 Ron Lach／Pexels 書寫筆記（8085269）、Yan Krukau／Pexels 多人討論（7640781）兩張專用真實攝影，ID 不在原庫存／來源紀錄。來源頁、ImageObject、相機資訊、原 JPEG、授權與成品已核對。1536×1024 WebP，55,546／87,058 bytes，均低於 450 KB；EXIF 方向、RGB／LANCZOS 中心 fit、quality83／method6，沒有生成、重繪或變色。alt 描述可見內容，圖說不宣稱真實 Lund 課綱、交換課堂、受訪者、會議紀錄或學習成果。

全部 15 張最終畫面已目視：桌面、320px 手機、兩圖、兩圖解、八段內容與 3:2／2:1 裁切。書寫手、筆、翻頁與多人討論主體保留；中英文及數學、權重與狀態表、Prompt 可讀。手機表格實際可左右捲，頁面無橫向溢出。長區塊截圖暫隱固定頁首／裝飾線避免拼接遮字，實際產品頁、完整畫面及斷言未改。

## 實際驗證

| 檢查 | 結果 |
| --- | --- |
| `scripts/check_editorial.py --base-ref origin/main` | 59 篇、0 errors |
| 六模組 SEO 單元／整合／release gate | 186 passed（85.18 秒） |
| 三模組桌面／手機 E2E | 69 passed（201.46 秒） |
| 兩篇 × 320／390／1440、JavaScript 關閉 | 六組通過：目錄、FAQ、圖片／credit、實際橫捲、相關／母校／目的地／工具連結、canonical／JSON-LD |
| Wheel、逐檔與 checkout 外載入 | 59 JSON、59 WebP、全部 59 CSS、481 字型目錄檔及閱讀資產，共 659 唯一檔相同；外部載入 59 篇及新 slug |

各執行一次通過；內容與圖片測前固定、最終雜湊相同。依最新 main 的 uv.lock 建立本日隔離環境，`uv sync --frozen --extra dev` 通過，Python 3.12.14、soupsieve 4.1.1，未修改共用虛擬環境。Wheel 2,528,871,407 bytes 僅留 cache；先清理過往任務可重建 wheel 及已完成且乾淨的 11/12 checkout，Git 歷史／PR／證據保留，未刪他人未提交工作。其他學校素材未全面重驗。這是本地驗收，不是 production、搜尋成效、已收錄或真實 Core Web Vitals。

- [來源版本／正文與限制](seo-editorial-sources-2026-11-17.json)、[Decimal／教材查核](seo-editorial-exercises-2026-11-17.json)
- [攝影授權](seo-editorial-photography-2026-11-17.json)、[57 篇原文雜湊](seo-editorial-inventory-2026-11-17.json)、[PR／日期查核](seo-editorial-pr-audit-2026-11-17.json)
- [完整 gate](seo-editorial-checks-2026-11-17.json)、[命令及輸出](seo-editorial-tests-2026-11-17.txt)、[套件逐檔](seo-editorial-package-2026-11-17.json)
- [瀏覽器／15 圖雜湊](seo-editorial-browser-2026-11-17.json)、[桌面](seo-previews-2026-11-17/desktop-1440.jpg)、[手機](seo-previews-2026-11-17/mobile-320.jpg)、[裁切](seo-previews-2026-11-17/photography-crops.jpg)

已建立 [PR #372](https://github.com/blizzard-new/abroad/pull/372)，OPEN、非 draft、base main，初始內容 head `7f2bad0ba3fdf217f556d4241789ab706676f236`，GitHub 顯示 MERGEABLE，未合併。初始 image CI 兩項進行中、Supabase Preview skipped；文件回填後另查目前 head，不能以本地測試冒稱遠端已通過。任務附加工具 40 秒無回覆，附件列表另等 10 秒也無回覆，**任務附件未確認**；PR 連結、狀態與 head 已由 GitHub 獨立驗證，未宣稱附加成功。未部署或要求索引。
