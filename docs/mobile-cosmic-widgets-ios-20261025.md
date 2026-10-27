# UniWay 2.1.6：星空、Widget 與 iOS 準備

## 合併與範圍

PR #125 已於台灣時間 2026-10-25 合併 main，merge commit 為
`252f633c4b4d859b3d7ca20df2005ec2208a8e8f`。新功能從此 main 建立
`codex/cosmic-widgets-ios`，沒有修改學校資料、擴充資料查核或部署 Jerry 後端。

本次使用 `ceorkm/mobile-app-ui-design` skill：保留單一主要操作、短文案、圖示、
44–48 以上點擊區、可讀對比與共用元件，並依使用者指定採用星空與 Liquid 風格。

## 變更

- 共用深色星空背景使用靜態繪製，避免常駐星空動畫。卡片、輸入、對話框、按鈕與底部導覽統一色彩。
- Liquid 按鈕帶半透明、邊緣高光與模糊；高對比／減少動畫設定使用不透明及無模糊呈現。
- 五個底部導覽只顯示圖示，保留 Tooltip 與語音名稱及選取狀態。
- Android / iOS 都有交換總覽、星軌倒數、極光待辦、軌道進度四款 Widget。
  每款有獨立 provider／kind，可以同時放在桌面。保留舊 Android 總覽 receiver，避免既有小工具失效。
- 小工具使用既有帳號的個人文件／行事曆摘要，顯示更新時間，登出清空。
  倒數只取已儲存的個人日期，沒有新增學校資訊。
- iOS 設定 bundle ID、App Group、Keychain、登入 scheme、WidgetKit extension 版本、
  本機通知初始化及明確的權限詢問；更新入口不顯示 APK。

## Android 驗證

- Flutter 116 項單元／Widget 測試通過，包括四款小工具更新、選擇、登出清空、
  320px / 2 倍字級、文字對比及 iOS 通知主動詢問權限。
- `flutter analyze` 無 error／warning；4 個原有字串插值 info 保留。
- Release APK 編譯成功：`tw.uniway.app`、2.1.6、versionCode 20、minSdk 24。
- `apksigner verify` 成功，沿用既有測試簽章，可原地更新。
- Android API 36.1 模擬器確認首頁、表單、詳情頁與圖示導覽；四款小工具均經系統確認加入桌面並渲染。
  倒數／待辦點擊可回到旅程。測試使用未登入空白狀態，未對正式帳號建立資料。
- 2.1.5 實際啟動出現 2.1.6 更新提醒；「下載更新」開啟正確 GitHub APK 網址。
  `adb install -r` 更新成功，套件版本讀回為 2.1.6 / 20。
- 公開下載以無登入 HTTP client 完整下載，79,765,108 bytes，SHA-256 與本機及 GitHub 相同。
  完整收據見 `android-public-download-2.1.6-20261025.json`。

Android 實測截圖存於本機 `output/android-cosmic-ui-20261025/`。
Windows 模擬器在軟體 GPU 模式出現數次程序退出，改用 host GPU 後完成更新測試；
這些測試不是所有實體手機或登入帳號流程的完整驗收。

## iOS 驗證與未完成事項

GitHub Actions [40119011254](https://github.com/blizzard-new/abroad/actions/runs/40119011254) 成功，
程式 commit 為 `85711d50ca866596edfd33597005a5423b11092d`，與 Android APK 一致。
Xcode 26.3 完成未簽署裝置版及 Simulator 版編譯，模擬器安裝及啟動成功，已檢視截圖。
WidgetKit extension 也已編譯；iOS 桌面上逐款 Widget 的互動尚未驗證。
首次使用 Xcode 16.4 時，Firebase SDK 13.1.1 要求較新 Swift tools，已切換到 Xcode 26.3 解決。
Simulator 和未簽署 ZIP 放在相同的 2.1.6 公開版本頁，明確標為開發測試檔。
尚未取得 Apple Developer 帳號、簽署憑證與實體 iPhone；不宣稱已可透過公開網址安裝到 iPhone。
Firebase/APNs 遠端推播仍待設定。真機登入、通知送達及 Widget 更新仍需後續驗證。
詳見 `ios-distribution.md`。
