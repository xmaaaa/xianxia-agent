from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    sect: Mapped[str] = mapped_column(String(128), nullable=False)
    spirit_root: Mapped[str] = mapped_column(String(256), nullable=False)
    realm: Mapped[str] = mapped_column(String(64), nullable=False, default="炼气初期")
    exp: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    location: Mapped[str] = mapped_column(String(128), nullable=False, default="青云镇")
    inventory: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    event_log: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
