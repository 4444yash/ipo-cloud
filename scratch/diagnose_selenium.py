import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def test_config(name, options_list):
    print(f"Testing Config: {name}")
    chrome_options = Options()
    for opt in options_list:
        chrome_options.add_argument(opt)
    
    # Common robust options
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = None
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get("https://www.google.com")
        print(f"SUCCESS: {name} worked!")
        return True
    except Exception as e:
        print(f"FAILED: {name} - {str(e).splitlines()[0]}")
        return False
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

configs = [
    ("Standard Headless", ["--headless"]),
    ("New Headless", ["--headless=new"]),
    ("Headless + No Sandbox", ["--headless", "--no-sandbox"]),
    ("Headless + Disable GPU", ["--headless", "--disable-gpu"]),
    ("Headless + No Sandbox + Disable GPU", ["--headless", "--no-sandbox", "--disable-gpu"]),
    ("New Headless + No Sandbox + Disable GPU", ["--headless=new", "--no-sandbox", "--disable-gpu"]),
    ("Minimal Headless", ["--headless", "--remote-debugging-port=9222"]),
]

for name, opts in configs:
    if test_config(name, opts):
        print(f"WINNER: Use config '{name}' with options {opts}")
        break
else:
    print("ALL CONFIGS FAILED.")
