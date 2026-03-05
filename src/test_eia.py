import os
from pathlib import Path
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

API_KEY = os.getenv("EIA_API_KEY")
if not API_KEY:
    raise ValueError(f"Missing EIA_API_KEY in {ROOT / '.env'}")

url = "https://api.eia.gov/v2/electricity/rto/fuel-type-data/data/"
params = {
    "api_key": API_KEY,
    "frequency": "hourly",
    "data[0]": "value",
    "sort[0][column]": "period",
    "sort[0][direction]": "desc",
    "length": 5
}

r = requests.get(url, params=params, timeout=30)
print("Request URL:", r.url)
r.raise_for_status()

j = r.json()
rows = j.get("response", {}).get("data", [])
print("OK ✅ Status:", r.status_code)
print("Rows returned:", len(rows))
print("Sample rows:")
for row in rows[:3]:
    print(row)