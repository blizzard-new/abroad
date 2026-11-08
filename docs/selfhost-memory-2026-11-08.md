# 自架網站記憶體修正（2026-11-08）

## 原因與修正

- 舊暖機逐一載入 66 校的合作校、工作流程與完整 JSON/gzip。每個 Uvicorn worker 各持有一份；現在只預載首頁 CGU 和共用翻譯，其餘在請求時載入，資料與來源欄位完整保留。
- 儀表板每 30 秒產生新快取鍵，舊版最多保留 96 份，沒有位元組預算。現在每個 worker 最多 64 MiB／32 份，同一學校與 base URL 只保留一個版本，使用 LRU 淘汰；超大回應完整送出但不留快取。原有單次建置、gzip、ETag、資料檔變更失效規則均保留。
- 爬蟲觸發跨校目錄更新時，glibc 會保留暫存配置。自架容器固定 `MALLOC_ARENA_MAX=2`、`MALLOC_TRIM_THRESHOLD_=131072`、`MALLOC_MMAP_THRESHOLD_=131072`，限制 arena 數並讓大型暫存配置及時釋放。沒有加入每個請求強制 GC、定時重啟或刪除資料的工作。
- 自架啟動預設為 4 workers、每程序 4 threads、1 個重型目錄請求；健康檢查不占目錄併發配額。app 容器記憶體預設上限 16 GiB，總記憶體與 swap 上限相同，不借用主機 swap。

## 量測

以修正前映像及相同資料的修正版，在沒有網路／正式資料庫的隔離 Linux 容器比較。每容器限 2 CPU、8 GiB；RSS 是單一程序，不是整個網站。程式版本基於 `0add152d04a0cb7273709a2a4163b97cdd0b8d5e`。

| 情境 | 修正前 | 修正後 |
| --- | ---: | ---: |
| 暖機完成 RSS | 1,609 MiB | 411 MiB |
| 儀表板反覆更新及讀取全部 66 校：最高 RSS | 1,823 MiB | 1,014 MiB |
| 同情境最後保留的回應內容 | 311 MiB | 63.54 MiB |
| 19 個公開跨校頁面、12 輪目錄快取過期：最高 RSS | 2,518 MiB | 1,149 MiB |

儀表板比較沒有套用配置器參數；跨校頁面修正版包含配置器參數。兩者都是整體修正的比較，不是各項參數的獨立效應。過期測試只推進目錄的快取時鐘，不改變來源日期或系統時間。最後的手動 `malloc_trim` 僅用於診斷配置器保留量，不是正式服務的修正方式。

43 項快取、資料完整性、單次建置、健康檢查背壓、跨校頁面與來源隔離測試通過。Windows 測試使用 `PYTHONUTF8=1`（既有測試讀 UTF-8 檔案依賴預設編碼）。本次沒有改動資料庫結構、登入或私有文件資料。

這些是工程情境的短期量測，不能代替千人容量或所有路徑的長期壓測。新增學校、資料量或服務後仍須重新評估總預算；容器上限是最後一道隔離界限，不是正常用量目標。

## 既有安裝與重啟

Git 不會覆寫既有 `deploy/selfhost/.env`，所以必須持久設定：

```dotenv
APP_WORKERS=4
APP_THREADS=4
APP_CATALOGUE_CONCURRENCY=1
APP_MEMORY_LIMIT=16g
```

更新程式及映像後，只重建 app，無須重啟 Docker／資料庫或刪除磁碟區：

```powershell
docker compose up -d --no-build --no-deps app
docker inspect uniway-app-1 --format '{{json .Config.Cmd}} {{.HostConfig.Memory}} {{.HostConfig.MemorySwap}}'
docker stats --no-stream uniway-app-1
```

預期指令為 4 workers，Memory 與 MemorySwap 均為 17179869184。單純 `docker restart` 會保留現有容器的設定；修改 `.env` 後必須先 `compose up` 重建一次。應保留修正前映像與受保護的 `.env` 備份，驗證首頁、健康檢查、目錄讀取及重啟後程序數，再確認部署完成。
