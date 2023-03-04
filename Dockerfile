FROM python:3.8-slim-buster
ENV TELEGRAM_TOKEN \
    OPENAI_API_KEY

ENV MYSQL_HOST="localhost" \
    MYSQL_PORT=3306 \
    MYSQL_DB="chatbot" \
    MYSQL_USER="root" \
    MYSQL_PASSWORD="changeme" \
    OPENAI_MODEL="gpt-3.5-turbo" \
    BOT_USERNAME="bushuohua_bot"

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "./main.py"]
