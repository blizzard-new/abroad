# 71校凍結候選：指定修正例外

基準資料 SHA：224284f1460a792daf0015a6ab4342d83968ab8f；證據補件 SHA：4d193536e36807e534555ab0b578f29ca4f09f18。2026-10-09依使用者獨立複核，只修下列三校，沒有接入下一批。71 partial／214、116完整核實0及原始來源921筆保持原樣。

- 東北 ncu-122：COE四件改為「校方COE通知後（可早於正式錄取）」，收到正式通知後才辦理；四筆政策移除强制錄取前提，保留 institutional confirmation、needs_confirmation 與當期未核。原[Preparing to Arrive – Fall 2026](https://www.insc.tohoku.ac.jp/english/exchange/preparing-to-arrive/)說明結果公告前須辦COE；2026/5/14期限不套中央116。此為資料時序不一致；沒有證據顯示實際學生文件曾被排除。
- 關西 ncu-129：僅 housing-visa-arrival summary/details 改為「收到錄取及e-COE後申請visa；取得visa後才購票」。依[2027春申請頁 Visa application](https://www.kansai-u.ac.jp/Kokusai/future/application_en/)。既有其他正確visa欄與報告沒有全局替換。
- 關西初次護照件：接上[一般FAQ](https://www.kansai-u.ac.jp/Kokusai/future/faq_en/)「passport is not ready」問答，允許先交能確認姓名的官方證件。官方未列具體證件、格式或補交期限；116適用待兩校確認，不免除赴日簽證所需護照。同步host_documents／visa可見摘要、該件來源及政策版本綁定。
- 日本中央 ncu-128：保留 arrival-visa ID作行前COE／入學許可／Student visa，另拆 arrival-orientation 到校正式選課步驟；保留[原申請頁](https://www.chuo-u.ac.jp/english/admissions/exchange/semester-or-full-year/)及既有附件、適用期間與未核註記，不添精確截止。UG／Grad期限、C1／C2、Part2 J／K／L、G2豁免沒有重改。

生成方式：全量 builder只寫 `/tmp/ncu-freeze-exceptions-bundle`作依賴計算，逐檔比對後僅複製有改動的產物。workflow只有三校、partners／destination／field-audit只有東北與關西，document policies只有五筆。原始 source-evidence、catalog-completeness、其他211校workflow及其他212校partners／profile／audit均未變。input provenance只更新兩個實際修改輸入檔hash。

預凍結檢查177件中176通過；新增測試誤取不存在的 applicability.reason 而失敗，實際API欄位是note，已修正測試。這是測試欄位錯誤，不是產品時序修正失敗；保留第一次XML。固定SHA後的結果與390／1440實際內容證據另附。

仍未解除：當期名額及完整116外校申請包、Kyutech原始失敗根因、遠端Quality工作流程無job失敗。沒有部署、正式DB操作、合併main或其他分支。
