# AppointHUB — Final Project Report

## Project information

| Field | Value |
| --- | --- |
| Project | AppointHUB |
| Domain | Appointment and shared team-resource management |
| Frontend | React, TypeScript, Vite |
| Backend | FastAPI, SQLAlchemy |
| Database | PostgreSQL for persistent deployment; SQLite for isolated tests |
| Student name / IUB ID / section / team | To be completed by the student |

This report consolidates the project PRD, SRS and TDD. The detailed source documents remain in [docs/PRD.md](./docs/PRD.md), [docs/SRS.md](./docs/SRS.md) and [docs/TDD.md](./docs/TDD.md).

## 1. Product Requirements (PRD)

### 1.1 Product overview and problem

AppointHUB supports patients who need to find a doctor, book appointments and share selected resources with a team. It combines a doctor directory and user-owned appointments with team-level permissions and administrator moderation.

### 1.2 Users and goals

- **User:** sign up, sign in, maintain a profile, browse active doctors, book/manage owned appointments, inspect/revoke sessions, and access permitted groups.
- **Administrator:** manage users, doctor profiles and content; apply bans/role changes; revoke sessions; inspect security/activity data; and export filtered data.
- **Group owner:** rename/delete their group, invite/remove members, assign member permissions, and control shared resources.
- **Group member:** view shared resources and create/edit only where granted.

### 1.3 Product scope

The current application includes registration/login, short-lived JWT access tokens, rotating refresh sessions, public active-doctor browsing, admin doctor management, doctor-linked appointment booking, user/admin roles, groups/resources, account settings, moderation, security statistics, activity logs and CSV exports. Nullable doctor/reason columns are added without deleting legacy appointments. Payment processing, doctor time-slot conflict scheduling and production monitoring are outside this implementation.

### 1.4 Acceptance goals

1. A user can only access their own appointments unless authorized as an administrator.
2. Protected requests reject missing, expired, malformed, revoked-session and banned-user tokens.
3. Admin endpoints enforce the role on the server.
4. Group permissions are enforced server-side and only the owner can manage group membership, rename/delete the group, or delete its shared resources.
5. Administrative actions and security-relevant authentication events are queryable and exportable.
6. The Vercel deployment uses persistent storage and is validated using live URLs before submission.

## 2. Software Requirements (SRS)

### 2.1 Functional requirements

- **Authentication:** user registration and login; Argon2 password hashes with an environment-sourced pepper; access JWT lifetime capped at 15 minutes; refresh token in an httpOnly cookie with a hashed database representation, rotation and revocation.
- **Account:** read/update own profile, change password after current-password verification, list/revoke own sessions, revoke all sessions after password changes.
- **Authorization:** database roles (`user`, `admin`), a common RBAC helper, immediate session rejection after session revocation or account ban, and owner checks for appointments.
- **Doctors and bookings:** public active-doctor directory; admin create/update/deactivate endpoints; authenticated booking with doctor, date/time, reason and status; inactive-doctor bookings rejected.
- **Groups:** create/join groups; per-member view/create/edit permissions; owner-only membership changes, group rename/deletion and shared-resource deletion.
- **Admin:** statistics; searchable/filterable/paginated user list; user detail with records, groups, sessions and recent events; justified ban/unban, role changes, bulk actions and session revocation; record/group moderation; failed-login summaries; searchable activity log; filtered CSV downloads.
- **Client behavior:** restore the refresh session before rendering guest content, renew an expired access token once and retry, sign out after refresh failure, and hide admin navigation for normal users.

### 2.2 Validation and error handling

Pydantic validates request data, including account/password fields. Login failures are recorded and temporarily rate-limited after five failures in a rolling 15-minute window by account or IP. Protected endpoints return 401 for invalid credentials/session and 403 for insufficient role/permission. Resource ownership failures use 404 to avoid disclosing another user's records.

### 2.3 Non-functional requirements

- Secrets are read from environment variables and examples contain placeholders only.
- CORS allows explicitly configured frontend origins, with local development origins only outside Vercel.
- API errors do not intentionally expose stack traces.
- Demo data is created only by an explicit provisioning script; demo passwords are environment inputs and are not printed.
- Production data must live in a hosted persistent database.

## 3. Technical Design (TDD)

### 3.1 Architecture

The TypeScript SPA calls a FastAPI REST API through a shared API service module. The backend performs authentication, validation and authorization before database operations. SQLAlchemy persists users, doctors, doctor-linked appointments, groups, group memberships/resources, refresh sessions, moderation records and user activity.

### 3.2 Authentication and authorization flow

1. Registration validates input and stores only an Argon2 hash of the pepper-prepared password.
2. Successful login creates a refresh session and an access token containing user ID, role and session ID.
3. Protected requests validate the signed JWT and verify the referenced active session and live user/ban status against the database.
4. Refresh atomically revokes the old session and issues a new refresh token/access token pair.
5. Logout, password change, role changes, admin session revocation and bans revoke sessions; access tokens backed by revoked sessions are rejected immediately.
6. Shared group operations require membership and the corresponding permission. Group management and resource deletion require owner identity.

### 3.3 API and deployment

The API is mounted under `/api`; the public doctor directory is `/api/doctors`, admin doctor operations are under `/api/admin/doctors`, OpenAPI docs are at `/api/docs`, schema at `/api/openapi.json`, and health check at `/api/health`. Vercel rewrites `/api/*` to FastAPI and other paths to the Vite frontend. Production must set persistent `DATABASE_URL`, `JWT_SECRET_KEY`, `PASSWORD_PEPPER`, secure-cookie configuration and, for split-origin hosting, exact `FRONTEND_ORIGINS` and `VITE_API_BASE_URL`.

### 3.4 Data and demo fixtures

The demo provisioner creates two admin accounts, three normal accounts, appointments, one shared group and a mixed-permission member set. It prints generated user/group IDs only. Actual instructor IDs depend on the target hosted database and are to be copied into the submission form after provisioning.

### 3.5 Test strategy and current verification

Automated backend tests cover invalid login, missing/invalid/expired/revoked access tokens, refresh rotation/logout, role denial/admin access, banned-user rejection, appointment ownership, group-owner restrictions, doctor access/booking rules and legacy appointment migration. The latest backend run passed **18 tests**. Frontend TypeScript type-checking and the Vite production build both passed.

## 4. Requirement status and submission checklist

| Requirement | Local code status | Remaining external step |
| --- | --- | --- |
| Authentication, password policy, refresh/logout, sessions | Implemented and tested | Configure production secrets/cookies |
| User/admin roles and ownership checks | Implemented and tested | Seed hosted demo users |
| Doctor directory and doctor-linked booking | Implemented locally; migration preserves existing appointment rows | Verify against hosted database and live URLs |
| Group mixed permissions and owner-only management | Implemented and tested | Verify with hosted demo accounts |
| Admin dashboard, moderation, activity/security, CSV | Implemented locally | Verify all paths against deployed data |
| Persistent database and CORS | Configuration documented | Attach hosted PostgreSQL and exact Vercel origins |
| Vercel frontend/API/docs | Deployment configuration present | Deploy from `main` and verify live URLs |
| Instructor IDs, live shared group and sample data | Idempotent seed script provided | Run it against the hosted database and record generated IDs |
| PDF screenshots and 5–8 minute video | Not included in this repository | Capture from the live deployment for the submission |
| Student/team identity and submission confirmation | Not provided | Complete in the final submission form |

**Deployment boundary:** this report and code have not been pushed to GitHub or deployed to Vercel. Live URLs, account IDs, deployment screenshots and video must only be claimed after the project owner completes and verifies those steps.
