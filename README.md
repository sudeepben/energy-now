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

👉 Result: **~47% simulated cost savings**

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

| Metric         | Value   |
| -------------- | ------- |
| Baseline Cost  | $7,094  |
| Optimized Cost | $3,763  |
| Savings        | $3,330  |
| Savings %      | **47%** |

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

* End-to-end data pipeline
* Real-time decision system
* Explainable logic
* Cost optimization
* Interactive dashboard
* Cloud deployment

---

## 🔮 Future Improvements

* Add machine learning for prediction
* Real-time streaming data
* Alert system (high temperature / high cost)
* API endpoints for integration

---

## 📢 Summary

This project demonstrates how **data + decision logic + visualization** can be combined to solve real-world problems like energy optimization.

👉 It transforms raw data into actionable insights
👉 It reduces cost significantly
👉 It is fully deployable and scalable

---
