import sqlite3
import json
from datetime import datetime

DB_PATH = "data/ipo_ml_withsme.db"

data = [
  {
    "IPO Name": "Leapfrog Engineering BSE SME",
    "GMP": "0",
    "Subscription": "0",
    "IPO Price": "23",
    "IPO Size": "84.08",
    "Lot Size": "6000",
    "Listing Date": "30-Apr",
    "Listing Price": None
  },
  {
    "IPO Name": "Amba Auto Sales & Services NSE SME",
    "GMP": "0",
    "Subscription": "0",
    "IPO Price": "135",
    "IPO Size": "61.86",
    "Lot Size": "1000",
    "Listing Date": "5-May",
    "Listing Price": None
  },
  {
    "IPO Name": "Adisoft Technologies NSE SME",
    "GMP": "10",
    "Subscription": "3.34",
    "IPO Price": "172",
    "IPO Size": "70.38",
    "Lot Size": "800",
    "Listing Date": "30-Apr",
    "Listing Price": None
  },
  {
    "IPO Name": "Citius Transnet InvIT IPO",
    "GMP": "3.5",
    "Subscription": "0.69",
    "IPO Price": "0",
    "IPO Size": "1105.00",
    "Lot Size": "0",
    "Listing Date": "29-Apr",
    "Listing Price": None
  },
  {
    "IPO Name": "Mehul Telecom BSE SME",
    "GMP": "3.75",
    "Subscription": "44.91",
    "IPO Price": "98",
    "IPO Size": "26.32",
    "Lot Size": "1200",
    "Listing Date": "24-Apr",
    "Listing Price": "108.00"
  },
  {
    "IPO Name": "Propshare Celestia IPO",
    "GMP": "0",
    "Subscription": "1.33",
    "IPO Price": "1050000",
    "IPO Size": "244.65",
    "Lot Size": "0",
    "Listing Date": "24-Apr",
    "Listing Price": "999900.01"
  },
  {
    "IPO Name": "Om Power Transmission IPO",
    "GMP": "2",
    "Subscription": "3.33",
    "IPO Price": "175",
    "IPO Size": "150.06",
    "Lot Size": "85",
    "Listing Date": "17-Apr",
    "Listing Price": "178.00"
  },
  {
    "IPO Name": "Safety Controls BSE SME",
    "GMP": "0",
    "Subscription": "1.28",
    "IPO Price": "80",
    "IPO Size": "45.57",
    "Lot Size": "1600",
    "Listing Date": "13-Apr",
    "Listing Price": "83.00"
  },
  {
    "IPO Name": "Emiac Technologies BSE SME",
    "GMP": "0",
    "Subscription": "3.22",
    "IPO Price": "98",
    "IPO Size": "30.11",
    "Lot Size": "1200",
    "Listing Date": "13-Apr",
    "Listing Price": "107.80"
  },
  {
    "IPO Name": "Vivid Electromech NSE SME",
    "GMP": "0",
    "Subscription": "1.06",
    "IPO Price": "555",
    "IPO Size": "123.94",
    "Lot Size": "240",
    "Listing Date": "7-Apr",
    "Listing Price": "565.00"
  }
]

def update_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Ensure table exists
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
        is_listed INTEGER DEFAULT 0
    )
    """)

    for item in data:
        name = item["IPO Name"]
        gmp = float(item["GMP"])
        sub = float(item["Subscription"])
        price = float(item["IPO Price"].replace(",", ""))
        size = float(item["IPO Size"].replace(",", ""))
        lot = int(item["Lot Size"].replace(",", "")) if item["Lot Size"] else 0
        l_date = item["Listing Date"]
        l_price = float(item["Listing Price"].replace(",", "")) if item["Listing Price"] else None
        is_listed = 1 if l_price else 0

        cur.execute("SELECT id FROM ipo_raw_data WHERE ipo_name = ?", (name,))
        exists = cur.fetchone()

        if exists:
            cur.execute("""
            UPDATE ipo_raw_data 
            SET gmp=?, subscription_x=?, ipo_price=?, ipo_size_cr=?, lot_size=?, listing_date=?, listing_price=?, is_listed=?, scraped_at=CURRENT_TIMESTAMP
            WHERE ipo_name=?
            """, (gmp, sub, price, size, lot, l_date, l_price, is_listed, name))
        else:
            cur.execute("""
            INSERT INTO ipo_raw_data (ipo_name, gmp, subscription_x, ipo_price, ipo_size_cr, lot_size, listing_date, listing_price, is_listed, scraped_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (name, gmp, sub, price, size, lot, l_date, l_price, is_listed))
            
    conn.commit()
    conn.close()
    print("✅ Database updated with latest data manually.")

if __name__ == "__main__":
    update_db()
