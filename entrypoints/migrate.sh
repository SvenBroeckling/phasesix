#!/bin/sh

/app/.venv/bin/python manage.py migrate
# /app/.venv/bin/python manage.py clear_unused_images
/app/.venv/bin/python manage.py collectstatic --noinput
/app/.venv/bin/python manage.py compress -f

