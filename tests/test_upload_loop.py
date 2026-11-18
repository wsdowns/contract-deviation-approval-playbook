"""First round, later round and signed copy through the real HTTP handlers, with the stub model."""
import base64
import json
import sys
import threading
import time
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "tests"))
import server  # noqa: E402
from test_contract_io import docx, run  # noqa: E402

REDLINE = ROOT / "examples/acme-saas/cases/case-1-acme-redline/inputs/Brightwater_Redline_of_ACME_SaaS_Agreement.docx"


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "RUNS", tmp_path)
    monkeypatch.setattr(server, "STUB", True)
    monkeypatch.setitem(server.RUN, "dir", None)
    srv = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_port}"
    srv.shutdown()


def post(base, path, body):
    req = urllib.request.Request(base + path, json.dumps(body).encode(), {"Content-Type": "application/json"})
    try:
        return json.load(urllib.request.urlopen(req))
    except urllib.error.HTTPError as e:
        return json.load(e)


def state(base):
    return json.load(urllib.request.urlopen(base + "/api/state"))


def wait(base):
    for _ in range(100):
        s = state(base)
        if s["job"]["status"] != "running":
            return s
        time.sleep(0.05)
    raise AssertionError("job did not finish")


def up(base, name, data, **kw):
    return post(base, "/api/upload", {"filename": name, "data": base64.b64encode(data).decode(), "profile": "p", **kw})


def signed_copy(change=None):
    import contract_io
    text = contract_io.extract("x.docx", REDLINE.read_bytes())["accepted"]
    if change:
        assert change[0] in text
        text = text.replace(*change)
    return docx(*[run(line.replace("&", "&amp;")) for line in text.split("\n")])


def test_three_paths(app):
    first = up(app, "round1.docx", REDLINE.read_bytes())
    assert first["started"] and first["kind"] == "docx-tracked"
    s1 = wait(app)
    r1 = s1["run"]
    assert s1["upload"]["differences"] == 7 and s1["upload"]["untracked"] == 0 and s1["stage3"]

    second = up(app, "round2.docx", REDLINE.read_bytes(), previous=r1)
    assert second["started"]
    s2 = wait(app)
    assert s2["upload"]["previous"] == r1 and s2["upload"]["since_previous"] == 0
    assert (Path(server.RUNS) / s2["run"] / "prior-record.md").exists()
    assert s2["run"] != r1

    ok = up(app, "signed.docx", signed_copy(), previous=r1, signed=True)
    assert ok["started"]
    s3 = wait(app)
    assert s3["job"]["status"] == "done", s3["job"]
    assert s3["upload"]["signed"] and s3["upload"]["since_previous"] == 0 and s3["signed_check"]

    bad = up(app, "signed-bad.docx", signed_copy(("payable within 45 days", "payable within 60 days")), previous=r1, signed=True)
    assert bad["started"]
    s4 = wait(app)
    assert s4["upload"]["since_previous"] == 1 and "payable within 60 days" in s4["upload"]["since_previous_text"]


def test_errors_are_plain(app):
    assert "round it was agreed from" in up(app, "s.docx", REDLINE.read_bytes(), signed=True)["error"]
    assert "not found" in up(app, "s.docx", REDLINE.read_bytes(), previous="app-none")["error"]
    assert "not a readable Word" in up(app, "s.docx", b"junk")["error"]


def test_a_later_round_carries_forward_what_was_decided(app):
    import portal
    first = up(app, "round1.docx", REDLINE.read_bytes())
    r1 = wait(app)["run"]
    cfg = server.CFG
    run1 = Path(server.RUNS) / r1
    q = next(x for x in portal.load(run1) if x["to_title"] == "Deal Desk Manager")
    portal.decide(run1, q["id"], portal.role_of(q["to_email"], server.MATRIX), "approved", "Net 45 is fine.", cfg)
    up(app, "round2.docx", REDLINE.read_bytes(), previous=r1)
    s2 = wait(app)
    items = json.loads((Path(server.RUNS) / s2["run"] / "assessment.json").read_text())["items"]
    carried = [i for i in items if i["outcome"] == "already_decided"]
    assert {i["where"] for i in carried} == {"Payment & Taxes > Payment", "General Terms > Logo Rights"}  # Darla's decision, and the pre-approved one
    assert any(i["prior"]["approver"].startswith("Darla") for i in carried)  # decided and unchanged: not asked again
    subjects = " | ".join(x["subject"] for x in s2["portal"])
    assert "Payment" not in subjects  # the decided change is not asked again
    assert {"Associate General Counsel", "VP Customer Success", "VP Finance"} <= {x["to_title"] for x in s2["portal"]}  # everything else is



    assert "Already decided in an earlier round" in s2["stage3"]


def test_several_contracts_are_analysed_at_once(app, monkeypatch):
    import threading
    gate, calls = threading.Event(), []

    def slow_first(prompt):
        calls.append(1)
        if len(calls) == 1:
            gate.wait(10)  # the first contract's analysis is stuck until released
        return server.stub(prompt)

    monkeypatch.setattr(server, "ask", slow_first)
    a = up(app, "first.docx", REDLINE.read_bytes())
    assert a["started"]
    for _ in range(100):
        if calls:
            break
        time.sleep(0.02)
    b = up(app, "second.docx", REDLINE.read_bytes())
    assert b["started"]  # not refused because the first is still running
    second = wait(app)
    by_title = {d["title"]: d for d in second["deals"]}
    assert by_title["first.docx"]["status"] == "analyzing" and by_title["second.docx"]["status"] in ("waiting", "ready", "decided")
    gate.set()
    for _ in range(200):
        if all(d["status"] != "analyzing" for d in state(app)["deals"]):
            break
        time.sleep(0.05)
    assert [d["status"] for d in state(app)["deals"]].count("analyzing") == 0
    # opening the first deal shows the first deal's own files, untouched by the second
    first = by_title["first.docx"]["name"]
    assert post(app, "/api/resume", {"run": first})["run"] == first and state(app)["upload"]["filename"] == "first.docx"


def state_of(base, run):
    return json.load(urllib.request.urlopen(f"{base}/api/state?run={run}"))


def test_every_request_names_its_own_deal(app):
    a = up(app, "alpha.docx", REDLINE.read_bytes())
    wait(app)
    b = up(app, "beta.docx", REDLINE.read_bytes())
    wait(app)
    ra, rb = a["run"], b["run"]
    assert ra != rb
    # two screens open at once, each on its own deal: neither disturbs the other
    assert state_of(app, ra)["upload"]["filename"] == "alpha.docx"
    assert state_of(app, rb)["upload"]["filename"] == "beta.docx"
    assert state_of(app, ra)["upload"]["filename"] == "alpha.docx"  # still alpha after beta was read
    # no deal named by the page means no deal, not "whatever was last"
    blank = state_of(app, "")
    assert blank["run"] is None and blank["upload"] is None and blank["stage3"] == ""
    # a made-up or foreign name means no deal
    assert state_of(app, "app-20990101-000000")["run"] is None and state_of(app, "../..")["run"] is None
    # an action aimed at alpha runs on alpha, though beta is the latest
    assert post(app, "/api/record", {"run": ra})["started"]
    for _ in range(100):
        if state_of(app, ra)["job"]["status"] != "running":
            break
        time.sleep(0.05)
    assert state_of(app, ra)["stage4"] and not state_of(app, rb)["stage4"]
    # an action with no deal named is refused
    assert "Start a request first" in post(app, "/api/record", {"run": ""})["error"]


def test_a_contract_on_the_customers_own_paper_is_refused(app):
    from test_contract_io import docx, run
    other = docx(*[run(f"Clause {i}. The Supplier shall deliver the goods described in schedule {i} within {i + 10} days of the order.") for i in range(60)])
    r = up(app, "their-paper.docx", other)
    assert "does not look like ACME's standard agreement" in r["error"] and "own paper is not supported" in r["error"]
    assert state(app)["deals"] == []  # nothing was created


def test_the_standard_itself_uploaded_back_has_no_changes(app, monkeypatch):
    def no_ai(prompt):
        raise AssertionError("no change was found, so the AI must not be called")
    monkeypatch.setattr(server, "ask", no_ai)
    r = up(app, "standard.docx", (ROOT / "examples/acme-saas/contracts/ACME_SaaS_Agreement_v1.0.docx").read_bytes())
    assert r["started"]
    s = wait(app)
    assert s["job"]["status"] == "done" and s["upload"]["differences"] == 0
    assert not s["portal"] and s["stage3"].lstrip().startswith("## Batch summary")
