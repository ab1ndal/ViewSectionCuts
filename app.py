from dash import Dash, html, dash_table, dcc, Input, Output, callback, callback_context, no_update, State, _dash_renderer, ALL
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
from utils.appComponents import createUploadComponent, createMultiSelectComponent, createTextInputComponent, createNumberInputComponent, createSelectComponent, createSingleNumberInputComponent, createRadioComponent, getCaseType, getCaseID, getCaseColor
from GeneralizedDisplacement.defineGenDisp import defineGenDisp
from GeneralizedDisplacement.plotGenDisp import GeneralizedDisplacement
from utils.unitConvertor import UnitConvertor
from utils.extraTools import wrap_text, rgb2hex
from flask import send_file
import threading
import tempfile
_dash_renderer._set_react_version("18.2.0")
Dash(external_stylesheets=dmc.styles.ALL)
pio.kaleido.scope.default_executable_path = r"C:\\Python312\\Lib\\site-packages\\kaleido\\executable\\kaleido"
#pio.orca.config.executable = r"C:\\Python312\\Lib\\site-packages\\kaleido\\executable\\kaleido.cmd"

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
        self.fileUploadProgress = {'upload-sectioncut-data-progress':0,
                                  'upload-height-data-progress':0,
                                  'upload-gendisp-group-progress':0,
                                  'vizGenDisp-upload-analysis-progress':0,
                                  'vizGenDisp-upload-height-progress':0}
        
        self.uploadCallbackRunning = False

        # Create subplots
        self.fig = make_subplots(rows=2, cols=3, subplot_titles=('F1 (A-Canyon)', 'F2 (X-Canyon)', 'F3 (Vertical)', 'M2 (A-Canyon)', 'M1 (X-Canyon)', 'M3'),
                                 vertical_spacing=0.1, horizontal_spacing=0.1, specs=[[{"secondary_y": True}, {"secondary_y": True}, {"secondary_y": True}],
                                                                                      [{"secondary_y": True}, {"secondary_y": True}, {"secondary_y": True}]])
        self.createMenu()
        #self.createLayout()
        self.registerCallbacks()
        
    def createMenu(self):
        self.app.layout = html.Div(
                style = {"padding": "20px"},
                children =[dmc.MantineProvider(
            theme={"colorScheme": "light"},
            children = [
                dcc.Store(id='file-upload-status'),
                dcc.Interval(id='interval-component', interval=2000, n_intervals=0),
                dmc.Title("Global Building Responses", c="blue", size="h2"),
                dmc.Tabs(
                    [
                        dmc.TabsList(
                            [
                                dmc.TabsTab("Section Cuts", value="section-cuts", id="section-cuts"),
                                dmc.TabsTab("Drifts", value="drifts", id="drifts"),
                            ]
                        ),
                        dmc.TabsPanel(
                            children=[
                                dmc.Tabs(
                                    [dmc.TabsList(
                                        [dmc.TabsTab("Define", value="define-section-cuts"),
                                        dmc.TabsTab("Visualize", value="visualize-section-cuts")]
                                    ),
                                    dmc.TabsPanel(id = 'define-section-cuts', value="define-section-cuts", children=[]),
                                    dmc.TabsPanel(id = 'visualize-section-cuts', value="visualize-section-cuts", children = [])
                                    ],
                                    color = "blue",
                                    orientation = "horizontal",
                                )], 
                            value="section-cuts"),
                        dmc.TabsPanel(
                            children=[
                                dmc.Tabs(
                                    [dmc.TabsList(
                                        [dmc.TabsTab("Define", value="define-drifts"),
                                        dmc.TabsTab("Visualize", value="visualize-drifts")]
                                    ),
                                    dmc.TabsPanel(id='define-drifts', value="define-drifts", children = []),
                                    dmc.TabsPanel(id='visualize-drifts', value="visualize-drifts", children = [])
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
        )])

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
                #dcc.Download(id="download-sectioncut-image"),
                createUploadComponent('upload-sectioncut-data', 'Section Cut'),
                createUploadComponent('upload-height-data', 'Height Label'),
                createUploadComponent('upload-sectioncut-template', 'Section Cut Template'),
                dmc.Grid([
                    createMultiSelectComponent('cut-name-list', 'Cuts'),
                    createMultiSelectComponent('load-case-name', 'Load Cases', value=['1.0D+0.5L', 'SC - TP', 'SC - TN', 'MCE-All GM Average (Seis Only)']),
                    createTextInputComponent(idName='sectionCut-model-name', label='Model Name', description='Enter the model name', value='305'),
                ]),
                dmc.Accordion(
                    children=[
                        dmc.AccordionItem(
                            [
                                dmc.AccordionControl(dmc.Text("Click to reveal plot formatting options...", fw=500, size = 'lg', c='blue')),
                                dmc.AccordionPanel(
                                    dmc.Grid([
                                        dmc.GridCol(
                                            html.Div(id='sectionCut-cutName-lineType-Table', children=[]),
                                            span=6,
                                            style={'display': 'flex', 'justifyContent': 'center'}
                                        ),
                                        dmc.GridCol(
                                            html.Div(id='sectionCut-case-id-color-type-Table', children=[]),
                                            span=6,
                                            style={'display': 'flex', 'justifyContent': 'center'}
                                        ),
                                    ], gutter=0),
                                )
                            ], value = 'ShowSectionCutPlotFormatting')
                    ], multiple = True, variant = 'filled', chevronPosition = 'left'),
                
                dmc.Grid([
                    createSelectComponent('sectionCut-input-unit', values=['lb,in,F', 'lb,ft,F', 'kip,in,F', 'kip,ft,F', 'kN,mm,C', 
                                                                           'kN,m,C', 'Kgf,mm,C', 'Kgf,m,C', 'N,mm,C', 'N,m,C', 
                                                                           'Tonf,mm,C','Tonf,m,C', 'kN,cm,C', 'Kgf,cm,C', 'N,cm,C', 
                                                                           'Tonf,cm,C'], label='Input Unit', defaultValue='kN,m,C'),
                    createSelectComponent('sectionCut-output-unit', values=['lb,in,F', 'lb,ft,F', 'kip,in,F', 'kip,ft,F', 'kN,mm,C', 
                                                                           'kN,m,C', 'Kgf,mm,C', 'Kgf,m,C', 'N,mm,C', 'N,m,C', 
                                                                           'Tonf,mm,C','Tonf,m,C', 'kN,cm,C', 'Kgf,cm,C', 'N,cm,C', 
                                                                           'Tonf,cm,C'], label='Output Unit', defaultValue='kN,m,C'),
                    createRadioComponent(idName='sectionCut-agg-type', values = ['Ind', 'Average', 'Min', 'Max'], showLabel = 'Aggregation Type'),
                ]),

                dmc.Grid([
                    createTextInputComponent(idName='sectionCut-plot-title',
                                             label='Enter the title for the plots'),
                    createTextInputComponent(idName='sectionCut-plot-filename',
                                             label='Enter the file name for the plots',
                                             value='SectionCut Forces'),
                ]),

                dmc.Accordion(
                    children=[
                        dmc.AccordionItem(
                            [
                                dmc.AccordionControl(dmc.Text("Click to reveal plot limit options...", fw=500, size = 'lg', c='blue')),
                                dmc.AccordionPanel(
                                    html.Div([createNumberInputComponent('Shear',    -25e2,   25e2, 500, 'kN'),
                                    createNumberInputComponent('Axial',        0,   25e3, 5e3, 'kN'),
                                    createNumberInputComponent('Moment',    -1e5,    2e5, 5e4, 'kNm'),
                                    createNumberInputComponent('Torsion',   -1e4,    1e4, 5e3, 'kNm'),
                                    createNumberInputComponent('Height', -60.365, 29.835,  10, 'm')])
                                )
                            ], value = 'ShowSectionCutPlotLimit')
                    ], multiple = True, variant = 'filled', chevronPosition = 'left'),
                            

                #horizontal_spacing=0.05
                dmc.Group([
                dmc.Button("Submit", id='submit-button-sectionCut', color="blue"),
                
                dmc.Button("Reset Axis", id='reset-button-sectionCut', color="teal"),
                
                dmc.Button("Clear Data", id='clear-button-sectionCut', color="red"),

                dmc.Button("PDF Export", id="pdf-export-sectionCut", color="green", disabled=True),

                ]),
                dmc.Grid([
                    dmc.GridCol([
                        dash_table.DataTable(id='data-table', page_size=12, style_table={'overflowX': 'auto'})
                    ], span=12),
                ]),
                dmc.Grid([
                        dmc.GridCol(dcc.Graph(id='sectionCut_figure', figure = {}, 
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
                dcc.Download(id="download-sectionCut-pdf"), 
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
                                      description='The file should contain the following tables: "Jt Displacements - Generalized", "Joint Coordinates", "Gen Displ Defs 1 - Translation", "Joint Displacements", "Groups 2 - Assignments"'),
                createUploadComponent('vizGenDisp-upload-height', 'Height Label',
                                      description='The file should contain the following tables: "Floor Elevations"'),
                dmc.Grid([
                    createMultiSelectComponent('vizGenDisp-GMlist', 'Load Cases'),
                    createMultiSelectComponent('vizGenDisp-grid-list', 'Grids'),
                    createMultiSelectComponent('vizGenDisp-disp-list', 'Displacements', data=['U1', 'U2'], value=['U1', 'U2']),  
                ]),

                html.Div(id='vizGenDisp-GMlist-Color-Table', children=[]),
                
                dmc.Grid([
                    createSelectComponent('vizGenDisp-input-unit', values=['lb,in,F', 'lb,ft,F', 'kip,in,F', 'kip,ft,F', 'kN,mm,C', 
                                                                           'kN,m,C', 'Kgf,mm,C', 'Kgf,m,C', 'N,mm,C', 'N,m,C', 
                                                                           'Tonf,mm,C','Tonf,m,C', 'kN,cm,C', 'Kgf,cm,C', 'N,cm,C', 
                                                                           'Tonf,cm,C'], label='Input Unit', defaultValue='kN,m,C'),
                    createSelectComponent('vizGenDisp-output-unit', values=['lb,in,F', 'lb,ft,F', 'kip,in,F', 'kip,ft,F', 'kN,mm,C', 
                                                                           'kN,m,C', 'Kgf,mm,C', 'Kgf,m,C', 'N,mm,C', 'N,m,C', 
                                                                           'Tonf,mm,C','Tonf,m,C', 'kN,cm,C', 'Kgf,cm,C', 'N,cm,C', 
                                                                           'Tonf,cm,C'], label='Output Unit', defaultValue='kip,in,F'),
                    createMultiSelectComponent('vizGenDisp-DispDrift', 'Component', data=['Drift', 'Disp'], value=['Drift', 'Disp']),
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
        self.registerUploadCallbacks('upload-sectioncut-template', 'Section Cut Template', self.updateTemplateUploadText)
        
        self.updateProgressBar('upload-sectioncut-data')
        self.updateProgressBar('upload-height-data')
        self.updateProgressBar('upload-gendisp-group')
        self.updateProgressBar('vizGenDisp-upload-analysis')
        self.updateProgressBar('vizGenDisp-upload-height')
        
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
        
        # Update File Name and plot title base of cuts in cutList
        @self.app.callback(
            [Output('sectionCut-plot-title', 'value'),
            Output('sectionCut-plot-filename', 'value')],
            [Input('cut-name-list', 'value'),
            Input('sectionCut-model-name', 'value')],
        )
        def updateSectionCutPlotTitle(cutList, modelName):
            if not cutList:
                return 'Model XX - Responses (XX)', 'XX_SectionCut_XX'
            return (f'Model {modelName} - Responses ({"_".join(cutList)})', f'{modelName}_SectionCut_{"_".join(cutList)}')


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

        @self.app.callback(
            Output('download-sectionCut-pdf', 'data'),
            Input('pdf-export-sectionCut', 'n_clicks'),
            State('sectionCut_figure', 'figure')
        )
        def exportSectionCutPDF(n_clicks, fig):
            if n_clicks:
                print('Exporting PDF')
                figObj = go.Figure(fig)
                buffer = io.BytesIO()
                pio.write_image(figObj, file=buffer, format='pdf', engine='orca')
                buffer.seek(0)
                #pdf_byte = figObj.to_image(format='pdf', engine = 'kaleido')
                #print(pdf_byte)
                return dcc.send_bytes(buffer.getvalue(), 'SectionCutForces.pdf')
            return None


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

        @self.app.callback(
            Output('sectionCut-cutName-lineType-Table', 'children'),
            Input('cut-name-list', 'value'),
        )
        def updateCutNameLineTypeTable(cutList):
            if not cutList:
                return []
            rows = []
            for cut in cutList:
                row = html.Tr([
                    html.Td(cut, style={'textAlign': 'center', 'padding': '0 15px'}),
                    html.Td(dmc.Select(
                        id = {"type": "sectionCut-lineType", "index": cut},
                        value = 'solid', 
                        data = ['solid', 'dash', 'dot', 'longdash', 'dashdot', 'longdashdot'],
                        nothingFoundMessage=f'No LineType Found',
                        searchable=True), 
                    style={'textAlign': 'center', 'padding': '0 15px'}),
                    html.Td(dmc.TextInput(
                        id = {"type": "sectionCut-cut-id", "index": cut},
                        value = '', required=True,error=''), style={'textAlign': 'center', 'padding': '0 15px'})
                ])
                rows.append(row)
            return html.Table([
                html.Thead(
                    html.Tr([
                        html.Th("Cut Name", style={'textAlign': 'center', 'padding': '0 15px'}),
                        html.Th("Line Type", style={'textAlign': 'center', 'padding': '0 15px'}),
                        html.Th("Cut ID", style={'textAlign': 'center', 'padding': '0 15px'})
                    ])
                ),
                html.Tbody(rows)
            ], style={'margin': 'auto'})
        
        @self.app.callback(
            Output('sectionCut-case-id-color-type-Table', 'children'),
            Input('load-case-name', 'value'),
        )
        def updateCaseIDColorTypeTable(caseList):
            if not caseList:
                return []
            rows = []
            colList = [rgb2hex(color) for color in distinctipy.get_colors(len(caseList), exclude_colors=[(1,1,1)])]
            for cI, case in enumerate(caseList):
                row = html.Tr([
                    html.Td(case, style={'textAlign': 'center', 'padding': '0 15px'}),
                    html.Td(dmc.TextInput(
                        id = {"type": "sectionCut-case-id", "index": case},
                        value = getCaseID(case), required=True,error=''), style={'textAlign': 'center', 'padding': '0 15px'}),
                    html.Td(dmc.ColorInput(
                        id = {"type": "sectionCut-case-color", "index": case},
                        value = getCaseColor(case, colList[cI]),
                        swatches=[ 
                        "#25262b","#868e96","#fa5252","#e64980","#be4bdb",
                        "#7950f2","#4c6ef5","#228be6","#15aabf","#12b886",
                        "#40c057","#82c91e","#fab005","#fd7e14"],
                        required=True,error=''), 
                        style={'textAlign': 'center', 'padding': '0 15px'}),
                    html.Td(dmc.Select(
                        id = {"type": "sectionCut-case-type", "index": case},
                        value = getCaseType(case), 
                        data = ['Lin', 'NonLin', 'RS', 'TH'],
                        nothingFoundMessage=f'No Load Case Type Found',
                        searchable=True), 
                        style={'textAlign': 'center', 'padding': '0 15px'})
                ])
                rows.append(row)
            return html.Table([
                html.Thead(
                    html.Tr([
                        html.Th("Case Name", style={'textAlign': 'center', 'padding': '0 15px'}),
                        html.Th("Case ID", style={'textAlign': 'center', 'padding': '0 15px'}),
                        html.Th("Case Color", style={'textAlign': 'center', 'padding': '0 15px'}),
                        html.Th("Case Type", style={'textAlign': 'center', 'padding': '0 15px'})
                    ])
                ),
                html.Tbody(rows)
            ], style={'margin': 'auto'})
        
        #Validate sectionCut-case-id and sectionCut-case-color
        @self.app.callback(
            [Output({'type': 'sectionCut-case-id', 'index': ALL}, 'error'),
            Output({'type': 'sectionCut-case-color', 'index': ALL}, 'error')],
            [Input({'type': 'sectionCut-case-id', 'index': ALL}, 'value'),
            Input({'type': 'sectionCut-case-color', 'index': ALL}, 'value')],
            prevent_initial_call=True
        )
        def validate_table_names_and_colors(names, colors):
            name_errors = [None] * len(names)
            color_errors = [None] * len(colors)
            if names:
                for i, name in enumerate(names):
                    if not name.strip():
                        name_errors[i] = 'Case ID cannot be blank.'
            
            if colors:
                for i, color in enumerate(colors):
                    if not color:
                        color_errors[i] = 'Case Color cannot be blank.'
            
            return name_errors, color_errors

        
        #Validate the field vizGenDisp-GMname and vizGenDisp-GMcolor
        @self.app.callback(
            [Output({'type': 'vizGenDisp-GMname', 'index': ALL}, 'error'),
            Output({'type': 'vizGenDisp-GMcolor', 'index': ALL}, 'error')],
            [Input({'type': 'vizGenDisp-GMname', 'index': ALL}, 'value'),
            Input({'type': 'vizGenDisp-GMcolor', 'index': ALL}, 'value')],
            prevent_initial_call=True
        )
        def validate_table_names_and_colors(names, colors):
            name_errors = [None] * len(names)
            color_errors = [None] * len(colors)
            if names:
                for i, name in enumerate(names):
                    if not name.strip():
                        name_errors[i] = 'Load Case Name cannot be blank.'
            
            if colors:
                for i, color in enumerate(colors):
                    if not color:
                        color_errors[i] = 'Load Case Color cannot be blank.'
            
            return name_errors, color_errors
        
        @self.app.callback(
            Output('vizGenDisp-GMlist-Color-Table', 'children'),
            Input('vizGenDisp-GMlist', "value")
        )
        def updateGMlistColorTable(GMlist):
            if not GMlist:
                return []
            rows = []
            colList = [rgb2hex(color) for color in distinctipy.get_colors(len(GMlist), exclude_colors=[(1,1,1)])]
            for i, GM in enumerate(GMlist):
                row = html.Tr([
                    html.Td(GM, style={'textAlign': 'center', 'padding': '0 15px'}),
                    html.Td(dmc.TextInput(
                        id = {"type": "vizGenDisp-GMname", "index": GM},
                        value = GM, required=True,error=''), style={'textAlign': 'center', 'padding': '0 15px'}),
                    html.Td(dmc.ColorInput(
                        id = {"type": "vizGenDisp-GMcolor", "index": GM},
                        value = colList[i],
                        swatches=[
                        "#25262b","#868e96","#fa5252","#e64980","#be4bdb",
                        "#7950f2","#4c6ef5","#228be6","#15aabf","#12b886",
                        "#40c057","#82c91e","#fab005","#fd7e14"],
                        required=True,error=''), 
                        style={'textAlign': 'center', 'padding': '0 15px'}),
                    html.Td(dmc.Select(
                        id = {"type": "vizGenDisp-case-type", "index": GM},
                        value = getCaseType(GM), 
                        data = ['Lin', 'NonLin', 'RS', 'TH'],
                        nothingFoundMessage=f'No Load Case Type Found',
                        searchable=True), 
                        style={'textAlign': 'center', 'padding': '0 15px'})
                ])
                rows.append(row)
            return html.Table([
                html.Thead(
                    html.Tr([
                        html.Th("Load Case Name", style={'textAlign': 'center', 'padding': '0 15px'}),
                        html.Th("Load Case Identifier", style={'textAlign': 'center', 'padding': '0 15px'}),
                        html.Th("Load Case Color", style={'textAlign': 'center', 'padding': '0 15px'}),
                        html.Th("Load Case Type", style={'textAlign': 'center', 'padding': '0 15px'})
                    ])
                ),
                html.Tbody(rows)
            ], style={'margin': 'auto'})

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
             Output('vizGenDisp-grid-list', 'value'),
             Output('vizGenDisp-disp-list', 'data'),
             Output('vizGenDisp-disp-list', 'value')],
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
            return no_update, no_update, no_update, no_update, no_update
        
        # Plot the Generalized Displacement
        @self.app.callback(
            Output('GenDispPlot-download-modal', 'hide'),
            Output('download-GenDispPlot-excel', 'data'),
            Input('plot-button-vizGenDisp', 'n_clicks'),
            State('vizGenDisp-GMlist', 'value'),
            State({'type': 'vizGenDisp-GMcolor', 'index': ALL}, 'value'),
            State({'type': 'vizGenDisp-GMname', 'index': ALL}, 'value'),
            State('vizGenDisp-grid-list', 'value'),
            State('vizGenDisp-disp-list', 'value'),
            State('vizGenDisp-DriftLim', 'value'),
            State('vizGenDisp-DriftMax', 'value'),
            State('vizGenDisp-HeightMin', 'value'),
            State('vizGenDisp-HeightMax', 'value'),
            State('vizGenDisp-DriftStep', 'value'),
            State('vizGenDisp-DriftLim-label', 'value'),
            State('vizGenDisp-ShowLimit', 'value'),
            State('vizGenDisp-DispDrift', 'value'),
            State({'type':'vizGenDisp-case-type', 'index': ALL}, 'value'),
            State('vizGenDisp-DispMin', 'value'),
            State('vizGenDisp-DispMax', 'value'),
            State('vizGenDisp-DispStep', 'value'),
            State('vizGenDisp-input-unit', 'value'),
            State('vizGenDisp-output-unit', 'value'),
            suppress_callback_exceptions=True
        )
        def plotGenDisp(n_clicks, GMlist, caseColor, caseName, gridList, dispList, 
                        Dlim, Dmax, Hmin, Hmax, Dstep, DlimName, showLimit, plotList, caseType, 
                        DispMin, DispMax, DispStep, inUnit, outUnit):
            if n_clicks:
                if self.conn is not None:
                    units = UnitConvertor(inUnit, outUnit)
                    lenConv = units.convert_length(1)
                    lenUnit = units.printUnit('length')
                    heightMult = UnitConvertor(inUnit, 'kN,m,C').convert_length(1)
                    self.genDisp = GeneralizedDisplacement(analysisFileConnection = self.conn,
                                                   heightFileConnection = self.height_conn,
                                                   Dlim = Dlim, Dmax=Dmax, DlimName = DlimName, Dstep = Dstep,
                                                   Hmin=Hmin, Hmax=Hmax, showLimit = showLimit, plotList = plotList, 
                                                   caseType = caseType, DispMin = DispMin, DispMax = DispMax, 
                                                   DispStep = DispStep, lenConv = lenConv, lenUnit = lenUnit, heightMult = heightMult)
                    self.genDisp.readMainFile()
                    self.genDisp.readDefinitionFile()
                    self.genDisp.readHeightFile()
                    return False, self.genDisp.plotData(gridList=gridList, GMList=GMlist, dispList=dispList, colList=caseColor, nameList=caseName)
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
             Output('sectionCut_figure', 'figure', allow_duplicate=True)],
            Input('clear-button-sectionCut', 'n_clicks'),
            prevent_initial_call=True,
            suppress_callback_exceptions=True
        )(self.clearData)

        # Reset the axis
        self.app.callback(
            Output('sectionCut_figure', 'figure', allow_duplicate=True),
            [Input('reset-button-sectionCut', 'n_clicks')],
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
            Output('sectionCut_figure', 'figure', allow_duplicate=True),
            Output('sectionCut_figure', 'config', allow_duplicate=True),],
            #Output("download-sectioncut-image", "data"),],
            [Input('submit-button-sectionCut', 'n_clicks')],
            [State('cut-name-list', 'value'),State({'type': 'sectionCut-lineType', 'index': ALL}, 'value'),
            State('load-case-name', 'value'),State({'type': 'sectionCut-case-color', 'index': ALL}, 'value'),State({'type': 'sectionCut-case-id', 'index': ALL}, 'value'),State({'type': 'sectionCut-case-type', 'index': ALL}, 'value'),
            State('sectionCut-plot-title', 'value'), State('sectionCut-plot-filename', 'value'),
            [State('shear-min', 'value'),State('shear-max', 'value'),State('shear-step', 'value')],
            [State('axial-min', 'value'),State('axial-max', 'value'),State('axial-step', 'value')],
            [State('moment-min', 'value'),State('moment-max', 'value'),State('moment-step', 'value')],
            [State('torsion-min', 'value'),State('torsion-max', 'value'),State('torsion-step', 'value')],
            [State('height-min', 'value'),State('height-max', 'value'),State('height-step', 'value')],
            State('sectionCut-agg-type', 'value'), State('sectionCut-input-unit', 'value'), State('sectionCut-output-unit', 'value'), 
            State({'type': 'sectionCut-cut-id', 'index': ALL}, 'value')],
            prevent_initial_call=True,
            suppress_callback_exceptions=True
        )(self.plotData)

        # Flask route for downloading the image
    
    def routes(self):
        @self.app.server.route('/download_image/<filename>')
        def download_image(filename):
            img_bytes = io.BytesIO()
            pio.write_image(self.fig, img_bytes, format='png')
            img_bytes.seek(0)
            return send_file(img_bytes, mimetype='image/png', attachment_filename=filename, as_attachment=True)

    
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
            [Output(f'{componentID}-progress', 'value'),
            Output('file-upload-status', 'data', allow_duplicate=True),
            Output(componentID, 'children')],
            [Input(componentID, 'contents'),
            State(componentID, 'filename'),
            State('file-upload-status', 'data')],
            prevent_initial_call=True,
            suppress_callback_exceptions=True,
            running=[(Output(f'{componentID}-progress', 'striped'), True, False), (Output(f'{componentID}-progress', 'animated'), True, False)]
        )
        def updateFileName(contents, filename, storedData):
            trigger = callback_context.triggered[0]['prop_id'].split('.')[0]
            
            generator = callbackMethod(contents=contents, filename=filename, 
                                     fileCategory=fileCategory,storedData=storedData)
            results = []
            for progressVal, storage, textVal in generator:
                self.fileUploadProgress[f'{componentID}-progress'] = progressVal
                results.append((progressVal, storage, textVal))
            
            return results[-1] if results else (0, storedData, no_update)
    
    # Create a callback to update the value of f'{componentID}-progress' continuously in the background
    def updateProgressBar(self, componentID):
        @self.app.callback(
            Output(f'{componentID}-progress', 'value', allow_duplicate=True),
            [Input('interval-component', 'n_intervals')],
            prevent_initial_call=True,
        )
        def updateProgress(n_intervals):
            if self.uploadCallbackRunning:
                return self.fileUploadProgress.get(f'{componentID}-progress', 0)
            else:
                return no_update

    
    def updateTemplateUploadText(self, **kwargs):
        contents = kwargs.get('contents')
        filename = kwargs.get('filename')
        fileCategory = kwargs.get('fileCategory')
        storedData = kwargs.get('storedData')
        self.SectionCutTemplate = None 
        if contents is not None:
            if storedData is None:
                storedData = {}
            _, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            file = io.BytesIO(decoded)
            self.plotList = pd.read_excel(file)
            print(self.plotList)
            yield 100, storedData, html.Div(['File ', html.B(html.A(filename, style = {'color':'blue'})), ' Uploaded. Drag/Drop/Select another file if desired.'])
        else:
            yield 0, no_update, html.Div([
                f'Drag and Drop the {fileCategory} File or ',
                html.A('Select a File')
            ])

        

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
            
            #print('Reading File....fileCategory:', fileCategory)
            if fileCategory in ['Section Cut', 'Drift Group','Generalized Displacement']:
                progress_gen = connectDB(file, dbName=fileCategory.replace(' ', '')+'File')
            else:
                progress_gen = connectDB(file, dbName='HeightFile')
            connection = None
            for progress in progress_gen:
                if isinstance(progress, dict):
                    self.uploadCallbackRunning = True
                    progressVal = progress.get('progress')
                    #print('Progress:', progressVal)
                    yield progressVal, no_update, no_update
                else:
                    connection = progress
            if connection:
                self.uploadCallbackRunning = False
                if fileCategory in ['Section Cut', 'Drift Group','Generalized Displacement']:
                    self.conn = connection
                    if fileCategory == 'Section Cut':
                        storedData['SectionCutDataFileUploaded'] = 'Complete'
                    elif fileCategory == 'Drift Group':
                        storedData['DriftGroupFileUploaded'] = 'Complete'
                    elif fileCategory == 'Generalized Displacement':
                        storedData['vizDataFileUploaded'] = 'Complete'                    
                else:                
                    self.height_conn = connection
                    query = 'SELECT "FloorLabel" as story, CAST("SAP2000Elev" AS NUMERIC) as height FROM "Floor Elevations"'        
                    self.height_data = getData(self.height_conn, query=query)
                    storedData['heightFileUploaded'] = 'Complete'
            yield 100, storedData, html.Div(['File ', html.B(html.A(filename, style = {'color':'blue'})), ' Uploaded. Drag/Drop/Select another file if desired.'])
        else:
            yield 0, no_update, html.Div([
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
                                                   Dlim = Dlim, Dmax=Dmax, DlimName = DlimName, Dstep = Dstep,
                                                   Hmin=Hmin, Hmax=Hmax, showLimit = showLimit)
            return self.genDisp.populateFields()
        return [], [], [], [], []


    def updateCutCaseName(self, contents):
        if not contents:
            return [],[]
        if self.conn is not None:
            query = 'SELECT DISTINCT "OutputCase" FROM "Section Cut Forces - Analysis"'
            data = getData(self.conn, query=query)
            data = data['OutputCase'].tolist()
            #data = [row[0] for row in data]
            data.sort()

            query = 'SELECT DISTINCT "SectionCut" FROM "Section Cut Forces - Analysis"'
            cutNames = getData(self.conn, query=query)
            cutGroups = getCutGroup(cutNames['SectionCut'].tolist())
            #cutGroups = getCutGroup([row[0] for row in cutNames])
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
    
    def plotData(self, plotClicks, cut_name_list, typeList, load_case_name, colList, loadLabel, 
                 loadType, plot_title,file_name, shear_lims, axial_lims, moment_lims, torsion_lims, 
                 height_lims, agg_type, inUnit, outUnit, cut_id):
        if plotClicks:
            self.fig.data = []
            data = getCutForces(self.conn, cut_name_list, load_case_name)
            self.allLegendList = []
            aggcolor = []

            for Li, lType in enumerate(loadType):
                if lType == 'TH' and agg_type != 'Ind':
                    aggcolor.append(colList[Li])
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
                        self.plotCases(colList, typeList, cutI, cut_id[cutI], cI, case, filtered_data, None, True, SF = 1.0, loadLabel = loadLabel[cI], inUnit = inUnit, outUnit = outUnit)
                    elif loadType[cI] == 'RS':
                        self.plotCases(colList, typeList, cutI, cut_id[cutI], cI, case, filtered_data, 'Max', True, SF = 1.0, loadLabel = loadLabel[cI], inUnit = inUnit, outUnit = outUnit)
                        self.plotCases(colList, typeList, cutI, cut_id[cutI], cI, case, filtered_data, 'Max', False, SF = -1.0, loadLabel = loadLabel[cI], inUnit = inUnit, outUnit = outUnit)
                    elif loadType[cI] == 'NonLin':
                        self.plotCases(colList, typeList, cutI, cut_id[cutI], cI, case, filtered_data, 'Max', True, SF = 1.0, loadLabel = loadLabel[cI], inUnit = inUnit, outUnit = outUnit)
                        self.plotCases(colList, typeList, cutI, cut_id[cutI], cI, case, filtered_data, 'Min', False, SF = 1.0, loadLabel = loadLabel[cI], inUnit = inUnit, outUnit = outUnit)
                    elif loadType[cI] == 'TH':
                        showLabel = True if agg_type == 'Ind' else False
                        lineWidth = 2 if agg_type == 'Ind' else 1
                        self.plotCases(colList, typeList, cutI, cut_id[cutI], cI, case, filtered_data, 'Max', showLabel, SF = 1.0, loadLabel = loadLabel[cI], lineWidth=lineWidth, inUnit = inUnit, outUnit = outUnit)
                        self.plotCases(colList, typeList, cutI, cut_id[cutI], cI, case, filtered_data, 'Min', False, SF = 1.0, loadLabel = loadLabel[cI], lineWidth=lineWidth, inUnit = inUnit, outUnit = outUnit)
                if agg_type == 'Average':
                    self.plotCases([aggcolor[0]], typeList, cutI, cut_id[cutI], cI, case, avgData, 'Max', True, SF = 1.0, loadLabel = 'Average MCE', inUnit = inUnit, outUnit = outUnit)
                    self.plotCases([aggcolor[0]], typeList, cutI, cut_id[cutI], cI, case, avgData, 'Min', False, SF = 1.0, loadLabel = 'Average MCE', inUnit = inUnit, outUnit = outUnit)
                if agg_type == 'Min':
                    self.plotCases([aggcolor[0]], typeList, cutI, cut_id[cutI], cI, case, minData, 'Max', True, SF = 1.0, loadLabel = 'Min MCE', inUnit = inUnit, outUnit = outUnit)
                    self.plotCases([aggcolor[0]], typeList, cutI, cut_id[cutI], cI, case, maxData, 'Min', False, SF = 1.0, loadLabel = 'Min MCE', inUnit = inUnit, outUnit = outUnit)
                if agg_type == 'Max':
                    self.plotCases([aggcolor[0]], typeList, cutI, cut_id[cutI], cI, case, maxData, 'Max', True, SF = 1.0, loadLabel = 'Max MCE', inUnit = inUnit, outUnit = outUnit)
                    self.plotCases([aggcolor[0]], typeList, cutI, cut_id[cutI], cI, case, minData, 'Min', False, SF = 1.0, loadLabel = 'Max MCE', inUnit = inUnit, outUnit = outUnit)
            
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

            config = {
            'displayModeBar': True,
            'displaylogo': False,
            'toImageButtonOptions': {
                'format': 'png',
                'filename': file_name,
                'scale': 6
            },
            'doubleClick': 'reset',
            'modeBarButtonsToAdd': ['drawline', 'drawcircle', 'drawrect', 'eraseshape', 'togglespikelines']
            }

            #print('Plotting Done')
            #with tempfile.NamedTemporaryFile(suffix=".png") as tmpfile:
            #    pio.write_image(self.fig, tmpfile.name, format="png")
            #    tmpfile.seek(0)
            #    img_bytes = tmpfile.read()

            #print('image bytes read')

            return data.to_dict('records'), self.fig, config
    
    def runApp(self):
        self.app.run_server(debug=True, port = self.port) 

    #def runApp(self):
        # Start Dash server in a separate thread
    #    app_thread = threading.Thread(target=self._run_dash_server)
    #    app_thread.daemon = True  # Allows thread to exit when the main program exits
    #    app_thread.start()

    def _run_dash_server(self):
        # This method will be run in a separate thread
        self.app.run_server(debug=True, port=self.port)    

    def plotCases(self, colList, typeList, cutI, cutName, cI, case, filtered_data, StepType, showLegend, SF=1.0, loadLabel = '', agg_type = 'Ind', lineWidth = 2, inUnit = 'kN,m,C', outUnit = 'kN,m,C'):
        if cutName:
            legendEntry = wrap_text(loadLabel+'_'+cutName)
        else:
            legendEntry = wrap_text(loadLabel)
        if StepType is not None:
            filtered_data = filtered_data[filtered_data['StepType'] == StepType]
        if legendEntry in self.allLegendList or loadLabel == '':
            showLegend = False
        else:
            self.allLegendList.append(legendEntry)
        units = UnitConvertor(inUnit, outUnit)
        self.fig.add_trace(go.Scatter(y=filtered_data['CutHeight'], x=units.convert(1,'force')*SF*filtered_data['F1'].apply(lambda x: float(x)), mode='lines', name=legendEntry, line = dict(color =colList[cI%len(colList)], dash=typeList[cutI%len(typeList)], width=lineWidth),showlegend=showLegend, legendgroup=loadLabel+cutName), row=1, col=1, secondary_y=False)
        self.fig.add_trace(go.Scatter(y=filtered_data['CutHeight'], x=units.convert(1,'force')*SF*filtered_data['F2'].apply(lambda x: float(x)), mode='lines', name=legendEntry, line = dict(color =colList[cI%len(colList)], dash=typeList[cutI%len(typeList)], width=lineWidth),showlegend=False, legendgroup=loadLabel+cutName), row=1, col=2, secondary_y=False)
        self.fig.add_trace(go.Scatter(y=filtered_data['CutHeight'], x=units.convert(1,'force')*SF*filtered_data['F3'].apply(lambda x: float(x)), mode='lines', name=legendEntry, line = dict(color =colList[cI%len(colList)], dash=typeList[cutI%len(typeList)], width=lineWidth),showlegend=False, legendgroup=loadLabel+cutName), row=1, col=3, secondary_y=False)
        self.fig.add_trace(go.Scatter(y=filtered_data['CutHeight'], x=units.convert(1,'moment')*SF*filtered_data['M2'].apply(lambda x: float(x)), mode='lines', name=legendEntry, line = dict(color =colList[cI%len(colList)], dash=typeList[cutI%len(typeList)], width=lineWidth),showlegend=False, legendgroup=loadLabel+cutName), row=2, col=1, secondary_y=False)
        self.fig.add_trace(go.Scatter(y=filtered_data['CutHeight'], x=units.convert(1,'moment')*SF*filtered_data['M1'].apply(lambda x: float(x)), mode='lines', name=legendEntry, line = dict(color =colList[cI%len(colList)], dash=typeList[cutI%len(typeList)], width=lineWidth),showlegend=False, legendgroup=loadLabel+cutName), row=2, col=2, secondary_y=False)
        self.fig.add_trace(go.Scatter(y=filtered_data['CutHeight'], x=units.convert(1,'moment')*SF*filtered_data['M3'].apply(lambda x: float(x)), mode='lines', name=legendEntry, line = dict(color =colList[cI%len(colList)], dash=typeList[cutI%len(typeList)], width=lineWidth),showlegend=False, legendgroup=loadLabel+cutName), row=2, col=3, secondary_y=False)

        

globalApp = GlobalAnalysisApp()
server = globalApp.app.server

if __name__ == '__main__':
    globalApp.runApp()
    
