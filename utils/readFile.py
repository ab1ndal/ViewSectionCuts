import pandas as pd
import sqlite3
import time
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
from sqlalchemy.exc import SQLAlchemyError
import psycopg2
from psycopg2 import sql

env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

db_params = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASS'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT')
}

def createConnection():
    try:
        conn = psycopg2.connect(**db_params)
        conn.autocommit = False
        return conn
    except psycopg2.Error as e:
        print(f'Error connecting to database: {e}')
        raise

def createTempDB(dbName):
    dropTempDB(dbName)
    conn = createConnection()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(dbName)))
        print(f'Database {dbName} created')
    except psycopg2.Error as e:
        print(f'Error creating database {dbName}: {e}')
        raise
    return f'postgresql+psycopg2://{db_params["user"]}:{db_params["password"]}@{db_params["host"]}:{db_params["port"]}/{dbName}'

def dropTempDB(dbName):
    conn = createConnection()
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(sql.SQL('DROP DATABASE IF EXISTS {}').format(sql.Identifier(dbName)))
    print(f'Database {dbName} dropped')

def getData(conn, **kwargs):
    tableName = kwargs.get('tableName')
    query = kwargs.get('query')
    if not tableName and not query:
        raise ValueError('tableName or query must be provided')
    if tableName:
        query = f'SELECT * FROM "{tableName}"'
    result = conn.execute(text(query))
    data = result.fetchall()
    columns = result.keys()
    df = pd.DataFrame(data, columns=columns)
    return df

def create_table_if_not_exists(connection, df, table_name):
    columns_with_types = ', '.join([f'"{col}" TEXT' for col in df.columns])
    create_table_query = f'''
    CREATE TABLE IF NOT EXISTS "{table_name}" (
        {columns_with_types}
    )
    '''
    try:
        connection.execute(text(create_table_query))
    except SQLAlchemyError as e:
        print(f"Error occurred while creating table {table_name}: {e}")
        raise

def insert_data_bulk(connection, df, table_name):
    create_table_if_not_exists(connection, df, table_name)
    connection.autoCommit = False
    try:        
        df.to_sql(
            name=table_name, 
            con=connection, 
            if_exists='append', 
            index=False,
            method='multi')
    except SQLAlchemyError as e:
        print(f"Error occurred while inserting data into {table_name}: {e}")
        raise

def connectDB(filePath, dbName = 'MainFile'):
    tempDB_url = createTempDB(dbName)
    engine = create_engine(tempDB_url, poolclass=NullPool)
    connection = engine.connect()
    try:
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
        yield connection
    except Exception as e:
        raise
