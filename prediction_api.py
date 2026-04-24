"""
prediction_api.py — FastAPI Backend for LSTM Stock Prediction
=============================================================
Serves predictions at: http://localhost:5001/predict?symbol=RELIANCE

Run with:
    uvicorn prediction_api:app --host 0.0.0.0 --port 5001 --reload
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import pandas as pd
import yfinance as yf
import joblib
import os
from datetime import datetime, timedelta
from tensorflow.keras.models import load_model
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────
# App Setup
# ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="LSTM Stock Prediction API",
    description="Predicts next-day stock closing price using a trained LSTM model.",
    version="1.0.0"
)

# Allow all origins (needed for n8n / Streamlit to call this)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────
MODEL_PATH  = "model/lstm_model.h5"
SCALER_PATH = "model/scaler.pkl"
FEATURES    = ["Open", "High", "Low", "Close", "Volume"]
TARGET_IDX  = 3          # Close is at index 3
SEQUENCE_LEN = 60        # model was trained on 60-day windows

# Map friendly ticker names → Yahoo Finance symbols
TICKER_MAP = {
    "RELIANCE"  : "RELIANCE.NS",
    "TCS"       : "TCS.NS",
    "INFY"      : "INFY.NS",
    "HDFCBANK"  : "HDFCBANK.NS",
    "ICICIBANK" : "ICICIBANK.NS",
    "AAPL"      : "AAPL",
    "MSFT"      : "MSFT",
    "GOOG"      : "GOOG",
    "TSLA"      : "TSLA",
}

# ─────────────────────────────────────────────────────────────
# Load Model & Scaler at startup
# ─────────────────────────────────────────────────────────────
print("Loading LSTM model and scaler...")

if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
    raise RuntimeError(
        f"Model files not found!\n"
        f"  Expected: {MODEL_PATH}  and  {SCALER_PATH}\n"
        f"  Run the Colab notebook first to train and download these files."
    )

lstm_model = load_model(MODEL_PATH, compile=False)
lstm_model.compile(optimizer="adam", loss="mean_squared_error")

scaler = joblib.load(SCALER_PATH)

print(f"✅ Model loaded  → {MODEL_PATH}")
print(f"✅ Scaler loaded → {SCALER_PATH}")


# ─────────────────────────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────────────────────────
def fetch_ohlcv(ticker_symbol: str) -> pd.DataFrame:
    """Download the last 90 days of OHLCV data for a ticker."""
    end   = datetime.today()
    start = end - timedelta(days=90)

    raw = yf.download(
        ticker_symbol,
        start=start.strftime("%Y-%m-%d"),
        end=end.strftime("%Y-%m-%d"),
        progress=False,
    )

    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)

    df = raw[FEATURES].dropna()
    return df


def predict_next_close(df: pd.DataFrame) -> dict:
    """
    Use the last SEQUENCE_LEN rows of df to predict the next closing price.
    Returns a dict with predicted_price, current_price, and signal.
    """
    if len(df) < SEQUENCE_LEN:
        raise ValueError(
            f"Not enough data: need {SEQUENCE_LEN} rows, got {len(df)}."
        )

    # Take last 60 rows and scale
    window = df[FEATURES].values[-SEQUENCE_LEN:]
    scaled = scaler.transform(window)                  # shape (60, 5)
    x_input = scaled.reshape(1, SEQUENCE_LEN, len(FEATURES))

    # Predict (scaled)
    pred_scaled = float(lstm_model.predict(x_input, verbose=0)[0, 0])

    # Inverse-transform — only the Close column
    dummy = np.zeros((1, len(FEATURES)))
    dummy[0, TARGET_IDX] = pred_scaled
    predicted_price = float(scaler.inverse_transform(dummy)[0, TARGET_IDX])

    # Moving averages for signal
    close_series = df["Close"].values
    short_ma = float(np.mean(close_series[-10:]))   # 10-day MA
    long_ma  = float(np.mean(close_series[-30:]))   # 30-day MA
    current_price = float(close_series[-1])

    pct_change = (predicted_price - current_price) / current_price * 100

    if short_ma > long_ma and pct_change > 0.5:
        signal = "BUY"
    elif short_ma < long_ma and pct_change < -0.5:
        signal = "SELL"
    else:
        signal = "HOLD"

    return {
        "predicted_price" : round(predicted_price, 2),
        "current_price"   : round(current_price, 2),
        "short_ma"        : round(short_ma, 2),
        "long_ma"         : round(long_ma, 2),
        "pct_change"      : round(pct_change, 2),
        "signal"          : signal,
    }


# ─────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────

@app.get("/")
def root():
    """Health check."""
    return {
        "status"  : "online",
        "message" : "LSTM Stock Prediction API is running.",
        "endpoints": ["/predict", "/health", "/docs"]
    }


@app.get("/health")
def health():
    """Detailed health check — used by n8n and Streamlit."""
    return {
        "status"    : "healthy",
        "model"     : MODEL_PATH,
        "scaler"    : SCALER_PATH,
        "timestamp" : datetime.utcnow().isoformat() + "Z",
    }


@app.get("/predict")
def predict(
    symbol: str = Query(
        default="RELIANCE",
        description="Stock ticker symbol, e.g. RELIANCE, TCS, AAPL"
    )
):
    """
    Predict next-day closing price for a given stock symbol.

    Returns:
    - symbol           : input symbol
    - yahoo_ticker     : resolved Yahoo Finance ticker
    - current_price    : latest actual closing price
    - predicted_price  : LSTM model prediction for next trading day
    - pct_change       : expected % change
    - short_ma         : 10-day moving average
    - long_ma          : 30-day moving average
    - signal           : BUY / SELL / HOLD
    - timestamp        : UTC time of prediction
    """
    # Resolve ticker
    symbol_upper = symbol.upper().strip()
    yahoo_ticker = TICKER_MAP.get(symbol_upper, symbol_upper)

    # Fetch data
    try:
        df = fetch_ohlcv(yahoo_ticker)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch data for '{yahoo_ticker}' from Yahoo Finance: {str(e)}"
        )

    if df.empty or len(df) < SEQUENCE_LEN:
        raise HTTPException(
            status_code=422,
            detail=f"Not enough data for '{yahoo_ticker}'. Got {len(df)} rows, need {SEQUENCE_LEN}."
        )

    # Predict
    try:
        result = predict_next_close(df)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )

    return {
        "symbol"          : symbol_upper,
        "yahoo_ticker"    : yahoo_ticker,
        "current_price"   : result["current_price"],
        "predicted_price" : result["predicted_price"],
        "pct_change"      : result["pct_change"],
        "short_ma"        : result["short_ma"],
        "long_ma"         : result["long_ma"],
        "signal"          : result["signal"],
        "timestamp"       : datetime.utcnow().isoformat() + "Z",
    }


# ─────────────────────────────────────────────────────────────
# Entry point (optional — normally run via uvicorn CLI)
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("prediction_api:app", host="0.0.0.0", port=5001, reload=True)
