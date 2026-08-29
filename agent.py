# agent.py — Step 7: NL-to-SQL agent
import os
import sqlite3
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PROJECT_DIR, "data", "market.db")

groq_client = Groq(api_key=GROQ_API_KEY)

SCHEMA = """
Table: gold_prices
Columns:
- id (INTEGER PRIMARY KEY)
- date (TEXT, format YYYY-MM-DD)
- close (REAL, daily closing price of gold futures in USD)
"""

def generate_sql(question: str) -> str:
    prompt = f"""You are a SQL expert. Given the following table schema, write a SQLite query to answer the user's question.

{SCHEMA}

User question: {question}

Return ONLY the SQL query, no explanation, no markdown. Make sure it is valid SQLite.
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

def nl_to_sql(question: str):
    sql = generate_sql(question)
    print(f"Generated SQL: {sql}")
    columns, rows = run_sql(sql)
    return {
        "question": question,
        "sql": sql,
        "columns": columns,
        "rows": rows
    }

if __name__ == "__main__":
    test_questions = [
        "What is the average gold price?",
        "What was the highest gold price in 2025?",
        "How many days of data do we have?",
        "What was the gold price on 2026-01-29?",
    ]
    
    for q in test_questions:
        print("\n" + "="*60)
        print(f"Question: {q}")
        result = nl_to_sql(q)
        print(f"Columns: {result['columns']}")
        print(f"Result: {result['rows'][:5]}")