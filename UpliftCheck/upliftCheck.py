from utils.readFile import *
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import cmcrameri.cm as cmc
import matplotlib.colors as mcolors

folderLoc = [r"C:\\Users\\abindal\\OneDrive - Nabih Youssef & Associates\\Documents\\00_Projects\\06_The Vault\\20240905_305\\",
             r"C:\\Users\\abindal\\OneDrive - Nabih Youssef & Associates\\Documents\\00_Projects\\06_The Vault\\",
             r"C:\\Users\\abindal\\OneDrive - Nabih Youssef & Associates\\Documents\\00_Projects\\06_The Vault\\"]
fileName = [r"20240905_305_LB_JointReaction.xlsx",
            r"20240911_205_UB_JointReactions.xlsx",
            r"20240906_302_JointReaction.xlsx"]
modelName = ['305_LB', '205_UB', '302']


# Read the excel file
class UpliftCheck:
    def __init__(self, folderLoc, fileName, modelName):
        self.conn = self.getConnection(folderLoc + fileName)
        self.modelName = modelName
        self.folderLoc = folderLoc

    def getConnection(self, file):
        data = connectDB(file)
        # Iterate through the generator to capture progress updates
        for update in data:
            if isinstance(update, dict) and 'progress' in update:
                print(update['message'])  # Handle progress reporting
            else:
                conn = update  # The connection will be yielded last
                break
        return conn


    def getReaction(self):
        reaction = getData(self.conn, query='SELECT "Joint", "OutputCase", "StepType", CAST("F1" AS NUMERIC) AS F1, CAST("F2" AS NUMERIC) AS F2, CAST("F3" AS NUMERIC) AS F3 FROM "Joint Reactions"')
        return reaction
    
    def getCoord(self):
        coord = getData(self.conn, query='SELECT "Joint", CAST("GlobalX" as NUMERIC) as X, CAST("GlobalY" as NUMERIC) as Y, CAST("GlobalZ" as NUMERIC) as Z FROM "Joint Coordinates"')
        return coord
    
    def drawGrid(self, ax):
        grids = getData(self.conn, query='SELECT "GridID", CAST("X1" as NUMERIC) AS x1, CAST("Y1" AS NUMERIC) AS y1, CAST("X2" as NUMERIC) AS x2, CAST("Y2" AS NUMERIC) AS y2 FROM "General Grids"')
        # Draw lines for each grid
        for i in range(len(grids)):
            grid = grids.iloc[i]
            ax.plot([grid['x1'], grid['x2']], [grid['y1'], grid['y2']], color='grey', linewidth=0.25, zorder=0)
            ax.annotate(grid['GridID'], (grid['x2'], grid['y2']), fontsize=6, color='black', ha='center',va='center')


    def getUplift(self):
        reaction = self.getReaction()
        coord = self.getCoord()
        uplift = reaction[reaction['f3']<0]
        # Create a bar plot of count of uplifts per OutputCase.
        upliftCount = uplift.groupby('OutputCase').count()[['Joint']]

        # Keep only the 'Joint' column and count the number of uplifts per Joint.
        # Show "Joint" as a column and "OutputCase" as a count.
        upliftJoint = uplift.groupby('Joint').count()[['OutputCase']]
        #Move the 'Joint' column to the index
        upliftJoint = upliftJoint.reset_index()
        #Rename the columns
        upliftJoint.columns = ['Joint', 'OutputCase']

        # Add other joints with no uplift. These are in reaction but not in uplift.
        # Get the joints that are not in uplift
        noUplift = reaction[~reaction['Joint'].isin(upliftJoint['Joint'])]
        #remove duplicates
        noUplift = noUplift.drop_duplicates(subset='Joint')
        # Count is 0 for these joints
        noUplift['OutputCase'] = 0
        upliftJoint = pd.concat([upliftJoint, noUplift[['Joint', 'OutputCase']]], ignore_index=True)


        # Join the upliftJoint with coord to get the coordinates of the uplift joints.
        upliftJoint = upliftJoint.join(coord.set_index('Joint'), on='Joint', how='left')


        return upliftCount, upliftJoint
    
    def plotUplift(self):
        upliftCount, upliftJoint = self.getUplift()
        norm = mcolors.Normalize(vmin=0, vmax=11)

        # Plot Uplift Joints in 2D plan view
        # Use a color map to represent the OutputCase the values are discrete from 0 to 11
        cmap = cmc.batlow
        fig, ax = plt.subplots()
        self.drawGrid(ax)
        # Add 1 to the value of upliftJoint to make it 1-based index
        ax.scatter(upliftJoint['x'], upliftJoint['y'], [2]*len(upliftJoint),
                   c=upliftJoint['OutputCase'], cmap=cmap,
                   vmin=0, vmax=11)
        # Annotate
        for i, txt in enumerate(upliftJoint.index):
            output_case = upliftJoint['OutputCase'][i]
            color = cmap(norm(output_case))
            # Calculate luminance to decide text color (white or black)
            luminance = 0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2]
            text_color = 'white' if luminance < 0.5 else 'black'
            ax.annotate(upliftJoint['OutputCase'][i], (upliftJoint['x'][i], upliftJoint['y'][i]), fontsize=2, color=text_color, ha='center',va='center')
        ax.set_title(f'Locations with uplift: Model {self.modelName}')
        ax.axis('equal')
        # Hide axis
        ax.axis('off')
       
        # Add a LEGEND WITH THE OUTPUT CASE VALUES. USE COLOR MAP TO REPRESENT THE OUTPUT CASE
        # Create a list of patches
        patches = [plt.Line2D([0], [0], marker='o', color=cmap(norm(i)), label=f'{i}', 
                      markersize=8, linestyle='') for i in range(0, 12)]
        ax.legend(handles=patches, title='Number of Uplift Case', loc='best', ncol=3,markerscale=0.7, fontsize='small', title_fontsize='small')
        plt.tight_layout()
        plt.savefig(self.folderLoc + self.modelName + '_UpliftJointsLoc.png', dpi=600)

        # Plot Uplift count per OutputCase
        fig, ax = plt.subplots()
        ax.bar(upliftCount.index, upliftCount['Joint'], color='red')
        ax.set_title(f'Uplift Joints per Load Case: Model {self.modelName}')
        ax.set_ylabel('Number of Joints')
        ax.set_xlabel('Load Case')
        ax.tick_params(axis='both', labelsize=6)
        plt.tight_layout()
        plt.savefig(self.folderLoc + self.modelName + '_UpliftCount.png', dpi=300)
        #upliftCount.plot(kind='bar', y='Joint', 
        #                 title='Uplift Joints per Load Case',
        #                 ylabel='Number of Joints', 
        #                 xlabel='Load Case',
        #                 legend=False,
        #                 color='red')
        

        #plt.tight_layout()
        #plt.savefig(self.folderLoc + self.modelName + '_UpliftCount.png', dpi=150)
    


if __name__ == '__main__':
    for i in range(0,3):
        uplift = UpliftCheck(folderLoc[i], fileName[i], modelName[i])
        uplift.plotUplift()