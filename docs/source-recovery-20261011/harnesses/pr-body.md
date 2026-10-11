六校資料增量目前固定在 `4a011fab8ecdb98e4bca2ca2368ec28eaf194b78`，已正常推送保存。此版含NCU baf98c0d、CCU258ce9bb、NTUdc9bbcdd；維持Draft，尚未完成本版全部驗收，未正式發布。

NCU432unit/23browser、CCU349unit/24browser在各自固定整合SHA通過。本SHA契約、原CGU154/NTPU409/NTU288 workflow位元組parity、來源交付、NCU完整payload、6671檔wheel及checkout外全新安裝/六校smoke通過。完整2970案例仍在執行；分片2有一項瀏覽器context setup error，相同SHA未改案例復跑1passed，原始失敗保留、根因未定。Storage runtime建立容器ENOSPC失敗，冷暖175步尚未跑；不能沿用160成功宣稱本版通過。

[固定原始證據與狀態](https://github.com/blizzard-new/abroad/blob/8b7570acca35fc10154e52e8621b9829bc9a815b/docs/source-recovery-20261011/README.md)。[TKU兩項照片的確切檔案、ID、SHA、缺項與驗收條件](https://github.com/blizzard-new/abroad/blob/8b7570acca35fc10154e52e8621b9829bc9a815b/docs/source-recovery-20261011/TKU-PHOTO-BLOCKERS.md)：第五批4f142ea3仍有Sunderland錯配UWE照片及UAEMEX署名/授權人链待核，未納入。CCU新固定1b9563c5待本輪已啟動測試結束後依父指示整合。

資料仍含missing/pending/歷年參考/官方TBC/明示零，沒有宣稱全校當期完整。本候選相對main59 migration增量0；未merge main、正式DB write或部署，未改Quality停用、Render自動部署、branch protection、憑證或付費。main會立即觸發Render，Actions帳務受阻不能假定DB同步；正式發布由父依固定證據及DB/備份現況協調。
