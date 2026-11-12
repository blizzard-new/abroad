// Renders a storyboard page to a 1920x1080, 30 fps, 30-second MP4 (H.264 + AAC).
//
//   node render.js                                   -> v2 with narration: out/uniway-cgu-opening-30s-narrated.mp4
//   node render.js --page opening.html --silent      -> v1 without narration: out/uniway-cgu-opening-30s.mp4
//   node render.js --stills 3,9,15,20,23,27          -> out/still-<t>.png (quick visual checks)
//
// Requires Playwright (Chromium) and ffmpeg. Screens in shots/ come from capture.js; the narration
// track and its timing (out/narration.wav, out/narration.json) come from narration.py. Google Fonts
// are fetched through HTTPS_PROXY when that variable is set.
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
let chromium;
try { ({ chromium } = require('playwright')); } catch { ({ chromium } = require('/opt/node-tools/node_modules/playwright')); }

const FPS = 30, DURATION = 30, W = 1920, H = 1080;
const here = __dirname;
const outDir = path.join(here, 'out');
fs.mkdirSync(outDir, { recursive: true });

const args = process.argv.slice(2);
const opt = (name, fallback) => (args.includes(name) ? args[args.indexOf(name) + 1] : fallback);
const silent = args.includes('--silent');
const pageFile = opt('--page', silent ? 'opening.html' : 'opening-v2.html');
const audioFile = silent ? null : path.join(outDir, 'narration.wav');
const outFile = path.join(outDir, opt('--out', silent ? 'uniway-cgu-opening-30s.mp4' : 'uniway-cgu-opening-30s-narrated.mp4'));
const stillsArg = opt('--stills', null);

(async () => {
  const proxy = process.env.HTTPS_PROXY ? { server: process.env.HTTPS_PROXY } : undefined;
  const browser = await chromium.launch({ proxy });
  const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
  const inject = {};
  const regionsFile = path.join(here, 'shots', 'regions.json');
  if (fs.existsSync(regionsFile)) inject.CAPTURED_REGIONS = JSON.parse(fs.readFileSync(regionsFile, 'utf8'));
  const narrationFile = path.join(outDir, 'narration.json');
  if (!silent && fs.existsSync(narrationFile)) inject.NARRATION = JSON.parse(fs.readFileSync(narrationFile, 'utf8'));
  if (audioFile && !fs.existsSync(audioFile)) throw new Error('Missing ' + audioFile + ' — run narration.py first.');
  await page.addInitScript((data) => Object.assign(window, data), inject);
  await page.goto('file://' + path.join(here, pageFile), { waitUntil: 'load', timeout: 120000 });
  // Render every part once so all glyph subsets are requested, then wait for fonts and images.
  for (let t = 0; t <= DURATION; t += 1.5) await page.evaluate((x) => render(x), t);
  await page.evaluate(async () => {
    document.querySelectorAll('.scene, .appear, #sub').forEach((el) => { el.style.opacity = 1; });
    await document.fonts.ready;
    await Promise.all([...document.images].map((im) => (im.complete ? 0 : new Promise((r) => { im.onload = im.onerror = r; }))));
  });
  await page.waitForTimeout(1500);
  await page.evaluate(() => document.fonts.ready);
  const broken = await page.evaluate(() => [...document.images].filter((im) => !im.naturalWidth).map((im) => im.src));
  if (broken.length) throw new Error('Missing images: ' + broken.join(', '));
  const missingFonts = await page.evaluate(() => ['Chiron GoRound TC', 'Luckiest Guy', 'Noto Sans TC']
    .filter((f) => document.querySelector('link[href*="fonts.googleapis"]') && !document.fonts.check(`32px "${f}"`)));
  if (missingFonts.length) console.warn('Fonts not loaded:', missingFonts.join(', '));

  if (stillsArg) {
    for (const t of stillsArg.split(',').map(Number)) {
      await page.evaluate((x) => render(x), t);
      await page.screenshot({ path: path.join(outDir, `still-${String(t).replace('.', '_')}.png`) });
    }
    await browser.close();
    return;
  }

  const audioIn = audioFile ? ['-i', audioFile] : ['-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=48000'];
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error',
    '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-', ...audioIn,
    '-map', '0:v', '-map', '1:a', '-t', String(DURATION),
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p', '-r', String(FPS),
    '-c:a', 'aac', '-b:a', '160k', '-ac', '2', '-movflags', '+faststart', outFile], { stdio: ['pipe', 'inherit', 'inherit'] });
  const total = FPS * DURATION;
  for (let i = 0; i < total; i++) {
    await page.evaluate((x) => render(x), i / FPS);
    const buf = await page.screenshot({ type: 'png' });
    if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
    if (i % 150 === 0) console.log(`frame ${i}/${total}`);
  }
  ff.stdin.end();
  await new Promise((r, j) => ff.on('close', (c) => (c === 0 ? r() : j(new Error('ffmpeg exit ' + c)))));
  await browser.close();
  console.log('wrote', outFile);
})().catch((e) => { console.error(e); process.exit(1); });
