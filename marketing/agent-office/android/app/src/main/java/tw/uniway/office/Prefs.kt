package tw.uniway.office

import android.content.Context

/** What the phone remembers: where the office is, the password, and which notifications it already showed. */
class Prefs(context: Context) {
    private val store = context.applicationContext.getSharedPreferences("office", Context.MODE_PRIVATE)

    var url: String
        get() = store.getString("url", "") ?: ""
        set(value) = store.edit().putString("url", value).apply()

    var token: String
        get() = store.getString("token", "") ?: ""
        set(value) = store.edit().putString("token", value).apply()

    var notify: Boolean
        get() = store.getBoolean("notify", true)
        set(value) = store.edit().putBoolean("notify", value).apply()

    /** Newest chat id already handled; -1 until the first successful look at the office. */
    var chatLast: Long
        get() = store.getLong("chat_last", -1L)
        set(value) = store.edit().putLong("chat_last", value).apply()

    var seen: Set<String>
        get() = HashSet(store.getStringSet("seen", emptySet()) ?: emptySet())
        set(value) = store.edit().putStringSet("seen", HashSet(value)).apply()

    val configured get() = url.isNotEmpty()

    /** A different office (or password) means nothing shown before applies any more. */
    fun forgetProgress() = store.edit().remove("chat_last").remove("seen").apply()
}

object AppState {
    /** True while the app's window is on screen; the watcher then leaves notifications to the screen itself. */
    @Volatile
    var foreground = false
}
