"""
Streamlit application for optimising breast diagnostic service locations
within the RDUH NHS Trust.

This file handles:
- User interface
- Data loading and validation
- Orchestration of analysis modules
- Visualisation and reporting

All computational logic lives in /analysis and /reporting.
"""

# ==============================
# Imports
# ==============================
import os

# Change working directory to the folder where app.py is
#os.chdir(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(BASE_DIR, "assets", "nhs_logo.jpeg")


import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium

# Project modules
from analysis.geography import get_lat_lon
from analysis.travel import compute_distance_time
from analysis.demand import nearest_metrics
from reporting.excel_report import to_excel_report


# =============================
# Page configuration
# =============================
st.set_page_config(
    page_title="NHS Breast Diagnostic Service Planning",
    layout="wide"
)

# =============================
# Header
# =============================
title_col, logo_col = st.columns([6, 1.5])
with title_col:
    st.markdown(
        "<h1 style='margin:0;'>Breast Diagnostic Service Optimisation</h1>",
        unsafe_allow_html=True
    )
with logo_col:
    if os.path.exists(logo_path):
        st.image(logo_path, width=200)
    else:
        st.write("**NHS Logo missing**")

st.markdown("<hr>", unsafe_allow_html=True)

# =============================
# Sidebar – Help
# =============================
with st.sidebar.expander("ℹ️ What does this tool do?", expanded=True):
    st.markdown("""
- Quantifies GP referral demand
- Calculates travel times to hospital sites
- Computes weighted access burden
- Tests new service locations
- Explores time / cost / CO₂ trade-offs
- Exports a full Excel planning report
""")

# =============================
# Upload data
# =============================
uploaded_file = st.file_uploader(
    "Upload GP & Hospital CSV",
    type=["csv"]
)

# =============================
# Sidebar – Model parameters
# =============================
st.sidebar.header("⚙️ Assumptions")

mode = st.sidebar.radio(
    "Analysis mode",
    ["Simple planning", "Advanced analysis"]
)

# NHS-safe defaults
car_speed = 40
pt_speed = 25
fuel_cost = 0.20
co2_per_mile = 0.25

if mode == "Advanced analysis":
    car_speed = st.sidebar.slider("Car speed (mph)", 20, 70, car_speed)
    pt_speed = st.sidebar.slider("PT speed (mph)", 10, 40, pt_speed)
    fuel_cost = st.sidebar.number_input("Fuel (£/mile)", 0.1, 1.0, fuel_cost)
    co2_per_mile = st.sidebar.number_input("CO₂ (kg/mile)", 0.1, 1.0, co2_per_mile)

# =============================
# Main workflow
# =============================
if not uploaded_file:
    st.info("Upload a CSV containing all GP practices and current hospital sites. You can then select which hospitals to include in the scenario.")
    st.stop()



# -----------------------------
# Load and validate data
# -----------------------------
df = pd.read_csv(uploaded_file)
df.columns = df.columns.str.strip()

if df["Description"].nunique() < 2:
    st.error("Dataset must contain GP practices and at least one hospital site.")
    st.stop()

required_cols = ["Description", "Postcode", "Referrals"]
if not all(c in df.columns for c in required_cols):
    st.error("CSV must contain: Description, Postcode, Referrals")
    st.stop()

# Ensure Referrals are numeric & non-negative
df["Referrals"] = pd.to_numeric(df["Referrals"], errors="coerce").fillna(0)
df.loc[df["Referrals"] < 0, "Referrals"] = 0

high_ref = df["Referrals"] > df["Referrals"].quantile(0.99)
low_ref = df["Referrals"] == 0

if high_ref.any():
    st.warning(f"{high_ref.sum()} GP(s) have unusually high referrals (top 1%). Consider reviewing.")

if low_ref.any():
    st.info(f"{low_ref.sum()} GP(s) have zero referrals.")


# -----------------------------
# Geocode if required
# -----------------------------
if "result_latitude" not in df.columns or "result_longitude" not in df.columns:
    st.info("Resolving postcodes to latitude/longitude (cached)...")
    latlon = df["Postcode"].apply(get_lat_lon)
    df["result_latitude"] = [x[0] for x in latlon]
    df["result_longitude"] = [x[1] for x in latlon]

missing_coords = df[["result_latitude", "result_longitude"]].isnull().any(axis=1)
if missing_coords.any():
    st.warning(f"{missing_coords.sum()} entries failed geocoding and will be removed.")
df = df.dropna(subset=["result_latitude", "result_longitude"])

# -----------------------------
# Select hospitals
# -----------------------------
hospital_names = st.multiselect(
    "Select hospital sites",
    options=df["Description"].unique().tolist()
)

st.markdown("### Optional: Test a new hospital location")
new_site_postcode = st.text_input("Enter postcode for proposed site")


if not hospital_names:
    st.warning("Select at least one hospital site.")
    st.stop()

hospital_df = df[df["Description"].isin(hospital_names)].copy()
gp_df = df[~df["Description"].isin(hospital_names)].copy()

if new_site_postcode:
    lat, lon = get_lat_lon(new_site_postcode)
    if lat and lon:
        proposed_site = pd.DataFrame([{
            "Description": "Proposed Site",
            "result_latitude": lat,
            "result_longitude": lon
        }])
        hospital_df = pd.concat([hospital_df, proposed_site], ignore_index=True)
        st.success("Proposed site added to scenario.")
    else:
        st.warning("Invalid postcode for proposed site.")

# -----------------------------
# Coordinates
# -----------------------------
gp_coords = gp_df[["result_latitude", "result_longitude"]].to_numpy()
hosp_coords = hospital_df[["result_latitude", "result_longitude"]].to_numpy()

# -----------------------------
# Distance & travel time
# -----------------------------
@st.cache_data
def compute_metrics_cached(gp_coords, hosp_coords, car_speed, pt_speed):
    return compute_distance_time(gp_coords, hosp_coords, car_speed, pt_speed)

dist, car_time, pt_time = compute_metrics_cached(gp_coords, hosp_coords, car_speed, pt_speed)

# -----------------------------
# Nearest metrics
# -----------------------------
(
    nearest_dist,
    nearest_car,
    nearest_pt,
    fuel,
    co2,
    weighted_car,
    weighted_pt,
    weighted_access_score
) = nearest_metrics(
    dist,
    car_time,
    pt_time,
    gp_df["Referrals"].to_numpy(),
    car_speed,
    fuel_cost,
    co2_per_mile
)

# -----------------------------
# Baseline comparisons (nearest hospital scenario)
# -----------------------------
# Naive baseline: all patients go to first selected hospital
baseline_car = car_time[:, 0]
baseline_pt = pt_time[:, 0]

baseline_weighted_car = baseline_car * gp_df["Referrals"].to_numpy()
baseline_weighted_pt = baseline_pt * gp_df["Referrals"].to_numpy()

# Overall access improvement (%)
total_weighted_car = weighted_car.sum()
total_weighted_pt = weighted_pt.sum()

baseline_total_car = baseline_weighted_car.sum()
baseline_total_pt = baseline_weighted_pt.sum()


if baseline_total_car > 0:
    improvement_car_pct = (baseline_total_car - total_weighted_car) / baseline_total_car * 100
else:
    improvement_car_pct = 0

if baseline_total_pt > 0:
    improvement_pt_pct = (baseline_total_pt - total_weighted_pt) / baseline_total_pt * 100
else:
    improvement_pt_pct = 0


# -----------------------------
# Build analysis table
# -----------------------------
combined_df = gp_df.reset_index(drop=True)
combined_df["Shortest Car Time (min)"] = nearest_car
combined_df["Shortest PT Time (min)"] = nearest_pt
combined_df["Fuel Cost (£)"] = fuel
combined_df["CO₂ (kg)"] = co2
combined_df["Weighted Demand (Car)"] = weighted_car
combined_df["Weighted Demand (PT)"] = weighted_pt



# -----------------------------
# Hospital summary
# -----------------------------
nearest_hospital_index = np.argmin(car_time, axis=1)

hospital_summary = pd.DataFrame({
    "Hospital": hospital_df["Description"].values,
    "Total Referrals Assigned": [
        gp_df.loc[nearest_hospital_index == i, "Referrals"].sum()
        for i in range(len(hospital_df))
    ],
    "Total Weighted Demand (Car)": [
        np.sum(car_time[:, i] * gp_df["Referrals"].values)
        for i in range(len(hospital_df))
    ],
    "Total Weighted Demand (PT)": [
        np.sum(pt_time[:, i] * gp_df["Referrals"].values)
        for i in range(len(hospital_df))
    ],
})


# =============================
# Tabs
# =============================
tabs = st.tabs([
    "Summary",
    "Charts",
    "Map",
    "Guide",
    "Downloads"
])

# -----------------------------
# Summary
# -----------------------------
with tabs[0]:

    # Total referrals
    st.metric(
        label="Total referrals",
        value=f"{int(gp_df['Referrals'].sum()):,}"
    )

    # Average travel times
    st.metric(
        label="Avg shortest car time (min)",
        value=f"{nearest_car.mean():.2f}",
        delta=f"{(nearest_car.mean() - baseline_car.mean()):.2f} min",
        delta_color="inverse"  # lower travel time is better
    )

    st.metric(
        label="Travel time variability (standard deviation)",
        value=f"{nearest_car.std():.2f} min"
    )


    st.metric(
        label="Avg shortest PT time (min)",
        value=f"{nearest_pt.mean():.2f}",
        delta=f"{(nearest_pt.mean() - baseline_pt.mean()):.2f} min",
        delta_color="inverse"
    )

    # CO2 and Fuel Cost
    st.metric(
        label="Total CO₂ (kg)",
        value=f"{co2.sum():,.2f}",
        delta=f"{(co2.sum() - (baseline_car / car_speed * co2_per_mile).sum()):,.2f}",
        delta_color="inverse"
    )
    st.metric(
        label="Total Fuel Cost (£)",
        value=f"{fuel.sum():,.2f}",
        delta=f"{(fuel.sum() - (baseline_car / car_speed * fuel_cost).sum()):,.2f}",
        delta_color="inverse"
    )

    # Weighted Access Score
    st.metric(
        label="Weighted Access Score (Car)",
        value=f"{weighted_car.sum():,.2f}",
        delta=f"{(weighted_car.sum() - baseline_total_car):,.2f}",
        delta_color="inverse"
    )
    st.metric(
        label="Weighted Access Score (PT)",
        value=f"{weighted_pt.sum():,.2f}",
        delta=f"{(weighted_pt.sum() - baseline_total_pt):,.2f}",
        delta_color="inverse"
    )

    # Access improvement vs baseline
    st.metric(
        label="Access improvement vs baseline (Car)",
        value=f"{round(improvement_car_pct, 1)}%",
        delta_color="normal"
    )
    st.metric(
        label="Access improvement vs baseline (PT)",
        value=f"{round(improvement_pt_pct, 1)}%",
        delta_color="normal"
    )

    # Comparison vs baseline table
    comparison_df = pd.DataFrame({
        "Metric": ["Weighted Access Score (Car)", "Weighted Access Score (PT)"],
        "Current scenario": [weighted_car.sum(), weighted_pt.sum()],
        "Baseline": [baseline_total_car, baseline_total_pt],
        "Improvement (%)": [improvement_car_pct, improvement_pt_pct]
    })

    st.markdown("**Comparison vs baseline:**")
    st.dataframe(
        comparison_df.style.format({
            "Current scenario": "{:,.2f}",
            "Baseline": "{:,.2f}",
            "Improvement (%)": "{:.1f}%"
        }),
        use_container_width=True
    )

    combined_df["Improvement (Car min)"] = baseline_car - nearest_car
    top_improved = combined_df.sort_values("Improvement (Car min)", ascending=False).head(10)

    st.markdown("### Top 10 GPs benefiting most")
    st.dataframe(top_improved[["Description", "Improvement (Car min)"]])

    # Hospital summary table
    st.markdown("**Hospital summary:**")
    hospital_summary_display = hospital_summary.copy().round(2)
    st.dataframe(
        hospital_summary_display.style.format({
            "Total Weighted Demand (Car)": "{:,.2f}",
            "Total Weighted Demand (PT)": "{:,.2f}"
        }),
        use_container_width=True
    )

    # Metric explanations
    st.markdown("""
**Metric explanations:**
- **Weighted Demand (Car/ PT)**: Referral count × travel time. Shows the 'access burden' for patients.
- **CO₂ (kg)**: Estimated emissions if all patients travelled by car.
- **Fuel Cost (£)**: Estimated travel cost by car.
- **Weighted Access Score**: Sum of all weighted demands, higher means longer or more difficult access.
                
**Access improvement vs baseline:**  
- Shows the percentage reduction in total weighted demand compared to an “ideal” scenario where every patient goes to their nearest hospital.  
- Higher values = more patients have shorter travel times, lower environmental impact, or lower fuel costs.  
- Helps planners see how much better the proposed hospital locations are versus current/nearest-hospital baseline.                
""")


# -----------------------------
# Charts
# -----------------------------
with tabs[1]:
    # Baseline line (single line across all GPs)
    baseline_car_value = baseline_car.mean()  
    baseline_pt_value = baseline_pt.mean()     

    chart_df = combined_df.copy()
    chart_df = chart_df.sort_values("Weighted Demand (Car)", ascending=False)
    chart_df["Baseline Weighted Demand (Car)"] = baseline_car
    chart_df["Baseline Weighted Demand (PT)"] = baseline_pt

    # Car weighted demand chart
    fig_car = go.Figure()
    fig_car.add_trace(go.Bar(
        x=chart_df["Description"],
        y=chart_df["Weighted Demand (Car)"],
        name="Weighted Demand (Car)",
        marker_color="#005EB8",
        hovertemplate="GP: %{x}<br>Weighted Demand: %{y:.2f}<extra></extra>"
    ))
    fig_car.add_trace(go.Scatter(
    x=chart_df["Description"],
    y=[baseline_car_value]*len(chart_df),
    name="Baseline Weighted Demand",
    mode="lines",
    line=dict(color="#FFB81C", width=2, dash="dash"),
    hovertemplate="Baseline: %{y:.2f}<extra></extra>"
    ))
    fig_car.update_layout(
        title="Weighted Demand (Car) vs Baseline",
        yaxis_title="Weighted Demand (min × referrals)",
        xaxis_title="GP",
        legend_title="Legend",
        template="plotly_white"
    )
    st.plotly_chart(fig_car, use_container_width=True)

    # PT weighted demand chart
    fig_pt = go.Figure()
    fig_pt.add_trace(go.Bar(
        x=chart_df["Description"],
        y=chart_df["Weighted Demand (PT)"],
        name="Weighted Demand (PT)",
        marker_color="#005EB8",
        hovertemplate="GP: %{x}<br>Weighted Demand: %{y:.2f}<extra></extra>"
    ))
    fig_pt.add_trace(go.Scatter(
    x=chart_df["Description"],
    y=[baseline_pt_value]*len(chart_df),
    name="Baseline Weighted Demand",
    mode="lines",
    line=dict(color="#FFB81C", width=2, dash="dash"),
    hovertemplate="Baseline: %{y:.2f}<extra></extra>"
    ))
    fig_pt.update_layout(
        title="Weighted Demand (PT) vs Baseline",
        yaxis_title="Weighted Demand (min × referrals)",
        xaxis_title="GP",
        legend_title="Legend",
        template="plotly_white"
    )
    st.plotly_chart(fig_pt, use_container_width=True)


# -----------------------------
# Map
# -----------------------------
with tabs[2]:
    if combined_df.empty or hospital_df.empty:
        st.write("No data to display on map.")
    else:
        m = folium.Map(tiles="CartoDB Positron")

        all_lats = list(combined_df["result_latitude"]) + list(hospital_df["result_latitude"])
        all_lons = list(combined_df["result_longitude"]) + list(hospital_df["result_longitude"])

        m.fit_bounds([
            [min(all_lats), min(all_lons)],
            [max(all_lats), max(all_lons)]
        ])

        HeatMap(
            combined_df[["result_latitude", "result_longitude", "Referrals"]].values.tolist(),
            radius=15,
            blur=10
        ).add_to(m)

        for _, row in hospital_df.iterrows():
            if row["Description"] == "Proposed Site":
                icon_color = "green"
            else:
                icon_color = "red"

            folium.Marker(
                [row["result_latitude"], row["result_longitude"]],
                tooltip=f"{row['Description']} (Hospital)",
                icon=folium.Icon(color=icon_color, icon="plus-sign")
            ).add_to(m)


        for _, row in combined_df.iterrows():
            folium.CircleMarker(
                [row["result_latitude"], row["result_longitude"]],
                radius=max(4, row["Weighted Demand (Car)"] / 500),
                color="#005EB8",
                fill=True,
                fill_opacity=0.7,
                tooltip=(
                f"{row['Description']}<br>"
                f"Referrals: {row['Referrals']}<br>"
                f"Weighted Demand: {row['Weighted Demand (Car)']:.2f}<br>"
                f"CO₂: {row['CO₂ (kg)']:.2f} kg"
                 )
            ).add_to(m)

        st_folium(m, width=1000, height=600)



# -----------------------------
# Guide
# -----------------------------
with tabs[3]:
    st.markdown("""
**Weighted demand = Referrals × Shortest travel time**  
Shows the burden of access for patients from each GP; higher numbers = harder to access care.

**CO₂ (kg)** = Estimated emissions if all patients travelled by car  

**Fuel Cost (£)** = Estimated travel cost by car  

**Weighted Access Score** = Sum of all weighted demands; higher = longer/more difficult access  

**Baseline** = All patients travel to a single-site model 
(using the first selected hospital as reference).
This provides comparison against a centralised service configuration

- Distances are calculated using the **Haversine formula**.
- Travel times assume **constant average speeds** for car / public transport.
- **CO₂ and fuel costs** are approximate.

This tool supports **strategic planning**, not day-to-day scheduling.
                
**Why this matters:**  
- Helps prioritise new hospital locations.  
- Shows impact on patient travel, environmental cost, and NHS resources.
""")


# -----------------------------
# Downloads
# -----------------------------
with tabs[4]:
    excel_bytes = to_excel_report(
        combined_df,
        hospital_summary,
        comparison_df,
        fig_car,
        fig_pt,
        {
            "Car speed": car_speed,
            "PT speed": pt_speed,
            "Fuel cost": fuel_cost,
            "CO₂ per mile": co2_per_mile
        }
    )
    st.download_button(
        "Download Excel report",
        excel_bytes,
        file_name="breast_diagnostic_planning.xlsx"
    )
