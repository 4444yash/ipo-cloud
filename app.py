from fastapi import FastAPI
import sqlite3
import pandas as pd
import os

app = FastAPI()

# Make sure this folder exists in your GitHub repo!
DB_PATH = "data/ipo_ml_withsme.db"

@app.get("/")
def home():
    return {"status": "IPO ML API running"}

@app.get("/today")
def today_predictions():
    # Check if DB exists to prevent a silent crash
    if not os.path.exists(DB_PATH):
        return {"error": f"Database not found at {DB_PATH}. Check your 'data' folder on GitHub."}
        
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        "SELECT * FROM ipo_predictions ORDER BY predicted_probability DESC",
        conn
    )
    conn.close()
    return df.to_dict(orient="records")
