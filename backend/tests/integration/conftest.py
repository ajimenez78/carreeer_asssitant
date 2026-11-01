from uuid import uuid4

import psycopg
import pytest
from psycopg import sql
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from career_assistant.config import Settings
from career_assistant.database import (
    database_engine,
    database_url,
    ensure_local_database,
    migrate_database,
)
from career_assistant.persistence import ensure_owner


@pytest.fixture(scope="session")
def database():
    # The creator rejects remote hosts before any connection or destructive action.
    url = database_url(Settings()).set(database=f"career_test_{uuid4().hex}")
    ensure_local_database(url)
    engine = database_engine(url)
    try:
        migrate_database(url)
        yield engine
    finally:
        engine.dispose()
        with psycopg.connect(
            url.set(drivername="postgresql", database="postgres").render_as_string(
                hide_password=False
            ),
            autocommit=True,
            connect_timeout=5,
        ) as connection:
            connection.execute(
                sql.SQL("DROP DATABASE {}").format(sql.Identifier(url.database))
            )


@pytest.fixture
def sessions(database):
    with database.begin() as connection:
        connection.execute(text("TRUNCATE owners, document_deletions CASCADE"))
    factory = sessionmaker(database, expire_on_commit=False)
    with factory.begin() as session:
        ensure_owner(session)
    return factory
