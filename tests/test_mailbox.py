"""The simulated mailbox: replies arrive only when the matching request was sent."""
import os
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
os.environ["DOA_STUB"] = "1"
import server  # noqa: E402


@pytest.fixture
def run(tmp_path, monkeypatch):
    def make(case):
        d = tmp_path / "run"
        d.mkdir(exist_ok=True)
        (d / "case.txt").write_text(case)
        monkeypatch.setitem(server.RUN, "dir", d)
        return d
    return make


def send(d, subject, to="x"):
    out = d / "outbox"
    out.mkdir(exist_ok=True)
    (out / f"{len(list(out.glob('*.md'))) + 1:02d}.md").write_text(f"**To:** {to}\n**Subject:** {subject}\n\nbody\n")
    time.sleep(0.01)  # mtimes must differ


def names(d):
    return sorted(p.name for p in (d / "inbox").glob("*.md"))


def test_nothing_arrives_without_a_request(run):
    run("case-3")
    assert server.deliver() == 0


def test_wrong_authority_reply_then_resend(run):
    d = run("case-3")
    send(d, "Summit Ridge Manufacturing: billing quarterly in advance")
    server.deliver()
    assert names(d) == ["01-vance-quarterly-billing.md"]  # the VP Finance reply is held back
    server.deliver()
    assert names(d) == ["01-vance-quarterly-billing.md"]
    send(d, "Summit Ridge Manufacturing: billing quarterly in advance", to="Vivian Fairfax")
    server.deliver()
    assert "01-vivian-quarterly-billing.md" in names(d)


def test_case_two_ruling_comes_before_the_approvals(run):
    d = run("case-2")
    send(d, "Lakeshore Health: authority for a liability cap of the greater of 3x fees or $5M")
    server.deliver()
    assert names(d) == ["01-grace-cap-authority-ruling.md"]
    send(d, "Lakeshore Health: liability cap of the greater of 3x fees or $5M", to="Grace Colton")
    server.deliver()
    assert names(d) == ["01-grace-cap-authority-ruling.md", "02-grace-cap-approval.md", "03-clifford-cap-approval.md"]


def test_every_case_has_its_paper():
    for cid, c in server.CASES.items():
        base = server.CASES_DIR / c["dir"] / "inputs"
        assert (base / c["paper"]).exists(), cid
        assert (base / "deal-profile.md").exists(), cid


def test_reply_matches_on_topic_not_exact_subject():
    req = lambda subj, body="": f"**To:** x\n**Subject:** {subj}\n\n{body}"
    same = server.same_point
    assert same("re: lakeshore: termination for convenience with refund", req("Lakeshore: termination for convenience on 60 days' notice"))
    assert same("summit ridge manufacturing: removing the cap on gross negligence and willful misconduct",
                req("Summit Ridge: uncap liability for gross negligence", "Please approve removing the cap for gross negligence."))
    assert not same("summit ridge manufacturing: billing quarterly in advance", req("Summit Ridge: cyber insurance limit of $10M", "liability"))
    assert not same("brightwater: renewal increase capped at 5%", req("Brightwater: renewal increase capped at 3%"))
