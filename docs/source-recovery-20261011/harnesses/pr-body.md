本分支恢復CGU公開名冊來源，整合六校資料與照片／地球識別，保留未知、待審、歷史參考與明示零。固定候選 `160aeacd15521d63df6a5624bd12821cc5d26cea` 已推送供復原；維持Draft，尚未宣告可發布。

完整本機測試：2,919個唯一collected cases逐項對帳，2,906 passed、13 skipped、0 failed、0 notrun；四分片起訖同一clean SHA。13 skips為9項既有Phase C及4項缺Ollama模型。完整35-migration Supabase runtime通過，含37 RLS表、真實Storage、跨校verified-email、原子治理與回滾；wheel實際打包／checkout外安裝6,579檔逐hash核對及六校API smoke通過。

175步冷暖記憶體仍待完成：兩次冷測分別因截圖與切校等待逾時中止；460 MiB門檻與等待未放寬，第三次原負載加失敗觀察器重跑，暖測待執行。初次runtime ENOSPC與所有重跑原始輸出保留。資料量不同的舊8e／3129結果不作本候選通過證據。

[固定原始證據](https://github.com/blizzard-new/abroad/blob/9f6cce7da9a24f18823b1ecffb6552c00d3e8782/docs/source-recovery-20261011/README.md)。下一批NCU baf98c0d、CCU258ce9bb、NTUdc9bbcdd尚未納入本SHA；TKU1619ba89仍有Sunderland錯校照片及UAEMEX署名待核阻擋。

此資料增量相對main59無新增或修改migration。沒有merge main、正式DB或部署，未改Quality停用、Render、分支保護、憑證或付費。main更新會觸發Render，Actions帳務受阻不能假定DB同步。正式發布由父對話依固定證據核對production SHA／DB版本／備份後協調，資料仍未全校當期完整。
