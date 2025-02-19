import time
from threading import Thread
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys

from app import GlobalAnalysisApp

# File Paths:
height_file_path = "C:\\Users\\abindal\\OneDrive - Nabih Youssef & Associates\\Documents - The Vault\\Calculations\\2025 -  Stage 3C\\305 - Model Results\\20250207_305_FineMesh_LB\\SectionCuts\\FloorElevations.xlsx"  # Update with the actual path to your height file
data_file_path = "C:\\Users\\abindal\\OneDrive - Nabih Youssef & Associates\\Documents - The Vault\\Calculations\\2025 -  Stage 3C\\305 - Model Results\\20250207_305_FineMesh_LB\\SectionCuts\\20250207_305_GapFriction_LB_FineMesh_AllCuts.xlsx"  # Update with the actual path to your data file


# List of different cut names for testing
cut_name_sets = ["S12-All", "S12A-All", "S12B-All"]

cutID = ['']
linetype = ['solid']

load_case_list = ['1.0D+0.5L', 'End of Staged Construction - TP', 'End of Staged Construction - TN', 'MCE-All GM Average (Seis Only)']
load_color_list = ['#25262b', '#fa5252', '#228be6', '#40c057']
load_case_id = ['D+0.5L', 'T-Pos', 'T-Neg', 'MCE-Only']
load_case_type = ['NonLin', 'NonLin', 'NonLin', 'TH']

inUnit = 'kN,m,C'
outUnit = 'kN,m,C'

shear_limits = [-18000,18000,6000]
axial_limits = [-15000,15000,5000]
moment_limits = [-300000,300000,100000]
torsion_limits = [-60000,60000,20000]
height_limits = [-60.365, 29.835]

model_name = '305 [LB]'


def run_app(globalApp):
    # Disable debug and use_reloader to avoid signal handling issues
    globalApp.app.run_server(debug=False, use_reloader=False, port=globalApp.port)

globalApp = GlobalAnalysisApp()
app_thread = Thread(target=run_app, args=(globalApp,))
app_thread.start()
time.sleep(10)

#Starting Selenium
chrome_service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=chrome_service)
driver.get('http://127.0.0.1:8050/')

def upload_file(input_id, file_path):
    """Upload a file to the input element with the given ID."""
    upload_input = driver.find_element(By.XPATH, f'//*[@id="{input_id}"]/div/input')
    driver.execute_script("arguments[0].style.display = 'block';", upload_input)  # Ensure visibility
    upload_input.send_keys(file_path)

wait = WebDriverWait(driver, 60)
# Click on "Section Cuts"
print("Clicking on Section Cuts")
print(driver.page_source)
section_cuts_tab = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[span[text()="Section Cuts"]]')))
section_cuts_tab.click()

print("Clicking on Visualize")
# Wait for the "Visualize" tab within Section Cuts to appear
visualize_tab = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[span[text()="Visualize"]]')))
visualize_tab.click()


# Upload files
upload_file("upload-height-data", height_file_path)
upload_file("upload-sectioncut-data", data_file_path)

# Input Unit
print("Setting input and output units")
if inUnit != 'kN,m,C':
    input_unit_dropdown = wait.until(EC.element_to_be_clickable((By.ID, "sectionCut-input-unit")))
    input_unit_dropdown.click()
    unit_option = wait.until(EC.element_to_be_clickable((By.XPATH, f"//div[contains(@class, 'mantine-Select-option') and @value='{inUnit}']")))
    unit_option.click()

# Output Unit
if outUnit != 'kN,m,C':
    output_unit_dropdown = wait.until(EC.element_to_be_clickable((By.ID, "sectionCut-output-unit")))
    output_unit_dropdown.click()
    unit_option = wait.until(EC.element_to_be_clickable((By.XPATH, f"//div[contains(@class, 'mantine-Select-option') and @value='{outUnit}']")))
    unit_option.click()

# Update Model name
print("Updating model name")
model_name_input = wait.until(EC.element_to_be_clickable((By.ID, "sectionCut-model-name")))
model_name_input.click()
model_name_input.clear()
model_name_input.send_keys(model_name)
print("Model name updated")

def wait_for_progress_to_complete(progress_element_id):
    while True:
        # Locate the main progress bar element
        progress_element = wait.until(EC.presence_of_element_located((By.ID, progress_element_id)))
        # Find the child element with the progress value
        progress_section = progress_element.find_element(By.CLASS_NAME, "m_2242eb65")
        # Get the value of 'aria-valuenow' from the child element
        aria_value_now = progress_section.get_attribute("aria-valuenow")
        # Check if the progress is 100%
        if aria_value_now == "100":
            print("Progress complete: 100%")
            break
        else:
            print(f"Current progress: {aria_value_now}%")
            time.sleep(1)

# Example usage for the specific progress bar
wait_for_progress_to_complete('upload-sectioncut-data-progress')

# update load case list
#print("Updating load case list")
#load_case_input = wait.until(EC.element_to_be_clickable((By.ID, "load-case-name")))
#load_case_input.click()

# Clear the existing load case list by clicking the first two options
# Get all the selected pills
#selected_pills = driver.find_elements(By.XPATH, "//div[contains(@class, 'mantine-MultiSelect-pill')]")

# Extract the text of each selected pill
#selected_options = [pill.find_element(By.CLASS_NAME, "mantine-Pill-label").text for pill in selected_pills]

#for option in selected_options:
#    case_option = wait.until(EC.element_to_be_clickable((By.XPATH, F"//div[contains(@class, 'mantine-MultiSelect-option') and @value='{option}']")))
#    case_option.click()

# Now loop through and select the options from the list using JavaScript if necessary
#for option in load_case_list:
#    try:
        # Locate the option using its value attribute
#        case_option = wait.until(EC.presence_of_element_located((By.XPATH, f"//div[contains(@class, 'mantine-MultiSelect-option') and @value='{option}']")))
        
        # Click the option using JavaScript
#        driver.execute_script("arguments[0].click();", case_option)
        
#    except Exception as e:
#        print(f"Error selecting option {option}: {e}")
#        continue  # Move to the next option if there's an error

# Close the dropdown
another_element = wait.until(EC.element_to_be_clickable((By.TAG_NAME, "body")))  # Clicking anywhere on the body
another_element.click()

accordion_button = driver.find_element(By.ID, "plot-limit-accordion-button")
accordion_button.click()

WebDriverWait(driver, 2).until(lambda d: accordion_button.get_attribute("aria-expanded") == "true")

def update_plot_limits(limit_type, limits, hasStep=False):
    # Locate the input elements for the limits
    print(f"Updating {limit_type} limits")
    min_lim = wait.until(EC.element_to_be_clickable((By.ID, f"{limit_type}-min")))
    min_lim.clear()
    min_lim.send_keys(limits[0])

    max_lim = wait.until(EC.element_to_be_clickable((By.ID, f"{limit_type}-max")))
    max_lim.clear()
    max_lim.send_keys(limits[1])

    if hasStep:
        step_lim = wait.until(EC.element_to_be_clickable((By.ID, f"{limit_type}-step")))
        step_lim.clear()
        step_lim.send_keys(limits[2])


# Update shear limits
print("Updating shear limits")
update_plot_limits("shear", shear_limits, hasStep=True)
update_plot_limits("axial", axial_limits, hasStep=True)
update_plot_limits("moment", moment_limits, hasStep=True)
update_plot_limits("torsion", torsion_limits, hasStep=True)
update_plot_limits("height", height_limits)



#driver.quit()
#app_thread.join()
    
