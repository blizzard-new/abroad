"""Turns drafts into media: IG carousel and story JPEGs, Reels/Shorts and long-form MP4s.

Pages load from a made-up origin (https://render.office/) that Playwright serves from disk, so the templates can use
the website's own fonts and the mascot artwork without a local web server. Videos are captured frame by frame like
marketing/promo-video/render.mjs: render(t) draws one moment, the screenshot goes to ffmpeg over a pipe.
"""

from __future__ import annotations

import mimetypes
import os
import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Iterator

from ..config import Settings
from ..models import CarouselDraft, Slide, VideoScript, VisualPlan
from ..visual import default_plan
from .soundtrack import soundtrack


def ffmpeg_exe() -> str:
    """The ffmpeg that comes with the imageio-ffmpeg package (IMAGEIO_FFMPEG_EXE points it at another one)."""
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()

TEMPLATES = Path(__file__).resolve().parent
ORIGIN = "https://render.office"
SIZES = {"portrait": (1080, 1920), "landscape": (1920, 1080)}

Progress = Callable[[int, int, Path | None], None]


class Renderer:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.roots = {
            "template": TEMPLATES,
            "brand": settings.brand_assets_dir,
            "fonts": settings.fonts_dir,
        }

    @contextmanager
    def _page(self, width: int, height: int) -> Iterator:
        from playwright.sync_api import sync_playwright

        executable = os.environ.get("CHROMIUM_PATH") or None
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=executable)
            try:
                page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
                page.route(f"{ORIGIN}/**", self._serve)
                yield page
            finally:
                browser.close()

    def _serve(self, route) -> None:
        path = route.request.url.removeprefix(ORIGIN).split("?")[0].lstrip("/")
        prefix, _, rest = path.partition("/")
        root = self.roots.get(prefix)
        target = (root / rest).resolve() if root else None
        if not target or not target.is_file() or root.resolve() not in target.parents:
            route.fulfill(status=404, body="not found")
            return
        mime = mimetypes.guess_type(target.name)[0] or ("font/woff2" if target.suffix == ".woff2" else "application/octet-stream")
        route.fulfill(status=200, body=target.read_bytes(), headers={"Content-Type": mime})

    def _art_url(self, art: Path | None) -> str | None:
        if not art or not art.is_file():
            return None
        self.roots["art"] = art.parent
        return f"{ORIGIN}/art/{art.name}"

    @staticmethod
    def _design(plan: VisualPlan | None, slides: list[Slide], index: int) -> dict:
        """What the template needs for one page: the set's shared spec and this page's layout (the plain plan when nobody designed)."""
        plan = plan or default_plan(slides)
        return {"spec": plan.spec.model_dump(), "slide": plan.slides[index].model_dump()}

    def carousel(self, draft: CarouselDraft, out_dir: Path, progress: Progress | None = None, art: Path | None = None,
                 plan: VisualPlan | None = None) -> list[Path]:
        out_dir.mkdir(parents=True, exist_ok=True)
        files = []
        art_url = self._art_url(art)
        plan = plan or default_plan(draft.slides)
        with self._page(1080, 1350) as page:
            page.goto(f"{ORIGIN}/template/carousel.html", wait_until="load")
            for index, slide in enumerate(draft.slides):
                page.evaluate(
                    "(args) => window.renderSlide(args)",
                    {"slide": slide.model_dump(), "index": index, "total": len(draft.slides), "site": self._site(), "story": False,
                     "art": art_url if slide.kind == "cover" else None, "design": self._design(plan, draft.slides, index)},
                )
                path = out_dir / f"slide-{index + 1:02d}.jpg"
                page.locator("#slide").screenshot(path=str(path), type="jpeg", quality=92)
                files.append(path)
                if progress:
                    progress(index + 1, len(draft.slides), path)
        return files

    def card(self, slide: Slide, out_path: Path, plan: VisualPlan | None = None) -> Path:
        """One 4:5 picture in the carousel's look, e.g. the image that goes with a Threads post."""
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with self._page(1080, 1350) as page:
            page.goto(f"{ORIGIN}/template/carousel.html", wait_until="load")
            page.evaluate(
                "(args) => window.renderSlide(args)",
                {"slide": slide.model_dump(), "index": 0, "total": 1, "site": self._site(), "story": False, "art": None,
                 "design": self._design(plan, [slide], 0)},
            )
            page.locator("#slide").screenshot(path=str(out_path), type="jpeg", quality=92)
        return out_path

    def story(self, cover: Slide, out_path: Path, art: Path | None = None, plan: VisualPlan | None = None) -> Path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        art_url = self._art_url(art)
        with self._page(1080, 1920) as page:
            page.goto(f"{ORIGIN}/template/carousel.html", wait_until="load")
            page.evaluate(
                "(args) => window.renderSlide(args)",
                {"slide": cover.model_dump(), "index": 0, "total": 1, "site": self._site(), "story": True, "art": art_url,
                 "design": self._design(plan, [cover], 0)},
            )
            page.locator("#slide").screenshot(path=str(out_path), type="jpeg", quality=92)
        return out_path

    def video(
        self,
        script: VideoScript,
        out_path: Path,
        *,
        orientation: str = "portrait",
        fps: int | None = None,
        progress: Progress | None = None,
    ) -> dict:
        fps = fps or self.settings.video_fps
        width, height = SIZES[orientation]
        out_path.parent.mkdir(parents=True, exist_ok=True)
        poster = out_path.with_name(out_path.stem + "-poster.jpg")
        music = out_path.with_suffix(".wav")
        with self._page(width, height) as page:
            page.goto(f"{ORIGIN}/template/video.html", wait_until="load")
            page.evaluate("([s, o]) => window.setup(s, o)", [script.model_dump(), orientation])
            duration = page.evaluate("window.DURATION")
            cues = page.evaluate("window.CUES")
            soundtrack(duration, cues, music, drums_in=script.scenes[0].seconds if script.scenes else 3.0)
            page.evaluate("(t) => window.render(t)", min(1.4, duration / 2))
            page.screenshot(path=str(poster), type="jpeg", quality=90)

            total = max(1, round(duration * fps))
            ffmpeg = subprocess.Popen(
                [
                    ffmpeg_exe(), "-y", "-loglevel", "error",
                    "-f", "image2pipe", "-framerate", str(fps), "-c:v", "mjpeg", "-i", "-",
                    "-i", str(music),
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-profile:v", "high",
                    "-r", str(fps), "-g", str(fps * 2),
                    "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
                    "-shortest", "-movflags", "+faststart",
                    str(out_path),
                ],
                stdin=subprocess.PIPE,
            )
            try:
                for frame in range(total):
                    page.evaluate("(t) => window.render(t)", frame / fps)
                    ffmpeg.stdin.write(page.screenshot(type="jpeg", quality=88))
                    if progress and (frame % fps == 0 or frame == total - 1):
                        progress(frame + 1, total, None)
            finally:
                ffmpeg.stdin.close()
                code = ffmpeg.wait()
        music.unlink(missing_ok=True)
        if code != 0:
            raise RuntimeError(f"ffmpeg exited with {code}")
        return {"path": out_path, "poster": poster, "duration": duration, "width": width, "height": height, "fps": fps}

    def _site(self) -> str:
        return self.settings.site_url.split("//")[-1]
