# HSMA_6016_optimising_location_breast_cancer_diagnostic_services
HSMA Project, link to project details here: https://hsma.co.uk/previous_projects/hsma_6/H6_6016_Optimising_the_location_of_breast_cancer_diagnostic_services/index.html

# Optimising the Location of Breast Cancer Diagnostic Services
*HSMA Project H6_6016*

![NHS Logo](assets/nhs_logo.jpegol to support NHS strategic decision‑making around diagnostic service locations.  
This GitHub repository implements the HSMA project:

🔗 **H6_6016 – Optimising the Location of Breast Cancer Diagnostic Services**  
https://hsma.co.uk/previous_projects/hsma_6/H6_6016_Optimising_the_location_of_breast_cancer_diagnostic_services/index.html

---

## Authors

- **Brandon Jones** – Royal Devon University Healthcare NHS Foundation Trust  
- **Kat Pamatmat** – Royal Devon University Healthcare NHS Foundation Trust  
- **Gill Baker** – Royal Devon University Healthcare NHS Foundation Trust  

---

## 📌 Project Overview

This repository contains a **Streamlit-based interactive tool** designed to support estates and diagnostic‑service planning across the NHS.

The tool operationalises the methodology developed for HSMA Project **H6_6016**, enabling planners to:

- Quantify demand from GP practices  
- Estimate travel times to existing or proposed hospital sites  
- Evaluate patient access burden, travel cost, and CO₂ impact  
- Compare alternative service configurations  
- Export structured planning reports in Excel  

> ⚠️ **Note:** This tool is for _strategic planning_, not real‑time routing or operational scheduling.

---

## 🎯 Project Aim (HSMA Brief)

The aim is to optimise diagnostic service locations by analysing travel burden and access equity across GP populations. This supports:

- **Equity of access** across geographies  
- **Minimising patient burden** (travel time, cost, emissions)  
- **Evidence‑based justification** for service location decisions  
- **Scenario testing**, including proposed new hospital sites  

This repository provides a practical, interactive tool that NHS planners can use with their own GP and hospital datasets.

---

## 🧠 Methodology (Aligned with HSMA Approach)

### **1. Distance & Travel Time Modelling**

- Straight‑line distances calculated with the **Haversine formula**  
- Travel times estimated using assumption‑based speeds:  
  - **Car:** 40 mph (default)  
  - **Public transport:** 25 mph (default)  

### **2. Weighted Access Burden**

For each GP practice:

Weighted Demand = Referrals × Shortest Travel Time

Quantifies patient burden in time units.

- **Low values = better access**
- Aggregated total weighted access score measures overall system burden

---

## 3) Baseline and Scenario Comparison

**Baseline:**  
All patients travel to a single reference hospital (first selected site).

**Scenario comparison:** evaluates benefits of multiple or proposed sites, including:

- Travel burden reductions (%)
- Cost savings
- CO₂ emissions reductions

---

# 🚀 Key Features

## ✔ Scenario Selection

- Upload GP + hospital datasets  
- Select any subset of existing hospitals  
- Add proposed new hospital by postcode  
- Supports bespoke scenario analysis  

## ✔ Metrics & Visualisations

**Summary dashboard includes:**

- Total referrals  
- Average travel times  
- Travel time variability  
- Weighted demand scores  
- Percent improvement vs baseline  

**Charts:**

- Bar charts of weighted demand vs baseline  
- Sorted charts highlighting most burdened GP practices  

**Map visualisation:**

- Heatmap of referral density  
- GP & hospital location markers  
- Hospital assignment circles sized by burden  

## ✔ Output Reporting

Downloadable Excel report includes:

- GP-level analysis  
- Hospital summary  
- Scenario comparison  
- Embedded charts  
- Model assumptions  

---

# 📥 Example CSV Format
Description,Postcode,Referrals
GP practice A,EX? 1??,150
Hospital X,EX? 2??,0

**Required columns:**  
- `Description`  
- `Postcode`  
- `Referrals`  

Latitude/longitude is automatically resolved if missing.

---

## 📦 Application Structure
```text
app.py                  # Main Streamlit app
analysis/
├─ geography.py         # Postcode lookup
├─ travel.py            # Distance & travel time calculations
└─ demand.py            # Nearest hospital metrics
reporting/
└─ excel_report.py      # Excel export logic
assets/
└─ nhs_logo.jpeg        # Logo
environment3.yml        # Conda environment
README.md
```
---

## 🛠 How to Run (Browser / Local)

### Clone repository
```bash
git clone https://github.com/Brandon-L-Jones/HSMA_6016_optimising_location_breast_cancer_diagnostic_services.git
cd HSMA_6016_optimising_location_breast_cancer_diagnostic_services
```

### Set up Conda environment
```bash
conda env create -f environment3.yml
conda activate hsma_webdev3  # Replace with environment name from yml
```
### Run the app
```bash
streamlit run app.py
```

### Open the app

- Streamlit should open a browser automatically.
- If not, copy the URL shown in the terminal (usually http://localhost:8501).
- Upload your CSV files to explore scenarios.


## 🧩 Assumptions & Limitations

- Distances are straight-line (not road routing)
- Constant average travel speeds assumed
- No hospital capacity modelling
- Designed for strategic planning, not real-time routing


## 📈 Output Interpretation

- Weighted demand: time burden per GP
- Improvements vs baseline: scenario benefits
- Travel time variability: distribution equity across GPs


## 📌 Use Cases

- NHS strategic estates planning
- Health service optimisation
- Equity analysis of access
- Academic modelling of service locations


## 📄 Suggested Citation

- Brandon Jones et al. (2025),
- Optimising the location of breast cancer diagnostic services — interactive NHS planning tool,
- GitHub repository: link

## 🏁 Next Enhancements (Future Work)

- Road-network travel time integration
- Capacity constraints per hospital
- Catchment assignment visualisation
- Advanced inequality metrics

