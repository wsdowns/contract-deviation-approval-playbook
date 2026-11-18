"""The approval portal, logins and notifications, through the real HTTP handlers with the stub model."""
import base64
import copy
import json
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "tests"))
import auth  # noqa: E402
import notify  # noqa: E402
import server  # noqa: E402

REDLINE = ROOT / "examples/acme-saas/cases/case-1-acme-redline/inputs/Brightwater_Redline_of_ACME_SaaS_Agreement.docx"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


OPENER = urllib.request.build_opener(NoRedirect)


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "RUNS", tmp_path)
    monkeypatch.setattr(server, "STUB", True)
    monkeypatch.setitem(server.RUN, "dir", None)
    monkeypatch.setattr(server, "CFG", copy.deepcopy(server.CFG))
    srv = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_port}", tmp_path
    srv.shutdown()


def call(base, path, data=None, cookie="", headers=None, form=True):
    body = None
    h = {"Cookie": cookie, **(headers or {})}
    if data is not None:
        body = (urllib.parse.urlencode(data) if form else json.dumps(data)).encode()
        h["Content-Type"] = "application/x-www-form-urlencoded" if form else "application/json"
    try:
        r = OPENER.open(urllib.request.Request(base + path, body, h))
    except urllib.error.HTTPError as e:
        r = e
    return r.status if hasattr(r, "status") else r.code, r.read().decode(), r.headers


def act_as(base, email):
    st, _, h = call(base, "/act-as", {"email": email})
    assert st == 303
    return h["Set-Cookie"].split(";")[0]


def wait(base, cookie=""):
    for _ in range(200):
        s = json.loads(call(base, "/api/state", cookie=cookie)[1])
        if s["job"]["status"] != "running":
            return s
        time.sleep(0.05)
    raise AssertionError("job did not finish")


def upload(base, cookie=""):
    data = {"filename": "r.docx", "data": base64.b64encode(REDLINE.read_bytes()).decode(), "profile": "p"}
    st, text, _ = call(base, "/api/upload", data, cookie, form=False)
    assert st == 200, text
    return wait(base, cookie)


def rid_for(state, name):
    return next(q["id"] for q in state["portal"] if name in q["to_name"])


def test_upload_auto_sends_and_creates_requests(app):
    base, runs = app
    s = upload(base, act_as(base, "alex.easton@acme.example"))
    assert s["outbox"] and len(s["portal"]) >= 2 and not s["send_problem"]
    run = runs / s["run"]
    assert (run / "seller.txt").read_text() == "alex.easton@acme.example"
    notes = list((run / "notifications").glob("*.txt"))
    assert len(notes) == len(s["portal"])
    text = notes[0].read_text()
    assert "/portal/request/RQ-" in text and "Cc:" in text and "alex.easton@acme.example" in text and "contracts@acme.example" in text


def test_approver_decides_and_it_reaches_the_record(app):
    base, runs = app
    alex = act_as(base, "alex.easton@acme.example")
    s = upload(base, alex)
    rid = rid_for(s, "Darla")
    darla = act_as(base, "darla.denkins@acme.example")
    assert rid in call(base, "/portal", cookie=darla)[1]
    page = call(base, f"/portal/request/{rid}", cookie=darla)[1]
    assert "Your decision" in page
    st, page, _ = call(base, f"/portal/request/{rid}/decide", {"decision": "conditional", "text": ""}, darla)
    assert "Say what the conditions are" in page
    st, page, _ = call(base, f"/portal/request/{rid}/decide", {"decision": "conditional", "text": "Only if fees stay above $100K."}, darla)
    assert "Decision recorded" in page
    msg = next((runs / s["run"] / "inbox").glob("*.md")).read_text()
    assert "From: Darla Denkins <darla.denkins@acme.example>" in msg and "Via: approval portal" in msg
    assert "Decision: Approved with conditions" in msg and "Only if fees stay above $100K." in msg
    assert "already been decided" in call(base, f"/portal/request/{rid}/decide", {"decision": "approved"}, darla)[1]
    state = wait(base, alex)
    assert next(q for q in state["portal"] if q["id"] == rid)["status"] == "decided"


def test_only_the_assigned_person_sees_a_request(app):
    base, _ = app
    s = upload(base, act_as(base, "alex.easton@acme.example"))
    rid = rid_for(s, "Darla")
    assert call(base, f"/portal/request/{rid}", cookie=act_as(base, "vivian.fairfax@acme.example"))[0] == 404
    assert call(base, f"/portal/request/{rid}", cookie="")[0] == 303  # not signed in: sent to sign in
    assert call(base, f"/portal/request/{rid}/decide", {"decision": "approved"}, act_as(base, "vivian.fairfax@acme.example"))[0] == 404


def test_delegation_is_the_approvers_own_act(app):
    base, runs = app
    s = upload(base, act_as(base, "alex.easton@acme.example"))
    rid = rid_for(s, "Vivian")
    viv = act_as(base, "vivian.fairfax@acme.example")
    assert "company" in call(base, f"/portal/request/{rid}/delegate", {"to_email": "pat@elsewhere.com"}, viv)[1]
    assert "Delegated" in call(base, f"/portal/request/{rid}/delegate", {"to_email": "cassie.sutton@acme.example", "to_name": "Cassie"}, viv)[1]
    cassie = act_as(base, "cassie.sutton@acme.example")
    page = call(base, f"/portal/request/{rid}", cookie=cassie)[1]
    assert "Delegated by the approver" in page and "Delegate this request" not in page  # no passing it on
    assert "can delegate" in call(base, f"/portal/request/{rid}/delegate", {"to_email": "chris.olsen@acme.example"}, cassie)[1]
    assert "Decision recorded" in call(base, f"/portal/request/{rid}/decide", {"decision": "approved", "text": "Fine."}, cassie)[1]
    msg = next((runs / s["run"] / "inbox").glob("*.md")).read_text()
    assert "From: Cassie Sutton" in msg and "Acting by delegation from: Vivian Fairfax, VP Finance" in msg


def test_a_question_keeps_the_request_open_and_tells_the_seller(app):
    base, runs = app
    alex = act_as(base, "alex.easton@acme.example")
    s = upload(base, alex)
    rid = rid_for(s, "Darla")
    darla = act_as(base, "darla.denkins@acme.example")
    assert "question was sent" in call(base, f"/portal/request/{rid}/ask", {"text": "Is this a renewal?"}, darla)[1]
    state = wait(base, alex)
    q = next(x for x in state["portal"] if x["id"] == rid)
    assert q["status"] == "open" and q["questions"][0]["text"] == "Is this a renewal?"
    assert any("Question about" in p.read_text() for p in (runs / s["run"] / "notifications").glob("*.txt"))


def test_unknown_recipient_stops_everything(app, tmp_path, monkeypatch):
    import shutil
    base, runs = app
    m = tmp_path / "matrix"
    shutil.copytree(server.MATRIX, m)
    lines = (m / "people.csv").read_text().splitlines()
    (m / "people.csv").write_text("\n".join(l for l in lines if not l.startswith("Deal Desk Manager")) + "\n")  # nobody holds that title
    monkeypatch.setattr(server, "MATRIX", m)
    server.CFG["matrix"]["folder"] = str(m)
    s = upload(base, act_as(base, "alex.easton@acme.example"))
    assert not s["outbox"] and "No approver in people.csv" in s["send_problem"]


def test_confirm_mode_waits_for_the_seller(app):
    base, _ = app
    server.CFG["portal"]["send_mode"] = "confirm"
    alex = act_as(base, "alex.easton@acme.example")
    s = upload(base, alex)
    assert not s["outbox"] and not s["portal"]
    st, text, _ = call(base, "/api/send", {"source": "stage3.md"}, alex, form=False)
    assert st == 200 and wait(base, alex)["portal"]


def test_local_logins_and_roles(app, tmp_path):
    base, _ = app
    users = tmp_path / "users.csv"
    auth.write_users(users, {e: {"Email": e, "Name": e, "Password hash": auth.hash_password("correct horse battery")}
                             for e in ("alex.easton@acme.example", "darla.denkins@acme.example")})
    server.CFG["auth"].update(provider="local", users_file=str(users))
    assert call(base, "/api/state")[0] == 401
    assert "did not match" in call(base, "/login", {"email": "alex.easton@acme.example", "password": "wrong"})[1]
    st, _, h = call(base, "/login", {"email": "alex.easton@acme.example", "password": "correct horse battery"})
    seller = h["Set-Cookie"].split(";")[0]
    assert st == 303 and "HttpOnly" in h["Set-Cookie"] and "SameSite=Lax" in h["Set-Cookie"]
    assert call(base, "/api/state", cookie=seller)[0] == 200
    _, _, h = call(base, "/login", {"email": "darla.denkins@acme.example", "password": "correct horse battery"})
    approver = h["Set-Cookie"].split(";")[0]
    assert call(base, "/api/state", cookie=approver)[0] == 403  # an approver is not a seller
    assert call(base, "/portal", cookie=approver)[0] == 200
    assert call(base, "/api/state", cookie=seller + "x")[0] == 401  # a tampered cookie is no cookie


def test_failed_logins_lock_the_address(app, tmp_path):
    base, _ = app
    users = tmp_path / "u.csv"
    auth.write_users(users, {"a@b.c": {"Email": "a@b.c", "Name": "A", "Password hash": auth.hash_password("correct horse battery")}})
    server.CFG["auth"].update(provider="local", users_file=str(users))
    auth.FAILS.clear()
    for _ in range(5):
        call(base, "/login", {"email": "a@b.c", "password": "no"})
    assert "did not match" in call(base, "/login", {"email": "a@b.c", "password": "correct horse battery"})[1]
    auth.FAILS.clear()


def test_proxy_header_provider(app):
    base, _ = app
    server.CFG["auth"].update(provider="proxy-header")
    assert call(base, "/api/state")[0] == 401
    assert call(base, "/api/state", headers={"X-Forwarded-Email": "alex.easton@acme.example"})[0] == 200
    assert call(base, "/api/state", headers={"X-Forwarded-Email": "stranger@x.com"})[0] == 403


def test_smtp_backend_sends_with_cc(monkeypatch, tmp_path):
    sent = {}

    class FakeSMTP:
        def __init__(self, host, port, timeout=0): sent["host"] = (host, port)
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def starttls(self): sent["tls"] = True
        def login(self, u, p): sent["login"] = (u, p)
        def send_message(self, msg, to_addrs): sent["msg"], sent["to"] = msg, to_addrs

    monkeypatch.setattr(notify.smtplib, "SMTP", FakeSMTP)
    monkeypatch.setenv("MAIL_PW", "pw")
    cfg = {"backend": "smtp", "host": "smtp.x", "port": 587, "starttls": True, "user": "u", "password_env": "MAIL_PW", "from_address": "no-reply@x"}
    notify.send(cfg, tmp_path, ["a@x"], ["b@x", "a@x", ""], "Subject", "Body")
    assert sent["to"] == ["a@x", "b@x"] and sent["tls"] and sent["login"] == ("u", "pw") and sent["msg"]["Cc"] == "b@x"
