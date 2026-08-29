# app.py — Step 11: FastAPI dashboard for Market Intelligence Agent
import os
import sqlite3
import pandas as pd
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq
from prophet import Prophet
import numpy as np

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PROJECT_DIR, "data", "market.db")

groq_client = Groq(api_key=GROQ_API_KEY)

app = FastAPI(title="Market Intelligence Agent", version="1.0.0")

SCHEMA = """
Table: gold_prices
Columns:
- id (INTEGER PRIMARY KEY)
- date (TEXT, format YYYY-MM-DD)
- close (REAL, daily closing price of gold futures in USD)
"""

def generate_sql(question: str) -> str:
    prompt = f"""Given the table schema, write a SQLite query to answer the user's question.

{SCHEMA}

User question: {question}

Return ONLY the SQL query, no explanation.
"""
    response = groq_client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=200,
    )
    return response.choices[0].message.content.strip()

def run_sql(sql: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description] if cursor.description else []
    conn.close()
    return columns, rows

def forecast():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT date, close FROM gold_prices ORDER BY date", conn)
    conn.close()
    df.columns = ["ds", "y"]
    df["ds"] = pd.to_datetime(df["ds"])
    model = Prophet(daily_seasonality=False)
    model.fit(df)
    future = model.make_future_dataframe(periods=30)
    forecast_df = model.predict(future)
    future_only = forecast_df[["ds", "yhat"]].tail(30)
    return future_only.to_dict(orient="records")

def anomalies():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT date, close FROM gold_prices ORDER BY date", conn)
    conn.close()
    df["pct_change"] = df["close"].pct_change() * 100
    mean = df["pct_change"].mean()
    std = df["pct_change"].std()
    df["z_score"] = (df["pct_change"] - mean) / std
    df["is_anomaly"] = df["z_score"].abs() > 2.5
    anom = df[df["is_anomaly"]].dropna(subset=["pct_change"])
    return anom[["date", "close", "pct_change"]].head(10).to_dict(orient="records")

def summary():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT date, close FROM gold_prices ORDER BY date", conn)
    conn.close()
    df["pct_change"] = df["close"].pct_change() * 100
    stats = {
        "current": round(df["close"].iloc[-1], 2),
        "avg": round(df["close"].mean(), 2),
        "max": round(df["close"].max(), 2),
        "min": round(df["close"].min(), 2),
        "volatility": round(df["pct_change"].std(), 2),
    }
    prompt = f"Write a 3-sentence executive summary on gold prices. Current: ${stats['current']}, Average: ${stats['avg']}, Max: ${stats['max']}, Min: ${stats['min']}, Volatility: {stats['volatility']}%."
    resp = groq_client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=300,
    )
    return resp.choices[0].message.content

class Query(BaseModel):
    question: str

@app.post("/query")
def query(request: Query):
    sql = generate_sql(request.question)
    columns, rows = run_sql(sql)
    return {"question": request.question, "sql": sql, "columns": columns, "rows": rows}

@app.get("/forecast")
def get_forecast():
    return forecast()

@app.get("/anomalies")
def get_anomalies():
    return anomalies()

@app.get("/summary")
def get_summary():
    return {"summary": summary()}

@app.get("/", response_class=HTMLResponse)
def dashboard():
    return """
<!doctype html>
<html>
<head>
  <title>Market Intelligence Agent</title>
  <style>
    body { font-family: -apple-system, Segoe UI, sans-serif; background:#f8fafc; padding:2rem; }
    .container { max-width:900px; margin:0 auto; }
    h1 { color:#0f172a; }
    .card { background:#fff; border-radius:16px; box-shadow:0 10px 25px rgba(0,0,0,.06); padding:24px; margin-top:20px; }
    input { width:70%; padding:12px; border:1px solid #e2e8f0; border-radius:10px; font-size:16px; }
    button { padding:12px 20px; margin-left:8px; background:#4f46e5; color:#fff; border:none; border-radius:10px; cursor:pointer; font-size:16px; }
    pre { background:#f1f5f9; padding:12px; border-radius:10px; overflow-x:auto; }
    .section { margin-top:14px; }
    table { border-collapse:collapse; width:100%; }
    td, th { border:1px solid #e2e8f0; padding:8px; text-align:left; }
  </style>
</head>
<body>
  <div class="container">
    <h1>📊 Market Intelligence Agent</h1>
    <p style="color:#64748b">Ask questions about gold prices. Built with NL-to-SQL + Prophet + Groq LLM.</p>

    <div class="card">
      <h3>Ask a question</h3>
      <input id="q" placeholder="e.g., What was the average gold price in 2025?" />
      <button onclick="ask()">Ask</button>
      <div id="sqlResult" class="section"></div>
    </div>

    <div class="card">
      <h3>📈 30-Day Forecast</h3>
      <button onclick="loadForecast()">Show Forecast</button>
      <div id="forecastResult" class="section"></div>
    </div>

    <div class="card">
      <h3>⚠️ Anomalies</h3>
      <button onclick="loadAnomalies()">Detect Anomalies</button>
      <div id="anomalyResult" class="section"></div>
    </div>

    <div class="card">
      <h3>📄 Executive Summary</h3>
      <button onclick="loadSummary()">Generate Summary</button>
      <div id="summaryResult" class="section"></div>
    </div>
  </div>

<script>
async function ask() {
  const q = document.getElementById('q').value;
  if (!q) return;
  const res = await fetch('/query', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({question:q})});
  const data = await res.json();
  document.getElementById('sqlResult').innerHTML = `<p><strong>SQL:</strong> ${data.sql}</p><pre>${JSON.stringify(data.rows)}</pre>`;
}
async function loadForecast() {
  const res = await fetch('/forecast');
  const data = await res.json();
  let html = '<table><tr><th>Date</th><th>Forecast</th></tr>';
  data.forEach(d => html += `<tr><td>${d.ds}</td><td>${d.yhat.toFixed(2)}</td></tr>`);
  html += '</table>';
  document.getElementById('forecastResult').innerHTML = html;
}
async function loadAnomalies() {
  const res = await fetch('/anomalies');
  const data = await res.json();
  let html = '<ul>';
  data.forEach(d => html += `<li>${d.date}: ${d.close.toFixed(2)} (${d.pct_change.toFixed(2)}%)</li>`);
  html += '</ul>';
  document.getElementById('anomalyResult').innerHTML = html;
}
async function loadSummary() {
  const res = await fetch('/summary');
  const data = await res.json();
  document.getElementById('summaryResult').innerHTML = `<p>${data.summary}</p>`;
}
</script>
</body>
</html>
"""