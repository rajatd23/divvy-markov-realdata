# Real-World Markov Process Simulation (Divvy GBFS → Python)

This project demonstrates an end-to-end **real-world Markov process simulation** built entirely in **Python**, using **live operational data** from the Divvy (Chicago) bike-share system.  
The goal is to show how **SAS-based Markov simulations and reporting workflows** can be **migrated to Python** while preserving analytical rigor, reproducibility, and decision-making value.

---

## 🔍 What This Project Does

1. **Collects real-world data** from Divvy’s public GBFS (General Bikeshare Feed Specification) API
2. **Converts numerical station availability data into discrete states**
3. **Learns transition probabilities from historical data**
4. **Builds a Markov transition matrix from real observations**
5. **Simulates future system behavior using the learned model**
6. **Exports SAS-like analytical outputs** (CSV tables, plots, reports)

This mirrors how Markov models are used in **utilities, transportation, logistics, finance, and reliability engineering**.

---

## 🌍 Real-World Motivation

Many organizations still rely on **SAS** to:
- model system behavior over time
- simulate risk and failure
- support operational and financial forecasting

This project shows how the **same logic** can be:
- implemented in **Python**
- automated
- validated using **real operational data**
- exported to modern analytics tools (Power BI, Excel, dashboards)

---

## 🧠 Conceptual Overview

Each **Divvy bike station** is treated as an **entity**.

At each time snapshot, the station is classified into one of four states based on bike availability:

| State  | Meaning |
|------|--------|
| EMPTY | No bikes available |
| LOW | Low availability |
| MEDIUM | Moderate availability |
| HIGH | High availability |

By observing how stations move between these states over time, we:
- learn transition probabilities
- construct a Markov model
- simulate future system behavior

---

## 📊 Outputs Generated

After running the pipeline, the following outputs are created:

- `transition_counts_real.csv`  
  → Frequency of state-to-state transitions (PROC FREQ equivalent)

- `transition_probs_real.csv`  
  → Learned Markov transition matrix

- `simulated_occupancy.csv`  
  → State distribution over time (simulation result)

- `simulated_occupancy.png`  
  → Visualization of state evolution

- `report.md`  
  → Auto-generated analytical summary

These outputs are **ready for dashboards, forecasting, and decision support**.

---

## ▶️ How to Run

### 1. Install dependencies
pip install -r requirements.txt

### 2. Collect real-world data (run multiple times)
python src/collect_divvy.py

### 3. python src/run_end_to_end.py
python src/run_end_to_end.py

