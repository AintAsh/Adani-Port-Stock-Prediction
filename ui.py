import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import streamlit.components.v1 as components

# =========================
# Page Config
# =========================
st.set_page_config(
    page_title="Stock Prediction Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Stock Prediction Dashboard")
st.caption("Next-Day Forecast · Risk · Multi-Day Projection")

st.markdown("---")

# =========================
# Layout
# =========================
left, center, right = st.columns([1.1, 1.9, 1.6])

# =========================
# LEFT — INPUTS
# =========================
with left:
    st.subheader("📊 Market Data Input")

    prev_close = st.number_input("Previous Close", value=1500.0)
    open_price = st.number_input("Open Price", value=1505.0)
    high_price = st.number_input("High Price", value=1520.0)
    low_price = st.number_input("Low Price", value=1490.0)
    close_price = st.number_input("Close Price", value=1502.0)
    volume = st.number_input("Volume", value=900000)

    run_btn = st.button("🚀 Run Prediction", use_container_width=True)

# =========================
# CENTER — SUMMARY
# =========================
with center:
    st.subheader("📈 Prediction Summary")

    if run_btn:
        payload = {
            "prev_close": prev_close,
            "open_price": open_price,
            "high_price": high_price,
            "low_price": low_price,
            "close_price": close_price,
            "volume": volume
        }

        response = requests.post(
            "https://adani-port-stock-prediction.onrender.com/predict",
            json=payload
        )

        if response.status_code == 200:
            predicted_close = response.json()["Predicted_Next_Day_Close"]

            # =========================
            # CORE CALCULATIONS
            # =========================
            predicted_return = ((predicted_close - close_price) / close_price) * 100
            confidence = min(95, max(40, abs(predicted_return) * 2))

            if predicted_return > 1:
                signal = "Bullish"
                signal_color = "#22c55e"
            elif predicted_return < -1:
                signal = "Bearish"
                signal_color = "#ef4444"
            else:
                signal = "Neutral"
                signal_color = "#eab308"

            intraday_volatility = (high_price - low_price) / close_price * 100
            risk_score = min(100, max(10, intraday_volatility * 10 + (100 - confidence)))

            risk_color = "#22c55e" if risk_score < 35 else "#eab308" if risk_score < 65 else "#ef4444"
            risk_label = "Low Risk" if risk_score < 35 else "Moderate Risk" if risk_score < 65 else "High Risk"

            # =========================
            # SUMMARY CARD (HTML)
            # =========================
            summary_html = f"""
            <div style="background:#0f172a;padding:28px;border-radius:18px;color:white;">
                <div style="color:#9ca3af">Predicted Return</div>
                <h1 style="color:{'#22c55e' if predicted_return > 0 else '#ef4444'}">
                    {predicted_return:.2f}%
                </h1>

                <div style="color:#9ca3af">Confidence</div>
                <h2 style="color:#38bdf8">{confidence:.0f}%</h2>
                <div style="background:#1f2933;border-radius:10px;height:8px;">
                    <div style="width:{confidence}%;background:#38bdf8;height:8px;border-radius:10px;"></div>
                </div>

                <div style="color:#9ca3af;margin-top:12px">Market Signal</div>
                <h2 style="color:{signal_color}">{signal}</h2>

                <div style="color:#9ca3af;margin-top:12px">Risk Score</div>
                <h2 style="color:{risk_color}">{risk_score:.0f} / 100</h2>
                <h3 style="color:{risk_color}; margin-top:4px;">
    {risk_label}
</h3>

            </div>
            """

            components.html(summary_html, height=450)

# =========================
# RIGHT — PRICE FORECAST + MULTI-DAY
# =========================
with right:
    if run_btn and response.status_code == 200:

        # =========================
        # NEXT-DAY PRICE ESTIMATES
        # =========================
        predicted_open = close_price + 0.3 * (predicted_close - close_price)
        daily_range = high_price - low_price

        predicted_high = max(predicted_open, predicted_close) + 0.5 * daily_range
        predicted_low = min(predicted_open, predicted_close) - 0.5 * daily_range

        price_html = f"""
        <div style="background:#020617;padding:26px;border-radius:18px;color:white;">
            <h3>📌 Next-Day Price Forecast</h3>

            <div style="color:#9ca3af">Predicted Open</div>
            <h2>₹ {predicted_open:.2f}</h2>

            <div style="color:#9ca3af">Predicted Close</div>
            <h2>₹ {predicted_close:.2f}</h2>

            <div style="color:#9ca3af">Expected Range</div>
            <h3>₹ {predicted_low:.2f} — ₹ {predicted_high:.2f}</h3>
            </div>
            """

        components.html(price_html, height=360)

        # =========================
        # MULTI-DAY FORECAST
        # =========================
        forecast_days = 5
        daily_return = predicted_return / 100
        volatility = (high_price - low_price) / close_price

        days = []
        mean_prices = []
        upper_band = []
        lower_band = []

        current_price = predicted_close

        for day in range(1, forecast_days + 1):
            current_price = current_price * (1 + daily_return)
            mean_prices.append(current_price)
            upper_band.append(current_price * (1 + volatility))
            lower_band.append(current_price * (1 - volatility))
            days.append(f"Day {day}")

        forecast_df = pd.DataFrame({
            "Day": days,
            "Mean": mean_prices,
            "Upper": upper_band,
            "Lower": lower_band
        })

        # =========================
        # PROBABILITY BAND CHART
        # =========================
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=forecast_df["Day"],
            y=forecast_df["Upper"],
            line=dict(width=0),
            showlegend=False
        ))

        fig.add_trace(go.Scatter(
            x=forecast_df["Day"],
            y=forecast_df["Lower"],
            fill="tonexty",
            fillcolor="rgba(56,189,248,0.25)",
            line=dict(width=0),
            showlegend=False
        ))

        fig.add_trace(go.Scatter(
            x=forecast_df["Day"],
            y=forecast_df["Mean"],
            mode="lines+markers",
            line=dict(color="#38bdf8", width=3),
            name="Expected Price"
        ))

        fig.update_layout(
            title="📈 5-Day Price Forecast (Probability Bands)",
            paper_bgcolor="#020617",
            plot_bgcolor="#020617",
            font_color="white",
            margin=dict(l=30, r=30, t=60, b=30),
            height=340
        )

        st.markdown("<br>", unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)

# =========================
# Footer
# =========================
st.markdown("---")
st.caption("FastAPI Backend · ML Model · Streamlit Dashboard")

