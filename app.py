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
from utils.appComponents import createUploadComponent, createMultiSelectComponent, createTextInputComponent, createNumberInputComponent



class GlobalAnalysisApp:
    def __init__(self):
        self.app = Dash(__name__)
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
        self.fig = make_subplots(rows=2, cols=3, subplot_titles=('F1', 'F2', 'F3', 'M1', 'M2', 'M3'),
                                 vertical_spacing=0.1, horizontal_spacing=0.08, specs=[[{"secondary_y": True}, {"secondary_y": True}, {"secondary_y": True}],
                                                                                      [{"secondary_y": True}, {"secondary_y": True}, {"secondary_y": True}]])
        self.createMenu()
        #self.createLayout()
        self.registerCallbacks()
        
    def createMenu(self):
        self.app.layout = dmc.MantineProvider(
            theme={"colorScheme": "light"},
            children = [
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
            dmc.Title("Define Section Cuts", c="blue", size="h2"),
        )

    def visualizeSectionCut(self):
        return dmc.MantineProvider(
            theme={"colorScheme": "light"},
            children=[
                createUploadComponent('upload-data', 'Section Cut'),
                createUploadComponent('upload-height-data', 'Height Label'),
                dmc.Grid([
                    createMultiSelectComponent('cut-name-list', 'Cuts'),
                    createTextInputComponent('line-type-list', 'Enter the line types for Cuts', 'Enter line types, separated by commas', 'solid'),
                    createTextInputComponent('load-case-types', 'Enter the Load Case type (Lin, RS, Others)', 'Enter Load Case types, separated by commas', ''),
                ]),
                dmc.Grid([
                    createMultiSelectComponent('load-case-name', 'Load Cases'),
                    createTextInputComponent('load-case-colors', 'Enter the colors for Load Cases', 'Enter Load Case colors, separated by commas', 'red,blue,black'),
                    createTextInputComponent('load-case-labels', 'Enter the labels for Load Cases', 'Enter Load Case labels, separated by commas', ''),

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
                dmc.Button("Submit", id='submit-button', color="blue"),
                
                dmc.Button("Reset Axis", id='reset-button', color="teal"),
                
                dmc.Button("Clear Data", id='clear-button', color="red"),
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
            dmc.Title("Define Generalized Displacements", c="blue", size="h2"),
        )
    
    def visualizeGeneralizedDisp(self):
        return dmc.MantineProvider(
            dmc.Title("Visualize Generalized Displacements", c="blue", size="h2"),
        )


    def registerCallbacks(self):
        @self.app.callback(
            Output('visualize-section-cuts', 'children'),
            [Input('visualize-section-cuts', 'value')]
        )
        def visualizeSectionCuts(tab):
            if tab == 'visualize-section-cuts':
                return self.visualizeSectionCut()
            return no_update

        @self.app.callback(
            Output('define-section-cuts', 'children'),
            [Input('define-section-cuts', 'value')]
        )
        def defineSectionCuts(tab):
            if tab == 'define-section-cuts':
                return self.defineSectionCut()
            return no_update
        
        @self.app.callback(
            Output('visualize-drifts', 'children'),
            [Input('visualize-drifts', 'value')]
        )
        def visualizeDrifts(tab):
            if tab == 'visualize-drifts':
                return self.visualizeGeneralizedDisp()
            return no_update
        
        @self.app.callback(
            Output('define-drifts', 'children'),
            [Input('define-drifts', 'value')]
        )
        def defineDrifts(tab):
            if tab == 'define-drifts':
                return self.defineGeneralizedDisp()
            return no_update

        #Update the Section Cut file
        self.app.callback(
            Output('upload-data', 'children'),
            Input('upload-data', 'contents'),
            State('upload-data', 'filename')
        )(self.updateCutFileUploadText)

        #Update the Height Label file
        self.app.callback(
            Output('upload-height-data', 'children'),
            Input('upload-height-data', 'contents'),
            State('upload-height-data', 'filename')
        )(self.updateHeightFileUploadText)

        #Update the Load Case Names and Section Cut Names
        self.app.callback(
        [Output('load-case-name', 'data'),
        Output('cut-name-list', 'data')],
        Input('upload-data', 'contents')
        )(self.updateCutCaseName)

        # Clear the data
        self.app.callback(
            [Output('data-table', 'data', allow_duplicate=True),
             Output('subplot-graph', 'figure', allow_duplicate=True)],
            Input('clear-button', 'n_clicks'),
            prevent_initial_call=True
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
            prevent_initial_call=True
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
            [State('height-min', 'value'),State('height-max', 'value'),State('height-step', 'value')]],
            prevent_initial_call=True
        )(self.plotData)

    def updateCutFileUploadText(self, contents, filename):
        if contents is not None:
            return html.Div(['File ', html.B(html.A(filename, style = {'color':'blue'})), ' Uploaded. Drag/Drop/Select another file if desired.'])
        else:
            return html.Div([
                'Drag and Drop the Section Cut File or ',
                html.A('Select a File')
            ])

    def updateHeightFileUploadText(self, content, filename):
        if content is not None:
            _, content_string = content.split(',')
            decoded = base64.b64decode(content_string)
            file = io.BytesIO(decoded)
            height_conn = connectDB(file)
            query = 'SELECT FloorLabel as story, SAP2000Elev as height FROM "Floor Elevations"'        
            self.height_data = getData(height_conn, query=query)
            height_conn.close()
            return html.Div(['File ', html.B(html.A(filename, style = {'color':'blue'})), ' Uploaded. Drag/Drop/Select another file if desired.'])
        else:
            return html.Div([
                'Drag and Drop the Height Label File or ',
                html.A('Select a File')
            ])

    def updateCutCaseName(self, content):
        if not content:
            return [],[]
        _, content_string = content.split(',')
        decoded = base64.b64decode(content_string)
        file = io.BytesIO(decoded)
        self.conn = connectDB(file)
        query = 'SELECT DISTINCT OutputCase FROM "Section Cut Forces - Analysis"'
        data = getData(self.conn, query=query)

        query = 'SELECT DISTINCT SectionCut FROM "Section Cut Forces - Analysis"'
        cutNames = getData(self.conn, query=query)
        cutGroups = getCutGroup(cutNames['SectionCut'].tolist())
        return data['OutputCase'].tolist(), cutGroups

    def updateAxis(self, shear_lims, axial_lims, moment_lims, torsion_lims, height_lims):
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
                    title_text=f"Shear Along Axis {col} (kN)",
                    title_font=self.AXIS_TITLE_FONT,
                    tickfont=self.TICK_FONT,
                    showline=True, showgrid=True, zeroline=True, mirror=True,
                    row=1, col=col,
                    range=shear_lims[0:2],
                    dtick=shear_lims[-1]
                )
                self.fig.update_xaxes(
                    title_text=f"Flexure About Axis {col} (kNm)",
                    title_font=self.AXIS_TITLE_FONT,
                    tickfont=self.TICK_FONT,
                    showline=True, showgrid=True, zeroline=True, mirror=True,
                    row=2, col=col,
                    range=moment_lims[0:2],
                    dtick=moment_lims[-1]
                )

        self.fig.update_xaxes(
                title_text="Axial (kN)",
                title_font=self.AXIS_TITLE_FONT,
                tickfont=self.TICK_FONT,
                showline=True, showgrid=True, zeroline=True, mirror=True,
                row=1, col=3,
                range=axial_lims[0:2],
                dtick=axial_lims[-1]
            )
        self.fig.update_xaxes(
                title_text="Torsion (kNm)",
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
    
    def plotData(self, plotClicks, cut_name_list, line_type_list, load_case_name, load_case_color, load_case_label, load_case_type, plot_title, shear_lims, axial_lims, moment_lims, torsion_lims, height_lims):
        if plotClicks:
            self.fig.data = []
            data = getCutForces(self.conn, cut_name_list, load_case_name)
            colList = load_case_color.split(',') if load_case_color else [distinctipy.get_hex(col) for col in distinctipy.get_colors(len(load_case_name))]
            typeList = line_type_list.split(',') if line_type_list else ['solid', 'dash', 'dot', 'dashdot', 'longdash', 'longdashdot']
            loadLabel = load_case_label.split(',') if load_case_label else load_case_name
            loadType = load_case_type.split(',') if load_case_type else ['Others']*len(load_case_name)
            self.allLegendList = []


            for cutI, cutName in enumerate(cut_name_list):
                for cI, case in enumerate(load_case_name):
                    filtered_data = data[(data['OutputCase'] == case) & (data['SectionCut'].str.startswith(cutName))]
                    if loadType[cI] == 'Lin':
                        self.plotCases(colList, typeList, cutI, cutName, cI, case, filtered_data, None, True, SF = 1.0, loadLabel = loadLabel[cI])
                    elif loadType[cI] == 'RS':
                        self.plotCases(colList, typeList, cutI, cutName, cI, case, filtered_data, 'Max', True, SF = 1.0, loadLabel = loadLabel[cI])
                        self.plotCases(colList, typeList, cutI, cutName, cI, case, filtered_data, 'Max', False, SF = -1.0, loadLabel = loadLabel[cI])
                    else:
                        self.plotCases(colList, typeList, cutI, cutName, cI, case, filtered_data, 'Max', True, SF = 1.0, loadLabel = loadLabel[cI])
                        self.plotCases(colList, typeList, cutI, cutName, cI, case, filtered_data, 'Min', False, SF = 1.0, loadLabel = loadLabel[cI])

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
                            orientation="h",
                            yanchor="bottom",
                            y=-0.1,
                            xanchor="center",
                            x=0.5,
                            traceorder="normal",
                            tracegroupgap=20,
                        ),
                        margin=dict(l=20, r=20, t=60, b=20),
                        )
            
            self.updateAxis(shear_lims, axial_lims, moment_lims, torsion_lims, height_lims)
            return data.to_dict('records'), self.fig
    
    def runApp(self):
        self.app.run_server(debug=True, port = self.port)     

    def plotCases(self, colList, typeList, cutI, cutName, cI, case, filtered_data, StepType, showLegend, SF=1.0, loadLabel = ''):
        if StepType is not None:
            filtered_data = filtered_data[filtered_data['StepType'] == StepType]
        #print(filtered_data)
        if loadLabel+'_'+cutName in self.allLegendList or loadLabel == '':
            showLegend = False
        else:
            self.allLegendList.append(loadLabel+'_'+cutName)
        self.fig.add_trace(go.Scatter(y=filtered_data['CutHeight'], x=SF*filtered_data['F1'], mode='lines', name=loadLabel+'_'+cutName, line = dict(color =colList[cI%len(colList)], dash=typeList[cutI%len(typeList)]),showlegend=showLegend, legendgroup=loadLabel+cutName), row=1, col=1, secondary_y=False)
        self.fig.add_trace(go.Scatter(y=filtered_data['CutHeight'], x=SF*filtered_data['F2'], mode='lines', name=loadLabel+'_'+cutName, line = dict(color =colList[cI%len(colList)], dash=typeList[cutI%len(typeList)]),showlegend=False, legendgroup=loadLabel+cutName), row=1, col=2, secondary_y=False)
        self.fig.add_trace(go.Scatter(y=filtered_data['CutHeight'], x=SF*filtered_data['F3'], mode='lines', name=loadLabel+'_'+cutName, line = dict(color =colList[cI%len(colList)], dash=typeList[cutI%len(typeList)]),showlegend=False, legendgroup=loadLabel+cutName), row=1, col=3, secondary_y=False)
        self.fig.add_trace(go.Scatter(y=filtered_data['CutHeight'], x=SF*filtered_data['M1'], mode='lines', name=loadLabel+'_'+cutName, line = dict(color =colList[cI%len(colList)], dash=typeList[cutI%len(typeList)]),showlegend=False, legendgroup=loadLabel+cutName), row=2, col=1, secondary_y=False)
        self.fig.add_trace(go.Scatter(y=filtered_data['CutHeight'], x=SF*filtered_data['M2'], mode='lines', name=loadLabel+'_'+cutName, line = dict(color =colList[cI%len(colList)], dash=typeList[cutI%len(typeList)]),showlegend=False, legendgroup=loadLabel+cutName), row=2, col=2, secondary_y=False)
        self.fig.add_trace(go.Scatter(y=filtered_data['CutHeight'], x=SF*filtered_data['M3'], mode='lines', name=loadLabel+'_'+cutName, line = dict(color =colList[cI%len(colList)], dash=typeList[cutI%len(typeList)]),showlegend=False, legendgroup=loadLabel+cutName), row=2, col=3, secondary_y=False)

        for i in range(1,3):
            for j in range(1,4):
                self.fig.add_trace(go.Scatter(y=[], x=[], mode='lines'), row=i, col=j, secondary_y=True)


globalApp = GlobalAnalysisApp()
server = globalApp.app.server

if __name__ == '__main__':
    globalApp.runApp()
    
