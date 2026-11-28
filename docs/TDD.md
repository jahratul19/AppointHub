# AppointHUB — Technical Design Document

## 1. Architecture

AppointHUB uses a React + TypeScript SPA, a FastAPI REST API and SQLAlchemy persistence. The frontend calls API functions in one service layer. FastAPI validates request schemas, authenticates the caller, enforces RBAC/ownership/group permissions and performs database operations.

## 2. Components

- `frontend/src/App.tsx`: session restoration, workspace navigation, appointments, account management and admin user workflows.
- `frontend/src/services/api.ts`: API calls, one-time refresh/retry after 401 and session-expired notifications.
- `frontend/src/pages/GroupsPage.tsx`: shared groups and member resource permissions.
- `frontend/src/pages/DoctorDirectoryPage.tsx`: active doctor browsing and booking selection.
- `frontend/src/pages/AdminDoctorsPage.tsx`: administrator doctor create/update/deactivate workflows.
- `frontend/src/pages/AppointmentsPage.tsx`: doctor selection and patient appointment details.
- `frontend/src/pages/AdminContentPage.tsx`: appointment/group moderation and filtered record export.
- `frontend/src/pages/AdminSecurityPage.tsx`: activity log, activity export and failed-login summaries.
- `backend/app/security.py`: Argon2/pepper password handling, JWT and refresh token primitives.
- `backend/app/rbac.py`: role constants and group permission checks.
- `backend/app/routes.py`: API routes, current user/admin dependencies, ownership checks and admin workflows.
- `backend/app/services.py`: authentication/session and appointment business logic, including active-doctor validation.
- `backend/app/models.py`: users, doctors, appointments, sessions, groups, resources, moderation and activity data.
- `backend/app/migrations.py`: additive migration for legacy appointment doctor/reason columns.
- `backend/app/activity.py`: request metadata and login rate-limit activity queries.

## 3. Authentication data flow

1. Password policy is validated before account creation/change.
2. The password is combined with an environment-sourced pepper and stored as an Argon2 hash.
3. Login creates a hashed refresh-session record and an access JWT with `sub`, `role`, `sid`, and `exp`.
4. Protected routes decode the JWT, load the referenced unrevoked/unexpired session and verify the current user is not banned.
5. Refresh atomically revokes the old refresh session and creates a replacement; replayed tokens fail.
6. Logout, password change, ban, role changes and session revocation invalidate sessions. The session ID check makes access tokens unusable immediately after revocation.

## 4. Data model

- **User:** unique username/email, Argon2 password hash, `user`/`admin` role and ban status.
- **Appointment:** appointment fields and owning user ID.
- **Doctor:** name, optional photo URL, specialty, description and active status.
- **Appointment:** owning user, nullable doctor foreign key, date, time, reason and status. Doctor/reason columns remain nullable for legacy records; new booking requests require an active doctor and a visit reason.
- **AuthSession:** user ID, unique refresh-token hash, creation/expiry/revocation timestamps.
- **Group / GroupMember:** group owner and each member's view/create/edit permissions.
- **GroupResource:** resource content, group and creator.
- **AdminModerationLog:** ban/unban/role management history.
- **UserActivity:** actor/target, event, account identifier, IP, user-agent, details and timestamp.

`Base.metadata.create_all` creates newly introduced tables. `migrate_appointment_doctor_fields` adds nullable doctor/reason columns to existing appointment tables without deleting or rewriting their rows. Production schema changes should continue to use an explicit migration process if future changes alter existing columns.

## 5. API surface

API routes are under `/api`. Major route groups include:

- `/api/auth/*`: register, login, refresh, logout, current profile, profile update, password change and sessions.
- `/api/appointments/*`: user-owned appointment CRUD.
- `/api/doctors`: public list of active doctors.
- `/api/admin/doctors`: admin-only doctor list/create/update/deactivate.
- `/api/groups/*`: group membership, owner-only management, permissions and shared resources.
- `/api/admin/*`: dashboard, user list/details/actions, activity/security, content moderation and CSV exports.

OpenAPI documentation is available at `/api/docs`, schema at `/api/openapi.json`, and health at `/api/health`.

## 6. Deployment and configuration

Vercel routes `/api/*` to FastAPI and the remaining paths to Vite. Production requires hosted persistent PostgreSQL, separate long random `JWT_SECRET_KEY` and `PASSWORD_PEPPER`, HTTPS secure cookies and exact frontend CORS origins when split origins are used. Same-origin frontend/API deployments can leave `VITE_API_BASE_URL` empty.

Never store credentials in source control. `.env.example` files contain placeholders. Demo accounts are provisioned by `backend/scripts/seed_demo_data.py` using environment-only passwords; generated IDs are printed for the final submission, and the script never prints passwords.

## 7. Testing and release

Backend tests exercise authentication, session revocation, role and ownership enforcement, group owner rules, login abuse controls, doctor authorization, active-doctor booking and legacy appointment migration. The frontend is type-checked and built with the Vite production build. Release acceptance still requires deployment from `main`, live URL/browser checks, hosted demo provisioning, screenshots/PDF and the recorded demo video.
