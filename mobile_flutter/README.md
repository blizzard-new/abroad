# 交換指南 Flutter App

這是 Android 與 iOS 共用的 Flutter 手機專案。網頁版、FastAPI 與爬蟲仍保留在主專案；Flutter 只取代原本需要分別維護的 Kotlin Compose 與 SwiftUI 手機介面。

## 已搬移功能

- Apple 風格淺色 Liquid Glass 設計系統與 44 px 以上觸控區域
- 全台學生共用的留學貼文首頁，支援全部、追蹤、公共板與長庚板動態
- 發文時選擇公共留學板或長庚大學板，並可追蹤長庚板
- 長庚大學板保留目的地探索、學生任務入口與四階段申請進度
- 公共留學首頁與長庚大學板採兩層獨立導覽，進入長庚板後才顯示計畫、找學校、申請文件、時程與討論板
- 申請文件工作台會依交換、雙聯、實習、短期學分及補助／役男身分整理需要填寫的文件
- 共用姓名、學號、學院、系所與聯絡資料只填一次，並帶入所有適用表單
- 逐份表單檢查必填欄位、日期順序與附件數量；正式表單會保留長庚表單編號與官方來源
- 可設定每份文件列印份數及待列印、待簽名、待核章、待送件、已完成狀態
- 產生單份或整包 PDF 後由學生自行預覽、列印、親簽與送件，不會自動送出申請
- 62 校官方照片導向的合作校搜尋、收藏與學校詳細資料；清單只顯示關鍵資訊，完整資格點進後查看
- 保存學院、學制、成績、語言、目標學期、國家與預算，並依公開條件排序推薦合作校
- 文件可標記為待準備、準備中或已完成，首頁顯示整體計畫進度與下一步
- 交換預算估算，整合生活費、一次性支出與預計補助
- 申請日曆可直接連接手機中的 Google、iCloud、Outlook 或本機日曆，新增與修改任務時同步寫入
- Android 與 iOS 桌面 Widget；Android 同時宣告鎖定畫面類別，iOS 提供三種鎖定畫面尺寸
- 不指定 App 專用字型，文字會使用 Android／iOS 系統字型並跟隨系統文字大小
- 長庚規定、補助要點及官方文件摘要
- 合作校詳細申請流程
- 生活情報、來源排序與具體重點
- 學生文章、影片及社群心得來源
- 截止日期與官方公告
- Email 建立帳號、登入、公開暱稱與個人申請資料
- 全校留學社群、結構化貼文、主題搜尋、留言與校別公開聊天室
- 邀請制私訊、接受邀請、封鎖與檢舉

Google 與 Facebook 按鈕會讀取後端 `/auth/providers` 狀態。尚未設定 OAuth 金鑰時會清楚顯示為不可用；行動 App 的正式第三方登入仍需在平台後台補上 App callback/deep link，Email 登入不受影響。

App 會讀取與網頁共用的 `/static/assets/school-images.json` 清冊，使用 62 間合作校各自的官方網站圖片。詳細頁可開啟「官方圖片來源」；圖片缺漏或載入失敗時只顯示中性校園圖示，不會套用其他學校或地區照片。正式商業上線前仍需逐一確認圖片使用授權。

## Windows 開發

Flutter 安裝位置：

```text
C:\Users\User\development\flutter
```

專案位於中文路徑時，Flutter 分析器可能無法解析 LSP 訊息。Release 腳本會同步到下列英文鏡像路徑後分析、測試與建置：

```text
C:\Users\User\development\exchange_guide_flutter_release_nav
```

執行分析與測試：

```powershell
$env:Path='C:\Users\User\development\flutter\bin;'+$env:Path
flutter analyze
flutter test
```

## Android 模擬器

先啟動主專案 FastAPI 的 `8000` port，再執行：

```powershell
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000/
```

建立 APK：

```powershell
flutter build apk --debug --dart-define=API_BASE_URL=http://10.0.2.2:8000/
```

目前驗證完成的 Release APK 位於：

```text
artifacts/exchange-guide-flutter-phone.apk
```

`1.9.0+12` 的 APK 目前連向 `http://192.168.50.232:8006/`，手機需和這台電腦位於同一個 Wi-Fi，且本機 API 必須保持啟動。若電腦 IP 改變或要跨網路使用，需以新的 LAN 位址重新建置，或改接正式公開的 HTTPS API。

App 內「長庚大學板 → 桌面小工具」可開啟 Android 系統的加入流程。Android 鎖定畫面是否提供小工具位置由系統版本、手機品牌與 Launcher 決定；不支援時仍可正常加入桌面。

因為 Flutter 的 Windows AOT 工具無法正確處理目前專案的中文路徑，Release APK 請使用已提供的一鍵腳本。腳本會先驗證英文鏡像路徑、同步程式碼、執行分析與測試，最後把 APK 放回 `artifacts/`：

```powershell
.\tool\build_windows_release.ps1 -ApiBaseUrl http://192.168.50.232:8006/
```

實體手機測試時，手機與電腦必須使用同一個 Wi-Fi，並將網址換成電腦的區域網路 IP：

```powershell
flutter build apk --debug --dart-define=API_BASE_URL=http://192.168.50.232:8006/
```

## iOS

Windows 可以維護 `lib/` 內所有共用介面與功能，也會保留完整 `ios/` 專案。最終 iOS 編譯、模擬器測試、簽署與 App Store 上架仍需要 macOS 與 Xcode：

```bash
flutter build ios --dart-define=API_BASE_URL=https://your-api.example.com/
```

iOS Widget Extension 的最低版本為 iOS 16，包含主畫面小／中尺寸及鎖定畫面的直列、圓形、矩形尺寸。第一次在 Mac 開啟時，請在 Xcode 為 `Runner` 與 `StudyPlanWidgetDefinitionHomeWidget` 選擇同一個 Team，並確認兩個 Target 都啟用下列 App Group：

```text
group.tw.edu.cgu.exchangeGuideFlutter
```

App Group 與實機簽署需要 Apple Developer 帳號。Widget 原生基礎由 `home_widget/study_plan_widget.dart` 產生；重新執行產生器可能覆寫已客製的 Android Glance 與 iOS WidgetKit 版型，更新前應先比對差異。

正式版本應使用 HTTPS API，不應沿用區域網路的 HTTP 網址。
