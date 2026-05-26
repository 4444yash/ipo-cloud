import sqlite3
import pandas as pd
import numpy as np
import joblib
import os
import requests
import sys
from tensorflow.keras.models import load_model

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# ======================
# CONFIGURATION
# ======================
DB_PATH = "data/ipo_ml_withsme.db"
MODEL_PATH = "ipo_dl_model.keras"
SCALER_PATH = "scaler.pkl"

# 👇 Dynamic API URL resolution with fallback
BASE_API_URL = os.getenv("API_URL")
if BASE_API_URL:
    SCORECARD_API_URL = BASE_API_URL.replace("upload_predictions", "upload_scorecard")
else:
    try:
        from ipo_predicition import API_URL as base_url
        SCORECARD_API_URL = base_url.replace("upload_predictions", "upload_scorecard")
    except Exception:
        SCORECARD_API_URL = "http://localhost:8000/upload_scorecard"

PROB_THRESHOLD = 0.70
GMP_MIN = 5.0
GMP_AUTO_INVEST = 15.0

print("\n" + "="*40)
print("🔹 Historical Scorecard Generator")
print("="*40)

if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
    print("❌ Error: Model or scaler not found.")
    exit()

model = load_model(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)

conn = sqlite3.connect(DB_PATH)
query = """
SELECT ipo_name, gmp, subscription_x, ipo_price, ipo_size_cr, has_anchor, listing_price, listing_date
FROM ipo_raw_data
WHERE is_listed = 1 AND listing_price > 0
ORDER BY scraped_at DESC
LIMIT 200
"""
df = pd.read_sql(query, conn)
conn.close()

if df.empty:
    print("⚠️ No listed IPO data found for scorecard.")
    exit()

from datetime import datetime

def parse_ipo_date(d):
    try:
        # Expected: "2-Apr" or "30-Mar"
        clean_d = str(d).strip().split("\n")[0]
        curr_year = datetime.now().year
        # Check if year is already provided
        if "-" in clean_d and len(clean_d.split("-")) == 3:
            return pd.to_datetime(clean_d) 
        return pd.to_datetime(f"{clean_d}-{curr_year}", format="%d-%b-%Y")
    except:
        return pd.to_datetime("2000-01-01")

df["sort_date"] = df["listing_date"].apply(parse_ipo_date)
df = df.sort_values(by="sort_date", ascending=False)


# Preprocessing
df["gmp_pct"] = (df["gmp"] / df["ipo_price"]) * 100
df["log_subscription"] = np.log1p(df["subscription_x"])
df["log_ipo_size"] = np.log1p(df["ipo_size_cr"])

features = [
    "gmp_pct", "subscription_x", "log_subscription", 
    "ipo_size_cr", "log_ipo_size", "ipo_price", "has_anchor"
]

# Ensure no NaNs drop
df = df.dropna(subset=features)

X = df[features]
if X.empty:
    print("⚠️ After dropping NaNs, no data left.")
    exit()

X_scaled = scaler.transform(X)

# Predict
df["predicted_probability"] = model.predict(X_scaled).flatten()

# Rules
df["final_decision"] = 0 
df.loc[df["gmp_pct"] >= GMP_AUTO_INVEST, "final_decision"] = 1
df.loc[
    (df["gmp_pct"] >= GMP_MIN) & 
    (df["gmp_pct"] < GMP_AUTO_INVEST) & 
    (df["predicted_probability"] >= PROB_THRESHOLD), 
    "final_decision"
] = 1

df["decision_label"] = df["final_decision"].map({1: "INVEST", 0: "SKIP"})

# Actual Gain
df["actual_gain_pct"] = ((df["listing_price"] - df["ipo_price"]) / df["ipo_price"]) * 100
df["actual_outcome"] = df["actual_gain_pct"].apply(lambda x: "GAIN" if x > 0 else "LOSS")

# Scorecard Correctness
df["was_correct"] = (
    (df["decision_label"] == "INVEST") & (df["actual_outcome"] == "GAIN")
).astype(int)

# Precision: Of the IPOs we said INVEST, how many actually gained?
invest_df = df[df["decision_label"] == "INVEST"]
if len(invest_df) > 0:
    accuracy = (invest_df["actual_outcome"] == "GAIN").sum() / len(invest_df) * 100
else:
    accuracy = 0.0

print(f"📊 Evaluated {len(df)} past listed IPOs.")
print(f"📈 Model said INVEST on {len(invest_df)} IPOs, {int((invest_df['actual_outcome'] == 'GAIN').sum())} actually gained.")
print(f"✅ INVEST Accuracy (Precision): {accuracy:.2f}%")

# Limit to top 15 recent for the dashboard send over
df_recent = df.head(15).copy()

# Drop the non-serializable sort_date before sending
if "sort_date" in df_recent.columns:
    df_recent = df_recent.drop(columns=["sort_date"])

payload = []
for _, row in df_recent.iterrows():
    p = row.to_dict()
    # Add overall accuracy back to the row so frontend can read it
    p["model_accuracy"] = accuracy
    payload.append(p)

# Import math for safe jsonify
import math
def _safe(v):
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return 0
    return v

safe_payload = [{k: _safe(v) for k, v in r.items()} for r in payload]

# Send to API
print(f"📡 Sending Scorecard data to {SCORECARD_API_URL}...")
try:
    response = requests.post(SCORECARD_API_URL, json=safe_payload)
    if response.status_code == 200:
        print("✅ SUCCESS: Scorecard pushed to API.")
    else:
        print(f"❌ FAILED: API Error {response.status_code}")
except Exception as e:
    print(f"❌ CONNECTION ERROR: {e}")
