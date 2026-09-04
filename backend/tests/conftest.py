import shutil
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings  # noqa: E402


@pytest.fixture(autouse=True)
def _isolated_vector_store(tmp_path, monkeypatch):
    """Point the vector store at a throwaway temp directory for every test."""
    get_settings.cache_clear()
    monkeypatch.setenv("VECTOR_STORE_DIR", str(tmp_path / "vector_store"))
    yield
    get_settings.cache_clear()


@pytest.fixture
def fake_bedrock_client():
    """A stand-in for boto3's bedrock-runtime client, no real AWS calls made."""
    client = MagicMock()
    return client

