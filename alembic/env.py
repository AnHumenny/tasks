import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))  # абсолютный путь всегда в самом верху до остальных импортов
from logging.config import fileConfig
from sqlalchemy import engine_from_config, QueuePool
from alembic import context
from shemas.database import DTutor
import os
from dotenv import load_dotenv
load_dotenv()

config = context.config

fileConfig(config.config_file_name)

config.set_main_option('sqlalchemy.url',
                       f'postgresql://{os.getenv("DB_USER")}:{os.getenv("DB_PASSWORD")}@{os.getenv("DB_HOST")}'
                       f':{os.getenv("DB_PORT")}/{os.getenv("DB_NAME")}')

target_metadata = DTutor.metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=QueuePool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()