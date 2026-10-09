# PR #2–#5 整合與發布證據（2026-10-09）

## 當前發布狀態

#5 final candidate **b33ad27ff13912780dfb94f91504dd11b1ef6a21**, tree **510235883bcd6b98b7eeb6e3cb66b1d318feeae8** 已完成 bounded release gate。main／Render 此文件建立時仍為 f6ad1b8；合併與實際部署結果另存 release-result.json，只有 status=live 加 HTTP／browser 驗證後才稱上架。#3/#4 因真 SQL board_forbidden 阻擋；#2 等原治理任務固定修復候選。沒有將 mergeable 當發布成功。

使用者先授權隔離候選；父端隨後轉達 12:49:55 與 13:00:44 UTC 的明確四 PR merge 授權及已告知 main→Render 自動部署，並指定本任務為唯一發布執行者。這涵蓋正常 code merge 與既有 auto deploy，不包含新正式 DB 變更。Quality 維持 disabled_manually。未變更部署設定、權限、保護、憑證或付費。

## 固定候選與原始結果

|項目|固定 SHA|實際結果|
|---|---|---|
|main clean collection|f6ad1b8cedc4dadb4d00c29eb3456a7a87856d59|1680 collected＋1 error：wrapper 依賴未追蹤 pyc；完整 pytest NOT RUN|
|#3 獨立 regression|5eadeb569ea0ae048e2c49450ee8c4012d24d630|472 passed／8 skipped／0 failed；8 skip 中含缺 xlrd|
|#3 XLS 補測|同上|安裝 repo optional requirement 後 1 passed；去重為473 passed／7原skip|
|#3 browser|同上|33 passed；四校實際 bundle、延遲切換、文件及來源顯示|
|#4 regression|eddd7af6e700e2d7685be95e3c96484a9fa378b1|520 passed／7 skipped／0 failed|
|#4 browser|同上|19 passed；含三校、保存及 Kyutech|
|#5 initial regression|b8833a6a6ffc8236276fa7870e4c1ff541c34117|130 passed／4 skipped／1 failed；北大 coverage 同錯誤已在 main 重現|
|#5 initial browser|同上|10 passed|
|#5 新 coverage 錯誤重現|1f57df2c225b042c519eda0deb9ce73bbf35bd35|1 failed；tuple 照片索引尚有 single-key caller|
|#5 final2 regression|b33ad27ff13912780dfb94f91504dd11b1ef6a21|169 passed／4既有skip／0 failed|
|#5 final2 browser|同上|19 passed／0 skipped／0 failed；390/1440、地球、照片、生活、三校切換、帳號條件保存|
|#5 final2 checks|同上|10 commands exit0：uv0.11.26 lock、OpenAPI、Python/JS、31 migrations parser、dependency audit、offline replay、clean、whitespace、wheel|
|論壇真SQL診斷|#3原HEAD＋main同31份migration中的原論壇subset|2 passed，成功重現 ccu/ncu 都 board_forbidden；不是產品通過|
|完整 Supabase runtime前置|main pinned image|FAILED: layer registration ENOSPC；migration/Storage full runtime NOT RUN|

每個 run 目录的 stdout.log、stderr.log、results.xml、metadata.json 保留原始 bytes。metadata 記 UTC 起迄、SHA/tree、git status、完整命令與 exit code。final2 三組起迄同 b33ad27 且 clean。較早 final-checks 的 pip-audit 因 home cache 唯讀失敗、wheel 產生未追蹤 build/，以及論壇冷下載60秒timeout均保留；調整為隔離可寫cache與先下載映像後另跑，未改寫原失敗。沒有改測試 skip 來造綠燈。

## #5 的界線與修正

- 最終266張具Commons授權／公有領域metadata；20張只有官網出處而缺重用授權，needs_review 且不展示。15新影像移出static package並由wheel檢查排除；5既有共用資產未改其他校。另2多校區 missing。原10/08快照與收據不改寫，授權overlay逐筆記hash。
- 269校級代表座標，19待核。不是保證錄取校區。
- 保存快照1627節錄全數可對上原文；其中秋田404頁5則導覽在final candidate排除，可展示124校／1622則。其餘學校仍保留缺口；9節錄來源收據時間有秒差或保留舊成功日期，未抬高為新查核。
- 生活年度、舊成本及交換生適用性仍以原文scope標明；282 pending／6 zero未改。
- E/V註記造成3所美國學校弱key碰撞已修：完整校名＋國家作生活與cache身分，288key不互相覆蓋。
- coverage image key、同母校destination範圍與NTPU既有coverage狀態修正；後兩hunks與已授權#3一致。
- CGU154／NTPU409／NTU288 workflow及原各校official_data逐檔byte parity。新增NTU student_life檔不算修改舊workflow。12張系統抽樣contact sheet已目視，沒有將抽樣聲稱成再次逐張人工看266張。

## 依賴、共用範圍與剩餘阻擋

本機完整diff：#2舊183 files、#3 2374、#4 **12421**（不是GitHub3000上限清單）、#5原301；共26 shared paths，見inventory/inventory.json。全部ref沒有AGENTS.md／SKILL.md／.agents files；已讀README與本機測試／部署指引。所用Supabase與Render skill僅指引本機驗證和已授權的既有服務發布。

可發布順序：#5 → **DB board compatibility gate** → #3 → #4 → #2修復後另驗。#5→#3的隔離merge候選 b6f0ce4f40f90754bbe9824788c13b2a8218dd74；唯一Git衝突在tests/test_school_photo_and_match.py，保留CCU fixture規則及新helper集合。该候選尚未做完整共同runtime，不可作main發布許可。#4／#2逐hunk共同整合尚未完成，六校完整回歸 NOT RUN。

#3/#4沒有migration，但API送出短ID ccu/ncu，正式基準函式只允許 cgu/ntpu/ntu 與 university: prefix。真PostgreSQL重現 new-school-forum-db-confirmed；提出 proposed-ccu-ncu-board-compatibility.sql 供父端協調，**只是證據分支的SQL提案，非supabase/migrations、未套正式DB**。此提案保留signature/owner/ACL/security/search_path/email門檻/receipt/鎖，只補兩個短ID校名配對。若未另授權正式DB升級，不得先merge這兩校。

#2固定舊5d48a01僅供診斷，未重做原任務的rollback-label／published-array修復。舊三migration：20261009040000_verified_email_school_community.sql、20261009060000_community_byline_aliases.sql、20261009080000_atomic_governance_commands.sql。前兩為函式替換／allowlist，第三替換治理RPC並新增command驗證及CAS/鎖，**不是單純新增table**。最後head到達須重核差異和相容性；舊60000亦缺CCU/NCU署名alias，需整合評估。

## 安全發布及回滾

1. #5不變31份migration、Render／workflow設定。正常merge觸發既有Render。逐次核deploy.commit.id=merge SHA、status=live、/health和三校dashboard以及手機／桌面關鍵頁，不把HTTP200當資料完整。
2. #3/#4先需父端協調並明確授權正式DB compatibility migration。先讀取正式migration history與目標函式definition/owner/ACL，確認備份／還原點，將提案正式化為唯一timestamp migration；舊app＋新DB、新app＋新DB及重播／負面案例先隔離驗證。只在精確前置狀態吻合後按版本套用並read back。Actions帳務不能當DB已套用證據。
3. DB gate通過後，#3與#4逐一更新base、逐hunk解衝突、回歸、正常push/merge；每支待Render live＋讀取驗收後再下一支。不可同時merge讓部署競跑。
4. #2需完整修復SHA、full collection／tests／governance安全／34+全migration含Storage runtime及DB前後相容證據。舊schema會fail closed，故正式DB先於需要新command的code；不依赖main push後異步db-push追上。
5. #5若失敗，停止後續merge，正常revert其merge commit（-m 1）觸發Render，核回滾deploy的commit/health；不改autoDeploy或force-push。#3/#4的兩校純allowlist可在程式回退時保留；若要復原DB function須用記錄的精確前版本forward migration，不盲目drop或回退整庫。#2舊RPC與治理資料／審批語意的downgrade須另證明，不假定git revert即DB rollback。
