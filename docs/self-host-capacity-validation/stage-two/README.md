# 第二階段容量驗證

2026-10-18。交付隔離混合讀寫工具與跨 worker 草稿版本保護，**沒有通過 1000 人容量驗收**。100 人情境在 1／2／4 workers 都通過；較高負載出現長延遲及逾時，不能只看 HTTP 200 或已啟動的使用者數。

## 2026-10-20 容量熱點修正

1000 人失敗集中在 `/student-dashboard`：原本每位訪客都會複製完整合作校資料、補圖片與座標，再重做 Pydantic JSON 序列化。現在每個 worker 會依學校、公開網址、資料檔簽章與 30 秒時間窗共用已序列化的 JSON／gzip；同一波首次請求只建立一次，並提供 ETag。登入驗證則由單一 service-role RPC 同時驗證未到期 session 並取得帳號／工作區快照，取代每個私人 API 的三次 PostgREST 往返；登出仍直接刪除共用資料庫 session，沒有加入跨 worker 不一致的驗證快取。

在相同開發雲端以 1 worker、loopback、已暖機長庚 dashboard 執行 1000 人於 10 秒內各載入一次，結果為 **0 失敗、p95 34.60 ms、p99 250.71 ms**；單次傳輸由未壓縮 355,383 bytes 降為 gzip 40,370 bytes。完整機器可讀結果見 [`capacity-read-path-2026-10-20.json`](../capacity-read-path-2026-10-20.json)。這只證明原本逾時的公開入口熱點已移除，**不能取代 4 workers、真實 PostgreSQL／PostgREST、混合讀寫一小時的 1000 人驗收**。套用新 migration 後仍須重跑下方完整案例。

## 環境與方法

測試在開發用雲端環境執行，工具所在 shell 的 CPU quota 為 4 CPU、記憶體上限 16 GiB；Docker daemon 回報 5 CPU／約 17.63 GiB，實際服務另受各自配額限制。這不是使用者的 i9-12900K／128 GB Windows 主機。app 上限 3 CPU／6 GB、每 worker 16 threads、2 個 catalogue slots；流量產生端上限 2 CPU／3 GB。完整設定見 [environment.json](environment.json)。

雲端 Docker 使用 VFS，32 GiB 工作磁碟無法容納專案固定的 Supabase PostgreSQL 映像及建置暫存，因此此處以較小的 PostgreSQL 17／pgvector 映像初始化相同角色並套用 **全部 39 個 migrations**，使用專案固定版本的 PostgREST、內部 HTTPS gateway 與 Caddy 壓縮入口。沒有啟動 Storage 服務。交付的 Windows compose 保留正式套件原本固定的 Supabase／PostgREST／Storage 映像。

最終量測時雲端工作磁碟約剩 0.8 GiB；VFS、主機 CPU 競爭、流量工具與網站同機，均限制結果的代表性。這些數字不代表 Windows 主機的上限，也不證明完整 Supabase stack 的吞吐量。雲端工具容器重用以避免 VFS 重複複製大型映像；執行的程式、掛載與配額與 compose profiles 相同。

每人使用不同合成帳號與正常 bearer session，先驗證帳號並載入長庚目錄，再每 10 秒一輪讀文件／期限、讀寫並讀回工作區、讀寫並讀回加密草稿。100 人測 60 秒、10 秒加入；較高負載的診斷測 30 秒、10 秒加入。後者不是長時間穩定性驗收。各程序共用加入時程，每個程序最多 100 人，1000 人使用 10 個程序。

初期的單一流量程序在高載時用滿 1 CPU，該批高載延遲不能用來判斷網站容量。最終工具改用多程序，合併原始延遲樣本計算 p95，並記錄各程序與配額的平均 CPU 使用量。下表只使用更新後工具的結果，流量產生端均未觸發飽和門檻。

## 結果

初始預算的 gateway／PostgREST 上限為 0.25／0.5 CPU。500 人診斷快照中 gateway 約用到 23.85% CPU，接近其配額；調高為各 1 CPU 後重測，仍未通過高載門檻，故不能把配額視為唯一瓶頸。

|預算|workers|人數／完成|實際 requests/s|最慢路徑 p95|非預期 HTTP 失敗|判定|
|---|---:|---:|---:|---:|---:|---|
|初始|1|100／100|78.45|0.417 秒|0|[通過](mixed-w1-u100.json)|
|初始|2|100／100|78.84|0.083 秒|0|[通過](mixed-w2-u100.json)|
|初始|4|100／100|78.83|0.078 秒|0|[通過](initial-budget-w4-u100.json)|
|初始|4|300／300|133.08|14.167 秒|0|[未通過](initial-budget-w4-u300.json)|
|初始|4|500／348|133.30|30.029 秒|152|[未通過](initial-budget-w4-u500.json)|
|初始|4|1000／324|134.84|30.051 秒|676|[未通過](initial-budget-w4-u1000.json)|
|調高配額|4|300／300|143.42|15.301 秒|0|[未通過](mixed-w4-u300.json)|
|調高配額|4|500／381|147.38|30.024 秒|119|[未通過](mixed-w4-u500.json)|
|調高配額|4|1000／383|135.49|30.072 秒|617|[未通過](mixed-w4-u1000.json)|

1000 人調高配額後，383 人完成操作，617 人在學校目錄請求逾時；這輪明確不合格。已完成的儲存均檢查 revision 及每人的內容標記，但這不代表未完成的學生也能順暢使用。沒有把較高負載的診斷結果當成可投入服務的容量。

每輪前置檢查都要求同一版本並行儲存一筆 200、一筆 409；多 worker 時必須記錄到不同 PID。登出後重新連線，確認每個預期 worker 都回 401，另一個帳號仍有效。對應的 PID、狀態與錯誤均在各 JSON。額外的 [兩個流量程序小型檢查](process-smoke.json) 通過。數據不含 bearer tokens、帳號內容或 service keys。

## 回歸與重現

依各案例最後結果去重，共 **119 個相異案例通過**：初次回歸 118 項，之後新增 1 項流量合併／CPU 飽和判定案例。可用以下指令重現目前的 119 項組合：

```bash
.venv/bin/python -m pytest -q \
  tests/test_capacity_stage_two.py tests/test_form_drafts.py \
  tests/test_catalogue_memory.py tests/test_selfhost_package.py \
  tests/test_catalog_access.py tests/test_atomic_auth_mutations.py \
  tests/test_account_workspace_api.py tests/test_transient_auth.py \
  tests/test_supabase_repositories.py
```

多程序工具新增後，重新執行 `tests/test_capacity_stage_two.py tests/test_selfhost_package.py`，**32 passed**（含重複案例）。另通過 OpenAPI `--check`、Python compileall、PowerShell 語法與隨機金鑰／JWT 檢查，以及實際 PowerShell Status 的 compose JSON／隔離檢查。Windows 的 ACL 與完整 Setup 尚未在 Windows 執行；Linux PowerShell 的 Status 檢查僅以 stub 替換 icacls。

實際主機的完整啟動、分級測試及 1000 人一小時測試指令見 [操作指南](../../../deploy/capacity/README.md)。應在自己的主機先從 100 人開始，未達標時先停止升級人數，檢查 CPU／節流、API 處理時間、資料庫查詢與連線等待。此處較高負載僅為隔離診斷；正式服務不受測試程式控制。

下一個有效的容量結論需要 Windows 主機的同配置測試；若仍看到同樣瓶頸，再依實際 profile 減少私人 API 的重複帳號／工作區讀取或調整資源。不能用增加記憶體取代量測，也不能以這次短測保證 1000 人。

PDF／Word、檔案上下載、多校大型目錄、瀏覽器資源與互動、外部 OAuth、外網與路由器 QoS、1500 人尖峰及一小時穩定性都不在已通過範圍。
