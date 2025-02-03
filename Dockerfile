FROM python:3.13-alpine

ARG USER_ID=1000
ARG USER_NAME=slack_order

RUN apk add --no-cache shadow \
    && adduser -D -u $USER_ID $USER_NAME

WORKDIR /app

USER $USER_NAME

COPY --chown=$USER_NAME:$USER_NAME . .

ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python", "slack_order.py"]
