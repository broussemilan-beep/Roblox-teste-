// Render many frames of a built viewer in ONE page load (fast): the "film" camera, clean (no HUD), as PNGs.
// usage: node tools/render_video.js viewer/output/x.html outdir [step=2] [first=0] [last=end] [width=960]
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const [file, outDir, stepArg = '2', firstArg = '0', lastArg = '', widthArg = '960'] = process.argv.slice(2);
  fs.mkdirSync(outDir, { recursive: true });
  const width = +widthArg, height = Math.round(width * 9 / 16);  // resized to the film's aspect once the page is up
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width, height } });
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  await page.goto('file://' + path.resolve(file) + '?paused=1&frame=0&cam=film&clean=1');
  await page.waitForFunction('window.__ready === true', null, { timeout: 30000 });
  const aspect = await page.evaluate(() => window.__aspect || 16 / 9);
  await page.setViewportSize({ width, height: Math.round(width / aspect) });
  await page.evaluate(() => window.dispatchEvent(new Event('resize')));
  const n = await page.evaluate(() => document.querySelector('#scrub') ? +document.querySelector('#scrub').max + 1 : 0);
  const last = lastArg === '' ? n - 1 : +lastArg;
  const canvas = await page.$('canvas');
  let k = 0;
  for (let f = +firstArg; f <= last; f += +stepArg) {
    await page.evaluate((fr) => window.__renderFrame(fr), f);
    await canvas.screenshot({ path: path.join(outDir, `f_${String(k).padStart(4, '0')}.png`) });
    k++;
  }
  await browser.close();
  console.log(`${k} frames -> ${outDir}`);
  if (errors.length) { console.error('PAGE ERRORS:\n' + [...new Set(errors)].join('\n')); process.exit(2); }
})();
