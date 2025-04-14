import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
plt.rcParams.update({'font.family': 'Arial'})

filePath = r'C:\\Users\\abindal\\OneDrive - Nabih Youssef & Associates\\Documents - The Vault\\Calculations\\2025 -  Stage 3C\\205 - Model Results\\20250324_205_UBSt_LBFr\\'
fileName = '20250324_205_UB stiffness lb friction_Story.xlsx'
inFile = filePath + fileName

loadCaseList = ['1.0D+0.5L', 'MCE-All GM Average (Seis Only)']
loadCaseName = ['Gravity', 'MCE-Only']

plotList = ['F1', 'F2', 'F3', 'M2', 'M1', 'M3']
xLabelList = ['Shear Along Axis 1 (kN)', 'Shear Along Axis 2 (kN)', 'Axial (kN)', 'Flexure About Axis 2 (kN-m)', 'Flexure About Axis 1 (kN-m)', 'Torsion (kN-m)']
titleList = ['F1 (A-Canyon)', 'F2 (X-Canyon)', 'F3 (Vertical)', 'M2 (A-Canyon)', 'M1 (X-Canyon)', 'M3']
#cutList = ['N12A-All', 'N12A-Conc', 'N12B-All', 'N12B-Conc', 'N12C-All', 'N12C-Conc', 'N12D-All', 'N12D-Conc', 'N12-All', 'N12-Conc', 'N13A-All', 'N13A-Conc', 'N13B-All', 'N13C-All', 
#           'N13D-All', 'N13E-All', 'N13F-All', 'N13G-All', 'N13H-All']
cutList = ['Overall', 'Conc_Overall', 'Steel_Overall']
#cutList = ['S12A-All', 'S12A-Conc', 'S12B-All', 'S12B-Conc', 'S12C-All', 'S12C-Conc', 'S12D-All', 'S12D-Conc', 'S12-All', 'S12-Conc', 'S13A-All', 'S13A-Conc', 'S13B-All',
#           'S13C-All', 'S13D-All', 'S13E-All', 'S13F-All', 'S13G-All', 'S13H-All', 'S13J-All', 'S13K-All']
collist = ["#25262b", "#fa5252", "#4c6ef5","#228be6","#15aabf","#12b886", "#40c057","#82c91e","#fab005","#fd7e14"]
modelName = '205_UBSt_LBFr'
#shear_limit = (-15000, 15000, 5000)
#moment_limit = (-50000, 75000, 25000)
#torsion_limit = (-15000, 10000, 5000)
#axial_limit = (-10000, 25000, 5000)
shear_limit = (-50000, 50000, 10000)
moment_limit = (-6000000, 2000000, 1000000)
torsion_limit = (-2000000, 2000000, 500000)
axial_limit = (-50000, 250000, 50000)
limit_list = [shear_limit, shear_limit, axial_limit, moment_limit, moment_limit, torsion_limit]

def gen_limit_vals(limit):
    return np.arange(limit[0], limit[1] + limit[2], limit[2])

z_dict = {
    '025': 29.835,
    '024': 25.435,
    '023': 21.035,
    '022': 16.635,
    '021': 12.235,
    '020': 7.835,
    '019': 3.435,
    '017': -0.965,
    '016': -5.365,
    '015': -9.765,
    '013': -14.165,
    '012': -18.565,
    '010': -22.965,
    '008': -27.365,
    '006': -31.765,
    '005': -36.165,
    '004': -40.365,
    '003': -45.365,
    '002': -50.365,
    '001': -55.365,
    'G01': -60.365
}


def custom_ticks(x, pos):
    if x >= 1e6 or x <= -1e6:
        return f'{x * 1e-6:.0f}M'
    elif x >= 1e3 or x <= -1e3:
        return f'{x * 1e-3:.0f}k'
    else:
        return str(int(x))

def readFile(file, sheetName):
    """
    Read the specified sheet from the Excel file and return it as a DataFrame.
    """
    try:
        df = pd.read_excel(file, sheet_name=sheetName, usecols="A:M",header=1)
        # Drop 1st row
        df = df.drop(df.index[0])
        # make F1, F2, F3, M1, M2, M3 columns numeric
        df['F1'] = pd.to_numeric(df['F1'], errors='coerce')
        df['F2'] = pd.to_numeric(df['F2'], errors='coerce')
        df['F3'] = pd.to_numeric(df['F3'], errors='coerce')
        df['M1'] = pd.to_numeric(df['M1'], errors='coerce')
        df['M2'] = pd.to_numeric(df['M2'], errors='coerce')
        df['M3'] = pd.to_numeric(df['M3'], errors='coerce')
        #df['GlobalZ'] = pd.to_numeric(df['GlobalZ'], errors='coerce')

        # Cut name is the SectionCut column before "-"
        df['Cut'] = df['SectionCut'].str.split(' - ').str[0]
        # Get Z from the SectionCut column "Conc_Overall - Z=0.0m"
        df['GlobalZ'] = df['SectionCut'].str.extract(r'Z=([+-]?\d+\.?\d*)')[0]
        df['GlobalZ'] = pd.to_numeric(df['GlobalZ'], errors='coerce')
        print(df)
        return df
    except Exception as e:
        print(f"Error reading {sheetName}: {e}")
        return None

df = readFile(inFile, 'Section Cut Forces - Analysis')

# Plotting
pdfs = []
for cut in cutList:       
    # Create a new figure for each load case
    if '-Conc' in cut:
        plotList = ['F1', 'F2', 'F3', 'M2', 'M1', 'M3']
    else:
        plotList = ['F1', 'F2', 'F3']
    fig, ax = plt.subplots(figsize=(10, len(plotList)), nrows=int(len(plotList)/3), ncols=3)
    ax = ax.flatten()
    for i in range(len(plotList)):
        ax[i].set_title(titleList[i], fontsize = 8)
        ax[i].set_ylabel('Story', fontsize = 6)
        ax[i].set_xlabel(xLabelList[i], fontsize = 6)
        ax[i].xaxis.set_major_formatter(FuncFormatter(custom_ticks))
        ax[i].yaxis.set_major_formatter(FuncFormatter(custom_ticks))
        ax[i].tick_params(axis='both', which='major', labelsize=6)
        ax[i].set_ylim(-60.365, 29.835)
        ax[i].set_xticks(gen_limit_vals(limit_list[i]))
        ax[i].set_xlim(limit_list[i][0], limit_list[i][1])
        # Use z_dict to set the ticks
        ax2 = ax[i].twinx()
        ax2.set_yticks(list(z_dict.values()))
        ax2.set_yticklabels([int(it) for it in list(z_dict.values())], fontsize=6)
        ax2.set_ylabel('Height (m)', fontsize=6)
        
        ax[i].set_yticks(list(z_dict.values()))
        ax[i].set_yticklabels(list(z_dict.keys()), fontsize=6)
        ax[i].grid()
        
    # Plot each force component
    for id in range(len(loadCaseList)):
        loadCase = loadCaseList[id]
        loadCaseID = loadCaseName[id]

        # Filter the DataFrame for the current cut and load case
        filtered_df = df[(df['Cut'] == cut) & (df['OutputCase'] == loadCase)]
        filtered_df = filtered_df.dropna(subset=['GlobalZ'])  # Drop rows where GlobalZ is NaN

        if filtered_df.empty:
            print(f"No data found for {cut} and {loadCase}")
            continue

        #sort by GlobalZ
        filtered_df = filtered_df.sort_values(by='GlobalZ', ascending=True)

        for i, plot in enumerate(plotList):
            #Plot Min and Max in StepType
            max_value = filtered_df[(filtered_df['StepType'] == 'Max')]
            min_value = filtered_df[(filtered_df['StepType'] == 'Min')]
            if i == 0:            
                ax[i].plot(max_value[plot], max_value['GlobalZ'], label=loadCaseID, color=collist[id], linestyle='-', linewidth=1)
            ax[i].plot(max_value[plot], max_value['GlobalZ'], color=collist[id], linestyle='-', linewidth=1)
            ax[i].plot(min_value[plot], min_value['GlobalZ'], color=collist[id], linestyle='-', linewidth=1)

    # Create Legend for the entire figure on middle left side
    fig.legend(loc='center right', fontsize=8, title='Load Cases', title_fontsize = 10)
    fig.suptitle(f"Model {modelName} - Responses ({cut})", fontsize=14, fontweight='bold')

    # Save the plot
    outputFile = f"{filePath}\\{modelName}_{cut}.pdf"
    pdfs.append(outputFile)
    #tight_layout()
    plt.tight_layout()
    plt.subplots_adjust(right=0.85)  # Adjust the right side to make space for the legend
    plt.savefig(outputFile, dpi=300, bbox_inches='tight')
    plt.close()

import PyPDF2
import os

output_pdf = f"{filePath}\\{modelName}_All_SectionCuts_Overall.pdf"

# Create a PdfFileMerger object
pdf_merger = PyPDF2.PdfMerger()

# Loop through the list of PDFs and append them to the merger
for pdf in pdfs:
    with open(pdf, 'rb') as file:
        pdf_merger.append(file)

# Write the combined PDF to a file
with open(output_pdf, 'wb') as output_file:
    pdf_merger.write(output_file)

print(f"PDFs merged successfully into {output_pdf}")

# Optionally, remove the individual PDFs after merging (if needed)
for pdf in pdfs:
    os.remove(pdf)
    print(f"Removed individual PDF: {pdf}")