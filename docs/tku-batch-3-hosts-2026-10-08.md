# TKU 第三批：四校外校申請、生活資料與逐欄完整度

2026-10-08查核。`blizzard-new/abroad`、`data/tku-exchange-20261008`、獨立目錄`/workspace/abroad-tku`。再次fetch的main仍為`293546e807294dc0812f390b240a4cfb68e86cd0`。此文件與本批validation JSON為目前交接；第一批文件、63.1%等舊統計僅歷史記錄。

## 可整合交付

- 最新核實2027–2028日語二甄4校7名；**母校2026/9/30 12:00臺北截止，0筆可新申請**。外校仍收件不表示校內重開。
- 舊期124計畫列（英歐89、中文35）保留，與4筆當期分開。128是計畫列，原文校名去重119，無重複ID；109 numeric、19 TBC provisional，空白／零／不確定狀態不混用。
- `official_data/tku/sources.json`現在72筆來源快照／嘗試；28份原附件可離線開啟並核對SHA。本批17份長崎／UEC PDF/DOCX已讀內容，非只看檔名。3個failed入口保留：舊日語附件404、誤試UEC life路徑404、日本出入國在留管理廳403；不作verified依據。
- `host_documents.json`四校53文件項目，保存condition、phase、來源頁碼、適用期、日期、表單URL／非公開取得方式。互斥學制、國籍、補助、健康條件分開，**不是全部必繳53份**。
- 四校workflow各6步，每校母校文件8項；外校申請立命館9／長崎11／成蹊10／UEC15；行前立命館6／UEC2。維持未正式發布參考，無截止提醒。
- 四校生活profile各14區塊，包含住宿、餐費、生活費、保險、官方簽證／居留、課程、行前、接送、獎助。已修成前端接受的`official_partial`；不稱全部完整。
- `completeness_matrix.json` **128計畫列×38欄**，每格有status、value/null、reason、evidence、checked_entries。一般頁、舊版、非公開表、未核實新版不因有URL而標全部完成。124舊列尚未逐校查當期host，明示來源僅archive discovery，未知格`not_verified_new`。

新校別模組：`tku_host_data.py`、`tku_life.py`、`tku_completeness.py`。抓取／人工提升／重建／驗證在`scripts/*tku*`；其餘原校別schema／資格／文件／摘要模組保留。離線API與瀏覽器能讀同一bundle。

## 四校當期／參考依據

| 學校 | 提名／申請 | 已讀內容與限制 |
| --- | --- | --- |
| 立命館2027 Spring SKP | 2026/10/22 09:00 JST提名；11/2 09:00 JST申請 | 22頁簡章，track／校區／學制／語言分開。提名後寄帳號，COE另交行政書士，健康及住宿表錄取後提供。50,000日圓含指定保險與COE，不含國保。 |
| 長崎2027春NICS | 2026/10/31消印有效，未載時刻；未另列提名截止 | 官方合作目錄列淡江，Form A及誓約書內文2027，其餘無年度表由當期公告直連。**淡江本輪表未寫NICS，最終track／碩士適用仍需承辦確認。** |
| 成蹊Spring2027 sheet，Aug2026內文 | 提名10/1、申請10/15，未載時刻 | 6頁全讀，母校承辦Email送件。COE在線表及財力證明；財務申告僅獎助申請人。當期清單已核實，但非公開空白表內容未取得。 |
| UEC一般JUSST，2025/10/28更新 | 一般April entry為October31，2027專屬未核實 | 9個PDF/DOCX版本讀內容，Form A©2023，ver22/ver23不當年度。文件API/UI逐項明示「一般參考／2027版未核實」。 |

官方入口及頁碼：[立命館2027簡章](https://en.ritsumei.ac.jp/skp-e/apply/pdf/Application_Guidelines_ENG.pdf) p.2、4、5–8、14–22及[申請頁](https://en.ritsumei.ac.jp/skp/apply/howto/)；[長崎2027 NICS](https://www.nagasaki-gaigo.ac.jp/studying-abroad/receiving_program/nics_program/)及[合作目錄](https://www.nagasaki-gaigo.ac.jp/studying-abroad/partner_university/)臺灣段；[成蹊2027 sheet](https://www.seikei.ac.jp/gakuen/siis/intl/%E2%97%8FInformation%20sheet%20Spring2027%28Seikei%20University%29_updated0827.pdf) p.1–5；[UEC一般申請／表單](https://www.fedu.uec.ac.jp/en/future_students/jusst/application/)。

長崎2027交換生學費0，活動費半年50,000／一年53,100（含A/B保險），行政15,000／20,000（含福岡接送）；單／雙人入寮費及21,000／42,000月租、30,000餐費分開。首學期原則全體Ampelos，房型偏好不保證，至6月底早餐／晚餐必訂。國保約2,000/月另付。一般非交換生270,000／540,000學費不套淡江互惠交換。

成蹊2027/9起MICHI120,000/月；此前Dormy／會館93,000/月，餐、水電、寢具及押金包含項目不同，不用前期價套全年。國保、手機、其他支出另列。立命館2026/3起住宿費、一般生活預算只是參考，每學期可改且保險可能與新支援費重複；不直接合計成2027確定總額。UEC25,000住宿、26,000保險原文沒有計費單位，不猜月／年；一般生活頁的2009保費表不升為當期。

UEC Form H已由實際內文修正：本人及母校國際處／授權人簽，錄取後UEC健康檢查，並非醫師簽表。SP全體、RP-U學士／RP-G研究生；財力自費者錄取後、TB僅指定國籍等適用者。淡江當期row4「有機會申請JASSO」已恢復，非保證獲獎。外校無日語入學門檻仍需修日語課；不能覆蓋淡江本期門檻。

簽證保存[日本台灣交流協會：臺灣護照持COE](https://www.koryu.or.jp/visa/taipei/general/detail1/)及[日本外務省學生簽證](https://www.mofa.go.jp/j_info/visit/visa/long/visa6.html)的一般指引，適用國籍／居住地與送件時規則，不是2027校方表。簽證4.5×3.5cm照片與外校4×3cm不同。住所／國保為一般官方指引，UI改「抵達後辦理事項」，不把14日住所登記義務稱72小時內全部完成。

## 逐校38欄與缺口

| 學校 | verified | reference_only | needs_confirmation | missing_in_source | not_verified_new |
| --- | ---: | ---: | ---: | ---: | ---: |
| 立命館 | 26 | 3 | 4 | 4 | 1 |
| 長崎 | 22 | 2 | 6 | 6 | 2 |
| 成蹊 | 26 | 1 | 5 | 5 | 1 |
| UEC | 11 | 14 | 4 | 2 | 7 |

詳細逐格見matrix及TKU `/school-data-completeness`。未核實系所較早截止、系所送國際處新截止、修正表舊日期及75／前40%替代。外校住宿申請確切日、指定抵達日、2027課表仍有逐校缺口。成蹊精確calendar連結AY2026、長崎calendar展示2026、UEC課表2026，未混入2027精確日期。

`conflicts.json`共13組：原7组全部保留，另長崎照片公告3張／指南2張、Form B日英文字數／語言、母校2027/4–2028/3與長崎2027/3–2028/2、NICS對應、立命館預算保險重複、UEC Form A Fall標題／April內文。正確長崎URL已核實，原表誤連城西仍保留問題記錄。

已重查母校新聞及赴外頁；英歐／中文2027–2028仍「尚未核實新版」，沒有官方明示「尚未公告」的證據。一般協議目錄與院系大三出國不當成本梯校級清單。124舊列保留全部，不偽裝其外校當期資料已全部收齊。未聯絡承辦、未建立外校帳號。

## 共用整合點

原registry（TKU PROFILE／別名）、models（3個availability enum）、API（校別分流／正規化／時窗）、storage（TKU bundles）、application_documents（2個準備稿）、app.js（可用性／外校期限）、index.html（篩選）、pyproject（DOCX/XLSX打包）均需中央集中整合。
另`docs/api/openapi.json`同步enum；本批API新增TKU逐欄完整度，app.js只在TKU分支調完整度措辭／抵達標題；`tests/test_school_completeness.py`因新增4校改总數287並assertCGU77／NTPU206保留。合計10個共用檔，校別邏輯均獨立。

CGU/NTPU官方資料相對main沒有diff；CGU116的77目的地（75校級＋2院級參考）及115的77workflow、NTPU206（169開放＋37協議）保持。沒有動臺大、共享工作目錄、憑證、方案、安全、付款、CI workflow，沒有merge／部署。

## 實際測試

TKU16 tests通過。擴大回歸**199 passed／9 failed／6 skipped**，九個failure ID均在未改main既有集合，new failures為0；此批因增加4校引起的舊硬編碼總數測試已修正。完整機器證據：`tku-batch-3-validation-2026-10-08.json`。

Chromium逐校實際展開詳情、外校文件流程、生活14區塊、完整度38格，無page error。文件中心在各校獨立新學生情境驗證當期／一般參考文件與條件。桌面1280×900、手機390×844；4列、open篩選0、closed4、East Asia4。截圖在`/tmp/tku-detail-{0..3}.png`及`/tmp/tku-browser-*.png`，可用`scripts/check_tku_browser.py`重做。

另觀察到共用文件中心「已有目標→換另一目標」確認後仍停原校，catalog仍是原目標、loading=false、dialog已關，造成測試timeout；不是文件API無資料。此跨目標規劃狀態問題的main重現尚未核實，沒有擴大改所有學校的計畫遷移處理；交中央整合查明。逐校新情境的文件顯示驗證與此問題分開。

OpenAPI --check、Python／JavaScript語法、diff --check、離線重建逐位元相同通過。`uv lock --check`在本分支及未改main都實際失敗：`The lockfile at uv.lock needs to be updated`，未改lockfile。使用既有venv／frozen安裝。
遠端quality run37719707403（92fc2fe）failure、無jobs/check-runs，取log為`failed to get run log: log not found`。原因未核實；推送後新run另記錄。本地通過項目不表示CI通過。

兩次健康命令實際成功（原分支、Python讀檔與JSON數量），環境可用。回傳session訊息工具另報`entitlement_required`（Business以上），訊息未送出；不把它當作shell離線，不改方案或另開環境。

離線重建：`PYTHONPATH=src .venv/bin/python scripts/build_tku_catalog.py`。抓取僅寫新staging；人工提升recipe明示已讀內容、原生年份及衝突，沒有自動把新檔當當期。剩餘項目需非公開錄取生材料、承辦澄清或新版官方資料後再核對，才能提升狀態及正式發布流程。
