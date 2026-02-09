from fastapi import FastAPI
import sqlite3
import pandas as pd
import os

app = FastAPI()

DB_PATH = "data/ipo_ml_withsme.db"

@app.get("/")
def home():
    return {"status": "IPO ML API running", "database": os.path.exists(DB_PATH)}

@app.get("/today")
def today_predictions():
    if not os.path.exists(DB_PATH):
        return {"error": "Database missing"}
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM ipo_predictions ORDER BY predicted_probability DESC", conn)
    conn.close()
    return df.to_dict(orient="records")
