"""Archiving a contract: any time, open requests are withdrawn, and it no longer shows in the seller's screens."""
import json

import ledger
import portal
import reminders
import server
from test_ledger import SELLER, up
from test_portal import act_as, app, call  # noqa: F401


def state(base, run, cookie):
    return json.loads(call(base, f"/api/state?run={run}", cookie=cookie)[1])


def test_archiving_withdraws_open_requests_and_hides_the_contract(app):
    base, runs = app
    seller = act_as(base, SELLER)
    s = up(base, seller)
    first = next(q for q in portal.load(runs / s["run"]) if q["to_title"] == "Deal Desk Manager" and q.get("kind") != "referral")
    portal.decide(runs / s["run"], first["id"], portal.role_of(first["to_email"], server.MATRIX), "approved", "Fine.", server.CFG)  # one decided, the rest open
    assert state(base, s["run"], seller)["deals"][0]["name"] == s["run"]

    r = call(base, "/api/archive", {"run": s["run"]}, seller, form=False)
    assert r[0] == 200 and json.loads(r[1]) == {"archived": True, "withdrawn": 4}  # the 4 requests that were still open

    reqs = portal.load(runs / s["run"])
    assert {q["status"] for q in reqs} == {"decided", "withdrawn"} and sum(q["status"] == "withdrawn" for q in reqs) == 4
    assert [d for d in state(base, "", seller)["deals"] if d["name"] == s["run"]] == []  # off the seller's list
    assert s["run"] not in [x["name"] for x in state(base, "", seller)["upload_runs"]]  # and off the later-round picker
    assert state(base, s["run"], seller)["run"] is None  # naming it now gives no deal
    assert "Start a request first" in call(base, "/api/record", {"run": s["run"]}, seller, form=False)[1]  # nothing more can be done to it
    assert (runs / s["run"] / "archived.json").exists()  # the files stay


def test_an_approver_sees_a_withdrawn_request_and_cannot_decide_it(app):
    base, runs = app
    seller = act_as(base, SELLER)
    s = up(base, seller)
    q = next(x for x in portal.load(runs / s["run"]) if x["to_title"] == "VP Finance")
    call(base, "/api/archive", {"run": s["run"]}, seller, form=False)
    vivian = act_as(base, q["to_email"])
    assert "Withdrawn" in call(base, "/portal", cookie=vivian)[1]
    page = call(base, f"/portal/request/{q['id']}", cookie=vivian)[1]
    assert "Withdrawn by the seller" in page and "Your decision" not in page and "name=decision" not in page
    assert "withdrawn by the seller" in call(base, f"/portal/request/{q['id']}/decide", {"decision": "approved"}, vivian)[1]


def test_reminders_stop_for_withdrawn_requests_and_the_ledger_records_it(app):
    base, runs = app
    seller = act_as(base, SELLER)
    s = up(base, seller)
    call(base, "/api/archive", {"run": s["run"]}, seller, form=False)
    from datetime import date, timedelta
    assert reminders.tick(server.CFG, runs, today=date.today() + timedelta(days=30)) == []  # nothing is chased any more
    db = ledger.connect(server.CFG["ledger"]["path"])
    assert db.execute("SELECT COUNT(*) FROM request_events WHERE event='withdrawn'").fetchone()[0] == 5
    ev = db.execute("SELECT event, by_email, detail FROM deal_events").fetchall()
    assert [(e["event"], e["by_email"]) for e in ev] == [("archived", SELLER)] and "5 open request" in ev[0]["detail"]
    assert "deal_events" in ledger.export(server.CFG, "deal_events") or ledger.export(server.CFG, "deal_events").startswith("id,run,deal_id,at,event,by_email,detail")


def test_archiving_a_contract_with_nothing_open_still_works_and_another_seller_cannot_archive_it(app):
    base, runs = app
    seller = act_as(base, SELLER)
    s = up(base, seller)
    for q in portal.load(runs / s["run"]):
        portal.decide(runs / s["run"], q["id"], portal.role_of(q["to_email"], server.MATRIX), "approved", "Fine.", server.CFG,
                      **({"authority": "policy"} if q.get("kind") == "referral" else {}))
    assert json.loads(call(base, "/api/archive", {"run": s["run"]}, seller, form=False)[1])["withdrawn"] == 0
    assert "Start a request first" in call(base, "/api/archive", {"run": s["run"]}, seller, form=False)[1]  # twice does nothing


def test_the_page_has_the_new_structure(app):
    page = (server.STATIC / "index.html").read_text()
    for part in ("Start Here: Demo (Staged Examples)", "Seller\\'s Associate: Your Contracts", "function contractsPage", "'Summary'", "'Requests/Status'", "'Appeals'", "'Final Check'", "archiveGo",
                 "This withdraws any open requests and can\\'t be undone"):
        assert part in page, part
    assert "x.disabled=cur>=1&&j.status==='running'" in page  # an analysis in progress never greys out the upload button on the Contracts page
    assert "PAGES.slice(1)" in page and "&larr; Contracts" in page  # every contract screen links to its other steps and back to Contracts
    assert '<tr class="mrow' in page and "<th>Open</th>" not in page  # each contract's menu sits in a row under it, not beside it
    for gone in ("Open a finished example", "Review a new redline", "Approvals mailbox", "Hand over the contract", "My deals"):
        assert gone not in page, gone
