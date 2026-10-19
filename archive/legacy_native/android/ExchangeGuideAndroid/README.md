# 交換留學資訊 Android App

這是「台灣大學生交換申請資訊整理系統」的 Android Studio 專案。第一階段只呈現長庚大學資料，資訊架構與 iOS App 一致，並使用 Android 原生 Kotlin、Jetpack Compose 與 Material 3 實作。

## 環境

- Android Studio 2025.3.2 或更新版本
- JDK 17+
- Android SDK 36.1
- FastAPI 後端位於本專案根目錄

## 開啟專案

1. 在 Android Studio 選擇 **Open**。
2. 開啟 `android/ExchangeGuideAndroid`。
3. 等待 Gradle Sync 完成。
4. 選擇模擬器後執行 `app`。

## 啟動後端

在整個留學專案根目錄執行：

```powershell
python -m uvicorn exchange_info.api:app --app-dir src --reload --host 0.0.0.0 --port 8000
```

Android 模擬器會透過 `http://10.0.2.2:8000/` 連到電腦上的 FastAPI。實機測試時，請把 `app/build.gradle.kts` 的 `API_BASE_URL` 改為電腦在同一個 Wi-Fi 的區域網路 IP。正式環境必須改用 HTTPS。

也可以在建置時覆寫網址，不必修改專案檔案：

```powershell
.\gradlew.bat -PAPI_BASE_URL=http://192.168.1.20:8000/ assembleDebug
```

實機與電腦必須連到同一個 Wi-Fi，後端服務則需監聽 `0.0.0.0`。只有 debug 版本允許區域網路的 HTTP 連線；正式版本仍使用限制較嚴格的網路設定。

## 已完成畫面與功能

- 總覽：長庚大學識別、資料量、學生任務入口、近期資訊
- 找學校：關鍵字、國家、方案篩選
- 學校詳情：可橫向滑動的重點指標列、四格申請摘要、可展開的完整條件與官方來源
- 詳細流程：校內推薦、合作校申請、文件、簽證與出發步驟
- 學生心得：公開文章、影片、跨來源重點與原始連結
- 生活情報：依來源覆蓋排序，直接顯示具體列點與原始連結
- 學生社群：整體指標列、貼文四格摘要、全文與留言收合、公開聊天、邀請制私訊、檢舉與封鎖
- 截止日期：長庚公告與合作校期限
- 補助與文件：摘要、適用對象、必要條件、注意事項、完整文件
- 資格檢查：學院、學制、成績與語言門檻初步比對
- 預設淺色乳白玻璃風格、圖示優先首頁、可收合資訊，以及與 iOS 相同的漂浮 Liquid Glass 底部導覽
- Loading 骨架、錯誤重試、48dp 最小觸控區

## 測試與建置

```powershell
./gradlew.bat testDebugUnitTest
./gradlew.bat assembleDebug
```

為避開 Windows 對非 ASCII 專案路徑的測試 classpath 限制，建置輸出會放在 `%USERPROFILE%/.gradle/exchange-guide-android-build/app`。Debug APK 位於該目錄下的 `outputs/apk/debug/app-debug.apk`，已驗證的副本也放在 `artifacts/exchange-guide-debug.apk`。

## 資料與隱私

App 只讀取後端整理過的公開資料，不登入校務系統、不收集個資。摘要用於快速理解，正式申請仍須開啟每筆資料保留的官方來源確認。
