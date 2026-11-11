"""developed streamlit dashboard for EV charging"""

from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Smart Energy & Electric Vehicle (EV) Fleet Management Platform", layout="wide")
st.markdown(
    """
    <style>
    .stApp,
[data-testid="stMain"],
[data-testid="stHeader"] {
    background-color: #F2F5F9;
}

[data-testid="stSidebar"] {
    background-color: #11263C;
}

[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
[data-testid="stSidebarNav"] a span {
    color: #F4F8FC;
}

[data-testid="stSidebarNav"] a[aria-current="page"] {
    background-color: #233C55;
}
    [data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #DCE5F0;
        border-radius: 14px;
        padding: 16px 18px;
    }

    [data-testid="stMetricValue"] {
        color: #11263C;
        font-weight: 700;
    }

    .ev-hero {
        background: linear-gradient(110deg, #11263C, #194760);
        border-radius: 18px;
        padding: 26px 30px;
        margin-bottom: 18px;
        color: #FFFFFF;
    }

    .ev-hero h1 {
        color: #FFFFFF;
        font-size: 2rem;
        margin: 0 0 8px;
        padding: 0;
    }

    .ev-hero p {
        color: #C9DAE9;
        margin: 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


DATA_FILE = Path(__file__).with_name("cleaned_energy_sales_data.csv")

REQUIRED_COLUMNS = {
    "Session_ID",
    "Charger_Type",
    "Start_Hour",
    "Energy_kWh",
    "Carbon_Savings_kgCO2",
    "Net_Billable_MYR",
    "Overstay_Mins",
    "Battery_Temp_C",
}

@st.cache_data
def load_data(file_path):
    """Load data from cleaned csv file and support dates for sidebar filters"""
    df = pd.read_csv(file_path)

    missing_columns = REQUIRED_COLUMNS - set(df.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    if df.empty:
        raise ValueError("The CSV file is empty.")

    if "Session_Date" in df.columns:
        df["Session_Date"] = pd.to_datetime(df["Session_Date"], errors="coerce").dt.normalize()

        if df["Session_Date"].isna().any():
            raise ValueError("Session_Date is missing or invalid dates.")

        return df, False

    # assign 30 demonstration dates in reproducible order
    df = df.sort_values("Session_ID").reset_index(drop=True)
    df["Session_Date"] = pd.Timestamp("2026-10-01") + pd.to_timedelta(df.index % 30, unit="D")
    return df, True

def risk_alert(df, max_temperature, max_overstay):
    """Identify session that exceed one or both thresholds"""
    exceed_temperature = df["Battery_Temp_C"] > max_temperature
    exceed_overstay = df["Overstay_Mins"] > max_overstay

    high_risk = exceed_temperature & exceed_overstay
    warnings = (exceed_temperature | exceed_overstay) & ~high_risk

    return high_risk, warnings

try:
    df, demo_dates = load_data(DATA_FILE)
except (OSError, FileNotFoundError, ValueError) as error:
    st.error(f"Could not load data: {error}")
    st.stop()

# filters for all pages
st.sidebar.header("Filters")
first_date = df["Session_Date"].min().date()
last_date = df["Session_Date"].max().date()

selected_dates = st.sidebar.date_input(
    "Session Date Range",
    value=(first_date, last_date),
    min_value=first_date,
    max_value=last_date,
)

min_energy = st.sidebar.slider(
    "Minimum Energy Delivered (kWh)",
    min_value=0.0,
    max_value=max(1.0, float(df["Energy_kWh"].max())),
    value=0.0,
    step=0.5,
)

charger_types = sorted(df["Charger_Type"].dropna().unique())
selected_charger = st.sidebar.multiselect(
    "Charger Type",
    options=charger_types,
    default=charger_types,
)

with st.sidebar:
    st.subheader("Alert thresholds")
    exceed_temperature = st.slider("Battery temperature (°C)", 20, 80, 50)
    exceed_overstay = st.slider("Overstay time (mins)", 0, 60, 15)


def filter_sessions():
    """return date range baseline and fully filtered sessions"""
    if len(selected_dates) != 2:
        st.info("Select both start date and end date")
        st.stop()

    start_date, end_date = selected_dates

    date_range = df["Session_Date"].between(
        pd.Timestamp(start_date), pd.Timestamp(end_date)
    )
    baseline = df.loc[date_range]

    filtered = baseline.loc[
        (baseline["Energy_kWh"] >= min_energy)
        & baseline["Charger_Type"].isin(selected_charger)
    ]

    return baseline, filtered

def dashboard_overview():
    """display KPIs and an hourly charging chart"""
    st.markdown(
        """
        <div class="ev-hero">
            <h1>Executive Overview</h1>
            <p>Monitor EV charging, revenue, and high-risk sessions.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    baseline, filtered = filter_sessions()

    metrics = [
        ("Total Energy Delivered", "Energy_kWh", "kWh"),
        ("Carbon Offset", "Carbon_Savings_kgCO2", "kg CO₂"),
        ("Total Revenue", "Net_Billable_MYR", "MYR"),
    ]
    cards = st.columns(4)

    for index, (label, column, unit) in enumerate(metrics):
        current = filtered[column].sum()
        change = current - baseline[column].sum()

        cards[index].metric(
            label,
            f"{current:,.2f} {unit}",
            delta=f"{change:+,.2f} {unit}",
            delta_color="off",
        )

    high_risk, warning = risk_alert(filtered, exceed_temperature, exceed_overstay)
    baseline_risk, baseline_warning = risk_alert(baseline, exceed_temperature, exceed_overstay)

    alert_count = int(high_risk.sum())
    alert_change = alert_count - int(baseline_risk.sum())

    cards[3].metric(
        "Active Alert Count",
        alert_count,
        delta=f"{alert_change:+d}",
        delta_color="off",
    )

    st.caption(
        "Deltas compare current selection with all sessions in same date range. "
        "The alert count include sessions that exceed both thresholds."
    )

    if filtered.empty:
        st.info("No charging sessions match the selected filters.")
        return

    st.subheader("Energy Delivered by Session Start Hour")
    hourly_energy = (
        filtered.groupby("Start_Hour")["Energy_kWh"].sum().reindex(range(24), fill_value=0).rename("Energy delivered (kWh)")
    )
    st.bar_chart(hourly_energy)

def alert_center():
    """show alert banner & risk chart"""
    st.title("High-Risk Overstay & Alert Center")
    baseline, filtered = filter_sessions()

    if filtered.empty:
        st.info("No charging sessions match the selected filters.")
        return

    high_risk, warning = risk_alert(filtered, exceed_temperature, exceed_overstay)
    alert_columns = ["Session_ID", "Charger_Type", "Battery_Temp_C", "Overstay_Mins",]

    chart_data = filtered.copy()
    chart_data["Alert_Status"] = "Normal"
    chart_data.loc[warning, "Alert_Status"] = "Warning"
    chart_data.loc[high_risk, "Alert_Status"] = "High Risk"

    fig = px.scatter(
        chart_data,
        x="Battery_Temp_C",
        y="Overstay_Mins",
        color="Alert_Status",
        hover_name="Session_ID",
        hover_data=["Charger_Type", "Energy_kWh"],
        color_discrete_map={
            "Normal": "#2E7D32",
            "Warning": "#C17C00",
            "High Risk": "#C62828",
        },
        category_orders={
            "Alert_Status": ["Normal", "Warning", "High Risk"]
        },
        labels={
            "Battery_Temp_C": "Battery temperature (°C)",
            "Overstay_Mins": "Actual overstay (min)",
            "Charger_Type": "Charger type",
            "Energy_kWh": "Energy delivered (kWh)",
            "Alert_Status": "Alert status",
        },
        title="Charging Sessions by Alert Status",
    )

    fig.add_vline(x=exceed_temperature, line_dash="dash", line_color="gray")
    fig.add_hline(y=exceed_overstay, line_dash="dash", line_color="gray")

    st.plotly_chart(fig)
    st.caption(
        f"Dashed lines show the alert thresholds of "
        f"{exceed_temperature}°C and {exceed_overstay} minutes."
    )


    if high_risk.any():
        st.error(f"High-risk: {high_risk.sum()} sessions exceed both alert thresholds.")
        st.dataframe(filtered.loc[high_risk, alert_columns], hide_index=True)

    if warning.any():
        st.warning(f"Warning: {warning.sum()} sessions exceed one alert threshold.")
        st.dataframe(filtered.loc[warning, alert_columns], hide_index=True)

    if not high_risk.any() and not warning.any():
        st.success("Normal - No sessions exceed the selected thresholds.")


def data_download():
    """Display and download data """
    st.title("Filtered Data Viewer")
    baseline, filtered = filter_sessions()

    st.caption(f"{len(filtered):,} sessions match the current filters.")
    st.dataframe(filtered, hide_index=True)

    st.download_button(
        label="Download filtered CSV file",
        data=filtered.to_csv(index=False, date_format="%Y-%m-%d"),
        file_name="filtered_ev_sessions.csv",
        mime="text/csv",
        disabled=filtered.empty,
        type="primary",
    )

pages = st.navigation([
    st.Page(dashboard_overview, title="Executive Overview"),
    st.Page(alert_center, title="Alert Center"),
    st.Page(data_download, title="Data Viewer"),
])

if demo_dates:
    st.info(
        "Demo dates are assigned for the date filter. "
        "The source CSV contains charging start hours only."
    )

pages.run()
