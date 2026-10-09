# TKU 3ccbf7c 實際驗證與遠端中斷證據

程式候選 `3ccbf7c3de75b47f2f93f7aa56e96143e2e48a38`，獨立分支 `data/tku-exchange-20261008`，[draft PR #2](https://github.com/blizzard-new/abroad/pull/2)。本分支只追加證據，沒有宣稱 artifact commit 另跑程式驗收。

本機固定 SHA 十步：1475 passed、24 failed、8 skipped；其他九步0，起訖乾淨且 commit 不變。19 隱私回歸、6/6探測、2 JLPT聚焦browser、4PDF及8render另有原始HTTP/JSONL/JUnit和guard；不可取代遠端完整suite。wheel重新從此候選建置，1009 package來源逐檔一致；138MB wheel不放入ZIP。建置產生untracked build目錄及首次copy路徑錯誤均保留真實錯誤與更正，沒有修改package來源或丟棄失败紀錄。

PR run37870196346、push37870191848均failure。兩次各收集1757 nodes，第0分片在812測試後 Progress長longrepr輸出遇到BlockingIOError而exit3；全分片合計實跑1032，725尚未實跑。PR 978 passed/39failed/15skipped+1internal error，push977/40/15+1internal error。不能把这些不完整結果稱為完整1757驗收。PR实际merge checkout d738f5434ff56ad559fbd2a9e85a8546bd31c9f5與3cc同git tree ad78d384e7b270f4765987aae9cf0dbe0cdb8725，完整原commit metadata另留。隔離Supabase runtime、資料後檢與原始artifact上傳成功，以原job metadata為準。

[remote/original-artifacts](remote/original-artifacts)保留原ZIP和完整解壓內容：8份原candidate JUnit、8份同job原main-control JUnit、pytest logs、collect-nodeids、partition、實際退出碼、瀏覽器/PDF（只有執行該案例的分片有）。原始byte完整保存，没有重建JUnit。CLI與Python預設User-Agent下载曾403，改瀏覽器User-Agent后成功下载且按原ZIP核對；沒有宣稱403是測試通過。全部4份原始JUnit實際含内部錯誤，未只擷取passing案例。

每次62個main控制使用固定f6ad runtime、原4e6測試、同一runner/job/interpreter/package/browser/Poppler；3passed/59failed。不是採用較舊不同環境的baseline截圖，也不是豁免候選失敗。控制確實運行且存實際pytest_exit1；shell0代表成功產出診斷，沒有宣稱baseline全綠。

只讀restore-probe對原3cc三案例實際1failed/2passed；程式沒有改，browserwrapper會影響時序，因此不能由兩次passing斷言工作區安全。working-tree-probes是先前有界診斷與main控制，scope另標，不加入精確SHA驗收統計。

資料與4e6相同：128 rows、4當期/7公告名額/124舊期參考，9/30校內截止、0個可新申請；89/152欄核實、63適用缺口、13矛盾；851 CGU/NTPU/NTU workflow hash不變。不能將舊資料、尚未查得新版或院系scope視為本期可申請。原三個歷史artifact保持完整且另有連結於summary.json。

[manifest.json](manifest.json)保留每檔bytes/SHA256；[acceptance-evidence.zip](acceptance-evidence.zip)是此資料夾可下載副本（不包含自身、manifest、checksum）。checksum通過不代表驗收通過。未merge、部署、正式DB或權限變更。
