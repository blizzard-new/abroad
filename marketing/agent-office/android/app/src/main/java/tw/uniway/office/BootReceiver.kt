package tw.uniway.office

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent

/** After the phone restarts or the app is updated, start watching the office again without waiting for the boss to open the app. */
class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Intent.ACTION_BOOT_COMPLETED || intent.action == Intent.ACTION_MY_PACKAGE_REPLACED) {
            WatchService.ensure(context)
        }
    }
}
