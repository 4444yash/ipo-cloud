
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

def test():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    print("[*] Navigating...")
    driver.get("https://www.investorgain.com/report/ipo-gmp-live/331/")
    time.sleep(5)
    
    print(f"[*] Title: {driver.title}")
    print(f"[*] URL: {driver.current_url}")
    
    with open("page_source.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    
    print("[*] Page source saved to page_source.html")
    driver.quit()

if __name__ == "__main__":
    test()
