# 現有查核成果交付快照（含第 49–52 輪補齊與 main 新增 6 校來源治理）

本分支基於 `main` 最新狀態（`10c95f0f`，已合併 PR #112 的 `a1e60b0a`），針對前次整理指出的最後一輪未套用來源（第 49–52 輪）、輔大舊保證金欄位不一致、輔大外部建置輸入缺口、臺科大 22 所大陸交換校一覽表、淡江日語一招簡章、成大接待校語檢與臺大 30 志願規劃工具容量一致性，以及 `main` 新增 6 校（彰師大、高師大、北醫、中山醫、中國醫、高醫）的來源證據與範本治理完成補齊。

## 本次包含

- **25 所原始母校與新增 3 筆自費方案（共 4,588 筆）**：
  - 延續第 1–48 輪母校／接待校欄位查核與更正。
  - **第 49 輪（輔仁大學接待校來源查核與保證金欄位統一）**：套用天普大學（Global Programs 接受 TOEIC L390/R390、TOEFL iBT 79／新制 4.0、IELTS 6.0、GPA 3.0，並明示與母校簡報第 30 頁泛稱之差異）、蒙特雷大學（UDEM 兩階段申請與英語 B2 要求，保留西語截斷待確認）、普福爾茨海姆大學（記錄官網 PHP 資安維護與 2026/2027 FactSheet PDF 雜湊，保留德語截斷待確認）、香港浸會大學（HKBU GPA 2.5、TOEFL iBT 79／IELTS 6.0 與 2025/26 宿舍整修停用，保留雙邊碩士名額待確認）；並將輔大 234 筆方案與母校單例檔（`exchange_info.json`、`scholarships.json`、`student_dashboard.json`）殘留的舊版「保證金 NT$10,000」及「返國後一個月內繳交 2,000 字心得」全面統一為待確認（共 472 個 row scopes、3 個單例檔、1,949 處欄位更新）。
  - **輔大自包含建置輸入**：將 5 份探索期 JSON（`label_40_parsed_rows.json`、`parsed_award_details.json`、`ror_resolved.json`、`quotas_115_1.json`、`quotas_115_2.json`）納入 `sources/fju/`，更新 `scripts/build_fju_catalog.py` 支援自動解析並串接 `apply_fju_host_review`。
  - **第 50 輪（成大與早稻田 WBS 後續來源套用）**：補齊成大 116-1 早稻田申請流程之「須具相關學科背景、不接受跨領域申請」限制；補入延世大學未來校區（Mirae Campus）2020/11/06 英語計畫合作名單查核紀錄（僅列臺科大與元培，未列成大，保留校區待確認）；為臺科大、臺大、政大之早稻田紀錄補入 Waseda Business School (`WBS`) 2026/07/10 院級合作名單來源證據（共 6 個 row scopes、9 處欄位更新）。
  - **第 52 輪（臺科大赴陸 22 校、淡江日語一招、成大接待校語檢與臺大 30 志願容量對齊）**：將臺科大 44 筆大陸合作校完整對照 `reviewed_1152_mainland_schools_20261021.pdf`（22 校 58 名）修正名額、院系與年級／應屆限制，並移除未列於表內之 22 所大陸姊妹校誤標名額；於淡江參考方案完整呈現 2027–2028 日語一招 25 校語檢與各系條件（含早稻田 N1／各系 GPA 附註）並將 `round42-followup-source-notes.json` 標為 `data_changed: true`；為成大維陶塔斯馬格努斯與俄斯特拉發技術大學補入接待端官方 `TOEIC 785` 語檢／Fact Sheet 證據；對齊臺大 30 志願與多校申請規劃工具（`PersonalApplicationPlanRequest`、`ApplicationPlanPreference`、`multi-plan.js` 及 OpenAPI 契約）容量上限（同時保留長庚 2 志願、中正 3 志願上限）。
- **`main` 新增 6 所母校（第 51 輪來源治理與範本撤除，共 938 筆方案）**：
  - 針對彰師大 (`ncue`, 150)、高師大 (`nknu`, 212)、北醫 (`tmu`, 201)、中山醫 (`csmu`, 64)、中國醫 (`cmu`, 127)、高醫 (`kmu`, 184) 全面套用與原 25 校一致的證據治理：
  - 為 938 筆 `partners.jsonl` 綁定 6 項核心欄位 `field_evidence`（324 筆當期開放標為 `verified_current`、614 筆歷年／合約名冊標為 `reference_only`）。
  - 將 938 筆 `destination_profiles.jsonl` 的區域預設生活費設為 `cost_evidence.status = "reference_only"`、`coverage_status = "official_partial"`，防止未經個校核實的區域預設金額在預算篩選 (`budget_fit`) 被誤判為 `within`。
  - 撤下 938 筆 `student_life.jsonl` 共 4,690 項建置器範本證據（移入 `reference_data` 保留追溯，並寫入 `reviewed_life_claims_round51.json` 防止跨校快取重升格）。
  - 撤下 190 筆 `student_experiences.jsonl` 未讀原文的 `full_text` 生成摘要（143 筆改為 `official_directory`、`metadata_only` 候選索引；47 筆甄選／雙聯／參訪紀錄改為 `official_program_record`），並將 `student-experience-digests.json` 的 `report_count` 重設為 `0`。
  - 各校 `verification_status.json` 與 `catalog-completeness.json` 明確記錄 `whole_partner_records_verified = 0`。

## 已有驗證

- 帳冊決策數：新增第 50 分檔（`review-decisions/part-00050.jsonl`，1,955 筆），全帳冊共 50 個分檔、131,723 筆欄位決策，對齊 4 套基準盤點（`baseline`、`derived-baseline`、`raw-catalog-baseline`、`special-catalog-baseline`）驗證 0 錯誤。
- 全 31 校執行時載入：5,526 筆目的地方案（原 25 校 4,588 筆 + `main` 6 校 938 筆），方案識別無碰撞。
- 第 49、50、51 輪套用函式重播均具冪等性（第二次執行變更數皆為 0），原值完整封存於 `reference_data`。
- 整合與回歸測試：原 25 校回歸測試、第 49–52 輪專屬測試（`test_fju_host_review.py`、`test_round50_followup_review.py`、`test_main6_source_review.py`、`test_round52_followup_review.py`）及新增 6 校整合測試全部通過。

## 明確未完成

- **完成全部欄位事實查核的整校數及整筆方案數仍為 0。** 自動測試與欄位證據分類不代表全部海外校外部事實已逐筆查完。
- 正式站資料庫比對及完整瀏覽器端對端視覺驗收尚未執行。
- 受外部登入牆（如輔大 M365 Factsheet、臺科大 Google Drive 短網址）或接待校網站維護（如普福爾茨海姆語言頁）阻擋的項目，均保留 `needs_confirmation`，不臆測或捏造數據。

## 閱讀入口

- [31 校已完成事項、14 所接待校原文範圍及已知缺漏摘要](DELIVERY-AND-GAPS.md)
- [逐合作方案缺漏與進度](partner-review-progress.csv)
- [另外新增的三筆方案](additional-partner-review-progress.csv)
- [整體查核說明與歷次發現](README.md)
- [第 48 輪查核摘要](round48-review-summary.md)
- [第 49 輪輔大接待校與保證金統一清單](round49-fju-host-and-cost-review.json)
- [第 50 輪成大與早稻田 WBS 追查清單](round50-ncku-waseda-followup-review.json)
- [第 51 輪 main 新增 6 校來源治理清單](round51-main6-provenance-review.json)
- [第 52 輪臺科大赴陸 22 校、淡江日語一招、成大接待校語檢與臺大 30 志願容量對齊清單](round52-ntust-tku-ncku-ntu-review.json)
- [機器可讀進度](review-progress.json)
