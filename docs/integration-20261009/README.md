# 六校整合與發布驗收（持續更新，2026-10-09 14:31 UTC）

## 已完成的正式發布

|PR|實際合併前 HEAD|main merge SHA|Render deploy|結果|
|---|---|---|---|---|
|#5|b33ad27ff13912780dfb94f91504dd11b1ef6a21|58a6b7cf09a36d1892a1ac14a71332f1e8747a33|dep-db4ethpbgiqc738r2iag|live；三校HTTP、NTU手機桌面地球／照片／生活 passed|
|#3|dc4d054c2746388c40bd256f4203ef066b60be03|b22220f811f91cd4b86e16da25da8e0684123d87|dep-db4f56rbc2fs73bo5ok0|live；四校HTTP和手機passed，桌面初次timeout保留，獨立重跑四校passed|
|#4|4a28daaa682b7aa55e6bb0497a8a6cde315a967f|e5c6d5ceafcb2099d45b67ab47aa464f7f82fa86|dep-db4feg0ae00c73a276s0|live；五校HTTP及390/1440切換10項passed|

所有部署逐次等前一版本live及實站驗收後才合併下一支。Render autoDeploy、main分支及Quality停用狀態未變，未新增憑證／付費／調整protection。實站只使用guest讀取，未建立正式測試帳號或內容。

## 正式 DB 狀態

只已套用 `20261009135343_ccu_ncu_school_board_compatibility`：在既有論壇函式補CCU/NCU短ID allowlist。精確函式MD5由 `b81840819d91b81f3557964da088ea3f` 到 `b032beac1990513b576f388328720999`；owner/ACL/security/search_path不變。先隔離真PostgreSQL驗證、再套用、再read back。rollback SQL有精確版本guard，不能覆蓋後續TKU版本。未bulk db push、未修寫既有migration歷史。

TKU三個migrations尚未套正式DB。Actions帳務阻擋不能當作DB已同步；後續會按已驗證順序先DB、後程式。

## PR #2 六校候選

上游固定 `b67d79aa3b6c30a9449801501256b64951f2c291`，其獨立證據位於 artifacts/tku-governance-m2 的固定 `c572cbc02d2e7c1ed5fa25721dd7cde5022444b2`。原340檔、94指定原檔、12chunks已驗證；原1827 unique案例1813P/0F/14skip不冒充六校結果。

完整runtime確認b67真實403：service_role的invoker治理RPC呼叫owner-only fingerprint helper。整合修復改用原有內建SQL運算，helper ACL維持拒絕；317向量與原canonical helper逐一等價。所有原operation-label／missing published陣列修復保留。

固定 `d1827d75f801921e49c67e29ecedecc85083ec7b`（已推integration/six-schools-20261009）：
- 全35 migration＋2 PostgREST＋真Storage完整runtime已passed；新建排序與實際發布排序各跑一次（前者f163，後者d182，SQL bytes相同）。RLS37表、browser grants0、治理CAS／雙審／回滾／部分失敗、Storage孤兒清理、帳號清理均通過；六校verified-email跨校12寫入、12未驗證拒絕、40alias vectors全部通過。
- 原pinned Supabase 17.6.1.136 digest完全相同的rootfs及runtime config，僅為Docker vfs限制重新封裝single layer。沒有更換Postgres版本、停用runtime項目或擴權。見pinned-image-flat-proof.json及兩次原始runtime logs。
- wheel 2527項成功建置；15張未授權新照片確實排除，TKU字体與OFL授權完整入包。
- 完整2641案例（2173 nonbrowser＋468 browser）四片正在執行；不能報成passed。已保留原始空年級回歸、舊四校數量、生活來源舊文案、NCU待確認舊文案失敗。
- 後繼隔離 `fe1cec66` 已修空年級request語意、六校grade控制測試；nonbrowser全量執行中。原d182 tree在整個測試期間不改寫。

## 資料界線與回退

仍保留CGU154／NTPU409／NTU288既有workflow；CCU55 legacy、NCU214 pending、TKU4有限流程不聲稱全校完整。NTU266 licensed photo／20 needs_review／2 missing；269代表位置；1622可展示生活節錄來自124校，舊年與scope不升格。其餘missing／pending／zero分別保留。

程式回退以正常revert該merge，等待Render對應commit live並重新驗收。PR2新DB保留舊RPC signature/owner/ACL與舊分支，允許回到五校程式；建議回退程式、保留相容DB及append-only治理紀錄。不要在capability marker存在時盲目還原舊RPC，DB問題用已備份definition核對後的forward migration修復。

原失敗、ENOSPC、初次timeout與較早階段未完成項目保留於 [歷史checkpoint](checkpoint-before-five-school-release.md)，那是當時狀態，以上述目前狀態為準。各run保留命令、UTC、SHA/tree、start/end guard、原log/XML；沒有修改skip條件來造綠燈。
