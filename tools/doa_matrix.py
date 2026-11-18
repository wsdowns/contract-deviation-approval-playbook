"""Validate a delegation of authority (DoA) matrix and build a formatted workbook.

The matrix is plain CSV so any organization can maintain its own, for any
contract type. See docs/matrix-format.md for the format.

Usage:
    python tools/doa_matrix.py validate MATRIX_DIR
    python tools/doa_matrix.py build MATRIX_DIR OUT.xlsx [--org NAME]
            [--email-format "you+{first}{last}@example.com"]

MATRIX_DIR holds doa_matrix.csv and roles.csv, and optionally people.csv
and settings.csv.
"""
from __future__ import annotations

import argparse
import csv
import math
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

LEVEL_RE = re.compile(r"^Level (\d+)$")
REQUIRED = ("Term", "Standard position", "Not approvable")
PREAPPROVED = "Pre-approved:"
# settings.csv keys whose value must be a role in roles.csv
ROLE_SETTINGS = ("Requester", "Matrix owner", "Record custodian", "Pre-signature check", "Terms not in the matrix")
SETTINGS = (*ROLE_SETTINGS, "Approvals mailbox")


@dataclass
class Matrix:
    headers: list[str]
    rows: list[dict[str, str]]
    roles: list[dict[str, str]]
    people: list[dict[str, str]] = field(default_factory=list)
    settings: dict[str, str] = field(default_factory=dict)

    @property
    def levels(self) -> list[str]:
        return [h for h in self.headers if LEVEL_RE.match(h)]


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = [{k: (v or "").strip() for k, v in r.items()} for r in reader]
        return list(reader.fieldnames or []), rows


def load(matrix_dir: str | Path) -> Matrix:
    d = Path(matrix_dir)
    headers, rows = _read_csv(d / "doa_matrix.csv")
    _, roles = _read_csv(d / "roles.csv")
    people = _read_csv(d / "people.csv")[1] if (d / "people.csv").exists() else []
    settings = {}
    if (d / "settings.csv").exists():
        settings = {r["Setting"]: r["Value"] for r in _read_csv(d / "settings.csv")[1]}
    return Matrix(headers, rows, roles, people, settings)


def approvers(cell: str) -> list[str]:
    """Return the approver titles in a level cell: the text after the last
    colon, split on '+'. An empty cell means not delegated at that level."""
    if not cell:
        return []
    if ":" not in cell:
        raise ValueError(f"no approver after a colon: {cell!r}")
    return [a.strip() for a in cell.rsplit(":", 1)[1].split("+") if a.strip()]


def validate(m: Matrix) -> list[str]:
    """Return a list of error messages; an empty list means the matrix is valid."""
    errors: list[str] = []
    for h in REQUIRED:
        if h not in m.headers:
            errors.append(f"doa_matrix.csv: missing column {h!r}")
    levels = m.levels
    if not levels:
        errors.append("doa_matrix.csv: needs at least one 'Level N' column")
    nums = [int(LEVEL_RE.match(h).group(1)) for h in levels]
    if nums != list(range(1, len(nums) + 1)):
        errors.append(f"doa_matrix.csv: level columns must be Level 1..Level N in order, got {levels}")

    known: dict[str, str] = {}
    for r in m.roles:
        for key in (r.get("Title", ""), r.get("Short title", "")):
            if key:
                if key in known:
                    errors.append(f"roles.csv: duplicate title or short title {key!r}")
                known[key] = r["Title"]

    seen_terms: set[str] = set()
    used: set[str] = set()
    for i, row in enumerate(m.rows, start=2):
        term = row.get("Term", "")
        where = f"doa_matrix.csv line {i} ({term or 'no term'})"
        if not term:
            errors.append(f"{where}: empty Term")
        elif term in seen_terms:
            errors.append(f"{where}: duplicate Term")
        seen_terms.add(term)
        if not any(row.get(lv) for lv in levels) and not row.get("Not approvable"):
            errors.append(f"{where}: no level grants authority and nothing is marked Not approvable")
        for lv in levels:
            try:
                names = approvers(row.get(lv, ""))
            except ValueError as e:
                errors.append(f"{where}, {lv}: {e}")
                continue
            for a in names:
                if a not in known:
                    errors.append(f"{where}, {lv}: approver {a!r} is not in roles.csv")
                else:
                    used.add(known[a])

    for key, value in m.settings.items():
        if key not in SETTINGS:
            errors.append(f"settings.csv: unknown setting {key!r}; expected one of {list(SETTINGS)}")
        elif key in ROLE_SETTINGS:
            if value not in known:
                errors.append(f"settings.csv: {key} {value!r} is not in roles.csv")
            else:
                used.add(known[value])
    for r in m.roles:
        if r["Title"] not in used:
            errors.append(f"roles.csv: {r['Title']!r} is not named anywhere in the matrix")
    titles = {r["Title"] for r in m.roles}
    for p in m.people:
        if p.get("Title") not in titles:
            errors.append(f"people.csv: title {p.get('Title')!r} is not in roles.csv")
    return errors


def _readme(org: str, levels: int, settings: dict[str, str]) -> list[str]:
    lines = [
        f"{org} Delegation of Authority Matrix: Contract Deviations",
        "",
        "How to read the matrix",
        f"1. Each row is a contract term. Standard position is {org}'s position. Any change from it is a deviation.",
        f"2. Levels 1 to {levels} rise in authority from left to right. A higher level may approve anything a lower level in the same row may approve.",
        "3. In each cell, the text after the last colon names the approver. \"+\" means every named approver must approve; one alone is an incomplete approval.",
        "4. \"Pre-approved\" means the named role may accept the change without escalation.",
        "5. A blank level cell means no one at that level may approve the change.",
        "6. Anything in the Not approvable column may not be approved by anyone unless the matrix itself is amended.",
        "7. A deviation the matrix does not cover goes to the matrix owner. Do not apply the nearest row by analogy.",
        "8. An approval must state what it approves. If it covers only part of the request, or adds conditions, record exactly that.",
    ]
    if settings:
        lines += ["", "Who does what"] + [f"{k}: {v}" for k, v in settings.items()]
    return lines


def build(m: Matrix, out: str | Path, org: str = "Company", email_format: str | None = None) -> None:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

    thin = Side(style="thin", color="999999")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    wrap = Alignment(wrap_text=True, vertical="top")
    head_font = Font(name="Arial", bold=True, color="FFFFFF", size=10)
    head_fill = PatternFill("solid", fgColor="1F3864")
    body = Font(name="Arial", size=10)
    grey = Font(name="Arial", size=10, italic=True, color="808080")
    not_delegated = "Not delegated at this level"

    def header(ws, names, widths):
        for col, (h, w) in enumerate(zip(names, widths), 1):
            c = ws.cell(row=1, column=col, value=h)
            c.font, c.fill, c.border = head_font, head_fill, border
            c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
            ws.column_dimensions[c.column_letter].width = w

    def fit(ws, r, values, widths):
        lines = max(math.ceil(len(str(v)) / (w * 1.05)) or 1 for v, w in zip(values, widths))
        ws.row_dimensions[r].height = 13.5 * lines + 5

    wb = Workbook()
    ws = wb.active
    ws.title = "Read Me"
    ws.column_dimensions["A"].width = 120
    for i, line in enumerate(_readme(org, len(m.levels), m.settings), 1):
        c = ws.cell(row=i, column=1, value=line)
        c.font = Font(name="Arial", size=12 if i == 1 else 10, bold=i == 1 or line in ("How to read the matrix", "Who does what"))
        c.alignment = wrap

    mx = wb.create_sheet("DoA Matrix")
    cols = ["Term", "Standard position", *m.levels, "Not approvable"]
    widths = [28, 32, *([34] * len(m.levels)), 36]
    header(mx, cols, widths)
    for r, row in enumerate(m.rows, 2):
        values = [row.get(h, "") for h in cols]
        for col, (h, v) in enumerate(zip(cols, values), 1):
            shown = not_delegated if h in m.levels and not v else v
            c = mx.cell(row=r, column=col, value=shown)
            c.font = Font(name="Arial", size=10, bold=True) if col == 1 else grey if shown == not_delegated else body
            c.alignment, c.border = wrap, border
        fit(mx, r, values, widths)
    mx.freeze_panes = "B2"
    mx.auto_filter.ref = mx.dimensions
    mx.page_setup.orientation = "landscape"
    mx.page_setup.fitToWidth, mx.page_setup.fitToHeight = 1, 0
    mx.sheet_properties.pageSetUpPr.fitToPage = True
    mx.print_title_rows = "1:1"

    ro = wb.create_sheet("Roles")
    rcols = ["Title", "Short title", "Function", "Notes"]
    rwidths = [36, 14, 20, 70]
    header(ro, rcols, rwidths)
    for r, role in enumerate(m.roles, 2):
        for col, h in enumerate(rcols, 1):
            c = ro.cell(row=r, column=col, value=role.get(h, ""))
            c.font, c.alignment, c.border = body, wrap, border

    if m.people:
        pe = wb.create_sheet("People")
        pcols, pwidths = ["Title", "Name", "Email"], [36, 24, 40]
        header(pe, pcols, pwidths)
        for r, p in enumerate(m.people, 2):
            email = p.get("Email", "")
            if email_format:
                parts = p["Name"].split()
                email = email_format.format(first=parts[0].lower(), last=parts[-1].lower())
            for col, v in enumerate([p.get("Title", ""), p.get("Name", ""), email], 1):
                c = pe.cell(row=r, column=col, value=v)
                c.font, c.alignment, c.border = body, wrap, border

    wb.active = 1
    wb.save(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate", help="check the matrix, roles and people files")
    v.add_argument("matrix_dir")
    v.add_argument("--standard", help="the standard agreement (.docx): also check the Contract location column against it and list places no row claims")
    b = sub.add_parser("build", help="validate, then write a formatted .xlsx")
    b.add_argument("matrix_dir")
    b.add_argument("out")
    b.add_argument("--org", default="Company", help="organization name shown in the workbook")
    b.add_argument("--email-format", help='override people emails, e.g. "you+{first}{last}@example.com"')
    args = ap.parse_args(argv)

    m = load(args.matrix_dir)
    errors = validate(m)
    for e in errors:
        print(f"error: {e}", file=sys.stderr)
    if errors:
        return 1
    if args.cmd == "build":
        build(m, args.out, args.org, args.email_format)
        print(f"wrote {args.out}: {len(m.rows)} terms, {len(m.levels)} levels, {len(m.roles)} roles")
    else:
        print(f"ok: {len(m.rows)} terms, {len(m.levels)} levels, {len(m.roles)} roles")
        if args.standard:
            sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
            import contract_io
            import locate
            paras = contract_io.paragraphs(contract_io.extract(Path(args.standard).name, Path(args.standard).read_bytes())["accepted"])
            problems = locate.matrix_problems(args.matrix_dir, paras)
            for e in problems:
                print(f"error: {e}", file=sys.stderr)
            if problems:
                return 1
            gaps = locate.unclaimed(args.matrix_dir, paras)
            print(f"ok: every Contract location is a real place in the standard.")
            print(f"{len(gaps)} places in the standard are claimed by no row. A change in one goes to the matrix owner as not in the matrix:")
            for g in gaps:
                print(f"  {g}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
