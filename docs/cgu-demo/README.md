# UniWay CGU｜長庚交換申請導航

這是長庚「教育 × 行政創新黑客松」獨立展示入口。它沿用 UniWay 的 FastAPI、原生 JavaScript、品牌 token、Logo 及有雜湊驗證的長庚歷史快照。沒有新增套件、資料庫或付費服務。正式入口 `exchange_info.api:app` 與正式 UI 沒有更動；不在主站啟用展示連結。

## 可操作的範圍

- 3 所歷史交換／自費研修參考校，可搜尋、展開條件及來源、選為研究目標；不宣稱是當期開放名單。
- 長庚校內資格、文件、一般時間與官方來源摘要；說明不同來源日期與學期矛盾。
- 六階段、共 15 個可勾選待辦。固定情境為虛構學生「林小程」、預設 Lincoln 研究目標、2027 下半年個人目標，目的校學期待確認；預先完成前兩個探索待辦，起始 2/15。
- 可改選研究目標後建立固定或空白計畫；計畫建立後要換校須先重設，避免把已完成進度套用另一校。非 Lincoln 目的校不繼承 Lincoln 的官方要求，相關任務改為目的校待確認。
- 第一個未完成項目為下一步；可瀏覽所有階段，不把下一步推算成錄取或審查狀態。
- 每項可設定／清除「個人目標日期（非官方期限）」，完成狀態與日期可跨頁面及重新整理保存。
- 只刪除 `uniway-cgu-demo:v1` 的展示重設；有確認、取消與 Escape 返回。
- 儲存封鎖／容量失敗會明示僅暫存；損壞／版本不符資料不自動覆蓋。另一分頁變更後鎖住舊頁編輯，要求重整，避免默默覆寫。
- 官方來源隨版保存、來源缺漏顯示待確認；內容失敗有重試；沒有學校資料時仍可閱讀官方摘要，但不建立虛假選校計畫。

## 規劃中及未做

AI 問答、校方公告同步、登入及申請狀態同步、文件送達／收件編號／受理 API 均為未來構想。產品 AI 現有 runtime 為 paused，本展示沒有模型呼叫，也不把規則待辦稱為 AI。

此展示不提供正式登入、文件上傳、PDF 工作台、收藏比較、日曆同步、跨裝置同步、實際送件或通知；既有主站有相應程式與 API，但本次不把它們接入展示帳號或宣稱全部已驗證。後續要擴充時需維持正式發布閘門及帳號隔離。流程以參考情境設計，面試、體檢、簽證與返國要求並非一律適用。

## 本機預演

在 repository 根目錄：

```sh
# 已安裝專案的環境（既有 .venv 或依 README 安裝 .[dev]）
PATH="$PWD/.venv/bin:$PATH" PORT=8765 sh scripts/run_cgu_demo.sh
```

開啟 `http://127.0.0.1:8765/` 或 `/cgu`。正式 app 不需要啟動。不需 `.env`、API key 或資料庫。環境變數範例見 `deploy/cgu-demo/demo.env.example`。

直接指令：

```sh
uvicorn exchange_info.cgu_demo:create_demo_app --factory --host 127.0.0.1 --port 8765 --workers 1 --no-proxy-headers
```

## 隔離設計

`cgu_demo.py` 建立獨立 FastAPI app，不 import 正式 `api.py`，不初始化帳號 repository、文件庫、通知、分析或表單草稿。僅有 GET 讀取路由及 5 個列入允許清單的靜態資產，不掛載整個正式靜態目錄。沒有登入、送件、上傳、重設 API，也不發信、不寫檔或背景刷新學校資料。`demo_catalogue()` 重用 `validate_snapshot()`，不呼叫會寫入 cache 的 `CguCatalogue.view(refresh=True)`。

前端的 `/demo/content` 請求使用 `credentials: omit`；沒有 session、token 或校務密碼儲存。本機資料名稱獨立且沒有 `localStorage.clear()`。不同子網域的 localStorage 天然分開；同一 host 開發時也不讀取正式 `exchange-guide-*` key。即使誤帶 Cookie，服務也不解析或恢復登入。正式站若設了父網域 Cookie，部署前仍應查核 cookie scope，避免不必要傳送。

所有回應提供 CSP、no-store、noindex/noarchive、frame 拒絕及 referrer 限制。noindex **不是存取控制**；預設此服務是可公開瀏覽的虛構資料展示。若要私人預覽，必須另用現有服務端／入口代理驗證，不能加入前端密碼。

## 經審查後部署至 demo.uniway-tw.com

以下是準備步驟，**本次未執行部署、改 DNS、開自動合併或修改正式服務**。

1. 審查 PR、來源限制、測試紀錄與下面的已知限制；決定是否允許公開虛構情境，或要在既有反向代理加入真正的服務端保護。
2. 在既有平台建立獨立 Web service／process，使用審查後的 commit。不要修改正式服務的啟動命令、登入環境、資料庫或掛載資料卷。不要照搬正式環境變數群組；展示無任何金鑰需求。
3. 使用既有 Python 3.12 工具鏈安裝專案，啟動命令指定上述 **demo factory**，host 設為 `0.0.0.0`、port 使用平台指定值。Docker 若沿用既有 image，僅在新的展示容器覆寫 CMD 為 demo factory；不掛正式資料卷。既有 image build／TLS 稽核規則維持不變。
4. 健康檢查 `/health` 應回 `mode=cgu-demo`、`persistence=browser-only`。驗證 `/auth/session`、`/account/workspace`、`/static/app.js` 不可用；確認沒有 Set-Cookie、資料庫連線、出信或私人文件端點。
5. 先在獨立平台暫時網址走完主線，再由使用者授權設定 `demo.uniway-tw.com` 的自訂網域、DNS 與 HTTPS。這次不推測 CNAME 目標，需平台建立服務後才能取得。只路由至展示服務，不代理正式 API。
6. HTTPS 下再重跑桌面／手機、重新整理、來源跳轉、reset、noindex／CSP 與 cookie scope 檢查。正式網域和子網域的 localStorage 不共用；現場請在實際展示網域載入固定情境。
7. 需要回復時只停止展示服務或還原其 commit；不得使用展示 reset 操作正式資料。暫不在主站頁尾啟用連結，避免尚未部署時連到不存在的網址。

既有完整專案 wheel 會收錄大量其他學校資料，這次打包約 2.3 GiB；建置暫存可超過 6 GiB。展示本身僅讀取長庚快照與少量資產。部署前需確認既有平台的 artifact／磁碟／build 限制；本次未另建精簡映像或新雲端服務。wheel 打包與抽取必要檔案的啟動驗證見 `validation.md`，不代表 Docker image 或遠端 host 已驗證。

## 交付文件

- [原始盤點與計畫](implementation-plan.md)
- [來源查核與適用限制](sources.md)
- [7 分鐘操作腳本及答詢](demo-script.md)
- [測試、截圖與已知問題](validation.md)
