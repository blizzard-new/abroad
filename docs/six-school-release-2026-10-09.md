# 六校整合發布紀錄（2026-10-09）

這份紀錄更新早期 TKU 文件中「完整 runtime 尚未驗證」的歷史狀態。原始錯誤及各階段結果仍保留，不能將前一階段的失敗改報為通過。

## 固定驗證範圍

- TKU 上游固定來源：`b67d79aa3b6c30a9449801501256b64951f2c291`。
- 六校完整驗證：`0fdc6cfa6a4902fb83374a77025f45dffb071562`，2,641 個唯一案例，2,627 passed／0 failed／14 既有 skipped。四片 collection、逐案例原 log 與 JUnit 完整對應，起訖 SHA/tree 相同且工作樹乾淨。
- 14 skip：9 項既有 Phase C、4 項本機 Ollama 未啟動、1 項 pytest opt-in Docker。另已執行完整 Docker runtime，沒有新增 skip 或放寬 skip 條件。
- 原 `d1827d75` 全套為 2,599 passed／28 failed／14 skipped，TKU offline builder 也造成來源 guard 失敗；原始紀錄保留。修正後同 28 案例均 passed，最後再執行上述完整全套。
- 同一 `0fdc6cfa` 完整 35 migration、兩個 PostgREST、Storage、治理交易與六校 verified-email 政策通過。使用原 pinned PostgreSQL rootfs 和 runtime config，僅因 Docker VFS 容量限制改為本機單層封裝，沒有更換 DB 版本或擴大權限。
- 原正式 `e5c6d5ceafcb2099d45b67ab47aa464f7f82fa86` 的 102 個 Python 模組及原模型在独立程序中完成建立修訂、雙審、發布、讀回，12 次 HTTP200，新舊讀回 payload 相同；依賴環境為現有相容版本。
- uv lock、OpenAPI、JS syntax、SQL parser、strict dependency audit、wheel 檢查通過。wheel 2,527 項，15 張無授權新照片排除，TKU 字型及 OFL 授權完整。

完整固定證據：[artifacts/integration-20261009 @ 94ebc563](https://github.com/blizzard-new/abroad/tree/94ebc563/docs/integration-20261009)。後續 DB readback、Render 與正式站驗收持續記錄於同證據分支；本文件不以 mergeable 或測試完成宣稱部署成功。

## 正式 DB 與版本對齊

Actions 帳務阻擋，不能依賴 main push 自動同步 DB。使用現有授權連線逐份套用已驗證 SQL，再核對函式 body、signature、owner、ACL、security mode、search_path 與角色存取。

| migration | 實際版本 | 原候選檔名版本 |
| --- | --- | --- |
| verified_email_school_community | 20261009153249 | 20261009040000 |
| community_byline_aliases | 20261009153347 | 20261009060000 |
| atomic_governance_commands | 20261009153438 | 20261009080000 |

三份 SQL 成功且 readback 相符，檔案僅依實際版本重命名，SQL bytes 不變。兩個治理 RPC 保留原 invoker signature 及既有 service_role 存取；fingerprint helper 仍不開放給 service_role，改用已驗證等價的內建 SQL 運算。capability marker 恰一筆、沒有 published payload、schema audit receipt 恰一筆。

既有五個遠端／repo migration timestamp 差異保持原狀，沒有 migration repair、重跑歷史或 bulk db push。既有 CCU/NCU compatibility migration 的 source guard 僅增加對 TKU 先行插入列的容忍，已分別驗證 fresh/deployed 順序；正式函式未重套該 migration。

`0fdc6cfa` 之後只增加本說明並重命名三份 SQL。程式、測試、套件依賴與 SQL 内容完全相同；最後再核對 migration 順序與 parser，原始完整 pytest 的 SHA 仍明確標為 `0fdc6cfa`。

## 發布次序與回退

已完成 #5 → CCU/NCU compatibility DB → #3 → #4，每次都等 Render 對應 merge SHA live 並驗收實站。現在完成 TKU DB 後，才以固定 head 合併 #2、等待 Render exact merge SHA live，再驗六校 HTTP／手機桌面／guest 論壇限制與 NTU 照片、位置、生活來源。

若 #2 程式需回退，以正常 Git revert 該 merge 恢復前一五校程式，等待該 revert SHA live 並再驗收；保留相容 DB 與 append-only 審核紀錄。不能在 capability marker 或新版 client 仍存在時盲目還原舊 RPC。DB 修復需核對已備份定義並採精確 forward migration，不清除 audit、不還原整庫。

Quality 374368612 保持 `disabled_manually`；原 TKU 分支的 quality.yml 改動保留，整合者未修改該檔。Render autoDeploy/main、Supabase deploy workflow、branch protection、憑證及付費設定沒有變更。

## 資料仍有缺口

CGU154／NTPU409／NTU288 既有完整 workflow model payload 與原 main `f6ad1b8` canonical hash 逐校相同。CCU55 legacy、NCU214 pending、TKU4 partial（另124筆舊年參考）不代表全校當期資料完整，missing／pending／zero 分開保留。

NTU266 licensed photo／20 needs_review／2 missing，269代表位置；1,622有效生活節錄／124校保留來源年度。43地區有既有出發提醒，另14地區仍缺研究資料，API明確404；測試要求完整列出這14個缺口，不製造來源或年份。
