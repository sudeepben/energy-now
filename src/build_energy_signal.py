import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

DEMAND_LATEST = DATA / "demand_hourly_CISO_latest.csv"
PRICE_LATEST = DATA / "caiso_lmp_dam_hourly_TH_NP15_GEN-APND_latest.csv"

OUT_SIGNAL_LATEST = DATA / "energy_signal_latest.csv"
OUT_SIGNAL_NOW = DATA / "energy_signal_now.json"

def load_demand_total() -> pd.DataFrame:
    if not DEMAND_LATEST.exists():
        raise FileNotFoundError(f"Missing: {DEMAND_LATEST}. Run pull_demand_hourly.py first.")

    d = pd.read_csv(DEMAND_LATEST)
    # period is UTC timestamp from your pull script
    d["period"] = pd.to_datetime(d["period"], utc=True, errors="coerce")
    d["value"] = pd.to_numeric(d["value"], errors="coerce")

    # Total CAISO demand per hour (sum across subba)
    demand_total = (
        d.groupby("period", as_index=False)["value"]
         .sum()
         .rename(columns={"period": "ts_utc", "value": "demand_mwh"})
         .sort_values("ts_utc")
         .reset_index(drop=True)
    )
    return demand_total

def load_price() -> pd.DataFrame:
    if not PRICE_LATEST.exists():
        raise FileNotFoundError(f"Missing: {PRICE_LATEST}. Run pull_caiso_lmp_dam_hourly.py first.")

    p = pd.read_csv(PRICE_LATEST)
    p["ts_utc"] = pd.to_datetime(p["ts_utc"], utc=True, errors="coerce")
    p["lmp_usd_per_mwh"] = pd.to_numeric(p["lmp_usd_per_mwh"], errors="coerce")
    p["price_usd_per_kwh"] = pd.to_numeric(p["price_usd_per_kwh"], errors="coerce")

    # Keep only the columns we need
    keep = ["ts_utc", "lmp_usd_per_mwh", "price_usd_per_kwh", "NODE", "MARKET_RUN_ID", "xml_data_item"]
    keep = [c for c in keep if c in p.columns]
    return p[keep].sort_values("ts_utc").reset_index(drop=True)

def label_prices(df: pd.DataFrame) -> pd.DataFrame:
    # Use distribution from the available window (later we’ll expand to 7d+)
    q25 = df["price_usd_per_kwh"].quantile(0.25)
    q75 = df["price_usd_per_kwh"].quantile(0.75)

    def lab(x):
        if pd.isna(x):
            return "UNKNOWN"
        if x <= q25:
            return "CHEAP"
        if x >= q75:
            return "EXPENSIVE"
        return "NORMAL"

    df["price_label"] = df["price_usd_per_kwh"].apply(lab)
    df["q25_price_usd_per_kwh"] = q25
    df["q75_price_usd_per_kwh"] = q75
    return df

def main():
    demand = load_demand_total()
    price = load_price()

    # Merge on timestamp
    merged = demand.merge(price, on="ts_utc", how="inner")

    if merged.empty:
        print("Merged dataset is empty. Check if timestamps overlap between demand and price files.")
        print("Demand range:", demand["ts_utc"].min(), "->", demand["ts_utc"].max())
        print("Price range:", price["ts_utc"].min(), "->", price["ts_utc"].max())
        return

    merged = label_prices(merged)

    # Add time features (useful later for modeling)
    merged["hour_utc"] = merged["ts_utc"].dt.hour
    merged["dow_utc"] = merged["ts_utc"].dt.day_name()

    merged.to_csv(OUT_SIGNAL_LATEST, index=False)
    print(f"Saved -> {OUT_SIGNAL_LATEST} ({len(merged)} rows)")

    # "Now" record = latest timestamp in merged
    latest = merged.sort_values("ts_utc").iloc[-1].to_dict()

    # Convert Timestamp to ISO for JSON
    latest["ts_utc"] = pd.Timestamp(latest["ts_utc"]).isoformat()

    with open(OUT_SIGNAL_NOW, "w", encoding="utf-8") as f:
        json.dump(latest, f, indent=2)
    print(f"Saved -> {OUT_SIGNAL_NOW}")
    print("NOW snapshot:", latest)

if __name__ == "__main__":
    main()