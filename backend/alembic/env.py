from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from career_agent.applications import models as application_models  # noqa: F401
from career_agent.collector import models as collector_models  # noqa: F401
from career_agent.database import Base
from career_agent.evidence import models as evidence_models  # noqa: F401
from career_agent.generation import models as generation_models  # noqa: F401
from career_agent.jobs import models as job_models  # noqa: F401
from career_agent.materials import models as material_models  # noqa: F401
from career_agent.planning import models as planning_models  # noqa: F401
from career_agent.practice import models as practice_models  # noqa: F401
from career_agent.settings import get_settings
from career_agent.workspace import models as workspace_models  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
config.set_main_option("sqlalchemy.url", get_settings().database_url)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
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
