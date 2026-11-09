# 2026-11-09 每日雙篇驗收

日期採 Asia/Taipei；即時時鐘為 2026-11-09 00:01 UTC，即臺灣 11/9 08:01。隔離分支 `codex/seo-daily-20261109`，兩篇完整繁體中文圖文文章同屬本日唯一 PR，待建立。選題依使用者方向 17、19 的編輯判斷，沒有使用者 Search Console、搜尋量、流量或排名資料。

| 完整文章 | slug | 獨立實作價值 |
| --- | --- | --- |
| 用 AI 練英文聽力怎麼做？聽寫 Prompt、漏聽分類與重聽訂正 | `ai-english-listening-dictation` | 三輪可填寫 Prompt、原創參考稿與錯稿、否定遺漏對照、回到音訊的核對流程、朗讀者保管新稿與新材料驗收 |
| 托福學術閱讀怎麼練？主旨、細節與推論的原創題目解析 | `toefl-academic-reading` | 兩段原創科學短文、六題四選一、主旨／細節／字彙／有限推論解析、原理與假設比較的區分、錯因紀錄 |

## 基準與去重

基於最新 main `aeb46b7089b3c4a180a7c4fad1fae02bfee08b5a`。實讀當期 workflow、最新 backlog 與 41 篇標題庫存；重讀 AI 四技能總覽、AI 精讀、交換面試等相關正文。既有托福總覽、缺字及其他任務正文已核對並排除。沒有適用 AGENTS.md，含祖先目錄與 Git 追蹤檔案查核。

全部四個 open PR #267、#269、#270、#271 的說明及完整分頁檔案清單已查核，沒有新增 editorial JSON；分別為校務提案、未合併前端設計與兩個校務型錄。沒有把待審分支當成已生效版型。開始前無同日分支／任何狀態同日 PR，見 [PR 查核](seo-editorial-pr-audit-2026-11-09.json)。#78、#92 已合併；#255、#266 也分別於 11/8 07:15:26／07:17:10 UTC 合併，四篇已在 main，排除重做。下方 backlog 歷史的待審字樣以本日查核為準。

10/30 `exchange-study-plan` 擴充仍保留原分支 `97de3fda`，沒有重做；候選 15 無可核對的三工具實測，未製造比較。本批直接沿用 main，沒有未合併基礎相依。

聽寫篇處理不先看稿的首次聽辨、空白與不確定處、文字差異及回到原音訊確認；與可見文字的精讀、本人作文改稿、四技能時間安排及面試對話分工。學術閱讀篇深入主旨、支持與推論範圍，以有科學來源的新材料及六題完整解析教學，與部分字母補全、AI 回饋流程及總覽不同。不是換品牌、年份或標題重發。[庫存雜湊](seo-editorial-inventory-2026-11-09.json) 證明原 41 篇 JSON 逐檔與基準相同，URL、published、modified／lastmod 保留；本分支共 43 篇。沒有改 renderer、schema、CSS、資料庫或原共用 checkout。

## 實讀來源與示例邊界

- 實讀 OpenAI Prompt 明確背景與逐輪修訂、準確性頁錯誤資訊／捏造引文／肯定語氣限制。當日相對標示為 Updated: 20 days ago／17 days ago，保留而不倒推確切修訂日。未作模型、方案、地區、語音、上傳或工具效果比較。
- 實讀 British Council 聽力頁的練習指示、Transcript、Task 1／2 與 B1 標示。官方音檔 HTTP 200、3,524,444 bytes，僅核對可取得，沒有播放聽辨、音質、ASR 或難度實測。文章連回原站，不嵌入或轉載其音檔、對話、題目；B1 只描述該官方頁面，不套用本人或自編短句。
- 原創聽寫例：離開前將藍色資料夾放在桌上，聽者不必印筆記，說話者會帶一份。自編錯稿留空 before you go、漏掉 don't，分別失去時間關係及反轉列印行動。可由文字確認差異，聲音原因仍須實際重聽，不斷言連音、口音或弱讀原因。
- 換稿為 office opens 之後可取鑰匙、door is locked 時依通知號碼聯絡；沒有真實開門時間或電話。第三輪由朗讀者操作並保管新稿，自己先看過新稿就不能稱首次聽力。工作紙是可執行練習方法及文字訂正示例，未提供配音或虛構學生聽寫結果。
- 實讀 ETS 現行 Reading 主旨／支持細節／字彙，以及作答資訊在文內、不需主題先備知識的說明；實讀 2026 Update 閱讀章節印刷頁 7–9 的主旨、支持資訊、跨句與推論能力。不是逐頁閱讀整份 PDF，不以 TextEvaluator、CEFR、固定字數或單題時間校準自編題目。
- 實讀 ETS January 2026 成績章節：2026-01-21 起 1–6 半分尺度，兩年過渡另有可對照的 0–120 整體分數。六題答對數、速度及自評均不換算正式分數。
- 實讀 EPA 熱島原因與特性（頁面 Last updated August 18, 2026）及植被 How Trees and Vegetation Reduce Heat（Last updated May 15, 2026）。核對表面吸收／慢慢釋熱、植被遮蔭、蒸散利用熱、風、建築配置及城內差異。兩段英文獨立重寫，沒有轉載官方原段、降溫數值、健康統計、成本或研究結果；也未宣稱追讀 EPA 所引文獻。
- 第二段兩街道同時在樹量、配置與風有差異，是原創假設比較，不是 EPA 實驗或觀測。文字不支持把全部差異歸給樹，沒有捏造城市、樣本數、溫度、受訪者或實驗結果。
- 六題答案為 B、C、A、D、B、C：主旨同時涵蓋表面與地方條件；細節支持慢慢釋熱；城內差異支持 may differ；release 在此為 give off；假設比較要考慮其他條件；遮蔭與蒸散段落在解釋機制。逐題核對原句、錯項範圍與因果，6×4＝24 個選項及答案標示已用程式核對。不是官方出題、真實 AI 輸出、學生心得、專家審核或已校準能力。

所有必要來源均 HTTP 200，未見固定修訂日的頁面揭露當日版本。沒有存檔替代或尚未核實的費用、期限、資格、獎助、簽證主張。可核對 URL、版本、讀取範圍、HTTP、回應 SHA-256、音檔可取得與未實測限制見 [來源紀錄](seo-editorial-sources-2026-11-09.json)。原始來源回應只留在任務 cache，不提交外部原文或音檔入 Git。

## 圖片與實際閱讀畫面

重新實讀 Pexels 原照片頁與 License，確認免費使用／修改、可選署名及不可暗示背書、冒犯性使用、原圖轉售、素材平台轉售與商標使用限制。沿用 Roxanne Minnish 耳機學習照與 PNW Production 書寫照，1536×1024 WebP，121,464／88,086 bytes，均低於 450 KB；逐位元證明照片未更改，沒有生成、替換、改色或沿用舊紙感插畫。alt、圖說及攝影者署名揭露素材情境，不稱真實參與者、校園、音訊、考試或學習成效，見 [攝影紀錄](seo-editorial-photography-2026-11-09.json)。

使用實際 create_app、拋棄式資料目錄與 Chromium；兩篇各 320／390／1440 px、關閉 JavaScript，共六組。核對 H1、canonical、Article／Breadcrumb JSON-LD、目錄跳轉、原生 FAQ、圖片載入／alt／lazy／來源／尺寸、相關文章及母校／目的地／選校工具。手機寬表格實際改變 scrollLeft 確認可讀，頁面本身不水平溢出。已目視全部 15 張截圖，原創圖解與英中例句清楚，3:2／2:1 裁切保留照片主體。

- [桌機](seo-previews-2026-11-09/desktop-1440.jpg)、[手機](seo-previews-2026-11-09/mobile-320.jpg)、[圖片裁切](seo-previews-2026-11-09/photography-crops.jpg)
- [聽寫原稿與錯稿](seo-previews-2026-11-09/ai-english-listening-dictation-original-dictation-390.jpg)、[比對 Prompt 與圖解](seo-previews-2026-11-09/ai-english-listening-dictation-prompt-two-and-relisten-390.jpg)、[錯誤回饋](seo-previews-2026-11-09/ai-english-listening-dictation-check-feedback-limits-390.jpg)、[換稿](seo-previews-2026-11-09/ai-english-listening-dictation-prompt-three-and-transfer-390.jpg)
- [學術短文一](seo-previews-2026-11-09/toefl-academic-reading-original-passage-390.jpg)、[題 1–4](seo-previews-2026-11-09/toefl-academic-reading-questions-one-to-four-390.jpg)、[解析與圖解](seo-previews-2026-11-09/toefl-academic-reading-answers-and-boundaries-390.jpg)、[第二段與題 5–6](seo-previews-2026-11-09/toefl-academic-reading-transfer-passage-390.jpg)
- [聽力篇照片與圖說](seo-previews-2026-11-09/english-guide-photo-390.jpg)、[閱讀篇照片與圖說](seo-previews-2026-11-09/writing-photo-390.jpg)

## 驗收

| 檢查 | 結果 |
| --- | --- |
| `scripts/check_editorial.py --base-ref origin/main` | 通過，43 篇 |
| SEO 單元／整合／release gate 六模組 | 165 passed |
| SEO 文章／頁面／analytics E2E 三模組 | 53 passed，無重跑 |
| 無 JavaScript 桌機／手機閱讀 | 六組通過，目視完成 |
| wheel 與套件核對／checkout 外載入 | 通過，43 JSON／27 唯一 WebP／CSS／renderer／init 共 73 檔逐位元相同；checkout 外可載入 43 篇及兩個新 slug |

證據見 [結構檢查](seo-editorial-checks-2026-11-09.json)、[測試紀錄](seo-editorial-tests-2026-11-09.txt)、[瀏覽器紀錄](seo-editorial-browser-2026-11-09.json)、[套件 manifest](seo-editorial-package-2026-11-09.json)。本批 wheel 為 2,407,307,641 bytes，留於任務 cache，未提交 Git。瀏覽器驗收是實驗室閱讀檢查，不代表實際使用者 Core Web Vitals。

## 待審與發布邊界

本日唯一 PR 待建立，兩篇一起審閱。沒有合併、Windows 正式部署、寄信或要求 Google 批次索引；文章完成、PR 與本機驗收不代表已上線、收錄或排名。
