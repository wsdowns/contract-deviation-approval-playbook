"""The approvals ledger: append-only storage, writers, audit views and who may read them."""
import base64
import json
import sqlite3

import pytest

import ledger
import server
from test_portal import act_as, app, call, rid_for, wait  # noqa: F401  (app is a fixture)
from test_portal import REDLINE

TABLE = """Approval record

| ID | Change | Matrix row and level | Approver (name, title) | Decision (exact words) | Status | Conditions (exact words) | Final outcome | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | Payment Net 45 | Payment terms, Level 1 | Darla Denkins, Deal Desk Manager | "Approved." | Approved | none | Conceded as approved | |
| 2 | Renewal cap 3% | Renewal pricing, Level 2 | Vivian Fairfax, VP Finance | "No." | Denied | none | Not conceded | |
"""
OWNER = "grace.colton@acme.example"
SELLER = "alex.easton@acme.example"


def test_ledger_is_append_only(tmp_path):
    db = ledger.connect(tmp_path / "l.db")
    db.execute("INSERT INTO matrix_versions VALUES ('h','now','{}')")
    for sql in ("UPDATE matrix_versions SET hash='x'", "DELETE FROM matrix_versions"):
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            db.execute(sql)
    assert db.execute("SELECT COUNT(*) FROM matrix_versions").fetchone()[0] == 1


def test_parse_record_reads_the_table():
    rows = ledger.parse_record(TABLE)
    assert [r["status"] for r in rows] == ["Approved", "Denied"]
    assert rows[1]["matrix_row_level"] == "Renewal pricing, Level 2" and rows[0]["final_outcome"] == "Conceded as approved"
    assert ledger.parse_record("no table here") == []


def up(base, cookie, deal=None):
    data = {"filename": "r.docx", "data": base64.b64encode(REDLINE.read_bytes()).decode(), "profile": "p",
            "deal": deal or {"customer": "Brightwater", "annual_fees": "250,000", "term_months": "24", "tier": "standard"}}
    st, text, _ = call(base, "/api/upload", data, cookie, form=False)
    assert st == 200, text
    return wait(base, cookie)


def test_decision_and_deal_are_written(app):
    base, runs = app
    s = up(base, act_as(base, SELLER))
    rid = rid_for(s, "Darla")
    call(base, f"/portal/request/{rid}/decide", {"decision": "approved", "text": "Fine."}, act_as(base, "darla.denkins@acme.example"))
    db = ledger.connect(server.CFG["ledger"]["path"])
    d = db.execute("SELECT * FROM decisions").fetchone()
    assert d["approver_title"] == "Deal Desk Manager" and d["decision"] == "Approved" and d["words"] == "Fine."
    assert d["response_hours"] is not None and d["response_hours"] >= 0 and len(d["matrix_version"]) == 12
    deal = db.execute("SELECT * FROM deals").fetchone()
    assert deal["annual_fees"] == 250000 and deal["term_months"] == 24 and deal["tier"] == "standard" and deal["seller_email"] == SELLER
    assert db.execute("SELECT COUNT(*) FROM matrix_versions").fetchone()[0] == 1
    assert "Annual fees $250,000" in (runs / s["run"] / "deal-profile.md").read_text()


def test_bad_deal_numbers_are_refused(app):
    base, _ = app
    data = {"filename": "r.docx", "data": base64.b64encode(REDLINE.read_bytes()).decode(), "deal": {"annual_fees": "lots"}}
    st, text, _ = call(base, "/api/upload", data, act_as(base, SELLER), form=False)
    assert st == 400 and "Annual fees must be a number" in text


def test_record_snapshots_count_each_change_once(app):
    base, runs = app
    seller = act_as(base, SELLER)
    s = up(base, seller)
    call(base, f"/portal/request/{rid_for(s, 'Darla')}/decide", {"decision": "approved", "text": "Ok"}, act_as(base, "darla.denkins@acme.example"))
    final = {"filename": "final.docx", "data": base64.b64encode(REDLINE.read_bytes()).decode()}
    for path, body in (("/api/record", {}), ("/api/final", final)):
        assert call(base, path, body, seller, form=False)[0] == 200
        wait(base, seller)
    n = len(json.loads((runs / s["run"] / "record.json").read_text()))
    assert n >= 5
    db = ledger.connect(server.CFG["ledger"]["path"])
    assert db.execute("SELECT COUNT(*) FROM record_rows").fetchone()[0] == 2 * n  # two snapshots of the same rows
    title, rows, _ = ledger.view(server.CFG, "terms")
    assert sum(r["Changes"] for r in rows) == n  # but each change is counted once


def test_rates_need_enough_requests(app):
    base, _ = app
    s = up(base, act_as(base, SELLER))
    call(base, f"/portal/request/{rid_for(s, 'Darla')}/decide", {"decision": "denied", "text": "No"}, act_as(base, "darla.denkins@acme.example"))
    _, rows, _ = ledger.view(server.CFG, "approvers")
    assert rows[0]["Requests"] == 1 and rows[0]["Denied"] == 1 and rows[0]["Denied rate"] == "too few requests"
    server.CFG["ledger"]["min_requests"] = 1
    _, rows, _ = ledger.view(server.CFG, "approvers")
    assert rows[0]["Denied rate"] == "100%"
    _, rows, _ = ledger.view(server.CFG, "deal-size")
    assert rows[0]["Annual fees"] == "$100K to $500K"


def test_only_the_owner_reads_the_audit(app):
    base, _ = app
    s = up(base, act_as(base, SELLER))
    call(base, f"/portal/request/{rid_for(s, 'Darla')}/decide", {"decision": "approved"}, act_as(base, "darla.denkins@acme.example"))
    assert call(base, "/audit")[0] == 303
    assert call(base, "/audit", cookie=act_as(base, SELLER))[0] == 403
    assert call(base, "/audit", cookie=act_as(base, "darla.denkins@acme.example"))[0] == 403
    owner = act_as(base, OWNER)
    st, page, _ = call(base, "/audit", cookie=owner)
    assert st == 200 and "Audit the approvers" in page and "Deal Desk Manager" in page
    st, text, h = call(base, "/audit/export/decisions.csv", cookie=owner)
    assert st == 200 and text.startswith("id,request_id") and "Deal Desk Manager" in text and "csv" in h["Content-Type"]
    assert call(base, "/audit/export/decisions.csv", cookie=act_as(base, SELLER))[0] == 403
    server.CFG["ledger"]["viewers"] = [SELLER]
    assert call(base, "/audit", cookie=act_as(base, SELLER))[0] == 200
