# UniWay 交換指南 Flutter App (`mobile_flutter`)

這是 Android 與 iOS 共用的唯一正式 Flutter 行動端專案（目前版本 `2.2.0+24`）。網頁版、FastAPI 與爬蟲位於主專案；早期獨立的原生參考實作已封存於 [`../archive/legacy_native/`](../archive/legacy_native/README.md)。

## 核心產品與設計原則（UniWay Metro 指標系統）

- **完整同步全台 71 所大專院校**：離線內建並同步後端 [`university_registry.py`](../src/exchange_info/university_registry.py) 全部 **71 所**台灣大專院校，底部彈出選單支援校名、簡稱、英文縮寫與「台／臺」即時搜尋，並將目前就讀大學置頂。
- **誠實去 AI 化（Deterministic Truth）**：遵循 [`../PRODUCT.md`](../PRODUCT.md) 與 [`../DESIGN.md`](../DESIGN.md)，移除所有失效或誤導性的雲端／本地 AI 改寫與對話端點；「格式與字數檢查」改接穩定運作的 `POST /document-check`（`consent=true`、`use_ai=false`），精確回報頁數、字數、字元數與版面規則檢查。
- **UniWay Metro 站體指標視覺**：採用高對比白底 `#FFFFFF`、輔助灰階 `#F3F4F6`、`1px solid #D6DAE1` 俐落邊框、頂部 `3px` 五色捷運指標線（`MetroLineBar`）與固定式底部導覽列（`旅程`、`學校`、`申請`、`論壇`、`我的`），全面支援 `2x` 系統字體放大與等寬數字（`tabularFigures`）。
- **開放狀態優先於個人配對**：合作校卡片明確區分 `本期開放`、`合作備查`、`名額未定`、`暫不開放` 與 `自費研修`；非本期開放學校絕不顯示誤導性的配對推薦標籤。

## 省時選校與申請工作流

1. **訪客與登入皆可儲存「我的選校條件」**：未登入訪客可於本機儲存學院、學制、平均成績與語檢分數，登入後自動銜接雲端工作區同步。
2. **高資訊密度合作校卡片與「僅看本期開放」篩選**：一頁直接閱讀國家、開放狀態、交換名額、申請期限、適用學制／語言重點與個人資格初判；僅在具備已驗證官方校園照片時顯示精簡照片列。
3. **2–4 校並排比較（Compare Tray）**：在找學校列表勾選 2 至 4 間合作校，即可拉出並排比較表對照開放狀態、名額、期限、語言門檻與費用摘要。
4. **一鍵「設為目標」直通申請文件**：在學校卡片、並排比較表或學校詳情點選「設為目標／設為申請目標校」，自動帶入申請文件上下文、預填空白學院與學制並切換至「申請」分頁（附復原 Undo）。
5. **真實優先截止日總覽**：首頁「下一個重要期限」合併校內官方申請期程、已收藏／目標合作校截止日與個人行事曆提醒，清楚標示 `校內官方`、`合作校` 或 `個人提醒` 來源與倒數天數。
6. **申請文件工作台與搜尋式目標校選擇器**：共用姓名、學號、系所與聯絡資料填寫一次即可套用至各表單；「申請設定」內合作校改為可搜尋清單並將已收藏學校置頂，支援匯出列印包 PDF。

## 串接公開與帳號 API

- 公開資料：`/universities`、`/student-dashboard?school=...`、`/deadlines?school=...`、`/application-workflow`、`/student-experiences`、`/application-center/templates`、`/application-center/pdf`
- 確定性文件檢查：`POST /document-check`（`consent=true`、`use_ai=false`，登入時附帶 `Authorization: Bearer <token>`）
- 社群、論壇與同步：`/auth/providers`、`/forum/boards`、`/forum/feed`、`/community/posts`、`/community/chat`、`/workspace`

## 本機開發與驗證

需要 Flutter `3.44.6`（Dart `^3.12.2`）：

```bash
cd mobile_flutter
flutter pub get
flutter analyze --no-pub
flutter test --no-pub
```

建置連線至正式站的 Android 預覽 APK：

```bash
flutter build apk --debug --dart-define=API_BASE_URL=https://app.uniway-tw.com/
```

若連接本機 FastAPI（Android 模擬器預設透過 `10.0.2.2` 連向主機 `8000` port）：

```bash
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000/
```

## CI 自動化預覽建置

- **Android APK Preview**：[`.github/workflows/flutter-android.yml`](../.github/workflows/flutter-android.yml) 會在 `mobile_flutter/**` 變更時自動執行 `flutter analyze --no-pub`、`flutter test --no-pub` 與 `flutter build apk --debug`，並上傳 `UniWay-Android-preview-debug.apk` 與 `.sha256` 校驗檔。
- **iOS Simulator & Unsigned Preview**：[`.github/workflows/ios-preview.yml`](../.github/workflows/ios-preview.yml) 會在 macOS 環境驗證 iOS 與 WidgetKit Extension 建置。
