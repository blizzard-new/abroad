"""Records the UniWay tutorial video: sign in from the home page, open 學校搜尋 and use everything on it.

    .venv/bin/python marketing/tutorial-video/demo_server.py &          # the real site, on port 8771
    .venv/bin/python marketing/tutorial-video/record.py                 # writes build/uniway-tutorial-school-search.mp4

A real Chromium drives the real site, step by step, at the speed a person would; Chromium's screencast keeps every
frame it paints. overlay.js draws the pointer, the click ripples, the captions and the title cards on top of the page.
music.py then writes the soundtrack (soft music plus a tick on every click) and ffmpeg puts it all into one MP4.

Without a GPU, Chromium paints a 1080p page about 8 times a second. So the whole session runs in slow motion (--slow,
4 times slower by default): the pointer, the pauses, the page's timers and its CSS animations all slow down together,
and the video is sped back up, which leaves about 30 painted frames for every second of video.

    --stills           only save a PNG at the end of each step (quick layout check, no video)
    --keep-frames      keep build/frames/ after encoding
    --no-music         video without sound
    --slow N           slow-motion factor while recording (1 = real time)
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import math
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

from playwright.async_api import Locator, Page, Route, async_playwright

HERE = Path(__file__).resolve().parent
VIEWPORT = {"width": 1600, "height": 900}
SCALE = 1.2  # 1600x900 CSS pixels -> 1920x1080 frames, the same zoom as the promo video's screenshots
FPS = 30
OUTPUT = "uniway-tutorial-school-search.mp4"
SLOW = 1  # set from --slow in main(); every wait below is multiplied by it


async def pause(seconds: float) -> None:
    """Wait this long on the video's clock."""
    await asyncio.sleep(seconds * SLOW)


def ms(seconds: float) -> float:
    """A Playwright timeout of this many seconds on the video's clock."""
    return seconds * 1000 * SLOW

# Google's own account picker is not part of UniWay and is not shown (demo_server.py answers for Google). In its
# place the recording shows this card for a few seconds; it says plainly that the step is skipped.
GOOGLE_STEP = """<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><title>UniWay</title>
<link rel="stylesheet" href="/static/typography.css"><style>
  html, body { margin: 0; height: 100%; font-family: var(--uw-font-ui, sans-serif); color: #10243a;
    background: radial-gradient(1100px 650px at 15% 10%, #c9ecf5 0%, transparent 60%),
                radial-gradient(900px 650px at 90% 95%, #f8e3d8 0%, transparent 60%), #eef5fb; }
  main { height: 100%; display: grid; place-items: center; }
  section { width: 640px; padding: 40px 44px; border-radius: 28px; background: rgba(255,255,255,.92);
    box-shadow: 0 24px 60px rgba(10,30,60,.16); text-align: center; }
  img { width: 64px; height: 64px; }
  h1 { margin: 14px 0 10px; font-size: 30px; }
  p { margin: 0; font-size: 19px; line-height: 1.7; color: #34495e; }
  b { color: #c2413a; }
  .note { margin-top: 18px; font-size: 15px; color: #6b7c8f; }
  .bar { height: 6px; margin-top: 26px; border-radius: 6px; background: #e3edf5; overflow: hidden; }
  .bar i { display: block; height: 100%; width: 0; background: #1f6f8b; animation: go 3.6s linear forwards; }
  @keyframes go { to { width: 100%; } }
</style></head><body><main><section>
  <img src="/static/assets/brand/uniway-mark.webp" alt="">
  <h1>接下來會開啟 Google 登入</h1>
  <p>選擇你的<b>學校 Google 帳號</b>（例如 ○○○@cgu.edu.tw），<br>同意後會自動回到 UniWay，並帶入你的學校。</p>
  <p class="note">教學影片略過 Google 的帳號選擇畫面</p>
  <div class="bar"><i></i></div>
</section></main>
<script>setTimeout(() => location.replace(NEXT), 3800);</script></body></html>"""


class Tape:
    """Every frame Chromium paints, with its time, plus the moments of clicks and the stretches to play faster."""

    def __init__(self, cdp, frames_dir: Path) -> None:
        self.cdp = cdp
        self.dir = frames_dir
        self.frames: list[tuple[float, str]] = []
        self.clicks: list[float] = []
        self.fast: list[list[float]] = []
        self.on = False

    async def start(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)
        self.dir.mkdir(parents=True)
        self.cdp.on("Page.screencastFrame", self._frame)
        await self._begin()
        self.on = True

    async def _begin(self) -> None:
        await self.cdp.send(
            "Page.startScreencast",
            {"format": "jpeg", "quality": 92, "maxWidth": 1920, "maxHeight": 1080, "everyNthFrame": 1},
        )

    def _frame(self, params: dict) -> None:
        asyncio.ensure_future(self.cdp.send("Page.screencastFrameAck", {"sessionId": params["sessionId"]}))
        if not self.on:
            return
        name = f"{len(self.frames):06d}.jpg"
        (self.dir / name).write_bytes(base64.b64decode(params["data"]))
        self.frames.append((params["metadata"]["timestamp"], name))

    async def stop(self) -> None:
        self.on = False
        await self.cdp.send("Page.stopScreencast")

    def click(self) -> None:
        self.clicks.append(time.time())

    def speed_from(self) -> float:
        return time.time()

    def speed_up(self, started: float, factor: float) -> None:
        self.fast.append([started, time.time(), factor])

    def timeline(self) -> dict:
        """Frame and click times on the finished video's clock (slow motion undone, sped-up stretches squeezed)."""
        start = self.frames[0][0]

        def out(t: float) -> float:
            shift = 0.0
            for t0, t1, factor in self.fast:
                overlap = max(0.0, min(t, t1) - t0)
                shift += overlap * (1 - 1 / factor)
            return (t - start - shift) / SLOW

        frames = [(out(t), name) for t, name in self.frames]
        return {
            "frames": frames,
            "clicks": [out(t) for t in self.clicks if t >= start],
            "duration": frames[-1][0] + 1.5,
        }


class Guide:
    """Moves the pointer like a person, clicks, types, and shows the captions."""

    def __init__(self, page: Page, tape: Tape | None, stills: Path | None) -> None:
        self.page = page
        self.tape = tape
        self.stills = stills
        self.x, self.y = VIEWPORT["width"] * 0.55, VIEWPORT["height"] * 0.6
        self.shot = 0

    async def hold(self, seconds: float) -> None:
        await pause(seconds if self.stills is None else min(seconds, 0.6))

    async def still(self, label: str) -> None:
        if self.stills is not None:
            self.shot += 1
            await self.page.screenshot(path=str(self.stills / f"{self.shot:02d}-{label}.png"))

    async def caption(self, step: int | None, title: str, body: str, where: str = "bottom") -> None:
        await self.page.evaluate("([s, t, b, w]) => window.__tut.caption(s, t, b, w)", [step, title, body, where])

    async def hide_caption(self) -> None:
        await self.page.evaluate("window.__tut.hideCaption()")

    async def ring(self, *selectors: str, pad: int = 8) -> None:
        await self.page.evaluate("([s, p]) => window.__tut.ring(s, p)", [list(selectors), pad])

    async def clear_ring(self) -> None:
        await self.page.evaluate("window.__tut.clearRing()")

    async def into_view(self, target: Locator, block: str = "center") -> None:
        await target.wait_for(state="visible", timeout=ms(30))
        box = await target.bounding_box()
        if box and 70 <= box["y"] and box["y"] + box["height"] <= VIEWPORT["height"] - 150:
            return
        await target.evaluate("(el, block) => el.scrollIntoView({ behavior: 'smooth', block })", block)
        await self.settle_scroll()

    async def scroll_by(self, dy: int) -> None:
        await self.page.evaluate("(dy) => window.scrollBy({ top: dy, behavior: 'smooth' })", dy)
        await self.settle_scroll()

    async def scroll_top(self) -> None:
        await self.page.evaluate("window.scrollTo({ top: 0, behavior: 'smooth' })")
        await self.settle_scroll()

    async def settle_scroll(self) -> None:
        last = None
        for _ in range(40):
            await pause(0.1)
            now = await self.page.evaluate("[scrollX, scrollY]")
            if now == last:
                break
            last = now
        await pause(0.15)

    async def point(self, target: Locator | tuple[float, float], seconds: float | None = None, at=(0.5, 0.5)) -> None:
        if isinstance(target, tuple):
            x, y = target
        else:
            await self.into_view(target)
            box = await target.bounding_box()
            x, y = box["x"] + box["width"] * at[0], box["y"] + box["height"] * at[1]
        distance = math.hypot(x - self.x, y - self.y)
        seconds = (seconds or min(1.1, 0.4 + distance / 1500)) * SLOW
        x0, y0 = self.x, self.y
        # A slight arc, like a hand moving a mouse. Progress follows the clock, however long each move takes.
        bend = min(60.0, distance * 0.08)
        nx, ny = (-(y - y0) / distance, (x - x0) / distance) if distance else (0, 0)
        clock = asyncio.get_running_loop().time
        started = clock()
        while True:
            p = min(1.0, (clock() - started) / seconds)
            e = p * p * (3 - 2 * p)
            arc = math.sin(math.pi * e) * bend
            await self.page.mouse.move(x0 + (x - x0) * e + nx * arc, y0 + (y - y0) * e + ny * arc)
            if p >= 1:
                break
            await asyncio.sleep(1 / 60)
        self.x, self.y = x, y

    async def click(self, target: Locator, at=(0.5, 0.5)) -> None:
        await self.point(target, at=at)
        await pause(0.18)
        if self.tape:
            self.tape.click()
        await self.page.mouse.down()
        await pause(0.09)
        await self.page.mouse.up()
        await pause(0.25)

    async def pretend_click(self, target: Locator) -> None:
        """A click the viewer sees, on a control whose browser pop-up a recording cannot show (a <select>)."""
        await self.point(target)
        await pause(0.18)
        if self.tape:
            self.tape.click()
        await self.page.evaluate("([x, y]) => window.__tut.ripple(x, y)", [self.x, self.y])
        await pause(0.35)

    async def choose(self, target: Locator, value: str) -> None:
        await self.pretend_click(target)
        await target.select_option(value)
        await pause(0.5)

    async def type(self, target: Locator, text: str, delay: float = 0.16) -> None:
        await self.click(target)
        for ch in text:
            await self.page.keyboard.type(ch)
            await pause(delay)

    async def wait_ready(self) -> None:
        await self.page.wait_for_selector("#boot-splash", state="detached", timeout=ms(120))
        await self.page.wait_for_function("() => window.__tut && document.querySelector('#tut-layer')", timeout=ms(30))
        await pause(0.6)


async def oauth_start(route: Route) -> None:
    """Let UniWay start the sign-in for real, then show GOOGLE_STEP instead of Google and continue to the callback."""
    answer = await route.fetch(max_redirects=0)
    google = parse_qs(urlparse(answer.headers["location"]).query)
    callback = f"{google['redirect_uri'][0]}?{urlencode({'state': google['state'][0], 'code': 'uniway-tutorial'})}"
    cookies = "\n".join(h["value"] for h in answer.headers_array if h["name"].lower() == "set-cookie")
    await route.fulfill(
        status=200,
        headers={"content-type": "text/html; charset=utf-8", "cache-control": "no-store", "set-cookie": cookies},
        body=GOOGLE_STEP.replace("NEXT", json.dumps(callback)),
    )


async def storyboard(g: Guide, page: Page) -> None:
    tape = g.tape
    pt = page.locator

    # ---- title card ---------------------------------------------------------------------------------------------
    await page.evaluate("""window.__tut.card(`
        <img class="mark" src="/static/assets/brand/uniway-mark.webp" alt="">
        <span class="eyebrow">UniWay 使用教學</span>
        <h1>登入與學校搜尋</h1>
        <p>一次學會找交換學校、篩選條件、收藏與比較</p>
        <div class="route"><span>登入</span><i>→</i><span>學校搜尋</span><i>→</i><span>篩選與排序</span><i>→</i><span>我的選校</span></div>
        <span class="mascot"><img src="/static/assets/mascot/suitcase.webp" alt=""><i></i><i></i></span>`)""")
    await page.evaluate("window.__tut.cursor(false)")
    await g.hold(4.2)
    await g.still("title")
    await page.evaluate("window.__tut.hideCard(); window.__tut.cursor(true)")
    await g.hold(0.9)

    # ---- 1 sign in ----------------------------------------------------------------------------------------------
    await g.caption(1, "從首頁登入", "瀏覽學校不用登入；要<em>收藏學校、保存條件與進度</em>時再登入。點左下角的<em>人像圖示</em>。")
    await g.hold(2.6)
    await g.ring("#account-button")
    await g.hold(1.0)
    await g.click(pt("#account-button"))
    await g.clear_ring()
    await page.wait_for_selector("#terms-consent", state="visible")
    await g.hold(0.8)
    await g.caption(1, "勾選同意條款", "第一次登入前，先勾選同意<em>使用條款與隱私權政策</em>。")
    await g.ring(".terms-consent")
    await g.hold(1.6)
    await g.click(pt("#terms-consent"))
    await g.hold(0.8)
    await g.caption(1, "使用 Google 繼續", "用<em>學校的 Google 信箱</em>（例如 @cgu.edu.tw）登入，會自動帶入你的學校。")
    await g.ring("[data-oauth-provider=google]", "#oauth-verification-note")
    await g.hold(3.0)
    await g.still("sign-in-dialog")
    await g.clear_ring()
    await g.click(pt("[data-oauth-provider=google]"))
    await page.wait_for_url(lambda url: "/auth/oauth/google/start" in url, timeout=ms(30))
    await page.wait_for_url(lambda url: url.endswith("#auth=success"), timeout=ms(30))
    fast = tape.speed_from() if tape else 0
    await page.wait_for_url(lambda url: "home=" in url and url.endswith("#home"), timeout=ms(60))
    await g.wait_ready()
    if tape:
        tape.speed_up(fast, 2)
    await g.hold(0.6)
    await g.caption(1, "登入完成", "左下角出現你的名字，上方的<em>就讀學校自動帶入「長庚大學」</em>。之後看到的合作校都以長庚為準。")
    await g.ring(".home-school-switcher, #school-switcher, .school-switcher")
    await g.point((470, 120))
    await g.hold(2.8)
    await g.still("signed-in")
    await g.ring("#account-button")
    await g.point(pt("#account-button"))
    await g.hold(1.8)
    await g.clear_ring()

    # ---- 2 學校搜尋 -------------------------------------------------------------------------------------------------
    await g.caption(2, "進入「學校搜尋」", "把滑鼠移到<em>左側選單</em>，選單會展開，點<em>「學校搜尋」</em>。")
    await g.point(pt("#glass-navigation a[href='#partners']"))
    await g.hold(1.4)
    await g.ring("#glass-navigation a[href='#partners']", pad=4)
    await g.hold(0.9)
    await g.click(pt("#glass-navigation a[href='#partners']"))
    await g.clear_ring()
    await g.point((900, 520), seconds=0.7)
    await page.wait_for_selector("#partner-table .pr-card, #partner-table article", timeout=ms(30))
    await g.hold(1.2)
    await g.caption(2, "長庚大學的全部合作學校", "上方顯示<em>共 77 所</em>，先列出 30 所；捲到最下面按「顯示更多學校」可以看其餘的。", "top")
    await g.ring("#partner-result-count")
    await g.hold(3.2)
    await g.still("partners")
    await g.clear_ring()
    await g.scroll_by(520)
    await g.hold(1.4)
    await g.scroll_top()
    await g.hold(0.4)

    # ---- 3 search box -------------------------------------------------------------------------------------------
    await g.caption(3, "用關鍵字搜尋", "在搜尋框輸入<em>國家、城市或學校名稱</em>，例如「日本」，再按<em>「搜尋學校」</em>。")
    await g.ring(".pr-search")
    await g.hold(1.6)
    await g.type(pt("#partner-search"), "日本", delay=0.35)
    await g.hold(0.5)
    await g.click(pt("#partner-search-submit"))
    await g.clear_ring()
    await g.hold(1.6)
    await g.scroll_top()
    await g.caption(3, "結果立刻更新", "只剩下日本的 <em>7 所</em>合作學校。旁邊也能指定<em>出發學期</em>與<em>語言檢定</em>。", "top")
    await g.ring("#partner-result-count")
    await g.point(pt("#partner-result-count"))
    await g.hold(2.2)
    await g.ring("label[for=partner-term-tile]", "label[for=partner-test-tile]")
    await g.point(pt("label[for=partner-test-tile]"))
    await g.hold(2.4)
    await g.still("search")
    await g.clear_ring()
    await g.click(pt("#partner-search"))
    await page.keyboard.press("Control+A")
    await pause(0.3)
    await page.keyboard.press("Backspace")
    await pause(0.4)
    await g.click(pt("#partner-search-submit"))
    await g.hold(1.0)
    await g.scroll_top()

    # ---- 4 cards / map ------------------------------------------------------------------------------------------
    await g.caption(4, "卡片／地圖", "右上角可以切換顯示方式。點<em>「地圖」</em>看合作學校在世界上的位置。")
    await g.ring(".pr-view-toggle")
    await g.hold(1.8)
    await g.click(pt("[data-partner-view=map]"))
    await g.clear_ring()
    await page.wait_for_selector("#partner-map-panel:not([hidden])", timeout=ms(30))
    await g.hold(1.0)
    await g.into_view(pt("#partner-map-panel"), block="start")
    await page.wait_for_function("() => !document.querySelector('#partner-map-status') || document.querySelector('#partner-map-status').hidden || !document.querySelector('#partner-map-status').textContent.includes('載入中')", timeout=ms(30))
    await g.hold(1.0)
    await g.caption(4, "在地圖上找學校", "點地圖上的學校可以預覽；也能用下方<em>「定位學校」</em>直接跳到某一所。", "top")
    await g.point(pt("#partner-globe"), seconds=0.9)
    await g.hold(2.4)
    await g.still("map")
    await g.into_view(pt("#map-school-select"))
    await g.ring("#map-school-select")
    await g.hold(0.6)
    option = await pt("#map-school-select option").nth(1).get_attribute("value")
    await g.choose(pt("#map-school-select"), option)
    await g.clear_ring()
    await g.hold(0.6)
    await g.into_view(pt("#partner-map-panel"), block="start")
    await g.hold(2.6)
    await g.still("map-preview")
    await g.scroll_top()
    await g.caption(4, "回到卡片", "點<em>「卡片」</em>回到學校列表。")
    await g.click(pt("[data-partner-view=list]"))
    await g.hold(1.6)

    # ---- 5 sorting ----------------------------------------------------------------------------------------------
    await g.caption(5, "三種排序", "<em>「截止最近」</em>把快要截止申請的學校排在最前面。")
    await g.ring("#partner-sort-tabs")
    await g.hold(1.6)
    await g.click(pt("[data-partner-sort=deadline]"))
    await g.clear_ring()
    await g.hold(1.0)
    await g.ring("#partner-table article")
    await g.hold(2.0)
    await g.clear_ring()
    await g.caption(5, "三種排序", "<em>「名額最多」</em>依交換名額由多到少排列。")
    await g.click(pt("[data-partner-sort=quota]"))
    await g.hold(1.0)
    await g.ring("#partner-table article")
    await g.hold(2.0)
    await g.clear_ring()
    await g.caption(5, "三種排序", "<em>「最符合條件」</em>會依你的語言成績、學業成績排序——要先填好<em>「我的條件」</em>（第 7 步）。")
    await g.click(pt("[data-partner-sort=match]"))
    await g.hold(3.0)
    await g.still("sort")

    # ---- 6 filters ----------------------------------------------------------------------------------------------
    await g.caption(6, "左側篩選：國家", "勾選國家只看那一國；右邊的數字是<em>該國的合作校數</em>。")
    await g.ring("#partner-facet-groups .pr-facet:first-child")
    await g.hold(1.8)
    await g.click(pt("label.pr-check:has(input[data-pr-facet=country][value='法國'])"))
    await g.clear_ring()
    await g.hold(1.0)
    await g.ring("#partner-result-count", "#partner-applied")
    await g.hold(2.2)
    await g.clear_ring()
    await g.caption(6, "左側篩選：交換名額", "再勾<em>「2 名以上」</em>，只看名額比較多、比較好申請的學校。")
    await g.click(pt("label.pr-check:has(input[data-pr-facet=quota][value='2plus'])"))
    await g.hold(1.0)
    await g.ring("#partner-result-count", "#partner-applied")
    await g.hold(2.2)
    await g.clear_ring()
    await g.still("filters")
    await g.caption(6, "更多條件", "<em>名額狀態、地區、國家、學院、學制</em>都能再細分。例如名額狀態選「當期名額已列」。")
    await g.into_view(pt(".pr-facet-selects"))
    await g.ring(".pr-facet-selects")
    await g.hold(2.2)
    await g.choose(pt("#availability-filter"), "open")
    await g.clear_ring()
    await g.hold(0.6)
    await g.point(pt("#college-filter"))
    await g.hold(0.9)
    await g.point(pt("#degree-filter"))
    await g.hold(1.2)
    await g.scroll_top()
    await g.ring("#partner-result-count", "#partner-applied")
    await g.hold(1.8)
    await g.clear_ring()
    await g.caption(6, "清除全部", "篩選太多找不到學校時，點<em>「清除全部」</em>一次重設。")
    await g.ring("#clear-partner-filters", pad=6)
    await g.hold(1.2)
    await g.click(pt("#clear-partner-filters"))
    await g.clear_ring()
    await g.hold(1.6)

    # ---- 7 my conditions ----------------------------------------------------------------------------------------
    await g.caption(7, "我的條件", "點<em>「我的條件」</em>，填入語言檢定與成績、學制；學業成績、交換學期有需要再填。")
    await g.ring("#discovery-criteria > summary")
    await g.hold(1.6)
    await g.click(pt("#discovery-criteria > summary"))
    await g.clear_ring()
    await g.hold(0.8)
    form = "#discovery-criteria-form"
    await g.choose(pt("#discovery-test"), "ielts")
    await g.type(pt("#discovery-score"), "6.5")
    await g.choose(pt(f"{form} [name=degree]"), "undergraduate")
    await g.point(pt(f"{form} [name=grade]"))
    await g.hold(1.2)
    await g.point(pt(f"{form} [name=term]"))
    await g.hold(1.0)
    await g.still("criteria")
    await g.caption(7, "套用條件", "按<em>「套用條件」</em>，系統會比對每一所學校公告的門檻。")
    await g.click(pt(f"{form} button[type=submit]"))
    await g.hold(1.4)
    await g.scroll_top()
    await g.caption(7, "看看哪些學校符合", "排序改成<em>「最符合條件」</em>，卡片上標出符合或待確認；條件<em>會保存在你的帳號</em>。", "top")
    await g.ring("[data-partner-sort=match]", "#discovery-criteria-result")
    await g.point(pt("[data-partner-sort=match]"))
    await g.hold(3.2)
    await g.clear_ring()
    await g.into_view(pt("#partner-table article").first, block="center")
    await g.ring("#partner-table article")
    await g.hold(2.6)
    await g.still("criteria-applied")
    await g.clear_ring()

    # ---- 8 detail + recently viewed -----------------------------------------------------------------------------
    await g.caption(8, "查看學校詳情", "點<em>學校名稱</em>，打開完整的申請條件、名額、截止日與官方來源。")
    first = pt("#partner-table .school-detail-trigger").first
    await g.ring("#partner-table .school-detail-trigger")
    await g.hold(1.4)
    await g.click(first)
    await g.clear_ring()
    await page.wait_for_function("() => location.hash.startsWith('#school=')", timeout=ms(30))
    await g.hold(2.2)
    await g.still("detail")
    await g.point((820, 600), seconds=0.6)
    await g.scroll_by(560)
    await g.hold(1.8)
    await g.scroll_by(560)
    await g.hold(1.6)
    await g.scroll_top()
    await g.caption(8, "返回列表", "看完點左上角<em>「返回」</em>回到學校搜尋。")
    back = pt("#back-to-schools:visible, #page-back:visible").first
    await g.ring("#back-to-schools", "#page-back")
    await g.hold(1.0)
    await g.click(back)
    await g.clear_ring()
    await page.wait_for_function("() => location.hash.startsWith('#partners')", timeout=ms(30))
    await g.hold(1.2)
    await g.scroll_top()
    await g.caption(8, "最近看過", "看過的學校會記在<em>「最近看過」</em>，點開就能快速回去。")
    recents = pt(".discovery-search-tools [data-discovery-recents] > summary")
    await g.ring(".discovery-search-tools [data-discovery-recents]")
    await g.hold(1.4)
    await g.click(recents)
    await g.hold(2.6)
    await g.still("recents")
    await g.click(recents)
    await g.clear_ring()
    await g.hold(0.6)

    # ---- 9 compare + my picks -----------------------------------------------------------------------------------
    await g.caption(9, "並排比較", "在想比較的學校勾<em>「加入比較」</em>（最多 3 所），它們也會一起收進<em>「我的選校」</em>。", "top")
    await g.click(pt("#partner-table .pr-compare").nth(0))
    await g.hold(1.0)
    await g.click(pt("#partner-table .pr-compare").nth(1))
    await g.hold(1.2)
    await g.caption(9, "收藏學校", "只想先收著的學校，點卡片右上角的<em>愛心</em>就好。", "top")
    await g.click(pt("#partner-table .favorite-toggle").nth(2))
    await g.hold(1.6)
    await g.ring(".discovery-search-tools .discovery-open-workspace", pad=6)
    await g.hold(1.4)
    await g.clear_ring()
    await g.caption(9, "並排比較", "下方的比較列顯示已選的學校，按<em>「並排比較」</em>。", "top")
    await g.ring("#partner-compare-tray")
    await g.hold(1.8)
    await g.still("compare-tray")
    await g.click(pt("#partner-compare-tray [data-open-compare]"))
    await g.clear_ring()
    await page.wait_for_function("() => location.hash.startsWith('#favorites')", timeout=ms(30))
    await g.hold(2.4)
    await g.caption(9, "並排比較", "語言門檻、費用、名額、研修期間與申請時程<em>並排列出</em>，差在哪裡一眼就看到。", "top")
    await g.hold(3.6)
    await g.still("comparison")
    await g.scroll_top()
    await g.caption(9, "我的選校", "收藏的學校都在<em>「我的選校」</em>；登入後會<em>同步到你的帳號</em>，換手機也看得到。")
    await g.point((900, 420), seconds=0.8)
    await g.hold(3.4)
    await g.still("favorites")
    await g.hide_caption()
    await g.hold(0.6)

    # ---- end card -----------------------------------------------------------------------------------------------
    await page.evaluate("window.__tut.cursor(false)")
    await page.evaluate("""window.__tut.card(`
        <span class="mascot"><img src="/static/assets/mascot/suitcase.webp" alt=""><i></i><i></i></span>
        <h1>開始找你的交換學校吧！</h1>
        <p>登入 → 學校搜尋 → 篩選、排序 → 收藏到我的選校</p>
        <div class="route"><span>app.uniway-tw.com</span></div>`)""")
    await g.hold(4.5)
    await g.still("end")


def encode(timeline: dict, frames_dir: Path, out: Path, music: Path | None) -> None:
    listing = frames_dir / "frames.txt"
    rows = timeline["frames"]
    with listing.open("w") as f:
        for i, (t, name) in enumerate(rows):
            nxt = rows[i + 1][0] if i + 1 < len(rows) else timeline["duration"]
            f.write(f"file '{name}'\nduration {max(nxt - t, 0.001):.4f}\n")
        f.write(f"file '{rows[-1][1]}'\n")
    command = ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listing)]
    if music:
        command += ["-i", str(music)]
    command += [
        "-vf", f"fps={FPS},scale=1920:1080:flags=lanczos,format=yuv420p",
        "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-profile:v", "high", "-tune", "animation",
    ]
    if music:
        command += ["-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-shortest"]
    command += ["-movflags", "+faststart", str(out)]
    subprocess.run(command, check=True)


def chromium_path() -> str | None:
    for candidate in (os.environ.get("CHROMIUM_PATH"), "/opt/pw-browsers/chromium"):
        if candidate and Path(candidate).exists():
            return candidate
    return None


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8771")
    parser.add_argument("--out", default=str(HERE / "build"))
    parser.add_argument("--stills", action="store_true")
    parser.add_argument("--keep-frames", action="store_true")
    parser.add_argument("--no-music", action="store_true")
    parser.add_argument("--slow", type=float, default=4.0)
    args = parser.parse_args()
    global SLOW
    SLOW = 1.0 if args.stills else max(1.0, args.slow)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    stills = out / "stills" if args.stills else None
    if stills:
        shutil.rmtree(stills, ignore_errors=True)
        stills.mkdir(parents=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=chromium_path())
        context = await browser.new_context(
            viewport=VIEWPORT, device_scale_factor=SCALE, locale="zh-TW", timezone_id="Asia/Taipei", color_scheme="light"
        )
        await context.add_init_script(script=f"window.__TUT_SLOW = {SLOW};")
        await context.add_init_script(path=str(HERE / "overlay.js"))
        await context.route("**/auth/oauth/google/start*", oauth_start)
        page = await context.new_page()
        page.set_default_timeout(ms(30))
        page.on("pageerror", lambda error: print("page error:", error, file=sys.stderr))
        cdp = await context.new_cdp_session(page)
        # CSS animations and transitions slow down with the page's clock (overlay.js); the rate survives navigation.
        await cdp.send("Animation.enable")
        await cdp.send("Animation.setPlaybackRate", {"playbackRate": 1 / SLOW})
        await page.goto(f"{args.base}/", wait_until="load", timeout=ms(120))
        guide = Guide(page, None, stills)
        await guide.wait_ready()
        await pause(1.5)  # let the home page finish its entrance before the first frame
        await page.mouse.move(guide.x, guide.y)

        tape = None
        if not stills:
            tape = Tape(cdp, out / "frames")
            guide.tape = tape
            await tape.start()
        try:
            await storyboard(guide, page)
        except Exception:
            await page.screenshot(path=str(out / "failed.png"))
            raise
        if tape:
            await tape.stop()
        await browser.close()

    if not tape:
        print(f"stills in {stills}")
        return
    timeline = tape.timeline()
    (out / "timeline.json").write_text(json.dumps({"duration": timeline["duration"], "clicks": timeline["clicks"]}, indent=1))
    print(f"{len(timeline['frames'])} frames, {timeline['duration']:.1f} s, {len(timeline['clicks'])} clicks")
    music = None
    if not args.no_music:
        music = out / "tutorial-music.wav"
        # music.py needs NumPy, which the project environment does not carry; any Python 3 that has it will do.
        python = os.environ.get("MUSIC_PYTHON", "python3")
        subprocess.run([python, str(HERE / "music.py"), str(out / "timeline.json"), str(music)], check=True)
    encode(timeline, out / "frames", out / OUTPUT, music)
    if not args.keep_frames:
        shutil.rmtree(out / "frames", ignore_errors=True)
    print(f"wrote {out / OUTPUT}")


if __name__ == "__main__":
    asyncio.run(main())
