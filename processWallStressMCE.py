import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
#plt.rcParams['text.usetex'] = True

######################################### INPUTS ######################################################
##### The following inputs are required to run the script: #####
# Excel file containing the wall properties (fc, fy, lw, tw, fce, fye)
# Excel file containing the section cut forces (F1, F2, F3, StepType, CaseType) in k-ft
#######################################################################################################
baseFile = '20250207_305_GapFriction_LB_MCE_WallStresses.xlsx'
wallProperties = 'Properties.xlsx'
wallList = ['S12A', 'S12B', 'S12C', 'S12D', 'S12', 'S13A', 'Avg']
#wallList = ['S12A']

sectionCutNames = 'S12A-Conc|S12B-Conc|S12C-Conc|S12D-Conc|S12-Conc|S13A-Conc'
#sectionCutNames = 'S12A-Conc'
Bgravity = 1
Bseismic = 1.35

# Toggle if you want to use Bseismic only
use_only_seismic = False
phi = 0.75
ModelName = '305-LB-Gap'
#ModelName = '305-UB-Control_FC3'  

# Name of the cases to be analyzed
# If you are getting ratios, the first two cases will be used to get the ratio
# 1st one should be Gravity Case
# 2nd one should be Seismic Only Case
tempCases = ['1.0D+0.5L', '1.3Ie*MCE,avg', 'MCE-GM01 (ENV)', 'MCE-GM02 (ENV)', 'MCE-GM03 (ENV)', 'MCE-GM04 (ENV)', 
             'MCE-GM05 (ENV)', 'MCE-GM06 (ENV)', 'MCE-GM07 (ENV)', 'MCE-GM08 (ENV)', 'MCE-GM09 (ENV)', 'MCE-GM10 (ENV)', 'MCE-GM11 (ENV)']
tempCaseName = ['Gravity', '1.3IeMCE,avg', 'Gravity+MCE01', 'Gravity+MCE02', 'Gravity+MCE03', 'Gravity+MCE04', 'Gravity+MCE05',
                'Gravity+MCE06', 'Gravity+MCE07', 'Gravity+MCE08', 'Gravity+MCE09', 'Gravity+MCE10', 'Gravity+MCE11']

#Get Ratio. If you don't want to compute ratios set this to False
getRatio = False

#tempCases = ['PushoverTest']
#tempCaseName = ['Push']

fileLoc = r'C:\\Users\\abindal\\OneDrive - Nabih Youssef & Associates\\Documents - The Vault\\Calculations\\2025.02.07 - Gap Friction Models Stage 3C\\Model Results\\305\\20250207_305_GapFriction_LB\\Wall Stresses\\'

########################################################################################################

if not os.path.exists(fileLoc):
    os.makedirs(fileLoc)

# Read the data from the excel file
properties = pd.read_excel(fileLoc + wallProperties, sheet_name='Sheet1', header=1).dropna()
print("Properties read")
# Reading section cut file
data = pd.read_excel(fileLoc + baseFile, sheet_name='Section Cut Forces - Analysis', header=1, usecols='A:G').dropna()
data = data.iloc[1:]
data = data[data['SectionCut'].str.contains(sectionCutNames)]
#print(data.head())
#print(data['SectionCut'].unique())
#Set the data types for F1 andf F2 to float
data['F1'] = data['F1'].astype(float).abs()
data['F2'] = data['F2'].astype(float).abs()
data['F3'] = data['F3'].astype(float)

data['Vdes'] = data['F2'].abs()/phi/Bgravity
#data['Vdes'] = data[['F1', 'F2']].abs().max(axis=1)/phi/Bgravity
if use_only_seismic:
    data['Vdes'] = data['Vdes']*Bgravity/Bseismic
else:
    data['Vdes'] = data.apply(lambda x: x['Vdes']*Bgravity/Bseismic if 'MCE' in x['CaseType'] else x['Vdes'], axis=1)
data['Vdes'] = data['Vdes'].round(0)

data.drop(columns=['F1', 'F2','StepType', 'CaseType'], inplace=True)

# max Vdes, group by SectionCut, OutputCase
maxVdes = data.groupby(['SectionCut', 'OutputCase']).max().reset_index()
# merge with properties
maxVdes = pd.merge(maxVdes, properties, left_on='SectionCut', right_on='Cut', how='inner')
maxVdes['sqrt_fc'] = maxVdes['fc']**0.5
maxVdes['StressRatio'] = maxVdes['Vdes']*1000/(maxVdes['lw']*maxVdes['tw']*maxVdes['sqrt_fc'])
maxVdes['StressRatio'] = maxVdes['StressRatio'].round(2)
maxVdes['AxialRatio'] = maxVdes['F3']*1000/(maxVdes['lw']*maxVdes['tw'])
maxVdes.drop(columns=['sqrt_fc', 'fc', 'fy', 'fye', 'lw', 'tw', 'fce', 'Cut', 'SectionCut', 'Vdes'], inplace=True)

print(maxVdes.head())

maxVdes_avg = maxVdes[['OutputCase', 'Z', 'StressRatio', 'AxialRatio']] \
    .groupby(['OutputCase', 'Z'])[['StressRatio', 'AxialRatio']].mean().reset_index()
maxVdes_avg['Wall'] = 'Avg'
print(maxVdes_avg.head())
maxVdes = pd.concat([maxVdes, maxVdes_avg], ignore_index=True)
maxVdes.to_excel(f'{fileLoc}{ModelName}_VdesRatios.xlsx', index=False)

def get_shear(loadCase, wallName):
    shear = maxVdes[maxVdes['Wall'] == wallName].reset_index(drop=True)
    shear = shear[shear['OutputCase'] == loadCase].reset_index(drop=True)
    return shear

# Plot a heat map of the stress ratio for the walls
# There are two options, per wall and per load case
def plot_heatmap(**kwargs):
    wallNames = kwargs['wallNames']
    loadCases = kwargs['loadCases']
    caseName = kwargs['caseName']
    ModelType = kwargs['ModelType']
    plotType = kwargs['plotType']

    if 'plotWalls' in kwargs:
        plotWalls = kwargs['plotWalls']
        if plotWalls:
            # Get the data for the load case
            # Create a new load case with Z, Wall, StressRatio
            stressRatio = pd.DataFrame()
            
            for wall in wallNames:
                shear = get_shear(loadCases, wall)
                stressRatio = pd.concat([stressRatio, shear[['Z', 'Wall', plotType]]], ignore_index=True)
            maxValue = stressRatio[plotType].max()

            # Keep the ordering of the walls in the pivot table
            stress_pivot = stressRatio.pivot(index='Z', columns='Wall', values=plotType)
            stress_pivot = stress_pivot.reindex(columns=wallNames)

            print(stress_pivot)

            # Plot the heat map
            fig, ax = plt.subplots(figsize=(5,10))
            if plotType == 'StressRatio':
                vmax = 10
                title_suffix = r"[V/(\phi B*l_w*t_w*sqrt(f'_{ce}))]"
            else:
                vmax = 2000
                title_suffix = r"[P/(l_w*t_w), psi]"
            sns.heatmap(stress_pivot, cmap='RdYlGn_r', ax=ax, cbar = True, vmin=0, vmax=vmax)
            ax.set_xlabel('Wall')
            ax.set_ylabel('Z (m)')
            ax.invert_yaxis()
            ax.set_yticks([i+0.5 for i in range(len(stress_pivot.index))])
            ax.set_yticklabels(stress_pivot.index)
            # set tick font size
            ax.tick_params(axis='y', labelsize=5)

            ax.set_title(rf'{caseName} ({ModelType})${title_suffix}$', fontsize=10)
            plt.tight_layout()
            # Show values on the heat map
            for i in range(len(stress_pivot.index)):
                for j in range(len(stress_pivot.columns)):
                    # if not NaN
                    if not pd.isna(stress_pivot.iloc[i,j]):
                        ax.text(j+0.5, i+0.5, round(stress_pivot.iloc[i,j],1), ha='center', 
                                va='center', color='black', fontsize=5)
            max_position = stress_pivot.stack().idxmax()
            max_row, max_col = max_position
            ax.add_patch(plt.Rectangle((wallNames.index(max_col), stress_pivot.index.get_loc(max_row)), 
                                       1, 1, fill=False, edgecolor='black', lw=1.5))
            # Create a PDF file with the heat map
            plt.savefig(f'{fileLoc}{caseName}_{plotType}.pdf', format='pdf', dpi=300)
            plt.close()
            return maxValue

# A similar function as above except we are plotting ratio of '1.3Ie*MCE,avg' to '(1.2D+Lexp)+0.5T,env'      
def plotRatioMap(**kwargs):
    wallNames = kwargs['wallNames']
    loadCases = kwargs['loadCases']
    caseName = kwargs['caseName']
    ModelType = kwargs['ModelType']
    plotType = kwargs['plotType']

    if 'plotWalls' in kwargs:
        plotWalls = kwargs['plotWalls']
        if plotWalls:
            # Get the data for the load case
            # Create a new load case with Z, Wall, StressRatio
            stressRatio = pd.DataFrame()
            
            for wall in wallNames:
                shear = get_shear(loadCases[0], wall)
                shear2 = get_shear(loadCases[1], wall)
                shear['StressRatio2'] = shear2[plotType]
                shear['StressRatio'] = shear[plotType]/shear['StressRatio2']
                shear.drop(columns=['StressRatio2'], inplace=True)
                stressRatio = pd.concat([stressRatio, shear[['Z', 'Wall', plotType]]], ignore_index=True)
            maxValue = stressRatio[plotType].max()

            # Keep the ordering of the walls in the pivot table
            stress_pivot = stressRatio.pivot(index='Z', columns='Wall', values=plotType)
            stress_pivot = stress_pivot.reindex(columns=wallNames)

            # Plot the heat map
            fig, ax = plt.subplots(figsize=(5,10))
            sns.heatmap(stress_pivot, cmap='RdYlGn_r', ax=ax, cbar = True, vmin=0, vmax=0.5)
            ax.set_xlabel('Wall')
            ax.set_ylabel('Z (m)')
            ax.invert_yaxis()
            # show all labels on y axis
            # offset tic locations up by 0..5
            ax.set_yticks([i+0.5 for i in range(len(stress_pivot.index))])
            ax.set_yticklabels(stress_pivot.index)
            # set tick font size
            ax.tick_params(axis='y', labelsize=5)

            ax.set_title(f'Gravity/Seismic Ratio ({ModelType})')
            plt.tight_layout()
            # Show values on the heat map
            for i in range(len(stress_pivot.index)):
                for j in range(len(stress_pivot.columns)):
                    # if not NaN
                    if not pd.isna(stress_pivot.iloc[i,j]):
                        ax.text(j+0.5, i+0.5, round(stress_pivot.iloc[i,j],2), ha='center', 
                                va='center', color='black', fontsize=5)
            max_position = stress_pivot.stack().idxmax()
            max_row, max_col = max_position
            ax.add_patch(plt.Rectangle((wallNames.index(max_col), stress_pivot.index.get_loc(max_row)), 
                                       1, 1, fill=False, edgecolor='black', lw=1.5))
            # Create a PDF file with the heat map
            plt.savefig(f'{fileLoc}{caseName}_{plotType}.pdf', format='pdf', dpi=300)
            plt.close()
            return maxValue





maxVals = []

for case in tempCases:
    #print(f'Processing {case}')
    maxVals.append(plot_heatmap(wallNames=wallList, 
                                loadCases=case, 
                                plotWalls=True,
                                caseName = tempCaseName[tempCases.index(case)],
                                ModelType = ModelName,
                                plotType = 'StressRatio'))
    maxVals.append(plot_heatmap(wallNames=wallList, 
                                loadCases=case, 
                                plotWalls=True,
                                caseName = tempCaseName[tempCases.index(case)],
                                ModelType = ModelName,
                                plotType = 'AxialRatio'))

# Plot the ratio of the two cases
if getRatio:
    #print(f'Processing Ratio of Shears')
    plotRatioMap(wallNames=wallList[:-1], 
                loadCases=[tempCases[0], tempCases[1]], 
                plotWalls=True,
                caseName = f'{ModelName}_Ratio of Shears',
                ModelType = ModelName,
                plotType = 'StressRatio')
    plotRatioMap(wallNames=wallList[:-1], 
                loadCases=[tempCases[0], tempCases[1]], 
                plotWalls=True,
                caseName = f'{ModelName}_Ratio of Axials',
                ModelType = ModelName,
                plotType = 'AxialRatio')
    

# plot the max values
print(maxVals)

#Combine all the heatmaps into a single pdf
from PyPDF2 import PdfMerger
pdfs = [f'{fileLoc}{case}_StressRatio.pdf' for case in tempCaseName]
pdfs.extend([f'{fileLoc}{case}_AxialRatio.pdf' for case in tempCaseName])
merger = PdfMerger()
for pdf in pdfs:
    merger.append(pdf)
if getRatio:
    merger.append(f'{fileLoc}{ModelName}_Ratio of Shears_StressRatio.pdf')
    #merger.append(f'{fileLoc}{ModelName}_Ratio of Axials_AxialRatio.pdf')
merger.write(f"{fileLoc}{ModelName}_Wall Stress Study.pdf")
merger.close()

# Delete the individual files
for pdf in pdfs:
    os.remove(pdf)
if getRatio:
    os.remove(f'{fileLoc}{ModelName}_Ratio of Shears_StressRatio.pdf')
    os.remove(f'{fileLoc}{ModelName}_Ratio of Axials_AxialRatio.pdf')








