// Renders index.html to an MP4, frame by frame.
//
//   node marketing/promo-video/render.mjs [--fps 30] [--frames 12.5,30.2] [--out marketing/promo-video/build]
//
// Needs a static server for the repository root on port 8770 (see README.md), Playwright, and ffmpeg.
// With --frames it only writes those moments as PNG stills, for checking the layout.
import { spawn } from "node:child_process";
import { mkdirSync } from "node:fs";
import { resolve } from "node:path";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");

const args = Object.fromEntries(process.argv.slice(2).reduce((acc, a, i, all) => (a.startsWith("--") ? [...acc, [a.slice(2), all[i + 1]]] : acc), []));
const fps = Number(args.fps || 30);
const out = resolve(args.out || "marketing/promo-video/build");
const base = args.url || "http://127.0.0.1:8770/marketing/promo-video/index.html?capture";
mkdirSync(out, { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
await page.goto(base, { waitUntil: "networkidle" });
await page.evaluate(() => window.ready);
const duration = await page.evaluate(() => window.DURATION);

if (args.frames) {
  for (const t of args.frames.split(",").map(Number)) {
    await page.evaluate((tt) => window.render(tt), t);
    await page.screenshot({ path: `${out}/still-${t.toFixed(2)}.png` });
    console.log(`still ${t}`);
  }
  await browser.close();
  process.exit(0);
}

const total = Math.round(duration * fps);
const ffmpeg = spawn("ffmpeg", [
  "-y", "-loglevel", "error",
  "-f", "image2pipe", "-framerate", String(fps), "-c:v", "mjpeg", "-i", "-",
  "-i", `${out}/music.wav`,
  "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-profile:v", "high",
  "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart",
  `${out}/uniway-promo-1080p.mp4`,
], { stdio: ["pipe", "inherit", "inherit"] });

for (let i = 0; i < total; i++) {
  await page.evaluate((tt) => window.render(tt), i / fps);
  const jpg = await page.screenshot({ type: "jpeg", quality: 95 });
  if (!ffmpeg.stdin.write(jpg)) await new Promise((r) => ffmpeg.stdin.once("drain", r));
  if (i % (fps * 5) === 0) console.log(`frame ${i}/${total}`);
}
ffmpeg.stdin.end();
await new Promise((r, j) => ffmpeg.on("close", (code) => (code === 0 ? r() : j(new Error(`ffmpeg exited ${code}`)))));
await browser.close();
console.log(`wrote ${out}/uniway-promo-1080p.mp4`);
