from readFile import getData

def getCutHeight(cutName):
    try:
        height = float(cutName.split('=')[-1][:-1])
    except:
        raise IndexError('Invalid Cut Name')
    return height

def getCutForces(conn, cutNameList, loadCaseName):
    query = 'SELECT SectionCut, OutputCase, StepType, round(F1,0) as F1, round(F2,0) as F2, round(F3,0) as F3, round(M1,0) as M1, round(M2,0) as M2, round(M3,0) as M3 FROM "Section Cut Forces - Analysis"'
    whereClauses = []
    if cutNameList:
        joinString = 'SectionCut LIKE '
        whereClauses.append(f"({' OR '.join([joinString + f'\'%{cut}%\'' for cut in cutNameList])})")
    if loadCaseName:
        joinString = 'OutputCase LIKE '
        whereClauses.append(f"({' OR '.join([joinString + f'\'%{load}%\'' for load in loadCaseName])})")
    if whereClauses:
        query += ' WHERE ' + ' AND '.join(whereClauses)

    data = getData(conn, query=query)
    data['CutHeight'] = data['SectionCut'].apply(getCutHeight)
    data = data.sort_values(by=['CutHeight', 'OutputCase'])
    return data

