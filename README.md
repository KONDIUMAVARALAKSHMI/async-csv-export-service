# Async CSV Export Service

This is a service to export a lot of database rows (like 10 million) into CSV files. It uses FastAPI and streaming to keep memory usage low.

## Features
- Exports millions of rows without crashing (stays under 150MB RAM).
- You can check the progress of the export.
- Supports Gzip compression for faster downloads.
- You can pick which columns you want and change the delimiter.
- Can cancel jobs and it cleans up the temporary files.

## How to run it

1. **Setup environment**:
   ```bash
   cp .env.example .env
   ```
2. **Run with Docker**:
   ```bash
   docker-compose up --build -d
   ```
   *The first time it runs, it seeds 10 million records so it takes about a minute.*

## Running for local dev (VS Code)

If you want to debug or run it without Docker:
1. Setup a virtual env:
   ```bash
   python -m venv venv
   source venv/bin/activate # or venv\Scripts\activate on windows
   pip install -r requirements.txt
   ```
2. Make sure the database is running (you can just run the DB from docker: `docker-compose up db -d`).
3. Update `.env` to use `localhost` for `DB_HOST`.
4. Run with uvicorn:
   ```bash
   uvicorn app.main:app --reload --port 8080
   ```

## API

- `POST /exports/csv` - Start a new export.
- `GET /exports/{job_id}/status` - Check how much is done.
- `GET /exports/{job_id}/download` - Download the file.
- `DELETE /exports/{job_id}` - Stop the export.

## Tech stack
- FastAPI
- SQLAlchemy (Async)
- PostgreSQL
- Docker

# Final submission ready