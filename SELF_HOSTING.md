# Self-Hosting Guide — Phase Six

Phase Six is a Django-based tabletop RPG platform. This guide covers everything you need to run it yourself, including a few bugs in the default configuration that must be fixed before the stack will work correctly.

---

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- A domain name (optional for local use)
- An SMTP email service (required for user registration)
- An OpenAI API key (optional — only needed for AI-assisted features)

---

## Known Issues to Fix Before Starting

There are several bugs in the default configuration that will prevent a working deployment. Fix these before doing anything else.

### 1. Port mismatch in `docker-compose.yml` (critical)

The `Dockerfile` starts Hypercorn on port **4444**, but `docker-compose.yml` maps `8000:8080`. Port `8080` is never used, so the web service will be unreachable.

**Fix** — edit `docker-compose.yml` and change the port mapping:

```yaml
# Change this:
ports:
  - "8000:8080"

# To this:
ports:
  - "8000:4444"
```

### 2. Migrations are never run on startup (critical)

`entrypoints/migrate.sh` (which runs migrations, collects static files, and compresses assets) is copied into the container but the `CMD` in the `Dockerfile` skips straight to starting Hypercorn. The database schema will never be created.

**Fix** — edit the `Dockerfile` and replace the `CMD` line:

```dockerfile
# Change this:
CMD ["/app/.venv/bin/hypercorn", "-w", "5", "-b", "0.0.0.0:4444", "phasesix.asgi:application"]

# To this:
CMD ["/bin/sh", "-c", "/app/migrate.sh && /app/.venv/bin/hypercorn -w 5 -b 0.0.0.0:4444 phasesix.asgi:application"]
```

### 3. No healthchecks on dependent services

`docker-compose.yml` uses `depends_on` but does not wait for Postgres and Redis to be *ready* before starting the web container. On first boot this causes a race condition where the app starts before the database accepts connections.

**Fix** — add healthchecks to `docker-compose.yml`:

```yaml
services:
  redis:
    image: redis
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  db:
    image: postgres
    volumes:
      - postgres-data:/var/lib/postgres/data
    environment:
      - POSTGRES_DB=postgres
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres        # Change this
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 10

  web:
    build: .
    volumes:
      - media-files:/app/media_files
      - static-files:/app/static_files
    ports:
      - "8000:4444"                        # Fixed port
    env_file:
      - .env.docker
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
```

---

## Step-by-Step Setup

### 1. Clone the repository

```bash
git clone <repo-url>
cd phasesix
```

### 2. Configure your environment

Copy `.env.docker` and update every value that says "example" or "postgres":

```bash
cp .env.docker .env.docker.local
```

Then edit `.env.docker.local` (or edit `.env.docker` directly):

| Variable | Required | Notes |
|---|---|---|
| `SECRET_KEY` | Yes | Generate with `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `DEBUG` | Yes | Must be `False` in production |
| `ALLOWED_HOSTS` | Yes | Comma-separated list of your domains and IPs |
| `BASE_URL` | Yes | Full URL of your site, e.g. `https://example.com` |
| `DATABASE_PASSWORD` | Yes | Change from the default `postgres` |
| `EMAIL_HOST` | Yes | SMTP server for user registration emails |
| `EMAIL_USER` | Yes | SMTP login username |
| `EMAIL_PASSWORD` | Yes | SMTP login password |
| `REDIS_HOST` | Yes | `redis` when using Docker Compose |
| `OPENAI_API_KEY` | No | Only needed for AI translation/generation features |

**Minimum working `.env.docker` for local use:**

```env
DEBUG=False
DEBUG_TOOLBAR=False
ALLOWED_HOSTS=localhost,127.0.0.1
BASE_URL=http://localhost:8000
DATABASE_ENGINE=django.db.backends.postgresql_psycopg2
DATABASE_HOST=db
DATABASE_NAME=postgres
DATABASE_USER=postgres
DATABASE_PASSWORD=change_me_now
DATABASE_PORT=5432
EMAIL_HOST=smtp.example.com
EMAIL_USER=user@example.com
EMAIL_PASSWORD=your_email_password
EMAIL_PORT=587
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=noreply@example.com
REDIS_HOST=redis
REDIS_PORT=6379
SECRET_KEY=generate_a_real_secret_key_here
STATIC_ROOT_RELATIVE=static_files
STATIC_URL=/static/
MEDIA_ROOT_RELATIVE=media_files
MEDIA_URL=/media/
```

Also update the `POSTGRES_PASSWORD` in `docker-compose.yml` to match `DATABASE_PASSWORD`.

### 3. Apply the fixes above

Make the three changes described in the **Known Issues** section:
- Fix the port mapping in `docker-compose.yml`
- Add healthchecks to `docker-compose.yml`
- Fix the `CMD` in `Dockerfile` to run migrations on startup

### 4. Build and start the stack

```bash
docker compose up --build -d
```

The first build takes several minutes. On first startup the web container will automatically run migrations, collect static files, and compress assets before accepting connections.

### 5. Load demo data

The app needs some baseline data (extensions, weapons, skills) to function. Once the containers are running:

```bash
docker compose exec web python manage.py loaddata demo_data.json
```

### 6. Create an admin user

```bash
docker compose exec web python manage.py createsuperuser
```

### 7. Access the site

- Site: http://localhost:8000
- Admin panel: http://localhost:8000/admin

---

## Production Checklist

Before exposing this to the internet:

- [ ] `DEBUG=False` in your env file
- [ ] `SECRET_KEY` is a long, randomly generated value — never the example key
- [ ] Database password changed from `postgres`
- [ ] `ALLOWED_HOSTS` contains only your real domains
- [ ] HTTPS configured via a reverse proxy (Nginx, Caddy, Traefik)
- [ ] Email delivery tested (user registration requires working email)
- [ ] Media and database volumes are backed up regularly

### Recommended: Reverse proxy with HTTPS

The Docker stack does not handle TLS. Put Nginx, Caddy, or Traefik in front and proxy to `localhost:8000`. Example Nginx block:

```nginx
server {
    listen 443 ssl;
    server_name example.com;

    ssl_certificate     /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    location /static/ {
        alias /path/to/static-files/;
    }

    location /media/ {
        alias /path/to/media-files/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        # WebSocket support (required for live campaign features)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## Services Overview

| Service | Purpose | Required? |
|---|---|---|
| PostgreSQL | Primary database | Yes (production) |
| Redis | WebSockets, caching, sessions | Yes |
| SMTP | User registration, notifications | Yes |
| OpenAI API | AI-generated names, translations | No |

SQLite3 works for local development (leave `DATABASE_ENGINE` unset in the `.env`), but PostgreSQL is required for any production use.

---

## Common Operations

**View logs:**
```bash
docker compose logs -f web
```

**Run a management command:**
```bash
docker compose exec web python manage.py <command>
```

**Run migrations after a code update:**
```bash
docker compose exec web python manage.py migrate
```

**Rebuild after code changes:**
```bash
docker compose up --build -d
```

**Restart the web container only:**
```bash
docker compose restart web
```

---

## Troubleshooting

**Site returns 502 / connection refused**
Check that the port fix was applied (`4444` not `8080` in `docker-compose.yml`) and the web container is running: `docker compose ps`.

**Database connection errors on startup**
The healthcheck fix in step 3 prevents this. If you haven't applied it, the web container starts before Postgres is ready. Run `docker compose restart web` once the db container is healthy.

**Static files missing (CSS/JS not loading)**
`collectstatic` and `compress` are run automatically via `migrate.sh` on startup. If you skipped the `CMD` fix, run them manually:
```bash
docker compose exec web python manage.py collectstatic --noinput
docker compose exec web python manage.py compress -f
```

**User registration emails not arriving**
Verify your SMTP settings in the env file. Test with:
```bash
docker compose exec web python manage.py shell -c "from django.core.mail import send_mail; send_mail('test', 'body', 'from@example.com', ['to@example.com'])"
```

**WebSocket / live campaign features not working**
Redis must be running and reachable. Check: `docker compose exec web python -c "import redis; redis.Redis(host='redis').ping()"`. Also ensure your reverse proxy passes `Upgrade` and `Connection` headers (see Nginx config above).

**`demo_data.json` not found**
This file may not be included in all distributions of the repo. The app will run without it, but will start with an empty database. Create content via the admin panel at `/admin`.
