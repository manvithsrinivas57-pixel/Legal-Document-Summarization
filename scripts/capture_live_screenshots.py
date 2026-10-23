"""Automated script to capture all genuine demonstration screenshots from live Streamlit app using Selenium Edge."""

import sys
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCREENSHOTS_DIR = PROJECT_ROOT / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

SAMPLE_PDF = (PROJECT_ROOT / "sample_data" / "sample_civil_appeal.pdf").resolve()

print(f"Sample PDF target: {SAMPLE_PDF} (exists: {SAMPLE_PDF.exists()})")

options = EdgeOptions()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1200")
options.add_argument("--no-sandbox")

driver = webdriver.Edge(options=options)
wait = WebDriverWait(driver, 120)

try:
    print("Navigating to http://localhost:8501 ...")
    driver.get("http://localhost:8501")
    time.sleep(6)  # allow Streamlit websocket to initialize and render

    # 1. Capture Home Page
    print("Capturing 01_home_page.png ...")
    driver.save_screenshot(str(SCREENSHOTS_DIR / "01_home_page.png"))

    # 2. Upload Judgment PDF
    print("Finding file uploader input...")
    file_inputs = driver.find_elements(By.CSS_SELECTOR, 'input[type="file"]')
    if file_inputs:
        print(f"Uploading {SAMPLE_PDF.name} ...")
        file_inputs[0].send_keys(str(SAMPLE_PDF))
        time.sleep(4)
        print("Capturing 02_pdf_uploaded.png ...")
        driver.save_screenshot(str(SCREENSHOTS_DIR / "02_pdf_uploaded.png"))
    else:
        print("File uploader input not immediately found, checking radio buttons...")
        # Check radio buttons for 'Upload Court Order / Judgment PDF'
        radios = driver.find_elements(By.CSS_SELECTOR, 'div[role="radiogroup"] label')
        for r in radios:
            if "Upload" in r.text:
                r.click()
                time.sleep(2)
                break
        file_inputs = driver.find_elements(By.CSS_SELECTOR, 'input[type="file"]')
        if file_inputs:
            file_inputs[0].send_keys(str(SAMPLE_PDF))
            time.sleep(4)
            driver.save_screenshot(str(SCREENSHOTS_DIR / "02_pdf_uploaded.png"))

    # 3. Trigger Pipeline Execution
    print("Triggering workflow execution...")
    buttons = driver.find_elements(By.TAG_NAME, "button")
    run_btn = None
    for b in buttons:
        if "Run Agentic Workflow" in b.text:
            run_btn = b
            break

    if not run_btn:
        print("Looking for button by CSS...")
        run_btn = driver.find_element(By.CSS_SELECTOR, 'button[kind="primary"]')

    run_btn.click()
    print("Run button clicked! Waiting for pipeline completion (up to 120s)...")

    # Wait for completion: either text 'Final Abstractive Summary' appears or 'Workflow execution complete!' toast
    def workflow_finished(d):
        text = d.page_source
        return ("Final Abstractive Summary" in text or "Research Integrity Halt" in text) and "Executing LangGraph" not in text

    wait.until(workflow_finished)
    print("Workflow completed successfully!")
    time.sleep(4)

    # 3. Capture Tab 1: Abstractive Summary & Top Metrics
    print("Capturing 03_abstractive_summary.png ...")
    driver.execute_script("window.scrollTo(0, 350);")
    time.sleep(1)
    driver.save_screenshot(str(SCREENSHOTS_DIR / "03_abstractive_summary.png"))

    # 4. Capture Downloadable Exports Section
    print("Capturing 07_downloadable_exports.png ...")
    driver.execute_script("window.scrollTo(0, 650);")
    time.sleep(1)
    driver.save_screenshot(str(SCREENSHOTS_DIR / "07_downloadable_exports.png"))

    # 5. Capture Tab 2: Legal Analysis & Doctrine
    print("Switching to Tab 2 (Legal Analysis & Doctrine)...")
    tabs = driver.find_elements(By.CSS_SELECTOR, 'button[data-testid="stTab"]')
    if len(tabs) >= 2:
        tabs[1].click()
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, 200);")
        time.sleep(1)
        print("Capturing 04_legal_analysis_and_doctrine.png ...")
        driver.save_screenshot(str(SCREENSHOTS_DIR / "04_legal_analysis_and_doctrine.png"))

    # 6. Capture Tab 3: Validation & Consistency
    print("Switching to Tab 3 (Validation & Consistency)...")
    tabs = driver.find_elements(By.CSS_SELECTOR, 'button[data-testid="stTab"]')
    if len(tabs) >= 3:
        tabs[2].click()
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, 200);")
        time.sleep(1)
        print("Capturing 05_validation_and_grounding.png ...")
        driver.save_screenshot(str(SCREENSHOTS_DIR / "05_validation_and_grounding.png"))

    # 7. Capture Tab 4: Audit Trail & Provenance
    print("Switching to Tab 4 (Audit Trail & Provenance)...")
    tabs = driver.find_elements(By.CSS_SELECTOR, 'button[data-testid="stTab"]')
    if len(tabs) >= 4:
        tabs[3].click()
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, 200);")
        time.sleep(1)
        print("Capturing 06_audit_trail.png ...")
        driver.save_screenshot(str(SCREENSHOTS_DIR / "06_audit_trail.png"))

    # 8. Capture Tab 5: Model & Training Status
    print("Switching to Tab 5 (Model & Training Status)...")
    tabs = driver.find_elements(By.CSS_SELECTOR, 'button[data-testid="stTab"]')
    if len(tabs) >= 5:
        tabs[4].click()
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, 150);")
        time.sleep(1)
        print("Capturing 08_model_status.png ...")
        driver.save_screenshot(str(SCREENSHOTS_DIR / "08_model_status.png"))

    print("\nALL SCREENSHOTS CAPTURED SUCCESSFULLY!")
    for p in sorted(SCREENSHOTS_DIR.glob("*.png")):
        print(f"  - {p.name}: {p.stat().st_size:,} bytes")

finally:
    driver.quit()
