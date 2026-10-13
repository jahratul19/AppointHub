# AppointHUB — Software Requirements Specification (SRS)

## 1. Introduction

### 1.1 Purpose

This document defines the functional and non-functional requirements for AppointHUB, a web-based appointment booking system. It serves as a reference for designing, developing, testing, and maintaining the application.

### 1.2 Scope

AppointHUB will allow customers to browse service providers, view available appointment slots, and manage their bookings. Service providers will manage their availability and appointments, while administrators will manage user accounts and access permissions.

### 1.3 Technology Stack

* Frontend: React.js with TypeScript
* Backend: FastAPI with Python
* Communication: REST APIs
* Security: Authentication, authorization, RBAC, and security scopes

## 2. User Roles

### 2.1 Customer

* Register and log in to the system.
* View available service providers.
* View available appointment slots.
* Book appointments.
* View and cancel their own appointments.

### 2.2 Service Provider

* Log in to the system.
* Create and manage availability.
* View appointments assigned to them.
* Manage appointment status where permitted.

### 2.3 Administrator

* Manage user accounts.
* Assign and manage user roles.
* Access administrative functions according to assigned permissions.

## 3. Functional Requirements

### FR-01: User Registration

The system shall allow a new customer to create an account by providing the required registration information.

### FR-02: User Authentication

The system shall authenticate users before granting access to protected resources.

### FR-03: Provider Listing

The system shall allow customers to view available service providers.

### FR-04: Availability Management

The system shall allow authorized service providers to create and update their available appointment slots.

### FR-05: Appointment Booking

The system shall allow authenticated customers to book an available appointment slot.

### FR-06: Appointment Conflict Prevention

The system shall prevent multiple customers from booking the same appointment slot.

### FR-07: Appointment Viewing

The system shall allow customers to view their own appointments and service providers to view appointments assigned to them.

### FR-08: Appointment Cancellation

The system shall allow customers to cancel their own eligible appointments according to the system's booking rules.

### FR-09: User and Role Management

The system shall allow authorized administrators to manage user accounts and role assignments.

### FR-10: Authorization

The system shall verify user roles, permissions, and resource ownership before allowing restricted actions.

## 4. Non-Functional Requirements

### NFR-01: Security

Passwords shall be stored using a secure password-hashing mechanism. Protected endpoints shall require authentication and appropriate authorization.

### NFR-02: Usability

The user interface shall provide clear navigation and understandable feedback for successful actions and errors.

### NFR-03: Reliability

The system shall validate appointment availability before confirming a booking and shall handle conflicting booking requests safely.

### NFR-04: Maintainability

The frontend and backend shall be organized into modular components and maintainable code structures.

### NFR-05: Performance

Common operations, such as viewing provider listings and appointments, should respond within a reasonable time under normal usage.

### NFR-06: Data Integrity

The system shall validate incoming data and maintain consistent appointment and user records.

## 5. Security and Access Control

* Authentication shall identify the currently logged-in user.
* Role-Based Access Control (RBAC) shall restrict functionality according to the user's role.
* Security scopes and permissions shall restrict access to protected operations.
* Customers shall not access or modify another customer's appointments.
* Service providers shall not manage another provider's availability or appointments without explicit authorization.
* Administrative endpoints shall only be accessible to authorized administrators.
* The backend shall enforce access controls independently of frontend restrictions.

## 6. Proposed REST API Requirements

| Method | Endpoint                                | Purpose                                  |
| ------ | --------------------------------------- | ---------------------------------------- |
| POST   | `/auth/register`                        | Register a customer                      |
| POST   | `/auth/token`                           | Authenticate and obtain an access token  |
| GET    | `/auth/me`                              | Retrieve the current user's profile      |
| GET    | `/providers`                            | List service providers                   |
| GET    | `/providers/{provider_id}/slots`        | View available appointment slots         |
| POST   | `/appointments`                         | Book an appointment                      |
| GET    | `/appointments/mine`                    | View the current customer's appointments |
| PATCH  | `/appointments/{appointment_id}/cancel` | Cancel an eligible appointment           |
| GET    | `/provider/appointments`                | View the provider's appointments         |
| POST   | `/provider/availability`                | Create provider availability             |
| GET    | `/admin/users`                          | List users for authorized administrators |

These endpoints describe the proposed API design and may be refined during implementation.

## 7. Validation and Error Handling

The system shall validate request data and return appropriate HTTP status codes.

* `200 OK`: Request completed successfully.
* `201 Created`: A resource was created successfully.
* `400 Bad Request`: The request is invalid.
* `401 Unauthorized`: Authentication is required or invalid.
* `403 Forbidden`: The user lacks the required permission.
* `404 Not Found`: The requested resource does not exist or is unavailable to the requester.
* `409 Conflict`: The requested appointment slot is no longer available.
* `422 Unprocessable Entity`: Request data fails validation.

Error responses should provide clear messages without exposing sensitive system information.

## 8. Assumptions and Constraints

* Users must have an appropriate account to access protected features.
* Appointment availability must be checked before booking confirmation.
* The initial release focuses on core booking and access-control functionality.
* Online payments, video consultations, and AI-based features are outside the initial scope.
* Database technology and detailed deployment configuration will be finalized during technical design.

## 9. Acceptance Criteria

* Customers can register, authenticate, and manage their own appointments.
* Service providers can manage their availability and view assigned appointments.
* Administrators can perform authorized user-management tasks.
* The system prevents conflicting bookings.
* Protected resources enforce authentication, roles, permissions, and ownership checks.
* Invalid requests return appropriate error responses.
