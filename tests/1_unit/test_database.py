# tests/unit/test_database.py

from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine

# --- Corrected Imports ---
# Removed 'src.' prefix
from sdd_cash_manager import database

# --- Fixture to patch global SQLAlchemy objects ---

@pytest.fixture(autouse=True) # autouse=True makes this fixture run for every test in this file
def patch_database_globals():
    """
    Patches global SQLAlchemy objects in database.py for testing purposes.
    It sets up an in-memory SQLite database for `create_tables` tests
    and mocks `SessionLocal` for `get_db` tests.
    Restores original objects after tests are run.
    """
    # Store original objects to restore them later
    original_engine = database.engine
    original_SessionLocal = database.SessionLocal
    original_DATABASE_URL = database.DATABASE_URL
    original_Base_metadata = database.Base.metadata

    # --- Setup for get_db tests ---
    # Create a mock session instance that will be returned by SessionLocal()
    mock_session_instance = MagicMock()
    # Ensure the mock session instance has a close method, which get_db calls
    mock_session_instance.close = MagicMock()

    # Create a mock sessionmaker that, when called, returns our mock session instance
    mock_session_factory = MagicMock()
    mock_session_factory.return_value = mock_session_instance

    # Replace the global SessionLocal in the database module with our mock factory
    database.SessionLocal = mock_session_factory

    # --- Setup for create_tables tests ---
    # Use an in-memory SQLite database for fast and isolated testing
    test_db_url = "sqlite:///:memory:"

    # Replace the global DATABASE_URL and engine with those for the in-memory DB
    database.DATABASE_URL = test_db_url
    # Create a new engine instance using the in-memory URL
    database.engine = create_engine(test_db_url)

    # Mock Base.metadata.create_all to verify it's called without actually creating tables
    mock_metadata = MagicMock()
    mock_metadata.create_all = MagicMock()
    # Replace the actual Base.metadata with our mock
    database.Base.metadata = mock_metadata

    # Yield control to the test function.
    # We yield the mock session instance and mock metadata so tests can assert on them.
    yield mock_session_instance, mock_metadata

    # --- Teardown: Restore original objects ---
    # This ensures that subsequent tests or other parts of the application
    # are not affected by the patching done in this fixture.
    database.SessionLocal = original_SessionLocal
    database.engine = original_engine
    database.DATABASE_URL = original_DATABASE_URL
    database.Base.metadata = original_Base_metadata

# --- Test Cases ---

def test_get_db_yields_session(patch_database_globals):
    """
    Tests that the `get_db` function correctly yields a session object
    and that `SessionLocal` is called as expected.
    """
    # Unpack the mocks provided by the fixture
    mock_session_instance, _ = patch_database_globals

    # Call the get_db generator
    db_generator = database.get_db()

    # Get the first yielded item (the database session)
    db_session = next(db_generator)

    # Assert that the yielded session is our mocked session instance
    assert db_session is mock_session_instance

    # Assert that our mock `SessionLocal` (which is `mock_session_factory`)
    # was called exactly once to create the session.
    database.SessionLocal.assert_called_once()

def test_get_db_closes_session(patch_database_globals):
    """
    Tests that the database session yielded by `get_db` is properly closed
    when the generator is exhausted.
    """
    # Unpack the mocks provided by the fixture
    mock_session_instance, _ = patch_database_globals

    # Call the get_db generator
    db_generator = database.get_db()

    # Get the session
    _ = next(db_generator)

    # Exhaust the generator. Since `get_db` yields only once,
    # the next call should raise StopIteration, which triggers the `finally` block.
    with pytest.raises(StopIteration):
        next(db_generator)

    # Assert that the `close` method on the mock session instance was called exactly once.
    mock_session_instance.close.assert_called_once()

def test_create_tables_calls_metadata_create_all(patch_database_globals):
    """
    Tests that `create_tables` correctly calls `Base.metadata.create_all`
    with the engine bound to the in-memory SQLite database.
    """
    # Unpack the mocks provided by the fixture
    _, mock_metadata = patch_database_globals

    # Call the `create_tables` function. This function uses the patched global
    # `database.engine` and `database.Base.metadata`.
    database.create_tables()

    # Assert that the `create_all` method on our mocked `Base.metadata`
    # was called exactly once.
    # The `bind` argument should be the patched `database.engine` that points
    # to the in-memory SQLite database.
    mock_metadata.create_all.assert_called_once_with(bind=database.engine)
