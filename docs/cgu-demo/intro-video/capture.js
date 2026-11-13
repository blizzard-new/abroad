// Captures real UniWay CGU demo screens (1440x900 @2x) for the 30-second intro video and
// records focus regions in <out>/regions.json. Creates the fictional student's demo plan,
// completes one task, then presses 重設我的展示資料 so only this browser's demo workspace is touched.
//   node capture.js <out-dir>
const fs = require('fs');
let chromium;
try { ({ chromium } = require('playwright')); } catch { ({ chromium } = require('/opt/node-tools/node_modules/playwright')); }
const OUT = process.argv[2] || 'shots';
const URL = process.env.CGU_DEMO_URL || 'https://demo.uniway-tw.com/';
fs.mkdirSync(OUT, { recursive: true });
(async () => {
  const browser = await chromium.launch({ proxy: process.env.HTTPS_PROXY ? { server: process.env.HTTPS_PROXY } : undefined });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2, locale: 'zh-TW', timezoneId: 'Asia/Taipei', reducedMotion: 'reduce' });
  const page = await ctx.newPage();
  page.setDefaultTimeout(240000); global.__page = page;
  const regions = {};
  const log = (...a) => console.log(new Date().toISOString().slice(11, 19), ...a);
  const rect = (sel) => page.evaluate((q) => { const r = document.querySelector(q).getBoundingClientRect(); return { x: Math.round(r.left), y: Math.round(r.top), w: Math.round(r.width), h: Math.round(r.height) }; }, sel);
  const ready = async () => { await page.locator('#boot-splash').waitFor({ state: 'hidden', timeout: 300000 }); await page.evaluate('appReady'); };
  const noSmooth = () => page.addStyleTag({ content: 'html,body{scroll-behavior:auto!important}' });
  const top = async () => { await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' })); await page.waitForTimeout(600); };
  const scrollTo = async (sel, offset) => { await page.evaluate(([q, o]) => { const el = document.querySelector(q); window.scrollTo({ top: el.getBoundingClientRect().top + scrollY - o, behavior: 'instant' }); }, [sel, offset]); await page.waitForTimeout(1200); };
  const imagesLoaded = async (sel) => {
    for (let i = 0; i < 60; i++) {
      const ok = await page.evaluate((s) => [...document.querySelectorAll(s + ' img')].filter(im => { const r = im.getBoundingClientRect(); return r.bottom > 0 && r.top < innerHeight; }).every(im => im.complete && im.naturalWidth > 0), sel);
      if (ok) return true; await page.waitForTimeout(1000);
    }
    return false;
  };
  await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 300000 }); await ready(); await noSmooth(); log('loaded');
  await page.waitForTimeout(2500); await top();

  // 1) 116-1 one-pager at the top of the CGU home page.
  await page.locator('#cgu-hero-onepager').waitFor({ state: 'visible' });
  regions.hero = await rect('#cgu-hero-onepager');
  await page.screenshot({ path: `${OUT}/a-hero.png` }); log('hero', JSON.stringify(regions.hero));

  // 2) Department finder (the fictional student is in 生物醫學工程學系).
  await scrollTo('#cgu-dept-finder', 72);
  regions.dept = await page.evaluate(() => { let el = document.querySelector('#cgu-dept-result-summary'); while (el && el.getBoundingClientRect().height < 70) el = el.parentElement; const r = el.getBoundingClientRect(); return { x: Math.round(r.left), y: Math.round(r.top), w: Math.round(r.width), h: Math.round(r.height) }; });
  regions.deptText = await page.locator('#cgu-dept-result-summary').innerText();
  await page.screenshot({ path: `${OUT}/b-dept.png` }); log('dept', JSON.stringify(regions.dept), regions.deptText.replace(/\n/g, ' '));

  // 3) School search in card view, scrolled to the first row of cards.
  await page.evaluate(() => { location.hash = 'partners'; }); await page.locator('#partner-result-count').waitFor();
  const cardBtn = page.locator('button:visible', { hasText: /^\s*卡片\s*$/ }).first();
  if (await cardBtn.count()) await cardBtn.click();
  await page.locator('#partner-table .pr-school-card').first().waitFor({ state: 'visible' });
  await scrollTo('#cgu-program-tabs', 76);
  await page.waitForTimeout(1500); log('partners images ok:', await imagesLoaded('#partner-table')); await page.waitForTimeout(800);
  // Focus: the 全部計畫／交換／雙學位 tabs plus the 長庚學院 quick bar.
  regions.filters = await page.evaluate(() => {
    const a = document.querySelector('#cgu-program-tabs').getBoundingClientRect();
    let el = document.querySelector('#cgu-college-quick-bar'); while (el.parentElement && el.parentElement.getBoundingClientRect().width < a.width + 40 && el.getBoundingClientRect().width < a.width - 40) el = el.parentElement;
    const b = el.getBoundingClientRect();
    const x = Math.min(a.left, b.left), y = Math.min(a.top, b.top), r = Math.max(a.right, b.right), btm = Math.max(a.bottom, b.bottom);
    return { x: Math.round(x), y: Math.round(y), w: Math.round(r - x), h: Math.round(btm - y) };
  });
  regions.filtersText = (await page.locator('#cgu-program-tabs').innerText()).replace(/\n/g, ' ') + ' | ' + (await page.locator('#cgu-college-quick-bar').innerText()).replace(/\n/g, ' ').slice(0, 120);
  await page.screenshot({ path: `${OUT}/c-partners.png` }); log('filters', JSON.stringify(regions.filters), regions.filtersText);

  // 4) 我的申請: load the demo plan, then complete the first task.
  // The seed button reloads the current URL when it carries search parameters, so start from the plain home URL.
  await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 300000 }); await ready(); await noSmooth(); await top();
  await page.locator('#cgu-demo-seed').click(); await page.locator('.today-primary').waitFor({ state: 'visible' }); await ready();
  await noSmooth(); await page.waitForTimeout(1500); await top();
  regions.today = await page.evaluate(() => { let el = document.querySelector('#today-focus-title'); while (el && el.getBoundingClientRect().height < 150) el = el.parentElement; const r = el.getBoundingClientRect(); return { x: Math.round(r.left), y: Math.round(r.top), w: Math.round(r.width), h: Math.round(r.height) }; });
  regions.todayText = await page.locator('#today-focus-title').innerText();
  await page.screenshot({ path: `${OUT}/d-today.png` }); log('today', JSON.stringify(regions.today), regions.todayText);
  await page.locator('.today-primary').click(); await page.locator('#level-form button[type=submit]').waitFor({ state: 'visible' });
  await page.locator('#level-form button[type=submit]').click(); await page.locator('.success-state', { hasText: '已同步' }).waitFor();
  await page.waitForTimeout(1200);
  regions.done = await rect('.success-state');
  regions.doneText = (await page.locator('.success-state').innerText()).slice(0, 160);
  await page.screenshot({ path: `${OUT}/e-done.png` }); log('done', JSON.stringify(regions.done), regions.doneText.replace(/\n/g, ' '));

  regions.revision = await page.evaluate(async () => (await (await fetch('/health')).json()).revision);
  regions.capturedAt = new Date().toISOString();
  fs.writeFileSync(`${OUT}/regions.json`, JSON.stringify(regions, null, 1));
  // Clean up this browser's fictional workspace.
  await page.locator('a.back-link').click(); await page.waitForTimeout(800);
  await page.locator('#cgu-demo-reset').click();
  await Promise.all([page.waitForNavigation({ waitUntil: 'domcontentloaded' }), page.locator('#cgu-demo-confirm').click()]);
  log('reset done');
  await browser.close();
})().catch(async (e) => {
  console.error('CAPTURE FAILED', e.message.split('\n')[0]);
  try { await global.__page.screenshot({ path: `${OUT}/FAIL.png` }); console.error('url', global.__page.url()); } catch {}
  process.exit(1);
});
