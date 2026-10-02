// Real end-to-end test: load index.html in jsdom, run its actual scripts,
// and assert the calculators produce correct numbers.
const fs = require('fs');
const { JSDOM } = require('jsdom');

const html = fs.readFileSync('index.html', 'utf8');
const dom = new JSDOM(html, { runScripts: 'dangerously', pretendToBeVisual: true });
const { window } = dom;
const doc = window.document;

const results = [];
function check(name, pass, detail) {
  results.push({ name, pass, detail });
}
const txt = id => (doc.getElementById(id)?.textContent || '').replace(/\s+/g, ' ').trim();

// give scripts a tick
setTimeout(() => {
  try {
    // --- structure ---
    check('6 calculator cards present', doc.querySelectorAll('main .card').length === 6,
      `${doc.querySelectorAll('main .card').length} cards`);
    check('why band rendered', doc.querySelectorAll('.why-item').length === 3,
      `${doc.querySelectorAll('.why-item').length} items`);
    check('footer present', !!doc.querySelector('footer.site'), 'footer');
    check('light-load rows seeded', doc.querySelectorAll('#e-rows tr').length === 5,
      `${doc.querySelectorAll('#e-rows tr').length} rows`);

    // --- HVAC outputs computed from defaults (50m2, 8 occ, 600W) ---
    const hvac = txt('hvac-out');
    check('HVAC produced results', /Total cooling/i.test(hvac), hvac.slice(0, 110));
    check('HVAC total = 8.40 kW (50m², 8 occ, 600W)', /8\.40 kW/.test(hvac), hvac.match(/[\d.]+ kW/)?.[0] || 'n/a');
    check('HVAC duct sized', /mm dia/i.test(hvac), hvac.match(/\d+ mm dia @ [\d.]+ m\/s/)?.[0] || 'n/a');

    // --- Electrical: 5 seeded loads ---
    const elec = txt('elec-out');
    check('Electrical produced results', /Connected load/i.test(elec), elec.slice(0, 110));
    check('Electrical main feeder sized', /Main feeder/i.test(elec),
      elec.match(/[\d.]+ A → [\d.]+ mm² Cu, \d+ A breaker/)?.[0] || 'n/a');

    // --- Plumbing: 80 WSFU, tank curve -> ~38 GPM ---
    const plumb = txt('plumb-out');
    check('Plumbing demand ≈38 GPM', /38\.[\d] GPM/.test(plumb),
      plumb.match(/[\d.]+ GPM[^·]*·[^L]*L\/s/)?.[0] || 'n/a');
    check('Plumbing pump head computed', /Pump head/i.test(plumb),
      plumb.match(/[\d.]+ m \([\d.]+ ft\)/)?.[0] || 'n/a');

    // --- Voltage drop verdict logic ---
    const vd = txt('vd-out');
    check('Voltage-drop verdict present', /PASS|FAIL/.test(vd),
      vd.match(/(PASS|FAIL)/)?.[0] || 'n/a');

    // --- Lighting lumen method ---
    const lux = txt('lux-out');
    check('Lighting layout suggested', /rows ×|—/.test(lux),
      lux.match(/\d+ rows × \d+ cols \(\d+ positions\)/)?.[0] || 'n/a');

    // --- Ventilation ---
    const vent = txt('vent-out');
    check('Ventilation airflow computed', /m³\/s/.test(vent),
      vent.match(/[\d.]+ m³\/s \([\d]+ CFM\)/)?.[0] || 'n/a');

    // --- interactivity: change a value, confirm live recalc ---
    const before = txt('hvac-out');
    doc.getElementById('h-area').value = '200';
    doc.getElementById('h-area').dispatchEvent(new window.Event('input', { bubbles: true }));
    const after = txt('hvac-out');
    check('LIVE RECALC: area 50→200 changes output', before !== after,
      after.match(/[\d.]+ kW/)?.[0] || 'n/a');

    // --- new marketing copy present ---
    check('OG meta tag present',
      !!doc.querySelector('meta[property="og:title"]'), 'og:title');
    check('GitHub source link in hero',
      !!doc.querySelector('.cta-row a[href*="github.com"]'), 'source link');

  } catch (e) {
    check('TEST HARNESS', false, 'threw: ' + e.message);
  }

  const passed = results.filter(r => r.pass).length;
  console.log('\n=== MEP TOOLKIT — END-TO-END TEST ===\n');
  for (const r of results) {
    console.log(`  [${r.pass ? 'PASS' : 'FAIL'}] ${r.name.padEnd(44)} ${r.detail}`);
  }
  console.log(`\n=== ${passed}/${results.length} PASSED ===`);
  process.exit(passed === results.length ? 0 : 1);
}, 400);
