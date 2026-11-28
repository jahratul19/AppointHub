# AppointHUB — Software Requirements Specification

## 1. Purpose and scope

This specification defines the implemented and deployment requirements for AppointHUB, a React/TypeScript frontend and FastAPI backend for appointment management, shared team resources and administration.

## 2. Roles and authorization

The database stores the roles `user` and `admin`. Every protected route verifies a signed access token, the active server-side session and the current database user/ban state. Administrative routes require the admin role. Normal appointment access is restricted to the record owner; inaccessible records return 404. Group actions additionally require membership and the relevant permission. Only a group owner may manage members, rename/delete the group or delete group resources.

## 3. Functional requirements

### FR-01 Authentication and profile

The system shall allow signup/login, profile changes, password changes after current-password verification, logout, session listing and session revocation. Passwords shall be Argon2-hashed after server-side pepper preparation and shall never be stored as plaintext.

### FR-02 Tokens and session lifecycle

Access JWTs shall expire within 15 minutes and include user ID and role claims. Refresh tokens shall be delivered only in an httpOnly cookie, stored hashed, rotated on refresh and revoked at logout/password change/session revocation. Requests using missing, invalid, expired or revoked sessions, or a banned account, shall receive 401.

### FR-03 Login abuse and event records

Failed logins shall be recorded with account identifier, IP, browser/user-agent and time. Five failed attempts within 15 minutes for an account or IP shall trigger temporary rate limiting. Login, failed login, logout, password change, role change, ban/unban, content deletion and exports shall be auditable.

### FR-04 Doctor directory and appointment booking

The public `GET /api/doctors` endpoint shall return active doctors with name, photo URL, specialty and description. Admin-only endpoints shall create and update doctors and deactivate them. Authenticated users shall book an active doctor with appointment date/time and a required visit reason. The server shall derive the patient name from the authenticated account, store doctor ID and appointment status (initially `Pending`), and reject booking an inactive or missing doctor. Users may read, update and delete only their own appointments; administrators may inspect and moderate all appointments. Existing appointment rows shall be preserved when nullable `doctor_id` and `reason` columns are added.

### FR-05 Groups and shared resources

Users shall create groups and invite existing users. Group owners shall grant view/create/edit permissions to each member and shall be the only users allowed to add/remove members, change the group name, delete the group or delete shared resources. Members may access/create/edit resources only when their membership permissions allow.

### FR-06 Administration

Administrators shall be able to:

- View totals for users, banned users, appointments, groups and recent activity.
- Search/filter/paginate users by name/email, role and account status.
- View a user's appointments, groups, sessions and recent events.
- Ban/unban users with a reason, change another user's role, bulk ban/unban and revoke sessions.
- Create, update and deactivate doctor profiles; inactive doctors shall not appear in the public directory or accept new bookings.
- Search and moderate appointments/groups.
- Inspect activity logs and failed login summaries by IP/account.
- Export users, appointment records and filtered activity as CSV.

An administrator shall not change their own role or ban an administrator.

### FR-07 Frontend session and navigation

The client shall wait for session restoration before rendering guest content. On an access-token 401 it shall refresh once and retry; if refresh fails it shall clear the client session and request login. Admin navigation shall be shown only for administrators.

## 4. Non-functional requirements

- Production secrets are environment variables; only placeholder environment examples are versioned.
- CORS allows configured frontend origins and local development origins only outside Vercel.
- Production data uses a persistent hosted database.
- User-facing views provide loading, error and empty states.
- The appointment schema update shall retain legacy rows; pre-existing appointments may have no doctor/reason.
- API docs are available at `/api/docs` and health is available at `/api/health`.

## 5. Error responses

| Status | Meaning |
| --- | --- |
| 400 | Invalid operation or action |
| 401 | Missing/invalid/expired/revoked authentication |
| 403 | Authenticated but not authorized |
| 404 | Resource missing or inaccessible due to ownership |
| 409 | Duplicate account data |
| 422 | Request validation failure |
| 429 | Login rate limit reached |

## 6. Verification criteria

Pytest covers invalid login, token rejection, refresh rotation/logout, role access, banned-user rejection, appointment ownership and group-owner restrictions. Deployment acceptance additionally requires live Vercel URLs, a persistent database, seeded demo users/group and browser verification; local test results alone do not satisfy the deployment requirement.
