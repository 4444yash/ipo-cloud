import sqlite3
import re
import os
import shutil
from datetime import datetime
import sys
import time

# Fix for Windows Unicode printing
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ===========================
# CONFIGURATION
# ===========================

DB_PATH = "data/ipo_ml_withsme.db"
URL = "https://www.investorgain.com/report/ipo-gmp-live/331/"

def get_driver():
    print("[*] Initializing Chrome Driver (Robust Mode)...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")

    # 👇 Support environment variables for headless cloud environments
    chrome_bin = os.getenv("CHROME_BIN")
    if chrome_bin:
        chrome_options.binary_location = chrome_bin
        print(f"[*] Using Chrome Binary: {chrome_bin}")

    chromedriver_path = os.getenv("CHROMEDRIVER_PATH")
    if chromedriver_path:
        print(f"[*] Using ChromeDriver: {chromedriver_path}")
        service = Service(executable_path=chromedriver_path)
        try:
            return webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            print(f"[!] Direct ChromeDriver initialization failed, falling back to manager. Error: {e}")

    try:
        from webdriver_manager.chrome import ChromeDriverManager
        driver_path = ChromeDriverManager().install()
        service = Service(executable_path=driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        print(f"[!] Driver Initialization Failed: {e}")
        raise

def clean_number(text):
    if not text:
        return 0.0
    text = str(text).split("\n")[0].split("(")[0].strip()
    text = text.replace(",", "").replace("₹", "").replace("Rs.", "").strip()
    match = re.search(r"(\d+\.?\d*)", text)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return 0.0
    return 0.0

def scrape_daily_ipos():
    driver = None
    ipo_rows = []

    try:
        driver = get_driver()
        print(f"[*] Connecting to {URL}...")
        driver.get(URL)

        wait = WebDriverWait(driver, 30)
        # Use a more generic selector for the table rows
        print("[*] Waiting for table content...")
        wait.until(EC.presence_of_element_located((By.ID, "reportTable")))
        
        # Give it a tiny bit of extra time for rows to render
        time.sleep(3)

        # Get all rows from the table
        rows = driver.find_elements(By.CSS_SELECTOR, "#reportTable tr")
        print(f"[*] Total rows found (including headers): {len(rows)}")

        # Retry once if no data rows found (page may not have fully rendered)
        data_rows = [r for r in rows if len(r.find_elements(By.TAG_NAME, 'td')) >= 10]
        if len(data_rows) == 0:
            print("[*] No data rows found, retrying with longer wait...")
            time.sleep(5)
            rows = driver.find_elements(By.CSS_SELECTOR, "#reportTable tr")
            print(f"[*] Retry: Total rows found: {len(rows)}")

        for i, row in enumerate(rows):
            cells = row.find_elements(By.TAG_NAME, "td")
            
            # Skip header rows or empty rows
            if len(cells) < 10:
                continue

            ipo_name_full = cells[0].text.strip()
            if not ipo_name_full or "IPO Name" in ipo_name_full:
                continue
                
            try:
                name_element = cells[0].find_element(By.TAG_NAME, "a")
                clean_name = name_element.text.strip()
            except:
                clean_name = ipo_name_full.split("\n")[0].strip()
            
            if not clean_name:
                continue

            # GMP Parsing
            gmp_text = cells[1].text
            # Support negative GMP (e.g. -₹10, ₹ -10, or ₹-10)
            gmp_match = re.search(r"(-?)\s*₹?\s*(-?\d+)", gmp_text)
            if gmp_match:
                is_neg = '-' in gmp_match.group(1) or '-' in gmp_match.group(2)
                val = abs(int(gmp_match.group(2)))
                gmp = float(-val if is_neg else val)
            else:
                gmp = 0.0


            # Subscription, Price, Size, Lot
            subscription_x = clean_number(cells[3].text)
            ipo_price = clean_number(cells[4].text)
            ipo_size_cr = clean_number(cells[5].text)
            lot_size = clean_number(cells[6].text)

            # Listing Price and Status
            listing_price = None
            is_listed = 0
            lp_match = re.search(r"L@(\d+\.?\d*)", ipo_name_full)
            if lp_match:
                listing_price = float(lp_match.group(1))
                is_listed = 1
            
            if any(p in ipo_name_full for p in ["Listed ", "listed "]):
                is_listed = 1

            # Listing Date
            listing_date = ""
            # Try columns 10, then 7, then 8
            for idx in [10, 7, 8]:
                if len(cells) > idx and cells[idx].text.strip():
                    listing_date = cells[idx].text.split("\n")[0].strip()
                    if listing_date: break
            
            # 👇 Parse Open & Close Dates
            open_date = cells[7].text.split("\n")[0].strip() if len(cells) > 7 else ""
            close_date = cells[8].text.split("\n")[0].strip() if len(cells) > 8 else ""

            # 👇 Determine IPO Type (SME vs Mainboard)
            is_sme = "SME" in clean_name.upper()

            # Check the href URL of the link (Foolproof fallback)
            try:
                name_element = cells[0].find_element(By.TAG_NAME, "a")
                href = name_element.get_attribute("href")
                if href and "/sme-ipo/" in href.lower():
                    is_sme = True
            except Exception:
                pass

            # Apply the Financial Rule (if price and lot size are known)
            if not is_sme and lot_size > 0 and ipo_price > 0:
                min_investment = lot_size * ipo_price
                if min_investment >= 80000:
                    is_sme = True

            # Apply high lot size threshold fallback
            if not is_sme and lot_size >= 500:
                is_sme = True

            ipo_type = "SME" if is_sme else "Mainboard"

            # Anchor Status
            has_anchor = 0
            if len(cells) > 12:
                cell_text = cells[12].text
                cell_html = cells[12].get_attribute('innerHTML')
                if "✅" in cell_text or "✅" in cell_html:
                    has_anchor = 1

            ipo_rows.append({
                "ipo_name": clean_name,
                "gmp": gmp,
                "subscription_x": subscription_x,
                "ipo_price": ipo_price,
                "ipo_size_cr": ipo_size_cr,
                "lot_size": int(lot_size),
                "listing_date": listing_date,
                "has_anchor": has_anchor,
                "listing_price": listing_price,
                "is_listed": is_listed,
                "open_date": open_date,
                "close_date": close_date,
                "ipo_type": ipo_type
            })

        listed_count = sum(1 for ipo in ipo_rows if ipo["is_listed"] == 1)
        unlisted_count = len(ipo_rows) - listed_count
        print(f"[*] Successfully parsed {len(ipo_rows)} IPOs ({listed_count} listed, {unlisted_count} unlisted).")

    except Exception as e:
        print(f"[ERR] Error during scraping: {e}")
        import traceback
        traceback.print_exc()
        if driver:
            try:
                driver.quit()
            except:
                pass
        sys.exit(1)
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

    return ipo_rows

def upsert_ipos(ipo_rows):
    if not ipo_rows:
        print("[WARN] No data to update.")
        return

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

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
        has_anchor INTEGER DEFAULT 0,
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        listing_price REAL,
        is_listed INTEGER DEFAULT 0,
        open_date TEXT,
        close_date TEXT,
        ipo_type TEXT
    )
    """)
    
    # 👇 Dynamic Column Migration (So existing DB upgrades instantly!)
    cols = [row[1] for row in cur.execute("PRAGMA table_info(ipo_raw_data)").fetchall()]
    for col_name in ["listing_price", "is_listed", "has_anchor", "open_date", "close_date", "ipo_type"]:
        if col_name not in cols:
            col_type = "INTEGER DEFAULT 0" if col_name in ["is_listed", "has_anchor"] else "TEXT"
            col_type = "REAL" if col_name == "listing_price" else col_type
            cur.execute(f"ALTER TABLE ipo_raw_data ADD COLUMN {col_name} {col_type}")

    for ipo in ipo_rows:
        cur.execute("SELECT gmp, listing_price, is_listed FROM ipo_raw_data WHERE ipo_name = ?", (ipo["ipo_name"],))
        old_data = cur.fetchone()

        if old_data:
            old_gmp, old_listing_price, old_is_listed = old_data
            final_gmp = ipo["gmp"] if (ipo["gmp"] != 0 or not old_gmp) else old_gmp
            final_lp = ipo["listing_price"] if (ipo["listing_price"] or not old_listing_price) else old_listing_price
            final_is_listed = max(ipo["is_listed"], old_is_listed)

            cur.execute("""
            UPDATE ipo_raw_data
            SET gmp=?, subscription_x=?, lot_size=?, ipo_price=?, 
                ipo_size_cr=?, listing_date=?, has_anchor=?, listing_price=?, is_listed=?, scraped_at=CURRENT_TIMESTAMP,
                open_date=?, close_date=?, ipo_type=?
            WHERE ipo_name=?
            """, (
                final_gmp, ipo["subscription_x"], ipo["lot_size"], ipo["ipo_price"],
                ipo["ipo_size_cr"], ipo["listing_date"], ipo["has_anchor"], final_lp, final_is_listed,
                ipo["open_date"], ipo["close_date"], ipo["ipo_type"], ipo["ipo_name"]
            ))
        else:
            cur.execute("""
            INSERT INTO ipo_raw_data (ipo_name, gmp, subscription_x, ipo_price, ipo_size_cr, lot_size, listing_date, listing_price, is_listed, has_anchor, open_date, close_date, ipo_type, scraped_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (ipo["ipo_name"], ipo["gmp"], ipo["subscription_x"], ipo["ipo_price"], ipo["ipo_size_cr"], ipo["lot_size"], ipo["ipo_date"] if "ipo_date" in ipo else ipo["listing_date"], ipo["listing_price"], ipo["is_listed"], ipo["has_anchor"], ipo["open_date"], ipo["close_date"], ipo["ipo_type"]))

    conn.commit()
    conn.close()
    print(f"[OK] Database Updated.")

def update_listed_status_from_tracker(driver):
    tracker_url = "https://www.investorgain.com/report/ipo-gmp-performance-tracker/377/"
    print(f"\n[*] Connecting to performance tracker: {tracker_url}...")
    try:
        driver.get(tracker_url)
        wait = WebDriverWait(driver, 30)
        wait.until(EC.presence_of_element_located((By.ID, "reportTable")))
        time.sleep(5)  # Wait longer for JS-rendered table content
        rows = driver.find_elements(By.CSS_SELECTOR, "#reportTable tr")
        print(f"[*] Found {len(rows)} rows in performance tracker.")
        
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        updated_count = 0
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) < 10:
                continue
            
            raw_name = cells[0].text.strip()
            if not raw_name:
                continue
            
            # Clean name — strip common suffixes to match our DB
            clean_name = raw_name
            for suffix in [" SME", " IPO", " InvIT"]:
                if clean_name.endswith(suffix):
                    clean_name = clean_name[:-len(suffix)].strip()
                    break
            
            # Parse Listing Price
            lp_text = cells[8].text.strip()
            lp_match = re.search(r"₹\s*(\d+\.?\d*)", lp_text)
            if lp_match:
                listing_price = float(lp_match.group(1))
                
                # Update database if the IPO is tracked in raw data
                cur.execute("SELECT is_listed, listing_price FROM ipo_raw_data WHERE ipo_name = ?", (clean_name,))
                db_row = cur.fetchone()
                if db_row:
                    db_is_listed, db_lp = db_row
                    if not db_is_listed or not db_lp:
                        cur.execute("""
                        UPDATE ipo_raw_data
                        SET is_listed = 1, listing_price = ?, listing_date = ?
                        WHERE ipo_name = ?
                        """, (listing_price, cells[2].text.strip().split("\n")[0].strip(), clean_name))
                        updated_count += 1
                        print(f"    -> Updated listed status for {clean_name}: Price = {listing_price}")
        
        conn.commit()
        conn.close()
        print(f"[*] Updated {updated_count} IPOs from performance tracker.")
    except Exception as e:
        print(f"[ERR] Error scraping performance tracker: {e}")

def auto_mark_listed_by_date():
    """Safety net: auto-mark IPOs as listed if their listing_date has passed by 1+ days.
    This handles cases where the scraper fails to detect L@ patterns or when
    the page no longer shows the IPO."""
    print("\n[*] Running date-based auto-listing check...")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT ipo_name, listing_date, close_date FROM ipo_raw_data
        WHERE is_listed = 0 AND (listing_date IS NOT NULL AND listing_date != '')
    """)
    candidates = cur.fetchall()
    
    now = datetime.now()
    updated_count = 0
    
    for ipo_name, listing_date_str, close_date_str in candidates:
        try:
            # Parse listing_date (format: "18-Jun" or "2-Jul")
            clean_date = str(listing_date_str).strip().split("\n")[0].strip()
            if not clean_date:
                continue
            parsed = datetime.strptime(clean_date, "%d-%b")
            listing_dt = parsed.replace(year=now.year)
            
            # Handle year boundary (e.g., Dec listing checked in Jan)
            if now.month in [1, 2] and parsed.month in [11, 12]:
                listing_dt = listing_dt.replace(year=now.year - 1)
            elif now.month in [11, 12] and parsed.month in [1, 2]:
                listing_dt = listing_dt.replace(year=now.year + 1)
            
            # If listing date was 1+ days ago, mark as listed
            if (now - listing_dt).days >= 1:
                cur.execute("""
                    UPDATE ipo_raw_data SET is_listed = 1
                    WHERE ipo_name = ? AND is_listed = 0
                """, (ipo_name,))
                updated_count += 1
                print(f"    -> Auto-marked '{ipo_name}' as listed (listing_date={clean_date}, {(now - listing_dt).days} days ago)")
        except Exception as e:
            # Also try with close_date as fallback (listing is typically 3 days after close)
            try:
                if close_date_str:
                    clean_close = str(close_date_str).strip().split("\n")[0].strip()
                    parsed_close = datetime.strptime(clean_close, "%d-%b")
                    close_dt = parsed_close.replace(year=now.year)
                    if now.month in [1, 2] and parsed_close.month in [11, 12]:
                        close_dt = close_dt.replace(year=now.year - 1)
                    # If close date was 5+ days ago, likely already listed
                    if (now - close_dt).days >= 5:
                        cur.execute("""
                            UPDATE ipo_raw_data SET is_listed = 1
                            WHERE ipo_name = ? AND is_listed = 0
                        """, (ipo_name,))
                        updated_count += 1
                        print(f"    -> Auto-marked '{ipo_name}' as listed (close_date={clean_close}, {(now - close_dt).days} days past close)")
            except:
                pass
    
    conn.commit()
    conn.close()
    print(f"[*] Auto-listed {updated_count} IPOs by date.")

if __name__ == "__main__":
    try:
        # 1. Scrape live IPOs
        ipos = scrape_daily_ipos()
        upsert_ipos(ipos)
        
        # 2. Scrape performance tracker to update listing prices of past IPOs
        print("\n[*] Starting Performance Tracker Scraper...")
        driver = get_driver()
        try:
            update_listed_status_from_tracker(driver)
        finally:
            driver.quit()
        
        # 3. Safety net: auto-mark IPOs whose listing date has passed
        auto_mark_listed_by_date()
            
        print("[*] Scrape Complete.")
    except Exception as e:
        print(f"[ERR] Scraper Failed: {e}")
        sys.exit(1)