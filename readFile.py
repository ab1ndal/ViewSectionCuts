import pandas as pd
import sqlite3

def getData(connection, **kwargs):
    tableName = kwargs.get('tableName')
    query = kwargs.get('query')

    if not tableName and not query:
        raise ValueError('tableName or query must be provided')
    
    if tableName:
        query = f'SELECT * FROM "{tableName}"'
    print("Applying the query")
    data = pd.read_sql(query, connection)
    print("Query Applied")
    return data

def connectDB(filePath, connection=None):
    if connection is None:
        connection = sqlite3.connect(':memory:')
    xls = pd.ExcelFile(filePath)
    for sheet in xls.sheet_names:
        df = pd.read_excel(filePath, sheet_name=sheet, header=1).iloc[1:]
        df.to_sql(sheet, connection, index=False)
    connection.commit()
    return connection

## Usage
# filePath = r'C:\\Users\\abindal\\OneDrive - Nabih Youssef & Associates\\Documents\\00_Projects\\06_The Vault\\17JuneModels\\Part 302\\Displacement Study.xlsx'
# resultFile = connectDB(filePath)
# getData(resultFile, tableName='Groups 2 - Assignments')

# query = 'SELECT * FROM "Groups 2 - Assignments"'
# getData(resultFile, query=query)
