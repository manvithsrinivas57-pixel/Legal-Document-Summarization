import sys
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions

options = EdgeOptions()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--no-sandbox")

try:
    print("Initializing Edge WebDriver...")
    driver = webdriver.Edge(options=options)
    print("Navigating to http://localhost:8501 ...")
    driver.get("http://localhost:8501")
    time.sleep(5)
    print("Page title:", driver.title)
    
    out_dir = Path("screenshots")
    out_dir.mkdir(exist_ok=True)
    driver.save_screenshot(str(out_dir / "01_home_page.png"))
    print("Screenshot saved to screenshots/01_home_page.png")
    driver.quit()
    print("SUCCESS")
except Exception as e:
    print("Error:", e)
    sys.exit(1)
