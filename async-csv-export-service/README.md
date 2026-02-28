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

## API Endpoints

- `POST /exports/csv`: Initiate a new export.
- `GET /exports/{id}/status`: Check progress.
- `GET /exports/{id}/download`: Download the file.
- `DELETE /exports/{id}`: Cancel a job.
- `GET /health`: Health status.

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
