package tw.uniway.office

import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
import android.os.Bundle
import android.provider.Settings
import android.text.InputType
import android.view.ViewGroup
import android.view.WindowInsets
import android.widget.Button
import android.widget.CheckBox
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.os.Build
import android.webkit.CookieManager
import kotlin.concurrent.thread

/** Where the office is and the password for it, plus whether to watch it in the background. */
class SettingsActivity : Activity() {
    private lateinit var prefs: Prefs
    private lateinit var url: EditText
    private lateinit var token: EditText
    private lateinit var notify: CheckBox
    private lateinit var result: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        prefs = Prefs(this)
        val column = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(20), dp(20), dp(20), dp(28))
        }
        fun text(value: String, size: Float = 15f, color: Int = Color.DKGRAY, top: Int = 12) = TextView(this).apply {
            text = value
            textSize = size
            setTextColor(color)
            setPadding(0, dp(top), 0, 0)
        }

        column.addView(text("UniWay 辦公室", 24f, Color.BLACK, 0))
        column.addView(text("這支手機要連到辦公室電腦上的 uv run office serve。手機和電腦要在同一個網路，或兩邊都裝 Tailscale（在外面也連得到）。"))

        column.addView(text("辦公室網址", 16f, Color.BLACK, 20))
        url = EditText(this).apply {
            hint = "例如 http://100.101.102.103:8780"
            inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_URI
            setSingleLine()
            setText(prefs.url)
        }
        column.addView(url)
        column.addView(text("電腦開辦公室時要用 uv run office serve --host 0.0.0.0，它會印出可以填的網址。", 13f))

        column.addView(text("通行碼", 16f, Color.BLACK, 20))
        token = EditText(this).apply {
            hint = "和電腦 .env 的 OFFICE_ACCESS_TOKEN 一樣"
            inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_PASSWORD
            setSingleLine()
            setText(prefs.token)
        }
        column.addView(token)
        column.addView(CheckBox(this).apply {
            text = "顯示通行碼"
            setOnCheckedChangeListener { _, shown ->
                val cursor = token.selectionEnd
                token.inputType = InputType.TYPE_CLASS_TEXT or if (shown) InputType.TYPE_TEXT_VARIATION_VISIBLE_PASSWORD else InputType.TYPE_TEXT_VARIATION_PASSWORD
                token.setSelection(cursor.coerceIn(0, token.text.length))
            }
        })
        column.addView(text("沒有通行碼？在電腦執行 uv run office token 產生一串，填進 .env 後重開辦公室。通行碼只存在這支手機裡。", 13f))

        notify = CheckBox(this).apply {
            text = "背景監看，有新草稿、發文結果、Leo 的訊息就通知"
            isChecked = prefs.notify
        }
        column.addView(notify, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply { topMargin = dp(20) })
        column.addView(Button(this).apply {
            text = "電池設定：讓系統不要把通知關掉"
            setOnClickListener {
                startActivity(Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS))
            }
        })
        column.addView(text("手機會為了省電把背景程式停掉。在清單裡找到「UniWay 辦公室」，選「不最佳化」或「不受限制」，通知才會及時。", 13f))

        column.addView(Button(this).apply {
            text = "測試連線"
            setOnClickListener { test() }
        }, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply { topMargin = dp(20) })
        result = text("", 15f, Color.BLACK, 6)
        column.addView(result)

        column.addView(Button(this).apply {
            text = "儲存並開啟辦公室"
            setOnClickListener { save() }
        }, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply { topMargin = dp(12) })
        column.addView(text("版本 ${version()}", 12f, Color.GRAY, 20))

        val scroll = ScrollView(this).apply {
            isFillViewport = true
            addView(column)
            setOnApplyWindowInsetsListener { view, insets ->
                if (Build.VERSION.SDK_INT >= 30) {
                    val bars = insets.getInsets(WindowInsets.Type.systemBars() or WindowInsets.Type.ime())
                    view.setPadding(bars.left, bars.top, bars.right, bars.bottom)
                } else {
                    @Suppress("DEPRECATION")
                    view.setPadding(insets.systemWindowInsetLeft, insets.systemWindowInsetTop, insets.systemWindowInsetRight, insets.systemWindowInsetBottom)
                }
                insets
            }
        }
        setContentView(scroll)
    }

    /** The address and password as typed, or null with the reason on screen. */
    private fun entered(): Pair<String, String>? {
        val address = Address.normalize(url.text.toString())
        if (address == null) {
            result.text = "❌ 網址看不懂。請填像 http://192.168.1.5:8780 這樣的辦公室網址。"
            return null
        }
        val secret = token.text.toString().trim()
        if (!Address.validToken(secret)) {
            result.text = "❌ 通行碼只能用英文字母、數字和符號，不能有中文或空白。"
            return null
        }
        return address to secret
    }

    private fun warning(address: String, secret: String): String =
        (if (!Address.isPrivate(address)) "\n⚠️ 這個網址沒有加密，路上的人看得到通行碼和內容。外面連線請用 Tailscale 或 https。" else "") +
            (if (secret.isEmpty()) "\n⚠️ 沒有通行碼：同一個網路的人都能按核准。" else "")

    private fun test() {
        val (address, secret) = entered() ?: return
        result.text = "連線中…"
        thread(name = "office-test") {
            val message = try {
                val feed = Office.feed(address, secret, null)
                "✅ 連上了。目前有 ${feed.waiting} 則等你審核。" + warning(address, secret)
            } catch (error: OfficeError) {
                "❌ ${error.message}"
            } catch (error: Exception) {
                "❌ 這個網址不是辦公室，或回應看不懂。"
            }
            runOnUiThread { result.text = message }
        }
    }

    private fun save() {
        val (address, secret) = entered() ?: return
        if (address != prefs.url || secret != prefs.token) {
            prefs.forgetProgress() // another office: what was shown before no longer applies
            CookieManager.getInstance().removeAllCookies(null)
        }
        prefs.url = address
        prefs.token = secret
        prefs.notify = notify.isChecked
        if (notify.isChecked) WatchService.ensure(this) else WatchService.stop(this)
        startActivity(Intent(this, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP))
        finish()
    }

    private fun dp(value: Int) = (value * resources.displayMetrics.density).toInt()

    private fun version(): String = try {
        packageManager.getPackageInfo(packageName, 0).versionName ?: ""
    } catch (error: PackageManager.NameNotFoundException) {
        ""
    }
}
