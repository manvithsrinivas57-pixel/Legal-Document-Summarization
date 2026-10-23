import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options

o = Options()
o.add_argument('--headless=new')
d = webdriver.Edge(options=o)
d.get('http://localhost:8501')
time.sleep(5)
tabs = d.find_elements(By.CSS_SELECTOR, '[data-testid="stTab"]')
print(f"Found stTab elements: {len(tabs)}")
for idx, t in enumerate(tabs):
    print(f"Tab {idx}: <{t.tag_name}> '{t.text}'")
d.quit()
