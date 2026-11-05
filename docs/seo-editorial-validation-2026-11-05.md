# 2026-11-05 每日雙篇驗收

日期採 Asia/Taipei。新增兩篇完整繁體中文圖文文章，選題依編輯判斷，沒有使用者提供的 Search Console、搜尋量或排名資料。隔離分支 `codex/seo-daily-20261105`，兩篇同屬一個 PR，PR 待建立。

| 方向／獨立問題 | slug | 本篇新增的實作價值 |
| --- | --- | --- |
| 19：托福 Build a Sentence 怎麼練？句子主幹、問句語序與原創組句題 | `toefl-build-a-sentence` | 六題原創組句、固定框架、直接／間接／主詞問句、子句、錯句修改及分級訂正表 |
| 20：多益 Part 2 怎麼練？問答意圖、間接應答與原創題目解析 | `toeic-part-two-responses` | 七題原創應答、回應功能與同字干擾解析、間接回答、否定問句及首聽／看稿／重聽紀錄 |

## 防重複與實作範圍

基於最新 main `aa29dacc31eadbb02460c757d743786ca5b7d817`。讀取當期 workflow、backlog、31 篇文章庫存及相關正文：托福總覽、Write an Email、多益聽讀總覽；核對所有四個 open PR 的說明與完整變更檔案清單。#233 是 11/4 待審的單字及 Part 3 圖表兩篇，均已選並排除；#234、#236、#237 只含學校稽核 proposal JSON，沒有 editorial 文章。沒有同日其他分支／任何狀態 PR。詳見 [PR 查核](seo-editorial-pr-audit-2026-11-05.json)。

基礎 #78 與流程 #92 已合併。本批直接沿用 main，不依賴 #233；相關文章清單只指向基準已存在的 slug。#213、#222 的四篇已在 main，沒有重做。10/30 讀書計畫更新仍保留於原分支 `97de3fda`；候選 15 沒有三工具實測，沒有製造比較。

托福總覽保留版本、四科、分數與讀書安排，郵件篇保留收件關係及多段任務；本篇深入給定字詞的句子層次重組。多益總覽保留全卷診斷／安排，Part 7 保留跨文件證據，待審 Part 3 保留對話與圖表；本篇深入單句題幹與應答關係。新增完整練習與解析，沒有以品牌或年份改標題重發。

原有 31 篇 JSON 與 Git 基準逐檔相同，URL、published、modified／lastmod 不變，見 [庫存雜湊](seo-editorial-inventory-2026-11-05.json)。本分支共 33 篇。沒有修改 renderer、CSS、schema、資料庫或共用 checkout 的未提交變更。

## 來源、版本與數學／示例核對

- 實讀 ETS 寫作頁、內容表及 2026 Update 規格文件的寫作相關段落，核對排列字詞／片語成完整句或問句，以及句構與情境範圍。未將文件中的預估題數、原始點數或網頁的基礎時間作每題固定秒數／分數換算。
- 實讀 ETS 成績頁的 January 2026 更新段落：2026-01-21 起採 1–6、半分級距，最高 6，兩年過渡期間另給可對照的 0–120 整體分數。本頁六題完全不估官方分數。
- 實讀 British Council《Questions and negatives》的文法本文，核對一般／wh 問句、who 作主詞及間接問句。舊路徑轉向現行 free-resources URL，未用留言區作依據。原先嘗試的兩個 Question forms 網址回應 404，未引用；另取回的 Reported speech 頁未使用，沒有當成已讀依據。
- 實讀臺灣多益官方內容表及 Part 2 directions：25 題，題幹可能是問題或陳述，三個英文回應，不印文字，播一次。頁面確有音檔連結，但官方音訊**未聆聽或轉錄**，沒有把它當成本篇原創對話的依據。
- 六題自編組句逐題驗證：提供字詞與參考答案的詞語計數相同、每個片段保持連續、固定前綴保留；再依情境核對語意與語序。各片段用一次是本頁自編規則，不宣稱是官方所有題目的共同規則。
- 七題自編應答答案依次為 **A、B、A、C、A、A、B**。第 4 題只表示將查信，第 5 題只表示將通知技師，第 7 題只表示自願帶領，未推成已取得房號、完成維修或已抵達。
- 題目、人物、回應、解析與錯句均為 UniWay 自編教學；沒有模型實測、學生訪談、官方題庫、專家審核、CEFR 校準或保證成績。沒有費用／期限／語言採認主張與假設統計。實際閱讀範圍、回應雜湊、版本與限制見 [來源紀錄](seo-editorial-sources-2026-11-05.json)。

## 圖片與閱讀畫面

重新讀取 Pexels 原始照片頁與 License。沿用 Zen Chung 的戶外寫作照及 kaboompics.com 的筆記照，1536×1024 WebP，111,030／167,686 bytes，皆低於 450 KB，像素不變。新增主題 alt／圖說並保留攝影者／來源；沒有冒稱真實托福／多益考生、考場、申請者或學習成果。詳見 [攝影與授權紀錄](seo-editorial-photography-2026-11-05.json)。

用實際 `create_app`、拋棄式資料目錄與 Chromium，關閉 JavaScript，兩篇各測 320／390／1440 px，共六組。檢查 H1、canonical、Article／Breadcrumb JSON-LD、目錄跳轉、FAQ、圖片 alt／lazy／來源／尺寸、相關文章與母校／目的地／選校工具連結。手機表格實際改變 scrollLeft 確認可捲動，頁面沒有水平溢出。目視預覽後補上英文參考答案引號，重新產生最終截圖並驗收。

- [桌機](seo-previews-2026-11-05/desktop-1440.jpg)、[手機](seo-previews-2026-11-05/mobile-320.jpg)、[3:2／2:1 裁切](seo-previews-2026-11-05/photography-crops.jpg)
- [托福組句題](seo-previews-2026-11-05/toefl-build-a-sentence-guided-practice-390.jpg)、[解析與圖解](seo-previews-2026-11-05/toefl-build-a-sentence-answers-and-clauses-390.jpg)、[換題](seo-previews-2026-11-05/toefl-build-a-sentence-transfer-practice-390.jpg)
- [多益題 1–4](seo-previews-2026-11-05/toeic-part-two-responses-original-questions-390.jpg)、[解析與圖解](seo-previews-2026-11-05/toeic-part-two-responses-answers-and-distractors-390.jpg)、[換題 5–7](seo-previews-2026-11-05/toeic-part-two-responses-transfer-questions-390.jpg)
- [托福篇照片與圖說](seo-previews-2026-11-05/toefl-study-photo-390.jpg)、[多益篇照片與圖說](seo-previews-2026-11-05/toeic-preparation-photo-390.jpg)

## 最終自動驗收

| 檢查 | 結果 |
| --- | --- |
| `scripts/check_editorial.py --base-ref origin/main` | 通過，33 篇 |
| SEO 單元／整合／release gate 六模組 | 149 passed |
| SEO 文章／頁面／analytics E2E 三模組 | 43 passed |
| 無 JavaScript 桌機／手機檢查 | 六組通過，目視完成 |
| `uv build --wheel`、套件比對、checkout 外載入 | 通過；33 JSON、27 張唯一 WebP、CSS／renderer／init 共 63 檔逐位元相同；checkout 外載入 33 篇含新 slug 成功 |

保留 [release gate 輸出](seo-editorial-checks-2026-11-05.json)、[測試紀錄](seo-editorial-tests-2026-11-05.txt)、[瀏覽器紀錄](seo-editorial-browser-2026-11-05.json) 與 [wheel manifest](seo-editorial-package-2026-11-05.json)。wheel 不提交 Git。

## 待審與發布邊界

PR 待建立。兩篇一起審閱，沒有合併、Windows 正式部署、寄信或要求 Google 批次索引。完成 PR 與本機驗收不代表已上線、收錄或具有排名；自編練習及一般學習建議不取代正式成績與使用者審稿。
