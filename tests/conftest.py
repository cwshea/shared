import os
import tempfile

import pytest

from app import create_app


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp()
    application = create_app({"DATABASE": db_path, "TESTING": True})

    yield application

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def sample_table(client):
    """Create a sample 'customers' table and return its response."""
    resp = client.post("/tables", json={
        "name": "customers",
        "columns": [
            {"name": "name", "type": "string"},
            {"name": "age", "type": "number"},
            {"name": "active", "type": "boolean"},
        ],
    })
    return resp.get_json()
