from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import pickle
from fastapi.responses import JSONResponse

# =========================
# Load trained model
# =========================
with open("Stock_Prediction.pkl", "rb") as f:
    model = pickle.load(f)

app = FastAPI(title="Stock Price Prediction API")

# =========================
# Input schema
# =========================
class StockInput(BaseModel):
    prev_close: float
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float

# =========================
# Prediction endpoint
# =========================
@app.post("/predict")
def predict_stock_price(data: StockInput):
    try:
        # Create DataFrame with EXACT training columns
        input_df = pd.DataFrame([{
            "Prev Close": data.prev_close,
            "Open": data.open_price,
            "High": data.high_price,
            "Low": data.low_price,
            "Close": data.close_price,
            "Volume": data.volume
        }])

        # Predict directly (NO scaler)
        pred = model.predict(input_df)

        prediction = float(pred[0])

        # Safety check
        prediction = max(0.0, prediction)

        return JSONResponse(content={
            "Predicted_Next_Day_Close": round(prediction, 2)
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =========================
# Health check
# =========================
@app.get("/")
def home():
    return {"message": "Stock Price Prediction API is running"}
