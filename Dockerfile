# Build stage
FROM python:3.8-alpine as build

ENV CHAT_ENV="prod"

COPY requirements.txt .

RUN apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev openssl-dev \
    && python -m venv /venv \
    && /venv/bin/pip install --no-cache-dir --upgrade pip \
    && /venv/bin/pip install --no-cache-dir -r requirements.txt \
    && apk del .build-deps

# Runtime stage
FROM python:3.8-alpine

ENV CHAT_ENV="prod"

COPY --from=build /venv /venv
WORKDIR /app
COPY . .

CMD ["/venv/bin/python", "./main.py"]

