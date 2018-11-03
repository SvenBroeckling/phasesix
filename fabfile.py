import json
import os

from fabric.api import local, run, env, get
from fabric.context_managers import settings, cd, prefix
from contextlib import contextmanager as _contextmanager


project = 'urpg'
db_user = 'urpg'
db_name = 'urpg'

env.hosts = ['sven@nimbostratus.de']  # master
env.cwd = '~/www/urpg/www'
env.forward_agent = True
env.activate = '. ~/.virtualenvs/urpg/bin/activate'


@_contextmanager
def virtualenv():
    with cd(env.cwd):
        with prefix(env.activate):
            yield


def dump_database():
    run("pg_dump %s -U %s | bzip2 > %s.sql.bz2" % (db_name, db_user, project))


def load_database():
    get('/home/sven/www/urpg/www/%s.sql.bz2' % project, '.')
    local('dropdb -U %s %s' % (db_user, db_name))
    local("createdb -U %s -T template0 -E utf8 -O %s %s" % (db_user,
                                                            db_user,
                                                            db_name))
    local("bunzip2 -c %s.sql.bz2 | psql -U %s %s" % (project, db_user, db_name))


def fetch_media():
    local('rsync -avz %s:%s/media_files .' % (env.hosts[0], env.cwd))


def update():
    dump_database()
    load_database()
    fetch_media()


def deploy():
    with virtualenv():
        run('git pull')
        run('pip install -r requirements.txt')
        run('./manage.py migrate')
        run('./manage.py collectstatic --no-input')
        run('sudo systemctl restart urpg')

