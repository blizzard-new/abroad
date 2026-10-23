# UniWay Android 測試版與 Jerry 主機設定

這次只做手機程式與服務整合，沒有新增大學資料查核。

## 先知道測試範圍

APK 的服務網址固定為 `https://app.uniway-tw.com/`，Android package 為
`tw.uniway.app`，最低 Android 7（API 24）。使用網站原本的 Google 帳號，
由瀏覽器完成登入，再以 PKCE 綁定的一次性代碼回到 App。
Google OAuth 原有 callback URL 不必改成手機 scheme。

收藏、選校條件、文件準備狀態、申請文件選擇、預算與個人日期會透過網站原本的
`/account/workspace` 同步。離線修改保存在目前帳號／學校的裝置快取中；恢復連線、
回到 App 或每 30 秒同步。兩邊修改同一欄會請使用者選擇，其他 Web 欄位保留。
2.1.1 起，表單的非敏感一般欄位也會透過既有 `/account/application-drafts` 加密同步。
開啟表單會讀取電腦草稿；即使尚未填完，按「儲存草稿」也能保存。離線草稿使用手機
安全儲存，依服務／帳號／學校隔離；重新開啟表單、回到 App 或定時同步時會重試。
尚未按儲存的輸入不會自動保存。電腦在手機編輯期間改了同一欄，會提示選擇版本。
敏感欄位與新選附件僅留在本次記憶體；私人文件上傳、保存同意與下載仍請由右上角開啟
Web 工作台。手機儲存草稿會保留既有附件引用，並顯示檔名；若要在手機匯出 PDF，
需重新選取檔案，或直接在 Web 匯出。使用者另行開啟的常用欄位裝置記憶是獨立選項。
這不是 Web 所有功能的完整替代版。

沒有 Firebase 的這份 APK 可以瀏覽、在後端更新後登入同步、使用本機日期提醒與 Widget。
Firebase 建立後要使用同一簽章重新建 APK，遠端推播才會啟用。

## Jerry 先更新後端

1. 將本分支 `codex/android-synced-preview` 的變更整合到要部署的分支；本交付不會自動合併 main。
2. 在 Jerry 的 `C:\uniway\app` 確認 Git remote 指向 `blizzard-new/abroad`，保留主機既有設定。
   先跑原有 `deploy/selfhost/scripts/update.ps1 -CheckOnly`，確認分支與工作目錄狀態。
3. 用原有部署程序更新該分支。`update.ps1` 先備份，`03-start.ps1` 執行 migration 及建置。
   這次新增 `20261024090000_mobile_push.sql`；不要跳過 migration。
4. 驗證 `/health` 仍正常，`/auth/mobile/config` 回應 enabled=true、pkce_method=S256。
   網頁 Google 登入應維持原行為。手機按 Google 登入後應回到 App，帳號 ID 與網站一致。
5. 手機收藏一間學校，在網頁重新整理確認；網頁改預算，回到手機確認；飛航模式修改後
   重開 App，再連線確認；兩端同時改相同預算應出現衝突選擇。
6. 電腦儲存一般表單草稿，手機開啟同一文件確認；手機改一欄並按儲存，電腦重開確認。
   離線儲存未填完的草稿後重開表單，內容應保留；兩邊同改一欄應提示選擇。
   登出後再次開啟表單不應看見上一帳號的答案或附件檔名。

正式站尚未更新時，手機登入會提示後端需要更新；這不能靠重新安裝 APK 解決。
本機端沒有 Jerry 主機的執行連線，因此不把本機測試當成正式站部署驗收。

## 建立 Firebase（可稍後完成）

1. 建立 Firebase 專案，新增 Android App，套件名填 `tw.uniway.app`。
   此處 Firebase 用於推播；Google 登入仍使用現有網站帳號。
2. 啟用 Firebase Cloud Messaging HTTP v1 API。建立只用於伺服器發送通知的服務帳號，
   授予發送 FCM 訊息的權限。服務帳號 JSON 存在 Jerry 的 repo 之外，例如
   `C:\uniway\secrets\firebase-service-account.json`，限制主機檔案讀取權限。
3. 在 `deploy/selfhost/.env` 增加 `FIREBASE_PROJECT_ID` 與
   `FIREBASE_SERVICE_ACCOUNT_FILE=C:/uniway/secrets/firebase-service-account.json`。
   不要把服務帳號 JSON、私鑰或 server credential 加進 APK、Git 或聊天。
4. 套用附帶的 optional overlay：

   ```powershell
   cd C:\uniway\app\deploy\selfhost
   docker compose --env-file .env -f docker-compose.yml -f docker-compose.mobile-push.example.yml up -d --no-deps app
   ```

   原有更新腳本只載入主 compose；每次更新後再套用此 overlay。
5. 在 Flutter 建置機建立 repo 外的 `firebase-public-config.json`，只填 Firebase Android
   App 的公開 client 設定（取自 Firebase project settings / google-services.json）：

   ```json
   {
     "FIREBASE_PROJECT_ID": "your-project-id",
     "FIREBASE_APP_ID": "1:sender:android:app-id",
     "FIREBASE_API_KEY": "your-android-client-api-key",
     "FIREBASE_SENDER_ID": "your-project-number"
   }
   ```

6. 用同一份簽章執行 `scripts/build-android-preview.ps1 -SigningDirectory <簽章資料夾>
   -FirebaseConfig <公開設定 JSON> -BuildDirectory <英文路徑>`。
   手機直接安裝更新，不要換簽章或套件名稱。
   腳本同時產生 Dart 設定與 Android 原生 Firebase resources，供 App 未開啟時初始化；
   只傳 `--dart-define` 而略過這份腳本不足以設定背景推播。
7. App 登入後在「通知與提醒」開啟提醒。Firebase 17 使用 `onRegistered` / `register()`
   提供的 FID；後端 HTTP v1 使用 `message.fid`，不要混用舊的 token API。

## 讓伺服器定期發送

先在 Jerry 主機手動執行一次（使用已套用 overlay 的 app 容器）：

```powershell
cd C:\uniway\app\deploy\selfhost
docker compose --env-file .env -f docker-compose.yml exec -T app python -m exchange_info.mobile_push_worker
```

成功後，以 Windows 工作排程器每 5 分鐘執行上述命令，工作目錄同上。
使用能操作 Docker 的主機帳號，設定前一次仍執行時不要重疊。
此程序只處理既有的已發布規定更新，不抓取或查核學校來源。
也可由已登入的內容管理員呼叫 `POST /admin/mobile-push/run-due`。

遠端推播只送與帳號計畫相關的規定更新，排除已讀、刪除、裝置註冊前及超過一天的通知。
日期提醒由手機排程，避免同一個期限收到本機與遠端兩則提醒。
資料庫以每則通知／裝置 claim 防止平行 worker 重複發送；失敗 5 分鐘後重試，最多 5 次。
FCM 成功後程序中斷仍可能重送，手機以相同通知 ID 更新同一則通知。
失效裝置會移除，刪帳號由資料庫外鍵連帶移除裝置及紀錄。

## 手機驗收

- 在通知畫面按「傳送一則測試通知」，確認系統通知顯示並點回時程頁。
- 儲存明確日期及提前提醒天數；本機於提醒日當地時間早上 9 點排程，Android 省電可能延後。
- 主畫面長按加入 UniWay「交換計畫」，調成窄／寬版；寬版顯示待辦，點擊回首頁。
  Widget 顯示最近一次同步快照與日期，開啟 App 才刷新雲端；不宣稱背景即時同步。
- 登出後 Widget 與本機排程清空，其他帳號不顯示前一位的內容。
- Firebase 設定後分別測前景、背景、關閉 App，以及登出後接收舊訊息。
  Android 強制停止 App 或部分品牌省電限制可能阻止背景推播，需要重新開啟 App。

## 重建與簽章

這台建置機的測試簽章存於 `%USERPROFILE%\.codex\private\uniway-android-preview`。
`password.dpapi` 只能由目前 Windows 使用者解密；移機前應以安全方式匯出密碼並備份
`uniway-preview.p12`。簽章不能遺失，否則既有安裝無法直接更新。
建置腳本不輸出密碼，release 禁止使用 debug 簽章。`output/android/SHA256SUMS.txt`
可用來確認 APK 傳輸完整性。iOS 尚未建置或驗證。

參考：[Firebase Flutter 註冊](https://firebase.google.com/docs/cloud-messaging/flutter/get-started)、
[HTTP v1 message schema](https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages)、
[背景訊息](https://firebase.google.com/docs/cloud-messaging/flutter/receive-messages)。
原生初始化參考：[Firebase Android resources](https://firebase.google.com/docs/projects/multiprojects)。
