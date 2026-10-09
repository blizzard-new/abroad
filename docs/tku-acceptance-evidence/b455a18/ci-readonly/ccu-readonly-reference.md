# CI 唯讀診斷與待整合建議

`e8383073552a89afb5ef548493da5be5cd2f8167` 的 GitHub run [37845141592](https://github.com/blizzard-new/abroad/actions/runs/37845141592) 為 failure／0 jobs，並未執行 CI 測試。官方 actionlint v1.7.7（release checksum 已驗）回報 `quality.yml:20`：`jobs.test.env` 不允許 `runner` context。GitHub 官方 [context availability](https://docs.github.com/en/actions/reference/workflows-and-actions/contexts#context-availability) 表亦顯示 job env 不含 runner，step run 才可使用 runner。可見故障有具體 workflow 語法原因；沒有證據歸因於付款、權限或憑證。

[建議 patch](quality-proposed.patch) 將路徑透過既有 `$RUNNER_TEMP` 寫入 `$GITHUB_ENV`，後續步驟沿用隔離測試資料目錄。在 clone 外的修改副本 actionlint exit 0；正式 `.github/workflows/quality.yml` **未修改**，沒有改存取、付款或安全設定，也沒有宣稱遠端 CI 已恢復。統一整合時須套用建議並在精確候選 SHA 重跑遠端 CI。

本診斷另保留 [目前語法錯誤](actionlint-current.txt) 與 [副本驗證結果](proposed-validation.json)。`/usr/bin/go` 並非可執行 `go run` 的 Go SDK，最初該檢查實際失敗；上述結果來自下載並驗證的 actionlint 二進位。
