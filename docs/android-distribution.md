# Android 公開下載與版本紀錄

固定入口：[UniWay Android 版本下載頁](https://github.com/blizzard-new/abroad/releases)。
首次公開版本為 [2.1.2 測試版](https://github.com/blizzard-new/abroad/releases/tag/android-v2.1.2-preview)，
發布日期為 2026-10-24；目前只有這一個已發布版本。

[直接下載 APK](https://github.com/blizzard-new/abroad/releases/download/android-v2.1.2-preview/UniWay-2.1.2-preview.apk)。
GitHub 公開 repository 的 Release 與附件不需要登入；本次以未登入的 HTTP client
實際完整下載，確認 80,023,240 bytes 及 SHA-256 與本機簽署 APK 相同。
驗證紀錄見 `android-public-download-20261024.json`。

使用者用 Android 手機開啟入口，下載 `.apk` 後安裝。遇到系統詢問時，允許使用中的
瀏覽器或檔案管理員安裝 App。`Source code` 壓縮檔不是手機安裝檔；iPhone 不能安裝 APK。

## 新版發布方式

1. 更新 `mobile_flutter/pubspec.yaml` 的版本號與 build number；Android `versionCode`
   必須高於已發布版本。目前最高為 2.1.2 / 16。
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
現有版本採手動發布、手動下載安裝；沒有新增排程、自動發布或 App 內自動更新。
同套件、同簽章且 versionCode 較高的新版，可直接安裝更新，不必先解除安裝。
不要將重新安裝舊版本描述成原地回復：Android 通常會阻擋較低 versionCode 的覆蓋安裝。

目前分享 `/releases` 而非 `/releases/latest`，因為公開版本是 prerelease。
下載頁列出版本、日期、更新內容、安裝步驟及測試版尚未啟用的功能。
Firebase 遠端推播仍待設定；本次發布未新增大學資料查核。

參考：[GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)、
[版本連結](https://docs.github.com/en/repositories/releasing-projects-on-github/linking-to-releases)。
