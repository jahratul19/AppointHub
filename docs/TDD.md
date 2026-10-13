# AppointHUB — Technical Design Document (TDD)

## 1. Introduction

### 1.1 Purpose

This document describes the proposed technical architecture, system components, API design, security model, and implementation approach for AppointHUB.

### 1.2 System Overview

AppointHUB is a web-based appointment booking system. It will use a React.js frontend with TypeScript and a FastAPI backend written in Python. The frontend will communicate with the backend through REST APIs.

This document describes the planned design. Implementation details may be adjusted during development.

## 2. Technology Stack

* Frontend: React.js
* Programming Language: TypeScript
* Backend Framework: FastAPI
* Backend Language: Python
* API Style: REST
* Data Validation: TypeScript types on the frontend and Pydantic models on the backend
* Authentication: Token-based authentication
* Authorization: Role-Based Access Control (RBAC), security scopes, and resource ownership checks
* Database: To be finalized during implementation

## 3. System Architecture

The system will follow a client-server architecture.

### 3.1 Frontend Layer

The React.js application will provide the user interface for customers, service providers, and administrators.

Responsibilities include:

* Displaying provider listings and appointment availability.
* Providing registration and login forms.
* Allowing customers to manage their appointments.
* Allowing providers to manage availability and appointments.
* Providing administrative interfaces for authorized users.
* Communicating with backend endpoints and displaying API responses.

### 3.2 Backend Layer

The FastAPI application will handle business logic and expose REST API endpoints.

Responsibilities include:

* Validating incoming requests.
* Authenticating users.
* Enforcing roles, scopes, permissions, and resource ownership.
* Managing provider availability and appointment bookings.
* Preventing conflicting bookings.
* Returning appropriate HTTP status codes and response data.

### 3.3 Data Layer

The data layer will store user accounts, roles, provider profiles, availability slots, and appointment records.

A relational database is a suitable option because these entities have structured relationships. The specific database technology will be selected during implementation.

## 4. Proposed Data Model

### 4.1 User

* `id`: Unique user identifier
* `name`: User's display name
* `email`: Unique email address
* `password_hash`: Securely hashed password
* `role`: Customer, provider, or administrator
* `created_at`: Account creation timestamp

### 4.2 ProviderProfile

* `id`: Unique provider profile identifier
* `user_id`: Reference to the provider's user account
* `service_name`: Name of the service provided
* `description`: Optional service description

### 4.3 AvailabilitySlot

* `id`: Unique slot identifier
* `provider_id`: Reference to the service provider
* `start_time`: Appointment start time
* `end_time`: Appointment end time
* `is_available`: Availability status

### 4.4 Appointment

* `id`: Unique appointment identifier
* `customer_id`: Reference to the customer
* `provider_id`: Reference to the service provider
* `start_time`: Appointment start time
* `end_time`: Appointment end time
* `status`: Booked, cancelled, or completed
* `created_at`: Booking creation timestamp

These models describe the proposed design and may be refined to match the final database schema.

## 5. REST API Design

The backend will expose versioned REST endpoints under `/api/v1`.

| Method | Endpoint                                       | Purpose                                  |
| ------ | ---------------------------------------------- | ---------------------------------------- |
| POST   | `/api/v1/auth/register`                        | Register a customer                      |
| POST   | `/api/v1/auth/token`                           | Authenticate and obtain an access token  |
| GET    | `/api/v1/auth/me`                              | Get the current user's profile           |
| GET    | `/api/v1/providers`                            | List service providers                   |
| GET    | `/api/v1/providers/{provider_id}/slots`        | View provider availability               |
| POST   | `/api/v1/appointments`                         | Book an appointment                      |
| GET    | `/api/v1/appointments/mine`                    | View the customer's appointments         |
| PATCH  | `/api/v1/appointments/{appointment_id}/cancel` | Cancel an appointment                    |
| GET    | `/api/v1/provider/appointments`                | View the provider's appointments         |
| POST   | `/api/v1/provider/availability`                | Create availability slots                |
| GET    | `/api/v1/admin/users`                          | List users for authorized administrators |

These endpoints are proposed. The final API implementation should remain consistent with the SRS.

## 6. Authentication and Authorization

### 6.1 Authentication Flow

1. A user submits valid login credentials.
2. The backend verifies the credentials.
3. The backend issues an access token if authentication succeeds.
4. The frontend uses the token when calling protected endpoints.
5. The backend validates the token before processing protected requests.

Passwords must never be stored in plain text. Token handling and storage must follow appropriate security practices.

### 6.2 Role-Based Access Control

The system will support three primary roles:

* **Customer:** Browse providers and manage their own appointments.
* **Provider:** Manage their own availability and assigned appointments.
* **Administrator:** Manage users and perform authorized administrative operations.

### 6.3 Security Scopes and Permissions

FastAPI security scopes and permission checks will be used to restrict access to protected operations.

Example proposed scopes:

* `appointments:read`
* `appointments:book`
* `appointments:cancel`
* `availability:manage`
* `provider:appointments:read`
* `users:manage`

The backend must also verify resource ownership. A valid role or token alone must not allow a customer to access another customer's appointment.

## 7. Appointment Booking Workflow

1. The customer selects a service provider.
2. The frontend requests available appointment slots.
3. The customer selects a slot and submits a booking request.
4. The backend authenticates the customer and validates the request.
5. The backend checks that the slot is still available.
6. The backend safely creates the appointment and prevents conflicting bookings.
7. The frontend displays the booking result.

Availability checks and booking creation should be handled safely to prevent two users from booking the same slot concurrently.

## 8. Error Handling

The backend will return consistent HTTP responses.

* `200 OK`: Successful request.
* `201 Created`: Resource created.
* `400 Bad Request`: Invalid request.
* `401 Unauthorized`: Authentication required or invalid.
* `403 Forbidden`: Insufficient permissions.
* `404 Not Found`: Resource not found.
* `409 Conflict`: Appointment slot conflict.
* `422 Unprocessable Entity`: Request validation failure.
* `500 Internal Server Error`: Unexpected server error.

Error responses must not reveal passwords, tokens, stack traces, or other sensitive information.

## 9. Frontend and Backend Integration

* The frontend will call backend REST endpoints through a shared API service layer.
* TypeScript interfaces or types will represent API request and response structures.
* FastAPI and Pydantic will validate backend requests and responses.
* The frontend will display loading, success, and error states.
* The backend will remain responsible for enforcing all security rules.
* Cross-Origin Resource Sharing (CORS) will be configured for the permitted frontend origin.

## 10. Testing Strategy

### 10.1 Frontend Testing

Test form validation, navigation, appointment workflows, and API error handling.

### 10.2 Backend Testing

Use automated tests to verify authentication, permissions, input validation, booking rules, and API responses.

### 10.3 Integration Testing

Verify that the React frontend communicates correctly with the FastAPI backend.

### 10.4 Security Testing

Verify that unauthorized users cannot access protected endpoints or modify resources belonging to other users.

## 11. Development and Deployment Considerations

* Keep configuration values and secrets outside source code.
* Use environment variables for environment-specific settings.
* Configure allowed frontend origins explicitly.
* Maintain clear separation between frontend and backend responsibilities.
* Document setup and execution instructions as the implementation evolves.

## 12. Future Enhancements

Potential future enhancements include appointment reminders, notifications, payment integration, and reporting. These features are outside the initial implementation scope unless approved separately.
