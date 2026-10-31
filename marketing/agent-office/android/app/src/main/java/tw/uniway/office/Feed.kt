package tw.uniway.office

import org.json.JSONObject

/** One draft that needs a notification: what waits for the boss, or what just went out or failed. */
data class Item(val id: Long, val status: String, val title: String, val text: String) {
    val key get() = "$id:$status"
    val waiting get() = status in WAITING
}

data class Chat(val id: Long, val text: String)

/** The office's answer to "what is new?" (GET /api/mobile/feed). */
data class Feed(val waiting: Int, val chatLast: Long, val chat: List<Chat>, val drafts: List<Item>) {
    companion object {
        fun parse(json: String): Feed {
            val root = JSONObject(json)
            val drafts = root.optJSONArray("drafts")
            val chat = root.optJSONArray("chat")
            return Feed(
                waiting = root.optInt("waiting"),
                chatLast = root.optLong("chat_last"),
                chat = (0 until (chat?.length() ?: 0)).map {
                    val m = chat!!.getJSONObject(it)
                    Chat(m.getLong("id"), m.optString("text"))
                },
                drafts = (0 until (drafts?.length() ?: 0)).map {
                    val d = drafts!!.getJSONObject(it)
                    Item(d.getLong("id"), d.getString("status"), d.optString("title"), d.optString("text"))
                },
            )
        }
    }
}

val WAITING = setOf("pending_approval", "needs_changes")

/** What to do with one answer from the office, given what the phone already showed. */
data class Plan(val show: List<Item>, val cancel: List<Long>, val chat: List<Chat>, val seen: Set<String>)

object Planner {
    /**
     * `seen` holds "id:status" for every draft shown last time. A draft is shown once per status; one that stopped
     * waiting (approved on the web, say) has its notification taken down. The first time ever, only what is waiting is
     * shown, so installing the app does not bury the phone in yesterday's results.
     */
    fun plan(feed: Feed, seen: Set<String>, firstRun: Boolean): Plan {
        val current = feed.drafts.map { it.key }.toSet()
        val stillWaiting = feed.drafts.filter { it.waiting }.map { it.id }.toSet()
        val wasWaiting = seen.filter { key -> WAITING.any { key.endsWith(":$it") } }.mapNotNull { it.substringBefore(':').toLongOrNull() }
        return Plan(
            show = feed.drafts.filter { it.key !in seen && (!firstRun || it.waiting) },
            cancel = wasWaiting.filter { it !in stillWaiting }.distinct(),
            chat = if (firstRun) emptyList() else feed.chat,
            seen = current,
        )
    }
}
