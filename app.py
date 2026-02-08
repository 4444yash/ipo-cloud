from fastapi import FastAPI
import sqlite3
import pandas as pd
import os

app = FastAPI()

# Point to the database folder you confirmed exists
DB_PATH = "data/ipo_ml_withsme.db"

@app.get("/")
def home():
    # Railway pings this to keep your app alive
    return {"status": "IPO ML API running", "database_found": os.path.exists(DB_PATH)}

@app.get("/today")
def today_predictions():
    if not os.path.exists(DB_PATH):
        return {"error": "Database file not found in /data folder"}
    
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM ipo_predictions ORDER BY predicted_probability DESC", conn)
    conn.close()
    return df.to_dict(orient="records")
