from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.models.character import Character


def load_character_profile(db: Session, character_id: int) -> Optional[str]:
    row = db.get(Character, character_id)
    if row is None:
        return None
    return (
        f"道号：{row.name}\n"
        f"所属门派：{row.sect}\n"
        f"灵根：{row.spirit_root}\n"
        f"当前境界：{row.realm}\n"
        f"修为值：{row.exp}"
    )
