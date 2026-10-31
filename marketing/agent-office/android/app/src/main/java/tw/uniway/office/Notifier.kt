package tw.uniway.office

import android.Manifest
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build

object Notifier {
    const val WATCH_ID = 1
    private const val PROBLEM_ID = 2
    private const val CHAT_BASE = 1_000_000
    private const val CH_WAIT = "waiting"
    private const val CH_RESULT = "results"
    private const val CH_CHAT = "chat"
    private const val CH_WATCH = "watch"

    fun channels(context: Context) {
        val manager = context.getSystemService(NotificationManager::class.java)
        manager.createNotificationChannels(
            listOf(
                NotificationChannel(CH_WAIT, "等你核准的草稿", NotificationManager.IMPORTANCE_HIGH).apply {
                    description = "新草稿等你核准、需要你看一下、發佈失敗"
                },
                NotificationChannel(CH_RESULT, "發文結果", NotificationManager.IMPORTANCE_DEFAULT).apply {
                    description = "貼文發出去了"
                },
                NotificationChannel(CH_CHAT, "Leo 的訊息", NotificationManager.IMPORTANCE_DEFAULT),
                NotificationChannel(CH_WATCH, "背景監看", NotificationManager.IMPORTANCE_MIN).apply {
                    description = "App 在背景定時看辦公室有沒有新東西時顯示的常駐通知"
                    setShowBadge(false)
                },
            ),
        )
    }

    /** The always-on notification a background service must show. */
    fun watching(context: Context, text: String): Notification =
        Notification.Builder(context, CH_WATCH)
            .setSmallIcon(R.drawable.ic_stat)
            .setContentTitle("UniWay 辦公室")
            .setContentText(text)
            .setOngoing(true)
            .setContentIntent(open(context, null))
            .build()

    fun update(context: Context, text: String) = notify(context, WATCH_ID, watching(context, text))

    fun show(context: Context, item: Item) {
        val channel = if (item.waiting || item.status == "failed") CH_WAIT else CH_RESULT
        notify(context, item.id.toInt(), build(context, channel, item.title, item.text, open(context, item.id)))
    }

    fun chat(context: Context, message: Chat) =
        notify(context, CHAT_BASE + (message.id % CHAT_BASE).toInt(), build(context, CH_CHAT, "Leo", message.text, open(context, null)))

    fun problem(context: Context, text: String) =
        notify(context, PROBLEM_ID, build(context, CH_WAIT, "UniWay 辦公室連不上", text, open(context, null)))

    fun cancel(context: Context, draftId: Long) = context.getSystemService(NotificationManager::class.java).cancel(draftId.toInt())

    private fun build(context: Context, channel: String, title: String, text: String, tap: PendingIntent): Notification =
        Notification.Builder(context, channel)
            .setSmallIcon(R.drawable.ic_stat)
            .setContentTitle(title)
            .setContentText(text.lineSequence().firstOrNull { it.isNotBlank() } ?: text)
            .setStyle(Notification.BigTextStyle().bigText(text))
            .setContentIntent(tap)
            .setAutoCancel(true)
            .build()

    private fun notify(context: Context, id: Int, notification: Notification) {
        // Without the permission (Android 13 and later) the system would drop it anyway; skipping keeps the logs quiet.
        if (Build.VERSION.SDK_INT >= 33 && context.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) return
        context.getSystemService(NotificationManager::class.java).notify(id, notification)
    }

    /** Tapping a notification opens the app, on that draft when it is about one. */
    private fun open(context: Context, draftId: Long?): PendingIntent {
        val intent = Intent(context, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP
            if (draftId != null) putExtra(MainActivity.EXTRA_DRAFT, draftId)
        }
        return PendingIntent.getActivity(context, (draftId ?: 0L).toInt(), intent, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
    }
}
