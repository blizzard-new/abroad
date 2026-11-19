# 2026-11-19 每日雙篇驗收

Asia/Taipei 批次，隔離分支 `codex/seo-daily-20261119`，base main `af32b61d2868923ce66496246def0a4ed6027b7b`。兩篇完整原創繁體中文圖文文章、來源與驗收完成，待同一個新 PR 審閱；未合併、部署或要求索引。

| 文章／候選方向 | slug | 獨立任務 |
| --- | --- | --- |
| 英文催信怎麼寫才有禮貌？用 AI 練追蹤信、明確請求與回覆 Prompt（17：AI 英文學習） | `ai-english-follow-up-email` | 前信、已知／未知、單一請求、禮貌與未定回覆判讀；三輪 Prompt、壞稿／修改稿、完整信及換題。 |
| 托福 Listen to an Academic Talk 怎麼練？主旨、例子與推論的原創短講解析（19：托福準備） | `toefl-listen-to-academic-talk` | 主張／機制／例子／限制；兩段新學術解說與八題解析，處理證據尺度及思想比較，區分機制與精確預測。 |

開始時鐘 2026-11-19 00:00:56 UTC，即台北 11/19 08:00:56。昨日 #398 已合併，柏林登記與多益代名詞兩篇已在 main 並排除重做；merge commit 正是本批 base。#78／#92 已在 main，無未合併基礎相依。讀取最新 workflow、backlog、61 篇庫存與相關正文；祖先與 tracked tree 無 AGENTS。唯一 open #399 的完整說明與 202 個變更檔案已查，另讀 `seo.py` 與 SEO E2E patch：主要為申請流程／合作校資料與快取，閱讀部分只有樣式網址版本號，無 editorial JSON；未複製它的修改。開始前無同日分支／PR，提交前 main／#399 head 未變，最近 100 全狀態 PR 無本日 SEO 批次。

選題是編輯判斷，沒有使用者 Search Console、搜尋量、排名或成效資料。追蹤信與既有文法訂正、正式托福回信任務分工。原考慮公告題，讀完多益 Part 4 後因方法重疊而未產出；改為解說性學術短講，非公告或短對話換皮。它練講者論述的功能與證據邊界，不是看著原文反覆精讀。原 61 篇 JSON、URL、published／modified 位元相同，共 63 篇；10/30 study-plan `97de3fda` 未重做，無三工具實測就不造比較。

兩篇都有直接回答、三點摘要、H1/H2、目錄、表格／清單、原創 HTML 五步圖、FAQ、來源／日期、相關文章及母校／目的地／選校工具連結。沿用 canonical、Article／Breadcrumb JSON-LD、社群、Sitemap、原生 FAQ 與手機橫捲；未改 renderer、CSS 或 JS。

## 來源、教材與限制

11 個文章引用一手來源皆可讀 HTTP 200，實讀相關正文。英文信篇讀 British Council 郵件組織、禮節及稱呼結尾，採目的、分段、必要收件者、附件、大寫及寄前核對原則；不複製其人物故事、完整信、工作紙或留言，也不推論固定回信期限。OpenAI 明確背景／逐輪修改／語氣及自信誤答限制已讀；更新顯示 `last month`／`27 days ago`，保留相對日期，不推定絕對發布日或模型版本。

Lin、11/10 前信、住宿／車次與所有信件皆原創虛構。沒有提早入住核准、寄放保證／免費、已訂房或已訂票、對方今日必回。壞稿故意加入的錯誤均在修改中撤回，請求只問寄放或正確窗口。完整人工信不是模型實測；模擬回覆的「正在查、確認前不能放」不是已核准。三輪填欄 Prompt、事實表、前後修改、模擬回覆與候補換題完整，分層是編輯安排，不是 CEFR 或官方分數。沒有三天／五天通則、回信率或提速保證，也沒有用工具寄信、附檔、查案件；真實材料需本人核對與依規定使用 AI。

托福篇讀 ETS 現行聽力、內容及成績頁，並下載 2026 Update PDF；讀封面、實體第 3 頁（印刷 2）定稿前可微調註記、第 5 頁（印刷 4）Listening 表，另渲染並目視該表。聽力頁導語寫 two task types 卻具名列四項，已交叉核對而不採其導語數字。Academic Talk 為主旨、支持、組織與推論等理解，不套舊制長題組、預估題量／時長／CEFR 或原始點數。2026-01-21 起 1–6 分制及各機構要求已查，未將八題換算正式分數。

EPA 頁尾更新 2026-08-18，核對材料吸放熱、遮蔭／水分與地表／空氣差別；USGS 教材日期 2018-06-05，核對不透水面、入滲、較快逕流與排水到溪流的機制，保留原年，不拿關聯卡片 2026 日期當正文更新。兩段腳本、庭院／樹與同雨量兩地的思想比較皆自寫，不是教授逐字稿、實際研究、EPA／USGS 原例的翻寫、真實校園測量或防災預報；沒有重製來源圖／照片、亞特蘭大房屋故事、歷史洪水或溫差統計。

兩段各四題，合計八題／32 選項；答案 B、D、C、A、D、B、A、C，逐項理由對回腳本。A 段避免單塊表面代表整區空氣，B 段避免機制比較變成精確地方預報；換題允許研究問題改為石頭表面時使用對應表面觀察，並非表面證據一律無用。沒有費用／分數模型或數值換算，題目配置明示教學自訂。未做音檔、口音、語速、ASR 或學生實驗；先不看稿的夥伴朗讀流程可自行練，已看稿須記文字理解，未冒稱真實聽力表現。

## 攝影與閱讀驗收

兩張專用新真實攝影：ANTONI SHKRABA production／Pexels 打字（8374259）、Ulises Peña／Pexels 大學走廊（12512761）；ID 不在既有來源與庫存。核對來源頁 ImageObject、作者、原 JPEG 及 Pexels License，讀網站使用／修改與禁止背書、不當描繪、原樣轉售或素材再分發等限制。1536×1024 WebP 為 90,044／129,384 bytes，低於 450 KB；EXIF 方向、RGB／LANCZOS 中心 fit、quality83／method6，無生成、重繪或變色。alt 符合裁切畫面，圖說不冒稱真實申請者、AI 畫面、寄件／校方回覆、ETS 考場、課堂或科學證據。

15 張最終畫面均目視：桌面 1440、手機 320、兩圖、兩圖解、八段內容、3:2／2:1 裁切。手與鍵盤、磚牆／開窗／燈／中庭護欄保留；中英文、Prompt、完整信、短講、八題解析與推論流程可讀。手機表格實際橫捲，頁面無橫向溢出；長區塊截圖暫隱固定頁首／裝飾線避免拼接遮字，產品頁、完整畫面及斷言未改。

| 檢查 | 實際結果 |
| --- | --- |
| `scripts/check_editorial.py --base-ref origin/main` | 63 篇、0 errors |
| 六模組 SEO 單元／整合／release gate | 190 passed（87.36 秒） |
| 三模組桌面／手機 E2E | 73 passed（219.98 秒） |
| 兩篇 × 320／390／1440、JavaScript 關閉 | 六組通過，含目錄／FAQ、圖片／credit、表格真實橫捲、相關及母校／目的地／工具、canonical／JSON-LD |
| Wheel 逐檔及 checkout 外匯入 | 63 JSON、63 WebP、全部 59 CSS、481 字型目錄檔及閱讀資產，共 667 唯一檔一致；外部載入 63 篇／新 slug |

各檢查一次通過，內容／圖片測前固定、最終雜湊相同，不以重跑膨脹覆蓋。最新 main uv.lock 建隔離 venv，`uv sync --frozen --extra dev` 完成，Python 3.12.14、soupsieve 4.1.1，未改共用 venv。Wheel 2,529,390,190 bytes 留 cache。為建置空間移除自己已完成且乾淨的 11/14、11/15 checkout 及昨日可重建 wheel，保留分支／Git 歷史／PR／來源和驗收證據；未動他人的未提交工作。此為本地驗收，不是已部署、已收錄、搜尋成效或實際 Core Web Vitals。

- [來源版本／HTTP／正文限制](seo-editorial-sources-2026-11-19.json)、[原創信件／短講及題目檢核](seo-editorial-exercises-2026-11-19.json)
- [攝影授權](seo-editorial-photography-2026-11-19.json)、[61 篇原文雜湊](seo-editorial-inventory-2026-11-19.json)、[PR／日期查核](seo-editorial-pr-audit-2026-11-19.json)
- [完整 gate](seo-editorial-checks-2026-11-19.json)、[命令／輸出](seo-editorial-tests-2026-11-19.txt)、[套件逐檔](seo-editorial-package-2026-11-19.json)
- [瀏覽器／15 圖雜湊](seo-editorial-browser-2026-11-19.json)、[桌面](seo-previews-2026-11-19/desktop-1440.jpg)、[手機](seo-previews-2026-11-19/mobile-320.jpg)、[裁切](seo-previews-2026-11-19/photography-crops.jpg)

[PR #400](https://github.com/blizzard-new/abroad/pull/400) 已建立，OPEN、非 draft、MERGEABLE。完整內容 head `4fba144e41af4c41523ef778630abe7246b66564`；後續只回填本驗收、PR audit 與 backlog，產品雜湊不變。此內容 head 兩個 TLS trust regression image 檢查仍進行中，Supabase Preview skipped；不宣稱遠端 CI 全通過，以 PR 最新狀態為準。

任務附加 `codex_app.attach_artifact` 等待 40 秒無回覆，`list_artifacts` 等待 10 秒也無回覆，因此附件未確認；實際 PR URL、head 與待審狀態已另行核對。未宣稱附加成功，未合併、部署或要求索引。
