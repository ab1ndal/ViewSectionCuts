from utils.readFile import *
import matplotlib.pyplot as plt
import glob
from PIL import Image

class BaseDisp:
    def __init__(self, fileLoc, fileName, caseList, groupList):
        self.fileLoc = fileLoc
        self.fileName = fileName
        self.db = getConnection(fileName)
        self.caseList = caseList
        self.groupList = groupList
        
    def getJointDisp(self, groupName):
        query = f"""
        WITH aggregated_disp AS(
            SELECT "Joint",
                "OutputCase",
               MAX(CAST("U1" AS NUMERIC))*1000 AS "U1max", 
               MAX(CAST("U2" AS NUMERIC))*1000 AS "U2max",
               MAX(CAST("U3" AS NUMERIC))*1000 AS "U3max",
                MIN(CAST("U1" AS NUMERIC))*1000 AS "U1min",
                MIN(CAST("U2" AS NUMERIC))*1000 AS "U2min",
                MIN(CAST("U3" AS NUMERIC))*1000 AS "U3min" 
            FROM "Joint Displacements" AS "Disp"
            WHERE "Joint" IN (
                SELECT "ObjectLabel"
                FROM "Groups 2 - Assignments"
                WHERE "GroupName" = '{groupName}' AND "ObjectType" = 'Joint'
            ) AND "OutputCase" IN ('{"','".join(self.caseList)}')
            GROUP BY "Joint", "OutputCase"
        ),
        min_coord AS (
            SELECT MAX(CAST("XorR" AS FLOAT)) AS "Xmax",
                   MAX(CAST("Y" AS FLOAT)) AS "Ymax"
            FROM "Joint Coordinates"
            WHERE "Joint" IN (
                SELECT "ObjectLabel"
                FROM "Groups 2 - Assignments"
                WHERE "GroupName" = '{groupName}' AND "ObjectType" = 'Joint'
            )
        )
        SELECT agg."Joint", 
               ROUND(CAST(SQRT(POWER(CAST("Coord"."XorR" AS FLOAT) - min_coord."Xmax", 2) + 
               POWER(CAST("Coord"."Y" AS FLOAT) - min_coord."Ymax", 2)) AS NUMERIC), 2) AS "T",
               ROUND(CAST("Z" AS NUMERIC), 2) AS "Z",
               agg."OutputCase",
               agg."U1min",
               agg."U1max",
               agg."U2min",
               agg."U2max",
               agg."U3min",
               agg."U3max"
        FROM aggregated_disp AS agg
        INNER JOIN "Joint Coordinates" AS "Coord"
        ON agg."Joint" = "Coord"."Joint"
        CROSS JOIN min_coord
        ORDER BY "Z" DESC, "T" DESC        
        """
        return getData(self.db, query=query)
    
    def plotBaseDisp(self,sf=10):
        #set colorscale for the arrow colors
        # colors maps values from -20 to +20 to colors red to blue
        cmap_U3 = plt.cm.RdYlGn_r
        cmap_U2 = plt.cm.RdYlGn
        norm = plt.Normalize(-10, 10)

        for group in self.groupList:
            df = self.getJointDisp(group)
            print(f'Group: {group}')
            print(f'max U2: {df["U2max"].max()}, min U2: {df["U2min"].min()}, max U3: {df["U3max"].max()}, min U3: {df["U3min"].min()}')
            for case in self.caseList:
                fig, ax = plt.subplots(1,2, figsize=(10,4))
                dfCase = df[df['OutputCase'] == case].reset_index(drop=True)
                # Sort by Z DESC and then T ASC
                dfCase = dfCase.sort_values(by=['Z', 'T'], ascending=[True,True])
                #dfCase = dfCase.sort_values(by=['Z'], ascending=[True])
                ax[0].plot(dfCase["T"], dfCase["Z"], color = 'black', linewidth=0.5)
                ax[1].plot(dfCase["T"], dfCase["Z"], color = 'black', linewidth=0.5)
                # draw arrows at each point to show the direction of the displacement
                ax[0].plot(dfCase["T"]-dfCase["U2min"]/1000*sf, dfCase["Z"], color='red',linewidth=0.5)
                ax[0].plot(dfCase["T"]-dfCase["U2max"]/1000*sf, dfCase["Z"], color='blue',linewidth=0.5)
                ax[1].plot(dfCase["T"], dfCase["Z"]+dfCase["U3min"]/1000*sf, color='red',linewidth=0.5)
                ax[1].plot(dfCase["T"], dfCase["Z"]+dfCase["U3max"]/1000*sf, color='blue',linewidth=0.5)
                #for i in range(len(dfCase)):
                #    u2Color = cmap_U2(norm(dfCase["U2max"].iloc[i]))
                #    u3Color = cmap_U3(norm(dfCase["U3max"].iloc[i]))
                #    ax[0].arrow(dfCase["T"].iloc[i], dfCase["Z"].iloc[i], dfCase["U2max"].iloc[i], 0, head_width=0.1, head_length=0.1, fc=u2Color, ec=u2Color)
                #    ax[1].arrow(dfCase["T"].iloc[i], dfCase["Z"].iloc[i], 0, dfCase["U3max"].iloc[i], head_width=0.1, head_length=0.1, fc=u3Color, ec=u3Color)
                
                ax[0].set_title(f'{case} - U2')
                ax[1].set_title(f'{case} - U3')
                # Add min max values to the plot as a text in the top left corner
                ax[0].text(0.05, 0.95, f'Max U2: {dfCase["U2max"].max():.2f} mm\nMin U2: {dfCase["U2min"].min():.2f} mm', transform=ax[0].transAxes, fontsize=8, verticalalignment='top')
                ax[1].text(0.05, 0.95, f'Max U3: {dfCase["U3max"].max():.2f} mm\nMin U3: {dfCase["U3min"].min():.2f} mm', transform=ax[1].transAxes, fontsize=8, verticalalignment='top')
                #Show colorbar
                #sm_U2 = plt.cm.ScalarMappable(cmap=cmap_U2, norm=norm)
                #sm_U2.set_array([])
                #cbar_U2 = plt.colorbar(sm_U2, ax=ax[0], orientation='horizontal')
                #cbar_U2.set_label('U2 (mm)', fontsize=8)
                #cbar_U2.ax.tick_params(labelsize=8)
                #sm_U3 = plt.cm.ScalarMappable(cmap=cmap_U3, norm=norm)
                #sm_U3.set_array([])
                #cbar_U3 = plt.colorbar(sm_U3, ax=ax[1], orientation='horizontal')
                #cbar_U3.set_label('U3 (mm)', fontsize=8)
                #cbar_U3.ax.tick_params(labelsize=8)
                ax[0].set_xlabel('Wall Length (m)')
                ax[0].set_ylabel('Height (m)')
                ax[1].set_xlabel('Wall Length (m)')
                ax[1].set_ylabel('Height (m)')
                ax[0].set_aspect('equal')
                ax[1].set_aspect('equal')
                ax[0].set_xlim(-10,100)
                ax[1].set_xlim(-10, 100)
                ax[0].set_ylim(-70, 30)
                ax[1].set_ylim(-70, 30)
                plt.suptitle(f'{group} - Scale Factor: {sf}')
                plt.tight_layout()
                plt.savefig(self.fileLoc + f'{group}_{case}.png', dpi=300)


def save_images_as_pdf(fileLoc, groupList):
    for group in groupList:
        fileName = fileLoc + f'{group}_Movement.pdf'
        # Find all png files for the group
        pngFiles = glob.glob(fileLoc + f'{group}_*.png')
        pngFiles.sort()

        # Open all the images
        images = [Image.open(png) for png in pngFiles]
        img_width, img_height = images[0].size  # Assuming all images are of the same size

        # Create a list to hold the PDF pages
        pdf_pages = []

        # Create a 2x1 grid (2 images per page)
        for i in range(0, len(images), 2):
            # Create a blank page of appropriate size to hold 2 images in a 2x1 grid (white background)
            grid_img = Image.new('RGB', (img_width, img_height * 2), color=(255, 255, 255))

            # Paste up to 2 images in the grid
            for j in range(2):
                if i + j < len(images):
                    # Calculate the position for the image in the grid (top or bottom)
                    y_offset = j * img_height
                    grid_img.paste(images[i + j], (0, y_offset))

            # Append the grid image to the list of PDF pages
            pdf_pages.append(grid_img)

        # Save the images as a PDF with white background
        pdf_pages[0].save(fileName, save_all=True, append_images=pdf_pages[1:], resolution=600)






if __name__ == '__main__':
    fileLoc = r'C:\\Users\\abindal\\OneDrive - Nabih Youssef & Associates\\Documents\\00_Projects\\06_The Vault\\305\\20240918\\'
    fileName = fileLoc + '20240918_305_BaseJointDisp.xlsx'
    #caseList = ['1.0D+0.5L+TP', '1.0D+0.5L+TN']
    caseList = ['MCE-GM01','MCE-GM02', 'MCE-GM03',
                'MCE-GM04', 'MCE-GM05', 'MCE-GM06',
                'MCE-GM07', 'MCE-GM08', 'MCE-GM09',
                'MCE-GM10', 'MCE-GM11']
    groupList = ['Base_S13A', 'Base_S12', 'Base_S12A', 'Base_S12B', 'Base_S12C', 'Base_S12D']
    #baseDisp = BaseDisp(fileLoc, fileName, caseList, groupList)
    #baseDisp.plotBaseDisp(sf=20)
    save_images_as_pdf(fileLoc, groupList)

