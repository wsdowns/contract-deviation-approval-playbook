"""The final check: upload the contract at its latest revision. Pass if every change is approved; if not, say where."""
import base64
import json

import contract_io
import ledger
import portal
import server
from test_contract_io import docx, run
from test_ledger import SELLER, up
from test_portal import REDLINE, act_as, app, call  # noqa: F401


def answer_all(runs, s, only_not=None, **decisions):
    """Decide every open request: approved, unless a title is named in decisions as {title: (decision, text)}."""
    for q in portal.load(runs / s["run"]):
        if q["status"] != "open" or q["to_title"] == only_not:
            continue
        d, text = decisions.get(q["to_title"] + ("/referral" if q.get("kind") == "referral" else ""), ("approved", "Fine."))
        portal.decide(runs / s["run"], q["id"], portal.role_of(q["to_email"], server.MATRIX), d, text, server.CFG,
                      **({"authority": "Legal practice"} if q.get("kind") == "referral" else {}))


def final_docx(edit=None):
    """The Brightwater contract with every change accepted, optionally edited: what the seller would upload as the final version."""
    lines = contract_io.extract("x.docx", REDLINE.read_bytes())["accepted"].split("\n")
    lines = edit(lines) if edit else lines
    return docx(*[run(l.replace("&", "&amp;")) for l in lines])


def check(base, seller, s, data):
    r = call(base, "/api/final", {"run": s["run"], "filename": "final.docx", "data": base64.b64encode(data).decode()}, seller, form=False)
    return r[0], json.loads(r[1])


def test_a_contract_with_only_approved_changes_passes(app):
    base, runs = app
    seller = act_as(base, SELLER)
    s = up(base, seller)
    answer_all(runs, s)
    st, r = check(base, seller, s, REDLINE.read_bytes())
    assert st == 200 and r["pass"] is True and r["failures"] == [] and r["changes_in_final"] == 6
    got = json.loads(call(base, f"/api/state?run={s['run']}", cookie=seller)[1])
    assert got["final_check"]["pass"] is True
    assert all(x["final_outcome"] for x in got["record"])  # the record now says what became of each change
    db = ledger.connect(server.CFG["ledger"]["path"])
    assert db.execute("SELECT COUNT(*) FROM record_rows WHERE stage='stage6'").fetchone()[0] == len(got["record"])


def test_a_denied_change_still_in_the_contract_fails_and_says_where(app):
    base, runs = app
    seller = act_as(base, SELLER)
    s = up(base, seller)
    answer_all(runs, s, **{"Deal Desk Manager": ("denied", "Too long.")})
    st, r = check(base, seller, s, REDLINE.read_bytes())
    assert r["pass"] is False
    f = next(x for x in r["failures"] if x["where"] == "Payment & Taxes > Payment")
    assert "was denied" in f["reason"] and "45 days" in f["contract"]


def test_a_denied_change_that_was_removed_passes(app):
    base, runs = app
    seller = act_as(base, SELLER)
    s = up(base, seller)
    answer_all(runs, s, **{"Deal Desk Manager": ("denied", "Too long.")})
    gone = lambda lines: [l.replace(" Unless the Order Form states otherwise, invoices are payable within 45 days of the invoice date.", "").replace("Unless the Order Form states otherwise, invoices are payable within 45 days of the invoice date.", "") for l in lines]
    st, r = check(base, seller, s, final_docx(gone))
    assert r["pass"] is True and any("denied" in x["what"] and "not in the final contract" in x["what"] for x in r["removed"])


def test_a_change_still_waiting_for_a_decision_fails(app):
    base, runs = app
    seller = act_as(base, SELLER)
    s = up(base, seller)
    answer_all(runs, s, only_not="VP Finance")  # the renewal cap is still open
    st, r = check(base, seller, s, REDLINE.read_bytes())
    assert r["pass"] is False and any("not been approved yet" in x["reason"] for x in r["failures"])


def test_changed_wording_and_a_change_nobody_submitted_both_fail(app):
    base, runs = app
    seller = act_as(base, SELLER)
    s = up(base, seller)
    answer_all(runs, s)
    def edit(lines):
        out = [l.replace("payable within 45 days", "payable within 60 days") for l in lines]
        return [l + " Customer pays no taxes." if l.startswith("Taxes.") else l for l in out]
    st, r = check(base, seller, s, final_docx(edit))
    assert r["pass"] is False
    reasons = {x["where"]: x["reason"] for x in r["failures"]}
    assert "not the wording that was submitted" in reasons["Payment & Taxes > Payment"]
    assert "never submitted for approval" in reasons["Payment & Taxes > Taxes"]


def test_conditions_are_listed_as_a_note_not_a_failure(app):
    base, runs = app
    seller = act_as(base, SELLER)
    s = up(base, seller)
    answer_all(runs, s, **{"Deal Desk Manager": ("conditional", "Net 45 for the first year only.")})
    st, r = check(base, seller, s, REDLINE.read_bytes())
    assert r["pass"] is True and any("Net 45 for the first year only." in n for n in r["notes"])


def test_the_wrong_file_is_refused_in_plain_words(app):
    base, runs = app
    seller = act_as(base, SELLER)
    s = up(base, seller)
    other = docx(*[run(f"Clause {i}. The Supplier shall deliver the goods in schedule {i} within {i + 10} days.") for i in range(60)])
    st, r = check(base, seller, s, other)
    assert st == 400 and "does not look like ACME's standard agreement" in r["error"]
    assert call(base, "/api/final", {"run": s["run"], "filename": "x.docx", "data": base64.b64encode(b"junk").decode()}, seller, form=False)[0] == 400
    assert call(base, "/api/final", {"run": "", "filename": "x.docx", "data": base64.b64encode(REDLINE.read_bytes()).decode()}, seller, form=False)[0] == 400  # no deal open
