# Hosting AssetFlow (including GitHub Pages)

For **Docker** (recommended single-host deploy), see **[DOCKER.md](./DOCKER.md)**.

AssetFlow is a **SPA + Django API** app. GitHub Pages can host the **frontend only** (static files). The Django backend needs a separate host.

## Why GitHub Pages alone is not enough

| Layer | GitHub Pages | What you need |
|-------|--------------|---------------|
| React (Vite build) | Yes | `npm run build` → publish `dist/` |
| Django API + Postgres + media/QR files | **No** (no Python server) | Railway, Render, Fly.io, VPS, etc. |
| JWT auth + private APIs | Needs HTTPS API URL | Set `VITE_API_BASE_URL` to your API |

## Recommended options

### Option A — GitHub Pages (frontend) + cloud API (best “GitHub Pages” path)

1. **Backend** on [Render](https://render.com), [Railway](https://railway.app), or [Fly.io](https://fly.io):
   - Deploy `backend/` with Postgres
   - Set `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS` to your Pages URL
2. **Frontend** on GitHub Pages:
   - Build with API base URL pointing at the cloud API
   - Example env for build: `VITE_API_BASE_URL=https://your-api.onrender.com/api`
   - Publish `frontend/dist` via GitHub Actions (`peaceiris/actions-gh-pages` or `actions/upload-pages-artifact`)
3. Update Axios base URL in `frontend/src/services/api.ts` to use `import.meta.env.VITE_API_BASE_URL`.

Caveats: camera QR scan needs HTTPS (Pages is fine). Media/QR images must be served from the API host (or S3/Cloudinary).

### Option B — Single host (simpler ops)

Deploy frontend + backend together:

- **Render / Railway / Fly** Docker or Procfile: Gunicorn for Django + serve Vite `dist` from Django/`whitenoise`, **or**
- **Vercel/Netlify** for FE + Render for BE

No GitHub Pages required.

### Option C — Demo-only static mock (not recommended)

Pages-only with mocked JSON — loses real auth, QR media, and approvals.

## Sample GitHub Actions (Pages frontend)

```yaml
# .github/workflows/pages.yml
name: Deploy frontend to Pages
on:
  push:
    branches: [main]
permissions:
  contents: read
  pages: write
  id-token: write
jobs:
  build-deploy:
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
          cache-dependency-path: frontend/package-lock.json
      - working-directory: frontend
        run: |
          npm ci
          echo "VITE_API_BASE_URL=${{ secrets.VITE_API_BASE_URL }}" > .env.production
          npm run build
      - uses: actions/upload-pages-artifact@v3
        with:
          path: frontend/dist
      - id: deployment
        uses: actions/deploy-pages@v4
```

Also set repo Settings → Pages → Source: **GitHub Actions**.

## Local multi-user testing (no hosting needed)

```bash
cd backend
source .venv/bin/activate
python manage.py seed_demo_users --settings=config.settings_local
```

Then open **two browsers** (or one normal + one private window) and log in as:

| Email | Role | Password |
|-------|------|----------|
| `admin@assetflow.local` | Admin | `Demo1234!` |
| `it@assetflow.local` | IT Team | `Demo1234!` |
| `manager@assetflow.local` | Manager | `Demo1234!` |
| `employee@assetflow.local` | Employee | `Demo1234!` |

Or create people from **Employees → Add employee** and log in with that email/password.
