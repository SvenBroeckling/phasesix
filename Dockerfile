FROM python:3.11-alpine

RUN apk add --no-cache postgresql-libs gettext zlib libjpeg libwebp libxml2-dev libxslt-dev glib-dev pango

ENV PYTHONUNBUFFERED 1

EXPOSE 8080

RUN mkdir /app
WORKDIR /app

COPY requirements.txt .

RUN apk add --no-cache --virtual .build-deps gcc g++ git openssh musl-dev postgresql-dev zlib-dev jpeg-dev libwebp-dev libffi-dev && \
    python -m venv venv && \
    /app/venv/bin/python -m pip install -U pip && \
    venv/bin/pip install -r requirements.txt --no-cache-dir && \
    apk --purge del .build-deps

COPY . .
RUN chmod +x entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
