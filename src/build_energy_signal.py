import json
from pathlib import Path
import pandas as pd
from zoneinfo import ZoneInfo

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
    # Add time buckets first
    df["hour_utc"] = df["ts_utc"].dt.hour
    df["dow_utc"] = df["ts_utc"].dt.day_name()

    # Hour-of-day baseline thresholds (better than global)
    grouped = df.groupby("hour_utc")["price_usd_per_kwh"]
    q25_by_hr = grouped.quantile(0.25)
    q75_by_hr = grouped.quantile(0.75)

    def lab(row):
        x = row["price_usd_per_kwh"]
        h = row["hour_utc"]
        if pd.isna(x):
            return "UNKNOWN"
        q25 = q25_by_hr.loc[h]
        q75 = q75_by_hr.loc[h]
        if x <= q25:
            return "CHEAP"
        if x >= q75:
            return "EXPENSIVE"
        return "NORMAL"

    df["price_label"] = df.apply(lab, axis=1)

    # Store the thresholds used for that row (useful for explanation)
    df["q25_hr_price_usd_per_kwh"] = df["hour_utc"].map(q25_by_hr)
    df["q75_hr_price_usd_per_kwh"] = df["hour_utc"].map(q75_by_hr)

    return df

def print_status(now_row: dict):
    tz = ZoneInfo("America/Denver")

    ts_utc = pd.to_datetime(now_row["ts_utc"], utc=True)
    ts_local = ts_utc.tz_convert(tz)

    price = now_row["price_usd_per_kwh"]
    lmp = now_row["lmp_usd_per_mwh"]
    demand = now_row["demand_mwh"]
    label = now_row["price_label"]

    q25 = now_row.get("q25_hr_price_usd_per_kwh")
    q75 = now_row.get("q75_hr_price_usd_per_kwh")

    print("\n================= ENERGY-NOW =================")
    print(f"Time (local): {ts_local.strftime('%Y-%m-%d %I:%M %p %Z')}  |  Time (UTC): {ts_utc.strftime('%Y-%m-%d %H:00 UTC')}")
    print(f"CAISO Node: {now_row.get('NODE')}  |  Market: {now_row.get('MARKET_RUN_ID')}  |  Metric: {now_row.get('xml_data_item')}")
    print(f"Price: ${price:.5f} / kWh   (=${lmp:.2f} / MWh)")
    print(f"Demand (CAISO total): {int(demand)} MWh (sum of sub-BA demand)")
    print(f"Signal: {label}")

    if q25 is not None and q75 is not None:
        print(f"Hour baseline (UTC hour={now_row.get('hour_utc')}): CHEAP <= {q25:.5f}, EXPENSIVE >= {q75:.5f} ($/kWh)")
    print("================================================\n")

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
    
    print_status(latest)

if __name__ == "__main__":
    main()