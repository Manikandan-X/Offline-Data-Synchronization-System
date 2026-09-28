# Offline-First Data Synchronization System — Backend

A backend system for an **Offline-First Data Synchronization System** built with **FastAPI, MySQL, Redis, SQLAlchemy, Alembic, and JWT authentication**.

The backend provides authentication, user management, record management, offline synchronization, conflict detection and resolution, sync history, audit logging, and synchronization dashboard APIs.

---

## 1. Project Overview

The system is designed for applications where users may continue working even when there is no internet connection.

The frontend can create, update, and delete data locally while offline. Once the network connection is restored, the frontend sends synchronization operations to the backend.

The backend:

* Authenticates users using JWT
* Provides role-based access control
* Stores application data in MySQL
* Processes offline synchronization operations
* Detects synchronization conflicts using record versions
* Supports multiple conflict-resolution strategies
* Prevents duplicate synchronization operations
* Uses Redis for distributed synchronization locking
* Stores synchronization history
* Maintains audit logs
* Provides synchronization dashboard information

---

## 2. Technology Stack

| Technology        | Purpose                                              |
| ----------------- | ---------------------------------------------------- |
| Python 3.12       | Backend programming language                         |
| FastAPI           | REST API framework                                   |
| Uvicorn           | ASGI application server                              |
| SQLAlchemy        | ORM and database interaction                         |
| MySQL 8.0         | Primary database                                     |
| Alembic           | Database migrations                                  |
| Redis             | Distributed locking and synchronization coordination |
| Pydantic          | Request/response validation                          |
| Pydantic Settings | Environment configuration                            |
| JWT               | Authentication                                       |
| pwdlib + Argon2   | Password hashing                                     |
| PyMySQL           | MySQL database driver                                |
| Docker            | Containerized development environment                |
| Docker Compose    | Multi-container application setup                    |
| Pytest            | Testing                                              |

---

## 3. Architecture

The backend follows a layered architecture:

```text
Client
  │
  ▼
FastAPI Router
  │
  ▼
Service Layer
  │
  ▼
Repository Layer
  │
  ▼
MySQL
```

Redis is used where synchronization coordination is required:

```text
                    ┌─────────────┐
                    │   FastAPI   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Service   │
                    │    Layer    │
                    └──────┬──────┘
                           │
             ┌─────────────┴─────────────┐
             │                           │
      ┌──────▼──────┐             ┌──────▼──────┐
      │    MySQL    │             │    Redis    │
      │ Source of   │             │ Sync Locks  │
      │    Truth    │             │             │
      └─────────────┘             └─────────────┘
```

### MySQL

MySQL is the **source of truth** for application data.

### Redis

Redis is used for synchronization coordination and distributed locking.

Redis is **not** the primary storage for application records.

---

## 4. Main Features

### Authentication

* User registration
* User login
* JWT access tokens
* Current-user authentication
* Active/inactive account validation
* Password hashing using Argon2

### Role-Based Access Control

The system currently supports:

* `Admin`
* `User`

Administrators can manage users and access administrative functionality.

### User Management

Administrators can:

* Create users
* View users
* Search users
* Filter users by role
* Filter users by active status
* View individual users
* Update user information
* Change user roles
* Activate users
* Deactivate users
* Delete users

### Record Management

Users can manage their own records:

* Create record
* Get record
* List records
* Update record
* Soft delete record

Records use version numbers for optimistic concurrency control.

### Offline Synchronization

The synchronization system supports:

* CREATE operations
* UPDATE operations
* DELETE operations
* Unique operation IDs
* Operation status tracking
* Retry/attempt counting
* Duplicate operation prevention
* Synchronization history
* Failure tracking

### Conflict Detection

Conflicts are detected using record versions.

Supported strategies:

```text
SERVER_WINS
CLIENT_WINS
LAST_WRITE_WINS
MANUAL
```

### Redis Distributed Locking

Redis prevents the same synchronization operation from being processed concurrently by multiple backend processes.

If Redis becomes unavailable, synchronization can continue using MySQL-based processing.

### Audit Logging

Important system actions are recorded in the audit log.

Examples:

```text
USER_CREATED
USER_UPDATED
USER_ROLE_CHANGED
USER_ACTIVATED
USER_DEACTIVATED
USER_DELETED

RECORD_CREATED
RECORD_UPDATED
RECORD_DELETED

SYNC_OPERATION_CREATED
SYNC_OPERATION_PROCESSED
SYNC_OPERATION_FAILED
SYNC_OPERATION_CONFLICT

CONFLICT_CREATED
CONFLICT_RESOLVED
```

### Synchronization Dashboard

The dashboard provides information such as:

* Total records
* Total operations
* Pending operations
* Successful operations
* Failed operations
* Conflict operations
* Total conflicts
* Pending conflicts
* Resolved conflicts
* Last synchronization time
* Sync operation search/filtering
* Pagination
* Sorting

---

# 5. Project Structure

```text
backend/
│
├── app/
│   ├── core/
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   ├── logging.py
│   │   ├── redis.py
│   │   └── security.py
│   │
│   ├── constants/
│   │   └── audit.py
│   │
│   ├── dependencies/
│   │   └── auth.py
│   │
│   ├── db/
│   │   ├── base.py
│   │   ├── base_class.py
│   │   ├── seed.py
│   │   └── session.py
│   │
│   ├── models/
│   │   ├── role.py
│   │   ├── user.py
│   │   ├── record.py
│   │   ├── local_sync_operation.py
│   │   ├── sync_history.py
│   │   ├── conflict.py
│   │   └── audit_log.py
│   │
│   ├── repositories/
│   │   ├── user_repository.py
│   │   ├── record_repository.py
│   │   ├── local_sync_operation_repository.py
│   │   ├── sync_history_repository.py
│   │   ├── conflict_repository.py
│   │   └── audit_log_repository.py
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── common.py
│   │   ├── user.py
│   │   ├── record.py
│   │   ├── sync.py
│   │   ├── sync_history.py
│   │   ├── conflict.py
│   │   ├── dashboard.py
│   │   └── audit_log.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── record_service.py
│   │   ├── sync_service.py
│   │   ├── sync_history_service.py
│   │   ├── conflict_service.py
│   │   ├── dashboard_service.py
│   │   └── audit_log_service.py
│   │
│   ├── routers/
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── record.py
│   │   ├── sync.py
│   │   ├── sync_history.py
│   │   ├── conflict.py
│   │   ├── dashboard.py
│   │   └── audit_log.py
│   │
│   └── main.py
│
├── alembic/
│   ├── versions/
│   │   ├── 9a438fab4b54_create_initial_synchronization_tables.py
│   │   └── e41dd66ef543_make_record_id_nullable.py
│   ├── env.py
│   └── script.py.mako
│
├── .env
├── .gitignore
├── alembic.ini
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

# 6. Database Tables

The backend currently uses the following main tables:

```text
roles
users
records
local_sync_operations
sync_history
conflicts
audit_logs
```

### roles

Stores available user roles.

Example:

```text
Admin
User
```

### users

Stores user accounts.

Important fields:

```text
id
first_name
last_name
email
hashed_password
is_active
role_id
created_at
updated_at
```

Passwords are stored as hashes, never as plain text.

### records

Stores application records.

Important fields:

```text
id
owner_id
data
version
is_deleted
created_at
updated_at
```

The `version` field is used for optimistic concurrency control.

### local_sync_operations

Stores synchronization operations received from clients.

Important fields:

```text
operation_id
record_id
user_id
operation_type
base_version
payload
status
attempt_count
error_message
```

### sync_history

Stores historical synchronization results.

Example statuses:

```text
SUCCESS
FAILED
CONFLICT
```

### conflicts

Stores detected synchronization conflicts.

Important information includes:

```text
record_id
user_id
client_version
server_version
client_data
server_data
resolution_strategy
resolution_status
resolution_notes
```

### audit_logs

Stores important system activity.

Important fields:

```text
user_id
action
entity_type
entity_id
details
created_at
updated_at
```

---

# 7. Requirements

Before running the project, install:

* Docker Desktop
* Git
* A REST API client such as Postman

The backend itself runs inside Docker, so Python does not need to be installed locally for normal Docker-based development.

---

# 8. Clone the Project

Clone the repository:

```bash
git clone <YOUR_REPOSITORY_URL>
```

Move into the backend directory:

```powershell
cd "C:\Projects\Offline Data Synchronization System\backend"
```

---

# 9. Environment Variables

Create a `.env` file in the backend directory.

Example:

```env
APP_NAME=Offline-First Data Synchronization System
APP_VERSION=1.0.0
DEBUG=True

MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_DATABASE=offline_sync_db
MYSQL_USER=sync_user
MYSQL_PASSWORD=yourpassword
MYSQL_ROOT_PASSWORD=yourpassword

DATABASE_URL=mysql+pymysql://sync_user:yourpassword@mysql:3306/offline_sync_db

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_CACHE_TTL=300
REDIS_URL=redis://redis:6379/0

JWT_SECRET_KEY=<CHANGE_THIS_TO_A_LONG_RANDOM_SECRET>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### Important

Do not commit the `.env` file to Git.

Add it to `.gitignore`:

```gitignore
.env
__pycache__/
*.pyc
.pytest_cache/
.coverage
```

For production, use a strong random JWT secret.

---

# 10. Docker Compose

The backend uses three containers:

```text
offline_sync_backend
offline_sync_mysql
offline_sync_redis
```

The architecture is:

```text
FastAPI
   │
   ├── MySQL
   │
   └── Redis
```

---

# 11. Build the Backend

From the backend directory:

```powershell
docker compose build
```

---

# 12. Start the Application

Start the containers:

```powershell
docker compose up -d
```

Check the containers:

```powershell
docker compose ps
```

Expected services:

```text
offline_sync_backend
offline_sync_mysql
offline_sync_redis
```

Check backend logs:

```powershell
docker compose logs backend
```

Follow the logs:

```powershell
docker compose logs -f backend
```

---

# 13. Check MySQL

Check MySQL status:

```powershell
docker compose ps mysql
```

The MySQL container should become:

```text
healthy
```

You can connect to MySQL using MySQL Workbench.

Typical connection details:

```text
Host: localhost
Port: 3307
Username: sync_user
Password: <MYSQL_PASSWORD>
Database: offline_sync_db
```

The internal Docker connection is:

```text
mysql:3306
```

The backend uses the internal Docker hostname rather than `localhost`.

---

# 14. Check Redis

Redis runs inside Docker.

The backend connects using:

```text
redis://redis:6379/0
```

You can check Redis logs:

```powershell
docker compose logs redis
```

---

# 15. Database Migrations

Alembic is used for database schema management.

Check the current migration:

```powershell
docker compose exec backend alembic current
```

Check migration history:

```powershell
docker compose exec backend alembic history
```

Run all pending migrations:

```powershell
docker compose exec backend alembic upgrade head
```

---

# 16. Creating a New Migration

After changing a SQLAlchemy model:

```powershell
docker compose exec backend alembic revision --autogenerate -m "describe your change"
```

Review the generated migration file before applying it.

Then:

```powershell
docker compose exec backend alembic upgrade head
```

---

# 17. Rolling Back a Migration

To roll back one migration:

```powershell
docker compose exec backend alembic downgrade -1
```

Check the current migration afterward:

```powershell
docker compose exec backend alembic current
```

Do not delete database volumes just to fix a migration problem.

---

# 18. Seed Roles

The project includes database seed functionality for the default roles.

The default roles are:

```text
Admin
User
```

Run the seed script using the project's configured seed mechanism after the database has been migrated.

---

# 19. Run the Backend

The backend runs using Uvicorn:

```text
uvicorn app.main:app
```

Inside Docker it listens on:

```text
0.0.0.0:8000
```

From the host machine:

```text
http://localhost:8000
```

---

# 20. Swagger API Documentation

FastAPI automatically provides Swagger UI.

Open:

```text
http://localhost:8000/docs
```

Swagger is the primary way to manually test the backend during development.

Alternative OpenAPI documentation:

```text
http://localhost:8000/redoc
```

---

# 21. Health Check

Endpoint:

```http
GET /health
```

Example:

```text
http://localhost:8000/health
```

Expected response:

```json
{
  "status": "healthy",
  "application": "Offline-First Data Synchronization System",
  "version": "1.0.0"
}
```

---

# 22. Authentication Flow

The basic authentication flow is:

```text
Register
   ↓
Login
   ↓
Receive JWT
   ↓
Send JWT in Authorization header
   ↓
Access protected endpoints
```

Authorization header:

```http
Authorization: Bearer <ACCESS_TOKEN>
```

---

# 23. Register

Endpoint:

```http
POST /auth/register
```

Example request:

```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "password": "password123"
}
```

The password is hashed before being stored in MySQL.

---

# 24. Login

Endpoint:

```http
POST /auth/login
```

Example:

```json
{
  "email": "john@example.com",
  "password": "password123"
}
```

The response contains an access token.

Example:

```json
{
  "access_token": "<JWT_TOKEN>",
  "token_type": "bearer"
}
```

Use this token for protected endpoints.

---

# 25. Check Current User

Endpoint:

```http
GET /auth/me
```

In Swagger:

1. Login
2. Copy the access token
3. Click **Authorize**
4. Enter the token
5. Call `/auth/me`

This endpoint is also useful for checking whether authentication and role information are working correctly.

---

# 26. User Management

User management endpoints use administrator authorization.

Base path:

```text
/users
```

Available operations include:

```http
POST   /users
GET    /users
GET    /users/{user_id}
PUT    /users/{user_id}
PATCH  /users/{user_id}/role
PATCH  /users/{user_id}/activate
PATCH  /users/{user_id}/deactivate
DELETE /users/{user_id}
```

Only authorized administrators can perform administrative user-management operations.

---

# 27. Record Management

Records belong to users.

A record contains:

```text
owner_id
data
version
is_deleted
```

The record version is important for synchronization.

Example record data:

```json
{
  "title": "Sample Record",
  "description": "Offline synchronization test"
}
```

Users only access records belonging to their account.

---

# 28. Offline Synchronization

The synchronization system uses a client-generated unique operation ID.

Example:

```text
operation_id:
550e8400-e29b-41d4-a716-446655440000
```

This prevents the same operation from being processed multiple times.

The synchronization flow is:

```text
Client works offline
       │
       ▼
Local operation created
       │
       ▼
Operation stored locally
       │
       ▼
Network becomes available
       │
       ▼
Client sends operation to backend
       │
       ▼
Backend validates operation
       │
       ▼
Redis synchronization lock
       │
       ▼
MySQL transaction
       │
       ├── Success
       │
       ├── Failure
       │
       └── Conflict
```

---

# 29. Synchronization Operation Types

The system supports:

```text
CREATE
UPDATE
DELETE
```

Each operation contains information such as:

```text
operation_id
record_id
operation_type
base_version
payload
```

---

# 30. Optimistic Concurrency Control

Each record has a version:

```text
version = 1
```

When the record is updated:

```text
version = version + 1
```

Example:

```text
Server record:

version = 3
```

Client sends:

```text
base_version = 3
```

The update can proceed.

If the server has:

```text
version = 4
```

but the client sends:

```text
base_version = 3
```

the backend detects a conflict.

---

# 31. Conflict Resolution

A conflict stores both versions of the data:

```text
Client Data
     │
     ├── Client Version
     │
     ▼
Conflict
     ▲
     │
     ├── Server Version
     │
     ▼
Server Data
```

Supported strategies:

### SERVER_WINS

The server version is selected.

### CLIENT_WINS

The client version is selected.

### LAST_WRITE_WINS

The version comparison determines which version is selected according to the current implementation.

### MANUAL

The user/application supplies the data that should become the resolved record.

---

# 32. Synchronization Status

A synchronization operation can have statuses such as:

```text
PENDING
PROCESSING
SUCCESS
FAILED
CONFLICT
```

These statuses describe the current processing state of an operation.

---

# 33. Sync History

`sync_history` stores historical synchronization results.

For example:

```text
SUCCESS
FAILED
CONFLICT
```

This is different from the current operation status.

For example:

```text
local_sync_operations
    status = FAILED
```

means the current operation is failed.

While:

```text
sync_history
    sync_status = FAILED
```

records that a failed synchronization event occurred.

---

# 34. Redis Distributed Lock

Redis is used to prevent concurrent processing of the same synchronization operation.

The lock uses a unique operation ID.

Conceptually:

```text
sync:operation:<operation_id>
```

Only one backend process should hold the lock for a particular operation at a time.

The lock also has a timeout to prevent a permanently held lock.

If Redis is unavailable, the synchronization system can continue with MySQL processing rather than treating Redis as the source of truth.

---

# 35. Audit Logging

Important system actions are stored in:

```text
audit_logs
```

Examples:

```text
USER_CREATED
USER_UPDATED
USER_ROLE_CHANGED
USER_ACTIVATED
USER_DEACTIVATED
USER_DELETED

RECORD_CREATED
RECORD_UPDATED
RECORD_DELETED

SYNC_OPERATION_CREATED
SYNC_OPERATION_PROCESSED
SYNC_OPERATION_FAILED
SYNC_OPERATION_CONFLICT

CONFLICT_CREATED
CONFLICT_RESOLVED
```

Audit logs can be used to understand what actions occurred in the system.

---

# 36. Audit Log API

Base path:

```text
/audit-logs
```

The system provides access to audit records according to the configured authorization rules.

Typical filtering capabilities include:

```text
action
entity_type
entity_id
from_date
to_date
page
page_size
sort_order
```

Administrative audit access requires administrator authorization.

---

# 37. Synchronization Dashboard

Base path:

```text
/dashboard
```

The dashboard provides synchronization statistics.

Example information:

```text
Total Records
Total Operations
Pending Operations
Successful Operations
Failed Operations
Conflict Operations
Total Conflicts
Pending Conflicts
Resolved Conflicts
Last Sync Time
```

Sync operations can also be searched, filtered, paginated, and sorted.

---

# 38. Error Handling

The backend uses centralized exception handling.

Common application exceptions include:

```text
BadRequestException
NotFoundException
UnauthorizedException
ForbiddenException
ConflictException
```

FastAPI validation errors are also handled centrally.

Database errors are handled through the application's database exception handler.

Unexpected errors return a generic internal-server-error response rather than exposing internal implementation details.

---

# 39. Security

The backend follows several security practices.

### Password hashing

Passwords are hashed using:

```text
pwdlib + Argon2
```

Plain-text passwords are not stored in the database.

### JWT

JWT tokens are used for authentication.

The token contains authentication-related information such as:

```text
user identity
role information
expiration
```

Synchronization state is not stored inside the JWT.

### Authorization

Protected endpoints verify:

```text
JWT
 ↓
User
 ↓
Active status
 ↓
Role permissions
```

### Environment variables

Database passwords and JWT secrets are stored in environment configuration rather than hard-coded in application source code.

---

# 40. Database Transactions

Database operations use SQLAlchemy transactions.

Typical successful flow:

```text
Create/Update
    ↓
Repository
    ↓
db.commit()
    ↓
db.refresh()
```

If an error occurs:

```text
Error
  ↓
db.rollback()
  ↓
Return error
```

This prevents partially completed database operations.

---

# 41. Docker Commands

### Start

```powershell
docker compose up -d
```

### Stop containers

```powershell
docker compose stop
```

### Start existing containers

```powershell
docker compose start
```

### View status

```powershell
docker compose ps
```

### Backend logs

```powershell
docker compose logs backend
```

### Follow backend logs

```powershell
docker compose logs -f backend
```

### MySQL logs

```powershell
docker compose logs mysql
```

### Redis logs

```powershell
docker compose logs redis
```

### Rebuild backend

```powershell
docker compose build backend
docker compose up -d
```

### Enter backend container

```powershell
docker compose exec backend bash
```

### Enter MySQL

```powershell
docker compose exec mysql mysql -u sync_user -p
```

---

# 42. Important Docker Data Safety

The MySQL database uses a Docker volume to persist data.

Do **not** use:

```powershell
docker compose down -v
```

unless you intentionally want to delete the project's Docker volumes and database data.

Normal stopping should use:

```powershell
docker compose stop
```

To remove containers without removing volumes:

```powershell
docker compose down
```

Then the database volume remains available for the next startup.

---

# 43. Rebuilding After Code Changes

For normal Python code changes, rebuild if the container image contains the source code from the build process:

```powershell
docker compose build backend
docker compose up -d
```

Then check:

```powershell
docker compose ps
```

and:

```powershell
docker compose logs backend
```

---

# 44. API Testing Workflow

The recommended development testing workflow is:

```text
1. Start Docker
        ↓
2. Check containers
        ↓
3. Run migrations
        ↓
4. Open Swagger
        ↓
5. Register/Login
        ↓
6. Authorize JWT
        ↓
7. Test protected APIs
        ↓
8. Verify MySQL data
        ↓
9. Verify Redis behavior when needed
```

Swagger:

```text
http://localhost:8000/docs
```

---

# 45. Recommended Testing Order

When manually testing the backend:

### Step 1 — Health

```http
GET /health
```

### Step 2 — Register

```http
POST /auth/register
```

### Step 3 — Login

```http
POST /auth/login
```

### Step 4 — Authorize

Use the returned JWT in Swagger.

### Step 5 — Current User

```http
GET /auth/me
```

### Step 6 — User Management

Test administrator functionality.

### Step 7 — Records

Create and modify records.

### Step 8 — Synchronization

Create and process synchronization operations.

### Step 9 — Conflicts

Create a version mismatch and verify conflict handling.

### Step 10 — Audit Logs

Verify that important actions create audit records.

### Step 11 — Dashboard

Verify synchronization statistics.

---

# 46. Running Tests

Pytest is included in the project requirements.

Run:

```powershell
docker compose exec backend pytest
```

For more detailed output:

```powershell
docker compose exec backend pytest -v
```

Testing will be expanded in the dedicated testing phase.

---

# 47. Development Workflow

Recommended workflow for new backend features:

```text
Requirement
    ↓
Model
    ↓
Migration
    ↓
Repository
    ↓
Schema
    ↓
Service
    ↓
Router
    ↓
Audit Logging
    ↓
Swagger Testing
    ↓
Database Verification
    ↓
Automated Tests
```

This keeps responsibilities separated between application layers.

---

# 48. Layer Responsibilities

## Router

Responsible for:

* HTTP endpoints
* Request parameters
* Authentication dependencies
* Calling services
* Returning responses

Routers should not contain business logic.

## Schema

Responsible for:

* Request validation
* Response serialization
* API data structures

## Service

Responsible for:

* Business logic
* Validation involving multiple entities
* Transactions
* Conflict handling
* Synchronization logic

## Repository

Responsible for:

* Database queries
* Creating records
* Updating records
* Deleting records
* Filtering and pagination

## Model

Responsible for:

* Database table structure
* SQLAlchemy relationships
* Column definitions

---

# 49. Current Development Phases

The backend has been developed incrementally.

```text
Phase 1   Project Setup
Phase 2   Authentication
Phase 3   User Management
Phase 4   Record Management
Phase 5   Offline Sync Operations
Phase 6   Sync History
Phase 7   Conflict Detection & Resolution
Phase 8   Synchronization Improvements
Phase 9   Dashboard
Phase 10  Redis Distributed Locking
Phase 11  Audit Logging
Phase 12  Testing & Validation
```

# 50. Profile Management

The backend provides profile-management functionality for authenticated users.

Users can manage their own:

```text
First name
Last name
Email
Password
```

Profile management is based on the currently authenticated user. The user cannot provide another user's ID to modify another account through the profile-management APIs.

Users cannot change their role through profile management.

Email changes use a simple update flow and do not require OTP verification.

Password changes require the appropriate password validation before updating the stored password.

The profile-management flow is:

```text
Authenticated User
        │
        ▼
   Profile API
        │
        ▼
 Current User from JWT
        │
        ▼
 Update Own Profile
```

Profile management is separate from administrative user management.

Administrators can manage users through the User Management APIs, while profile-management APIs are intended for a user to manage their own account information.

---

# 51. Frontend

The frontend has been implemented as part of the Offline-First Data Synchronization System.

The frontend uses:

```text
React
Vite
TypeScript
Material UI
Axios
React Router
IndexedDB
```

The frontend provides the user-facing application and supports the offline-first workflow.

### Frontend Responsibilities

The frontend handles:

```text
User Interface
Authentication
Profile Management
Record Management
Local Offline Storage
Offline Operation Queue
Network Availability Detection
Synchronization Requests
Conflict Handling
Dashboard
```

### Offline Storage

IndexedDB is used to store data locally in the browser.

When the application is offline, user changes can be stored locally instead of requiring an immediate request to the backend.

When connectivity is restored, pending operations can be synchronized with the backend.

The frontend communicates with the backend through REST APIs using Axios.

### Frontend Routing

React Router is used for application navigation and protected application routes.

Material UI is used for the user interface components and application layout.



# 52. Complete Project Flow

The completed system allows users to work with records even when the client temporarily has no internet connection.

The overall architecture is:


                         FRONTEND
                            │
                 ┌──────────┴──────────┐
                 │                     │
              ONLINE                 OFFLINE
                 │                     │
                 ▼                     ▼
           Backend API           IndexedDB
                 │                     │
                 │              Pending Operations
                 │                     │
                 │              Network Returns
                 │                     │
                 └──────────┬──────────┘
                            │
                            ▼
                     Synchronization
                            │
                            ▼
                    ┌───────────────┐
                    │    FastAPI    │
                    └───────┬───────┘
                            │
                 ┌──────────┴──────────┐
                 │                     │
                 ▼                     ▼
              MySQL                  Redis
          Source of Truth       Sync Coordination
                 │
                 ▼
           Audit Logging
                 │
                 ▼
          Sync History
                 │
                 ▼
             Conflicts
                 │
          ┌──────┴──────┐
          │             │
          ▼             ▼
       Resolve        Retry
       Conflict       Failed

### Online Flow

User
  │
  ▼
Frontend
  │
  ▼
FastAPI Backend
  │
  ▼
Service Layer
  │
  ▼
Repository Layer
  │
  ▼
MySQL


Redis is used for synchronization coordination and distributed locking where required.

### Offline Flow


User
  │
  ▼
Frontend
  │
  ▼
IndexedDB
  │
  ▼
Pending Sync Operations
  │
  │
  └──── Network unavailable
                 │
                 ▼
          Network restored
                 │
                 ▼
          Backend Sync API
                 │
       ┌─────────┼─────────┐
       │         │         │
       ▼         ▼         ▼
    Success    Failed    Conflict
       │         │         │
       ▼         ▼         ▼
     Sync      Retry     Resolve
    History    Later     Conflict


### Final System Architecture

The completed system consists of:


Frontend
   │
   │ REST API
   ▼
FastAPI Backend
   │
   ├── Authentication
   ├── Authorization / RBAC
   ├── Profile Management
   ├── User Management
   ├── Record Management
   ├── Offline Synchronization
   ├── Conflict Detection
   ├── Conflict Resolution
   ├── Sync History
   ├── Audit Logging
   └── Dashboard
          │
          ├──────────────► MySQL
          │                 Source of Truth
          │
          └──────────────► Redis
                            Synchronization Coordination

The backend acts as the central source of truth, while the frontend provides the offline-first experience through local IndexedDB storage and synchronization of pending changes when connectivity is restored.

