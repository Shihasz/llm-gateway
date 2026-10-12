import os
from collections.abc import Iterator

import fakeredis
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401  (registers tables on Base)
from app.core import cache, ratelimit
from app.core.db import Base, get_db
from tests.clock import FakeClock

# Disable the OpenTelemetry SDK so tests never try to export spans to a collector.
os.environ.setdefault("OTEL_SDK_DISABLED", "true")


@pytest.fixture
def fake_redis(monkeypatch: pytest.MonkeyPatch) -> fakeredis.FakeRedis:
    # A fresh FakeServer per test keeps state from leaking between tests.
    client = fakeredis.FakeRedis(server=fakeredis.FakeServer(), decode_responses=True)
    monkeypatch.setattr(cache, "_client", client)
    return client


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> FakeClock:
    fake = FakeClock()
    monkeypatch.setattr(ratelimit, "time", fake)
    return fake


@pytest.fixture
def db_engine() -> Iterator[Engine]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def client(fake_redis: fakeredis.FakeRedis, db_engine: Engine) -> Iterator[TestClient]:
    # Imported here so the OTEL env var above is set before the app (and tracing) loads.
    from app.main import app

    session_factory = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)

    def override_get_db() -> Iterator[Session]:
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    # Not used as a context manager on purpose: that would run the startup hook
    # and try to create tables in the real database.
    yield TestClient(app)
    app.dependency_overrides.clear()
