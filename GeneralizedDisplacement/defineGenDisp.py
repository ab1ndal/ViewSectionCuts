from utils.readFile import *
import pandasql as ps
import pandas as pd

# Requires file with following tables:
# 1. "Joint Coordinates" with columns Joint, X, Y, Z
# 2. "Groups 2 - Assignments" with columns GroupName, ObjectLabel, ObjectType


def groupListFromGrid(gridList, topSuffix, botSuffix):
    grid = gridList.split(',')
    groupList = [f"'{topSuffix}{x}', '{botSuffix}{x}'" for x in grid]
    groupListSQL = ",".join(groupList)
    query = f"""
        SELECT GroupName, ObjectLabel
        FROM "Groups 2 - Assignments" 
        WHERE ObjectType = "Joint"
        AND GroupName IN ({groupListSQL})
    """
    return query,grid

def defineGenDisp(connection, gridList, topSuffix, botSuffix):
    query, grid = groupListFromGrid(gridList, topSuffix, botSuffix)
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

    for g in grid:
        topPoint = data[data['GroupName'] == f'{topSuffix}{g}'].reset_index(drop=True)
        botPoint = data[data['GroupName'] == f'{botSuffix}{g}'].reset_index(drop=True)
        merged = pd.concat([topPoint, botPoint], axis=1)
        merged.columns = ['TopGroupName', 'TopJoint', 'TopZ', 'BotGroupName', 'BotJoint', 'BotZ']
        merged.drop(['TopGroupName', 'BotGroupName'], axis=1, inplace=True)
        merged['Height'] = merged['TopZ'] - merged['BotZ']
        merged['Grid'] = g
        merged = merged[['Grid', 'TopJoint', 'BotJoint', 'TopZ', 'BotZ', 'Height']]
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
    return [driftPoints, genDisp]
