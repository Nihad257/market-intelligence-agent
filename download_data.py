# download_data.py — Step 4: Download gold futures data
import os
import pandas as pd
import yfinance as yf

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

print("Downloading gold futures data (GC=F)...")
df = yf.download("GC=F", period="2y", interval="1d", progress=False)

# Reset index so Date becomes a column
df = df.reset_index()

# Keep only necessary columns
df = df[["Date", "Close"]]
df.columns = ["date", "close"]

# Save to CSV
csv_path = os.path.join(DATA_DIR, "gold_prices.csv")
df.to_csv(csv_path, index=False)

print(f"✅ Saved {len(df)} rows to {csv_path}")
print(df.head())