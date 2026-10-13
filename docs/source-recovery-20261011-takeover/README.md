# PR12 接手恢復點（尚未整體驗收）

唯一整合寫入者於 2026-10-11 從可驗證遠端恢復；沒有取得或延用失敗 session 的未提交工作樹。

- PR12 remote head：`5e7114182093fa77203ee946a4f86a88d3b10345`，分支 `integration/six-school-recovery-20261011`；Draft／main 未合併。
- [原 checkpoint eb903552](https://github.com/blizzard-new/abroad/blob/eb90355259e2f8b85f46dd526382a1a2c56a3180/docs/source-recovery-20261011/README.md)：6686 檔、1213294439 bytes 全部 manifest hash 通過。原始四 shard log／XML 在 original-final7；完整24案 traceback 已另存。初跑仍是3073 passed／24 failed／13 skipped，不能稱通過。
- 目前修復：未知名額保持「待核實」、TKU262張與264座標、隔離JS載入activeHomeSchool、配對script版本、Turku到校規則、關西精確查核日期。沒有刪除 assertion／延長 wait／改動460MiB門檻。
- 修復後52單元案例通過；這是 dirty-tree focused 檢查，不是最終SHA驗收。NTU23757a06與NCUa1d6b7aa固定來源byte／引用稽核重跑通過；無回應記錄保留missing/null，不要求body hash。
- 四校更新尚待接入；完整suite、六校手機桌面、wheel fresh install、Supabase本機runtime、175步cold/warm須於最後候選重跑。
- 原生Docker VFS拉取Postgres因ENOSPC失敗；後續沿用既有exact-rootfs單層包裝工具，保留原錯誤。不涉及正式DB、部署、Quality啟用、帳務或新增憑證。

第二恢復點：NTU23757a06、NCUa1d6b7aa已接入；NCU更新7筆既有紀錄與5筆新增，保留圖爾庫/明治修正及原條件；NCU/NTU兩次離線rebuild逐檔hash一致。14個來源測試檔assert/wait AST保留，僅已核定未知名額標籤改為待核實。所有550筆共用座標內容不變（生成器排序）；仍待完整驗收及NCU最後凍結。新NTU截圖輸出改tmp_path/browser。恢復點的本機测试產生runtime資料已排除，不屬交付資料。
