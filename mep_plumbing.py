#!/usr/bin/env python3
"""MEP plumbing rough estimator: fixture units -> demand (GPM/LPS), pipe size, pump head.

Stdlib only. Rough sizing aid -- verify against local code before design use.
Usage:
  python mep_plumbing.py --fixture-units 80
  python mep_plumbing.py --fixtures "wc_tank=10,lav=12,shower=6,sink=4" --system tank --static-head-m 15 --pipe-length-m 60
  python mep_plumbing.py --fixture-units 120 --system valve --static-head-m 20 --pipe-length-m 80 --csv out.csv
"""
import argparse
import csv
import math
from datetime import datetime, timezone
from pathlib import Path

GPM_TO_LPS = 0.0630902
GPM_TO_M3S = 0.0000630902
M_TO_FT = 3.28084

# Rough Hunter-curve fits (interpolated). Labeled ROUGH -- check local code tables.
# Predominantly flush-tank systems
TANK_FU =  [0, 5, 10, 15, 20, 30, 40, 50, 60, 80, 100, 140, 200, 300, 500, 1000, 2000]
TANK_GPM = [0, 5,  8, 11, 14, 20, 25, 29, 32, 38,  43,  53,  65,  85, 115, 175,  280]
# Predominantly flush-valve systems
VALVE_FU =  [0, 5, 10, 15, 20, 30, 40, 50, 60, 80, 100, 140, 200, 300, 500, 1000]
VALVE_GPM = [0, 15, 27, 34, 38, 44, 48, 52, 55, 60,  67,  78,  92, 110, 145, 210]

# WSFU weights per fixture (cold+hot combined, private-use-ish rough values)
FU_WEIGHTS = {
    "wc_tank": 3.0, "wc_valve": 10.0, "urinal_tank": 3.0, "urinal_valve": 5.0,
    "lav": 1.0, "sink": 2.0, "shower": 2.0, "bathtub": 2.0,
    "dishwasher": 2.0, "washing": 4.0, "hose": 3.0, "mop": 3.0,
}

# Standard nominal sizes (mm) with approx inch label
STD_SIZES = [(15, '1/2"'), (20, '3/4"'), (25, '1"'), (32, '1-1/4"'),
             (40, '1-1/2"'), (50, '2"'), (65, '2-1/2"'), (80, '3"'), (100, '4"')]


def interp(x, xs, ys):
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:  # extrapolate gently with last-segment slope
        slope = (ys[-1] - ys[-2]) / (xs[-1] - xs[-2])
        return ys[-1] + slope * (x - xs[-1])
    for i in range(1, len(xs)):
        if x <= xs[i]:
            t = (x - xs[i - 1]) / (xs[i] - xs[i - 1])
            return ys[i - 1] + t * (ys[i] - ys[i - 1])
    return ys[-1]


def demand_gpm(fu, system):
    if system == "valve":
        return interp(fu, VALVE_FU, VALVE_GPM)
    return interp(fu, TANK_FU, TANK_GPM)


def parse_fixtures(spec):
    """'wc_tank=10,lav=12' -> (total_fu, breakdown dict)."""
    total, breakdown = 0.0, {}
    for item in spec.split(","):
        item = item.strip()
        if not item:
            continue
        if "=" not in item:
            raise ValueError(f"bad fixture entry '{item}', want name=count")
        name, count = item.split("=", 1)
        name, count = name.strip().lower(), float(count.strip())
        if name not in FU_WEIGHTS:
            raise ValueError(f"unknown fixture '{name}', known: {sorted(FU_WEIGHTS)}")
        fu = FU_WEIGHTS[name] * count
        breakdown[name] = {"count": count, "fu_each": FU_WEIGHTS[name], "fu": fu}
        total += fu
    return total, breakdown


def suggest_pipe(q_m3s, vmax=1.8):
    """Required ID for velocity limit, then next standard size up."""
    d_req = math.sqrt(4 * q_m3s / (math.pi * vmax)) * 1000  # mm
    chosen = STD_SIZES[-1]
    for s in STD_SIZES:
        if s[0] >= d_req:
            chosen = s
            break
    area = math.pi * (chosen[0] / 1000) ** 2 / 4
    vel = q_m3s / area if area else 0.0
    return d_req, chosen[0], chosen[1], vel


def hazen_williams_hf(q_m3s, d_mm, length_m, c=140):
    d = d_mm / 1000.0
    if q_m3s <= 0 or d <= 0:
        return 0.0
    return 10.67 * length_m * (q_m3s ** 1.852) / ((c ** 1.852) * (d ** 4.87))


def main():
    ap = argparse.ArgumentParser(description="Plumbing rough estimator: FU->GPM/LPS, pipe size, pump head.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--fixture-units", type=float, help="total water supply fixture units (WSFU)")
    g.add_argument("--fixtures", help='fixture counts, e.g. "wc_tank=10,lav=12,shower=6"')
    ap.add_argument("--system", choices=["tank", "valve"], default="tank",
                    help="demand curve: flush-tank or flush-valve predominant (default tank)")
    ap.add_argument("--velocity", type=float, default=1.8, help="max velocity for pipe sizing m/s (default 1.8)")
    ap.add_argument("--static-head-m", type=float, default=10.0, help="static lift m (default 10)")
    ap.add_argument("--pipe-length-m", type=float, default=50.0, help="developed pipe length m (default 50)")
    ap.add_argument("--pipe-dia-mm", type=float, default=0.0,
                    help="pipe ID for head calc; 0 = use auto-suggested size (default 0)")
    ap.add_argument("--hazenc", type=float, default=140.0, help="Hazen-Williams C (default 140)")
    ap.add_argument("--fitting-factor", type=float, default=0.3,
                    help="extra equivalent length fraction for fittings (default 0.3 = +30%%)")
    ap.add_argument("--residual-head-m", type=float, default=10.0,
                    help="required residual pressure at top fixture, m head (default 10)")
    ap.add_argument("--csv", default="mep_plumbing_result.csv", help="CSV output path (default mep_plumbing_result.csv; use '' to skip)")
    args = ap.parse_args()

    if args.fixtures:
        fu, breakdown = parse_fixtures(args.fixtures)
    else:
        if args.fixture_units < 0:
            ap.error("--fixture-units must be >= 0")
        fu, breakdown = args.fixture_units, {}

    gpm = demand_gpm(fu, args.system)
    lps = gpm * GPM_TO_LPS
    q_m3s = gpm * GPM_TO_M3S

    d_req, d_nom, d_in, vel = suggest_pipe(q_m3s, args.velocity)
    d_calc = args.pipe_dia_mm if args.pipe_dia_mm > 0 else d_nom
    leq = args.pipe_length_m * (1.0 + args.fitting_factor)
    hf = hazen_williams_hf(q_m3s, d_calc, leq, args.hazenc)
    total_head = args.static_head_m + hf + args.residual_head_m
    power_kw = (1000 * 9.81 * q_m3s * total_head / 0.65 / 1000) if q_m3s > 0 else 0.0  # 65% wire-to-water

    rows = [
        ("timestamp_utc", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")),
        ("system_curve", args.system),
        ("fixture_units", round(fu, 2)),
        ("demand_gpm", round(gpm, 2)),
        ("demand_lps", round(lps, 3)),
        ("demand_m3s", round(q_m3s, 6)),
        ("req_id_mm@Vmax", round(d_req, 1)),
        ("suggested_nom_mm", d_nom),
        ("suggested_nom_in", d_in),
        ("velocity_m_s", round(vel, 2)),
        ("head_pipe_id_mm", d_calc),
        ("static_head_m", args.static_head_m),
        ("pipe_length_m", args.pipe_length_m),
        ("equiv_length_m", round(leq, 1)),
        ("friction_loss_m", round(hf, 2)),
        ("residual_head_m", args.residual_head_m),
        ("total_head_m", round(total_head, 2)),
        ("total_head_ft", round(total_head * M_TO_FT, 1)),
        ("pump_power_kw@65pct", round(power_kw, 2)),
    ]

    print("=== MEP Plumbing Rough Estimate ===")
    print(f"Fixture units : {fu:.1f} WSFU ({args.system}-curve)")
    if breakdown:
        for k, v in breakdown.items():
            print(f"  {k:12s} x{v['count']:g} @ {v['fu_each']:g} FU = {v['fu']:.1f} FU")
    print(f"Demand        : {gpm:.1f} GPM  |  {lps:.2f} L/s")
    print(f"Pipe          : req ID {d_req:.1f} mm @ {args.velocity} m/s -> use {d_nom} mm ({d_in}), v={vel:.2f} m/s")
    print(f"Pump head     : static {args.static_head_m:.1f} + friction {hf:.2f} + residual {args.residual_head_m:.1f} = {total_head:.2f} m ({total_head * M_TO_FT:.1f} ft)")
    print(f"  (friction via Hazen-Williams C={args.hazenc:g}, Leq={leq:.1f} m on {d_calc:g} mm ID)")
    print(f"Pump power    : ~{power_kw:.2f} kW (wire-to-water 65%)")
    print("NOTE: rough sizing only -- verify against local code (IPC/UPC Hunter tables).")

    if args.csv:
        p = Path(args.csv)
        with p.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["parameter", "value"])
            w.writerows(rows)
        print(f"Saved CSV     : {p.resolve()}")

if __name__ == "__main__":
    main()
