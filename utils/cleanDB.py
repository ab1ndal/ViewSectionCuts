def cleanDB(df):
    return df.dropna(axis=1, how='all')