package tw.uniway.office

import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder

/**
 * Looks at the office every half minute while the app is closed and turns what is new into notifications: a draft
 * waiting for the boss, a post that went out or failed, something Leo said. It runs as a foreground service (Android
 * shows its small "監看中" notification), the way a phone keeps a connection alive without Google's push service.
 */
class WatchService : Service() {
    private var worker: Thread? = null

    @Volatile
    private var running = false

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        Notifier.channels(this)
        val note = Notifier.watching(this, "連線中…")
        if (Build.VERSION.SDK_INT >= 34) {
            startForeground(Notifier.WATCH_ID, note, FOREGROUND_SERVICE_TYPE_SPECIAL_USE)
        } else {
            startForeground(Notifier.WATCH_ID, note)
        }
        if (!running) {
            running = true
            worker = Thread({ loop() }, "office-watch").also {
                it.isDaemon = true
                it.start()
            }
        }
        return START_STICKY
    }

    override fun onDestroy() {
        running = false
        worker?.interrupt()
        super.onDestroy()
    }

    private fun loop() {
        var failures = 0
        while (running) {
            val prefs = Prefs(this)
            if (!prefs.notify || !prefs.configured) {
                stopSelf()
                return
            }
            try {
                look(prefs)
                failures = 0
            } catch (error: OfficeError.Auth) {
                Notifier.problem(this, error.message ?: "通行碼不對")
                stopSelf()
                return
            } catch (error: OfficeError) {
                failures++
                Notifier.update(this, "連不上辦公室，稍後重試")
            } catch (error: Exception) {
                failures++
                Notifier.update(this, "辦公室的回應看不懂，稍後重試")
            }
            // After failures wait longer each time (1, 2, 4 minutes, at most 5) instead of hammering a computer that is off.
            val wait = if (failures == 0) POLL_MS else minOf(POLL_MS shl minOf(failures, 4), MAX_WAIT_MS)
            try {
                Thread.sleep(wait)
            } catch (error: InterruptedException) {
                return
            }
        }
    }

    private fun look(prefs: Prefs) {
        val first = prefs.chatLast < 0
        val feed = Office.feed(prefs.url, prefs.token, if (first) null else prefs.chatLast)
        val plan = Planner.plan(feed, prefs.seen, first)
        plan.cancel.forEach { Notifier.cancel(this, it) }
        if (!AppState.foreground) {
            plan.show.forEach { Notifier.show(this, it) }
            plan.chat.forEach { Notifier.chat(this, it) }
        }
        prefs.seen = plan.seen
        prefs.chatLast = feed.chatLast
        Notifier.update(this, if (feed.waiting > 0) "連線正常｜${feed.waiting} 則等你審核" else "連線正常｜沒有等你審核的內容")
    }

    companion object {
        private const val POLL_MS = 30_000L
        private const val MAX_WAIT_MS = 300_000L
        private const val FOREGROUND_SERVICE_TYPE_SPECIAL_USE = 0x40000000 // ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE

        /** Starts the watcher (when notifications are on and an office is set) from a screen or a boot broadcast. */
        fun ensure(context: Context) {
            val prefs = Prefs(context)
            if (!prefs.notify || !prefs.configured) return
            try {
                context.startForegroundService(Intent(context, WatchService::class.java))
            } catch (error: Exception) {
                // Android may refuse a background start (a phone with strict battery rules); opening the app starts it again.
            }
        }

        fun stop(context: Context) {
            context.stopService(Intent(context, WatchService::class.java))
        }
    }
}
