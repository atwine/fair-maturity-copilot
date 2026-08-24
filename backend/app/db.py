from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from app.config import settings

engine = create_engine(settings.database_url, echo=False)


def init_db() -> None:
    """Dev convenience only — real schema changes go through Alembic
    migrations (alembic/versions/), never through create_all in anything
    that touches a real environment."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
