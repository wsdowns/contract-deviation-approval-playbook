"""Routing and drafting for an uploaded contract.

Code finds each change and the matrix row it falls under (locate.py). One AI call reads each change against
its row and names the level. Code then checks that reading against the matrix (the row must be one of the
candidates, the level's cell must exist, and the words the AI quotes must really be in the cell), takes the
approvers from the cell itself, and writes the routing table and every request. The AI never names a person.
"""
import difflib
import json
import re
from pathlib import Path

import portal
import routing
from contract_io import _QUOTES

PROMPT = Path(__file__).resolve().parent / "prompts" / "assess.md"


def _n(s):
    return re.sub(r"\s+", " ", str(s).translate(_QUOTES)).strip().lower()


def cell_titles(cell, shorts):
    """The approver titles a cell names, in order: what follows the last colon, split on '+'."""
    out = []
    for n in cell.rsplit(":", 1)[-1].split("+"):
        t = shorts.get(n.strip().lower(), n.strip())
        if t and t not in out:
            out.append(t)
    return out


NUM = re.compile(r"\$?\s*(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s*(%|x\b|million\b|billion\b|thousand\b|[MKB]\b)?", re.I)
SCALE = {"million": 1e6, "m": 1e6, "billion": 1e9, "b": 1e9, "thousand": 1e3, "k": 1e3}


def _fmt(v):
    return format(v, "f").rstrip("0").rstrip(".")


def nums(text):
    """The numbers in a text as comparable tokens: 45, 3%, 2x, 99.9%, and money as plain numbers ($10M and $10,000,000 are both 10000000)."""
    out = set()
    for m in NUM.finditer(text or ""):
        v, unit = float(m.group(1).replace(",", "")), (m.group(2) or "").lower()
        out.add(_fmt(v) + unit if unit in ("%", "x") else _fmt(v * SCALE.get(unit, 1)))
    return out


def level_by_numbers(new_text, old_text, row):
    """The lowest level whose cell contains the most of the numbers the change introduced, or None when no cell names any of them.

    Only numbers that are new in the customer's wording count (a number already in the standard sentence decides nothing)."""
    wanted = nums(new_text) - nums(old_text)
    if not wanted:
        return None
    score = {lv: len(wanted & nums(row.get(f"Level {lv}", ""))) for lv in (1, 2, 3) if row.get(f"Level {lv}", "").strip()}
    best = max(score.values(), default=0)
    top = [lv for lv, sc in score.items() if sc == best]
    return min(top) if best else None  # the lowest level that names those numbers: route to the lowest that covers it


def worddiff(old, new, context=7):
    """Show exactly which words changed: [-removed words-]{+added words+}, with a little surrounding text."""
    a, b = old.split(), new.split()
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == "equal":
            seg = a[i1:i2]
            out.append(" ".join(seg) if len(seg) <= 2 * context else " ".join(seg[:context]) + " ... " + " ".join(seg[-context:]))
        else:
            if i2 > i1:
                out.append("[-" + " ".join(a[i1:i2]) + "-]")
            if j2 > j1:
                out.append("{+" + " ".join(b[j1:j2]) + "+}")
    return " ".join(out)


def heading_of(where):
    """A plain name for where a change sits: 'Notices', or the new section's own heading."""
    return where[len("New section: "):] if where.startswith("New section: ") else where.split(" > ")[-1]


def _rows(matrix):
    import locate
    return {r["term"]: r["row"] for r in locate.read_rows(matrix)}


def _row_text(row):
    cells = " | ".join(f"{lv}: {row[lv]}" for lv in ("Level 1", "Level 2", "Level 3") if row.get(lv, "").strip())
    return f"{row['Term']} | Standard position: {row['Standard position']} | {cells} | Not approvable: {row.get('Not approvable', '') or '(none)'}"


def deal_text(run):
    """The deal facts for the AI and the requests: the numbers from the form, then every filled row of the seller's profile."""
    run = Path(run)
    deal = json.loads((run / "deal.json").read_text()) if (run / "deal.json").exists() else {}
    bits = []
    bits.append(f"Annual fees: ${deal['annual_fees']:,.0f}" if deal.get("annual_fees") is not None else "Annual fees: not provided")
    bits.append(f"Term: {deal['term_months']} months" if deal.get("term_months") is not None else "Term: not provided")
    if deal.get("tier"):
        bits.append(f"Tier: {deal['tier']}")
    extra = []
    prof = run / "deal-profile.md"
    if prof.exists():
        for l in prof.read_text(encoding="utf-8").splitlines():
            c = [x.strip() for x in l.strip().strip("|").split("|")]
            if l.startswith("|") and len(c) == 2 and c[0] and c[1] and c[0].lower() not in ("field", "deal") and not set(c[0]) <= set("-: "):
                extra.append(f"{c[0]}: {c[1]}")
    return "\n".join(bits + extra)


def stated_reasons(run):
    """The seller's notes on why the customer asks for each change, if the profile has that section."""
    prof = Path(run) / "deal-profile.md"
    if not prof.exists():
        return ""
    m = re.search(r"(?ims)^##\s+Why the customer[^\n]*\n(.+?)(?=^##\s|\Z)", prof.read_text(encoding="utf-8"))
    return m.group(1).strip() if m else ""


def build_prompt(devs, rows, run):
    blocks = []
    for d in devs:
        if d["status"] not in ("located", "ambiguous"):
            continue
        cands = "\n".join(f"- {_row_text(rows[t])}" for t in d["rows"])
        blocks.append(f"### {d['id']} ({d['kind']}, in {d['where']})\nStandard: {d['baseline'] or '(nothing)'}\nRequested: {d['other'] or '(removed)'}\n"
                      f"Matrix row{'s' if len(d['rows']) > 1 else ''} for this change:\n{cands}")
    outside = "\n\n".join(f"#### {d['id']} ({d['kind']}, in {d['where']})\nStandard: {d['baseline'] or '(nothing)'}\nRequested: {d['other'] or '(removed)'}"
                          for d in devs if d["status"] == "unlocated") or "(none)"
    text = PROMPT.read_text(encoding="utf-8").replace("{outside}", outside)
    why = stated_reasons(run)
    deal = deal_text(run) + (f"\n\nWhy the customer asks for each change (the seller's notes):\n{why}" if why else "")
    return text.replace("{deal}", deal).replace("{changes}", "\n\n".join(blocks))


def parse_all(text):
    """The assessments, and the plain explanations of changes outside the matrix, both keyed by change id."""
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("The AI did not return the structured answer that was asked for.")
    try:
        data = json.loads(m.group(0))
        items = data.get("assessments", [])
        expl = data.get("explanations") or {}
    except (ValueError, AttributeError, TypeError):
        raise ValueError("The AI's answer was not in the structured form that was asked for.")
    return ({str(i.get("id")): i for i in items if isinstance(i, dict)},
            {str(k): str(v) for k, v in expl.items()} if isinstance(expl, dict) else {})


def parse(text):
    return parse_all(text)[0]


def verify(devs, items, rows, shorts):
    """Check the AI's reading against the matrix. Returns (good, problems), both keyed by change id."""
    good, bad = {}, {}
    for d in devs:
        if d["status"] not in ("located", "ambiguous"):
            continue
        it = items.get(d["id"])
        if not it:
            bad[d["id"]] = "No answer was given for this change."
            continue
        term = it.get("row") if d["status"] == "ambiguous" else d["rows"][0]
        if term not in d["rows"]:
            bad[d["id"]] = f"'{term}' is not one of the rows for this change ({', '.join(d['rows'])})."
            continue
        row, quote, outcome = rows[term], _n(it.get("cell_quote", "")), it.get("outcome")
        if outcome == "route":
            try:
                lv = int(it.get("level"))
            except (TypeError, ValueError):
                bad[d["id"]] = "No level was given."
                continue
            cell = row.get(f"Level {lv}", "").strip()
            if lv not in (1, 2, 3) or not cell:
                bad[d["id"]] = f"'{term}' has no approval at Level {lv}."
            elif len(quote) < 6 or quote not in _n(cell):
                bad[d["id"]] = f"The words quoted are not in the Level {lv} cell of '{term}'. The cell says: {cell}"
            else:
                note, found = "", level_by_numbers(d["other"], d["baseline"], row)
                if found and found > lv:  # the numbers point to a more senior level: take it. Never lower the AI's level.
                    shared = sorted((nums(d["other"]) - nums(d["baseline"])) & nums(row[f"Level {found}"]))
                    note = (f"Raised from Level {lv} to Level {found} by code: the number{'s' if len(shared) > 1 else ''} "
                            f"{', '.join(shared)} in the request match{'' if len(shared) > 1 else 'es'} the Level {found} cell, not the Level {lv} cell.")
                    lv, cell = found, row[f"Level {found}"].strip()
                good[d["id"]] = {**it, "row": term, "level": lv, "cell": cell, "number_note": note}
        elif outcome == "not_approvable":
            cell = row.get("Not approvable", "").strip()
            if not cell or len(quote) < 6 or quote not in _n(cell):
                bad[d["id"]] = f"The words quoted are not in the Not approvable cell of '{term}'."
            else:
                good[d["id"]] = {**it, "row": term, "cell": cell}
        elif outcome == "unclear":
            good[d["id"]] = {**it, "row": term}
        else:
            bad[d["id"]] = f"Unknown outcome '{outcome}'."
    return good, bad


def assess(devs, matrix, run, ask):
    """Read every located change against its row. At most two AI calls (the second only to correct a bad answer)."""
    rows, shorts = _rows(matrix), routing._short_titles(matrix)
    todo = [d for d in devs if d["status"] in ("located", "ambiguous")]
    outside = [d for d in devs if d["status"] == "unlocated"]
    if not todo and not outside:
        return {}
    prompt = build_prompt(devs, rows, run)
    try:
        items, expl = parse_all(ask(prompt))
    except ValueError:
        items, expl = {}, {}
    good, bad = verify(devs, items, rows, shorts)
    if bad:
        fix = "\n".join(f"- {k}: {v}" for k, v in bad.items())
        again = f"{prompt}\n\nYour earlier answer had problems for these changes. Answer for every change again, correcting them:\n{fix}\n"
        g2, b2 = verify(devs, parse_or_empty(ask(again)), rows, shorts)
        for k, v in g2.items():
            if k in bad:
                good[k] = v
        bad = {k: v for k, v in b2.items() if k not in good}
    for d in outside:  # only explained, never routed
        good[d["id"]] = {"explanation": expl.get(d["id"], "").strip()}
    for k, v in bad.items():  # still wrong: fail safe. Nothing is routed on an answer that did not match the matrix.
        good[k] = {"outcome": "unclear", "row": next(d["rows"][0] for d in devs if d["id"] == k), "short": "", "reasoning": "The AI's reading did not match the matrix, so this was not routed. " + v, "unverified": True}
    return good


def parse_or_empty(text):
    try:
        return parse(text)
    except ValueError:
        return {}


# ------------------------------------------------------------------ everything after the reading is code

DECIDED = ("Approved", "Approved (pre-approved)", "Conditional")


def q(s, n=700):
    s = re.sub(r"\s+", " ", str(s)).strip()
    return s if len(s) <= n else s[:n].rstrip() + "..."


def finalize(devs, ai, matrix, prev_rows=None, prev_items=None):
    """One record per change, with its outcome. prev_* are the earlier round's items and record rows, if any."""
    rows, shorts = _rows(matrix), routing._short_titles(matrix)
    items = []
    for d in devs:
        it = {"id": d["id"], "kind": d["kind"], "where": d["where"], "baseline": d["baseline"], "other": d["other"], "how": d.get("how", "")}
        if d["status"] == "placeholder":
            it.update(outcome="placeholder", short="Filled in a blank of the standard")
        elif d["status"] == "unlocated":
            h = heading_of(d["where"])
            it.update(outcome="not_in_matrix", short=(f"New '{h}' section" if d["where"].startswith("New section") else f"{d['kind']} {h} clause") + " (not in the matrix)",
                      row="", explanation=(ai.get(d["id"]) or {}).get("explanation", ""),
                      reasoning=f"No matrix row covers {('a section called ' + repr(h)) if d['where'].startswith('New section') else 'the ' + h + ' clause'}, so the matrix does not say who may approve a change to it.")
        else:
            a = ai[d["id"]]
            it.update(row=a["row"], short=a.get("short") or d["where"], reasoning=(a.get("reasoning", "") + " " + a.get("number_note", "")).strip(), exposure=a.get("exposure", ""),
                      recommendation=a.get("recommendation", ""), prerequisites=a.get("prerequisites") or [], unverified=bool(a.get("unverified")),
                      why=a.get("customer_reason", ""))
            if a["outcome"] == "route":
                titles = cell_titles(a["cell"], shorts)
                pre = a["cell"].strip().lower().startswith("pre-approved")
                it.update(outcome="pre_approved" if pre else "route", level=a["level"], cell=a["cell"], titles=titles, joint=len(titles) > 1)
            elif a["outcome"] == "not_approvable":
                it.update(outcome="not_approvable", cell=a["cell"])
            else:
                it.update(outcome="unclear")
        # a later round: look the same place up in the earlier round
        if prev_items and it["outcome"] not in ("placeholder",):
            old = next((p for p in prev_items if p["where"] == it["where"] and p["id"] in (prev_rows or {})), None)
            if old:
                row = prev_rows[old["id"]]
                same = _n(old["other"]) == _n(it["other"])
                if same and row["status"] in DECIDED:
                    it.update(outcome="already_decided", prior=row)
                else:
                    it["earlier"] = row
        items.append(it)
    return items


def _person(matrix, title):
    return next((p for p in portal.people(matrix) if p["Title"] == title), None)


def _to(matrix, title):
    p = _person(matrix, title)
    return f"{p['Name']}, {title}" if p else title


def request_blocks(items, matrix, run, customer):
    """The requests, as '### Request N' blocks. Returns (text, table_rows, owner_items)."""
    deal = deal_text(run).replace("\n", ". ")
    st = portal.settings(matrix)
    referee = st.get("Terms not in the matrix") or st.get("Matrix owner", "")
    done = [i for i in items if i["outcome"] == "already_decided"]
    blocks, table, n = [], [], 0
    for it in items:
        if it["outcome"] != "route":
            continue
        for t in it["titles"]:
            n += 1
            others = [x for x in it["titles"] if x != t]
            earlier = it.get("earlier")
            e = (f"\n**2a. Earlier decision on this point.** {earlier['approver']} decided: {earlier['status']}. {earlier['decision_words']}\n" if earlier else "")
            body = (
                f"### Request {n}\n**To:** {_to(matrix, t)}\n**Subject:** {customer}: {it['short']}\n**Matrix row:** {it['row']}\n**Level:** {it['level']}\n**Change ID:** {it['id']}\n\n"
                f"**1. Decision needed.** Approve or deny this change: {it['short']}.\n"
                f"**2. The change.** {it['kind']} in {it['where']}. "
                + (f"The customer's words: \"{q(it['other'])}\"" if it["other"] else f"The customer removed: \"{q(it['baseline'])}\"") + "\n"
                + (f"   What changed, shown as [-removed-] and {{+added+}} words: {worddiff(it['baseline'], it['other'])}\n" if it["kind"] == "Changed" and it["baseline"] and it["other"] else "") + e +
                f"**3. Our standard.** {_matrix_standard(matrix, it['row'])}" + (f" The standard agreement says: \"{q(it['baseline'], 400)}\"" if it["baseline"] and it["kind"] == "Changed" else "") + "\n"
                f"**4. Why the customer asks.** " + (f"{q(it['why'], 300)} (from the seller's deal profile)" if it.get("why") and it["why"].strip().lower().rstrip(".") != "not provided" else "Not provided.") + "\n"
                f"**5. The deal.** {deal}.\n"
                f"**6. Exposure.** {it.get('exposure') or 'Not provided.'}\n"
                f"**7. Already approved in this deal.** " + ("; ".join(f"{x['short']} ({x['prior']['approver']})" for x in done) or "None yet.") + "\n"
                f"**8. Who else decides.** " + (f"Also required: {', '.join(others)}. Each decides separately." if others else "No one else.") + "\n"
                f"**9. Recommendation.** {it.get('recommendation') or 'None.'}\n"
                "**10. How to reply.** Open the link, then choose Approve, Approve with conditions, or Deny. Say exactly what you approve. If you approve only part, say which part.\n")
            blocks.append(body)
            table.append(f"| {n} | {_to(matrix, t)} | {it['short']} | Approve or deny: {it['where']} |")
    ask = [i for i in items if i["outcome"] in ("not_in_matrix", "unclear")]
    for i in ask:  # a change the matrix does not settle: one request to the Deal Desk for each, so each has its own outcome and authority
        n += 1
        group = i["where"].split(" > ")[0] if " > " in i["where"] else "a section the customer added"
        blocks.append(
            f"### Request {n}\n**To:** {_to(matrix, referee)}\n**Subject:** {customer}: {i['short'] or i['where']}\n"
            f"**Matrix row:** none\n**Level:** none\n**Change ID:** {i['id']}\n**Request kind:** referral\n\n"
            "**1. What is needed.** This change is to a term the matrix does not settle. Please find out what is needed, get any approval that is required, "
            "and record the outcome here, with the authority you relied on.\n"
            f"**2. The clause.** {heading_of(i['where'])} ({group}). The customer {i['kind'].lower()} it."
            + (f" The matrix row involved: {i['row']}." if i.get("row") else "") + "\n"
            + (f"**3. In plain words.** {i['explanation']}\n" if i.get("explanation") else "")
            + (f"**4. What the standard says.** \"{q(i['baseline'], 700)}\"\n" if i["baseline"] else "**4. What the standard says.** Nothing: the standard has no such clause.\n")
            + (f"**5. What the customer's version says.** \"{q(i['other'], 700)}\"\n" if i["other"] else "**5. What the customer's version says.** The customer removed it.\n")
            + (f"**6. What changed**, shown as [-removed-] and {{+added+}} words: {worddiff(i['baseline'], i['other'])}\n" if i["baseline"] and i["other"] else "")
            + f"**7. Why this came to you.** {i['reasoning']}\n"
            "**8. How to reply.** Open the link. Choose the outcome, and say who or what you relied on: a person and their title, a policy, or a fact. Add a reference if you have one.\n")
        table.append(f"| {n} | {_to(matrix, referee)} | {i['short'] or i['where']} | Find out what is needed and record the outcome |")
    return "\n".join(blocks), table, ask


def appeal_text(orig, orig_text, customer, context):
    """The request that goes back to the approver who denied a change: the denial in their words, the seller's new context, the original."""
    head = {k: (re.search(rf"(?mi)^\*\*{k}:\*\*\s*(.+)$", orig_text) or [None, ""])[1] for k in ("Matrix row", "Level", "Change ID")}
    d = orig["decision"]
    body = orig_text.split("\n\n", 1)[-1].strip()
    kind = "**Request kind:** referral\n" if orig.get("kind") == "referral" else ""
    return (f"**To:** {orig['to_name']}, {orig['to_title']}\n**Subject:** Appeal: {orig['subject']}\n**Matrix row:** {head['Matrix row']}\n**Level:** {head['Level']}\n"
            f"**Change ID:** {head['Change ID']}\n{kind}\n"
            "**1. What is asked.** The seller asks you to reconsider your decision on the change below. This is the only appeal: your answer ends it, and your earlier decision stands unless you change it.\n"
            f"**2. Your earlier decision.** {d['decision']} on {d['at']}: \"{d['text']}\""
            + (f" Authority or basis you cited: {d['authority']}." if d.get("authority") else "") + "\n"
            f"**3. New context from the seller.** " + (f"\"{context}\"" if context else "None given.") + "\n"
            "**4. How to reply.** Open the link and decide again. Say exactly what you approve, your conditions, or your reason.\n\n"
            "**The original request, as you received it:**\n" + "\n".join("> " + l for l in body.splitlines()) + "\n")


def _matrix_standard(matrix, term):
    return _rows(matrix).get(term, {}).get("Standard position", "")


def render_stage1(items):
    out = ["Found by comparing the contract with ACME's standard agreement. Every difference is listed.", "",
           "| ID | Requested (exact words) | Standard (exact words) | Where | Kind |", "|---|---|---|---|---|"]
    for i in items:
        out.append(f"| {i['id']} | {q(i['other'], 220) or '(removed)'} | {q(i['baseline'], 220) or '(nothing)'} | {i['where']} | {i['kind']} |")
    return "\n".join(out) + "\n"


def render_stage2(items, matrix):
    out = ["| ID | Matrix row | Outcome | Approver titles | Joint? | Prerequisites | Reasoning |", "|---|---|---|---|---|---|---|"]
    names = {"route": lambda i: f"Route to Level {i['level']}", "pre_approved": lambda i: "Pre-approved", "not_approvable": lambda i: "Not approvable",
             "unclear": lambda i: "Referred to the Deal Desk", "not_in_matrix": lambda i: "Referred to the Deal Desk", "placeholder": lambda i: "Not a deviation",
             "already_decided": lambda i: f"Already decided ({i['prior']['status']})"}
    for i in items:
        out.append(f"| {i['id']} | {i.get('row') or ''} | {names[i['outcome']](i)} | {', '.join(i.get('titles', []))} | "
                   f"{'Yes' if i.get('joint') else 'No'} | {'; '.join(i.get('prerequisites') or []) or 'None stated'} | {q(i.get('reasoning', '') or i.get('how', ''), 300)} |")
    ask = [i for i in items if i["outcome"] in ("not_in_matrix", "unclear")]
    if ask:
        out += ["", "## Referred to the Deal Desk", "", "The matrix does not settle these. The Deal Desk finds out what is needed and records the outcome.", ""] + \
               [f"- **{i['id']}** {i['short'] or i['where']}: {i.get('explanation') or i['reasoning']}" for i in ask]
    flags = [f"- {i['id']}: the reading did not match the matrix, so this was not routed." for i in items if i.get("unverified")]
    if flags:
        out += ["", "## Flags", ""] + flags
    return "\n".join(out) + "\n"


def render_stage3(items, matrix, run, customer, auto):
    blocks, table, ask = request_blocks(items, matrix, run, customer)
    sec = ["## Batch summary", ""]
    if table:
        sec += ["| Request | To | Change | Decision needed |", "|---|---|---|---|"] + table + [""]
    def lst(title, picked, fmt):
        if picked:
            sec.extend([f"**{title}**", ""] + [fmt(i) for i in picked] + [""])
    lst("Pre-approved (no request)", [i for i in items if i["outcome"] == "pre_approved"], lambda i: f"- {i['id']} {i['short']}: pre-approved for {', '.join(i['titles'])}. The cell says: {q(i['cell'], 200)}")
    lst("Not approvable (negotiate out, or ask the matrix owner to amend the matrix)", [i for i in items if i["outcome"] == "not_approvable"],
        lambda i: f"- {i['id']} {i['short']}: the matrix says it cannot be approved: {q(i['cell'], 200)}. The standard is: {_matrix_standard(matrix, i['row'])}")
    lst("Referred to the Deal Desk (the matrix does not settle these)", ask, lambda i: f"- {i['id']} {i['short'] or i['where']}: " + (i.get("explanation") or i["reasoning"]))
    lst("Not a deviation", [i for i in items if i["outcome"] == "placeholder"], lambda i: f"- {i['id']} {i['where']}: {i['short']}. Check that the name or value filled in is correct: \"{q(i['other'], 160)}\"")
    lst("Already decided in an earlier round", [i for i in items if i["outcome"] == "already_decided"],
        lambda i: f"- {i['id']} {i['short']}: {i['prior']['status']} by {i['prior']['approver']}. Unchanged since.")
    deal = json.loads((Path(run) / "deal.json").read_text()) if (Path(run) / "deal.json").exists() else {}
    missing = [k for k, lab in (("annual_fees", "annual fees"), ("term_months", "term")) if deal.get(k) in (None, "")]
    if missing:
        sec += [f"**Missing from the deal profile:** {', '.join(missing)}. Requests say \"not provided\" for these.", ""]
    if table and not auto:
        sec.append("Confirm to send all requests.")
    return "\n".join(sec) + "\n\n" + blocks
