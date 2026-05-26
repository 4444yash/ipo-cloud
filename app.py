from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sqlite3
import subprocess
import pandas as pd
import os
import json

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# KEEP THIS: The API still needs a place to save what it receives
# Ensure your API service has a volume mounted at /app/data
DB_PATH = "data/ipo_ml_withsme.db" 

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
            subscription_x REAL,
            open_date TEXT,
            close_date TEXT,
            ipo_type TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS market_meter (
            score INTEGER,
            mood_label TEXT,
            color TEXT,
            nifty_price REAL,
            nifty_change_pct REAL,
            vix_value REAL,
            updated_at TEXT
        )
    """)
    # 👇 NEW: Manual VIP keys table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS vip_keys (
            key TEXT PRIMARY KEY,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.close()

init_db()

# Helper to verify key status
def check_vip_key(key: str) -> bool:
    if not key:
        return False
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM vip_keys WHERE key = ?", (key.strip(),))
    row = cursor.fetchone()
    conn.close()
    return row is not None

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    upi_id = os.getenv("UPI_ID", "yourname@upi")
    return templates.TemplateResponse("index.html", {"request": request, "upi_id": upi_id})

@app.get("/today")
def today_predictions(key: str = None):
    if not os.path.exists(DB_PATH):
        return {"error": "Database not initialized yet"}
    
    is_vip = check_vip_key(key)
    conn = sqlite3.connect(DB_PATH)
    try:
        # Get the latest predictions
        df = pd.read_sql("SELECT * FROM ipo_predictions ORDER BY predicted_probability DESC", conn)
        df = df.fillna("") # 👇 Clean NaN/None values for safe JSON serialization
        
        # 👇 NEW: If not a valid VIP, redact key ML signal columns for Freemium paywall
        if not is_vip and not df.empty:
            df["decision_label"] = "LOCKED"
            df["predicted_probability"] = 0.0
            df["final_decision"] = 0
            
        return df.to_dict(orient="records")
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

# 👇 NEW: Secure admin route to dynamically add GPay-purchased access keys
@app.get("/add-vip-key")
def add_vip_key(admin_pass: str, key: str, notes: str = ""):
    required_pass = os.getenv("ADMIN_PASS", "GPayAdminPass123")
    if admin_pass != required_pass:
        return {"status": "error", "message": "Unauthorized: Incorrect admin_pass"}
        
    if not key or len(key.strip()) < 3:
        return {"status": "error", "message": "Invalid key format"}
        
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("INSERT OR REPLACE INTO vip_keys (key, notes) VALUES (?, ?)", (key.strip(), notes.strip()))
        conn.commit()
        return {"status": "success", "message": f"Access Key '{key}' successfully activated!"}
    except Exception as e:
        return {"status": "error", "message": f"Database error: {e}"}
    finally:
        conn.close()

@app.get("/scorecard_data")
def scorecard_data():
    if not os.path.exists(DB_PATH):
        return {"error": "Database not initialized yet"}
    
    conn = sqlite3.connect(DB_PATH)
    try:
        # Get the latest scorecard
        df = pd.read_sql("SELECT * FROM ipo_scorecard", conn)
        return df.to_dict(orient="records")
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

@app.get("/market_meter_data")
def market_meter_data():
    if not os.path.exists(DB_PATH):
        return {"error": "Database not initialized yet"}
    
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql("SELECT * FROM market_meter", conn)
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
        
        # Save to the API's local database
        conn = sqlite3.connect(DB_PATH)
        
        if df.empty:
            # Clear the predictions table so dashboard shows "No predictions" properly
            cur = conn.cursor()
            cur.execute("DELETE FROM ipo_predictions")
            conn.commit()
            conn.close()
            return {"status": "success", "message": "Dashboard cleared (no active IPOs)"}

        df.to_sql("ipo_predictions", conn, if_exists="replace", index=False)
        conn.close()
        
        return {"status": "success", "rows_updated": len(df)}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/upload_scorecard")
async def upload_scorecard(request: Request):
    try:
        data = await request.json()
        df = pd.DataFrame(data)
        
        if df.empty:
            return {"message": "No data received"}

        conn = sqlite3.connect(DB_PATH)
        df.to_sql("ipo_scorecard", conn, if_exists="replace", index=False)
        conn.close()
        
        return {"status": "success", "rows_updated": len(df)}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/upload_market_meter")
async def upload_market_meter(request: Request):
    try:
        data = await request.json()
        df = pd.DataFrame(data)
        
        if df.empty:
            return {"message": "No data received"}

        conn = sqlite3.connect(DB_PATH)
        df.to_sql("market_meter", conn, if_exists="replace", index=False)
        conn.close()
        
        return {"status": "success", "rows_updated": len(df)}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/refresh-pipeline")
async def refresh_pipeline(background_tasks: BackgroundTasks):
    def run_p():
        try:
            print("⏳ Manual Refresh Triggered via API...")
            subprocess.run(["python", "run_pipeline.py"], check=True)
            print("✅ Manual Refresh Complete.")
        except Exception as e:
            print(f"❌ Manual Refresh Failed: {e}")

    background_tasks.add_task(run_p)
    return {"status": "success", "message": "Pipeline started in background"}
