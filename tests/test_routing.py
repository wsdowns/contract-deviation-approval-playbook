"""The code check of drafted requests against the matrix."""
from pathlib import Path

import pytest

import routing
import server
from test_portal import act_as, app, call, wait  # noqa: F401
from test_ledger import SELLER, up

MATRIX = Path(__file__).resolve().parents[1] / "examples/acme-saas/doa-matrix"


def req(to, row, level, subject="x"):
    lines = f"**To:** {to}\n**Subject:** {subject}\n" + (f"**Matrix row:** {row}\n" if row is not None else "") + (f"**Level:** {level}\n" if level else "") + "\nBody"
    return {"to": to, "subject": subject, "text": lines}


DARLA = "Darla Denkins, Deal Desk Manager"
VIV = "Vivian Fairfax, VP Finance"


def problems(reqs, **kw):
    with pytest.raises(ValueError) as e:
        routing.check(reqs, MATRIX, **kw)
    return str(e.value)


def test_a_matching_request_passes():
    routing.check([req(DARLA, "Payment terms", "1"), req(VIV, "Renewal price increase cap", "Level 2")], MATRIX)


def test_wrong_person_for_the_row_is_refused():
    assert "not an approver for 'Payment terms' at Level 1" in problems([req(VIV, "Payment terms", "1")])


def test_unknown_row_blank_level_and_missing_lines_are_refused():
    assert "not a Term" in problems([req(DARLA, "Free lunch", "1")])
    assert "no approval at" in problems([req(DARLA, "Fraud carve-out", "2")])  # Level 2 cell is blank
    assert "does not name the matrix row" in problems([req(DARLA, None, "1")])
    assert "no level named" in problems([req(DARLA, "Payment terms", None)])


def test_a_joint_approval_needs_every_approver():
    gc = "Gordon Cole, General Counsel"
    only_gc = [req(gc, "General liability cap", "3")]
    assert "no request goes to Chief Financial Officer" in problems(only_gc)
    routing.check(only_gc, MATRIX, complete=False)  # a follow-up to one approver is allowed
    both = only_gc + [req("Cora Finch, Chief Financial Officer", "General liability cap", "Level 3")]
    routing.check(both, MATRIX)


def test_requests_without_a_row_go_only_to_whoever_handles_terms_not_in_the_matrix():
    routing.check([req(DARLA, "none", None)], MATRIX)  # the Deal Desk Manager, per the 'Terms not in the matrix' setting
    assert "goes to Deal Desk Manager" in problems([req("Grace Colton, General Counsel", "none", None)])


def test_titles_in_cells():
    shorts = routing._short_titles(MATRIX)
    assert routing.titles_in("Up to 3x fees, or a fixed floor up to $5M: General Counsel + CFO", shorts) == {"General Counsel", "Chief Financial Officer"}
    assert routing.titles_in("Pre-approved: express fraud carve-out: Contracts Manager", shorts) == {"Contracts Manager"}


def test_a_reading_that_does_not_match_the_matrix_is_not_routed(app, monkeypatch):
    """The AI quotes words that are not in the cell it names: nothing goes to that approver, and the change goes to the matrix owner."""
    import json as _json
    base, runs = app
    real = server.stub_assess

    def bad(prompt):
        out = _json.loads(real(prompt))
        for a in out["assessments"]:
            a["cell_quote"] = "words that are not in any cell of the matrix"
        return _json.dumps(out)

    monkeypatch.setattr(server, "stub_assess", bad)
    s = up(base, act_as(base, SELLER))
    items = _json.loads((runs / s["run"] / "assessment.json").read_text())["items"]
    assert all(i["outcome"] != "route" for i in items if i.get("row"))
    assert any(i.get("unverified") for i in items)
    titles = {q["to_title"] for q in s["portal"]}
    assert titles == {"Deal Desk Manager"}  # only the Deal Desk is asked: nothing is routed on a reading that did not match


def test_numbers_in_the_request_raise_a_level_the_ai_set_too_low(app, monkeypatch):
    """The AI puts the 3% renewal cap at Level 1 (a 5% cap). The request's number matches Level 2, so code takes Level 2."""
    import json as _json
    base, runs = app
    real = server.stub_assess

    def low(prompt):
        out = _json.loads(real(prompt))
        for a in out["assessments"]:
            if a["row"] == "Renewal price increase cap":
                a["level"], a["cell_quote"] = 1, "Cap at 5%"
        return _json.dumps(out)

    monkeypatch.setattr(server, "stub_assess", low)
    s = up(base, act_as(base, SELLER))
    items = {i["where"]: i for i in _json.loads((runs / s["run"] / "assessment.json").read_text())["items"]}
    renewal = items["New section: Renewal Pricing"]
    assert renewal["level"] == 2 and renewal["titles"] == ["VP Finance"] and "Raised from Level 1 to Level 2" in renewal["reasoning"]


def test_the_number_check_never_lowers_a_level():
    import assess
    row = {"Level 1": "Net 45: Deal Desk Manager", "Level 2": "Net 60: VP Finance", "Level 3": "Net 90: CFO"}
    assert assess.level_by_numbers("invoices are payable within 45 days", "", row) == 1
    assert assess.level_by_numbers("invoices are payable within 60 days", "", row) == 2
    assert assess.level_by_numbers("invoices are payable within 50 days", "", row) is None  # no cell names 50: the AI's reading stands
    assert assess.level_by_numbers("within 30 days", "within 30 days", row) is None  # a number already in the standard decides nothing
    renewal = {"Level 1": "Cap at 5%: Deal Desk Manager", "Level 2": "Cap at 3%: VP Finance", "Level 3": "Lesser of 3% or CPI: CFO"}
    assert assess.level_by_numbers("increase the Fees by no more than 3%", "", renewal) == 2  # Levels 2 and 3 both name 3%: the lowest
    two = {"Level 1": "Up to 1.5x fees: Contracts Manager", "Level 2": "Up to 2x fees: Associate General Counsel", "Level 3": ""}
    assert assess.level_by_numbers("a cap of 2x the Fees", "1x the Fees", two) == 2


def test_worddiff_shows_exactly_which_words_changed():
    import assess
    d = assess.worddiff("Notices will be deemed given (a) upon confirmed delivery if by email; or (b) two days after mailing.",
                        "A notice is deemed given (a) upon confirmed delivery if by email; or (b) two days after mailing.")
    assert d.startswith("[-Notices will be-] {+A notice is+} deemed given")
    assert assess.worddiff("1x the Fees", "2x the Fees").startswith("[-1x-] {+2x+}")
    assert assess.worddiff("", "a new sentence") == "{+a new sentence+}"
