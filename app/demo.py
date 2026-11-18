"""Demo mode: the AI plays each approver, so the whole process can be shown without waiting for people.

An AI-played approver sees only the request, the deal profile and the matrix rows where its own title has
authority. It never sees answer keys or other approvers' replies. Its decision goes through the same
portal code a real approver uses, and is marked simulated everywhere. Demo mode never sends email.
"""
import csv
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

import portal

PROMPT = Path(__file__).resolve().parents[1] / "playbook" / "demo" / "approver.md"
CLOCK = {"days": 0}  # days the demo clock has been moved forward


def today():
    return date.today() + timedelta(days=CLOCK["days"])


def advance_to_next_business_day(holidays=()):
    while True:
        CLOCK["days"] += 1
        d = today()
        if d.weekday() < 5 and d.isoformat() not in set(holidays):
            return d


def _role(matrix, title):
    with open(Path(matrix) / "roles.csv", newline="", encoding="utf-8") as f:
        return next((r for r in csv.DictReader(f) if r["Title"] == title), {})


def authority_rows(matrix, title):
    """The matrix rows in which this title appears at any level, as plain text."""
    role = _role(matrix, title)
    names = [n for n in (title, role.get("Short title", "")) if n]
    out = []
    with open(Path(matrix) / "doa_matrix.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            hits = [lv for lv, cell in row.items() if lv.startswith("Level") and any(re.search(r"\b" + re.escape(n) + r"\b", cell) for n in names)]
            if hits:
                out.append(f"- {row['Term']}. Standard: {row['Standard position']}. "
                           + " ".join(f"{lv}: {row[lv]}." for lv in row if lv.startswith("Level") and row[lv])
                           + (f" Not approvable: {row['Not approvable']}." if row.get("Not approvable") else "")
                           + f" (Your title is at {', '.join(hits)}.)")
    return out


def prompt_for(cfg, run, q):
    matrix = cfg["matrix"]["folder"]
    role = _role(matrix, q["to_title"])
    rows = authority_rows(matrix, q["to_title"]) or ["(Your title is not named in any matrix row.)"]
    request = (Path(run) / "outbox" / q["file"]).read_text(encoding="utf-8")
    profile = (Path(run) / "deal-profile.md").read_text(encoding="utf-8") if (Path(run) / "deal-profile.md").exists() else ""
    return (PROMPT.read_text(encoding="utf-8").replace("{name}", q["to_name"]).replace("{title}", q["to_title"])
            .replace("{role_notes}", role.get("Notes") or role.get("Function") or "").replace("{rows}", "\n".join(rows))
            .replace("{request}", request).replace("{profile}", profile))


def parse(text):
    d = re.search(r"(?mi)^\W*DECISION:?\W*(approved|conditional|denied)", text)
    r = re.search(r"(?is)REPLY:\s*(.+)", text)
    return (d.group(1).lower(), r.group(1).strip()) if d and r else None


REFERRAL_PROMPT = Path(__file__).resolve().parent / "prompts" / "demo_referral.md"


def parse_referral(text):
    d = re.search(r"(?mi)^\W*DECISION:?\W*(approved|conditional|denied|none_needed)", text)
    a = re.search(r"(?mi)^\W*AUTHORITY:?\W*(.+)$", text)
    r = re.search(r"(?is)REPLY:\s*(.+)", text)
    return (d.group(1).lower(), a.group(1).strip(), (r.group(1).strip() if r else "")) if d and a else None


def referral_prompt(cfg, run, q):
    request = (Path(run) / "outbox" / q["file"]).read_text(encoding="utf-8")
    return REFERRAL_PROMPT.read_text(encoding="utf-8").replace("{name}", q["to_name"]).replace("{title}", q["to_title"]).replace("{request}", request)


def play(cfg, runs, run, ask, log=print):
    """Answer every open request in this run, all at the same time. Returns what happened, in request order."""
    d = cfg["demo"]
    matrix = cfg["matrix"]["folder"]
    todo = [q for q in portal.load(run) if q["status"] == "open"]

    def one(q):
        who = portal.role_of(q["to_email"], matrix)
        if q["to_title"] in d["silent_titles"]:
            return f"{q['id']}: silent (demo scenario)"
        time.sleep(d["delay_seconds"])
        if q["to_title"] in d["delegating_titles"]:
            fb = next((p for p in portal.people(matrix) if p["Email"].lower() == q["to_email"]), {}).get("Fallback email", "")
            if fb:
                portal.delegate(run, q["id"], who, fb, "", cfg)
                q = next(x for x in portal.load(run) if x["id"] == q["id"])
                who = portal.role_of(fb, matrix)
                who["name"] = who["name"] or fb
        if q.get("kind") == "referral":
            try:
                got = parse_referral(ask(referral_prompt(cfg, run, q)))
            except Exception as e:
                log(f"demo Deal Desk for {q['id']} failed: {e}")
                return f"{q['id']}: failed"
            if not got:
                return f"{q['id']}: no answer"
            decision, authority, text = got
            if decision == "conditional" and not text:
                text = "Conditions as stated in my reply."
            portal.decide(run, q["id"], who, decision, text, cfg, simulated=True, authority=authority)
            return f"{q['id']}: {decision}"
        try:
            got = parse(ask(prompt_for(cfg, run, q)))
        except Exception as e:
            log(f"demo approver for {q['id']} failed: {e}")
            return f"{q['id']}: failed"
        if not got:
            log(f"demo approver for {q['id']} gave no usable answer")
            return f"{q['id']}: no answer"
        decision, text = got
        if decision == "conditional" and not text:
            text = "Conditions as stated in my reply."
        portal.decide(run, q["id"], who, decision, text, cfg, simulated=True)
        return f"{q['id']}: {decision}"

    with ThreadPoolExecutor(max_workers=max(1, min(8, len(todo)))) as pool:
        return list(pool.map(one, todo))
