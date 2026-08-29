# build_db.py — Step 5: Create SQLite database and load gold prices
import os
import sqlite3
import pandas as pd

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "market.db")
CSV_PATH = os.path.join(DATA_DIR, "gold_prices.csv")

# Load CSV
print("Loading gold prices CSV...")
df = pd.read_csv(CSV_PATH)

# Remove rows with missing data
df = df.dropna(subset=["date", "close"])
print(f"Loaded {len(df)} clean rows.")

# Connect to SQLite
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create table
cursor.execute("""
CREATE TABLE IF NOT EXISTS gold_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    close REAL NOT NULL
)
""")

# Clear old data
cursor.execute("DELETE FROM gold_prices")

# Insert all clean rows
inserted = 0
for _, row in df.iterrows():
    date_val = str(row["date"]).strip()
    close_val = float(row["close"])
    cursor.execute(
        "INSERT INTO gold_prices (date, close) VALUES (?, ?)",
        (date_val, close_val)
    )
    inserted += 1

conn.commit()
conn.close()

print(f"✅ Database saved at {DB_PATH}")
print(f"Inserted {inserted} rows into gold_prices table.")