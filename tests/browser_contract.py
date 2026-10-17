"""Browser contract check for Person 1 / Person 2 Flask APIs + Person 3 UI.

Run tests/fixture_server.py on port 5077 first. Requires Selenium and ChromeDriver.
No Oracle database required: route aggregation services use deterministic fixtures.
"""
import tempfile
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
import os

options=Options()
options.binary_location=os.getenv('CHROMIUM_BIN','/usr/bin/chromium')
for a in ('--no-sandbox','--disable-dev-shm-usage','--disable-gpu','--headless=new','--window-size=1440,1000'):
    options.add_argument(a)
directory=tempfile.mkdtemp(prefix='placement-api-contract-')
options.add_experimental_option('prefs',{'download.default_directory':directory,'download.prompt_for_download':False})
options.set_capability('goog:loggingPrefs',{'browser':'ALL'})
d=webdriver.Chrome(service=Service(os.getenv('CHROMEDRIVER_BIN','/usr/bin/chromedriver')),options=options)
wait=WebDriverWait(d,15)
try:
    d.get('http://127.0.0.1:5077/analytics')
    wait.until(lambda driver: driver.find_element(By.ID,'kpi-students').text == '10')
    assert d.find_element(By.ID,'kpi-placed').text == '7'
    assert d.find_element(By.ID,'kpi-applications').text == '20'
    assert d.find_element(By.ID,'kpi-highest').text == '₹21.00'
    assert not d.find_element(By.ID,'demo-banner').is_displayed()
    assert 'connected' in d.find_element(By.ID,'status-message').text.lower()
    assert 'Candidate Alpha' in d.find_element(By.ID,'recent-table').text
    print('PASS Person 1 overview/application/placement routes drive live dashboard KPIs and table')
    assert 'Alpha Labs' in d.find_element(By.ID,'recent-table').text
    assert d.find_element(By.ID,'package-avg').text == '₹10.29'
    assert d.find_element(By.ID,'interview-rate').text == '75.0%'
    for id in ['status-chart','branch-chart','recruiter-chart','package-chart','interview-chart']:
        assert d.execute_script('return !!Chart.getChart(document.getElementById(arguments[0]))',id), id
    print('PASS Person 2 companies/branches/packages + Person 3 interviews render all five charts')
    wait.until(lambda driver: len(Select(driver.find_element(By.ID,'branch-filter')).options)>1)
    Select(d.find_element(By.ID,'branch-filter')).select_by_value('CSE')
    wait.until(lambda driver:driver.find_element(By.ID,'kpi-students').text=='6')
    assert d.find_element(By.ID,'kpi-placed').text=='4'
    assert not d.find_element(By.ID,'demo-banner').is_displayed()
    print('PASS Oracle-scoped endpoint and filter response contract')
    d.find_element(By.ID,'reset-filters').click()
    wait.until(lambda driver:driver.find_element(By.ID,'kpi-students').text=='10')
    d.find_element(By.ID,'export-btn').click()
    wait.until(lambda _:len(list(Path(directory).glob('*.csv')))>=1)
    filename=list(Path(directory).glob('*.csv'))[0].name
    assert 'SAMPLE' not in filename,filename
    print('PASS clear filters returns to team endpoints and live-data CSV is not labeled sample')
    errors=[x['message'] for x in d.get_log('browser') if x['level']=='SEVERE' and 'Failed to load resource' not in x['message']]
    assert not errors,errors
    print('PASS no uncaught JS errors in complete cross-contributor workflow')
    print('INTEGRATION BROWSER PASS')
finally:
    d.quit()
