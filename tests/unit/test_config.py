from __future__ import annotations

import importlib
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
