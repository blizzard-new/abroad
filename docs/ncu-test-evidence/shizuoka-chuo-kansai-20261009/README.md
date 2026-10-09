# 固定候選來源／平台查驗：靜岡、日本中央、關西

資料71 partial／214，143項尚待逐欄人工整理，116全欄核准0。三校24個host階段／43筆條件仍需兩校確認；母校七件另列，沒有因錄取／住校解除116封鎖。此為本批查驗證據，整體資料驗收仍blocked，不能宣称完整214校或CI通過。

| 固定候選 | 單元／API | 共享／gate | 新三校browser | 界線 |
| --- | --- | --- | --- | --- |
| `672eb5899693f06b211afdf517c2f63c1ec5f0c9` | 315 pass | 193 pass＋2 skip／65 pass | 4 pass／2 fail | 測試搜尋第一項誤開關西國際；原URL與失敗PNG保留 |
| `16e95c3b9e73efdbf41686fcdac1fe6a61aa9fb1` | 315 pass | 193 pass＋2 skip／65 pass | 4 pass／2 fail | 已精確開關西；生活頁漏500000保證上限，文件／source已過，生活原斷言失敗 |
| `224284f1460a792daf0015a6ab4342d83968ab8f` | 25受影響三校API／source与生活 pass | 共享／gate沿用16原SHA證據，不重跑 | 6 pass，390／1440 | 房租deposit與債務保證上限已分列，保留原生活斷言／timeout |

三個候選起迄均同SHA且乾淨worktree，各自原始manifest／log／JUnit／browser事件与PNG完整分資料夾保存。224查驗2026-10-09 05:17:32.748239至05:20:12.383999 UTC，本批`necessary_local_tests_passed=true`，`data_acceptance_passed=false`、`acceptance_status=blocked`、`full_ci_equivalence=false`。它只包含表列本批檢查，不是重跑全部既有browser。

三候選OpenAPI、三JS、lock、diff及main f6ad1b8的851條既有CGU／NTPU／NTU同schema multiset語義比較均通過。224重驗851／OpenAPI，main runtime export沿用16已驗的未修改main，不冒稱又做新的main取件。315／193／65保持16版本，不改標成224新跑結果。

25個受影響測試涵蓋母校／host各自文件、研究所／住房／COE前後順序、年度／空名額／當期封鎖、學制與建議語言范围、日期與成本、原件SHA／查核日、未讀Excel、HTTP200首頁錯件／404、摘錄變更拒用。6 browser讀實際卡片／詳情／學生摘要、來源與閱讀缺口、初次件與生活價格；驗證完整school identity、390／1440無頁面橫向溢出及無pageerror。

224共18張原始viewport PNG與6筆事件；8張已實際view_image人工檢視，檔名与SHA在[actual-browser-images-viewed](actual-browser-images-viewed.json)。其他PNG不宣稱已人工看圖。raw `original-browser`與`browser`有相同檔案的保存副本，不把複製計成額外實際畫面。

预檢v1 5 pass／3 fail與v2 8 pass的原始log／XML另留：v1 Word路徑預期誤寫7月，靜岡協議差異与關西課本未取得未進學生摘要；v2先修這些，後續健康附件与生活保證上限又在固定候選修正，不覆寫原預檢。

[資料差異](data-scope-delta-224284f.json)確認與59209e6相比只有三校partner／workflow／生活profile改變，其餘211校逐筆相同，既有870筆host證據逐筆保持一致，追加51次取件。總921 host checks／115現存錯誤；Drive459、29全件閱讀／7視覺／1OCR仍維持既有範圍，不以取件與提取稱完整當期核准。51次原件URL／SHA／HTTP／閱讀與DOC提取重試在[來源manifest](../../../sources/ncu/2026-10-08/host-shizuoka-chuo-kansai-original-manifest-20261009.json)，4頁實際原圖在[來源圖片manifest](../../ncu-source-evidence/shizuoka-chuo-kansai-original-pages/manifest.json)。

GitHub原生Actions查詢包含push runs，避免connector只回PR觸發而漏掉失敗：16 Quality37886955794与224 Quality37887889161均failure／0 jobs，combined pending、0 statuses。各自原始runs／jobs／combined JSON保留。CI未驗收；共用quality workflow的修正仍依分工留TKU，本分支沒有改它。

Kyutech原e79的20案例19 pass／1 fail仍有效，後續一次3 pass不關閉根因。[有界診斷59209e6](../kyutech-bounded-diagnosis-20261009/README.md)有兩次有瑕疵實驗（模組未套instrument、cProfile互斥造成500）及離線三請求；沒有改原assertion或重跑更多Kyutech，沒有以新六個pass宣稱舊延遲修好。

[合併點](merge-points.json)記錄main f6ad1b8、CCU5eadeb5／15交集、TKU4133667／20交集。本批只NCU資料／測試／說明，沒有merge、部署、正式DB、credentials／security變更或對外聯絡。

[checksums](checksums.json)的179筆均驗證一致；README與checksums本身不作自我checksum。只有`candidate-672eb58/browser_next3_content.xml`與`candidate-16e95c3/browser_next3_content.xml`因原始失敗包含native trailing whitespace，保留原位元組且僅這兩檔從diff空白檢查排除；其他staged檔全通過，未改全域設定。
