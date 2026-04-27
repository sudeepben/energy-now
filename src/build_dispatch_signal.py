from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

INPUT_FILE = DATA_DIR / "compute_latest.csv"
OUTPUT_FILE = DATA_DIR / "dispatch_signal_latest.csv"
NOW_FILE = DATA_DIR / "dispatch_now.json"


def classify_price(price: float) -> str:
    if price <= 0.15:
        return "cheap"
    elif price >= 0.35:
        return "expensive"
    else:
        return "normal"


def decide_battery_action(price_state: str, battery_state: str) -> str:
    if price_state == "cheap" and battery_state != "high":
        return "charge"
    elif price_state == "expensive" and battery_state != "low":
        return "discharge"
    return "hold"


def decide_power_source(price_state: str, battery_state: str) -> str:
    if price_state == "cheap":
        return "grid"
    elif price_state == "expensive" and battery_state != "low":
        return "battery"
    return "hybrid"


def decide_compute_mode(thermal_state: str, workload_state: str, price_state: str) -> str:
    if thermal_state == "hot":
        return "critical_only"
    elif thermal_state == "warm" and price_state == "expensive":
        return "reduced"
    elif workload_state == "high":
        return "full"
    elif workload_state == "medium":
        return "reduced"
    return "critical_only"


def decide_reason(
    battery_action: str,
    power_source: str,
    compute_mode: str,
    thermal_state: str,
    workload_state: str,
    price_state: str
) -> str:
    if thermal_state == "hot":
        return "thermal_limit_high"

    if price_state == "expensive" and power_source == "battery":
        if compute_mode == "critical_only":
            return "expensive_battery_critical_only"
        elif compute_mode == "reduced":
            return "expensive_battery_reduce_load"
        return "high_price_use_battery"

    if price_state == "cheap" and battery_action == "charge":
        if workload_state == "high":
            return "cheap_power_charge_high_workload"
        elif workload_state == "medium":
            return "cheap_power_charge_medium_workload"
        return "cheap_power_charge_low_workload"

    if price_state == "cheap" and power_source == "grid":
        if compute_mode == "full":
            return "cheap_grid_run_full"
        elif compute_mode == "reduced":
            return "cheap_grid_reduce_mode"
        return "cheap_grid_critical_only"

    if price_state == "normal":
        if compute_mode == "full":
            return "normal_price_run_full"
        elif compute_mode == "reduced":
            return "normal_price_reduce_mode"
        return "normal_price_critical_only"

    return "fallback_dispatch_rule"


def main():
    print("Loading compute_latest.csv...")
    df = pd.read_csv(INPUT_FILE)

    print("Creating dispatch decisions...")

    df["price_state"] = df["electricity_price_usd_per_kwh"].apply(classify_price)

    df["battery_action"] = df.apply(
        lambda row: decide_battery_action(row["price_state"], row["battery_state"]),
        axis=1
    )

    df["power_source"] = df.apply(
        lambda row: decide_power_source(row["price_state"], row["battery_state"]),
        axis=1
    )

    df["compute_mode"] = df.apply(
        lambda row: decide_compute_mode(
            row["thermal_state"],
            row["workload_state"],
            row["price_state"]
        ),
        axis=1
    )

    df["decision_reason"] = df.apply(
        lambda row: decide_reason(
            row["battery_action"],
            row["power_source"],
            row["compute_mode"],
            row["thermal_state"],
            row["workload_state"],
            row["price_state"]
        ),
        axis=1
    )
    
    
    # ---------------- COST CALCULATION ----------------

    # Assume:
    # if using battery → cost = 0 (already stored energy)
    # if using grid → cost = price * power

    df["cost_actual"] = df.apply(
        lambda row: row["electricity_price_usd_per_kwh"] * row["power_kw_total"]
        if row["power_source"] == "grid"
        else 0,
        axis=1
    )

    # Baseline: always use grid
    df["cost_baseline"] = df["electricity_price_usd_per_kwh"] * df["power_kw_total"]

    # Savings
    df["cost_savings"] = df["cost_baseline"] - df["cost_actual"]
    
    print(f"Saving dispatch output to: {OUTPUT_FILE}")
    df.to_csv(OUTPUT_FILE, index=False)

    # Save latest row as JSON for "current system decision"
    latest_row = df.sort_values("timestamp").iloc[-1]

    dispatch_now = {
        "timestamp": str(latest_row["timestamp"]),
        "cluster_id": latest_row["cluster_id"],
        "electricity_price_usd_per_kwh": float(latest_row["electricity_price_usd_per_kwh"]),
        "price_state": latest_row["price_state"],
        "battery_soc_pct": float(latest_row["battery_soc_pct"]),
        "battery_state": latest_row["battery_state"],
        "thermal_state": latest_row["thermal_state"],
        "workload_state": latest_row["workload_state"],
        "battery_action": latest_row["battery_action"],
        "power_source": latest_row["power_source"],
        "compute_mode": latest_row["compute_mode"],
        "decision_reason": latest_row["decision_reason"],
    }

    print(f"Saving current dispatch status to: {NOW_FILE}")
    pd.Series(dispatch_now).to_json(NOW_FILE, indent=2)

    print("\nDone.")
    print("Output shape:", df.shape)

    print("\nDispatch columns added:")
    print([
        "price_state",
        "battery_action",
        "power_source",
        "compute_mode",
        "decision_reason"
    ])

    print("\nFirst 10 rows of dispatch view:")
    print(df[
        [
            "timestamp",
            "electricity_price_usd_per_kwh",
            "price_state",
            "battery_state",
            "thermal_state",
            "workload_state",
            "battery_action",
            "power_source",
            "compute_mode",
            "decision_reason"
        ]
    ].head(10))


if __name__ == "__main__":
    main()