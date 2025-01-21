idmovi# Movie Theater API Project

Welcome to the **Movie Theater API** project! This educational assignment is designed to help you develop and refine
your skills in creating robust web applications using FastAPI, SQLAlchemy, and Docker. Here's what the project offers:

- **Database setup**:
    - **PostgreSQL for development**: The application uses PostgreSQL as the main database for the development
      environment, configured via Docker Compose.
    - **SQLite for testing**: A lightweight SQLite database is utilized for testing, ensuring fast and isolated test
      execution.

- **Data population**:
    - The database can be automatically populated with movie data from a provided dataset. This includes associated
      entities such as genres, actors, languages, and countries, ensuring a rich and interconnected data structure.

- **Docker integration**:
    - The project is fully Dockerized, allowing seamless setup and execution of the application and its dependencies.
      Docker Compose simplifies the orchestration of services like the FastAPI application, PostgreSQL database, and any
      other required components.

- **Project structure**:
    - A well-organized and modular project structure is provided, including:
        - Database models and schemas for movies and related entities.
        - Routing logic for managing API endpoints.
        - Utility scripts for tasks like data seeding and database migrations.

### Project Structure Overview

The **Movie Theater API** project follows a modular and organized structure to simplify development, testing, and
deployment. Below is an overview of the main components:

Here is a visual representation of the project structure:

```
.
├── Dockerfile
├── README.md
├── alembic.ini
├── commands
│   ├── run_migration.sh
│   └── run_web_server_dev.sh
├── docker-compose.yml
├── init.sql
├── poetry.lock
├── pyproject.toml
├── pytest.ini
└── src
    ├── config
    │   ├── __init__.py
    │   └── settings.py
    ├── database
    │   ├── __init__.py
    │   ├── models.py
    │   ├── populate.py
    │   ├── session_postgresql.py
    │   ├── session_sqlite.py
    │   ├── migrations
    │   │   ├── README
    │   │   ├── env.py
    │   │   ├── script.py.mako
    │   │   └── versions
    │   │       ├── 3cd3b7913067_temp_migration.py
    │   │       └── dac4daee7459_initial_migration.py
    │   ├── seed_data
    │   │   ├── imdb_movies.csv
    │   │   └── test_data.csv
    │   └── source
    │       └── theater.db
    ├── main.py
    ├── routes
    │   ├── __init__.py
    │   └── movies.py
    ├── schemas
    │   ├── __init__.py
    │   └── movies.py
    └── tests
        ├── __init__.py
        ├── conftest.py
        └── test_integration
            ├── __init__.py
            └── test_movies.py
```

#### **Root Directory**

- **`Dockerfile`**: Defines the container configuration for the FastAPI application.
- **`docker-compose.yml`**: Orchestrates the application and its dependencies, such as PostgreSQL, in a development
  environment.
- **`README.md`**: Provides detailed documentation for the project.
- **`alembic.ini`**: Configuration file for Alembic, the tool used for database migrations.
- **`init.sql`**: Contains initial SQL commands for setting up the PostgreSQL database.
- **`poetry.lock`** and **`pyproject.toml`**: Manage dependencies and project configurations using Poetry.
- **`pytest.ini`**: Configuration file for pytest, specifying test settings and options.

#### **Commands**

- **`run_migration.sh`**: A script to execute database migrations.
- **`run_web_server_dev.sh`**: A script to start the FastAPI development server.

#### **Source Directory (`src`)**

The `src` directory contains the core application logic and is organized as follows:

1. **`config`**:
    - **`settings.py`**: Defines project configurations, including database connections for both development and testing
      environments.

2. **`database`**:
    - **`models.py`**: Contains SQLAlchemy models for movies and related entities.
    - **`populate.py`**: Provides logic for seeding the database with movie data from datasets.
    - **`session_postgresql.py`**: Manages the PostgreSQL database session for development.
    - **`session_sqlite.py`**: Manages the SQLite database session for testing.
    - **`migrations/`**: Houses Alembic migration scripts.
    - **`seed_data/`**: Contains datasets (`imdb_movies.csv` and `test_data.csv`) used for populating the database.
    - **`source/`**: Stores the SQLite database file (`theater.db`) for testing.

3. **`routes`**:
    - **`movies.py`**: Defines API endpoints related to movies, such as retrieving, creating, updating, and deleting
      movies.

4. **`schemas`**:
    - **`movies.py`**: Contains Pydantic models for request and response validation.

5. **`tests`**:
    - **`conftest.py`**: Defines shared fixtures for test configuration.
    - **`test_integration/`**: Contains integration tests for API endpoints.

6. **`main.py`**:
    - The entry point for the application, responsible for initializing and running the FastAPI app.

### Tip: Using `get_db` for Dependency Injection in FastAPI

The `get_db` function is a generator that provides a SQLAlchemy session for interacting with the database. This function
is particularly useful in FastAPI as it can be injected into route handlers using the `Depends` mechanism. Here’s how
you can use it effectively:

```python
from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session
from database import get_db  # Import the get_db generator

router = APIRouter()


@router.get("/example")
def example_route(db: Session = Depends(get_db)):
# Use the db session here to interact with the database
```

#### Key Points:

- The `Depends` function simplifies injecting dependencies like the database session into your route handlers.
- The `get_db` function ensures proper session handling: the session is created before the route logic executes and is
  closed automatically afterward.
- This approach promotes cleaner, more testable code by separating dependency setup from business logic.

You can use this pattern across your application for any routes that need database access.

### Services Overview

The project is configured with the following services in the `docker-compose.yml` file. These services collectively
support the development, testing, and deployment of the Movie Theater API:

#### **1. Database Service (`db`)**

- **Image**: `postgres:latest`
- **Purpose**: Acts as the primary database for the project, running a PostgreSQL instance.
- **Configuration**:
    - Loads initial SQL setup from `init.sql`.
    - Stores persistent data using a named Docker volume `postgres_theater_data`.
    - Exposes PostgreSQL on port `5432`.
- **Health Check**: Ensures the database is ready by using the `pg_isready` command.
- **Network**: Attached to `theater_network`.

#### **2. pgAdmin Service (`pgadmin`)**

- **Image**: `dpage/pgadmin4`
- **Purpose**: Provides a web-based interface for managing and monitoring the PostgreSQL database.
- **Configuration**:
    - Exposes pgAdmin on port `3333`.
    - Stores pgAdmin data in the `pgadmin_theater_data` volume.
- **Dependency**: Starts only after the `db` service is healthy.
- **Network**: Attached to `theater_network`.

#### **3. Backend Service (`web`)**

- **Build Context**: Builds the FastAPI application from the local directory (`.`).
- **Purpose**: Runs the FastAPI application, serving the Movie Theater API backend.
- **Configuration**:
    - Exposes the backend on port `8000`.
    - Uses the `run_web_server_dev.sh` script to start the development server.
    - Watches for file changes in the `src` directory using `WATCHFILES_FORCE_POLLING=true`.
    - Mounts the `src` directory to `/usr/src/fastapi` inside the container for live development.
- **Dependency**: Starts only after the `db` service is healthy.
- **Network**: Attached to `theater_network`.

#### **4. Database Migrator Service (`migrator`)**

- **Build Context**: Shares the same build context as the backend service.
- **Purpose**: Runs database migrations using Alembic to ensure the schema is up-to-date.
- **Configuration**:
    - Executes the `run_migration.sh` script to apply migrations.
    - Uses the `src` directory as the source for migration scripts.
- **Dependency**: Starts only after the `db` service is healthy.
- **Network**: Attached to `theater_network`.

### Volumes

- **`postgres_theater_data`**:
    - Stores persistent PostgreSQL data.
- **`pgadmin_theater_data`**:
    - Stores persistent data for pgAdmin.

### Networks

- **`theater_network`**:
    - A bridge network connecting all services, enabling inter-service communication.

### How to Run the Project

Follow these steps to set up and run the **Movie Theater API** project on your local machine.

#### **1. Clone the Repository**

Start by cloning the project repository from GitHub:

```bash
git clone <repository-url>
cd <repository-folder>
```

#### **2. Create and Activate a Virtual Environment**

It is recommended to use a virtual environment to isolate project dependencies:

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

#### **3. Install Dependencies with Poetry**

This project uses Poetry for dependency management. Install dependencies as follows:

```bash
# Install Poetry if not already installed
pip install poetry

# Install project dependencies
poetry install
```

#### **4. Create a `.env` File**

Create a `.env` file in the project root directory with the following variables. Customize the values as needed:

```env
# PostgreSQL
POSTGRES_DB=movies_db
POSTGRES_DB_PORT=5432
POSTGRES_USER=admin
POSTGRES_PASSWORD=some_password
POSTGRES_HOST=postgres_theater

# pgAdmin
PGADMIN_DEFAULT_EMAIL=admin@gmail.com
PGADMIN_DEFAULT_PASSWORD=admin
```

#### **5. Run the Project with Docker Compose**

The project is Dockerized for easy setup. To start all the required services (PostgreSQL, pgAdmin, FastAPI app, and
Alembic migrator), run:

```bash
docker-compose up --build
```

**Note**: On the first run, the database will be populated with data from the dataset. This process may take some time,
so please be patient.

#### **6. Access the Services**

- **API**: The Movie Theater API will be available at `http://localhost:8000`.
- **pgAdmin**: The pgAdmin web interface will be available at `http://localhost:3333`. Use the credentials you defined
  in the `.env` file to log in.

#### **7. Verify Setup**

After all services are running, you can test the API by accessing the OpenAPI documentation:

```plaintext
http://localhost:8000/docs
```

### Models and Entities Overview

The project defines the following entities and relationships using SQLAlchemy. Each entity represents a table in the
database and maps to a specific domain concept in the Movie Theater API.

#### **1. MovieModel**

Represents a movie in the database.

- **Table Name**: `movies`
- **Fields**:
    - `id` (Primary Key): Unique identifier for each movie.
    - `name`: Name of the movie.
    - `date`: Release date of the movie.
    - `score`: Movie rating score (e.g., IMDb score).
    - `overview`: A short description or synopsis of the movie.
    - `status`: Production status of the movie (e.g., Released, In Production).
    - `budget`: The budget of the movie (stored as a decimal value).
    - `revenue`: The revenue generated by the movie.
    - `country_id`: Foreign key linking to the `countries` table.

- **Relationships**:
    - `country`: Links to the `CountryModel`.
    - `genres`: Many-to-many relationship with `GenreModel`.
    - `actors`: Many-to-many relationship with `ActorModel`.
    - `languages`: Many-to-many relationship with `LanguageModel`.

- **Constraints**:
    - Unique constraint on `name` and `date` to prevent duplicate entries.

#### **2. GenreModel**

Represents a genre (e.g., Action, Comedy).

- **Table Name**: `genres`
- **Fields**:
    - `id` (Primary Key): Unique identifier for each genre.
    - `name`: Name of the genre (e.g., Action, Drama).

- **Relationships**:
    - `movies`: Many-to-many relationship with `MovieModel`.

#### **3. ActorModel**

Represents an actor in the database.

- **Table Name**: `actors`
- **Fields**:
    - `id` (Primary Key): Unique identifier for each actor.
    - `name`: Name of the actor.

- **Relationships**:
    - `movies`: Many-to-many relationship with `MovieModel`.

#### **4. CountryModel**

Represents a country associated with a movie (e.g., production country).

- **Table Name**: `countries`
- **Fields**:
    - `id` (Primary Key): Unique identifier for each country.
    - `code`: ISO 3166-1 alpha-2 country code (e.g., US, FR).
    - `name`: Full name of the country.

- **Relationships**:
    - `movies`: One-to-many relationship with `MovieModel`.

#### **5. LanguageModel**

Represents a language spoken in a movie.

- **Table Name**: `languages`
- **Fields**:
    - `id` (Primary Key): Unique identifier for each language.
    - `name`: Name of the language (e.g., English, French).

- **Relationships**:
    - `movies`: Many-to-many relationship with `MovieModel`.

#### **6. Association Tables**

Used to establish many-to-many relationships between entities.

- **`MoviesGenresModel`**:
    - Links `movies` and `genres`.
    - Fields: `movie_id`, `genre_id`.

- **`ActorsMoviesModel`**:
    - Links `movies` and `actors`.
    - Fields: `movie_id`, `actor_id`.

- **`MoviesLanguagesModel`**:
    - Links `movies` and `languages`.
    - Fields: `movie_id`, `language_id`.

### Task Description: Extending the Cinema Application

In this assignment, you are tasked with continuing the development of the cinema application. Your objective is to
implement two endpoints in the `schemas/movies.py` and `routes/movies.py` files. The rest of the application, including
database models and utility functions, has already been provided.

### 1: Implement Movies List Endpoint

Your task is to implement an endpoint in the `routes/movies.py` file that retrieves a **paginated list of movies** from
the database. The required response structure is detailed below.


#### Endpoint Details

- **HTTP Method**: `GET`
- **Path**: `/movies/`


#### Query Parameters

- **`page`** (integer):
    - Specifies the page number to retrieve.
    - **Default**: `1`
    - **Constraints**: Must be greater than or equal to `1`.

- **`per_page`** (integer):
    - Specifies the number of items to display per page.
    - **Default**: `10`
    - **Constraints**: Must be between `1` and `20` (inclusive).


#### Response Structure

The endpoint should return the following JSON response:

```json
{
  "movies": [
    {
      "id": 9936,
      "name": "Avatar new",
      "date": "2022-12-15",
      "score": 78.0,
      "overview": "Set more than a decade after the events of the first film..."
    }
  ],
  "prev_page": null,
  "next_page": "/theater/movies/?page=2&per_page=1",
  "total_pages": 9934,
  "total_items": 9934
}
```

#### Behavior

1. **Sorting**: Movies must be sorted in descending order by their `id`.
2. **Pagination**:
    - The `page` and `per_page` parameters control pagination.
    - The `prev_page` and `next_page` fields should provide links to the previous and next pages, respectively, or
      `null` if no such page exists.
3. **Empty Results**:
    - If no movies are found for the specified page, the endpoint should return a `404 Not Found` error with the
      message: `"No movies found."`

#### HTTP Responses

- **200 OK**: Successfully retrieved a paginated list of movies.
- **404 Not Found**: No movies found for the specified page.

This task requires you to implement both the endpoint logic in `routes/movies.py` and the response structure in
`schemas/movies.py`. Ensure that your implementation handles all edge cases, such as invalid query parameters or empty
results.

### 2: Implement Movie Creation Endpoint

Your task is to implement an endpoint in the `routes/movies.py` file that allows the creation of a new movie in the database. The required request and response structures are detailed below.


#### Endpoint Details

- **HTTP Method**: `POST`
- **Path**: `/movies/`


#### Request Body

The endpoint accepts a JSON object with the following fields:

```json
{
  "name": "string",
  "date": "date",
  "score": "float (0-100)",
  "overview": "string",
  "status": "string (Released | Post Production | In Production)",
  "budget": "float (>= 0)",
  "revenue": "float (>= 0)",
  "country": "string (ISO 3166-1 alpha-2 code)",
  "genres": ["string"],
  "actors": ["string"],
  "languages": ["string"]
}
```


#### Response Structure

The endpoint returns the created movie's details in the following format:

```json
{
  "id": "integer",
  "name": "string",
  "date": "date",
  "score": "float",
  "overview": "string",
  "status": "string",
  "budget": "float",
  "revenue": "float",
  "country": {
    "id": "integer",
    "code": "string",
    "name": "string or null"
  },
  "genres": [
    {
      "id": "integer",
      "name": "string"
    }
  ],
  "actors": [
    {
      "id": "integer",
      "name": "string"
    }
  ],
  "languages": [
    {
      "id": "integer",
      "name": "string"
    }
  ]
}
```


#### Behavior

1. **Validation**:
   - The `name` must not exceed 255 characters.
   - The `date` must not be more than one year in the future.
   - The `score` must be between 0 and 100.
   - The `budget` and `revenue` must be non-negative.

2. **Entity Linking**:
   - The endpoint automatically links or creates related entities (country, genres, actors, languages) if they do not already exist in the database.

3. **Duplicate Check**:
   - If a movie with the same `name` and `date` already exists, the endpoint returns a `409 Conflict` error with an appropriate message.
   - Message: "A movie with the name '{name}' and release date '{date}' already exists."
   
4. **Error Handling**:
   - Returns a `400 Bad Request` if the input data is invalid.


#### HTTP Responses

- **201 Created**: The movie was successfully created, and its details are returned in the response.
- **400 Bad Request**: The input data is invalid (e.g., missing required fields, invalid values).
- **409 Conflict**: A movie with the same `name` and `date` already exists.


#### Example Requests

1. **Request**:
   ```http
   POST /movies/
   Content-Type: application/json

   {
     "name": "Inception",
     "date": "2010-07-16",
     "score": 8.8,
     "overview": "A mind-bending thriller about dreams within dreams.",
     "status": "Released",
     "budget": 160000000.00,
     "revenue": 829895144.00,
     "country": "US",
     "genres": ["Action", "Sci-Fi"],
     "actors": ["Leonardo DiCaprio", "Joseph Gordon-Levitt"],
     "languages": ["English", "Japanese"]
   }
   ```

   **Response**:
   ```json
   {
     "id": 1,
     "name": "Inception",
     "date": "2010-07-16",
     "score": 8.8,
     "overview": "A mind-bending thriller about dreams within dreams.",
     "status": "Released",
     "budget": 160000000.00,
     "revenue": 829895144.00,
     "country": {
       "id": 1,
       "code": "US",
       "name": "United States"
     },
     "genres": [
       {
         "id": 1,
         "name": "Action"
       },
       {
         "id": 2,
         "name": "Sci-Fi"
       }
     ],
     "actors": [
       {
         "id": 1,
         "name": "Leonardo DiCaprio"
       },
       {
         "id": 2,
         "name": "Joseph Gordon-Levitt"
       }
     ],
     "languages": [
       {
         "id": 1,
         "name": "English"
       },
       {
         "id": 2,
         "name": "Japanese"
       }
     ]
   }
   ```

2. **Request**:
   ```http
   POST /movies/
   Content-Type: application/json

   {
     "name": "Inception",
     "date": "2010-07-16"
   }
   ```

   **Response**:
   ```json
   {
     "detail": "Invalid input data."
   }
   ```

### 3: Implement Movie Details Endpoint

Your task is to implement an endpoint in the `routes/movies.py` file that retrieves detailed information about a specific movie by its unique ID. The required response structure is detailed below.


#### Endpoint Details

- **HTTP Method**: `GET`
- **Path**: `/movies/{movie_id}/`


#### Path Parameters

- **`movie_id`** (integer):  
  The unique identifier of the movie to retrieve.


#### Response Structure

The endpoint should return the details of the movie in the following format:

```json
{
  "id": "integer",
  "name": "string",
  "date": "date",
  "score": "float",
  "overview": "string",
  "status": "string (Released | Post Production | In Production)",
  "budget": "float",
  "revenue": "float",
  "country": {
    "id": "integer",
    "code": "string",
    "name": "string or null"
  },
  "genres": [
    {
      "id": "integer",
      "name": "string"
    }
  ],
  "actors": [
    {
      "id": "integer",
      "name": "string"
    }
  ],
  "languages": [
    {
      "id": "integer",
      "name": "string"
    }
  ]
}
```


#### Behavior

1. **Validation**:
   - The `movie_id` must be a valid integer corresponding to an existing movie in the database.

2. **Entity Linking**:
   - The endpoint should include all related entities (country, genres, actors, languages) in the response.

3. **Error Handling**:
   - If the movie with the given `movie_id` is not found, the endpoint must return a `404 Not Found` error with the message: `"Movie with the given ID was not found."`


#### HTTP Responses

- **200 OK**: Successfully retrieved the movie details.
- **404 Not Found**: The movie with the specified ID does not exist.


#### Example Requests

1. **Request**:
   ```http
   GET /movies/1/
   ```

   **Response**:
   ```json
   {
     "id": 1,
     "name": "Inception",
     "date": "2010-07-16",
     "score": 8.8,
     "overview": "A mind-bending thriller about dreams within dreams.",
     "status": "Released",
     "budget": 160000000.00,
     "revenue": 829895144.00,
     "country": {
       "id": 1,
       "code": "US",
       "name": "United States"
     },
     "genres": [
       {
         "id": 1,
         "name": "Action"
       },
       {
         "id": 2,
         "name": "Sci-Fi"
       }
     ],
     "actors": [
       {
         "id": 1,
         "name": "Leonardo DiCaprio"
       },
       {
         "id": 2,
         "name": "Joseph Gordon-Levitt"
       }
     ],
     "languages": [
       {
         "id": 1,
         "name": "English"
       },
       {
         "id": 2,
         "name": "Japanese"
       }
     ]
   }
   ```

2. **Request**:
   ```http
   GET /movies/999/
   ```

   **Response**:
   ```json
   {
     "detail": "Movie with the given ID was not found."
   }
   ```

### 4: Implement Movie Deletion Endpoint

Your task is to implement an endpoint in the `routes/movies.py` file that deletes a specific movie by its unique ID. The required details for this endpoint are provided below.


#### Endpoint Details

- **HTTP Method**: `DELETE`
- **Path**: `/movies/{movie_id}/`


#### Path Parameters

- **`movie_id`** (integer):  
  The unique identifier of the movie to delete.


#### Response Structure

The endpoint does not return a response body on success. Instead, it responds with the following status codes:


#### HTTP Responses

- **204 No Content**: The movie was successfully deleted.
- **404 Not Found**: The movie with the specified ID does not exist.


#### Behavior

1. **Validation**:
   - The `movie_id` must correspond to an existing movie in the database.

2. **Error Handling**:
   - If the movie with the given `movie_id` does not exist, the endpoint must return a `404 Not Found` error with the message: `"Movie with the given ID was not found."`

3. **Successful Deletion**:
   - The movie is removed from the database, and the endpoint returns a `204 No Content` status.


#### Example Requests

1. **Request**:
   ```http
   DELETE /movies/1/
   ```

   **Response**:
   - **Status Code**: `204 No Content`

2. **Request**:
   ```http
   DELETE /movies/999/
   ```

   **Response**:
   ```json
   {
     "detail": "Movie with the given ID was not found."
   }
   ```

### 5: Implement Movie Update Endpoint

Your task is to implement an endpoint in the `routes/movies.py` file that updates the details of a specific movie by its unique ID. The details for this endpoint are provided below.


#### Endpoint Details

- **HTTP Method**: `PATCH`
- **Path**: `/movies/{movie_id}/`


#### Path Parameters

- **`movie_id`** (integer):  
  The unique identifier of the movie to update.


#### Request Body

The endpoint accepts a JSON object with the following optional fields. Any fields not provided will remain unchanged in the database:

```json
{
  "name": "string",
  "date": "date",
  "score": "float (0-100)",
  "overview": "string",
  "status": "string (Released | Post Production | In Production)",
  "budget": "float (>= 0)",
  "revenue": "float (>= 0)"
}
```


#### Response Structure

The endpoint returns a response indicating the result of the update operation:


#### HTTP Responses

- **200 OK**: Successfully updated the movie.
  ```json
  {
    "detail": "Movie updated successfully."
  }
  ```

- **404 Not Found**: The movie with the specified ID does not exist.
  ```json
  {
    "detail": "Movie with the given ID was not found."
  }
  ```

- **400 Bad Request**: The input data is invalid (e.g., violates constraints).
  ```json
  {
    "detail": "Invalid input data."
  }
  ```


#### Behavior

1. **Validation**:
   - Only the provided fields in the request body are updated.
   - The `score` must be between 0 and 100.
   - The `budget` and `revenue` must be non-negative.

2. **Entity Retrieval**:
   - The endpoint checks if a movie with the given `movie_id` exists. If not, it returns a `404 Not Found` error.

3. **Partial Update**:
   - Updates only the fields provided in the request body, leaving all other fields unchanged.

4. **Error Handling**:
   - If invalid input data is provided, the endpoint returns a `400 Bad Request` error.


#### Example Requests

1. **Request**:
   ```http
   PATCH /movies/1/
   Content-Type: application/json

   {
     "name": "Updated Movie Name",
     "score": 95.0
   }
   ```

   **Response**:
   ```json
   {
     "detail": "Movie updated successfully."
   }
   ```

2. **Request**:
   ```http
   PATCH /movies/999/
   Content-Type: application/json

   {
     "name": "Nonexistent Movie"
   }
   ```

   **Response**:
   ```json
   {
     "detail": "Movie with the given ID was not found."
   }
   ```

3. **Request**:
   ```http
   PATCH /movies/1/
   Content-Type: application/json

   {
     "score": 150.0
   }
   ```

   **Response**:
   ```json
   {
     "detail": "Invalid input data."
   }
   ```

---

### Tips and Guidance

If you’re unsure about the expected behavior or need clarification, **refer to the provided test suite**. Running the tests will:
- Show the expected logic and flow for each endpoint.
- Help you identify edge cases and handle errors correctly.
- Ensure your implementation aligns with the project's requirements.

To run the tests, use the following command in the project root directory:
```bash
pytest
```

The test results will indicate any discrepancies between your implementation and the expected behavior, providing clear guidance on how to fix them.
