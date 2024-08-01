import pandas as pd
import sqlite3
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, Boolean
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError


def getData(conn, **kwargs):
    tableName = kwargs.get('tableName')
    query = kwargs.get('query')

    # print(engine)
    # inspector = inspect(engine)
    # tables = inspector.get_table_names()
    # print("Tables in the database after transfer:")
    # for table in tables:
    #     print(table)

    if not tableName and not query:
        raise ValueError('tableName or query must be provided')
    
    if tableName:
        query = f'SELECT * FROM "{tableName}"'

    # with engine.connect() as conn:
    data = pd.read_sql(query, conn)

    return data

def connectDB(filePath, connection=None):
    if connection is None:
        connection = sqlite3.connect(':memory:', check_same_thread=False)
    xls = pd.ExcelFile(filePath)
    for sheet in xls.sheet_names:
        df = pd.read_excel(filePath, sheet_name=sheet, header=1).iloc[1:]
        df.to_sql(sheet, connection, index=False)
    connection.commit()
    return connection

# def connectDB(filePath, connection_str='sqlite:///:memory:', engine=None):
#     if engine is None:
#         engine = create_engine(connection_str, echo=False)
    
#     metadata = MetaData()
    
#     xls = pd.ExcelFile(filePath)
#     for sheet in xls.sheet_names:
#         df = pd.read_excel(filePath, sheet_name=sheet, header=1).iloc[1:]
        
#         columns = [Column(col, mapType(dtype)) for col, dtype in df.dtypes.items()]
#         table = Table(sheet, metadata, *columns, extend_existing=True)
    
#     # Create all tables in the database
#     metadata.create_all(engine)
    
#     for sheet in xls.sheet_names:
#         df = pd.read_excel(filePath, sheet_name=sheet, header=1).iloc[1:]
#         table = Table(sheet, metadata, autoload_with=engine)
        
#         data = df.to_dict(orient='records')
        
#         with engine.connect() as conn:
#             try:
#                 conn.execute(table.insert(), data)
#             except SQLAlchemyError as e:
#                 print(f"{e}: Error inserting data into {sheet}")

#     print(engine)
#     inspector = inspect(engine)
#     tables = inspector.get_table_names()
#     print("Tables in the database after transfer:")
#     for table in tables:
#         print(table)
    
#     return engine

# def mapType(dtype):
#     if pd.api.types.is_integer_dtype(dtype):
#         return Integer
#     elif pd.api.types.is_float_dtype(dtype):
#         return Float
#     elif pd.api.types.is_bool_dtype(dtype):
#         return Boolean
#     else:
#         return String

## Usage
# filePath = r'C:\\Users\\abindal\\OneDrive - Nabih Youssef & Associates\\Documents\\00_Projects\\06_The Vault\\17JuneModels\\Part 302\\Displacement Study.xlsx'
# resultFile = connectDB(filePath)
# getData(resultFile, tableName='Groups 2 - Assignments')

# query = 'SELECT * FROM "Groups 2 - Assignments"'
# getData(resultFile, query=query)
