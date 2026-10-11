# 六校隔離驗收證據

最新已完成並推送的應用檢查點：[`8e65c47d1d42bd0d065ff53c8d6572d0be994bf2`](https://github.com/blizzard-new/abroad/commit/8e65c47d1d42bd0d065ff53c8d6572d0be994bf2)，[Draft PR12](https://github.com/blizzard-new/abroad/pull/12)。[完整檢查點報告](checkpoint-8e65c47d.md)：非E2E **2293 passed／12 skipped**，browser **91 passed**，另隔離PostgreSQL **2 passed**；冷暖162步 **456.80／457.52MiB**，460門檻通過。每項原始命令、起訖SHA／tree／工作樹、時間及exit code均保留，不把重疊run相加。

包含NTU第三批ed747907、CCU cf4d86f、NCU第三批06bfdfa、TKU第一批f4819dab、PR8身份修正与CGU來源恢復。[前一0d檢查點](checkpoint-0d3d671e.md)保留同資料修正前556.27→暖454.56／冷458.49MiB的完整162步比較。

## 正在驗收的下一固定資料批次

NCU第四輪358a72e7及TKU第二批88bd0053已只讀核對來源後整合為59aa522a，尚未推為驗收通過；新增資料的175步冷470.74／暖463.55MiB **均失敗**。原始失敗結果已保存，記憶體修復及重跑仍在進行，不能把8e的結果套用到這輪。

- [NCU固定輸入](ncu-fourth-fixed-input-audit.json)：646來源、237段落閱讀、45全文原生PDF、2全文圖文PDF、319成功未讀候選；214項quota null／agreement_only、workflow pending。[47份公開PDF原始SHA](ncu-fourth-live-pdf-hashes.json)全部獨立GET相符，串流取hash，未保留原件副本。
- [TKU來源與圖片](tku-second-fixed-input-audit.json)：264圖片全量hash／解碼／校別列對應，260點含255代表點及5校園點；18分片3616成員，原2576不變。[264張視覺檢查](tku-second-contact-visual-review.json)。[授權一致性](tku-second-license-consistency.json)：207封存Commons metadata，54固定基線素材；[其餘3份原始授權頁](tku-second-three-manual-license-checks.json)另核對。54基線匹配不冒稱全部重新下載上游。
- 代表點、照片拍攝校區與當期分配校區分開。TKU仍缺23照片／27座標、283名額未知；NTU仍939欄待讀，16校無任一生活evidence與38校缺獨立host生活來源是不同分母；NCU當期完整核准仍0。全部資料尚未完成。

## 正式邊界與未執行

沒有merge main、正式DB變更或部署，沒有改Quality停用、Render autoDeploy、branch protection、憑證或付費。相對main59各固定增量migration均0；[前一安全發布計畫](RELEASE-PLAN.md)與[8e migration核對](ntu3-migration-audit.json)。main更新會觸發Render，Actions帳務受阻不能假定DB同步；父對話須核對實際production SHA、DB已套版本及備份，再決定單一已驗收候選的發布／回滾順序。

尚未執行正式部署驗收、正式DB、全部repo E2E、全新wheel隔離安裝。本機完整四容器runtime正在準備，已跑的單一PostgreSQL RPC案例不代替完整runtime。已驗證wheel的舊二進位為節省空間已移除，逐檔hash清單、原始buildlog仍保留；最新候選將重建。

[所有原始run](run-index.json)、[檔案hash](artifact-manifest.json)、[工具](harnesses/)。只封存公開來源、測試截圖及計量，runtime帳號／session／私人文件與憑證未納入。
