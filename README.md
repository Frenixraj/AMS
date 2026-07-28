# AssetFlow

Smart Asset Management Platform — QR tracking, approval workflows, maintenance, notifications, dashboards, and reports.

## Structure

```
AMS/
├── backend/
│   ├── config/          # Django settings, urls, wsgi/asgi
│   ├── apps/            # Domain apps
│   │   ├── authentication/
│   │   ├── assets/
│   │   ├── employees/
│   │   ├── approvals/
│   │   ├── maintenance/
│   │   ├── notifications/
│   │   ├── reports/
│   │   ├── dashboard/
│   │   └── common/
│   ├── manage.py
│   └── requirements.txt
├── frontend/            # React + Vite + TypeScript + Tailwind + shadcn
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── hooks/
│       ├── services/
│       ├── contexts/
│       ├── types/
│       ├── utils/
│       └── layouts/
├── .gitignore
└── README.md
```

## Prerequisites

- Python 3.10+
- Node.js 18+ and npm
- PostgreSQL 14+

## Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # set DB_* credentials
createdb assetflow
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

API: `http://localhost:8000`

### Key API surfaces

| Area | Base path |
|------|-----------|
| Auth | `/api/auth/token/`, `/api/auth/me/`, `/api/auth/users/` |
| Assets + QR | `/api/assets/` |
| Categories / Vendors | `/api/assets/categories/`, `/api/assets/vendors/` |
| Assignments | `/api/assets/assignments/` |
| Employees / Departments | `/api/employees/`, `/api/employees/departments/` |
| Approvals | `/api/approvals/requests/` |
| Maintenance | `/api/maintenance/tickets/` |
| Notifications | `/api/notifications/` |
| Dashboard | `/api/dashboard/summary/` |
| Reports | `/api/reports/` |
| Audit logs | `/api/audit-logs/` |

## Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

App: `http://localhost:5173` (proxies `/api` and `/media` to Django)

## Roles

| Role | Capabilities |
|------|----------------|
| Admin | Full access |
| IT Team | Assets, master data, assign/return, fulfill requests, maintenance, reports, audit |
| Manager | Approve/reject department requests, view employees/reports |
| Employee | Request assets, report issues, view assigned assets, scan QR |

## Suggested first data

1. Create users with roles in Django admin
2. Create Department (set manager)
3. Link Employee profile (Employees page or admin)
4. Create categories/vendors (Master data) and assets
5. Exercise request → approve → fulfill, or direct assign

## Tests

```bash
cd backend && source .venv/bin/activate
# Prefer Postgres when available; SQLite in-memory for local/CI without DB:
python manage.py test --settings=config.settings_test
```
