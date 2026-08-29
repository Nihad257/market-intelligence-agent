# test_db.py — Step 6: Verify SQLite database works
import sqlite3
import os

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PROJECT_DIR, "data", "market.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("=" * 60)
print("DATABASE TESTS")
print("=" * 60)

# Test 1: Count rows
cursor.execute("SELECT COUNT(*) FROM gold_prices")
count = cursor.fetchone()[0]
print(f"\n1. Total rows: {count}")

# Test 2: Earliest and latest date
cursor.execute("SELECT MIN(date), MAX(date) FROM gold_prices")
min_date, max_date = cursor.fetchone()
print(f"2. Date range: {min_date} to {max_date}")

# Test 3: Average close price
cursor.execute("SELECT AVG(close) FROM gold_prices")
avg_price = cursor.fetchone()[0]
print(f"3. Average close price: ${avg_price:.2f}")

# Test 4: Latest 5 days
cursor.execute("SELECT date, close FROM gold_prices ORDER BY date DESC LIMIT 5")
print("\n4. Latest 5 days:")
for row in cursor.fetchall():
    print(f"   {row[0]} → ${row[1]:.2f}")

# Test 5: Highest close price
cursor.execute("SELECT date, close FROM gold_prices ORDER BY close DESC LIMIT 1")
highest = cursor.fetchone()
print(f"\n5. Highest close: ${highest[1]:.2f} on {highest[0]}")

conn.close()
print("\n✅ All database tests passed.")