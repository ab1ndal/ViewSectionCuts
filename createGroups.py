from utils.readFile import *
import pandasql as ps
import pandas as pd


filePath = r'C:\\Users\\abindal\\OneDrive - Nabih Youssef & Associates\\Documents\\00_Projects\\06_The Vault\\20240624 Models\\305\\'
fileName = 'Connectivity_305.xlsx'
connections = connectDB(filePath + fileName)

query = """
SELECT Frame, JointI, JointJ, 
       ROUND(J1.XorR,2) AS Xi, ROUND(J1.Y,2) AS Yi, ROUND(J1.Z,3) AS Zi, 
       ROUND(J2.XorR,2) AS Xj, ROUND(J2.Y,2) AS Yj, ROUND(J2.Z,3) AS Zj 
FROM "Connectivity - Frame" 
INNER JOIN "Joint Coordinates" AS J1 ON JointI = J1.Joint
INNER JOIN "Joint Coordinates" AS J2 ON JointJ = J2.Joint
"""
allFrame = getData(connections, query=query)

query = 'SELECT * FROM allFrame WHERE Xi = Xj and Yi = Yj and ABS(Zi - Zj) > 1'
allColumn = ps.sqldf(query, locals())

print(allColumn.head())

query = 'SELECT * FROM allFrame WHERE ABS(Zi-Zj) > 1  AND Frame NOT IN (SELECT Frame FROM allColumn)'
allBrace = ps.sqldf(query, locals())
print(allBrace.head())

def createGroups(dataframe, groupName, colorName): 
    query = f"""
    SELECT '{groupName}' AS GroupName, 'Frame' AS ObjectType, Frame AS ObjectLabel
    FROM dataframe
    UNION
    SELECT '{groupName}' AS GroupName, 'Joint' AS ObjectType, JointI AS ObjectLabel
    FROM dataframe
    UNION
    SELECT '{groupName}' AS GroupName, 'Joint' AS ObjectType, JointJ AS ObjectLabel
    FROM dataframe
    """
    group2 = ps.sqldf(query, locals())

    group1 = pd.DataFrame({'GroupName': [groupName], 'Selection': 'Yes', 'SectionCut': 'Yes', 
                           'Steel':'No',	'Concrete': 'No',	'Aluminum': 'No',	'ColdFormed': 'No',	
                           'Stage': 'No',	'Bridge': 'No',	'AutoSeismic': 'No',	'AutoWind': 'No',	
                           'SelDesSteel': 'No',	'SelDesAlum': 'No',	'SelDesCold': 'No',	'MassWeight': 'Yes',	
                           'Color': [colorName]})
    return group1, group2

# Create empty groups and append the data
group1 = pd.DataFrame()
group2 = pd.DataFrame()

g1, g2 = createGroups(allBrace, 'AllBrace', 'blue')
group1 = pd.concat([group1, g1], ignore_index=True)
group2 = pd.concat([group2, g2], ignore_index=True)

g1, g2 = createGroups(allColumn, 'AllColumn', 'red')
group1 = pd.concat([group1, g1], ignore_index=True)
group2 = pd.concat([group2, g2], ignore_index=True)

# Save the dataframe into a new excel file groups should be in separate sheets
with pd.ExcelWriter(filePath + 'Groups.xlsx') as writer:
    group1.to_excel(writer, sheet_name='Groups 1 - Definitions', index=False)
    group2.to_excel(writer, sheet_name='Groups 2 - Assignments', index=False)