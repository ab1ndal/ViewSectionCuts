import pandas as pd
from pandasql import sqldf
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import matplotlib.colors as mcolors
import random
import distinctipy
import numpy as np
from fpdf import FPDF
from PyPDF2 import PdfMerger
import os

folder = r'C:\\Users\\abindal\\OneDrive - Nabih Youssef & Associates\\Documents - The Vault\\Calculations\\2025 -  Stage 3C\\205 - Model Results\\20250310_205\\Foundation Movements\\'
modelName = '205_LB'
plotSections = False
plotLinks = False
plotDisp = True
plotRxns = False
# Needs this file to contain the 'Jt Displacements - Generalized' sheet
DispFile = '20250310_205_LB_FoundationMovt.xlsx'
inUnit = 'mm'
outUnit = 'mm' 
# Needs this file to contain the ''Joint Reactions'' sheet
RxnFile = '2025.02.03 - 305 LB Overall Base Reactions (Coarse Mesh).xlsx'
unitDict = {'mm': 1, 'm': 1000, 'in': 25.4, 'ft': 304.8}
color_map_name = 'rainbow'

def convert_units(value, inUnit, outUnit):
    return value * unitDict[inUnit] / unitDict[outUnit]

def get_colors(n, exclusion_list = [(1,1,1), (0,1,1)]):
    return distinctipy.get_colors(n_colors = n, exclude_colors = exclusion_list, rng = random.seed(1))


def read_file(file_path, sheet_name, colNames=None):
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=1)
        df = df[1:]
        if colNames:
            df=df[colNames]
        return df
    except Exception as e:
        print(e)
        return None

def plot_rxn(ax, caseName, GMid, scale, jointRxns):
    norm = plt.Normalize(vmin=jointRxns[caseName].min(), vmax=jointRxns[caseName].max())
    col_map = plt.cm.RdYlGn_r
    query = f"Select Joint, {caseName}, GlobalX, GlobalY from jointRxns where OutputCase = '{GMid}'"
    rxns = sqldf(query, locals())
    if not rxns.empty:
        max_rxn, min_rxn = rxns[caseName].max(), rxns[caseName].min()
        ax.scatter(rxns.GlobalX, rxns.GlobalY, 
                        s=rxns[caseName] * scale,  # Marker size
                        c=rxns[caseName],  # Color mapping
                        cmap=col_map, norm=norm, 
                        edgecolors='black', linewidths=0.1)
        # Show min and max values at bottom right corner
        ax.annotate(f'Max: {max_rxn:.2f} {units}', xy=(0.95, 0.05), xycoords='axes fraction', fontsize=4, ha='right', va='bottom')
        ax.annotate(f'Min: {min_rxn:.2f} {units}', xy=(0.95, 0.1), xycoords='axes fraction', fontsize=4, ha='right', va='bottom')
        # add color bar
        #cbar = plt.colorbar(ax, orientation='horizontal', fraction=0.046, pad=0.04)
        #cbar.set_label(f'{caseName} ({units})')

        #tick_values = np.linspace(min_rxn, max_rxn, num=10)  # 10 evenly spaced ticks
        #cbar.set_ticks(tick_values)
        #cbar.set_ticklabels([f"{int(val)}" for val in tick_values])


    else:
        print(f"No data for {caseName} {GMid}")
    return max_rxn, min_rxn


def plot_disp(ax, caseName, GMid, scale, jointDisp):
    # Color from red to Green where red is max green is 0
    #norm = plt.Normalize(vmin=jointDisp["Translation"].min(), vmax=jointDisp["Translation"].max())
    bounds = np.linspace(0, 60, 15)
    cmap = plt.get_cmap(color_map_name, len(bounds)-1)
    norm = mcolors.BoundaryNorm(bounds, cmap.N, clip=True)


    #col_map = plt.cm.RdYlGn_r
    query = f"Select Joint, Translation, GlobalX, GlobalY from jointDisp where DispType = '{caseName}' and OutputCase = '{GMid}'"
    disp = sqldf(query, locals())
    #if caseName == 'U3n':
    #    scale = 2*scale
    if not disp.empty:
        max_disp, min_disp = disp["Translation"].max(), disp["Translation"].min()
        ax.scatter(disp.GlobalX, disp.GlobalY, 
                        s=disp.Translation * scale,  # Marker size
                        c=disp.Translation,  # Color mapping
                        cmap=cmap, norm=norm, edgecolors = 'black', linewidths=0.05)
        # Show min and max values at bottom right corner
        ax.annotate(f'Max: {max_disp:.2f} {outUnit}', xy=(0.95, 0.05), xycoords='axes fraction', fontsize=4, ha='right', va='bottom')
        ax.annotate(f'Min: {min_disp:.2f} {outUnit}', xy=(0.95, 0.1), xycoords='axes fraction', fontsize=4, ha='right', va='bottom')
    else:
        print(f"No data for {caseName} {GMid}")
    return max_disp, min_disp


path = folder + '20250310_205_LinkAssignments.xlsx'
sheet = 'Area Spring Assignments'
areaAssigns = read_file(path, sheet, colNames=['Area', 'LinkProp'])
print(areaAssigns.head())

sheet = 'Area Section Assignments'
sectionAssigns = read_file(path, sheet, colNames=['Area', 'Section'])
print(sectionAssigns.head())

sheet = 'Connectivity - Area'
areasCoord = read_file(path, sheet, colNames=['Area', 'NumJoints', 'Joint1', 'Joint2', 'Joint3', 'Joint4'])
print(areasCoord.head())

sheet = 'Joint Coordinates'
jointCoord = read_file(path, sheet, colNames=['Joint', 'GlobalX', 'GlobalY'])
print(jointCoord.head())

query = 'Select areasCoord.*, p1.GlobalX as x1, p1.GlobalY as y1, p2.GlobalX as x2, p2.GlobalY as y2, p3.GlobalX as x3, p3.GlobalY as y3, p4.GlobalX as x4, p4.GlobalY as y4 ' \
        'from areasCoord '\
        'left join jointCoord as p1 on areasCoord.Joint1 = p1.Joint '\
        'left join jointCoord as p2 on areasCoord.Joint2 = p2.Joint '\
        'left join jointCoord as p3 on areasCoord.Joint3 = p3.Joint '\
        'left join jointCoord as p4 on areasCoord.Joint4 = p4.Joint'
slabCoord = sqldf(query, locals())
# get slabs that are assigned to a foundation section i.e. FND in the name of the section
query = 'Select slabCoord.*, Section, LinkProp '\
        'from slabCoord '\
        'left join sectionAssigns on slabCoord.Area = sectionAssigns.Area '\
        'left join areaAssigns on slabCoord.Area = areaAssigns.Area '\
        'where Section like \'%-F%\''
slabCoord = sqldf(query, locals())
# replace nan values with empty string in column Section, LinkProp
slabCoord['Section'] = slabCoord['Section'].fillna('Unassigned')
slabCoord['LinkProp'] = slabCoord['LinkProp'].fillna('Unassigned')
print(len(slabCoord))

gridCoord = read_file(path, 'General Grids', colNames=['GridID', 'X1', 'Y1', 'X2', 'Y2'])
def draw_grid(ax, gridCoord):
    for i in range(len(gridCoord)):
        ax.plot([gridCoord.X1[i+1], gridCoord.X2[i+1]], [gridCoord.Y1[i+1], gridCoord.Y2[i+1]], 
                color='grey', linewidth=0.15, linestyle='--', zorder=0)
        ax.annotate(gridCoord.GridID[i+1], 
                    (gridCoord.X1[i+1], gridCoord.Y1[i+1]), ha = 'center', va = 'center', size = 2,
                    bbox = dict(boxstyle = "circle,pad=0.3", fc = 'white', ec = 'black', lw=0.2, alpha = 0.5), zorder = 0)
    return
def draw_slab(ax, slabCoord, **kwargs):
    print('making slab plot')
    print(slabCoord.head())
    if 'plot_section' in kwargs:
        legend_list = slabCoord.Section.unique()
        col_list = get_colors(len(legend_list))
        plotCol = 'Section'
        alpha = 0.3

    elif 'plot_single' in kwargs:
        legend_list = slabCoord.Section.unique()
        col_list = len(legend_list)*get_colors(1)
        plotCol = 'Section'
        alpha = 0.1
    
    elif 'plot_link' in kwargs:
        legend_list = slabCoord.LinkProp.unique()
        col_list = get_colors(len(legend_list))
        plotCol = 'LinkProp'
        alpha = 0.3

    # SORT LEGEND LIST
    #print(legend_list)
    legend_list = list(legend_list)
    legend_list.sort(key=str.lower)
    
    col_map = {}
    for s_i, s in enumerate(legend_list):
        col_map[s] = col_list[s_i]
    
    col_map['Unassigned'] = (1, 1, 1)

    for i in range(len(slabCoord)):
        if slabCoord.NumJoints[i] == 4.0:
            vertices = [[slabCoord.x1[i], slabCoord.y1[i]], 
                        [slabCoord.x2[i], slabCoord.y2[i]], 
                        [slabCoord.x3[i], slabCoord.y3[i]], 
                        [slabCoord.x4[i], slabCoord.y4[i]], 
                        [slabCoord.x1[i], slabCoord.y1[i]]]
            
            
        else:
            vertices = [[slabCoord.x1[i], slabCoord.y1[i]], 
                        [slabCoord.x2[i], slabCoord.y2[i]], 
                        [slabCoord.x3[i], slabCoord.y3[i]], 
                        [slabCoord.x1[i], slabCoord.y1[i]]]
            

        if slabCoord['LinkProp'][i] and 'MLP' in slabCoord['LinkProp'][i]:
            linewidth = 0.5
        else:
            linewidth = 0.25
        poly = Polygon(vertices, facecolor = col_map[slabCoord[plotCol][i]], alpha = alpha, edgecolor = (0,0,0,1), 
                       linewidth=linewidth, antialiased=True)
        ax.add_patch(poly)
    ax.set_aspect('equal')
    return col_map

##############################################################
#  plot slabs that are assigned to a specific section
if plotSections:
    print("Plotting slabs assigned to a specific section")
    fig, ax = plt.subplots(figsize=(8, 4))
    plt.rcParams['savefig.dpi'] = 900
    col_map = draw_slab(ax, slabCoord, plot_section = True)
    draw_grid(ax, gridCoord)
    # Hide axes
    ax.set_xticks([])
    ax.set_yticks([])
    #show legend using col_map
    handles = [plt.Rectangle((0,0),1,1, facecolor=col_map[label], alpha = 0.3, edgecolor = 'black', linewidth = 0.25) for label in col_map]
    ax.legend(handles, col_map.keys(), loc='lower right', fontsize=4, title_fontsize=6, title='Sections', frameon=False)
    ax.set_title(f'Slabs Assigned to Foundation Sections (Model {modelName})')
    plt.tight_layout()
    plt.savefig(folder + modelName + 'slabs_assigned_to_section.png', dpi=900, bbox_inches='tight', transparent=False)

###############################################################
# plot slabs that are assigned to a specific link property
if plotLinks:
    print("Plotting slabs assigned to a specific link property")
    fig, ax = plt.subplots(figsize=(8, 4))
    plt.rcParams['savefig.dpi'] = 900
    col_map = draw_slab(ax, slabCoord, plot_link = True)
    draw_grid(ax, gridCoord)
    # Hide axes
    ax.set_xticks([])
    ax.set_yticks([])
    #show legend using col_map
    handles = [plt.Rectangle((0,0),1,1, facecolor=col_map[label], alpha = 0.3, edgecolor = 'black', linewidth = 0.25) for label in col_map]
    ax.legend(handles, col_map.keys(), loc='lower right', 
            ncol=2, fontsize=3, title_fontsize=4, 
            title='Link Properites', frameon=False)
    ax.set_title(f'Slabs Assigned to Link Properties (Model {modelName})')
    plt.tight_layout()
    plt.savefig(folder + modelName + 'slabs_assigned_to_links.png', dpi=900, bbox_inches='tight', transparent=False)


#########################################    Create Joint Reaction Plot   ########################################
if plotRxns:
    print("Plotting slabs with joint reactions")
    envRxnsFile = folder + RxnFile
    sheet = 'Joint Reactions'
    jointRxns = read_file(envRxnsFile, sheet, colNames=['Joint', 'OutputCase', 'F1', 'F2', 'F3'])
    jointRxns['F1'] = jointRxns['F1'].abs()
    jointRxns['F2'] = jointRxns['F2'].abs()

    jointRxns = jointRxns.groupby(['Joint', 'OutputCase'], as_index=False)[['F1', 'F2', 'F3']].max()
    avgRxn = jointRxns.groupby(['Joint'], as_index=False)[['F1', 'F2', 'F3']].mean()
    avgRxn['OutputCase'] = 'Average'
    jointRxns = pd.concat([jointRxns, avgRxn], ignore_index=True)
    # Round off to integer fir joint reactions F1 F2 F3
    jointRxns['F1'] = jointRxns['F1'].round(0)
    jointRxns['F2'] = jointRxns['F2'].round(0)
    jointRxns['F3'] = jointRxns['F3'].round(0)
    jointRxns.fillna(0, inplace=True)

    query = 'Select jointRxns.*, GlobalX, GlobalY from jointRxns inner join jointCoord where jointRxns.Joint = jointCoord.Joint'
    jointRxns = sqldf(query, locals())
    units = 'kN'
    scale = 0.0001
    loadCaseList = jointRxns.OutputCase.unique()

    pdfs = []
    boundListRn = {}
    for GMid in loadCaseList:
        print(f"Plotting joint reactions for {GMid}")
        fig, ax = plt.subplots(figsize=(8, 8), nrows=2, ncols=2, constrained_layout=True)
        plt.rcParams['savefig.dpi'] = 1200
        # flatten ax
        ax = ax.flatten()
        [draw_slab(ax[i], slabCoord, plot_single = True, color = 'lightgrey') for i in range(3)]
        [draw_grid(ax[i], gridCoord) for i in range(3)]
        # Hide axes
        [ax[i].set_xticks([]) for i in range(4)]
        [ax[i].set_yticks([]) for i in range(4)]
        # plot joint reactions
        boundListRn[GMid] = {}
        for i in range(3):
            max_val, min_val = plot_rxn(ax[i], f'F{i+1}', GMid, scale, jointRxns)
            boundListRn[GMid][f'F{i+1}'] = (max_val, min_val)
        ax[0].set_title(f'Joint Reaction [F1] (Absolute)')
        ax[1].set_title(f'Joint Reaction [F2] (Absolute)')
        ax[2].set_title(f'Joint Reaction [F3] (Absolute)')
        plt.suptitle(f'Joint Reactions (Model {modelName}) [{GMid}]')
        # Show a colorbar
        #vmin, vmax = jointRxns.F1.min(), jointRxns.F1.max()
        #sm = plt.cm.ScalarMappable(cmap=plt.cm.RdYlGn_r, norm=plt.Normalize(vmin=vmin, vmax=vmax))
        #sm.set_array([])  

        # Create the colorbar
        #cbar = plt.colorbar(sm, ax=ax, orientation='horizontal', fraction=0.046, pad=0.04)
        #cbar.set_label(f'Reaction ({units})')

        # Set colorbar ticks and labels
        #tick_values = np.linspace(vmin, vmax, num=10)  # 5 evenly spaced ticks
        #cbar.set_ticks(tick_values)
        #cbar.set_ticklabels([f"{int(val)}" for val in tick_values])
        plt.savefig(f'{folder}/{modelName}_slabs_joint_reaction_{GMid}.pdf', dpi=1200, bbox_inches='tight', transparent=False)
        pdfs.append(f'{folder}/{modelName}_slabs_joint_reaction_{GMid}.pdf')
        plt.close()


######################################### Create Joint Displacement Plots ########################################
if plotDisp:
    print("Plotting slabs with joint displacements")
    envDispFile = folder + DispFile
    sheet = 'Jt Displacements - Generalized'
    jointDisp = read_file(envDispFile, sheet, colNames=['GenDispl', 'OutputCase', 'Translation'])
    # Support Group is first 4 digits
    # DispType is the last 2 digits
    # Everything else is the joint number
    jointDisp['Joint'] = jointDisp.GenDispl.str.slice(5,-3)
    jointDisp['DispType'] = jointDisp.GenDispl.str.extract(r'-(\w+)$')
    #jointDisp['SupportGroup'] = jointDisp.GenDispl.str.extract(r'^SP(\d+)-')

    # take absolute value of translation if DispType is U1, U2
    #jointDisp.loc[jointDisp.DispType.isin(['U1', 'U2']), 'Translation'] = jointDisp.Translation.abs()

    # If DispType is U3, make it U3p is positive, U3n if negative
    jointDisp.loc[(jointDisp['DispType'] == 'U1') & (jointDisp['Translation'] >= 0), 'DispType'] = 'U1p'
    jointDisp.loc[(jointDisp['DispType'] == 'U1') & (jointDisp['Translation'] < 0), 'DispType'] = 'U1n'
    
    jointDisp.loc[(jointDisp['DispType'] == 'U2') & (jointDisp['Translation'] >= 0), 'DispType'] = 'U2p'
    jointDisp.loc[(jointDisp['DispType'] == 'U2') & (jointDisp['Translation'] < 0), 'DispType'] = 'U2n'

    jointDisp.loc[(jointDisp['DispType'] == 'U3') & (jointDisp['Translation'] >= 0), 'DispType'] = 'U3p'
    jointDisp.loc[(jointDisp['DispType'] == 'U3') & (jointDisp['Translation'] < 0), 'DispType'] = 'U3n'

    # Drop  GenDispl
    jointDisp.drop(columns=['GenDispl'], inplace=True)

    # Take absolute max of translation for each joint, output case, DispType
    jointDisp['Translation'] = jointDisp['Translation'].abs()

    # apply unit conversion
    jointDisp['Translation'] = jointDisp['Translation'].apply(convert_units, args=(inUnit, outUnit))

    jointDisp = jointDisp.groupby(['Joint', 'OutputCase', 'DispType'], as_index=False)['Translation'].max()

    jointDisp = jointDisp.pivot_table(index=['Joint', 'OutputCase'], columns='DispType', values='Translation', aggfunc='first').fillna(0)
    jointDisp = jointDisp.reset_index().melt(id_vars=['Joint', 'OutputCase'], var_name='DispType', value_name='Translation')

    #average_disp = jointDisp.groupby(['Joint', 'DispType'], as_index=False)['Translation'].mean()
    #average_disp['OutputCase'] = 'Average'

    #jointDisp = pd.concat([jointDisp, average_disp], ignore_index=True)

    max_disp = jointDisp.groupby(['Joint', 'DispType'], as_index=False)['Translation'].max()
    max_disp['OutputCase'] = 'Max'
    jointDisp = pd.concat([jointDisp, max_disp], ignore_index=True)

    #Join with jointCoord to get GlobalX, GlobalY
    jointDisp = pd.merge(jointDisp, jointCoord, left_on='Joint', right_on='Joint', how='left')
    print(jointDisp)
    units = outUnit
    scale = 0.2
    loadCaseList = jointDisp.OutputCase.unique()
    caseList = ['U1p', 'U1n', 'U2p', 'U2n', 'U3p', 'U3n']
    pdfs = []

    boundList = {}

    for GMid in loadCaseList:
        print(f"Plotting joint displacements for {GMid}")
        fig, ax = plt.subplots(figsize=(5, 8), nrows=3, ncols=2, constrained_layout=True)
        plt.rcParams['savefig.dpi'] = 1200
        # flatten ax
        ax = ax.flatten()
        [draw_slab(ax[i], slabCoord, plot_single = True, color = 'lightgrey') for i in range(6)]
        [draw_grid(ax[i], gridCoord) for i in range(6)]
        # Hide axes
        [ax[i].set_xticks([]) for i in range(6)]
        [ax[i].set_yticks([]) for i in range(6)]
        # plot joint displacements
        boundList[GMid] = {}
        for i in range(6):
            max_val, min_val = plot_disp(ax[i], caseList[i], GMid, scale, jointDisp)
            boundList[GMid][caseList[i]] = (max_val, min_val)
        ax[0].set_title(f'Relative Joint Displacement [U1] (Positive)', fontsize=5)
        ax[1].set_title(f'Relative Joint Displacement [U1] (Negative)', fontsize=5)
        ax[2].set_title(f'Relative Joint Displacement [U2] (Positive)', fontsize=5)        
        ax[3].set_title(f'Relative Joint Displacement [U2] (Negative)', fontsize=5)
        ax[4].set_title(f'Relative Joint Displacement [U3] (Positive)', fontsize=5)
        ax[5].set_title(f'Relative Joint Displacement [U3] (Negative)', fontsize=5)
        plt.suptitle(f'Relative Joint Displacement (Model {modelName}) [{GMid}]', fontsize=8)
        # Show a colorbar
        vmin, vmax = jointDisp.Translation.min(), jointDisp.Translation.max()
        bounds = np.linspace(0, 60, 15)
        cmap = plt.get_cmap(color_map_name, len(bounds)-1)
        norm = mcolors.BoundaryNorm(bounds, cmap.N, clip=True)

        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        #sm = plt.cm.ScalarMappable(cmap=plt.cm.RdYlGn_r, norm=plt.Normalize(vmin=vmin, vmax=vmax))
        sm.set_array([])  

        # Create the colorbar
        cbar = plt.colorbar(sm, ax=ax, orientation='horizontal', fraction=0.046, pad=0.04)
        cbar.set_label(f'Displacement ({units})')

        # Set colorbar ticks and labels
        #tick_values = np.linspace(0, 30, num=10)  # 10 evenly spaced ticks

        cbar.set_ticks(bounds)
        cbar.set_ticklabels([f"{int(val)}" for val in bounds])
        plt.savefig(f'{folder}/{modelName}_slabs_jointDisp_{GMid}.pdf', dpi=1200, bbox_inches='tight', transparent=False)
        pdfs.append(f'{folder}/{modelName}_slabs_jointDisp_{GMid}.pdf')
        plt.close()

    # Create a table of max and min values for each case and each displacement and put it in a pdf
    pdf = FPDF(format = 'letter')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=8)

    # Title
    pdf.cell(200, 10, f"Model {modelName} - Relative Joint Displacements ({units})", 0, 1, 'C')
    pdf.ln(10)

    # Set font size for table
    pdf.set_font("Arial", size=8)

    # Define column widths
    col_widths = [40] + [25] * len(caseList) * 2  # GMid + (Min/Max for each case)

    # Header Row with Borders
    pdf.cell(col_widths[0], 10, "Output Case", 1, 0, 'C')
    for case in caseList:
        pdf.cell(col_widths[2], 10, f"{case}", 1, 0, 'C')
    pdf.ln()

    # Data Rows with Borders
    for GMid in loadCaseList:
        pdf.cell(col_widths[0], 10, GMid, 1, 0, 'C')  # Output Case column
        for case in caseList:
            max_val, min_val = boundList[GMid][case]  # Get min/max values
            #pdf.cell(col_widths[1], 10, f"{min_val:.2f}", 1, 0, 'C')
            pdf.cell(col_widths[2], 10, f"{max_val:.2f}", 1, 0, 'C')
        pdf.ln()

    # Save PDF
    pdf.output(f'{folder}/{modelName}_slabs_jointDisp_table.pdf')
    # add to pdfs list in the beginning
    pdfs.insert(0, f'{folder}/{modelName}_slabs_jointDisp_table.pdf')

    # Combine all pdfs into a single pdf
    merger = PdfMerger()
    for pdf in pdfs:
        merger.append(pdf)
    merger.write(f'{folder}/{modelName}_Foundation_JointDisp.pdf')
    merger.close()

    for pdf in pdfs:
        os.remove(pdf)
    print("Done")

