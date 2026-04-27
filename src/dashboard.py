from pathlib import Path
import json
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

dispatch_csv = DATA_DIR / "dispatch_signal_latest.csv"
dispatch_json = DATA_DIR / "dispatch_now.json"

st.set_page_config(
    page_title="Energy-Aware GPU Dispatch Dashboard",
    layout="wide"
)

st.title("Energy-Aware GPU Dispatch Dashboard")
st.caption("GPU workload + battery + electricity price decision system")

st_autorefresh(interval=5000, key="datarefresh")

df = pd.read_csv(dispatch_csv)
df["timestamp"] = pd.to_datetime(df["timestamp"])

with open(dispatch_json, "r") as f:
    now = json.load(f)

st.subheader("Current Dispatch Decision")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Battery Action", now["battery_action"])
col2.metric("Power Source", now["power_source"])
col3.metric("Compute Mode", now["compute_mode"])
col4.metric("Price State", now["price_state"])

st.write("Decision reason:", now["decision_reason"])

st.info(
    f"""
    Current system recommendation: use **{now['power_source']}** power, 
    set compute mode to **{now['compute_mode']}**, and **{now['battery_action']}** the battery.

    Reason: `{now['decision_reason']}`.
    """
)

st.subheader("Cost Summary")    

baseline = df["cost_baseline"].sum()
actual = df["cost_actual"].sum()
savings = df["cost_savings"].sum()
savings_pct = (savings / baseline) * 100

c1, c2, c3, c4 = st.columns(4)
c1.metric("Baseline Cost", f"${baseline:,.2f}")
c2.metric("Optimized Cost", f"${actual:,.2f}")
c3.metric("Savings", f"${savings:,.2f}")
c4.metric("Savings %", f"{savings_pct:.1f}%")

st.subheader("Battery SOC Over Time")
st.line_chart(df.set_index("timestamp")["battery_soc_pct"])

st.subheader("Electricity Price Over Time")
st.line_chart(df.set_index("timestamp")["electricity_price_usd_per_kwh"])

st.subheader("Dispatch Data Preview")
st.dataframe(df.tail(20), use_container_width=True)


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


st.subheader("Cumulative Cost Comparison")

cost_df = df[["timestamp", "cost_baseline", "cost_actual"]].copy()
cost_df["cumulative_baseline"] = cost_df["cost_baseline"].cumsum()
cost_df["cumulative_actual"] = cost_df["cost_actual"].cumsum()

st.line_chart(
    cost_df.set_index("timestamp")[["cumulative_baseline", "cumulative_actual"]]
)