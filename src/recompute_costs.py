"""Re-apply the honest cost model to an existing dispatch_signal_latest.csv.

The full pipeline (build_dispatch_signal.py) needs upstream telemetry CSVs that
aren't checked into the repo. This script lets you regenerate the cost columns
in-place from the dispatch CSV alone, so the dashboard reflects the new model.
"""
from pathlib import Path
import json
import pandas as pd

from build_dispatch_signal import compute_costs

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DISPATCH_CSV = DATA_DIR / "dispatch_signal_latest.csv"
NOW_JSON = DATA_DIR / "dispatch_now.json"


def main():
    df = pd.read_csv(DISPATCH_CSV)
    df = compute_costs(df)

    df.to_csv(DISPATCH_CSV, index=False)

    latest = df.sort_values("timestamp").iloc[-1]
    now = json.loads(NOW_JSON.read_text()) if NOW_JSON.exists() else {}
    now.update({
        "timestamp": str(latest["timestamp"]),
        "electricity_price_usd_per_kwh": float(latest["electricity_price_usd_per_kwh"]),
        "price_state": latest["price_state"],
        "battery_soc_pct": float(latest["battery_soc_pct"]),
        "battery_state": latest["battery_state"],
        "thermal_state": latest["thermal_state"],
        "workload_state": latest["workload_state"],
        "battery_action": latest["battery_action"],
        "power_source": latest["power_source"],
        "compute_mode": latest["compute_mode"],
        "decision_reason": latest["decision_reason"],
    })
    NOW_JSON.write_text(json.dumps(now, indent=2))

    baseline = df["cost_baseline"].sum()
    actual = df["cost_actual"].sum()
    savings = df["cost_savings"].sum()
    pct = (savings / baseline) * 100 if baseline else 0
    print(f"Baseline cost:  ${baseline:,.2f}")
    print(f"Actual cost:    ${actual:,.2f}")
    print(f"Savings:        ${savings:,.2f}  ({pct:.1f}%)")


if __name__ == "__main__":
    main()
