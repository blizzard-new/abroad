# UniWay 明亮版交付 — 2026-10-25

使用者要求明亮背景、圖示化及整體一致，取代先前的深色星空方向。
設計依據與 skill 搜尋紀錄見 [Daylight design system](../design-system/uniway-daylight/MASTER.md)。

## 實作

共用主題、頁面背景、卡片、按鈕、搜尋、表單和狀態列改為淺色。
首頁以旅程下一步、學校收藏、文件與日期為重點；原創旅行插圖不依賴網路。
學校卡片改為大圖與短資訊，列表按需建構；沒有變更任何大學資料。
申請頁移除重複的進度文字，保留單一摘要。論壇錯誤提示固定於送出按鈕附近。
Android 與 iOS Widget 改用同一套色票，保持原有識別碼、帳號隔離與登出清除行為。

## 驗證

- Flutter：119 tests passed。
- Analyze：0 error / 0 warning；4 項原有字串插值 info，位於 models.dart 與 global_community_screen.dart。
- 主頁面：375×812、812×375、768×1024，2× 字體、減少動畫及高對比。
- 既有深層頁：320px、2× 字體，表單儲存與學校詳情分頁。
- 詳情分頁測試先垂直載入、再捲動橫向分頁到可點位置，斷言 selected 確實變更。
- 對比：主要/次要文字及主色於淺色表面 ≥4.5:1；主要按鈕白字於兩端漸層 ≥4.5:1。
- Android 模擬器：首頁、找學校、學校詳情、申請、論壇、我的、文件表單、已存在的原生小工具；覆蓋安裝成功。
- APK `2.1.7+21`，package `tw.uniway.app`，minSdk 24 / targetSdk 36；延續既有簽章。
- 公開下載完整檔案及 SHA-256 核對見 [下載紀錄](android-public-download-2.1.7-20261025.json)。
- iOS：在 [Actions #40128312769](https://github.com/blizzard-new/abroad/actions/runs/40128312769) 完成裝置版、WidgetKit extension、Simulator 編譯及模擬器安裝啟動；已檢視淺色首頁截圖。App 與 Widget 版本均為 `2.1.7+21`，產物紀錄見 [iOS 建置紀錄](ios-build-2.1.7-20261025.json)。

## 邊界

APK 對應的產品程式碼為 `a4df32cf514b0702926df7fc01123d6026de44a8`，
發布 tag 指向包含測試修正的 `b71115a975350c9836d4461dea7622ee79d72160`；兩者產品程式碼相同。
原始碼持續於草稿 PR #131，未合併 main。未部署 Web 或後端。
未宣稱實體 iPhone 測試、四款 iOS Widget 桌面互動或人工 TalkBack/VoiceOver 審查。
無 Apple 簽署設定，因此沒有一般 iPhone 安裝包。Firebase 遠端推播設定仍未提供。
