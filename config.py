import os


class Telegram:
    token = os.environ.get('TELEGRAM_TOKEN')


class Mysql:
    host = os.environ.get('MYSQL_HOST')
    db = os.environ.get('MYSQL_DB')
    port = os.environ.get('MYSQL_PORT')
    user = os.environ.get('MYSQL_USER')
    password = os.environ.get('MYSQL_PASSWORD')


class Openai:
    api_key = os.environ.get('OPENAI_API_KEY')
    model = os.environ.get('OPENAI_MODEL')


class Bot:
    username = os.environ.get('BOT_USERNAME')


class Config:
    telegram = Telegram()
    mysql = Mysql()
    openai = Openai()
    bot = Bot()
