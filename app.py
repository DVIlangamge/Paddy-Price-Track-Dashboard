"""
PaddyTrack — Rice Price Intelligence Dashboard
------------------------------------------------
A Streamlit dashboard for exploring historical rice prices across Sri Lankan
districts and rice types, and reviewing the PaddyTrack forecasting model's
output (forecasted price, error diagnostics, volatility, and key drivers).

Data sources (place these in the `data/` folder):
  1. wfp_food_prices_lka.csv      -> historical actual rice prices (WFP)
  2. rice_predictions.csv         -> model output / forecast features
  3. Historicl_Diesel_Price-_from_2010.xlsx -> fuel price reference (optional)
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

# --------------------------------------------------------------------------
# 1. PAGE CONFIG & STYLING
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="PaddyTrack | Rice Price Dashboard",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

PRIMARY_GREEN = "#0B3D2E"
ACCENT_GOLD = "#C8A24A"
LIGHT_GOLD = "#E8D9AE"
BG_CARD = "#F6F3EA"
TEXT_DARK = "#1D2B22"

st.markdown(
    f"""
    <style>
    .stApp {{ background-color: #FBFAF6; }}
    .main-title {{
        color: {PRIMARY_GREEN};
        font-size: 2.1rem;
        font-weight: 800;
        margin-bottom: 0px;
    }}
    .sub-title {{
        color: #5B6B60;
        font-size: 1rem;
        margin-top: 0px;
        margin-bottom: 1.2rem;
    }}
    .kpi-card {{
        background: linear-gradient(135deg, {PRIMARY_GREEN} 0%, #14513c 100%);
        border-radius: 14px;
        padding: 18px 20px;
        color: white;
        box-shadow: 0 4px 14px rgba(11,61,46,0.18);
    }}
    .kpi-label {{
        font-size: 0.82rem;
        color: {LIGHT_GOLD};
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 6px;
    }}
    .kpi-value {{
        font-size: 1.6rem;
        font-weight: 800;
        color: white;
    }}
    .kpi-sub {{
        font-size: 0.78rem;
        color: #D9E6DF;
        margin-top: 4px;
    }}
    .section-header {{
        color: {PRIMARY_GREEN};
        font-size: 1.15rem;
        font-weight: 700;
        border-left: 5px solid {ACCENT_GOLD};
        padding-left: 10px;
        margin: 1.4rem 0 0.6rem 0;
    }}
    [data-testid="stSidebar"] {{
        background-color: {PRIMARY_GREEN};
    }}
    /* Only force white on labels/headings/captions - NOT on the dropdown
       boxes themselves, so their native (readable) text stays visible. */
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {{
        color: white !important;
    }}
    </style>
    
    """,
    unsafe_allow_html=True,
)

st.markdown('<p class="main-title">🌾 PaddyTrack Rice Price Dashboard</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-title">Monitoring actual & forecasted rice prices across Sri Lanka\'s districts</p>',
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------
# 2. DATA LOADING (cached so files are only read once)
# --------------------------------------------------------------------------
@st.cache_data
def load_wfp_data(path="wfp_food_prices_lka.csv"):
    """Load actual historical rice prices (district + rice type level)."""
    df = pd.read_csv(path, skiprows=[1])  # row 1 is a HXL tag row, not data
    df["date"] = pd.to_datetime(df["date"])
    rice = df[df["commodity"].str.contains("Rice", case=False, na=False)].copy()
    rice = rice.rename(columns={"admin2": "district", "commodity": "rice_type"})
    rice["rice_type"] = rice["rice_type"].str.replace("Rice \\(", "", regex=True).str.replace("\\)", "", regex=True).str.title()
    rice = rice.dropna(subset=["district", "price"])
    return rice


@st.cache_data
def load_forecast_data(path="rice_predictions.csv"):
    """Load the PaddyTrack model's feature/prediction dataset (national/aggregate)."""
    df = pd.read_csv(path)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").reset_index(drop=True)
    # prediction_label is the model's predicted log-return for the next step.
    # Reconstruct an implied forecast price from it for display purposes.
    df["predicted_price"] = df["price"] * np.exp(df["prediction_label"])
    df["abs_error"] = (df["price"] - df["predicted_price"]).abs()
    df["pct_error"] = (df["abs_error"] / df["price"]) * 100
    return df


try:
    wfp = load_wfp_data()
    forecast = load_forecast_data()
except FileNotFoundError as e:
    st.error(f"Could not find a data file: {e}. Make sure the `data/` folder contains the three source files.")
    st.stop()

# --------------------------------------------------------------------------
# 3. SIDEBAR FILTERS
# --------------------------------------------------------------------------
st.sidebar.header("🔎 Filters")

districts = sorted(wfp["district"].unique())
rice_types = sorted(wfp["rice_type"].unique())

selected_district = st.sidebar.selectbox("District", districts, index=districts.index("Anuradhapura") if "Anuradhapura" in districts else 0)
selected_rice_type = st.sidebar.selectbox("Rice Type", rice_types)

st.sidebar.markdown("---")
st.sidebar.caption(
    "The **forecast, error diagnostics and volatility gauge** are produced by the "
    "PaddyTrack SVR model, which was trained on an aggregate national price series. "
    "District/rice-type filters apply to the **historical actuals** below."
)

filtered = wfp[
    (wfp["district"] == selected_district) & (wfp["rice_type"] == selected_rice_type)
].sort_values("date")

if filtered.empty:
    st.warning("No records for this district/rice type combination. Try another selection.")
    st.stop()

# --------------------------------------------------------------------------
# 4. KPI CALCULATIONS
# --------------------------------------------------------------------------
latest_row = filtered.iloc[-1]
latest_price = latest_row["price"]
latest_date = latest_row["date"].strftime("%b %Y")

prev_row = filtered.iloc[-2] if len(filtered) > 1 else latest_row
price_change_pct = ((latest_price - prev_row["price"]) / prev_row["price"]) * 100 if prev_row["price"] else 0

avg_forecast_price = forecast["predicted_price"].tail(6).mean()
forecast_asof = forecast["Date"].max().strftime("%b %Y")

# Volatility score: coefficient of variation of the last 12 months, scaled 0-100
recent = filtered.tail(12)
cv = (recent["price"].std() / recent["price"].mean()) * 100 if recent["price"].mean() else 0
volatility_score = float(np.clip(cv * 3, 0, 100))  # scaled for a readable gauge range

# --------------------------------------------------------------------------
# 5. KPI ROW
# --------------------------------------------------------------------------
k1, k2, k3 = st.columns(3)

with k1:
    arrow = "▲" if price_change_pct >= 0 else "▼"
    st.markdown(
        f"""<div class="kpi-card">
        <div class="kpi-label">Latest Rice Price</div>
        <div class="kpi-value">LKR {latest_price:,.2f}</div>
        <div class="kpi-sub">{arrow} {price_change_pct:+.1f}% vs previous record · {latest_date}</div>
        </div>""",
        unsafe_allow_html=True,
    )

with k2:
    st.markdown(
        f"""<div class="kpi-card">
        <div class="kpi-label">Avg. Forecasted Price</div>
        <div class="kpi-value">LKR {avg_forecast_price:,.2f}</div>
        <div class="kpi-sub">Model average, last 6 records (as of {forecast_asof})</div>
        </div>""",
        unsafe_allow_html=True,
    )

with k3:
    st.markdown(
        f"""<div class="kpi-card">
        <div class="kpi-label">Rice Type</div>
        <div class="kpi-value">{selected_rice_type}</div>
        <div class="kpi-sub">District: {selected_district}</div>
        </div>""",
        unsafe_allow_html=True,
    )

# --------------------------------------------------------------------------
# 6. PRICE TREND + VOLATILITY GAUGE
# --------------------------------------------------------------------------
st.markdown('<p class="section-header">📈 Rice Price Trend</p>', unsafe_allow_html=True)

col_trend, col_gauge = st.columns([2, 1])

with col_trend:
    fig_trend = px.line(
        filtered, x="date", y="price",
        markers=True,
        labels={"date": "Date", "price": "Price (LKR/kg)"},
    )
    fig_trend.update_traces(line_color=PRIMARY_GREEN, marker=dict(color=ACCENT_GOLD, size=6))
    fig_trend.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=10, r=10, t=10, b=10),
        height=360,
    )
    st.plotly_chart(fig_trend, use_container_width=True)

with col_gauge:
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=volatility_score,
        title={"text": "Volatility Score", "font": {"size": 16, "color": PRIMARY_GREEN}},
        number={"suffix": " / 100", "font": {"color": PRIMARY_GREEN}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": PRIMARY_GREEN},
            "bar": {"color": ACCENT_GOLD},
            "steps": [
                {"range": [0, 33], "color": "#D9EFE1"},
                {"range": [33, 66], "color": LIGHT_GOLD},
                {"range": [66, 100], "color": "#F1B9A8"},
            ],
            "threshold": {
                "line": {"color": PRIMARY_GREEN, "width": 3},
                "thickness": 0.8,
                "value": volatility_score,
            },
        },
    ))
    fig_gauge.update_layout(height=360, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig_gauge, use_container_width=True)

# --------------------------------------------------------------------------
# 7. MONTHLY AVERAGE + KEY INFLUENCES
# --------------------------------------------------------------------------
st.markdown('<p class="section-header">📊 Monthly Average Price & Key Influences</p>', unsafe_allow_html=True)

col_month, col_influence = st.columns([1.3, 1])

with col_month:
    monthly = filtered.copy()
    monthly["month"] = monthly["date"].dt.to_period("M").dt.to_timestamp()
    monthly_avg = monthly.groupby("month", as_index=False)["price"].mean()

    fig_month = px.bar(
        monthly_avg, x="month", y="price",
        labels={"month": "Month", "price": "Avg. Price (LKR/kg)"},
    )
    fig_month.update_traces(marker_color=PRIMARY_GREEN)
    fig_month.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=10, r=10, t=10, b=10),
        height=340,
    )
    st.plotly_chart(fig_month, use_container_width=True)

with col_influence:
    drivers = {
        "Fuel Price Index": forecast["price"].corr(forecast["fuel_pc1"]),
        "Max Temperature": forecast["price"].corr(forecast["tempmax"]),
        "Humidity": forecast["price"].corr(forecast["humidity"]),
        "Precipitation": forecast["price"].corr(forecast["precip"]),
        "Previous Month Price": forecast["price"].corr(forecast["price_lag_1"]),
    }
    driver_df = pd.DataFrame({"Factor": drivers.keys(), "Correlation": drivers.values()})
    driver_df = driver_df.reindex(driver_df["Correlation"].abs().sort_values().index)

    fig_drivers = px.bar(
        driver_df, x="Correlation", y="Factor", orientation="h",
        color="Correlation", color_continuous_scale=[ACCENT_GOLD, PRIMARY_GREEN],
    )
    fig_drivers.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=10, r=10, t=10, b=10),
        height=340, coloraxis_showscale=False,
    )
    st.plotly_chart(fig_drivers, use_container_width=True)
    st.caption("Correlation of each factor with rice price, based on the PaddyTrack model dataset.")

# --------------------------------------------------------------------------
# 8. ERROR DIAGNOSTICS
# --------------------------------------------------------------------------
st.markdown('<p class="section-header">🎯 Forecast Error Diagnostics</p>', unsafe_allow_html=True)

col_err_chart, col_err_metrics = st.columns([2, 1])

with col_err_chart:
    fig_err = go.Figure()
    fig_err.add_trace(go.Scatter(
        x=forecast["Date"], y=forecast["price"], mode="lines+markers",
        name="Actual", line=dict(color=PRIMARY_GREEN, width=2),
    ))
    fig_err.add_trace(go.Scatter(
        x=forecast["Date"], y=forecast["predicted_price"], mode="lines+markers",
        name="Predicted", line=dict(color=ACCENT_GOLD, width=2, dash="dash"),
    ))
    fig_err.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=10, r=10, t=10, b=10),
        height=340, legend=dict(orientation="h", y=1.1),
        yaxis_title="Price",
    )
    st.plotly_chart(fig_err, use_container_width=True)

st.markdown("---")
st.caption(
    "Data sources: WFP Food Prices (Sri Lanka) and the PaddyTrack SVR forecasting model. "
    "Built with Streamlit + Plotly."
)
