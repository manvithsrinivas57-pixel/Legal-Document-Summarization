import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options as EdgeOptions

options = EdgeOptions()
options.add_argument("--headless=new")
driver = webdriver.Edge(options=options)
try:
    driver.get("http://localhost:8501")
    time.sleep(5)
    # Check different tab selectors
    for sel in ['button[role="tab"]', 'div[data-testid="stTabs"] button', '[data-baseweb="tab"]', 'button']:
        elems = driver.find_elements(By.CSS_SELECTOR, sel)
        matches = [e.text for e in elems if any(k in e.text for k in ["Summarization", "Analysis", "Validation", "Audit", "Model"])]
        if matches:
            print(f"Selector '{sel}' found matches: {matches}")
finally:
    driver.quit()
