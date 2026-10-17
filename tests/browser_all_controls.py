"""Every dashboard button & filter checked in real headless Chrome.

Test-only fixture server: python tests/fixture_server.py (127.0.0.1:5077)
Offline app server: python -c 'from app import app;app.run(port=5059,debug=False)'
Run: python tests/browser_all_controls.py
Uses no real Oracle data and never writes to GitHub.
"""
import os
import tempfile
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select

LIVE=os.getenv("PLACEMENT_CONTRACT_URL","http://127.0.0.1:5077/analytics")
OFFLINE=os.getenv("PLACEMENT_DASHBOARD_URL","http://127.0.0.1:5059/analytics")
TMP=tempfile.mkdtemp(prefix="campus-all-buttons-")
options=Options()
options.binary_location=os.getenv("CHROMIUM_BIN","/usr/bin/chromium")
for a in ("--headless=new","--disable-gpu","--no-sandbox","--disable-dev-shm-usage","--window-size=1440,1050"):
    options.add_argument(a)
options.add_experimental_option("prefs",{"download.default_directory":TMP,"download.prompt_for_download":False})
options.set_capability("goog:loggingPrefs",{"browser":"ALL"})
d=webdriver.Chrome(service=Service(os.getenv("CHROMEDRIVER_BIN","/usr/bin/chromedriver")),options=options)
wait=WebDriverWait(d,15)

def loaded(kpi):
    wait.until(lambda x:x.find_element(By.ID,"kpi-students").text == kpi)

def requests(path):
    return d.execute_script("return performance.getEntriesByType('resource').filter(x=>x.name.includes(arguments[0])).length",path)

def click(id):
    element=d.find_element(By.ID,id)
    d.execute_script("document.documentElement.style.scrollBehavior='auto'; arguments[0].scrollIntoView({block: 'center', behavior:'instant'})",element)
    wait.until(lambda x: 0 <= x.execute_script("return arguments[0].getBoundingClientRect().top",element) < x.execute_script("return innerHeight"))
    element.click()

def note(message):
    print("PASS",message,flush=True)

try:
    d.get(LIVE);loaded("10")
    assert not d.find_element(By.ID,"demo-banner").is_displayed()
    assert "connected" in d.find_element(By.ID,"status-message").text.lower()
    assert len(d.find_elements(By.CSS_SELECTOR,".sidebar a[href]")) >= 8
    note("Live dashboard and sidebar links from team Flask routes")

    for key in ("placements","recruiters","interviews"):
        d.find_element(By.CSS_SELECTOR,".sidebar a[href='#"+key+"']").click()
        assert d.execute_script("return location.hash") == "#"+key
    note("Placement, recruiters and interview navigation anchors")

    before=requests("/analytics/overview")
    click("refresh-btn")
    wait.until(lambda x:requests("/analytics/overview") > before)
    loaded("10")
    note("Refresh sends new live API requests")

    click("sample-preview-btn");loaded("840")
    assert d.find_element(By.ID,"demo-banner").is_displayed()
    note("Permanent Sample Preview button and synthetic labeling")

    Select(d.find_element(By.ID,"branch-filter")).select_by_value("CSE")
    loaded("290")
    Select(d.find_element(By.ID,"company-filter")).select_by_visible_text("Microsoft")
    assert d.find_element(By.ID,"kpi-placed").text != "238"
    Select(d.find_element(By.ID,"year-filter")).select_by_value("2025")
    wait.until(lambda x:x.find_element(By.ID,"kpi-applications").text == "0")
    note("All three dropdown filters update preview, including empty dataset")

    click("reset-filters");loaded("840")
    assert not any(d.find_element(By.ID,i).get_attribute("value") for i in ("branch-filter","company-filter","year-filter"))
    note("Clear all resets every dropdown and every KPI")

    click("export-btn")
    wait.until(lambda x:any("SAMPLE-" in p.name for p in Path(TMP).glob("*.csv")))
    note("Export sample CSV visibly labeled SAMPLE")

    Select(d.find_element(By.ID,"branch-filter")).select_by_value("CSE")
    click("leave-demo");loaded("10")
    assert not d.find_element(By.ID,"demo-banner").is_displayed()
    assert d.find_element(By.ID,"branch-filter").get_attribute("value") == ""
    note("Return to live clears synthetic filters and loads real API contract")

    click("export-btn")
    wait.until(lambda x:any("SAMPLE-" not in p.name for p in Path(TMP).glob("*.csv")))
    note("Export live CSV distinguished from sample export")

    d.set_window_size(390,850)
    click("menu-toggle")
    wait.until(lambda x:"open" in x.find_element(By.ID,"sidebar").get_attribute("class"))
    ActionChains(d).move_to_element_with_offset(d.find_element(By.ID,"mobile-shade"),160,0).click().perform()
    wait.until(lambda x:"open" not in x.find_element(By.ID,"sidebar").get_attribute("class"))
    click("menu-toggle")
    wait.until(lambda x:"open" in x.find_element(By.ID,"sidebar").get_attribute("class"))
    d.find_element(By.CSS_SELECTOR,"body").send_keys("\ue00c") # Escape
    wait.until(lambda x:"open" not in x.find_element(By.ID,"sidebar").get_attribute("class"))
    note("Mobile menu, backdrop close and keyboard Escape close")

    d.set_window_size(1440,1000)
    d.get(OFFLINE)
    wait.until(lambda x:x.find_element(By.ID,"error-box").is_displayed())
    loaded("840")
    click("demo-btn")
    assert not d.find_element(By.ID,"error-box").is_displayed()
    note("Error-panel Preview sample data button")

    click("refresh-btn")
    wait.until(lambda x:x.find_element(By.ID,"error-box").is_displayed())
    loaded("840")
    note("Refresh during sample/offline mode retries and returns to preview")

    before=requests("/analytics/overview")
    click("retry-btn")
    wait.until(lambda x:requests("/analytics/overview") > before)
    wait.until(lambda x:x.find_element(By.ID,"error-box").is_displayed())
    note("Retry attempts a new Oracle-backed request")

    click("leave-demo")
    wait.until(lambda x:x.find_element(By.ID,"error-box").is_displayed())
    loaded("840")
    note("Return-to-live handles offline Oracle without freezing")

    bad=[r["message"] for r in d.get_log("browser") if r["level"]=="SEVERE"
         and "Failed to load resource" not in r["message"]]
    assert not bad,bad
    buttons={e.get_attribute("id") for e in d.find_elements(By.CSS_SELECTOR,"button[id]")}
    expected={"menu-toggle","sample-preview-btn","export-btn","refresh-btn","reset-filters",
              "retry-btn","demo-btn","leave-demo"}
    assert expected <= buttons,expected-buttons
    note("All 8 dashboard buttons, all filters, and no uncaught JavaScript errors")
    print("ALL-CONTROLS BROWSER PASS",flush=True)
finally:
    d.quit()
