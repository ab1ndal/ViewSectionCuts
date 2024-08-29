from utils.readFile import *
from utils.cleanDB import *
import pandasql as ps
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import distinctipy
import time
import tempfile
from dash import dcc
import zipfile
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib
matplotlib.use('Agg')

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

        if 'DlimName' in kwargs:
            self.DlimName = kwargs['DlimName']

        if 'showLimit' in kwargs:
            self.showLimit = kwargs['showLimit'] == 'True'

        if 'plotList' in kwargs:
            self.plotList = kwargs['plotList']
        else:
            self.plotList = ['Drift']
        
        if 'caseType' in kwargs:
            self.caseType = kwargs['caseType']

        if 'Disp' in self.plotList:
            self.DispMin = kwargs['DispMin']
            self.DispMax = kwargs['DispMax']
            self.DispStep = kwargs['DispStep']

        if 'lenConv' in kwargs:
            self.lenConv = kwargs['lenConv']
            self.lenUnit = kwargs['lenUnit']

        self.compiledDrift = None
        self.LABEL_LEGEND_FONT_SIZE = 8
        self.assignDriftLimit(Dlim = kwargs['Dlim'], Dmax = kwargs['Dmax'], Dstep = kwargs['Dstep'])
        self.assignHeightLimits(Hmin = kwargs['Hmin'], Hmax = kwargs['Hmax'])

    def populateFields(self):
        self.readMainFile()
        self.GMList = self.getGMList()
        self.GridList = self.getGridList()
        self.DispList = self.getDispList()
        return self.GMList, self.GridList, self.GridList, self.DispList, self.DispList

    def readMainFile(self):
        #self.connection = connectDB(self.analysisFile)
        if 'Drift' in self.plotList:
            query = f"""
            SELECT GenDispl, OutputCase, max(abs(Translation)) as Disp
            FROM "Jt Displacements - Generalized"
            GROUP BY GenDispl, OutputCase
            """
            #connection = connectDB(inputFile)
            self.genDispData = getData(self.connection, query=query)
        if 'Disp' in self.plotList:
            query = f"""
            SELECT Joint, OutputCase, StepType, U1, U2, U3
            FROM "Joint Displacements"
            """
            #connection = connectDB(inputFile)
            self.dispData = getData(self.connection, query=query)


    def readDefinitionFile(self):
        self.jointData = getData(self.connection, query='SELECT Joint, Z FROM "Joint Coordinates"')
        if 'Drift' in self.plotList:
            self.genDispDefn = getData(self.connection, query='SELECT GenDispl, Joint, U1SF, U2SF FROM "Gen Displ Defs 1 - Translation"')
            self.genDispDefn['Loc'] = self.genDispDefn['U1SF'] + self.genDispDefn['U2SF']
            self.genDispDefn.drop(columns=['U1SF', 'U2SF'], inplace=True)
        if 'Disp' in self.plotList:
            self.jointGroup = getData(self.connection, 
                                      query='SELECT GroupName, ObjectLabel FROM "Groups 2 - Assignments" WHERE ObjectType = "Joint" AND GroupName LIKE "Drift_Top_%"')
            

    def readHeightFile(self):
        #self.heightConnection = connectDB(self.heightFile)
        self.heightData = getData(self.heightConnection, tableName='Floor Elevations')

    def getGMList(self):
        return sorted(self.genDispData['OutputCase'].unique().tolist())
    
    def getGridList(self):
        return sorted(self.genDispData['GenDispl'].str.split('_').str[0].unique().tolist())
    
    def getDispList(self):
        return sorted(self.genDispData['GenDispl'].str.split('_').str[2].unique().tolist())

    def assignDriftLimit(self, Dlim=0.004, Dmax=0.006, Dstep=0.001):
        self.Dlim = Dlim
        self.Dmax = Dmax
        self.Dstep = Dstep
    
    def assignHeightLimits(self, Hmin=-60.365, Hmax=29.835):
        self.Hmin = Hmin
        self.Hmax = Hmax

    def processData(self, gridList, GMList, dispList, colList):
        self.compiledDrift = pd.DataFrame(columns=['GenDispl', 'OutputCase', 'Disp', 'TopJoint', 'TopZ', 'BotJoint', 'BotZ', 'Drift'])
        self.compiledDisp = pd.DataFrame(columns=['Grid', 'Joint', 'Z', 'OutputCase', 'StepType', 'U1', 'U2', 'U3'])
        jointData = self.jointData
        if colList is None:
            colList = distinctipy.get_colors(len(GMList))
        if 'Drift' in self.plotList:        
            genDispDefn = self.genDispDefn
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
                        condition1 = self.genDispData['GenDispl'].str.contains(g+"_")
                        condition2 = self.genDispData['OutputCase'] == gm
                        condition3 = self.genDispData['GenDispl'].str.contains(d)
                        selGrid = self.genDispData[condition1 & condition2 & condition3].reset_index(drop=True)
                        query = f"""
                        SELECT selGrid.GenDispl, OutputCase, Disp, topJoint.Joint as TopJoint,topJoint.Z as TopZ, botJoint.Joint as BotJoint, botJoint.Z as BotZ
                        FROM selGrid
                        JOIN topJoint
                        ON selGrid.GenDispl = topJoint.GenDispl
                        JOIN botJoint
                        ON selGrid.GenDispl = botJoint.GenDispl
                        """
                        finalData = ps.sqldf(query, locals())
                        finalData['Drift'] = abs(finalData['Disp']/(finalData['TopZ'] - finalData['BotZ']))
                        self.compiledDrift = pd.concat([self.compiledDrift, finalData], ignore_index=True)
        if 'Disp' in self.plotList:
            jointGroup = self.jointGroup
            for g_i, g in enumerate(gridList):
                dispData = self.dispData
                query = f"""
                SELECT '{g}' as Grid, dispData.Joint, Z, OutputCase, StepType, U1, U2, U3
                FROM dispData
                JOIN jointData
                ON dispData.Joint = jointData.Joint
                JOIN jointGroup
                ON dispData.Joint = ObjectLabel                
                WHERE GroupName = 'Drift_Top_{g}'
                """
                finalData = ps.sqldf(query, locals())
                self.compiledDisp = pd.concat([self.compiledDisp, finalData], ignore_index=True)
        
        return self.compiledDrift
    
    def plotData(self, gridList, GMList, dispList, colList, nameList):
        # Generate the compiled data
        self.processData(gridList, GMList, dispList, colList)
        # Temp path
        output_dir = os.path.join(tempfile.gettempdir(), 'disp_drifts_plots')
        os.makedirs(output_dir, exist_ok=True)
        excel_file_path = os.path.join(output_dir, 'outputDriftDisp.xlsx')

        pdf_file_path = os.path.join(output_dir, 'disp_drifts_plots.pdf')
        # Save the compiled data
        #self.compiledDrift.to_excel(excel_file_path, index=False)
        with pd.ExcelWriter(excel_file_path) as writer:
            self.compiledDrift.to_excel(writer, sheet_name='Drift', index=False)
            self.compiledDisp.to_excel(writer, sheet_name='Disp', index=False)

        print('Data Processed and Saved')
        # Plot the data
        print('Plotting Data')
        plot_files = []
        title = ['A-Canyon', 'X-Canyon']
        colListGM = distinctipy.get_colors(len(gridList), exclude_colors = [(1,1,1)])

        with PdfPages(pdf_file_path) as pdf:
            if 'Drift' in self.plotList:
                for g in gridList:
                    print(f'Plotting {g}')
                    fig, ax = plt.subplots(1,len(dispList), figsize=(5*len(dispList),5))
                    condition1 = self.compiledDrift['GenDispl'].str.contains(g+"_")
                    for d_i, d in enumerate(dispList):
                        ax[d_i].set_title(f'{g} - {d} ({title[d_i]})')
                        condition3 = self.compiledDrift['GenDispl'].str.contains(d)
                        for gm_i, gm in enumerate(GMList):
                            condition2 = self.compiledDrift['OutputCase'] == gm
                            selGrid = self.compiledDrift[condition1 & condition2 & condition3].reset_index(drop=True).sort_values(by='TopZ', ascending=False)
                            ax[d_i].step(selGrid['Drift'], selGrid['TopZ'], label=nameList[gm_i], color = colList[gm_i%len(colList)])
                        self.formataxis(ax[d_i], 'Drift')
                    plt.tight_layout()
                    #New Save File
                    plot_file_path = os.path.join(output_dir, f'{g}_Drift.png')
                    plt.savefig(plot_file_path, dpi = 300)
                    plot_files.append(plot_file_path)
                    #Old Save File
                    pdf.savefig(fig)
                    #plt.savefig(inputFileLoc + f'\\DRIFTS\\{g}_Drift.png', dpi = 300)
                    plt.close()

                
                for gm_i, gm in enumerate(GMList):
                    print(f'Plotting {gm}')
                    fig, ax = plt.subplots(1,len(dispList), figsize=(5*len(dispList),5))
                    condition2 = self.compiledDrift['OutputCase'] == gm
                    for d_i, d in enumerate(dispList):
                        ax[d_i].set_title(f'{nameList[gm_i]} - {d} ({title[d_i]})')
                        condition3 = self.compiledDrift['GenDispl'].str.contains(d)
                        for g_i, g in enumerate(gridList):
                            condition1 = self.compiledDrift['GenDispl'].str.contains(g+"_")
                            selGrid = self.compiledDrift[condition1 & condition2 & condition3].reset_index(drop=True).sort_values(by='TopZ', ascending=False)
                            ax[d_i].step(selGrid['Drift'], selGrid['TopZ'], label=g, color = colListGM[g_i%len(colListGM)])
                        self.formataxis(ax[d_i], 'Drift')
                    plt.tight_layout()
                    #New Save File
                    plot_file_path = os.path.join(output_dir, f'{gm}_Drift.png')
                    plt.savefig(plot_file_path, dpi = 300)
                    plot_files.append(plot_file_path)
                    pdf.savefig(fig)
                    plt.close()

            if 'Disp' in self.plotList:
                for g in gridList:
                    fig, ax = plt.subplots(1,len(dispList), figsize=(5*len(dispList),5))
                    condition1 = self.compiledDisp['Grid'] == g
                    for gm_i, gm in enumerate(GMList):
                        condition2 = self.compiledDisp['OutputCase'] == gm
                        selGrid = self.compiledDisp[condition1 & condition2].reset_index(drop=True).sort_values(by='Z', ascending=False)
                        for d_i, d in enumerate(dispList):
                            ax[d_i].set_title(f'{g} - {d} ({title[d_i]})')
                            if self.caseType[gm_i] == 'Lin':
                                ax[d_i].plot(self.lenConv*selGrid[f'U{d_i+1}'], selGrid['Z'], label=nameList[gm_i], color = colList[gm_i%len(colList)])
                            elif self.caseType[gm_i] == 'NonLin':
                                maxSelGrid = selGrid[selGrid['StepType'] == 'Max']
                                ax[d_i].plot(self.lenConv*maxSelGrid[f'U{d_i+1}'], maxSelGrid['Z'], label=nameList[gm_i], color = colList[gm_i%len(colList)])
                            elif self.caseType[gm_i] == 'RS':
                                maxSelGrid = selGrid[selGrid['StepType'] == 'Max']
                                ax[d_i].plot(self.lenConv*maxSelGrid[f'U{d_i+1}'], maxSelGrid['Z'], label=nameList[gm_i], color = colList[gm_i%len(colList)])
                                ax[d_i].plot(-self.lenConv*maxSelGrid[f'U{d_i+1}'], maxSelGrid['Z'], color = colList[gm_i%len(colList)])
                            
                            else:
                                maxSelGrid = selGrid[selGrid['StepType'] == 'Max']
                                minSelGrid = selGrid[selGrid['StepType'] == 'Min']
                                ax[d_i].plot(self.lenConv*maxSelGrid[f'U{d_i+1}'], maxSelGrid['Z'], label=nameList[gm_i], color = colList[gm_i%len(colList)])
                                ax[d_i].plot(self.lenConv*minSelGrid[f'U{d_i+1}'], minSelGrid['Z'], color = colList[gm_i%len(colList)])
                            
                    for i in range(len(dispList)):
                        ax[i].vlines(0, self.Hmin, self.Hmax, linestyle='--', color = 'black', linewidth=1)
                        self.formataxis(ax[i], 'Disp')
                    plt.tight_layout()
                    #New Save File
                    plot_file_path = os.path.join(output_dir, f'{g}_Disp.png')
                    plt.savefig(plot_file_path, dpi = 300)
                    plot_files.append(plot_file_path)
                    #Old Save File
                    pdf.savefig(fig)
                    #plt.savefig(inputFileLoc + f'\\DRIFTS\\{g}_Disp.png', dpi = 300)
                    plt.close()
                for gm_i, gm in enumerate(GMList):
                    fig, ax = plt.subplots(1,len(dispList), figsize=(5*len(dispList),5))
                    condition2 = self.compiledDisp['OutputCase'] == gm
                    for g_i, g in enumerate(gridList):
                        condition1 = self.compiledDisp['Grid'] == g
                        selGrid = self.compiledDisp[condition1 & condition2].reset_index(drop=True).sort_values(by='Z', ascending=False)
                        for d_i, d in enumerate(dispList):
                            ax[d_i].set_title(f'{nameList[gm_i]} - {d} ({title[d_i]})')
                            if self.caseType[gm_i] == 'Lin':
                                ax[d_i].plot(self.lenConv*selGrid[f'U{d_i+1}'], selGrid['Z'], label=g, color = colListGM[g_i%len(colListGM)])
                            elif self.caseType[gm_i] == 'NonLin':
                                maxSelGrid = selGrid[selGrid['StepType'] == 'Max']
                                ax[d_i].plot(self.lenConv*maxSelGrid[f'U{d_i+1}'], maxSelGrid['Z'], label=g, color = colListGM[g_i%len(colListGM)])
                            elif self.caseType[gm_i] == 'RS':
                                maxSelGrid = selGrid[selGrid['StepType'] == 'Max']
                                ax[d_i].plot(self.lenConv*maxSelGrid[f'U{d_i+1}'], maxSelGrid['Z'], label=g, color = colListGM[g_i%len(colListGM)])
                                ax[d_i].plot(-self.lenConv*maxSelGrid[f'U{d_i+1}'], maxSelGrid['Z'], color = colListGM[g_i%len(colListGM)])
                            else:
                                maxSelGrid = selGrid[selGrid['StepType'] == 'Max']
                                minSelGrid = selGrid[selGrid['StepType'] == 'Min']
                                ax[d_i].plot(self.lenConv*maxSelGrid[f'U{d_i+1}'], maxSelGrid['Z'], label=g, color = colListGM[g_i%len(colListGM)])
                                ax[d_i].plot(self.lenConv*minSelGrid[f'U{d_i+1}'], minSelGrid['Z'], color = colListGM[g_i%len(colListGM)])
                            
                    for i in range(len(dispList)):
                        ax[i].vlines(0, self.Hmin, self.Hmax, linestyle='--', color = 'black', linewidth=1)
                        self.formataxis(ax[i], 'Disp')

                    plt.tight_layout()
                    #New Save File
                    plot_file_path = os.path.join(output_dir, f'{gm}_Disp.png')
                    plt.savefig(plot_file_path, dpi = 300)
                    plot_files.append(plot_file_path)
                    pdf.savefig(fig)
                    plt.close()            
        print('Data Plotted and Saved')
        zip_file_path = os.path.join(output_dir, 'disp_drifts_plots.zip')
        with zipfile.ZipFile(zip_file_path, 'w') as zipf:
            zipf.write(excel_file_path, os.path.basename(excel_file_path))
            for plot_file in plot_files:
                zipf.write(plot_file, os.path.basename(plot_file))
            zipf.write(pdf_file_path, os.path.basename(pdf_file_path))
        return dcc.send_file(zip_file_path, filename = 'disp_drifts_plots.zip')
    
    def formataxis(self, ax, plotType):
        ax.set_yticks(self.heightData['SAP2000Elev'])
        ax.set_yticklabels(self.heightData['FloorLabel'], fontsize=self.LABEL_LEGEND_FONT_SIZE)
        ax.set_ylabel('Story')
        secax_y = ax.secondary_yaxis('right')
        secax_y.set_yticks(self.heightData['SAP2000Elev'])
        secax_y.set_yticklabels([int(round(x,0)) for x in self.heightData['SAP2000Elev']], fontsize=self.LABEL_LEGEND_FONT_SIZE)
        secax_y.set_ylabel('Height (m)')
        ax.set_ylim(self.Hmin, self.Hmax)

        if plotType == 'Drift':
            ax.set_xlim(0, self.Dmax)
            if self.showLimit:
                ax.vlines(self.Dlim, self.Hmin, self.Hmax, linestyle='--', color = 'red', linewidth=1.5, label=self.DlimName)
            ax.set_xticks(np.arange(0, self.Dmax + self.Dstep, self.Dstep))
            ax.set_xticklabels(['{:.1f}%'.format(x*100) for x in ax.get_xticks()], fontsize=self.LABEL_LEGEND_FONT_SIZE)
            ax.set_xlabel('Drift (%)')
        if plotType == 'Disp':
            ax.set_xlim(self.DispMin, self.DispMax)
            ax.set_xticks(np.arange(self.DispMin, self.DispMax + self.DispStep, self.DispStep))
            ax.set_xticklabels(['{:.2f}'.format(x) for x in ax.get_xticks()], fontsize=self.LABEL_LEGEND_FONT_SIZE)
            ax.set_xlabel(f'Displacement ({self.lenUnit})')
        ax.grid(which='both', linestyle='--', linewidth=0.5)
        ax.legend(loc='lower right', fontsize=self.LABEL_LEGEND_FONT_SIZE)
        
        return ax

"""
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
                                      DlimName = 'SLE Limit', Dlim = 0.004, Dmax = 0.005, Dstep = 0.001,
                                      Hmin=-22.965, Hmax=126.635)
    genDisp.readMainFile()
    genDisp.readDefinitionFile()
    genDisp.readHeightFile()
    genDisp.plotData(gridList, GMList, dispList)               
"""