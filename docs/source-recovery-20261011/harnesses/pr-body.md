CGU 兩份公開來源暫時失敗時，原本的 partner cache 會永久保留空陣列，dashboard 也可能把既有77列替換成0。本候選改為共用帶日期的完整來源快照：任一來源失敗保留資料、完整成功原子替換，列表／詳細頁顯示真實取得時間與參考性，空啟動明確顯示暫不可用。

本 Draft 從 PR #8 `9927ec1d8765a9772671bbaa68e7f920995f1258` 開始，將分批納入固定的學校資料檢查點。**尚未完成全部驗收，不可據此發布。** 沒有 merge main、部署、正式DB、Quality、Render設定、憑證或付費變更。

目前：初輪46來源/API測試通過、4手機桌面故障／恢復瀏覽器通過、兩份真實live公開來源HTTP200且77列hash相同；完整suite、六校回歸與512MiB單worker仍在進行。原始失敗／重跑結果將一併交付。

待整合：#9 NTU固定4566f7f（原文缺件與13fixture修復待作者新SHA）、#10 CCU固定c18aebf、#11 NCU固定5a3b690，TKU本輪固定SHA尚待提供。各校不完整／舊年／missing／pending／zero保留，不把一般校園內容視為當期可申請條件。

設計、來源收據及DB／程式發布與回滾邊界：`docs/integration/cgu-source-recovery-20261011.md`。各資料批次與本修复相對main均無migration；Render main commit會自動部署，而Actions DB同步不能假定成功，正式順序交由父對話另行協調。
