# energy-now

# Energy-Now (CAISO + EIA)

A small data pipeline that answers: **“Is power cheap or expensive right now?”** using:
- **EIA Open Data API** → CAISO demand (sub-BA demand aggregated to total demand)
- **CAISO OASIS API** → Day-Ahead hourly LMP (hub: `TH_NP15_GEN-APND`)
- A join + labeling step to classify hourly price as **CHEAP / NORMAL / EXPENSIVE**
- A visualization report (time series, heatmap, boxplots)

## What’s implemented (so far)
✅ Pull hourly CAISO demand (EIA) for a configurable lookback window  
✅ Pull CAISO Day-Ahead hourly LMP from OASIS (total LMP: `LMP_PRC`)  
✅ Merge demand + price into a single “energy signal” dataset  
✅ Label prices using **hour-of-day percentile baseline** (more accurate than global threshold)  
✅ CLI status output in local time (America/Denver)  
✅ Visualization report saved as PNGs

## Repo structure
- `src/`
  - `pull_demand_hourly.py` — EIA demand pull (CAISO parent = `CISO`)
  - `pull_caiso_lmp_dam_hourly.py` — CAISO OASIS DAM LMP pull
  - `build_energy_signal.py` — merge + label + “now” snapshot + CLI report
  - `run_pipeline.py` — runs the full pipeline
  - `viz_report.py` — generates PNG charts
- `data/` (ignored) — generated CSVs and JSON
- `reports/figures/` — charts (PNG)

## Setup (Windows / VS Code)
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt


Config

Create a .env file in the repo root (this file is ignored by git):

EIA_API_KEY=YOUR_EIA_KEY
EIA_PARENT=CISO
CAISO_NODE=TH_NP15_GEN-APND
LOOKBACK_DAYS=7

Security note: never commit .env. Rotate keys if accidentally shared.

Run the pipeline
python src/run_pipeline.py

Outputs:

data/demand_hourly_CISO_latest.csv

data/caiso_lmp_dam_hourly_TH_NP15_GEN-APND_latest.csv

data/energy_signal_latest.csv

data/energy_signal_now.json

Run visualizations
python src/viz_report.py

Charts saved to:

reports/figures/

Interpreting the label

Price labels are based on hour-of-day baselines:

CHEAP: below (or equal) the 25th percentile for that UTC hour

EXPENSIVE: above (or equal) the 75th percentile for that UTC hour

NORMAL: in between

Next steps (not done yet)

Automate hourly runs (Task Scheduler / cron)

Add FastAPI endpoint (/now) returning the JSON snapshot

Add alerts when EXPENSIVE