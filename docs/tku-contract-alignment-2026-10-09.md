# TKU 候選的十二項既有契約校正

基準：`09386aa318c9574862a6f3b1447c5022a6c26433`；查核日：2026-10-09。
本批只校正下列既有測試的 fixture、現行介面與公開資料契約；不改 production source、官方資料、migration、OpenAPI 或治理路由。所有 test function names／IDs 保留，沒有新增 skip／xfail、降低登入門檻、還原舊資產版本或添加僅供字串比對的無效 production 文案。

| 原測試 | 實際原因 | 校正後保留的檢查 |
|---|---|---|
| `test_experience_api_reads_cache_and_refreshes_selected_school` | 當前 API 會加入林肯大學兩篇 bundled digest sources；原單一快取 fixture 未隔離這個額外資料來源 | 只在此 fixture 將 digest bundle loader 設為空；原 cache=1、coverage、refresh 合併新舊 URL、實際儲存與 audit 全保留。正式 bundle 不改，既有 digest／生活來源測試另行執行 |
| `test_destination_profile_api_returns_verified_official_summary` | 公開 city 已中文化；不是原資料被覆寫 | API 單筆／列表均為「林肯, 坎特伯里」；新增實際儲存仍為 `Lincoln, Canterbury` 與原 review status 不變的斷言 |
| `test_web_routes_states_and_touch_targets_are_consistent` | feed 已由獨立 reader 處理錯誤，舊 app 字串不再存在 | 現行 reader 錯誤回應、status、retry、escape；保留路由 heading、觸控尺寸及其他狀態斷言 |
| `test_community_identity_preview_matches_public_name_and_resets_per_submission` | transport 現行呼叫帶 options，舊字串只接受單一參數 | 真 transport 呼叫、same-origin credentials、request context；原署名預覽、reset、delete 斷言保留 |
| `test_web_notification_center_and_explicit_email_opt_in_are_present` | 通知已提供「查看逐項變更」而非舊文案 | 現行變更按鈕、目前 plan 一致性及歷史通知提示；原明確 email opt-in、讀取／標已讀、官方來源與觸控尺寸保留 |
| `test_application_center_separates_official_requirements_from_preparation_tools` | 未找到正式目錄時，現行 UI 引導向校方確認，旧文案已移除 | 目錄的母校／目標／系所／年度／梯次 context key、無適用 workflow 時的 guard；原官方表格與準備工具隔離保留 |
| `test_successful_login_closes_before_noncritical_account_hydration` | 固定在歷史 app／CSS cache tag | 解析真 HTML 資產、要求唯一引用／本地檔存在／有效 cache version；登入視窗先關閉、全部 hydration tasks 和 partial failure 斷言保留 |
| `test_personal_application_plan_uses_structured_api_and_progressive_login` | 系所改為共用 `advisor-department`，仍屬同一份條件表 | 真 department name／advisor form／submit 接線、年度梯次、原三志願及現行四五志願；原 API 與 progressive login 保留 |
| `test_global_home_board_routing_and_following_are_present` | 政策已明確改為跨校 verified-Email，舊學籍驗證文案不適用 | 現行驗證狀態入口、verified-Email 跨校政策；原板路由、發文權限、unavailable reason 和追蹤保留 |
| `test_departmental_partner_references_are_visible_but_blocked_from_formal_plans` | 說明改為向學院／國際處確認，舊 HTML 固定文案已移除；志願選項現在共用 availability 判定，以保留其他母校待公告規劃政策 | departmental branch 明確 `blocked:true`、確認提示；原按鈕 disabled、blocked guard 保留，志願 filter 必須實際使用同一 blocked 判定，院級參考仍被排除 |
| `test_hash_router_shows_one_feature_page_without_scroll_spying` | 搜尋入口是 `#partners`，`#search` 保留舊連結支援而無舊 submit handler | 真搜尋入口／輸入、舊 hash 被接受、既有 showUniversityPage 路由；原單頁 hidden／active dataset／無 scroll spying 保留 |
| `test_route_assets_are_cache_busted_together` | 多個資產已更新，但舊測試固定七個歷史版本 | 真 HTML 中八個唯一、可解析、本地存在且有 version 的資產；app／reader 配對版本及載入順序；原 scroll／invite 行為斷言保留 |

共用測試 helper：`tests/static_asset_contract.py`，只解析既有 HTML，不改產品資產。三個既有測試檔合計 126 個 test functions，AST 比對名稱與順序均相同。正式驗證在提交後以固定 SHA、乾淨起迄工作樹執行，結果另保存，不把 precommit inspection 當成驗收。

五組治理產品能力維持 pending：管理工作台、來源替換、snapshot staging、目的地審核／發布／回滾、流程歷史／readiness／回滾。尚未收到本批範圍選擇，不擴張接線；亦不刪除這五個失敗測試。

## 全量 CI 發現的額外 router fixture 時序

`c6e6155` PR run 37895974293 第1分片的原 XML 記錄 `test_search_updates_are_bounded_and_rapid_navigation_cancels_old_motion` 最終 opacity 為 `0.65`；同源 push 分片75案例全通過，本地固定 c6e6155 原單案亦通過（實際18.2秒含起迄檢查）。這些結果分開保存，不宣稱本地重現、不豁免原 PR 失敗。

現行 `motion.js` 的 route 在 requestAnimationFrame 排程動畫；原 fixture 只問目前是否無動畫，可能在排隊動畫開始前越過等待。只補真實兩個排程影格 barrier，並同時等原 UniWay 動畫皆結束且 computed opacity=1；原最後 opacity=1、快速導航四步及 delay<=90 斷言保留。沒有固定 sleep、關閉動畫、mock response 或 production source 修改。此原 test ID 保留，提交後另以固定 SHA 驗證。

前輪 c6e6155 push 第0分片原 XML 另記錄多志願1754寬度原案例等不到重排 PUT（30秒）。此 fixture 的第一個進度 checkbox 仍只等可能殘留的「已同步」標籤，登入也會先於初始化 hydration 關閉；首輪固定SHA相關browser沒有涵蓋此file。只補真實初始化 load／network idle，並要求第一筆包含兩志願及該 task=true 的實際 PUT200 後才開始重排。原重排PUT、server直接讀回、progress、reload、移除再加入與兩個原寬度的全部斷言保留，不替代API或放寬條件。
