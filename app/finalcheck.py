"""The final check: does the contract, at its latest revision, contain any change that was not approved? Pass or fail.

The seller uploads the final contract. When an approval is granted the contract is updated (the redline accepted, with an
"approved" comment) or a denial is explained, so the upload is simply the same contract at a later revision. This module
finds every change the upload still has against ACME's standard, in code, and compares each one with the approvals recorded
for the deal. It passes only if every change is covered. If it fails, it says where.

Each change in the final contract falls into one of these:
  approved, in the same words      covered (conditions, if any, are listed as a note: the app cannot check that they are met)
  denied, or not approvable        fails: it was refused and is still in the contract
  still waiting for a decision     fails: not yet approved
  in the same place, other words   fails: not approved in the form it appears
  in a place with no approval      fails: never submitted for approval
A denied change that is no longer in the contract is fine. So is an approved change that the contract does not use.
"""
import json
import re
from pathlib import Path

import assess
import contract_io
import locate
import record as recordmod


def _kind(row):
    """How a record row stands: 'approved', 'denied' or 'open'."""
    s = row["status"]
    if s.startswith(("Denied", "Not approvable")):
        return "denied"
    if s.startswith(("Approved", "Conditional", "No approval needed")):
        return "approved"
    return "open"


def check(baseline_text, final_text, matrix, run):
    """Compare the final contract with the approvals for this deal. Returns a result dict; result['pass'] is the verdict."""
    items = recordmod.items(run)
    rows = recordmod.rows(run)
    if not items:
        raise ValueError("There is nothing to check this contract against yet: no changes were analysed for this deal.")
    diffs = contract_io.differences(baseline_text, final_text)
    found = locate.locate(diffs, contract_io.paragraphs(baseline_text), contract_io.paragraphs(final_text), matrix)
    by_where = {}
    for it in items:
        if it["outcome"] != "placeholder":
            by_where.setdefault(it["where"], []).append(it)
    failures, notes, ok, used = [], [], [], set()
    for d in found:
        if d["status"] == "placeholder":
            continue  # a blank of the standard filled in, such as the customer's name
        text = d["other"] or "(removed)"
        here = by_where.get(d["where"], [])
        same = next((i for i in here if assess._n(i["other"]) == assess._n(d["other"])), None)
        if same:
            used.add(same["id"])
            row = rows.get(same["id"])
            k = _kind(row) if row else "open"
            label = f"{same['id']} {same['short']}"
            if k == "approved":
                ok.append({"where": d["where"], "what": f"{label}: approved by {row['approver']}."})
                if row["conditions"] and row["conditions"] != "none":
                    notes.append(f"{label}: approved with conditions. Confirm the contract meets them: {row['conditions']}")
            elif k == "denied":
                failures.append({"where": d["where"], "contract": text, "reference": same["other"] or "(removed)",
                                 "reason": f"{label} was denied ({row['status']}), and it is still in the contract."})
            else:
                failures.append({"where": d["where"], "contract": text, "reference": same["other"] or "(removed)",
                                 "reason": f"{label} has not been approved yet ({row['status'] if row else 'no decision'})."})
        elif here:
            failures.append({"where": d["where"], "contract": text, "reference": " / ".join(i["other"] or "(removed)" for i in here),
                             "reason": "The wording in the contract is not the wording that was submitted for approval, so it is not covered by the approval."})
        else:
            failures.append({"where": d["where"], "contract": text, "reference": "(nothing was submitted for this place)",
                             "reason": "This change was never submitted for approval."})
    removed = []
    for it in items:
        if it["outcome"] == "placeholder" or it["id"] in used:
            continue
        row = rows.get(it["id"])
        if row:
            removed.append({"where": it["where"], "what": f"{it['id']} {it['short']}: {row['status'].lower()}, and it is not in the final contract."})
    by_id = {}
    for it in items:
        if it["id"] in used:
            continue
        by_id[it["id"]] = "Not in the final contract"
    for it in items:
        if it["id"] in used:
            row = rows.get(it["id"])
            by_id[it["id"]] = "In the final contract, approved" if row and _kind(row) == "approved" else "In the final contract: NOT covered"
    return {"pass": not failures, "failures": failures, "notes": notes, "ok": ok, "removed": removed, "by_id": by_id,
            "changes_in_final": len([d for d in found if d["status"] != "placeholder"])}
