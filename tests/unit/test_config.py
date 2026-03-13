from __future__ import annotations

import importlib
import os
from pathlib import Path

from sdd_cash_manager.core import config


def test_load_dotenv_populates_environment(tmp_path, monkeypatch):
    project_root = Path.cwd()
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "SDD_CASH_MANAGER_DATABASE_URL=sqlite:///./env.db",
                "SDD_CASH_MANAGER_SECURITY_ENABLED=true",
            ]
        )
    )
    monkeypatch.chdir(tmp_path)
    importlib.reload(config)
    try:
        settings = config.settings
        assert settings.database_url == "sqlite:///./env.db"
        assert settings.security_enabled
    finally:
        monkeypatch.chdir(project_root)
        env_file.unlink()
        importlib.reload(config)

def test_load_dotenv_no_env_file(tmp_path, monkeypatch):
    project_root = Path.cwd()
    monkeypatch.chdir(tmp_path)
    # Ensure no .env file exists
    if (tmp_path / ".env").exists():
        (tmp_path / ".env").unlink()

    # Reload config to ensure _load_dotenv runs without a file
    original_env = os.environ.copy()
    importlib.reload(config)
    try:
        # Assert that no new vars were added from a non-existent file
        assert os.environ == original_env
    finally:
        monkeypatch.chdir(project_root)
        importlib.reload(config) # Reload original config

def test_load_dotenv_empty_and_commented_lines(tmp_path, monkeypatch):
    project_root = Path.cwd()
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "",
                "# This is a comment",
                "    ",
                "KEY=VALUE_SHOULD_BE_LOADED"
            ]
        )
    )
    monkeypatch.chdir(tmp_path)
    original_env_keys = set(os.environ.keys())
    importlib.reload(config)
    try:
        assert os.environ.get("KEY") == "VALUE_SHOULD_BE_LOADED" # Check if the one valid line was loaded
        # Assert no other keys were added from empty/commented lines
        new_env_keys = set(os.environ.keys())
        assert len(new_env_keys - original_env_keys) == 1
    finally:
        monkeypatch.chdir(project_root)
        env_file.unlink()
        importlib.reload(config)

def test_load_dotenv_malformed_lines(tmp_path, monkeypatch):
    project_root = Path.cwd()
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "MALFORMED_LINE_NO_EQUALS",
                "=VALUE_NO_KEY",
                "  KEY_SPACE = VALUE_SPACE  " # This should still be parsed correctly
            ]
        )
    )
    monkeypatch.chdir(tmp_path)
    original_env_keys = set(os.environ.keys())
    importlib.reload(config)
    try:
        # Check for the correctly parsed line
        assert os.environ.get("KEY_SPACE") == "VALUE_SPACE"
        # Ensure malformed lines did not populate env
        new_env_keys = set(os.environ.keys())
        assert len(new_env_keys - original_env_keys) == 1
    finally:
        monkeypatch.chdir(project_root)
        env_file.unlink()
        importlib.reload(config)


def test_coerce_bool_various_inputs(monkeypatch):
    # Test with default value (raw is None)
    monkeypatch.delenv("TEST_BOOL_VAR", raising=False)
    assert config._coerce_bool("TEST_BOOL_VAR", True) is True
    assert config._coerce_bool("TEST_BOOL_VAR", False) is False

    # Test "false" values
    monkeypatch.setenv("TEST_BOOL_VAR", "0")
    assert config._coerce_bool("TEST_BOOL_VAR", True) is False
    monkeypatch.setenv("TEST_BOOL_VAR", "false")
    assert config._coerce_bool("TEST_BOOL_VAR", True) is False
    monkeypatch.setenv("TEST_BOOL_VAR", "no")
    assert config._coerce_bool("TEST_BOOL_VAR", True) is False
    monkeypatch.setenv("TEST_BOOL_VAR", "off")
    assert config._coerce_bool("TEST_BOOL_VAR", True) is False

    # Test "true" values (already covered, but for completeness)
    monkeypatch.setenv("TEST_BOOL_VAR", "1")
    assert config._coerce_bool("TEST_BOOL_VAR", False) is True
    monkeypatch.setenv("TEST_BOOL_VAR", "true")
    assert config._coerce_bool("TEST_BOOL_VAR", False) is True
    monkeypatch.setenv("TEST_BOOL_VAR", "yes")
    assert config._coerce_bool("TEST_BOOL_VAR", False) is True
    monkeypatch.setenv("TEST_BOOL_VAR", "on")
    assert config._coerce_bool("TEST_BOOL_VAR", False) is True

    # Test arbitrary string (should return False as per current logic)
    monkeypatch.setenv("TEST_BOOL_VAR", "arbitrary_string")
    assert config._coerce_bool("TEST_BOOL_VAR", True) is False
