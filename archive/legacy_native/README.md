# 舊版原生 App 封存目錄（Legacy Native Apps Archive）

本目錄封存早期分別以 SwiftUI 與 Kotlin Jetpack Compose 獨立開發的舊版原生雛形：

- `ios/ExchangeGuide/`：早期 SwiftUI 單校（長庚大學）原型
- `android/ExchangeGuideAndroid/`：早期 Kotlin Compose 單校（長庚大學）原型

## 封存原因与現行架構

1. **統一跨平台工程線**：目前行動端已全面收斂至根目錄下的 [`mobile_flutter/`](../../mobile_flutter/README.md)，由單一 Flutter 程式碼庫同時支援 iOS 與 Android，並共享 FastAPI 公開 API 與 18 所台灣大學註冊表（`GET /universities`）。
2. **避免雙線維護與認知混淆**：舊版原生目錄僅支援單一學校（長庚大學）且不再隨 18 校公開 API、申請文件工作台與社群架構更新，因此移入 `archive/legacy_native/` 作為歷史遷移參照，不再作為現行開發或發布目標。
3. **現行開發入口**：請見 [`mobile_flutter/README.md`](../../mobile_flutter/README.md)。
