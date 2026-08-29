# detect_anomalies.py — Step 9: Find unusual gold price movements
import os
import sqlite3
import pandas as pd
import numpy as np

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PROJECT_DIR, "data", "market.db")

# Load data
conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query("SELECT date, close FROM gold_prices ORDER BY date", conn)
conn.close()

df["date"] = pd.to_datetime(df["date"])

# Calculate daily percentage change
df["pct_change"] = df["close"].pct_change() * 100

# Z-score method: flag days where |z-score| > 2.5
mean_change = df["pct_change"].mean()
std_change = df["pct_change"].std()

df["z_score"] = (df["pct_change"] - mean_change) / std_change
df["is_anomaly"] = df["z_score"].abs() > 2.5

# Show anomalies
anomalies = df[df["is_anomaly"]].copy()
anomalies = anomalies.dropna(subset=["pct_change"])

print("=" * 60)
print("ANOMALY DETECTION RESULTS")
print("=" * 60)
print(f"\nTotal days analyzed: {len(df)}")
print(f"Normal days: {len(df) - len(anomalies)}")
print(f"Anomalous days: {len(anomalies)}\n")

if len(anomalies) > 0:
    print("Top anomalies (unusual price moves):\n")
    top = anomalies.nlargest(10, "pct_change")[["date", "close", "pct_change", "z_score"]]
    for _, row in top.iterrows():
        direction = "📈 UP" if row["pct_change"] > 0 else "📉 DOWN"
        print(f"  {row['date'].date()} | ${row['close']:.2f} | {row['pct_change']:.2f}% | z={row['z_score']:.2f} | {direction}")
else:
    print("No strong anomalies detected.")

# Save anomalies to CSV
output_path = os.path.join(PROJECT_DIR, "data", "gold_anomalies.csv")
anomalies.to_csv(output_path, index=False)
print(f"\n✅ Saved anomalies to {output_path}")