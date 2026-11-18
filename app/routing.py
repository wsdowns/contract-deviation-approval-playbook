"""A code check of every drafted request against the matrix, before anything is sent.

The AI picks the approver for each change. This module does not trust that pick. Each request must name the
matrix row and the level it relies on (`**Matrix row:**` and `**Level:**`), and the code checks, from the
matrix files alone, that:

  1. the row exists and the level's cell is not blank;
  2. the person addressed holds a title named in that cell;
  3. for a joint approval, every title in the cell is being asked (first send of a round only);
  4. a request with no row ("none") goes to whoever handles terms not in the matrix (the 'Terms not in the matrix' setting, else the matrix owner), and only to them.

What it cannot check: whether the level chosen is the lowest one that covers the change (that needs the
amounts and the wording read against the cell), so a contract that misleads the AI into naming a lower
level of the right row passes. That gap closes only with deterministic rules. See docs/deterministic-rules.md.
"""
import csv
import re
from pathlib import Path

import portal

NO_ROW = {"none", "n/a", "not in matrix", "authority unclear", "matrix owner"}


def _rows(matrix):
    with open(Path(matrix) / "doa_matrix.csv", newline="", encoding="utf-8") as f:
        return {r["Term"].strip().lower(): r for r in csv.DictReader(f)}


def _short_titles(matrix):
    out = {}
    for r in portal._csv(Path(matrix) / "roles.csv"):
        full = r["Title"].strip()
        out[full.lower()] = full
        if r.get("Short title", "").strip():
            out[r["Short title"].strip().lower()] = full
    return out


def titles_in(cell, shorts):
    """The titles a matrix cell names: what follows the last colon, split on '+'."""
    names = cell.rsplit(":", 1)[-1].split("+")
    return {shorts.get(n.strip().lower(), n.strip()) for n in names if n.strip()}


def _field(text, name):
    m = re.search(rf"(?mi)^\W*{name}:?\W*\s*(.+)$", text)
    return m.group(1).strip("* ").strip() if m else ""


def check(reqs, matrix, complete=True):
    """Raise ValueError naming every problem. Call after portal.check_recipients."""
    rows, shorts = _rows(matrix), _short_titles(matrix)
    st = portal.settings(matrix)
    owner = st.get("Terms not in the matrix") or st.get("Matrix owner", "")
    problems, asked = [], {}
    for r in reqs:
        who = portal.resolve(r["to"], matrix)
        title = shorts.get(who["Title"].lower(), who["Title"])
        label = r["subject"] or r["to"]
        term = _field(r["text"], "Matrix row")
        if not term:
            problems.append(f"{label}: the request does not name the matrix row it relies on.")
            continue
        if term.lower() in NO_ROW:
            if title != shorts.get(owner.lower(), owner):
                problems.append(f"{label}: a request with no matrix row goes to {owner}, who handles terms the matrix does not settle, not {title}.")
            continue
        row = rows.get(term.lower())
        if not row:
            problems.append(f"{label}: '{term}' is not a Term in doa_matrix.csv.")
            continue
        n = re.search(r"\d+", _field(r["text"], "Level"))
        col = f"Level {n.group()}" if n else ""
        if col not in row or not row[col].strip():
            problems.append(f"{label}: '{term}' has no approval at '{_field(r['text'], 'Level') or 'no level named'}'.")
            continue
        named = titles_in(row[col], shorts)
        if title not in named:
            problems.append(f"{label}: {title} is not an approver for '{row['Term']}' at {col} (the matrix names {', '.join(sorted(named))}).")
            continue
        asked.setdefault((row["Term"], col), set()).add(title)
    if complete:
        for (term, col), got in asked.items():
            missing = titles_in(rows[term.lower()][col], shorts) - got
            if missing:
                problems.append(f"'{term}' at {col} needs every named approver; no request goes to {', '.join(sorted(missing))}.")
    if problems:
        raise ValueError("The requests do not match the matrix. Nothing was sent.\n- " + "\n- ".join(problems))
