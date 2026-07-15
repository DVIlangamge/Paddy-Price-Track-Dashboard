# PaddyTrack Rice Price Dashboard — Setup Steps

## 1. Folder structure
Keep this layout (already set up for you in this download):

```
rice_dashboard/
├── app.py
├── requirements.txt
└── data/
    ├── wfp_food_prices_lka.csv
    ├── rice_predictions.csv
    └── Historicl_Diesel_Price-_from_2010.xlsx
```

## 2. Install Python and dependencies
Make sure you have Python 3.9+ installed, then from inside the `rice_dashboard` folder run:

```bash
pip install -r requirements.txt
```

## 3. Run the dashboard
```bash
streamlit run app.py
```
Streamlit will open a browser tab automatically (usually `http://localhost:8501`).
If it doesn't open, copy the "Local URL" printed in the terminal into your browser.

## 4. Using the dashboard
- Use the **District** and **Rice Type** dropdowns in the left sidebar to filter the
  historical price data (price trend, monthly average, latest price).
- The **forecast, error diagnostics, volatility gauge, and key influences** panels come
  from the PaddyTrack model dataset (`rice_predictions.csv`), which was trained on an
  aggregate national series — these do not change with the district/rice-type filter.
  A caption in the sidebar explains this.

## 5. Customizing
- **Colors**: edit the `PRIMARY_GREEN` / `ACCENT_GOLD` variables near the top of `app.py`.
- **Default district**: change the `index=` argument in the `st.sidebar.selectbox("District", ...)` line.
- **Volatility scaling**: the gauge uses `coefficient of variation × 3`, capped at 100 —
  adjust the multiplier in the `volatility_score` calculation if you want it more/less sensitive.

## 6. Deploying (optional)
Once it works locally, you can deploy for free on
[Streamlit Community Cloud](https://streamlit.io/cloud):
1. Push this folder to a GitHub repo.
2. Go to share.streamlit.io, connect the repo, and point it at `app.py`.
3. Community Cloud installs `requirements.txt` automatically.

## What each section shows
| Section | Source | Description |
|---|---|---|
| Latest Rice Price | WFP data (filtered) | Most recent recorded price for the selected district/rice type |
| Avg. Forecasted Price | rice_predictions.csv | Average of the model's last 6 forecast points |
| Price Trend | WFP data (filtered) | Line chart of historical prices |
| Volatility Gauge | WFP data (filtered) | Coefficient of variation of the last 12 records, scaled 0–100 |
| Monthly Average Price | WFP data (filtered) | Bar chart of monthly average prices |
| Key Influences | rice_predictions.csv | Correlation of price with fuel index, weather, and lagged price |
| Error Diagnostics | rice_predictions.csv | Actual vs. predicted price line, plus MAE / RMSE / MAPE |
