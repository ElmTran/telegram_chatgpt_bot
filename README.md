# bushuohua

A telegram bot using gpt-3.5-turbo model.   

It's a learning project. Kindly don't use it for any commercial purpose.

Thanks for your star and fork.

## Usage

1. Create a telegram bot and get the token.

2. Clone this repo and install dependencies.

    ```bash
    git clone https://github.com/ElmTran/telegram_chatgpt_bot.git

    cd telegram_chatgpt_bot

    pip install -r requirements.txt
    ```

3. Set your config in `config.py`.

4. Run the bot.

    ```bash
    python main.py
    ```

## Docker Usage

1. Create a telegram bot and get the token.

2. Clone this repo and build the docker image.

    ```bash

    git clone https://github.com/ElmTran/telegram_chatgpt_bot.

    cd telegram_chatgpt_bot

    docker build -t telegram_chatgpt_bot .
    ```

3. Set your config in `config.py`.

4. Run the bot.

    ```bash

    docker run -d --name telegram_chatgpt_bot telegram_chatgpt_bot
    ```

5. A template docker-compose.yml is provided. You can use it to deploy the bot.

    ```yaml
    version: '3'
    services:
        chatbot:
            image: elmtran/telegram_chatgpt_bot:latest
            environment:
                - TELEGRAM_TOKEN="token"
                - MYSQL_HOST="localhost"
                - MYSQL_PORT=3306
                - MYSQL_DB="dbname"
                - MYSQL_USER="username"
                - MYSQL_PASSWORD="password"
                - OPENAI_API_KEY="api_key"
                - BOT_USERNAME="bot_username"
    ```


## Built With

* [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)

* [openai](https://platform.openai.com/)

* [sqlalchemy](https://www.sqlalchemy.org/)

## License

Apache License 2.0
