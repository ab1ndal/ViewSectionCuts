import pandas as pd
import sqlite3
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, Boolean
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError
import time


def getData(conn, **kwargs):
    tableName = kwargs.get('tableName')
    query = kwargs.get('query')

    if not tableName and not query:
        raise ValueError('tableName or query must be provided')
    
    if tableName:
        query = f'SELECT * FROM "{tableName}"'

    data = pd.read_sql(query, conn)

    return data

def connectDB(filePath, connection=None):
    #measure execution time
    start = time.time()
    if connection is None:
        connection = sqlite3.connect(':memory:', check_same_thread=False)
    xls = pd.ExcelFile(filePath)
    totalSheets = len(xls.sheet_names)
    for i, sheet in enumerate(xls.sheet_names,1):
        print(f'Processing {sheet}')
        df = pd.read_excel(filePath, sheet_name=sheet, header=1).iloc[1:]
        connection.execute('PRAGMA journal_mode=WAL;')
        df.to_sql(sheet, connection, index=False, if_exists='replace')
        progressVal = int((i/totalSheets)*100)
        if progressVal != 100:
            print(progressVal)
            yield {'progress': progressVal, 'message': f'Processing {i} of {totalSheets} Sheets: {sheet}...'}
    connection.commit()
    end = time.time()
    print(f'Execution time: {end - start}')
    yield connection


## Usage
# filePath = r'C:\\Users\\abindal\\OneDrive - Nabih Youssef & Associates\\Documents\\00_Projects\\06_The Vault\\17JuneModels\\Part 302\\Displacement Study.xlsx'
# resultFile = connectDB(filePath)
# getData(resultFile, tableName='Groups 2 - Assignments')

# query = 'SELECT * FROM "Groups 2 - Assignments"'
# getData(resultFile, query=query)
