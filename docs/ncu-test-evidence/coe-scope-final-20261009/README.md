# 東北COE、來源日期與閱讀範圍修正的固定SHA證據

實作固定於`e79e0ba50cd247284f8a61b86f6fb5ff4c9a6409`，乾淨checkout `/tmp/abroad-ncu-coe-scope-final`起迄同SHA且clean。2026-10-09 03:34:32 UTC開始、03:47:40 UTC完成。本機整組仍未通過；補測不能覆蓋原失敗。

| 檢查 | 實際結果 | 原始證據 |
| --- | --- | --- |
| NCU資料／API／年度／文件／來源與新修正 | 307 passed | candidate-e79e0ba/ncu_unit.log、.xml |
| CGU／NTPU／NTU與共用回歸 | 193 passed、2 skipped | candidate-e79e0ba/shared_regression.log、.xml |
| 既有gate | 65 passed | candidate-e79e0ba/existing_gate_failures.log、.xml |
| OpenAPI、三JS、lock、候選diff | exit 0 | candidate-e79e0ba對應原始log |
| main851流程同schema／multiset比較 | 0差異；CGU154、NTPU409、NTU288 | candidate-e79e0ba/workflow_parity.log與manifest |
| 來源／文件／生活browser | **19 passed／1 failed，452.53秒** | candidate-e79e0ba/browser_source_scope.log、.xml；20筆事件、57張原始PNG、1張failure PNG |
| 一次有界補測 | 原九州工業1440與東北390／1440共3 passed；東北另4張實際畫面 | bounded-coe-kyutech-e79e0ba/manifest.json、browser.log、.xml與visual |
| CI | Quality37880006012 failure／0 jobs；Supabase113657273870 skipped；combined pending | ci-e79e0ba原始API JSON |

[原manifest](candidate-e79e0ba/manifest.json)保留`necessary_local_tests_passed=false`、`data_acceptance_passed=false`、`acceptance_status=blocked`。失敗為九州工業1440桌面在原5秒內等不到「校規初次三類」流程內容；事件顯示application-workflow request20755.39ms、response headers28418.81ms（約7.663秒）、HTTP200，destination-profile也同時結束。這是已觀察的HTTP延遲，不是其唯一根因已證實；沒有pageerror或requestfailed可據此推定其他結論。只做一次原案例補測，其通過不能把整組19／1改為全通過，不再無限重試或增加timeout。

本次20個案例含新增三校六個、既有關西國際／駒澤／東北六個、新潟兩個、九州工業兩個及北海道四個。東北COE四類、JASSO完整禁用、護照再次上傳／Proceeding替代條件，以及先前六個57／83頁閱讀範圍回歸案例均通過；舊95的14／6仍在[原始失敗證據](../next3-68-20261009/README.md)。前一2ce完整62browser通過及舊3b55／1、9bf52／4也各自保留，不把它們改標新SHA或宣稱旧GPA5秒失敗根因關閉。

補測與視覺capture使用同一e79乾淨checkout，原測試斷言與timeout未改。`visual-390.json`及`visual-1440.json`保存實際COE文字、展開學生摘要文字及PNG SHA；四張圖均實際檢視。另看TCU失敗來源網址手機、富山生活桌面與福井初次流程手機共三張，[人工檢視紀錄](visual-inspection.json)總7張；没有稱57張原畫面皆人工看過。兩項未提交時來源日期／ZIP及COE API預檢在preview保留，不稱固定SHA結果。

原始JSON、log、JUnit、事件與執行script未清洗；較大的JSON以確定性gzip保留原bytes。`checksum-manifest.json`逐檔列原始／存檔SHA，圖像ZIP列每張PNG SHA。原trace ZIP可能帶隔離測試session header，仍留/tmp；公開事件不含headers或response body。原始失败log與JUnit的尾端空白只豁免`candidate-e79e0ba/browser_source_scope.log`和`candidate-e79e0ba/browser_source_scope.xml`兩個精確路徑，其餘照常diff-check，不改全域ignore／attributes。

資料仍68／214 partial、146項待逐欄整理、116 full核准0；870筆保存的host取件／112失敗，Drive459取得／29明確人工全文（含原生或視覺）／7視覺／1OCR。引用原來源日期與四個ZIP member不等於取得當期接收包。最新main f6ad1b8、CCU5eadeb5交集15、TKU4133667交集20在[合併點](merge-points.json)列明；未merge、部署、正式DB操作、credentials／security更動或聯絡學校。
