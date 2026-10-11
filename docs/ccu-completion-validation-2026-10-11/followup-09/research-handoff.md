本輪可達範圍驗收已完成，可停止擴大公開研究，等待整合。這是已知來源與具體缺欄的有限結案，沒有宣稱全網窮盡、所有外鏈已讀或新版官方明示未公告。

資料／程式／測試凍結 commit：`a4e425d456409f0113126d15347fb5d886e13f01`。分支 `data/ccu-completion-20261011`，Draft PR #10；本輪 fetch 後 `origin/main` 仍是 `59a20f27fcee00fb597abc79e75ec11778317422`。最終證據 commit 與推送 readback 另見最後交付。

263 筆第八輪 absent/false full-visible flags 逐筆對照：17 筆原本已明示完整閱讀，只補 canonical ledger 的旗標；246 筆原為真正抽讀，其中17筆補讀相關主体／子頁，其餘229筆保留原讀取範圍與不適用理由。不可把263全數解釋為未讀正文，也不可把229的有限結案解釋為全文讀完。第八輪 input/progress/測試證據完整保留。33個明確相關官方子頁／附件用正常TLS取得，HTTP200不等於政策確認；31個新子頁可見主体完整讀取，NJU住房管理後半及EdUHK學程例外表只讀指定部分。5個PDF合計12頁已完整抽取核對。

更新21個接待欄位，其中19個原missing：2個明確當期、6個歷史／不同學期參考、11個未標年或需確認。其餘2個更新既有欄位，保留舊證據。1768個接待欄位目前361 verified_current、318 reference_only、585 missing、416 needs_confirmation、87 conflict、1 explicit_not_announced；只有該既有一欄保留官方明示尚未公告。585嚴格空值不是585個已證明私有或不存在的資料。

重點核對結果：

- EdUHK繁體中文是台港澳指定版本，GPA2.5/4、TOEFL80（2026-01-21之前考）／新版4（當日及之後）、IELTS Academic6或老師證明。考試改制日不是交換申請學年。當期2026/27校曆正文與2026-08-28更新已核：Spring2027一般非畢業班授課至5/3、考試至5/17；畢業班4/12／4/24，學程例外另核，不當離境或宿舍期限。
- Chandigarh網頁Fall Intake2026/27 SEP partner scholarship免學費／住宿與Spring2027分開。factsheet正文仍SemesterDates2021及online模式，提名11/15、4/15只歷史；未標年網頁學生申請10/30、3/30不能拼成同年流程。Partner Universities連結實際InternationalTransferPrograms outbound學位路徑，排除。AdmissionForm是未標年泛用國際生表；75%是上課出席，不是入學GPA。
- KMITL表格頁公開正文明示Registered users only、Login/Register及special permission；未取得表格／版本。只有該步驟受限，學校其他公開政策不被標私有。
- ZHAW SoE完整5頁PDF日期22.04.2026，沒有Spring2027適用年。Mobility-Online完整文件在母校提名後取得；本科Winterthur與MSEZurich、學制與freemover分開。MSE spring intro week37與網頁／timeline week7既有衝突保留；14週授課不當最長交換期間。簽證／L permit／財力CHF1750月只校方未年指引，不是最新台籍法律判定。
- Strasbourg非EU bilateral正文2026/27第二campaign僅semester2，第一campaign可一／二學期或full year；選上後母校轉個人form link並簽包上傳portal。Acceptance letter段仍2025/26，既有衝突不改成2027。公開文件清單與個人表格獲取限制分開。
- Nankai明示校際交換保險依交流協議；一般外國留學生500/semester、1000/year不直接套台籍CCU。八里台／津南公寓一般參考不保本期住房。NJU2022外國留學生費用、BUT2025生活費及Østfold2022住房頁分年／對象保存，不作2027價格或法律結論。

母校與資產保持：104校／25國，52公開名額（49正整數、3不限），3空白（71/80/107）、49灰字未開放、零名額0；104校內申請視窗均closed。Fall2027新版仍未核實，沒有改為官方尚未公告。原55份profile位元前綴保持，CGU77／NTPU206資料未變。本輪沒有新增核心registry/API/UI/資格／文件共用程式變更；整個PR既有共用適配仍為api.py、static/index.html、pyproject.toml，請整合者集中合併。

資產最後安全檢查只重新驗證既有快取與來源hash，無重試網路：101座標、100有授權照片、103網站身份保持。缺座標DNTU(71)、Silesian University School of Business Karviná(111)、墨西哥Cuernavaca Uninter(119)；缺照片UEL(66)、DNTU(71)、Presidency Bangalore印度(80)、Uninter墨西哥(119)；Keimyung(44)官方網站身份仍因可讀正文不足。Karviná與Opava不同，opakarvina.cz是錯誤學校；相機EXIF／viewer／ROR城市／租屋點不能當機構marker。官方刊圖不等重用授權，沒有來源不足的城市點或未授權圖補值。

Gamma現有正常TLS公開頁仍pageProps空，完整協議卡片內容及全量分母未取得。先前瀏覽器TLS錯誤／匿名snapshot FORBIDDEN並非獨占校方帳號證明；本輪不再重試同失敗。需要CCU國際處提供有版次／查核日的全卡片PDF/CSV/XLSX公開匯出；104只交換清單分母。

精確外部輸入表：`src/exchange_info/official_data/ccu/completion-ninth-external-inputs.{json,csv}`，1407個非verified_current欄位逐校逐欄列出最小文件、目標學期、來源證據及獲取步驟，其中585個是嚴格missing。這張表不宣稱全部只能私下取得。校方接待當期簡章／具年版表單、去識別提名後指引可補年度／身份缺口；不要求帳號或憑證。8個校園資產缺項另要求明確校区機構marker、正確圖像及權利人授權、或可讀官方身份聲明；Gamma全量匯出另列。

有明示個人／提名後／登入表格步驟共10校11欄：49 Sungshin forms、59 KMITL forms、66 UEL forms、87 Strasbourg forms、88 Lille FGES documents+forms、89 SDU forms、103 ZHAW SoE forms、112 CZU forms、117 Oneonta forms、120 QUT forms。當期空白模板／完整清單與去識別個人獲取程序需要校方補充，沒有註冊、登入、填送、聯絡校方或繞過保護。

整合時仍須獨立處理先前全平台2668測試中的NTU截圖路徑／單一Jena問題，以及pinned Supabase Postgres17.6.1.136映像layer磁碟限制；本輪不重試DB、不修改安全／付款／存取設定。保留Draft，不merge/deploy。
