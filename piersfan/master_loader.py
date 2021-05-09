import os
import re
import logging
import datetime
import toml
import pandas as pd
import dataset as ds
from piersfan import config
from piersfan.config import Config
from piersfan.converter import Converter
from piersfan.datastore import Datastore

Description = '''
config.tomlに定義したマスターデータを SQLite3 にインポートします。
'''

_logger = logging.getLogger(__name__)


class MasterLoader:
    def __init__(self, db_name=config.ChokaDB):
        """
        SQLite3 データベースへの接続と、各モデル定義を初期化します
        """
        self.db_path = Config.get_db_path(db_name)
        self.db = ds.connect('sqlite:///{}'.format(self.db_path))
        self.target = pd.DataFrame(columns=['Target', 'Species'])

    def load_config(self, config_path=Config.get_config_path()):
        """
        設定ファイルを読み、ホームページダウンロードパラメータを登録します
        """
        config_toml = toml.load(open(config_path))

        """魚種ターゲットの読み込み"""
        if 'target' in config_toml:
            targets = config_toml['target']
            for target in targets:
                target_name = target['name']
                for species in target['species']:
                    values = {'Target': target_name, 'Species': species}
                    self.target = self.target.append(values, ignore_index=True)

        return self

    def check_config(self):
        """
        設定値のチェック
        """
        return self

    def initial_load(self):
        """
        テーブルを作成し、データフレームをロード(上書き更新)します
        """
        if len(self.target) > 0:
            self.target.to_sql("fishing_target", self.db.engine, if_exists="replace")

    def run(self):
        """
        SQLite3 から指定した期間の履歴データをCSVにエクスポートします
        """
        _logger.info("master loader")
        _logger.info(len(self.target))
        self.initial_load()
