// Renders opening.html to a 1920x1080, 30 fps, 30-second MP4 (H.264 + silent AAC track).
//
//   node render.js                          -> out/uniway-cgu-opening-30s.mp4
//   node render.js --stills 3,9,15,20,23,27  -> out/still-<t>.png (quick visual checks)
//
// Requires Playwright (Chromium) and ffmpeg. Screens in shots/ come from capture.js.
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
let chromium;
try { ({ chromium } = require('playwright')); } catch { ({ chromium } = require('/opt/node-tools/node_modules/playwright')); }

const FPS = 30, DURATION = 30, W = 1920, H = 1080;
const here = __dirname;
const outDir = path.join(here, 'out');
fs.mkdirSync(outDir, { recursive: true });

(async () => {
  const args = process.argv.slice(2);
  const stillsArg = args.includes('--stills') ? args[args.indexOf('--stills') + 1] : null;
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
  const regionsFile = path.join(here, 'shots', 'regions.json');
  if (fs.existsSync(regionsFile)) {
    const captured = JSON.parse(fs.readFileSync(regionsFile, 'utf8'));
    await page.addInitScript((r) => { window.CAPTURED_REGIONS = r; }, captured);
  }
  await page.goto('file://' + path.join(here, 'opening.html'));
  // Render every scene once so all glyph subsets are requested, then wait for fonts and images.
  for (const t of [3, 9, 15, 20, 23, 27]) await page.evaluate((x) => render(x), t);
  await page.evaluate(async () => {
    document.querySelectorAll('.scene, .appear').forEach((el) => { el.style.opacity = 1; });
    await document.fonts.ready;
    await Promise.all([...document.images].map((im) => (im.complete ? 0 : new Promise((r) => { im.onload = im.onerror = r; }))));
  });
  const broken = await page.evaluate(() => [...document.images].filter((im) => !im.naturalWidth).map((im) => im.src));
  if (broken.length) throw new Error('Missing images: ' + broken.join(', '));

  if (stillsArg) {
    for (const t of stillsArg.split(',').map(Number)) {
      await page.evaluate((x) => render(x), t);
      await page.screenshot({ path: path.join(outDir, `still-${String(t).replace('.', '_')}.png`) });
    }
    await browser.close();
    return;
  }

  const outFile = path.join(outDir, 'uniway-cgu-opening-30s.mp4');
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error',
    '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-',
    '-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=48000',
    '-map', '0:v', '-map', '1:a', '-t', String(DURATION),
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p', '-r', String(FPS),
    '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', outFile], { stdio: ['pipe', 'inherit', 'inherit'] });
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
