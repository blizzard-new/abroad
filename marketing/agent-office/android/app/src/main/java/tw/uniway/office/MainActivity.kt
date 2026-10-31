package tw.uniway.office

import android.Manifest
import android.app.Activity
import android.content.ActivityNotFoundException
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.view.WindowInsets
import android.webkit.CookieManager
import android.webkit.JavascriptInterface
import android.webkit.WebChromeClient
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Button
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.TextView

/**
 * The office in a window: the phone page the office serves at /m (Leo's chat, the inbox, the schedule), signed in with
 * the password from the settings screen. Everything else (links to the posts, the sources) opens in the phone's browser.
 */
class MainActivity : Activity() {
    private lateinit var prefs: Prefs
    private lateinit var web: WebView
    private lateinit var bar: ProgressBar
    private lateinit var problem: LinearLayout
    private lateinit var problemText: TextView
    private var failed = false
    private var loadedFor = ""

    /** What the page can ask of the app (shown as "App 設定" in its menu). */
    inner class Bridge {
        @JavascriptInterface
        fun openSettings() {
            runOnUiThread { startActivity(Intent(this@MainActivity, SettingsActivity::class.java)) }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        prefs = Prefs(this)
        if (!prefs.configured) {
            startActivity(Intent(this, SettingsActivity::class.java))
            finish()
            return
        }
        buildScreen()
        if (Build.VERSION.SDK_INT >= 33 && prefs.notify && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 1)
        }
        load(intent)
    }

    private fun buildScreen() {
        val root = FrameLayout(this).apply { setBackgroundColor(NAVY) }
        root.setOnApplyWindowInsetsListener { view, insets ->
            // Android 15 draws apps edge to edge: keep the page out from under the status bar, the keyboard and the gesture bar.
            if (Build.VERSION.SDK_INT >= 30) {
                val bars = insets.getInsets(WindowInsets.Type.systemBars() or WindowInsets.Type.ime())
                view.setPadding(bars.left, bars.top, bars.right, bars.bottom)
            } else {
                @Suppress("DEPRECATION")
                view.setPadding(insets.systemWindowInsetLeft, insets.systemWindowInsetTop, insets.systemWindowInsetRight, insets.systemWindowInsetBottom)
            }
            insets
        }

        web = WebView(this).apply {
            settings.javaScriptEnabled = true
            settings.domStorageEnabled = true
            settings.setSupportZoom(false)
            settings.userAgentString = settings.userAgentString + " UniWayOffice/" + versionName()
            addJavascriptInterface(Bridge(), "UniWayApp")
            webViewClient = object : WebViewClient() {
                override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                    if (Address.sameOrigin(prefs.url, request.url.toString())) return false
                    try {
                        startActivity(Intent(Intent.ACTION_VIEW, request.url))
                    } catch (error: ActivityNotFoundException) {
                        // nothing on the phone opens this kind of link
                    }
                    return true
                }

                override fun onPageStarted(view: WebView, url: String, favicon: android.graphics.Bitmap?) {
                    failed = false
                    bar.visibility = View.VISIBLE
                }

                override fun onPageFinished(view: WebView, url: String) {
                    bar.visibility = View.GONE
                    if (!failed) problem.visibility = View.GONE
                }

                override fun onReceivedError(view: WebView, request: WebResourceRequest, error: WebResourceError) {
                    if (request.isForMainFrame) showProblem("連不上辦公室（${error.description}）\n\n確認辦公室電腦開著、`uv run office serve --host 0.0.0.0` 有在跑、手機和電腦在同一個網路（或兩邊都開 Tailscale）。")
                }

                override fun onReceivedHttpError(view: WebView, request: WebResourceRequest, response: WebResourceResponse) {
                    if (!request.isForMainFrame) return
                    when (response.statusCode) {
                        401 -> showProblem("通行碼不對。要和辦公室電腦 .env 的 OFFICE_ACCESS_TOKEN 一模一樣。")
                        429 -> showProblem("通行碼錯太多次，辦公室暫時鎖住這支手機，15 分鐘後再試。")
                        else -> showProblem("辦公室回應 HTTP ${response.statusCode}，這個網址可能不是辦公室。")
                    }
                }
            }
            webChromeClient = object : WebChromeClient() {
                override fun onProgressChanged(view: WebView, newProgress: Int) {
                    bar.progress = newProgress
                }
            }
        }
        root.addView(web, FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT))

        bar = ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal).apply {
            max = 100
            visibility = View.GONE
        }
        root.addView(bar, FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(4)))

        problemText = TextView(this).apply {
            textSize = 16f
            setTextColor(Color.WHITE)
            gravity = Gravity.CENTER
        }
        problem = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setBackgroundColor(NAVY)
            setPadding(dp(24), dp(24), dp(24), dp(24))
            visibility = View.GONE
            addView(problemText)
            addView(Button(context).apply {
                text = "重試"
                setOnClickListener { load(intent) }
            }, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply { topMargin = dp(20) })
            addView(Button(context).apply {
                text = "App 設定"
                setOnClickListener { startActivity(Intent(this@MainActivity, SettingsActivity::class.java)) }
            })
        }
        root.addView(problem, FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT))
        setContentView(root)
    }

    private fun load(from: Intent?) {
        val draft = from?.getLongExtra(EXTRA_DRAFT, 0L) ?: 0L
        failed = false
        problem.visibility = View.GONE
        loadedFor = prefs.url + "\n" + prefs.token
        val headers = if (prefs.token.isEmpty()) emptyMap() else mapOf("Authorization" to "Bearer ${prefs.token}")
        web.loadUrl("${prefs.url}/m" + if (draft > 0) "#draft-$draft" else "", headers)
    }

    private fun showProblem(text: String) {
        failed = true
        problemText.text = text
        problem.visibility = View.VISIBLE
        bar.visibility = View.GONE
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        val draft = intent.getLongExtra(EXTRA_DRAFT, 0L)
        if (draft > 0 && !failed && web.url != null) {
            web.evaluateJavascript("location.hash = '#draft-$draft'", null) // the page scrolls to that card
        } else {
            load(intent)
        }
    }

    override fun onResume() {
        super.onResume()
        AppState.foreground = true
        if (!::prefs.isInitialized || !prefs.configured) return
        if (loadedFor != prefs.url + "\n" + prefs.token) {
            // Back from the settings screen with a different office or password: start over with a clean sign-in.
            CookieManager.getInstance().removeAllCookies(null)
            load(null)
        }
        WatchService.ensure(this)
    }

    override fun onPause() {
        AppState.foreground = false
        super.onPause()
    }

    @Suppress("DEPRECATION", "OVERRIDE_DEPRECATION")
    override fun onBackPressed() {
        if (::web.isInitialized && web.canGoBack()) web.goBack() else super.onBackPressed()
    }

    override fun onDestroy() {
        if (::web.isInitialized) web.destroy()
        super.onDestroy()
    }

    private fun dp(value: Int) = (value * resources.displayMetrics.density).toInt()

    private fun versionName(): String = try {
        packageManager.getPackageInfo(packageName, 0).versionName ?: ""
    } catch (error: PackageManager.NameNotFoundException) {
        ""
    }

    companion object {
        const val EXTRA_DRAFT = "draft"
        private val NAVY = Color.parseColor("#10294a")
    }
}
