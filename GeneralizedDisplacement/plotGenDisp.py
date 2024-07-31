from utils.readFile import *
from utils.cleanDB import *
import pandasql as ps
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import distinctipy

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

        self.GMList = self.getGMList()
        self.GridList = self.getGridList()
        self.DispList = self.getDispList()

        self.readAnalysisFile()
        self.readHeightFile()
        self.assignDriftLimit()
        self.assignHeightLimits()
        self.compiledData = None

    def readAnalysisFile(self):
        #self.connection = connectDB(self.analysisFile)
        query = f"""
        SELECT GenDispl, OutputCase, max(abs(Translation)) as Disp
        FROM "Jt Displacements - Generalized"
        GROUP BY GenDispl, OutputCase
        """
        #connection = connectDB(inputFile)
        self.dispData = getData(self.connection, query=query)
        self.jointData = getData(self.connection, query='SELECT Joint, Z FROM "Joint Coordinates"')
        self.genDispDefn = getData(self.connection, query='SELECT GenDispl, Joint, U1SF, U2SF FROM "Gen Displ Defs 1 - Translation"')
        self.genDispDefn['Loc'] = self.genDispDefn['U1SF'] + self.genDispDefn['U2SF']
        self.genDispDefn.drop(columns=['U1SF', 'U2SF'], inplace=True)

    def readHeightFile(self):
        #self.heightConnection = connectDB(self.heightFile)
        self.heightData = getData(self.heightConnection, tableName='Floor Elevations')

    def getGMList(self):
        return self.dispData['OutputCase'].unique()
    
    def getGridList(self):
        return self.dispData['GenDispl'].str.split('_').str[0].unique()
    
    def getDispList(self):
        return self.dispData['GenDispl'].str.split('_').str[2].unique()

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
        for g in gridList:
            for gm_i, gm in enumerate(GMList):
                for d_i, d in enumerate(dispList):
                    condition1 = self.dispData['GenDispl'].str.contains(g+"_")
                    condition2 = self.dispData['OutputCase'] == gm
                    condition3 = self.dispData['GenDispl'].str.contains(d)
                    selGrid = self.dispData[condition1 & condition2 & condition3].reset_index(drop=True)
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
                    self.compiledData = cleanDB(self.compiledData)
                    finalData = cleanDB(finalData)
                    self.compiledData = pd.concat([self.compiledData, finalData], ignore_index=True)
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
        ax.set_ylim(self.Hmin, self.Hmax)
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
        return ax

if __name__ == '__main__':
    #################################### USER INPUT ####################################
    inputFileLoc = r"C:\\Users\\abindal\\OneDrive - Nabih Youssef & Associates\\Documents\\00_Projects\\06_The Vault\\20240715 Models\\305\\try\\"
    inputFile = inputFileLoc + "\\20240715_GenDispForces_305_Seq.xlsx"
    heightFile = inputFileLoc + '\\FloorElevations.xlsx'

    gridList = ['S12A', 'S12B', 'S12C', 'S12D', 'S12', 
            'S13A', 'S13B', 'S13C', 'S13D', 'S13E',
            'S13F', 'S13G', 'S13H', 'S13J', 'S13K']
    GMList = ['SLE - 2% Damped - U1', 'SLE - 2% Damped - U2']
    dispList = ['U1', 'U2']
    LABEL_LEGEND_FONT_SIZE = 8
    ####################################################################################
    
    if not os.path.exists(inputFileLoc + f'\\DRIFTS'):
        os.makedirs(inputFileLoc + f'\\DRIFTS')

    genDisp = GeneralizedDisplacement(inputFile, heightFile)
    genDisp.plotData(gridList, GMList, dispList)               
   