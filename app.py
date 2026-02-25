from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sqlite3
import pandas as pd
import os
import json

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# KEEP THIS: The API still needs a place to save what it receives
# Ensure your API service has a volume mounted at /app/data
DB_PATH = "/app/data/ipo_ml_withsme.db" 

# Create the table if it doesn't exist (First run setup)
def init_db():
    if not os.path.exists(os.path.dirname(DB_PATH)):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    # Basic table structure if empty
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ipo_predictions (
            ipo_name TEXT,
            predicted_probability REAL,
            gmp_pct REAL,
            final_decision INTEGER,
            decision_label TEXT,
            predicted_at TEXT,
            listing_date TEXT,
            subscription_x REAL
        )
    """)
    conn.close()

init_db()

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/today")
def today_predictions():
    if not os.path.exists(DB_PATH):
        return {"error": "Database not initialized yet"}
    
    conn = sqlite3.connect(DB_PATH)
    try:
        # Get the latest predictions
        df = pd.read_sql("SELECT * FROM ipo_predictions ORDER BY predicted_probability DESC", conn)
        return df.to_dict(orient="records")
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

# 🚀 NEW ENDPOINT: The Scraper sends data here!
@app.post("/upload_predictions")
async def upload_predictions(request: Request):
    try:
        data = await request.json() # Receive JSON data
        
        # Convert JSON back to DataFrame
        df = pd.DataFrame(data)
        
        if df.empty:
            return {"message": "No data received"}

        # Save to the API's local database
        conn = sqlite3.connect(DB_PATH)
        df.to_sql("ipo_predictions", conn, if_exists="replace", index=False)
        conn.close()
        
        return {"status": "success", "rows_updated": len(df)}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}
