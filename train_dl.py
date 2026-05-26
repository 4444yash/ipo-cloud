import sqlite3
import pandas as pd
import numpy as np
import joblib

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, roc_auc_score,
    confusion_matrix, precision_score, recall_score
)

import matplotlib.pyplot as plt

# =====================================================
# 1. LOAD DATA
# =====================================================

print("\n🔹 Connecting to SQLite database...")

DB_PATH = r"C:\Users\ASAD\Desktop\NOGPTML\databases\ipo_ml.db"

conn = sqlite3.connect(DB_PATH)
df = pd.read_sql("SELECT * FROM ipo_raw_data", conn)
conn.close()

print(f"✅ Rows loaded: {len(df)}")

if df.empty:
    raise SystemExit("❌ No data found")


# =====================================================
# 2. FEATURE ENGINEERING
# =====================================================

print("\n🔹 Feature engineering...")

df = df[(df["ipo_price"] > 0) & (df["listing_price"] > 0)]

df["gmp_pct"] = (df["gmp"] / df["ipo_price"]) * 100
df["listing_gain_pct"] = (
    (df["listing_price"] - df["ipo_price"]) / df["ipo_price"]
) * 100

df["target"] = (df["listing_gain_pct"] > 0).astype(int)

df["log_ipo_size"] = np.log1p(df["ipo_size_cr"])
df["log_subscription"] = np.log1p(df["subscription_x"])

print(f"✅ Rows after cleaning: {len(df)}")


# =====================================================
# 3. REMOVE RULE-BASED AUTO-BUY IPOs (GMP ≥ 15%)
# =====================================================

GMP_RULE_THRESHOLD =1000.0

before = len(df)
df = df[df["gmp_pct"] < GMP_RULE_THRESHOLD]
after = len(df)

print(
    f"🔹 Removed GMP ≥ {GMP_RULE_THRESHOLD}% IPOs: "
    f"{before - after} | Remaining: {after}"
)


# =====================================================
# 4. FEATURE SET
# =====================================================

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
y = df["target"]


# =====================================================
# 5. TRAIN / TEST SPLIT
# =====================================================

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, shuffle=False
)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

joblib.dump(scaler, "scaler.pkl")
print("✅ Scaler saved as scaler.pkl")

print(f"📊 Train size: {len(X_train)} | Test size: {len(X_test)}")


# =====================================================
# 6. MODEL TRAINING
# =====================================================

tf.random.set_seed(42)

model = Sequential([
    Dense(32, activation='relu', input_shape=(X_train_scaled.shape[1],)),
    Dropout(0.2),
    Dense(16, activation='relu'),
    Dropout(0.2),
    Dense(1, activation='sigmoid')
])

model.compile(
    optimizer='adam',
    loss='binary_crossentropy',
    metrics=['accuracy']
)

# Use early stopping to avoid overfitting
early_stop = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)

history = model.fit(
    X_train_scaled, y_train,
    validation_data=(X_test_scaled, y_test),
    epochs=100,
    batch_size=32,
    callbacks=[early_stop],
    verbose=1
)
print("✅ Model training completed")


# =====================================================
# 7. BASELINE EVALUATION (GMP = 10%, PROB = 0.5)
# =====================================================

BASE_GMP = 10.0
BASE_PROB = 0.50

y_prob_raw = model.predict(X_test_scaled)
y_prob = y_prob_raw.flatten()

y_pred_base = (
    (y_prob >= BASE_PROB) &
    (X_test["gmp_pct"] >= BASE_GMP)
).astype(int)

print("\n📌 BASELINE CONFIG")
print(f"   GMP ≥ {BASE_GMP}% | Probability ≥ {BASE_PROB}")

print(f"✅ Accuracy : {accuracy_score(y_test, y_pred_base):.4f}")
print(f"✅ Precision: {precision_score(y_test, y_pred_base, zero_division=0):.4f}")
print(f"✅ Recall   : {recall_score(y_test, y_pred_base, zero_division=0):.4f}")
print(f"✅ AUC      : {roc_auc_score(y_test, y_prob):.4f}")

print("✅ Confusion Matrix:")
print(confusion_matrix(y_test, y_pred_base))


# =====================================================
# 8. SENSITIVITY ANALYSIS (WHAT YOU ASKED FOR)
# =====================================================

print("\n🧪 GMP × Probability Sensitivity Analysis")

gmp_values = [0, 5, 10]
prob_values = [0.3, 0.4, 0.5, 0.6]

results = []

for gmp_cut in gmp_values:
    mask = X_test["gmp_pct"] >= gmp_cut
    if mask.sum() == 0:
        continue

    y_t = y_test[mask]
    y_p = y_prob[mask]

    for prob_cut in prob_values:
        y_pred = (y_p >= prob_cut).astype(int)

        results.append({
            "gmp_min": gmp_cut,
            "prob_threshold": prob_cut,
            "eligible_rows": len(y_t),
            "accuracy": accuracy_score(y_t, y_pred),
            "precision": precision_score(y_t, y_pred, zero_division=0),
            "recall": recall_score(y_t, y_pred, zero_division=0),
            "auc": roc_auc_score(y_t, y_p) if y_t.nunique() > 1 else np.nan,
            "positives_predicted": y_pred.sum()
        })

results_df = pd.DataFrame(results)

print("\n📊 Sensitivity Results (sorted by Recall ↓ Precision):")
print(
    results_df
    .sort_values(["recall", "precision"], ascending=False)
    .to_string(index=False)
)


# =====================================================
# 9. FALSE NEGATIVE ANALYSIS (BASELINE ONLY)
# =====================================================

print("\n❌ False Negatives (Missed Profitable IPOs)")

fn_mask = (y_test == 1) & (y_pred_base == 0)

fn_df = df.loc[X_test.index][fn_mask].copy()
fn_df["predicted_probability"] = y_prob[fn_mask]

cols = [
    "ipo_name",
    "gmp_pct",
    "subscription_x",
    "has_anchor",
    "predicted_probability",
    "listing_gain_pct"
]

if fn_df.empty:
    print("🎉 No false negatives!")
else:
    print(
        fn_df[cols]
        .sort_values("predicted_probability", ascending=False)
        .to_string(index=False)
    )


# =====================================================
# 10. TRAINING HISTORY PLOT
# =====================================================

import os
if not os.path.exists(r"C:\Users\ASAD\Desktop\nogptml\ml_model"):
    os.makedirs(r"C:\Users\ASAD\Desktop\nogptml\ml_model")

plt.figure(figsize=(10, 4))
plt.subplot(1, 2, 1)
plt.plot(history.history['loss'], label='Train Loss')
plt.plot(history.history['val_loss'], label='Val Loss')
plt.title('Model Loss')
plt.legend()

plt.subplot(1, 2, 2)
plt.plot(history.history['accuracy'], label='Train Acc')
plt.plot(history.history['val_accuracy'], label='Val Acc')
plt.title('Model Accuracy')
plt.legend()

plt.tight_layout()
plt.savefig(r"C:\Users\ASAD\Desktop\nogptml\ml_model\ipo_dl_history.png")
plt.close()

model.save("ipo_dl_model.keras")
print("✅ Model saved as ipo_dl_model.keras")
print("\n🎯 SCRIPT COMPLETED SUCCESSFULLY")
