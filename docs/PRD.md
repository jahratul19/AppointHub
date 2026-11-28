# AppointHUB — Product Requirements Document

## 1. Product overview

AppointHUB is a healthcare appointment application with a doctor directory, secure user accounts, administrator moderation and shared group resources. Patients browse active doctors and book appointments with a selected doctor.

## 2. Problem and goals

Appointments kept across separate tools are difficult to track and can expose one user's information to another. AppointHUB centralizes appointments and shared team resources while enforcing identity, ownership and permission checks on the backend.

Product goals:

- Provide a responsive sign-up/login and account-management experience.
- Let patients browse doctors and book appointments with a selected active doctor.
- Let administrators maintain doctor profiles and availability status.
- Protect individual appointments and account data from other ordinary users.
- Let group owners share selected resources with different member permissions.
- Give administrators tools for account management, content moderation, security review and reporting.
- Support persistent hosted deployment through Vercel and a hosted relational database.

## 3. User types

- **User:** manages their own profile and sessions, browses active doctors, books/manages their own appointments, and accesses permitted group resources.
- **Administrator:** manages users, sessions, doctors, records and groups and can inspect audit/security information.
- **Group owner:** creates, renames and deletes a group; adds/removes members and grants view/create/edit permissions.
- **Group member:** participates in shared work only within the permissions assigned by the group owner.

## 4. Main product requirements

### Accounts and security

- Signup and login with Argon2 password hashing and a server-side password pepper.
- Short-lived signed access tokens and rotating, revocable httpOnly refresh sessions.
- Profile updates, password changes requiring the current password, session listing/revocation and logout.
- Rate-limited failed login attempts and activity records for security-relevant events.

### Appointments and groups

- The public doctor directory displays active doctors' names, profile photos, specialties and descriptions.
- Administrators create, update and deactivate doctor profiles; inactive doctors are excluded from the directory and cannot receive new bookings.
- Authenticated users book an active doctor by selecting an appointment date/time and providing a visit reason. The server records the user, doctor and appointment status.
- Users create, view, update and delete their own appointments; existing appointment records are preserved when doctor/reason columns are introduced.
- Administrators can moderate all appointment records.
- Group members can have distinct view/create/edit permissions.
- The group owner alone can rename/delete the group, manage members and delete shared resources.

### Administrator workspace

- Dashboard statistics, searchable and filterable user lists, pagination and user details.
- Ban/unban with a reason, role updates, bulk actions and session revocation.
- Appointment/group moderation, failed-login summaries, searchable activity logs and filtered CSV exports.

## 5. Out of scope

Online payments, provider time-slot availability scheduling, notification delivery, and health-record storage are not part of this project version. A selected date/time is recorded, but the system does not prevent scheduling conflicts.

## 6. Success criteria

The project is successful when protected actions are denied by backend checks when identity, ownership, role or group permission is missing; account sessions can be invalidated; admin activity is reviewable; and the deployed Vercel application is verified against a persistent database.

## 7. Release and demo requirements

The repository includes an idempotent demo-data provisioning script for two admins, three normal users, appointment records and a shared mixed-permission group. Production secrets/passwords remain outside version control. Generated user IDs, live URLs, screenshots/PDF and the demo video must be collected after hosted provisioning and deployment.
