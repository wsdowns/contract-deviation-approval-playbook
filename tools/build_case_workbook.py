"""Build the three-case Excel workbook from the saved runs (same sources as the Word workbook)."""
import json
import re
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation

sys.path.insert(0, str(Path(__file__).parent))
from extract_worked_examples import RUNS, table  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FP = ROOT / "final-package"
RUN = {"C1": "app-20261111-170919", "C2": "app-20261112-080614", "C3": "app-20261113-104345"}
TITLE = {"C1": "Case 1: Brightwater Logistics ($20K a year)", "C2": "Case 2: Lakeshore Health ($1M a year)", "C3": "Case 3: Summit Ridge ($250K a year)"}
NAVY, WHITE = "0B2A4A", "FFFFFF"
STATUS_FILL = {"Approved": "D5EBDD", "Approved (pre-approved)": "D5EBDD", "Conditional": "FBE9B7", "Partial": "FBE9B7", "Unclear": "FBE9B7",
               "Missing co-approval": "FBE9B7", "Wrong authority": "F6C9C5", "Authority unclear": "FBE9B7", "Not in matrix": "FBE9B7",
               "Not approvable": "F6C9C5", "Denied": "F6C9C5"}
STATUSES = list(STATUS_FILL)
thin = Side(style="thin", color="C9CED6")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)
wb = Workbook()


def plain(t):
    return re.sub(r"\*\*|`", "", t or "")


def sheet(name, headers, rows, widths, status_col=None, freeze="A2", title=None):
    ws = wb.create_sheet(name)
    r0 = 1
    if title:
        ws.cell(1, 1, title).font = Font(bold=True, size=13, color=NAVY)
        r0 = 3
    for j, h in enumerate(headers, 1):
        c = ws.cell(r0, j, h)
        c.font = Font(bold=True, color=WHITE)
        c.fill = PatternFill("solid", fgColor=NAVY)
        c.alignment = Alignment(wrap_text=True, vertical="center")
        c.border = BORDER
    for i, row in enumerate(rows, r0 + 1):
        for j, v in enumerate(row, 1):
            c = ws.cell(i, j, plain(v))
            c.alignment = Alignment(wrap_text=True, vertical="top")
            c.border = BORDER
        if status_col is not None:
            st = ws.cell(i, status_col).value
            if st in STATUS_FILL:
                ws.cell(i, status_col).fill = PatternFill("solid", fgColor=STATUS_FILL[st])
    for j, w in enumerate(widths, 1):
        ws.column_dimensions[ws.cell(r0, j).column_letter].width = w
    ws.freeze_panes = ws.cell(r0 + 1, 1)
    return ws, r0


# ---- README
ws = wb.active
ws.title = "README"
lines = [
    ("Contract Deviation Approval Playbook: three-case workbook", True),
    ("Cases and company names are fictional stand-ins.", False),
    ("", False),
    ("What this is", True),
    ("The tables from three real runs of the playbook: the changes found, the routing, and the approval record for each case, plus the rules the AI ran against (matrix and people).", False),
    ("The AI never saw the answer keys. The 'Key check' sheet compares each run with its key.", False),
    ("", False),
    ("Sheets", True),
    ("Matrix, People, Settings: the rules and the titles-to-names list the AI was given.", False),
    ("C1, C2, C3 Changes / Routing / Record: Stage 1 (changes), Stage 2 (who may approve), Stages 4 to 6 (approval record).", False),
    ("Key check: expected result against the run result, per change.", False),
    ("Summary: counts of each status per case (formulas over the Record sheets).", False),
    ("Blank record: a template with a status drop-down, for running a new case by hand.", False),
    ("Prompts: the full text of the five playbook prompts, one per row.", False),
    ("AI gate: the setup gate for the AI environment, with sign-off fields. Complete it before any real deal.", False),
    ("", False),
    ("Status colours", True),
    ("Green: approved. Amber: open, conditional or needs a person's ruling. Red: denied, wrong authority or not approvable.", False),
    ("", False),
    ("Limits", True),
    ("Matching a reply to its request rests on subject and content. A unique request ID is the planned fix; the runs predate it.", False),
    ("Replies were simulated from messages written in advance. The wording of the cases is a stand-in. The hand-off test by an independent person has not been run.", False),
]
for i, (t, b) in enumerate(lines, 1):
    c = ws.cell(i, 1, t)
    c.font = Font(bold=b, size=14 if i == 1 else 11, color=NAVY if b else "000000")
    c.alignment = Alignment(wrap_text=True, vertical="top")
ws.column_dimensions["A"].width = 120

# ---- rules
mx = json.load(open(FP / "matrix.json"))
sheet("Matrix", mx["matrix"][0], [[c or "None" for c in r] for r in mx["matrix"][1:]], [28, 38, 34, 38, 44, 38])
sheet("People", ["Title", "Name", "Email", "Function", "Role in the process"], mx["people"], [34, 22, 32, 18, 70])
sheet("Settings", ["Setting", "Held by"], mx["settings"], [26, 40])

# ---- cases
record_ranges = {}
for cid, run in RUN.items():
    d = RUNS / run
    rd = lambda n: (d / n).read_text() if (d / n).exists() else ""
    s1, s2 = table(rd("stage1.md"), "Deviations"), table(rd("stage2.md"), None)
    rec = table(rd("stage6.md") or rd("stage4.md"), "Approval record")
    h1 = ["ID", "Clause", "Standard position", "Requested position (exact words)", "Kind", "Notes"]
    sheet(f"{cid} Changes", h1, [[r.get(k, "") for k in h1] for r in s1], [6, 30, 50, 55, 12, 55], title=TITLE[cid] + ": changes found (Stage 1)")
    h2 = ["ID", "Matrix row", "Outcome", "Cell relied on (exact words)", "Approver titles", "Joint?", "Prerequisites", "Reasoning"]
    sheet(f"{cid} Routing", h2, [[r.get(k, "") for k in h2] for r in s2], [6, 28, 20, 55, 28, 10, 24, 60], title=TITLE[cid] + ": who may approve (Stage 2)")
    h4 = ["ID", "Change", "Matrix row and level", "Approver (name, title)", "Decision (exact words)", "Date and time", "Evidence", "Status", "Conditions (exact words)", "Final outcome", "Notes"]
    ws4, r0 = sheet(f"{cid} Record", h4, [[r.get(k, "") for k in h4] for r in rec], [7, 34, 34, 30, 48, 22, 34, 20, 26, 20, 60], status_col=8, title=TITLE[cid] + ": approval record (Stages 4 to 6)")
    record_ranges[cid] = (f"'{cid} Record'", r0 + 1, r0 + len(rec))

# ---- key check
N = json.load(open(FP / "case_notes.json"))
rows = []
for cid, key in (("C1", "case-1"), ("C2", "case-2"), ("C3", "case-3")):
    for r in N[key]["keyRows"]:
        rows.append([TITLE[cid].split(" (")[0]] + r)
ws, r0 = sheet("Key check", ["Case", "Change", "Answer key", "The run produced", "Match"], rows, [26, 40, 46, 56, 20])
for i in range(r0 + 1, r0 + 1 + len(rows)):
    m = ws.cell(i, 5)
    m.fill = PatternFill("solid", fgColor="D5EBDD" if str(m.value).startswith("Yes") else "F6C9C5")

# ---- summary (formulas)
ws = wb.create_sheet("Summary")
ws["A1"] = "Rows per status in each approval record"
ws["A1"].font = Font(bold=True, size=13, color=NAVY)
for j, h in enumerate(["Status", "Case 1", "Case 2", "Case 3"], 1):
    c = ws.cell(3, j, h)
    c.font = Font(bold=True, color=WHITE)
    c.fill = PatternFill("solid", fgColor=NAVY)
for i, st in enumerate(STATUSES, 4):
    ws.cell(i, 1, st).fill = PatternFill("solid", fgColor=STATUS_FILL[st])
    for j, cid in enumerate(("C1", "C2", "C3"), 2):
        sh, a, b = record_ranges[cid]
        ws.cell(i, j, f'=COUNTIF({sh}!$H${a}:$H${b},$A{i})')
last = 3 + len(STATUSES)
ws.cell(last + 1, 1, "Total rows").font = Font(bold=True)
for j in (2, 3, 4):
    col = ws.cell(3, j).column_letter
    ws.cell(last + 1, j, f"=SUM({col}4:{col}{last})").font = Font(bold=True)
ws.column_dimensions["A"].width = 28
for col in "BCD":
    ws.column_dimensions[col].width = 12

# ---- blank record
h4 = ["ID", "Change", "Matrix row and level", "Approver (name, title)", "Decision (exact words)", "Date and time", "Evidence", "Status", "Conditions (exact words)", "Final outcome", "Notes"]
ws, r0 = sheet("Blank record", h4, [[""] * 11 for _ in range(15)], [7, 34, 34, 30, 48, 22, 34, 20, 26, 20, 60])
dv = DataValidation(type="list", formula1='"' + ",".join(STATUSES) + '"', allow_blank=True)
ws.add_data_validation(dv)
dv.add(f"H{r0 + 1}:H{r0 + 15}")
dv2 = DataValidation(type="list", formula1='"Conceded as approved,Not conceded,Conceded differently"', allow_blank=True)
ws.add_data_validation(dv2)
dv2.add(f"J{r0 + 1}:J{r0 + 15}")

PROMPTS = [("00-standing-instructions.md", "Standing instructions: give first"), ("01-identify.md", "Stage 1: identify each changed term"), ("02-locate.md", "Stage 2: locate the DoA rule"), ("03-draft-requests.md", "Stage 3: draft the escalation requests"), ("04-record-decisions.md", "Stage 4: document the actual decisions")]
ws, r0 = sheet("Prompts", ["File", "What it does", "Full text (paste as written)"], [[f, t, (ROOT / "playbook" / f).read_text()] for f, t in PROMPTS], [30, 36, 140])
for i in range(r0 + 1, r0 + 1 + len(PROMPTS)):
    ws.row_dimensions[i].height = 400
gate = [
    ["1", "No retention you do not control: zero data retention (ZDR) in writing, or a private instance (own infrastructure, or a hosted private deployment in the company's own cloud tenancy)", "Signed terms. Ask what is still logged and for how long", "", ""],
    ["2", "No training on inputs or outputs", "Agreement says so in terms", "", ""],
    ["3", "Confidentiality covers customers' terms; subprocessors listed", "At least as strict as duties owed to customers", "", ""],
    ["4", "Access control and audit", "Named users, company sign-in, company-controlled logs", "", ""],
    ["5", "Known data location and deletion", "Where processed; how to delete", "", ""],
    ["6", "Sign-off on record", "Legal and security approved; name, date, model and version", "", ""],
    ["7", "Not a personal or free account", "Consumer chat apps are out for real deals", "", ""],
    ["Q", "Model qualified: Case 1 run and compared with its answer key", "Misses changes, picks levels itself, or reads silence as approval means not fit", "", ""],
]
ws, r0 = sheet("AI gate", ["#", "Requirement", "What to check", "Pass or fail", "Evidence, name, date"], gate, [5, 70, 55, 14, 40])
dvg = DataValidation(type="list", formula1='"Pass,Fail,Not checked"', allow_blank=True)
ws.add_data_validation(dvg)
dvg.add(f"D{r0 + 1}:D{r0 + len(gate)}")
ws.cell(r0 + len(gate) + 2, 2, "Environment (name, version, date):").font = Font(bold=True)
ws.cell(r0 + len(gate) + 3, 2, "Approved by:").font = Font(bold=True)
ws.cell(r0 + len(gate) + 5, 2, "Stand-in data only needs no gate. Real deals need every row to pass.").font = Font(italic=True)

out = FP / "Contract_Deviation_Approval_Playbook_Case_Workbook.xlsx"
wb.save(out)
print(out.name, wb.sheetnames)
