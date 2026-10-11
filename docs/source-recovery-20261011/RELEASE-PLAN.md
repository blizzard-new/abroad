# 隔離候選的發布順序與回滾計畫

本計畫只供父對話審核，沒有執行正式發布。此任務不 merge main、不寫 production DB、不部署，也不變更 Quality 停用、Render 自動部署、branch protection、憑證或付費。最新驗收狀態以同目錄 README 與每個 run 的固定 SHA／原始結果為準；本計畫不能替代通過紀錄。

## 固定輸入與依賴

本輪起點 main `59a20f27fcee00fb597abc79e75ec11778317422`。PR8共用地球識別與CGU來源恢復／記憶體修復為基底；最新已推送候選 `7a7c7e3560527ce08ca225c0930397772a8b79aa` 包含 NTU PR9 `c7357f974faaec8e60ef19698d4d21633c322dc8`、CCU PR10 `52ed6370c63f053da445a9aff6eb9e2a3d2ad6c8`、NCU PR11 `a2df55b16f72455f7154d7afff44934fc8dbf99d`、TKU PR13 `93cbd9dfee3af95f9ecc89cceb1ccd0e100778af`。逐hunk順序 CCU e16381c → NCU d0c84c5 → NTU 7e0c29e → TKU ca194735。

共用面包括 api.py 照片scope／coverage／座標、school_content.py、university_locations.py、共享照片／位置、app.js選校／來源／名額、index.html載入次序、discovery-core.js、multi-plan.js、package-data、OpenAPI、分母與來源交付。NCU保留候選優先與explicit operator override、圖爾庫舊文件及簽章、明治五個月；CCU保留三項原文修正；TKU保留lazy identifier及operator override，同時接入NICS資料。Git無衝突不代表語意正確。

TKU兩拒用照片已移至 `sources/tku/withdrawn-campus-assets/`，不在public static或Python package source。保留研究原件不等允許公開部署；發布前必須驗 direct URL404、六校cache/fallback無復活、最終wheel無路徑／內容hash。完整候選現在驗收中，任何較早SHA綠燈不能代替 7a7c7e35。

歷史160aeacd是上一資料批次完整驗收點（2919 unique，2906pass13skip，完整runtime、wheel、175冷暖<460MiB）；4a011fab批次2970unique為2956pass13skip1setup error，另一次單案重跑pass不替代全套；dbc4afd6批次2985unique為2803pass43fail126setup error13skip且Storage ENOSPC。完整原始結果均保留。

## 原 PR2–5 migrations

只讀狀態已確認原 PR2–5 在此次續作之前由協調流程合併；本任務没有執行 main merge。下表列相對原始 main `f6ad1b8` 的必要項目，完整 fixed heads 在 `original-pr-status-readonly.json`。

| PR | migration | 相容性／發布要求 |
|---|---|---|
| #5 | 無 | 本地照片／地球／生活來源資產；仍需檢查照片授權、機構身分、原文年度與其他校回歸。 |
| #3、#4 | `20261009135343_ccu_ncu_school_board_compatibility.sql`（共用，同一檔只套用一次） | 擴充 CCU／NCU 校名與論壇相容；先核對正式 DB 是否已有該版本及函式定義，再發布依賴新校別的程式。 |
| #2 | 上述共用檔，以及 `20261009153249_verified_email_school_community.sql` | 保留既有 verified-email 跨校寫入 gate，補 TKU 對映並限制 verified-school/department 署名只能使用伺服器核驗身分。不是以選校冒充學生核驗；不能為回滾前端撤回限制。 |
| #2 | `20261009153347_community_byline_aliases.sql` | 署名與 canonical alias 相容；需和程式 registry／preview 一致，拒絕自填／空白／不支援署名。 |
| #2 | `20261009153438_atomic_governance_commands.sql` | 原子治理指令、競爭與 replay／rollback 驗證；依賴新 RPC 的程式必須在正式 DB 定義就緒後才發布。回滾程式需選仍相容且含安全修復的版本。 |

本次 PR8／9／10／11／13 的固定資料增量相對 main59，migration 新增或修改皆為 **0**；35份 migration 的內容雜湊另有機讀清單。本地完整 Supabase runtime 會實際套用35份並驗證 Postgres、兩個 PostgREST instance、Storage file backend、RLS／grant、治理審核／發布／回滾、跨校 verified-email、帳號刪除清理；每次結果只證明該本地固定 SHA，不代表 production 已同步。

## 安全發布順序

1. 保持 Draft，先完成本地完整驗收：全部 collected tests 分組聯集無遺漏／重複、六校手機桌面／帳號保存／校別切換／文件條件、原 CGU154／NTPU409／NTU288 workflow 位元組 parity、來源與授權、真實 wheel 安裝、完整本地 Supabase runtime，以及同一175步冷暖負載的460 MiB門檻。保留所有失敗、取消、skip及未執行項；不能拿重疊測試次數相加冒充唯一案例数。
2. 父對話依固定證據決定有限資料是否符合此次發布範圍。CCU／NCU／TKU／NTU 未取得、歷年參考、待確認、官方明示尚未公告與零名額保留區分；來源HTTP200、照片或座標增加不等於當期流程完成。
3. 正式改動前，只讀核對 main、Render 實際成功 deploy SHA／服務健康、production migration history 與必要函式定義、備份與可回復點。不要假定 main 等於 production。若無已授權讀取工具，回報具體缺少哪個讀取，不能新增憑證。
4. Render `srv-db26bgjbc2fs73fdsmhg` 已由父對話查得 `branch=main, autoDeploy=yes, trigger=commit`，所以每次 main 更新都是潛在立即部署。Actions 帳務受阻；main 的 Supabase workflow 只在 migrations 路徑變更時觸發，不能把程式 push 視為 DB 已完成。Quality374368612 繼續 `disabled_manually`。
5. 如 production 已有 main59 所需35份定義，此資料候選沒有新 DB 變更需要執行。如缺少既有 migration，先停止程式發布；由父對話審核精確待套用 SQL、備份及舊程式相容性，再另外授權正式 DB 操作並验证成功。不要重跑已套用 migration 或在隔離任務中直接 db push。
6. 父對話選定已驗收的單一整合結果後，再安排 main 更新，避免依序合併讓 Render 發布未驗收中間狀態。正式操作后須等 Render 的實際結果，核對部署 SHA／health／核心 smoke／錯誤／記憶體；不能用任務完成、PR mergeable、合併或 CI 綠燈當作上線成功。

## 回滾

- 事先記錄正式部署前的安全穩定 SHA、DB migration/function 狀態與備份位置。只在父對話授權的正式步驟中，以正常 revert commit 或明確 Render rollback 回到相容版本；不 force-push main、不更改 branch protection／autoDeploy。
- 此資料候選無 DB schema 增量，程式回復不需要 down migration、不刪正式資料。若另行套用 additive SQL，先保留相容 schema 與資料；不得退回可繞過 verified-email 或治理完整性檢查的舊函式。若只有修復前程式可選，先回報不能安全回滾的具體依賴，由父對話決定前向修復。
- CGU 只有兩個官方來源完整成功才原子替換本地快照；HTTP／解析／空內容／寫入任一失敗保留完整舊版本，沒有有效快照則明示不可用。舊年度資料不自動升格；回退不含此保護的程式須列為功能影響。
- 治理回滾需保留原子交易、operation label／published 完整性、CAS、一致 replay 及 audit；失敗必須零部分寫入。論壇仍要求 verified-email，六校 canonical alias 對齊。這些安全性不能為了回到舊畫面而解除。

## 尚未執行的正式步驟

本隔離任務沒有執行 production DB migration/history/backup 的最終現況驗收、production DB write、main merge 或 production deploy；所有本地通過仍需父對話按上述順序協調正式發布。需要額外批准時，必須精確列出「讀哪個正式狀態／套哪些 SQL／更新哪個 main SHA／部署或回滾哪個版本」，不能用籠統的任務授權擴充範圍。

## 本次續作保存點

7a7c7e35已推送Draft PR12，四校最終固定輸入全數為祖先。完整35SQL／真Storage本地runtime、contracts、來源交付、wheel逐檔hash與隔離fresh install已通過；撤回兩圖在wheel及六校靜態URL驗證不公開。ca194舊套件因tracked截圖輸出中止（118觀察passed、2967未完成），全部原始結果保留；7a7只修4個NCU測試模組的輸出位置，test function／wait／assert不變。175步冷暖与此SHA完整3085套件尚待完成，以README及逐run記錄更新。正式發布邊界不變。
