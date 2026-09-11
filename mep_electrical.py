#!/usr/bin/env python3
"""MEP Electrical module: building load schedule, demand calc, cable/breaker sizing.

Usage:
  python mep_electrical.py
  python mep_electrical.py --load "Lighting:25" --load "HVAC:60" --load "Sockets:15" --voltage 400 --phases 3 --pf 0.85
  python mep_electrical.py --csv loads.csv

Stdlib only.
"""
import argparse
import csv
import sys

# Demand factors per load type (fraction of connected load counted as demand)
DEMAND_FACTORS = {
    "lighting": 0.90,
    "hvac": 1.00,
    "sockets": 0.50,       # receptacle / socket outlets
    "receptacle": 0.50,
    "elevator": 0.75,
    "lift": 0.75,
    "pump": 0.80,
    "fire": 1.00,
    "it": 0.85,
    "server": 0.85,
    "kitchen": 0.65,
    "misc": 0.80,
    "other": 0.80,
}

# (min_current_A, cable_mm2_cu, breaker_A) — simplified copper PVC suggestion table
CABLE_TABLE = [
    (0,    1.5,  10),
    (15.5, 2.5,  20),
    (21,   4,    25),
    (28,   6,    32),
    (36,   10,   40),
    (50,   16,   63),
    (66,   25,   80),
    (84,   35,   100),
    (104,  50,   125),
    (125,  70,   160),
    (160,  95,   200),
    (200,  120,  250),
    (245,  150,  315),
    (300,  185,  400),
    (350,  240,  500),
]


def parse_load(spec):
    """Parse 'Name:kW' or 'Name:kW:factor'."""
    parts = spec.split(":")
    if len(parts) < 2:
        raise ValueError(f"Bad --load spec {spec!r}, expected Name:kW[:factor]")
    name = parts[0].strip()
    try:
        kw = float(parts[1])
    except ValueError:
        raise ValueError(f"Bad kW value in {spec!r}")
    factor = None
    if len(parts) >= 3 and parts[2].strip():
        factor = float(parts[2])
    return name, kw, factor


def demand_factor_for(name, override=None):
    if override is not None:
        return override
    return DEMAND_FACTORS.get(name.strip().lower(), DEMAND_FACTORS["other"])


def size_cable_breaker(current_a):
    for lo, mm2, brk in reversed(CABLE_TABLE):
        if current_a >= lo:
            return mm2, brk
    return CABLE_TABLE[0][1], CABLE_TABLE[0][2]


def current_per_load(demand_kw, voltage, phases, pf):
    w = demand_kw * 1000.0
    if phases == 3:
        return w / (3 ** 0.5 * voltage * pf)
    return w / (voltage * pf)


def build_schedule(loads, voltage, phases, pf):
    rows = []
    for name, kw, fover in loads:
        df = demand_factor_for(name, fover)
        dkw = round(kw * df, 2)
        amps = round(current_per_load(dkw, voltage, phases, pf), 2)
        mm2, brk = size_cable_breaker(amps)
        rows.append({"load": name, "connected_kw": kw, "demand_factor": df,
                     "demand_kw": dkw, "current_a": amps,
                     "cable_mm2_cu": mm2, "breaker_a": brk})
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description="Building electrical load schedule + cable/breaker sizing")
    ap.add_argument("--load", action="append", default=[],
                    help="Load as Name:kW[:factor], repeatable")
    ap.add_argument("--voltage", type=float, default=400)
    ap.add_argument("--phases", type=int, choices=[1, 3], default=3)
    ap.add_argument("--pf", type=float, default=0.85, help="Power factor")
    ap.add_argument("--csv", default="electrical_schedule.csv", help="CSV output path")
    ap.add_argument("--no-csv", action="store_true")
    args = ap.parse_args(argv)

    if args.load:
        loads = [parse_load(s) for s in args.load]
    else:
        loads = [("Lighting", 25, None), ("HVAC", 60, None),
                 ("Sockets", 15, None), ("Elevator", 12, None),
                 ("IT", 10, None)]

    rows = build_schedule(loads, args.voltage, args.phases, args.pf)
    tot_conn = sum(r["connected_kw"] for r in rows)
    tot_dem = sum(r["demand_kw"] for r in rows)
    tot_i = round(current_per_load(tot_dem, args.voltage, args.phases, args.pf), 2)
    mm2, brk = size_cable_breaker(tot_i)

    h = ["Load", "Conn kW", "DF", "Dem kW", "Amps", "Cable Cu", "Breaker"]
    print(f"Electrical Load Schedule ({args.phases}ph, {args.voltage:g}V, pf={args.pf})")
    print("-" * 74)
    print(f"{h[0]:<12}{h[1]:>9}{h[2]:>6}{h[3]:>9}{h[4]:>9}{h[5]:>11}{h[6]:>9}")
    print("-" * 74)
    for r in rows:
        print(f"{r['load']:<12}{r['connected_kw']:>9.2f}{r['demand_factor']:>6.2f}"
              f"{r['demand_kw']:>9.2f}{r['current_a']:>9.2f}"
              f"{str(r['cable_mm2_cu']) + 'mm2':>11}{str(r['breaker_a']) + 'A':>9}")
    print("-" * 74)
    print(f"{'TOTAL':<12}{tot_conn:>9.2f}{'':>6}{tot_dem:>9.2f}{tot_i:>9.2f}"
          f"{str(mm2) + 'mm2':>11}{str(brk) + 'A':>9}  <-- main feeder")
    print(f"\nConnected: {tot_conn:.2f} kW | Demand: {tot_dem:.2f} kW | "
          f"Main: {tot_i:.1f} A -> {mm2}mm2 Cu, {brk}A breaker")

    if not args.no_csv:
        with open(args.csv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"Saved CSV: {args.csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
