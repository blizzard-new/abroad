# TKU 固定 SHA CI 續查驗收：4e6cabd

程式候選 `4e6cabd073e4792f94959545efeb4e323fefc3f5`，原分支 `data/tku-exchange-20261008`，[draft PR #2](https://github.com/blizzard-new/abroad/pull/2)。本證據分支以此候選為基礎，只新增此資料夾；沒有宣稱 artifact commit 本身另跑測試。原89217e1證據1159874b7a3d3f48299d18c810646f38396c6ad9完整保留。

實際 **1475 passed、24 failed、8 skipped**。原39失敗中修復15，仍有24失敗；新增失敗0。Runner exit 1，all_checks_passed=false；不能以main同失敗當作驗收通過。十步均執行，起訖同SHA且工作樹乾淨。主pytest包含所有頂層unit（含恢復wrapper）、七個E2E檔及CGU PDF node；其他E2E與Ollama不算通過。851個既有CGU/NTPU/NTU workflow雜湊無差異。

- [完整結果](acceptance-results.json)、[逐步guard／退出碼](run.json)、[JUnit](suite.xml)、[原39案例逐項診斷](failure-diagnostics.json)、[main基準](baseline-f6ad/suite.xml)
- [同方法原始HTTP修復前](privacy-before-raw.json)／[修復後](privacy-after-raw.json)、[原始比較](privacy-comparison.json)、[19案例原始邊界trace](privacy-boundary-http-trace.json)／[JUnit](privacy-boundary-regressions.xml)／[log](privacy-boundary-regressions.log)、[未解API](shared-contract-probe.json)。原始before重新在乾淨89217e1隔離checkout重現，不冒稱before是b455a18或正式資料。附capture-privacy-raw.py、capture-privacy-boundaries.py與回歸原碼。
- [原67缺口逐項續查](source-review/gap_triage.json)、[逐欄年度](source-review/completeness_matrix.json)、[全部來源連結查核](source-review/source-link-check.csv)
- [遠端推送與CI](remote-evidence.json)、[CI逐步jobs](ci-pr-jobs.json)、[CI四組完整摘要](ci-pr-complete-summary.json)、[第0組分段](ci-pr-shard-0-log-part-00.log)、[CLI截斷日誌](ci-pr.log)、[完整1757逐案例結果](ci-pr-complete-case-results.json)、[actionlint修復前後](ci-readonly/actionlint-before-after.txt)
- [共用整合差異](shared-integration-risks.json)、[CGU實際比較](cgu-acceptance-comparison.json)、[打包檢查](packaging-check.json)

128筆含4當期日語二甄校／7名、124旧期參考；9/30校內截止，0個可新申請。當期152欄核實89（58.6%）；四項有直接依據的映射已補正，63缺口仍保留為45個限定公開範圍未取得、18個矛盾／更正後適用性待確認；沒有把未查得新版改成官方尚未公告。13組來源矛盾仍未解。12新來源JSON為已核對及標註適用性的全文摘取；資傳頁訪客IP尾段在摘取時排除，sha256仍是原HTTP內容雜湊，不冒稱摘取文字與原HTTP bytes相同。

JLPT N1–N5與英語數值分開，保存與重载；未知年度／梯次不帶當期證據或借用資格。`/coverage`按母校來源計數，不升級部分資料狀態。合成隔離資料證明護照422／訪客不可見、刪帳後本名與作者關聯清除，6/6探測通過；自身POST ID移除不被當作原訪客ID洩漏證據。Supabase路由單元為模擬；另遠端CI有隔離DB runtime驗證，正式DB未讀寫。

私訊初送201重試422；衝突board_id/school_name請求仍201且board_id優先；跨校發文現行政策與舊測試／OpenAPI不一致；缺管理審查／發布API。這些都保留為阻礙，未擴權或加虛構路由。UI字面契約失敗沒有因挑選browser通過而豁免。遠端CI狀態以remote-evidence.json與原jobs／log為準；workflow語法修復不等於整個CI通過。原b455a18兩次CI45分鐘逾時保存於原artifact；本次4e6cabd按所有1757個收集案例分四組，0漏項／0重複／0新skip，完整終態及逐案例結果見remote-evidence.json、ci-pr-case-results.json與各job原日誌。正式runtime不變。CI改為逐案例即時結果與耗時、fail-fast=false、完整檔案分組；45分鐘／隔離DB20分鐘上限、權限／secrets／actions pins未改。若某組仍逾時或未完成，不能算整個suite完成；實際總數與完整性由CI逐案例結果判斷。

## 可下載目視證據

[browser](browser)包含主執行14個逐案例JSON與14張截圖、4個新SHA準備稿PDF和8頁render。截圖前明確等待遮罩消失；JLPT手機／桌面保存與重載納入本次主suite。另於browser-followup補同SHA捲到N1與截止查核欄位的局部畫面；額外2次focused案例與visual-followup.xml不加進主suite統計，附可重現capture-jlpt-followup.py。全為合成測試資料；準備稿不是官方表格。[official-source-pdfs](official-source-pdfs)另有5份核對PDF与7頁PNG，含2026參考行事曆，不能當作2027文件。

[historical-e476dd3](historical-e476dd3)保留前一個候選完整JUnit／guard／統計及報告分類錯誤；其中兩張JLPT原圖被載入遮罩擋住，另附當時的同SHA補拍，明確是e476dd3歷史證據，不加進4e6cabd統計。b455a18另有177檔原始證據完整保留於e33127d413cd83dc15173c3f18d4cd5bd55228d5，包含45分鐘逾時的GitHub註記及完整日誌。4e6cabd只再改善CI完整分組與兩個browser測試同步；所有src程式及資料與b455a18/e476dd3相同，見runtime-source-equivalence.json。


wheel新檔／附件／21,658,056bytes中文字型與OFL均已驗入包；wheel建置來源為e476dd3，逐檔比對1009個完整package來源與b455a18完全相同；未宣稱重建新wheel。138MB wheel不重複放入本ZIP。首次候選venv缺setuptools失敗保留於packaging-venv-environment-failure.log，使用既有system setuptools重試成功。wrapper只恢復唯一可還原的RPC原碼測試，未知舊pyc覆蓋不宣稱；uv只移除早已不在pyproject的pytesseract殘項。

[manifest.json](manifest.json)逐檔保存長度和SHA256。下載[acceptance-evidence.zip](acceptance-evidence.zip)後可直接目視PDF/PNG，或執行`python verify-evidence.py`；checksum通過不是驗收綠燈。ZIP雜湊見[archive-sha256.txt](archive-sha256.txt)。未merge main、未部署、未改正式資料或權限。

[CI逾時具體續查](ci-timeout-followup/README.md)保留b455a18原始7/3、main對照8/2、修正working tree9/1與新固定SHA的十案例原始timing/JUnit，各scope分開；working tree診斷不是精確SHA驗收。CI原45分鐘逾時不可轉稱手動取消或配額問題。本次遠端console逐案例結果可核對所有1757案例。完整遠端結果1675通過／66失敗／16跳過，第0組1470／51／16；不是本機結果或逾時。第0組16.9MB原log每2000行切分，可依ci-pr-complete-summary.json核雜湊及重組。四組collect-nodeids保留原ID，兩個合成userinfo網址參數被GitHub自動遮罩，逐案數量與排序已核對；runner暫存JUnit沒有上傳，未冒稱有遠端JUnit附件。
