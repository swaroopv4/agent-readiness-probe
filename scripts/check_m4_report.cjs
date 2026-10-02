// Local, headless rendering QA. Does not execute trajectories or alter report data.
const {chromium} = require('C:/Users/ADMIN/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs = require('fs');
const path = require('path');
const root = path.resolve(__dirname, '..');
async function main() {
  const browser = await chromium.launch({headless:true, executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
  const page = await browser.newPage({viewport:{width:1440,height:1100}});
  const requests = [], errors = [];
  page.on('request', r => requests.push(r.url()));
  page.on('pageerror', e => errors.push(String(e)));
  // file:// proves the HTML works without the preview server or other assets.
  await page.goto('file:///' + path.join(root, 'reports/click_readiness.html').replaceAll('\\','/'));
  const snapshot = await page.locator('#recorded-data').textContent();
  const data = JSON.parse(snapshot);
  if (data.diagnostics.attempts.length !== 48 || data.M5.analysis.primary_confirmation.estimate !== 0) throw new Error('Embedded evidence mismatch');
  await page.screenshot({path:path.join(root,'artifacts/private/m4-desktop.png')});
  await page.locator('#mechanism').scrollIntoViewIfNeeded();
  await page.screenshot({path:path.join(root,'artifacts/private/m4-mechanism.png')});
  await page.locator('#fixes').scrollIntoViewIfNeeded();
  await page.screenshot({path:path.join(root,'artifacts/private/m4-fixes.png')});
  const widths = [];
  for (const width of [1440, 760, 390]) {
    await page.setViewportSize({width,height:844});
    await page.evaluate(() => {document.querySelectorAll('details').forEach(d => d.open=true)});
    widths.push(await page.evaluate(() => ({viewport:innerWidth, document:document.documentElement.scrollWidth, sections:document.querySelectorAll('section').length})));
  }
  await page.evaluate(() => {document.querySelectorAll('details').forEach(d => d.open=false); scrollTo(0,0)});
  await page.screenshot({path:path.join(root,'artifacts/private/m4-mobile.png')});
  await page.setViewportSize({width:1440,height:1100});
  await page.pdf({path:path.join(root,'artifacts/private/m4-print-qa.pdf'),format:'A4',printBackground:true});
  const external = requests.filter(u => !u.startsWith('file:///'));
  if (widths.some(w => w.document > w.viewport) || errors.length || external.length) throw new Error(JSON.stringify({widths,errors,external}));
  const audit = {status:'passed', mode:'standalone file URL', viewports:widths, external_requests:external, page_errors:errors,
                 embedded_attempts:data.diagnostics.attempts.length, print_rendered:true};
  fs.writeFileSync(path.join(root,'artifacts/private/m4-browser-audit.json'),JSON.stringify(audit,null,2)+'\n');
  console.log(JSON.stringify(audit));
  await browser.close();
}
main().catch(e => {console.error(e); process.exit(1)});
