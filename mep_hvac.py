#!/usr/bin/env python3
"""HVAC cooling load estimator + duct size suggestion. Stdlib only."""
import argparse
import csv
import math
import sys

# Rule-of-thumb factors (documented in output)
W_PER_M2_ENVELOPE = 120.0   # envelope + ventilation allowance per m^2 floor area
W_PER_PERSON = 130.0        # sensible+latent per occupant
W_PER_W_LIGHTING = 1.0      # lighting watts -> cooling watts (all becomes heat)

DUCT_TABLE = [  # (max airflow m3/s, suggested round duct mm)
    (0.05, 150), (0.10, 200), (0.20, 250), (0.35, 300),
    (0.50, 350), (0.75, 400), (1.00, 450), (1.50, 500),
    (2.00, 550), (3.00, 600), (float("inf"), 650),
]


def cooling_load(area_m2, occupancy, lighting_w):
    envelope = area_m2 * W_PER_M2_ENVELOPE
    people = occupancy * W_PER_PERSON
    lights = lighting_w * W_PER_W_LIGHTING
    sensible_subtotal = envelope + lights + people * 0.7
    total = (envelope + people + lights) * 1.10  # 10% safety factor
    return {
        "envelope_w": round(envelope, 1),
        "people_w": round(people, 1),
        "lighting_w": round(lights, 1),
        "sensible_w": round(sensible_subtotal, 1),
        "total_w": round(total, 1),
        "total_kw": round(total / 1000, 2),
        "total_btu_hr": round(total * 3.412, 0),
        "tons": round(total / 3517, 2),
    }


def duct_size(total_w):
    # Airflow: Q = P / (rho * cp * dT), dT=10K supply-return
    airflow = total_w / (1.2 * 1005 * 10)
    dia = next(d for limit, d in DUCT_TABLE if airflow <= limit)
    # velocity check for noise (V = Q / A)
    area = math.pi * (dia / 2000) ** 2
    velocity = airflow / area if area else 0
    return {"airflow_m3s": round(airflow, 3), "airflow_cfm": round(airflow * 2118.88, 0),
            "duct_mm": dia, "velocity_ms": round(velocity, 1)}


def main(argv=None):
    p = argparse.ArgumentParser(description="HVAC cooling load estimator")
    p.add_argument("--area", type=float, required=True, help="Room floor area in m^2")
    p.add_argument("--occupancy", type=int, required=True, help="Number of occupants")
    p.add_argument("--lighting", type=float, required=True, help="Lighting load in watts")
    p.add_argument("--csv", default="hvac_result.csv", help="CSV output path")
    p.add_argument("--no-csv", action="store_true", help="Skip CSV save")
    a = p.parse_args(argv)

    if a.area <= 0 or a.occupancy < 0 or a.lighting < 0:
        p.error("area must be >0; occupancy/lighting must be >=0")

    load = cooling_load(a.area, a.occupancy, a.lighting)
    duct = duct_size(load["total_w"])

    print("=== HVAC Cooling Load Estimate ===")
    print(f"Inputs: area={a.area} m2, occupancy={a.occupancy}, lighting={a.lighting} W")
    print(f"  Envelope/ventilation : {load['envelope_w']:>9.1f} W")
    print(f"  Occupants            : {load['people_w']:>9.1f} W")
    print(f"  Lighting             : {load['lighting_w']:>9.1f} W")
    print(f"  Sensible subtotal    : {load['sensible_w']:>9.1f} W")
    print(f"  Total (+10% safety)  : {load['total_w']:>9.1f} W "
          f"({load['total_kw']} kW / {load['total_btu_hr']:.0f} BTU/hr / {load['tons']} tons)")
    print(f"Duct: {duct['airflow_m3s']} m3/s ({duct['airflow_cfm']:.0f} CFM) -> "
          f"round {duct['duct_mm']} mm dia @ {duct['velocity_ms']} m/s")

    if not a.no_csv:
        row = {"area_m2": a.area, "occupancy": a.occupancy, "lighting_w": a.lighting,
               **load, **duct}
        with open(a.csv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(row.keys()))
            w.writeheader()
            w.writerow(row)
        print(f"Saved: {a.csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
