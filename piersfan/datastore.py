import os
import logging
import pandas as pd
import dataset as ds
from piersfan import config
from piersfan.config import Config

Description = '''
SQLite3を用いて釣果情報を管理します。
釣りビジョン釣果情報ホームページから釣果を取得した、csv データをインポートします。
'''


class Table:
    def __init__(self, table_name, index_columns, csv):
        self.table_name = table_name
        self.index_columns = index_columns
        self.csv = csv


class Datastore:
    def __init__(self, db_name=config.ChokaDB):
        db = ds.connect('sqlite:///{}/{}'.format(config.DataDir, db_name))
        self.db = db
        self.db_path = Config.get_data_path(db_name)
        self.tables = [
            Table('fishing_results', ['Date', 'Point', 'Species'], 'choka.csv'),
            Table('fishing_comments', ['Date', 'Point'], 'comment.csv'),
            Table('fishing_newslines', ['Date', 'Time', 'Point'], 'newsline.csv'),
        ]
        self.load_counts = dict()
        logging.getLogger(__name__).info("database created")

    def reset_load_file(self, filename):
        load_path = Config.get_data_path(filename)
        if os.path.exists(load_path):
            os.remove(load_path)
        self.load_counts[filename] = 0

    def reset_load_files(self):
        for table in self.tables:
            self.reset_load_file(table.csv)
        return self

    def reset_database(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        return self

    def create_index(self, table_name, index_columns):
        self.db.create_table(table_name).create_index(index_columns)

    def create_indexes(self):
        for table in self.tables:
            self.create_index(table.table_name, table.index_columns)

    def initial_load(self, csv, table_name):
        results = pd.read_csv(Config.get_data_path(csv), index_col=0)
        print(results.columns)
        results.to_sql(table_name, self.db.engine, if_exists="replace")
        self.load_counts[csv] = len(results.index)

    def initial_loads(self):
        self.reset_database()
        for table in self.tables:
            self.initial_load(table.csv, table.table_name)

        logging.getLogger(__name__).info("loaded")
        self.create_indexes()

    def upsert_row(self, table_name, index_columns, values):
        table = self.db[table_name]
        keys = dict()
        for index_column in index_columns:
            keys[index_column] = values[index_column]
        if table.find_one(**keys):
            table.update(values, index_columns)
        else:
            table.insert(values)

    def append_load(self, csv, table_name, index_columns):
        results = pd.read_csv(Config.get_data_path(csv), index_col=0)
        for result in results.to_dict(orient='records'):
            self.upsert_row(table_name, index_columns, result)
        self.load_counts[csv] = len(results.index)
        return self

    def append_loads(self):
        for table in self.tables:
            self.append_load(table.csv, table.table_name, table.index_columns)
        return self

    def csv_import(self):
        if os.path.exists(self.db_path):
            self.append_loads()
        else:
            self.initial_loads()
        return self
