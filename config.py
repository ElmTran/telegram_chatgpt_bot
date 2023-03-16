import os
import configparser


env = os.environ.get('CHAT_ENV', 'dev')
cfg = configparser.ConfigParser()
cfg.read(f'config/{env}.ini')
