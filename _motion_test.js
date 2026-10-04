// Verify Astra#2 tween: animates from current value, cancels, settles exactly.
const fs = require('fs');
const { JSDOM } = require('jsdom');

const html = fs.readFileSync('index.html', 'utf8');
const dom = new JSDOM(html, { runScripts: 'dangerously', pretendToBeVisual: true });
const { window } = dom;
const doc = window.document;
const out = [];
const T = (n, p, d) => out.push({ n, p, d });

const txt = id => (doc.getElementById(id)?.textContent || '').replace(/\s+/g, ' ').trim();

setTimeout(() => {
  try {
    // reduced-motion path must settle immediately
    const hvac = txt('hvac-out');
    T('results settled after load (no zero-state)', /8\.40 kW/.test(hvac), hvac.match(/[\d.]+ kW/)?.[0]);

    // drive a change and confirm the FINAL settled value is correct (tween must land exactly)
    const el = doc.getElementById('h-area');
    el.value = '200';
    el.dispatchEvent(new window.Event('input', { bubbles: true }));

    T('tween: value correct immediately after input', /28\.20 kW/.test(txt('hvac-out')),
      txt('hvac-out').match(/[\d.]+ kW/)?.[0]);

    // rapid successive inputs must not leave a stale/garbled number (cancellation test)
    for (const v of ['30', '90', '150', '77']) {
      el.value = v;
      el.dispatchEvent(new window.Event('input', { bubbles: true }));
    }
    const expectedKw = ((77 * 120) + (8 * 130) + 600) * 1.10 / 1000;
    const expectStr = expectedKw.toFixed(2);

    setTimeout(() => {
      const finalTxt = txt('hvac-out');
      const gotKw = (finalTxt.match(/([\d.]+) kW/) || [])[1];
      T('tween cancellation: settles on the LAST input', gotKw === expectStr,
        `expected ${expectStr} kW, got ${gotKw}`);
      T('no NaN/garbage after rapid input',
        !/NaN|undefined|null/.test(finalTxt), finalTxt.slice(0, 70));

      // hero chips must NOT start at zero (Astra #4)
      const chips = [...doc.querySelectorAll('[data-count]')].map(e => e.textContent);
      T('hero chips show final values (no count-up from 0)',
        chips.join(',') === '6,0,100%', chips.join(' , '));

      // units preserved
      T('units intact in results', /m³\/s|kW|GPM|mm|A /.test(finalTxt), 'units present');

      const pass = out.filter(r => r.p).length;
      console.log('\n=== TWEEN / MOTION VERIFICATION ===\n');
      for (const r of out) console.log(`  [${r.p ? 'PASS' : 'FAIL'}] ${r.n.padEnd(46)} ${r.d}`);
      console.log(`\n=== ${pass}/${out.length} PASSED ===`);
      process.exit(pass === out.length ? 0 : 1);
    }, 400);
  } catch (e) {
    console.log('HARNESS THREW:', e.message);
    process.exit(1);
  }
}, 500);
