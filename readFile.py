import pandas as pd
import sqlite3

def getData(connection, **kwargs):
    tableName = kwargs.get('tableName')
    query = kwargs.get('query')

    if not tableName and not query:
        raise ValueError('tableName or query must be provided')
    
    if tableName:
        query = f'SELECT * FROM "{tableName}"'
    data = pd.read_sql(query, connection)
    return data

def connectDB(filePath, conn=None):
    if conn is None:
        conn = sqlite3.connect(':memory:')
    xls = pd.ExcelFile(filePath)
    for sheet in xls.sheet_names:
        df = pd.read_excel(filePath, sheet_name=sheet, header=1).iloc[1:]
        df.to_sql(sheet, conn, index=False)
    conn.commit()
    return conn

## Usage
# filePath = r'C:\\Users\\abindal\\OneDrive - Nabih Youssef & Associates\\Documents\\00_Projects\\06_The Vault\\17JuneModels\\Part 302\\Displacement Study.xlsx'
# resultFile = connectDB(filePath)
# getData(resultFile, tableName='Groups 2 - Assignments')

# query = 'SELECT * FROM "Groups 2 - Assignments"'
# getData(resultFile, query=query)
