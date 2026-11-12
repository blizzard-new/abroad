// Captures real UniWay CGU demo screens (1440x900 @2x) for the opening video and records
// focus regions in <out>/regions.json. Creates the fictional student's demo plan, completes
// one task, then presses 重設我的展示資料 so only this browser's demo workspace is touched.
//   node capture.js <out-dir>
const fs = require('fs');
let chromium;
try { ({ chromium } = require('playwright')); } catch { ({ chromium } = require('/opt/node-tools/node_modules/playwright')); }
const OUT = process.argv[2] || 'shots';
const URL = 'https://demo.uniway-tw.com/';
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
  const top = async () => { await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' })); await page.waitForTimeout(600); };
  const imagesLoaded = async (sel) => {
    for (let i = 0; i < 60; i++) {
      const ok = await page.evaluate((s) => [...document.querySelectorAll(s + ' img')].filter(im => { const r = im.getBoundingClientRect(); return r.bottom > 0 && r.top < innerHeight; }).every(im => im.complete && im.naturalWidth > 0), sel);
      if (ok) return true; await page.waitForTimeout(1000);
    }
    return false;
  };
  await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 300000 }); await ready(); log('loaded');
  await page.addStyleTag({ content: 'html,body{scroll-behavior:auto!important}' });
  // Seed from the plain home URL (the seed button reloads the current URL when it carries search parameters).
  await page.locator('#cgu-demo-seed').click(); await page.locator('.today-primary').waitFor({ state: 'visible' }); await ready();
  await page.addStyleTag({ content: 'html,body{scroll-behavior:auto!important}' });
  await page.waitForTimeout(1500); await top();
  regions.p3Card = await page.evaluate(() => { let el = document.querySelector('#today-focus-title'); while (el && el.getBoundingClientRect().height < 150) el = el.parentElement; const r = el.getBoundingClientRect(); return { x: Math.round(r.left), y: Math.round(r.top), w: Math.round(r.width), h: Math.round(r.height) }; });
  await page.screenshot({ path: `${OUT}/p3-today.png` }); log('p3', JSON.stringify(regions.p3Card));
  await page.locator('.today-primary').click(); await page.locator('#level-form button[type=submit]').waitFor({ state: 'visible' });
  await page.locator('#level-form button[type=submit]').click(); await page.locator('.success-state', { hasText: '已同步' }).waitFor();
  await page.waitForTimeout(1200);
  regions.p4Done = await rect('.success-state');
  await page.screenshot({ path: `${OUT}/p4-done.png` }); log('p4', JSON.stringify(regions.p4Done));
  await page.locator('a.back-link').click(); await page.locator('a[data-tab=today]:visible').first().click();
  await page.locator('#today-focus-title', { hasText: '整理兩所志願' }).waitFor(); await page.waitForTimeout(1200); await top();
  await page.screenshot({ path: `${OUT}/p5-next.png` }); log('p5');
  // School search in card view, scrolled to the first row of cards.
  await page.evaluate(() => { location.hash = 'partners'; }); await page.locator('#partner-result-count').waitFor();
  const cardBtn = page.locator('button:visible', { hasText: /^\s*卡片\s*$/ }).first();
  if (await cardBtn.count()) await cardBtn.click();
  await page.locator('#partner-table .pr-school-card').first().waitFor({ state: 'visible' });
  await page.evaluate(() => { const el = document.querySelector('#partner-table .pr-school-card'); window.scrollTo({ top: el.getBoundingClientRect().top + scrollY - 150, behavior: 'instant' }); });
  await page.waitForTimeout(2500); log('partners images ok:', await imagesLoaded('#partner-table')); await page.waitForTimeout(800);
  regions.p1Card = await rect('#partner-table .pr-school-card');
  await page.screenshot({ path: `${OUT}/p1-partners.png` }); log('p1', JSON.stringify(regions.p1Card));
  // Lincoln detail.
  await page.locator('#partner-search').fill('Lincoln'); await page.locator('#partner-table', { hasText: '林肯' }).waitFor();
  await page.locator('#partner-table .school-detail-trigger').first().click(); await page.locator('#detail-favorite-button').waitFor({ state: 'visible' });
  await page.waitForTimeout(1500); log('detail images ok:', await imagesLoaded('main')); await top();
  await page.screenshot({ path: `${OUT}/p2-detail.png` }); log('p2');
  fs.writeFileSync(`${OUT}/regions.json`, JSON.stringify(regions, null, 1));
  // Clean up this browser's fictional workspace.
  await page.locator('#cgu-demo-reset').click();
  await Promise.all([page.waitForNavigation({ waitUntil: 'domcontentloaded' }), page.locator('#cgu-demo-confirm').click()]);
  log('reset done');
  await browser.close();
})().catch(async (e) => {
  console.error('CAPTURE FAILED', e.message.split('\n')[0]);
  try { await global.__page.screenshot({ path: `${OUT}/FAIL.png` }); console.error('url', global.__page.url()); } catch {}
  process.exit(1);
});
