import logging
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import ask, health, playlists, search, videos
from ytrag.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("api.main")

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Verify backend services during startup without loading Whisper models."""
    logger.info("Initializing VidSage API serving dependencies...")
    try:
        settings.validate_for_answering()
        logger.info("Credentials validated. Vector database and Groq ready.")
    except Exception as e:
        logger.warning(f"Startup credential check warning: {e}")
    yield


# Initialize FastAPI application
app = FastAPI(
    title="VidSage API",
    description="AI-Powered YouTube Lecture Search & Revision Assistant Backend",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Configuration
# Allows requests from Vite development server and production frontends
allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "*",  # Permissive for development; can be restricted via environment variable
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log incoming HTTP request method, path, and processing duration."""
    start_time = time.time()
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        logger.info(
            f"{request.method} {request.url.path} completed with {response.status_code} in {process_time:.1f}ms"
        )
        return response
    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        logger.error(
            f"{request.method} {request.url.path} failed with error: {str(e)} in {process_time:.1f}ms"
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error. Please try again later."},
        )


# Register routers
app.include_router(health.router)
app.include_router(ask.router)
app.include_router(search.router)
app.include_router(videos.router)
app.include_router(playlists.router)


@app.get("/")
def root():
    """Root redirect / information endpoint."""
    return {
        "app": "VidSage API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }
