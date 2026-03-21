from __future__ import annotations

import runpy
import sys

import sdd_cash_manager.database as database


def test_main_startup_invokes_uvicorn_and_create_tables(monkeypatch):
    uvicorn_calls: list[tuple[object, ...]] = []

    def fake_create_tables() -> None:
        uvicorn_calls.append(("create_tables",))

    def fake_uvicorn_run(app, host, port, reload):
        uvicorn_calls.append((app, host, port, reload))

    monkeypatch.setattr(database, "create_tables", fake_create_tables)
    monkeypatch.setattr("uvicorn.run", fake_uvicorn_run)
    sys.modules.pop("src.main", None)

    runpy.run_module("src.main", run_name="__main__")

    assert uvicorn_calls[0] == ("create_tables",)
    _, host, port, reload = uvicorn_calls[-1]
    assert (host, port, reload) == ("127.0.0.1", 8000, True)
