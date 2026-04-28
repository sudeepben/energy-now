# ⚡ Energy-Aware GPU Dispatch System

## 🌐 Live Demo

👉 https://energy-now-h6ld3wowdzazeya7w9azlr.streamlit.app

---

## 📌 Project Overview

This project is a **smart energy management system** for GPU-based workloads.

It helps answer a simple but powerful question:

👉 *“When should we run GPUs, use battery power, or rely on grid electricity to save cost?”*

The system combines:

* Electricity price data
* GPU workload information
* Battery status
* Temperature conditions

and makes **real-time decisions** to optimize energy usage.

---

## 💡 Why This Project Matters

Running GPUs (for AI, ML, data processing) consumes a lot of electricity.

Without optimization:

* Systems always use grid power ❌
* Costs increase significantly ❌

With this system:

* Uses battery when electricity is expensive ✅
* Charges battery when electricity is cheap ✅
* Adjusts compute load intelligently ✅

👉 Result on the included sample day: **~17% simulated cost savings** (see *Limitations & Assumptions* below for what this number does and doesn't mean).

---

## 🧠 What the System Does

Every minute, the system decides:

### 🔋 Battery Action

* Charge
* Hold
* Discharge

### ⚡ Power Source

* Grid
* Battery

### 🖥️ Compute Mode

* Full (maximum performance)
* Reduced (moderate usage)
* Critical Only (minimum usage)

### 📝 Decision Reason

Each decision includes a **clear explanation**.

---

## ⚙️ How It Works (Simple Flow)

1. **Collect Data**

   * Electricity prices (CAISO)
   * Demand data (EIA)
   * GPU and cluster telemetry

2. **Process Data**

   * Clean and combine datasets
   * Generate useful features (battery state, workload level, etc.)

3. **Make Decisions**

   * Apply rule-based logic
   * Decide energy usage strategy

4. **Calculate Cost**

   * Compare optimized vs baseline (grid-only)
   * Compute savings

5. **Visualize Results**

   * Dashboard shows decisions and trends

---

## 📊 Key Results

Single sample day (1,440 minutes, one cluster):

| Metric         | Value     |
| -------------- | --------- |
| Baseline Cost  | $118.24   |
| Optimized Cost | $98.49    |
| Savings        | $19.75    |
| Savings %      | **16.7%** |

These numbers come from the cost model in `src/build_dispatch_signal.py::compute_costs`. See *Limitations & Assumptions* for the model.

---

## ⚠️ Limitations & Assumptions

This is a portfolio-level simulation, not a production system. To keep the savings number honest:

* **Battery energy is not free.** When the battery delivers a kWh, it was charged from the grid earlier. Since we don't have the per-kWh charge-price history, we impute it at the period's *average* grid price, scaled up by `1 / round_trip_efficiency` (default `0.85`) to account for charge/discharge losses.
* **Round-trip efficiency:** assumed `0.85` (typical Li-ion). Realistic but a single number — no degradation cost, no rate-limit on charge/discharge.
* **Battery capacity:** the included data only varies SoC by a small amount, so a specific kWh capacity isn't load-bearing for the headline number. The capacity assumption matters more once you wire in real charge/discharge dynamics.
* **Decision logic is rule-based, not optimized.** The thresholds in `build_dispatch_signal.py` (`<=$0.15` → cheap, `>=$0.35` → expensive, etc.) are hand-picked. A linear-programming or model-predictive-control formulation would be the natural next step.
* **Single sample day.** Numbers will move once tested across a month of CAISO data with multiple clusters.
* **Baseline = always-grid.** Showing this beats grid is necessary but not sufficient. A stronger comparator is a simple time-of-use heuristic.

---

## 🖥️ Dashboard Features

The live dashboard shows:

* Current system decision
* Battery status and actions
* Power source selection
* Compute mode
* Cost savings
* Time-series charts
* Decision explanations

👉 Designed for both technical and non-technical users

---

## 🏗️ Project Structure

```
energy-now/
│
├── src/
│   ├── dashboard.py
│   ├── run_pipeline.py
│   ├── build_dispatch_signal.py
│   ├── ingest_compute_telemetry.py
│   └── other scripts
│
├── data/
│   ├── dispatch_signal_latest.csv
│   ├── dispatch_now.json
│   └── other datasets
│
├── reports/
│   ├── charts and visualizations
│
├── requirements.txt
└── README.md
```

---

## 🚀 How to Run Locally

### 1. Install dependencies

```
pip install -r requirements.txt
```

### 2. Run the pipeline

```
python src/run_pipeline.py
```

### 3. Start dashboard

```
streamlit run src/dashboard.py
```

### 4. (Optional) Re-run the cost model on the included sample data

If you don't have the upstream telemetry CSVs, you can still apply the cost model to the bundled `dispatch_signal_latest.csv`:

```
python src/recompute_costs.py
```

### 5. Run tests

```
pip install pytest
pytest tests/
```

---

## ☁️ Deployment

The project is deployed using:

* GitHub (code hosting)
* Streamlit Community Cloud (dashboard hosting)

---

## 🧑‍💻 Technologies Used

* Python
* Pandas
* Matplotlib
* Streamlit
* REST APIs (EIA, CAISO)

---

## 🎯 Key Highlights

* End-to-end data pipeline (CAISO + EIA → cleaning → decisions → dashboard)
* Rule-based, explainable dispatch logic
* Honest cost model with documented assumptions
* Interactive Streamlit dashboard, deployed to Streamlit Community Cloud
* Pure-function decision logic with pytest coverage

---

## 🔮 Future Improvements

* Replace rule thresholds with a linear-programming dispatch optimizer (`pulp` / `cvxpy`) — minimize cost over a 24h horizon subject to SoC, charge/discharge rate, and thermal limits
* Add a price forecaster (SARIMA or gradient boosting on CAISO history) and feed forecasts into the optimizer
* Backtest harness across a full month of CAISO data — report mean / median / p95 savings, not a single day
* Compare against a simple time-of-use heuristic, not just always-grid
* Carbon-aware dispatch using CAISO grid-mix data (gCO₂/kWh, not just $/kWh)

---

## 📢 Summary

This project demonstrates how **data + decision logic + visualization** can be combined to solve real-world problems like energy optimization.

👉 It transforms raw data into actionable insights
👉 It reduces cost significantly
👉 It is fully deployable and scalable

---
