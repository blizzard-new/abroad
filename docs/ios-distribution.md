# UniWay iOS 建置與公開測試

目前完成 iOS 程式與免簽署的雲端建置流程。使用者尚無 Apple Developer Program 帳號及 Mac，
因此這一階段不提供可在一般 iPhone 安裝的 IPA，也沒有 TestFlight 邀請連結。

## 安裝檔與分享方式

Android 使用 APK。iOS 的封裝格式是 IPA，但把 IPA 放到 GitHub 並不會讓所有 iPhone 都能安裝。
公開測試建議使用 TestFlight：完成開發者註冊、簽署、上傳及外部測試審核後，分享公開邀請連結。
使用者透過 TestFlight 安裝及更新。正式版本則使用 App Store。

GitHub 上的 `UniWay-iOS-unsigned-app.zip` 是未簽署裝置程式，`UniWay-iOS-simulator.zip`
是 Mac 上 iOS Simulator 使用的程式，兩者都不是一般 iPhone 的公開安裝檔。

## 已完成的設定

| 項目 | 設定 |
| --- | --- |
| App bundle ID | `tw.uniway.app` |
| Widget extension ID | `tw.uniway.app.StudyPlanWidgetDefinitionHomeWidget` |
| App Group | `group.tw.uniway.app` |
| iOS 最低版本 | 16.0 |
| API | `https://app.uniway-tw.com/` |
| 登入回傳 | `tw.uniway.app://auth`，沿用後端 PKCE 流程 |
| Widget 點擊 | `tw.uniway.app://journey` |
| 四款 Widget | 交換總覽、星軌倒數、極光待辦、軌道進度 |

App 與 Widget 共用已儲存的個人計畫摘要；登入憑證只存 App 的 Keychain。
登出會清除 Widget 的個人摘要。Widget 顯示最近更新時間，並非持續背景即時同步。
倒數來自使用者儲存的日期，不會推測學校申請截止日。

本機通知由使用者主動開啟後才詢問權限。iOS 排程保留最多 60 筆提醒。
Firebase/APNs 遠端推播尚未配置；程式建置成功不代表遠端推播或正式帳號流程已完成真機驗證。
iOS 更新入口不會提供 Android APK。

## 雲端建置

GitHub Actions 的 **iOS preview** 工作流程使用 macOS、Flutter 3.44.6、Xcode 26.3。
合併至 main 後，選擇欲測試分支執行 `workflow_dispatch`，或在 main 更新手機程式觸發。
產物包含未簽署裝置程式、Simulator 程式、啟動畫面及 SHA-256。
Actions 附件保留 14 天；需要長期保留的版本另放到公開 GitHub Release。

2.1.6 已在 [Actions #40119011254](https://github.com/blizzard-new/abroad/actions/runs/40119011254)
完成裝置及模擬器編譯、安裝與啟動；已檢視啟動畫面。四款 WidgetKit 已編入 extension，
尚未逐款完成 iOS 桌面互動及實體裝置測試。
開發測試 ZIP 與截圖放在 [2.1.6 版本頁](https://github.com/blizzard-new/abroad/releases/tag/android-v2.1.6-preview)。

在 Apple Silicon Mac 的 Simulator 開啟一台 iPhone 後，解壓 `UniWay-iOS-simulator.zip`，
可用 `xcrun simctl install booted Runner.app` 安裝，再執行 `xcrun simctl launch booted tw.uniway.app`。
本次雲端產物以 Xcode 26.3 的 Simulator SDK 建置，建議使用同版或相容的新版本。

建置分為裝置編譯、Simulator 編譯、模擬器安裝及啟動，需各步成功才能認定對應部分完成。
目前不需要上傳任何 Apple 密碼、私鑰或憑證到 repository。

在有 Xcode 的 Mac 也能執行：

```sh
cd mobile_flutter
flutter pub get
flutter build ios --release --no-codesign --dart-define=API_BASE_URL=https://app.uniway-tw.com/
flutter build ios --simulator --debug --dart-define=API_BASE_URL=https://app.uniway-tw.com/
```

## 未來啟用 TestFlight

1. 加入 Apple Developer Program，在 App Store Connect 建立 UniWay。
2. 註冊上述兩個 bundle ID 與 App Group，App 及 Widget 都開啟 App Groups capability。
3. 用 Xcode 開啟 `mobile_flutter/ios/Runner.xcworkspace`，在 Runner 和 Widget target
   選擇相同開發者 Team，配置簽署及 provisioning profiles，保留既有 bundle ID。
4. 在實體 iPhone 測試 Google 登入回傳、跨裝置資料同步、Keychain、通知權限、排程及 Widget。
   如需遠端推播，再啟用 Push Notifications、配置 Firebase iOS app 和 APNs key。
5. 提高版本與 build number，以 `flutter build ipa --release --dart-define=API_BASE_URL=https://app.uniway-tw.com/`
   建立 archive／IPA，透過 Xcode Organizer 或 Transporter 上傳 App Store Connect。
6. 補齊測試資訊、隱私資料、所需審核資料，提交外部 Beta App Review。通過後開啟測試群組公開連結。
7. 將真正的 TestFlight 邀請網址加入 GitHub Release；往後透過 TestFlight 發布測試更新。

參考：[Flutter iOS 發布](https://docs.flutter.dev/deployment/ios)、
[Apple TestFlight](https://developer.apple.com/testflight/)、
[TestFlight overview](https://developer.apple.com/help/app-store-connect/test-a-beta-version/testflight-overview/)。
