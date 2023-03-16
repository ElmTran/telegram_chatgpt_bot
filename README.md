# Telegram ChatGPT Bot

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

3. Copy `config/prod.template` to `config/prod.ini` and fill in the values.

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

    docker build -t chatbot .
    ```

3. Run the docker image.

    ```bash
    docker run -d --name chatbot -v /path/to/prod.ini:/app/config/prod.ini chatbot
    ```


4. A template docker-compose.yml is provided. You can use it to deploy the bot.

    ```yaml
    version: '3'
    services:
        chatbot:
            image: elmtran/chatbot:latest
            environment:
                - CHATBOT_ENV=prod
            volumes:
                - /path/to/prod.ini:/app/config/prod.ini
    ```

## Built With

* [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)

* [openai](https://platform.openai.com/)

* [sqlalchemy](https://www.sqlalchemy.org/)

## License

Apache License 2.0
