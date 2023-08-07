## Phase Six Pen'n"Paper Roleplay Platform

This repository contains the source code which runs the RPG Sites [Phase Six](https://phasesix.org/) and [Realms of Tirakan](https://tirakans-reiche.de/). This is a [Django](https://www.djangoproject.com/) project.

The code is licensed under the [GNU GPLv3](https://www.gnu.org/licenses/gpl-3.0.en.html) as stated in the LICENSE.txt file. However, the contents of both phasesix.org and tirakans-reiche.de (game elements, rules, images, etc.) are licensed under the [CC-BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).

This source code comes with a minimal example set of demo data, which can be inserted into a database to get started.

### Getting Started - Docker Compose

To run the project in a docker compose environment, all you need is an installed [Docker engine](https://www.docker.com/) or Docker Desktop, and the docker-compose package.

```shell
$ docker-compose up
$ docker-compose exec web venv/bin/python manage.py loaddata demo_data.json
```

### Getting Started - Native setup

Alternatively, you can install the needed setup locally on your machine without docker.

You need a Linux (WSL2 works too), macOS (untested) or Windows (untested) machine to run this project. There are some prerequisites used by this django project.

#### Redis

Phase Six relies on a locally [redis](https://redis.io/) server. The installation depends on your system. For linux, use your package manager (i.e. `apt install redis-server`). On macOS, use Homebrew to `brew install redis`.

#### Python and virtualenv

The supported python versions are 3.8-3.11. A system-wide installed python interpreter is fine, but you want to create a virtualenv. This can be done with:

```shell
$ python -m venv venv
```

The second parameter is the venv folder, which *should not* be in the project directory. The virtualenv can be activated for a single shell with `source venv/bin/activate`. Every python/pip call after that will use the virtualenv.

#### Requirements

The requirements are listed in the file `requirements.txt`. They can be installed with pip:

```shell
(venv) $ pip install -r requirements.txt
```

These will be installed into the virtualenv, so that nothing collides with your system-wide python.

#### Environment, Database, Superuser

This project uses a `.env` file to set basic settings (like mail server and database). There is an example `.env.example`, which can be copied to the name `.env` in the project folder. Adjust the settings for your needs. The default settings should run fine for a local setup with sqlite3 database.

The database file `db.sqlite3` will be created in the project folder. If you use a postgres database, you have to create the database and an owner before running migrations.

To create the database tables, run the django migrations:

```shell
(venv) $ python manage.py migrate
```

This will not create a superuser for the site, so you need to use the django management command to do this:

```shell
(venv) $ python manage.py createsuperuser
```

#### Demo data

After this, a simple setup without any data should be ready to run. Although phase six needs some prerequisites present in the database. A simple set of demo data containing some extensions, weapons, armour and skills can be inserted from a json file.

```shell
(venv) $ python manage.py loaddata demo_data.json
```

#### Running the local server

To run the local development server, just run the following management command:

```shell
(venv) $ python manage.py runserver
```

A single threaded server will be available at http://localhost:8000. Note that this server is not suitable for production deployment. There are many ways to [deploy a django project](https://docs.djangoproject.com/en/4.2/howto/deployment/).

