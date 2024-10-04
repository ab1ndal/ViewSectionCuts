import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import requests
import os
import time
from threading import Thread
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Assuming `app.py` contains your Dash app
from app import GlobalAnalysisApp  # Adjust the import if necessary

# List of different cut names for testing
cut_name_sets = [
    "S12-All",
    "S12A-All",   
    "S12B-All",
]

cutID = ['']
linetype = ['solid']

load_case_list = ['1.0D+0.5L', 'SC - TP', 'SC - TN', 'MCE-All GM Average (Seis Only)']
load_color_list = ['#25262b', '#fa5252', '#228be6', '#40c057']
load_case_id = ['D+0.5L', 'T-Pos', 'T-Neg', 'MCE-Only']
load_case_type = ['NonLin', 'NonLin', 'NonLin', 'TH']

inUnit = 'kip,in,F'
outUnit = 'kN,m,C'

shear_limits = [-18000,18000,6000]
axial_limits = [-15000,15000,5000]
moment_limits = [-300000,300000,100000]
torsion_limits = [-60000,60000,20000]

plot_title_prefix = 'Model 305 (LB) - Responses '
plot_name_prefix = '305_LB_SectionCut_'


def run_app(globalApp):
    # Disable debug and use_reloader to avoid signal handling issues
    globalApp.app.run_server(debug=False, use_reloader=False, port=globalApp.port)


def simulate_file_upload_and_plot(driver, height_file_path, data_file_path, cut_name_sets):
    """Simulate file upload and plot generation for different cut names."""
    
    wait = WebDriverWait(driver, 200)  # Define a wait time of 60 seconds

    # Simulate dropdown interactions
    driver.find_element(By.CSS_SELECTOR, '[id*="sectionCut-input-unit"]').click()
    option_to_select = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, f"//div[@value='{inUnit}']")))
    option_to_select.click()

    #driver.find_element(By.CSS_SELECTOR, '[id*="sectionCut-output-unit"]').click()
    #option_to_select = WebDriverWait(driver, 10).until(
    #EC.element_to_be_clickable((By.XPATH, f"//div[@value='{outUnit}']")))
    #option_to_select.click()

    print('Uploading files...')

    # Upload height file (using the ID containing 'upload-height-data')
    upload_component_height = driver.find_element_by_xpath('//*[@id="upload-height-data"]/div/input')

    #upload_component_height = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[id*="upload-height-data"]')))
    upload_component_height.send_keys(height_file_path)
    #driver.execute_script("arguments[0].setAttribute('value', arguments[1]);", upload_component_height, height_file_path)

    # Upload data file (using the ID containing 'upload-sectioncut-data')
    upload_component_data = driver.find_element_by_xpath('//*[@id="upload-sectioncut-data"]/div/input')
    #upload_component_data = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[id*="upload-sectioncut-data"]')))
    upload_component_data.send_keys(data_file_path)

    # Wait for the second file to upload
    #wait.until(EC.text_to_be_present_in_element((By.ID, 'file-upload-status'), 'SectionCutDataFileUploaded'))
    time.sleep(90)

    print('Files uploaded. Setting up the form...')

    

    #driver.find_element(By.CSS_SELECTOR, '[id*="sectionCut-output-unit"]').send_keys(outUnit)
    #driver.find_element(By.CSS_SELECTOR, '[id*="load-case-name"]').send_keys(load_case_list[0])
    multiselect = driver.find_element(By.CSS_SELECTOR, '[id*="load-case-name"]')
    multiselect.click()
    for caseName in load_case_list:
        option_to_select = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, f"//div[@value='{caseName}']")))
        option_to_select.click()
    multiselect.click()
      
    

    # Loop through cut names and generate plot for each
    print('Iterating through cut names...')
    for cut_names in cut_name_sets:
        #driver.find_element(By.CSS_SELECTOR, '[id*="cut-name-list"]').send_keys(cut_names)
        driver.find_element(By.CSS_SELECTOR, '[id*="sectionCut-plot-title"]').send_keys(f'{plot_title_prefix} [{cut_names}]')
        driver.find_element(By.CSS_SELECTOR, '[id*="sectionCut-plot-filename"]').send_keys(f'{plot_name_prefix}{cut_names}]')
        driver.find_element(By.CSS_SELECTOR, '[id*="cut-name-list"]').click()
        option_to_select = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, f"//div[@value='{cut_names}']")))
        option_to_select.click()
        

        # Click submit button
        driver.find_element(By.CSS_SELECTOR, '[id*="submit-button-sectionCut"]').click()

        # Wait for the graph to be updated (you could also wait for a specific DOM change indicating the graph is ready)
        time.sleep(5)  # Adjust this to the response time of your app

        print(f"Plot generated for {cut_names[0]}")

if __name__ == "__main__":
    # File paths for the height and data files
    height_file_path = "C:\\Users\\abindal\\OneDrive - Nabih Youssef & Associates\\Documents\\00_Projects\\06_The Vault\\305\\20240924\\FloorElevations.xlsx"  # Update with the actual path to your height file
    data_file_path = "C:\\Users\\abindal\\OneDrive - Nabih Youssef & Associates\\Documents\\00_Projects\\06_The Vault\\305\\20240924\\LB\\20240924_305_LB_NewSizes2_SectionCut.xlsx"  # Update with the actual path to your data file

    globalApp = GlobalAnalysisApp()

    # Run the Dash app in a separate thread
    app_thread = Thread(target=run_app, args=(globalApp,))
    app_thread.start()

    # Give the app time to start
    time.sleep(10)


    # Setup Selenium WebDriver (Chrome)
    chrome_service = Service(executable_path="C:\\Users\\abindal\\Downloads\\chromedriver-win64 (1)\\chromedriver-win64\\chromedriver.exe")  # Update with your actual path to chromedriver
    driver = webdriver.Chrome(service=chrome_service)
    
    driver.get('http://127.0.0.1:8050/')  # Assuming your app is hosted at this URL

    try:
        wait = WebDriverWait(driver, 60)
        section_cut_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[id*="section-cut"]')))
        section_cut_button.click()
        section_cut_visualize = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[id*="visualize-section-cuts"]')))
        section_cut_visualize.click()
        # Use Selenium to simulate interactions and test the app
        simulate_file_upload_and_plot(driver, height_file_path, data_file_path, cut_name_sets)
    except Exception as e:
        print(f"An error occurred: {e}")
        driver.quit()
    finally:
        # Clean up
        driver.quit()

    # Ensure the app thread is cleaned up
    app_thread.join()
