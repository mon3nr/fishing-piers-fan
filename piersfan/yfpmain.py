"""
横浜フィッシングピアースの釣果情報を取得する。

Parametrs
---------
-c config_paths : str[]
    コンフィグファイルパスを指定します。
-m month : int
    何カ月前のからの釣果情報ホームページをダウンロードするかを指定します。
-i init : bool
    True の場合データベースをリセットします。
"""

import logging
import argparse
from piersfan import config
from piersfan.config import Config
from piersfan.downloader import Download
from piersfan.parser import Parser
from piersfan.datastore import Datastore
from piersfan.exporter import Exporter
from piersfan.master_loader import MasterLoader


Description='''
横浜フィッシングピアースの釣果情報を取得する。
'''


_logger = logging.getLogger(__name__)

class YFPFan():

    def set_envoronment(self, args):
        """
        環境変数の初期化。以下のコードで初期化する
        """
        self.config_path = args.config
        self.month = args.month
        self.page = args.page
        self.init = args.init
        self.keep = args.keep
        self.log_enable = args.log
        self.show = args.show
        self.export = args.export
        self.time = args.time
        self.loadmaster = args.loadmaster

    def parser(self):
        """
        コマンド実行オプションの解析
        """
        parser = argparse.ArgumentParser(description=Description)
        parser.add_argument("-c", "--config", type = str, 
                            default = Config.get_config_path(), 
                            help = "<path>\\config.toml")
        parser.add_argument("-m", "--month", type = int, default = 0, 
                            help = "last n month before downloading")
        parser.add_argument("-p", "--page", type = int, default = config.MaxPage, 
                            help = "max number of pages to visit the homepage")
        parser.add_argument("-i", "--init", action="store_true", 
                            help = "initialize database")
        parser.add_argument("-k", "--keep", action="store_true", 
                            help = "keep old download files")
        parser.add_argument("-l", "--log", action="store_true", 
                            help = "write log to file")
        parser.add_argument("-s", "--show", action="store_true", 
                            help = "show config parameter")
        parser.add_argument("-e", "--export", action="store_true",
                            help = "export csv data")
        parser.add_argument("--loadmaster", action="store_true",
                            help = "import master data")
        parser.add_argument("-t", "--time", type = str,
                            default="1day",
                            help = "time period to export")
        return parser.parse_args()

    def main(self):
        """
        メイン処理。コマンド引数別に処理する
        """
        args = self.parser()
        self.set_envoronment(args)
        log_path = None
        if self.log_enable:
            log_path = Config.get_ap_log_path()
        logging.basicConfig(
            filename=log_path,
            level=getattr(logging, 'INFO'),
            format='%(asctime)s [%(levelname)s] %(module)s %(message)s',
            datefmt='%Y/%m/%d %H:%M:%S',
        )
        if self.show:
            Config.show_config()
            return

        elif self.export:
            Exporter().run(self.time)

        elif self.loadmaster:
            loader = MasterLoader().load_config()
            if loader:
                loader.run()

        elif self.init:
            Datastore().reset_database()
            MasterLoader().load_config().run()
            Download().reset_download()
            return

        else:
            downloader = Download(self.page).load_config(self.config_path).check_config()
            if downloader:
                downloader.run(self.month, self.keep)
                Parser().run()
                Datastore().csv_import()
            return

if __name__ == '__main__':
    YFPFan().main()
