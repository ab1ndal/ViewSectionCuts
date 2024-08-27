from dash import Dash, html, dash_table, dcc, Input, Output, callback, callback_context, no_update, State
import pandas as pd
from utils.readFile import connectDB, getData
from SectionCutForces.plotGlobalForces import getCutForces, getCutGroup
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import dash_mantine_components as dmc
import distinctipy
import plotly.io as pio
import base64
import io
import os
from utils.appComponents import createUploadComponent, createMultiSelectComponent, createTextInputComponent, createNumberInputComponent, createSelectComponent, createSingleNumberInputComponent, createRadioComponent
from GeneralizedDisplacement.defineGenDisp import defineGenDisp
from GeneralizedDisplacement.plotGenDisp import GeneralizedDisplacement
from utils.unitConvertor import UnitConvertor
from utils.extraTools import wrap_text


class GlobalAnalysisApp:
    def __init__(self):
        self.app = Dash(__name__)
        self.app.config.suppress_callback_exceptions = True
        #server = app.server
        self.AXIS_TITLE_FONT = dict(size=14)
        self.PLOT_TITLE_FONT = dict(size=20)
        self.OVERALL_PLOT_TITLE_FONT = {'size':25}
        self.TICK_FONT = dict(size=12)
        self.LEGEND_FONT = dict(size=14)
        self.conn = None
        self.height_data = None
        self.port = 8050
        self.server = self.app.server
        self.allLegendList = []

        # Create subplots
        self.fig = make_subplots(rows=2, cols=3, subplot_titles=('F1 (A-Canyon)', 'F2 (X-Canyon)', 'F3 (Vertical)', 'M2 (A-Canyon)', 'M1 (X-Canyon)', 'M3'),
                                 vertical_spacing=0.1, horizontal_spacing=0.1, specs=[[{"secondary_y": True}, {"secondary_y": True}, {"secondary_y": True}],
                                                                                      [{"secondary_y": True}, {"secondary_y": True}, {"secondary_y": True}]])
        self.createMenu()
        #self.createLayout()
        self.registerCallbacks()
        
    def createMenu(self):
        self.app.layout = dmc.MantineProvider(
            theme={"colorScheme": "light"},
            children = [
                dcc.Store(id='file-upload-status'),
                dmc.Title("Global Building Responses", c="blue", size="h2"),
                dmc.Tabs(
                    [
                        dmc.TabsList(
                            [
                                dmc.Tab("Section Cuts", value="section-cuts"),
                                dmc.Tab("Drifts", value="drifts"),
                            ]
                        ),
                        dmc.TabsPanel(
                            children=[
                                dmc.Tabs(
                                    [dmc.TabsList(
                                        [dmc.Tab("Define", value="define-section-cuts"),
                                        dmc.Tab("Visualize", value="visualize-section-cuts")]
                                    ),
                                    dmc.TabsPanel(id = 'define-section-cuts', value="define-section-cuts"),
                                    dmc.TabsPanel(id = 'visualize-section-cuts', value="visualize-section-cuts")
                                    ],
                                    color = "blue",
                                    orientation = "horizontal",
                                )], 
                            value="section-cuts"),
                        dmc.TabsPanel(
                            children=[
                                dmc.Tabs(
                                    [dmc.TabsList(
                                        [dmc.Tab("Define", value="define-drifts"),
                                        dmc.Tab("Visualize", value="visualize-drifts")]
                                    ),
                                    dmc.TabsPanel(id='define-drifts', value="define-drifts"),
                                    dmc.TabsPanel(id='visualize-drifts', value="visualize-drifts")
                                    ],
                                    color = "blue",
                                    orientation = "horizontal",
                                )]
                            , value="drifts"),
                    ],
                    color = "blue",
                    orientation = "horizontal",
                )
            ]
        )

    def defineSectionCut(self):
        return dmc.MantineProvider(
            theme={"colorScheme": "light"},
            children=[
                dmc.Grid([
                    createTextInputComponent(idName='Def-cutName', 
                                             label='Section Cut Prefix', 
                                             description='Enter the prefix to be used in Section Cut names', 
                                             placeholder='S12'),
                ]),
                dmc.Grid([
                    createSelectComponent('Def-cutDirection', 'Normal Direction', description = 'Specify the direction normal to the Section Cut plane',
                                          values=['X', 'Y', 'Z']),
                ]),
                dmc.Grid([
                    createTextInputComponent(idName='Def-groupName', 
                                             label='Section Cut Group', 
                                             description='Enter name of the group that the Section Cut cuts through', 
                                             value='All'),
                ]),
                createNumberInputComponent('Normal Coordinate', -60.365, 29.835,  10, 'm'),

            ]
        )

    def visualizeSectionCut(self):
        return dmc.MantineProvider(
            theme={"colorScheme": "light"},
            children=[
                createUploadComponent('upload-sectioncut-data', 'Section Cut'),
                createUploadComponent('upload-height-data', 'Height Label'),
                dmc.Grid([
                    createMultiSelectComponent('cut-name-list', 'Cuts'),
                    createTextInputComponent(idName='line-type-list', 
                                             label='Enter the line types for Cuts', 
                                             description='Enter line types, separated by commas', 
                                             value='solid'),
                    createTextInputComponent(idName='load-case-types', 
                                             label='Enter Load Case type (Lin, NonLin, RS, TH)', 
                                             description='Enter Load Case types, separated by commas', 
                                             value=''),
                ]),
                dmc.Grid([
                    createMultiSelectComponent('load-case-name', 'Load Cases'),
                    createTextInputComponent(idName='load-case-colors', 
                                             label='Enter the colors for Load Cases', 
                                             description='Enter Load Case colors, separated by commas', 
                                             value='red,blue,black'),
                    createTextInputComponent(idName='load-case-labels', 
                                             label='Enter the labels for Load Cases', 
                                             description='Enter Load Case labels, separated by commas', 
                                             value='', 
                                             placeholder = 'Leave black for aggregation'),

                ]),
                
                dmc.Grid([
                    createSelectComponent('sectionCut-input-unit', values=['lb,in,F', 'lb,ft,F', 'kip,in,F', 'kip,ft,F', 'kN,mm,C', 
                                                                           'kN,m,C', 'Kgf,mm,C', 'Kgf,m,C', 'N,mm,C', 'N,m,C', 
                                                                           'Tonf,mm,C','Tonf,m,C', 'kN,cm,C', 'Kgf,cm,C', 'N,cm,C', 
                                                                           'Tonf,cm,C'], label='Input Unit', defaultValue='kN,m,C'),
                    createSelectComponent('sectionCut-output-unit', values=['lb,in,F', 'lb,ft,F', 'kip,in,F', 'kip,ft,F', 'kN,mm,C', 
                                                                           'kN,m,C', 'Kgf,mm,C', 'Kgf,m,C', 'N,mm,C', 'N,m,C', 
                                                                           'Tonf,mm,C','Tonf,m,C', 'kN,cm,C', 'Kgf,cm,C', 'N,cm,C', 
                                                                           'Tonf,cm,C'], label='Output Unit', defaultValue='kip,ft,F'),
                    createRadioComponent(idName='sectionCut-agg-type', values = ['Ind', 'Average', 'Min', 'Max'], showLabel = 'Aggregation Type'),
                ]),

                dmc.TextInput(label='Enter the title for the plots',
                        w = 300,
                        id='plot-title'),

                createNumberInputComponent('Shear',    -25e2,   25e2, 500, 'kN'),
                createNumberInputComponent('Axial',        0,   25e3, 5e3, 'kN'),
                createNumberInputComponent('Moment',    -1e5,    2e5, 5e4, 'kNm'),
                createNumberInputComponent('Torsion',   -1e4,    1e4, 5e3, 'kNm'),
                createNumberInputComponent('Height', -60.365, 29.835,  10, 'm'),
                
                #horizontal_spacing=0.05
                dmc.Group([
                dmc.Button("Submit", id='submit-button', color="blue"),
                
                dmc.Button("Reset Axis", id='reset-button', color="teal"),
                
                dmc.Button("Clear Data", id='clear-button', color="red"),
                ]),
                dmc.Grid([
                    dmc.Col([
                        dash_table.DataTable(id='data-table', page_size=12, style_table={'overflowX': 'auto'})
                    ], span=12),
                ]),
                dmc.Grid([
                        dmc.Col(dcc.Graph(id='subplot-graph', figure = {}, 
                                        config={'displayModeBar':True, 
                                                'displaylogo':False, 
                                                'toImageButtonOptions': {
                                                        'format': 'png',
                                                        'filename': 'SectionCut Forces',
                                                        'scale': 6
                                                    },
                                                    'doubleClick': 'reset',
                                                    'modeBarButtonsToAdd': ['drawline', 'drawcircle', 'drawrect', 'eraseshape', 'togglespikelines']
                                                }), span=12)
                    ], gutter=0),   
            ])

    # Function to utilize Gene
    def defineGeneralizedDisp(self):
        return dmc.MantineProvider(
            theme={"colorScheme": "light"},
            children=[
                createUploadComponent('upload-gendisp-group', 'Drift Group Information', description='Upload the file with the following tables: "Joint Coordinates" and "Groups 2 - Assignments"'),
                dmc.Grid([
                createTextInputComponent(idName = 'grid-list', 
                                         label = 'Grid List', 
                                         description = 'Enter grid labels separated by commas', 
                                         placeholder = 'S12A,S12B,S12C'),
                ]),
                dmc.Grid([
                    createTextInputComponent(idName = 'drift-top-suffix', 
                                             label = 'Suffix for Top Joint group', 
                                             description = 'Enter the suffix used in the group definition', 
                                             placeholder='Drift_Top_'),
                    createTextInputComponent(idName = 'drift-bot-suffix',
                                             label = 'Suffix for Bottom Joint group',
                                             description = 'Enter the suffix used in the group definition',
                                             placeholder='Drift_Bot_'),
                ]),
                dmc.Grid([
                createTextInputComponent(idName = 'output-file-name', 
                                         label = 'Output File Name', 
                                         description = 'Enter the name of the output excel file', 
                                         value='GeneralizedDisplacement_Definition'),
                ]),
                dmc.Group([
                dmc.Button("Submit", id='submit-button-defineGenDisp', color="blue"),
                dmc.Button("Clear Data", id='clear-button-defineGenDisp', color="red"),
                ],
                ),
                dcc.Download(id="download-GenDispDefn-excel"),
                dmc.Alert("The file has been downloaded",
                          id='GenDispDefn-download-modal',
                          color = 'green',
                          duration=2000),
            ])
    
    def visualizeGeneralizedDisp(self):
        return dmc.MantineProvider(
            theme={"colorScheme": "light"},
            children=[
                createUploadComponent('vizGenDisp-upload-analysis', 'General Displacement Analysis File', 
                                      description='The file should contain the following tables: "Jt Displacements - Generalized", "Joint Coordinates", "Gen Displ Defs 1 - Translation"'),
                createUploadComponent('vizGenDisp-upload-height', 'Height Label',
                                      description='The file should contain the following tables: "Floor Elevations"'),
                dmc.Grid([
                    createMultiSelectComponent('vizGenDisp-GMlist', 'Load Cases'),
                    createTextInputComponent(idName = 'vizGenDisp-case-color', 
                                             label = 'Enter colors for Load Cases', 
                                             description = 'Enter values, separated by commas', 
                                             value='#1f77b4,#ff7f0e'),            
                ]),
                dmc.Grid([
                    createMultiSelectComponent('vizGenDisp-grid-list', 'Grids'),
                    createMultiSelectComponent('vizGenDisp-disp-list', 'Displacements'),
                ]),
                dmc.Grid([
                    createSelectComponent('vizGenDisp-input-unit', values=['lb,in,F', 'lb,ft,F', 'kip,in,F', 'kip,ft,F', 'kN,mm,C', 
                                                                           'kN,m,C', 'Kgf,mm,C', 'Kgf,m,C', 'N,mm,C', 'N,m,C', 
                                                                           'Tonf,mm,C','Tonf,m,C', 'kN,cm,C', 'Kgf,cm,C', 'N,cm,C', 
                                                                           'Tonf,cm,C'], label='Input Unit', defaultValue='kN,m,C'),
                    createSelectComponent('vizGenDisp-output-unit', values=['lb,in,F', 'lb,ft,F', 'kip,in,F', 'kip,ft,F', 'kN,mm,C', 
                                                                           'kN,m,C', 'Kgf,mm,C', 'Kgf,m,C', 'N,mm,C', 'N,m,C', 
                                                                           'Tonf,mm,C','Tonf,m,C', 'kN,cm,C', 'Kgf,cm,C', 'N,cm,C', 
                                                                           'Tonf,cm,C'], label='Output Unit', defaultValue='kip,in,F'),
                ]),
                dmc.Grid([
                    createTextInputComponent(idName = 'vizGenDisp-DriftLim-label', 
                                             label  = 'Enter the label for drift limit',
                                             description = 'Enter the legend label for the drift limit', 
                                             value  = 'SLE Limit'), 
                    createSingleNumberInputComponent(id='vizGenDisp-DriftLim', value = 0.004, 
                                                     label= 'Code Limit for Drift Plots',
                                                     description='Enter drift limits per code'),
                    # Add a checkbox to show the limit if true
                    createRadioComponent(idName='vizGenDisp-ShowLimit', values = ['True', 'False'], showLabel = 'Show Limit'),
                ]),
                dmc.Grid([
                    createSingleNumberInputComponent(id='vizGenDisp-DriftStep', value = 0.001, 
                                                     label= 'Drift Plot Step Size',
                                                     description='Enter plot step size'),

                    createSingleNumberInputComponent(id='vizGenDisp-DriftMax', value = 0.006, 
                                                     label= 'Maximum Drift Plot Limit',
                                                     description='Enter maximum plot value'),
                ]),
                dmc.Grid([
                    createSingleNumberInputComponent(id='vizGenDisp-DispMin', value = -5, 
                                                     label= 'Minimum Displacement Plot Limit (in)',
                                                     description='Enter minimum plot value'),

                    createSingleNumberInputComponent(id='vizGenDisp-DispMax', value = 5, 
                                                     label= 'Maximum Displacement Plot Limit (in)',
                                                     description='Enter maximum plot value'),

                    createSingleNumberInputComponent(id='vizGenDisp-DispStep', value = 1, 
                                                     label= 'Displacement Plot Step Size (in)',
                                                     description='Enter plot step size'),
                ]),
                dmc.Grid([
                    createSingleNumberInputComponent(id='vizGenDisp-HeightMin', value = -22.965, 
                                                     label= 'Minimum Height Plot Limit (m)',
                                                     description='Enter minimum plot value'),
                    createSingleNumberInputComponent(id='vizGenDisp-HeightMax', value = 126.635, 
                                                     label= 'Maximum Height Plot Limit (m)',
                                                     description='Enter maximum plot value'),
                ]),
                dmc.Group([
                dmc.Button("Plot!", id='plot-button-vizGenDisp', color="blue"),
                dmc.Button("Clear", id='clear-button-vizGenDisp', color="red"),
                ]),
                dmc.Alert("The file has been downloaded",
                          id='GenDispPlot-download-modal',
                          color = 'green',
                          duration=2000),
                dcc.Download(id="download-GenDispPlot-excel"),
            ]
        )


    def registerCallbacks(self):
        # Tab Change callbacks
        self.registerTabChangeCallbacks('visualize-section-cuts', self.visualizeSectionCut)
        self.registerTabChangeCallbacks('define-section-cuts', self.defineSectionCut)
        self.registerTabChangeCallbacks('visualize-drifts', self.visualizeGeneralizedDisp)
        self.registerTabChangeCallbacks('define-drifts', self.defineGeneralizedDisp)
        
        # Register callbacks for uploading file
        self.registerUploadCallbacks('upload-sectioncut-data', 'Section Cut', self.updateFileUploadText)
        self.registerUploadCallbacks('upload-height-data', 'Height Label', self.updateFileUploadText)
        self.registerUploadCallbacks('upload-gendisp-group', 'Drift Group', self.updateFileUploadText)
        self.registerUploadCallbacks('vizGenDisp-upload-analysis', 'Generalized Displacement', self.updateFileUploadText)
        self.registerUploadCallbacks('vizGenDisp-upload-height', 'Height Label', self.updateFileUploadText)
        
        
        @self.app.callback(
            Output('download-GenDispDefn-excel', 'data'),
            Output('GenDispDefn-download-modal', 'hide'),
            Input('submit-button-defineGenDisp', 'n_clicks'),
            State('grid-list', 'value'),
            State('drift-top-suffix', 'value'),
            State('drift-bot-suffix', 'value'),
            State('output-file-name', 'value'),
            prevent_initial_call=True,
            suppress_callback_exceptions=True
        )
        def handleGenDispDefnSubmit(n_clicks, gridList, topSuffix, botSuffix, outputFileName):
            if n_clicks:
                dfList = defineGenDisp(self.conn, gridList, topSuffix, botSuffix)
                downloadData = dcc.send_bytes(self.downloadExcelFile(data=dfList, sheetnames=['DriftPoints', 'GenDispDefn'])
                                                , f'{outputFileName}.xlsx')
                # Show a modal with the message that the file was downloaded

                return downloadData, False
            return no_update, True
        
        # Update label of shear-min, shear-max, shear-step, axial-min, axial-max, axial-step, moment-min, moment-max, moment-step, torsion-min, torsion-max, torsion-step
        @self.app.callback(
            [Output('shear-min', 'label'),
            Output('shear-max', 'label'),
            Output('shear-step', 'label'),
            Output('axial-min', 'label'),
            Output('axial-max', 'label'),
            Output('axial-step', 'label'),
            Output('moment-min', 'label'),
            Output('moment-max', 'label'),
            Output('moment-step', 'label'),
            Output('torsion-min', 'label'),
            Output('torsion-max', 'label'),
            Output('torsion-step', 'label'),
            State('sectionCut-input-unit', 'value'),
            Input('sectionCut-output-unit', 'value'),
            ],
        )
        def updateSecCutLabel(inUnit, outUnit):
            units = UnitConvertor(inUnit, outUnit)
            return (f"Shear - Minimum ({units.printUnit('force')})",
                    f"Shear - Maximum ({units.printUnit('force')})",
                    f"Shear - Step Size ({units.printUnit('force')})",
                    f"Axial - Minimum ({units.printUnit('force')})",
                    f"Axial - Maximum ({units.printUnit('force')})",
                    f"Axial - Step Size ({units.printUnit('force')})",
                    f"Moment - Minimum ({units.printUnit('moment')})",
                    f"Moment - Maximum ({units.printUnit('moment')})",
                    f"Moment - Step Size ({units.printUnit('moment')})",
                    f"Torsion - Minimum ({units.printUnit('moment')})",
                    f"Torsion - Maximum ({units.printUnit('moment')})",
                    f"Torsion - Step Size ({units.printUnit('moment')})")
        
        @self.app.callback(
            [Output('vizGenDisp-DispMin', 'label'),
             Output('vizGenDisp-DispStep', 'label'),
             Output('vizGenDisp-DispMax', 'label'),
             State('vizGenDisp-input-unit', 'value'),
             Input('vizGenDisp-output-unit', 'value')],
        )
        def updateDispLabel(inUnit, outUnit):
            units = UnitConvertor(inUnit, outUnit)
            return (f"Minimum Displacement Plot Limit ({units.printUnit('length')})",
                    f"Displacement Plot Step Size ({units.printUnit('length')})",
                    f"Maximum Displacement Plot Limit ({units.printUnit('length')})")

        
        #Clear the data
        @self.app.callback(
            [Output('upload-gendisp-group', 'children',allow_duplicate=True),
            Output('grid-list', 'value'),
            Output('drift-top-suffix', 'value'),
            Output('drift-bot-suffix', 'value'),
            Output('output-file-name', 'value'),
            Input('clear-button-defineGenDisp', 'n_clicks'),
            ],
            prevent_initial_call=True,
        )
        def clearGenDispDefnData(n_clicks):
            if n_clicks:
                self.conn = None
                
                return (self.updateFileUploadText(contents=None, filename='', fileCategory='Drift Group'), '', '', '', 'GeneralizedDisplacement_Definition')
                
            return no_update, no_update, no_update, no_update, no_update

        #Update the Load Case Names and Section Cut Names
        @self.app.callback(
        [Output('load-case-name', 'data'),
        Output('cut-name-list', 'data')],
        Input('file-upload-status', 'data'),
        suppress_callback_exceptions=True
        )
        def updateSectionCut_NameCases(data):
            if data and 'SectionCutDataFileUploaded' in data.keys() and data['SectionCutDataFileUploaded'] == 'Complete':
                return self.updateCutCaseName(data)
            return no_update, no_update
        
        # Update load case names, grid names, displacements in Viz Generalized Disp
        @self.app.callback(
            [Output('vizGenDisp-GMlist', 'data'),
             Output('vizGenDisp-grid-list', 'data'),
             Output('vizGenDisp-disp-list', 'data')],
            [Input('file-upload-status', 'data'),
             State('vizGenDisp-DriftLim', 'data'),
             State('vizGenDisp-DriftMax', 'data'),
             State('vizGenDisp-HeightMin', 'data'),
             State('vizGenDisp-HeightMax', 'data'),
             State('vizGenDisp-DriftStep', 'data'),
             State('vizGenDisp-DriftLim-label', 'data'),
             State('vizGenDisp-ShowLimit', 'value')],
            suppress_callback_exceptions=True
        )
        def updateCaseGridDisp_VizDisp(data, Dlim, Dmax, Hmin, Hmax, Dstep, DlimName, showLimit):
            if data and 'vizDataFileUploaded' in data.keys() and data['vizDataFileUploaded'] == 'Complete':
                return self.updateCaseGridDisp(Dlim, Dmax, Hmin, Hmax, Dstep, DlimName, showLimit)
            return no_update, no_update, no_update
        
        # Plot the Generalized Displacement
        @self.app.callback(
            Output('GenDispPlot-download-modal', 'hide'),
            Output('download-GenDispPlot-excel', 'data'),
            Input('plot-button-vizGenDisp', 'n_clicks'),
            State('vizGenDisp-GMlist', 'value'),
            State('vizGenDisp-case-color', 'value'),
            State('vizGenDisp-grid-list', 'value'),
            State('vizGenDisp-disp-list', 'value'),
            State('vizGenDisp-DriftLim', 'value'),
            State('vizGenDisp-DriftMax', 'value'),
            State('vizGenDisp-HeightMin', 'value'),
            State('vizGenDisp-HeightMax', 'value'),
            State('vizGenDisp-DriftStep', 'value'),
            State('vizGenDisp-DriftLim-label', 'value'),
            State('vizGenDisp-ShowLimit', 'value'),
            suppress_callback_exceptions=True
        )
        def plotGenDisp(n_clicks, GMlist, caseColor, gridList, dispList, Dlim, Dmax, Hmin, Hmax, Dstep, DlimName, showLimit):
            if n_clicks:
                if self.conn is not None:
                    self.genDisp = GeneralizedDisplacement(analysisFileConnection = self.conn,
                                                   heightFileConnection = self.height_conn,
                                                   Dlim = Dlim, Dmax=Dmax, DlimName = DlimName, Dstep = Dstep,
                                                   Hmin=Hmin, Hmax=Hmax, showLimit = showLimit)
                    self.genDisp.readMainFile()
                    self.genDisp.readDefinitionFile()
                    self.genDisp.readHeightFile()
                    return False, self.genDisp.plotData(gridList=gridList, GMList=GMlist, dispList=dispList, colList=caseColor.split(','))
            return True, no_update
        
        # If vizGenDisp-ShowLimit is False, disable inputs to vizGenDisp-DriftLim and vizGenDisp-DriftLim-label
        @self.app.callback(
            Output('vizGenDisp-DriftLim', 'disabled'),
            Output('vizGenDisp-DriftLim-label', 'disabled'),
            Input('vizGenDisp-ShowLimit', 'value'),
            suppress_callback_exceptions=True,
            prevent_initial_call=True
        )
        def disableDriftLimit(showLimit):
            if showLimit == 'True':
                return False, False
            return True, True


        # Clear the data
        self.app.callback(
            [Output('data-table', 'data', allow_duplicate=True),
             Output('subplot-graph', 'figure', allow_duplicate=True)],
            Input('clear-button', 'n_clicks'),
            prevent_initial_call=True,
            suppress_callback_exceptions=True
        )(self.clearData)

        # Reset the axis
        self.app.callback(
            Output('subplot-graph', 'figure', allow_duplicate=True),
            [Input('reset-button', 'n_clicks')],
            [[State('shear-min', 'value'),State('shear-max', 'value'),State('shear-step', 'value')],
            [State('axial-min', 'value'),State('axial-max', 'value'),State('axial-step', 'value')],
            [State('moment-min', 'value'),State('moment-max', 'value'),State('moment-step', 'value')],
            [State('torsion-min', 'value'),State('torsion-max', 'value'),State('torsion-step', 'value')],
            [State('height-min', 'value'),State('height-max', 'value'),State('height-step', 'value')]],
            prevent_initial_call=True,
            suppress_callback_exceptions=True
        )(self.resetAxis)

        # Plot the data
        self.app.callback(
            [Output('data-table', 'data', allow_duplicate=True),
            Output('subplot-graph', 'figure', allow_duplicate=True)],
            [Input('submit-button', 'n_clicks')],
            [State('cut-name-list', 'value'),State('line-type-list', 'value'),
            State('load-case-name', 'value'),State('load-case-colors', 'value'),State('load-case-labels', 'value'),State('load-case-types', 'value'),
            State('plot-title', 'value'),
            [State('shear-min', 'value'),State('shear-max', 'value'),State('shear-step', 'value')],
            [State('axial-min', 'value'),State('axial-max', 'value'),State('axial-step', 'value')],
            [State('moment-min', 'value'),State('moment-max', 'value'),State('moment-step', 'value')],
            [State('torsion-min', 'value'),State('torsion-max', 'value'),State('torsion-step', 'value')],
            [State('height-min', 'value'),State('height-max', 'value'),State('height-step', 'value')],
            State('sectionCut-agg-type', 'value'), State('sectionCut-input-unit', 'value'), State('sectionCut-output-unit', 'value')],
            prevent_initial_call=True,
            suppress_callback_exceptions=True
        )(self.plotData)

    
    def registerTabChangeCallbacks(self, componentID, callbackMethod):
        @self.app.callback(
            Output(componentID, 'children'),
            [Input(componentID, 'value')],
            suppress_callback_exceptions=True
        )
        def tabChange(tab):
            if tab == componentID:
                return callbackMethod()
            return no_update
    
    def registerUploadCallbacks(self, componentID, fileCategory, callbackMethod):
        @self.app.callback(
            [Output('file-upload-status', 'data', allow_duplicate=True),
            Output(componentID, 'children')],
            [Input(componentID, 'contents'),
            State(componentID, 'filename'),
            State('file-upload-status', 'data')],
            prevent_initial_call=True,
            suppress_callback_exceptions=True
        )
        def updateFileName(contents, filename, storedData):
            trigger = callback_context.triggered[0]['prop_id'].split('.')[0]
            print('Trigger:', trigger)
            return callbackMethod(contents=contents, filename=filename, 
                                     fileCategory=fileCategory,storedData=storedData)
    
    
    def updateFileUploadText(self, **kwargs):
        contents = kwargs.get('contents')
        filename = kwargs.get('filename')
        fileCategory = kwargs.get('fileCategory')
        storedData = kwargs.get('storedData')
        if contents is not None:
            if storedData is None:
                storedData = {}
            _, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            file = io.BytesIO(decoded)
            if fileCategory in ['Section Cut', 'Drift Group','Generalized Displacement']:
                print('Reading File....fileCategory:', fileCategory)
                self.conn = connectDB(file)
                if fileCategory == 'Section Cut':
                    storedData['SectionCutDataFileUploaded'] = 'Complete'
                elif fileCategory == 'Drift Group':
                    storedData['DriftGroupFileUploaded'] = 'Complete'
                elif fileCategory == 'Generalized Displacement':
                    storedData['vizDataFileUploaded'] = 'Complete'
                    
            else:
                self.height_conn = connectDB(file)
                query = 'SELECT FloorLabel as story, SAP2000Elev as height FROM "Floor Elevations"'        
                self.height_data = getData(self.height_conn, query=query)
                storedData['heightFileUploaded'] = 'Complete'
            return storedData, html.Div(['File ', html.B(html.A(filename, style = {'color':'blue'})), ' Uploaded. Drag/Drop/Select another file if desired.'])
        else:
            return no_update, html.Div([
                f'Drag and Drop the {fileCategory} File or ',
                html.A('Select a File')
            ])
    
    #Function to create an excel file from the data and download it to the user
    # inputs: list of dataframes with information, filename to save the file as
    # output: download the file to the user
    def downloadExcelFile(self, **kwargs):
        data = kwargs.get('data')
        sheetnames = kwargs.get('sheetnames')
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='openpyxl')
        for i, df in enumerate(data):
            df.to_excel(writer, sheet_name=sheetnames[i], index=False)
        writer.close()
        processedData = output.getvalue()
        return processedData
    
    def updateCaseGridDisp(self, Dlim, Dmax, Hmin, Hmax, Dstep, DlimName, showLimit):
        if self.conn is not None:
            self.genDisp = GeneralizedDisplacement(analysisFileConnection = self.conn,
                                                   heightFileConnection = self.height_conn,
                                                   Dlim = Dlim, Dmax=Dmax, DlimName = DlimName, Dstep = Dstep,
                                                   Hmin=Hmin, Hmax=Hmax, showLimit = showLimit)
            return self.genDisp.populateFields()
        return [], [], []


    def updateCutCaseName(self, contents):
        if not contents:
            return [],[]
        if self.conn is not None:
            query = 'SELECT DISTINCT OutputCase FROM "Section Cut Forces - Analysis"'
            data = getData(self.conn, query=query)
            data = data['OutputCase'].tolist()
            data.sort()

            query = 'SELECT DISTINCT SectionCut FROM "Section Cut Forces - Analysis"'
            cutNames = getData(self.conn, query=query)
            cutGroups = getCutGroup(cutNames['SectionCut'].tolist())
            cutGroups.sort()
            return data, cutGroups
        return [], []

    def updateAxis(self, shear_lims, axial_lims, moment_lims, torsion_lims, height_lims, inUnit='kN,m,C', outUnit='kN,m,C'):
        units = UnitConvertor(inUnit, outUnit)
        for row in range(1, 3):
                for col in range(1, 4):
                    if self.height_data is not None:
                        self.fig.update_yaxes(
                            title_text="Story",
                            title_font=self.AXIS_TITLE_FONT,
                            tickfont=self.TICK_FONT,
                            showline=True, showgrid=True, mirror=True,
                            row=row, col=col,
                            range=height_lims[0:2],
                            tickvals=self.height_data['height'].tolist(),
                            ticktext=self.height_data['story'].tolist(),
                            secondary_y=False
                        )
                        self.fig.update_yaxes(
                            title_text="Height (m)",
                            title_font=self.AXIS_TITLE_FONT,
                            tickfont=self.TICK_FONT,
                            showline=False, showgrid=False, mirror=True,
                            row=row, col=col,
                            range=height_lims[0:2],
                            tickvals=self.height_data['height'].tolist(),
                            ticktext=[round(x,0) for x in self.height_data['height'].tolist()],
                            secondary_y=True
                        )
                    else:
                        self.fig.update_yaxes(
                            title_text="Height (m)",
                            title_font=self.AXIS_TITLE_FONT,
                            tickfont=self.TICK_FONT,
                            showline=True, showgrid=True, mirror=True,
                            row=row, col=col,
                            range=height_lims[0:2],
                            dtick=height_lims[-1]
                        )
        for col in range(1,3):
                self.fig.update_xaxes(
                    title_text=f"Shear Along Axis {col} ({units.printUnit('force')})",
                    title_font=self.AXIS_TITLE_FONT,
                    tickfont=self.TICK_FONT,
                    showline=True, showgrid=True, zeroline=True, mirror=True,
                    row=1, col=col,
                    range=shear_lims[0:2],
                    dtick=shear_lims[-1]
                )
                self.fig.update_xaxes(
                    title_text=f"Flexure About Axis {col} ({units.printUnit('moment')})",
                    title_font=self.AXIS_TITLE_FONT,
                    tickfont=self.TICK_FONT,
                    showline=True, showgrid=True, zeroline=True, mirror=True,
                    row=2, col=col,
                    range=moment_lims[0:2],
                    dtick=moment_lims[-1]
                )

        self.fig.update_xaxes(
                title_text=f"Axial ({units.printUnit('force')})",
                title_font=self.AXIS_TITLE_FONT,
                tickfont=self.TICK_FONT,
                showline=True, showgrid=True, zeroline=True, mirror=True,
                row=1, col=3,
                range=axial_lims[0:2],
                dtick=axial_lims[-1]
            )
        self.fig.update_xaxes(
                title_text=f"Torsion ({units.printUnit('moment')})",
                title_font=self.AXIS_TITLE_FONT,
                tickfont=self.TICK_FONT,
                showline=True, showgrid=True, zeroline=True, mirror=True,
                row=2, col=3,
                range=torsion_lims[0:2],
                dtick=torsion_lims[-1]
            )
    
    def resetAxis(self, resetClicks, shear_lims, axial_lims, moment_lims, torsion_lims, height_lims):
        if resetClicks:
            self.updateAxis(shear_lims, axial_lims, moment_lims, torsion_lims, height_lims)
            return self.fig
    
    def clearData(self, clearClicks):
        if clearClicks:
            self.fig.data = []
            return [], self.fig
    
    def plotData(self, plotClicks, cut_name_list, line_type_list, load_case_name, load_case_color, load_case_label, load_case_type, plot_title, shear_lims, axial_lims, moment_lims, torsion_lims, height_lims, agg_type, inUnit, outUnit):
        if plotClicks:
            self.fig.data = []
            data = getCutForces(self.conn, cut_name_list, load_case_name)
            def rgb2hex(color):
                return "#{:02x}{:02x}{:02x}".format(int(color[0]*255),int(color[1]*255),int(color[2]*255))
            
            defaultColor = [rgb2hex(color) for color in distinctipy.get_colors(len(load_case_name),[(1,1,1)])]
            colList = load_case_color.split(',') if load_case_color else defaultColor

            
            typeList = line_type_list.split(',') if line_type_list else ['solid', 'dash', 'dot', 'dashdot', 'longdash', 'longdashdot']
            loadLabel = load_case_label.split(',') if load_case_label else load_case_name
            loadType = load_case_type.split(',') if load_case_type else ['NonLin']*len(load_case_name)
            self.allLegendList = []

            for Li, lType in enumerate(loadType):
                if lType == 'TH' and agg_type != 'Ind':
                    colList[Li] = '#D3D3D3'
            for i in range(1,3):
                for j in range(1,4):
                    self.fig.add_trace(go.Scatter(y=[], x=[], mode='lines'), row=i, col=j, secondary_y=True)
        
            

            for cutI, cutName in enumerate(cut_name_list):
                # For each cutName in the list find average for all load case name
                dataCut = data[data['SectionCut'].str.startswith(cutName+' - ')].reset_index(drop=True)
                aggCaseList = []
                for i, case in enumerate(load_case_name):
                    if loadType[i] == 'TH':
                        aggCaseList.append(case)
                dataCutCase = dataCut[dataCut['OutputCase'].isin(aggCaseList)].reset_index(drop=True)
                dataCutCase = dataCutCase.drop(columns=['OutputCase', 'SectionCut'])
                if agg_type == 'Average':
                    avgData = dataCutCase.groupby(['CutHeight', 'StepType']).mean().reset_index()
                if agg_type == 'Min' or agg_type == 'Max':
                    maxData = dataCutCase.groupby(['CutHeight', 'StepType']).max().reset_index()
                    minData = dataCutCase.groupby(['CutHeight', 'StepType']).min().reset_index()
                for cI, case in enumerate(load_case_name):
                    filtered_data = data[(data['OutputCase'] == case) & (data['SectionCut'].str.startswith(cutName + ' - '))]
                    if loadType[cI] == 'Lin':
                        self.plotCases(colList, typeList, cutI, cutName, cI, case, filtered_data, None, True, SF = 1.0, loadLabel = loadLabel[cI], inUnit = inUnit, outUnit = outUnit)
                    elif loadType[cI] == 'RS':
                        self.plotCases(colList, typeList, cutI, cutName, cI, case, filtered_data, 'Max', True, SF = 1.0, loadLabel = loadLabel[cI], inUnit = inUnit, outUnit = outUnit)
                        self.plotCases(colList, typeList, cutI, cutName, cI, case, filtered_data, 'Max', False, SF = -1.0, loadLabel = loadLabel[cI], inUnit = inUnit, outUnit = outUnit)
                    elif loadType[cI] == 'NonLin':
                        self.plotCases(colList, typeList, cutI, cutName, cI, case, filtered_data, 'Max', True, SF = 1.0, loadLabel = loadLabel[cI], inUnit = inUnit, outUnit = outUnit)
                        self.plotCases(colList, typeList, cutI, cutName, cI, case, filtered_data, 'Min', False, SF = 1.0, loadLabel = loadLabel[cI], inUnit = inUnit, outUnit = outUnit)
                    elif loadType[cI] == 'TH':
                        showLabel = True if agg_type == 'Ind' else False
                        lineWidth = 2 if agg_type == 'Ind' else 1
                        self.plotCases(colList, typeList, cutI, cutName, cI, case, filtered_data, 'Max', showLabel, SF = 1.0, loadLabel = loadLabel[cI], lineWidth=lineWidth, inUnit = inUnit, outUnit = outUnit)
                        self.plotCases(colList, typeList, cutI, cutName, cI, case, filtered_data, 'Min', False, SF = 1.0, loadLabel = loadLabel[cI], lineWidth=lineWidth, inUnit = inUnit, outUnit = outUnit)
                if agg_type == 'Average':
                    self.plotCases(['green'], typeList, cutI, cutName, cI, case, avgData, 'Max', True, SF = 1.0, loadLabel = 'Average MCE', inUnit = inUnit, outUnit = outUnit)
                    self.plotCases(['green'], typeList, cutI, cutName, cI, case, avgData, 'Min', False, SF = 1.0, loadLabel = 'Average MCE', inUnit = inUnit, outUnit = outUnit)
                if agg_type == 'Min':
                    self.plotCases(['green'], typeList, cutI, cutName, cI, case, minData, 'Max', True, SF = 1.0, loadLabel = 'Min MCE', inUnit = inUnit, outUnit = outUnit)
                    self.plotCases(['green'], typeList, cutI, cutName, cI, case, maxData, 'Min', False, SF = 1.0, loadLabel = 'Min MCE', inUnit = inUnit, outUnit = outUnit)
                if agg_type == 'Max':
                    self.plotCases(['green'], typeList, cutI, cutName, cI, case, maxData, 'Max', True, SF = 1.0, loadLabel = 'Max MCE', inUnit = inUnit, outUnit = outUnit)
                    self.plotCases(['green'], typeList, cutI, cutName, cI, case, minData, 'Min', False, SF = 1.0, loadLabel = 'Max MCE', inUnit = inUnit, outUnit = outUnit)
            
            for i in range(1,3):
                for j in range(1,4):
                    self.fig.add_vline(
                        x=0, line_width=1, line_dash="dash",line_color="black",
                        row=i, col=j, secondary_y=True
                        )
                    
            self.fig.update_layout(
                        title={
                            'text': plot_title,
                            'x': 0.5,
                            'xanchor': 'center',
                            'font': self.OVERALL_PLOT_TITLE_FONT
                        },
                        height=1000, width=1500,
                        template="plotly_white",
                        legend=dict(
                            font = self.LEGEND_FONT,
                            orientation="v",
                            yanchor="middle",
                            y=0.5,
                            xanchor="left",
                            x=1.008,
                            traceorder="normal",
                            tracegroupgap=20,
                            valign='middle',
                            itemsizing='constant',
                            itemwidth=80
                        ),
                        margin=dict(l=20, r=100, t=60, b=20),
                        )
            
            self.updateAxis(shear_lims, axial_lims, moment_lims, torsion_lims, height_lims, inUnit, outUnit)
            return data.to_dict('records'), self.fig
    
    def runApp(self):
        self.app.run_server(debug=True, port = self.port)     

    def plotCases(self, colList, typeList, cutI, cutName, cI, case, filtered_data, StepType, showLegend, SF=1.0, loadLabel = '', agg_type = 'Ind', lineWidth = 2, inUnit = 'kN,m,C', outUnit = 'kN,m,C'):
        if StepType is not None:
            filtered_data = filtered_data[filtered_data['StepType'] == StepType]
        if wrap_text(loadLabel+'_'+cutName) in self.allLegendList or loadLabel == '':
            showLegend = False
        else:
            self.allLegendList.append(wrap_text(loadLabel+'_'+cutName))
        units = UnitConvertor(inUnit, outUnit)
        self.fig.add_trace(go.Scatter(y=filtered_data['CutHeight'], x=units.convert(1,'force')*SF*filtered_data['F1'], mode='lines', name=wrap_text(loadLabel+'_'+cutName), line = dict(color =colList[cI%len(colList)], dash=typeList[cutI%len(typeList)], width=lineWidth),showlegend=showLegend, legendgroup=loadLabel+cutName), row=1, col=1, secondary_y=False)
        self.fig.add_trace(go.Scatter(y=filtered_data['CutHeight'], x=units.convert(1,'force')*SF*filtered_data['F2'], mode='lines', name=wrap_text(loadLabel+'_'+cutName), line = dict(color =colList[cI%len(colList)], dash=typeList[cutI%len(typeList)], width=lineWidth),showlegend=False, legendgroup=loadLabel+cutName), row=1, col=2, secondary_y=False)
        self.fig.add_trace(go.Scatter(y=filtered_data['CutHeight'], x=units.convert(1,'force')*SF*filtered_data['F3'], mode='lines', name=wrap_text(loadLabel+'_'+cutName), line = dict(color =colList[cI%len(colList)], dash=typeList[cutI%len(typeList)], width=lineWidth),showlegend=False, legendgroup=loadLabel+cutName), row=1, col=3, secondary_y=False)
        self.fig.add_trace(go.Scatter(y=filtered_data['CutHeight'], x=units.convert(1,'moment')*SF*filtered_data['M2'], mode='lines', name=wrap_text(loadLabel+'_'+cutName), line = dict(color =colList[cI%len(colList)], dash=typeList[cutI%len(typeList)], width=lineWidth),showlegend=False, legendgroup=loadLabel+cutName), row=2, col=1, secondary_y=False)
        self.fig.add_trace(go.Scatter(y=filtered_data['CutHeight'], x=units.convert(1,'moment')*SF*filtered_data['M1'], mode='lines', name=wrap_text(loadLabel+'_'+cutName), line = dict(color =colList[cI%len(colList)], dash=typeList[cutI%len(typeList)], width=lineWidth),showlegend=False, legendgroup=loadLabel+cutName), row=2, col=2, secondary_y=False)
        self.fig.add_trace(go.Scatter(y=filtered_data['CutHeight'], x=units.convert(1,'moment')*SF*filtered_data['M3'], mode='lines', name=wrap_text(loadLabel+'_'+cutName), line = dict(color =colList[cI%len(colList)], dash=typeList[cutI%len(typeList)], width=lineWidth),showlegend=False, legendgroup=loadLabel+cutName), row=2, col=3, secondary_y=False)

        

globalApp = GlobalAnalysisApp()
server = globalApp.app.server

if __name__ == '__main__':
    globalApp.runApp()
    
