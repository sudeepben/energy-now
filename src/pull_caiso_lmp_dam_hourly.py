import os
import io
import zipfile
from pathlib import Path
from datetime import datetime, timedelta
import requests
import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

OASIS_BASE = "https://oasis.caiso.com/oasisapi/SingleZip"
NODE = os.getenv("CAISO_NODE", "TH_NP15_GEN-APND")

def fmt_oasis_utc(dt: datetime) -> str:
    return dt.strftime("%Y%m%dT%H:%M-0000")

def read_singlezip_csv_from_bytes(content: bytes) -> pd.DataFrame:
    with zipfile.ZipFile(io.BytesIO(content)) as z:
        csv_names = [n for n in z.namelist() if n.lower().endswith(".csv")]
        if not csv_names:
            raise ValueError(f"No CSV found in zip. Files: {z.namelist()}")
        with z.open(csv_names[0]) as f:
            return pd.read_csv(f)

def main():
    end_utc = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    start_utc = end_utc - timedelta(hours=24)

    params = {
        "queryname": "PRC_LMP",
        "market_run_id": "DAM",
        "node": NODE,
        "startdatetime": fmt_oasis_utc(start_utc),
        "enddatetime": fmt_oasis_utc(end_utc),
        "version": 12,
        "resultformat": 6,
    }

    r = requests.get(OASIS_BASE, params=params, timeout=90)
    print("Request URL:", r.url)
    r.raise_for_status()

    df = read_singlezip_csv_from_bytes(r.content)

    # Standardize columns
    cols = {c.lower(): c for c in df.columns}

    # Time column is present in your output
    time_col = cols.get("intervalstarttime_gmt")
    if not time_col:
        print("Columns:", df.columns.tolist())
        raise ValueError("Missing INTERVALSTARTTIME_GMT")

    df[time_col] = pd.to_datetime(df[time_col], utc=True, errors="coerce")

    # In this PRC_LMP extract, the numeric value is in MW, and XML_DATA_ITEM tells what it is
    value_col = cols.get("mw")
    item_col = cols.get("xml_data_item")
    if not value_col or not item_col:
        print("Columns:", df.columns.tolist())
        raise ValueError("Expected MW and XML_DATA_ITEM columns not found")

    df[value_col] = pd.to_numeric(df[value_col], errors="coerce")

    # Inspect what "items" exist (helpful for debugging)
    items = sorted(df[item_col].dropna().unique().tolist())
    print("XML_DATA_ITEM values (sample):", items[:12], "..." if len(items) > 12 else "")

    # Keep only price rows.
    # Commonly, total LMP rows are tagged with something containing 'LMP'
    price_df = df[df[item_col].astype(str).str.contains("LMP", case=False, na=False)].copy()

    if price_df.empty:
        # Fallback: sometimes it's tagged differently; print a hint
        print("No rows matched 'LMP' in XML_DATA_ITEM. Try checking XML_DATA_ITEM values above.")
        raise ValueError("Could not identify LMP rows in the response.")

    # If there are multiple LMP components, prefer the "total" one if present
    # (keep the most informative subset; if not available, keep all LMP-tagged rows)
    total_mask = price_df[item_col].astype(str).str.contains("TOTAL", case=False, na=False)
    if total_mask.any():
        price_df = price_df[total_mask].copy()

    # Rename for clarity
    price_df = price_df.rename(columns={
        time_col: "ts_utc",
        value_col: "lmp_usd_per_mwh",
        item_col: "xml_data_item",
    })

    # Convert $/MWh -> $/kWh
    price_df["price_usd_per_kwh"] = price_df["lmp_usd_per_mwh"] / 1000.0

    out_dir = ROOT / "data"
    out_dir.mkdir(exist_ok=True)

    stamp = end_utc.strftime("%Y%m%dT%H%MZ")
    archive_path = out_dir / f"caiso_lmp_dam_hourly_{NODE}_{stamp}.csv"
    latest_path = out_dir / f"caiso_lmp_dam_hourly_{NODE}_latest.csv"

    price_df.to_csv(archive_path, index=False)
    price_df.to_csv(latest_path, index=False)

    print(f"Saved -> {archive_path}")
    print(f"Updated latest -> {latest_path}")
    print("Head row:", price_df.iloc[0].to_dict())

if __name__ == "__main__":
    main()