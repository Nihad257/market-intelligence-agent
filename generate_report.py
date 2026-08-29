# generate_report.py — Step 10: LLM executive summary
import os
import sqlite3
import pandas as pd
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PROJECT_DIR, "data", "market.db")

groq_client = Groq(api_key=GROQ_API_KEY)

# Load summary stats
conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query("SELECT date, close FROM gold_prices ORDER BY date", conn)
conn.close()

df["date"] = pd.to_datetime(df["date"])
df["pct_change"] = df["close"].pct_change() * 100

stats = {
    "start_date": df["date"].min().date(),
    "end_date": df["date"].max().date(),
    "days": len(df),
    "current_price": round(df["close"].iloc[-1], 2),
    "average_price": round(df["close"].mean(), 2),
    "max_price": round(df["close"].max(), 2),
    "min_price": round(df["close"].min(), 2),
    "avg_daily_change": round(df["pct_change"].mean(), 2),
    "volatility": round(df["pct_change"].std(), 2),
}

# Create prompt
prompt = f"""You are a financial analyst. Write a short executive summary (3-4 sentences) about the gold market using the following data.

Gold Price Data:
- Period: {stats['start_date']} to {stats['end_date']}
- Total days: {stats['days']}
- Current price: ${stats['current_price']}
- Average price: ${stats['average_price']}
- Maximum price: ${stats['max_price']}
- Minimum price: ${stats['min_price']}
- Average daily change: {stats['avg_daily_change']}%
- Volatility (std dev of daily change): {stats['volatility']}%

Write in plain English, no jargon. Highlight the main trend, recent levels, and what stands out.
"""

print("Generating executive summary...\n")

response = groq_client.chat.completions.create(
    model="openai/gpt-oss-20b",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.3,
    max_tokens=400,
)

summary = response.choices[0].message.content

print("=" * 60)
print("EXECUTIVE SUMMARY")
print("=" * 60)
print(summary)
print("=" * 60)

# Save summary
output_path = os.path.join(PROJECT_DIR, "data", "executive_summary.txt")
with open(output_path, "w", encoding="utf-8") as f:
    f.write(summary)

print(f"\n✅ Summary saved to {output_path}")