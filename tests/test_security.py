"""Things that must not be possible, checked through the real handlers."""
import http.client
import json
import time
from pathlib import Path

import server
from test_ledger import SELLER, up
from test_portal import act_as, app, call, wait  # noqa: F401


def state_run(base, cookie):
    return json.loads(call(base, "/api/state", cookie=cookie)[1])["run"]


def test_resume_cannot_point_outside_the_runs_folder(app):
    base, runs = app
    seller = act_as(base, SELLER)
    s = up(base, seller)
    for bad in ("../", "..", "../../..", "app-20261113-104345/../..", "/etc", ""):
        st, text, _ = call(base, "/api/resume", {"run": bad}, seller, form=False)
        assert state_run(base, seller) == s["run"], bad
    outside = runs.parent / "outside"
    outside.mkdir(exist_ok=True)
    call(base, "/api/resume", {"run": "../outside"}, seller, form=False)
    assert state_run(base, seller) == s["run"]
    st, text, _ = call(base, "/api/resume", {"run": s["run"]}, seller, form=False)
    assert st == 200 and json.loads(text)["run"] == s["run"]


def test_oversized_request_is_refused_before_it_is_read(app):
    base, _ = app
    host, port = base.replace("http://", "").split(":")
    c = http.client.HTTPConnection(host, int(port))
    c.putrequest("POST", "/api/upload")
    c.putheader("Content-Length", str(server.MAX_BODY + 1))
    c.putheader("Content-Type", "application/json")
    c.endheaders()
    assert c.getresponse().status == 413


def test_post_from_another_site_is_refused(app, monkeypatch):
    base, _ = app
    monkeypatch.setattr(server, "BASE_ORIGIN", "https://sellersassociate.com")
    server.CFG["portal"]["base_url"] = "https://sellersassociate.com"
    seller = act_as(base, SELLER)
    st, text, _ = call(base, "/api/send", {"source": "stage3.md"}, seller, headers={"Origin": "https://evil.example"}, form=False)
    assert st == 403 and "sellersassociate.com" in text
    st, text, _ = call(base, "/portal/request/RQ-00/decide", {"decision": "approved"}, seller, headers={"Origin": "https://evil.example"})
    assert st == 403
    st, _, _ = call(base, "/act-as", {"email": SELLER}, headers={"Origin": "https://sellersassociate.com"})
    assert st == 303  # the real site is fine


def test_a_failed_login_is_logged(app, tmp_path, capsys):
    import auth
    base, _ = app
    users = tmp_path / "u.csv"
    auth.write_users(users, {"a@b.c": {"Email": "a@b.c", "Name": "A", "Password hash": auth.hash_password("correct horse battery")}})
    server.CFG["auth"].update(provider="local", users_file=str(users))
    auth.FAILS.clear()
    call(base, "/login", {"email": "a@b.c", "password": "no"})
    assert "login failed for a@b.c" in capsys.readouterr().out
    auth.FAILS.clear()


def test_no_traversal_in_file_routes(app):
    base, _ = app
    for p in ("/files/../config.toml", "/files/case-1/../../x", "/files/standard.docx/../../app/server.py", "/../app/server.py"):
        st, text, _ = call(base, p, cookie=act_as(base, SELLER))
        assert st in (404, 303) and "def main" not in text


def test_sellers_do_not_share_a_deal_or_see_each_others_runs(app, tmp_path, monkeypatch):
    import shutil
    base, runs = app
    matrix = tmp_path / "matrix"
    shutil.copytree(server.MATRIX, matrix)
    with open(matrix / "sellers.csv", "a", encoding="utf-8") as f:
        f.write("sam.second@acme.example,Sam Second,Enterprise\n")
    monkeypatch.setattr(server, "MATRIX", matrix)
    alex, sam = act_as(base, SELLER), act_as(base, "sam.second@acme.example")
    a = up(base, alex)
    assert state_run(base, alex) == a["run"] and state_run(base, sam) is None  # Sam has no deal open
    b = up(base, sam)
    assert b["run"] != a["run"] and state_run(base, alex) == a["run"]  # Sam's upload did not move Alex
    names = lambda c, k: [r["name"] for r in json.loads(call(base, "/api/state", cookie=c)[1])[k]]
    assert a["run"] not in names(sam, "upload_runs") and b["run"] not in names(alex, "upload_runs")
    call(base, "/api/resume", {"run": b["run"]}, alex, form=False)  # Alex cannot open Sam's deal
    assert state_run(base, alex) == a["run"]
    assert json.loads(call(base, f"/api/state?run={b['run']}", cookie=alex)[1])["run"] is None  # nor name it directly


def test_a_staged_example_is_a_separate_deal_labelled_demo(app):
    base, runs = app
    alex = act_as(base, SELLER)
    mine = up(base, alex)
    st, text, _ = call(base, "/api/start", {"case": "case-1", "run": ""}, alex, form=False)
    demo_run = json.loads(text)["run"]
    assert demo_run != mine["run"]
    deals = json.loads(call(base, f"/api/state?run={mine['run']}", cookie=alex)[1])["deals"]
    by_name = {d["name"]: d for d in deals}
    assert by_name[demo_run]["demo"] is True and by_name[mine["run"]]["demo"] is False
    # starting the demo did not change the real deal
    assert json.loads(call(base, f"/api/state?run={mine['run']}", cookie=alex)[1])["upload"]["filename"] == "r.docx"


def test_all_three_staged_examples_run_through_the_upload_path(app):
    base, runs = app
    alex = act_as(base, SELLER)
    for cid in ("case-1", "case-2", "case-3"):
        st, text, _ = call(base, "/api/start", {"case": cid, "run": ""}, alex, form=False)
        assert st == 200, text
        run = json.loads(text)["run"]
        s = None
        for _ in range(100):
            s = json.loads(call(base, f"/api/state?run={run}", cookie=alex)[1])
            if s["job"]["status"] != "running":
                break
            time.sleep(0.05)
        assert s["job"]["status"] == "done", s["job"]
        assert s["upload"]["demo"] is True and s["upload"]["differences"] >= 5 and s["portal"], cid
    assert call(base, "/api/start", {"case": "case-9", "run": ""}, alex, form=False)[0] == 400
