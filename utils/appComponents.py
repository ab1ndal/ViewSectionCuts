import dash_mantine_components as dmc
from dash import dcc, html

def createUploadComponent(idName, label, **kwargs):
    if 'description' in kwargs:
        description = kwargs['description']
    else:
        description = None
    return dmc.Grid([
                dmc.Col([
                    dmc.Text(f"Upload {label} File", fw=500, size = 'sm'),
                    dmc.Text(description, size = 'xs', color='dimmed'),
                    dcc.Upload(
                        id=idName,
                        children=html.Div([
                            f'Drag and Drop the {label} File or ',
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
            ])

def createMultiSelectComponent(idName, label):
    return dmc.Col([
                    dmc.MultiSelect(
                    label=f'Select the names of {label}',
                    w = 300,
                    description=f'Select {label} from the list',
                    required=True,
                    error = True,
                    id=idName,
                    data=[],
                    nothingFound=f'No {label} Found',
                    searchable=True)
    ], span=4)

def createSelectComponent(idName, label, **kwargs):
    values = kwargs.get('values')
    if not values:
        values = []
    if 'description' in kwargs:
        description = kwargs['description']
    else:
        description = f'Select {label} from the list'
    return dmc.Col([
                    dmc.Select(
                    label=f'Select the name of {label}',
                    w = 300,
                    description=description,
                    required=True,
                    error = True,
                    id=idName,
                    data=values,
                    nothingFound=f'No {label} Found',
                    searchable=True)
    ], span=4)

def createTextInputComponent(idName, label, description, **kwargs):
    if 'placeholder' in kwargs:
        placeholder = kwargs['placeholder']
    else:
        placeholder = None

    if 'value' in kwargs:
        value = kwargs['value']
    else:
        value = None
        
    return dmc.Col([
                dmc.TextInput(label=label,
                        w = 300,
                        error = True,
                        id=idName,
                        description=description,
                        required=True,
                        placeholder=placeholder,
                        value=value),
            ], span=4)
        
def createNumberInputComponent(labelPrefix, minValue, maxValue, stepValue, unit):
    return dmc.Grid([
            dmc.Col([
                dmc.NumberInput(min=-1e8, max=1e8,precision=3,label=f'{labelPrefix} - Minimum ({unit})', id=f'{labelPrefix.lower()}-min', w=300, value=minValue),
            ], span=4),
            dmc.Col([
                dmc.NumberInput(min=-1e8, max=1e8,precision=3,label=f'{labelPrefix} - Maximum ({unit})', id=f'{labelPrefix.lower()}-max', w=300, value=maxValue),
            ], span=4),
            dmc.Col([
                dmc.NumberInput(min=-1e8, max=1e8,precision=3,label=f'{labelPrefix} - Step Size ({unit})', id=f'{labelPrefix.lower()}-step', w=300, value=stepValue),
            ], span=4),
        ])
