"""Generate a 1-second-cadence dispatch dataset from the bundled 1-minute data.

Linearly interpolates numeric telemetry (price, SoC, temps, load) to 1-second
resolution, re-runs `decide_dispatch` on every row at 1Hz, and recomputes costs.

Also produces a "blackout" variant where the grid is forced unavailable for a
configurable window — to demo how the dispatch logic responds to an outage.

Outputs:
  data/dispatch_signal_1s.csv          (normal 1Hz simulation)
  data/dispatch_signal_1s_blackout.csv (with a synthetic blackout window)
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from build_dispatch_signal import (
    BATTERY_CAPACITY_KWH,
    SOC_DEPLETED_PCT,
    compute_costs,
    decide_dispatch,
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
INPUT_FILE = DATA_DIR / "dispatch_signal_latest.csv"
OUTPUT_FILE = DATA_DIR / "dispatch_signal_1s.csv"
OUTPUT_BLACKOUT_FILE = DATA_DIR / "dispatch_signal_1s_blackout.csv"

# Blackout default: a 30-min window starting partway through the day.
BLACKOUT_START = "14:00:00"
BLACKOUT_END = "14:30:00"

NUMERIC_INTERP_COLS = [
    "electricity_price_usd_per_kwh",
    "battery_soc_pct",
    "power_kw_total",
    "power_kw_it",
    "power_kw_cooling",
    "gpu_temp_avg_c",
    "gpu_temp_max_c",
    "gpu_utilization_pct",
    "ambient_temp_c",
    "tokens_per_sec",
    "active_gpu_count",
]

CATEGORICAL_FFILL_COLS = [
    "battery_state",
    "thermal_state",
    "workload_state",
    "cluster_id",
]


def upsample_to_1hz(df_min: pd.DataFrame) -> pd.DataFrame:
    df = df_min.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").set_index("timestamp")

    new_index = pd.date_range(
        start=df.index.min(), end=df.index.max(), freq="1s"
    )
    out = pd.DataFrame(index=new_index)

    for col in NUMERIC_INTERP_COLS:
        if col in df.columns:
            out[col] = df[col].reindex(new_index).interpolate(method="time")

    for col in CATEGORICAL_FFILL_COLS:
        if col in df.columns:
            out[col] = df[col].reindex(new_index).ffill()

    out.index.name = "timestamp"
    return out.reset_index()


def apply_decisions(df: pd.DataFrame, *, blackout_mask: pd.Series | None = None) -> pd.DataFrame:
    df = df.copy()
    if blackout_mask is None:
        blackout_mask = pd.Series(False, index=df.index)
    df["grid_available"] = ~blackout_mask

    decisions = []
    for row, available in zip(df.to_dict(orient="records"), df["grid_available"]):
        decisions.append(decide_dispatch(row, grid_available=bool(available)))

    decisions_df = pd.DataFrame(decisions)
    return pd.concat([df.reset_index(drop=True), decisions_df.reset_index(drop=True)], axis=1)


def make_blackout_mask(df: pd.DataFrame, start: str, end: str) -> pd.Series:
    ts = pd.to_datetime(df["timestamp"])
    day = ts.dt.normalize().iloc[0]
    start_ts = pd.Timestamp(f"{day.date()} {start}")
    end_ts = pd.Timestamp(f"{day.date()} {end}")
    return (ts >= start_ts) & (ts < end_ts)


def main():
    print(f"Loading {INPUT_FILE.name} ...")
    df_min = pd.read_csv(INPUT_FILE)
    print(f"  rows: {len(df_min)}")

    print("Interpolating to 1-second cadence ...")
    df_1s = upsample_to_1hz(df_min)
    print(f"  rows: {len(df_1s)}")

    print("Running decisions at 1Hz (normal scenario) ...")
    df_normal = apply_decisions(df_1s)
    df_normal = compute_costs(df_normal, timestep_minutes=1 / 60.0)
    df_normal.to_csv(OUTPUT_FILE, index=False)
    _summarize("Normal", df_normal)
    print(f"  wrote: {OUTPUT_FILE}")

    print(f"Running decisions at 1Hz (blackout {BLACKOUT_START}-{BLACKOUT_END}) ...")
    blackout_mask = make_blackout_mask(df_1s, BLACKOUT_START, BLACKOUT_END)
    df_blackout = apply_decisions(df_1s, blackout_mask=blackout_mask)
    df_blackout = compute_costs(df_blackout, timestep_minutes=1 / 60.0)
    df_blackout.to_csv(OUTPUT_BLACKOUT_FILE, index=False)
    _summarize("Blackout", df_blackout)
    print(f"  wrote: {OUTPUT_BLACKOUT_FILE}")


def _summarize(label: str, df: pd.DataFrame):
    baseline = df["cost_baseline"].sum()
    actual = df["cost_actual"].sum()
    savings_pct = ((baseline - actual) / baseline * 100) if baseline else 0
    sources = df["power_source"].value_counts().to_dict()
    min_runtime = df["battery_runtime_minutes"].replace(np.inf, np.nan).min()
    print(
        f"  [{label}] baseline=${baseline:.2f}  actual=${actual:.2f}  "
        f"savings={savings_pct:.1f}%  sources={sources}  "
        f"min_runtime={min_runtime:.1f} min"
    )


if __name__ == "__main__":
    main()
