# Cat Spy API

A FastAPI-based application build for Spy Cat Agency for managing cats and their missions with admin capabilities.

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
- Make copy of .env.exemple file, rename it to `.env` and fill it with your credentials.


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

- **GET /cats/me** - Get current cat's profile information

- **PUT /cats/target/complete/{target_id}** - Mark a target as completed

- **POST /cats/target/{target_id}** - Create a note for a specific target

- **GET /cats/notes** - Get all notes for the current cat

- **PUT /cats/note/{note_id}** - Update a specific note

#### Admin Endpoints (`/admin`)

**Cat Management:**

- **GET /admin/cats** - Get all cats in the system (Admin access required)

- **GET /admin/cats/name** - Get cats by name search (Admin access required)

- **GET /admin/cats/{cat_id}** - Get a cat by its ID (Admin access required)

- **PUT /admin/cats/update/{cat_id}** - Update a cat's salary (Admin access required)

- **DELETE /admin/cats/delete/{cat_id}** - Delete a cat by its ID (Admin access required)

**Mission Management:**

- **POST /admin/mission/create** - Create a new mission (Admin access required)

- **GET /admin/missions** - Get all missions in the system (Admin access required)

- **GET /admin/mission/{mission_id}** - Get a mission by its ID (Admin access required)

- **PUT /admin/mission/complete/{mission_id}** - Mark a mission as completed (Admin access required)

- **PUT /admin/mission/assign/{mission_id}** - Assign cats to a mission (Admin access required)

- **DELETE /admin/mission/delete/{mission_id}** - Delete a mission by its ID (Admin access required)

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