from readFile import *
import matplotlib.pyplot as plt
import pandas as pd
import pandasql as ps
import os
import numpy as np
import distinctipy

LABEL_LEGEND_FONT_SIZE = 8

def plotDispEnv(connection, saveLocation, **kwargs):
    whereClause = []
    # Read the groups we have to read from the database
    groupName = kwargs.get('groupName')
    if groupName:
        groupSQL = "','".join(groupName)
        query = f"SELECT GroupName, ObjectLabel FROM 'Groups 2 - Assignments' WHERE GroupName IN ('{groupSQL}') AND ObjectType = 'Joint'"
        selectedJoint = getData(connection, query=query)
        groupSQL = "','".join(selectedJoint['ObjectLabel'])
        queryGroup = f"Joint IN ('{groupSQL}')"
        whereClause.append(queryGroup)


    # Read the displacement data, read only the cases we need
    caseName = kwargs.get('caseName')
    if caseName:
        caseSQL = "','".join(caseName)
        queryCase = f"OutputCase IN ('{caseSQL}')"
        whereClause.append(queryCase)                               
        

    query = f"SELECT Joint, OutputCase, max(abs(U1)) as UX, max(abs(U2)) as UY FROM 'Joint Displacements'"

    if whereClause:
        query += f" WHERE {' AND '.join(whereClause)}"
    
    query += " GROUP BY Joint, OutputCase"

    dispData = getData(connection, query=query)

    heightData = getData(connection, tableName='Joint Coordinates')

    # Join dispData and selectedJoint
    query = """Select GroupName, dispData.Joint, OutputCase, CAST(Z AS FLOAT) AS Z_NUM, UX, UY 
    FROM dispData INNER JOIN selectedJoint 
        ON dispData.Joint = selectedJoint.ObjectLabel 
    INNER JOIN heightData ON dispData.Joint = heightData.Joint
    ORDER BY Z_NUM DESC"""
    dispData = ps.sqldf(query, locals())
    
    
    # plot the data, plot UX and UY in a 1X2 plot, the x axis is the value, the y axis is the height.
    # Case Name should be in the legend of the plot by color
    # Group Name should be in the legend as line style
    # The plot should be saved as a png file
    fig, ax = plt.subplots(1, 2, figsize=(10, 5))
    #lineStyleList = ['-', '--', '-.', ':']
    #colorList = ['r', 'g', 'b', 'k']
    colorList = distinctipy.get_colors(len(groupName), [(1,1,1)])
    lineStyleList = ['-', '--', '-.', ':']
    for c_i, caseI in enumerate(caseName):
        for g_i, group in enumerate(groupName):
            data = dispData[(dispData['OutputCase'] == caseI) & (dispData['GroupName'] == group)]
            ax[0].plot(data['UX'], data['Z_NUM'], label=f'{group}_{caseI}', linestyle=lineStyleList[c_i%4], color=colorList[g_i])
            ax[1].plot(data['UY'], data['Z_NUM'], label=f'{group}_{caseI}', linestyle=lineStyleList[c_i%4], color=colorList[g_i])
    ax[0].set_xlabel('UX (m)')
    ax[0].set_ylabel('Height (m)')
    ax[0].set_title('X Displacement')
    ax[0].set_xlim(0, 0.1)
    ax[0].legend(loc='lower right', fontsize=LABEL_LEGEND_FONT_SIZE)
    ax[1].set_xlabel('UY (m)')
    ax[1].set_ylabel('Height (m)')
    ax[1].set_title('Y Displacement')
    ax[1].set_xlim(0, 0.1)
    ax[1].legend(loc='lower right', fontsize=LABEL_LEGEND_FONT_SIZE)
    if 'elevationData' in kwargs:
        ax[0].set_yticks(kwargs['elevationData']['SAP2000Elev'])
        ax[0].set_yticklabels(kwargs['elevationData']['FloorLabel'])
        ax[1].set_yticks(kwargs['elevationData']['SAP2000Elev'])
        ax[1].set_yticklabels(kwargs['elevationData']['FloorLabel'])
        ax[0].set_ylim(kwargs['elevationData']['SAP2000Elev'].iloc[-1], kwargs['elevationData']['SAP2000Elev'].iloc[0])
        ax[1].set_ylim(kwargs['elevationData']['SAP2000Elev'].iloc[-1], kwargs['elevationData']['SAP2000Elev'].iloc[0])
    plt.tight_layout()
    plt.savefig(saveLocation + f'DispPlot_{caseName[0]}.png', dpi = 300)

    pass


class Drifts:
    def __init__(self, inputFile, outFolder, objectType, Dmax, Dlim, Hmin, Hmax):
        self.analysisConn = connectDB(inputFile) 
        self.outFolder = outFolder
        inputLoc = os.path.dirname(inputFile)
        heightFile = inputLoc + '\\FloorElevations.xlsx'
        heightConnection = connectDB(heightFile)
        self.heightData = getData(heightConnection, tableName='Floor Elevations')
        self.objectType = objectType
        self.Dmax = Dmax
        self.Dlim = Dlim
        self.Hmin = Hmin
        self.Hmax = Hmax

    def getElements(self, groupName):
        #print(f'Getting elements for {groupName}')
        if self.objectType == 'Links':
            query = f"""
            SELECT ObjectLabel, MIN(CAST(C1.Z AS FLOAT),CAST(C2.Z AS FLOAT)) AS Zmin, MAX(CAST(C1.Z AS FLOAT),CAST(C2.Z AS FLOAT)) AS Zmax
            FROM 'Groups 2 - Assignments' AS G 
            INNER JOIN 'Connectivity - Link' AS L ON ObjectLabel = Link
            INNER JOIN 'Joint Coordinates' AS C1 ON JointI = C1.Joint
            INNER JOIN 'Joint Coordinates' AS C2 ON JointJ = C2.Joint
            WHERE GroupName = '{groupName}' AND ObjectType = 'Link'
            ORDER BY Zmax DESC"""
        else:
            query = f"""
            SELECT ObjectLabel, CAST(Z AS FLOAT) AS Zmax
            FROM 'Groups 2 - Assignments' AS G INNER JOIN 'Joint Coordinates' AS C 
            ON ObjectLabel = Joint
            WHERE GroupName = '{groupName}' AND ObjectType = 'Joint'
            ORDER BY Zmax DESC"""
        return getData(self.analysisConn, query=query)

    
    def getSingleDrift(self, elementList, caseName, height, caseType='Env'):    
        if caseType == 'Env':
            query = f"""
            SELECT max(abs(U1)) as UX, max(abs(U2)) as UY 
            FROM 'Joint Displacements' 
            WHERE Joint ='{elementList[0]}' AND OutputCase = '{caseName}'
            """
            DispUp = getData(self.analysisConn, query=query)
            query = f"""
            SELECT max(abs(U1)) as UX, max(abs(U2)) as UY
            FROM 'Joint Displacements' 
            WHERE Joint ='{elementList[1]}' AND OutputCase = '{caseName}'
            """
            DispDown = getData(self.analysisConn, query=query)
            driftX, DriftY = (DispUp['UX'] - DispDown['UX'])/height, (DispUp['UY'] - DispDown['UY'])/height
            driftX = driftX.iloc[0]
            DriftY = DriftY.iloc[0]
            return driftX, DriftY
            #print(f'DriftX: {driftX.iloc[0]}, DriftY: {DriftY.iloc[0]} for Joint {elementList[0]} and case {caseName}')
        elif caseType == 'TH':
            query = f"""
            SELECT CAST(StepNum AS FLOAT) Steps, U1, U2 
            FROM 'Joint Displacements' 
            WHERE Joint ='{elementList[0]}' AND OutputCase = '{caseName}'
            """
            DispUp = getData(self.analysisConn, query=query)
            query = f"""
            SELECT CAST(StepNum AS FLOAT) Steps, U1, U2 
            FROM 'Joint Displacements' 
            WHERE Joint ='{elementList[1]}' AND OutputCase = '{caseName}'
            """
            DispDown = getData(self.analysisConn, query=query)

            query = f"""
            SELECT max(abs(DispUp.U1-DispDown.U1))/{height} as D2, max(abs(DispUp.U2-DispDown.U2))/{height} as D3
            from DispUp INNER JOIN DispDown ON DispUp.Steps = DispDown.Steps
            """
            driftAll = ps.sqldf(query, locals())
            return driftAll['D2'].iloc[0], driftAll['D3'].iloc[0]
            

    def getDrift(self, groupName, caseName, caseType='Env'):
        elementList = self.getElements(groupName)
        #print('Elements found!')
        #print(elementList)
        if self.objectType == 'Links':
            if caseType == 'Env':
                query = f"""
                SELECT Link, max(abs(U2)) as D2, max(abs(U3)) as D3 
                FROM 'Element Deformations - Links'
                WHERE OutputCase = '{caseName}'
                GROUP BY Link
                """
                driftData = getData(self.analysisConn, query=query)
                query = f"""
                SELECT Link, Zmax, D2/(Zmax-Zmin) as D2, D3/(Zmax-Zmin) as D3
                FROM elementList INNER JOIN driftData ON ObjectLabel = Link
                ORDER BY Zmax DESC
                """
                driftData = ps.sqldf(query, locals())
                #print("Drift Data")
                #print(driftData)
                return driftData

        elif self.objectType == 'Joints':
            elementList['D2'] = 0.0
            elementList['D3'] = 0.0
            for i in range(len(elementList)-1):
                height = elementList['Zmax'][i] - elementList['Zmax'][i+1]
                if caseType == 'Env':
                    elementList.loc[i, 'D2'], elementList.loc[i, 'D3'] = \
                        self.getSingleDrift([elementList['ObjectLabel'][i], elementList['ObjectLabel'][i+1]], caseName, height, caseType)
                else:
                    elementList.loc[i, 'D2'], elementList.loc[i, 'D3'] = \
                        self.getSingleDrift([elementList['ObjectLabel'][i], elementList['ObjectLabel'][i+1]], caseName, height, caseType)
            return elementList
    
    def getDriftPlot(self, groupList, caseList, caseType='Env'):
        #colList = distinctipy.get_colors(len(caseList), [(1,1,1)])
        colList = ['#1f77b4','#ff7f0e']
        allData = pd.DataFrame()
        for group in groupList:
            fig, ax = plt.subplots(1, 2, figsize=(10, 5))
            ax[0].set_title(f'{group} (D2)')
            ax[1].set_title(f'{group} (D3)')
            for i, caseName in enumerate(caseList):
                driftData = self.getDrift(group, caseName, caseType)
                driftData['Case'] = caseName
                driftData['Group'] = group
                allData = pd.concat([allData, driftData], ignore_index=True)
                ax[0].step(driftData['D2'], driftData['Zmax'], color = colList[i], marker = '.', label=caseName)
                ax[1].step(driftData['D3'], driftData['Zmax'], color = colList[i], marker = '.', label=caseName)
            for i in range(2):
                ax[i].set_xlim(0, self.Dmax)
                # set y ticks
                ax[i].set_yticks(self.heightData['SAP2000Elev'])
                ax[i].set_yticklabels(self.heightData['FloorLabel'])
                ax[i].vlines(self.Dlim, self.Hmin, self.Hmax, linestyle='--', color = 'red', linewidth=1.5, label='SLE Limit')
                ax[i].set_ylim(self.Hmin, self.Hmax)

                # show as percentage
                ax[i].set_xticks(np.arange(0, self.Dmax+0.001, 0.001))
                ax[i].set_xticklabels(['{:.1f}%'.format(x*100) for x in ax[i].get_xticks()])
                ax[i].tick_params(axis='both', labelsize=LABEL_LEGEND_FONT_SIZE)
                ax[i].set_xlabel('Drift (%)')
                ax[i].set_ylabel('Story')
                ax[i].legend(loc='lower right', fontsize=LABEL_LEGEND_FONT_SIZE)
                ax[i].grid(which='both', linestyle='--', linewidth=0.5)
            plt.tight_layout()
            #Create the folder if it does not exist
            if not os.path.exists(self.outFolder + f'\\DRIFTS'):
                os.makedirs(self.outFolder + f'\\DRIFTS')
            plt.savefig(self.outFolder + f'\\DRIFTS\\DriftPlot_{group}.png', dpi = 300)
            plt.close()
            #reorder the columns
            if self.objectType == 'Joints':
                allData = allData[['Group', 'Case', 'ObjectLabel', 'Zmax', 'D2', 'D3']]
            else:
                allData = allData[['Group', 'Case', 'Link', 'Zmax', 'D2', 'D3']]
        return allData

    def outputDrifts(self, groupList, caseList, caseType='Env'):
        allData = self.getDriftPlot(groupList, caseList, caseType)
        allData.to_excel(self.outFolder + '\\DRIFTS\\DriftData.xlsx', index=False)
        return allData

#filePath = r'C:\\Users\\abindal\\OneDrive - Nabih Youssef & Associates\\Documents\\00_Projects\\06_The Vault\\17JuneModels\\Part 302\\Displacement Study.xlsx'
#saveLocation = r'C:\\Users\\abindal\\OneDrive - Nabih Youssef & Associates\\Documents\\00_Projects\\06_The Vault\\17JuneModels\\Part 302\\'
#resultFile = connectDB(filePath)
#plotDispEnv(resultFile, groupName=['JointLine01', 'JointLine02'], caseName=['MCEr-Disp-GM11-HorOnly', 'MCEr-Disp-GM11-VertOnly'], saveLocation=saveLocation)

"""
filePath = r'C:\\Users\\abindal\\OneDrive - Nabih Youssef & Associates\\Documents\\00_Projects\\06_The Vault\\20240624 Models\\305\\JointDisplacement_305.xlsx'
saveLocation = r'C:\\Users\\abindal\\OneDrive - Nabih Youssef & Associates\\Documents\\00_Projects\\06_The Vault\\20240624 Models\\305\\'
driftObj = Drifts(filePath, saveLocation)
groupList = ['S12A_DRIFT', 'S12B_DRIFT', 'S12C_DRIFT', 'S12D_DRIFT', 'S12_DRIFT', 
             'S13A_DRIFT','S13B_DRIFT','S13C_DRIFT','S13D_DRIFT','S13E_DRIFT',
             'S13F_DRIFT','S13G_DRIFT','S13H_DRIFT','S13J_DRIFT','S13K_DRIFT']
caseList = ['SLE-X', 'SLE-Y']
driftObj.getDriftPlot(groupList, caseList, caseType='Env')

filePath = r'C:\\Users\\abindal\\OneDrive - Nabih Youssef & Associates\\Documents\\00_Projects\\06_The Vault\\20240624 Models\\302\\JointDisplacement_302_TH.xlsx'
saveLocation = r'C:\\Users\\abindal\\OneDrive - Nabih Youssef & Associates\\Documents\\00_Projects\\06_The Vault\\20240624 Models\\302\\'
driftObj = Drifts(filePath, saveLocation)
groupList = ['S2_DRIFT']
caseList = ['MCEr-Disp-GM11-HorOnly']
driftObj.getDriftPlot(groupList, caseList, caseType='TH')
"""
# filePath = r'C:\\Users\\abindal\\OneDrive - Nabih Youssef & Associates\\Documents\\00_Projects\\06_The Vault\\20240715 Models\\305\\20240715_LinkDeformation_305.xlsx'
# saveLocation = r'C:\\Users\\abindal\\OneDrive - Nabih Youssef & Associates\\Documents\\00_Projects\\06_The Vault\\20240715 Models\\305\\'
# driftObj = Drifts(filePath, saveLocation, objectType='Links', Dmax=0.011, Dlim=0.004, Hmin=-60.365, Hmax=29.835)
# groupList = ['Drift_S12A', 'Drift_S12B', 'Drift_S12C', 'Drift_S13D', 'Drift_S12', 
#              'Drift_S13A', 'Drift_S13B', 'Drift_S13C', 'Drift_S13D', 'Drift_S13E', 
#              'Drift_S13F', 'Drift_S13G', 'Drift_S13H', 'Drift_S13J', 'Drift_S13K']
# #groupList = ['S12B_DRIFT']

# caseList = ['SLE-X', 'SLE-Y']
# driftObj.outputDrifts(groupList, caseList, caseType='Env')


filePath = r'C:\\Users\\abindal\\OneDrive - Nabih Youssef & Associates\\Documents\\00_Projects\\06_The Vault\\20240715 Models\\305\\20240715_ResponseAll_Pin_305.xlsx'
saveLocation = r'C:\\Users\\abindal\\OneDrive - Nabih Youssef & Associates\\Documents\\00_Projects\\06_The Vault\\20240715 Models\\305\\'
resultFile = connectDB(filePath)
inputLoc = os.path.dirname(filePath)
heightFile = inputLoc + '\\FloorElevations.xlsx'
heightConnection = connectDB(heightFile)
elevationData = getData(heightConnection, tableName='Floor Elevations')
plotDispEnv(resultFile, groupName=['Disp_S12A', 'Disp_S12B', 'Disp_S12C', 'Disp_S13D', 'Disp_S12', 
             'Disp_S13A', 'Disp_S13B', 'Disp_S13C', 'Disp_S13D', 'Disp_S13E', 
             'Disp_S13F', 'Disp_S13G', 'Disp_S13H', 'Disp_S13J', 'Disp_S13K'], 
            caseName=['SLE-Y'], saveLocation=saveLocation, elevationData=elevationData)
