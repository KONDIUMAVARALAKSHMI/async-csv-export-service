import os
from dotenv import load_dotenv

# Search for .env in current and parent directories
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

def is_running_in_docker():
    """Check if the process is running inside a Docker container."""
    return os.path.exists('/.dockerenv') or os.environ.get('DOCKER_CONTAINER') == 'true'

class Settings:
    # Auto-detect defaults based on environment
    _default_host = "db" if is_running_in_docker() else "localhost"
    
    DB_USER = os.getenv("DB_USER", "exporter")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "secret")
    DB_HOST = os.getenv("DB_HOST", _default_host)
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "exports_db")

    @property
    def DATABASE_URL(self):
        # If DB_HOST is "db" but we are clearly NOT in docker, override to localhost
        host = self.DB_HOST
        if host == "db" and not is_running_in_docker():
            host = "localhost"

        return (
            f"postgresql+asyncpg://{self.DB_USER}:"
            f"{self.DB_PASSWORD}@{host}:"
            f"{self.DB_PORT}/{self.DB_NAME}"
        )

settings = Settings()