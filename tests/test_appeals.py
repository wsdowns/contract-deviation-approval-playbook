"""A denial can be appealed once, to the same approver. The record shows both decisions."""
import json
import time

import portal
import server
from test_ledger import SELLER, up
from test_portal import act_as, app, call  # noqa: F401

DARLA = "darla.denkins@acme.example"


def state(base, run, cookie):
    return json.loads(call(base, f"/api/state?run={run}", cookie=cookie)[1])


def deny_payment(base, runs, s):
    q = next(x for x in portal.load(runs / s["run"]) if x["to_title"] == "Deal Desk Manager" and x.get("kind") != "referral")
    portal.decide(runs / s["run"], q["id"], portal.role_of(q["to_email"], server.MATRIX), "denied", "Net 45 is too long for a customer this small.", server.CFG)
    return q


def test_a_denial_is_appealed_once_to_the_same_approver_and_the_record_shows_both(app):
    base, runs = app
    seller = act_as(base, SELLER)
    s = up(base, seller)
    q = deny_payment(base, runs, s)
    st = state(base, s["run"], seller)
    row = next(a for a in st["appeals"] if a["request"] == q["id"])
    assert row["state"] == "open" and row["approver"].startswith("Darla") and "too long" in row["words"] and row["change"]

    r = call(base, "/api/appeal", {"run": s["run"], "request": q["id"], "context": "They are a 12-user account on a 6-month pilot."}, seller, form=False)
    assert r[0] == 200
    new = next(x for x in portal.load(runs / s["run"]) if x.get("appeal_of") == q["id"])
    assert new["to_email"] == q["to_email"] and new["subject"].startswith("Appeal: ")  # the same approver, never someone above
    text = (runs / s["run"] / "outbox" / new["file"]).read_text()
    for part in ("only appeal", "too long for a customer this small", "12-user account on a 6-month pilot", "The original request"):
        assert part in text, part

    after = state(base, s["run"], seller)
    assert next(a for a in after["appeals"] if a["request"] == q["id"])["state"] == "pending"
    assert next(x for x in after["record"] if x["id"] == q["dev"])["status"] == "Appeal pending"

    # one appeal per denial; an appeal cannot itself be appealed; only a denial can be appealed
    assert "already been appealed" in call(base, "/api/appeal", {"run": s["run"], "request": q["id"], "context": ""}, seller, form=False)[1]
    assert "Choose a denied change" in call(base, "/api/appeal", {"run": s["run"], "request": new["id"], "context": ""}, seller, form=False)[1]
    other = next(x for x in portal.load(runs / s["run"]) if x["to_title"] == "VP Finance")
    assert "Only a denied change" in call(base, "/api/appeal", {"run": s["run"], "request": other["id"], "context": ""}, seller, form=False)[1]

    portal.decide(runs / s["run"], new["id"], portal.role_of(new["to_email"], server.MATRIX), "conditional", "Net 45 only for the first year.", server.CFG)
    done = state(base, s["run"], seller)
    rec = next(x for x in done["record"] if x["id"] == q["dev"])
    assert rec["status"] == "Conditional" and "Decided on appeal." in rec["notes"]
    assert "too long for a customer" in rec["decision_words"] and "Then, on appeal" in rec["decision_words"] and "first year" in rec["decision_words"]
    last = next(a for a in done["appeals"] if a["request"] == q["id"])
    assert last["state"] == "decided" and last["outcome"] == "Approved with conditions"
    assert "already been appealed" in call(base, "/api/appeal", {"run": s["run"], "request": q["id"], "context": ""}, seller, form=False)[1]  # the decision stands


def test_a_denial_that_stands_after_appeal_stays_denied(app):
    base, runs = app
    seller = act_as(base, SELLER)
    s = up(base, seller)
    q = deny_payment(base, runs, s)
    call(base, "/api/appeal", {"run": s["run"], "request": q["id"], "context": ""}, seller, form=False)
    new = next(x for x in portal.load(runs / s["run"]) if x.get("appeal_of") == q["id"])
    portal.decide(runs / s["run"], new["id"], portal.role_of(new["to_email"], server.MATRIX), "denied", "My answer stands.", server.CFG)
    rec = next(x for x in state(base, s["run"], seller)["record"] if x["id"] == q["dev"])
    assert rec["status"] == "Denied" and "My answer stands." in rec["decision_words"]


def test_a_denied_referral_is_appealed_to_the_deal_desk(app):
    base, runs = app
    seller = act_as(base, SELLER)
    s = up(base, seller)
    ref = next(x for x in portal.load(runs / s["run"]) if x.get("kind") == "referral")
    portal.decide(runs / s["run"], ref["id"], portal.role_of(ref["to_email"], server.MATRIX), "denied", "Not acceptable.", server.CFG, authority="Legal practice")
    assert call(base, "/api/appeal", {"run": s["run"], "request": ref["id"], "context": "Our operations team does send by registered mail."}, seller, form=False)[0] == 200
    new = next(x for x in portal.load(runs / s["run"]) if x.get("appeal_of") == ref["id"])
    assert new["kind"] == "referral" and new["to_title"] == "Deal Desk Manager"  # it gets the same response form: outcome and authority


def test_a_simulated_approver_answers_an_appeal_in_demo_mode(app):
    base, runs = app
    server.CFG["demo"]["ai_approvers"] = True
    seller = act_as(base, SELLER)
    s = up(base, seller)
    for _ in range(100):
        if all(x["status"] == "decided" for x in portal.load(runs / s["run"])):
            break
        time.sleep(0.05)
    q = next(x for x in portal.load(runs / s["run"]) if x["to_title"] == "VP Finance")
    # the stub approvers approved everything; turn one decision into a denial so there is something to appeal
    reqs = portal.load(runs / s["run"])
    for x in reqs:
        if x["id"] == q["id"]:
            x["decision"]["decision"] = "Denied"
    portal._save(runs / s["run"], reqs)
    assert call(base, "/api/appeal", {"run": s["run"], "request": q["id"], "context": ""}, seller, form=False)[0] == 200
    new_id = next(x for x in portal.load(runs / s["run"]) if x.get("appeal_of") == q["id"])["id"]
    for _ in range(100):
        got = next(x for x in portal.load(runs / s["run"]) if x["id"] == new_id)
        if got["status"] == "decided":
            break
        time.sleep(0.05)
    assert got["decision"]["simulated"]


def test_the_old_follow_up_and_counterproposal_features_are_gone(app):
    base, runs = app
    seller = act_as(base, SELLER)
    s = up(base, seller)
    assert call(base, "/api/followup", {"run": s["run"]}, seller, form=False)[0] == 404
    assert call(base, "/api/counter", {"run": s["run"], "message": "x"}, seller, form=False)[0] == 404
    page = (server.STATIC / "index.html").read_text()
    assert "Draft follow-ups" not in page and "Draft the new request" not in page and "'Appeals'" in page
