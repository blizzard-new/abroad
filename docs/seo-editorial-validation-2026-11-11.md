# 2026-11-11 每日雙篇驗收

日期採 Asia/Taipei；開始即時時鐘為 2026-11-11 00:00:07 UTC，即臺灣 11/11 08:00。隔離分支 `codex/seo-daily-20261111`，兩篇完整繁體中文圖文文章同屬本日批次，驗收後建立一個待審 PR。選題依候選方向 17、20 的編輯判斷，沒有使用者 Search Console、搜尋量、流量或排名資料。

| 完整文章 | slug | 獨立實作價值 |
| --- | --- | --- |
| 英文沒聽懂怎麼問？用 AI 練澄清、確認意思與接回對話的 Prompt | `ai-english-clarification` | 三種澄清缺口、三輪可填寫 Prompt、三段原創對話、弱稿修改、錯誤回饋辨識與換題 |
| 多益 Part 1 照片描述怎麼練？可見證據、動作與狀態的原創題解析 | `toeic-part-one-photographs` | 真實授權圖片、同圖兩組四選一、八個選項逐項解析、動作／狀態／位置與主被動改述、換圖訂正 |

## main、待審與去重

基於最新 main `bff878eaf829230e2da1de027652300aa6cad5de`。讀取最新 workflow、backlog、41 篇標題與庫存，重讀 AI 四技能、交換面試、多益聽讀總覽全文。main 的 41 篇 JSON 與前日 main `d7ec093d` 相同，過去已讀的其他題型維持原用途。祖先目錄及最新 Git 追蹤檔案未發現適用 AGENTS.md；#78、#92 的合併 commit 已確認是此 main 的祖先。

開始前沒有同日分支或任何狀態同日 PR。核對全部 29 個 open PR 的完整分頁變更清單及相關文章、前端、展示與目錄的說明。只有 #272、#285 含 editorial JSON，四篇全部視為已選並排除：`ai-english-listening-dictation`、`toefl-academic-reading`、`japan-residence-registration`、`toeic-part-four-talks`。其他僅有稽核提案或不含文章 JSON 的功能／目錄變更；#299、#301 內容未搬入本批。見 [PR 查核](seo-editorial-pr-audit-2026-11-11.json)。

澄清篇深入「指出缺口→提問→回覆→重述→接回行動」的完整互動，與四技能每日安排、面試真實經歷追問、讀寫與聽寫分工；新文有獨立教材與查核流程，不重發總覽。Part 1 處理照片與句子整體關係，與單句應答、圖表對話、獨白與閱讀任務不同，不換品牌或年份重發。10/30 `exchange-study-plan` 原更新 `97de3fda` 未重做；候選 15 無三工具實測，未捏造比較。

原有 41 篇逐位元與基準相同，URL、published、modified／lastmod 保留；本分支共 43 篇，見 [庫存雜湊](seo-editorial-inventory-2026-11-11.json)。沒有修改 schema、renderer、CSS、資料庫或原共用 checkout；新的 main metro／固定導覽列沿用並重新驗收。

## 實讀來源與原創教材

- British Council Checking understanding：讀教材說明、完整 Transcript、練習入口與 A1 標示，不使用使用者留言。重說、放慢、確認指涉作為功能分類；A1 只指該課分類。未聲稱看／聽影片或轉載完整腳本，三段對話獨立自寫。
- OpenAI 提示頁：讀清楚具體背景與迭代修改原則，當日顯示 Updated: 22 days ago；準確性頁讀自信錯答及重要資訊查證，Updated: 19 days ago。保留相對日期，不換算絕對修訂日。沒有模型、方案、地區或語音功能比較／實測主張。
- 三段澄清：Birch Room 只確認名稱，大樓樓層時間仍未知；it 原先不明，後來確認 summary、slides 留原處；short outline 原先可能只有標題，後來確認每個標題下一句。沒有替角色增加期限、許可或真實校規。
- 三輪 Prompt 分別處理來回對話、文字證據回饋、新情境轉用；有填寫欄位。人工預期回覆及錯誤回饋均明示示例；「有禮貌所以可以晚交一天」缺乏證據，已要求刪除。換題 poster／handout 不沿用 summary；沒有文字推估發音、聽力、CEFR 或官方分數。
- TOEIC 官方內容表及 Part 1 directions：六題、每題四敘述、選最符合照片的一句、敘述不印出且只說一次。本文限 Listening & Reading；未替子題型設官方獨立分鐘數，未轉載官方圖片／題目／音檔，也未做官方音訊聽辨測試。
- 實際目視本篇圖片：人物持紙、電腦在桌上開啟、文件在桌面、椅子分開及畫面仍有人。原創兩題答案 A／C，共 2×4＝8 選項已驗算及核對標記。第 1 題 D 改為明確的電腦在桌下說法，排除遠處背景人物辨認可能造成的歧義。
- British Council 文法正文：被動 be＋過去分詞、現在進行被動 is／are being＋過去分詞、完成被動 has／have been＋過去分詞；現在進行式構成、當下活動及其他上下文用途。只用正文與結構表，不用留言。本文不說所有被動／完成句都錯；本題 stacked 不符是因椅子未堆疊。
- 同圖兩組、已讀 alt／觀察提示、文字選項與真正首次聽辨清楚區分；沒有將示例冒稱完整六張模考。holding 改成 being held 保留關係，改成 tearing 增加沒有證據的動作；新圖須有使用權並另留第一次結果。

必要來源及照片／授權頁皆 HTTP 200，未使用官方存檔替代。沒有未核實的金額、期限、資格、獎助或簽證要求。原創對話、題目與人物不是模型輸出、學生心得、訪談、專家審核或實證成效。URL、版本、HTTP、回應大小／雜湊、實讀範圍見 [來源紀錄](seo-editorial-sources-2026-11-11.json)；外部原始回應只留任務 cache。

## 照片與畫面

實讀 Pexels 原照片頁及 License：免費使用／修改、可選署名，以及不得冒犯性使用、暗示背書、原圖轉售、素材平台轉售或商標使用。沿用 fauxels 說明情境照與 Mikhail Nilov 文件閱讀照，真實攝影、1536×1024 WebP、每張低於 450 KB，與 main 逐位元相同。未生成、替換、改色或用紙感插畫；alt、圖說及署名沒有冒稱真實申請者、語伴、考生或校園，見 [攝影紀錄](seo-editorial-photography-2026-11-11.json)。

實際 create_app、拋棄式資料目錄與 Chromium；兩篇各 320／390／1440 px、關閉 JavaScript。H1、canonical、Article／Breadcrumb JSON-LD、目錄跳轉、原生 FAQ、圖片載入／alt／lazy／來源／尺寸、相關文章導覽與母校／目的地／選校工具連結均檢查。手機三個寬表格實際設定 scrollLeft 確認可捲動，整頁無水平溢出。

已目視全部 15 張最終驗收圖，文字、Prompt、圖解及圖說可讀，攝影裁切保留主體。長分段截圖暫時以 screenshot style 隱藏固定 6px 彩條及固定 reading header，避免捲動拼接時蓋入正文；沒有改產品 CSS、文章或驗收斷言。整頁桌機／手機預覽保留原版導覽列與彩條。

- [桌機](seo-previews-2026-11-11/desktop-1440.jpg)、[手機](seo-previews-2026-11-11/mobile-320.jpg)、[3:2／2:1 裁切](seo-previews-2026-11-11/photography-crops.jpg)
- [第一輪 Prompt](seo-previews-2026-11-11/ai-english-clarification-prompt-roleplay-390.jpg)、[三段對話](seo-previews-2026-11-11/ai-english-clarification-original-repair-dialogues-390.jpg)、[回饋與檢查表](seo-previews-2026-11-11/ai-english-clarification-prompt-review-and-check-390.jpg)、[換題與複習](seo-previews-2026-11-11/ai-english-clarification-transfer-and-review-390.jpg)
- [照片兩題](seo-previews-2026-11-11/toeic-part-one-photographs-original-photo-questions-390.jpg)、[逐項解析](seo-previews-2026-11-11/toeic-part-one-photographs-answers-and-visible-evidence-390.jpg)、[動作與狀態](seo-previews-2026-11-11/toeic-part-one-photographs-actions-and-states-390.jpg)、[換圖與紀錄](seo-previews-2026-11-11/toeic-part-one-photographs-transfer-and-record-390.jpg)
- [澄清圖解](seo-previews-2026-11-11/ai-english-clarification-diagram-390.jpg)、[照片題圖解](seo-previews-2026-11-11/toeic-part-one-photographs-diagram-390.jpg)、[說明情境照／圖說](seo-previews-2026-11-11/interview-practice-photo-390.jpg)、[題目照片／圖說](seo-previews-2026-11-11/planning-photo-390.jpg)

## 驗收結果

| 檢查 | 結果 |
| --- | --- |
| `scripts/check_editorial.py --base-ref origin/main` | 最終版通過，43 篇 |
| SEO 單元／整合／release gate 六模組 | 最終版完整重跑 165 passed |
| SEO 文章／頁面／analytics E2E 三模組 | 初跑 53 passed；最終兩篇手機案例另跑 2 passed，不重複計為新覆蓋 |
| 無 JavaScript 桌機／手機閱讀 | 最終六組通過，15 張目視完成 |
| wheel 建置、逐檔核對及 checkout 外載入 | 通過；43 JSON／27 唯一 WebP／全部 56 CSS／481 個字型目錄檔案及其他閱讀資產，共 608 個唯一檔逐位元相同；checkout 外可載入 43 篇及兩個新 slug |

SEO 初跑為 164 passed／1 failed：照片選項校對時，已載入的 ARTICLES 與剛更新的檔案內容不同，觸發 shipped JSON 等價斷言。確認是同次執行中檔案修改的落差，未更改或放寬測試；固定內容後完整六模組重跑 165 passed。瀏覽器亦在最後內容及長截圖方式固定後重新檢查；保留初跑與重跑紀錄。

證據：[結構檢查](seo-editorial-checks-2026-11-11.json)、[原始測試及各跑次](seo-editorial-tests-2026-11-11.txt)、[瀏覽器紀錄](seo-editorial-browser-2026-11-11.json)、[套件 manifest](seo-editorial-package-2026-11-11.json)。本批 wheel 2,411,960,732 bytes，只留任務 cache；字型目錄計數包含其中 CSS，總檔數已去重。瀏覽器結果是實驗室閱讀檢查，不代表實際使用者 Core Web Vitals。

## 待審與發布邊界

待建立本日唯一 PR，兩篇一起審閱。未合併、未部署 Windows 正式環境、未寄信或要求 Google 批次索引；文章與 PR 完成不代表已上線、收錄或排名。
