from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

dispatch_file = DATA_DIR / "dispatch_signal_latest.csv"

df = pd.read_csv(dispatch_file)

print("\n===== DISPATCH SHAPE =====")
print(df.shape)

print("\n===== PRICE STATE COUNTS =====")
print(df["price_state"].value_counts(dropna=False))

print("\n===== BATTERY ACTION COUNTS =====")
print(df["battery_action"].value_counts(dropna=False))

print("\n===== POWER SOURCE COUNTS =====")
print(df["power_source"].value_counts(dropna=False))

print("\n===== COMPUTE MODE COUNTS =====")
print(df["compute_mode"].value_counts(dropna=False))

print("\n===== DECISION REASON COUNTS =====")
print(df["decision_reason"].value_counts(dropna=False))

print("\n===== SAMPLE ROWS BY DECISION =====")
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
].sample(10, random_state=42))