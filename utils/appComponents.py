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
                        multiple=False 
                    ),
                    dmc.Progress(
                        id=f'{idName}-progress',
                        value=0,
                        striped=False,
                        animated=False,
                        size='md',
                        color='blue',
                        mt = 10
                    )
                ], span=12),
            ])

def getCaseType(caseName):
    # value = 'TH' if 'MCE' in case else 'NonLin' if '1.0D' in case or 'TP' or 'TN') in case else 'RS' if 'SLE' in case else 'Lin'
    if 'MCE' in caseName:
        return 'TH'
    elif '1.0D' in caseName or 'TP' in caseName or 'TN' in caseName:
        return 'NonLin'
    elif 'SLE' in caseName:
        return 'RS'
    else:
        return 'Lin'

def getCaseID(caseName):
    if 'MCE' in caseName:
        return 'MCE-Only'
    elif '1.0D' in caseName:
        return 'D+0.5L'
    elif 'TP' in caseName:
        return 'T-Pos'
    elif 'TN' in caseName:
        return 'T-Neg'
    return caseName

def getCaseColor(caseName, colorName):
    if 'MCE' in caseName:
        return '#40c057'
    elif '1.0D' in caseName:
        return '#25262b'
    elif 'TP' in caseName:
        return '#fa5252'
    elif 'TN' in caseName:
        return '#228be6'
    return colorName

def getRoundValue(valList):

    #get the absolute max and min value in the list, then get the max of the absolute value
    #then round to nearest 1000 if the value is in the range of 1000 to 10000
    #round to nearest 10000 if the value is in the range of 10000 to 100000
    #round to nearest 100000 if the value is in the range of 100000 to 1000000
    #round to nearest 1000000 if the value is in the range of 1000000 to 10000000
    #round to nearest 10000000 if the value is in the range of 10000000 to 100000000
    #return rounded value from -value to +value
    # also determine a step size which is 1/8th of the rounded value

    maxVal = max(valList)
    minVal = min(valList)
    absMax = max(abs(maxVal), abs(minVal))
    if absMax < 10000:
        roundVal = round(absMax, -3)
        stepVal = roundVal/8
    elif absMax < 100000:
        roundVal = round(absMax, -4)
        stepVal = roundVal/8
    elif absMax < 1000000:
        roundVal = round(absMax, -5)
        stepVal = roundVal/8
    elif absMax < 10000000:
        roundVal = round(absMax, -6)
        stepVal = roundVal/8
    elif absMax < 100000000:
        roundVal = round(absMax, -7)
        stepVal = roundVal/8
    else:
        roundVal = round(absMax, -8)
        stepVal = roundVal/8
    
    return roundVal, stepVal

def createMultiSelectComponent(idName, label, **kwargs):
    if 'data' in kwargs:
        data = kwargs['data']
    else:
        data = []
    if 'value' in kwargs:
        value = kwargs['value']
    else:
        value = []

    return dmc.GridCol([
                    dmc.MultiSelect(
                    label=f'Select the names of {label}',
                    w = 300,
                    description=f'Select {label} from the list',
                    required=True,
                    id=idName,
                    data=data,
                    value=value,
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
                        id=idName,
                        description=description,
                        required=True,
                        placeholder=placeholder,
                        value=value,
                        style = {'color': 'black'},
                        className = 'custom-placeholder'),
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
