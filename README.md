# Async CSV Export Service

A high-performance, containerized service for exporting millions of database records to CSV files using asynchronous streaming and progress tracking.

## Architecture

- **FastAPI**: Asynchronous web framework for the API.
- **SQLAlchemy (Async)**: For memory-efficient database streaming using `stream()`.
- **PostgreSQL**: Primary data store with 10 million seeded user records.
- **Docker Compose**: Full orchestration with healthchecks and resource limits.

## Key Features

- **Large-Scale Export**: Handle 10M+ rows with constant memory footprint (< 150MB).
- **Real-time Progress**: Track job percentage and status via polling.
- **Advanced Networking**: Resumable downloads and on-the-fly Gzip compression.
- **Customizable Formatting**: Select columns, delimiters, and quote characters.
- **Graceful Cancellation**: Stop ongoing jobs and cleanup temporary files instantly.

## Quick Start

1. **Clone the repository.**
2. **Setup environment**:
   ```bash
   cp .env.example .env
   ```
3. **Launch with Docker**:
   ```bash
   docker-compose up --build -d
   ```
   _Note: The first run will take ~30-60 seconds to seed 10 million records._

## Local Development (VS Code)

To run the project locally without Docker (e.g., for debugging in VS Code):

1. **Prerequisites**: Ensure you have Python 3.11+ and PostgreSQL installed locally.
2. **Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. **Database**: If you are using the database from the Docker container, ensure it's running (`docker-compose up db -d`).
4. **Environment Setup**:
   - Rename `.env.example` to `.env`.
   - Set `DB_HOST=localhost` (if the DB is running locally or exposed via Docker port 5432).
5. **Run the App**:
   ```bash
   uvicorn app.main:app --reload --port 8080
   ```
6. **VS Code Debugging**:
   - Create a `.vscode/launch.json` file.
   - Use the "Python: FastAPI" template or point to `uvicorn` with `app.main:app`.

## API Endpoints

## Configuration

Settings are managed via environment variables in `.env`. Key parameters include database credentials and the `EXPORT_STORAGE_PATH` for temporary files.

## API Endpoints

POST /export/users
GET /export/status/{job_id}

## Architecture

- FastAPI
- PostgreSQL
- Redis
- Async Background Jobs
