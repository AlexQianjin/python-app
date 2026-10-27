from asyncio import run
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from app.core.config import settings
from app.db.base import Base
from app.db.urls import async_database_url
from app.modules.ai.models import (  # noqa: F401
    Conversation,
    Document,
    MemoryJob,
    Message,
)
from app.modules.orders.models import CartItem, Order, OrderItem  # noqa: F401
from app.modules.products.models import Product  # noqa: F401
from app.modules.users.models import User  # noqa: F401

config = context.config
config.set_main_option(
    "sqlalchemy.url",
    async_database_url(settings.database_url)
    .render_as_string(hide_password=False)
    .replace("%", "%%"),
)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
external_tables = {
    "user",
    "session",
    "account",
    "verification",
    "jwks",
    "checkpoints",
    "checkpoint_blobs",
    "checkpoint_writes",
    "checkpoint_migrations",
}


def include_name(name: str | None, type_: str, _parent_names: dict) -> bool:
    return type_ != "table" or name not in external_tables


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        include_name=include_name,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        include_name=include_name,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run(run_migrations_online())
