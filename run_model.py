"""Simple monthly reservoir water-balance demonstration for the Ujani proposal.

IMPORTANT: Input data are synthetic and are not observed Ujani Reservoir records.
Run from the repository root: python code/run_model.py
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT_CSV = ROOT / "data" / "synthetic_monthly_inputs.csv"
MONTHLY_OUTPUT = ROOT / "results" / "baseline_monthly_results.csv"
ANNUAL_OUTPUT = ROOT / "results" / "baseline_annual_summary.csv"
FIGURE_OUTPUT = ROOT / "figures" / "baseline_demand_satisfaction.png"

# Illustrative model parameters only; verify against official records before real analysis.
INITIAL_STORAGE_MCM = 1200.0
MAX_STORAGE_MCM = 2500.0
DEAD_STORAGE_MCM = 150.0


def load_inputs(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    rows.sort(key=lambda row: (int(row["simulation_year"]), int(row["month"])))
    return rows


def allocate_priority(demand: float, available: float) -> tuple[float, float]:
    """Meet one demand category up to the available water and return release, remainder."""
    release = min(demand, max(0.0, available))
    return release, max(0.0, available - release)


def run_model(rows: list[dict[str, str]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    storage = INITIAL_STORAGE_MCM
    monthly_results: list[dict[str, object]] = []
    annual = defaultdict(lambda: {
        "simulation_year": 0, "scenario_label": "", "inflow_mcm": 0.0,
        "evaporation_mcm": 0.0, "potential_evaporation_mcm": 0.0, "municipal_demand_mcm": 0.0,
        "municipal_release_mcm": 0.0, "irrigation_demand_mcm": 0.0,
        "irrigation_release_mcm": 0.0, "environmental_demand_mcm": 0.0,
        "environmental_release_mcm": 0.0, "spill_mcm": 0.0,
        "municipal_deficit_mcm": 0.0, "irrigation_deficit_mcm": 0.0,
        "environmental_deficit_mcm": 0.0, "start_storage_mcm": None,
        "end_storage_mcm": 0.0,
    })

    for row in rows:
        year = int(row["simulation_year"])
        month = int(row["month"])
        scenario = row["scenario_label"]
        inflow = float(row["inflow_mcm"])
        potential_evaporation = float(row["potential_evaporation_mcm"])
        start_storage = storage
        # Keep storage at/above assumed dead storage by capping evaporation when water is scarce.
        actual_evaporation = min(potential_evaporation, max(0.0, start_storage + inflow - DEAD_STORAGE_MCM))
        municipal_demand = float(row["municipal_demand_mcm"])
        irrigation_demand = float(row["irrigation_demand_mcm"])
        environmental_demand = float(row["environmental_flow_target_mcm"])

        # Available water above the assumed dead-storage level after evaporation.
        available = max(0.0, start_storage + inflow - actual_evaporation - DEAD_STORAGE_MCM)
        municipal_release, available = allocate_priority(municipal_demand, available)
        irrigation_release, available = allocate_priority(irrigation_demand, available)
        environmental_release, available = allocate_priority(environmental_demand, available)

        pre_spill_storage = start_storage + inflow - actual_evaporation - municipal_release - irrigation_release - environmental_release
        spill = max(0.0, pre_spill_storage - MAX_STORAGE_MCM)
        storage = min(MAX_STORAGE_MCM, max(DEAD_STORAGE_MCM, pre_spill_storage - spill))

        municipal_deficit = municipal_demand - municipal_release
        irrigation_deficit = irrigation_demand - irrigation_release
        environmental_deficit = environmental_demand - environmental_release

        monthly_results.append({
            "simulation_year": year,
            "scenario_label": scenario,
            "month": month,
            "month_name": row["month_name"],
            "data_status": row["data_status"],
            "start_storage_mcm": round(start_storage, 2),
            "inflow_mcm": round(inflow, 2),
            "potential_evaporation_mcm": round(potential_evaporation, 2),
            "actual_evaporation_mcm": round(actual_evaporation, 2),
            "municipal_demand_mcm": round(municipal_demand, 2),
            "municipal_release_mcm": round(municipal_release, 2),
            "municipal_deficit_mcm": round(municipal_deficit, 2),
            "irrigation_demand_mcm": round(irrigation_demand, 2),
            "irrigation_release_mcm": round(irrigation_release, 2),
            "irrigation_deficit_mcm": round(irrigation_deficit, 2),
            "environmental_flow_target_mcm": round(environmental_demand, 2),
            "environmental_release_mcm": round(environmental_release, 2),
            "environmental_deficit_mcm": round(environmental_deficit, 2),
            "spill_mcm": round(spill, 2),
            "end_storage_mcm": round(storage, 2),
        })

        a = annual[year]
        a["simulation_year"] = year
        a["scenario_label"] = scenario
        if a["start_storage_mcm"] is None:
            a["start_storage_mcm"] = start_storage
        for key, value in [
            ("inflow_mcm", inflow), ("evaporation_mcm", actual_evaporation),
            ("potential_evaporation_mcm", potential_evaporation),
            ("municipal_demand_mcm", municipal_demand), ("municipal_release_mcm", municipal_release),
            ("irrigation_demand_mcm", irrigation_demand), ("irrigation_release_mcm", irrigation_release),
            ("environmental_demand_mcm", environmental_demand), ("environmental_release_mcm", environmental_release),
            ("spill_mcm", spill), ("municipal_deficit_mcm", municipal_deficit),
            ("irrigation_deficit_mcm", irrigation_deficit), ("environmental_deficit_mcm", environmental_deficit),
        ]:
            a[key] += value
        a["end_storage_mcm"] = storage

    annual_results: list[dict[str, object]] = []
    for year in sorted(annual):
        a = annual[year]
        for category in ("municipal", "irrigation", "environmental"):
            demand_key = f"{category}_demand_mcm" if category != "environmental" else "environmental_demand_mcm"
            release_key = f"{category}_release_mcm" if category != "environmental" else "environmental_release_mcm"
            demand = float(a[demand_key])
            release = float(a[release_key])
            a[f"{category}_satisfaction_pct"] = 100.0 * release / demand if demand else 100.0
        annual_results.append({k: round(v, 2) if isinstance(v, float) else v for k, v in a.items()})

    return monthly_results, annual_results


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def make_figure(annual_results: list[dict[str, object]]) -> None:
    import matplotlib.pyplot as plt

    years = [f"Y{r['simulation_year']}\n{r['scenario_label']}" for r in annual_results]
    x = list(range(len(years)))
    width = 0.24
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for offset, category, label in [
        (-width, "municipal_satisfaction_pct", "Municipal supply"),
        (0, "irrigation_satisfaction_pct", "Irrigation"),
        (width, "environmental_satisfaction_pct", "Environmental flow"),
    ]:
        values = [float(r[category]) for r in annual_results]
        ax.bar([i + offset for i in x], values, width=width, label=label)
    ax.set_ylabel("Annual demand satisfied (%)")
    ax.set_xlabel("Synthetic simulation year / inflow condition")
    ax.set_title("Baseline rule: annual demand satisfaction (synthetic demonstration)")
    ax.set_ylim(0, 105)
    ax.set_xticks(x, years)
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False, ncols=3, loc="lower left")
    fig.text(0.5, 0.01, "Illustrative synthetic inputs only; not observed Ujani Reservoir performance.", ha="center", fontsize=9)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    FIGURE_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE_OUTPUT, dpi=180, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    rows = load_inputs(INPUT_CSV)
    monthly, annual = run_model(rows)
    write_csv(MONTHLY_OUTPUT, monthly)
    write_csv(ANNUAL_OUTPUT, annual)
    make_figure(annual)
    print(f"Read {len(rows)} synthetic monthly records.")
    print(f"Wrote {MONTHLY_OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {ANNUAL_OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {FIGURE_OUTPUT.relative_to(ROOT)}")
    print("Reminder: results are illustrative and must not be described as measured Ujani observations.")


if __name__ == "__main__":
    main()
