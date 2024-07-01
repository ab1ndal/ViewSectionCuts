from scripts.readFile import *
import matplotlib.pyplot as plt
import pandas as pd
import pandasql as ps

LEGEND_FONT_SIZE = 6

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
    query = "Select GroupName, dispData.Joint, OutputCase, Z, UX, UY FROM dispData INNER JOIN selectedJoint ON dispData.Joint = selectedJoint.ObjectLabel INNER JOIN heightData ON dispData.Joint = heightData.Joint"
    dispData = ps.sqldf(query, locals())
    print(dispData.head(1))
    
    # plot the data, plot UX and UY in a 1X2 plot, the x axis is the value, the y axis is the height.
    # Case Name should be in the legend of the plot by color
    # Group Name should be in the legend as line style
    # The plot should be saved as a png file
    fig, ax = plt.subplots(1, 2, figsize=(10, 5))
    lineStyleList = ['-', '--', '-.', ':']
    colorList = ['r', 'g', 'b', 'k']
    for c_i, caseI in enumerate(caseName):
        for g_i, group in enumerate(groupName):
            data = dispData[(dispData['OutputCase'] == caseI) & (dispData['GroupName'] == group)]
            # Sort the data by height
            data = data.sort_values(by='Z')
            ax[0].plot(data['UX'], data['Z'], label=group+caseI, linestyle=lineStyleList[g_i], color=colorList[c_i])
            ax[1].plot(data['UY'], data['Z'], label=group+caseI, linestyle=lineStyleList[g_i], color=colorList[c_i])
    ax[0].set_xlabel('UX (m)')
    ax[0].set_ylabel('Height (m)')
    ax[0].set_title('X Displacement')
    ax[0].set_xlim(0, 0.12)
    ax[0].legend(loc='lower right', fontsize=LEGEND_FONT_SIZE)
    ax[1].set_xlabel('UY (m)')
    ax[1].set_ylabel('Height (m)')
    ax[1].set_title('Y Displacement')
    ax[1].set_xlim(0, 0.12)
    ax[1].legend(loc='lower right', fontsize=LEGEND_FONT_SIZE)
    plt.tight_layout()
    plt.savefig(saveLocation + 'DispPlot.png', dpi = 300)

    pass


filePath = r'C:\\Users\\abindal\\OneDrive - Nabih Youssef & Associates\\Documents\\00_Projects\\06_The Vault\\17JuneModels\\Part 302\\Displacement Study.xlsx'
saveLocation = r'C:\\Users\\abindal\\OneDrive - Nabih Youssef & Associates\\Documents\\00_Projects\\06_The Vault\\17JuneModels\\Part 302\\'
resultFile = connectDB(filePath)
plotDispEnv(resultFile, groupName=['JointLine01', 'JointLine02'], caseName=['MCEr-Disp-GM11-HorOnly', 'MCEr-Disp-GM11-VertOnly'], saveLocation=saveLocation)
