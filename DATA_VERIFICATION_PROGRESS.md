# Uniway 資料驗證執行進度與後續待查核追蹤清單（DATA_VERIFICATION_PROGRESS）

> **記錄時間**：`2026-10-15`  
> **首輪盤點查核覆蓋率**：**100.0%（`1,237 / 1,237` 筆平台資料均已完成第一輪官方來源比對；惟其中 `591` 筆（`47.8%`）仍屬「待人工確認」，不得將全平台資料視為已 100% 最終驗收定案）**

---

## 一、執行進度總覽

| 執行階段 | 任務內容 | 狀態 | 首輪執行進度 | 產出成果與後續狀態說明 |
|---|---|---|---|---|
| **第一階段** | GitHub Repository 與自架伺服器（`C:\uniway\app` + PostgreSQL `uniway-db-1`）全面分析與資料盤點 | 已完成 | `100%` | [`DATA_SOURCE_INVENTORY.md`](file:///C:/Users/Administrator/.gemini/antigravity/scratch/abroad-pr/DATA_SOURCE_INVENTORY.md) |
| **第二階段** | 全平台 6 校（`cgu`, `ntpu`, `ntu`, `ncu`, `ccu`, `tku`）及維護子系統共 1,237 筆資料執行首輪官方來源交叉驗證 | 首輪已完成（`591` 筆待後續追蹤確認） | `100%`（首輪比對） | [`DATA_VERIFICATION_REPORT.md`](file:///C:/Users/Administrator/.gemini/antigravity/scratch/abroad-pr/DATA_VERIFICATION_REPORT.md) |
| **第三階段** | 針對已確認之資料不一致問題建立獨立修正 Pull Requests（含官方證據、Git Diff、自動化測試與安全 SQL Migration） | 已建立待審 | `100%` | **PR [#29](https://github.com/blizzard-new/abroad/pull/29)、[#30](https://github.com/blizzard-new/abroad/pull/30)、[#31](https://github.com/blizzard-new/abroad/pull/31)、[#32](https://github.com/blizzard-new/abroad/pull/32)、[#33](https://github.com/blizzard-new/abroad/pull/33)**（並保留 **[#24](https://github.com/blizzard-new/abroad/pull/24)**、**[#28](https://github.com/blizzard-new/abroad/pull/28)** 補充證據） |
| **第四階段** | 產生逐筆獨立查核紀錄（12 欄位標準格式） | 已完成 | `100%` | [`DATA_VERIFICATION_DETAILS.csv`](file:///C:/Users/Administrator/.gemini/antigravity/scratch/abroad-pr/DATA_VERIFICATION_DETAILS.csv)（1,237 筆紀錄） |
| **第五階段** | 統計驗證完成度、錯誤分布與覆蓋率 | 已完成 | `100%` | [`DATA_CORRECTION_TRACKER.md`](file:///C:/Users/Administrator/.gemini/antigravity/scratch/abroad-pr/DATA_CORRECTION_TRACKER.md) |
| **第六階段** | 透過獨立報告 PR 提交 5 份稽核文件 | 已完成 | `100%` | 本檔案及同分支報告 PR（[#34](https://github.com/blizzard-new/abroad/pull/34)） |

---

## 二、標記為「待人工確認（`needs_confirmation`）」之 591 筆項目分類與後續追蹤計畫

遵循任務規範：**「如果證據不足、官方公告互相衝突或無法判斷適用年度，請將該問題標記為『待人工確認』，不要自行猜測或提出無依據的修正。」**  
目前標記為「待人工確認」之 **591 筆紀錄**均已完成首輪官方網頁查證，其待確認原因與後續查核觸發條件如下：

### 1. 台灣母校國際事務處「當期名額或新學期簡章尚未公布」項目（共 544 筆）

| 學校 | 筆數 | 目前官方狀態與證據 | 後續追蹤與重新查核時點 |
|---|---:|---|---|
| **國立臺灣大學 (`ntu`)** | `261` 校 | 臺大國合處 `https://oia.ntu.edu.tw/outgoing/school.list` 截至 `2026-10-15` 已公布 20 校確定名額與 7 校 0 名額，其餘 **261 校**於官網表格仍顯示 **「尚未確定」**（臺大 116-1 線上報名將於 `2026/11/02` 開放，國合處正分批更新名額）。 | 建議於 `2026-10-16` 至 `2026-11-02` 報名開放前，每日透過 `school.list` 追蹤新公布之姊妹校名額。 |
| **淡江大學 (`tku`)** | `283` 校 | 淡江國際處 `https://oieie.tku.edu.tw/` 截至 `2026-10-15` 僅公告 **116 學年度赴日交換二次甄選（4 校）**；英語組、歐語組與大陸組之 116 學年度甄選簡章與名額表尚未發布，目前平台保留 **124 校** 115 學年度簡章參考與 **159 校**締約姊妹校名錄。 | 待淡江國際處發布 116 學年度英語組/大陸組甄選簡章時，重新比對當期開放學校與名額。 |

### 2. 非當期開放之歷史締約參考與未刊載名額項目（共 40 筆 `待人工確認` + 中正 49 筆 `reference_only`）

| 學校 | 筆數 | 目前官方狀態與證據 | 後續追蹤與重新查核時點 |
|---|---:|---|---|
| **國立臺北大學 (`ntpu`)** | `37` 校 (`reference_115`) | 該 37 校列於臺北大學 115 學年度交換名單，惟未出現於 116 學年度英（133 校）/日（16 校）/中（21 校）三語組甄選一覽表，平台已明確標記為 `agreement_only (115 參考)`。 | 待臺北大學 116 學年度第 2 次甄選（預計 `2027-02-25` 截止前）確認是否重新開缺。 |
| **國立中正大學 (`ccu`)** | `3` 校 (`not_published`) + `49` 校 (`reference_only`) | 中正國合處 2027 春季班開放 52 校；另有 **3 校**於國合處表格未刊載名額（列為 `待人工確認`），以及 49 校為僅於秋季班開放或當期未開缺之締約校。中正國合處截至 `2026-10-15` 尚未發布 2027 秋季班（116-1）簡章。 | 待中正國合處於 2026 年底 / 2027 年初公告 116 學年度秋季班簡章時重新核對。 |

### 3. 國立中央大學 116-1 姐妹校列表「名額欄空白」追蹤事項（涵蓋於 PR #32 之 215 筆）

- 中央大學國合處雖於 `2026/10/13` 發布 `https://oia.ncu.edu.tw/var/file/26/1026/img/272/116exchangeschoollist-1013.pdf`（已於 **PR #32** 完整整合 215 筆學校名單、語言門檻與備註），但該份官方 PDF 之 **「名額」欄位目前全數留白**。
- **後續待辦**：於 `2026/11/10` 申請說明會及 `2026/11/16` 線上申請開放前，持續監測中央國合處是否發布填入確切名額數字之更新版 PDF。

### 4. 平台設計與欄位語意待人工裁決項目（共 7 筆紀錄）

1. **`CGU-002`（長庚大學 77 筆已發布工作流之 Step 3–6 時程，對應 `RULE-CGU-WORKFLOWS-STEP3-6`）**：
   - `src/exchange_info/official_data/cgu/application_workflows.jsonl` 中 77 筆已發布工作流將 Step 3–6（提名、外校申請、行前、返國抵免）之 `deadline_at` 統一設為校內截止日 `2025-12-20T17:00:00+08:00`。建議由產品負責人確認是否統一改為 `deadline_status="window_or_tbd"` 或依各外校 Fact Sheet 批次更新。
2. **`CGU-004`、`NTPU-007`、`CCU-001`（首頁學校卡片 `partner_count_hint` 顯示語意，對應 `UNIV-CGU-PROFILE`、`UNIV-NTPU-PROFILE`、`UNIV-CCU-PROFILE`）**：
   - 目前 `university_registry.py` 中，臺大（`288`）、中央（`215`）、淡江（`287`）之 `partner_count_hint` 代表「目錄總校數」，而長庚（`75` vs 總數 `77`）、北大（`169` vs 總數 `206`）、中正（`52` vs 總數 `104`）則填寫「當期校級開放校數」。建議人工確認首頁卡片是否維持「當期開放數」或統一改為「目錄總校數」。
3. **各校 `partner_research.jsonl` 之 `verification_status="needs_review"` 欄位（對應 NTPU、NCU、TKU 等外校單頁簽核狀態）**：
   - 依 `tests/test_ntpu_bundled_data.py:108` 與 `scripts/build_ncu_catalog.py:384` 之自動化測試契約，未完成外校單頁人工簽核前須維持 `needs_review` 以避免前端誤標為「外校官網當期已人工簽核」。

---

## 三、PR 審查與正式環境部署注意事項（供專案維護者使用）

- [ ] **注意事項 1（維護後台審核警示）**：在 [PR #33](https://github.com/blizzard-new/abroad/pull/33) 合併部署前，`routes.py` 會在特定情況下於本地 `MaintenanceStore` 產生展示用名額/期限變更並標記為 `SOURCE_CHANGE`（「官方來源更新」）。目前僅確認程式有此風險，正式站尚未受影響；**管理員於後台若看到無原始官方公告支持的變更，請勿點擊「核准發布」**。
- [ ] **步驟 1**：依序審查本次建立之 5 個資料修正 PR：
  - [ ] [PR #29](https://github.com/blizzard-new/abroad/pull/29)（長庚 `cgu`：排除 TEEP 來臺計畫與更新雷恩商學院參考連結）
  - [ ] [PR #30](https://github.com/blizzard-new/abroad/pull/30)（北大 `ntpu`：補齊中文組 21 校名額、清理 22 校誤吸校名、修正英語組 9 校名額/期間與簡章連結）
  - [ ] [PR #31](https://github.com/blizzard-new/abroad/pull/31)（臺大 `ntu`：整合 116-1 最新 20 校名額、女王大學 0 名額、夏威夷大學希羅分校正名與管院獎學金）
  - [ ] [PR #32](https://github.com/blizzard-new/abroad/pull/32)（中央 `ncu`：整合 2026/10/13 公告之 116-1 姐妹校列表、系統升級公告與說明會公告）
  - [ ] [PR #33](https://github.com/blizzard-new/abroad/pull/33)（維護子系統 `maintenance`：修正六校 Shadow Store 匯入完整性、排除預設展示用臺大截止日變更集並新增防護性 DB 清理 Migration）
- [ ] **步驟 2**：保留既有 [PR #24](https://github.com/blizzard-new/abroad/pull/24)（含 `reviewed-source-bodies-2026-10-14.zip` 與細目頁補充證據）與 [PR #28](https://github.com/blizzard-new/abroad/pull/28)（含 `docs/ntu-official-update-20261015/` 與筑波大學 `#107` 補充證據）供交叉審查，**請勿直接關閉**。
- [ ] **步驟 3**：審查本報告 PR（[#34](https://github.com/blizzard-new/abroad/pull/34)），並持續依第二節計畫追蹤 `591` 筆「待人工確認」項目。
- [ ] **步驟 4**：於自架伺服器（`C:\uniway\app`）執行資料庫備份後，套用 `supabase/migrations/20261015130000_cleanup_synthetic_maintenance_demo_data.sql` 並重建 `uniway-app-1` 容器。
