from pathlib import Path

from alembic import command
from alembic.config import Config

ROOT = Path(__file__).resolve().parent.parent


def _alembic_config(tmp_path: Path) -> Config:
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{tmp_path / 'migrations.db'}")
    return config


def test_migrations_are_in_sync_with_models(tmp_path: Path) -> None:
    config = _alembic_config(tmp_path)

    command.upgrade(config, "head")

    # Raises if the models contain changes that no migration covers.
    command.check(config)


def test_migrations_can_be_downgraded(tmp_path: Path) -> None:
    config = _alembic_config(tmp_path)

    command.upgrade(config, "head")
    command.downgrade(config, "base")
