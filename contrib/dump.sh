#!/bin/sh

python manage.py dumpdata world rules characters > contrib/fixtures.json
