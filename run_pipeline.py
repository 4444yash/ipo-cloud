import os
import sys
import time

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def run_all():
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

    # --- STEP 3: RUN THE HISTORICAL SCORER ---
    print("\n" + "="*40)
    print("🔹 STEP 3: Starting Scorecard Generator (historical_scorer.py)")
    print("="*40)

    exit_code_3 = os.system("python historical_scorer.py")

    if exit_code_3 != 0:
        print("⚠️ WARNING: Historical Scorecard script failed, but continuing.")
    else:
        print("✅ Scorecard Generator finished successfully.")

    # --- STEP 4: RUN THE MARKET METER ---
    print("\n" + "="*40)
    print("🔹 STEP 4: Starting Market Condition Meter (market_meter.py)")
    print("="*40)

    exit_code_4 = os.system("python market_meter.py")

    if exit_code_4 != 0:
        print("⚠️ WARNING: Market Meter script failed, but continuing.")
    else:
        print("✅ Market Meter finished successfully.")

    print("\n✨ PIPELINE COMPLETE: All data scraped and sent to API.")

if __name__ == "__main__":
    if "--daemon" in sys.argv:
        print("🕒 Running in Daemon Mode. Pipeline is scheduled to run daily at 15:00 (3 PM).")
        print("   To change the time, edit 'run_pipeline.py'.")
        try:
            import schedule
        except ImportError:
            print("❌ Please run: pip install schedule")
            sys.exit(1)
            
        schedule.every().day.at("15:00").do(run_all)
        
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        run_all()
