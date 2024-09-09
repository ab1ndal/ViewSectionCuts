from utils.readFile import getData

def getCutHeight(cutName):
    try:
        height = float(cutName.split('=')[-1][:-1])
    except:
        raise IndexError('Invalid Cut Name')
    return height

def getCutGroup(cutNameList):
    cutGroups = []
    for cut in cutNameList:
        try:
            getCutHeight(cut)
            # if no exception is raised, then the cut is valid
            cutGroups.append(cut.split('=')[0][:-4])
            
        except:
            continue
    cutGroups = list(set(cutGroups))
    return cutGroups

def getCutForces(connection, cutNameList, loadCaseName):
    
    query = """
    SELECT "SectionCut", 
           "OutputCase", 
           "StepType", 
           round(CAST("F1" AS NUMERIC),0) as "F1", 
           round(CAST("F2" AS NUMERIC),0) as "F2", 
           round(CAST("F3" AS NUMERIC),0) as "F3", 
           round(CAST("M1" AS NUMERIC),0) as "M1", 
           round(CAST("M2" AS NUMERIC),0) as "M2", 
           round(CAST("M3" AS NUMERIC),0) as "M3" 
    FROM "Section Cut Forces - Analysis"
    """
    whereClauses = []
    if cutNameList:
        joinString = '"SectionCut" LIKE '
        whereClauses.append('(' + ' OR '.join([joinString + f"'{cut} - %'" for cut in cutNameList]) + ')')
    if loadCaseName:
        joinString = '"OutputCase" = '
        whereClauses.append('(' + ' OR '.join([joinString + f"'{load}'" for load in loadCaseName]) + ')')
    if whereClauses:
        query += ' WHERE ' + ' AND '.join(whereClauses)

    data = getData(connection, query=query)
    data['CutHeight'] = data['SectionCut'].apply(getCutHeight)
    data = data.sort_values(by=['CutHeight', 'OutputCase'])
    return data

