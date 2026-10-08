# 中央外校條件文件：已實作的參考條件與當期查核邊界

UOS兩項住宿健康文件與HUST一項錄取後健康報告已具備明確條件判斷，接入API文件目錄、個人準備清單、統一任務清單與實際手機UI。條件未知不當作全部必繳或全部免交。這項開發已完成，不能再列成外部資料取得阻礙。

| 文件 | 參考條件 | 結果與限制 |
| --- | --- | --- |
| UOS MMR兩劑／宿舍核准醫師替代證明 | 已取得外校錄取且選校內宿舍 | 校外住宿不適用；尚未錄取延後；錄取或住宿未知需確認；醫師替代仍須宿舍核准 |
| UOS Health & Medical Clearance Form | 已取得外校錄取且選校內宿舍 | 四態同上；醫師及本人簽名、六個月內TB；不能取代MMR另件 |
| HUST近三月健康報告／醫院公章 | 已取得外校錄取 | 未錄取延後、錄取未知需確認；沒有住房前提，也不移到初次申請 |

政策逐件明列於[source policy](../sources/ncu/2026-10-08/document-conditions.json)，按學校及完整文件名稱匹配；不以MMR、health或費用正則猜門檻。builder驗證policy的rule_id、文件名稱、來源URL與逐原件SHA，並寫入可離線重建的bundle；原件變更、取得失敗或缺少版本綁定時阻止重建，須重新明確查核。原始文件、年度、SHA與查核日仍在field-audit／source-evidence；條件政策並不取代來源查核。

`PartnerDocumentPreparationState`只接受明確的錄取與住宿狀態；`DocumentApplicability`回傳applicable／not_applicable／deferred／needs_confirmation。申請設定以學校＋學年度＋梯次＋學期為鍵保存每個狀態快照。切換學校、年度、梯次或學期，不借用另一期間的已錄取狀態；不同鍵跨裝置合併，同一鍵保持一組狀態，不把兩裝置欄位拼成未選過的組合。

`/application-center/catalog`帶錄取、住宿與學期參數；`/application-plan/evaluate`由各志願提供自己的狀態，清單與統一任務共用[ncu_document_conditions.py](../src/exchange_info/ncu_document_conditions.py)。延後、不適用與未知文件不列在當前「要準備的文件」清單，仍以條件說明可見；符合條件也只表示符合參考範圍。未發布文件繼續needs_confirmation／不可正式下載，沒有host精確期限或提醒。中央未發布流程不能被借用為另一未來年度的估計清單。

既有工作區JSON欄可保存狀態，沒有套用正式DB或準備migration，也没有新增流程文件規則模型欄位，因此CGU／NTPU／NTU的851份workflow content hash均與f6ad1b8相同。共享API模型與OpenAPI快照已更新為2026-10-08.5；功能與當期資料核准分開驗證。

仍待外部核實：UOS當期接收包、住宿保障／價格／入住期限、TB與替代證明的當期宿舍通知；HUST中央116適用通知、當期健康檢查時效與各院追加件。這些缺口仍顯示在逐欄稽核。UNDIP十項文件保留Online／Visa類及portal要求；這次沒有任意把Visa類移到錄取後。
