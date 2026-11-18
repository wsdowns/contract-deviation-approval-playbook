import csv
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import doa_matrix as dm  # noqa: E402

EXAMPLE = ROOT / "examples" / "acme-saas" / "doa-matrix"


def write(d, name, header, rows):
    with (d / name).open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


@pytest.fixture
def tiny(tmp_path):
    """A two-level matrix for a non-SaaS contract type (a supply agreement)."""
    write(tmp_path, "doa_matrix.csv",
          ["Term", "Standard position", "Level 1", "Level 2", "Not approvable"],
          [["Payment terms", "Net 30", "Net 45: Buyer", "Net 60: Finance Director", "Over Net 90"],
           ["Exclusivity", "None", "", "", "Any exclusivity"]])
    write(tmp_path, "roles.csv", ["Title", "Short title", "Function", "Notes"],
          [["Buyer", "", "Procurement", ""], ["Finance Director", "FD", "Finance", ""]])
    return tmp_path


def test_example_matrix_is_valid():
    assert dm.validate(dm.load(EXAMPLE)) == []


def test_any_contract_type_and_level_count(tiny):
    m = dm.load(tiny)
    assert m.levels == ["Level 1", "Level 2"]
    assert dm.validate(m) == []


def test_approvers_parsing():
    assert dm.approvers("Up to $5M: General Counsel + CFO") == ["General Counsel", "CFO"]
    assert dm.approvers("Pre-approved: remove publicity right: Contracts Manager") == ["Contracts Manager"]
    assert dm.approvers("") == []
    with pytest.raises(ValueError):
        dm.approvers("General Counsel")


def test_unknown_approver_is_an_error(tiny):
    m = dm.load(tiny)
    m.rows[0]["Level 2"] = "Net 60: Treasurer"
    assert any("'Treasurer' is not in roles.csv" in e for e in dm.validate(m))


def test_row_with_no_authority_must_say_not_approvable(tiny):
    m = dm.load(tiny)
    m.rows[1]["Not approvable"] = ""
    assert any("no level grants authority" in e for e in dm.validate(m))


def test_unused_role_and_unknown_person(tiny):
    m = dm.load(tiny)
    m.roles.append({"Title": "CEO", "Short title": "", "Function": "", "Notes": ""})
    m.people.append({"Title": "COO", "Name": "Pat Doe", "Email": "pat@example.com"})
    errors = dm.validate(m)
    assert any("'CEO' is not named anywhere" in e for e in errors)
    assert any("people.csv: title 'COO'" in e for e in errors)


def test_settings_roles_are_checked(tiny):
    m = dm.load(tiny)
    m.settings = {"Record custodian": "Buyer", "Approvals mailbox": "contracts@example.com"}
    assert dm.validate(m) == []
    m.settings["Matrix owner"] = "Chief Legal Officer"
    m.settings["Escalation fax"] = "555-0100"
    errors = dm.validate(m)
    assert any("Matrix owner 'Chief Legal Officer' is not in roles.csv" in e for e in errors)
    assert any("unknown setting 'Escalation fax'" in e for e in errors)


def test_build_writes_workbook(tmp_path):
    from openpyxl import load_workbook
    out = tmp_path / "m.xlsx"
    dm.build(dm.load(EXAMPLE), out, org="ACME, Inc.", email_format="test+{first}{last}@example.com")
    wb = load_workbook(out)
    assert wb.sheetnames == ["Read Me", "DoA Matrix", "Roles", "People"]
    assert wb["DoA Matrix"]["A1"].value == "Term"
    emails = {r[1]: r[2] for r in wb["People"].iter_rows(min_row=2, values_only=True)}
    assert emails["Darla Denkins"] == "test+darladenkins@example.com"
    readme = [c.value for c in wb["Read Me"]["A"]]
    assert "Record custodian: Contracts Manager" in readme
