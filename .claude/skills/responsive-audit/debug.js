// Print the widest elements crossing the right viewport edge (incl. position:fixed,
// which audit.js skips). Use to name the exact culprit behind an overflow.
// Usage: node debug.js <url-path> [width]
//   node debug.js /malaka/<course>/<module>/<lesson>/ 375
const { chromium } = require('playwright');

const BASE = process.env.BASE_URL || 'http://127.0.0.1:8009';
const path = process.argv[2] || '/';
const width = Number(process.argv[3] || 375);
// Optional: pass a sessionid to audit an authenticated page.
const SESSION = process.env.SESSIONID || '';

(async () => {
  const browser = await chromium.launch({ channel: 'chrome' });
  const ctx = await browser.newContext({ viewport: { width, height: 900 } });
  if (SESSION) await ctx.addCookies([{ name: 'sessionid', value: SESSION, domain: '127.0.0.1', path: '/' }]);
  const page = await ctx.newPage();
  await page.goto(BASE + path, { waitUntil: 'networkidle' });
  const info = await page.evaluate(() => {
    const de = document.documentElement;
    const vw = de.clientWidth;
    const out = [];
    document.querySelectorAll('*').forEach(el => {
      const r = el.getBoundingClientRect();
      if (r.right > vw + 1 && r.width > 40 && r.height > 0) {
        const cs = getComputedStyle(el);
        out.push({ tag: el.tagName.toLowerCase(), id: el.id, cls: (el.className || '').toString().slice(0, 45),
          w: Math.round(r.width), left: Math.round(r.left), right: Math.round(r.right),
          pos: cs.position, ws: cs.whiteSpace, txt: (el.textContent || '').trim().slice(0, 25) });
      }
    });
    const seen = {};
    out.forEach(o => { const k = o.tag + o.id + o.cls; if (!seen[k] || seen[k].right < o.right) seen[k] = o; });
    return { vw, scrollW: de.scrollWidth, list: Object.values(seen).sort((a, b) => b.right - a.right).slice(0, 12) };
  });
  console.log(`vw=${info.vw} scrollW=${info.scrollW} (overflow +${info.scrollW - info.vw}px)`);
  info.list.forEach(o => console.log(
    `  r${o.right} w${o.w} l${o.left} ${o.pos} ws:${o.ws} <${o.tag}#${o.id}.${o.cls}> "${o.txt}"`));
  await browser.close();
})();
