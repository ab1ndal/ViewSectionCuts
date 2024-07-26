from utils.readFile import *
import matplotlib.pyplot as plt

class BaseDisp:
    def __init__(self, fileLoc, fileName, caseList, groupList):
        self.fileLoc = fileLoc
        self.fileName = fileName
        self.db = connectDB(fileName)
        self.caseList = caseList
        self.groupList = groupList
        

    def getJointDisp(self, groupName):
        query = f"""
        SELECT Disp.Joint, 
               CAST(XorR AS FLOAT) AS X, 
               CAST(Y AS FLOAT) AS Y, 
               CAST(Z AS FLOAT) AS Z, 
               OutputCase,
               MAX(CAST(U1 AS FLOAT))*1000 AS U1, 
               -MAX(CAST(U2 AS FLOAT))*1000 AS U2,
               MAX(CAST(U3 AS FLOAT))*1000 AS U3 
        FROM "Joint Displacements" AS Disp
        INNER JOIN "Joint Coordinates" AS Coord
        ON Disp.Joint = Coord.Joint
        WHERE Disp.Joint IN (
            SELECT ObjectLabel 
            FROM "Groups 2 - Assignments"
            WHERE GroupName = '{groupName}'
        ) AND OutputCase IN ("{'","'.join(self.caseList)}")
        GROUP BY Disp.Joint, OutputCase
        ORDER BY Z DESC, X ASC, Y ASC        
        """
        return getData(self.db, query=query)
    
    def plotBaseDisp(self):
        #set colorscale for the arrow colors
        # colors maps values from -20 to +20 to colors red to blue
        cmap_U3 = plt.cm.RdYlGn_r
        cmap_U2 = plt.cm.RdYlGn
        norm = plt.Normalize(-10, 10)

        for group in self.groupList:
            df = self.getJointDisp(group)
            print(f'Group: {group}')
            print(f'max U2: {df["U2"].max()}, min U2: {df["U2"].min()}, max U3: {df["U3"].max()}, min U3: {df["U3"].min()}')
            df["T"] = ((df["X"] - df["X"].iloc[-1])**2 + (df["Y"] - df["Y"].iloc[-1])**2)**0.5
            for case in self.caseList:
                fig, ax = plt.subplots(1,2, figsize=(10,5))
                dfCase = df[df['OutputCase'] == case].reset_index(drop=True)
                # Sort by Z DESC and then T ASC
                dfCase = dfCase.sort_values(by=['T','Z'], ascending=[True,True])
                #dfCase = dfCase.sort_values(by=['Z'], ascending=[True])
                ax[0].plot(dfCase["T"], dfCase["Z"], color = 'black', linewidth=0.5,)
                ax[1].plot(dfCase["T"], dfCase["Z"], color = 'black', linewidth=0.5)
                # draw arrows at each point to show the direction of the displacement
                for i in range(len(dfCase)):
                    u2Color = cmap_U2(norm(dfCase["U2"].iloc[i]))
                    u3Color = cmap_U3(norm(dfCase["U3"].iloc[i]))
                    ax[0].arrow(dfCase["T"].iloc[i], dfCase["Z"].iloc[i], dfCase["U2"].iloc[i], 0, head_width=0.1, head_length=0.1, fc=u2Color, ec=u2Color)
                    ax[1].arrow(dfCase["T"].iloc[i], dfCase["Z"].iloc[i], 0, dfCase["U3"].iloc[i], head_width=0.1, head_length=0.1, fc=u3Color, ec=u3Color)
                
                ax[0].set_title(f'{case} - U2')
                ax[1].set_title(f'{case} - U3')
                # Add min max values to the plot as a text in the top left corner
                ax[0].text(0.05, 0.95, f'Max U2: {dfCase["U2"].max():.2f} mm\nMin U2: {dfCase["U2"].min():.2f} mm', transform=ax[0].transAxes, fontsize=8, verticalalignment='top')
                ax[1].text(0.05, 0.95, f'Max U3: {dfCase["U3"].max():.2f} mm\nMin U3: {dfCase["U3"].min():.2f} mm', transform=ax[1].transAxes, fontsize=8, verticalalignment='top')
                #Show colorbar
                sm_U2 = plt.cm.ScalarMappable(cmap=cmap_U2, norm=norm)
                sm_U2.set_array([])
                cbar_U2 = plt.colorbar(sm_U2, ax=ax[0], orientation='horizontal')
                cbar_U2.set_label('U2 (mm)', fontsize=8)
                cbar_U2.ax.tick_params(labelsize=8)
                sm_U3 = plt.cm.ScalarMappable(cmap=cmap_U3, norm=norm)
                sm_U3.set_array([])
                cbar_U3 = plt.colorbar(sm_U3, ax=ax[1], orientation='horizontal')
                cbar_U3.set_label('U3 (mm)', fontsize=8)
                cbar_U3.ax.tick_params(labelsize=8)
                ax[0].set_xlabel('T (m)')
                ax[0].set_ylabel('Height (m)')
                ax[1].set_xlabel('T (m)')
                ax[1].set_ylabel('Height (m)')
                ax[0].set_aspect('equal')
                ax[1].set_aspect('equal')
                ax[0].set_xlim(-10,100)
                ax[1].set_xlim(-10, 100)
                ax[0].set_ylim(-65, 20)
                ax[1].set_ylim(-65, 20)
                plt.suptitle(f'{group}')
                plt.tight_layout()
                plt.savefig(self.fileLoc + f'{group}_{case}.png', dpi=300)


if __name__ == '__main__':
    fileLoc = r'C:\\Users\\abindal\\OneDrive - Nabih Youssef & Associates\\Documents\\00_Projects\\06_The Vault\\20240715 Models\\305 Static\\'
    fileName = fileLoc + '20240725_BaseDisplacement_305_Seq_StaticSpring.xlsx'
    caseList = ['1.0D+0.5L+TP', '1.0D+0.5L+TN']
    groupList = ['Base_S13A', 'Base_S12', 'Base_S12A', 'Base_S12B', 'Base_S12C', 'Base_S12D']
    baseDisp = BaseDisp(fileLoc, fileName, caseList, groupList)
    baseDisp.plotBaseDisp()

