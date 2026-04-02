from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import character, chat
from app.core.config import settings

app = FastAPI(
    title="Xianxia Agent API",
    description="修仙 RPG AI Agent — Phase 1",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(character.router, prefix="/api/v1/characters", tags=["characters"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
