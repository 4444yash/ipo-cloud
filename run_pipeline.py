import os
import sys
import time

print("🚀 PIPELINE STARTED: Orchestrating your IPO workflow...")

# --- STEP 1: RUN THE SCRAPER ---
print("\n" + "="*40)
print("🔹 STEP 1: Starting Scraper (dail_scarper.py)")
print("="*40)

# We use os.system to run the command just like a terminal
exit_code_1 = os.system("python dail_scarper.py")

if exit_code_1 != 0:
    print("❌ CRITICAL ERROR: Scraper failed. Stopping pipeline.")
    sys.exit(1)
else:
    print("✅ Scraper finished successfully.")

# Tiny pause to ensure file system sync
time.sleep(2)

# --- STEP 2: RUN THE PREDICTOR ---
print("\n" + "="*40)
print("🔹 STEP 2: Starting Predictor (ipo_predicition.py)")
print("="*40)

exit_code_2 = os.system("python ipo_predicition.py")

if exit_code_2 != 0:
    print("❌ CRITICAL ERROR: Prediction script failed.")
    sys.exit(1)
else:
    print("✅ Predictor finished successfully.")

print("\n✨ PIPELINE COMPLETE: All data scraped and sent to API.")
