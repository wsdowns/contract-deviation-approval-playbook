import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
import server  # noqa: E402


@pytest.fixture(autouse=True)
def private_ledger(tmp_path_factory, monkeypatch):
    """Tests never touch the real ledger.db."""
    monkeypatch.setitem(server.CFG["ledger"], "path", str(tmp_path_factory.mktemp("ledger") / "ledger.db"))


@pytest.fixture(autouse=True)
def no_ai_approvers_unless_asked(monkeypatch):
    """Most tests play the approvers themselves. Demo tests switch the AI approvers on."""
    monkeypatch.setitem(server.CFG["demo"], "ai_approvers", False)


@pytest.fixture(autouse=True)
def fresh_seller_state(monkeypatch):
    """Each test starts with nobody's deal or job open."""
    monkeypatch.setattr(server.ME, "run", None, raising=False)
    monkeypatch.setattr(server, "RUN", server.Current(lambda: {"dir": None}))
    monkeypatch.setattr(server, "JOB", server.PerDeal(lambda: {"name": "", "status": "idle", "message": ""}))
