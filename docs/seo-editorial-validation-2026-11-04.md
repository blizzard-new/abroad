# 2026-11-04 每日雙篇驗收

日期採 Asia/Taipei。新增兩篇完整原創繁體中文文章，選題依編輯判斷；沒有使用者提供的 Search Console、搜尋量或排名資料。兩篇同屬 `codex/seo-daily-20261104`，PR 待建立。

| 候選方向 | 完整文章 | slug | 主要新增價值 |
| --- | --- | --- | --- |
| 17 AI 英文學習 | 用 AI 背英文單字怎麼練？回想測驗、情境造句與複習 Prompt | `ai-english-vocabulary-practice` | 三輪可填寫 Prompt、borrow／lend／return 用法卡、三個回想情境、角色反向訂正、延後複習表與新情境驗收 |
| 20 多益聽讀 | 多益 Part 3 圖表題怎麼練？預讀圖表、聽力定位與原創題組 | `toeic-part-three-graphics` | 四列原創取件圖表、雙人對話、三題與證據鏈、時間用途辨別及替換對話練習 |

## 範圍與防重複

基於最新 main `f081c6b489c6d020850b5a66b584b6e920005104`。開始前與建立 PR 前核對全部 open PR，結果為零；同日 head 的所有狀態 PR 也為零。#78、#92 已合併，直接沿用 main，不需未合併基礎分支。#213、#222 已合併，其四篇視為已選並排除；下方歷史 backlog 的「待審」僅代表當時狀態。詳見 [PR 查核](seo-editorial-pr-audit-2026-11-04.json)。

盤點 main 31 篇，重讀相關總覽、11/3 閱讀精讀及 11/2 跨篇閱讀正文。單字篇處理提取、搭配、詞形與語意方向；原 `ai-english-learning` 保留每日聽說讀寫安排，`ai-english-reading-practice` 保留單段文本證據。Part 3 篇處理聽到的條件如何定位圖表，原多益總覽保留全卷診斷／計畫，Part 7 篇保留書面跨文件連結。沒有為品牌、年份或同一問題重建近似頁。

10/30 `exchange-study-plan` 更新保留在原分支 `97de3fda`，本批未重做。候選 15 未取得三工具實測，不製造比較。原有 31 篇 JSON 逐檔對 Git 基準核對相同，URL、published、modified／lastmod 均保留，見 [庫存紀錄](seo-editorial-inventory-2026-11-04.json)。原共享 checkout 與其他分支保留；在本批獨立 worktree 實作。

## 來源與示例查核

- 單字：實讀 Merriam-Webster 三個原始詞條的相關義項、詞形及句式；核對借入／借出／歸還方向。Cambridge 原計畫四頁回應 403，已捨棄，沒有把阻擋頁當成字典來源，也未繞過封鎖。
- 學習原則：實讀 IES／WWC 官方摘要與連結 PDF 的分散學習、測驗／提取及回饋相關段落。版本為 **2007 年 9 月**，只支持一般學習原則，未說成本文 AI Prompt 的效果試驗、固定複習天數或進步保證。
- Prompt：實讀 OpenAI 提示與準確性說明，當日相對更新標籤分別為 15 days ago、12 days ago；未反推精確修訂日。沒有方案、地區、語音、上傳、提醒功能或模型可靠度比較。
- 多益：實讀臺灣官方內容頁與 Part 3 directions／題型範例，並目視官方連結圖表。39 = 3 × 13；兩人或以上、每段三題、對話播一次及圖表參照題皆核對。頁面未載明固定修訂日，適用範圍為 2026-11-04 所見現行範例，未外推固定圖表題數。官方音檔僅驗證可下載，**未聆聽或轉錄**，未以它支持對話內容。
- 所有教學人物、Prompt、回饋、圖表、選項、對話與預期答案為自編示例，沒有冒稱實際模型輸出、學生故事、官方試題、專家審核或已校準等級。本頁沒有自編音檔，清楚區分看稿分析、同伴朗讀及官方音訊練習。
- 題組逐項核對：原題答案 A／B（P18）／A；11:30 可取件與 12:00 保留期限分開。換題為 P31、12:30 取件、13:00 保留；提早到 12:00 未獲接受。沒有推定現在時間、研討課結束時間或已完成保留。沒有費用試算、語言採認保證或非官方分數換算。

可核對的來源 URL、版本、HTTP 狀態、回應 SHA-256、支持主張、讀取範圍與存取限制見 [來源紀錄](seo-editorial-sources-2026-11-04.json)。原始官方媒體與回應保留於本機任務 cache，不轉載入專案。

## 圖片與閱讀畫面

重新讀取兩張 Pexels 原始頁與 License，沿用既有攝影原檔，未生成或替換圖片。照片分別為 Roxanne Minnish 的筆電學習情境及 kaboompics.com 的筆記情境；1536×1024 WebP、121,464／167,686 bytes，皆低於 450 KB。文章給定主題 alt、素材情境圖說、攝影者及來源，不當成真實考生／申請者、學習成果或校園認證。授權及雜湊見 [攝影紀錄](seo-editorial-photography-2026-11-04.json)。

使用實際 `create_app` 與拋棄式資料目錄、Chromium、關閉 JavaScript，兩篇各測 320／390／1440 px 共六組。檢查 H1、canonical、Article／Breadcrumb JSON-LD、目錄跳轉、原生 FAQ、圖片載入／alt／尺寸／lazy／來源、相關文章導覽與母校／目的地／選校工具連結。手機表格實際改變 scrollLeft 驗證可捲動，頁面本身沒有水平溢出；桌機表格完整呈現。詳見 [瀏覽器結果](seo-editorial-browser-2026-11-04.json)。

撰文代理已實際目視以下截圖，文字、圖解、來源與照片可讀，並檢查 3:2／2:1 裁切保留適切主體：

- [桌機 1440 px](seo-previews-2026-11-04/desktop-1440.jpg)、[手機 320 px](seo-previews-2026-11-04/mobile-320.jpg)、[攝影裁切](seo-previews-2026-11-04/photography-crops.jpg)
- [單字 Prompt](seo-previews-2026-11-04/ai-english-vocabulary-practice-prompt-card-390.jpg)、[回想練習](seo-previews-2026-11-04/ai-english-vocabulary-practice-recall-before-feedback-390.jpg)、[訂正與圖解](seo-previews-2026-11-04/ai-english-vocabulary-practice-revision-example-390.jpg)
- [多益圖表](seo-previews-2026-11-04/toeic-part-three-graphics-original-graphic-390.jpg)、[三題](seo-previews-2026-11-04/toeic-part-three-graphics-three-questions-390.jpg)、[對話](seo-previews-2026-11-04/toeic-part-three-graphics-original-dialogue-390.jpg)、[解析與圖解](seo-previews-2026-11-04/toeic-part-three-graphics-answers-and-evidence-390.jpg)
- [單字篇攝影與圖說](seo-previews-2026-11-04/english-guide-photo-390.jpg)、[多益篇攝影與圖說](seo-previews-2026-11-04/toeic-preparation-photo-390.jpg)

## 自動驗收與套件

| 檢查 | 結果 |
| --- | --- |
| `scripts/check_editorial.py --base-ref origin/main` | 通過，33 篇；新文正文 5,791／5,678 字元，非依字數填充 |
| SEO 單元／整合及 release gate 六個模組 | 149 passed |
| SEO 文章／頁面／analytics E2E 三個模組 | 43 passed |
| 無 JavaScript 桌機／手機閱讀 | 六組通過，目視已完成 |
| `uv build --wheel` 與抽出套件驗證 | 通過；33 JSON、27 張唯一 WebP、CSS／renderer／init 共 63 檔逐位元相同 |
| checkout 外的套件載入 | 通過；33 篇可載入且包含兩個新 slug |

檢查輸出見 [editorial gate](seo-editorial-checks-2026-11-04.json)、[測試紀錄](seo-editorial-tests-2026-11-04.txt)、[wheel manifest](seo-editorial-package-2026-11-04.json)。wheel 為本批實際建置的 2,372,172,067 bytes 檔案，沒有提交至 Git。未修改 renderer、CSS、schema 或資料庫。

## 待審與發布邊界

PR 待建立。兩篇須一起審閱。沒有合併、部署 Windows 正式機、寄信或要求 Google 批次索引；PR 與套件驗收不代表已上線、收錄或具有排名。沒有假裝模型實測或已核對未聽取的音訊；其餘必要來源與檢查若有失敗會另列，以上未取代使用者的內容審閱。
