from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from app.config import settings

# pool_pre_ping + connect_timeout matter specifically because Neon's Free-tier
# compute scales to zero after 5 minutes idle -- without pre_ping, SQLAlchemy
# can hand out a pooled connection that went stale while the compute was
# suspended, and the app hangs indefinitely waiting on a dead socket instead
# of transparently reconnecting. connect_timeout bounds how long a *new*
# connection attempt (e.g. while the compute is waking back up, ~30-40s) can
# hang before failing with a clear error instead of hanging forever.
engine = create_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    connect_args={"connect_timeout": 10} if "sqlite" not in settings.database_url else {},
)


def init_db() -> None:
    """Dev convenience only — real schema changes go through Alembic
    migrations (alembic/versions/), never through create_all in anything
    that touches a real environment."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
