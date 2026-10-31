package tw.uniway.office

import org.junit.Assert.assertTrue
import org.junit.Assume.assumeNotNull
import org.junit.Before
import org.junit.Test

/**
 * The phone's client against a real, running office. Skipped unless OFFICE_E2E_URL is set:
 *
 *     OFFICE_E2E_URL=http://127.0.0.1:8780 OFFICE_E2E_TOKEN=<its OFFICE_ACCESS_TOKEN> ./gradlew testDebugUnitTest
 */
class ServerEndToEndTest {
    private val url: String? = System.getenv("OFFICE_E2E_URL")
    private val token: String = System.getenv("OFFICE_E2E_TOKEN") ?: ""

    @Before
    fun onlyWithAnOffice() = assumeNotNull(url)

    @Test
    fun theFeedComesBackInTheShapeThePhoneReads() {
        val feed = Office.feed(url!!, token, null)
        assertTrue(feed.waiting >= 0 && feed.chatLast >= 0)
        feed.drafts.forEach { assertTrue(it.title.contains("#${it.id}")) }
    }

    @Test
    fun theFirstLookAndTheNextOne_agreeOnWhereTheChatIs() {
        val first = Office.feed(url!!, token, null)
        val next = Office.feed(url, token, first.chatLast)
        assertTrue(next.chat.isEmpty() && next.chatLast == first.chatLast)
    }

    @Test
    fun aWrongPassword_isRefused_whenTheOfficeHasOne() {
        if (token.isEmpty()) return // an office with no password lets everyone in
        val error = runCatching { Office.get(url!!, "definitely-not-it", "/api/mobile/feed") }.exceptionOrNull()
        assertTrue(error is OfficeError.Auth)
    }

    @Test
    fun thePhonePageIsServed() {
        assertTrue(Office.get(url!!, token, "/m").contains("總管 Leo"))
    }
}
