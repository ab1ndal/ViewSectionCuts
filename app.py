from dash import Dash, html, dash_table, dcc, Input, Output, callback, callback_context, no_update, State
import pandas as pd
from readFile import connectDB, getData
from plotGlobalForces import getCutForces, getCutGroup
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import dash_mantine_components as dmc
import distinctipy
import plotly.io as pio
import base64
import io

app = Dash(__name__)
server = app.server

AXIS_TITLE_FONT = dict(size=14)
PLOT_TITLE_FONT = dict(size=20)
OVERALL_PLOT_TITLE_FONT = 25
TICK_FONT = dict(size=12)
LEGEND_FONT = dict(size=14)
conn = None

# Create subplots
fig = make_subplots(rows=2, cols=3, subplot_titles=('F1', 'F2', 'F3', 'M1', 'M2', 'M3'),
                        vertical_spacing=0.1, horizontal_spacing=0.05)

app.layout = dmc.MantineProvider(
    theme={"colorScheme": "light"},
    children=[
        dmc.Title("Global Building Responses", c="blue", size="h2"),
        dmc.Grid([
            dmc.Col([
                dmc.Text("Upload Section Cut File", fw=500, size = 'sm'),
                dcc.Upload(
                    id='upload-data',
                    children=html.Div([
                        'Drag and Drop the Section Cut File or ',
                        html.A('Select a File')
                    ]),
                    style={
                        'width': '90%',
                        'height': '40px',
                        'lineHeight': '40px',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                        'margin': '10px'
                    },
                    multiple=False  # Allow only one file to be uploaded at a time
                )
            ], span=12),
        ]),
        dmc.Grid([
            dmc.Col([
                dmc.Text("Upload Height Label File", fw=500, size = 'sm'),
                dcc.Upload(
                    id='upload-height-data',
                    children=html.Div([
                        'Drag and Drop the Height Labels or ',
                        html.A('Select a File')
                    ]),
                    style={
                        'width': '90%',
                        'height': '40px',
                        'lineHeight': '40px',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                        'margin': '10px'
                    },
                    multiple=False  # Allow only one file to be uploaded at a time
                )
            ], span=12),
        ]),
        dmc.Grid([
        dmc.Col([
            dmc.MultiSelect(
                label='Select the names of Cuts',
                w = 300,
                description='Select Cut Names from the list',
                required=True,
                error = True,
                id='cut-name-list',
                data=[],
                nothingFound='No Cuts Found',
                searchable=True),


        # dmc.TextInput(label='Enter the names of Cuts',
        #               w = 300,
        #               error = True,
        #               id='cut-name-list', 
        #               description='Enter cut names, separated by commas',
        #               required=True),
        ], span=4),
        dmc.Col([
        dmc.TextInput(label='Enter the line types for Load Cases',
                      w = 300,
                      error = True,
                      id='line-type-list',
                      description='Enter line types, separated by commas',
                      required=True,
                      value='solid'),
        ], span=4),
        ]),
        
        dmc.Grid([
            dmc.Col([
            dmc.MultiSelect(
                label='Enter the names of Load Cases',
                w = 300,
                description='Select Load Case Names from the list',
                required=True,
                error = True,
                id='load-case-name',
                data=[],
                nothingFound='No Load Cases Found',
                searchable=True,
                ),
            ], span=4),
            dmc.Col([
            dmc.TextInput(label='Enter the names of colors for load cases',
                      w = 300,
                      error = True,
                      id='load-case-colors', 
                      description='Enter load case color names, separated by commas',
                      required=True,
                      value='red,blue,black'),
            ], span=4),
        ]),
        dmc.TextInput(label='Enter the title for the plots',
                  w = 300,
                  id='plot-title'),
        # Specify the range for the x-axis and y-axis for each subplot
        # each row should have min limit, max limit and step size
        dmc.Grid([
            dmc.Col([
                dmc.NumberInput(min=-9999999, max=9999999,precision=3,label='Shear - Minimum (kN)', id='shear-min', w=300, value=-25e2),
                dmc.NumberInput(min=-9999999, max=9999999,precision=3,label='Axial - Minimum (kN)', id='axial-min', w=300, value=0),
                dmc.NumberInput(min=-9999999, max=9999999,precision=3,label='Moment - Minimum (kNm)', id='moment-min', w=300, value=-1e5),
                dmc.NumberInput(min=-9999999, max=9999999,precision=3,label='Torsion - Minimum (kNm)', id='torsion-min', w=300, value=-1e4),
                dmc.NumberInput(min=-9999999, max=9999999,precision=3,label='Height - Minimum (m)', id='height-min', w=300, value=-60.365),
            ], span=4),
            dmc.Col([
                dmc.NumberInput(min=-9999999, max=9999999,precision=3,label='Shear - Maximum (kN)', id='shear-max', w=300, value=25e2),
                dmc.NumberInput(min=-9999999, max=9999999,precision=3,label='Axial - Maximum (kN)', id='axial-max', w=300, value=25e3),
                dmc.NumberInput(min=-9999999, max=9999999,precision=3,label='Moment - Maximum (kNm)', id='moment-max', w=300, value=2e5),
                dmc.NumberInput(min=-9999999, max=9999999,precision=3,label='Torsion - Maximum (kNm)', id='torsion-max', w=300, value=1e4),
                dmc.NumberInput(min=-9999999, max=9999999,precision=3,label='Height - Maximum (m)', id='height-max', w=300, value=29.835),
            ], span=4),
            dmc.Col([
                dmc.NumberInput(min=-9999999, max=9999999,precision=3,label='Shear - Step Size (kN)', id='shear-step', w=300, value=500),
                dmc.NumberInput(min=-9999999, max=9999999,precision=3,label='Axial - Step Size (kN)', id='axial-step', w=300, value=5e3),
                dmc.NumberInput(min=-9999999, max=9999999,precision=3,label='Moment - Step Size (kNm)', id='moment-step', w=300, value=5e4),
                dmc.NumberInput(min=-9999999, max=9999999,precision=3,label='Torsion - Step Size (kNm)', id='torsion-step', w=300, value=5e3),
                dmc.NumberInput(min=-9999999, max=9999999,precision=3,label='Height - Step Size (m)', id='height-step', w=300, value=10),
            ], span=4),
        ]),
        
        #horizontal_spacing=0.05
        dmc.Button("Submit", id='submit-button', color="blue"),
        
        dmc.Button("Reset Axis", id='reset-button', color="teal"),
        
        dmc.Button("Clear Data", id='clear-button', color="red"),
        dmc.Grid([
            dmc.Col([
                dash_table.DataTable(id='data-table', page_size=12, style_table={'overflowX': 'auto'})
            ], span=12),
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
    ]
)

@app.callback(
    Output('upload-data', 'children'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def update_upload_text(contents, filename):
    if contents is not None:
        return html.Div(['File ', html.B(html.A(filename, style = {'color':'blue'})), ' Uploaded. Drag/Drop/Select another file if desired.'])
    else:
        return html.Div([
            'Drag and Drop the Section Cut File or ',
            html.A('Select a File')
        ])

@app.callback(
    Output('upload-height-data', 'children'),
    Input('upload-height-data', 'contents'),
    State('upload-height-data', 'filename')
)
def update_upload_text(contents, filename):
    if contents is not None:
        return html.Div(['File ', html.B(html.A(filename, style = {'color':'blue'})), ' Uploaded. Drag/Drop/Select another file if desired.'])
    else:
        return html.Div([
            'Drag and Drop the Height Data File or ',
            html.A('Select a File')
        ])


#When upload-data is triggered, the contents of the file are read and the data is stored in the conn variable (used globally)
#Autoupdate the multi-select with the load case names and cut names
@callback(
    Output('load-case-name', 'data'),
    Output('cut-name-list', 'data'),
    Input('upload-data', 'contents')
)
def update_load_case_names(content):
    global conn
    if not content:
        return [],[]
    _, content_string = content.split(',')
    decoded = base64.b64decode(content_string)
    file = io.BytesIO(decoded)
    conn = connectDB(file)
    query = 'SELECT DISTINCT OutputCase FROM "Section Cut Forces - Analysis"'
    data = getData(conn, query=query)

    query = 'SELECT DISTINCT SectionCut FROM "Section Cut Forces - Analysis"'
    cutNames = getData(conn, query=query)
    cutGroups = getCutGroup(cutNames['SectionCut'].tolist())
    return data['OutputCase'].tolist(), cutGroups





@callback(
    [Output('data-table', 'data'),
     Output('subplot-graph', 'figure')],
    [Input('submit-button', 'n_clicks'),
     Input('upload-data', 'contents'),
     Input('upload-height-data', 'contents'),
     Input('cut-name-list', 'value'),
     Input('load-case-name', 'value'),
     Input('load-case-colors', 'value'),
     Input('reset-button', 'n_clicks'),
     Input('plot-title', 'value'),
     Input('clear-button', 'n_clicks'),
     Input('line-type-list', 'value'),
     [Input('shear-min', 'value'),
     Input('shear-max', 'value'),
     Input('shear-step', 'value')],
     [Input('axial-min', 'value'),
     Input('axial-max', 'value'),
     Input('axial-step', 'value')],
     [Input('moment-min', 'value'),
     Input('moment-max', 'value'),
     Input('moment-step', 'value')],
     [Input('torsion-min', 'value'),
     Input('torsion-max', 'value'),
     Input('torsion-step', 'value')],
     [Input('height-min', 'value'),
     Input('height-max', 'value'),
     Input('height-step', 'value')]]
)
def update_output(n_clicks, content, height_content, cut_name_list, load_case_name, load_case_color, reset_clicks, plot_title, clear_clicks, line_type_list, shear_lims, axial_lims, moment_lims, torsion_lims, height_lims):
    global conn
    if not callback_context.triggered:
        return no_update, no_update
    
    if n_clicks or reset_clicks:
        _, height_content_string = height_content.split(',')
        decoded_height = base64.b64decode(height_content_string)
        height_file = io.BytesIO(decoded_height)
        conn_height=connectDB(height_file)
        query = 'SELECT FloorLabel as story, SAP2000Elev as height FROM "Floor Elevations"'        
        height_data = getData(conn_height, query=query)
        conn_height.close()
    
    trigger_id = callback_context.triggered[0]['prop_id'].split('.')[0]

    # Clear data if clear-button was clicked
    if trigger_id == 'clear-button' and clear_clicks:
        fig.data = []
        return no_update, fig
    
    # Reset axes if reset-button was clicked
    if trigger_id == 'reset-button' and reset_clicks:
        # Update y-axes with default settings and ranges
        for row in range(1, 3):
            for col in range(1, 4):
                fig.update_yaxes(
                    row=row, col=col,
                    range=height_lims[0:2],
                    dtick=height_lims[-1],
                    tickvals=height_data['height'].tolist(),
                    ticktext=height_data['story'].tolist()
                )

        # Update x-axes with default settings and ranges
        fig.update_xaxes(row=1, col=1,range=shear_lims[0:2],dtick=shear_lims[-1])

        fig.update_xaxes(row=1, col=2,range=shear_lims[0:2],dtick=shear_lims[-1])

        fig.update_xaxes(row=1, col=3,range=axial_lims[0:2],dtick=axial_lims[-1])

        fig.update_xaxes(row=2, col=1,range=moment_lims[0:2],dtick=moment_lims[-1])

        fig.update_xaxes(row=2, col=2,range=moment_lims[0:2],dtick=moment_lims[-1])

        fig.update_xaxes(row=2, col=3,range=torsion_lims[0:2],dtick=torsion_lims[-1])

        return no_update, fig
    
    if trigger_id == 'submit-button' and n_clicks:
        fig.data = []

        # Default values if inputs are empty
        #cut_name_list = cut_name_list.split(',') if cut_name_list else ['Overall']
        #load_case_name = load_case_name.split(',') if load_case_name else ['SLE-X', 'SLE-Y', '1.0D+0.5L']
        colList = load_case_color.split(',') if load_case_color else [distinctipy.get_hex(col) for col in distinctipy.get_colors(len(load_case_name))]
        typeList = line_type_list.split(',') if line_type_list else ['solid', 'dash', 'dot', 'dashdot', 'longdash', 'longdashdot']

        # Query the database
        # TODO: remove this....
        _, content_string = content.split(',')
        decoded = base64.b64decode(content_string)
        file = io.BytesIO(decoded)
        connection = connectDB(file)

        data = getCutForces(connection, cut_name_list, load_case_name)
        
        output_cases = load_case_name
        

        for cutI, cutName in enumerate(cut_name_list):
            for cI, case in enumerate(output_cases):
                filtered_data = data[(data['OutputCase'] == case) & (data['SectionCut'].str.contains(cutName))]
                plotCases(colList, typeList, cutI, cutName, cI, case, filtered_data, 'Max', True)
                plotCases(colList, typeList, cutI, cutName, cI, case, filtered_data, 'Min', False)

        

        fig.update_layout(
                        title_text=plot_title,
                        title_x=0.5,
                        title_font_size=OVERALL_PLOT_TITLE_FONT,
                        height=1000, width=1500,
                        title = dict(font=PLOT_TITLE_FONT), template="plotly_white",
                        legend=dict(
                            font = LEGEND_FONT,
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        ),
                        margin=dict(l=20, r=20, t=40, b=20),
                        )
        


        fig.update_yaxes(title_text="Height (m)", row=1, col=1, title_font=AXIS_TITLE_FONT, tickfont=TICK_FONT, range=height_lims[0:2], dtick=height_lims[-1], showline=True, showgrid=True, mirror=True, tickvals=height_data['height'].tolist(), ticktext=height_data['story'].tolist())
        fig.update_yaxes(title_text="Height (m)", row=1, col=2, title_font=AXIS_TITLE_FONT, tickfont=TICK_FONT, range=height_lims[0:2], dtick=height_lims[-1], showline=True, showgrid=True, mirror=True, tickvals=height_data['height'].tolist(), ticktext=height_data['story'].tolist())
        fig.update_yaxes(title_text="Height (m)", row=1, col=3, title_font=AXIS_TITLE_FONT, tickfont=TICK_FONT, range=height_lims[0:2], dtick=height_lims[-1], showline=True, showgrid=True, mirror=True, tickvals=height_data['height'].tolist(), ticktext=height_data['story'].tolist())
        fig.update_yaxes(title_text="Height (m)", row=2, col=1, title_font=AXIS_TITLE_FONT, tickfont=TICK_FONT, range=height_lims[0:2], dtick=height_lims[-1], showline=True, showgrid=True, mirror=True, tickvals=height_data['height'].tolist(), ticktext=height_data['story'].tolist())
        fig.update_yaxes(title_text="Height (m)", row=2, col=2, title_font=AXIS_TITLE_FONT, tickfont=TICK_FONT, range=height_lims[0:2], dtick=height_lims[-1], showline=True, showgrid=True, mirror=True, tickvals=height_data['height'].tolist(), ticktext=height_data['story'].tolist())
        fig.update_yaxes(title_text="Height (m)", row=2, col=3, title_font=AXIS_TITLE_FONT, tickfont=TICK_FONT, range=height_lims[0:2], dtick=height_lims[-1], showline=True, showgrid=True, mirror=True, tickvals=height_data['height'].tolist(), ticktext=height_data['story'].tolist())
        fig.update_xaxes(title_text="Shear Along Axis 1 (kN)", row=1, col=1, title_font=AXIS_TITLE_FONT, tickfont=TICK_FONT, range=shear_lims[0:2], dtick=shear_lims[-1], showline=True, showgrid=True, zeroline=True, mirror=True)
        fig.update_xaxes(title_text="Shear Along Axis 2 (kN)", row=1, col=2, title_font=AXIS_TITLE_FONT, tickfont=TICK_FONT, range=shear_lims[0:2], dtick=shear_lims[-1], showline=True, showgrid=True, zeroline=True, mirror=True)
        fig.update_xaxes(title_text="Axial (kN)", row=1, col=3, title_font=AXIS_TITLE_FONT, tickfont=TICK_FONT, range=axial_lims[0:2], dtick=axial_lims[-1],showline=True, showgrid=True, zeroline=True, mirror=True)
        fig.update_xaxes(title_text="Flexure About Axis 1 (kNm)", row=2, col=1, title_font=AXIS_TITLE_FONT, tickfont=TICK_FONT, range=moment_lims[0:2], dtick=moment_lims[-1], showline=True, showgrid=True, zeroline=True, mirror=True)
        fig.update_xaxes(title_text="Flexure About Axis 2 (kNm)", row=2, col=2, title_font=AXIS_TITLE_FONT, tickfont=TICK_FONT, range=moment_lims[0:2], dtick=moment_lims[-1], showline=True, showgrid=True, zeroline=True, mirror=True)
        fig.update_xaxes(title_text="Torsion (kNm)", row=2, col=3, title_font=AXIS_TITLE_FONT, tickfont=TICK_FONT, range=torsion_lims[0:2], dtick=torsion_lims[-1], showline=True, showgrid=True, zeroline=True, mirror=True)

        
        
        return data.to_dict('records'), fig
    return no_update, no_update

def plotCases(colList, typeList, cutI, cutName, cI, case, filtered_data, StepType, showLegend):
    filtered_data = filtered_data[filtered_data['StepType'] == StepType]
    fig.add_trace(go.Scatter(y=filtered_data['CutHeight'], x=filtered_data['F1'], mode='lines', name=f'{case}_{cutName}', line = dict(color =colList[cI%len(colList)], dash=typeList[cutI%len(typeList)]),showlegend=showLegend, legendgroup=case+cutName), row=1, col=1)
    fig.add_trace(go.Scatter(y=filtered_data['CutHeight'], x=filtered_data['F2'], mode='lines', name=f'{case}_{cutName}', line = dict(color =colList[cI%len(colList)], dash=typeList[cutI%len(typeList)]),showlegend=False, legendgroup=case+cutName), row=1, col=2)
    fig.add_trace(go.Scatter(y=filtered_data['CutHeight'], x=filtered_data['F3'], mode='lines', name=f'{case}_{cutName}', line = dict(color =colList[cI%len(colList)], dash=typeList[cutI%len(typeList)]),showlegend=False, legendgroup=case+cutName), row=1, col=3)
    fig.add_trace(go.Scatter(y=filtered_data['CutHeight'], x=filtered_data['M1'], mode='lines', name=f'{case}_{cutName}', line = dict(color =colList[cI%len(colList)], dash=typeList[cutI%len(typeList)]),showlegend=False, legendgroup=case+cutName), row=2, col=1)
    fig.add_trace(go.Scatter(y=filtered_data['CutHeight'], x=filtered_data['M2'], mode='lines', name=f'{case}_{cutName}', line = dict(color =colList[cI%len(colList)], dash=typeList[cutI%len(typeList)]),showlegend=False, legendgroup=case+cutName), row=2, col=2)
    fig.add_trace(go.Scatter(y=filtered_data['CutHeight'], x=filtered_data['M3'], mode='lines', name=f'{case}_{cutName}', line = dict(color =colList[cI%len(colList)], dash=typeList[cutI%len(typeList)]),showlegend=False, legendgroup=case+cutName), row=2, col=3)

if __name__ == '__main__':
    app.run_server(debug=True)
