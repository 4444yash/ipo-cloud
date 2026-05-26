
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import sys

def test():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    print("[*] Installing driver...")
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("[*] Driver started. Navigating to investorgain...")
        driver.get("https://www.investorgain.com/report/ipo-gmp-live/331/")
        print(f"[*] Title: {driver.title}")
        print("[*] Success!")
        driver.quit()
    except Exception as e:
        print(f"[!] FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test()
