import os


class Telegram:
    token = os.environ.get('TELEGRAM_TOKEN')


class Mysql:
    host = os.environ.get('MYSQL_HOST')
    db = os.environ.get('MYSQL_DB')
    user = os.environ.get('MYSQL_USER')
    password = os.environ.get('MYSQL_PASSWORD')


class Openai:
    api_key = os.environ.get('OPENAI_API_KEY')
    model = os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo')


class Bot:
    username = os.environ.get('BOT_USERNAME', 'ChatGPT')


class Config:
    telegram = Telegram()
    mysql = Mysql()
    openai = Openai()
    bot = Bot()
