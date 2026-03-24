# Load environment variables
from dotenv import load_dotenv

load_dotenv()

import os
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.exceptions import HTTPException as StarletteHTTPException


# Configure standard library logging to work with loguru
class InterceptHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        # 定义需要过滤的日志记录器名称
        self.filtered_loggers = {
            "logging",  # 避免日志系统自身的递归
            "urllib3",  # 过滤过于详细的HTTP客户端日志
            "charset_normalizer",  # 过滤字符集检测日志
            "websockets",  # 过滤WebSocket详细连接日志
        }

    def emit(self, record):
        # 跳过日志系统自身的调用
        if (
            record.name.startswith("logging")
            or "callHandlers" in record.funcName
            or record.name in self.filtered_loggers
        ):
            return

        # 跳过特定的重复消息
        if "= connection is OPEN" in record.getMessage():
            return

        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where the logged message originated
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


from api.auth import PasswordAuthMiddleware
from api.routers import (
    auth,
    chat,
    config,
    context,
    embedding,
    embedding_rebuild,
    episode_profiles,
    insights,
    models,
    notebooks,
    notes,
    podcasts,
    search,
    settings,
    source_chat,
    sources,
    speaker_profiles,
    transformations,
)
from api.routers import commands as commands_router
from open_notebook.database.async_migrate import AsyncMigrationManager


# Configure loguru logger
def setup_logging():
    """Configure logging based on environment variables."""
    log_level = os.getenv("LOGLEVEL", "INFO").upper()
    log_file = os.getenv("LOG_FILE", "")
    log_rotation = os.getenv("LOG_ROTATION", "10 MB")
    log_retention = os.getenv("LOG_RETENTION", "7 days")

    # Remove default handler
    logger.remove()

    # Add console handler
    logger.add(
        sink=sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
        backtrace=True,
        diagnose=True,
        enqueue=True,
    )

    # Add file handler if LOG_FILE is specified
    if log_file:
        logger.add(
            sink=log_file,
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation=log_rotation,
            retention=log_retention,
            compression="gz",
            enqueue=True,
            backtrace=True,
            diagnose=True,
        )
        logger.info(f"Logging to file: {log_file}")

    # Configure standard library logging interception
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Configure specific loggers for better coverage
    important_loggers = [
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "fastapi",
        "surrealdb",
        "open_notebook",
        "esperanto",
        "content_core",
        "podcast_creator",
        "langchain",
    ]

    # 设置重要logger的级别
    for logger_name in important_loggers:
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [InterceptHandler()]
        logging_logger.setLevel(getattr(logging, log_level, logging.INFO))
        logging_logger.propagate = False

    # 设置一些嘈杂logger的级别为WARNING或更高
    noisy_loggers = [
        "httpx",
        "httpcore",
        "asyncio",
        "websockets",
        "urllib3",
        "charset_normalizer",
    ]

    for logger_name in noisy_loggers:
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [InterceptHandler()]
        logging_logger.setLevel(logging.WARNING)  # 只记录WARNING及以上级别
        logging_logger.propagate = False


# Setup logging
setup_logging()

# Import commands to register them in the API process
try:
    logger.info("Commands imported in API process")
except Exception as e:
    logger.error(f"Failed to import commands in API process: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for the FastAPI application.
    Runs database migrations automatically on startup.
    """
    # Startup: Run database migrations
    logger.info("Starting API initialization...")

    try:
        migration_manager = AsyncMigrationManager()
        current_version = await migration_manager.get_current_version()
        logger.info(f"Current database version: {current_version}")

        if await migration_manager.needs_migration():
            logger.warning("Database migrations are pending. Running migrations...")
            await migration_manager.run_migration_up()
            new_version = await migration_manager.get_current_version()
            logger.success(
                f"Migrations completed successfully. Database is now at version {new_version}"
            )
        else:
            logger.info(
                "Database is already at the latest version. No migrations needed."
            )
    except Exception as e:
        logger.error(f"CRITICAL: Database migration failed: {str(e)}")
        logger.exception(e)
        # Fail fast - don't start the API with an outdated database schema
        raise RuntimeError(f"Failed to run database migrations: {str(e)}") from e

    logger.success("API initialization completed successfully")

    # Yield control to the application
    yield

    # Shutdown: cleanup if needed
    logger.info("API shutdown complete")


app = FastAPI(
    title="Open Notebook API",
    description="API for Open Notebook - Research Assistant",
    lifespan=lifespan,
)

# Add password authentication middleware first
# Exclude /api/auth/status and /api/config from authentication
app.add_middleware(
    PasswordAuthMiddleware,
    excluded_paths=[
        "/",
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/api/auth/status",
        "/api/config",
    ],
)

# Add CORS middleware last (so it processes first)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom exception handler to ensure CORS headers are included in error responses
# This helps when errors occur before the CORS middleware can process them
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Custom exception handler that ensures CORS headers are included in error responses.
    This is particularly important for 413 (Payload Too Large) errors during file uploads.

    Note: If a reverse proxy (nginx, traefik) returns 413 before the request reaches
    FastAPI, this handler won't be called. In that case, configure your reverse proxy
    to add CORS headers to error responses.
    """
    # Get the origin from the request
    origin = request.headers.get("origin", "*")

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={
            **(exc.headers or {}),
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )


# Include routers
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(config.router, prefix="/api", tags=["config"])
app.include_router(notebooks.router, prefix="/api", tags=["notebooks"])
app.include_router(search.router, prefix="/api", tags=["search"])
app.include_router(models.router, prefix="/api", tags=["models"])
app.include_router(transformations.router, prefix="/api", tags=["transformations"])
app.include_router(notes.router, prefix="/api", tags=["notes"])
app.include_router(embedding.router, prefix="/api", tags=["embedding"])
app.include_router(
    embedding_rebuild.router, prefix="/api/embeddings", tags=["embeddings"]
)
app.include_router(settings.router, prefix="/api", tags=["settings"])
app.include_router(context.router, prefix="/api", tags=["context"])
app.include_router(sources.router, prefix="/api", tags=["sources"])
app.include_router(insights.router, prefix="/api", tags=["insights"])
app.include_router(commands_router.router, prefix="/api", tags=["commands"])
app.include_router(podcasts.router, prefix="/api", tags=["podcasts"])
app.include_router(episode_profiles.router, prefix="/api", tags=["episode-profiles"])
app.include_router(speaker_profiles.router, prefix="/api", tags=["speaker-profiles"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(source_chat.router, prefix="/api", tags=["source-chat"])


@app.get("/")
async def root():
    return {"message": "Open Notebook API is running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
