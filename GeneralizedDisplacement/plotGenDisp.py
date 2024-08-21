from utils.readFile import *
from utils.cleanDB import *
import pandasql as ps
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import distinctipy
import time

# To run please run "python -m GeneralizedDisplacement.plotGenDisp" from the main folder

# The analysis file should have the following tables:
# 1. "Jt Displacements - Generalized"
# 2. "Joint Coordinates"
# 3. "Gen Displ Defs 1 - Translation"

# The height file should have the following tables:
# 1. "Floor Elevations"

class GeneralizedDisplacement:
    def __init__(self, **kwargs):#,analysisFile, heightFile):
        if 'analysisFile' in kwargs:
            self.analysisFile = kwargs['analysisFile']
            self.connection = connectDB(self.analysisFile)
        if 'heightFile' in kwargs:
            self.heightFile = kwargs['heightFile']
            self.heightConnection = connectDB(self.heightFile)

        if 'analysisFileConnection' in kwargs:
            self.connection = kwargs['analysisFileConnection']
        if 'heightFileConnection' in kwargs:
            self.heightConnection = kwargs['heightFileConnection']

        self.compiledData = None
        self.assignDriftLimit(Dlim = kwargs['Dlim'], Dmax = kwargs['Dmax'])
        self.assignHeightLimits(Hmin = kwargs['Hmin'], Hmax = kwargs['Hmax'])

    def populateFields(self):
        self.readMainFile()
        self.GMList = self.getGMList()
        self.GridList = self.getGridList()
        self.DispList = self.getDispList()
        return self.GMList, self.GridList, self.DispList

    def readMainFile(self):
        #self.connection = connectDB(self.analysisFile)
        query = f"""
        SELECT GenDispl, OutputCase, max(abs(Translation)) as Disp
        FROM "Jt Displacements - Generalized"
        GROUP BY GenDispl, OutputCase
        """
        #connection = connectDB(inputFile)
        self.dispData = getData(self.connection, query=query)


    def readDefinitionFile(self):
        self.jointData = getData(self.connection, query='SELECT Joint, Z FROM "Joint Coordinates"')
        self.genDispDefn = getData(self.connection, query='SELECT GenDispl, Joint, U1SF, U2SF FROM "Gen Displ Defs 1 - Translation"')
        self.genDispDefn['Loc'] = self.genDispDefn['U1SF'] + self.genDispDefn['U2SF']
        self.genDispDefn.drop(columns=['U1SF', 'U2SF'], inplace=True)

    def readHeightFile(self):
        #self.heightConnection = connectDB(self.heightFile)
        self.heightData = getData(self.heightConnection, tableName='Floor Elevations')

    def getGMList(self):
        return sorted(self.dispData['OutputCase'].unique().tolist())
    
    def getGridList(self):
        return sorted(self.dispData['GenDispl'].str.split('_').str[0].unique().tolist())
    
    def getDispList(self):
        return sorted(self.dispData['GenDispl'].str.split('_').str[2].unique().tolist())

    def assignDriftLimit(self, Dlim=0.004, Dmax=0.006):
        self.Dlim = Dlim
        self.Dmax = Dmax
    
    def assignHeightLimits(self, Hmin=-60.365, Hmax=29.835):
        self.Hmin = Hmin
        self.Hmax = Hmax

    def processData(self, gridList, GMList, dispList, colList=['#1f77b4','#ff7f0e']):
        print('Processing Data')
        self.compiledData = pd.DataFrame(columns=['GenDispl', 'OutputCase', 'Disp', 'TopJoint', 'TopZ', 'BotJoint', 'BotZ', 'Drift'])
        genDispDefn = self.genDispDefn
        jointData = self.jointData
        if colList is None:
            colList = distinctipy.get_colors(len(GMList))
        query = f"""
        SELECT GenDispl, genDispDefn.Joint, cast(Z as float) as Z
        FROM genDispDefn
        INNER JOIN jointData
        ON genDispDefn.Joint = jointData.Joint
        WHERE Loc = 1
        """
        topJoint = ps.sqldf(query, locals())
        query = f"""
        SELECT GenDispl, genDispDefn.Joint, cast(Z as float) as Z
        FROM genDispDefn
        INNER JOIN jointData
        ON genDispDefn.Joint = jointData.Joint
        WHERE Loc = -1
        """
        botJoint = ps.sqldf(query, locals())

        for g in gridList:
            for gm_i, gm in enumerate(GMList):
                for d_i, d in enumerate(dispList):
                    print(g, gm, d)
                    t1 = time.time()
                    condition1 = self.dispData['GenDispl'].str.contains(g+"_")
                    condition2 = self.dispData['OutputCase'] == gm
                    condition3 = self.dispData['GenDispl'].str.contains(d)
                    selGrid = self.dispData[condition1 & condition2 & condition3].reset_index(drop=True)
                    t2 = time.time()
                    print(f'Selection Time: {t2-t1}')
                    query = f"""
                    SELECT selGrid.GenDispl, OutputCase, Disp, topJoint.Joint as TopJoint,topJoint.Z as TopZ, botJoint.Joint as BotJoint, botJoint.Z as BotZ
                    FROM selGrid
                    JOIN topJoint
                    ON selGrid.GenDispl = topJoint.GenDispl
                    JOIN botJoint
                    ON selGrid.GenDispl = botJoint.GenDispl
                    """
                    finalData = ps.sqldf(query, locals())
                    t3 = time.time()
                    print(f'Join Time: {t3-t2}')
                    finalData['Drift'] = abs(finalData['Disp']/(finalData['TopZ'] - finalData['BotZ']))
                    t4 = time.time()
                    print(f'Drift Time: {t4-t3}')
                    #self.compiledData = cleanDB(self.compiledData)
                    #finalData = cleanDB(finalData)
                    self.compiledData = pd.concat([self.compiledData, finalData], ignore_index=True)
                    t5 = time.time()
                    print(f'Concat Time: {t5-t4}')
        return self.compiledData
    
    def plotData(self, gridList, GMList, dispList, colList=['#1f77b4','#ff7f0e']):
        # Generate the compiled data
        self.processData(gridList, GMList, dispList, colList)
        # Save the compiled data
        self.compiledData.to_excel(inputFileLoc + '\\DRIFTS\\outputDrifts.xlsx', index=False)
        print('Data Processed and Saved')
        # Plot the data
        print('Plotting Data')
        for g in gridList:
            fig, ax = plt.subplots(1,len(dispList), figsize=(5*len(dispList),5))
            for d_i, d in enumerate(dispList):
                ax[d_i].set_title(f'{g} - {d}')
                for gm_i, gm in enumerate(GMList):
                    condition1 = self.compiledData['GenDispl'].str.contains(g+"_")
                    condition2 = self.compiledData['OutputCase'] == gm
                    condition3 = self.compiledData['GenDispl'].str.contains(d)
                    selGrid = self.compiledData[condition1 & condition2 & condition3].reset_index(drop=True).sort_values(by='TopZ', ascending=False)
                    ax[d_i].step(selGrid['Drift'], selGrid['TopZ'], label=gm, color = colList[gm_i%len(colList)], marker = '.')
                self.formataxis(ax[d_i])
            plt.tight_layout()
            plt.savefig(inputFileLoc + f'\\DRIFTS\\{g}_Drift.png', dpi = 300)
            plt.close()
        print('Data Plotted and Saved')
    
    def formataxis(self, ax):
        ax.set_xlim(0, self.Dmax)
        
        ax.vlines(self.Dlim, self.Hmin, self.Hmax, linestyle='--', color = 'red', linewidth=1.5, label='SLE Limit')
        ax.set_xticks(np.arange(0, self.Dmax+0.001, 0.001))
        ax.set_xticklabels(['{:.1f}%'.format(x*100) for x in ax.get_xticks()], fontsize=LABEL_LEGEND_FONT_SIZE)
        ax.set_yticks(self.heightData['SAP2000Elev'])
        ax.set_yticklabels(self.heightData['FloorLabel'], fontsize=LABEL_LEGEND_FONT_SIZE)
        ax.legend(loc='lower right', fontsize=LABEL_LEGEND_FONT_SIZE)
        ax.set_xlabel('Drift (%)')
        ax.set_ylabel('Story')
        ax.grid(which='both', linestyle='--', linewidth=0.5)
        secax_y = ax.secondary_yaxis('right')
        secax_y.set_yticks(self.heightData['SAP2000Elev'])
        secax_y.set_yticklabels([int(round(x,0)) for x in self.heightData['SAP2000Elev']], fontsize=LABEL_LEGEND_FONT_SIZE)
        secax_y.set_ylabel('Height (m)')
        ax.set_ylim(self.Hmin, self.Hmax)
        return ax

if __name__ == '__main__':
    #################################### USER INPUT ####################################
    inputFileLoc = r"C:\\Users\\abindal\\OneDrive - Nabih Youssef & Associates\\Documents\\00_Projects\\06_The Vault\\20240715 Models\\20240814_302\\"
    inputFile = inputFileLoc + "\\20240821_ResponseSpectrum.xlsx"
    heightFile = inputFileLoc + '\\FloorElevations.xlsx'

    #gridList = ['N12A', 'N12B', 'N12C', 'N12D', 'N12', 
    #        'N13A', 'N13B', 'N13C', 'N13D', 'N13E',
    #        'N13F', 'N13G', 'N13H']
    GMList = ['SLE - 2% Damped - U1', 'SLE - 2% Damped - U2']

    #gridList = ['S12A', 'S12B', 'S12C', 'S12D', 'S12', 
    #        'S13A', 'S13B', 'S13C', 'S13D', 'S13E',
    #        'S13F', 'S13G', 'S13H', 'S13J', 'S13K']
    #GMList = ['Absolute Avg']
    gridList = ['S2', 'S3A', 'S3B', 'S3C', 'S3D', 'S3', 'S4A', 'S4B', 'S4C', 'S4D', 'S4', 'S5A', 'S5B', 'S5C', 'S5D', 'S5.1', 'S5.2']

    dispList = ['U1', 'U2']
    LABEL_LEGEND_FONT_SIZE = 8
    ####################################################################################
    
    if not os.path.exists(inputFileLoc + f'\\DRIFTS'):
        os.makedirs(inputFileLoc + f'\\DRIFTS')

    genDisp = GeneralizedDisplacement(analysisFile=inputFile, heightFile=heightFile, 
                                      Dlim = 0.004, Dmax = 0.005, 
                                      Hmin=-22.965, Hmax=126.635)
    genDisp.readMainFile()
    genDisp.readDefinitionFile()
    genDisp.readHeightFile()
    genDisp.plotData(gridList, GMList, dispList)               
   