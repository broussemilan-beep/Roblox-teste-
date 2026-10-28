// Render the viewer's two transparent fx layers for every frame (for the Blender compositor).
// usage: node tools/render_layers.js viewer/output/x.html outdir first last width
// writes outdir/world_%04d.png and outdir/screen_%04d.png (RGBA, non-premultiplied)
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const [file, outDir, firstArg = '0', lastArg = '', widthArg = '737'] = process.argv.slice(2);
  fs.mkdirSync(outDir, { recursive: true });
  const width = +widthArg;
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width, height: Math.round(width * 9 / 16) } });
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  for (const layer of ['world', 'screen']) {
    await page.goto('file://' + path.resolve(file) + `?paused=1&frame=0&cam=film&clean=1&layer=${layer}`);
    await page.waitForFunction('window.__ready === true', null, { timeout: 30000 });
    await page.addStyleTag({ content: 'html,body,#cv,canvas,.stage,main{background:transparent !important}' });
    const aspect = await page.evaluate(() => window.__aspect || 16 / 9);
    await page.setViewportSize({ width, height: Math.round(width / aspect) });
    await page.evaluate(() => window.dispatchEvent(new Event('resize')));
    const n = await page.evaluate(() => document.querySelector('#scrub') ? +document.querySelector('#scrub').max + 1 : 0);
    const last = lastArg === '' ? n - 1 : +lastArg;
    const canvas = await page.$('canvas');
    for (let f = +firstArg; f <= last; f++) {
      await page.evaluate((fr) => window.__renderFrame(fr), f);
      await canvas.screenshot({ path: path.join(outDir, `${layer}_${String(f).padStart(4, '0')}.png`), omitBackground: true });
    }
  }
  await browser.close();
  if (errors.length) { console.error('PAGE ERRORS:\n' + [...new Set(errors)].join('\n')); process.exit(2); }
})();
