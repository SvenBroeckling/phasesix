#!/bin/sh

. venv/bin/activate

python manage.py migrate
python manage.py collectstatic --noinput

exec gunicorn urpg.asgi:application --bind 0.0.0.0:8080 -w 7 -k uvicorn.workers.UvicornWorker
