from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sqlite3
import pandas as pd
import os
import re

app = FastAPI()
templates = Jinja2Templates(directory="templates")

DB_PATH = "/app/data/ipo_ml_withsme.db"

def init_db():
    if not os.path.exists(os.path.dirname(DB_PATH)):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ipo_predictions (
            ipo_name TEXT,
            predicted_probability REAL,
            gmp_pct REAL,
            gmp REAL,
            final_decision INTEGER,
            decision_label TEXT,
            predicted_at TEXT,
            listing_date TEXT,
            subscription_x REAL,
            ipo_price REAL,
            has_anchor INTEGER
        )
    """)
    conn.close()

init_db()

def clean_ipo_name(name: str) -> str:
    """Strip exchange/market/status suffixes to get the base IPO name.
    Handles: NSE, BSE, SME, O, C, CT, U, LT, CAllotted, Allotted and all combos.
    """
    name = name.strip()
    # Strip exchange (NSE/BSE) + optional SME + optional status code
    name = re.sub(
        r'\s+(NSE|BSE)(\s+SME)?(\s+(O|C|CT|U|LT|CAllotted|Allotted))?$',
        '', name, flags=re.IGNORECASE
    )
    # Strip any remaining standalone status codes
    name = re.sub(
        r'\s+(O|C|CT|U|LT|CAllotted|Allotted)$',
        '', name, flags=re.IGNORECASE
    )
    return name.strip()

def clean_listing_date(val) -> str:
    """Take only the first line of the listing date field (strip scraped garbage)."""
    if not val:
        return val
    return str(val).split('\n')[0].strip()

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/today")
def today_predictions():
    if not os.path.exists(DB_PATH):
        return {"error": "Database not initialized yet"}
    
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql("SELECT * FROM ipo_predictions ORDER BY predicted_probability DESC", conn)

        # Return only clean, user-facing fields
        display_cols = [c for c in [
            "ipo_name", "listing_date", "ipo_price", "gmp",
            "gmp_pct", "subscription_x", "has_anchor",
            "predicted_probability", "decision_label", "predicted_at"
        ] if c in df.columns]

        df = df[display_cols].copy()

        # Clean dirty listing_date values (e.g. "25-Feb\nGMP: 0")
        if "listing_date" in df.columns:
            df["listing_date"] = df["listing_date"].apply(clean_listing_date)

        # Deduplicate: compute base name, keep highest-probability row per IPO
        df["_base_name"] = df["ipo_name"].apply(clean_ipo_name)
        df = (
            df.sort_values("predicted_probability", ascending=False)
              .drop_duplicates(subset=["_base_name"])
              .drop(columns=["_base_name"])
        )
        # Replace display name with cleaned version
        df["ipo_name"] = df["ipo_name"].apply(clean_ipo_name)

        return df.to_dict(orient="records")
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

@app.post("/upload_predictions")
async def upload_predictions(request: Request):
    try:
        data = await request.json()
        df = pd.DataFrame(data)
        
        if df.empty:
            return {"message": "No data received"}

        conn = sqlite3.connect(DB_PATH)
        df.to_sql("ipo_predictions", conn, if_exists="replace", index=False)
        conn.close()
        
        return {"status": "success", "rows_updated": len(df)}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}
