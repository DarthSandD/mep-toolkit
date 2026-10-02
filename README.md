# 🧰 MEP Toolkit — Free Building-Services Calculators

> Six engineering calculators for mechanical, electrical & plumbing design.
> **Type or slide a value — every result recalculates live.** No install. No signup. Works offline.

**▶️ [Open the live toolkit](https://darthsandd.github.io/mep-toolkit/)**

---

## The six calculators

| # | Tool | What it does |
|---|---|---|
| 01 | ❄️ **HVAC Cooling Load + Duct** | Envelope + occupants + lighting with safety margin → kW, BTU/hr, tons, airflow, round duct size |
| 02 | ⚡ **Electrical Load Schedule** | Editable load table with auto-matched demand factors → per-load amps, cable size, breaker rating, main feeder |
| 03 | 🚰 **Plumbing Demand + Pump Head** | Fixture units → demand via Hunter curve, pipe by velocity limit, head via Hazen-Williams |
| 04 | 🔌 **Voltage Drop** | Cable R/X → drop in volts and %, instant PASS/FAIL against your limit |
| 05 | 💡 **Lighting Design** | Lumen method → luminaire count and a suggested rows × cols layout |
| 06 | 🌀 **Ventilation** | ACH and occupancy rates → design airflow (whichever governs) + supply duct |

---

## Why it's built this way

**The math is inspectable.** Every calculator ships alongside its Python reference implementation. A black-box calculator gives you a number; these give you the *formula*, the *assumptions*, and the *units* — so you can verify rather than trust.

```bash
python mep_electrical.py --load "Lighting:25" --load "HVAC:60" --voltage 400 --phases 3 --pf 0.85
python mep_hvac.py --area 50 --occupants 8 --lighting 600
python mep_plumbing.py --fixture-units 80 --system tank --static-head-m 15 --pipe-length-m 60
```

**Live, not submit-and-wait.** Results update as you type or drag a slider. No calculate button.

**Works on site.** One HTML file, zero dependencies, no network calls. Open it from a laptop or phone in a plant room with no signal.

---

## What's under the hood

Real engineering formulas, not approximations:

- **Cable sizing** — lookup table mapping design current → copper cross-section + breaker rating
- **Demand factors** — matched from the load name (lighting .9, HVAC 1.0, sockets .5, elevator .75, pump .8, fire 1.0, IT/server .85, kitchen .65)
- **Hunter curves** — separate tank-flush and valve-flush fixture-unit → GPM tables, interpolated
- **Hazen-Williams** — pipe friction `hf = 10.67 · L · Q^1.852 / (C^1.852 · d^4.87)` with C=140
- **Voltage drop** — `ΔV = k · I · (R·cosφ + X·sinφ)`, k=2 single-phase / √3 three-phase
- **Lumen method** — `N = E · A / (Φ · UF · MF)`

---

## Tech

`HTML` · `CSS` · `JavaScript` · `Python` — **zero runtime dependencies**

```
index.html           # all six calculators (single self-contained file)
mep_electrical.py    # electrical reference — load schedule, DF, cable/breaker
mep_hvac.py          # HVAC reference — cooling load, airflow, duct sizing
mep_plumbing.py      # plumbing reference — fixture units, pipe, pump head
```

---

## Run locally

```bash
git clone https://github.com/DarthSandD/mep-toolkit.git
cd mep-toolkit
python -m http.server 8080
# → http://localhost:8080
```

Or just open `index.html` directly — it needs no server.

---

## Tests

An end-to-end suite loads the page, runs its real JavaScript, and asserts the calculators produce correct engineering values:

```bash
npm install --no-save jsdom
node _e2e_test.js
# → 17/17 PASSED
```

---

## ⚠️ Sizing aid, not a substitute for design review

These are documented rule-of-thumb estimators. **Verify against local code and a qualified engineer before design or construction use.**

---

**Built by [Darren Lieu](https://darrenlin.pages.dev/)** · [@DarthSandD](https://github.com/DarthSandD) · [@darren.lin_ai](https://www.instagram.com/darren.lin_ai)
