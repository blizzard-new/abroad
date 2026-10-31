package tw.uniway.office

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class AddressTest {
    @Test
    fun anAddressWithoutAScheme_getsHttp_andLosesAnythingAfterThePort() {
        assertEquals("http://192.168.1.5:8780", Address.normalize(" 192.168.1.5:8780/ "))
        assertEquals("http://100.101.102.103:8780", Address.normalize("100.101.102.103:8780/m?token=x"))
        assertEquals("https://office.example.com", Address.normalize("https://office.example.com/"))
        assertEquals("http://my-pc.tail1234.ts.net:8780", Address.normalize("my-pc.tail1234.ts.net:8780"))
    }

    @Test
    fun somethingThatIsNotAnOfficeAddress_isRefused() {
        assertNull(Address.normalize(""))
        assertNull(Address.normalize("   "))
        assertNull(Address.normalize("ftp://192.168.1.5"))
        assertNull(Address.normalize("http://"))
        assertNull(Address.normalize("not a url at all"))
    }

    @Test
    fun theTokenTravelsInAHeader_soOnlyVisibleAsciiIsAccepted() {
        assertTrue(Address.validToken(""))
        assertTrue(Address.validToken("Ab3-_xYz9~"))
        assertFalse(Address.validToken("has space"))
        assertFalse(Address.validToken("通行碼"))
        assertFalse(Address.validToken("line\nbreak"))
    }

    @Test
    fun plainHttpIsFineOnlyInsideAPrivateNetworkOrTailscale() {
        listOf(
            "http://192.168.1.5:8780", "http://10.0.0.7:8780", "http://172.20.1.1:1", "http://100.101.1.1:8780",
            "http://localhost:8780", "http://my-pc.local:8780", "http://my-pc.tail1234.ts.net:8780", "http://my-pc:8780",
            "https://office.example.com",
        ).forEach { assertTrue(it, Address.isPrivate(it)) }
        listOf("http://8.8.8.8:8780", "http://office.example.com", "http://172.32.0.1", "http://100.128.0.1", "http://192.169.1.1")
            .forEach { assertFalse(it, Address.isPrivate(it)) }
    }

    @Test
    fun sameOrigin_comparesSchemeHostAndPort() {
        assertTrue(Address.sameOrigin("http://192.168.1.5:8780", "http://192.168.1.5:8780/media/x.png"))
        assertFalse(Address.sameOrigin("http://192.168.1.5:8780", "http://192.168.1.5:9000/"))
        assertFalse(Address.sameOrigin("http://192.168.1.5:8780", "https://www.threads.com/@uniway.tw"))
        assertTrue(Address.sameOrigin("https://office.example.com", "https://office.example.com:443/m"))
    }
}
