# Web ↔ Flutter 對等驗證矩陣

本矩陣追蹤 Web 與 Flutter 功能之間的對等狀態。

## 功能對等

| 功能領域 | Web 狀態 | Flutter 狀態 | 測試覆蓋 | 備註 |
|---|---|---|---|---|
| **帳號驗證 (D-01)** | ✅ 完成 | ✅ 完成 | `d01_auth_workspace_test.dart` (7 tests) | AccountSession、Token 過期、401/403 處理、ProductAccessTier round-trip |
| **多校動態字串 (D-02)** | ✅ 完成 | ✅ 完成 | `d02_guest_login_path_test.dart` (4 tests) | CGU/NTPU 動態 homeUniversity、Guest 預設狀態 |
| **Workspace 同步 (D-01)** | ✅ 完成 | ✅ 完成 | `d01_auth_workspace_test.dart` (3 tests) | 收藏、步驟進度、登出清除 |
| **PDF 產生 (D-03)** | ✅ 完成 | ✅ 完成 | `d03_document_consent_test.dart` (2 tests) | PDF API 呼叫與 500 錯誤處理 |
| **敏感資料排除 (D-03)** | ✅ 完成 | ✅ 完成 | `d03_document_consent_test.dart` (2 tests) | id_number、passport_number、birth_date 不在裝置記憶中 |
| **文件進度狀態 (D-03)** | ✅ 完成 | ✅ 完成 | `d03_document_consent_test.dart` (2 tests) | 6 階段狀態機、完成度百分比 |
| **AI Consent (D-03)** | ✅ 完成 | ✅ 完成 | `d03_document_consent_test.dart` (1 test) | rewriteDocument 傳送 ai_consent_granted |
| **日期擷取 (D-04)** | ✅ 完成 | ✅ 完成 | `d04_calendar_reminder_test.dart` (3 tests) | 中文月日、英文格式、年度翻轉 |
| **倒數標籤 (D-04)** | ✅ 完成 | ✅ 完成 | `d04_calendar_reminder_test.dart` (4 tests) | 今天、明天、X天後、已過X天 |
| **行事曆事件 (D-04)** | ✅ 完成 | ✅ 完成 | `d04_calendar_reminder_test.dart` (4 tests) | 事件建構、描述、dateKey round-trip |
| **提醒間隔 (D-04)** | ✅ 完成 | ✅ 完成 | `d04_calendar_reminder_test.dart` (1 test) | 30/14/7/3/1 天閾值 |
| **社群權限 (D-05)** | ✅ 完成 | ✅ 完成 | `d05_community_permission_test.dart` (3 tests) | Guest 無帳號、匿名身分、貼文解析 |
| **跨校存取 (D-05)** | ✅ 完成 | ✅ 完成 | `d05_community_permission_test.dart` (3 tests) | CGU↔NTPU 隔離、未驗證學生 |
| **帳號刪除 (D-05)** | ✅ 完成 | ✅ 完成 | `d05_community_permission_test.dart` (2 tests) | 登出清除、收藏切換 |

## 測試摘要

| 測試類別 | 檔案數 | 測試數 |
|---|---|---|
| 原有單元測試 | 9 | 28 |
| D-01 Auth/Workspace | 1 | 7 |
| D-02 Guest/Multi-university | 1 | 4 |
| D-03 PDF/Consent/Sync | 1 | 7 |
| D-04 Calendar/Reminders | 1 | 12 |
| D-05 Community/Deletion | 1 | 8 |
| D-06 Integration (smoke) | 1 | 2 |
| **總計** | **15** | **67+2** |

## 跨平台驗收需人工確認

- [ ] Web 與 Flutter 使用同一帳號交叉操作
- [ ] iOS / Android 模擬器走 guest 與登入黃金路徑
- [ ] 跨端草稿同步（Web 建立→App 繼續，反向亦同）
- [ ] Push notification 前景/背景測試
- [ ] Deep link 正確導向對應畫面
