# 六校隔離驗收證據

目前固定且已正常推送的隔離候選：[160aeacd15521d63df6a5624bd12821cc5d26cea](https://github.com/blizzard-new/abroad/commit/160aeacd15521d63df6a5624bd12821cc5d26cea)，tree `fb517db5d7dbfec18ca160e54f3a3622d8893635`，[Draft PR12](https://github.com/blizzard-new/abroad/pull/12)。**仍在驗收，尚未宣告可發布**。此檢查點 supersedes 前次README的「未推／全量尚未執行」狀態；[原檢查點原文](checkpoint-before160-full-16541847.md)保留歷史。

## 160aeacd 固定結果

- **完整收集2,919 unique cases：2,906 passed、13 skipped、0 failed、0 notrun**。[逐案例對帳](integration160-full-suite-summary.json)核對四分片collection、JUnit聯集與clean起訖SHA，沒有遺漏／重複；9項既有Phase C、4項缺Ollama模型保持skip。`integration160-full-shard-0..3`保留stdout/stderr、XML及分母。兩項本機PostgreSQL opt-in案例實際執行，不是略過。
- [完整本機Supabase runtime](integration160-runtime-summary.json) **passed**：35 migrations、37 RLS表、0 browser grants、真實Storage API、兩個PostgREST；六校各6貼文／留言、12次未驗證信箱拒絕、40 alias、治理74 RPC／31 audit／17檢查、六種晚期失敗0部分寫入、CAS／replay／帳號刪除／清理均通過。原始成功run `integration160-full-supabase-runtime-r2/`；初次Storage啟動ENOSPC失敗完整保留。
- `integration160-wheel-build-r2`、`integration160-installed-wheel`、`integration160-delivery`、`integration160-ncu-parity`及`next-ccu-sixth-contracts` **passed**。實際wheel與隔離安裝6,579檔逐hash相同，checkout外六校smoke及CGU雙來源77筆通過；SHA256 `2af961b4f031bda5f8a54b90cf92b52e1fb9f364302f716626f6b8d3706973a7`，940,658,817 bytes。原CGU154／NTPU409／NTU288 workflow bytes不變，35 SQL相對main59不變。
- **175步冷暖記憶體尚未通過完整验收**。第一次冷run114樣本後截圖30秒逾時；第二次104樣本後桌面NTU→CCU切校90秒逾時。原始腳本、460MiB門檻及等待未放寬；[精確樣本／峰值](checkpoint-160aeacd-full.json)。第三次冷run只加失敗觀察器，記錄網路、狀態及截圖，原負載程式SHA固定；暖run尚未執行。部分樣本不能當完整通過。

容量處理只針對本任務擁有的工具、歷史證據及產物。10,007份同byte二進位檔核hash後共用inode，內容與原路徑保留；搬移中斷後均恢復原路徑。所有wheel與原始證據保留，沒有prune Docker或改系統／部署設定；機讀收據為`historical-evidence-deduplication.json`及`owned-...json`。

## 下一輪固定輸入

- **NCU PR11 baf98c0df400ef96aa83fb587107eb22513c0b97**：[來源bytes audit](ncu-fifth-fixed-input-audit.json)、[獨立原件語意／照片／校區審核](ncu-fifth-independent-source-review.json)。200圖全decode、193舊圖與署名原樣、7新圖實視；5項CC原metadata及兩種非CC原作者grant／條款／歷史實讀，7具名座標數值溯源。KTU 2021／2025-26／2026-27與Meiji2027分年；9頁明治指南、9頁KTU圖式factsheet及健康／證照圖均實視，四DOCX原XML逐段。整合時修正明治「約五月」→「約五個月」，保留Turku舊完整明細及operator override；NCU明確hold規則只留一套。台北10/12 00:10官方仍為116簡章＋115舊校表；名額未核不得變零／open。此輸入尚未合入160。
- **TKU PR13 1619ba890e3dc282bb26f92ebeeeece375e9ffe8**：[固定照片阻擋核對](tku-fourth-photo-blocker-check.json)。manifest與563fb932完全相同：tku-sister-65 Sunderland仍錯配UWE Frenchay；tku-sister-52 CC BY4作者仍Unknown author。未接受這批照片，已回報父端，不代作者重做。第四批renderer／來源年度增量待獨立整合驗證。
- **CCU PR10 258ce9bbb38081792658f9720bdb457a5344b2bb**：已接收為下一固定輸入；160仍含獨立複核的6bd批次及10題醫療修正，新37優先URL批次尚未算整合通過。
- **NTU PR9 dc9bbcddcf2cd2cf47ef7768e530c6aab6fa4401**：先前51未匯入問題已有固定解答；已fetch並閱讀NTU專用摘要分組hunk，下一輪須核700則、19封存分件與全欄可見性。作者的2185單元及browser不作本組合驗收證據。

以上都不是全校當期完整。有限資料、歷年參考、pending、missing、明示未公告與零名額必須分開。

## 歷史失敗與發布邊界

3129候選完整結果2874 passed／4 failed／13 skipped及175步／runtime成功保留，四失敗的修正已在160全套驗證。初始8e已接受較小資料版本的報告也保留，不沿用到新批次。針對測試345/40等有重疊，不能與全套相加冒充唯一案例數。

本任務未merge main、未寫正式DB、未部署，未改Quality停用、Render autoDeploy、branch protection、憑證或付費。[安全發布及回滾計畫](RELEASE-PLAN.md)。main更新立即觸發Render，Actions帳務受阻，不能假定DB同步；父對話須按固定證據協調正式步驟。完成任務／mergeable不等於上線成功。

[原始run索引](run-index.json)、[全部證據hash](artifact-manifest.json)。只封存公開來源、合成測試輸出／截圖及計量，不封存runtime帳號、session、私人文件或憑證。
