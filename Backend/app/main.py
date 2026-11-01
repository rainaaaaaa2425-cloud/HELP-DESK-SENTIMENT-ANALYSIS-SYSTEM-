import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection, db
from app.api.calls import router as calls_router
from app.api.dashboard import router as dashboard_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # MongoDB connection startup
    await connect_to_mongo()
    yield
    # MongoDB connection shutdown
    await close_mongo_connection()

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan
)

# Enable CORS for React local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes under /api
app.include_router(calls_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")

@app.get("/api/health")
async def health_check():
    db_connected = False
    try:
        if db.client:
            await db.client.admin.command('ping')
            db_connected = True
    except Exception:
        pass
        
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "database": "connected" if db_connected else "disconnected",
        "mock_mode": settings.USE_MOCK_AI
    }
