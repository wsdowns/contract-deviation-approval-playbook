"""Pull the worked-example tables out of saved app runs, for the final workbook.

usage: extract_worked_examples.py case-1=<run> case-2=<run> case-3=<run> > data.json
"""
import json
import re
import sys
from pathlib import Path

RUNS = Path(__file__).resolve().parents[1] / "runs"


def table(md, start):
    """Rows of the first markdown table after the line containing `start`."""
    lines = md.split("\n")
    i = next((k for k, l in enumerate(lines) if start and start in l), 0)
    while i < len(lines) and not lines[i].lstrip().startswith("|"):
        i += 1
    if i >= len(lines):
        return []
    head = [c.strip() for c in lines[i].strip().strip("|").split("|")]
    rows = []
    for l in lines[i + 2:]:
        if not l.lstrip().startswith("|"):
            break
        cells = [c.strip() for c in l.strip().strip("|").split("|")]
        rows.append(dict(zip(head, cells)))
    return rows


def clip(t, n):
    t = re.sub(r"\*\*|`", "", t or "")
    if len(t) <= n:
        return t
    cut = t[:n].rsplit(" ", 1)[0].rstrip(",;:")
    return cut + " ..."


def first_name(t):
    return re.split(r",|\(", t or "")[0].strip()


def case(run):
    d = RUNS / run
    rd = lambda n: (d / n).read_text() if (d / n).exists() else ""
    s1, s2, s3 = rd("stage1.md"), rd("stage2.md"), rd("stage3.md")
    rec = rd("stage6.md") or rd("stage4.md")
    out = {"run": run, "final_check": bool(rd("stage6.md")), "inbox": len(list((d / "inbox").glob("*.md"))),
           "outbox": len(list((d / "outbox").glob("*.md")))}
    out["stage1"] = [[r.get("ID", ""), clip(r.get("Clause", ""), 60), clip(r.get("Requested position (exact words)", ""), 150)]
                     for r in table(s1, "Deviations")]
    out["stage2"] = [[r.get("ID", ""), clip(r.get("Matrix row", ""), 40), clip(r.get("Outcome", ""), 40), clip(r.get("Approver titles", ""), 60)]
                     for r in table(s2, None)]
    out["record"] = [[re.split(r" \(", r.get("ID", ""))[0], clip(r.get("Change", ""), 70), clip(first_name(r.get("Approver (name, title)", "")), 45),
                      clip(r.get("Status", ""), 30), clip(r.get("Final outcome", ""), 30)] for r in table(rec, "Approval record")]
    lines = rec.split("\n")
    k = next((i for i, l in enumerate(lines) if "seller note" in l.lower() and len(l) < 120 and not l.lstrip().startswith("|")), None)
    note = []
    if k is not None:
        seen4 = False
        for l in lines[k + 1:]:
            if re.match(r"\s*(\*Draft|\*\*|---|#)", l) and note:
                break
            if seen4 and not l.strip():
                break
            seen4 = seen4 or l.lstrip().startswith("4.")
            note.append(l)
    out["seller_note"] = "\n".join(note).strip()[:1100]
    req = re.search(r"(?s)### Request 1\n(.*?)\n### Request 2", s3)
    out["request1"] = req.group(1).strip() if req else ""
    return out


if __name__ == "__main__":
    print(json.dumps({k: case(v) for k, v in (a.split("=") for a in sys.argv[1:])}, indent=1))
