# Cat Spy API

A FastAPI-based application build for Spy Cat Agency for managing cats and their missions with admin capabilities.
This system now includes Model Context Protocol (MCP) integration, currently enabling intelligent database interactions for streamlined cat and mission oversight with future expansion. 

## Prerequisites

Before running this project, ensure you have the following installed:

- **Docker** and **Docker Compose**
- **UV** - The project uses UV package manager. Please install it first:

  ```bash
  # Install UV (choose one method)
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # or via pip
  pip install uv
  ```
- Make copy of `.env.exemple` file, rename it to `.env` and fill it with your credentials.


## Quick Start

Follow these steps to get the project running:

1. **Initial setup** (build containers and install migrations):
   ```bash
   make dev
   ```

2. **Run the application**:
   ```bash
   make up
   ```

3. **Access the API documentation**:
   Open your browser and navigate to: http://localhost:8000/docs

## API Endpoints

Once the application is running, you can test all endpoints through the interactive Swagger documentation at `http://localhost:8000/docs`.

### Available Endpoints:

#### Authorization Endpoints (`/auth`)

- **POST /auth/signup** - Register a new cat account
  - Validates breed using external API
  - Checks for existing cat with the same name
  - Hashes password and creates new cat account

- **POST /auth/login** - Login to get access and refresh tokens
  - Verifies cat credentials
  - Generates JWT access and refresh tokens
  - Stores refresh token in the database

- **GET /auth/refresh_token** - Refresh access token using refresh token

- **POST /auth/forgot_password** - Initiate password reset process
  - Verifies cat exists with the provided email
  - Generates a password reset token
  - Sends reset link via email

- **POST /auth/reset_password/{token}** - Reset password using reset token

#### Cats Endpoints (`/cats`)

- **GET /me** - Get current cat's profile information

- **GET /missions** - Get all missions for current cat

- **PUT /target/{target_uuid}/assign** - Assign a target to the current cat

- GET /target/{target_uuid} - Get details of a specific target

- **GET /targets** - Get all targets assigned to the current cat

- **PUT /target/complete/{target_uuid}** - Mark a target as completed

- **POST /target-note/{target_uuid}** - Create a note for a specific target

- **GET /notes** - Get all notes for the current cat

- **PUT /note/{note_uuid}** - Update a specific note

#### Admin Endpoints (`/admin`)

**Cat Management:**

- **GET /cats** - Get all cats in the system (Admin access required)

- **GET /cats/name** - Get cats by name search (Admin access required)

- **GET /cats/{cat_uuid}** - Get a cat by its uuid (Admin access required)

- **PUT /cats/update/{cat_uuid}** - Update a cat's salary (Admin access required)

- **DELETE /cats/delete/{cat_uuid}** - Delete a cat by its uuid (Admin access required)

**Mission Management:**

- **POST /mission/create** - Create a new mission (Admin access required)

- **GET /missions** - Get all missions in the system (Admin access required)

- **GET /mission/{mission_uuid}** - Get a mission by its uuid (Admin access required)

- **PUT /mission/{mission_uuid}/complete** - Mark a mission as completed (Admin access required)

- **PUT /mission/{mission_uuid}/assign** - Assign cats to a mission (Admin access required)

- **DELETE /mission/delete/{mission_uuid}** - Delete a mission by its uuid (Admin access required)

## Development

- Use `make dev` to set up the development environment
- Use `make up` to start the running containers
- Use `make down` to stop the containers

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. Most endpoints require either:
- Regular user authentication (for `/cats` endpoints)
- Admin privileges (for `/admin` endpoints)

To access protected endpoints:
1. First, register/signup a new cat account
2. Login to get access and refresh tokens
3. Use the access token in the Authorization header: `Bearer <access_token>`

## Environment Variables

The project uses environment variables for configuration. Make sure to set up the required environment variables before running the application. 

## Testing

Run test for all project (in Docker bash):
```
uv run pytest
```
Run test for specific file::endpoint::case:
```
uv run pytest tests/integration/test_admin.py::TestUpdateCatSalary::test_update_cat_salary_success
```

Check test coverage for all project by running:
```
pytest --cov=src tests/ --cov-report=term-missing
```

---

For more detailed information about specific endpoints, request/response schemas, and their usage, please refer to the interactive documentation at `http://localhost:8000/docs`.