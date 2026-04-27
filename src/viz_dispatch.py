from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"

REPORTS_DIR.mkdir(exist_ok=True)

dispatch_file = DATA_DIR / "dispatch_signal_latest.csv"
df = pd.read_csv(dispatch_file)

df["timestamp"] = pd.to_datetime(df["timestamp"])


# -------- Chart 1: Battery SOC over time --------
plt.figure(figsize=(12, 5))
plt.plot(df["timestamp"], df["battery_soc_pct"])
plt.title("Battery State of Charge Over Time")
plt.xlabel("Time")
plt.ylabel("Battery SOC (%)")
plt.tight_layout()
plt.savefig(REPORTS_DIR / "battery_soc.png")
plt.close()


# -------- Chart 2: Price vs Battery Action --------
action_map = {"charge": 1, "hold": 0, "discharge": -1}
df["battery_action_numeric"] = df["battery_action"].map(action_map)

plt.figure(figsize=(12, 5))
plt.plot(df["timestamp"], df["electricity_price_usd_per_kwh"], label="Price")
plt.plot(df["timestamp"], df["battery_action_numeric"], label="Battery Action")
plt.title("Price vs Battery Action")
plt.legend()
plt.tight_layout()
plt.savefig(REPORTS_DIR / "price_vs_battery_action.png")
plt.close()


# -------- Chart 3: Compute Mode Timeline --------
mode_map = {"full": 2, "reduced": 1, "critical_only": 0}
df["compute_mode_numeric"] = df["compute_mode"].map(mode_map)

plt.figure(figsize=(12, 5))
plt.plot(df["timestamp"], df["compute_mode_numeric"])
plt.title("Compute Mode Over Time")
plt.xlabel("Time")
plt.ylabel("Mode (2=full, 1=reduced, 0=critical)")
plt.tight_layout()
plt.savefig(REPORTS_DIR / "compute_mode.png")
plt.close()

# -------- Chart 4: Cost Comparison --------
df["cumulative_baseline"] = df["cost_baseline"].cumsum()
df["cumulative_actual"] = df["cost_actual"].cumsum()

plt.figure(figsize=(12, 5))
plt.plot(df["timestamp"], df["cumulative_baseline"], label="Baseline Cost")
plt.plot(df["timestamp"], df["cumulative_actual"], label="Actual Cost")
plt.title("Cumulative Cost: Baseline vs Optimized")
plt.xlabel("Time")
plt.ylabel("Cost ($)")
plt.legend()
plt.tight_layout()
plt.savefig(REPORTS_DIR / "cost_comparison.png")
plt.close()


print("Charts saved in reports/")