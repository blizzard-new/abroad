# 2026-11-10 每日雙篇驗收

日期採 Asia/Taipei；開始時即時時鐘 2026-11-10 00:03:59 UTC，即臺灣 11/10 08:03。隔離分支 `codex/seo-daily-20261110`，兩篇完整繁體中文圖文文章同屬本日唯一 [PR #285](https://github.com/blizzard-new/abroad/pull/285)，待審、尚未合併。選題依使用者候選方向 6、20 的編輯判斷，沒有使用者 Search Console、搜尋量、流量或排名資料。

| 完整文章 | slug | 獨立實作價值 |
| --- | --- | --- |
| 日本交換生住址登記怎麼辦？以新宿區為例，核對文件、期限與窗口 | `japan-residence-registration` | 辨認自治體與程序、官方版本差異、卡片與家庭文件條件、可填寫詢問範本、假設案例與辦理紀錄 |
| 多益 Part 4 怎麼練？簡短獨白的目的、關鍵資訊與原創題組解析 | `toeic-part-four-talks` | 兩段原創獨白、六道四選一及解析、局部限制／否定／未指派狀態、條件換題與分級訂正 |

## main、待審與去重

基於最新 main `d7ec093dbf1abfdfff8aece59c37b09256901800`。讀取 workflow、backlog 與 41 篇庫存，重讀抵達第一週、日本預算、多益總覽、Part 3 圖表對話相關正文。祖先目錄及追蹤檔案未發現適用 AGENTS.md。使用獨立 worktree，保留原共用 checkout；未搬入待審前端變更或改寫 publishing renderer。

全部 14 個 open PR #267、#270–#277、#279、#281–#284 的說明及完整分頁檔案清單均已核對。只有 #272 含 editorial JSON：`ai-english-listening-dictation` 與 `toefl-academic-reading`，兩題已選並排除，保持原批次。本批不依賴 #272。#78、#92 已合併；#255、#266 的四篇已在 main。開始前無同日分支／任何狀態同日 PR，見 [PR 查核](seo-editorial-pr-audit-2026-11-10.json)。10/30 `exchange-study-plan` 更新保留原分支 `97de3fda`；候選 15 沒有三工具實測，不製造比較。

新宿區程序深入地址所屬、文件條件、受理確認及完成紀錄，既有第一週指南維持整體抵達安排，日本費用文維持預算用途。Part 4 處理單人談話的目的、範圍與人選狀態，與單句應答、雙人圖表對話、詞形、段落填句及跨文件閱讀分工，沒有換年份、品牌或改標題重發。原有 41 篇 JSON 與基準逐位元相同，URL、published、modified／lastmod 保留，本分支共 43 篇；見 [庫存雜湊](seo-editorial-inventory-2026-11-10.json)。

## 實讀來源、版本與原創教材

- 新宿區目前指南入口日期 2025-01-27，實讀其所連 `202501` 多語 PDF 的印刷第 38–39 頁，並目視日文／中文／英文頁。住民記錄、適用中長期在留者、轉入、在留卡／後日領卡者護照、家庭證明條件、搬家及住民票副本有費用均有對應；未外推保險、年金、簽證或費用金額。
- PDF 日文、中文為入境後開始在區內居住起 14 日，英文寫入境起；本文明確揭露差異，請讀者提供兩個日期給自治體確認，不自行裁決個案起算、末日或逾期結果。當日可讀地址變更網頁另列變更後 14 日。未假設開學日或校方報到日就是起算日。
- 日文國外轉入頁標示 2021-09-10，仍留舊疫情等待措施；只作版本提醒，沒有當現行延後依據，也未引用其夜間／假日／代理／住宿限制保證 2026 受理。諮詢頁日期 2026-04-01，確認免費、本廳舍一樓及中英韓語言；其他未明示修訂日的網頁揭露當日版本。
- 出入國在留管理廳兩頁 HTTP 403，沒有可讀內容，不引用其主張、不捏造官方存檔。兩個舊／猜測路徑 404，改循新宿區實際導覽取得可讀官方資料。使用新宿區一手資料並限定案例範圍；仍需由讀者向自己的自治體確認個案與當日安排。
- TOEIC 當日官方內容表及 Part 4 directions／範例形式實讀：30 題（3×10）、單一說話者、每段三題、四選一、談話不印出、只播放一次；官方例子含圖表，不宣稱獨白都沒有圖表。未替 Part 4 設獨立官方分鐘數，未做官方音訊聽辨或語速測試，沒有轉載其題目／逐字稿／音檔。
- 兩段獨白與六題均自寫。答案 B／D／C：暴風雨損橋→局部關閉→改走東側並可先領地圖；答案 A／D／B：活動協調者→用品已足夠→攝影角色尚未指派。各干擾項逐一對照缺乏依據或矛盾，沒有把日期當作已完成證據。
- 換題只讓上午組用品足夠、下午組自備，示範範圍與條件改變時修正重述；不推算未給定的人數或缺額。3×10＝30、6×4＝24 選項及六個答案標記已程式核對。沒有金額試算、個案期限計算或練習到正式分數的換算。
- 本篇無自製音檔，已看稿不當作第一次聽力；夥伴藏稿朗讀與官方原站音訊的練法分開。假設學生、弱稿／修正版、英文教材均明示編輯設計，不冒稱學生心得、模型實測、專家審核或成效保證。

可核對 URL、HTTP、回應大小與雜湊、來源版本、實讀範圍及限制見 [來源紀錄](seo-editorial-sources-2026-11-10.json)。原始外部回應及 PDF 僅留任務 cache，未複製入 Git。

## 照片與閱讀畫面

實讀 Pexels 兩張來源頁與 License，核對可免費使用／修改、可選署名，以及不可冒犯性使用、暗示背書、原圖轉售、素材平台轉售或商標使用。沿用 Mikhail Nilov 文件閱讀照、Roxanne Minnish 耳機電腦照，均為既有真實攝影，1536×1024 WebP、每張低於 450 KB，與 main 逐位元相同；未生成、替換、改色或使用紙感插畫。alt、文中圖說與署名不將素材人物說成真實申請者、窗口人員、考生或校園，見 [攝影紀錄](seo-editorial-photography-2026-11-10.json)。

沿用最新 main 的 metro／typography／閱讀樣式；實際 create_app、拋棄式資料目錄與 Chromium，兩篇各 320／390／1440 px，關閉 JavaScript，共六組。檢查 H1、canonical、Article／Breadcrumb JSON-LD、目錄跳轉、原生 FAQ、圖片載入／alt／lazy／來源／1536 尺寸、相關導覽與母校／目的地／選校連結。手機三個寬表格各實際設定 scrollLeft 確認可捲動，頁面無水平溢出。

已目視全部 15 張最終驗收圖，文字、圖解與圖說可讀，裁切保留主體。分段長截圖會把 main 的固定 6px 裝飾彩條畫進段落；重新取分段圖時只在 screenshot 的暫時 style 隱藏該偽元素，沒有修改產品 CSS、文字、資料或瀏覽器驗收條件。桌機／手機整頁預覽保留原版彩條。

- [桌機](seo-previews-2026-11-10/desktop-1440.jpg)、[手機](seo-previews-2026-11-10/mobile-320.jpg)、[3:2／2:1 裁切](seo-previews-2026-11-10/photography-crops.jpg)
- [日期與版本](seo-previews-2026-11-10/japan-residence-registration-dates-and-source-versions-390.jpg)、[文件與圖解](seo-previews-2026-11-10/japan-residence-registration-prepare-documents-390.jpg)、[詢問範本](seo-previews-2026-11-10/japan-residence-registration-ask-the-right-counter-390.jpg)、[假設案例與紀錄](seo-previews-2026-11-10/japan-residence-registration-worked-case-and-check-390.jpg)
- [獨白題組一](seo-previews-2026-11-10/toeic-part-four-talks-original-park-announcement-390.jpg)、[題一解析](seo-previews-2026-11-10/toeic-part-four-talks-park-answers-and-evidence-390.jpg)、[獨白題組二](seo-previews-2026-11-10/toeic-part-four-talks-original-garden-message-390.jpg)、[題二解析與換題](seo-previews-2026-11-10/toeic-part-four-talks-garden-answers-and-transfer-390.jpg)
- [登記圖解](seo-previews-2026-11-10/japan-residence-registration-diagram-390.jpg)、[獨白圖解](seo-previews-2026-11-10/toeic-part-four-talks-diagram-390.jpg)、[登記照片／圖說](seo-previews-2026-11-10/planning-photo-390.jpg)、[聽力照片／圖說](seo-previews-2026-11-10/english-guide-photo-390.jpg)

## 驗收結果

| 檢查 | 結果 |
| --- | --- |
| `scripts/check_editorial.py --base-ref origin/main` | 通過，43 篇 |
| SEO 單元／整合／release gate 六模組 | 165 passed，首次通過 |
| SEO 文章／頁面／analytics E2E 三模組 | 53 passed，首次通過 |
| 無 JavaScript 桌機／手機閱讀 | 六組通過；分段截圖重新取圖以排除固定裝飾條的長截圖現象 |
| wheel 建置、逐檔核對與 checkout 外載入 | 通過；43 JSON、27 唯一 WebP、全部 56 CSS、481 個字型目錄檔案及其他閱讀資產，合計 608 個唯一檔逐位元相同；checkout 外載入 43 篇與兩個新 slug |

證據：[結構檢查](seo-editorial-checks-2026-11-10.json)、[測試紀錄](seo-editorial-tests-2026-11-10.txt)、[瀏覽器紀錄](seo-editorial-browser-2026-11-10.json)、[套件 manifest](seo-editorial-package-2026-11-10.json)。本批 wheel 2,412,785,888 bytes，留在任務 cache，未提交 Git。字型目錄計數包含其中 CSS，總檔數已去重。瀏覽器檢查是實驗室閱讀驗收，不代表實際使用者 Core Web Vitals。

## 待審與發布邊界

[PR #285](https://github.com/blizzard-new/abroad/pull/285) 已建立並核對 open／merged=false，兩篇一起審閱。未合併、未部署 Windows 正式環境、未寄信或要求 Google 批次索引；文章、PR 與本機驗收不代表已上線、收錄或排名。

任務附件工具已呼叫，40 秒未回覆；附件清單亦於 10 秒內未回覆，無法確認掛載。PR 本身已獨立透過 GitHub 核對存在，附件狀態不冒稱成功。
