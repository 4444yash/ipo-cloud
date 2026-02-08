import sqlite3
import numpy as np
import pandas as pd
import joblib
from datetime import datetime

# ======================
# CONFIG
# ======================

DB_PATH = "ipo_ml_withsme.db"
MODEL_PATH = "ipo_xgb_model.pkl"

PROB_THRESHOLD = 0.70
GMP_MIN = 5.0
GMP_AUTO_INVEST = 15.0   # Auto-invest rule

# ======================
# LOAD MODEL
# ======================

model = joblib.load(MODEL_PATH)
print("✅ Model loaded")

# ======================
# LOAD TODAY'S DATA
# ======================

conn = sqlite3.connect(DB_PATH)

query = """
SELECT *
FROM ipo_raw_data
WHERE DATE(scraped_at) = DATE('now', 'localtime')
"""

df = pd.read_sql(query, conn)
conn.close()

print(f"✅ Rows scraped today: {len(df)}")

if df.empty:
    print("⚠️ No IPO data scraped today. Exiting safely.")
    exit()
 
# ======================
# REMOVE ALREADY LISTED IPOs
# ======================

listed_patterns = [
    r"L@",          # Listed price marker
    r"\(\d+\.?\d*%\)",  # Gain % shown
    r"Listed"
]

pattern = "|".join(listed_patterns)

before = len(df)

df = df[~df["ipo_name"].str.contains(pattern, regex=True, na=False)]

print(f"🧹 Removed {before - len(df)} already listed IPOs")

# ======================
# FORCE NUMERIC TYPES (CRITICAL)
# ======================

numeric_cols = [
    "gmp",
    "subscription_x",
    "ipo_price",
    "ipo_size_cr",
    "has_anchor"
]

for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=["gmp", "ipo_price", "ipo_size_cr"])

# ======================
# FEATURE ENGINEERING
# ======================

df = df[df["ipo_price"] > 0].copy()

df["gmp_pct"] = (df["gmp"] / df["ipo_price"]) * 100
df["log_subscription"] = np.log1p(df["subscription_x"])
df["log_ipo_size"] = np.log1p(df["ipo_size_cr"])

features = [
    "gmp_pct",
    "subscription_x",
    "log_subscription",
    "ipo_size_cr",
    "log_ipo_size",
    "ipo_price",
    "has_anchor"
]

X = df[features]

# ======================
# MODEL PREDICTION
# ======================

df["predicted_probability"] = model.predict_proba(X)[:, 1]

# ======================
# FINAL DECISION LOGIC (3-TIER SYSTEM)
# ======================

df["final_decision"] = 0  # default SKIP

# 🟢 Tier 1: High GMP → auto INVEST
df.loc[
    df["gmp_pct"] >= GMP_AUTO_INVEST,
    "final_decision"
] = 1

# 🟡 Tier 2: ML zone
df.loc[
    (df["gmp_pct"] >= GMP_MIN) &
    (df["gmp_pct"] < GMP_AUTO_INVEST) &
    (df["predicted_probability"] >= PROB_THRESHOLD),
    "final_decision"
] = 1

df["decision_label"] = df["final_decision"].map({
    1: "INVEST",
    0: "SKIP"
})

df["predicted_at"] = datetime.now()

# ======================
# SAVE RESULTS
# ======================

conn = sqlite3.connect(DB_PATH)

df[[
    "ipo_name",
    "predicted_probability",
    "gmp_pct",
    "final_decision",
    "decision_label",
    "predicted_at"
]].to_sql(
    "ipo_predictions",
    conn,
    if_exists="replace",
    index=False
)

conn.close()

print("✅ Predictions saved")

# ======================
# PRINT SUMMARY
# ======================

print("\n🔥 TODAY'S INVEST PICKS:")

invest_df = df[df["final_decision"] == 1]

if invest_df.empty:
    print("❌ No INVEST-worthy IPOs today")
else:
    print(
        invest_df
        .sort_values(["gmp_pct", "predicted_probability"], ascending=False)
        [["ipo_name", "gmp_pct", "predicted_probability","listing_date","subscription_x"]]
        .to_string(index=False)
    )
