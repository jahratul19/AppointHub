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
| POST   | `/api/v1/auth/register`                        | Register a customer                      |
| POST   | `/api/v1/auth/token`                           | Authenticate and obtain an access token  |
| GET    | `/api/v1/auth/me`                              | Retrieve the current user's profile      |
| GET    | `/api/v1/providers`                            | List service providers                   |
| GET    | `/api/v1/providers/{provider_id}/slots`        | View available appointment slots         |
| POST   | `/api/v1/appointments`                         | Book an appointment                      |
| GET    | `/api/v1/appointments/mine`                    | View the current customer's appointments |
| PATCH  | `/api/v1/appointments/{appointment_id}/cancel` | Cancel an eligible appointment           |
| GET    | `/api/v1/provider/appointments`                | View the provider's appointments         |
| POST   | `/api/v1/provider/availability`                | Create provider availability             |
| GET    | `/api/v1/admin/users`                          | List users for authorized administrators |

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
## 10. Use Cases

### UC-01: User Registration

* **Primary Actor:** Visitor
* **Precondition:** The visitor does not already have an account.
* **Main Flow:**
  1. The visitor opens the registration page.
  2. The visitor enters the required registration information.
  3. The frontend sends the registration request to the backend.
  4. The backend validates the information.
  5. The system creates the user account and returns a success response.
* **Alternative Flow:** If the information is invalid or the account already exists, the system returns an appropriate error message.
* **Postcondition:** A new customer account is created successfully.

### UC-02: User Login

* **Primary Actor:** Registered User
* **Precondition:** The user has a registered account.
* **Main Flow:**
  1. The user opens the login page.
  2. The user enters their login credentials.
  3. The frontend sends the credentials to the backend.
  4. The backend verifies the credentials.
  5. The system returns an authentication response.
* **Alternative Flow:** If the credentials are invalid, the system returns an authentication error.
* **Postcondition:** The user is authenticated and can access authorized features.

### UC-03: View Service Providers

* **Primary Actor:** Customer
* **Precondition:** The application is accessible.
* **Main Flow:**
  1. The customer opens the service provider listing page.
  2. The frontend requests the provider list from the backend.
  3. The backend retrieves the available service providers.
  4. The frontend displays the provider information.
* **Alternative Flow:** If no providers are available, the system displays an appropriate message.
* **Postcondition:** The customer can view available service providers.

### UC-04: View Available Appointment Slots

* **Primary Actor:** Customer
* **Precondition:** The selected service provider has availability information.
* **Main Flow:**
  1. The customer selects a service provider.
  2. The frontend requests the provider's available appointment slots.
  3. The backend retrieves the available slots.
  4. The frontend displays the available appointment slots.
* **Alternative Flow:** If no appointment slots are available, the system displays an appropriate message.
* **Postcondition:** The customer can view available appointment slots.

### UC-05: Manage Provider Availability

* **Primary Actor:** Service Provider
* **Precondition:** The service provider is authenticated and authorized.
* **Main Flow:**
  1. The service provider opens the availability management page.
  2. The provider enters or updates availability information.
  3. The frontend sends the request to the backend.
  4. The backend validates the information and authorization.
  5. The system saves the availability information.
* **Alternative Flow:** If the information is invalid or permission is denied, the system returns an appropriate error.
* **Postcondition:** The provider's availability is created or updated successfully.

### UC-06: Book an Appointment

* **Primary Actor:** Customer
* **Precondition:** The customer is authenticated and the selected appointment slot is available.
* **Main Flow:**
  1. The customer selects a service provider and an available appointment slot.
  2. The customer submits the booking request.
  3. The frontend sends the request to the backend.
  4. The backend validates the request and checks slot availability.
  5. The backend creates the appointment.
  6. The system returns a booking confirmation.
* **Alternative Flow:** If the selected slot is already booked or the request is invalid, the system returns an appropriate error.
* **Postcondition:** The appointment is successfully booked.

### UC-07: View Appointments

* **Primary Actor:** Customer or Service Provider
* **Precondition:** The user is authenticated.
* **Main Flow:**
  1. The user opens the appointment management page.
  2. The frontend requests the relevant appointment records.
  3. The backend verifies the user's identity and permissions.
  4. The backend retrieves the authorized appointment records.
  5. The frontend displays the appointment information.
* **Alternative Flow:** If no appointments are found, the system displays an appropriate message.
* **Postcondition:** The user can view appointments they are authorized to access.

### UC-08: Cancel an Appointment

* **Primary Actor:** Customer
* **Precondition:** The customer is authenticated and owns an eligible appointment.
* **Main Flow:**
  1. The customer opens their appointment list.
  2. The customer selects an eligible appointment.
  3. The customer confirms the cancellation.
  4. The frontend sends the cancellation request to the backend.
  5. The backend verifies ownership and cancellation rules.
  6. The system processes the cancellation and returns a response.
* **Alternative Flow:** If the appointment does not exist, is not eligible for cancellation, or belongs to another user, the system returns an appropriate error.
* **Postcondition:** The eligible appointment is cancelled successfully.

### UC-09: Manage User Accounts and Roles

* **Primary Actor:** Administrator
* **Precondition:** The administrator is authenticated and has the required permissions.
* **Main Flow:**
  1. The administrator opens the user management page.
  2. The frontend requests the user records from the backend.
  3. The backend verifies administrative permissions.
  4. The system displays the authorized user information.
  5. The administrator performs an authorized user or role management action.
  6. The backend validates and processes the requested action.
* **Alternative Flow:** If the administrator lacks permission or the requested information is invalid, the system returns an appropriate error.
* **Postcondition:** The authorized user-management action is completed successfully.
