# 2026-11-08 每日雙篇驗收

日期採 Asia/Taipei；即時時鐘為 2026-11-08 00:02 UTC，即臺灣 11/8 08:02。隔離分支 `codex/seo-daily-20261108`，新增兩篇完整繁體中文圖文文章，同屬本日唯一 PR，待建立。選題依使用者候選方向 19、20 的編輯判斷，沒有使用者 Search Console、搜尋量、流量或排名資料。

| 完整文章 | slug | 獨立實作價值 |
| --- | --- | --- |
| 托福 Take an Interview 怎麼答？口說展開、原創模擬題與錄音訂正 | `toefl-take-an-interview` | 四題原創問題、題目任務對照、弱稿與人工修改、不同任務回答、錄音回聽與分層訂正 |
| 多益 Part 6 句子填入怎麼判斷？段落銜接、指涉與原創題組 | `toeic-part-six-sentence-insertion` | 兩份原創文件、兩道整句四選一、八選項逐項解析、前後證據、開放式換題與錯因紀錄 |

## main、待審與去重

基於最新 main `b5caecf856c184e349ffaecc2ffc384c6615d9a3`。讀取 workflow，確認與最新已讀版本相同；讀 main backlog、待審 11/7 backlog、37 篇 main 庫存及兩篇待審題目，重讀托福總覽、交換面試、多益聽讀總覽與 Part 5 相關正文。未發現適用 AGENTS.md，含祖先目錄與 Git 追蹤檔案查核。

全部 11 個 open PR #255–#265 的說明與完整變更檔案清單已讀；#256–#265 僅含校務資料稽核 proposal，#255 含 11/7 的 AI 英文改稿與托福缺字兩篇，均視為已選並排除。開始前沒有同日分支或任何狀態同日 PR，見 [PR 查核](seo-editorial-pr-audit-2026-11-08.json)。#78、#92 已合併，直接使用 main，沒有未合併基礎相依，也沒有把 #255 的內容納入本批。

10/30 `exchange-study-plan` 擴充仍保留原分支 `97de3fda`；候選 15 沒有可核對三工具實測，未製造比較。main backlog 歷史中的待審字樣，以本日盤點及 #255 保留狀態優先。

訪談篇處理 TOEFL 學術／校園情境的即時原創回答，並提供題目任務變化、弱稿修改與回聽證據；與聽後準確重述、四科安排、真實交換甄選程序分工。Part 6 篇處理同一篇文件的整句銜接及狀態一致性，與單句詞形、跨文件證據、圖表聽力與單句應答不同。不是以品牌、年份或改標題重發總覽。[庫存雜湊](seo-editorial-inventory-2026-11-08.json) 證明原有 37 篇 JSON 逐檔與基準相同，URL、published、modified／lastmod 均保留；本分支共 39 篇。沒有改 renderer、schema、CSS、資料庫或原共用 checkout。

## 實讀來源、題目與數學

- 實讀 ETS 現行 Speaking 本文及 What to Expect：Take an Interview 為學術／校園情境的經驗與意見回答，對麥克風錄音，重視清楚溝通、自然節奏及合宜語言。未從簡介推定官方題數、每題秒數或準備時間。
- 實讀 ETS 2026 Update 標題及口說章節印刷頁 15–17，包括可理解與連貫表達、由事實發展至意見／解釋／敘述、語音刺激與評分限制。沒有聲稱逐頁讀完整份 PDF；原始點數與 CEFR 描述不套用自編範例，沒有自稱官方評分表。
- 實讀 ETS 成績頁 January 2026 更新：2026-01-21 起 1–6 半分尺度；兩年過渡另有可對照的 0–120 整體分數。沒有用錄音勾選數、字數或自編答對率換算官方成績。
- 訪談四題分別問地點及理由、某次變動與行動、個人偏好、假設空間優先順序；不是官方固定四題配置。題 3 修改先準備 alone first，透過列疑問支持後續討論，沒有誇稱不合作、提分或量化成效；題 4 改談假設資源選擇，以 if／would 保留假設，不編造任何校園使用率。文字參考未做錄音、語速或發音實測，文中清楚區分聽題、看題與讀範例。
- 實讀臺灣 TOEIC 現行內容表及 Part 6 directions／樣題形式：Part 6 段落填空 16 題（4×4），與其他閱讀共用 75 分鐘；可缺字、片語或句子，四選一選最佳答案。4×4＝16 已核對，不將全部 16 題說成句子填入，不自行設單題固定秒數。官方樣題、答案與音檔沒有轉載。
- Part 6 題一答案 C：投影機維修→改至 Room 204→只改房間、時間與原報名不變。A 取消整場、B 改到星期五、D 取消報名，各違反保留項目。Room 204 是合理的新資訊，沒有因前文未出現就排除。題二答案 B：圖太小→草稿放大→請查看放大圖；尚待發布、收回饋與預約不變。A 已定稿且停止收回饋、C 刪掉全部圖、D 改預約網站，各與本文矛盾。
- 兩份自編文件各一整句空格、四選項，共八選項，已以程式核對，清楚揭露不是官方一篇四題的完整配置。第三個開放換題容許不同自然寫法，以櫃台到線上表單、在家預約的關係驗收，不宣稱唯一標準句。所有日期、教室、通知與圖書館情境均虛構，沒有當成真實規定。

必要來源均 HTTP 200，未見固定修訂日的網頁揭露當日版本；沒有存檔替代或尚未核實的費用、期限、資格、獎助、簽證主張。全部教材為 UniWay 自編，不是 ETS 真題、AI 實測輸出、學生訪談、專家審核或分數校準。可核對 URL、版本、HTTP 狀態、回應雜湊、實讀範圍及限制見 [來源紀錄](seo-editorial-sources-2026-11-08.json)。原始回應留在任務 cache，未複製外部原文入 Git。

## 照片與畫面

實讀 Pexels 兩張原照片頁與 License，核對免費使用／修改、可選署名及不可暗示背書、冒犯性使用、原圖轉售、素材平台轉售與商標使用限制。沿用 Zen Chung 耳機筆記照與 PNW Production 書寫特寫，1536×1024 WebP，111,030／88,086 bytes，均低於 450 KB；逐位元核對為既有素材，未生成、替換、改色或沿用舊紙感插畫。alt、文中圖說與署名揭露素材情境，沒有將人物當真實受訪者、考生、校園、活動或成績案例；見 [攝影紀錄](seo-editorial-photography-2026-11-08.json)。

實際 create_app、拋棄式資料目錄及 Chromium；兩篇各 320／390／1440 px，關閉 JavaScript，共六組。H1、canonical、Article／Breadcrumb JSON-LD、目錄跳轉、原生 FAQ、圖片載入／alt／lazy／來源／尺寸、相關文章及母校／目的地／選校工具連結均檢查。手機寬表格實際改變 scrollLeft 確認可捲動，頁面無水平溢出。已目視全部 14 張驗收圖：桌機、手機、兩圖解、全部主要題目／解析／換題、文中照片與署名，以及 3:2／2:1 裁切；文字可讀且照片主體保留。

- [桌機](seo-previews-2026-11-08/desktop-1440.jpg)、[手機](seo-previews-2026-11-08/mobile-320.jpg)、[圖片裁切](seo-previews-2026-11-08/photography-crops.jpg)
- [訪談四題](seo-previews-2026-11-08/toefl-take-an-interview-original-questions-390.jpg)、[弱稿與修改／圖解](seo-previews-2026-11-08/toefl-take-an-interview-revise-a-response-390.jpg)、[換題回答](seo-previews-2026-11-08/toefl-take-an-interview-adapt-to-a-new-question-390.jpg)
- [Part 6 題一](seo-previews-2026-11-08/toeic-part-six-sentence-insertion-original-room-notice-390.jpg)、[解析與圖解](seo-previews-2026-11-08/toeic-part-six-sentence-insertion-room-answer-and-evidence-390.jpg)、[題二及解析](seo-previews-2026-11-08/toeic-part-six-sentence-insertion-original-guide-email-390.jpg)、[換題](seo-previews-2026-11-08/toeic-part-six-sentence-insertion-transfer-and-revise-390.jpg)
- [訪談篇照片與圖說](seo-previews-2026-11-08/toefl-study-photo-390.jpg)、[Part 6 照片與圖說](seo-previews-2026-11-08/writing-photo-390.jpg)

## 驗收

| 檢查 | 結果 |
| --- | --- |
| `scripts/check_editorial.py --base-ref origin/main` | 通過，39 篇 |
| SEO 單元／整合／release gate 六模組 | 161 passed |
| SEO 文章／頁面／analytics E2E 三模組 | 49 passed，無重跑 |
| 無 JavaScript 桌機／手機閱讀 | 六組通過，目視完成 |
| wheel 建置與套件核對／checkout 外載入 | 通過，39 JSON／27 唯一 WebP／CSS／renderer／init 共 69 檔逐位元相同；checkout 外可載入 39 篇及兩個新 slug |

證據見 [結構檢查](seo-editorial-checks-2026-11-08.json)、[測試紀錄](seo-editorial-tests-2026-11-08.txt)、[瀏覽器紀錄](seo-editorial-browser-2026-11-08.json)、[套件 manifest](seo-editorial-package-2026-11-08.json)。本批實際 wheel 為 2,407,276,708 bytes，留在任務 cache，未提交 Git。瀏覽器驗收是實驗室閱讀檢查，不代表實際使用者 Core Web Vitals。

## 待審與發布邊界

本日唯一 PR 待建立，兩篇一起審閱。沒有合併、Windows 正式部署、寄信或要求 Google 批次索引；文章完成、PR 與本機驗收不代表已上線、收錄或排名。
