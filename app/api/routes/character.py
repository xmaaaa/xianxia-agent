from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.character import Character
from app.schemas.character import CharacterCreate, CharacterRead, CharacterUpdate

router = APIRouter()


def _get_owned_character(db: Session, character_id: int, user_id: str) -> Character:
    row = db.get(Character, character_id)
    if row is None or row.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    return row


@router.post("/", response_model=CharacterRead, status_code=status.HTTP_201_CREATED)
def create_character(payload: CharacterCreate, db: Session = Depends(get_db)) -> Character:
    row = Character(
        user_id=payload.user_id,
        name=payload.name,
        sect=payload.sect,
        spirit_root=payload.spirit_root,
        realm=payload.realm,
        exp=payload.exp,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/{character_id}", response_model=CharacterRead)
def get_character(
    character_id: int,
    user_id: str = Query(..., min_length=1, max_length=128),
    db: Session = Depends(get_db),
) -> Character:
    return _get_owned_character(db, character_id, user_id)


@router.get("/", response_model=list[CharacterRead])
def list_characters(
    user_id: str = Query(..., min_length=1, max_length=128),
    db: Session = Depends(get_db),
) -> list[Character]:
    stmt = select(Character).where(Character.user_id == user_id).order_by(Character.id.desc())
    return list(db.scalars(stmt).all())


@router.patch("/{character_id}", response_model=CharacterRead)
def update_character(
    character_id: int,
    payload: CharacterUpdate,
    user_id: str = Query(..., min_length=1, max_length=128),
    db: Session = Depends(get_db),
) -> Character:
    row = _get_owned_character(db, character_id, user_id)
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_character(
    character_id: int,
    user_id: str = Query(..., min_length=1, max_length=128),
    db: Session = Depends(get_db),
) -> None:
    row = _get_owned_character(db, character_id, user_id)
    db.delete(row)
    db.commit()
