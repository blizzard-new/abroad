# TKU 治理接線進度

使用者於 2026-10-09 07:33 UTC 選擇原有計畫選項 3，本批納入五組審核、發布與回滾接線。只在候選分支與隔離合成資料實作／驗證；正式資料庫、main、部署、憑證與存取設定均不在授權範圍。

前一個獨立里程碑 `5af863f50f4ceecbb2b042d512137344fb2988d7` 已推送：12 項舊契約修正，182 項相關單元與 32 項瀏覽器測試通過，實際 collect 1,789 IDs／184 檔與 `09386aa` 原始 CI 相同，沒有移除、重複或新增 skip。產品 src 與 supabase tree 在這個里程碑仍與 `09386aa` 相同。之前 `c6e6155` 兩輪完整 CI 各為 1,767 passed／6 failed／16 skipped；5 項治理缺口及兩輪各一項非同步等待失敗保留原始證據，不予豁免。

治理第一階段將管理 HTML、admin session、來源候選／缺口／快照 CSV、deterministic staging、目的地審核／promote／history／rollback、流程 history／readiness／rollback 接到原有服務。既有 approve/reject/publish 與新增接線共用程序內鎖，所有入口仍用原有管理員驗證，private/no-store。CSV 是唯讀清單，沒有匯入 approvals；工作台沿用現有 UI，沒有自動批准或填補官方缺值。

尚不能由 API 接線宣稱交易驗收完成：現有 workflow publication 先分次儲存 revision 再改公開資料，目的地 Supabase event 寫入亦缺少跨程序 CAS。下一階段需補既有 stores 的原子命令提交／精確 snapshot 校驗、故障回復與冪等測試；不擴出平行審核機制，不降低雙審與來源／rule hash 門檻。readiness 僅呈現資料阻擋原因，並非部署許可。TKU 63 項官方缺口、未發布的 4 個 workflow 與所有既有學校資料保持原狀。

固定 SHA `e300479` 複核：32 項 API／權限／快照單元通過，但原有管理台錯誤回報 browser case 實際失敗（已結案卡片仍在待處理清單）。API 原本忽略 status query；第一次未固定 SHA 的短暫通過及本次真實失敗分別保留。後續追加 API enum 篩選與隔離回歸，不移除原卡片消失／完整 audit 等斷言。
