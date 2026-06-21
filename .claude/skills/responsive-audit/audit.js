// Render every page at narrow widths in both themes, flag horizontal overflow,
// and screenshot each. Usage:
//   AUDIT_JSON=/tmp/respaudit/audit.json OUT_DIR=/tmp/respaudit/shots node audit.js <label>
// Reads audit.json (from setup.py): { sessions, urls, auth_map }.
const { chromium } = require('playwright');
const fs = require('fs');

const BASE = process.env.BASE_URL || 'http://127.0.0.1:8009';
const JSON_PATH = process.env.AUDIT_JSON || '/tmp/respaudit/audit.json';
const OUT_ROOT = process.env.OUT_DIR || '/tmp/respaudit/shots';
const widths = (process.env.WIDTHS || '375,414,768').split(',').map(Number);
const themes = ['light', 'dark'];
const OUT = process.argv[2] || 'run';

const data = JSON.parse(fs.readFileSync(JSON_PATH, 'utf8'));
const shotDir = `${OUT_ROOT}/${OUT}`;
fs.mkdirSync(shotDir, { recursive: true });

function cookieFor(name) {
  const role = data.auth_map[name];
  if (!role) return null;
  return { name: 'sessionid', value: data.sessions[role], domain: '127.0.0.1', path: '/' };
}

(async () => {
  const browser = await chromium.launch({ channel: 'chrome' });
  const results = [];
  for (const [name, path] of Object.entries(data.urls)) {
    if (!path) continue;
    for (const theme of themes) {
      const ctx = await browser.newContext({ viewport: { width: widths[0], height: 900 } });
      const cookie = cookieFor(name);
      if (cookie) await ctx.addCookies([cookie]);
      await ctx.addInitScript((t) => { try { localStorage.setItem('theme', t); } catch (e) {} }, theme);
      const page = await ctx.newPage();
      for (const w of widths) {
        await page.setViewportSize({ width: w, height: 900 });
        try {
          const resp = await page.goto(BASE + path, { waitUntil: 'networkidle', timeout: 20000 });
          var status = resp ? resp.status() : 0;
        } catch (e) {
          results.push({ name, theme, w, error: String(e).slice(0, 120) });
          continue;
        }
        await page.evaluate((t) => document.documentElement.setAttribute('data-theme', t), theme);
        await page.waitForTimeout(250);
        const metrics = await page.evaluate(() => {
          const de = document.documentElement;
          const overflow = de.scrollWidth - de.clientWidth;
          const vw = de.clientWidth;
          const offenders = [];
          document.querySelectorAll('body *').forEach(el => {
            const r = el.getBoundingClientRect();
            if (r.width > vw + 1 && r.right > vw + 1 && r.height > 0) {
              if (getComputedStyle(el).position === 'fixed') return; // fixed handled by debug.js
              offenders.push({ tag: el.tagName.toLowerCase(),
                cls: (el.className && el.className.toString().slice(0, 40)) || '', w: Math.round(r.width) });
            }
          });
          const seen = {};
          offenders.forEach(o => { const k = o.tag + '.' + o.cls; if (!seen[k] || seen[k].w < o.w) seen[k] = o; });
          return { overflow, offenders: Object.values(seen).sort((a, b) => b.w - a.w).slice(0, 6) };
        });
        await page.screenshot({ path: `${shotDir}/${name}__${theme}__${w}.png`, fullPage: true });
        results.push({ name, theme, w, status, overflow: metrics.overflow, offenders: metrics.offenders });
        if (metrics.overflow > 1) {
          console.log(`OVERFLOW ${name} ${theme} ${w}px = +${metrics.overflow}px  ::`,
            metrics.offenders.map(o => `${o.tag}.${o.cls}(${o.w})`).join(', '));
        }
      }
      await ctx.close();
    }
  }
  await browser.close();
  fs.writeFileSync(`${OUT_ROOT}/results-${OUT}.json`, JSON.stringify(results, null, 1));
  const ovf = results.filter(r => r.overflow > 1);
  const errs = results.filter(r => r.error);
  console.log(`\n=== ${OUT}: ${results.length} renders, ${ovf.length} with overflow, ${errs.length} errors ===`);
  errs.forEach(e => console.log('ERR', e.name, e.theme, e.w, e.error));
})();
