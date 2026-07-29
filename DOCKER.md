# Deploy AssetFlow with Docker

AssetFlow runs as three containers: **Postgres**, **Django API (Gunicorn)**, and **React (nginx)**. nginx proxies `/api` and `/media` to the backend so the browser uses one origin.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine + Compose v2)
- Ports **80** free (or change `APP_PORT` in `.env`)

## Steps

### 1. Configure environment

From the repo root:

```bash
cp .env.example .env
```

Edit `.env` and set at least:

- `SECRET_KEY` — long random string
- `DB_PASSWORD` — strong password
- `ALLOWED_HOSTS` — your hostname(s), e.g. `localhost,127.0.0.1,your.domain.com`
- `CORS_ALLOWED_ORIGINS` / `CSRF_TRUSTED_ORIGINS` — match how users open the app, e.g. `http://localhost` or `https://your.domain.com`

Leave `VITE_API_BASE_URL` empty so the SPA calls same-origin `/api` (nginx proxies to Django).

### 2. Build and start

```bash
docker compose up --build -d
```

First boot runs migrations, collectstatic, and (if `SEED_DEMO_USERS=true`) creates demo accounts.

### 3. Open the app

- App: http://localhost (or `http://localhost:$APP_PORT`)
- Demo password: `Demo1234!`
- Accounts: `admin@assetflow.local`, `assetmanager@assetflow.local`, `manager@assetflow.local`, `employee@assetflow.local`

### 4. Useful commands

```bash
# Logs
docker compose logs -f

# Backend shell
docker compose exec backend python manage.py shell

# Stop
docker compose down

# Stop and wipe database/media volumes
docker compose down -v
```

## Architecture

| Service    | Image / build        | Role                                      |
|------------|----------------------|-------------------------------------------|
| `db`       | `postgres:16-alpine` | Database                                  |
| `backend`  | `./backend`          | Django + Gunicorn on `:8000` (internal)   |
| `frontend` | `./frontend`         | Vite build + nginx on host `:80`          |

Files:

- `docker-compose.yml` — orchestration
- `backend/Dockerfile` + `backend/scripts/entrypoint.sh`
- `frontend/Dockerfile` + `frontend/nginx.conf`
- `.env.example` — template for `.env`

## Production notes

1. Put TLS in front (Caddy, Traefik, or a cloud load balancer) and set `CORS`/`CSRF`/`ALLOWED_HOSTS` to your HTTPS URL.
2. Change all default passwords and `SECRET_KEY`.
3. Set `SEED_DEMO_USERS=false` outside demos.
4. For large media libraries, move uploads to S3/compatible storage instead of the `media_data` volume.
5. Back up the `postgres_data` volume regularly.
