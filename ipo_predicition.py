import sqlite3
import numpy as np
import pandas as pd
import joblib
import requests  # <--- NEW: Needed to talk to the API
import json
import os
from datetime import datetime

# ======================
# CONFIG
# ======================

# Raw data source (Created by the scraper in the previous step)
DB_PATH = "/app/data/ipo_ml_withsme.db"
MODEL_PATH = "ipo_xgb_model.pkl"

# 👇 REPLACE THIS WITH YOUR ACTUAL RAILWAY APP URL
# Example: "https://ipo-cloud-production.up.railway.app/upload_predictions"
API_URL = "https://ipo-cloud-production.up.railway.app/upload_predictions"

PROB_THRESHOLD = 0.70
GMP_MIN = 5.0
GMP_AUTO_INVEST = 15.0

# ======================
# LOAD MODEL
# ======================

if not os.path.exists(MODEL_PATH):
    print(f"❌ Error: Model file not found at {MODEL_PATH}")
    exit()

model = joblib.load(MODEL_PATH)
print("✅ Model loaded")

# ======================
# LOAD RAW DATA (From Local Scraper)
# ======================

conn = sqlite3.connect(DB_PATH)

# Only fetch rows that have NOT been predicted yet
query = """
SELECT *
FROM ipo_raw_data
WHERE is_predicted = 0
"""

try:
    df = pd.read_sql(query, conn)
except Exception as e:
    print(f"⚠️ Database error (Table might not exist yet): {e}")
    conn.close()
    exit()

conn.close()

print(f"✅ New (unprocessed) rows found: {len(df)}")

if df.empty:
    print("⚠️ No new IPO data to predict. Exiting.")
    exit()

# ======================
# PREPROCESSING & CLEANING
# ======================

# Remove listed IPOs
listed_patterns = [r"L@", r"\(\d+\.?\d*%\)", r"Listed"]
pattern = "|".join(listed_patterns)
df = df[~df["ipo_name"].str.contains(pattern, regex=True, na=False)]

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

# ======================
# MODEL PREDICTION
# ======================

df["predicted_probability"] = model.predict_proba(X)[:, 1]

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
# SEND TO API (New Logic)
# ======================

print(f"\n📡 Sending {len(df)} predictions to API...")

# Prepare payload
payload = df.to_dict(orient="records")

try:
    response = requests.post(API_URL, json=payload)
    
    if response.status_code == 200:
        print("✅ SUCCESS: Data successfully sent to the Website!")
        print("Server Response:", response.json())

        # Mark these rows as predicted so they won't be re-sent next run
        predicted_names = df["ipo_name"].tolist()
        placeholders = ",".join(["?"] * len(predicted_names))
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            f"UPDATE ipo_raw_data SET is_predicted = 1 WHERE ipo_name IN ({placeholders})",
            predicted_names
        )
        conn.commit()
        conn.close()
        print(f"✅ Marked {len(predicted_names)} rows as predicted in DB.")
    else:
        print(f"❌ FAILED: API Error {response.status_code}")
        print(response.text)
        print("⚠️ Rows NOT marked as predicted — will retry next run.")

except Exception as e:
    print(f"❌ CONNECTION ERROR: Could not reach API. {e}")
    print(f"   -> Check if '{API_URL}' is correct.")
    print("⚠️ Rows NOT marked as predicted — will retry next run.")

