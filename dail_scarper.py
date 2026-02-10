import sqlite3
import re
import os
import shutil
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ===========================
# CONFIGURATION
# ===========================

# CRITICAL: Must be the absolute path to the shared volume
DB_PATH = "/app/data/ipo_ml_withsme.db"
URL = "https://www.investorgain.com/report/ipo-gmp-live/331/"

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # 1. FIND CHROMIUM BINARY AUTOMATICALLY
    chromium_path = shutil.which("chromium")
    if chromium_path:
        chrome_options.binary_location = chromium_path
    
    # 2. FIND CHROMEDRIVER AUTOMATICALLY
    driver_path = shutil.which("chromedriver")
    
    if driver_path:
        print(f"✅ Found system driver at: {driver_path}")
        service = Service(driver_path)
    else:
        print("⚠️ System driver not found. Trying fallback...")
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())

    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver
def clean_number(text):
    if not text:
        return 0.0
    text = text.replace(",", "").strip()
    # Handle cases like "15.5%" or "Rs. 100"
    text = re.sub(r"[^\d.]", "", text)
    try:
        return float(text)
    except ValueError:
        return 0.0

def scrape_daily_ipos():
    driver = get_driver()
    ipo_rows = []

    try:
        print(f"🚀 Connecting to {URL}...")
        driver.get(URL)

        wait = WebDriverWait(driver, 20)
        # Wait for the table body to load
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#report_table tbody tr")))

        rows = driver.find_elements(By.CSS_SELECTOR, "#report_table tbody tr")
        print(f"🔹 Rows detected: {len(rows)}")

        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")

            if len(cells) < 13:
                continue

            ipo_name = cells[0].text.strip()
            
            # --- Extract GMP ---
            gmp_text = cells[1].text
            gmp_match = re.search(r"₹\s*(\d+)", gmp_text)
            gmp = float(gmp_match.group(1)) if gmp_match else 0.0

            # --- Extract Other Fields ---
            subscription_x = clean_number(cells[3].text)
            ipo_price = clean_number(cells[4].text)
            ipo_size_cr = clean_number(cells[5].text)
            lot_size = clean_number(cells[6].text)
            
            # Listing Date
            listing_date = cells[10].text.strip()
            
            # Anchor Status (Check for tick mark)
            has_anchor = 1 if "✅" in cells[12].text else 0

            # Only add valid rows
            if ipo_name:
                ipo_rows.append({
                    "ipo_name": ipo_name,
                    "gmp": gmp,
                    "subscription_x": subscription_x,
                    "ipo_price": ipo_price,
                    "ipo_size_cr": ipo_size_cr,
                    "lot_size": int(lot_size),
                    "listing_date": listing_date,
                    "has_anchor": has_anchor
                })

    except Exception as e:
        print(f"❌ Error during scraping: {e}")
    finally:
        driver.quit()

    return ipo_rows

def upsert_ipos(ipo_rows):
    if not ipo_rows:
        print("⚠️ No data to update.")
        return

    # Ensure directory exists (just in case)
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Create table if it doesn't exist (Safety check for fresh volume)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ipo_raw_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ipo_name TEXT UNIQUE,
        gmp REAL,
        subscription_x REAL,
        ipo_price REAL,
        ipo_size_cr REAL,
        lot_size INTEGER,
        listing_date TEXT,
        has_anchor INTEGER,
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    updated_count = 0
    new_count = 0

    for ipo in ipo_rows:
        # Check if IPO exists
        cur.execute("SELECT id FROM ipo_raw_data WHERE ipo_name = ?", (ipo["ipo_name"],))
        exists = cur.fetchone()

        if exists:
            cur.execute("""
            UPDATE ipo_raw_data
            SET gmp=?, subscription_x=?, lot_size=?, ipo_price=?, 
                ipo_size_cr=?, listing_date=?, has_anchor=?, scraped_at=CURRENT_TIMESTAMP
            WHERE ipo_name=?
            """, (
                ipo["gmp"], ipo["subscription_x"], ipo["lot_size"], ipo["ipo_price"],
                ipo["ipo_size_cr"], ipo["listing_date"], ipo["has_anchor"], ipo["ipo_name"]
            ))
            updated_count += 1
        else:
            cur.execute("""
            INSERT INTO ipo_raw_data (
                ipo_name, gmp, subscription_x, ipo_price, ipo_size_cr, 
                lot_size, listing_date, has_anchor, scraped_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                ipo["ipo_name"], ipo["gmp"], ipo["subscription_x"], ipo["ipo_price"],
                ipo["ipo_size_cr"], ipo["lot_size"], ipo["listing_date"], ipo["has_anchor"]
            ))
            new_count += 1

    conn.commit()
    conn.close()
    print(f"✅ Database Updated: {new_count} New | {updated_count} Updated")

if __name__ == "__main__":
    print(f"📅 Starting Daily Scrape at {datetime.now()}")
    ipos = scrape_daily_ipos()
    upsert_ipos(ipos)
    print("✨ Scrape & Update Complete.")
