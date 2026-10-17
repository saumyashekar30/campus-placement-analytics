"""Optional headless browser verification.

Start Flask on http://127.0.0.1:5059, then run:
    python tests/browser_smoke.py
Install selenium and Chromium/ChromeDriver first.
No Oracle connection is required; checks the explicitly labeled synthetic preview.
"""
from pathlib import Path
import os
import tempfile
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait

ROOT = os.getenv("PLACEMENT_DASHBOARD_URL", "http://127.0.0.1:5059/analytics")
download = tempfile.mkdtemp(prefix="campus-export-")
opts = Options()
opts.binary_location = os.getenv("CHROMIUM_BIN", "/usr/bin/chromium")
for arg in ("--headless=new", "--no-sandbox", "--disable-dev-shm-usage",
            "--disable-gpu", "--window-size=1440,1000"):
    opts.add_argument(arg)
opts.add_experimental_option("prefs", {
    "download.default_directory":download,
    "download.prompt_for_download":False,
})
opts.set_capability("goog:loggingPrefs", {"browser":"ALL"})
service = Service(os.getenv("CHROMEDRIVER_BIN", "/usr/bin/chromedriver"))
browser = webdriver.Chrome(service=service, options=opts)
wait = WebDriverWait(browser, 10)
try:
    browser.get(ROOT)
    wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
    assert browser.find_element(By.ID, "sample-preview-btn").is_displayed()
    browser.find_element(By.ID, "sample-preview-btn").click()
    wait.until(lambda d: d.find_element(By.ID, "kpi-students").text == "840")
    assert browser.find_element(By.ID, "demo-banner").is_displayed()
    assert "synthetic" in browser.find_element(By.ID, "status-message").text.lower()
    assert browser.execute_script("return typeof window.Chart") == "function"
    assert browser.execute_script("return !!Chart.getChart(document.getElementById('status-chart'))")
    print("PASS sample preview shows explicit synthetic data and Chart.js charts")
    Select(browser.find_element(By.ID,"branch-filter")).select_by_value("CSE")
    wait.until(lambda d: d.find_element(By.ID,"kpi-students").text == "290")
    print("PASS sample branch filter updates cards")
    Select(browser.find_element(By.ID,"company-filter")).select_by_visible_text("Microsoft")
    wait.until(lambda d: d.find_element(By.ID,"kpi-placed").text != "238")
    assert browser.find_element(By.ID,"demo-banner").is_displayed()
    print("PASS sample company filter updates charts without leaving preview")
    Select(browser.find_element(By.ID,"year-filter")).select_by_value("2025")
    wait.until(lambda d: d.find_element(By.ID,"kpi-applications").text == "0")
    print("PASS year filter displays empty sample year")
    browser.find_element(By.ID,"reset-filters").click()
    wait.until(lambda d: d.find_element(By.ID,"kpi-students").text == "840")
    print("PASS clear filters restores original preview")
    browser.find_element(By.ID,"export-btn").click()
    wait.until(lambda _: any(Path(download).glob("*.csv")))
    assert "SAMPLE-" in next(Path(download).glob("*.csv")).name
    print("PASS CSV export downloads explicitly sample-named file")
    browser.refresh()
    wait.until(lambda d: d.find_element(By.ID,"demo-banner").is_displayed())
    assert browser.find_element(By.ID,"error-box").is_displayed()
    assert browser.find_element(By.ID,"kpi-students").text == "840"
    print("PASS offline API automatically falls back within timeout")
    previous=browser.execute_script("return performance.getEntriesByType('resource').filter(x=>x.name.includes('/analytics/overview')).length")
    browser.find_element(By.ID,"retry-btn").click()
    wait.until(lambda d: d.execute_script("return performance.getEntriesByType('resource').filter(x=>x.name.includes('/analytics/overview')).length")>previous)
    wait.until(lambda d: d.find_element(By.ID,"demo-banner").is_displayed())
    print("PASS retry triggers another API request and returns to preview")
    browser.set_window_size(390,850)
    browser.find_element(By.ID,"menu-toggle").click()
    wait.until(lambda d: "open" in d.find_element(By.ID,"sidebar").get_attribute("class"))
    print("PASS mobile navigation toggles open")
    severe=[r["message"] for r in browser.get_log("browser")
            if r["level"]=="SEVERE" and
            "Failed to load resource" not in r["message"]]
    assert not severe, severe
    print("PASS no uncaught JavaScript console errors")
    print("BROWSER PASS")
finally:
    browser.quit()
