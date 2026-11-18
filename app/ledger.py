"""The approvals ledger: one append-only SQLite file for auditing approvers and terms over time.

Rows are added and never changed or deleted: triggers in the database refuse UPDATE and DELETE. A
correction is a new row that names the row it corrects. Standard library only.
"""
import csv
import hashlib
import io
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

TABLES = {
    "deals": """run TEXT PRIMARY KEY, deal_id TEXT, created_at TEXT, seller_email TEXT, customer TEXT, annual_fees REAL,
                term_months INTEGER, tier TEXT, filename TEXT, kind TEXT""",
    "decisions": """id INTEGER PRIMARY KEY AUTOINCREMENT, request_id TEXT, run TEXT, deal_id TEXT, requested_at TEXT, decided_at TEXT,
                response_hours REAL, subject TEXT, approver_title TEXT, approver_name TEXT, approver_email TEXT, acting_for TEXT,
                decision TEXT, words TEXT, matrix_version TEXT, approved_by_rule TEXT DEFAULT '', corrects INTEGER, simulated INTEGER DEFAULT 0""",
    "record_rows": """id INTEGER PRIMARY KEY AUTOINCREMENT, snapshot_at TEXT, run TEXT, deal_id TEXT, stage TEXT, row_id TEXT, change TEXT,
                matrix_row_level TEXT, approver TEXT, decision_words TEXT, status TEXT, conditions TEXT, final_outcome TEXT, matrix_version TEXT""",
    "request_events": """id INTEGER PRIMARY KEY AUTOINCREMENT, request_id TEXT, run TEXT, deal_id TEXT, at TEXT, event TEXT,
                approver_title TEXT, approver_name TEXT, detail TEXT""",
    "matrix_versions": "hash TEXT PRIMARY KEY, first_seen TEXT, files_json TEXT",
    "deal_events": "id INTEGER PRIMARY KEY AUTOINCREMENT, run TEXT, deal_id TEXT, at TEXT, event TEXT, by_email TEXT, detail TEXT",
}
MATRIX_FILES = ("doa_matrix.csv", "roles.csv", "people.csv", "settings.csv")
APPROVED = ("Approved", "Approved (pre-approved)", "Conditional")


def now():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def connect(path):
    db = sqlite3.connect(path, timeout=15)
    db.row_factory = sqlite3.Row
    for name, cols in TABLES.items():
        db.execute(f"CREATE TABLE IF NOT EXISTS {name} ({cols})")
        for op in ("UPDATE", "DELETE"):
            db.execute(f"CREATE TRIGGER IF NOT EXISTS {name}_no_{op.lower()} BEFORE {op} ON {name} "
                       "BEGIN SELECT RAISE(ABORT, 'the ledger is append-only'); END")
    cols = {r[1] for r in db.execute("PRAGMA table_info(decisions)")}
    if "simulated" not in cols:  # a ledger made before demo mode existed
        db.execute("ALTER TABLE decisions ADD COLUMN simulated INTEGER DEFAULT 0")
    return db


def matrix_version(db, matrix_dir):
    """A short hash of the four matrix files. The files are stored once per version so it can be reconstructed."""
    files = {n: (Path(matrix_dir) / n).read_text(encoding="utf-8") for n in MATRIX_FILES if (Path(matrix_dir) / n).exists()}
    h = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()[:12]
    db.execute("INSERT OR IGNORE INTO matrix_versions VALUES (?,?,?)", (h, now(), json.dumps(files)))
    return h


def deal_id_of(run):
    f = Path(run) / "upload.json"
    return (json.loads(f.read_text()).get("deal_id") or Path(run).name) if f.exists() else Path(run).name


def add_deal(cfg, run, seller, deal, filename, kind):
    db = connect(cfg["ledger"]["path"])
    with db:
        db.execute("INSERT OR IGNORE INTO deals VALUES (?,?,?,?,?,?,?,?,?,?)",
                   (Path(run).name, deal_id_of(run), now(), seller, deal.get("customer", ""), deal.get("annual_fees"),
                    deal.get("term_months"), deal.get("tier", ""), filename, kind))
    db.close()


def add_deal_event(cfg, run, event, by="", detail=""):
    """What happened to a whole deal, such as archived. The ledger keeps it after the deal leaves the seller's list."""
    db = connect(cfg["ledger"]["path"])
    with db:
        db.execute("INSERT INTO deal_events (run,deal_id,at,event,by_email,detail) VALUES (?,?,?,?,?,?)",
                   (Path(run).name, deal_id_of(run), now(), event, by, detail))
    db.close()


def add_event(cfg, run, q, event, detail=""):
    """created, delegated, question, reminder, escalated. Silence shows up here, since it never makes a decision row."""
    db = connect(cfg["ledger"]["path"])
    with db:
        db.execute("INSERT INTO request_events (request_id,run,deal_id,at,event,approver_title,approver_name,detail) VALUES (?,?,?,?,?,?,?,?)",
                   (q["id"], Path(run).name, deal_id_of(run), now(), event, q["to_title"], q["to_name"], detail))
    db.close()


def add_decision(cfg, run, q, who, decision, words):
    db = connect(cfg["ledger"]["path"])
    hours = None
    try:
        hours = round((datetime.fromisoformat(q["decision"]["at"]) - datetime.fromisoformat(q["created"])).total_seconds() / 3600, 2)
    except (ValueError, TypeError, KeyError):
        pass
    with db:
        mv = matrix_version(db, cfg["matrix"]["folder"])
        db.execute("INSERT INTO decisions (request_id,run,deal_id,requested_at,decided_at,response_hours,subject,approver_title,approver_name,"
                   "approver_email,acting_for,decision,words,matrix_version,simulated) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                   (q["id"], Path(run).name, deal_id_of(run), q["created"], q["decision"]["at"], hours, q["subject"], q["to_title"],
                    who["name"], who["email"], q["decision"]["acting_for"], decision, words, mv, int(bool(q["decision"].get("simulated")))))
    db.close()


def parse_record(text):
    """Rows of the approval record table (the one with 'Matrix row and level' and 'Status' columns)."""
    lines = [l.strip() for l in text.split("\n")]
    for i, l in enumerate(lines):
        if l.startswith("|") and "matrix row" in l.lower() and "status" in l.lower() and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|?$", lines[i + 1]):
            cells = lambda r: [c.strip() for c in r.strip("|").split("|")]
            head = [h.lower() for h in cells(l)]
            col = lambda *keys: next((j for j, h in enumerate(head) if any(k in h for k in keys)), None)
            idx = {"row_id": col("id"), "change": col("change"), "matrix_row_level": col("matrix row"), "approver": col("approver"),
                   "decision_words": col("decision"), "status": col("status"), "conditions": col("condition"), "final_outcome": col("final")}
            out = []
            for r in lines[i + 2:]:
                if not r.startswith("|"):
                    break
                c = cells(r)
                out.append({k: (c[j] if j is not None and j < len(c) else "") for k, j in idx.items()})
            return out
    return []


def add_record(cfg, run, stage, text):
    rows = parse_record(text)
    if not rows:
        return 0
    db = connect(cfg["ledger"]["path"])
    with db:
        mv = matrix_version(db, cfg["matrix"]["folder"])
        for r in rows:
            db.execute("INSERT INTO record_rows (snapshot_at,run,deal_id,stage,row_id,change,matrix_row_level,approver,decision_words,status,"
                       "conditions,final_outcome,matrix_version) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                       (now(), Path(run).name, deal_id_of(run), stage, r["row_id"], r["change"], r["matrix_row_level"], r["approver"],
                        r["decision_words"], r["status"], r["conditions"], r["final_outcome"], mv))
    db.close()
    return len(rows)


BANDS = ("CASE WHEN d.annual_fees IS NULL THEN 'Not given' WHEN d.annual_fees < 100000 THEN 'Under $100K' "
         "WHEN d.annual_fees < 500000 THEN '$100K to $500K' WHEN d.annual_fees < 1000000 THEN '$500K to $1M' ELSE '$1M and over' END")

VIEWS = {
    "responsiveness": ("Responsiveness", """SELECT e.approver_title AS "Title", e.approver_name AS "Approver",
        COUNT(DISTINCT CASE WHEN e.event='created' THEN e.request_id END) AS "Received", COUNT(DISTINCT x.request_id) AS "Decided",
        SUM(e.event='reminder') AS "Reminders", SUM(e.event='escalated') AS "Escalations"
        FROM request_events e LEFT JOIN decisions x ON x.request_id = e.request_id AND e.event='created'
        GROUP BY e.approver_title, e.approver_name ORDER BY 3 DESC""", ("Decided", "Escalations")),
    "approvers": ("Approvers", """SELECT approver_title AS "Title", approver_name AS "Decided by", COUNT(*) AS "Requests",
        SUM(decision='Approved') AS "Approved", SUM(decision='Approved with conditions') AS "With conditions", SUM(decision='Denied') AS "Denied",
        ROUND(AVG(response_hours),1) AS "Avg hours to decide", SUM(acting_for<>'') AS "By delegation"
        FROM decisions GROUP BY approver_title, approver_name ORDER BY COUNT(*) DESC""", ("Approved", "With conditions", "Denied")),
    "terms": ("Terms", """SELECT matrix_row_level AS "Matrix row and level", COUNT(*) AS "Changes",
        SUM(status IN ('Approved','Approved (pre-approved)','Conditional')) AS "Approved or conditional",
        SUM(status='Denied') AS "Denied", SUM(status NOT IN ('Approved','Approved (pre-approved)','Conditional','Denied')) AS "Other"
        FROM record_rows WHERE id IN (SELECT MAX(id) FROM record_rows GROUP BY run, row_id) GROUP BY matrix_row_level ORDER BY COUNT(*) DESC""",
              ("Approved or conditional", "Denied", "Other")),
    "deal-size": ("Deal size", f"""SELECT {BANDS} AS "Annual fees", COUNT(*) AS "Requests",
        SUM(x.decision='Approved') AS "Approved", SUM(x.decision='Approved with conditions') AS "With conditions", SUM(x.decision='Denied') AS "Denied"
        FROM decisions x LEFT JOIN deals d ON d.run = x.run GROUP BY 1 ORDER BY COUNT(*) DESC""", ("Approved", "With conditions", "Denied")),
}


def view(cfg, key):
    """Rows of one audit view. A rate is shown only when the group has at least min_requests rows; counts always are."""
    title, sql, rate_cols = VIEWS[key]
    db = connect(cfg["ledger"]["path"])
    rows = [dict(r) for r in db.execute(sql)]
    db.close()
    n_key = next(k for k in rows[0].keys() if k in ("Requests", "Changes", "Received")) if rows else None
    minimum = cfg["ledger"]["min_requests"]
    for r in rows:
        r["_enough"] = r[n_key] >= minimum
        for c in rate_cols:
            r[c + " rate"] = f"{round(100 * r[c] / r[n_key])}%" if r["_enough"] and r[n_key] else "too few requests"
    return title, rows, rate_cols


def export(cfg, table):
    if table not in TABLES:
        raise ValueError("Unknown table.")
    db = connect(cfg["ledger"]["path"])
    cur = db.execute(f"SELECT * FROM {table}")
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow([d[0] for d in cur.description])
    w.writerows(cur.fetchall())
    db.close()
    return buf.getvalue()
