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
from decimal import Decimal
import logging
import tempfile

env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

log_dir = tempfile.gettempdir()
log_file = os.path.join(log_dir, 'app.log')
# Set up basic logging configuration
log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler(log_file)  # File output, can be accessed via SSH on Render if needed
    ]
)



db_params = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASS'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT')
}

def convert_decimals_to_floats(df):
    for col in df.select_dtypes(include=[object]):  # Iterate over object columns
        df[col] = df[col].apply(lambda x: float(x) if isinstance(x, Decimal) else x)
    return df

def createConnection():
    try:
        logging.info('Connecting to database...')
        logging.info(f'DB Params: {db_params}')
        conn = psycopg2.connect(**db_params)
        conn.autocommit = False
        logging.info('Connected to database')
        return conn
    except psycopg2.Error as e:
        logging.error(f'Error connecting to database: {e}')
        raise

def createTempDB(dbName):
    dropTempDB(dbName)
    conn = createConnection()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(dbName)))
        logging.info(f'Database {dbName} created')
    except psycopg2.Error as e:
        logging.error(f'Error creating database {dbName}: {e}')
        raise
    return f'postgresql+psycopg2://{db_params["user"]}:{db_params["password"]}@{db_params["host"]}:{db_params["port"]}/{dbName}'

def dropTempDB(dbName):
    conn = createConnection()
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(
                sql.SQL(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = %s AND pid <> pg_backend_pid();"
                ),
                [dbName]
            )
        cur.execute(sql.SQL('DROP DATABASE IF EXISTS {}').format(sql.Identifier(dbName)))
    logging.info(f'Database {dbName} dropped')

def getData(conn, **kwargs):
    tableName = kwargs.get('tableName')
    query = kwargs.get('query')
    if not tableName and not query:
        logging.error('tableName or query must be provided')
        raise ValueError('tableName or query must be provided')
    if tableName:
        query = f'SELECT * FROM "{tableName}"'
    result = conn.execute(text(query))
    data = result.fetchall()
    columns = result.keys()
    df = pd.DataFrame(data, columns=columns)
    logging.info(f'Fetched data from {tableName}')
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
        logging.error(f"Error occurred while creating table {table_name}: {e}")
        raise

def insert_data_bulk(connection, df, table_name):
    create_table_if_not_exists(connection, df, table_name)
    df = convert_decimals_to_floats(df)
    connection.autoCommit = False
    try:        
        df.to_sql(
            name=table_name, 
            con=connection, 
            if_exists='append', 
            index=False,
            method='multi')
    except SQLAlchemyError as e:
        logging.error(f"Error occurred while inserting data into {table_name}: {e}")
        raise

def getConnection(file, dBName = 'MainFile'):
        data = connectDB(file, dBName)
        # Iterate through the generator to capture progress updates
        for update in data:
            if isinstance(update, dict) and 'progress' in update:
                print(update['message'])  # Handle progress reporting
            else:
                conn = update  # The connection will be yielded last
                break
        return conn

def connectDB(filePath, dbName = 'MainFile'):
    tempDB_url = createTempDB(dbName)
    engine = create_engine(tempDB_url, poolclass=NullPool)
    connection = engine.connect()
    try:
        xls = pd.ExcelFile(filePath)
        totalSheets = len(xls.sheet_names)
        for i, sheet in enumerate(xls.sheet_names,1):
            logging.info(f'Processing {sheet}')
            progressVal = int(((i-0.5)/totalSheets)*100)
            logging.info(f'Progress: {progressVal}')
            if progressVal < 100:
                yield {'progress': progressVal, 'message': f'Processing {i} of {totalSheets} Sheets: {sheet}...'}
            df = pd.read_excel(filePath, sheet_name=sheet, header=1).iloc[1:]
            insert_data_bulk(connection, df, sheet)
            progressVal = int(((i)/totalSheets)*100)
            if progressVal != 100:
                yield {'progress': progressVal, 'message': f'Finished Processing {i} of {totalSheets} Sheets: {sheet}...'}
        yield connection
    except Exception as e:
        logging.error(f'Error occurred while connecting to DB: {e}')
        raise
