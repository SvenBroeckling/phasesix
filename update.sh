#!/bin/sh

ssh sven@nimbostratus.de "cd www/urpg/www ; pg_dump urpg -U urpg | bzip2 > urpg.sql.bz2"
scp sven@nimbostratus.de:www/urpg/www/urpg.sql.bz2 .
dropdb -U urpg urpg
createdb -U urpg -T template0 -E utf8 -O urpg urpg
bunzip2 -c urpg.sql.bz2 | psql -U urpg urpg

rsync -avz sven@nimbostratus.de:www/urpg/www/media_files .
