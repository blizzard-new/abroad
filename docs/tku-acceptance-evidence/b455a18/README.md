# TKU 固定 SHA 續查驗收：b455a18

程式候選 `b455a18ce12ebf679f12c4f8ef4295f6546b2c60`，原分支 `data/tku-exchange-20261008`，[draft PR #2](https://github.com/blizzard-new/abroad/pull/2)。本證據分支以此候選為基礎，只新增此資料夾；沒有宣稱 artifact commit 本身另跑測試。原89217e1證據1159874b7a3d3f48299d18c810646f38396c6ad9完整保留。

實際 **1475 passed、24 failed、8 skipped**。原39失敗中修復15，仍有24失敗；新增失敗0。Runner exit 1，all_checks_passed=false；不能以main同失敗當作驗收通過。十步均執行，起訖同SHA且工作樹乾淨。主pytest包含所有頂層unit（含恢復wrapper）、七個E2E檔及CGU PDF node；其他E2E與Ollama不算通過。851個既有CGU/NTPU/NTU workflow雜湊無差異。

- [完整結果](acceptance-results.json)、[逐步guard／退出碼](run.json)、[JUnit](suite.xml)、[原39案例逐項診斷](failure-diagnostics.json)、[main基準](baseline-f6ad/suite.xml)
- [同方法原始HTTP修復前](privacy-before-raw.json)／[修復後](privacy-after-raw.json)、[原始比較](privacy-comparison.json)、[19案例原始邊界trace](privacy-boundary-http-trace.json)／[JUnit](privacy-boundary-regressions.xml)／[log](privacy-boundary-regressions.log)、[未解API](shared-contract-probe.json)。原始before重新在乾淨89217e1隔離checkout重現，不冒稱before是b455a18或正式資料。附capture-privacy-raw.py、capture-privacy-boundaries.py與回歸原碼。
- [原67缺口逐項續查](source-review/gap_triage.json)、[逐欄年度](source-review/completeness_matrix.json)、[全部來源連結查核](source-review/source-link-check.csv)
- [遠端推送與CI](remote-evidence.json)、[CI逐步jobs](ci-pr-jobs.json)、[CI原日誌](ci-pr.log)、[GitHub逾時原始註記](ci-pr-annotations.json)、[actionlint修復前後](ci-readonly/actionlint-before-after.txt)
- [共用整合差異](shared-integration-risks.json)、[CGU實際比較](cgu-acceptance-comparison.json)、[打包檢查](packaging-check.json)

128筆含4當期日語二甄校／7名、124旧期參考；9/30校內截止，0個可新申請。當期152欄核實89（58.6%）；四項有直接依據的映射已補正，63缺口仍保留為45個限定公開範圍未取得、18個矛盾／更正後適用性待確認；沒有把未查得新版改成官方尚未公告。13組來源矛盾仍未解。12新來源JSON為已核對及標註適用性的全文摘取；資傳頁訪客IP尾段在摘取時排除，sha256仍是原HTTP內容雜湊，不冒稱摘取文字與原HTTP bytes相同。

JLPT N1–N5與英語數值分開，保存與重载；未知年度／梯次不帶當期證據或借用資格。`/coverage`按母校來源計數，不升級部分資料狀態。合成隔離資料證明護照422／訪客不可見、刪帳後本名與作者關聯清除，6/6探測通過；自身POST ID移除不被當作原訪客ID洩漏證據。Supabase路由單元為模擬；另遠端CI有隔離DB runtime驗證，正式DB未讀寫。

私訊初送201重試422；衝突board_id/school_name請求仍201且board_id優先；跨校發文現行政策與舊測試／OpenAPI不一致；缺管理審查／發布API。這些都保留為阻礙，未擴權或加虛構路由。UI字面契約失敗沒有因挑選browser通過而豁免。遠端CI狀態以remote-evidence.json與原jobs／log為準；workflow語法修復不等於整個CI通過。固定b455a18的PR與push兩次遠端CI皆於既有45分鐘上限後cancelled；GitHub原始註記直接確認逾時。Web日誌最後只顯示12%進度、已有F但未輸出案例名稱或完整統計，不能歸為本地24項或宣稱完整suite通過；資料未變動後檢查被跳過。安裝／uv lock、語法、frozen OpenAPI、31份migration解析、依賴稽核與隔離Supabase runtime皆實際通過。既有timeout／權限／secrets／actions pins未改。

## 可下載目視證據

[browser](browser)包含主執行14個逐案例JSON與14張截圖、4個新SHA準備稿PDF和8頁render。截圖前明確等待遮罩消失；JLPT手機／桌面保存與重載納入本次主suite。另於browser-followup補同SHA捲到N1與截止查核欄位的局部畫面；額外2次focused案例與visual-followup.xml不加進主suite統計，附可重現capture-jlpt-followup.py。全為合成測試資料；準備稿不是官方表格。[official-source-pdfs](official-source-pdfs)另有5份核對PDF与7頁PNG，含2026參考行事曆，不能當作2027文件。

[historical-e476dd3](historical-e476dd3)保留前一個候選完整JUnit／guard／統計及報告分類錯誤；其中兩張JLPT原圖被載入遮罩擋住，另附當時的同SHA補拍，明確是e476dd3歷史證據，不加進b455a18統計。新候選只補診斷分類與截圖等待兩行，所有src程式及資料與e476dd3相同。


wheel新檔／附件／21,658,056bytes中文字型與OFL均已驗入包；wheel建置來源為e476dd3，逐檔比對1009個完整package來源與b455a18完全相同；未宣稱重建新wheel。138MB wheel不重複放入本ZIP。首次候選venv缺setuptools失敗保留於packaging-venv-environment-failure.log，使用既有system setuptools重試成功。wrapper只恢復唯一可還原的RPC原碼測試，未知舊pyc覆蓋不宣稱；uv只移除早已不在pyproject的pytesseract殘項。

[manifest.json](manifest.json)逐檔保存長度和SHA256。下載[acceptance-evidence.zip](acceptance-evidence.zip)後可直接目視PDF/PNG，或執行`python verify-evidence.py`；checksum通過不是驗收綠燈。ZIP雜湊見[archive-sha256.txt](archive-sha256.txt)。未merge main、未部署、未改正式資料或權限。
