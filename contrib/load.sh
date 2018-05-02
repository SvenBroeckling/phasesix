#!/bin/sh

rm db.sqlite3
python manage.py migrate
python manage.py loaddata contrib/fixtures.json
python manage.py createsuperuser --username sven --email sven@tirakans-reiche.de
