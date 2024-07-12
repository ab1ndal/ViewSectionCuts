from readFile import *
import pandasql as ps
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


filePath = r'C:\\Users\\abindal\\OneDrive - Nabih Youssef & Associates\\Documents\\00_Projects\\06_The Vault\\20240624 Models\\305\\'
fileName = r'TorsionCheck_305.xlsx'

connections = connectDB(filePath + fileName)

groupName = 'TorsionGroup'

query = f"""
SELECT CAST(Z AS FLOAT) AS Z, OutputCase, max(CAST(U1 AS FLOAT)) as U1max, max(CAST(U2 AS FLOAT)) as U2max, avg(CAST(U1 AS FLOAT)) as U1avg, avg(CAST(U2 AS FLOAT)) as U2avg
FROM "Joint Displacements" AS D INNER JOIN "Joint Coordinates" AS C ON C.Joint = D.Joint
WHERE D.Joint IN (SELECT ObjectLabel FROM "Groups 2 - Assignments" WHERE GroupName = '{groupName}' AND ObjectType = 'Joint')
GROUP BY Z, OutputCase
ORDER BY Z DESC
"""
torsionInfo = getData(connections, query=query)
torsionInfo['A1'] = (torsionInfo['U1max']/1.2/torsionInfo['U1avg'])**2
torsionInfo['A2'] = (torsionInfo['U2max']/1.2/torsionInfo['U2avg'])**2
print(torsionInfo)

fig, ax = plt.subplots(1, 2, figsize=(10, 5))

for case in torsionInfo['OutputCase'].unique():
    data = torsionInfo[torsionInfo['OutputCase'] == case]
    ax[0].scatter(data['A1'], data['Z'], label=case)
    ax[1].scatter(data['A2'], data['Z'], label=case)
for i in range(2):
    ax[i].set_title(f'Amplification in A{i+1} direction')
    ax[i].set_xlabel('A1' if i == 0 else 'A2')
    ax[i].set_ylabel('Height (m)')
    ax[i].legend()
    ax[i].vlines(3, -40,-20, colors='r', linestyles='dashed')
    ax[i].vlines(1, -40,-20, colors='r', linestyles='dashed')
    ax[i].set_ylim(-40, -20)
    ax[i].set_xlim(0, 5)

plt.show()