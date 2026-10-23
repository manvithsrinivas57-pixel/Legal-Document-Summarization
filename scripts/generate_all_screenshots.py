"""Complete, robust automated screenshot capture for all 7 required presentation views."""

import sys
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options as EdgeOptions

# Set UTF-8 output encoding for Windows console
sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCREENSHOTS_DIR = PROJECT_ROOT / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)
SAMPLE_PDF = (PROJECT_ROOT / "sample_data" / "sample_civil_appeal.pdf").resolve()

options = EdgeOptions()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1200")

driver = webdriver.Edge(options=options)

try:
    print("1. Opening http://localhost:8501 ...")
    driver.get("http://localhost:8501")
    time.sleep(5)

    # 1. Home Page
    print("Saving 01_home_page.png ...")
    driver.save_screenshot(str(SCREENSHOTS_DIR / "01_home_page.png"))

    # 2. Upload Judgment PDF
    print(f"2. Uploading PDF: {SAMPLE_PDF.name} ...")
    file_input = driver.find_element(By.CSS_SELECTOR, 'input[type="file"]')
    file_input.send_keys(str(SAMPLE_PDF))
    time.sleep(5)

    print("Saving 02_pdf_uploaded.png ...")
    driver.save_screenshot(str(SCREENSHOTS_DIR / "02_pdf_uploaded.png"))

    # 3. Trigger Pipeline
    print("3. Clicking '🚀 Run Agentic Workflow' ...")
    buttons = driver.find_elements(By.TAG_NAME, "button")
    run_btn = [b for b in buttons if "Run Agentic Workflow" in b.text][0]
    run_btn.click()

    # Poll for completion
    print("Waiting for pipeline execution...")
    for sec in range(120):
        time.sleep(1)
        src = driver.page_source
        if "Final Abstractive Summary" in src or "Workflow Status" in src and "Executing LangGraph" not in src:
            print(f"Workflow completed in ~{sec} seconds!")
            break
    time.sleep(3)

    # 4. Abstractive Summary & Metrics
    print("Saving 03_abstractive_summary.png ...")
    driver.execute_script("let m = document.querySelector('section.main'); if (m) m.scrollTop = 500;")
    time.sleep(1)
    driver.save_screenshot(str(SCREENSHOTS_DIR / "03_abstractive_summary.png"))

    # 5. Export Download Buttons
    print("Saving 07_downloadable_exports.png ...")
    driver.execute_script("let m = document.querySelector('section.main'); if (m) m.scrollTop = 850;")
    time.sleep(1)
    driver.save_screenshot(str(SCREENSHOTS_DIR / "07_downloadable_exports.png"))

    # Find all tabs using [data-testid="stTab"]
    tabs = driver.find_elements(By.CSS_SELECTOR, '[data-testid="stTab"]')
    print(f"Found {len(tabs)} tabs!")

    # 6. Tab 2: Legal Analysis & Doctrine
    if len(tabs) >= 2:
        print("Clicking Tab 2: Legal Analysis & Doctrine...")
        tabs[1].click()
        time.sleep(3)
        driver.execute_script("let m = document.querySelector('section.main'); if (m) m.scrollTop = 150;")
        time.sleep(1)
        driver.save_screenshot(str(SCREENSHOTS_DIR / "04_legal_analysis_and_doctrine.png"))
        print("Saved 04_legal_analysis_and_doctrine.png")

    # 7. Tab 3: Validation & Consistency
    if len(tabs) >= 3:
        print("Clicking Tab 3: Validation & Consistency...")
        tabs[2].click()
        time.sleep(3)
        driver.execute_script("let m = document.querySelector('section.main'); if (m) m.scrollTop = 150;")
        time.sleep(1)
        driver.save_screenshot(str(SCREENSHOTS_DIR / "05_validation_and_grounding.png"))
        print("Saved 05_validation_and_grounding.png")

    # 8. Tab 4: Audit Trail & Provenance
    if len(tabs) >= 4:
        print("Clicking Tab 4: Audit Trail & Provenance...")
        tabs[3].click()
        time.sleep(3)
        driver.execute_script("let m = document.querySelector('section.main'); if (m) m.scrollTop = 150;")
        time.sleep(1)
        driver.save_screenshot(str(SCREENSHOTS_DIR / "06_audit_trail.png"))
        print("Saved 06_audit_trail.png")

    # 9. Tab 5: Model & Training Status
    if len(tabs) >= 5:
        print("Clicking Tab 5: Model & Training Status...")
        tabs[4].click()
        time.sleep(3)
        driver.execute_script("let m = document.querySelector('section.main'); if (m) m.scrollTop = 150;")
        time.sleep(1)
        driver.save_screenshot(str(SCREENSHOTS_DIR / "08_model_status.png"))
        print("Saved 08_model_status.png")

    print("\nALL SCREENSHOTS CAPTURED SUCCESSFULLY:")
    for p in sorted(SCREENSHOTS_DIR.glob("*.png")):
        print(f"  - {p.name}: {p.stat().st_size:,} bytes")

finally:
    driver.quit()
