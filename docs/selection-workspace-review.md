# Web 選校流程：七項改善驗收

日期：2026-09-24。分支：`codex/native-liquid-navigation`。

本次在現有 FastAPI、原生 JavaScript 與 MapLibre 架構上實作，沒有另外建立前端應用。僅更新 Web 和共用 API 的相容欄位；未修改 App，未提交 Git、部署或發布。

## 功能與操作

| 項目 | 已實作 | 驗證 |
| --- | --- | --- |
| 1. 搜尋與地圖預覽 | 保留列表與 3D 地圖切換；側邊卡先顯示名額、語言、費用、心得摘要及來源，再進入完整學校頁 | 真正載入 MapLibre；選校、預覽、開啟心得、返回與錯誤恢復測試；本機臺北大學資料人工查看 |
| 2. 個人條件篩選 | IELTS、TOEFL iBT、TOEIC、JLPT、TOPIK、Duolingo、學業成績與計分制、學制、交換學期 | 門檻比對、JLPT 反向等級、不同 GPA 制、不同方案、多項檢定、未公告名額與未知條件案例 |
| 3. 收藏、比較與志願 | 搜尋頁直接進入「我的選校」；最多比較 3 校；志願可拖曳、上下移動或 Alt＋方向鍵；前三個開放志願可帶入申請表 | 收藏與排序持久化、鍵盤排序、申請表帶入、桌機及 393px 手機版 |
| 4. 喜愛度與備註 | 1–5 顆愛心、「很想去／考慮中」、私人備註；輸入即保存，備註也出現在比較表 | 重整保存、隔離帳號、不同母校、全新瀏覽器情境從 API 還原 |
| 5. 分主題心得 | 住宿、吃飯、交通等主題；中文摘要優先；交換學期與發表日期分列；原文摘要折疊；連回完整文章或影片 | 主題切換、中文／原文、來源、閱讀視窗與鍵盤關閉；不把發表年份當成交換學期 |
| 6. 單獨收藏心得 | 心得與學校分開收藏；依國家篩選、依學校分組；保留文章原始連結 | 收藏後重整、國家與學校篩選、跨瀏覽器帳號同步 |
| 7. 最近看過 | 搜尋頁、登入入口與帳號頁提供學校／心得的最近瀏覽 | 查看學校與文章後記錄、帳號頁找回、登入過期與登出清除帳號快取 |

## 保存方式與相容性

- 訪客收藏、備註、志願、心得收藏與最近瀏覽依母校儲存在本機。個人成績僅用於當次篩選，不放入分享網址。
- 登入後使用既有 `/account/workspace`、revision 與衝突合併流程。資料按帳號及母校隔離。
- 修正母校切換時把空白載入狀態誤當修改上傳的問題；返回原母校會還原其收藏和筆記。
- `discovery` 是工作區的新欄位；舊客戶端未傳這個欄位時，API 保留現有值。明確傳空物件才清除。
- 登出或同步收到登入過期回應時，清除帳號的瀏覽器快取與閱讀視窗；伺服器保存的選校內容仍可於重新登入後取回。
- 文章 URL 限 HTTP(S)，筆記、排序、收藏與歷史都有長度及數量限制。

## 資料限制

- 「已知門檻符合」是依公開條件初篩，不等同錄取資格。缺少門檻、單科限制、方案差異或名額未公告時顯示「待確認」。
- 沒有學生心得時保留生活情報入口；既有官方資料與 AI 推論分類繼續使用。
- 未有中文翻譯時顯示待補並保留原文；不把英文硬標成中文。
- 缺少交換學期時標示「未標示」。費用顯示可確認的中文費用資訊或「待確認」，不自行估出價格。
- 測試截圖使用隔離的林肯／明治測試資料，不代表這兩校當期真實申請條件。

## 驗證紀錄

- 單元、API、資料整理、翻譯與前端契約：**168 項通過**。結果：`output/selection-workspace/unit-results.xml`。
- 新流程、地球地圖、生活情報、同步衝突與帳號隔離瀏覽器測試：**25 項通過**。結果儲存於 `output/selection-workspace/e2e-results.xml`。
- 額外登入／登出 API 測試：2 項通過。
- 四個相關 JavaScript 檔案通過 `node --check`。OpenAPI 快照已重新產生，`scripts/export_openapi.py --check` 通過。
- 畫面：`output/selection-workspace/desktop.png`、`mobile.png`。本機預覽：`http://127.0.0.1:8767/`。

原有廣域檢查另發現 5 項失敗，沒有因此宣稱全專案測試通過：

1. API 契約版本 metadata 缺少。
2. 私人社群 mutation header 未列於 schema。
3. 問題回報 mutation header 未列於 schema。
4. 舊訪客端到端測試的操作完成，但 `/community/boards` 404 使無 console error 斷言失敗。
5. 舊測試透過通知中心觸發登入過期檢查失敗；目前 API schema 未列 `/account/notifications`。新選校流程另外透過實際工作區保存的 401 驗證過期清理。

前 3 項在移除本次 discovery API 變更後仍可重現，記錄於 `output/selection-workspace/contract-baseline-check.json`；缺少的社群／通知路由另記於 `route-audit.json`。這些不屬於本次七項選校功能，保留待處理，未放寬其斷言。

## 主要程式位置

- `src/exchange_info/static/discovery-core.js`：條件判斷、資料裁切與 URL 檢查。
- `src/exchange_info/static/discovery-ui.js`、`discovery.css`：選校工作區、心得閱讀與收藏、最近瀏覽。
- `src/exchange_info/static/app.js`、`index.html`、`partner-map.js`：原有搜尋、地圖與帳號工作區整合。
- `src/exchange_info/discovery.py`、`models.py`、`api.py`：帳號資料欄位與中文心得來源整理。
- `tests/test_discovery.py`、`tests/e2e/test_discovery_workspace.py`：新增行為測試。

工作目錄原本已有大量未提交變更。本次沒有清除、還原或提交那些變更。
