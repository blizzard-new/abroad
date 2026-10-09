# CCU 正常 TLS 修正與指定補核的固定 SHA 驗證

測試僅屬程式／資料 commit **`9b18b409a370fd8a4fecc7cff1d18d399f4f9ab3`**，後續純證據 commit 未重跑程式測試。[完整 summary](final-validation-summary.json)、[選檔](test-selection.json)、[起始](git-boundary-start.json)與[結束](git-boundary-end.json)證明同一 SHA、工作目錄乾淨。[驗收結果](acceptance-results.json)區分資料完整度、本地測試、外部擷取與遠端 CI。

|實際檢查|結果|
|---|---|
|480 回歸|473 passed、7 skipped、0 failed、0 errors；JUnit 406.15s|
|106 瀏覽器|106 passed、0 skipped、0 failed、0 errors；两組 JUnit 1244.55s，較長組 wall 634.42s|
|產物／打包|7 builders 的1,215 CCU檔逐byte不變；wheel相同1,215檔，SHA `58cbb8e3bb3895dcda7a9f348966a867f59066693dbd586207bd1ff38ea21a3c`|
|既有資料保留|1,091份77dfd84來源／附件、46份main官方資料及77個CGU published hash不變|
|舊證據／原始來源|77候選88檔、92候選96檔及歷史10 source JSON+10 payload逐byte保留|
|契約與檢查|110 API paths和既有required保留；OpenAPI、uv0.11.26鎖檔、Python、4JS與指定Ruff通過|

[原始回歸 log](regression.txt)／[XML](regression.xml)、[browser XML](browser.xml)、[案例聯集](case-union.json)、兩組各自log/XML及browser-evidence保持原始內容。7 skip為6既有Phase C與1 Docker opt-in。4個390／1440四校正式bundle UI/API案例沒有response/state mock；8個延遲／排隊案例使用真實API回應或browser clock，未另延遲life頁。其他既有e2e fixture會替換CGU partner list，與4個獨立案例區分。

104合作條目：52曾列非零名額、3 名額未知，不能視為 0、49灰字參考；55接收流程／概要。980來源、33校250文件要求（184當期、66待確認、59條件項）。935海外欄307當期、334待确认、202缺值、71矛盾、20參考、1官方明示未公告；0校17欄全當期、0完整host文件清單，functional_parity_complete=false。母校2027春三梯已截止，2027秋新版尚未核實，不等於官方明示尚未公告。

CCU擷取程式已移除忽略憑證錯誤的context／CLI路徑，正常Chromium實際ERR_CERT_AUTHORITY_INVALID並fail closed。[14份逐來源正常TLS讀取收據](normal-tls-revalidation)分別是11份Mapúa／UNINTER重核及3份AMU指定頁。9份歷史不安全DOM／影像禁止現行引用；舊手冊本來就是正常TLS取得，另下載驗證與34頁抽取文字一致。[20份原始保留](historical-20-raw-files-preservation.json)、[舊目錄保留](prior-evidence-preservation.json)、[來源影響](../../../src/exchange_info/official_data/ccu/tls-source-impact.json)及[安全說明](../../ccu-tls-security-2026-10-09.md)保留方法與時序。共用既有image/content collectors未執行、未改；沒有宣稱整個repository已清除所有歷史bypass，範圍見[掃描證據](ccu-bypass-removal-scope.json)。

正常TLS UNINTER公开題目API列48項metadata，表題Autumn2026／Spring2027；實際顯示、分支及必填仍待核，舊44題仅作歷史，不宣稱正常browser已核。Mapúa校曆影像日期已目視；一般手冊價格／簽證不推為2027春當期。AMU General／Additional／Medical Services已限定一般學生、NFZ與私人方案、舊費率及投保階段，insurance補pending。Mapúa手冊p18／21的停留結束後6月護照條件与當期factsheet無起算點分開；p33 TOR／clearance通常1–2週放返國準備pending，未列初次申請附件。兩項生活指南經實際API與production renderer驗證。詳細待確認事項見[指定補核](../../ccu-bounded-followups-2026-10-09.md)。

新API／影像摘要逐來源列10/09與格式，保留舊factsheet各頁碼／10/08；新4個UI回歸與原始JSONL/API回歸另列，見[複合摘要修正](../../ccu-composite-provenance-2026-10-09.md)。e42f684因新增來源顯示要求中止，沒有完整通過結果，[原紀錄](../e42f684-aborted/README.md)另保留。

新增複合UI初輪因未切母校4失敗；修正實際母校切換後2個UNINTER案例又因廣泛li selector同時選中摘要／文件說明而失敗，中止後改用具體欄標題定位。原log/XML與停止收據均保留，最後四個UI案例另核。

44f6de1完整回歸曾468pass／7skip／3fail，瀏覽器gate未完成；[原失敗紀錄](../44f6de1-aborted/README.md)保留。安全初輪31測試的兩次失敗及renderer新增測試路徑错误也原樣保留於normal-tls-revalidation，沒有删除保護測試、改寫來源方法或重用失敗SHA的成功結果。旧92证据中不安全擷取部分由本轮安全覆核明确限制，原历史文件未覆寫。

323筆既有研究佇列的限定處置保留，不等於所有來源全文／所有政策完成。[當前候選CI](remote-ci-current-candidate.json)獨立記錄，不能把本地gate當遠端CI通过。Jena正常browser外部表單下載憑證失敗亦保留於browser-evidence，與local UI測試分開。其他分支未合併、跨分支整合／全部repo測試、Supabase、依賴漏洞審查及部署未執行。17個必要共用檔見[整合邊界](../../ccu-followup-integration-boundary-2026-10-08.json)，本次安全與指定補核没有再改它們。

原始HTTP HTML的CRLF／尾端空白保留，完整diff --check有實際非零結果；僅排除原始HTML的編寫檔檢查另记，未正規化payload或logs/XML。manifest存各檔SHA256且排除自身。未merge main、部署、登入校方系統、提交表單或更改憑證／權限／付款／安全設定。

純證據staged diff亦因11份原始log／XML空白回傳2；僅排除這些原始log／XML的編寫檔檢查為0。[實際staging證明](evidence-publication-staging-proof.json)列明全部純證據路徑與範圍，原始結果沒有正規化。
