package tw.uniway.office

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class PlannerTest {
    private fun item(id: Long, status: String) = Item(id, status, "title $id", "text $id")
    private fun feed(vararg drafts: Item, chat: List<Chat> = emptyList()) =
        Feed(waiting = drafts.count { it.waiting }, chatLast = 9, chat = chat, drafts = drafts.toList())

    @Test
    fun theFirstLook_showsOnlyWhatIsWaiting_andStaysQuietAboutOldNews() {
        val plan = Planner.plan(feed(item(1, "pending_approval"), item(2, "published"), item(3, "failed")), emptySet(), firstRun = true)
        assertEquals(listOf(1L), plan.show.map { it.id })
        assertEquals(setOf("1:pending_approval", "2:published", "3:failed"), plan.seen)
        assertTrue(plan.chat.isEmpty())
    }

    @Test
    fun aDraftIsShownOncePerStatus() {
        val seen = setOf("1:pending_approval")
        assertTrue(Planner.plan(feed(item(1, "pending_approval")), seen, firstRun = false).show.isEmpty())
        val moved = Planner.plan(feed(item(1, "published")), seen, firstRun = false)
        assertEquals(listOf("1:published"), moved.show.map { it.key }) // it went out: a new notice for the same draft
    }

    @Test
    fun aDraftThatStoppedWaiting_hasItsNotificationTakenDown() {
        val seen = setOf("1:pending_approval", "2:needs_changes", "3:pending_approval")
        val plan = Planner.plan(feed(item(3, "pending_approval")), seen, firstRun = false) // 1 and 2 were handled elsewhere
        assertEquals(setOf(1L, 2L), plan.cancel.toSet())
        assertEquals(setOf("3:pending_approval"), plan.seen)
    }

    @Test
    fun leosMessagesComeThrough_exceptOnTheFirstLook() {
        val messages = listOf(Chat(5, "開工了"))
        assertEquals(messages, Planner.plan(feed(chat = messages), emptySet(), firstRun = false).chat)
        assertTrue(Planner.plan(feed(chat = messages), emptySet(), firstRun = true).chat.isEmpty())
    }

    @Test
    fun theFeedTheOfficeSends_isReadAsIs() {
        val json = """{"now":"2026-10-31T00:00:00+00:00","waiting":1,"chat_last":12,
            "chat":[{"id":12,"text":"3 則等你審","ts":"x"}],
            "drafts":[{"id":4,"status":"pending_approval","title":"📝 等你核准 #4｜Threads 貼文","text":"內文","scheduled_at":null,"updated_at":"x"}]}"""
        val feed = Feed.parse(json)
        assertEquals(1, feed.waiting)
        assertEquals(12L, feed.chatLast)
        assertEquals(listOf(Chat(12, "3 則等你審")), feed.chat)
        assertEquals(Item(4, "pending_approval", "📝 等你核准 #4｜Threads 貼文", "內文"), feed.drafts.single())
        assertTrue(feed.drafts.single().waiting)
    }

    @Test
    fun anEmptyOffice_isAnEmptyFeed() {
        val feed = Feed.parse("""{"waiting":0,"chat_last":0,"chat":[],"drafts":[]}""")
        assertTrue(feed.drafts.isEmpty() && feed.chat.isEmpty())
    }
}
