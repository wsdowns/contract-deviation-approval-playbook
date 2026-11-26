"""The approval portal: requests as data, decisions made by signed-in approvers.

A request is created when the seller's requests go out. The approver is told by email and decides on a
page: approve, approve with conditions, deny, delegate or ask a question. A decision is written to the
run's inbox in the same shape as a reply, so the recording stage reads it unchanged; the sender is the
signed-in person, not an address typed in a message.
"""
import csv
import html
import json
import os
import re
import secrets
import threading
from datetime import datetime, timezone
from pathlib import Path

import ledger
import notify

LOCK = threading.Lock()
esc = lambda s: html.escape(str(s), quote=True)
DECISIONS = {"approved": "Approved", "conditional": "Approved with conditions", "denied": "Denied"}
REFERRAL_OUTCOMES = {**DECISIONS, "none_needed": "No approval needed"}  # a term the matrix does not settle goes to the Deal Desk


def now():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _csv(path):
    p = Path(path)
    if not p.exists():
        return []
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def people(matrix):
    return _csv(Path(matrix) / "people.csv")


def sellers(matrix):
    return _csv(Path(matrix) / "sellers.csv")


def settings(matrix):
    return {r["Setting"]: r["Value"] for r in _csv(Path(matrix) / "settings.csv")}


def role_of(email, matrix):
    e = (email or "").lower()
    ppl = [p for p in people(matrix) if p["Email"].lower() == e]
    sel = [s for s in sellers(matrix) if s["Email"].lower() == e]
    return {"email": e, "name": (ppl or sel or [{"Name": e}])[0]["Name"], "title": ppl[0]["Title"] if ppl else "",
            "approver": bool(ppl), "seller": bool(sel)}


def resolve(to_text, matrix):
    """The person a drafted 'To:' line names, by email, then name, then title."""
    t = to_text.lower()
    ppl = people(matrix)
    for p in ppl:
        if p["Email"].lower() in t:
            return p
    for p in ppl:
        if p["Name"].lower() in t:
            return p
    for p in sorted(ppl, key=lambda p: -len(p["Title"])):
        if re.search(r"\b" + re.escape(p["Title"].lower()) + r"\b", t):
            return p
    return None


def _file(run):
    return Path(run) / "requests.json"


def load(run):
    f = _file(run)
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else []


def write(path, text):
    """Write a whole file or nothing, so a page that reads it at the same moment never sees half of it."""
    path = Path(path)
    tmp = path.with_name(f"{path.name}.{os.getpid()}-{threading.get_ident()}.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def _save(run, reqs):
    write(_file(run), json.dumps(reqs, indent=1))


def check_recipients(reqs, matrix):
    bad = [r["subject"] or r["to"] for r in reqs if not resolve(r["to"], matrix)]
    if bad:
        raise ValueError("No approver in people.csv matches the recipient of: " + "; ".join(bad) +
                         ". Nothing was sent. Fix the matrix or the request.")


def seller_email(run, matrix):
    f = Path(run) / "seller.txt"
    if f.exists():
        return f.read_text().strip()
    who = settings(matrix).get("Requester", "")
    return next((p["Email"] for p in people(matrix) if p["Title"] == who), "")


def _links(cfg, rid):
    return f"{cfg['portal']['base_url'].rstrip('/')}/portal/request/{rid}"


def create(run, reqs, files, cfg):
    """reqs: parsed requests; files: their outbox file names. Notifies each approver."""
    matrix = cfg["matrix"]["folder"]
    check_recipients(reqs, matrix)
    mailbox = settings(matrix).get("Approvals mailbox", "")
    me = seller_email(run, matrix)
    made = []
    with LOCK:
        cur = load(run)
        for r, fname in zip(reqs, files):
            p = resolve(r["to"], matrix)
            rid = "RQ-" + secrets.token_hex(5)
            made.append({"id": rid, "file": fname, "subject": r["subject"], "to_email": p["Email"].lower(), "to_name": p["Name"],
                         "to_title": p["Title"], "assigned": [p["Email"].lower()], "status": "open", "decision": None,
                         "delegations": [], "questions": [], "created": now(), "dev": r.get("dev", ""), "kind": r.get("kind") or "approval", "appeal_of": r.get("appeal_of", "")})
            if r.get("appeal_of"):  # one appeal per denial: the first one marks the denial, a second is refused
                orig = next((o for o in cur if o["id"] == r["appeal_of"]), None)
                if orig is None or orig.get("appealed"):
                    raise ValueError("This denial has already been appealed. The decision stands.")
                orig["appealed"] = rid
        _save(run, cur + made)
    for q in made:
        ledger.add_event(cfg, run, q, "created")
        notify.send(cfg["mail"], run, [q["to_email"]], [me, mailbox], f"Approval needed: {q['subject']}",
                    f"{q['to_name']},\n\nA contract change needs your decision as {q['to_title']}.\n\n{q['subject']}\n\n"
                    f"Open the request, read it and decide here:\n{_links(cfg, q['id'])}\n\n"
                    "Please decide in the portal. Replies to this email are not read.\n")
    return made


def denials(run):
    """Every denial in a deal, with where its one appeal stands: open (can be appealed), pending, or decided."""
    reqs = load(run)
    by = {q["id"]: q for q in reqs}
    out = []
    for q in reqs:
        if q["status"] != "decided" or q["decision"]["decision"] != "Denied" or q.get("appeal_of"):
            continue
        a = by.get(q.get("appealed", ""))
        d = q["decision"]
        row = {"request": q["id"], "dev": q.get("dev", ""), "approver": f"{q['to_name']}, {q['to_title']}",
               "words": d["text"] + (f" Authority or basis: {d['authority']}." if d.get("authority") else ""), "state": "open"}
        if a:
            row["state"] = "decided" if a["status"] == "decided" else "pending"
            if a["status"] == "decided":
                row["outcome"], row["outcome_words"] = a["decision"]["decision"], a["decision"]["text"]
        out.append(row)
    return out


def withdraw(run, cfg):
    """Withdraw every request in a deal that is still open: the approvers are told, and no reminder is sent for it again. Returns how many."""
    gone = []
    with LOCK:
        reqs = load(run)
        for q in reqs:
            if q["status"] == "open":
                q["status"], q["withdrawn_at"] = "withdrawn", now()
                gone.append(q)
        _save(run, reqs)
    matrix = cfg["matrix"]["folder"]
    for q in gone:
        ledger.add_event(cfg, run, q, "withdrawn")
        notify.send(cfg["mail"], run, [q["to_email"]], [seller_email(run, matrix), settings(matrix).get("Approvals mailbox", "")],
                    f"Withdrawn: {q['subject']}", f"The seller has withdrawn this request. No decision is needed.\n\n{q['subject']}\n")
    return len(gone)


def find(rid, runs):
    for run in sorted(Path(runs).glob("app-*")):
        for q in load(run):
            if q["id"] == rid:
                return run, q
    return None, None


def mine(email, runs):
    out = []
    for run in sorted(Path(runs).glob("app-*"), reverse=True):
        for q in load(run):
            if email.lower() in q["assigned"]:
                out.append((run, q))
    return out


INBOX_LOCK = threading.Lock()  # approvers may decide at the same moment (demo approvers do): each message needs its own number


def _inbox_message(run, q, who, kind, text, delegated_from, simulated=False):
    with INBOX_LOCK:
        _write_inbox(run, q, who, kind, text, delegated_from, simulated)


def _write_inbox(run, q, who, kind, text, delegated_from, simulated):
    box = Path(run) / "inbox"
    box.mkdir(exist_ok=True)
    k = len(list(box.glob("*.md"))) + 1
    slug = re.sub(r"[^a-z0-9]+", "-", q["subject"].lower()).strip("-")[:40]
    lines = [f"From: {who['name']} <{who['email']}>", "To: approvals mailbox", f"Date: {now()}",
             f"Subject: RE: {q['subject']}", f"Via: approval portal, signed in as {who['email']}"]
    if simulated:
        lines.append("Simulated: yes. This reply was written by an AI-played approver in demo mode. It is not a real approval.")
    if delegated_from:
        d = delegated_from
        lines.append(f"Acting by delegation from: {d['name']}, {d['title']} (delegated by them in the portal on {d['at']}). "
                     "Record the decision as this title's, and show both names.")
    body = f"Decision: {kind}\n\n{text.strip()}\n\n{who['name']}"
    (box / f"{k:02d}-portal-{slug}.md").write_text("\n".join(lines) + "\n\n" + body + "\n", encoding="utf-8")


AFTER_DECISION = None  # set by the server: called with the run folder once no request in it is still open


def decide(run, rid, who, decision, text, cfg, simulated=False, authority="", reference=""):
    """Record a decision by a signed-in person who holds the request. Raises ValueError with a plain message.

    A request referred to the Deal Desk (a term the matrix does not settle) also takes the authority or basis the
    Deal Desk relied on, in its own words, and an optional reference. The system records it; it cannot verify it."""
    with LOCK:
        reqs = load(run)
        q = next(x for x in reqs if x["id"] == rid)
        referral = q.get("kind") == "referral"
        table = REFERRAL_OUTCOMES if referral else DECISIONS
        if decision not in table:
            raise ValueError("Choose the outcome." if referral else "Choose Approve, Approve with conditions or Deny.")
        if decision == "conditional" and not text.strip():
            raise ValueError("Say what the conditions are.")
        if referral and not authority.strip():
            raise ValueError("Say who or what you relied on: a person and their title, a policy, or a fact. It is recorded as the authority for this outcome.")
        if who["email"] not in q["assigned"]:
            raise ValueError("This request is not assigned to you.")
        if q["status"] != "open":
            raise ValueError("This request was withdrawn by the seller." if q["status"] == "withdrawn" else "This request has already been decided.")
        d = next((x for x in q["delegations"] if x["to"] == who["email"]), None)
        body = text.strip() or ("Approved as requested." if decision == "approved" else f"{table[decision]}.")
        q["status"] = "decided"
        q["decision"] = {"by": who["email"], "name": who["name"], "decision": table[decision], "text": body, "at": now(),
                         "acting_for": d["by_email"] if d else "", "simulated": simulated}
        if referral:
            q["decision"].update(authority=authority.strip(), reference=reference.strip())
        _save(run, reqs)
    words = body + (f" Authority or basis: {authority.strip()}." + (f" Reference: {reference.strip()}." if reference.strip() else "") if referral else "")
    ledger.add_decision(cfg, run, q, who, table[decision], words)
    deleg = None
    if d:
        deleg = {"name": q["to_name"], "title": q["to_title"], "at": d["at"]}
    _inbox_message(run, q, who, table[decision], words, deleg, simulated)
    matrix = cfg["matrix"]["folder"]
    notify.send(cfg["mail"], run, [seller_email(run, matrix)], [q["to_email"], settings(matrix).get("Approvals mailbox", "")],
                f"Decision recorded: {q['subject']}", f"{who['name']} decided: {table[decision]}.\n\n{words}\n")
    if AFTER_DECISION and not any(x["status"] == "open" for x in load(run)):
        try:
            AFTER_DECISION(Path(run))
        except Exception as e:  # a failed snapshot must never undo a decision
            print("approval record snapshot failed:", e, flush=True)
    return q


def delegate(run, rid, who, to_email, to_name, cfg):
    if not cfg["portal"]["allow_delegation"]:
        raise ValueError("Delegation is switched off for this organization.")
    to_email = to_email.strip().lower()
    if "@" not in to_email or to_email.split("@")[1] != who["email"].split("@")[1]:
        raise ValueError("A delegate must have an address at your company.")
    if to_email == who["email"]:
        raise ValueError("Choose someone else.")
    with LOCK:
        reqs = load(run)
        q = next(x for x in reqs if x["id"] == rid)
        if who["email"] != q["to_email"]:
            raise ValueError("Only the approver named on the request can delegate it. A delegate cannot pass it on.")
        if q["status"] != "open":
            raise ValueError("This request has already been decided.")
        q["assigned"].append(to_email)
        q["delegations"].append({"by_email": who["email"], "to": to_email, "name": to_name.strip() or to_email, "at": now()})
        _save(run, reqs)
    ledger.add_event(cfg, run, q, "delegated", to_email)
    matrix = cfg["matrix"]["folder"]
    notify.send(cfg["mail"], run, [to_email], [who["email"], seller_email(run, matrix), settings(matrix).get("Approvals mailbox", "")],
                f"Approval delegated to you: {q['subject']}",
                f"{who['name']} ({q['to_title']}) has asked you to decide this on their behalf.\n\n{_links(cfg, rid)}\n")
    return q


def ask(run, rid, who, text, cfg):
    if not text.strip():
        raise ValueError("Write your question.")
    with LOCK:
        reqs = load(run)
        q = next(x for x in reqs if x["id"] == rid)
        if who["email"] not in q["assigned"]:
            raise ValueError("This request is not assigned to you.")
        q["questions"].append({"by": who["name"], "text": text.strip(), "at": now()})
        _save(run, reqs)
    ledger.add_event(cfg, run, q, "question")
    matrix = cfg["matrix"]["folder"]
    notify.send(cfg["mail"], run, [seller_email(run, matrix)], [who["email"], settings(matrix).get("Approvals mailbox", "")],
                f"Question about: {q['subject']}", f"{who['name']} asks:\n\n{text.strip()}\n\nThe request stays open.\n")
    return q


# ---------------------------------------------------------------- pages

CSS = """:root{--bg:#fafaf8;--card:#fff;--ink:#1f1f1d;--mute:#6b6a64;--line:#e3e1da;--acc:#185fa5;--no:#791f1f;--ok:#27500a}
@media(prefers-color-scheme:dark){:root{--bg:#1c1c1a;--card:#262624;--ink:#ecebe6;--mute:#a3a29a;--line:#3a3a37;--acc:#85b7eb;--no:#f7c1c1;--ok:#c0dd97}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
header{padding:14px 20px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap}
main{max-width:760px;margin:0 auto;padding:16px 20px 60px}.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin-bottom:14px}
h1{font-size:17px;margin:0;font-weight:500}h2{font-size:18px;font-weight:500;margin:0 0 6px}.mute{color:var(--mute);font-size:13px}
a{color:var(--acc)}pre{white-space:pre-wrap;font:13px/1.5 ui-monospace,Menlo,monospace;background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:10px}
label{display:block;margin:8px 0}input[type=text],input[type=email],input[type=password],textarea,select{width:100%;font:inherit;padding:8px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--ink)}
button{font:inherit;padding:8px 16px;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--ink);cursor:pointer;margin:4px 6px 4px 0}
button.go{background:var(--acc);border-color:var(--acc);color:var(--bg)}.err{border:1px solid var(--no);color:var(--no);border-radius:8px;padding:10px;margin-bottom:12px}
.chip{font-size:12px;padding:1px 8px;border-radius:8px;border:1px solid var(--line)}table{width:100%;border-collapse:collapse}td{border-top:1px solid var(--line);padding:6px 4px;vertical-align:top}"""


def page(title, body, user=None, status=200):
    who = f"{esc(user['name'])} · <a href='/logout'>Sign out</a>" if user else ""
    return status, ("<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
                    f"<title>{esc(title)}</title><style>{CSS}</style><header><h1>ACME Corporation · Seller's Associate</h1>"
                    f"<span class=mute>{who}</span></header><main>{body}</main>")


def login_page(error=""):
    e = f"<div class=err>{esc(error)}</div>" if error else ""
    return page("Sign in", f"<div class=card><h2>Sign in</h2>{e}<form method=post action=/login><label>Email<input type=email name=email required autofocus></label>"
                "<label>Password<input type=password name=password required></label><button class=go>Sign in</button></form></div>")


def actas_page(matrix, error=""):
    opts = "".join(f"<option value='{esc(p['Email'])}'>{esc(p['Name'])}, {esc(p['Title'])}</option>" for p in people(matrix))
    opts += "".join(f"<option value='{esc(s['Email'])}'>{esc(s['Name'])}, seller</option>" for s in sellers(matrix))
    return page("Demo sign-in", "<div class=card><h2>Demo: act as</h2><p class=mute>Demo mode has no passwords. Pick who you are acting as. "
                "Real use needs a login method in config.toml.</p>"
                f"<form method=post action=/act-as><label>Act as<select name=email>{opts}</select></label><button class=go>Continue</button></form></div>")


def list_page(user, runs):
    rows = ""
    for run, q in mine(user["email"], runs):
        state = ("<span class=chip>Open</span>" if q["status"] == "open" else "<span class=chip>Withdrawn</span>" if q["status"] == "withdrawn"
                 else f"<span class=chip>{esc(q['decision']['decision'])}</span>")
        rows += f"<tr><td><a href='/portal/request/{q['id']}'>{esc(q['subject'])}</a></td><td>{state}</td><td class=mute>{esc(q['created'][:10])}</td></tr>"
    body = ("<div class=card><h2>Your requests</h2>" + (f"<table>{rows}</table>" if rows else "<p class=mute>Nothing is waiting for you.</p>") + "</div>")
    return page("Your requests", body, user)


REFERRAL_CARD = ("<div class=card><h2>Your response</h2>"
                 "<p class=mute>The matrix does not settle this change. Find out what is needed, get any approval required, then record the outcome here "
                 "and the authority you relied on.</p>"
                 "<form method=post action='/portal/request/{id}/decide'>"
                 "<label><input type=radio name=decision value=approved required> Approved: the change can go ahead as written</label>"
                 "<label><input type=radio name=decision value=conditional> Approved with conditions</label>"
                 "<label><input type=radio name=decision value=denied> Not approved: the customer must change or drop it</label>"
                 "<label><input type=radio name=decision value=none_needed> No approval needed</label>"
                 "<label>Authority or basis (required). Who or what you relied on: a person and their title, a policy, or a fact, "
                 "for example &quot;Operations confirmed we ship by registered mail&quot;."
                 "<textarea name=authority rows=3 required></textarea></label>"
                 "<label>Reference (optional): an email subject, ticket number or document name<input type=text name=reference></label>"
                 "<label>Conditions or notes. Required if you chose conditions."
                 "<textarea name=text rows=3></textarea></label><button class=go>Record my response</button></form></div>")


def request_page(user, run, q, error="", note=""):
    text = (Path(run) / "outbox" / q["file"]).read_text(encoding="utf-8")
    e = f"<div class=err>{esc(error)}</div>" if error else ""
    who = f"<p class=mute>Addressed to {esc(q['to_name'])}, {esc(q['to_title'])}.</p>"
    hist = ""
    for d in q["delegations"]:
        hist += f"<p class=mute>Delegated by the approver to {esc(d['name'])} on {esc(d['at'])}.</p>"
    for x in q["questions"]:
        hist += f"<p class=mute>Question from {esc(x['by'])} on {esc(x['at'])}: {esc(x['text'])}</p>"
    if q["status"] == "withdrawn":
        form = f"<div class=card><h2>Withdrawn by the seller</h2><p>No decision is needed. The seller withdrew this request on {esc(q.get('withdrawn_at', ''))}.</p></div>"
    elif q["status"] != "open":
        dd = q["decision"]
        auth = (f"<p>Authority or basis: {esc(dd['authority'])}" + (f" (reference: {esc(dd['reference'])})" if dd.get("reference") else "") + "</p>") if dd.get("authority") else ""
        form = f"<div class=card><h2>Decided: {esc(dd['decision'])}{' (simulated)' if dd.get('simulated') else ''}</h2><p>{esc(dd['text'])}</p>{auth}<p class=mute>{esc(dd['name'])}, {esc(dd['at'])}</p></div>"
    else:
        can_delegate = user["email"] == q["to_email"]
        dele = ("<h3>Delegate this request</h3><p class=mute>Choose someone at your company to decide it for you. They cannot pass it on.</p>"
                "<form method=post action='/portal/request/%s/delegate'><label>Their email<input type=email name=to_email required></label>"
                "<label>Their name<input type=text name=to_name></label><button>Delegate</button></form>" % q["id"]) if can_delegate else ""
        card = (REFERRAL_CARD.replace("{id}", q["id"]) if q.get("kind") == "referral" else
                ("<div class=card><h2>Your decision</h2>"
                 f"<form method=post action='/portal/request/{q['id']}/decide'>"
                 "<label><input type=radio name=decision value=approved required> Approve as requested</label>"
                 "<label><input type=radio name=decision value=conditional> Approve with conditions</label>"
                 "<label><input type=radio name=decision value=denied> Deny</label>"
                 "<label>Say exactly what you approve, your conditions, or your reason. This is recorded in your words."
                 "<textarea name=text rows=5></textarea></label><button class=go>Record my decision</button></form></div>"))
        form = (card +
                f"<div class=card><h3>Ask the seller a question</h3><form method=post action='/portal/request/{q['id']}/ask'>"
                "<label><textarea name=text rows=3></textarea></label><button>Send question</button></form></div>"
                f"<div class=card>{dele}</div>")
    n = f"<p class=mute>{esc(note)}</p>" if note else ""
    return page(q["subject"], f"<p><a href=/portal>All requests</a></p>{e}{n}<div class=card><h2>{esc(q['subject'])}</h2>{who}{hist}<pre>{esc(text)}</pre></div>{form}", user)


def may_audit(user, cfg):
    """The matrix owner, plus anyone listed under [ledger] viewers."""
    matrix = cfg["matrix"]["folder"]
    owner = settings(matrix).get("Matrix owner", "")
    owners = [x["Email"].lower() for x in people(matrix) if x["Title"] == owner]
    return user["email"] in owners or user["email"] in [v.lower() for v in cfg["ledger"]["viewers"]]


def audit_page(user, cfg):
    n = cfg["ledger"]["min_requests"]
    body = ("<div class=card><h2>Audit the approvers</h2><p class=mute>Each figure is a question for the matrix owner, not a verdict. "
            "An approver who always approves may be rubber-stamping, or the matrix may be sending them requests that never needed escalating. "
            "One who never approves may be a blocker, or sellers may only ask for what is out of bounds. Sellers also send the requests they expect to win. "
            f"Rates appear only once a group has {n} requests.</p></div>")
    for key in ledger.VIEWS:
        title, rows, rate_cols = ledger.view(cfg, key)
        if not rows:
            body += f"<div class=card><h2>{esc(title)}</h2><p class=mute>No data yet.</p></div>"
            continue
        cols = [c for c in rows[0] if not c.startswith("_")]
        head = "".join(f"<th>{esc(c)}</th>" for c in cols)
        trs = "".join("<tr>" + "".join(f"<td>{esc(r[c] if r[c] is not None else '')}</td>" for c in cols) + "</tr>" for r in rows)
        body += f"<div class=card><h2>{esc(title)}</h2><div style='overflow-x:auto'><table><tr>{head}</tr>{trs}</table></div></div>"
    links = " · ".join(f"<a href='/audit/export/{t}.csv'>{t}.csv</a>" for t in ("decisions", "request_events", "record_rows", "deals", "deal_events", "matrix_versions"))
    body += f"<div class=card><h2>Export</h2><p class=mute>{links}</p><p class=mute>The ledger holds approvers' names and customers' deal facts. Treat it as confidential.</p></div>"
    return page("Audit", body, user)
