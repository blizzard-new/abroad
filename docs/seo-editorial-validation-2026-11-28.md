# 2026-11-28 交換學生指南驗收

批次使用臺北日期 2026-11-28。隔離分支為 `codex/seo-daily-20261128`，基準為 `3663c9ed56c0795c5aface05987a4c16458fa48a`。

| 文章 | 讀者的問題與做法 |
| --- | --- |
| [成大交換學校怎麼找？校級、院級與系級申請管道比較](../src/exchange_info/editorial/ncku-exchange-program-routes.json) | 成大學生找到多張合作校表，讀完可用學籍、梯次、名額狀態與費用，整理自己有資格送件的管道。 |
| [日本交換學生國民健康保險怎麼辦？加保、看診證明與費用](../src/exchange_info/editorial/japan-exchange-national-health-insurance.json) | 台灣學生赴日交換後需要使用國保，讀完可確認申辦窗口、就醫證明、診費自付及墊付後應保留的文件。 |

## 選題與查重

核對最新主分支 79 篇文章、選題紀錄及三個待審 PR（#414、#415、#416）的說明與檔案清單。#411 的臺大兩階段志願及 ECTS 工作量已在主分支。未發現本日同批，未改動既有文章。

- 成大篇參考 Leo 轉述的 2026/10/18–11/24 Search Console 摘要，其中有「成大 交換學校」。用三種甄選管道、學制與各自收件規則補充母校總覽。臺大篇的範圍是已進入臺大校級甄選後的兩輪志願。待審的合作校比較功能對照選定學校，本篇先解決學生應從哪一個管道找清單。
- 日本國保篇採編輯判斷。居住登記篇處理地址申報，日本預算篇處理全學期開支。國保篇深入加保、資格文件、核對就醫帳單及保留墊付憑證。未取得國保專屬的查詢量或排名。

## 來源與適用範圍

以下正文均於 2026-11-28 核讀。文章內保留來源機構、版本或查核日期，以及各節對應的資料。

- 成大國際處的 [113 年版甄選要點](https://oia.ncku.edu.tw/p/404-1032-229871.php?Lang=zh-tw) 與 [116-1 公告及簡章](https://oia.ncku.edu.tw/p/406-1032-306703,r3650.php?Lang=zh-tw) 用於確認校級流程、當期時程、學制與 77 分或前 50% 的學業門檻。其他梯次與合作校另核對。
- 成大 [電資學院院級交換頁](https://eecs.ncku.edu.tw/p/412-1020-18361.php?Lang=zh-tw) 提供參考時程與京都、關西方案的不同範圍。成大 [電機系公告](https://www.ee.ncku.edu.tw/announcement_content.php?ann_id=4435) 的 2027 秋季附件支持 2027/1/15 17:00 截止、紙本及電子雙軌、學籍與費用差異。院級名額仍須承辦確認。案例中的小恆為原創假設。
- [東京大學留學生指南](https://www.u-tokyo.ac.jp/adm/inbound/en/life-daily-mn.html) 與 [厚生勞動省國保說明](https://www.mhlw.go.jp/content/001764098.pdf) 用於確認留學在留、到所在地辦理、一般成年自付及自治體保費。厚生勞動省的 [資格確認指引](https://www.mhlw.go.jp/stf/newpage_50657.html) 用於區分資格確認書、資格資訊通知和完成登錄的 My Number 卡。
- [新宿區資格](https://www.city.shinjuku.lg.jp/kenkou/hoken01_002065_00002.html)、[屆出](https://www.foreign.city.shinjuku.lg.jp/jp/kurashi/kokuhotodokede/) 與[療養費](https://www.city.shinjuku.lg.jp/hoken/file02_04_00003.html) 只作地方範例，支持資格排除、搬離時退出和墊付請款文件。假設帳單以 6,000 × 0.30 ＝ 1,800 日圓，加 1,000 ＝ 2,800。全額當次付 7,000，差額 4,200。個別保費、醫療費及給付由投保地與醫療機構判定。

## 圖片與驗收

兩張攝影依 [Pexels License](https://www.pexels.com/license/) 使用與裁切。兩圖分別為 George Pak 的戶外校園情境、Alexander Zvir 的診間工作情境，圖說有揭露素材用途。兩個 WebP 均為 1536×1024，依序為 143,618 及 74,272 bytes。兩篇各附一張有標題和文字步驟的原創 HTML 圖解。

[攝影紀錄](seo-editorial-photography-2026-11-28.json) · [截圖與 3:2／2:1 裁切](seo-editorial-previews/2026-11-28/) · [無 JavaScript 紀錄](seo-editorial-browser-2026-11-28.json)

| 檢查 | 結果 |
| --- | --- |
| `scripts/check_editorial.py --base-ref origin/main` | 81 篇、0 錯誤。既有 79 篇未改動。 |
| SEO 單元、整合及文章發佈檢查 | 210 通過。 |
| 三組專案瀏覽器測試 | 94 通過。 |
| 兩篇 × 320、390、1440 px，停用 JavaScript | 6 組通過。驗證唯一主標題、標準網址、社群圖、結構化資料、Sitemap、目錄、FAQ、圖片載入、表格橫捲及相關路由。 |
| 人工目視 | 查看兩張來源照片及 10 個驗收截圖檔，含桌機、手機、主要表格、步驟圖及兩種裁切。 |

Windows 檢核第一次因地區預設編碼而無法讀取 Git 回傳的 UTF-8，使用 UTF-8 模式後通過。第一次單元測試啟動後，依目視結果修正日本國保篇替代文字，造成測試中讀到不同版本。已在定稿重跑全部單元測試與停用 JavaScript 驗收。
