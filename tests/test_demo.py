"""Demo mode: AI-played approvers see only their own authority, are labeled simulated, and never email."""
import json
import time
from datetime import datetime
from pathlib import Path

import pytest

import demo
import ledger
import server
from test_ledger import SELLER, up
from test_portal import act_as, app, call, wait  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]


def settle(base, cookie, n=1):
    """Wait until the AI approvers have answered every open request."""
    for _ in range(200):
        s = wait(base, cookie)
        if s["portal"] and all(q["status"] != "open" for q in s["portal"]):
            return s
        time.sleep(0.05)
    raise AssertionError("approvers did not answer")


def test_prompt_shows_only_the_approvers_own_rows_and_no_answer_keys(app):
    base, runs = app
    s = up(base, act_as(base, SELLER))
    run = runs / s["run"]
    darla = next(q for q in s["portal"] if "Darla" in q["to_name"])
    text = demo.prompt_for(server.CFG, run, darla)
    assert "Darla Denkins" in text and "Deal Desk Manager" in text and "DEMO_APPROVER" in text
    rows = demo.authority_rows(server.CFG["matrix"]["folder"], "Deal Desk Manager")
    assert rows and all("Deal Desk Manager" in r for r in rows)
    ceo_only = [r for r in demo.authority_rows(server.CFG["matrix"]["folder"], "Chief Executive Officer")]
    assert not any(r in text for r in ceo_only if "Deal Desk Manager" not in r)
    assert "answer-key" not in text.lower() and "answer key" not in text.lower()
    for key in (ROOT / "examples/acme-saas/cases").glob("*/answer-key.md"):
        first_line = key.read_text().split("\n")[2].strip()
        assert first_line and first_line not in text  # nothing from the keys can reach the approver


def test_parse_reply():
    assert demo.parse("DECISION: Denied\nREPLY: No, we hold the standard.") == ("denied", "No, we hold the standard.")
    assert demo.parse("DECISION: conditional\nREPLY: Only up to 2x.") == ("conditional", "Only up to 2x.")
    assert demo.parse("I think it is fine") is None


def test_ai_approvers_decide_through_the_portal_and_are_labeled(app):
    base, runs = app
    server.CFG["demo"]["ai_approvers"] = True
    seller = act_as(base, SELLER)
    s = up(base, seller)
    s = settle(base, seller)
    assert all(q["decision"]["simulated"] for q in s["portal"])
    msgs = [p.read_text() for p in (runs / s["run"] / "inbox").glob("*.md")]
    assert len(msgs) == len(s["portal"]) and all("Simulated: yes" in m and "Via: approval portal" in m for m in msgs)
    db = ledger.connect(server.CFG["ledger"]["path"])
    assert db.execute("SELECT SUM(simulated), COUNT(*) FROM decisions").fetchone()[:] == (len(msgs), len(msgs))
    page = call(base, f"/portal/request/{s['portal'][0]['id']}", cookie=act_as(base, s["portal"][0]["to_email"]))[1]
    assert "(simulated)" in page


def test_scenarios_silent_and_delegating(app):
    base, runs = app
    server.CFG["demo"].update(ai_approvers=True, silent_titles=["Deal Desk Manager"], delegating_titles=["VP Finance"])
    seller = act_as(base, SELLER)
    up(base, seller)
    for _ in range(200):
        s = wait(base, seller)
        viv = next(q for q in s["portal"] if "Vivian" in q["to_name"])
        if viv["status"] == "decided":
            break
        time.sleep(0.05)
    darla = next(q for q in s["portal"] if "Darla" in q["to_name"])
    assert darla["status"] == "open" and not darla["decision"]  # silent
    assert viv["delegations"][0]["to"] == "cassie.sutton@acme.example" and viv["decision"]["acting_for"] == "vivian.fairfax@acme.example"


def test_the_demo_clock_drives_reminders(app):
    base, runs = app
    server.CFG["demo"].update(ai_approvers=True, silent_titles=["Deal Desk Manager", "VP Finance"])
    server.CFG["reminders"].update(first_after_days=1, second_after_days=2, escalate_after_days=3)
    demo.CLOCK["days"] = 0
    seller = act_as(base, SELLER)
    up(base, seller)
    time.sleep(0.5)
    got = []
    for _ in range(5):
        st, text, _ = call(base, "/api/demo/advance", {}, seller, form=False)
        assert st == 200, text
        got += json.loads(text)["done"]
    # two silent titles: VP Finance (one request) and the Deal Desk Manager (the payment request, and the referral of a term the matrix does not settle)
    assert sum("reminder 1" in x for x in got) == 3 and sum("escalated" in x for x in got) == 3
    s = wait(base, seller)
    assert s["demo"]["days"] >= 5
    demo.CLOCK["days"] = 0


def test_advance_refused_outside_demo(app):
    base, _ = app
    server.CFG["app"]["mode"] = "live"
    st, text, _ = call(base, "/api/demo/advance", {}, act_as(base, SELLER), form=False)
    assert st == 400 and "demo mode" in text
