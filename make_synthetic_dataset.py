"""Regenerate the illustrative dataset. Values are synthetic, not observed data."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "synthetic_monthly_inputs.csv"

months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
# Artificial seasonal inflows (MCM): low in the dry season, higher during monsoon.
base_inflow = [8, 6, 6, 8, 15, 80, 250, 430, 450, 240, 80, 25]
municipal_demand = [18, 18, 19, 19, 20, 20, 21, 21, 21, 20, 19, 19]
irrigation_demand = [110, 100, 110, 100, 80, 30, 20, 20, 40, 120, 150, 130]
environmental_target = [15, 15, 15, 15, 20, 25, 30, 30, 30, 25, 20, 15]
evaporation = [15, 16, 20, 25, 30, 25, 18, 15, 15, 18, 16, 14]

# Variation is deliberately simple and transparent for an undergraduate prototype.
profiles = [
    (1, "normal", 1.00, [1.00, 0.95, 1.05, 0.90, 1.00, 1.00, 0.95, 1.05, 1.00, 1.05, 0.90, 1.00]),
    (2, "wet", 1.30, [1.10, 0.95, 1.00, 1.10, 1.15, 1.30, 1.20, 1.35, 1.30, 1.25, 1.10, 1.00]),
    (3, "dry", 0.70, [0.80, 0.85, 0.80, 0.85, 0.70, 0.65, 0.60, 0.55, 0.60, 0.70, 0.75, 0.80]),
    (4, "normal-low", 0.95, [0.90, 1.00, 1.00, 0.90, 0.95, 0.95, 1.00, 1.00, 0.95, 0.90, 0.95, 1.00]),
    (5, "severe-dry", 0.50, [0.75, 0.80, 0.75, 0.70, 0.60, 0.50, 0.45, 0.40, 0.45, 0.55, 0.65, 0.70]),
]

fieldnames = [
    "simulation_year", "scenario_label", "month", "month_name", "inflow_mcm",
    "municipal_demand_mcm", "irrigation_demand_mcm", "environmental_flow_target_mcm",
    "potential_evaporation_mcm", "data_status",
]
rows = []
for year, label, factor, monthly_profile in profiles:
    for i, month in enumerate(months):
        inflow = base_inflow[i] * factor * monthly_profile[i]
        rows.append({
            "simulation_year": year,
            "scenario_label": label,
            "month": i + 1,
            "month_name": month,
            "inflow_mcm": round(inflow, 2),
            "municipal_demand_mcm": municipal_demand[i],
            "irrigation_demand_mcm": irrigation_demand[i],
            "environmental_flow_target_mcm": environmental_target[i],
            "potential_evaporation_mcm": evaporation[i],
            "data_status": "synthetic_illustration_not_observed",
        })

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
with OUTPUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
print(f"Wrote {len(rows)} rows to {OUTPUT}")
