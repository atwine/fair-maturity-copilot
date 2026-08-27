"""Shared API test fixtures: a throwaway SQLite DB per test, seeded with
every registered adapter's real indicators (routes that build a report
query Indicator rows from the DB, not from the adapter directly), and a
TestClient wired to it via FastAPI's dependency_overrides."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from app.adapters.fair import content as fair_content
from app.adapters.harmonization import content as harmonization_content
from app.db import get_session
from app.main import app

# Kept in sync with scripts/seed_indicators.py's _CONTENT_MODULES -- every
# adapter's content needs to be present for any API test to exercise it.
_CONTENT_MODULES = [fair_content, harmonization_content]


@pytest.fixture()
def db_engine(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        for content_module in _CONTENT_MODULES:
            session.add(content_module.load_adapter_metadata())
            for indicator in content_module.load_indicators():
                session.add(indicator)
        session.commit()

    return engine


@pytest.fixture()
def client(db_engine):
    def _get_session_override():
        with Session(db_engine) as session:
            yield session

    app.dependency_overrides[get_session] = _get_session_override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
