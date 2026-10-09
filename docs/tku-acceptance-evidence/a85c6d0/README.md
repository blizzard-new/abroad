# TKU a85c6d0 固定候選驗收

本機十步全部執行，guard 起訖皆為乾淨 a85c6d0d39fe7896e7560cea15a3c55f02facc83。主 suite 1526 項：1502 passed／16 failed／8 skipped；54 相關 browser 通過，其他九步 exit0。851 個 CGU／NTPU／NTU workflow hash 不變。剩餘 16 個失敗原文保留，不因 baseline 相同而豁免。

另 19 隱私回歸通過，保存 54 次實際 HTTP 回應。Supabase mock routing 明確標記，不當成資料庫整合。兩輪 a85 CI 都在新政策 probe 的 `Policy retry differs` 失敗，Web suite／main controls 未跑、零 JUnit artifact；原八個 job log 和 metadata 保留。此 probe 誤比較首次 idempotent:false 與 replay:true，獨立修正在 5e010b8。沒有重新標記 a85 結果。

本機 Docker layer no space error、首次 SHA 参数抄錯的 guard exit2／零執行、修補驗證首次拼錯測試檔名 exit4／零測試均留原紀錄。後續正確測試分開保存。GitHub CLI 401 是工具觀測轉錄，活躍連接器正常授權讀取；未改憑證、權限或重试其他環境 403 資源。

資料保持 128 方案列（4 当期／124 参考）；2027–2028 日語二甄校內9/30中午臺北截止已過，0 個可新申請。89／152 重要欄核實（58.6%），63 缺口、13 矛盾組仍保留。五組治理接線只交具體整合計畫，不以新建產品消除測試失敗。

原 XML、log、JSON 和 browser 成果保留在本目錄；summary.json 是索引，不改原 bytes。各結果綁定原 commit。最新 5e010b8 的獨立增量驗證及 CI 在其專用證據分支交付。未 merge main、部署或操作正式資料庫。
