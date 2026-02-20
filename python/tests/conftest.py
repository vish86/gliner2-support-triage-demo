"""
Pytest fixtures: load app, test client, golden tickets.
Run from repo root or python/: pytest python/tests -v
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Import app after path setup so server can load .env from project root
import sys
_server_dir = Path(__file__).resolve().parent.parent
if str(_server_dir) not in sys.path:
    sys.path.insert(0, str(_server_dir))

from server import app

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
GOLDEN_TICKETS_PATH = FIXTURES_DIR / "golden_tickets.json"


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


@pytest.fixture(scope="session")
def golden_tickets():
    with open(GOLDEN_TICKETS_PATH) as f:
        return json.load(f)


# Thresholds to run tests over (user requested multiple)
THRESHOLDS = [0.5, 0.6, 0.7, 0.75]


def pytest_sessionfinish(session, exitstatus):
    """Write metrics results to file for the report generator."""
    try:
        from tests.test_triage import METRICS_RESULTS
        out_path = Path(__file__).resolve().parent / ".metrics_results.json"
        with open(out_path, "w") as f:
            json.dump(METRICS_RESULTS, f, indent=2)
    except Exception:
        pass
