import pandas as pd
from pandasql import sqldf
from pathlib import Path

def read_file(file_path, sheet_name, colNames=None):
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=1)
        df = df[1:]
        if colNames:
            df=df[colNames]
        return df
    except Exception as e:
        print(e)
        return None
    
# Read Group Information
modelName = '305'
raw_path = r"C:\Users\abindal\Downloads"
path = Path(raw_path)
fileName = "20250602_305_LB_Groups.xlsx"
sheet = 'Groups 2 - Assignments'
groupInfo = read_file(path / fileName, sheet)
query = "Select GroupName, ObjectLabel as Joints "\
        "from groupInfo where ObjectType = 'Joint' "\
        "and GroupName GLOB 'Support Group 0[0-9]'"
jointGroups = sqldf(query, locals())
print(jointGroups.head())
print(jointGroups.GroupName.unique())

# Seperate out group info based on support group
# Create a dictionary with support group as key and list of elements as value
jointDict = {}
for group in jointGroups.GroupName.unique():
    query = "Select Joints from jointGroups where GroupName = '{}'".format(group)
    joints = sqldf(query, locals())
    jointDict[group] = joints.Joints.values

# A list of control points for each support group
if modelName == '305':
    # Model 305 has 8 support groups
    contlPoints = {'Support Group 01': 9329, 
                   'Support Group 02': 14539, 
                   'Support Group 03': 14472, 
                   'Support Group 04': 14278,
                   'Support Group 05': 14586,
                   'Support Group 06': 14579,
                   'Support Group 07': 14578,
                   'Support Group 08': 13351}

elif modelName == '205':
    # Model 205 has 8 support groups
    contlPoints = {'Support Group 01': 3608, 
                   'Support Group 02': 3609, 
                   'Support Group 03': 3647, 
                   'Support Group 04': 3662,
                   'Support Group 05': 3753,
                   'Support Group 06': 3820,
                   'Support Group 07': 3830,
                   'Support Group 08': 3858}

# For each support group, for each element in the list, add entry into a dataframe for transational displacements compared to control point.
genDisp = pd.DataFrame(columns=['GenDispl', 'Joint', 'U1SF', 'U2SF', 'U3SF', 'R1SF', 'R2SF', 'R3SF'])
data = []
for group in jointDict.keys():
    for joint in jointDict[group]:
        data.extend([
            {'GenDispl': f'SP{group[-2:]}-{joint}-U1', 'Joint': joint,              'U1SF':  1, 'U2SF':  0, 'U3SF':  0, 'R1SF': 0, 'R2SF': 0, 'R3SF': 0},
            {'GenDispl': f'SP{group[-2:]}-{joint}-U1', 'Joint': contlPoints[group], 'U1SF': -1, 'U2SF':  0, 'U3SF':  0, 'R1SF': 0, 'R2SF': 0, 'R3SF': 0},
            {'GenDispl': f'SP{group[-2:]}-{joint}-U2', 'Joint': joint,              'U1SF':  0, 'U2SF':  1, 'U3SF':  0, 'R1SF': 0, 'R2SF': 0, 'R3SF': 0},
            {'GenDispl': f'SP{group[-2:]}-{joint}-U2', 'Joint': contlPoints[group], 'U1SF':  0, 'U2SF': -1, 'U3SF':  0, 'R1SF': 0, 'R2SF': 0, 'R3SF': 0},
            {'GenDispl': f'SP{group[-2:]}-{joint}-U3', 'Joint': joint,              'U1SF':  0, 'U2SF':  0, 'U3SF':  1, 'R1SF': 0, 'R2SF': 0, 'R3SF': 0},
            {'GenDispl': f'SP{group[-2:]}-{joint}-U3', 'Joint': contlPoints[group], 'U1SF':  0, 'U2SF':  0, 'U3SF': -1, 'R1SF': 0, 'R2SF': 0, 'R3SF': 0}])

genDisp = pd.concat([genDisp, pd.DataFrame(data)], ignore_index=True)
        
# Export the dataframe to a excel file
genDisp.to_excel(path / f'{modelName}_General Displacements to import.xlsx', index=False)