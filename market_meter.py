import yfinance as yf
import requests
import datetime
import math
import sys
import os

# Force UTF-8 output so emojis don't crash the console on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# 👇 Dynamic API URL resolution with fallback
BASE_API_URL = os.getenv("API_URL")
if BASE_API_URL:
    API_URL = BASE_API_URL.replace("upload_predictions", "upload_market_meter")
else:
    try:
        from ipo_predicition import API_URL as base_url
        API_URL = base_url.replace("upload_predictions", "upload_market_meter")
    except Exception:
        API_URL = "http://localhost:8000/upload_market_meter"

print("\n" + "="*40)
print("🔹 Market Condition & Fear/Greed Meter")
print("="*40)

def safe_number(x):
    if math.isnan(float(x)) or math.isinf(float(x)):
        return 0.0
    return float(x)

try:
    # 1. Fetch Nifty 50 Data
    nifty = yf.Ticker("^NSEI")
    
    # Use fast_info for more immediate current day stats
    try:
        current_nifty = nifty.fast_info['lastPrice']
        prev_close = nifty.fast_info['previousClose']
        nifty_pct_change = ((current_nifty - prev_close) / prev_close) * 100
    except:
        # Fallback to history if fast_info fails
        n_hist = nifty.history(period="2d")
        if len(n_hist) >= 2:
            current_nifty = n_hist['Close'].iloc[-1]
            prev_close = n_hist['Close'].iloc[-2]
            nifty_pct_change = ((current_nifty - prev_close) / prev_close) * 100
        else:
            current_nifty = 22000.0
            nifty_pct_change = 0.0

    # 2. Fetch India VIX Data
    vix = yf.Ticker("^INDIAVIX")
    v_hist = vix.history(period="1d")
    if len(v_hist) >= 1:
        current_vix = v_hist['Close'][-1]
    else:
        current_vix = 14.0 # safe fallback
        
    current_nifty = safe_number(current_nifty)
    nifty_pct_change = safe_number(nifty_pct_change)
    current_vix = safe_number(current_vix)

    print(f"📉 NIFTY 50: {current_nifty:.2f} ({nifty_pct_change:+.2f}%)")
    print(f"📊 INDIA VIX: {current_vix:.2f}")

    # 3. Calculate 0-100 Fear & Greed Score
    # Baseline: VIX of 10 gives a high score (Greed). VIX of 25 gives a low score (Fear).
    base_score = 100 - (current_vix * 3.5)
    
    # Add momentum from daily Nifty change (+1% adds 20 points, -1% removes 20 points)
    momentum_boost = nifty_pct_change * 20
    
    final_score = base_score + momentum_boost
    
    # Clamp score between 0 and 100
    final_score = max(0, min(100, final_score))
    
    # 4. Determine Text Label
    if final_score <= 25:
        mood = "Extreme Fear"
        color = "#ef4444"
    elif final_score <= 45:
        mood = "Fear"
        color = "#f97316"
    elif final_score <= 55:
        mood = "Neutral"
        color = "#eab308"
    elif final_score <= 75:
        mood = "Greed"
        color = "#84cc16"
    else:
        mood = "Extreme Greed"
        color = "#22c55e"

    print(f"🌡️ MARKET SCORE: {final_score:.0f}/100 -> {mood}")

    payload = {
        "score": round(final_score),
        "mood_label": mood,
        "color": color,
        "nifty_price": round(current_nifty, 2),
        "nifty_change_pct": round(nifty_pct_change, 2),
        "vix_value": round(current_vix, 2),
        "updated_at": datetime.datetime.now().isoformat()
    }

    # 5. Send to Server
    print(f"📡 Pushing to {API_URL}...")
    resp = requests.post(API_URL, json=[payload])
    
    if resp.status_code == 200:
        print("✅ SUCCESS: Market Meter updated.")
    else:
        print(f"❌ API ERROR: {resp.status_code} - {resp.text}")

except Exception as e:
    print(f"❌ FAULT: Failed to calculate Market Meter: {e}")
