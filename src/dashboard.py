from pathlib import Path
import json
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

DISPATCH_1MIN_CSV = DATA_DIR / "dispatch_signal_latest.csv"
DISPATCH_1S_CSV = DATA_DIR / "dispatch_signal_1s.csv"
DISPATCH_1S_BLACKOUT_CSV = DATA_DIR / "dispatch_signal_1s_blackout.csv"
DISPATCH_NOW_JSON = DATA_DIR / "dispatch_now.json"

st.set_page_config(
    page_title="Energy-Aware GPU Dispatch Dashboard",
    layout="wide"
)

st.title("Energy-Aware GPU Dispatch Dashboard")
st.caption("GPU workload + battery + electricity price decision system")

# --- Sidebar controls ----------------------------------------------------
with st.sidebar:
    st.header("Simulation")

    available_modes = []
    if DISPATCH_1S_CSV.exists():
        available_modes.append("Per-second (1Hz)")
    if DISPATCH_1S_BLACKOUT_CSV.exists():
        available_modes.append("Per-second + blackout")
    available_modes.append("Per-minute (legacy)")

    mode = st.radio("Cadence / scenario", available_modes, index=0)

    if mode == "Per-second (1Hz)":
        active_csv = DISPATCH_1S_CSV
        refresh_ms = 1000
        st.caption("Decisions re-evaluated every second.")
    elif mode == "Per-second + blackout":
        active_csv = DISPATCH_1S_BLACKOUT_CSV
        refresh_ms = 1000
        st.caption("Synthetic grid outage 14:00–14:30. Watch the dispatch flip to battery.")
    else:
        active_csv = DISPATCH_1MIN_CSV
        refresh_ms = 5000
        st.caption("1-minute cadence (original).")

    show_decision_table = st.checkbox("Show recent decisions", value=True)

st_autorefresh(interval=refresh_ms, key="datarefresh")


# --- Load data -----------------------------------------------------------
@st.cache_data(ttl=10)
def load(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df

df = load(active_csv)

# "Now" — for the 1s scenarios there's no separate JSON, so use the latest row.
latest = df.sort_values("timestamp").iloc[-1].to_dict()
if mode.startswith("Per-minute") and DISPATCH_NOW_JSON.exists():
    with open(DISPATCH_NOW_JSON, "r") as f:
        latest = {**latest, **json.load(f)}


# --- Current decision ----------------------------------------------------
st.subheader("Current Dispatch Decision")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Battery Action", latest.get("battery_action", "?"))
c2.metric("Power Source", latest.get("power_source", "?"))
c3.metric("Compute Mode", latest.get("compute_mode", "?"))
c4.metric("Price State", latest.get("price_state", "?"))

reason = latest.get("decision_reason", "")
if reason.startswith("blackout_"):
    st.error(f"⚠ Grid outage detected. Reason: `{reason}`")
else:
    st.info(
        f"Current recommendation: use **{latest.get('power_source')}** power, "
        f"set compute to **{latest.get('compute_mode')}**, and "
        f"**{latest.get('battery_action')}** the battery. "
        f"Reason: `{reason}`."
    )


# --- Battery health & runtime -------------------------------------------
st.subheader("Battery Status")

soc = float(latest.get("battery_soc_pct", 0))
runtime = float(latest.get("battery_runtime_minutes", float("nan")))
grid_available = bool(latest.get("grid_available", True))

b1, b2, b3 = st.columns(3)
b1.metric("State of Charge", f"{soc:.1f}%")
if runtime != runtime:  # NaN
    b2.metric("Runtime at current load", "—")
elif runtime == float("inf"):
    b2.metric("Runtime at current load", "∞ (no load)")
else:
    b2.metric("Runtime at current load", f"{runtime:,.0f} min")
b3.metric("Grid available", "yes" if grid_available else "NO — outage")


# --- Cost summary --------------------------------------------------------
st.subheader("Cost Summary (this dataset)")

baseline = df["cost_baseline"].sum()
actual = df["cost_actual"].sum()
savings = df["cost_savings"].sum()
savings_pct = (savings / baseline) * 100 if baseline else 0

s1, s2, s3, s4 = st.columns(4)
s1.metric("Baseline Cost", f"${baseline:,.2f}")
s2.metric("Optimized Cost", f"${actual:,.2f}")
s3.metric("Savings", f"${savings:,.2f}")
s4.metric("Savings %", f"{savings_pct:.1f}%")


# --- Time series --------------------------------------------------------
st.subheader("Battery SOC Over Time")
st.line_chart(df.set_index("timestamp")["battery_soc_pct"])

st.subheader("Electricity Price Over Time")
st.line_chart(df.set_index("timestamp")["electricity_price_usd_per_kwh"])

st.subheader("Cumulative Cost: Baseline vs. Optimized")
cost_df = df[["timestamp", "cost_baseline", "cost_actual"]].copy()
cost_df["cumulative_baseline"] = cost_df["cost_baseline"].cumsum()
cost_df["cumulative_actual"] = cost_df["cost_actual"].cumsum()
st.line_chart(cost_df.set_index("timestamp")[["cumulative_baseline", "cumulative_actual"]])


# --- Decision counts ----------------------------------------------------
st.subheader("Dispatch Decision Counts")
col_a, col_b, col_c = st.columns(3)
with col_a:
    st.write("Battery Actions")
    st.bar_chart(df["battery_action"].value_counts())
with col_b:
    st.write("Power Sources")
    st.bar_chart(df["power_source"].value_counts())
with col_c:
    st.write("Compute Modes")
    st.bar_chart(df["compute_mode"].value_counts())


if show_decision_table:
    st.subheader("Most recent decisions")
    cols = ["timestamp", "power_source", "compute_mode", "battery_action",
            "decision_reason", "battery_soc_pct", "electricity_price_usd_per_kwh"]
    cols = [c for c in cols if c in df.columns]
    st.dataframe(df.sort_values("timestamp").tail(20)[cols], width="stretch")
