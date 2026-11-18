"""A change the matrix does not settle goes to the Deal Desk, which resolves it and records the authority it relied on."""
import json

import pytest

import portal
import server
from test_ledger import SELLER, up
from test_portal import act_as, app, call, wait  # noqa: F401

DARLA = "darla.denkins@acme.example"


def referral(s):
    return next(q for q in s["portal"] if q.get("kind") == "referral")


def test_an_unmatrixed_change_is_referred_to_the_deal_desk_with_the_clause_explained(app):
    base, runs = app
    s = up(base, act_as(base, SELLER))
    q = referral(s)
    assert q["to_title"] == "Deal Desk Manager" and q["dev"] == "D7"
    text = next(m["text"] for m in s["outbox"] if m["name"] == q["file"])
    for part in ("**Request kind:** referral", "**2. The clause.** Notices (General Terms)", "**3. In plain words.**",
                 "**4. What the standard says.** \"Notices will be deemed given", "**5. What the customer's version says.** \"A notice is deemed given",
                 "[-Notices will be-] {+A notice is+} deemed given", "**8. How to reply.**"):
        assert part in text, part
    assert "Changed outside the matrix" not in text and "matrix owner" not in text.lower()
    assert "Referred to the Deal Desk" in s["stage3"] and "Cell relied on" not in s["stage2"]  # the routing table no longer shows the cell
    assert s["stage1"].splitlines()[2].startswith("| ID | Requested (exact words) | Standard (exact words) | Where | Kind |")


def test_each_unmatrixed_change_is_its_own_request(app, monkeypatch):
    base, runs = app
    # make two places unmatrixed: drop the Publicity row's claim on Logo Rights as well
    import shutil
    m = runs.parent / "m2"
    shutil.copytree(server.MATRIX, m)
    t = (m / "doa_matrix.csv").read_text().replace("General Terms > Logo Rights", "General Terms > Nowhere Else")
    (m / "doa_matrix.csv").write_text(t)
    monkeypatch.setattr(server, "MATRIX", m)
    server.CFG["matrix"]["folder"] = str(m)
    s = up(base, act_as(base, SELLER))
    refs = [q for q in s["portal"] if q.get("kind") == "referral"]
    assert len(refs) == 2 and {q["dev"] for q in refs} == {"D6", "D7"}  # one request each, so each has its own outcome and authority


def test_the_response_must_cite_an_authority_and_is_recorded_as_the_deal_desks_statement(app):
    base, runs = app
    seller = act_as(base, SELLER)
    s = up(base, seller)
    q = referral(s)
    darla = act_as(base, DARLA)
    page = call(base, f"/portal/request/{q['id']}", cookie=darla)[1]
    assert "name=authority" in page and "No approval needed" in page and "Authority or basis" in page
    path = f"/portal/request/{q['id']}/decide"
    assert "Say who or what you relied on" in call(base, path, {"decision": "none_needed", "text": "", "authority": ""}, darla)[1]
    assert "Choose the outcome" in call(base, path, {"decision": "", "authority": "x"}, darla)[1]
    assert "Say what the conditions are" in call(base, path, {"decision": "conditional", "text": "", "authority": "x"}, darla)[1]
    ok = call(base, path, {"decision": "none_needed", "text": "Notices wording only.", "authority": "Legal's standing practice: tense changes to notices need no approval; confirmed by General Counsel on Nov 18", "reference": "email 'Notices' 11/18"}, darla)[1]
    assert "Decision recorded" in ok and "Authority or basis" in ok
    done = json.loads(call(base, "/api/state?run=" + s["run"], cookie=seller)[1])
    d = referral(done)["decision"]
    assert d["decision"] == "No approval needed" and d["authority"].startswith("Legal's standing practice") and d["reference"] == "email 'Notices' 11/18"
    call(base, "/api/record", {"run": s["run"]}, seller, form=False)
    wait(base, seller)
    record = json.loads(call(base, "/api/state?run=" + s["run"], cookie=seller)[1])["stage4"]
    row = next(l for l in record.splitlines() if l.startswith("| D7"))
    assert "No approval needed (Deal Desk)" in row and "Deal Desk: Legal's standing practice" in row and "not verified in the system" in row
    import ledger
    db = ledger.connect(server.CFG["ledger"]["path"])
    assert "Authority or basis: Legal's standing practice" in db.execute("SELECT words FROM decisions WHERE decision='No approval needed'").fetchone()[0]


def test_a_denied_referral_gets_a_seller_note(app):
    base, runs = app
    seller = act_as(base, SELLER)
    s = up(base, seller)
    q = referral(s)
    call(base, f"/portal/request/{q['id']}/decide", {"decision": "denied", "text": "We do not accept this.", "authority": "General Counsel, by phone"}, act_as(base, DARLA))
    call(base, "/api/record", {"run": s["run"]}, seller, form=False)
    wait(base, seller)
    record = json.loads(call(base, "/api/state?run=" + s["run"], cookie=seller)[1])["stage4"]
    assert "Denied (Deal Desk)" in record and "Seller notes" in record


def test_a_simulated_deal_desk_answers_in_demo_mode(app):
    base, runs = app
    server.CFG["demo"]["ai_approvers"] = True
    s = up(base, act_as(base, SELLER))
    for _ in range(100):
        s = json.loads(call(base, "/api/state?run=" + s["run"], cookie=act_as(base, SELLER))[1])
        if all(q["status"] == "decided" for q in s["portal"]):
            break
        import time
        time.sleep(0.05)
    d = referral(s)["decision"]
    assert d["simulated"] and d["authority"].startswith("SIMULATED")


def test_the_status_table_is_live_and_the_ledger_snapshot_happens_when_the_last_request_is_answered(app):
    import ledger
    base, runs = app
    seller = act_as(base, SELLER)
    s = up(base, seller)
    path = f"/api/state?run={s['run']}"
    rows = json.loads(call(base, path, cookie=seller)[1])["record"]
    assert len(rows) >= 6 and all(r["status"] in ("Awaiting reply", "Approved (pre-approved)", "Referred to Deal Desk") for r in rows)  # nothing decided yet
    db = ledger.connect(server.CFG["ledger"]["path"])
    assert db.execute("SELECT COUNT(*) FROM record_rows").fetchone()[0] == 0
    open_ones = [q for q in portal.load(runs / s["run"]) if q["status"] == "open"]
    for q in open_ones[:-1]:
        portal.decide(runs / s["run"], q["id"], portal.role_of(q["to_email"], server.MATRIX), "approved", "Fine.", server.CFG,
                      **({"authority": "policy"} if q.get("kind") == "referral" else {}))
    assert db.execute("SELECT COUNT(*) FROM record_rows").fetchone()[0] == 0  # one request is still open: no snapshot yet
    last = open_ones[-1]
    portal.decide(runs / s["run"], last["id"], portal.role_of(last["to_email"], server.MATRIX), "denied", "No.", server.CFG,
                  **({"authority": "policy"} if last.get("kind") == "referral" else {}))
    done = json.loads(call(base, path, cookie=seller)[1])
    assert db.execute("SELECT COUNT(*) FROM record_rows").fetchone()[0] == len(done["record"])  # snapshot taken once, when the last answer came in
    assert "## Approval record" in done["stage4"]
    statuses = [r["status"] for r in done["record"]]
    assert any(x.startswith("Approved") for x in statuses) and any(x.startswith("Denied") for x in statuses)
