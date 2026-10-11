# 六校隔離驗收證據

目前隔離候選已正常推送：[4a011fab8ecdb98e4bca2ca2368ec28eaf194b78](https://github.com/blizzard-new/abroad/commit/4a011fab8ecdb98e4bca2ca2368ec28eaf194b78)，[Draft PR12](https://github.com/blizzard-new/abroad/pull/12)。**目前為未完成驗收的保存點，未正式發布。** 環境斷線通知後已實際讀回clean git/status、SHA及執行進程，不以inProgress當恢復證據。

本候選含固定NCU `baf98c0df400ef96aa83fb587107eb22513c0b97`、CCU `258ce9bbb38081792658f9720bdb457a5344b2bb`、NTU `dc9bbcddcf2cd2cf47ef7768e530c6aab6fa4401`。新固定CCU `1b9563c58e2fa83c3c2510a40b7ccdd126db9dd1`已獨立核對，依父指示待本輪固定測試結束後接入。TKU `4f142ea36e69338d2956b4ea5d3d37a9f4116e52`未納入。

## 已完成與仍在執行

- NCU整合單元432 passed；照片／KTU／Meiji／其他校回歸23 browser passed。前次8 failed/15 passed因測試仍預期「待公告」而實際已核實語意為「待核實」，只改該測試literal，原失敗保留。3d97單元與345b瀏覽器為各自固定SHA，不混稱同SHA全套。
- CCU第七批整合SHA46227：349 unit passed、24 browser passed，6處衝突逐hunk核對只涉及既有11→10題修正；派生檔重建位元組相同。
- 本SHA契約、CGU154／NTPU409／NTU288 workflow位元組parity、來源交付、NCU完整payload一致性passed。Wheel建置及checkout外全新安裝6671檔逐hash核對、六校smoke與CGU雙來源77筆passed；wheel SHA256 `682c304eaa6926b56a8ab675f601755b907b7a7d4601686d6640002c446e45a4`。
- 完整2970 unique collected cases仍在執行。已結束分片2有一項setup error：`Browser.new_context: Response has been disposed`；該次案例本體未執行；相同SHA未修改案例獨立復跑1 passed，根因未定。不可宣稱全套通過。
- 本SHA完整Supabase runtime **failed**：35份migration套用後Storage容器建立ENOSPC。原始stdout/stderr保留、隔離資源已清理；不能沿用160成功當本版成功。冷暖175步尚未執行；最終候選仍須通過完整runtime與原460MiB門檻。

## TKU 精確阻擋交接

[兩項照片的固定檔案／ID／SHA／缺失證據／驗收條件](TKU-PHOTO-BLOCKERS.md)，[第五批機讀比對](tku-fifth-photo-blocker-check.json)。Sunderland錯配UWE Frenchay；UAEMEX CC BY4.0的署名／授權人鏈待核。可換成可核來源或退missing/pending，不能以數量264代替授權及機構驗收。沒有判定匿名照片必然侵權，沒有替作者重做修復。

## 資料與發布邊界

NCU7新圖、7具名位置與KTU／Meiji原件已獨立複核；明治「約五月」更正為「約五個月」，Turku已核明細與10個仍未解除的hold保留。CCU第七批618接待空欄、第八批604空欄；NTU700說明均保留來源與scope並可在前10點完整顯示，267新增文字逐項讀、重要來源另全文／版面複核；沒有宣稱101新來源都已全文重讀。均不是全校當期完整。

[160完整本地驗收檢查點](checkpoint160-complete-668c8b4.md)及全部歷史失敗保留。容量處理只共用經hash相同的歷史檔／已封存證據，或退役已完成且有固定來源、全檔hash與測試紀錄的可重建暫存目錄；所有wheel與原始測試／來源證據保留，未prune Docker或改服務設定。

本任務未merge main、未正式DB write／部署，未改Quality停用、Render、branch protection、憑證或付費。相對main59 migration增量0；[安全發布／回滾計畫](RELEASE-PLAN.md)中的順序與授權界線仍適用。正式main會觸發Render，Actions帳務受阻不可假設DB同步。

[原始run索引](run-index.json)、[證據檔案hash](artifact-manifest.json)。本頁的保存點不能當作上線成功。
