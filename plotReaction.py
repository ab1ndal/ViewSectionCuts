from utils.readFile import connectDB, getData
import pandasql as ps
import matplotlib.pyplot as plt
import distinctipy


filePath = r"C:\\Users\\abindal\\OneDrive - Nabih Youssef & Associates\\Documents\\00_Projects\\06_The Vault\\20240715 Models\\305\\"
rxnFile = "20240715_ResponseAll_Pin_305.xlsx"
connection = connectDB(filePath+rxnFile)

query = 'SELECT * FROM "Groups 2 - Assignments"'
groupData = getData(connection, query=query)

query = 'SELECT R.Joint, XorR as X, Y, Z, OutputCase, StepType, round(F1,0) as F1, round(F2,0) as F2, round(F3,0) as F3 FROM "Joint Reactions" as R INNER JOIN "Joint Coordinates" as C ON R.Joint = C.Joint'
reactionData = getData(connection, query=query)

def getReactionGroupAll(reactionAll, groupData, groupNames, caseName, stepName):
    groupSQL = "','".join(groupNames)
    query =f"""
    SELECT G.GroupName, sum(F1) as F1_Total, sum(F2) as F2_Total, sum(F3) as F3_Total
    FROM 
    reactionAll as R 
    INNER JOIN 
    (SELECT GroupName, ObjectLabel FROM groupData WHERE ObjectType = 'Joint' AND GroupName in ('{groupSQL}')) as G
    ON R.Joint = G.ObjectLabel
    WHERE 
    R.OutputCase = '{caseName}' AND R.StepType = '{stepName}'
    GROUP BY GroupName
    """
    reactionGroup = ps.sqldf(query, locals())
    return reactionGroup

def plotFriction2(filePath, reactionData, groupData, EQx = 'MCE-X', EQy = 'MCE-Y'):
    fig, ax = plt.subplots(1, 2, figsize=(10, 5))
    groupNames = ['FND_Zone1','FND_Zone2','FND_Zone3','FND_Zone4','FND_Zone5','FND_Zone6']
    reactionDL = getReactionGroupAll(reactionData, groupData, groupNames, '1.0D+0.5L', 'Max')
    reactionEQx = getReactionGroupAll(reactionData, groupData, groupNames, EQx, 'Max')
    reactionEQy = getReactionGroupAll(reactionData, groupData, groupNames, EQy, 'Max')
    barWidth = 0.8/2
    bars = ax[0].bar([x for x in range(len(reactionDL['GroupName']))], reactionDL['F3_Total'], label='1.0D+0.5L (F3)', width = barWidth)
    for bar in bars:
        ax[0].text(bar.get_x() + bar.get_width()/2, bar.get_height(), f'{int(bar.get_height())}', ha='center', va='bottom',fontsize=6)
    bars = ax[1].bar([x-barWidth/2 for x in range(len(reactionEQx['GroupName']))], reactionEQx['F1_Total'], label= EQx + ' (F1)', width = barWidth)
    for bar in bars:
        ax[1].text(bar.get_x() + bar.get_width()/2, bar.get_height(), f'{int(bar.get_height())}', ha='center', va='bottom',fontsize=6)
    bars = ax[1].bar([x+barWidth/2 for x in range(len(reactionEQy['GroupName']))], reactionEQy['F2_Total'], label=EQy + ' (F2)', width = barWidth)
    for bar in bars:
        ax[1].text(bar.get_x() + bar.get_width()/2, bar.get_height(), f'{int(bar.get_height())}', ha='center', va='bottom',fontsize=6)
    for i in range(2):
        ax[i].set_xticks(range(len(reactionDL['GroupName'])))
        ax[i].set_xticklabels(reactionDL['GroupName'],fontsize=6)
        # y tick font setting
        ax[i].tick_params(axis='y', labelsize=6)
        ax[i].set_ylabel('Reaction (kN)')
        ax[i].set_xlabel('Groups')
        ax[i].legend(loc='upper right', fontsize=10)
        ax[i].set_title('Base Reaction at Foundation Groups')
    ax[0].set_ylim([0, 5e5])
    ax[1].set_ylim([0, 3.5e5])
    plt.tight_layout()
    plt.savefig(filePath + 'ReactionPlotTotal.png', dpi = 300)
    
    fig, ax = plt.subplots(1, 1, figsize=(5, 5))
    barWidth = 0.8/2
    bars = ax.bar([x-barWidth/2 for x in range(len(reactionDL['GroupName']))], reactionEQx['F1_Total']/reactionDL['F3_Total'], label=EQx, width = barWidth)
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f'{round(bar.get_height(),3)}', ha='center', va='bottom', fontsize=6)
    bars = ax.bar([x+barWidth/2 for x in range(len(reactionDL['GroupName']))], reactionEQy['F2_Total']/reactionDL['F3_Total'], label=EQy, width = barWidth)
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f'{round(bar.get_height(),3)}', ha='center', va='bottom', fontsize=6)
    ax.set_xticks(range(len(reactionDL['GroupName'])))
    ax.set_xticklabels(reactionDL['GroupName'],fontsize=6)
    # y tick font setting
    ax.tick_params(axis='y', labelsize=6)
    ax.set_ylabel('Friction')
    ax.set_xlabel('Groups')
    ax.legend(loc='upper right', fontsize=10)
    ax.set_title('Base Friction at Foundation Groups')
    ax.set_ylim([0, 1.4])

    plt.tight_layout()
    plt.savefig(filePath + 'FrictionPlotTotal.png', dpi = 300)


def getReactionGroup(reactionData, groupData, groupName, caseName, stepName):
    query =f"""
    SELECT ObjectLabel
    FROM groupData
    WHERE GroupName = '{groupName}' AND ObjectType = 'Joint'
    """
    jointList = ps.sqldf(query, locals())['ObjectLabel'].tolist()
    
    query = f"""
    SELECT Joint, CAST(X as REAL) as Xfloat, CAST(Y as REAL) as Yfloat, CAST(Z as REAL) as Zfloat, F1, F2, F3
    FROM reactionData
    WHERE Joint IN {tuple(jointList)} AND OutputCase = '{caseName}' AND StepType = '{stepName}'
    ORDER BY Zfloat DESC, Xfloat ASC, Yfloat ASC 
    """
    reactionData = ps.sqldf(query, locals())
    query = """
    SELECT * FROM
    (SELECT round(Zfloat,0) as Height, avg(Xfloat) as Xavg, avg(Yfloat) as Yavg, sum(F3) as F3, sum(F1) as F1, sum(F2) as F2 
    FROM reactionData
    GROUP BY Height)
    WHERE F3 > 0
    ORDER BY Height DESC
    """
    reactionGroup = ps.sqldf(query, locals())
    return jointList, reactionData, reactionGroup

def plotReaction(groupList):
    fig, ax = plt.subplots(1, 1, figsize=(5, 5))
    for g in groupList:
        _, _, reactionGroup = getReactionGroup(reactionData, groupData, g, '1.0D+0.5L', 'Max')
        ax.plot(reactionGroup['Reaction'], reactionGroup['Height'], label=g)
    ax.set_xlabel('Reaction (kN)')
    ax.set_ylabel('Height (m)')
    ax.set_title('Reaction')
    ax.legend(loc='upper right', fontsize=10)
    plt.tight_layout()
    plt.show()

def addSingleReactionPlot(ax, reactionGroup, index, label, groupName, color, groupIndex=0,numGroups=6,heightDict=None):
    barWidth = 0.8/numGroups
    bars = ax.bar([heightDict[h] + barWidth*(groupIndex+0.5-numGroups/2) for h in reactionGroup['Height']], 
           reactionGroup[index], label=groupName, width = barWidth, color=color)
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f'{int(bar.get_height())}', ha='center', va='bottom')
    ax.set_ylabel(label)
    ax.set_xlabel('Height (m)')
    ax.set_title(label)

def addSingleFrictionPlot(ax, NumData, DemData, index, label, groupName, color, groupIndex=0,numGroups=6,heightDict=None):
    barWidth = 0.8/numGroups
    bars = ax.bar([heightDict[h] + barWidth*(groupIndex+0.5-numGroups/2) for h in NumData['Height']], 
           NumData[index]/DemData["F3"], label=groupName, width = barWidth, color=color)
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f'{round(bar.get_height(),2)}', ha='center', va='bottom')
    ax.set_ylabel(label)
    ax.set_xlabel('Height (m)')
    ax.set_title(label)

def plotAllGroups(groupList, saveLocation=None, suffix = 'All',isReaction=True):
    if isReaction:
        numPlots = 3
        fig, ax = plt.subplots(numPlots, 1, figsize=(18, 18))
    else:
        numPlots = 2
        fig, ax = plt.subplots(numPlots, 1, figsize=(18, 12))
    colList = distinctipy.get_colors(len(groupList))
    heightList = []
    for gI, g in enumerate(groupList):
        _, _, reactionGrouped = getReactionGroup(reactionData, groupData, g, '1.0D+0.5L', 'Max')
        heightList += [h for h in reactionGrouped['Height']]
    heightList = list(set(heightList))
    heightList.sort(reverse=True)
    heightDict = {h: i for i, h in enumerate(heightList)}

    for gI, g in enumerate(groupList):
        if isReaction:
            _, _, reactionGrouped = getReactionGroup(reactionData, groupData, g, '1.0D+0.5L', 'Max')
            addSingleReactionPlot(ax[0], reactionGrouped, "F3", 'Base Reaction, F3 (kN)', g, colList[gI],gI,len(groupList),heightDict)
            _, _, reactionGrouped = getReactionGroup(reactionData, groupData, g, 'SLE-X', 'Max')
            addSingleReactionPlot(ax[1], reactionGrouped, "F1", 'Base Reaction, F1 (kN)', g, colList[gI],gI,len(groupList),heightDict)
            _, _, reactionGrouped = getReactionGroup(reactionData, groupData, g, 'SLE-Y', 'Max')
            addSingleReactionPlot(ax[2], reactionGrouped, "F2", 'Base Reaction, F2 (kN)', g, colList[gI],gI,len(groupList),heightDict)
        else:
            _, _, reactionGroupedD = getReactionGroup(reactionData, groupData, g, '1.0D+0.5L', 'Max')
            _, _, reactionGroupedN = getReactionGroup(reactionData, groupData, g, 'SLE-X', 'Max')
            addSingleFrictionPlot(ax[0], reactionGroupedN, reactionGroupedD, "F1", 'Base Friction', g, colList[gI],gI,len(groupList),heightDict)
            _, _, reactionGroupedN = getReactionGroup(reactionData, groupData, g, 'SLE-Y', 'Max')
            addSingleFrictionPlot(ax[1], reactionGroupedN,reactionGroupedD, "F2", 'Base Friction', g, colList[gI],gI,len(groupList),heightDict)
    
    for i in range(numPlots):
        ax[i].legend(loc='upper right', fontsize=10)
        # set x labels
        ax[i].set_xticks(range(len(heightList)))
        ax[i].set_xticklabels([f'H=\n{h}m' for h in heightList])
    
    if isReaction:
        ax[0].set_ylim([0, 140000])
        ax[1].set_ylim([0, 6000])
        ax[2].set_ylim([0, 6000])
    plt.tight_layout()
    if isReaction:
        plt.savefig(saveLocation + f'ReactionPlot{suffix}.png', dpi = 300)
    else:
        plt.savefig(saveLocation + f'FrictionPlot{suffix}.png', dpi = 300)


def plotElevation(groupList, loadCase, saveLocation=None, plotIndex='F3', label = 'Base Reaction (kN)', isEQ=False):
    fig, ax = plt.subplots(1, len(groupList), figsize=(6*len(groupList), 5))
    for gI, g in enumerate(groupList):
        _, _, reactionGrouped = getReactionGroup(reactionData, groupData, g, loadCase, 'Max')
        bars = ax[gI].bar([f'H =\n{h}m' for h in reactionGrouped['Height']], reactionGrouped[plotIndex], color = 'red', width =0.5)
        for bar in bars:
            ax[gI].text(bar.get_x() + bar.get_width()/2, bar.get_height(), f'{int(bar.get_height())}', ha='center', va='bottom')
        ax[gI].set_ylabel(label)
        ax[gI].set_xlabel('Height (m)')
        ax[gI].set_title(f'{label} at {g}')

    if isEQ:
        ax[0].set_ylim([0, 250])
        ax[1].set_ylim([0, 2500])
        ax[2].set_ylim([0, 1200])
    else:
        ax[0].set_ylim([0, 10000])
        ax[1].set_ylim([0, 100000])
        ax[2].set_ylim([0, 35000])
    plt.tight_layout()
    plt.savefig(saveLocation + f'ReactionPlot_{loadCase}.png', dpi = 300)

def plotFriction(groupList, loadCase, saveLocation=None, plotIndex=['F3'], label = 'Base Reaction (kN)'):
    fig, ax = plt.subplots(1, len(groupList), figsize=(6*len(groupList), 5))
    for gI, g in enumerate(groupList):
        _, _, reactionGroupedN = getReactionGroup(reactionData, groupData, g, loadCase[0], 'Max')
        _, _, reactionGroupedD = getReactionGroup(reactionData, groupData, g, loadCase[1], 'Max')
        print(reactionGroupedN[plotIndex[0]])
        
        bars = ax[gI].bar([f'H =\n{h}m' for h in reactionGroupedN['Height']], reactionGroupedN[plotIndex[0]]/reactionGroupedD[plotIndex[1]], color = 'red', width =0.5)
        for bar in bars:
            ax[gI].text(bar.get_x() + bar.get_width()/2, bar.get_height(), f'{round(bar.get_height(),3)}', ha='center', va='bottom')
        ax[gI].set_ylabel(label)
        ax[gI].set_xlabel('Height (m)')
        ax[gI].set_title(f'{label} at {g}')

    ax[0].set_ylim([0, 0.04])
    ax[1].set_ylim([0, 0.12])
    ax[2].set_ylim([0, 0.1])
    plt.tight_layout()
    plt.savefig(saveLocation + f'BaseFrictionPlot_{plotIndex[0]}.png', dpi = 300)


#plotElevation(['S12A_WALL', 'S12B-12D_WALL', 'S12-S13A_WALL'], '1.0D+0.5L', filePath, 'F3', 'Base Reaction, F3(kN)', isEQ=False)
#plotElevation(['S12A_WALL', 'S12B-12D_WALL', 'S12-S13A_WALL'], 'SLE-X', filePath, 'F1', 'Base Reaction, F1(kN)', isEQ=True)
#plotElevation(['S12A_WALL', 'S12B-12D_WALL', 'S12-S13A_WALL'], 'SLE-Y', filePath, 'F2', 'Base Reaction, F2(kN)', isEQ=True)
#plotFriction(['S12A_WALL', 'S12B-12D_WALL', 'S12-S13A_WALL'], ['SLE-X', '1.0D+0.5L'], filePath, ['F1','F3'], 'Base Friction')
#plotFriction(['S12A_WALL', 'S12B-12D_WALL', 'S12-S13A_WALL'], ['SLE-Y', '1.0D+0.5L'], filePath, ['F2','F3'], 'Base Friction')

#plotAllGroups(['FND_Zone1','FND_Zone2','FND_Zone3','FND_Zone4','FND_Zone5','FND_Zone6'], filePath, "All",isReaction=True)
#plotAllGroups(['FND_Zone2','FND_Zone3','FND_Zone4','FND_Zone5','FND_Zone6'], filePath, "Cols",isReaction=True)


#plotAllGroups(['FND_Zone1','FND_Zone2','FND_Zone3','FND_Zone4','FND_Zone5','FND_Zone6'], filePath, "All",isReaction=False)
#plotAllGroups(['FND_Zone2','FND_Zone3','FND_Zone4','FND_Zone5','FND_Zone6'], filePath, "Cols",isReaction=False)

plotFriction2(filePath, reactionData, groupData, EQx = 'MCE-X', EQy = 'MCE-Y')

#plotElevation(['AcCanyon', 'ColumnBase'], '1.0D+0.5L', filePath, 'F3', 'Base Reaction (kN)', isEQ=False)
#plotElevation(['AcCanyon', 'ColumnBase'], 'SLE-X', filePath, 'F1', 'Base Reaction (kN)', isEQ=True)
#plotElevation(['AcCanyon', 'ColumnBase'], 'SLE-Y', filePath, 'F2', 'Base Reaction (kN)', isEQ=True)
#plotFriction(['AcCanyon', 'ColumnBase'], ['SLE-X', '1.0D+0.5L'], filePath, ['F1','F3'], 'Base Friction')
#plotFriction(['AcCanyon', 'ColumnBase'], ['SLE-Y', '1.0D+0.5L'], filePath, ['F2','F3'], 'Base Friction')
