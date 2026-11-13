// Renders intro.html to a 1920x1080, 30 fps, 30-second MP4 (H.264 + AAC background music).
//
//   node render.js                            -> out/uniway-cgu-intro-30s.mp4
//   node render.js --stills 2.5,7,12,17.5,22,24.8,28  -> out/still-<t>.png (quick visual checks)
//   node render.js --silent                   -> same video with a silent audio track
//
// Requires Playwright (Chromium), ffmpeg and python3 with numpy (for the synthesised music,
// marketing/promo-video/music.py preset "cgu-intro"). Screens in shots/ come from capture.js.
const path = require('path');
const fs = require('fs');
const { spawn, execFileSync } = require('child_process');
let chromium;
try { ({ chromium } = require('playwright')); } catch { ({ chromium } = require('/opt/node-tools/node_modules/playwright')); }

const FPS = 30, DURATION = 30, W = 1920, H = 1080;
const here = __dirname;
const outDir = path.join(here, 'out');
fs.mkdirSync(outDir, { recursive: true });

(async () => {
  const args = process.argv.slice(2);
  const stillsArg = args.includes('--stills') ? args[args.indexOf('--stills') + 1] : null;
  const silent = args.includes('--silent');
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
  const regionsFile = path.join(here, 'shots', 'regions.json');
  if (fs.existsSync(regionsFile)) {
    const captured = JSON.parse(fs.readFileSync(regionsFile, 'utf8'));
    await page.addInitScript((r) => { window.CAPTURED_REGIONS = r; }, captured);
  }
  await page.goto('file://' + path.join(here, 'intro.html'));
  // Render every scene once so all glyph subsets are requested, then wait for fonts and images.
  for (const t of [2.5, 7, 12, 17, 22, 24.5, 28]) await page.evaluate((x) => render(x), t);
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

  let audioIn = ['-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=48000'];
  if (!silent) {
    const wav = path.join(outDir, 'music.wav');
    execFileSync('python3', [path.join(here, '../../../marketing/promo-video/music.py'), wav, 'cgu-intro'], { stdio: 'inherit' });
    audioIn = ['-i', wav];
  }
  const outFile = path.join(outDir, 'uniway-cgu-intro-30s.mp4');
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error',
    '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-', ...audioIn,
    '-map', '0:v', '-map', '1:a', '-t', String(DURATION),
    '-af', `afade=t=in:d=0.3,afade=t=out:st=${DURATION - 1.2}:d=1.2`,
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-r', String(FPS),
    '-c:a', 'aac', '-b:a', '160k', '-ar', '48000', '-movflags', '+faststart', outFile], { stdio: ['pipe', 'inherit', 'inherit'] });
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
