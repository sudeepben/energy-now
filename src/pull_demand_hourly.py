import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
import requests
import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

API_KEY = os.getenv("EIA_API_KEY")
if not API_KEY:
    raise ValueError(f"Missing EIA_API_KEY in {ROOT / '.env'}")

PARENT = os.getenv("EIA_PARENT", "CISO")  # CAISO example
URL = "https://api.eia.gov/v2/electricity/rto/region-sub-ba-data/data/"

def iso_hour(dt):
    return dt.strftime("%Y-%m-%dT%H")

def fetch_all(start_dt_utc: datetime, end_dt_utc: datetime, page_size: int = 5000):
    """Fetch all pages from EIA v2 (uses offset pagination)."""
    all_rows = []
    offset = 0

    while True:
        params = {
            "api_key": API_KEY,
            "frequency": "hourly",
            "data[0]": "value",
            "facets[parent][]": PARENT,
            "start": iso_hour(start_dt_utc),
            "end": iso_hour(end_dt_utc),
            "sort[0][column]": "period",
            "sort[0][direction]": "asc",
            "length": page_size,
            "offset": offset,
        }

        r = requests.get(URL, params=params, timeout=60)
        print("Request URL:", r.url)
        r.raise_for_status()

        payload = r.json().get("response", {})
        rows = payload.get("data", [])
        if not rows:
            break

        all_rows.extend(rows)

        # If we got fewer than page_size, we're done
        if len(rows) < page_size:
            break

        offset += page_size

    return all_rows

def clean(df: pd.DataFrame) -> pd.DataFrame:
    # period is like 2026-02-28T07 (hourly). Keep as UTC for now.
    df["period"] = pd.to_datetime(df["period"], format="%Y-%m-%dT%H", utc=True)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.sort_values(["period", "subba"]).reset_index(drop=True)
    return df

def main():
    end_dt = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    LOOKBACK_DAYS = int(os.getenv("LOOKBACK_DAYS", "7"))
    start_dt = end_dt - timedelta(days=LOOKBACK_DAYS)

    rows = fetch_all(start_dt, end_dt)
    if not rows:
        print("No rows returned.")
        return

    df = clean(pd.DataFrame(rows))

    out_dir = ROOT / "data"
    out_dir.mkdir(exist_ok=True)

    # Timestamped archive file
    stamp = end_dt.strftime("%Y%m%dT%H%MZ")
    archive_path = out_dir / f"demand_hourly_{PARENT}_{stamp}.csv"
    df.to_csv(archive_path, index=False)

    # Always-updated "latest" file
    latest_path = out_dir / f"demand_hourly_{PARENT}_latest.csv"
    df.to_csv(latest_path, index=False)

    print(f"Saved {len(df)} rows -> {archive_path}")
    print(f"Updated latest -> {latest_path}")
    print("First row:", df.iloc[0].to_dict())
    print("Last row:", df.iloc[-1].to_dict())

if __name__ == "__main__":
    main()