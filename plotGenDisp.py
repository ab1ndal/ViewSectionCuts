from utils.readFile import *
import pandasql as ps
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

inputFileLoc = r"C:\\Users\\abindal\\OneDrive - Nabih Youssef & Associates\\Documents\\00_Projects\\06_The Vault\\20240715 Models\\305\\"
inputFile = inputFileLoc + "20240715_GenDispForces_305_Seq.xlsx"

heightFile = inputFileLoc + '\\FloorElevations.xlsx'
heightConnection = connectDB(heightFile)
heightData = getData(heightConnection, tableName='Floor Elevations')

gridList = ['S12A', 'S12B', 'S12C', 'S12D', 'S12', 
            'S13A', 'S13B', 'S13C', 'S13D', 'S13E',
            'S13F', 'S13G', 'S13H', 'S13J', 'S13K']
GMList = ['SLE - 2% Damped - U1', 'SLE - 2% Damped - U2']
dispList = ['U1', 'U2']
LABEL_LEGEND_FONT_SIZE = 8
Dmax = 0.006
Hmin=-60.365
Hmax=29.835
Dlim=0.004

if not os.path.exists(inputFileLoc + f'\\DRIFTS'):
    os.makedirs(inputFileLoc + f'\\DRIFTS')

query = f"""
SELECT GenDispl, OutputCase, max(abs(Translation)) as Disp
FROM "Jt Displacements - Generalized"
GROUP BY GenDispl, OutputCase
"""
connection = connectDB(inputFile)
dispData = getData(connection, query=query)
jointData = getData(connection, query='SELECT Joint, Z FROM "Joint Coordinates"')
genDispDefn = getData(connection, query='SELECT GenDispl, Joint, U1SF, U2SF FROM "Gen Displ Defs 1 - Translation"')
genDispDefn['Loc'] = genDispDefn['U1SF'] + genDispDefn['U2SF']

compiledData = pd.DataFrame(columns=['GenDispl', 'OutputCase', 'Disp', 'TopJoint', 'TopZ', 'BotJoint', 'BotZ', 'Drift'])

# The name of the column GenDispl has the format <Grid Name>_Z=<Z>m_<U1/U2>
# Based on U1 or U2, Disp should be labeled as U1 or U2
colList = ['#1f77b4','#ff7f0e']
for g in gridList:
    print(f'Grid: {g}')
    fig, ax = plt.subplots(1,2, figsize=(10,5))
    ax[0].set_title(f'{g} - U1')
    ax[1].set_title(f'{g} - U2')
    for gm_i, gm in enumerate(GMList):
        print(f'GM: {gm}')
        for d_i, d in enumerate(dispList):
            print(f'Disp: {d}')
            selGrid = dispData[dispData['GenDispl'].str.contains(g+"_")][dispData['OutputCase'] == gm][dispData['GenDispl'].str.contains(d)]
            selGrid = selGrid.reset_index(drop=True)
            query = f"""
            SELECT selGrid.GenDispl, OutputCase, Disp, Gen1.Joint as TopJoint, CAST(J1.Z AS FLOAT) as TopZ, Gen2.Joint as BotJoint, CAST(J2.Z AS FLOAT) as BotZ
            FROM selGrid
            INNER JOIN genDispDefn as Gen1
            ON selGrid.GenDispl = Gen1.GenDispl AND Gen1.Loc = 1
            INNER JOIN genDispDefn as Gen2
            ON selGrid.GenDispl = Gen2.GenDispl AND Gen2.Loc = -1
            INNER JOIN jointData as J1
            ON Gen1.Joint = J1.Joint
            INNER JOIN jointData as J2
            ON Gen2.Joint = J2.Joint
            """
            finalData = ps.sqldf(query, locals())
            finalData['Drift'] = finalData['Disp']/(finalData['TopZ'] - finalData['BotZ'])
            ax[d_i].step(finalData['Drift'], finalData['TopZ'], label=gm, color = colList[gm_i], marker = '.')
            compiledData = pd.concat([compiledData, finalData], ignore_index=True)
            print(finalData)
    for i in range(2):
        ax[i].set_xlim(0, Dmax)
        ax[i].set_ylim(Hmin, Hmax)
        ax[i].vlines(Dlim, Hmin, Hmax, linestyle='--', color = 'red', linewidth=1.5, label='SLE Limit')
        ax[i].set_xticks(np.arange(0, Dmax+0.001, 0.001))
        ax[i].set_xticklabels(['{:.1f}%'.format(x*100) for x in ax[i].get_xticks()], fontsize=LABEL_LEGEND_FONT_SIZE)
        ax[i].set_yticks(heightData['SAP2000Elev'])
        ax[i].set_yticklabels(heightData['FloorLabel'], fontsize=LABEL_LEGEND_FONT_SIZE)
        ax[i].legend(loc='lower right', fontsize=LABEL_LEGEND_FONT_SIZE)
        ax[i].set_xlabel('Drift (%)')
        ax[i].set_ylabel('Story')
        ax[i].grid(which='both', linestyle='--', linewidth=0.5)
        secax_y = ax[i].secondary_yaxis('right')
        secax_y.set_yticks(heightData['SAP2000Elev'])
        secax_y.set_yticklabels([int(round(x,0)) for x in heightData['SAP2000Elev']], fontsize=LABEL_LEGEND_FONT_SIZE)
        secax_y.set_ylabel('Height (m)')
    plt.tight_layout()
    plt.savefig(inputFileLoc + f'\\DRIFTS\\{g}_Drift.png', dpi = 300)
    plt.close()

compiledData.to_excel(inputFileLoc + 'outputDrifts.xlsx', index=False)

