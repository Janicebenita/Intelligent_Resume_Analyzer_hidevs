"""Shared synthetic fixtures; no private candidate data."""

from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.demo import DEMO_RESUME, demo_job
from app.main import create_app
from app.service import analyze


@pytest.fixture
def report():
    return analyze(DEMO_RESUME, demo_job(), date(2025, 1, 1))


@pytest.fixture
def client():
    with TestClient(create_app(), raise_server_exceptions=False) as instance:
        yield instance
