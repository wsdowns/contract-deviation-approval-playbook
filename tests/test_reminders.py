"""Reminders and escalation, with the clock passed in so no test waits."""
import copy
import shutil
from datetime import date, datetime, timedelta

import ledger
import reminders
import server
from test_ledger import SELLER, up
from test_portal import act_as, app, call, rid_for, wait  # noqa: F401

OWNER = "grace.colton@acme.example"


def day_with_age(start, age, holidays=()):
    d = start
    while reminders.business_days(start, d, set(holidays)) < age:
        d += timedelta(days=1)
    return d


def quick(cfg):
    cfg["reminders"].update(first_after_days=1, second_after_days=2, escalate_after_days=3)


def notes(runs, run):
    d = runs / run / "notifications"
    return sorted((p.read_text() for p in d.glob("*.txt")), key=len) if d.exists() else []


def test_business_days_skip_weekends_and_holidays():
    fri = date(2026, 11, 13)
    assert reminders.business_days(fri, date(2026, 11, 16), set()) == 1  # Monday
    assert reminders.business_days(fri, date(2026, 11, 17), set()) == 2
    assert reminders.business_days(fri, date(2026, 11, 17), {"2026-11-16"}) == 1
    assert reminders.business_days(fri, fri, set()) == 0


def test_one_step_per_check_in_order(app):
    base, runs = app
    quick(server.CFG)
    s = up(base, act_as(base, SELLER))
    start = datetime.fromisoformat(s["portal"][0]["created"]).date()
    assert reminders.tick(server.CFG, runs, today=start) == []
    late = day_with_age(start, 10)  # far overdue: still only one step per check
    steps = []
    for _ in range(4):
        steps += reminders.tick(server.CFG, runs, today=late)
    per_request = [x.split(": ")[1] for x in steps if x.startswith(s["portal"][0]["id"])]
    assert per_request == ["reminder 1", "reminder 2", "escalated"]


def test_reminder_goes_to_the_approver_with_seller_and_mailbox_copied(app):
    base, runs = app
    quick(server.CFG)
    s = up(base, act_as(base, SELLER))
    start = datetime.fromisoformat(s["portal"][0]["created"]).date()
    before = len(notes(runs, s["run"]))
    reminders.tick(server.CFG, runs, today=day_with_age(start, 1))
    new = [n for n in notes(runs, s["run"]) if n.split("\n")[2].startswith("Subject: Reminder")]
    assert len(new) == len(s["portal"]) and len(notes(runs, s["run"])) == before + len(new)
    darla = next(n for n in new if "darla.denkins@acme.example" in n.split("\n")[0])
    assert SELLER in darla.split("\n")[1] and "contracts@acme.example" in darla.split("\n")[1] and "/portal/request/RQ-" in darla


def test_escalation_tells_seller_and_matrix_owner_together(app):
    base, runs = app
    quick(server.CFG)
    s = up(base, act_as(base, SELLER))
    start = datetime.fromisoformat(s["portal"][0]["created"]).date()
    for age in (1, 2, 3):
        reminders.tick(server.CFG, runs, today=day_with_age(start, age))
    esc = [n for n in notes(runs, s["run"]) if "Subject: No answer yet" in n]
    assert len(esc) == len(s["portal"])
    darla = next(n for n in esc if "Darla" in n)
    to = darla.split("\n")[0]
    assert SELLER in to and OWNER in to and "darla.denkins@acme.example" in darla.split("\n")[1]
    assert "Silence is not approval" in darla and "no fallback contact" in darla.lower()


def test_standing_fallback_receives_and_can_decide(app, tmp_path):
    base, runs = app
    quick(server.CFG)
    m = tmp_path / "matrix"
    shutil.copytree(server.MATRIX, m)
    server.CFG["matrix"]["folder"] = str(m)
    alex = act_as(base, SELLER)
    s = up(base, alex)
    rid = rid_for(s, "Vivian")
    start = datetime.fromisoformat(s["portal"][0]["created"]).date()
    for age in (1, 2, 3):
        reminders.tick(server.CFG, runs, today=day_with_age(start, age))
    q = next(x for x in wait(base, alex)["portal"] if x["id"] == rid)
    assert q["escalated"]["fallback"] == "cassie.sutton@acme.example" and "cassie.sutton@acme.example" in q["assigned"]
    assert q["delegations"][-1]["standing"] is True
    cassie = act_as(base, "cassie.sutton@acme.example")
    assert "Decision recorded" in call(base, f"/portal/request/{rid}/decide", {"decision": "approved", "text": "Covering."}, cassie)[1]
    msg = next(p for p in (runs / s["run"] / "inbox").glob("*.md")).read_text()
    assert "Acting by delegation from: Vivian Fairfax, VP Finance" in msg
    esc = next(n for n in notes(runs, s["run"]) if "Subject: No answer yet" in n and "Vivian" in n)
    assert "Cassie Sutton" in esc


def test_decided_and_disabled_get_nothing(app):
    base, runs = app
    quick(server.CFG)
    s = up(base, act_as(base, SELLER))
    rid = rid_for(s, "Darla")
    call(base, f"/portal/request/{rid}/decide", {"decision": "approved"}, act_as(base, "darla.denkins@acme.example"))
    start = datetime.fromisoformat(s["portal"][0]["created"]).date()
    out = reminders.tick(server.CFG, runs, today=day_with_age(start, 1))
    assert not any(x.startswith(rid) for x in out) and any(not x.startswith(rid) for x in out)
    server.CFG["reminders"]["enabled"] = False
    assert reminders.tick(server.CFG, runs, today=day_with_age(start, 9)) == []


def test_silence_shows_in_the_audit(app):
    base, runs = app
    quick(server.CFG)
    server.CFG["ledger"]["min_requests"] = 1
    s = up(base, act_as(base, SELLER))
    start = datetime.fromisoformat(s["portal"][0]["created"]).date()
    for age in (1, 2, 3):
        reminders.tick(server.CFG, runs, today=day_with_age(start, age))
    call(base, f"/portal/request/{rid_for(s, 'Darla')}/decide", {"decision": "approved"}, act_as(base, "darla.denkins@acme.example"))
    _, rows, _ = ledger.view(server.CFG, "responsiveness")
    vivian = next(r for r in rows if r["Approver"] == "Vivian Fairfax")
    assert (vivian["Received"], vivian["Decided"], vivian["Reminders"], vivian["Escalations"]) == (1, 0, 2, 1)
    assert vivian["Decided rate"] == "0%" and vivian["Escalations rate"] == "100%"
    page = call(base, "/audit", cookie=act_as(base, OWNER))[1]
    assert "Responsiveness" in page and "Vivian Fairfax" in page
