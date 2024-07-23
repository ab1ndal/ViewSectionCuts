from utils.readFile import *
import pandasql as ps
import pandas as pd

inputFileLoc = r"C:\\Users\\abindal\\OneDrive - Nabih Youssef & Associates\\Documents\\00_Projects\\06_The Vault\\20240715 Models\\305\\"
inputFile = inputFileLoc + "20240715_GenDispDefn_305_Seq.xlsx"

gridList = ['S12A', 'S12B', 'S12C', 'S12D', 'S12', 
            'S13A', 'S13B', 'S13C', 'S13D', 'S13E',
            'S13F', 'S13G', 'S13H', 'S13J', 'S13K']
gridListNew = [f"'Drift_Top_{x}', 'Drift_Bot_{x}'" for x in gridList]
gridSQL = ",".join(gridListNew)

query = f"""
SELECT GroupName, ObjectLabel
FROM "Groups 2 - Assignments" 
WHERE ObjectType = "Joint"
AND GroupName IN ({gridSQL})
"""
connection = connectDB(inputFile)
groupData = getData(connection, query=query)

coordList = getData(connection, query = 'Select Joint, CAST(Z AS FLOAT) AS Z from "Joint Coordinates"')

query = """
Select GroupName, ObjectLabel, Z 
from groupData inner join coordList 
on ObjectLabel = Joint
order by GroupName ASC, Z DESC
"""
data = ps.sqldf(query, locals())

driftPoints = pd.DataFrame(columns=['Grid', 'TopJoint', 'BotJoint', 'TopZ', 'BotZ', 'Height'])

for g in gridList:
    print(f'Grid: {g}')
    topPoint = data[data['GroupName'] == f'Drift_Top_{g}'].reset_index(drop=True)
    botPoint = data[data['GroupName'] == f'Drift_Bot_{g}'].reset_index(drop=True)
    # merge the two dataframes, with renamed columns, the order should be in as in the original dataframes
    merged = pd.concat([topPoint, botPoint], axis=1)
    merged.columns = ['TopGroupName', 'TopJoint', 'TopZ', 'BotGroupName', 'BotJoint', 'BotZ']
    #drop columns that are not needed
    merged.drop(['TopGroupName', 'BotGroupName'], axis=1, inplace=True)
    merged['Height'] = merged['TopZ'] - merged['BotZ']
    merged['Grid'] = g
    #reorder columns
    merged = merged[['Grid', 'TopJoint', 'BotJoint', 'TopZ', 'BotZ', 'Height']]
    #append to the driftPoints dataframe
    driftPoints = pd.concat([driftPoints, merged], ignore_index=True)

genDisp = pd.DataFrame(columns=['GenDispl', 'Joint', 'U1SF', 'U2SF', 'U3SF', 'R1SF', 'R2SF', 'R3SF'])

for index, row in driftPoints.iterrows():
    newRows = pd.DataFrame([
        [f"{row['Grid']}_Z={round(row['TopZ'],1)}m_U1", row['TopJoint'],  1,  0, 0, 0, 0, 0],
        [f"{row['Grid']}_Z={round(row['TopZ'],1)}m_U1", row['BotJoint'], -1,  0, 0, 0, 0, 0],
        [f"{row['Grid']}_Z={round(row['TopZ'],1)}m_U2", row['TopJoint'],  0,  1, 0, 0, 0, 0],
        [f"{row['Grid']}_Z={round(row['TopZ'],1)}m_U2", row['BotJoint'],  0, -1, 0, 0, 0, 0]
    ], columns = genDisp.columns)
    genDisp = pd.concat([genDisp, newRows], ignore_index=True)
print(genDisp)

# Save the dataframes to excel
with pd.ExcelWriter(inputFileLoc+ 'outputGenDisp.xlsx') as writer:
    driftPoints.to_excel(writer, sheet_name='DriftPoints', index=False)
    genDisp.to_excel(writer, sheet_name='GenDisp', index=False)
