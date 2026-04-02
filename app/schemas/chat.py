from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=128)
    character_id: int = Field(..., ge=1)
    message: str = Field(..., min_length=1, max_length=8000)
    stream: bool = Field(default=False)


class ChatResponse(BaseModel):
    reply: str
    retrieved_context: str = ""
    current_intent: str = ""
