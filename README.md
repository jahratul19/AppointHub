# AppointHUB

AppointHUB is a multi-user healthcare appointment platform built with React, TypeScript, FastAPI and SQLAlchemy. It provides a public active-doctor directory, doctor-linked appointment booking, JWT authentication, account/session management, database-enforced roles, group permissions and an administrator workspace.

## Project layout

- `backend/` — FastAPI API and SQLAlchemy models.
- `frontend/` — React + TypeScript web app.
- `docs/` — product, requirements and technical design documents.
- `FINAL_REPORT.md` — consolidated project report.

## Local setup

Use Python 3.10+ and Node.js 22+.

1. Copy `backend/.env.example` to `backend/.env` and set a persistent database URL, a unique `JWT_SECRET_KEY`, and a separate `PASSWORD_PEPPER`.
2. Install backend dependencies and run the API:

   ```powershell
   cd backend
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   fastapi dev main.py
   ```

   API docs are served at `http://localhost:8002/api/docs`.
   The public directory is `GET /api/doctors`; doctor create/update/deactivate routes require an admin token under `/api/admin/doctors`.
3. In another terminal, install and run the frontend:

   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

   Local Vite requests proxy `/api` to the backend. `frontend/.env.example` is only needed when the frontend and API are deployed on different origins.

## Environment and deployment

Do not commit `.env` files, API keys, database credentials, or demo passwords. Use Vercel Environment Variables for production values:

- `DATABASE_URL`: hosted PostgreSQL connection string with SSL; do not use an ephemeral SQLite file.
- `JWT_SECRET_KEY` and `PASSWORD_PEPPER`: independently generated long random secrets.
- `FRONTEND_ORIGINS`: comma-separated exact frontend origins if frontend and backend use different domains.
- `COOKIE_SECURE=true` for HTTPS. The backend sets secure cookies automatically in Vercel when this variable is omitted.
- `VITE_API_BASE_URL`: leave empty when the Vercel rewrite serves both app and API on one origin; otherwise set the API origin.

Deploy from the `main` branch after all changes are reviewed and merged. The API docs path is `/api/docs`; the API OpenAPI schema is `/api/openapi.json`. Verify the deployed frontend, API health endpoint (`/api/health`), API docs, CORS, cookies, database persistence and reload/deep-link behavior on the actual Vercel URLs.

This workspace change has not been pushed or deployed. Vercel project settings, hosted database provisioning and live URLs must be completed by the project owner.

## Provisioning instructor demo data

Set the `DEMO_ADMIN1_*`, `DEMO_ADMIN2_*`, and `DEMO_USER1_*` through `DEMO_USER3_*` values from `backend/.env.example` in a secure environment. Use demo-only passwords that satisfy the policy. Never place passwords in this repository or README.

Run this against the intended persistent database only:

```powershell
cd backend
python -m scripts.seed_demo_data
```

The script is repeatable and prints the generated IDs and roles, not passwords. It provisions two admins, three normal users, appointment records and a shared `AppointHUB Demo Team` owned by `demo_admin_1`. The owner can manage/delete the group and assign permissions; `demo_admin_2` can view/create, `demo_user_1` can view, `demo_user_2` can view/create, and `demo_user_3` can view/edit. The seeded owner alone can delete resources or manage team membership.
It also provisions sample active doctors and doctor-linked bookings. On startup, an additive migration adds nullable `doctor_id` and `reason` columns to legacy appointment tables without removing existing records.

### Instructor account identifiers

User IDs are database-generated and are not known until the demo seeding script has been run against the instructor's hosted database. After seeding, copy the five printed IDs and roles into the submission form; do not add passwords here.

| Account | Role | User ID |
| --- | --- | --- |
| `demo_admin_1` | admin, group owner | Generated at provisioning |
| `demo_admin_2` | admin | Generated at provisioning |
| `demo_user_1` | user | Generated at provisioning |
| `demo_user_2` | user | Generated at provisioning |
| `demo_user_3` | user | Generated at provisioning |

## Tests and build

From the repository root:

```powershell
$env:PYTHONPATH = "backend"
python -m pytest backend\tests -q
cd frontend
npm run build
```

The project tests cover login, access-token rejection, refresh rotation/logout, admin role checks, record ownership, group-owner restrictions, doctor access/booking rules and legacy appointment migration.
