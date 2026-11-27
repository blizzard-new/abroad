# 2026-11-27 交換學生雙篇驗收

本批以臺北時間 2026-11-27 記錄，分支 `codex/seo-daily-20261127`，基準 `0160f25950bc514cf4a6af1659fa2e3c9d562367`。原有 77 篇文章與其刊載日期、URL 和最後修改日期保留。

| 新文章 | 讀者遇到的問題與讀完能完成的事 |
| --- | --- |
| [臺大交換志願怎麼填？校級兩階段名額、志願序與報到時程](../src/exchange_info/editorial/ntu-exchange-preference-rounds.json) | 臺大校級申請者不知道兩輪要填哪些志願。讀完可依志願代碼、適用學院、交換期長和名額排出可接受清單，分別記下送出及報到截止。 |
| [ECTS 學分怎麼算？歐洲交換的選課量與讀書時數試算](../src/exchange_info/editorial/ects-exchange-course-load.json) | 歐洲交換學生知道學期總學分，卻看不出課程集中在哪些週。讀完可估算各分期每週工作量，並準備適合同分期的備用課。 |

## 選題與查重

核對 `origin/main` 的 77 篇文章、工作流程、選題紀錄、GitHub 目前待審清單及近期 100 個各狀態 PR。起始無待審 PR 或同日批次。#408、#409、#410 已合併，未納入當日新增。

臺大篇由編輯判斷，深入該校兩階段分發、志願代碼與報到取捨，與跨校的申請總覽、一般資格及 Fact Sheet 指南分工。ECTS 篇承接行銷主管轉述的 2026/10/18–11/24 Google Search Console 查詢摘要，該摘要有 `ects 學分` 曝光，未提供此詞的個別量或平均排名。文章處理分期負擔與備用課，既有抵免篇仍處理預審、返臺採認及繳交文件。另核對 #410 已合併的 ECTS 學分換算器。換算器提供跨學制估算、整體時數和門檻免登入試算，本文補足每週與分期的工作量、先修及備用課配置。

## 一手來源與適用範圍

7 頁一手資料於 2026-11-27 讀取正文，各連結與說明亦載於文章的 `sources`。

- 臺大國際事務處的 [116-1 甄選簡章](https://studyabroad.ntu.edu.tw/wp-content/uploads/2026/07/116-1-Selection-Guidelines_CH.pdf) 與 [申請流程第 5 至 8 步](https://studyabroad.ntu.edu.tw/exchange-student/how-to-apply/) 交叉確認 2026/12/2、7、10、15、17、21、24、29 的下午 4 時起訖、兩階段分發、報到及第二輪資格。簡章適用 116-1 出國的校級甄選，院系計畫須看各自規則。流程頁內的 113-2 舊公告未引用。
- 臺大 [116-1 第一階段交換學生名單](https://oiasystem.ntu.edu.tw/OutboundExchange/school.exam.group/list/id/MapR7e6Jtahd) 讀取 E0042、E0046、E0054 的名額與期長，京都 E0042 有當梯次第二階段不開放的備註。第二階段的校表由校方另外公告。甲、乙、丙是選填練習用的假設志願。
- 歐洲執委會 [ECTS 概要](https://education.ec.europa.eu/eu/education-levels/higher-education/inclusive-and-connected-higher-education/european-credit-transfer-and-accumulation-system)（標示 2022-09-13 更新）與 [2015 年使用指南第一章](https://education.ec.europa.eu/sites/default/files/document-library-docs/ects-users-guide_en.pdf) 支持全時學年 60 ECTS 及多數情形每學分 25–30 小時的典型工作量。臺灣採認依個別母校。
- [隆德大學交換生申請](https://www.lunduniversity.lu.se/node/7476) 支持該校全時 30 ECTS 與主選／備用課，[經濟與管理學院選課說明](https://www.lusem.lu.se/study/international-opportunities/incoming-exchange-students-lusem/courses-incoming-exchange-students) 支持該院的分期配置與先修檢查。兩段各 10 週與四門 7.5 ECTS 課程是原創試算。將學分乘上 25、30 再除以假設週數，所得 15、22.5、7.5 ECTS 每週各為 37.5–45、56.25–67.5、18.75–22.5 小時。學期為 30 ECTS／750–900 小時。移除一門後剩 22.5，補同量後為 30。分配在後期時前後期為 7.5／22.5，補回同期則為 15／15。

## 圖片與驗收證據

兩張 Pexels 真實攝影皆有畫面說明、攝影者及來源。Pexels License 允許網站使用和修改，素材不可用於暗示背書、作為商標或重新分發為庫存圖。原圖、轉檔來源與雜湊見[攝影紀錄](seo-editorial-photography-2026-11-27.json)。WebP 為 1536×1024，臺大篇 55,896 bytes、ECTS 篇 53,906 bytes。兩篇都有原創逐步 HTML 圖解。

| 檢查 | 結果 |
| --- | --- |
| `scripts/check_editorial.py --base-ref origin/main` | 79 篇，0 錯誤 |
| 六組 SEO 單元／整合與文章發佈檢查 | 208 通過 |
| 三組既有瀏覽器測試 | 92 通過 |
| 兩篇 × 320、390、1440 px，停用 JavaScript | 6 組通過。目錄錨點、FAQ、WebP、表格橫捲、相關文章、母校索引、選校工具、臺大篇的日本目的地連結、標準網址、社群主圖、結構化資料、Sitemap 均確認。 |
| 安裝套件重建及外部載入 | 79 篇 JSON、79 張 WebP、60 個 CSS，連同字型及閱讀資產共 365 檔逐一比對相符。從隔離目錄載入 79 篇，並成功渲染新兩篇。 |
| 人工目視 | 兩張來源原圖，以及 10 份桌機、手機、表格、圖解與 3:2／2:1 裁切檔。 |

[桌機、手機、重點段落與裁切圖](seo-editorial-previews/2026-11-27/) · [無 JavaScript 測試紀錄](seo-editorial-browser-2026-11-27.json)

初次直接執行單元測試時，已合併的 `main` 直接匯入 `exchange_info.seo` 會遇到循環匯入，已在獨立乾淨 checkout 重現。重跑以正常應用入口先載入 `exchange_info.api`，並為測試程序使用隔離環境與固定測試值，208 項全過。文章與模板未因測試啟動順序變更。首次長路徑 wheel 建置失敗，已改用較短的隔離暫存路徑。
