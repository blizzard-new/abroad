# CCU 正常 TLS 重核與來源影響

安全修正以證據發布 commit `da009c7811c94e29485dcb99b39eaf8b5662953e` 為基準。此前使用忽略 HTTPS 憑證錯誤的 browser context 不再沿用。`fetch_ccu_public_renders.py` 已移除 CLI 選項與 context 參數；正常 browser 憑證失敗實際回傳 1，中止且沒有 fallback。`revalidate_ccu_public_sources.py` 只以 `requests.get(..., verify=True)` 逐來源讀取官方 HTTPS，任何 TLS 例外直接失敗，不判定當期適用性、不填寫表單或請求學生回覆。

原 8 份 rendered DOM、其衍生的 1 張校曆影像共 9 份來源禁止用於現行欄位／文件／概要映射。原始 10 份來源 JSON 與 10 份 payload 均逐 byte 保留，原取得時間與 `acquisition_method` 沒有改寫。[影響清單](../src/exchange_info/official_data/ccu/tls-source-impact.json)保存原 SHA、逐項新來源、回應 hash、13 個替換 evidence 位置及剩餘問題；API 的 CCU 驗證器會拒絕再引用受限歷史來源。各衍生 inventory 另標 `historical_insecure_acquisition_not_current_evidence`。

|歷史來源範圍|本輪正常 TLS 核實|適用性與限制|
|---|---|---|
|Mapúa root、calendar-index、ilrad-contact、visa、application、dormitories、handbook 七份 DOM|每一 URL 各自 HTTP200；解碼該回應的 `data-page` 結構並選指定公開段落，不使用 browser DOM|泛稱 AY2027–28 degree banner、一般簽證／提早申請／住宿價格不推為2027春當期；原矛盾保留|
|Mapúa calendar-image|獨立 HTTP200 校曆回應，依唯一 College AY2026–27 標題取得內嵌 JPEG，目視日期，影像 hash `0fced0e26cfd2ac7963a422db3a18108fad9120088fe77400f6738bc8aa65ad3` 與原圖相同|第三季2027-02-01至04-24、第四季05-03至07-17；註冊日不是交換申請截止|
|UNINTER current-form DOM|正常 TLS 前端頁揭示 question-only `prefetchFormUrl`，另正常 TLS GET 公開題目 API，兩份原始回應分開保存|API 表題 Autumn2026 / Spring2027、48筆題目 metadata；不能宣稱正常 browser 已顯示44題或48題皆顯示／必填。渲染與分支仍待核，其他附件也未核齊|
|Mapúa International Handbook PDF|原取得本來即獨立 requests verified TLS；本輪另 HTTP200 下載48,433,633 bytes，hash與全部34頁抽取文字相同|©2026一般手冊與April2026估價不推2027春全適用；舊、新記錄只承接指定已映射段落|

共 11 次獨立正常 TLS HTTP 讀取，形成 11 份新來源；另有一筆舊正常 TLS 手冊的完全相同正文關聯。逐項正文、頁碼、年度、時間與 hash 見[新查核 ledger](../src/exchange_info/official_data/ccu/twentyseventh-source-review.json)。[原第二十六輪 ledger](../src/exchange_info/official_data/ccu/twentysixth-source-review.json)增加安全重核註記，原正文與原查核時間仍保留；基準 commit 提供其修改前原檔。

`overseas-reviewed-fields`、`partner-document-requirements` 改用各自獨立正常 TLS 新來源，`profile-reviewed-fields` 原先没有引用這9份正文，新增各自正常查核 source_checks。UNINTER 現行說明改為48筆 API metadata，舊44題只明示為歷史。欄位、文件及生活顯示改用 evidence 實際查核日期，母校原文件2026-10-08日期保留。所有離線產物重建；沒有共用 registry/API/UI 核心邏輯變更。

初輪測試曾指出舊正常 TLS 手冊失去直接映射後應補完全相同正文關聯；隨後新測試又要求不可把舊來源改寫成新 receipt，已分開檢查原來源與正常 TLS counterpart。修正後31項相關測試通過；原失敗結果保留在本 session 的 round27 工件，最終固定 SHA 檢查另記。未修改系統、repo 憑證或信任設定，未合併、部署。

正常TLS原始HTTP HTML含CRLF與尾端空白，完整diff --check實際為2；排除僅原始public_responses HTML後為0，未正規化正文以免更動hash。
