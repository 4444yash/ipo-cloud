import sqlite3
import re
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


DB_PATH = "app/data/ipo_ml_withsme.db"
URL = "https://www.investorgain.com/report/ipo-gmp-live/331/"

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")

  driver = webdriver.Chrome(options=chrome_options) 
    return driver

def clean_number(text):
    if not text:
        return 0.0
    text = text.replace(",", "").strip()
    return float(text) if text.replace(".", "").isdigit() else 0.0


def scrape_daily_ipos():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    ipo_rows = []

    try:
        driver.get(URL)

        wait = WebDriverWait(driver, 20)

        # ✅ Wait until table rows are present
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#report_table tbody tr"))
        )

        rows = driver.find_elements(By.CSS_SELECTOR, "#report_table tbody tr")

        print(f"🔹 Rows detected: {len(rows)}")

        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")

            if len(cells) < 13:
                continue  # safety

            ipo_name = cells[0].text.strip()

            # GMP
            gmp_text = cells[1].text
            gmp_match = re.search(r"₹\s*(\d+)", gmp_text)
            gmp = float(gmp_match.group(1)) if gmp_match else 0.0

            # Subscription (Sub)
            subscription_x = clean_number(cells[3].text)

            # Price
            ipo_price = clean_number(cells[4].text)

            # IPO Size
            ipo_size_cr = clean_number(cells[5].text)

            # Lot
            lot_size = int(clean_number(cells[6].text))

            # Listing Date
            listing_date = cells[10].text.strip()

            # Anchor
            has_anchor = 1 if "✅" in cells[12].text else 0

            ipo_rows.append({
                "ipo_name": ipo_name,
                "gmp": gmp,
                "subscription_x": subscription_x,
                "ipo_price": ipo_price,
                "ipo_size_cr": ipo_size_cr,
                "lot_size": lot_size,
                "listing_date": listing_date,
                "has_anchor": has_anchor,
                "scraped_at": datetime.now()
            })

    finally:
        driver.quit()

    return ipo_rows


def upsert_ipos(ipo_rows):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    for ipo in ipo_rows:
        cur.execute(
            "SELECT id FROM ipo_raw_data WHERE ipo_name = ?",
            (ipo["ipo_name"],)
        )
        exists = cur.fetchone()

        if exists:
            cur.execute("""
            UPDATE ipo_raw_data
            SET
                gmp = ?,
                subscription_x = ?,
                lot_size = ?,
                ipo_price = ?,
                ipo_size_cr = ?,
                listing_date = ?,
                has_anchor = ?,
                scraped_at = CURRENT_TIMESTAMP
            WHERE ipo_name = ?
            """, (
                ipo["gmp"],
                ipo["subscription_x"],
                ipo["lot_size"],
                ipo["ipo_price"],
                ipo["ipo_size_cr"],
                ipo["listing_date"],
                ipo["has_anchor"],
                ipo["ipo_name"]
            ))
        else:
            cur.execute("""
            INSERT INTO ipo_raw_data (
                ipo_name, gmp, subscription_x,
                ipo_price, ipo_size_cr, lot_size,
                listing_date, has_anchor
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ipo["ipo_name"],
                ipo["gmp"],
                ipo["subscription_x"],
                ipo["ipo_price"],
                ipo["ipo_size_cr"],
                ipo["lot_size"],
                ipo["listing_date"],
                ipo["has_anchor"]
            ))

    conn.commit()
    conn.close()


if __name__ == "__main__":
    ipos = scrape_daily_ipos()
    upsert_ipos(ipos)
    print(f"✅ Daily scraper updated {len(ipos)} IPOs (Selenium)")
