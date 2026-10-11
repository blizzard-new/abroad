# 六校隔離驗收證據

目前保存候選已正常推送：[dbc4afd64b4116e199c218d0d22e4223c9ff2db1](https://github.com/blizzard-new/abroad/commit/dbc4afd64b4116e199c218d0d22e4223c9ff2db1)，[Draft PR12](https://github.com/blizzard-new/abroad/pull/12)。**此版未完成驗收，未正式發布。**

本版含NCU `baf98c0df400ef96aa83fb587107eb22513c0b97`、CCU `1b9563c58e2fa83c3c2510a40b7ccdd126db9dd1`、NTU `dc9bbcddcf2cd2cf47ef7768e530c6aab6fa4401`及先前accepted TKU88bd。父指定下一組為NCU `a2df55b16f72455f7154d7afff44934fc8dbf99d`、CCU `52ed6370c63f053da445a9aff6eb9e2a3d2ad6c8`（data/test frozen `a4e425d456409f0113126d15347fb5d886e13f01`）、NTU `c7357f974faaec8e60ef19698d4d21633c322dc8`。目前先獨立審查，待已啟動測試結束後接入，不修改測試中的HEAD。

## 當前固定結果

- CCU第八批五個自動合併共用檔逐檔確認：完整incoming加上既有11→10題修正。獨立讀24欄及11支援原件，依原文澄清Oneonta轉學生住宿選擇條件與保險最多16日。兩轮JSON重建及再一輪136個JSON/JSONL/CSV全檔重建均一致，原55條CCU workflow不變。helper最初誤把作者evidence路徑寫成completion-evidence，scope assertion失敗；更正為實際completion-validation後嚴格逐檔範圍檢查通過，原失敗保留。
- dbc4契約、CGU154／NTPU409／NTU288 workflow位元組parity、來源交付、NCU完整payload一致性passed。新SHA沒有SQL／API／前端／dependency增量。
- dbc4完整2985案例仍在執行。分片2已失敗：10passed／8failed／126setup errors，起始錯誤為`Target crashed`，隨後`Page crashed`／browser關閉。其他分片仍在跑。環境接近磁碟／記憶體限制的唯讀快照已保存；沒有足夠證據宣稱已證明崩潰原因。所有原始failure/error保留。下一候選將降低同時執行分片數，原測試、assertions、wait與460MiB門檻不改。
- dbc4完整Supabase runtime **failed**：35份migration完成，Storage容器建立ENOSPC。隔離容器／volumes已清理，Docker仍4原image；不沿用舊版成功。dbc4 wheel、175步冷／暖尚未跑，隨下一固定資料組合重新驗收。
- 前版4a完整2970unique已對帳：2956passed、13skipped（9 Phase C／4Ollama unavailable）、1setup error、0notrun（所有collected案例都有結果，但setup error本體未執行）。相同4a案例獨立重跑1passed，原全套仍failed。4a wheel及全新安裝6671檔hash／六校smoke已passed；這不代表dbc4或下一版passed。[全套對帳](integration-next1-full-suite-summary.json)。

## 下一組獨立審查與未納入項

NTU c735已驗證1228原文版本／1227來源ID／42archive parts全部hash、611引文與頁码、舊59原件及前554版本不變。700既有observations逐物件不變，新增673合計1373；全部文字、scope、URL仍可在前10個summary點完整容納。這是資料層檢查，尚未代表新資料的組合browser／memory通過。原文脈絡的獨立抽查另記，不宣稱重讀所有作者501組全文。接待來源39缺口的蘭州差異與PR8擷取修補另核。PR9本批不修改該PR8測試；當前候選自己的修補只有cache變數及4個依赖函式加入，移除這兩處後與作者保存的修補前測試逐位元組相同，無刪除／放寬assertion。作者模擬after hash與本候選不同且未提供該after原檔，因此未聲稱兩者同一檔。

[TKU兩項精確照片阻擋](TKU-PHOTO-BLOCKERS.md)：4f142仍將Sunderland換成UWE Frenchay；UAEMEX CC BY4.0署名／授權人鏈待核。父已17:41轉交作者，不再缺泛稱對照。兩照片都不在目前接受的候選中。[固定前後比較](tku-fifth-blockers-not-in-current-candidate.json)。可換可核來源或保留missing/pending，沒有判定匿名署名必然侵權，也沒有替作者重做修復。

## 容量與可重現性

所有原始失敗保留。已完成暫存可重建目錄及四個Oct9 clean歷史worktree退役前逐tracked blob核對，commit／branch與還原指令保留；當前候選及測試環境未移除。兩個Oct9大型raw log只是lossless gzip，解壓原始SHA一致。九個歷史wheel以精確ZIP位元組range去重封存，逐份重建SHA全等原件，另外實際還原一整包並通過CRC；完整4a基底wheel仍保留。可用`harnesses/restore_archived_wheel.py`配`historical-wheel-lossless-archive.json`中的recipe離線還原，不能把已封存的舊wheel路徑誤認為仍有plain wheel。沒有Docker prune或修改daemon、服務、憑證、付費。

## 發布邊界

資料不是全校當期完整。CCU第八批仍604missing欄；NTU仍生活16缺／獨立host39缺／3圖3點限制，當期完整未宣告。新輸入的限制須按原來源與適用對象驗收，不以空值本身拒絕誠實的限制表達。

[160完整本地驗收檢查點](checkpoint160-complete-668c8b4.md)僅證明160。未merge main、未正式DB write或部署，未改Quality停用、Render、branch protection、憑證或付費。相對main59 migration增量0；[發布／回滾順序](RELEASE-PLAN.md)仍適用。main會立即觸發Render，Actions帳務受阻不能假設DB同步。正式DB現況／備份／成功deploy須由父另外核對。

[原始run索引](run-index.json)、[證據hash清單](artifact-manifest.json)。保存點或mergeable不代表上線成功。
