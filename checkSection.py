import pandas as pd
import re
import requests
from bs4 import BeautifulSoup


# Load your Excel file
loc = "C:\\Users\\abindal\\Downloads\\302_Sections.xlsx"
sections = pd.read_excel(loc, sheet_name="Frame Props 01 - General", header=1, usecols="A:K").iloc[1:]


# Function to parse UKB and UKC sections
def parse_ukb_ukc_section(section_name):
    # Regular expression to extract values from the input string (works for both UKB and UKC)
    match = re.match(r'(UK[BC])(\d+)X(\d+)X(\d+)', section_name)
    if not match:
        return f"Invalid section format: {section_name}"
    
    section_type = match.group(1)  # UKB or UKC
    t3 = match.group(2)  # Depth
    t2 = match.group(3)  # Width
    tw = match.group(4)  # Thickness
    
    return {
        "section_type": section_type,
        "t3": t3,
        "t2": t2,
        "tw": tw
    }

# Function to get section data from the web for UKB and UKC sections
def get_section_data_from_web(t3, t2, tw, section_type):
    base_url = 'https://beamdimensions.com/database/British/Steel/Universal_columns/'
    
    # Adjust URL formatting based on whether it's UKB or UKC
    formatted_size = f"{t3}X{t2}_{section_type}_{tw}"
    url = f"{base_url}{formatted_size}/"
    
    try:
        # Get the page content
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the table or relevant content for dimensions
        section_table = soup.find('table')  # Adjust based on actual HTML structure
        if section_table:
            rows = section_table.find_all('tr')
            section_data = {}
            for row in rows:
                columns = row.find_all('td')
                if len(columns) > 1:
                    key = columns[0].text.strip()
                    value = columns[1].text.strip()

                    # Mapping the specific dimensions to the corresponding parameters
                    if key == "Depth":
                        section_data["t3"] = value
                    elif key == "Top Width":
                        section_data["t2"] = value
                    elif key == "Top Thickness":
                        section_data["tf"] = value
                    elif key == "Web Thickness":
                        section_data["tw"] = value
                    elif key == "Bottom Width":
                        section_data["t2b"] = value
                    elif key == "Bottom Thickness":
                        section_data["tfb"] = value

            print(section_data)
            return section_data
        else:
            return f"No table found for {section_type} size {t3}X{t2}X{tw}."
    
    except requests.exceptions.HTTPError as e:
        return f"Error: {e}"


# Function to extract section details based on sectionType
def extract_section_details(section_name):
    # Extract section type (text before the first number)
    section_type = re.findall(r'[A-Za-z_-]+', section_name)[0]
    
    if section_type == 'CHHF':
        # CHHF: Extract t3 and tw (e.g., CHHF114.3X6.3 -> t3=114.3, tw=6.3)
        match = re.search(r'([0-9.]+)X([0-9.]+)', section_name)
        if match:
            t3 = float(match.group(1))  # First number before 'X'
            tw = float(match.group(2))  # Second number after 'X'
        else:
            t3, tw = None, None
        return section_type, t3, None, tw, None, None, None
    
    elif section_type == 'SHCF' or section_type == 'SHS' or section_type == 'SHHF':
        # SHCF: Extract t3, t2, tf, tw (e.g., SHCF100X50X5)
        match = re.search(r'([0-9.]+)X([0-9.]+)X([0-9.]+)X([0-9.]+)', section_name)
        if match:
            t3 = float(match.group(1))
            t2 = float(match.group(2))
            tf = float(match.group(3))
            tw = float(match.group(3))
        else:
            t3, t2, tw, tf = None, None, None, None
        return section_type, t3, t2, tw, tf, None, None

    elif section_type == 'Auto-RHS':
        # Auto-RHS: Return "OK" for this sectionType (no need for t3/t2/tw/tf/t2b/tfb values)
        return section_type, None, None, None, None, None, None

    elif section_type == 'I-':
        # I-: Extract t3, t2, tf, t2b, tw, tfb (e.g., I-1000X500/25X40)
        match = re.search(r'([0-9.]+)X([0-9.]+)/([0-9.]+)X([0-9.]+)', section_name)
        if match:
            t3 = float(match.group(1))  # First number (1000)
            t2 = float(match.group(2))  # Second number (500)
            tw = float(match.group(3))  # Third number (25, for tw)
            tf = float(match.group(4))  # Fourth number (40, for tf)
            # Assigning t2b and tfb the same values as t2 and tf
            t2b = t2
            tfb = tf
        else:
            t3, t2, tw, tf, t2b, tfb = None, None, None, None, None, None
        return section_type, t3, t2, tw, tf, t2b, tfb

    elif section_type == 'RHS':
        # RHS: Extract t3, t2, tf, tw (e.g., RHS1000X700X20)
        match = re.search(r'([0-9.]+)X([0-9.]+)X([0-9.]+)', section_name)
        if match:
            t3 = float(match.group(1))  # First number (1000)
            t2 = float(match.group(2))  # Second number (700)
            tf = float(match.group(3))  # Third number (20)
            tw = tf  # Same as tf for RHS
        else:
            t3, t2, tw, tf = None, None, None, None
        return section_type, t3, t2, tw, tf, None, None
    
    #elif section_type in ['UKB', 'UKC']:
    #    parsed = parse_ukb_ukc_section(section_name)
    #    if isinstance(parsed, dict):
            # Fetch section data from the web for UKB/UKC
    #        web_data = get_section_data_from_web(parsed['t3'], parsed['t2'], parsed['tw'], section_type)
    #        if isinstance(web_data, dict):
    #            return section_type, web_data.get('t3'), web_data.get('t2'), web_data.get('tw'), web_data.get('tf'), web_data.get('t2b'), web_data.get('tfb')
    #        else:
    #            return section_type, None, None, None, None, None, None  # Error in fetching data from web
    #    else:
    #        return section_type, None, None, None, None, None, None


    else:
        #print(f"No specific logic for sectionType '{section_type}'")
        # Default case if no specific logic is needed
        return section_type, None, None, None, None, None, None

# Apply the extraction to the 'SectionName' column
sections[['sectionType', 'extracted_t3', 'extracted_t2', 'extracted_tw', 'extracted_tf', 'extracted_t2b', 'extracted_tfb']] = sections['SectionName'].apply(
    lambda x: pd.Series(extract_section_details(x))
)





# Function to check if extracted values match with the existing ones in the DataFrame
def check_values(row):
    if row['sectionType'] == 'Auto-RHS':
        return 'OK'
    
    # Compare the extracted values with the respective values in the row
    for col in ['t3', 't2', 'tw', 'tf', 't2b', 'tfb']:
        extracted_value = row.get(f'extracted_{col}')
        actual_value = row.get(col)
        if pd.notna(extracted_value) and round(extracted_value,1) != round(actual_value,1):
            return 'NG'  # Return 'NG' if there is a mismatch
    
    return 'OK'  # Return 'OK' if everything matches

# Assuming the columns `t3`, `t2`, `tw`, `tf`, `t2b`, `tfb` exist in the original dataset, we check the values
# Apply the check function and create a new column 'Checked'
sections['Checked'] = sections.apply(check_values, axis=1)

# List of section types you want to filter
sectionTypeList = ['Auto-RHS', 'CHHF',"SHS", "CHS", "I-", "RHS", "SHCF", "SHHF", "UKB", "UKC", "UKPFC"]

# Filter and display results based on section types
for s in sectionTypeList:
    # Filter rows that match the current sectionType
    specSec = sections[sections['sectionType'].str.startswith(s)]
    
    # Check if any rows match the filter
    if not specSec.empty:
        pass
        #print(f"Rows matching sectionType '{s}':")
        #print(specSec[['SectionName', 'sectionType', 't3', 't2', 'tw', 'tf', 't2b', 'tfb', 'Checked']].head())  # Print relevant columns
    else:
        print(f"No rows found for sectionType '{s}'.")

# show sections that are NG
print("Sections that are NG:")
# If tf or tfb are present, check if they are > 1, else put Checked as NG
sections.loc[sections['tf'].notnull() & (sections['tf'] < 1), 'Checked'] = 'NG'
sections.loc[sections['tfb'].notnull() & (sections['tfb'] < 1), 'Checked'] = 'NG'

# if tf or tfb are present, check if they are > 30 and put Checked as NG
sections.loc[sections['tf'].notnull() & (sections['tf'] > 100), 'Checked'] = 'NG'
sections.loc[sections['tfb'].notnull() & (sections['tfb'] > 100), 'Checked'] = 'NG'

# if tw is present, check if it is > 30 and put Checked as NG
sections.loc[sections['tw'].notnull() & (sections['tw'] > 100), 'Checked'] = 'NG'

print(sections[sections['Checked'] == 'NG'][['SectionName', 'sectionType', 't3', 't2', 'tw', 'tf', 't2b', 'tfb', 'Checked']])

# sort sections aseending by tf and print first 10
# Print SectionName, t3, t2, tw, tf, t2b, tfb
print("Sections sorted by tf:")
print(sections.sort_values(by='tf', ascending=True).head(10)[['SectionName', 't3', 't2', 'tw', 'tf', 't2b', 'tfb']])

# sort sections ascending by tw and print first 10
print("Sections sorted by tw:")
print(sections.sort_values(by='tw', ascending=True).head(10)[['SectionName', 't3', 't2', 'tw', 'tf', 't2b', 'tfb']])

