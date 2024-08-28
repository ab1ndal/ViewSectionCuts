import dash_mantine_components as dmc
from dash import dcc, html

def createUploadComponent(idName, label, **kwargs):
    if 'description' in kwargs:
        description = kwargs['description']
    else:
        description = None
    return dmc.Grid([
                dmc.GridCol([
                    dmc.Text(f"Upload {label} File", fw=500, size = 'sm'),
                    dmc.Text(description, size = 'xs'),
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
    return dmc.GridCol([
                    dmc.MultiSelect(
                    label=f'Select the names of {label}',
                    w = 300,
                    description=f'Select {label} from the list',
                    required=True,
                    error = True,
                    id=idName,
                    data=[],
                    value=[],
                    nothingFoundMessage=f'No {label} Found',
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

    if 'defaultValue' in kwargs:
        defaultValue = kwargs['defaultValue']
    else:
        defaultValue = None

    return dmc.GridCol([
                    dmc.Select(
                    label=f'Select the name of {label}',
                    w = 300,
                    description=description,
                    required=True,
                    error = True,
                    id=idName,
                    data=values,
                    value=defaultValue,
                    nothingFoundMessage=f'No {label} Found',
                    searchable=True)
    ], span=4)

def createTextInputComponent(idName, label, **kwargs):
    if 'placeholder' in kwargs:
        placeholder = kwargs['placeholder']
    else:
        placeholder = None

    if 'value' in kwargs:
        value = kwargs['value']
    else:
        value = None

    if 'description' in kwargs:
        description = kwargs['description']
    else:
        description = None
        
    return dmc.GridCol([
                dmc.TextInput(label=label,
                        w = 300,
                        error = True,
                        id=idName,
                        description=description,
                        required=True,
                        placeholder=placeholder,
                        value=value),
            ], span=4)

def createRadioComponent(idName, **kwargs):
    values = kwargs.get('values')
    if not values:
        values = []
    
    showLabel = kwargs.get('showLabel')
    
    return dmc.GridCol([
                    dmc.RadioGroup(
                        children = dmc.Group([dmc.Radio(label=value, value=value) for value in values]),
                    label=showLabel,
                    w = 300,
                    value = values[0],
                    description = 'Select the option from the list',
                    id=idName,
                    size = 'sm',
                    mb = 2)
    ], span=4)
        
def createNumberInputComponent(labelPrefix, minValue, maxValue, stepValue, unit):
    return dmc.Grid([
            dmc.GridCol([
                dmc.NumberInput(min=-1e10, max=1e10,allowDecimal=True,decimalScale=3,thousandSeparator=",", label=f'{labelPrefix} - Minimum ({unit})', id=f'{labelPrefix.lower()}-min', w=300, value=minValue),
            ], span=4),
            dmc.GridCol([
                dmc.NumberInput(min=-1e10, max=1e10,allowDecimal=True,decimalScale=3,thousandSeparator=",", label=f'{labelPrefix} - Maximum ({unit})', id=f'{labelPrefix.lower()}-max', w=300, value=maxValue),
            ], span=4),
            dmc.GridCol([
                dmc.NumberInput(min=-1e10, max=1e10,allowDecimal=True,decimalScale=3,thousandSeparator=",", label=f'{labelPrefix} - Step Size ({unit})', id=f'{labelPrefix.lower()}-step', w=300, value=stepValue),
            ], span=4),
        ])

def createSingleNumberInputComponent(**kwargs):
    value = None
    label = None
    placeholder = None
    description = None
    if 'value' in kwargs:
        value = kwargs['value']
    if 'id' in kwargs:
        id = kwargs['id']
    if 'label' in kwargs:
        label = kwargs['label']
    if 'placeholder' in kwargs and 'value' not in kwargs:
        placeholder = kwargs['placeholder']
    if 'description' in kwargs:
        description = kwargs['description']
    return dmc.GridCol([
                dmc.NumberInput(min=-1e10, max=1e10,
                                allowDecimal=True,
                                decimalScale=3,
                                label=label, 
                                id=id, 
                                w=300, 
                                value=value,
                                placeholder=placeholder,
                                description=description),
        ], span=4)
