"""The approval record, built in code from the assessment and the decisions people made in the portal.

A decision in the portal is already structured (who, approve / approve with conditions / deny, their exact
words, whether by delegation, whether simulated), so nothing here needs an AI. The table has the columns the
ledger reads. The record is proof of authority for the changes, not proof of the changes.
"""
import json
from pathlib import Path

import portal

HEAD = ["ID", "Change", "Matrix row and level", "Approver (name, title)", "Decision (exact words)", "Status", "Conditions (exact words)", "Final outcome", "Notes"]
SIM = "SIMULATED APPROVERS: demo only, not proof of authority."


def items(run):
    f = Path(run) / "assessment.json"
    return json.loads(f.read_text(encoding="utf-8"))["items"] if f.exists() else []


def _who(q):
    d = q["decision"]
    name = d["name"] or d["by"]
    return f"{name}, {q['to_title']}" + (f" (by delegation from {q['to_name']})" if d.get("acting_for") else "")


def _threads(reqs, dev_id, kind=None):
    """Each original request for a change, with its one appeal if there is one: [(request, appeal or None)]."""
    appeals = {q["appeal_of"]: q for q in reqs if q.get("appeal_of")}
    return [(q, appeals.get(q["id"])) for q in reqs if q.get("dev") == dev_id and not q.get("appeal_of") and (kind is None or q.get("kind") == kind)]


def _words(q, a):
    """The approver's words, and the appeal's outcome after them."""
    d = q["decision"]
    text = f"{d['name'] or d['by']}: \"{d['text']}\""
    if a and a["status"] == "decided":
        e = a["decision"]
        text += f" Then, on appeal, {e['name'] or e['by']}: \"{e['text']}\""
    elif a:
        text += " The seller has appealed. Pending."
    return text


def rows(run, round_label=""):
    """One row per change that needed a decision or a note: {id: row}. Ordered as in the contract."""
    reqs = portal.load(run)
    fc = Path(run) / "final-check.json"
    final = json.loads(fc.read_text(encoding="utf-8")).get("by_id", {}) if fc.exists() else {}
    out = {}
    for it in items(run):
        o = it["outcome"]
        if o == "placeholder":
            continue
        r = {"id": it["id"], "change": it["short"] or it["where"], "matrix_row_level": "", "approver": "", "decision_words": "",
             "status": "", "conditions": "", "final_outcome": "", "notes": ""}
        if o == "route":
            th = _threads(reqs, it["id"])
            qs = [q for q, _ in th]
            effs = [(a if a and a["status"] == "decided" else q) for q, a in th]
            done = [e for e in effs if e["status"] == "decided"]
            pending = any(a and a["status"] == "open" for _, a in th)
            r["matrix_row_level"] = f"{it['row']}, Level {it['level']}"
            r["approver"] = "; ".join(_who(q) if q["status"] == "decided" else f"{q['to_name']}, {q['to_title']} (awaiting)" for q in qs) or ", ".join(it["titles"]) + " (not sent)"
            r["decision_words"] = " / ".join(_words(q, a) for q, a in th if q["status"] == "decided") or "(no reply yet)"
            decs = [e["decision"]["decision"] for e in done]
            if pending:
                r["status"] = "Appeal pending"
            elif "Denied" in decs:
                r["status"] = "Denied"
            elif qs and len(done) == len(qs):
                r["status"] = "Conditional" if "Approved with conditions" in decs else "Approved"
            elif done:
                r["status"] = "Missing co-approval"
            else:
                r["status"] = "Awaiting reply" if qs else "Not sent"
            r["conditions"] = " / ".join(e["decision"]["text"] for e in done if e["decision"]["decision"] == "Approved with conditions") or "none"
            notes = []
            if any(e["decision"].get("simulated") for e in done):
                notes.append("Simulated approver (demo): not proof of authority.")
            if any(a and a["status"] == "decided" for _, a in th):
                notes.append("Decided on appeal.")
            notes += [f"Decided {e['decision']['at']}" for e in done[:1]]
            if it.get("earlier"):
                notes.append(f"Earlier decision on this point: {it['earlier']['status']}.")
            r["notes"] = " ".join(notes)
        elif o == "pre_approved":
            r.update(matrix_row_level=f"{it['row']}, Level {it['level']}", approver=f"{', '.join(it['titles'])} (pre-approved by the matrix)",
                     decision_words=f"Pre-approved by the matrix: {it['cell']}", status="Approved (pre-approved)", conditions="none", notes="No escalation needed.")
        elif o == "not_approvable":
            r.update(matrix_row_level=f"{it['row']}, Not approvable", approver="(no one: the matrix does not allow it)",
                     decision_words=f"The matrix says: {it['cell']}", status="Not approvable", conditions="none",
                     notes="Negotiate it out, or ask the matrix owner to amend the matrix.")
        elif o in ("unclear", "not_in_matrix"):
            th = _threads(reqs, it["id"], "referral")
            ref, app = (th[0] if th else (None, None))
            eff = app if app and app["status"] == "decided" else ref
            r.update(matrix_row_level=it.get("row") or "(none)", conditions="none")
            if app and app["status"] == "open":
                r.update(status="Appeal pending", approver=f"Deal Desk: {ref['decision'].get('authority', '')}", decision_words=_words(ref, app),
                         notes="The seller has appealed the Deal Desk's decision. It is with the Deal Desk.")
            elif eff and eff["status"] == "decided":
                d = eff["decision"]
                r.update(status=f"{d['decision']} (Deal Desk)",
                         approver=f"Deal Desk: {d.get('authority', '')}" + (f" (reference: {d['reference']})" if d.get("reference") else ""),
                         decision_words=_words(ref, app),
                         conditions=d["text"] if d["decision"] == "Approved with conditions" else "none",
                         notes=("Decided on appeal. " if app else "") + "Resolved by the Deal Desk. The authority cited is the Deal Desk's statement and is not verified in the system."
                               + (" Simulated: not proof of authority." if d.get("simulated") else ""))
            else:
                r.update(status="Referred to Deal Desk", approver="(Deal Desk: response needed)", decision_words="(no response yet)", notes=it.get("reasoning", ""))
        elif o == "already_decided":
            p = it["prior"]
            r.update({k: p.get(k, "") for k in ("matrix_row_level", "approver", "decision_words", "status", "conditions")},
                     notes=f"Carried forward{round_label}: unchanged since it was decided.")
        r["final_outcome"] = final.get(it["id"], "")
        out[it["id"]] = r
    return out


def _cell(s):
    return str(s).replace("|", "/").replace("\n", " ")


def build(run, matrix):
    """The record as markdown, and its rows."""
    rs = rows(run)
    reqs = portal.load(run)
    sim = any(q["decision"] and q["decision"].get("simulated") for q in reqs if q["status"] == "decided")
    out = ([SIM, ""] if sim else []) + ["## Approval record", "", "| " + " | ".join(HEAD) + " |", "|" + "---|" * len(HEAD)]
    for r in rs.values():
        out.append("| " + " | ".join(_cell(x) for x in (r["id"], r["change"], r["matrix_row_level"], r["approver"], r["decision_words"], r["status"], r["conditions"], r["final_outcome"], r["notes"])) + " |")
    waiting = [f"{q['to_name']}, {q['to_title']}: {q['subject']}" for q in reqs if q["status"] == "open"]
    notes = []
    standards = {i["id"]: i for i in items(run)}
    for r in rs.values():
        if r["status"] in ("Denied", "Not approvable") or r["status"].startswith("Denied"):
            it = standards[r["id"]]
            notes.append(f"- **{r['id']} {r['change']}.** The standard stays. A line you may say to the customer: \"We are not able to agree to this change. "
                         f"Our standard position is {_standard(matrix, it.get('row', ''))}\" This is a draft for you to adapt. It makes no promise.")
    if notes:
        out += ["", "## Seller notes (drafts)", ""] + notes
    if waiting:
        out += ["", "## Still open", ""] + [f"- {w}" for w in waiting]
    return "\n".join(out) + "\n", rs


def _standard(matrix, term):
    import assess
    return (assess._rows(matrix).get(term, {}).get("Standard position") or "the standard agreement.").rstrip(".") + "."
