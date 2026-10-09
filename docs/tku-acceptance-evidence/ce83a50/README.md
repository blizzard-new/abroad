# TKU ce83a50 原始驗收與中斷證據

候選 `ce83a502e33a42906fdf716bfaa606e777970d61`，分支 `data/tku-exchange-20261008`，[draft PR #2](https://github.com/blizzard-new/abroad/pull/2)。此分支只追加證據，artifact commit 沒有冒稱重跑程式驗收。

本機固定 SHA 十步完整：1482 passed、24 failed、8 skipped；其他九步exit0，所有起訖與逐步guard乾淨、commit不變。54相關browser通過；19隱私回歸、6/6探測、2JLPT及2原文來源browser另留實際HTTP/JSONL/JUnit/截图。報表原not_run仍誤寫七份selected；保留原報表並附acceptance-scope-correction.json列實際九份，不將未跑案例改稱通過。fresh wheel從此SHA建置，1009package來源逐檔相同；138MB wheel只保留雜湊與結果。851 CGU/NTPU/NTU workflow hash及各校完整資料bundle相同。

PR run37873683592、push37873678412均failure。每輪收集1764 nodes/182 files，實跑1037：1006 passed、16 failed、15 skipped，另1 internal error；727案例未跑。第1/2/3片75/74/74全部通過；第0片長longrepr TextIO寫出再度BlockingIOError，pytest exit3。啟動時blocking修正尚未足夠，不能稱完整1764验收。下一候選4133667改為原始FD/實際bytes/EAGAIN重試，另跑固定SHA驗收。

原66失败：35個原案例實際通過、16仍失败、15尚未跑；沒有新增案例failure，但有真實内部錯誤。不能把尚未跑15當解決，也不能用baseline豁免。每輪62個同job、同runner main控制為3passed/59failed；固定f6ad runtime/4e6原測試，原JUnit/實際pytest退出碼均保留。全部8份candidate+8份main-control原JUnit、原ZIP/完整解壓、pytest logs/collect/partition/result和整輪原log ZIP在remote/；沒有重建JUnit或刪除failures。PR merge 291af195與ce83相同tree37eed24b，原metadata附檔。

資料128rows，4當期2027–2028日語二甄/7公告名額、124舊期參考；9/30中午臺北校內截止已過，0個可新申請。89/152欄核實（58.6%），63適用缺口、13矛盾組。10/9重新GET官方公告與附件：19頁簡章與1頁名額表內容及SHA完全相同既有capture；限中央這兩份，沒有宣稱所有host 2027表格已核實。新版尚未核實與官方尚未公告分開，系所deadline不自動沿用中央延期，名額不是即時剩餘席次。

working-tree-probes保留有界診斷和中間失敗，包含後續4133667 logger probe，不加入ce83驗收統計。原歷史artifact不覆寫。manifest.json逐檔bytes/SHA256；acceptance-evidence.zip可下載且不含自身/manifest/checksum。checksum通過不代表測試全綠。未merge、部署、正式DB或權限變更。
