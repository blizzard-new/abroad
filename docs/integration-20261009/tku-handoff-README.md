# TKU固定b67d79a的完整交接證據

產品候選固定 `b67d79aa3b6c30a9449801501256b64951f2c291`。本目錄只追加原始證據，不修改產品、不重跑測試、不merge或部署。既有純證據提交 `1343abda9d1f2c099947699096e3c86f0e1d42c0` 的內容維持不變。

- [最終驗收摘要](raw/final-b67d79a/final-review-summary.json)：完整1827案例，1813通過／0失敗／14原跳過；原b8完整1804／9／14保留，相同九案例另跑全通過。
- [完整案例逐筆結果](raw/final-b67d79a/full-case-results.json)、[完整四片結果](raw/final-b67d79a/full-suite-summary.json)、[原b8失敗](raw/predecessor-b8f5e07/original-full-failure-details.json)、[九案例重跑guard](raw/final-b67d79a/isolated-original-failures/guard.json)。每片原始log、XML、收集IDs及source guard在兩個raw目錄的shard-0至shard-3。
- [SQL17組／74RPC／31audit摘要](raw/final-b67d79a/SQL-readable-summary.json)、[完整實際SQL結果](raw/final-b67d79a/sql-diagnostic/result.json)、[原RPC005固定envelope](raw/final-b67d79a/original-envelope-fixed/result.json)、[原缺published精確重播](raw/final-b67d79a/missing-array-original-fixed/result.json)。原修前200／mutated及各次真正診斷失敗、driver、compose、完整六表快照均在raw/recovery及raw/final-b67d79a，沒有重標。
- [migration相容性](raw/final-b67d79a/migration-compatibility.json)、[來源byte/tree保存](raw/final-b67d79a/source-preservation.json)、[7項實際檢查](raw/final-b67d79a/checks-run.json)、[推送及遠端tree證明](raw/final-b67d79a/remote-push-readback-proof.json)。
- [完整映像空間模型](raw/recovery/complete-runtime-image-space-model.json)、[安全替代與阻擋](raw/recovery/space-blocker-and-safe-alternative.json)、[原完整runtime ENOSPC](raw/recovery/full-runtime-5d48a01-original.log)、[原固定5d runtime guard](raw/recovery/full-runtime-5d48a01-run.json)、[安全清理](raw/recovery/cleanup-result.json)。完整34-migration／Storage仍未驗證；空間模型約38.97GiB，規劃42GiB需owner核實daemon掛載／quota，未付費擴容或開新環境。
- [Quality停用證據](raw/recovery/quality-disable-proof.json)、[產品push後workflow回讀](raw/final-b67d79a/workflow-list-after-push.json)、[本次產品SHA Actions run=0](raw/final-b67d79a/actions-runs-for-pushed-SHA.json)。Quality仍disabled_manually；部署workflow、權限、憑證不變。

[manifest.json](manifest.json)映射每個原檔的source path到實際GitHub repository path，保存bytes、SHA256和git blob SHA1；原94檔全部逐byte確認後另補完整logs、driver、browser產物及空間模型。source path僅是來源識別，交付應讀repository path。所有raw原bytes仍可下載；大於480KB的原檔另提供[readable-chunks](readable-chunks)，每片低於500KB，依index逐offset可重組原檔。執行 `python verify.py` 可核對全部原檔及真實重組，不啟動產品測試。

只排除快取、isolated-data本機金鑰、bytecode與重复生成的舊readable chunks；[排除清單](excluded-files.json)不包含其內容。合成測試compose使用公開的runtime-only參數，沒有正式project URL/token或實際憑證。瀏覽器截圖／PDF及JSON屬合成測試，原檔保留。
