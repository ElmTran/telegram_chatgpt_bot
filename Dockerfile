# Build stage
FROM python:3.8-alpine as build

ENV TELEGRAM_TOKEN \
    OPENAI_API_KEY

ENV MYSQL_HOST="localhost" \
    MYSQL_PORT=3306 \
    MYSQL_DB="chatbot" \
    MYSQL_USER="root" \
    MYSQL_PASSWORD="changeme" \
    OPENAI_MODEL="gpt-3.5-turbo" \
    BOT_USERNAME="bushuohua_bot"

COPY requirements.txt .

RUN apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev openssl-dev \
    && python -m venv /venv \
    && /venv/bin/pip install --no-cache-dir --upgrade pip \
    && /venv/bin/pip install --no-cache-dir -r requirements.txt \
    && apk del .build-deps

# Runtime stage
FROM python:3.8-alpine

ENV TELEGRAM_TOKEN \
    OPENAI_API_KEY

ENV MYSQL_HOST="localhost" \
    MYSQL_PORT=3306 \
    MYSQL_DB="chatbot" \
    MYSQL_USER="root" \
    MYSQL_PASSWORD="changeme" \
    OPENAI_MODEL="gpt-3.5-turbo" \
    BOT_USERNAME="bushuohua_bot"

COPY --from=build /venv /venv
WORKDIR /app
COPY . .

CMD ["/venv/bin/python", "./main.py"]

