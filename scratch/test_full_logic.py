
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
        print("[*] Navigating to investorgain...")
        driver.get("https://www.investorgain.com/report/ipo-gmp-live/331/")
        
        print("[*] Waiting for table...")
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#report_table tbody tr")))
        
        rows = driver.find_elements(By.CSS_SELECTOR, "#report_table tbody tr")
        print(f"[*] Found {len(rows)} rows.")
        
        # Test parsing one row
        if rows:
            print(f"[*] First row text: {rows[0].text[:50]}...")
            
        print("[*] Success!")
        driver.quit()
    except Exception as e:
        print(f"[!] FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test()
