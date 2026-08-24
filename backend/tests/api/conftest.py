"""Shared API test fixtures: a throwaway SQLite DB per test, seeded with
the real FAIR indicators (routes that build a report query Indicator rows
from the DB, not from the adapter directly), and a TestClient wired to it
via FastAPI's dependency_overrides."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from app.adapters.fair.content import load_adapter_metadata, load_indicators
from app.db import get_session
from app.main import app


@pytest.fixture()
def db_engine(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(load_adapter_metadata())
        for indicator in load_indicators():
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
