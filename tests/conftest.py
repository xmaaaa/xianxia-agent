from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.session import get_db
from app.main import app
from app.models.base import Base


@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session: Session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def mock_redis():
    fake_store: dict[str, str] = {}

    mock_r = MagicMock()
    mock_r.get.side_effect = lambda k: fake_store.get(k)
    mock_r.setex.side_effect = lambda k, _ttl, v: fake_store.__setitem__(k, v)
    mock_r.delete.side_effect = lambda k: fake_store.pop(k, None)

    with patch("app.memory.short_term._client", return_value=mock_r):
        yield mock_r


@pytest.fixture()
def mock_openai():
    fake_response = MagicMock()
    fake_response.content = "本座已知晓。"

    async def _fake_astream(*_args, **_kwargs):
        yield fake_response

    with patch("app.agent.nodes._llm") as mock_llm:
        instance = MagicMock()
        instance.invoke.return_value = fake_response
        instance.astream = _fake_astream
        instance.bind.return_value = instance
        mock_llm.return_value = instance
        yield instance
