from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CharacterCreate(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=128)
    name: str = Field(..., min_length=1, max_length=64)
    sect: str = Field(..., min_length=1, max_length=128)
    spirit_root: str = Field(..., min_length=1, max_length=256)
    realm: str = Field(default="炼气初期", max_length=64)
    exp: int = Field(default=0, ge=0)


class CharacterUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=64)
    sect: Optional[str] = Field(default=None, min_length=1, max_length=128)
    spirit_root: Optional[str] = Field(default=None, min_length=1, max_length=256)
    realm: Optional[str] = Field(default=None, max_length=64)
    exp: Optional[int] = Field(default=None, ge=0)


class CharacterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: str
    name: str
    sect: str
    spirit_root: str
    realm: str
    exp: int
    created_at: datetime
