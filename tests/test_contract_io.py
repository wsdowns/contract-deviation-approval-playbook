"""Reading uploaded contracts and finding differences without AI."""
import io
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
import contract_io as c  # noqa: E402

EX = ROOT / "examples" / "acme-saas"
NS = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'


def docx(*paras):
    """paras: strings of run XML, each wrapped in a paragraph."""
    body = "".join(f"<w:p>{p}</w:p>" for p in paras)
    xml = f'<?xml version="1.0" encoding="UTF-8"?><w:document {NS}><w:body>{body}</w:body></w:document>'
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("word/document.xml", xml)
    return buf.getvalue()


def run(t):
    return f'<w:r><w:t xml:space="preserve">{t}</w:t></w:r>'


def ins(t):
    return f'<w:ins w:id="1" w:author="x"><w:r><w:t xml:space="preserve">{t}</w:t></w:r></w:ins>'


def dele(t):
    return f'<w:del w:id="2" w:author="x"><w:r><w:delText xml:space="preserve">{t}</w:delText></w:r></w:del>'


BASE = "Payment terms. Customer will pay within 30 days. Liability is capped at 1x fees."


def test_tracked_changes_give_accepted_rejected_and_marked_text():
    f = docx(run("Payment terms. Customer will pay within ") + dele("30") + ins("45") + run(" days. Liability is capped at 1x fees."))
    r = c.extract("a.docx", f)
    assert r["kind"] == "docx-tracked" and r["tracked_count"] == 1
    assert "45 days" in r["accepted"] and "30" not in r["accepted"]
    assert r["rejected"] == BASE
    assert "~~30~~**45**" in r["tracked_text"]


def test_clean_word_file_is_flagged_with_no_tracked_changes():
    r = c.extract("a.docx", docx(run(BASE)))
    assert r["kind"] == "docx-clean" and r["warnings"]


def test_untracked_edit_is_found():
    # the customer changed 30 to 90 and the change is not tracked; a second change is tracked
    f = docx(run("Payment terms. Customer will pay within 90 days. Liability is capped at ") + dele("1x") + ins("2x") + run(" fees."))
    r = c.analyse("a.docx", f, BASE)
    assert len(r["total"]) == 1  # the sentences are compared as a whole
    assert len(r["untracked"]) >= 1
    assert any("90" in d["other"] for d in r["untracked"])


def test_fully_tracked_file_has_no_untracked_differences():
    f = docx(run("Payment terms. Customer will pay within ") + dele("30") + ins("45") + run(" days. Liability is capped at 1x fees."))
    r = c.analyse("a.docx", f, BASE)
    assert r["untracked"] == [] and len(r["total"]) == 1


def test_layout_and_quote_style_are_not_differences():
    assert c.differences("The Customer’s fees:  due now.", "The Customer's   fees: due now.") == []


def test_text_and_pdf_and_bad_files():
    t = c.extract("a.txt", b"hello")
    assert t["kind"] == "text" and t["warnings"]
    with pytest.raises(c.ContractError):
        c.extract("a.exe", b"x")
    with pytest.raises(c.ContractError):
        c.extract("a.docx", b"not a zip")
    with pytest.raises(c.ContractError):
        c.extract("a.txt", b"x" * (c.MAX_BYTES + 1))


def test_real_redline_matches_the_key_exactly():
    base = c.extract("s.docx", (EX / "contracts" / "ACME_SaaS_Agreement_v1.0.docx").read_bytes())["accepted"]
    r = c.analyse("b.docx", (EX / "cases" / "case-1-acme-redline" / "inputs" / "Brightwater_Redline_of_ACME_SaaS_Agreement.docx").read_bytes(), base)
    assert r["kind"] == "docx-tracked" and r["untracked"] == []
    assert len(r["total"]) == 7  # preamble, cap, service levels, payment, renewal, logo, notices
