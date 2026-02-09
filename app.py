from fastapi import FastAPI
import sqlite3
import pandas as pd
import os

app = FastAPI()

# Ensure this matches the folder name in your GitHub repo (case-sensitive!)
DB_PATH = "data/ipo_ml_withsme.db"

@app.get("/")
def home():
    # This acts as your Health Check
    return {
        "status": "IPO ML API running",
        "database_connected": os.path.exists(DB_PATH)
    }

@app.get("/today")
def today_predictions():
    if not os.path.exists(DB_PATH):
        return {"error": "Database file not found. Please upload 'data/ipo_ml_withsme.db'"}
    
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql(
            "SELECT * FROM ipo_predictions ORDER BY predicted_probability DESC",
            conn
        )
        conn.close()
        return df.to_dict(orient="records")
    except Exception as e:
        return {"error": str(e)}
