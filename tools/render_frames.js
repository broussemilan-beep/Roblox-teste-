// Render frames of a built viewer to PNG with headless Chromium.
// usage: node tools/render_frames.js viewer/output/x.html outdir cam frame,frame,...
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const [file, outDir, cam = 'game', frames = '0'] = process.argv.slice(2);
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 960, height: 540 } });
  for (const f of frames.split(',')) {
    const url = 'file://' + path.resolve(file) + `?paused=1&frame=${f}&cam=${cam}&trail=1`;
    await page.goto(url);
    await page.waitForFunction('window.__ready === true');
    const canvas = await page.$('canvas');
    await canvas.screenshot({ path: path.join(outDir, `${cam}_${String(f).padStart(3, '0')}.png`) });
  }
  await browser.close();
})();
