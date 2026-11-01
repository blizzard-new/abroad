# UniWay PR 整合紀錄 — 2026-11-01

本次整合使用者指定的 29 個未合併 PR，保留所有原始分支 head 的祖先關係。整合 PR：[#207](https://github.com/blizzard-new/abroad/pull/207)。驗證結果與合併狀態記錄於 PR。

## 整合內容與衝突處理

- 合併 14 所新增母校，以及網頁申請 UX、Flutter 介面、SEO、行銷派工測試。
- 共用學校 registry、API dispatch、資格規則、表單、寫作引導、地圖／照片索引、前台與後台選單採完整聯集；依學校名稱和國家保留獨立圖片／地點資料。
- 合併後 50 所母校、9,026 筆母校／目的地資料；目的地筆數不是去重後的海外大學數量，也不代表當期全部開放申請。
- 11 個資料更新提案保留提案性質，沒有自動轉為已核對的官方申請規則。
- 更新 pypdf 6.21.4、pyasn1 0.6.5，修復既有 PR 的漏洞掃描失敗；保留安全檢查。
- 修正既有瀏覽器測試的過時前提：分頁操作先切換到卡片；選校器依完整校庫驗證，Taipei 允許對應多所學校，仍驗證鍵盤選擇、焦點與保存行為。

## 校園照片核對

整合測試發現實踐大學的一筆校園照無法匹配，追查也發現原照片屬於其他學校。以下兩張照片已於 2026-11-01 以官方校區頁與實際圖片核對，更新共用索引及相關校庫副本；原始合作校公告快照保持原樣。

| 學校 | 官方照片來源頁 | 修正 |
| --- | --- | --- |
| Southern Cross University | [Gold Coast campus](https://www.scu.edu.au/experience/explore-our-campuses/gold-coast/) | 取代錯配的 Berlin-Lankwitz Siemens Villa 圖片；補齊澳洲／澳大利亞名稱對應 |
| University of Cumbria | [Carlisle Fusehill Street campus](https://www.cumbria.ac.uk/student-life/locations/carlisle/campus/) | 取代錯配的 University of London Institute of Education 圖片 |

新圖片的 SHA-256、尺寸、來源 URL 與核對日期記錄在 `src/exchange_info/static/assets/school-images.json`。圖片呈現代表校區，實際就讀校區仍以校方通知為準。

## 合併後母校名單

首頁 50 個學校選項與 `SUPPORTED_UNIVERSITIES` 完全一致。

### 公立（32 所）

- 國立臺北大學
- 國立臺灣大學
- 國立中正大學
- 國立中央大學
- 國立臺灣師範大學
- 國立臺灣科技大學
- 國立中山大學
- 國立中興大學
- 國立臺北科技大學
- 國立政治大學
- 國立成功大學
- 國立陽明交通大學
- 國立清華大學
- 國立高雄科技大學
- 國立雲林科技大學
- 國立臺灣海洋大學
- 國立彰化師範大學
- 國立高雄師範大學
- 國立臺北商業大學
- 國立暨南國際大學
- 國立東華大學
- 國立高雄大學
- 國立嘉義大學
- 國立臺中科技大學
- 國立虎尾科技大學
- 臺北市立大學
- 國立臺中教育大學
- 國立臺北藝術大學
- 國立臺灣藝術大學
- 國立臺北教育大學
- 國立勤益科技大學
- 國立屏東科技大學

### 私立（18 所）

- 長庚大學
- 淡江大學
- 天主教輔仁大學
- 東吳大學
- 中原大學
- 元智大學
- 逢甲大學
- 中國文化大學
- 文藻外語大學
- 臺北醫學大學
- 中山醫學大學
- 中國醫藥大學
- 高雄醫學大學
- 銘傳大學
- 東海大學
- 世新大學
- 靜宜大學
- 實踐大學

## 原始 PR

[#168](https://github.com/blizzard-new/abroad/pull/168), [#169](https://github.com/blizzard-new/abroad/pull/169), [#174](https://github.com/blizzard-new/abroad/pull/174), [#175](https://github.com/blizzard-new/abroad/pull/175), [#178](https://github.com/blizzard-new/abroad/pull/178), [#179](https://github.com/blizzard-new/abroad/pull/179), [#180](https://github.com/blizzard-new/abroad/pull/180), [#182](https://github.com/blizzard-new/abroad/pull/182), [#181](https://github.com/blizzard-new/abroad/pull/181), [#183](https://github.com/blizzard-new/abroad/pull/183), [#184](https://github.com/blizzard-new/abroad/pull/184), [#185](https://github.com/blizzard-new/abroad/pull/185), [#186](https://github.com/blizzard-new/abroad/pull/186), [#187](https://github.com/blizzard-new/abroad/pull/187), [#188](https://github.com/blizzard-new/abroad/pull/188), [#190](https://github.com/blizzard-new/abroad/pull/190), [#191](https://github.com/blizzard-new/abroad/pull/191), [#192](https://github.com/blizzard-new/abroad/pull/192), [#193](https://github.com/blizzard-new/abroad/pull/193), [#194](https://github.com/blizzard-new/abroad/pull/194), [#197](https://github.com/blizzard-new/abroad/pull/197), [#198](https://github.com/blizzard-new/abroad/pull/198), [#199](https://github.com/blizzard-new/abroad/pull/199), [#201](https://github.com/blizzard-new/abroad/pull/201), [#202](https://github.com/blizzard-new/abroad/pull/202), [#203](https://github.com/blizzard-new/abroad/pull/203), [#204](https://github.com/blizzard-new/abroad/pull/204), [#205](https://github.com/blizzard-new/abroad/pull/205), [#206](https://github.com/blizzard-new/abroad/pull/206)
