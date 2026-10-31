package tw.uniway.office

import org.json.JSONObject
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL

/** Why the office could not be asked, in words the boss can act on. */
sealed class OfficeError(message: String) : Exception(message) {
    class Auth : OfficeError("通行碼不對：要和辦公室電腦 .env 的 OFFICE_ACCESS_TOKEN 一模一樣")
    class Locked(message: String) : OfficeError(message)
    class Unreachable(message: String) : OfficeError(message)
    class Server(message: String) : OfficeError(message)
}

/** The phone's one conversation with the office: plain HTTP, the token in an Authorization header. */
object Office {
    fun get(base: String, token: String, path: String, timeoutMs: Int = 20_000): String {
        val connection = try {
            URL(base + path).openConnection() as HttpURLConnection
        } catch (error: IOException) {
            throw OfficeError.Unreachable("網址不對：$base")
        }
        try {
            connection.connectTimeout = 8_000
            connection.readTimeout = timeoutMs
            connection.setRequestProperty("Accept", "application/json")
            if (token.isNotEmpty()) connection.setRequestProperty("Authorization", "Bearer $token")
            val code = connection.responseCode
            val stream = if (code in 200..299) connection.inputStream else connection.errorStream
            val body = stream?.bufferedReader(Charsets.UTF_8)?.use { it.readText() } ?: ""
            return when (code) {
                in 200..299 -> body
                401 -> throw OfficeError.Auth()
                429 -> throw OfficeError.Locked(detail(body) ?: "錯太多次，暫時被鎖住了，過幾分鐘再試")
                else -> throw OfficeError.Server("辦公室回應 HTTP $code")
            }
        } catch (error: OfficeError) {
            throw error
        } catch (error: IOException) {
            throw OfficeError.Unreachable("連不上 $base（${error.javaClass.simpleName}）")
        } finally {
            connection.disconnect()
        }
    }

    fun feed(base: String, token: String, chatAfter: Long?): Feed =
        try {
            Feed.parse(get(base, token, "/api/mobile/feed" + (if (chatAfter != null) "?chat_after=$chatAfter" else "")))
        } catch (error: org.json.JSONException) {
            throw OfficeError.Server("這個網址不是辦公室（回應看不懂）")
        }

    private fun detail(body: String): String? = try {
        JSONObject(body).optString("detail").ifEmpty { null }
    } catch (error: org.json.JSONException) {
        null
    }
}
