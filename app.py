from fastapi import FastAPI
import sqlite3
import pandas as pd

app = FastAPI()

DB_PATH = "data/ipo_ml_withsme.db"

@app.get("/")
def home():
    return {"status": "IPO ML API running"}

@app.get("/today")
def today_predictions():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        "SELECT * FROM ipo_predictions ORDER BY predicted_probability DESC",
        conn
    )
    conn.close()
    return df.to_dict(orient="records")
