import sqlite3
import numpy as np
import pandas as pd
import joblib
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import requests  # <--- NEW: Needed to talk to the API
import json
import os
from datetime import datetime
from tensorflow.keras.models import load_model

# ======================
# CONFIG
# ======================

# Raw data source (Created by the scraper in the previous step)
DB_PATH = "data/ipo_ml_withsme.db"
MODEL_PATH = "ipo_dl_model.h5"
SCALER_PATH = "scaler.pkl"

# 👇 REPLACE THIS WITH YOUR ACTUAL RAILWAY APP URL OR USE ENVIRONMENT VARIABLES
API_URL = os.getenv("API_URL", "http://localhost:8000/upload_predictions")

NTFY_TOPIC = os.getenv("NTFY_TOPIC", "ipo_alerts_my_portfolio")  # Change this to whatever word you want!

PROB_THRESHOLD = 0.70
GMP_MIN = 5.0
GMP_AUTO_INVEST = 15.0

# ======================
# LOAD MODEL
# ======================

if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
    print(f"❌ Error: Model or scaler file not found")
    exit()


model = load_model(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)
print("✅ Model and Scaler loaded")

# ======================
# LOAD RAW DATA (From Local Scraper)
# ======================

conn = sqlite3.connect(DB_PATH)

# Get data scraped in the last 24 hours that is NOT yet listed
query = """
SELECT *
FROM ipo_raw_data
WHERE scraped_at >= datetime('now', '-24 hours') AND is_listed = 0
"""

try:
    df = pd.read_sql(query, conn)
except Exception as e:
    print(f"⚠️ Database error (Table might not exist yet): {e}")
    conn.close()
    exit()

conn.close()

print(f"✅ Rows scraped recently: {len(df)}")

if df.empty:
    print("⚠️ No IPO data found for today. Exiting.")
    exit()

# ======================
# PREPROCESSING & CLEANING
# ======================

# Remove listed or closed IPOs that we should no longer track as 'Live'
# Logic: We already filtered by is_listed = 0 in SQL, but we keep this as a double-safety
listed_patterns = [
    r"L@", r"\(-?\d+\.?\d*%\)", r"Listed", r"listed", 
    r"Allotted", r"Basis", r"Allotment", r"allotted", r"basis"
]
pattern = "|".join(listed_patterns)
df = df[~df["ipo_name"].str.contains(pattern, regex=True, na=False)]

if df.empty:
    print("⚠️ No ACTIVE IPOs detected (all are likely listed or closed). Clearing dashboard.")
    try:
        requests.post(API_URL, json=[])
        print("✅ Dashboard cleared successfully.")
    except Exception as e:
        print(f"❌ Failed to clear dashboard: {e}")
    exit()

# Fix Column Names (Safety Check)
if "subscription" in df.columns and "subscription_x" not in df.columns:
    df.rename(columns={"subscription": "subscription_x"}, inplace=True)

# Force Numeric
numeric_cols = ["gmp", "subscription_x", "ipo_price", "ipo_size_cr", "has_anchor"]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=["gmp", "ipo_price", "ipo_size_cr"])
df = df[df["ipo_price"] > 0].copy()

# ======================
# FEATURE ENGINEERING
# ======================

df["gmp_pct"] = (df["gmp"] / df["ipo_price"]) * 100
df["log_subscription"] = np.log1p(df["subscription_x"])
df["log_ipo_size"] = np.log1p(df["ipo_size_cr"])

features = [
    "gmp_pct", "subscription_x", "log_subscription", 
    "ipo_size_cr", "log_ipo_size", "ipo_price", "has_anchor"
]

X = df[features]
X_scaled = scaler.transform(X)

# ======================
# MODEL PREDICTION
# ======================

df["predicted_probability"] = model.predict(X_scaled).flatten()

# Decision Logic
df["final_decision"] = 0 
df.loc[df["gmp_pct"] >= GMP_AUTO_INVEST, "final_decision"] = 1
df.loc[
    (df["gmp_pct"] >= GMP_MIN) & 
    (df["gmp_pct"] < GMP_AUTO_INVEST) & 
    (df["predicted_probability"] >= PROB_THRESHOLD), 
    "final_decision"
] = 1

df["decision_label"] = df["final_decision"].map({1: "INVEST", 0: "SKIP"})

# Convert timestamps to string for JSON serialization
df["predicted_at"] = datetime.now().isoformat()
df["listing_date"] = df["listing_date"].astype(str) 

# ======================
# PUSH NOTIFICATIONS (NTFY)
# ======================
print("\n🔔 Checking for new INVEST alerts...")
ALERTS_FILE = "data/sent_alerts.txt"
if not os.path.exists(ALERTS_FILE):
    open(ALERTS_FILE, "w").close()

with open(ALERTS_FILE, "r") as f:
    sent_alerts = f.read().splitlines()

new_alerts_sent = 0
for _, row in df[df["decision_label"] == "INVEST"].iterrows():
    ipo_name = row["ipo_name"]
    if ipo_name not in sent_alerts:
        msg = f"🟢 INVEST ALERT: {ipo_name}\nGMP: {row['gmp_pct']:.1f}%\nProb: {row['predicted_probability']:.0%}\nPrice: ₹{row['ipo_price']}"
        try:
            requests.post(f"https://ntfy.sh/{NTFY_TOPIC}", data=msg.encode('utf-8'))
            with open(ALERTS_FILE, "a") as f:
                f.write(ipo_name + "\n")
            new_alerts_sent += 1
            print(f"   -> Sent alert for {ipo_name}")
        except Exception as e:
            print(f"❌ Failed to send alert: {e}")

if new_alerts_sent == 0:
    print("   -> No new alerts to send today.")

# ======================
# SEND TO API (New Logic)
# ======================

print(f"\n📡 Sending {len(df)} predictions to API...")

# Prepare payload
import math

def _safe(v):
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return 0
    return v

payload = [
    {k: _safe(v) for k, v in row.items()}
    for row in df.to_dict(orient="records")
]

try:
    response = requests.post(API_URL, json=payload)

    if response.status_code == 200:
        print("✅ SUCCESS: Data successfully sent to the Website!")
        print("Server Response:", response.json())
    else:
        print(f"❌ FAILED: API Error {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"❌ CONNECTION ERROR: Could not reach API. {e}")
    print(f"   -> Check if '{API_URL}' is correct.")