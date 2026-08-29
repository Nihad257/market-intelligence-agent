# forecast.py — Step 8: Forecast future gold prices with Prophet
import os
import sqlite3
import pandas as pd
from prophet import Prophet

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PROJECT_DIR, "data", "market.db")

# Load data from SQLite
conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query("SELECT date, close FROM gold_prices ORDER BY date", conn)
conn.close()

# Prophet requires columns named ds and y
df.columns = ["ds", "y"]
df["ds"] = pd.to_datetime(df["ds"])

print(f"Loaded {len(df)} days of data.")
print(f"Date range: {df['ds'].min().date()} to {df['ds'].max().date()}")

# Create and fit Prophet model
print("\nTraining Prophet model...")
model = Prophet(daily_seasonality=False, yearly_seasonality=True, weekly_seasonality=True)
model.fit(df)

# Forecast next 30 days
print("Forecasting next 30 days...")
future = model.make_future_dataframe(periods=30)
forecast = model.predict(future)

# Show the forecasted future values only
forecast_future = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(30)
print("\n✅ Forecast for next 30 days:")
print(forecast_future.to_string(index=False))

# Save forecast to CSV
output_path = os.path.join(PROJECT_DIR, "data", "gold_forecast.csv")
forecast_future.to_csv(output_path, index=False)
print(f"\n✅ Saved forecast to {output_path}")