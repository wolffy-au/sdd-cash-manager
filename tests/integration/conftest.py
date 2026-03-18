from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session


@pytest.fixture
def mock_db_session():
    mock_session = MagicMock(spec=Session)
    mock_session.commit.return_value = None
    mock_session.flush.return_value = None
    mock_session.refresh.return_value = None
    return mock_session
