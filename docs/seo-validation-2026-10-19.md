# SEO 驗收紀錄（2026-10-19）

基準：`6d48e08549e4a8bf05b13adeaf03f2ec4b29d46f`；隔離開發資料與本機 HTTP 服務，不接正式帳戶或資料庫。

## 已驗證

- 29 項 SEO 測試通過：18 所母校的目錄、合作校正文與 sitemap 對應；metadata、canonical、JSON-LD、來源狀態、跳回母校、HEAD、404／503、noindex、惡意文字轉義、公開頁面不查私人 session、快取到期更新與錯誤處理。
- API／首頁 UI 契約共 7 項通過；法律頁面、request origin、自架套件共 54 項通過。最初有一項舊首頁標題比對失敗，依新的 SEO 標題更新後已重跑通過。
- Chromium 3 項通過：390px／1280px 在 JavaScript 關閉時，目錄 → 母校 → 合作校 → 母校導覽正常且無水平溢出；正常首頁啟動 JavaScript 後保留 SEO 標題。
- 以上是 **93 個相異測試**，不是整個 repository 的全套測試。使用現有 `tests/e2e` fixture 與系統 Chromium；瀏覽器校庫是明確的合成測試資料。
- OpenAPI 契約、Python compileall、app.js 語法與 `git diff --check` 通過。未更動內建官方資料或資料庫 migrations。
- [完整 HTTP 檢查輸出的 JSON 報告](seo-http-check-2026-10-19.json)：18 所母校、3,540 個合作校頁面，加首頁、目錄、母校頁共 **3,560 個 HTML 網址**，19 份子 sitemap；總共 3,581 次順序 HTTP 請求，全部通過。這是現有校庫的網頁數，同一海外學校對不同母校可有不同頁面，不代表 3,540 所不同學校或當期可申請名額。

完整 HTTP 檢查使用真實 bundled catalogue 與隔離 runtime；長庚來源可沿用已驗證快照。此檢查沒有重新核對每條官方規定，也不代表 Google 已收錄。快取調整後執行完整驗收，未用局部抽樣替代。

## 重現指令

```bash
EXCHANGE_INFO_DATA_DIR=/tmp/uniway-seo-tests PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium \
  .venv/bin/python -m pytest -q tests/test_seo.py tests/test_api.py tests/test_uniway_ui_contract.py tests/e2e/test_seo_pages.py
EXCHANGE_INFO_DATA_DIR=/tmp/uniway-seo-regression \
  .venv/bin/python -m pytest -q tests/test_legal_pages.py tests/test_request_origin.py tests/test_selfhost_package.py
EXCHANGE_INFO_DATA_DIR=/tmp/uniway-seo-contract .venv/bin/python scripts/export_openapi.py --check
.venv/bin/python -m compileall -q src
node --check src/exchange_info/static/app.js
```

若沒有 `/usr/bin/chromium`，使用 repo 原本安裝的 Playwright Chromium 並省略 executable 設定。

另啟動測試服務後執行（canonical 仍指向正式站）：

```bash
EXCHANGE_INFO_DATA_DIR=/tmp/uniway-seo-local EXCHANGE_SEO_INDEXABLE=true \
  EXCHANGE_PUBLIC_BASE_URL=https://app.uniway-tw.com \
  .venv/bin/uvicorn exchange_info.api:app --host 127.0.0.1 --port 8019
.venv/bin/python scripts/check_seo.py --base-url http://127.0.0.1:8019 --all-pages --delay 0
```

## 尚需外部驗收

- PR 的遠端完整 CI 結果以 GitHub 當前狀態為準。
- Windows 自架正式站合併／部署後，再跑正式網域 HTTP 驗收與登入／選校煙霧測試。
- 使用者已確認 Search Console 完成網站驗證；sitemap 提交與網址審查尚未執行，因本環境沒有該登入工作階段／API 或 Windows 主機連線。
- 搜尋收錄、曝光與排名需持續觀察，不能算入本次程式驗收。

部署、回復、Search Console 連結與追蹤指標見 [SEO 上線指南](seo-launch.md)。Notion 兩項任務在完成上述外部驗收前維持「進行中」。
