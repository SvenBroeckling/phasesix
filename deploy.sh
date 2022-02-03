#!/bin/sh

ssh sven@nimbostratus.de "cd www/urpg/www ; git pull"
ssh sven@nimbostratus.de "cd www/urpg/www ; ~/.virtualenvs/urpg/bin/pip install -U pip"
ssh sven@nimbostratus.de "cd www/urpg/www ; ~/.virtualenvs/urpg/bin/pip install -r requirements.txt"

ssh sven@nimbostratus.de "cd www/urpg/www ; ~/.virtualenvs/urpg/bin/python manage.py migrate"
ssh sven@nimbostratus.de "cd www/urpg/www ; ~/.virtualenvs/urpg/bin/python manage.py collectstatic --no-input"

ssh sven@nimbostratus.de "sudo systemctl restart urpg-ws"
ssh sven@nimbostratus.de "sudo systemctl restart urpg-http"
