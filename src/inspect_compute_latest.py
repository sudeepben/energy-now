from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

compute_file = DATA_DIR / "compute_latest.csv"

df = pd.read_csv(compute_file)

print("\n===== COMPUTE LATEST SHAPE =====")
print(df.shape)

print("\n===== COLUMNS =====")
print(df.columns.tolist())

print("\n===== NUMERIC SUMMARY =====")
cols = [
    "gpu_utilization_pct",
    "tokens_per_sec",
    "power_kw_it",
    "power_kw_cooling",
    "power_kw_total",
    "battery_soc_pct",
    "electricity_price_usd_per_kwh",
    "ambient_temp_c",
    "gpu_temp_avg_c",
    "gpu_temp_max_c",
    "cooling_to_it_ratio",
    "power_per_token",
]
print(df[cols].describe())

print("\n===== BATTERY STATE COUNTS =====")
print(df["battery_state"].value_counts(dropna=False))

print("\n===== THERMAL STATE COUNTS =====")
print(df["thermal_state"].value_counts(dropna=False))

print("\n===== WORKLOAD STATE COUNTS =====")
print(df["workload_state"].value_counts(dropna=False))