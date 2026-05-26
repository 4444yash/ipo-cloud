import requests

url = "https://www.investorgain.com/report/ipo-gmp-live/331/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

try:
    response = requests.get(url, headers=headers, timeout=15)
    print(f"Status Code: {response.status_code}")
    if "report_table" in response.text:
        print("✅ SUCCESS: Found the data table in the HTML!")
    else:
        print("❌ FAILED: Table not found. JavaScript might be required.")
except Exception as e:
    print(f"❌ ERROR: {e}")
