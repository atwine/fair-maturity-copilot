"""Wires Alembic to this app's own settings/models instead of a hardcoded
connection string or a separately-maintained metadata import list -- the
same DATABASE_URL from .env that app/db.py uses, and SQLModel.metadata
(populated by importing app.engine.models, which declares every table)."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

from app.config import settings
from app.engine import models  # noqa: F401 -- registers every table on SQLModel.metadata

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# set_main_option stores this in a ConfigParser, which interpolates `%` on
# read by default -- a literal `%` anywhere in the URL (a URL-encoded
# character in a password or query param, which Neon-generated credentials
# can in principle contain) would raise InterpolationSyntaxError the next
# time this value is read, breaking every alembic invocation. `%%` is the
# escaped form ConfigParser expects.
config.set_main_option("sqlalchemy.url", settings.database_url.replace("%", "%%"))

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
