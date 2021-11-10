import os
from typing import Dict, Generator
from unittest.mock import patch

import pytest


@pytest.fixture(name="environment_dict")
def fixture_environment_dict() -> Generator[Dict[str, str], None, None]:
    yield {
        "DEBUG": True,
        # Add here more project configuration settings from
        # `user_management.core.config.settings` module, to be used
        # in your unit tests.
    }


@pytest.fixture(autouse=True)
def mock_settings_env(environment_dict) -> Generator[None, None, None]:
    """
    Pydantic `BaseSettings` class will use environment variables **over `.env` file defined ones**
    when they are available.
    This fixture can be used to override settings in tests, when needed.
    """
    with patch.dict(os.environ, environment_dict):
        yield
