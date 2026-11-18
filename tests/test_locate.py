"""Placing each change on a matrix row in code, with no AI."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "tests"))
import contract_io  # noqa: E402
import locate  # noqa: E402

M = ROOT / "examples/acme-saas/doa-matrix"
STD = ROOT / "examples/acme-saas/contracts/ACME_SaaS_Agreement_v1.0.docx"
REDLINE = ROOT / "examples/acme-saas/cases/case-1-acme-redline/inputs/Brightwater_Redline_of_ACME_SaaS_Agreement.docx"
BASE = contract_io.extract("s.docx", STD.read_bytes())["accepted"]


def variant(edit):
    """The standard agreement with one paragraph changed. edit(paragraphs) edits the list in place."""
    paras = contract_io.paragraphs(BASE)
    edit(paras)
    return "\n".join(paras)


def append_to(prefix, text):
    def go(paras):
        i = next(n for n, p in enumerate(paras) if p.startswith(prefix))
        paras[i] += " " + text
    return go


def place(text):
    return locate.locate(contract_io.differences(BASE, text), contract_io.paragraphs(BASE), contract_io.paragraphs(text), M)


def test_the_brightwater_redline_is_placed_as_the_answer_key_expects():
    r = contract_io.extract("r.docx", REDLINE.read_bytes())["accepted"]
    got = {d["where"]: (d["status"], d["rows"]) for d in place(r)}
    assert got["Key Terms > General Cap Amount"] == ("located", ["General liability cap"])
    assert got["New section: Service Levels"] == ("located", ["Service levels and credits"])
    assert got["Payment & Taxes > Payment"] == ("located", ["Payment terms"])
    assert got["New section: Renewal Pricing"] == ("located", ["Renewal price increase cap"])
    assert got["General Terms > Logo Rights"] == ("located", ["Publicity"])
    assert got["General Terms > Notices"] == ("unlocated", [])  # no row claims Notices: the matrix owner is asked
    assert any(d["status"] == "placeholder" for d in place(r))  # the customer's name fills a blank: not a deviation


def test_two_rows_sharing_a_paragraph_are_told_apart_by_keywords():
    pay = place(variant(append_to("Payment. ", "Unless the Order Form states otherwise, invoices are payable within 45 days of the invoice date.")))
    bill = place(variant(append_to("Payment. ", "Provider will invoice Fees quarterly in advance.")))
    assert [d["rows"] for d in pay] == [["Payment terms"]] and pay[0]["how"] == "contract location and keywords"
    assert [d["rows"] for d in bill] == [["Billing frequency"]]


def test_an_edit_the_keywords_cannot_decide_is_ambiguous_and_lists_the_candidates():
    d = place(variant(append_to("Payment. ", "Both parties will agree the schedule in writing.")))
    assert d[0]["status"] == "ambiguous" and set(d[0]["rows"]) == {"Payment terms", "Billing frequency"}


def test_an_unnumbered_new_heading_the_matrix_does_not_know_is_unlocated():
    d = place(variant(lambda paras: paras.insert(60, "Fees Escalator.  Fees rise by 3% a year.")))
    assert d[0]["status"] == "unlocated" and d[0]["where"] == "New section: Fees Escalator"


def test_a_change_in_a_place_no_row_claims_is_unlocated():
    d = place(variant(append_to("Taxes. ", "Customer pays no taxes.")))
    assert d[0]["status"] == "unlocated" and d[0]["where"] == "Payment & Taxes > Taxes"


def test_the_changed_words_decide_between_rows_that_share_a_place():
    """Several rows claim the Uncapped Claims field. A new clause about gross negligence belongs to one of them."""
    d = place(variant(append_to("Notwithstanding anything to the contrary, the following claims", "(c) gross negligence or willful misconduct.")))
    assert d[0]["where"] == "Key Terms > Uncapped Claims" and d[0]["rows"] == ["Uncapped gross negligence and willful misconduct"]


def test_the_shipped_matrix_has_sound_locations():
    assert locate.matrix_problems(M, contract_io.paragraphs(BASE)) == []


def test_matrix_problems_are_reported_in_plain_words(tmp_path):
    import shutil
    m = tmp_path / "m"
    shutil.copytree(M, m)
    text = (m / "doa_matrix.csv").read_text()
    (m / "doa_matrix.csv").write_text(text.replace("Payment & Taxes > Payment\",\"payable", "Payment & Taxes > Paymnt\",\"payable").replace("Key Terms > General Cap Amount;", "Nowhere > Nothing;"))
    problems = locate.matrix_problems(m, contract_io.paragraphs(BASE))
    assert any("not a place in the standard" in p for p in problems)
    (m / "doa_matrix.csv").write_text(text.replace("payable; within; days; due; net", ""))
    assert any("needs Keywords" in p or "Keywords" in p for p in locate.matrix_problems(m, contract_io.paragraphs(BASE)))
    (m / "doa_matrix.csv").write_text(text.replace(",Contract location,Keywords", ",Elsewhere,Keywords", 1))
    assert "no 'Contract location' column" in locate.matrix_problems(m, contract_io.paragraphs(BASE))[0]


CASES = ROOT / "examples/acme-saas/cases"
EXPECTED = {
    "case-2-lakeshore-paper/inputs/Lakeshore_Redline_of_ACME_SaaS_Agreement.docx": {
        "Key Terms > Governing Law": "Governing law and venue",
        "Key Terms > Chosen Courts": "Governing law and venue",
        "Key Terms > General Cap Amount": "General liability cap",
        "Key Terms > Security Policy": "Security commitments and audit",
        "New section: Most-Favored Customer Pricing": "Most-favored customer pricing",
        "New section: Termination for Convenience": "Customer termination for convenience",
        "New section: Data Location": "Data residency"},
    "case-3-acme-redline-2/inputs/SummitRidge_Redline_of_ACME_SaaS_Agreement.docx": {
        "Key Terms > Covered Claims": "Provider indemnification scope",
        "Key Terms > Uncapped Claims": "Uncapped gross negligence and willful misconduct",
        "Key Terms > Insurance Minimums": "Insurance",
        "New section: Service Levels": "Service levels and credits",
        "Payment & Taxes > Payment": "Billing frequency"},
}


@pytest.mark.parametrize("path", sorted(EXPECTED))
def test_the_staged_redlines_are_true_redlines_and_are_placed_as_designed(path):
    r = contract_io.extract("r.docx", (CASES / path).read_bytes())
    assert r["kind"] == "docx-tracked" and r["tracked_count"] >= 6
    assert contract_io.differences(BASE, r["rejected"]) == []  # rejecting every tracked change gives back ACME's standard exactly
    got = {d["where"]: (d["rows"][0] if d["rows"] else None) for d in place(r["accepted"]) if d["status"] != "placeholder"}
    assert got == EXPECTED[path]
