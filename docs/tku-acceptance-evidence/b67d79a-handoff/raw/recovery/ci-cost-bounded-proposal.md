# GitHub自動測試停用與未實施的節省方案

使用者於2026-10-09T11:36:59.368787+00:00明確批准僅關閉blizzard-new/abroad自動測試。既有gh存取可用，官方PUT /repos/blizzard-new/abroad/actions/workflows/374368612/disable於11:41:04 UTC成功；回讀disabled_manually。API名稱.github/workflows/quality.yml、檔內名稱Web quality。部署workflow374368613 Deploy to Supabase仍active。未推main、改Render、branch protection、付款、權限或token；原runs／artifact／notifications未刪。workflow-list-before/after與quality-disable-proof.json保存原始回讀。

目前安排為開發環境跑完整測試後再推產品程式碼，自動Quality保持停用。GitHub帳務只阻塞該runner渠道，不是本機驗收必須付款的前提。不重試帳務失敗run，不建立runner憑證。下列僅是未實施的未来方案；是否恢復自動測試及更動YAML需另獲授權。

## 現況的可量測重複

quality.yml觸發push／pull_request／workflow_dispatch，兩種自動event各4shards。concurrency group使用github.ref，因此branch ref和refs/pull/.../merge不同，不會對同一PR+push去重。每shard都重做syntax、OpenAPI、34-migration parse、dependency audit及完整隔離Supabase／Storage runtime；完整Web suite才分片。artifact以run_id/shard命名，retention-days30，always保留。

完整M1來源e1c551a的PR37905061634和push37905055678各4 artifacts，實際API sizes分別9,649,280／9,629,842 bytes，合計19,279,122 bytes（18.39 MiB），同來源兩輪各1802 IDs全部執行。8份artifact原樣保留，不刪remote或改到期日。原始metadata見ci-cost-pr-artifacts.json和ci-cost-push-artifacts.json。測試minutes不能用這個單樣本推為每月帳單，失敗啟動前的run亦不能當已消耗完整suite minutes。

## 建議邊界

1. 現在維持Quality disabled_manually，完整collection、原斷言／skip狀態與實際DB／Storage測試留在開發環境；不把少跑案例或放寬閘門当節省。新增自動Quality runner minutes與artifacts為0；既有artifacts仍照原30日期限，沒有刪除。
2. 若日後明確恢復CI，可只對PR與main push跑全量4shards，保留manual dispatch。Feature branch push不重複跑第二輪；同一PR更新由一組完整4shards驗收。和當前PR+feature-push 8jobs相比，該更新可少約50%的重複全量工作，main merge驗證與部署workflow仍保留。PR synthetic merge／code tree差異必須記錄，不能把不同tree結果假裝同一版本。
3. 可把完全相同的syntax／OpenAPI／migration parse／dependency audit／fullRuntime移到一個獨立validation job，每次run只做一輪；Web matrix仍執行全部原IDs。每項成功／失敗仍是必要驗收，不能因shared gate失敗就隱藏Web完整結果；所有原始logs／runtimeJSON／collection／partition／JUnit與失敗screenshots需always保存。這部分省的是重複執行，不能以subset代替34-migration／Storage。
4. Artifact優先以取消重複event減少新增份數，保留30天及全部唯一結果。只對已逐檔hash核實為pinned程式碼重建副本的build/lib、依賴cache提出未来排除；原XML／full log／原始官方附件／HTTP失敗內容／唯一截图不可排除。現有artifact不變。不建議在原證據未另封存前縮短retention；若另授權未来30→14天，storage byte-days約少53%，不影響既有artifact到期日，但目前未執行這項選擇。

官方依據：
- Events／branch filters：https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
- Concurrency：https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency
- Artifact retention：https://docs.github.com/en/actions/tutorials/store-and-share-data

這些估計由現有workflow與單次完整M1 sample推出，不是已生效設定或每月價格預測。唯一已生效操作是Quality官方disable。
