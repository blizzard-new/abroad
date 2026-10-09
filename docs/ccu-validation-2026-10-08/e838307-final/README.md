# e838307 最終固定 SHA 原始验收證據

唯一受測程式 commit：`e8383073552a89afb5ef548493da5be5cd2f8167`。本目錄是其後證據專用 commit 所存的原始結果；並未為後續證據 commit 執行這套測試。不能把證據 commit 的 HEAD 當成受測程式 SHA。

原執行指令：`.venv/bin/python scripts/validate_ccu_candidate.py --output /workspace/ccu-artifacts-20261008/final-e838307`。工具整體exit1，因既有NTPU failure，並非全套green或可上線。

- 原始回歸JUnit／log：445案例＝437passed／7skipped／1 NTPU failure，394.98s。
- 原始瀏覽器JUnit為兩個獨立server组之合併，37＋57＝94passed，0fail/error/skip；group wall分别471.96／571.98s，合併JUnit time是相加，不能當單一wall。
- `browser-case-ids.txt`與`browser-case-identity-proof.json`對應原始94案例，4個独立production-bundle四校驗收無API／state mocks；其餘舊e2e fixture替換CGU partner list，已在selection聲明。
- `final-validation-summary.json`是原gate輸出；`boundary-evidence.json`由當時已成功執行的嚴格起訖assertions與原summary解讀。起訖HEAD都是e838307且porcelain為空；當時沒有另外記錄起訖git stdout檔，本目錄不偽造額外的歷史執行。實際受測gate原始程式及SHA256亦附。
- 6 builders、1160檔確定性重建、46 main data、77CGU published hash、API110 paths／required、wheel與研究用XLS版本證據分開列檔。
- Jena外部DOC實點TLS失敗仍保留，不由本地瀏覽器套件通過推論外部下載通過；資料完整度false，CIfailure／0jobs，跨分支隔離整合未跑。

`file-manifest.json`核對本目錄每份證據bytes。wheel binary與大型臨時server資料未提交；已提交wheel檔名、SHA256及逐byte驗證結果。沒有merge／部署／更改帳務或權限。
