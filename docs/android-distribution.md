# Android 公開下載與版本紀錄

固定入口：[UniWay Android 版本下載頁](https://github.com/blizzard-new/abroad/releases)。
首次公開版本為 [2.1.2 測試版](https://github.com/blizzard-new/abroad/releases/tag/android-v2.1.2-preview)，
發布日期為 2026-10-24；後續版本依序保留在同一頁面。

目前新版：[2.1.6 APK](https://github.com/blizzard-new/abroad/releases/download/android-v2.1.6-preview/UniWay-2.1.6-preview.apk)。
2026-10-25（台灣時間）已發布，匿名完整下載 79,765,108 bytes，SHA-256 與本機及 GitHub asset digest 相同。
2.1.5 已實際跳出 2.1.6 更新提醒，下載按鈕開啟正確 APK 網址；模擬器以 `adb install -r` 覆蓋更新成功。
新功能為星空 Liquid 介面、純圖示導覽與四款桌面小工具。
紀錄見 `android-public-download-2.1.6-20261025.json`；iPhone 發布準備見 `ios-distribution.md`。

前一版：[2.1.5 APK](https://github.com/blizzard-new/abroad/releases/download/android-v2.1.5-preview/UniWay-2.1.5-preview.apk)。
2026-10-25（台灣時間）已發布，匿名完整下載 79,695,696 bytes，SHA-256 與本機 APK、GitHub asset digest 相同。
2.1.4 的實際更新提醒及下載連結已驗證；模擬器以 `adb install -r` 覆蓋安裝到 2.1.5 成功。
紀錄見 `android-public-download-2.1.5-20261025.json`，深層介面變更見 `android-deep-ui-20261025.md`。

前一版：[2.1.4 APK](https://github.com/blizzard-new/abroad/releases/download/android-v2.1.4-preview/UniWay-2.1.4-preview.apk)。
主頁改版見 `android-ui-redesign-20261024.md`；歷史下載與更新紀錄保留於 `android-public-download-2.1.4-20261024.json`。

歷史版本：[2.1.3 APK](https://github.com/blizzard-new/abroad/releases/download/android-v2.1.3-preview/UniWay-2.1.3-preview.apk)。
GitHub 公開 repository 的 Release 與附件不需要登入。2.1.3 已於 2026-10-24 發布，
並以未登入的 HTTP client 完整下載，確認 80,384,008 bytes 及 SHA-256 與本機簽署 APK 相同。
驗證紀錄見 `android-public-download-2.1.3-20261024.json`；2.1.2 的歷史紀錄保留於 `android-public-download-20261024.json`。

使用者用 Android 手機開啟入口，下載 `.apk` 後安裝。遇到系統詢問時，允許使用中的
瀏覽器或檔案管理員安裝 App。`Source code` 壓縮檔不是手機安裝檔；iPhone 不能安裝 APK。

## 新版發布方式

1. 更新 `mobile_flutter/pubspec.yaml` 的版本號與 build number；Android `versionCode`
   必須高於已發布版本。2.1.6 使用 versionCode 20；後續版本必須同時提高三段版本號與 versionCode。
2. 沿用 `tw.uniway.app` 與現有測試簽章，透過 `scripts/build-android-preview.ps1` 建置。
   私鑰及密碼只留在建置機的安全目錄，不可放到 Release 或 repository。
3. 執行對應功能驗證，確認 APK 內部版本、簽章及 SHA-256；檔名需與內部版本相符。
4. 建立新的版本 tag 與 draft Release，target 指向實際建置程式碼的 commit。
   上傳 APK、SHA256SUMS 與繁體中文更新說明；測試版標記為 prerelease。
5. 上傳成功後核對 GitHub asset 的 size、digest 與本機檔案，再發布 Release。
   最後以未登入方式驗證頁面及 APK 下載。
6. 保留舊版本的 tag、APK 與更新紀錄，分享相同 `/releases` 入口。
   發現新版問題時另發修正版，不覆蓋相同版本的二進位檔。

可使用 GitHub Release 頁面或 `gh release create/upload/edit` 完成上述流程。
版本仍由維護者發布。2.1.3 起，App 會自動檢查新版並提供直接下載按鈕，安裝由 Android 詢問使用者確認。
同套件、同簽章且 versionCode 較高的新版，可直接安裝更新，不必先解除安裝。
不要將重新安裝舊版本描述成原地回復：Android 通常會阻擋較低 versionCode 的覆蓋安裝。

目前分享 `/releases` 而非 `/releases/latest`，因為公開版本是 prerelease。
下載頁列出版本、日期、更新內容、安裝步驟及測試版尚未啟用的功能。
Firebase 遠端推播仍待設定；本次發布未新增大學資料查核。

## App 自動檢查更新（2.1.3 起）

- 啟動及回到前景時，匿名讀取此 repository 的 GitHub Releases API；成功檢查間隔 6 小時，連線失敗退避 15 分鐘。
- 「我的 → 檢查更新」可立即重查；自動檢查失敗不打斷操作。點「稍後提醒」或關閉提醒後，同一版本延後 24 小時再提醒。
- 從最新 100 筆公開 Release 挑出比目前版本高的 Android 版本，數字比較版本號；包含測試版，排除 draft、缺少 APK、不同 repository 或不符合檔名的附件。
- tag 使用 `android-vX.Y.Z-preview`，附件命名為 `UniWay-X.Y.Z-preview.apk`；正式版可使用 `android-vX.Y.Z` / `UniWay-X.Y.Z.apk`。不可重用版本號；同一版本只發布一個 universal APK。
- 下載按鈕開啟官方 Release 的 APK 附件；使用者下載完成後開啟檔案並確認安裝。App 不會靜默安裝，也不要求安裝套件權限。
- 2.1.2 尚無檢查功能，必須先手動安裝一次 2.1.6（或其他 2.1.3 以上版本），之後才有自動提醒。GitHub 網路或 API 速率限制可能延遲提醒。
- 檢查版本不傳送 UniWay 帳號憑證、學校、收藏或任何私人資料給 GitHub。

參考：[GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)、
[版本連結](https://docs.github.com/en/repositories/releasing-projects-on-github/linking-to-releases)。
