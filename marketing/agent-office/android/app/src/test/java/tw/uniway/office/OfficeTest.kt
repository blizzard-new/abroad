package tw.uniway.office

import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import java.net.InetAddress
import java.net.ServerSocket
import kotlin.concurrent.thread

/** The phone's HTTP code against a stand-in for the office, so every way an answer can go wrong is checked. */
class OfficeTest {
    private lateinit var socket: ServerSocket
    private val seen = java.util.Collections.synchronizedList(mutableListOf<Pair<String, String?>>()) // path with query, Authorization header

    @Volatile
    private var status = 200

    @Volatile
    private var body = "{}"

    private val base get() = "http://127.0.0.1:${socket.localPort}"

    @Before
    fun start() {
        socket = ServerSocket(0, 10, InetAddress.getByName("127.0.0.1"))
        thread(isDaemon = true, name = "fake-office") {
            while (!socket.isClosed) {
                try {
                    socket.accept().use { client ->
                        val reader = client.getInputStream().bufferedReader(Charsets.UTF_8)
                        val path = reader.readLine().split(" ")[1]
                        var auth: String? = null
                        while (true) {
                            val line = reader.readLine() ?: break
                            if (line.isEmpty()) break
                            if (line.startsWith("Authorization:", ignoreCase = true)) auth = line.substringAfter(":").trim()
                        }
                        seen += path to auth
                        val bytes = body.toByteArray(Charsets.UTF_8)
                        val head = "HTTP/1.1 $status X\r\nContent-Type: application/json; charset=utf-8\r\nContent-Length: ${bytes.size}\r\nConnection: close\r\n\r\n"
                        client.getOutputStream().apply {
                            write(head.toByteArray(Charsets.UTF_8))
                            write(bytes)
                            flush()
                        }
                    }
                } catch (error: java.io.IOException) {
                    // the test is over and the socket closed under accept()
                }
            }
        }
    }

    @After
    fun stop() = socket.close()

    @Test
    fun theTokenGoesInABearerHeader_andIsLeftOutWhenThereIsNone() {
        Office.get(base, "secret-1", "/api/mobile/feed")
        Office.get(base, "", "/api/mobile/feed")
        assertEquals("Bearer secret-1", seen[0].second)
        assertNull(seen[1].second)
    }

    @Test
    fun aWrongPassword_isSaidPlainly() {
        status = 401
        body = """{"detail":"需要辦公室通行碼"}"""
        try {
            Office.get(base, "wrong", "/api/state")
            throw AssertionError("expected Auth")
        } catch (error: OfficeError.Auth) {
            assertTrue(error.message!!.contains("OFFICE_ACCESS_TOKEN"))
        }
    }

    @Test
    fun beingLockedOut_carriesTheOfficesOwnWords() {
        status = 429
        body = """{"detail":"錯誤太多次，請 15 分鐘後再試"}"""
        try {
            Office.get(base, "wrong", "/api/state")
            throw AssertionError("expected Locked")
        } catch (error: OfficeError.Locked) {
            assertEquals("錯誤太多次，請 15 分鐘後再試", error.message)
        }
    }

    @Test
    fun anOfficeThatIsOff_isUnreachable_andAnOddAnswerIsAServerProblem() {
        val dead = Office.runCatching { get("http://127.0.0.1:1", "t", "/api/state", 2_000) }.exceptionOrNull()
        assertTrue(dead is OfficeError.Unreachable)
        status = 500
        val broken = Office.runCatching { get(base, "t", "/api/state") }.exceptionOrNull()
        assertTrue(broken is OfficeError.Server && broken.message!!.contains("500"))
    }

    @Test
    fun theFeedAsksAfterTheNewestChatItHasSeen_andReadsWhatComesBack() {
        body = """{"waiting":0,"chat_last":3,"chat":[],"drafts":[]}"""
        Office.feed(base, "t", null)
        val feed = Office.feed(base, "t", 7)
        assertEquals("/api/mobile/feed", seen[0].first)
        assertEquals("/api/mobile/feed?chat_after=7", seen[1].first)
        assertEquals(3L, feed.chatLast)
    }

    @Test
    fun somethingThatIsNotTheOffice_isRecognisedByItsAnswer() {
        body = "<html>router login</html>"
        val error = Office.runCatching { feed(base, "t", null) }.exceptionOrNull()
        assertTrue(error is OfficeError.Server && error.message!!.contains("不是辦公室"))
    }
}
