package tw.uniway.office

import java.net.URI

/** What the boss types into the settings screen, made safe to use. No Android classes, so it is easy to test. */
object Address {
    /** "192.168.1.5:8780" becomes "http://192.168.1.5:8780"; anything that is not an http(s) address with a host gives null. */
    fun normalize(input: String): String? {
        var text = input.trim()
        if (text.isEmpty()) return null
        if (!text.contains("://")) text = "http://$text"
        val uri = try {
            URI(text)
        } catch (error: Exception) {
            return null
        }
        val scheme = uri.scheme?.lowercase()
        val host = uri.host
        if ((scheme != "http" && scheme != "https") || host.isNullOrEmpty()) return null
        val port = if (uri.port == -1) "" else ":${uri.port}"
        return "$scheme://$host$port"
    }

    /** The token travels in an HTTP header, which carries only visible ASCII without spaces. Empty is allowed (an office with no token). */
    fun validToken(token: String): Boolean = token.all { it.code in 33..126 }

    /**
     * Whether traffic to this address is already protected or stays inside a private network: https, a home or office
     * network, Tailscale (its own encrypted tunnel), or the computer itself. Plain http to anything else is open to
     * everyone on the way, and the settings screen says so.
     */
    fun isPrivate(url: String): Boolean {
        if (url.startsWith("https://")) return true
        val host = try {
            URI(url).host
        } catch (error: Exception) {
            null
        } ?: return false
        if (host == "localhost" || host.endsWith(".local") || host.endsWith(".ts.net") || !host.contains('.')) return true
        val parts = host.split('.').map { it.toIntOrNull() }
        if (parts.size != 4 || parts.any { it == null }) return false
        val a = parts[0]!!
        val b = parts[1]!!
        return a == 10 || a == 127 || (a == 192 && b == 168) || (a == 172 && b in 16..31) || (a == 100 && b in 64..127)
    }

    fun sameOrigin(base: String, other: String): Boolean = try {
        val x = URI(base)
        val y = URI(other)
        x.scheme.equals(y.scheme, true) && x.host.equals(y.host, true) && port(x) == port(y)
    } catch (error: Exception) {
        false
    }

    private fun port(uri: URI): Int = if (uri.port != -1) uri.port else if (uri.scheme.equals("https", true)) 443 else 80
}
