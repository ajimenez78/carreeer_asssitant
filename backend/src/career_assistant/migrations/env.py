from alembic import context

from career_assistant.config import Settings
from career_assistant.database import database_engine, database_url
from career_assistant.models import Base


def run(connection):
    context.configure(connection=connection, target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    context.configure(
        url=database_url(Settings(), direct=True),
        target_metadata=Base.metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()
elif connection := context.config.attributes.get("connection"):
    run(connection)
else:
    engine = database_engine(database_url(Settings(), direct=True))
    try:
        with engine.connect() as connection:
            run(connection)
    finally:
        engine.dispose()
