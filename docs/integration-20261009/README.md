# PR #6 完整回歸最後驗證中：2026-10-09 17:05 UTC

最終候選 `9327cfe0cb836ad09818310c46ad7322555ef4bb`；[PR #6](https://github.com/blizzard-new/abroad/pull/6)仍為draft，尚未合併。完整產品回歸SHA是`f3e0b666`；最終只改一份測試的pipe讀取，產品、資料、SQL、依賴、runner及部署設定完全相同：[identity proof](memory-final-test-only-identity.json)。

暖快取長跑384GET／36選校／6NTU照片地球生活／3批八併發全部passed，峰值445.76MiB：[summary](memory-final-warm-soak-summary.json)。這是本機程序RSS/HWM，不是Render cgroup。最終f3的35migration／Storage／治理／舊Python相容性、wheel、lock、OpenAPI、JS、SQL也通過。完整2647案尚未全部完成；三筆本機ENOSPC導覽截圖失敗已在相同SHA上原案例全部補跑通過。原始失敗保留。

前一bedc完整2645案是2628P／3F／14原skip：兩個UI/日期原因已修正；第三個測試stderr緩衝問題已有獨立可重現證據及9327提交後3案通過。讀[memory-progress.md](memory-progress.md)與[execution-status.json](execution-status.json)看當前門檻。

---

# 發布穩定性阻擋：2026-10-09 15:59 UTC

四支PR與DB已合併／套用，Render merge SHA `1c715d21` 曾於15:46:11 live；六校6 HTTP、6 guest forum拒絕、12手機桌面切換passed。但其後台大照片/地球/生活回歸在15:54:55遭多個502，Render事件明確確認512Mi OOM kill，15:55:31自動恢復。**尚未完成穩定上線驗收。**

[OOM事件](pr2-render-oom-events.json)、[記憶體指標](pr2-render-memory-502-metrics.json)、[原失敗run](pr2-production-ntu-regression/metadata.json)。記憶體從約207MB持續上升到533MB，再隨重啟下降；不是單純放寬timeout可以解決。新隔離分支 `integration/six-school-memory-20261009` 正定位原因，未改付費/Render設定/Quality/憑證。下面保留較早發布紀錄。

# 六校整合發布驗收：2026-10-09 15:41 UTC

**四支授權PR皆已合併；最後Render建置及六校實站驗收仍在進行，尚未宣稱上線完成。**

|PR|驗收HEAD|main merge SHA|Render|
|---|---|---|---|
|#5|b33ad27ff13912780dfb94f91504dd11b1ef6a21|58a6b7cf09a36d1892a1ac14a71332f1e8747a33|dep-db4ethpbgiqc738r2iag；當時live及NTU/三校實站passed|
|#3|dc4d054c2746388c40bd256f4203ef066b60be03|b22220f811f91cd4b86e16da25da8e0684123d87|dep-db4f56rbc2fs73bo5ok0；當時live及四校實站passed|
|#4|4a28daaa682b7aa55e6bb0497a8a6cde315a967f|e5c6d5ceafcb2099d45b67ab47aa464f7f82fa86|dep-db4feg0ae00c73a276s0；當時live及5 HTTP/10 browser passed|
|#2|31234305f6ecd477ff8eb3915dd2d3d6f4141477|1c715d21d1fd23a87087b74bbb068f4efbe74aa1|dep-db4gm549v7es73an3su0；build_in_progress|

## 完整驗證

固定`0fdc6cfa6a4902fb83374a77025f45dffb071562`：**2641唯一案例，2627 passed／0 failed／14既有skipped**。468 browser為466P/2S，2173 nonbrowser為2161P/12S；collection、原log及JUnit完全對應，四片起訖SHA/tree與clean status一致。詳見[six-final-full-summary.json](six-final-full-summary.json)及各shard原檔。

最終HEAD`31234305`只比上述增加一份發布說明、三份SQL依實際version重命名；app src、tests、SQL bytes及migration執行順序完全相同，merge tree也與最終HEAD相同。[機器比對](six-release-identity-proof.json)。最終HEAD再次通過35 migration/2 PostgREST/真Storage完整runtime及cleanup，[原始结果](six-final-applied-version-runtime-result.json)。原pinned DB rootfs與runtime config保留，只有本機VFS單層封裝調整。

17組治理安全案例、74 RPC、31 audit；六校12跨校發文留言、12未驗證拒絕、40 alias vectors通過。原正式e5c6d5c的102個Python模組與原模型在獨立程序完成stage/雙審/publish/readback，12 HTTP200，新舊payload一致。原helper仍未授權service_role。uv lock、OpenAPI、JS/SQL、strict dependency audit、wheel通過；wheel2527檔排除15張無授權新照片並保留TKU字型OFL。

## 正式DB已完成

按序成功套用並逐份readback：`20261009153249_verified_email_school_community`、`20261009153347_community_byline_aliases`、`20261009153438_atomic_governance_commands`。函式source hash符合已驗證SQL，signature、owner、ACL、security、search_path及五函式角色存取均不變。内部capability marker恰1筆、公開payload0、receipt1。

[SQL實際版本mapping](production-tku-migration-mapping.json)、[第1份讀回](production-tku-01-readback.json)、[第2份讀回](production-tku-02-readback.json)、[第3份讀回](production-tku-03-readback.json)。原五個migration版本差異保持原狀，未repair或bulk db push。CCU/NCU compatibility早已先於PR3套用`20261009135343`。

Quality374368612持續disabled_manually，沒有為綠燈啟用Actions。原TKU quality.yml改動保留、整合者未修改該檔；Supabase deploy workflow、Render autoDeploy/main、branch protection、憑證及費用不變。main合併觸發的Supabase workflow failure另留原紀錄，不冒充DB部署成功；DB成功以工具回執及實際定義核對為準。

## 保留的失敗、未跑與資料界線

原完整d182為2599P/28F/14S，離線builder造成35個metadata差異的source-guard失敗保留；原28失敗修正後逐項passed，再完整跑固定0fdc。原b67 runtime403、ENOSPC、正式站初次timeout、audit唯讀快取及新增舊程式輔助驗證的模型名稱錯誤均保留，沒有覆寫成成功。大型原stdout/XML以無損gzip交付，[原始及壓縮SHA256](lossless-compression-manifest.json)。

14原skip：[清單](original-full-skips.json)，9 Phase C、4 Ollama未啟動、1 pytest opt-in Docker（完整runtime另已執行）。正式站只作guest讀取，不建立正式測試帳號或寫合成內容。

CGU154/NTPU409/NTU288完整model payload與原main f6ad canonical hash逐校相同。CCU55 legacy、NCU214 pending、TKU4 partial+124舊年參考不代表全校完整；missing/pending/zero分開。NTU266 licensed/20 needs_review/2 missing、269代表位置、1622生活節錄/124校保留來源年度；14地區出發提醒仍缺研究、API明確404。

回退：正常revert PR2 merge還原五校程式，保留相容DB與append-only audit；等待revert SHA live並重驗。不要在capability marker/新版client存在時盲目還原舊RPC，DB問題按備份作精確forward migration。詳見[release-plan.md](release-plan.md)。

最新機器狀態：[execution-status.json](execution-status.json)。歷史階段：[checkpoint-before-pr2-merge.md](checkpoint-before-pr2-merge.md)。全檔SHA256：[file-manifest.json](file-manifest.json)。
