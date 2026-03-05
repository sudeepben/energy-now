from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT_DIR = ROOT / "reports" / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SIGNAL = DATA / "energy_signal_latest.csv"

def savefig(path: Path):
    plt.tight_layout()
    plt.savefig(path, dpi=200)
    plt.close()
    print(f"Saved figure -> {path}")

def load_signal() -> pd.DataFrame:
    if not SIGNAL.exists():
        raise FileNotFoundError(f"Missing {SIGNAL}. Run pipeline first: python src/run_pipeline.py")

    df = pd.read_csv(SIGNAL)
    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True, errors="coerce")
    df["price_usd_per_kwh"] = pd.to_numeric(df["price_usd_per_kwh"], errors="coerce")
    df["demand_mwh"] = pd.to_numeric(df["demand_mwh"], errors="coerce")

    # Ensure hour/dow exist
    if "hour_utc" not in df.columns:
        df["hour_utc"] = df["ts_utc"].dt.hour
    if "dow_utc" not in df.columns:
        df["dow_utc"] = df["ts_utc"].dt.day_name()

    return df.sort_values("ts_utc").reset_index(drop=True)

def plot_price_timeseries(df: pd.DataFrame):
    plt.figure()
    plt.plot(df["ts_utc"], df["price_usd_per_kwh"], marker="o", linewidth=1)

    plt.title("CAISO Day-Ahead Price (LMP) — $/kWh (Hub)")
    plt.xlabel("Time (UTC)")
    plt.ylabel("Price ($/kWh)")
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%m-%d\n%H:%M"))
    plt.grid(True, linewidth=0.3)

    savefig(OUT_DIR / "01_price_timeseries.png")

def plot_demand_timeseries(df: pd.DataFrame):
    plt.figure()
    plt.plot(df["ts_utc"], df["demand_mwh"], marker="o", linewidth=1)

    plt.title("CAISO Total Demand (sum of sub-BA demand) — MWh")
    plt.xlabel("Time (UTC)")
    plt.ylabel("Demand (MWh)")
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%m-%d\n%H:%M"))
    plt.grid(True, linewidth=0.3)

    savefig(OUT_DIR / "02_demand_timeseries.png")

def plot_demand_vs_price_scatter(df: pd.DataFrame):
    plt.figure()
    plt.scatter(df["demand_mwh"], df["price_usd_per_kwh"])
    plt.title("Demand vs Price (CAISO) — last window")
    plt.xlabel("Demand (MWh)")
    plt.ylabel("Price ($/kWh)")
    plt.grid(True, linewidth=0.3)

    savefig(OUT_DIR / "03_demand_vs_price_scatter.png")

def plot_hourly_profile(df: pd.DataFrame):
    # Average price by hour (UTC)
    g = df.groupby("hour_utc")["price_usd_per_kwh"].agg(["mean", "median"]).reset_index()

    plt.figure()
    plt.plot(g["hour_utc"], g["mean"], marker="o", label="Mean")
    plt.plot(g["hour_utc"], g["median"], marker="o", label="Median")
    plt.title("Hourly Price Profile (UTC hour)")
    plt.xlabel("Hour of day (UTC)")
    plt.ylabel("Price ($/kWh)")
    plt.xticks(range(0, 24, 1))
    plt.grid(True, linewidth=0.3)
    plt.legend()

    savefig(OUT_DIR / "04_hourly_price_profile.png")

def plot_heatmap_dow_hour(df: pd.DataFrame):
    # Heatmap: avg price by day-of-week and hour
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    pivot = (
        df.pivot_table(index="dow_utc", columns="hour_utc", values="price_usd_per_kwh", aggfunc="mean")
          .reindex(order)
    )

    plt.figure()
    plt.imshow(pivot.values, aspect="auto")
    plt.title("Avg Price Heatmap — Day of Week vs Hour (UTC)")
    plt.xlabel("Hour (UTC)")
    plt.ylabel("Day of Week")
    plt.xticks(ticks=range(0, 24, 1), labels=[str(i) for i in range(24)], rotation=0)
    plt.yticks(ticks=range(len(pivot.index)), labels=pivot.index.tolist())

    plt.colorbar(label="Price ($/kWh)")
    savefig(OUT_DIR / "05_heatmap_dow_hour.png")

def plot_box_by_hour(df: pd.DataFrame):
    # Boxplot price by hour (UTC)
    hours = list(range(24))
    data = [df.loc[df["hour_utc"] == h, "price_usd_per_kwh"].dropna().values for h in hours]

    plt.figure()
    plt.boxplot(data, showfliers=False)
    plt.title("Price Distribution by Hour (UTC) — Boxplot")
    plt.xlabel("Hour (UTC)")
    plt.ylabel("Price ($/kWh)")
    plt.xticks(ticks=range(1, 25), labels=[str(h) for h in hours], rotation=0)
    plt.grid(True, axis="y", linewidth=0.3)

    savefig(OUT_DIR / "06_boxplot_price_by_hour.png")

def main():
    df = load_signal()
    plot_price_timeseries(df)
    plot_demand_timeseries(df)
    plot_demand_vs_price_scatter(df)
    plot_hourly_profile(df)
    plot_heatmap_dow_hour(df)
    plot_box_by_hour(df)

    print("\n✅ Visual report complete.")
    print(f"Open: {OUT_DIR}")

if __name__ == "__main__":
    main()