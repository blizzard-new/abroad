package tw.uniway.office

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * `feed.json` is a real answer from the office (tests/test_mobile.py checks the Python side produces these fields), so
 * if either side renames one, one of the two test suites fails instead of the phone silently showing nothing.
 */
class FeedContractTest {
    private val feed = Feed.parse(javaClass.getResource("/feed.json")!!.readText(Charsets.UTF_8))

    @Test
    fun theOfficesOwnAnswer_isReadCompletely() {
        assertEquals(2, feed.waiting)
        assertEquals(2L, feed.chatLast)
        assertEquals(listOf(Chat(2, "今天排了 4 則，3 則等你審。")), feed.chat)
        assertEquals(listOf(4L, 3L, 2L), feed.drafts.map { it.id })
        assertEquals(listOf("failed", "pending_approval", "pending_approval"), feed.drafts.map { it.status })
        assertTrue(feed.drafts.all { it.title.contains("#${it.id}") && it.text.isNotEmpty() })
    }

    @Test
    fun whatWaitsIsShown_andTheFailureToo_onTheFirstLook() {
        val first = Planner.plan(feed, emptySet(), firstRun = true)
        assertEquals(listOf(3L, 2L), first.show.map { it.id }) // waiting only: the failure is old news on a fresh install
        val later = Planner.plan(feed, emptySet(), firstRun = false)
        assertEquals(listOf(4L, 3L, 2L), later.show.map { it.id })
    }
}
