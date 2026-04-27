from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

dispatch_file = DATA_DIR / "dispatch_signal_latest.csv"

df = pd.read_csv(dispatch_file)

price_col = "electricity_price_usd_per_kwh"

print("\n===== PRICE SUMMARY =====")
print(df[price_col].describe())

print("\n===== PRICE QUANTILES =====")
print(df[price_col].quantile([0.10, 0.25, 0.50, 0.75, 0.90, 0.95]))

print("\n===== UNIQUE SAMPLE PRICES =====")
print(df[price_col].sort_values().head(20).tolist())

print("\n===== TOP 20 HIGHEST PRICES =====")
print(df[price_col].sort_values(ascending=False).head(20).tolist())