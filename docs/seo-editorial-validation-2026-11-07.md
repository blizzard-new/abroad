# 2026-11-07 每日雙篇驗收

日期採 Asia/Taipei；即時時鐘為 2026-11-06 23:58 UTC，臺灣已為 11/7，依當日批次處理。隔離分支 `codex/seo-daily-20261107`；兩篇完整繁體中文圖文文章同屬本日唯一 PR，待建立。選題依編輯判斷，沒有使用者 Search Console、搜尋量、流量或排名資料。

| 方向／完整文章 | slug | 獨立實作價值 |
| --- | --- | --- |
| 17：用 AI 改英文作文怎麼做？文法 Prompt、最小修改與原意檢查 | `ai-english-writing-feedback` | 三輪可填寫 Prompt、原創初稿、兩處必要修改、錯誤回饋反例、換情境重寫與人工檢查表 |
| 19：托福 Complete the Words 怎麼練？缺字補全、上下文與原創題解析 | `toefl-complete-the-words` | 兩段原創短文、八個缺字、上下文／詞形解析、保留與新增字母驗算、分級訂正紀錄 |

## 基準與防重複

基於最新 main `b5caecf856c184e349ffaecc2ffc384c6615d9a3`。讀取當期 workflow、backlog、37 篇庫存及相關正文：自然寫作 Prompt、AI 聽說讀寫總覽、AI 閱讀精讀與單字、托福總覽與各任務、多益詞性等。沒有適用 AGENTS.md。開始前所有 open PR 為零，同日任何狀態 PR 為零；提交前再次核對 main 未變、兩份清單仍為零，見 [PR 查核](seo-editorial-pr-audit-2026-11-07.json)。

#78、#92 已合併，無基礎相依。前批 #247 已於 2026-11-06 15:35:12 UTC 合併；其討論寫作及多益詞性兩篇已在 main，視為已選並排除。10/30 `exchange-study-plan` 擴充仍保留原分支 `97de3fda`，未重做；候選 15 沒有三工具實測，不製造比較。下方 backlog 歷史的待審標示為當時狀態，以本日盤點為準。

AI 篇深入英文回饋的文法／風格／意思分流與改稿核對；自然寫作篇保留素材、結構與個人語氣，總覽保留四技能安排，閱讀／單字篇各有不同練習。托福篇處理短文中部分字母補全、語篇與拼字的交叉判斷；與多益四選一詞性、托福給定片段組句及其他完整任務不同。兩篇不是換年份、品牌或標題重發總覽。

[庫存雜湊](seo-editorial-inventory-2026-11-07.json) 證明原 37 篇 JSON 逐檔與基準相同，URL、published、modified／lastmod 保留。本批共 39 篇；沒有改 renderer、CSS、schema、資料庫或共用 checkout。

## 實讀來源與示例查核

- 實讀 OpenAI Prompt 與準確性說明：清楚任務、背景、逐輪修訂及回答可能錯誤／肯定語氣不保證準確。頁面分別顯示 Updated: 18 days ago／15 days ago，保留相對標示，不倒推確切修訂日。未宣稱實測工具版本、方案、地區、語音、上傳、記憶、提醒或品牌效果。
- 實讀 British Council 過去簡單式、現在完成式及 may／might 的教學本文，沒有依賴留言。確認 meet／met、已發生事件、have＋過去分詞、否定句 yet 與可能性用法；未見固定修訂日期，揭露 11/7 當日版本。原路徑會轉向現行 free-resources 路徑，來源紀錄保留 requested／resolved URL。
- 初稿與情境均自編：開會及決定在過去，測試在寫作當下的下週，改期限仍不確定，教室目前仍未訂。參考修改只將 meet→met、decide→decided；保留 might 與 have not booked ... yet。故意錯稿將不確定改成 confirmed／will、未訂改成 booked，明示不是任何模型的真實輸出。換題 finished／have not checked 也分別對照過去事件及現在未完成狀態。
- 實讀 ETS 現行 Reading 任務說明及 2026 Update 規格印刷頁 7–8：以短文補全部分缺字，結合字彙、拼字、詞形、語法與上下文。未聲稱逐頁審閱整份 PDF，未把估計時間、原始點數、缺字比例或本篇符號顯示方式當成正式考試規定。
- 實讀 ETS 成績頁 January 2026 章節：2026-01-21 起 1–6 半分尺度，兩年過渡另有可對照的 0–120 整體分數。自編題目不換算官方成績，不承諾滿分、難度校準或提分幅度。
- 兩段短文與八個預期答案均為 UniWay 自編，未轉載官方題目：notice、explained、equipment、summary、include、received、complete、future。逐項以程式核對保留字母＋新增字母＝答案、底線數＝新增字母數及表格總數；八項皆成立。上下文另外人工核對，特別區分過去敘事、asked us to／could 後原形與不可數 equipment。
- 本篇每條底線代表一個缺字及保留的字首，是自編練習標記，並非 ETS 固定比例、題數或介面。替代答案仍須符合整句意思與字母限制，不把作者預期答案視為官方唯一性認證。分級為編輯安排，非 CEFR 或官方校準。

所有必要來源均 HTTP 200，沒有存檔替代、連線失敗或尚未核實的費用、資格、期限、獎助或簽證主張。可核對 URL、版本、HTTP 狀態、回應 SHA-256、實讀範圍與限制見 [來源紀錄](seo-editorial-sources-2026-11-07.json)。原始來源回應留於任務 cache，未將外部原文複製入 Git。

## 攝影與閱讀畫面

重新讀取兩張 Pexels 原照片頁及 License，確認免費使用／修改、可選署名與使用限制；實際提供攝影者署名。沿用 PNW Production 書寫照、Roxanne Minnish 耳機學習照，1536×1024 WebP，88,086／121,464 bytes，皆低於 450 KB，原像素不變。沒有新增生成圖或沿用舊紙感插畫。alt、圖說與來源明示素材情境，沒有聲稱本文 AI 操作、真實考生／考場、虛構課程參與者或學習成果；見 [攝影授權](seo-editorial-photography-2026-11-07.json)。

使用實際 `create_app`、拋棄式資料目錄及 Chromium，關閉 JavaScript；兩篇各 320／390／1440 px，共六組。核對 H1、canonical、Article／Breadcrumb JSON-LD、目錄跳轉、原生 FAQ、圖片與來源／alt／lazy／尺寸、相關文章、母校／目的地／選校工具。手機每個寬表格實際改變 scrollLeft，確認可橫向閱讀；頁面本身無水平溢出。已目視檢查桌機、手機、兩圖解、全部主要英文例句與解析、攝影及圖說；3:2／2:1 裁切主體保留。這些是實驗室閱讀檢查，不是實際使用者 Core Web Vitals。

- [桌機](seo-previews-2026-11-07/desktop-1440.jpg)、[手機](seo-previews-2026-11-07/mobile-320.jpg)、[圖片裁切](seo-previews-2026-11-07/photography-crops.jpg)
- [AI 初稿](seo-previews-2026-11-07/ai-english-writing-feedback-original-draft-390.jpg)、[最小修改與圖解](seo-previews-2026-11-07/ai-english-writing-feedback-prompt-two-and-revision-390.jpg)、[錯誤回饋](seo-previews-2026-11-07/ai-english-writing-feedback-check-bad-feedback-390.jpg)、[換題](seo-previews-2026-11-07/ai-english-writing-feedback-prompt-three-and-transfer-390.jpg)
- [缺字短文](seo-previews-2026-11-07/toefl-complete-the-words-original-text-390.jpg)、[逐題解析與圖解](seo-previews-2026-11-07/toefl-complete-the-words-answers-and-letter-check-390.jpg)、[第二段與驗算](seo-previews-2026-11-07/toefl-complete-the-words-transfer-text-390.jpg)
- [書寫照片與圖說](seo-previews-2026-11-07/writing-photo-390.jpg)、[閱讀照片與圖說](seo-previews-2026-11-07/english-guide-photo-390.jpg)

## 驗收

| 檢查 | 結果 |
| --- | --- |
| `scripts/check_editorial.py --base-ref origin/main` | 通過，39 篇 |
| SEO 單元／整合／release gate 六模組 | 161 passed |
| SEO E2E 三模組 | 初跑 48 passed／1 navigation timeout；單一失敗案例重跑 1 passed；文章模組完整重跑 41 passed，其餘 8 項初跑已通過 |
| 兩篇無 JavaScript 桌機／手機閱讀 | 六組通過，目視完成 |
| `uv build --wheel` 與內容核對 | 通過，39 JSON／27 唯一 WebP／CSS／renderer／init 共 69 檔逐位元相同 |
| checkout 外載入抽出套件 | 通過，39 篇與兩個新 slug 可載入 |

首次 E2E 失敗為既有 exchange-budget→japan-exchange-cost→目的地導覽的 390 px 案例：連結可見且 click 已完成，等待目的地導航超過 30 秒。其他 48 項通過。未改文章、renderer、測試或 timeout，單獨重跑通過；完整文章模組再跑 41 passed，搭配初跑已通過的另外兩模組 8 項，49 個案例均已有通過紀錄。不把首次失敗隱藏或把可能的資源／時序因素寫成已證實原因。

證據見 [release gate](seo-editorial-checks-2026-11-07.json)、[測試原始紀錄](seo-editorial-tests-2026-11-07.txt)、[瀏覽器紀錄](seo-editorial-browser-2026-11-07.json)、[套件 manifest](seo-editorial-package-2026-11-07.json)。wheel 為 2,407,275,437 bytes，留於任務 cache，未提交 Git。

## 待審與發布邊界

本日唯一 PR 待建立，兩篇一起審閱。沒有合併、Windows 正式部署、寄信或要求 Google 批次索引；產文、PR 與本機驗收不代表已上線、收錄或排名。
