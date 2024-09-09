import pandas as pd
import sqlite3
import time
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
import psycopg2
from psycopg2 import sql

load_dotenv()

base_db_url = os.getenv('DB_URL', 'postgresql+psycopg2://myuser:password@localhost:5432/MainFile')

db_params = {
    'dbname': 'postgres',  # Default database for administrative tasks
    'user': 'myuser',
    'password': 'password',
    'host': 'localhost',
    'port': '5432'
}

def createConnection():
    conn = psycopg2.connect(**db_params)
    conn.autocommit = True
    return conn

def createTempDB(dbName):
    dropTempDB(dbName)
    conn = createConnection()
    with conn.cursor() as cur:
        cur.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(dbName)))
    print(f'Database {dbName} created')
    conn.close()
    return f'postgresql+psycopg2://myuser:password@localhost:5432/{dbName}'

def dropTempDB(dbName):
    conn = createConnection()
    with conn.cursor() as cur:
        cur.execute(sql.SQL('DROP DATABASE IF EXISTS {}').format(sql.Identifier(dbName)))
    print(f'Database {dbName} dropped')
    conn.close()


def getData(conn, **kwargs):
    tableName = kwargs.get('tableName')
    query = kwargs.get('query')

    print(query)

    if not tableName and not query:
        raise ValueError('tableName or query must be provided')
    
    if tableName:
        query = f'SELECT * FROM "{tableName}"'

    result = conn.execute(text(query))
    data = result.fetchall()
    columns = result.keys()

    df = pd.DataFrame(data, columns=columns)

    print(df.head())
    return df

def create_table_if_not_exists(connection, df, table_name):
    # Create the table if it does not exist
    columns_with_types = ', '.join([f'"{col}" TEXT' for col in df.columns])
    create_table_query = f'''
    CREATE TABLE IF NOT EXISTS "{table_name}" (
        {columns_with_types}
    )
    '''
    connection.execute(text(create_table_query))

def insert_data_bulk(connection, df, table_name):
    # Ensure the table exists
    create_table_if_not_exists(connection, df, table_name)
    
    # Convert DataFrame to a list of dictionaries
    data = df.to_dict(orient='records')
    
    # Prepare the SQL statement for bulk insert
    columns = ", ".join([f'"{col}"' for col in df.columns])
    placeholders = ", ".join([f":{col}" for col in df.columns])
    
    insert_query = f'''
    INSERT INTO "{table_name}" ({columns})
    VALUES ({placeholders})
    '''
    
    # Execute the bulk insert
    connection.execute(
        text(insert_query),
        data
    )

def connectDB(filePath, DB_URL=base_db_url, dbName = 'MainFile'):
    #baseEngine = create_engine(DB_URL, poolclass=NullPool)
    #connection = baseEngine.connect()
    try:
        tempDB_url = createTempDB(dbName)
        engine = create_engine(tempDB_url, poolclass=NullPool)
        connection = engine.connect()

        start = time.time()
        xls = pd.ExcelFile(filePath)
        totalSheets = len(xls.sheet_names)

        for i, sheet in enumerate(xls.sheet_names,1):
            print(f'Processing {sheet}')
            progressVal = int((i-0.5/totalSheets)*100)
            if progressVal < 100:
                yield {'progress': progressVal, 'message': f'Processing {i} of {totalSheets} Sheets: {sheet}...'}
            df = pd.read_excel(filePath, sheet_name=sheet, header=1).iloc[1:]
            insert_data_bulk(connection, df, sheet)
            progressVal = int((i/totalSheets)*100)
            if progressVal != 100:
                yield {'progress': progressVal, 'message': f'Processing {i} of {totalSheets} Sheets: {sheet}...'}
        connection.commit()
        end = time.time()
        print(f'Execution time: {end - start}')
        yield connection
    except Exception as e:
        print(e)
        #dropTempDB(connection, dbName)
        raise e


def OLDconnectDB(filePath, connection=None):
    #measure execution time
    start = time.time()
    if connection is None:
        connection = sqlite3.connect(':memory:', check_same_thread=False)
    xls = pd.ExcelFile(filePath)
    totalSheets = len(xls.sheet_names)
    for i, sheet in enumerate(xls.sheet_names,1):
        print(f'Processing {sheet}')
        progressVal = int((i-0.5/totalSheets)*100)
        if progressVal < 100:
            yield {'progress': progressVal, 'message': f'Processing {i} of {totalSheets} Sheets: {sheet}...'}
        df = pd.read_excel(filePath, sheet_name=sheet, header=1).iloc[1:]
        connection.execute('PRAGMA journal_mode=WAL;')
        df.to_sql(sheet, connection, index=False, if_exists='replace')
        progressVal = int((i/totalSheets)*100)
        if progressVal != 100:
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
