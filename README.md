# 🧰 MEP Building Services Toolkit

> Interactive mechanical / electrical / plumbing calculators — **runs 100% in your browser.**

**▶️ [Open the live toolkit](https://darthsandd.github.io/mep-toolkit/)**

The lightweight companion to the [MEP Engineering Automation Suite](https://github.com/DarthSandD/mep-engineering-suite). Fast, focused calculators for everyday building-services work — plus the Python reference implementations behind each one.

---

## What's inside

| Module | File | Covers |
|---|---|---|
| ⚡ **Electrical** | `mep_electrical.py` | Loads, circuits, cable sizing |
| 🌬️ **HVAC** | `mep_hvac.py` | Airflow, cooling/heating loads |
| 🚰 **Plumbing** | `mep_plumbing.py` | Pipe sizing, flow, pressure |

Each module ships **two ways**: as an interactive browser calculator in `index.html`, and as a readable Python reference you can import, audit, or extend.

## Why the Python files matter

Engineering calculations should be **inspectable**. A black-box calculator gives you a number; the Python modules give you the *formula*, the *assumptions*, and the *units* — so you can verify the math instead of trusting it.

---

## Tech

`HTML` · `CSS` · `JavaScript` · `Python`

```
index.html           # interactive calculators (single file)
mep_electrical.py    # electrical reference implementation
mep_hvac.py          # HVAC reference implementation
mep_plumbing.py      # plumbing reference implementation
```

---

## Run locally

**Browser calculators:**
```bash
git clone https://github.com/DarthSandD/mep-toolkit.git
cd mep-toolkit
python -m http.server 8080
# → http://localhost:8080
```

**Python modules:**
```bash
python -c "import mep_electrical; print(mep_electrical.__doc__)"
```

---

## Related

- **[mep-engineering-suite](https://github.com/DarthSandD/mep-engineering-suite)** — full engineering suite with SLD generation

---

## License

Open source. See repository for details.

**Built by [Darren Lieu](https://darrenlin.pages.dev/)** · [@DarthSandD](https://github.com/DarthSandD)
