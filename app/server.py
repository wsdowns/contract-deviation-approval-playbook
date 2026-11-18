"""Seller app for the Contract Deviation Approval Playbook.

A small local web app. It runs the playbook prompts through the `claude` command
(Claude Code), keeps a simulated approvals mailbox on disk, and shows the seller
one screen per step. Standard library only.

    python app/server.py            # then open http://localhost:8765
    DOA_STUB=1 python app/server.py # canned model output, for testing the app itself
"""
import csv
import difflib
import json
import os
import re
import subprocess
import tempfile
import threading
import time
from collections.abc import MutableMapping
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import base64
import config as appconfig
import auth
import contract_io
import demo
import models
import ledger
import notify  # noqa: F401
import routing
import locate
import assess
import finalcheck
import record as recordmod
import portal
import reminders
from http.cookies import SimpleCookie
from urllib.parse import urlsplit, parse_qs

EXAMPLE = ROOT / "examples" / "acme-saas"
CASES_DIR = EXAMPLE / "cases"
CFG = appconfig.load()
MATRIX = Path(CFG["matrix"]["folder"])
PLAYBOOK = ROOT / "playbook"
RUNS = ROOT / "runs"
STATIC = Path(__file__).resolve().parent / "static"
STUB = os.environ.get("DOA_STUB") == "1"

DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

# The three cases. "paper" is what the customer sent; the app reads it as the contract under review.
CASES = {
    "case-1": {"dir": "case-1-acme-redline", "title": "Brightwater Logistics, Case 1", "kind": "redline",
               "paper": "redline.md",
               "docx": "Brightwater_Redline_of_ACME_SaaS_Agreement.docx", "label": "Brightwater redline (Word, tracked changes)",
               "deal": {"customer": "Brightwater Logistics, Inc.", "annual_fees": "20000", "term_months": "12", "tier": "standard"},
               "final": "Net 45 agreed. 2x liability cap agreed. 99.9% availability with 15% credits agreed. Renewal increase capped at 5%. Logo right removed."},
    "case-2": {"dir": "case-2-lakeshore-paper", "title": "Lakeshore Health, Case 2", "kind": "redline",
               "paper": "Lakeshore_Health_SaaS_Agreement.txt",  # the original customer-paper draft, kept for the old prepared-reply tests only
               "docx": "Lakeshore_Redline_of_ACME_SaaS_Agreement.docx", "label": "Lakeshore redline (Word, tracked changes)",
               "deal": {"customer": "Lakeshore Health, Inc.", "annual_fees": "1000000", "term_months": "36", "tier": "strategic"},
               "final": "Illinois law and Cook County courts agreed. US-only storage agreed. Termination for convenience agreed. Cap of the greater of 3x fees or $5M agreed. Most-favored pricing removed. HITRUST certification agreed."},
    "case-3": {"dir": "case-3-acme-redline-2", "title": "Summit Ridge Manufacturing, Case 3", "kind": "redline",
               "paper": "redline.md",
               "docx": "SummitRidge_Redline_of_ACME_SaaS_Agreement.docx", "label": "Summit Ridge redline (Word, tracked changes)",
               "deal": {"customer": "Summit Ridge Manufacturing, Inc.", "annual_fees": "250000", "term_months": "24", "tier": "standard"},
               "final": "Quarterly billing agreed. Service credits up to 25% agreed. Cyber insurance stays at $5M. Gross negligence carve-out agreed. Indemnity for violation of law agreed, under the general cap."},
}

STAGED = ("case-1", "case-2", "case-3")  # the examples that are full Word contracts, run through the same path as an upload
MIN_SIMILARITY = 0.5  # below this share of the standard's sentences, the file is not ACME's standard agreement
SECRET = auth.secret(ROOT)
MAX_BODY = 25 * 1024 * 1024  # a 15 MB upload is about 20 MB once encoded
BASE_ORIGIN = "/".join(CFG["portal"]["base_url"].rstrip("/").split("/")[:3])
LOCK = threading.Lock()
ME = threading.local()  # who the current request, or the job it started, is working for


class PerSeller(MutableMapping):
    """A dict with one copy per signed-in seller. The code reads and writes it as if it were one shared dict;
    each seller gets their own current deal and job, so sellers never see or disturb each other's work."""

    def __init__(self, make):
        self.make, self.by, self.lock = make, {}, threading.Lock()

    def mine(self):
        with self.lock:
            return self.by.setdefault(getattr(ME, "owner", ""), self.make())

    def __getitem__(self, k): return self.mine()[k]
    def __setitem__(self, k, v): self.mine()[k] = v
    def __delitem__(self, k): del self.mine()[k]
    def __iter__(self): return iter(self.mine())
    def __len__(self): return len(self.mine())


class Current(PerSeller):
    """The deal a request or job is working on. A request names its deal; a job keeps the deal it was started for.
    With no deal named, the seller's latest deal is used. A pin of False means 'no deal'."""

    def __getitem__(self, k):
        pinned = getattr(ME, "run", None)
        if k == "dir" and pinned is not None:
            return None if pinned is False else pinned
        return super().__getitem__(k)

    def __setitem__(self, k, v):
        super().__setitem__(k, v)
        if k == "dir":
            ME.run = v  # the rest of this request, and any job it starts, work on this deal

    def remember(self, v):
        super().__setitem__("dir", v)


def super_dir(cur):
    return PerSeller.__getitem__(cur, "dir")


class PerDeal(PerSeller):
    """One job record per deal, so several deals can be analysed at the same time."""

    def mine(self):
        d = RUN["dir"]
        with self.lock:
            return self.by.setdefault(d.name if d else "", self.make())

    def of(self, name):
        with self.lock:
            return dict(self.by.get(name, {}))


RUN = Current(lambda: {"dir": None})
JOB = PerDeal(lambda: {"name": "", "status": "idle", "message": ""})


def owner():
    return getattr(ME, "owner", "")


def visible(run):
    """A run belongs to the seller who made it. Runs with no recorded seller (the prepared demo cases) are open to all."""
    f = Path(run) / "seller.txt"
    return not f.exists() or read(f).strip().lower() == owner()


def case_id():
    d = RUN["dir"]
    f = d / "case.txt" if d else None
    return read(f).strip() if f and f.exists() else "case-1"


def is_upload():
    return case_id() == "upload"


def case_dir():
    if is_upload():  # an uploaded contract has no prepared replies; the run folder holds its inputs
        return RUN["dir"] / "_no-prepared-replies"
    return CASES_DIR / CASES[case_id()]["dir"]


def upload_meta():
    d = RUN["dir"]
    f = d / "upload.json" if d else None
    return json.loads(read(f)) if f and f.exists() else None


def read(path):
    return Path(path).read_text(encoding="utf-8")


def now():
    return datetime.now().strftime("%Y%m%d-%H%M%S")


# ---------------------------------------------------------------- model

def ask(prompt):
    """Send one prompt to the model and return its text."""
    if STUB:
        return stub(prompt)
    return models.ask(prompt, CFG["model"])


STUB_LEVELS = {"payment terms": 1, "renewal price increase cap": 2, "general liability cap": 2}


def stub_assess(prompt):
    """A canned but valid reading: for each change, the first listed row, at a fixed or the lowest level, quoting its cell."""
    out = []
    for block in re.split(r"(?m)^### ", prompt.split("The changes", 1)[-1])[1:]:
        cid = block.split(" ", 1)[0]
        line = next((l for l in block.splitlines() if l.startswith("- ")), "")
        parts = [x.strip() for x in line[2:].split(" | ")]
        term = parts[0]
        cells = {int(x[6]): x.split(": ", 1)[1] for x in parts if re.match(r"Level [123]: ", x)}
        if not cells:  # a row with no level at all can only be "not approvable"
            na = next((x.split(": ", 1)[1] for x in parts if x.startswith("Not approvable: ")), "")
            out.append({"id": cid, "row": term, "outcome": "not_approvable", "level": None, "cell_quote": na, "short": f"{term} change",
                        "reasoning": "Stub reading.", "prerequisites": [], "exposure": "", "recommendation": "Recommendation: hold the standard."})
            continue
        lv = STUB_LEVELS.get(term.lower())
        lv = lv if lv in cells else min(cells)
        out.append({"id": cid, "row": term, "outcome": "route", "level": lv, "cell_quote": cells[lv], "short": f"{term} change",
                    "reasoning": "Stub reading.", "prerequisites": [], "exposure": "Stub exposure.", "recommendation": "Recommendation: hold the standard."})
    outside = re.findall(r"(?m)^#### (D\d+)", prompt)
    return json.dumps({"assessments": out, "explanations": {i: "Stub explanation of what this clause does and what changed." for i in outside}})


def stub(prompt):
    if '"assessments"' in prompt:
        return stub_assess(prompt)
    if "DEMO_REFERRAL" in prompt:
        return "DECISION: approved\nAUTHORITY: SIMULATED: stub authority for a term the matrix does not settle.\nREPLY: Stub resolution."
    if "DEMO_APPROVER" in prompt:
        return "DECISION: approved\nREPLY: Stub approval."
    if "Stage 4" in prompt.split("TASK:")[-1]:
        return "## Approval record\n\n| ID | Change | Status |\n|---|---|---|\n| D1 | Stub row | Approved |\n\n## Follow-up drafts\n\nSeller note: stub."
    if "Stage 3" in prompt.split("TASK:")[-1]:
        return ("## Batch summary\n\n| Request | To | Change |\n|---|---|---|\n| 1 | Stub | Stub |\n\n"
                "### Request 1\n**To:** Darla Denkins, Deal Desk Manager\n**Subject:** Stub: payment terms Net 45\n**Matrix row:** Payment terms\n**Level:** 1\n\nStub body.\n\n"
                "### Request 2\n**To:** Vivian Fairfax, VP Finance\n**Subject:** Stub: renewal price increase capped at 3%\n**Matrix row:** Renewal price increase cap\n**Level:** 2\n\nStub body.\n")
    return "## Stub stage output\n\n| ID | Item |\n|---|---|\n| D1 | stub |"


# ---------------------------------------------------------------- inputs

def deal_facts(raw, prev):
    """The deal facts the ledger and later rules need, as numbers, not prose. Blank facts carry over from the earlier round."""
    raw = raw or {}
    carried = json.loads(read(prev / "deal.json")) if prev and (prev / "deal.json").exists() else {}
    out = {"customer": str(raw.get("customer", "")).strip(), "annual_fees": None, "term_months": None,
           "tier": str(raw.get("tier", "")).strip()}
    try:
        if str(raw.get("annual_fees", "")).strip():
            out["annual_fees"] = float(str(raw["annual_fees"]).replace(",", "").replace("$", ""))
            if out["annual_fees"] < 0:
                raise ValueError
        if str(raw.get("term_months", "")).strip():
            out["term_months"] = int(raw["term_months"])
            if out["term_months"] < 0:
                raise ValueError
    except (ValueError, TypeError):
        raise ValueError("Annual fees must be a number and the term a whole number of months.")
    if out["tier"] not in ("", "standard", "strategic"):
        raise ValueError("Choose standard or strategic.")
    return {k: (carried.get(k) if v in ("", None) else v) for k, v in out.items()} if carried else out


def profile_text(deal, extra):
    rows = []
    if deal.get("customer"):
        rows.append(f"| Customer | {deal['customer']} |")
    if deal.get("annual_fees") is not None or deal.get("term_months") is not None:
        fees = f"Annual fees ${deal['annual_fees']:,.0f}" if deal.get("annual_fees") is not None else ""
        term = f"Term {deal['term_months']} months" if deal.get("term_months") is not None else ""
        rows.append("| Deal | " + ". ".join(x for x in (fees, term) if x) + " |")
    if deal.get("tier"):
        rows.append(f"| Strategic or standard | {deal['tier'].capitalize()} |")
    head = "| Field | |\n|---|---|\n" + "\n".join(rows) + "\n\n" if rows else ""
    return head + (extra or "")


def baseline_text():
    """The standard agreement, read the same way as an upload so layout does not show up as a change."""
    word = Path(CFG["contracts"]["standard_download"])
    if word.suffix.lower() == ".docx" and word.exists():
        return contract_io.extract(word.name, word.read_bytes())["accepted"]
    return read(Path(CFG["contracts"]["standard_text"]))


def redline_text():
    """The contract as the customer sent it: drop the author's drafting note above the first rule."""
    if is_upload():
        return read(RUN["dir"] / "contract-under-review.md")
    t = read(case_dir() / "inputs" / CASES[case_id()]["paper"])
    return t.split("\n---\n", 1)[1].strip() if t.startswith("#") and "\n---\n" in t else t


def env_block():
    e = CFG["environment"]
    if e["stand_in_data_only"]:
        return ""
    return (f"<ai_environment>{e['name']}; approved by {e['approved_by']} on {e['approved_on']}. "
            "Put this on the record header.</ai_environment>\n\n")


def prior_record(run):
    """The decisions so far on this deal: the latest approval record of the earlier round."""
    for n in ("stage6.md", "stage4.md"):
        if (run / n).exists():
            return read(run / n)
    return "(No approvals have been recorded for the earlier round yet.)"


def upload_blocks():
    """For an uploaded contract: the exact differences found by code, and any edits that were not tracked."""
    if not is_upload():
        return ""
    d = RUN["dir"]
    m = upload_meta()
    rounds = ""
    if m.get("previous"):
        rounds = (
            f"<prior_approval_record round='{m['previous']}'>\nThe decisions so far on this deal.\n{read(d / 'prior-record.md')}\n</prior_approval_record>\n\n"
            "<differences_since_previous_round>\nFound by a plain text comparison of this round with the previous round's text.\n"
            f"{read(d / 'since-previous.md')}\n</differences_since_previous_round>\n\n")
    return rounds + (
        "<computed_differences>\nFound by a plain text comparison of the contract under review (changes accepted) "
        "with the standard agreement. The list is exact and complete. Account for every item.\n"
        f"{read(d / 'computed-differences.md')}\n</computed_differences>\n\n"
        "<untracked_differences>\nDifferences that appear in the file's text but are not marked as tracked changes. "
        "If this is not 'None.', flag each item to the seller as an untracked change.\n"
        f"{read(d / 'untracked-differences.md')}\n</untracked_differences>\n\n")


def context(profile):
    matrix = "\n\n".join(
        f"### {name}\n{read(MATRIX / name)}" for name in ("doa_matrix.csv", "roles.csv", "people.csv", "settings.csv")
    )
    return (
        f"<standard_agreement>\n{read(Path(CFG['contracts']['standard_text']))}\n</standard_agreement>\n\n"
        f"<matrix_files>\n{matrix}\n</matrix_files>\n\n"
        f"{env_block()}"
        f"<deal_profile>\n{profile}\n</deal_profile>\n\n"
        f"{upload_blocks()}"
        f"<contract_under_review>\n{redline_text()}\n</contract_under_review>\n"
    )


NONINTERACTIVE = (
    "This run is non-interactive. Where a stage says to ask the seller, list the question in your output "
    "and carry on, treating the answer as not provided. Do not include anything before or after the stage output."
)


def build(stage_file, ctx, extra, task):
    return (
        f"{read(PLAYBOOK / '00-standing-instructions.md')}\n\n---\n\n{read(PLAYBOOK / stage_file)}\n\n---\n\n"
        f"{ctx}\n{extra}\n{NONINTERACTIVE}\n\nTASK: {task}"
    )


def run_dir():
    return RUN["dir"]


def save(name, text):
    (run_dir() / name).write_text(text, encoding="utf-8")


def load(name):
    p = run_dir() / name if run_dir() else None
    return read(p) if p and p.exists() else ""


# ---------------------------------------------------------------- jobs

def start_job(name, fn):
    with LOCK:
        if JOB["status"] == "running":
            return False
        JOB.update(name=name, status="running", message="Starting")
    who, deal = owner(), RUN["dir"]
    record = JOB.mine()  # this deal's own record, held here so the thread never looks it up by whatever is open later

    def go():
        ME.owner, ME.run = who, deal
        try:
            fn()
            record.update(status="done", message="")
        except Exception as e:  # shown to the seller, not hidden
            record.update(status="error", message=str(e))

    threading.Thread(target=go, daemon=True).start()
    return True


def say(msg):
    JOB["message"] = msg


def deviations():
    """Every change in the uploaded contract, placed on a matrix row by code."""
    base, acc = baseline_text(), read(run_dir() / "accepted.txt")
    return locate.locate(contract_io.differences(base, acc), contract_io.paragraphs(base), contract_io.paragraphs(acc), MATRIX)


def analyze():
    d = run_dir()
    say("Finding and placing every change")
    devs = deviations()
    save("deviations.json", json.dumps(devs, indent=1))
    say("Reading each change against its matrix cell")
    ai = assess.assess(devs, MATRIX, d, ask)
    prev_items = prev_rows = None
    m = upload_meta()
    if m.get("previous"):
        prev_items, prev_rows = recordmod.items(RUNS / m["previous"]), recordmod.rows(RUNS / m["previous"])
    items = assess.finalize(devs, ai, MATRIX, prev_rows, prev_items)
    save("assessment.json", json.dumps({"items": items}, indent=1))
    deal = json.loads(load("deal.json") or "{}")
    customer = deal.get("customer") or Path(m["filename"]).stem
    auto = CFG["portal"]["send_mode"] == "auto"
    save("stage1.md", assess.render_stage1(items))
    save("stage2.md", assess.render_stage2(items, MATRIX))
    save("stage3.md", assess.render_stage3(items, MATRIX, d, customer, auto))
    if auto:
        try:
            say("Sending the requests")
            send("stage3.md")
        except ValueError as e:
            save("send-problem.md", str(e))


def signed_check():
    d = RUN["dir"]
    m = upload_meta()
    prev = RUNS / m["previous"]
    ctx = context(load("deal-profile.md"))
    extra = (
        f"<signed_copy_differences_from_last_agreed_draft>\n{read(d / 'since-previous.md')}\n</signed_copy_differences_from_last_agreed_draft>\n"
        f"<last_agreed_draft_record round='{m['previous']}'>\n{read(d / 'prior-record.md')}\n</last_agreed_draft_record>\n")
    task = ("The seller has uploaded the SIGNED copy. Do not run any stage. Produce a Pre-signature check only. "
            "(1) State whether the signed copy matches the last agreed draft, using the differences listed. "
            "(2) For each difference from the standard agreement in the signed copy (see computed_differences), name the approval in the "
            "record that covers it, or say it is not covered. (3) List any condition an approver attached that the signed copy does not meet. "
            "(4) Say whether it is safe to file, and what must be resolved if not. Quote the contract text. Do not approve anything.")
    say("Checking the signed copy")
    save("signed-check.md", ask(build("04-record-decisions.md", ctx, extra, task)))


def record():
    say("Building the approval record")
    md, rows = recordmod.build(run_dir(), MATRIX)
    save("record.json", json.dumps(rows, indent=1))
    save("stage4.md", md)
    if is_upload():
        ledger.add_record(CFG, run_dir(), "stage4", md)


def final_check(name, data):
    """Pass or fail: does the contract, at its latest revision, contain any change that was not approved? No AI is involved."""
    run = run_dir()
    base = baseline_text()
    r = contract_io.extract(name, data)
    ua, ub = contract_io.units(base), contract_io.units(r["accepted"])
    kept = sum(b.size for b in difflib.SequenceMatcher(None, ua, ub, autojunk=False).get_matching_blocks())
    if len(ua) >= 20 and kept / len(ua) < MIN_SIMILARITY:
        raise ValueError(NOT_STANDARD.format(pct=round(100 * kept / len(ua))))
    result = finalcheck.check(base, r["accepted"], MATRIX, run)
    result.update(filename=name, at=portal.now(), warnings=r["warnings"])
    save("final-check.json", json.dumps(result, indent=1))
    md, rows = recordmod.build(run, MATRIX)  # the record now carries each change's final outcome
    save("record.json", json.dumps(rows, indent=1))
    save("stage6.md", md)
    ledger.add_record(CFG, run, "stage6", md)
    return result


def appeals_list():
    """The denials in the open deal and where each one's single appeal stands, for the Appeals page."""
    d = run_dir()
    if d is None:
        return []
    items = {i["id"]: i for i in recordmod.items(d)}
    return [{**x, "change": (items.get(x["dev"]) or {}).get("short") or x["dev"]} for x in portal.denials(d)]


def appeal(rid, context):
    """Send one denial back to the approver who made it, once, with the seller's new context. Raises ValueError with a plain message."""
    run = run_dir()
    orig = next((q for q in portal.load(run) if q["id"] == rid), None)
    if not orig or orig.get("appeal_of"):
        raise ValueError("Choose a denied change from the table.")
    if orig["status"] != "decided" or orig["decision"]["decision"] != "Denied":
        raise ValueError("Only a denied change can be appealed.")
    if orig.get("appealed"):
        raise ValueError("This denial has already been appealed. The decision stands.")
    deal = json.loads(load("deal.json") or "{}")
    customer = deal.get("customer") or Path(upload_meta()["filename"]).stem
    text = assess.appeal_text(orig, read(run / "outbox" / orig["file"]), customer, (context or "").strip()[:2000])
    out = box("outbox")
    k = len(list(out.glob("*.md"))) + 1
    fname = f"{k:02d}-appeal-{re.sub(r'[^a-z0-9]+', '-', orig['subject'].lower()).strip('-')[:40]}.md"
    (out / fname).write_text(text, encoding="utf-8")
    req = requests_from("### Request 1\n" + text)[0]
    req["appeal_of"] = orig["id"]
    try:
        made = portal.create(run, [req], [fname], CFG)
    except ValueError:
        (out / fname).unlink()
        raise
    if CFG["app"]["mode"] == "demo" and CFG["demo"]["ai_approvers"]:
        threading.Thread(target=lambda: demo.play(CFG, RUNS, run, ask, log=lambda m: print("demo:", m, flush=True)), daemon=True).start()
    return made[0]["id"]


def snapshot(run):
    """The approval record as it stands, saved and added to the ledger. Called once every request in a deal has an answer."""
    md, rows = recordmod.build(run, MATRIX)
    (run / "record.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    (run / "stage4.md").write_text(md, encoding="utf-8")
    ledger.add_record(CFG, run, "stage4", md)


portal.AFTER_DECISION = snapshot


# ---------------------------------------------------------------- mailbox (simulated)

def requests_from(text):
    blocks = re.split(r"(?m)^#{2,4}\s*Request\s*\d+[^\n]*\n", text)[1:]
    out = []
    for b in blocks:
        b = re.split(r"(?m)^#{1,3}\s+(?!Request)", b)[0].strip()
        to = re.search(r"(?mi)^\W*To:?\W*\s*(.+)$", b)
        subj = re.search(r"(?mi)^\W*Subject:?\W*\s*(.+)$", b)
        cid = re.search(r"(?mi)^\W*Change ID:?\W*\s*(\S+)", b)
        kind = re.search(r"(?mi)^\W*Request kind:?\W*\s*(\S+)", b)
        out.append({"to": to.group(1).strip("* ") if to else "", "subject": subj.group(1).strip("* ") if subj else "", "text": b,
                    "dev": cid.group(1).strip("* ") if cid else "", "kind": kind.group(1).strip("* ") if kind else "approval"})
    return out


def box(name):
    d = run_dir() / name
    d.mkdir(exist_ok=True)
    return d


def outbox():
    return [{"name": p.name, "text": read(p)} for p in sorted(box("outbox").glob("*.md"))] if run_dir() else []


def inbox():
    return [{"name": p.name, "text": read(p)} for p in sorted(box("inbox").glob("*.md"))] if run_dir() else []


def send(source):
    text = load(source)
    reqs = requests_from(text)
    if not reqs:
        raise ValueError("No requests found to send.")
    if is_upload():
        portal.check_recipients(reqs, MATRIX)  # nothing goes out if any recipient is not a known approver
        routing.check(reqs, MATRIX, complete=(source == "stage3.md"))  # nor if a request does not match the matrix
    d = box("outbox")
    k = len(list(d.glob("*.md")))
    files = []
    for r in reqs:
        k += 1
        slug = re.sub(r"[^a-z0-9]+", "-", r["subject"].lower()).strip("-")[:50] or f"request-{k}"
        (d / f"{k:02d}-{slug}.md").write_text(r["text"], encoding="utf-8")
        files.append(f"{k:02d}-{slug}.md")
    if is_upload():
        made = portal.create(run_dir(), reqs, files, CFG)
        if CFG["app"]["mode"] == "demo" and CFG["demo"]["ai_approvers"] and made:
            run = run_dir()  # captured now: the seller may open another run before the approvers answer
            threading.Thread(target=lambda: demo.play(CFG, RUNS, run, ask, log=lambda m: print("demo:", m, flush=True)), daemon=True).start()
    return len(reqs)


def subject_of(text):
    m = re.search(r"(?mi)^\W*Subject:?\W*\s*(.+)$", text)
    return re.sub(r"^(re:\s*)+", "", m.group(1).strip("* ").lower()) if m else ""


def topic(subject):
    """The part of a subject after the company name: 'summit ridge: billing quarterly' -> 'billing quarterly'."""
    return subject.split(":", 1)[1] if ":" in subject else subject


def stems(t):
    return {w[:5] for w in re.findall(r"[a-z]{3,}", t.lower())}


def nums(t):
    return set(re.findall(r"\d+(?:\.\d+)?", t))


def similar(a, b):
    """Two reply subjects are about the same point if they carry no conflicting numbers and share most words."""
    wa, wb = stems(topic(a)), stems(topic(b))
    return (nums(a) <= nums(b) or nums(b) <= nums(a)) and len(wa & wb) / max(1, len(wa | wb)) >= 0.4


def same_point(reply_subject, request_text):
    """A reply answers a request if its subject's topic words appear in the request and no number in the subjects conflicts."""
    rs, qs = nums(reply_subject), nums(subject_of(request_text))
    if not (rs <= qs or qs <= rs):
        return False
    w = stems(topic(reply_subject))
    return bool(w) and len(w & stems(request_text)) / len(w) >= 0.6


def deliver():
    """Simulated approvers: a reply from the case folder arrives only if a request with a matching subject was sent."""
    have = {m["name"] for m in inbox()}
    new = 0
    first = sorted((case_dir() / "approvals").glob("[0-9]*.md"))
    later = sorted((case_dir() / "approvals" / "later-replies").glob("*.md"))
    sent_at = [(read(p), p.stat().st_mtime_ns) for p in sorted(box("outbox").glob("*.md"))]
    received = [(subject_of(read(p)), p.stat().st_mtime_ns) for p in box("inbox").glob("*.md")]  # as at the start of this check
    taken = []  # subjects of later replies delivered in this check
    for f in first + later:
        if f.name in have:
            continue
        s = subject_of(read(f))
        times = [t for x, t in sent_at if same_point(s, x)]
        if not times:
            continue
        if f in later:
            # A later reply answers a follow-up: some matching request must be newer than every reply already received on
            # that point. Later replies on one point arrive in order: a ruling first, then the approvals it calls for.
            got = [t for x, t in received if similar(s, x)]
            if got and max(times) <= max(got):
                continue
            if any(similar(s, e) and s != e for e in taken):
                continue
            taken.append(s)
        (box("inbox") / f.name).write_text(read(f), encoding="utf-8")
        if f not in later:
            received.append((s, (box("inbox") / f.name).stat().st_mtime_ns))
        new += 1
    return new


# ---------------------------------------------------------------- http

def upload_info():
    m = upload_meta()
    return {"id": "upload", "title": f"Uploaded: {m['filename']}", "kind": m["kind"],
            "final": "One line per change, saying what the final contract says.",
            "links": [{"label": "ACME standard agreement (Word)", "href": "/files/standard.docx"}],
            "profile": load("deal-profile.md")}


def run_title(r):
    cid = read(r / "case.txt").strip() if (r / "case.txt").exists() else "case-1"
    if cid == "upload":
        return "Uploaded: " + json.loads(read(r / "upload.json"))["filename"]
    return CASES[cid]["title"]


def case_info(cid):
    c = CASES[cid]
    links = [{"label": c["label"], "href": f"/files/{cid}/paper"}] if not c.get("docx") else [{"label": c["label"], "href": f"/files/{cid}/docx"}]
    links.append({"label": "ACME standard agreement (Word)", "href": "/files/standard.docx"})
    return {"id": cid, "title": c["title"], "kind": c["kind"], "final": c["final"], "links": links,
            "profile": read(CASES_DIR / c["dir"] / "inputs" / "deal-profile.md")}


def archived(r):
    return (Path(r) / "archived.json").exists()


def archive_deal(by):
    """Archive the open deal: withdraw its open requests, take it off the seller's list, and record it in the ledger. It cannot be undone."""
    run = run_dir()
    if run is None:
        raise ValueError("Choose a contract first.")
    n = portal.withdraw(run, CFG)
    (run / "archived.json").write_text(json.dumps({"at": portal.now(), "by": by, "withdrawn": n}), encoding="utf-8")
    ledger.add_deal_event(CFG, run, "archived", by, f"{n} open request(s) withdrawn")
    return n


def deals():
    """Every contract this seller has handed over, newest first, with where each stands."""
    out = []
    for r in sorted(RUNS.glob("app-*"), reverse=True):
        if not visible(r) or archived(r) or not (r / "upload.json").exists():
            continue
        job = JOB.of(r.name)
        reqs = portal.load(r)
        if job.get("status") == "running":
            status, note = "analyzing", job.get("message", "")
        elif job.get("status") == "error":
            status, note = "failed", job.get("message", "")
        elif (r / "send-problem.md").exists():
            status, note = "held", "The requests do not match the matrix. Open it to see why."
        elif (r / "signed-check.md").exists():
            status, note = "checked", "Signed copy checked."
        elif reqs:
            done = sum(q["status"] == "decided" for q in reqs)
            status, note = ("decided" if done == len(reqs) else "waiting"), f"{done} of {len(reqs)} decided"
        elif (r / "stage3.md").exists():
            status, note = "ready", "Changes found. Open it to review and send."
        else:
            status, note = "stopped", "This did not finish (the app may have restarted). Upload it again."
        meta = json.loads(read(r / "upload.json"))
        out.append({"name": r.name, "title": meta["filename"], "customer": (json.loads(read(r / "deal.json")).get("customer") or "") if (r / "deal.json").exists() else "",
                    "when": r.name[4:], "status": status, "note": note,
                    "signed": bool(meta.get("signed")), "demo": bool(meta.get("demo")), "current": RUN["dir"] == r})
    return out


def state():
    job = dict(JOB)  # read first: if it says done, every file below is already written
    d = run_dir()
    cid = case_id()
    return {
        "run": d.name if d else None, "deals": deals(),
        "record": list(recordmod.rows(d).values()) if d and (d / "assessment.json").exists() else [],
        "runs": [{"name": r.name, "case": (read(r / "case.txt").strip() if (r / "case.txt").exists() else "case-1"), "title": run_title(r)}
                 for r in sorted(RUNS.glob("app-*"), reverse=True) if visible(r) and ((r / "stage4.md").exists() or (r / "signed-check.md").exists())],
        "case": upload_info() if cid == "upload" else case_info(cid), "cases": {k: case_info(k) for k in STAGED},
        "upload": upload_meta(), "signed_check": load("signed-check.md"),
        "portal": portal.load(d) if d else [], "send_problem": load("send-problem.md"),
        "mode": CFG["app"]["mode"], "demo": {"ai_approvers": CFG["demo"]["ai_approvers"], "days": demo.CLOCK["days"]},
        "provider": CFG["auth"]["provider"], "send_mode": CFG["portal"]["send_mode"],
        "upload_runs": [{"name": r.name, "title": run_title(r)} for r in sorted(RUNS.glob("app-*"), reverse=True)
                        if visible(r) and not archived(r) and (r / "accepted.txt").exists() and (r / "stage3.md").exists() and not json.loads(read(r / "upload.json")).get("signed")],
        "profile": load("deal-profile.md") or case_info(cid)["profile"],
        "stage1": load("stage1.md"), "stage2": load("stage2.md"), "stage3": load("stage3.md"),
        "stage4": load("stage4.md"), "stage6": load("stage6.md"),
        "appeals": appeals_list(),
        "final_check": json.loads(load("final-check.json") or "null"),
        "outbox": outbox(), "inbox": inbox(), "job": job, "stub": STUB, "env": {"stand_in": CFG["environment"]["stand_in_data_only"], "backend": CFG["model"]["backend"], "model": CFG["model"]["name"], "problem": appconfig.gate_problem(CFG)},
    }


def new_run_dir():
    d, k = RUNS / f"app-{now()}", 1
    while d.exists():  # two starts in the same second
        k += 1
        d = RUNS / f"app-{now()}-{k}"
    return d


NOT_STANDARD = ("This does not look like ACME's standard agreement: only {pct}% of the standard's sentences are in it. "
                "Seller's Associate works on ACME's standard contract with the customer's changes. A contract on the customer's own paper is not supported yet. "
                "If this is the standard agreement saved as PDF or text, upload the Word file instead.")


def make_upload(name, data, profile, deal_raw, prev, signed, seller, demo=False):
    """Read a contract and set up its run folder. Raises ValueError or ContractError with a plain message."""
    base = baseline_text()
    r = contract_io.analyse(name, data, base, read(prev / "accepted.txt") if prev else None)
    if r["similarity"] < MIN_SIMILARITY and len(contract_io.units(base)) >= 20:
        raise ValueError(NOT_STANDARD.format(pct=round(r["similarity"] * 100)))
    deal = deal_facts(deal_raw, prev)
    d = new_run_dir()
    RUN["dir"] = d
    d.mkdir(parents=True)
    save("case.txt", "upload")
    if seller:
        save("seller.txt", seller)
    (d / "original").mkdir()
    (d / "original" / (name or "contract")).write_bytes(data)
    save("deal.json", json.dumps(deal))
    save("deal-profile.md", profile_text(deal, profile or (read(prev / "deal-profile.md") if prev and not any(deal.values()) else "")))
    save("accepted.txt", r["accepted"])
    save("contract-under-review.md", r["tracked_text"] or r["accepted"])
    save("computed-differences.md", contract_io.render(r["total"]))
    save("untracked-differences.md", contract_io.render(r["untracked"]))
    meta = {"filename": name, "kind": r["kind"], "warnings": r["warnings"], "tracked_paragraphs": r["tracked_count"],
            "differences": len(r["total"]), "untracked": len(r["untracked"]),
            "untracked_text": contract_io.render(r["untracked"]), "untracked_base": r["untracked_base"],
            "signed": signed, "previous": prev.name if prev else "", "demo": demo,
            "deal_id": ledger.deal_id_of(prev) if prev else d.name}
    if prev:
        save("since-previous.md", contract_io.render(r["since_previous"]))
        save("prior-record.md", prior_record(prev))
        meta["since_previous"] = len(r["since_previous"])
        meta["since_previous_text"] = contract_io.render(r["since_previous"])
    save("upload.json", json.dumps(meta))
    ledger.add_deal(CFG, d, seller, deal, name, r["kind"])
    return d, r


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def redirect(self, where, cookie=None):
        self.send_response(303)
        self.send_header("Location", where)
        if cookie is not None:
            self.send_header("Set-Cookie", cookie)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def cookie_for(self, email):
        secure = "; Secure" if CFG["portal"]["base_url"].startswith("https") else ""
        hours = CFG["auth"]["session_hours"]
        tok = auth.make_token(email, SECRET, hours) if email else ""
        return f"doa_session={tok}; HttpOnly; SameSite=Lax; Path=/; Max-Age={hours * 3600 if email else 0}{secure}"

    def user(self):
        """The signed-in person, or None. The login method only supplies a verified email."""
        mode = CFG["auth"]["provider"]
        if mode == "proxy-header":
            email = self.headers.get(CFG["auth"]["proxy_header"], "")
        else:
            c = SimpleCookie(self.headers.get("Cookie", ""))
            email = auth.read_token(c["doa_session"].value, SECRET) if "doa_session" in c else None
        return portal.role_of(email, MATRIX) if email else None

    def bind(self):
        """Mark this request as one seller's."""
        u = self.user()
        ME.owner = u["email"] if u else ""

    def scope(self, name):
        """The deal this request is about. '' means none. Not named at all: the seller's latest deal."""
        if name is None:
            if super_dir(RUN) is None:
                mine = [r for r in sorted(RUNS.glob("app-*")) if visible(r)]
                if mine:
                    RUN.remember(mine[-1])
            return
        ok = re.fullmatch(r"app-\d{8}-\d{6}(-\d+)?", name) and (RUNS / name).is_dir() and visible(RUNS / name) and not archived(RUNS / name)
        ME.run = (RUNS / name) if ok else False

    def seller_gate(self):
        """For the seller's screens. Demo mode (provider none) is open; otherwise the person must be a listed seller."""
        if CFG["auth"]["provider"] == "none":
            return self.user() or {}
        u = self.user()
        if not u:
            return None
        return u if u["seller"] else False

    def reply(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def json(self, obj, code=200):
        self.reply(code, json.dumps(obj))

    def web(self, status_page):
        status, text = status_page
        self.reply(status, text, "text/html; charset=utf-8")

    def do_GET(self):
        self.bind()
        path = self.path.split("?")[0]
        self.scope(parse_qs(urlsplit(self.path).query, keep_blank_values=True).get("run", [None])[0])
        if path == "/login":
            mode = CFG["auth"]["provider"]
            return self.web(portal.actas_page(MATRIX) if mode == "none" else portal.login_page()) if mode != "proxy-header" else self.redirect("/")
        if path == "/logout":
            return self.redirect("/login", self.cookie_for(None))
        if path == "/audit" or path.startswith("/audit/"):
            u = self.user()
            if not u:
                return self.redirect("/login")
            if not portal.may_audit(u, CFG):
                return self.web(portal.page("Audit", "<div class=card><h2>Audit</h2><p class=mute>The audit pages are for the matrix owner and the people the organization has listed.</p></div>", u, 403))
            m = re.fullmatch(r"/audit/export/(deals|decisions|record_rows|request_events|matrix_versions)\.csv", path)
            if m:
                return self.reply(200, ledger.export(CFG, m.group(1)), "text/csv; charset=utf-8")
            return self.web(portal.audit_page(u, CFG))
        if path.startswith("/portal"):
            u = self.user()
            if not u:
                return self.redirect("/login")
            if path == "/portal":
                return self.web(portal.list_page(u, RUNS))
            m = re.fullmatch(r"/portal/request/(RQ-[0-9a-f]+)", path)
            run, q = portal.find(m.group(1), RUNS) if m else (None, None)
            if not q or u["email"] not in q["assigned"]:
                return self.web(portal.page("Not found", "<div class=card><h2>Not found</h2><p class=mute>That request does not exist or is not assigned to you.</p></div>", u, 404))
            return self.web(portal.request_page(u, run, q))
        if CFG["auth"]["provider"] != "none" or path != "/":
            g = self.seller_gate()
            if g is None:
                return self.redirect("/login") if not path.startswith("/api") else self.json({"error": "Sign in."}, 401)
            if g is False:
                return self.json({"error": "Only listed sellers can use this screen."}, 403)
        if path == "/":
            return self.reply(200, (STATIC / "index.html").read_bytes(), "text/html; charset=utf-8")
        if path == "/api/state":
            return self.json(state())
        if path == "/api/matrix":
            def rows(n):
                with open(MATRIX / n, newline="", encoding="utf-8") as f:
                    return list(csv.reader(f))
            return self.json({k: rows(f"{k}.csv") for k in ("doa_matrix", "people", "settings")})
        if path == "/files/standard.docx":
            return self.reply(200, Path(CFG["contracts"]["standard_download"]).read_bytes(), DOCX)
        m = re.fullmatch(r"/files/(case-\d)/(docx|paper)", path)
        if m and m.group(1) in CASES:
            c = CASES[m.group(1)]
            inputs = CASES_DIR / c["dir"] / "inputs"
            if m.group(2) == "docx" and c.get("docx"):
                return self.reply(200, (inputs / c["docx"]).read_bytes(), DOCX)
            return self.reply(200, (inputs / c["paper"]).read_bytes(), "text/plain; charset=utf-8")
        self.reply(404, "not found", "text/plain")

    def form_post(self, path, f):
        mode = CFG["auth"]["provider"]
        if path == "/login":
            if mode != "local":
                return self.redirect("/login")
            email = auth.login(CFG["auth"]["users_file"], f.get("email", ""), f.get("password", ""))
            if not email:
                print("login failed for", f.get("email", "")[:80], flush=True)
                return self.web(portal.login_page("That email and password did not match, or the account is locked for a minute."))
            return self.redirect("/" if portal.role_of(email, MATRIX)["seller"] else "/portal", self.cookie_for(email))
        if path == "/act-as":
            if mode != "none":
                return self.redirect("/login")
            email = f.get("email", "")
            r = portal.role_of(email, MATRIX)
            if not (r["approver"] or r["seller"]):
                return self.web(portal.actas_page(MATRIX))
            return self.redirect("/" if r["seller"] else "/portal", self.cookie_for(email))
        u = self.user()
        if not u:
            return self.redirect("/login")
        m = re.fullmatch(r"/portal/request/(RQ-[0-9a-f]+)/(decide|delegate|ask)", path)
        run, q = portal.find(m.group(1), RUNS) if m else (None, None)
        if not q or u["email"] not in q["assigned"]:
            return self.web(portal.page("Not found", "<div class=card><h2>Not found</h2></div>", u, 404))
        try:
            if m.group(2) == "decide":
                portal.decide(run, q["id"], u, f.get("decision", ""), f.get("text", ""), CFG, authority=f.get("authority", ""), reference=f.get("reference", ""))
                note = "Decision recorded. Thank you."
            elif m.group(2) == "delegate":
                portal.delegate(run, q["id"], u, f.get("to_email", ""), f.get("to_name", ""), CFG)
                note = "Delegated. They have been told by email."
            else:
                portal.ask(run, q["id"], u, f.get("text", ""), CFG)
                note = "Your question was sent to the seller. The request stays open."
        except ValueError as e:
            run, q = portal.find(q["id"], RUNS)
            return self.web(portal.request_page(u, run, q, error=str(e)))
        run, q = portal.find(q["id"], RUNS)
        return self.web(portal.request_page(u, run, q, note=note))

    def do_POST(self):
        self.bind()
        n = int(self.headers.get("Content-Length") or 0)
        if n > MAX_BODY:
            return self.json({"error": "That request is too large."}, 413)
        origin = self.headers.get("Origin")
        if origin and origin.rstrip("/") != BASE_ORIGIN:
            return self.json({"error": f"Open the app at {CFG['portal']['base_url']} and try again."}, 403)
        raw = self.rfile.read(n) or b"{}"
        path = self.path.split("?")[0]
        if path in ("/login", "/act-as") or path.startswith("/portal"):
            return self.form_post(path, {k: v[0] for k, v in parse_qs(raw.decode("utf-8", "replace")).items()})
        g = self.seller_gate()
        if g is None:
            return self.json({"error": "Sign in."}, 401)
        if g is False:
            return self.json({"error": "Only listed sellers can use this screen."}, 403)
        body = json.loads(raw)
        self.scope(body.get("run") if isinstance(body.get("run"), str) else None)
        body["_seller"] = g.get("email", "")
        try:
            path = self.path
            if path == "/api/start":
                if appconfig.gate_problem(CFG):
                    return self.json({"error": appconfig.gate_problem(CFG)}, 400)
                cid = body.get("case", "case-1")
                if cid not in STAGED:
                    return self.json({"error": "unknown case"}, 400)
                c = CASES[cid]
                inputs = CASES_DIR / c["dir"] / "inputs"
                try:
                    d, r = make_upload(c["docx"], (inputs / c["docx"]).read_bytes(), body.get("profile") or read(inputs / "deal-profile.md"),
                                       c["deal"], None, False, body.get("_seller", ""), demo=True)
                except (ValueError, contract_io.ContractError) as e:
                    return self.json({"error": str(e)}, 400)
                return self.json({"started": start_job("analyze", analyze), "run": d.name})
            if path == "/api/upload":
                if appconfig.gate_problem(CFG):
                    return self.json({"error": appconfig.gate_problem(CFG)}, 400)
                name = Path(str(body.get("filename", ""))).name
                signed = bool(body.get("signed"))
                prev = None
                if body.get("previous"):
                    pdir = RUNS / Path(str(body["previous"])).name
                    if not (pdir / "accepted.txt").exists() or not (pdir / "stage3.md").exists() or not visible(pdir):
                        return self.json({"error": "That earlier round was not found, or it has not finished finding the changes."}, 400)
                    prev = pdir
                if signed and not prev:
                    return self.json({"error": "A signed copy is checked against the round it was agreed from. Choose that round."}, 400)
                try:
                    data = base64.b64decode(body.get("data", ""), validate=True)
                    d, r = make_upload(name, data, body.get("profile"), body.get("deal"), prev, signed, body.get("_seller", ""))
                except (ValueError, contract_io.ContractError) as e:
                    return self.json({"error": str(e)}, 400)
                job = start_job("signed", signed_check) if signed else start_job("analyze", analyze)
                return self.json({"started": job, "kind": r["kind"], "warnings": r["warnings"], "run": d.name})
            if path == "/api/demo/advance":
                if CFG["app"]["mode"] != "demo":
                    return self.json({"error": "The demo clock exists only in demo mode."}, 400)
                day = demo.advance_to_next_business_day(CFG["reminders"]["holidays"])
                return self.json({"day": day.isoformat(), "done": reminders.tick(CFG, RUNS, today=day)})
            if path == "/api/resume" and RUN["dir"] is not None:
                RUN.remember(RUN["dir"])  # the seller's latest deal, for a client that does not name one
                return self.json({"run": RUN["dir"].name})
            if run_dir() is None:
                return self.json({"error": "Start a request first."}, 400)
            if path == "/api/send":
                src = body.get("source", "stage3.md")
                if src != "stage3.md":
                    return self.json({"error": "bad source"}, 400)
                return self.json({"sent": send(src)})
            if path == "/api/deliver":
                return self.json({"delivered": deliver()})
            if path == "/api/record":
                return self.json({"started": start_job("record", record)})
            if path == "/api/archive":
                try:
                    return self.json({"archived": True, "withdrawn": archive_deal(body.get("_seller", ""))})
                except ValueError as e:
                    return self.json({"error": str(e)}, 400)
            if path == "/api/appeal":
                try:
                    return self.json({"appealed": appeal(str(body.get("request", "")), str(body.get("context", "")))})
                except ValueError as e:
                    return self.json({"error": str(e)}, 400)
            if path == "/api/final":
                try:
                    return self.json(final_check(Path(str(body.get("filename", ""))).name, base64.b64decode(body.get("data", ""), validate=True)))
                except (ValueError, contract_io.ContractError) as e:
                    return self.json({"error": str(e)}, 400)
            self.json({"error": "not found"}, 404)
        except Exception as e:
            self.json({"error": str(e)}, 500)


def reminder_loop():
    """Check for unanswered requests every few minutes. A failure is logged and the loop carries on."""
    while True:
        try:
            for line in reminders.tick(CFG, RUNS, today=demo.today() if CFG["app"]["mode"] == "demo" else None):
                print("reminders:", line, flush=True)
        except Exception as e:
            print("reminders: check failed:", e, flush=True)
        time.sleep(CFG["reminders"]["check_minutes"] * 60)


def main():
    port = int(os.environ.get("PORT", "8765"))
    RUNS.mkdir(exist_ok=True)
    try:
        for problem in locate.matrix_problems(MATRIX, contract_io.paragraphs(baseline_text())):
            print("MATRIX WARNING:", problem, flush=True)
    except Exception as e:
        print("MATRIX WARNING: could not check the matrix against the standard:", e, flush=True)
    if CFG["reminders"]["enabled"] and not STUB:
        threading.Thread(target=reminder_loop, daemon=True).start()
    print(f"Seller app on http://localhost:{port}" + ("  (stub model)" if STUB else ""))
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
