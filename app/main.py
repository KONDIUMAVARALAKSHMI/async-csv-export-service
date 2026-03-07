from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

from app.database import engine, Base
from app.routes import router

# -------------------- Logging Configuration --------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------- Lifespan Context Manager --------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Database Initialization
    async with engine.begin() as conn:
        logger.info("Initializing database...")
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: (Optional cleanup)
    logger.info("Shutting down...")

# -------------------- App Initialization --------------------
# Main FastAPI application instance
app = FastAPI(
    title="Large-Scale CSV Export Service",
    lifespan=lifespan
)

# Health Check
@app.get("/health")
async def health():
    return {"status": "ok"}

# Include Routes
app.include_router(router)
