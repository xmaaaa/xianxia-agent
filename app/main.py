import logging
from contextlib import asynccontextmanager

import redis
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.routes import character, chat
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import engine

setup_logging()
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(application: FastAPI):
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        logger.warning("PostgreSQL is unreachable — character APIs will fail until DB is up")

    try:
        r = redis.from_url(settings.redis_url)
        r.ping()
        r.close()
    except Exception:
        logger.warning("Redis is unreachable — session memory will fail until Redis is up")

    key = settings.openai_api_key
    if not key or len(key) < 10:
        logger.warning("OPENAI_API_KEY is not set — chat endpoints will return errors")

    yield
    engine.dispose()


app = FastAPI(
    title="Xianxia Agent API",
    description="修仙 RPG AI Agent — Phase 2d",
    version="0.3.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(redis.exceptions.ConnectionError)
async def redis_connection_error_handler(request: Request, exc: redis.exceptions.ConnectionError):
    logger.error("Redis unavailable: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "会话存储暂不可用，请稍后重试。"},
    )


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError):
    msg = str(exc)
    if "OPENAI_API_KEY" in msg:
        logger.error("OpenAI key missing: %s", msg)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": "语言模型未配置，请联系管理员。"},
        )
    logger.exception("RuntimeError on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"内部错误：{msg[:200]}"},
    )


@app.exception_handler(Exception)
async def catch_all_handler(request: Request, exc: Exception):
    logger.exception("%s on %s %s: %s", type(exc).__name__, request.method, request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"{type(exc).__name__}: {str(exc)[:200]}"},
    )


app.include_router(character.router, prefix="/api/v1/characters", tags=["characters"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
