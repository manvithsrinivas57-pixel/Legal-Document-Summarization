import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options as EdgeOptions

SCREENSHOTS_DIR = Path("screenshots").resolve()
SCREENSHOTS_DIR.mkdir(exist_ok=True)

options = EdgeOptions()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1200")

driver = webdriver.Edge(options=options)

try:
    print("Navigating to http://localhost:8501 ...")
    driver.get("http://localhost:8501")
    time.sleep(5)

    # 1. Capture Full Abstractive Summary view (scrolled into view)
    print("Capturing 03_abstractive_summary.png ...")
    driver.execute_script("let m = document.querySelector('section.main'); if (m) m.scrollTop = 500;")
    time.sleep(1)
    driver.save_screenshot(str(SCREENSHOTS_DIR / "03_abstractive_summary.png"))

    # 2. Capture Downloadable Exports view (scrolled further down)
    print("Capturing 07_downloadable_exports.png ...")
    driver.execute_script("let m = document.querySelector('section.main'); if (m) m.scrollTop = 850;")
    time.sleep(1)
    driver.save_screenshot(str(SCREENSHOTS_DIR / "07_downloadable_exports.png"))

    # Find tabs
    tabs = driver.find_elements(By.CSS_SELECTOR, 'button[data-testid="stTab"]')
    print(f"Found {len(tabs)} tabs!")
    for idx, t in enumerate(tabs):
        print(f"Tab {idx}: {t.text}")

    # Tab 2: Legal Analysis & Doctrine
    if len(tabs) >= 2:
        print("Clicking Tab 2: Legal Analysis...")
        tabs[1].click()
        time.sleep(2)
        driver.execute_script("let m = document.querySelector('section.main'); if (m) m.scrollTop = 150;")
        time.sleep(1)
        driver.save_screenshot(str(SCREENSHOTS_DIR / "04_legal_analysis_and_doctrine.png"))
        print("Saved 04_legal_analysis_and_doctrine.png")

    # Tab 3: Validation & Consistency
    if len(tabs) >= 3:
        print("Clicking Tab 3: Validation & Consistency...")
        tabs[2].click()
        time.sleep(2)
        driver.execute_script("let m = document.querySelector('section.main'); if (m) m.scrollTop = 150;")
        time.sleep(1)
        driver.save_screenshot(str(SCREENSHOTS_DIR / "05_validation_and_grounding.png"))
        print("Saved 05_validation_and_grounding.png")

    # Tab 4: Audit Trail & Provenance
    if len(tabs) >= 4:
        print("Clicking Tab 4: Audit Trail & Provenance...")
        tabs[3].click()
        time.sleep(2)
        driver.execute_script("let m = document.querySelector('section.main'); if (m) m.scrollTop = 150;")
        time.sleep(1)
        driver.save_screenshot(str(SCREENSHOTS_DIR / "06_audit_trail.png"))
        print("Saved 06_audit_trail.png")

    # Tab 5: Model & Training Status
    if len(tabs) >= 5:
        print("Clicking Tab 5: Model & Training Status...")
        tabs[4].click()
        time.sleep(2)
        driver.execute_script("let m = document.querySelector('section.main'); if (m) m.scrollTop = 150;")
        time.sleep(1)
        driver.save_screenshot(str(SCREENSHOTS_DIR / "08_model_status.png"))
        print("Saved 08_model_status.png")

    print("Finished tab screenshots!")

finally:
    driver.quit()
